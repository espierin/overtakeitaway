"""Portable GitHub storage and static publication, without changing analysis/renderers.

Originals live in verified, immutable season tarballs. Pages contains the same DOM,
JSON and scripts, with content-addressed script storage and lossless raster storage.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote as url_quote, unquote, urlsplit

from PIL import Image
import yaml

from .io import read_json, write_json
from .data_storage import pack_data, verify_data, materialize_data


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def settings(root):
    return yaml.safe_load((Path(root) / 'config/publication.yaml').read_text())


def storage_entries(registry):
    return [*registry['seasons'].values(),*[registry[key] for key in ['sources','presentation'] if registry.get(key)]]


def inside(root, path):
    root, path = Path(root).resolve(), Path(path).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Pad buiten project: {path}')
    return path


def latest_runs(root, from_year=1950):
    root = Path(root).resolve()
    for pointer in sorted((root / 'analyses').glob('*/*/latest.json')):
        if int(pointer.parent.parent.name) < from_year:
            continue
        run = inside(pointer.parent, pointer.parent / read_json(pointer)['run'])
        if not run.is_dir():
            raise ValueError(f'Uitvoering ontbreekt: {run}')
        m = read_json(run / 'manifest.json')
        if m['status'] not in ('volledig', 'gedeeltelijk'):
            raise ValueError(f'Latest verwijst naar ongeslaagde uitvoering: {pointer}')
        yield pointer, run, m


def verify_bundle(path, expected=None):
    """Read all bytes and validate every member; reject unsafe or duplicate paths."""
    if expected and digest(path) != expected:
        raise ValueError(f'Archiefhash wijkt af: {path}')
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(names) != len(set(names)):
            raise ValueError('Dubbele archiefpaden')
        for m in members:
            p = Path(m.name)
            if p.is_absolute() or '..' in p.parts or not m.isfile():
                raise ValueError(f'Onveilig archiefpad: {m.name}')
        meta = json.load(archive.extractfile('_bundle.json'))
        if set(names) != set(meta['files']) | {'_bundle.json'}:
            raise ValueError('Archiefinventaris wijkt af')
        for name, sha in meta['files'].items():
            h = hashlib.sha256()
            with archive.extractfile(name) as f:
                for block in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(block)
            if h.hexdigest() != sha:
                raise ValueError(f'Archiefbestand beschadigd: {name}')
    return meta


def bundle(root, files, directory, label):
    root, directory = Path(root).resolve(), Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    files = sorted(set(inside(root, p) for p in files))
    hashes = {p.relative_to(root).as_posix(): digest(p) for p in files}
    fingerprint = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    name = f'{label}-{fingerprint[:24]}.tar.gz'
    target = directory / name
    if not target.exists():
        temp = target.with_suffix('.partial')
        try:
            with temp.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, compresslevel=6) as gz, tarfile.open(fileobj=gz, mode='w|') as archive:
                data = json.dumps({'schema': 1, 'files': hashes}, sort_keys=True).encode()
                info = tarfile.TarInfo('_bundle.json'); info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
                for p in files:
                    info = archive.gettarinfo(str(p), p.relative_to(root).as_posix())
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ''
                    with p.open('rb') as f:
                        archive.addfile(info, f)
            verify_bundle(temp)
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
    sha = digest(target)
    verify_bundle(target, sha)
    return {'asset': name, 'sha256': sha, 'bytes': target.stat().st_size, 'files': len(files)}


def archive_seasons(root, directory, from_year=1950, years=None):
    root = Path(root).resolve()
    registry_path = root / '_storage/index.json'
    registry = read_json(registry_path) if registry_path.exists() else {'schema': 1, 'seasons': {}}
    groups = {}; shared_sources=[]
    for pointer, run, manifest in latest_runs(root, from_year):
        year = pointer.parent.parent.name
        if years and int(year) not in years:
            continue
        # Compact snapshots have no raw inputs. Keep their existing verified archive.
        if not (run / 'data/raw').exists():
            if year not in registry['seasons']:
                raise ValueError(f'Brondata en archiefreferentie ontbreken voor {year}')
            continue
        group = groups.setdefault(year, [])
        group.extend([pointer, *(p for p in run.rglob('*') if p.is_file()),
                      *(p for p in (pointer.parent / 'corrections').rglob('*') if p.is_file())])
        normalized = run / 'data/normalized/input.json'
        if normalized.is_file():
            history_cache = read_json(normalized).get('history_cache')
            if history_cache:
                cached = inside(root, root / history_cache)
                if not (cached / 'bundle.json').is_file() or not (cached / 'locations.json.gz').is_file():
                    raise ValueError(f'FastF1-herstelgegevens ontbreken: {history_cache}')
                group.extend(p for p in cached.rglob('*') if p.is_file())
        # Keep original HTTP response bytes and request metadata for offline reanalysis.
        # Identical requests are deduplicated within each season bundle.
        for source in manifest.get('sources',[]):
            if not source.get('url'):continue
            key=hashlib.sha256(source['url'].encode()).hexdigest()
            body=root/'cache'/f'{key}.body';metadata=root/'cache'/f'{key}.meta.json'
            if body.is_file() and metadata.is_file() and (not source.get('sha256') or digest(body)==source['sha256']):
                (shared_sources if int(year)<2020 else group).extend([body,metadata])
    for year, files in groups.items():
        # Never replace a whole season archive with just its newly added races.
        if year in registry['seasons']:
            expected = [r for r in latest_runs(root, from_year) if r[0].parent.parent.name == year]
            if any(not (run / 'data/raw').exists() for _, run, _ in expected):
                raise ValueError(f'Herstel eerst het complete seizoen {year} uit het archief')
        print(f'Archiveren en verifiëren: {year}', flush=True)
        entry = bundle(root, files, directory, f'season-{year}')
        entry['tag'] = settings(root)['archive_tag_prefix'] + year
        registry['seasons'][year] = entry
    source_files = [p for p in (root / 'analyses/sources').rglob('*') if p.is_file()]+shared_sources
    for name in registry.get('sources',{}).get('cache_files',[]):
        p=inside(root,root/name)
        if not p.is_file():raise ValueError('Herstel eerst het gedeelde bronarchief vóór opnieuw archiveren')
        source_files.append(p)
    if source_files:
        entry = bundle(root, source_files, directory, 'sources')
        entry['tag'] = settings(root)['archive_tag_prefix'] + 'sources'
        entry['cache_files']=sorted({p.relative_to(root).as_posix() for p in source_files if p.relative_to(root).parts[0]=='cache'})
        registry['sources'] = entry
    if registry.get('presentation') and groups:
        # New base archives already include the currently selected presentation.
        covered=set(registry['presentation'].get('covered_years',[]))|set(groups)
        if covered.issuperset(registry['seasons']):registry.pop('presentation')
        else:registry['presentation']['covered_years']=sorted(covered)
    write_json(registry_path, registry)
    return registry


def restore_bundle(path, root, expected=None, overwrite=False):
    root = Path(root).resolve(); root.mkdir(parents=True, exist_ok=True)
    meta = verify_bundle(path, expected)
    # Inspect every destination before changing anything (including symlink escape).
    for name, sha in meta['files'].items():
        target = inside(root, root / name)
        if target.exists() and digest(target) != sha and not overwrite:
            raise ValueError(f'Bestaand afwijkend bestand: {target}; gebruik --overwrite')
    with tarfile.open(path, 'r:gz') as archive:
        for name in meta['files']:
            target = inside(root, root / name); target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(target.name + '.restore-partial')
            with archive.extractfile(name) as src, temp.open('wb') as dst:
                shutil.copyfileobj(src, dst)
            os.replace(temp, target)
    return len(meta['files'])


def materialize_run(root, run):
    """Restore missing run inputs on demand after a verified local cleanup."""
    root,run=Path(root).resolve(),Path(run).resolve()
    inside(root,run)
    registry_path=root/'_storage/index.json'
    if not registry_path.exists():return
    year=run.relative_to(root).parts[1]
    registry=read_json(registry_path)
    entry=registry.get('seasons',{}).get(year)
    if not entry:return
    package=root/'storage/archives'/entry['asset']
    if not package.exists():
        if not (run/'data/derived/analysis.json').exists() and not (run/'data/raw/race.json').exists():
            raise ValueError(f'Herstel eerst seizoen {year} uit GitHub Releases: {entry["asset"]}')
        return
    meta=verify_bundle(package,entry['sha256'])
    prefix=run.relative_to(root).as_posix()+'/data/'
    with tarfile.open(package,'r:gz') as archive:
        for name in meta['files']:
            target=inside(root,root/name)
            if name.startswith(prefix) and not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.extractfile(name) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
        # Restore missing exact HTTP cache entries as well. Existing newer entries stay.
        for name in meta['files']:
            target=inside(root,root/name)
            if name.startswith('cache/') and not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.extractfile(name) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
    shared=registry.get('sources')
    if shared and (root/'storage/archives'/shared['asset']).exists():
        shared_path=root/'storage/archives'/shared['asset']
        shared_meta=verify_bundle(shared_path,shared['sha256'])
        with tarfile.open(shared_path,'r:gz') as archive:
            for name in shared_meta['files']:
                target=inside(root,root/name)
                if not target.exists():
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with archive.extractfile(name) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)


def restore_presentation(path,root,expected=None,exclude_years=(),selected_years=None):
    """Apply UI files only to currently selected runs, without rolling back pointers."""
    root=Path(root).resolve();meta=verify_bundle(path,expected)
    prefixes=[run.relative_to(root).as_posix()+'/' for pointer,run,_ in latest_runs(root)
              if pointer.parent.parent.name not in {str(year) for year in exclude_years}
              and (selected_years is None or int(pointer.parent.parent.name) in selected_years)]
    with tarfile.open(path,'r:gz') as archive:
        for name in meta['files']:
            if not any(name.startswith(prefix) for prefix in prefixes):continue
            target=inside(root,root/name);target.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(name) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)


def freeze_website(root,output,archives):
    """Capture a copy while the owner continues editing. Never touch their files.

    Heavy analysis inputs remain in the already verified season archives; small
    presentation changes get their own immutable overlay, avoiding raw-data copies.
    """
    root,output,archives=Path(root).resolve(),Path(output).resolve(),Path(archives).resolve()
    if output.exists():raise ValueError('Bevroren bronmap bestaat al')
    output.mkdir(parents=True)
    registry=read_json(root/'_storage/index.json');files=set();inventories={}
    for year,entry in registry['seasons'].items():
        with tarfile.open(archives/entry['asset'],'r:gz') as archive:
            inventories[year]=json.load(archive.extractfile('_bundle.json'))['files']
    def copy(source):
        dest=output/source.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True)
        for attempt in range(5):
            before=source.stat();data=source.read_bytes();after=source.stat()
            if (before.st_mtime_ns,before.st_size)==(after.st_mtime_ns,after.st_size):
                dest.write_bytes(data);return dest
        raise ValueError(f'Bestand blijft wijzigen tijdens kopiëren: {source}')
    for pointer,run,m in latest_runs(root):
        year=pointer.parent.parent.name;original=inventories[year]
        # A presentation overlay cannot substitute for absent/changed internal data.
        for name,sha in m.get('file_hashes',{}).items():
            if name.startswith('data/') and original.get((run/name).relative_to(root).as_posix())!=sha:
                raise ValueError(f'Archiveer eerst gewijzigde analyse-invoer: {run/name}')
        copy(pointer)
        for p in run.rglob('*'):
            if p.is_file() and 'data' not in p.relative_to(run).parts:files.add(p)
        files.update(p for p in (pointer.parent/'corrections').rglob('*') if p.is_file())
    for name in ['index.html','analyses/index.html','analyses/index.json']:
        if (root/name).exists():files.add(root/name)
    for directory in ['assets','config','src']:
        files.update(p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not any(part.endswith('.egg-info') for part in p.parts))
    # Copy pages and their actually linked source data. Keep original hrefs here.
    pending=list(files);seen=set();overlay=[]
    while pending:
        source=pending.pop()
        if source in seen:continue
        seen.add(source);dest=copy(source)
        parts=source.relative_to(root).parts
        if len(parts)>4 and parts[0]=='analyses' and parts[1].isdigit() and parts[3]=='runs':
            if inventories[parts[1]].get(source.relative_to(root).as_posix())!=digest(dest):overlay.append(dest)
        if parts[0] in ('src','config'):continue
        if source.suffix not in ('.html','.md','.css'):continue
        text=dest.read_text()
        if source.suffix=='.html':
            from bs4 import BeautifulSoup
            soup=BeautifulSoup(text,'html.parser')
            urls=[n.get('href') or n.get('src') for n in soup.find_all(['a','img','script','link'])]
            urls.extend(m.group(1) for m in CSS_URL.finditer('\n'.join(n.get_text() for n in soup.find_all('style'))))
        elif source.suffix=='.md':urls=re.findall(r'\]\(([^)]+)\)',text)
        else:urls=[m.group(1) for m in CSS_URL.finditer(text)]
        for url in urls:
            if not url:continue
            target=local_target(root,source,url)
            if target is not None and target not in seen:pending.append(target)
    if overlay:
        entry=bundle(output,overlay,archives,'presentation')
        entry['tag']=settings(root)['archive_tag_prefix']+'presentation'
        registry['presentation']=entry
    write_json(output/'_storage/index.json',registry)
    return {'files':len(seen),'presentation_files':len(overlay)}


SCRIPT = re.compile(r'<script\b([^>]*)>([\s\S]*?)</script>', re.I)
STYLE = re.compile(r'<style\b([^>]*)>([\s\S]*?)</style>', re.I)
URL_ATTR = re.compile(r'\b(href|src)=("|\')([^"\']+)\2', re.I)
CSS_URL = re.compile(r'(?<![\w])url\([\s]*["\']?([^\)"\']+)["\']?[\s]*\)', re.I)


def relative(path, parent):
    return Path(os.path.relpath(path, parent)).as_posix()


def local_target(root, source, url):
    parts = urlsplit(html.unescape(url))
    if parts.scheme or parts.netloc or not parts.path:
        return None
    if parts.path.startswith('/'):
        raise ValueError(f'Absoluut webpad is niet geschikt voor project-Pages: {source}: {url}')
    return inside(root, source.parent / unquote(parts.path))


MEDIA_VIEWER = '''<!doctype html><meta charset="utf-8"><title>Grafiek</title><script>
(async()=>{try{
 const [id,params]=location.hash.slice(1).split('?'), requestedPath=new URLSearchParams(params).get('path'), index=await fetch('index.json.gz').then(async r=>{if(!r.ok)throw Error('Mediaregister ontbreekt');return JSON.parse(await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text())}), m=index[id];
 if(!m)throw Error('Grafiek ontbreekt');
 if('serviceWorker' in navigator && m.paths?.length){
  try{
   await navigator.serviceWorker.register('../media-worker.js',{scope:'../',updateViaCache:'none'});
   await navigator.serviceWorker.ready;
   if(!navigator.serviceWorker.controller)await new Promise((resolve,reject)=>{
    navigator.serviceWorker.addEventListener('controllerchange',resolve,{once:true});
    setTimeout(()=>reject(Error('worker-timeout')),8000);
   });
   const path=requestedPath&&m.paths.includes(requestedPath)?requestedPath:m.paths[0];
   location.replace(new URL('../'+path,location.href));return;
  }catch(e){/* Older browsers fall back to their native blob image viewer. */}
 }
 let blob;
 if(m.kind==='svg'){
  const r=await fetch(m.file);if(!r.ok)throw Error('Grafiek ontbreekt');
  blob=await new Response(r.body.pipeThrough(new DecompressionStream('gzip')),{headers:{'Content-Type':'image/svg+xml'}}).blob();
 }else{
  const image=await new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=reject;i.src=m.file});
  const c=document.createElement('canvas');c.width=image.naturalWidth;c.height=image.naturalHeight;c.getContext('2d').drawImage(image,0,0);
  blob=await new Promise(resolve=>c.toBlob(resolve,'image/png'));
 }
 if(!blob)throw Error('Grafiek kon niet worden geopend');
 const url=URL.createObjectURL(blob);
 // Native image viewer, same as opening the original PNG/SVG link.
 location.replace(url);
}catch(e){document.body.textContent=e.message||'Grafiek kon niet worden geopend';}})();
</script>'''

MEDIA_WORKER = '''const version='MEDIA_VERSION';let registry;
self.addEventListener('install',event=>event.waitUntil(self.skipWaiting()));
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
const base=new URL('./',self.location.href);
async function routes(){if(!registry)registry=fetch(new URL('_media/index.json.gz',base),{cache:'no-cache'}).then(async r=>JSON.parse(await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text())).then(rows=>{const map={};for(const m of Object.values(rows))for(const p of m.paths||[])map[p]=m;return map;});return registry;}
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);
 if(url.origin!==base.origin||!url.pathname.startsWith(base.pathname)||!/\\.(png|svg)$/.test(url.pathname))return;
 event.respondWith((async()=>{
  const path=decodeURIComponent(url.pathname.slice(base.pathname.length));let m=(await routes())[path];
  if(!m){registry=null;m=(await routes())[path];}
  if(!m)return fetch(event.request);
  const r=await fetch(new URL('_media/'+m.file,base));if(!r.ok)return r;
  let blob;
  if(m.kind==='svg')blob=await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).blob();
  else{const image=await createImageBitmap(await r.blob()),canvas=new OffscreenCanvas(image.width,image.height);canvas.getContext('2d').drawImage(image,0,0);blob=await canvas.convertToBlob({type:'image/png'});image.close();}
  return new Response(blob,{headers:{'Content-Type':m.kind==='svg'?'image/svg+xml':'image/png','Content-Disposition':'inline; filename="'+path.split('/').at(-1)+'"'}});
 })());
});'''

DOCUMENT_LOADER=Path(__file__).with_name('document_loader.js').read_text()


def site_html(source,root=None):
    """Read the actual page DOM, whether stored directly or losslessly packed."""
    source=Path(source);text=source.read_text()
    match=re.search(r'data-f1-document="([^"]+)"',text)
    if not match:return text
    target=(source.parent/html.unescape(match.group(1))).resolve()
    if root is not None:inside(root,target)
    data=gzip.decompress(target.read_bytes())
    if hashlib.sha256(data).hexdigest()!=target.name.split('.')[0]:
        raise ValueError(f'Paginahash wijkt af: {source}')
    return data.decode()


def pack_documents(site):
    site=Path(site);directory=site/'_documents';directory.mkdir(exist_ok=True)
    used=set();count=0
    for source in list(site.rglob('*.html')):
        if source.relative_to(site).parts[0] in ('_media','_data'):continue
        content=site_html(source,site);sha=hashlib.sha256(content.encode()).hexdigest()
        name=sha+'.html.gz';used.add(name);target=directory/name
        if not target.exists():target.write_bytes(gzip.compress(content.encode(),compresslevel=6,mtime=0))
        # A short storage bootstrap disappears before the original document executes.
        title=re.search(r'<title>([\s\S]*?)</title>',content,re.I)
        title=title.group(1) if title else 'Overtake It Away'
        shell=' data-f1-shell' if source.name=='overzicht.html' and ('dashboard-data' in content or 'archive-data' in content) else ''
        source.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title>'
                          '<style>html{background:#10141d}</style></head><body><script'+shell+' data-f1-document="'+
                          html.escape(relative(target,source.parent),quote=True)+'" src="'+
                          html.escape(relative(directory/'loader.js',source.parent),quote=True)+'?v='+hashlib.sha256(DOCUMENT_LOADER.encode()).hexdigest()[:12]+'"></script></body></html>')
        count+=1
    for p in directory.glob('*.gz'):
        if p.name not in used:p.unlink()
    (directory/'loader.js').write_text(DOCUMENT_LOADER)
    return count


def build_site(root, output, max_bytes=None, from_year=1950):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output == root or root.is_relative_to(output):
        raise ValueError('Publicatiemap mag het bronproject niet vervangen/omsluiten')
    if output.exists() and any(output.iterdir()):
        raise ValueError(f'Publicatiemap moet leeg zijn: {output}')
    materialize_data(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='f1-pages-', dir=output.parent))
    media = read_json(root / '_media/index.json') if (root / '_media/index.json').exists() else {}
    index_overrides={}
    if from_year>1950:
        # Generate the selected catalogue with the existing renderer. Never let a
        # full catalogue pull excluded years back in through link traversal.
        from .render import update_index
        with tempfile.TemporaryDirectory(prefix='f1-selected-index-') as selected_dir:
            selected=Path(selected_dir)
            for pointer,run,manifest in latest_runs(root,from_year):
                dest=selected/run.relative_to(root);dest.mkdir(parents=True)
                write_json(dest/'manifest.json',manifest);(dest/'overzicht.html').touch()
                write_json(selected/pointer.relative_to(root),read_json(pointer))
            update_index(selected)
            for name in ['index.html','analyses/index.html','analyses/index.json']:
                index_overrides[root/name]=(selected/name).read_text()
    def source_text(source):
        text=index_overrides[source] if source in index_overrides else (site_html(source,root) if source.suffix=='.html' else source.read_text())
        return with_race_notifications(text,source,root) if source.suffix=='.html' else text
    files = set()
    for pointer, run, _ in latest_runs(root, from_year):
        files.add(pointer)
        files.update(p for p in run.rglob('*') if p.is_file() and 'data' not in p.relative_to(run).parts)
        files.update(p for p in (pointer.parent / 'corrections').rglob('*') if p.is_file())
    for name in ['index.html', 'analyses/index.html', 'analyses/index.json', '_storage/index.json', '_storage/update-state.json', '_storage/season-calendar.json', 'race-updates.json']:
        if (root / name).exists(): files.add(root / name)
    for directory in ['assets', '_shared', '_media', '_documents']:
        files.update(p for p in (root / directory).rglob('*') if p.is_file() and p.name != 'index.json')
    # Presentation files are shared, so restoring a season must not reintroduce
    # thousands of unused copies. Actual links below still include any needed file.
    if (root/'assets/dashboard-core.js').exists():
        files={p for p in files if not (p.parent.name=='interactive' and p.name in ('dashboard.js','archive.js','archive.css'))}
    if (root/'assets/dashboard.css').exists():
        files={p for p in files if not (p.parent.name=='interactive' and p.name=='dashboard.css')}
    try:
        # Include original data/source files actually linked from reports, not all internal data.
        pending = list(files); seen = set()
        while pending:
            source = pending.pop()
            if source in seen: continue
            seen.add(source)
            if source.suffix not in ('.html', '.css', '.md'): continue
            text = source_text(source)
            if source.suffix == '.html':
                from bs4 import BeautifulSoup
                soup=BeautifulSoup(text, 'html.parser')
                urls=[node.get('href') or node.get('src') for node in soup.find_all(['a','img','script','link'])]
                urls=[url for url in urls if url]
                css='\n'.join(node.get_text() for node in soup.find_all('style'))
                urls += [m.group(1) for m in CSS_URL.finditer(css)]
            elif source.suffix == '.css':
                urls=[m.group(1) for m in CSS_URL.finditer(text)]
            else:
                urls=re.findall(r'\]\(([^)]+)\)', text)
            for url in urls:
                target = local_target(root, source, url)
                if target is None: continue
                if target == root/'_data/reader.js':continue
                if not target.is_file():
                    raise ValueError(f'Ontbrekende bronlink: {source.relative_to(root)} → {url}')
                if target not in files: files.add(target); pending.append(target)
        figures = {p for p in files if '/figures/' in p.as_posix() and p.suffix in ('.png', '.svg')}
        figure_refs = {}
        jobs={}
        for p in sorted(figures):
            sha = digest(p); ext = 'webp' if p.suffix == '.png' else 'svg.gz'
            name=f'{sha}.{ext}'
            jobs.setdefault(sha,(p,name))
            entry=media.setdefault(sha,{'kind':p.suffix[1:],'file':name,'name':p.name,'original_sha256':sha,'paths':[]})
            if p.relative_to(root).as_posix() not in entry.setdefault('paths',[]):entry['paths'].append(p.relative_to(root).as_posix())
            figure_refs[p] = sha
        cache=root/'storage/media-cache'; cache.mkdir(parents=True,exist_ok=True)
        def convert(job):
            p,name=job;cached=cache/name
            if not cached.exists():
                temp=cached.with_suffix(cached.suffix+'.partial')
                previous=root/'_media'/name
                if previous.is_file():
                    shutil.copyfile(previous,temp)
                elif p.suffix == '.png':
                    with Image.open(p) as image:
                        image.save(temp, format='WEBP', lossless=True, method=4, exact=True)
                        with Image.open(temp) as decoded:
                            if decoded.convert('RGBA').tobytes() != image.convert('RGBA').tobytes():
                                raise ValueError(f'Verliesloze beeldcontrole mislukt: {p}')
                else:
                    temp.write_bytes(gzip.compress(p.read_bytes(), compresslevel=9, mtime=0))
                os.replace(temp,cached)
            if p.suffix=='.png':
                with Image.open(p) as original,Image.open(cached) as decoded:
                    if original.convert('RGBA').tobytes()!=decoded.convert('RGBA').tobytes():
                        raise ValueError(f'Verliesloze cachecontrole mislukt: {p}')
            dest=staging/'_media'/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(cached,dest)
        print(f'Verliesloze publicatie van {len(figures)} grafieken ({len(jobs)} unieke bestanden)',flush=True)
        with ThreadPoolExecutor(max_workers=4) as executor:
            for i,_ in enumerate(executor.map(convert,jobs.values()),1):
                if i%500==0:print(f'Grafieken: {i}/{len(jobs)}',flush=True)
        def shared(body, ext, source):
            sha = hashlib.sha256(body.encode()).hexdigest()
            path = staging / '_shared' / f'{sha}.{ext}'; path.parent.mkdir(exist_ok=True)
            if not path.exists(): path.write_text(body)
            return relative(path, (staging / source.relative_to(root)).parent)
        for source in sorted(files - figures):
            dest = staging / source.relative_to(root); dest.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix == '.html' and '_media' not in source.relative_to(root).parts:
                text = source_text(source)
                def script(m):
                    attrs, body = m.groups()
                    if re.search(r'\bsrc\s*=', attrs, re.I) or re.search(r'type\s*=\s*["\']application/json', attrs, re.I): return m.group(0)
                    if not body.strip(): return m.group(0)
                    return f'<script{attrs} src="{shared(body, "js", source)}"></script>'
                def style(m):
                    attrs, body = m.groups()
                    # Keep relative image URLs and style-element IDs untouched.
                    # Image URLs supplied through custom properties also resolve
                    # against this stylesheet, even when url() lives on the element.
                    variable_image = re.search(r'(?:background(?:-image)?|mask(?:-image)?)\s*:[^;{}]*var\(', body, re.I)
                    if attrs.strip() or 'url(' in body or '@import' in body or variable_image: return m.group(0)
                    return f'<link rel="stylesheet" href="{shared(body, "css", source)}">'
                text = SCRIPT.sub(script, text); text = STYLE.sub(style, text)
                def link(m):
                    attr, quote, url = m.groups(); target = local_target(root, source, url)
                    if target not in figure_refs: return m.group(0)
                    sha = figure_refs[target]
                    if attr.lower() == 'src' and target.suffix == '.png':
                        link = relative(staging / '_media' / media[sha]['file'], dest.parent)
                    else:
                        link = relative(staging / '_media/view.html', dest.parent) + '#' + sha+'?path='+url_quote(target.relative_to(root).as_posix(),safe='')
                    return f'{attr}={quote}{link}{quote}'
                text = URL_ATTR.sub(link, text)
                dest.write_text(text)
            elif source.suffix == '.md':
                def mdlink(m):
                    target = local_target(root, source, m.group(1))
                    if target not in figure_refs: return m.group(0)
                    return '](' + relative(staging / '_media/view.html', dest.parent) + '#' + figure_refs[target]+'?path='+url_quote(target.relative_to(root).as_posix(),safe='') + ')'
                dest.write_text(re.sub(r'\]\(([^)]+)\)', mdlink, source.read_text()))
            elif source.suffix == '.json':
                data=json.loads(source_text(source))
                if source.name=='manifest.json':
                    data['publication']={'originals':'verified-season-archive-with-optional-presentation-overlay','archive_registry':relative(staging/'_storage/index.json',dest.parent),
                                         'hash_scope':'file_hashes refer to the original archived files; published HTML/JSON may be repackaged and PNG is losslessly re-encoded'}
                if source.name=='manifest.json':
                    dest.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False))
                elif source in index_overrides:dest.write_text(source_text(source))
                else:dest.write_bytes(source.read_bytes())
            else: shutil.copyfile(source, dest)
        (staging / '_media').mkdir(exist_ok=True)
        used=set()
        for p in staging.rglob('*'):
            if p.is_file() and p.suffix in ('.html','.md','.css'):
                used.update(re.findall(r'\b[a-f0-9]{64}\b',p.read_text()))
        media={sha:entry for sha,entry in media.items() if sha in used}
        allowed={entry['file'] for entry in media.values()}
        for p in (staging/'_media').iterdir():
            if p.is_file() and p.name not in allowed:p.unlink()
        for p in (staging/'_shared').glob('*'):
            if p.stem not in used:p.unlink()
        for entry in media.values():entry['stored_sha256']=digest(staging/'_media'/entry['file'])
        (staging/'_media/index.json').write_text(json.dumps(media,ensure_ascii=False,separators=(',',':')))
        (staging/'_media/index.json.gz').write_bytes(gzip.compress((staging/'_media/index.json').read_bytes(),compresslevel=6,mtime=0))
        (staging / '_media/view.html').write_text(MEDIA_VIEWER)
        (staging / 'media-worker.js').write_text(MEDIA_WORKER.replace('MEDIA_VERSION',digest(staging/'_media/index.json')))
        (staging / '.nojekyll').touch()
        data_report=pack_data(staging)
        pack_documents(staging)
        report = verify_site(staging)
        report['data_compression']=data_report
        base_bytes=report['bytes']
        for _ in range(10):
            total=base_bytes+len(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False).encode())
            if total==report['bytes']:break
            report['bytes']=total
        limit = max_bytes if max_bytes is not None else settings(root)['max_site_bytes']
        if report['bytes'] > limit:
            raise ValueError(f'Website {report["bytes"]} bytes overschrijdt budget {limit}')
        write_json(staging / '_storage/site-report.json', report)
        if output.exists(): output.rmdir()
        os.replace(staging, output)
        return report
    finally:
        if staging.exists(): shutil.rmtree(staging)


def verify_site(root):
    root = Path(root).resolve(); checked = 0
    from bs4 import BeautifulSoup
    for source in root.rglob('*.html'):
        soup = BeautifulSoup(site_html(source,root), 'html.parser')
        for node in soup.find_all(['a', 'img', 'script', 'link']):
            url = node.get('href') or node.get('src')
            if not url: continue
            target = local_target(root, source, url)
            if target is not None:
                packed=target.with_name(target.name+'.gz')
                if not target.is_file() and not (target.suffix in ('.json','.csv') and packed.is_file()):
                    raise ValueError(f'Publicatielink ontbreekt: {source} → {url}')
                checked += 1
    for source in root.rglob('*.css'):
        for m in CSS_URL.finditer(source.read_text()):
            target = local_target(root, source, m.group(1))
            if target is not None and not target.is_file(): raise ValueError(f'CSS-bron ontbreekt: {source} → {m.group(1)}')
    media = read_json(root / '_media/index.json')
    verify_data(root)
    for sha, entry in media.items():
        target = inside(root, root / '_media' / entry['file'])
        if not target.is_file(): raise ValueError(f'Media ontbreken: {sha}')
        if entry.get('stored_sha256') and digest(target)!=entry['stored_sha256']:raise ValueError(f'Mediahash wijkt af: {sha}')
        if entry['kind'] == 'svg' and hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest() != sha:
            raise ValueError(f'SVG-hash wijkt af: {sha}')
    return {'bytes': sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),
            'races': len(list((root / 'analyses').glob('*/*/latest.json'))), 'checked_links': checked, 'media': len(media)}


def with_primary_race_facts(text):
    """Refresh missing race facts from the same complete data as the selections."""
    from .highlights import facts
    pattern=re.compile(r'(<script\b[^>]*\bid=["\']dashboard-data["\'][^>]*>)(.*?)(</script>)',re.S|re.I)
    def replace(match):
        payload=json.loads(match[2])
        if payload.get('historical'):return match[0]
        existing=payload.get('highlights',{})
        if all(existing.get(k) for k in ('winner','pole','fastest','gainers')):return match[0]
        drivers=payload.get('drivers',[]);styles=payload.get('styles',{})
        data={'drivers':[{'driver_number':d['driver_number'],'full_name':d.get('name'),'name_acronym':d.get('code'),
                          'team_colour':styles.get(str(d['driver_number']),{}).get('color','')} for d in drivers],
              'session_result':[dict(d.get('result',{}),driver_number=d['driver_number']) for d in drivers if d.get('result')],
              'starting_grid':[{'driver_number':d['driver_number'],'position':d.get('grid')} for d in drivers],
              'laps':[{'driver_number':l['driver'],'lap_number':l['lap'],'lap_duration':l.get('duration'),
                       'is_deleted':any('deleted' in str(r).lower() or 'verwijderd' in str(r).lower() for r in l.get('reasons',[]))} for l in payload.get('all_laps',[])]}
        primary=facts(data)
        payload['highlights']={**primary,**existing}
        if payload['highlights']==existing:return match[0]
        return match[1]+json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')+match[3]
    return pattern.sub(replace,text)


def with_dashboard_components(text, source, root):
    # Stored dashboards keep their original race inputs. Shared presentation
    # components also apply fixes when an older season archive is restored.
    if 'dashboard-data' in text:
        normalized=Path(source).parent/'data/normalized/input.json'
        if normalized.exists():
            from .race_explorer import playback_data
            replay=playback_data(read_json(normalized))
            if replay:
                def add_replay(match):
                    payload=json.loads(match[2])
                    if payload.get('historical'):return match[0]
                    payload.setdefault('explorer',{})['playback']=replay
                    return match[1]+json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')+match[3]
                text=re.sub(r'(<script\b[^>]*\bid=[\"\']dashboard-data[\"\'][^>]*>)(.*?)(</script>)',add_replay,text,flags=re.S)
        css_asset=Path(root)/'assets/dashboard.css'
        if css_asset.exists():
            css_src=relative(css_asset,Path(source).parent)
            text=text.replace('href="interactive/dashboard.css"',f'href="{css_src}"')
        core_asset=Path(root)/'assets/dashboard-core.js'
        if core_asset.exists():
            core_src=relative(core_asset,Path(source).parent)
            text=re.sub(r'<script\b[^>]*\bsrc=["\'][^"\']*interactive/dashboard\.js["\'][^>]*>\s*</script>',
                        lambda _: f'<script data-dashboard-core src="{core_src}"></script>',text)
        explorer_asset=Path(root)/'assets/race-explorer.js'
        if explorer_asset.exists():
            explorer_src=relative(explorer_asset,Path(source).parent)+'?v='+hashlib.sha256(explorer_asset.read_bytes()).hexdigest()[:12]
            text=re.sub(r'<script\b(?=[^>]*\bdata-race-explorer\b)[^>]*>[\s\S]*?</script>',
                        lambda _: f'<script data-race-explorer src="{explorer_src}"></script>',text)
        for name,attribute in [('circuit-map','data-circuit-map'),('strategy-popup','data-strategy-popup'),('overtake-popup','data-overtake-popup')]:
            asset=Path(root)/f'assets/{name}.js'
            if asset.exists() and attribute not in text:
                src=relative(asset,Path(source).parent)
                text=text.replace('</body>',f'<script defer {attribute} src="{src}"></script></body>',1)
    return text


def with_race_notifications(text, source, root):
    """Install shared presentation fixes and visitor notifications on every page."""
    from .branding import with_original_wordmark, with_hero_flag
    from .historical_dashboard import modernize
    text=modernize(text,source,root)
    # Older packed catalogues must use the same initial season as new builds.
    if 'catalogue-data' in text:
        text=text.replace("let year=+store.get('catalogue-year')||years[0]", "let year=new Date().getFullYear()")
        catalogue_asset=Path(root)/'assets/catalogue.js'
        if catalogue_asset.exists():
            def catalogue_script(match):
                src=re.search(r'\bsrc=["\']([^"\']+)["\']',match[1])
                target=local_target(root,source,src[1]) if src else None
                code=target.read_text() if target and target.is_file() else match[2]
                if 'compileRaceSearch' in code and 'catalogue-data' in code:
                    return '<script data-catalogue src="'+relative(catalogue_asset,Path(source).parent)+'"></script>'
                return match[0]
            text=re.sub(r'<script\b([^>]*)>(.*?)</script>',catalogue_script,text,flags=re.S)
    if 'data-f1-reader' not in text:
        src=relative(Path(root)/'_data/reader.js',Path(source).parent)
        script=f'<script data-f1-reader src="{src}"></script>'
        text=text.replace('</head>',script+'</head>',1) if '</head>' in text else script+text
    text=with_original_wordmark(text)
    text=with_hero_flag(text,source,root)
    from .race_navigation import refresh_navigation
    text=refresh_navigation(text,source,root)
    text=with_primary_race_facts(text)
    text=with_dashboard_components(text,source,root)
    if "'Eerste stop':'First stop'" not in text:
        text=text.replace('const exact={',"const exact={'Eerste stop':'First stop','Tweede stop':'Second stop','Beoordeling':'Assessment',",1)

    if "['Eerste stop','First stop']" not in text:
        text=text.replace('const phrases=[',"const phrases=[['Eerste stop','First stop'],['Tweede stop','Second stop'],['Beoordeling','Assessment'],",1)
    position_asset=Path(root)/'assets/race-navigation-position.js'
    init_asset=Path(root)/'assets/race-navigation-init.js'
    if init_asset.exists() and 'race-navigation' in text:
        init_src=relative(init_asset,Path(source).parent)
        text=re.sub(r'<script\b(?=[^>]*\bdata-race-navigation\b)[^>]*>[\s\S]*?</script>',
                    lambda _: f'<script defer data-race-navigation src="{init_src}"></script>',text)
    if position_asset.exists() and 'data-navigation-position' not in text and 'race-navigation' in text:
        position_src=os.path.relpath(position_asset,Path(source).parent).replace(os.sep,'/')
        text=text.replace('</body>',f'<script defer data-navigation-position src="{position_src}"></script></body>',1)
    overtake_asset=Path(root)/'assets/overtake-popup.js'
    if overtake_asset.exists() and 'data-overtake-popup' not in text and 'dashboard-data' in text:
        overtake_src=os.path.relpath(overtake_asset,Path(source).parent).replace(os.sep,'/')
        text=text.replace('</body>',f'<script defer data-overtake-popup src="{overtake_src}"></script></body>',1)
    strategy_asset=Path(root)/'assets/strategy-popup.js'
    if strategy_asset.exists() and 'data-strategy-popup' not in text and 'dashboard-data' in text:
        strategy_src=os.path.relpath(strategy_asset,Path(source).parent).replace(os.sep,'/')
        text=text.replace('</body>',f'<script defer data-strategy-popup src="{strategy_src}"></script></body>',1)
    events_asset=Path(root)/'assets/events-selection.js'
    if events_asset.exists() and 'data-events-selection' not in text and 'id="event-search"' in text:
        events_src=os.path.relpath(events_asset,Path(source).parent).replace(os.sep,'/')
        text=text.replace('</body>',f'<script defer data-events-selection src="{events_src}"></script></body>',1)
    asset=Path(root)/'assets/race-updates.js'
    if asset.is_file() and 'data-race-updates' not in text:
        href=relative(asset,Path(source).parent)
        script='<script defer data-race-updates src="'+href+'"></script>'
        text=text.replace('</body>',script+'</body>') if '</body>' in text else text+script
    positions_asset=Path(root)/'assets/positions-gained.js'
    if positions_asset.exists() and 'data-positions-gained' not in text and 'dashboard-data' in text:
        positions_src=os.path.relpath(positions_asset,Path(source).parent).replace(os.sep,'/')+'?v='+hashlib.sha256(positions_asset.read_bytes()).hexdigest()[:12]
        text=text.replace('</body>',f'<script defer data-positions-gained src="{positions_src}"></script></body>',1)
    history_asset=Path(root)/'assets/historical-data.js'
    if history_asset.exists() and 'data-historical-data' not in text and 'archive-data' in text and 'historical_supplement' in text:
        history_src=os.path.relpath(history_asset,Path(source).parent).replace(os.sep,'/')
        text=text.replace('</body>',f'<script defer data-historical-data src="{history_src}"></script></body>',1)
    if positions_asset.exists():
        positions_version=hashlib.sha256(positions_asset.read_bytes()).hexdigest()[:12]
        text=re.sub(r'(?<=src=")([^"?]*assets/positions-gained\.js)(?:\?[^" ]*)?(?=")',
                    lambda m:m[1]+'?v='+positions_version,text)
    for name in ('dashboard.css','dashboard-core.js','historical-dashboard.js','strategy-popup.js'):
        asset=Path(root)/'assets'/name
        if not asset.exists():continue
        version=hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        text=re.sub(r'((?:href|src)=["\'])([^"\'?]*assets/'+re.escape(name)+r')(?:\?[^"\']*)?(["\'])',
                    lambda m:m[1]+m[2]+'?v='+version+m[3],text)
    return text


def compare_pages(root, site):
    """Prove that packaging preserved visible text, controls, executable code and data."""
    from bs4 import BeautifulSoup
    root,site=Path(root).resolve(),Path(site).resolve();pages=payloads=0
    if not (site/'index.html').is_file():raise ValueError('Publicatie ontbreekt: '+str(site))
    def code(soup,parent):
        result=[]
        for node in soup.find_all('script'):
            src=node.get('src')
            if src:
                if urlsplit(src).scheme:result.append(('external',src));continue
                target=(parent/unquote(urlsplit(src).path)).resolve()
                text=Path(__file__).with_name('data_reader.js').read_text() if node.has_attr('data-f1-reader') else target.read_text()
            else:text=node.string or ''
            result.append((node.get('type',''),text))
        return result
    def css(soup,parent):
        result=[]
        for node in soup.find_all(['style','link']):
            if node.name=='style':result.append(node.string or '')
            elif 'stylesheet' in node.get('rel',[]):
                href=node['href']
                result.append(href if urlsplit(href).scheme else (parent/unquote(urlsplit(href).path)).resolve().read_text())
        return result
    for published in site.rglob('*.html'):
        relative_path=published.relative_to(site)
        if relative_path.parts[0] in ('_media','_data'):continue
        original=root/relative_path
        if not original.is_file():raise ValueError(f'Geen oorspronkelijke pagina: {relative_path}')
        a=BeautifulSoup(with_race_notifications(site_html(original,root),original,root),'html.parser');b=BeautifulSoup(site_html(published,site),'html.parser')
        if a.get_text()!=b.get_text():raise ValueError(f'Zichtbare tekst gewijzigd: {relative_path}')
        controls=lambda soup:[(n.name,dict(n.attrs),n.get_text()) for n in soup.find_all(['input','button','select','option','dialog'])]
        if controls(a)!=controls(b):raise ValueError(f'Bediening gewijzigd: {relative_path}')
        if code(a,original.parent)!=code(b,published.parent):raise ValueError(f'Code/data gewijzigd: {relative_path}')
        if css(a,original.parent)!=css(b,published.parent):raise ValueError(f'Stijl gewijzigd: {relative_path}')
        payloads+=len(a.find_all('script',type='application/json'));pages+=1
    return {'pages':pages,'payloads':payloads,'visible_text':'identical','controls':'identical','scripts_and_data':'identical','styles':'identical'}


def cleanup(root, directory, apply=False, cache_days=21):
    """Remove only archived heavy run data; never dashboards, figures or latest pointers."""
    from datetime import datetime, timezone
    root, directory = Path(root).resolve(), Path(directory).resolve()
    registry = read_json(root / '_storage/index.json'); candidates = []; inventory = {}
    published_data=verify_data(root)
    for entry in [*registry['seasons'].values(),*([registry['sources']] if registry.get('sources') else [])]:
        if not (directory/entry['asset']).is_file():continue
        meta = verify_bundle(directory / entry['asset'], entry['sha256'])
        inventory.update(meta['files'])
    for _, run, _ in latest_runs(root):
        linked=set()
        for q in run.rglob('*.html'):
            # Downloaded source HTML is evidence, not a generated site page.
            if 'data' in q.relative_to(run).parts:continue
            from bs4 import BeautifulSoup
            soup=BeautifulSoup(site_html(q,root),'html.parser')
            for node in soup.find_all(['a','img','script','link']):
                url=node.get('href') or node.get('src')
                if url:
                    target=local_target(root,q,url)
                    if target is not None:linked.add(target)
        for sub in ['data/raw', 'data/normalized', 'data/derived']:
            for p in (run / sub).rglob('*'):
                if not p.is_file(): continue
                if p.resolve() in linked:continue
                name = p.relative_to(root).as_posix()
                if name.endswith('.gz') and name[:-3] in published_data:continue
                if inventory.get(name) != digest(p): raise ValueError(f'Geen gelijk archief voor {p}')
                # Linked source data must remain readable locally.
                candidates.append(p)
    cutoff = datetime.now(timezone.utc).timestamp() - cache_days * 86400
    for p in (root / 'cache').glob('*.body'):
        if p.stat().st_mtime < cutoff and inventory.get(p.relative_to(root).as_posix())==digest(p):
            # Cache is disposable; archived raw sources preserve the actual analysis inputs.
            candidates.append(p)
            metadata = p.with_suffix('.meta.json')
            if metadata.exists(): candidates.append(metadata)
    report = {'files': len(candidates), 'bytes': sum(p.stat().st_size for p in candidates), 'applied': apply}
    if apply:
        for p in candidates: p.unlink()
    return report


def main():
    parser = argparse.ArgumentParser(description='GitHub-publicatie en veilige seizoenopslag')
    parser.add_argument('--root', default='.')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('archive'); p.add_argument('--directory', default='storage/archives'); p.add_argument('--years', nargs='+', type=int)
    p = sub.add_parser('freeze'); p.add_argument('--output',default='storage/frozen-source'); p.add_argument('--directory',default='storage/archives')
    p = sub.add_parser('build'); p.add_argument('--output', default='dist/pages'); p.add_argument('--from-year', type=int)
    p = sub.add_parser('verify'); p.add_argument('--site', default='dist/pages')
    p = sub.add_parser('compare'); p.add_argument('--site',default='dist/pages')
    p = sub.add_parser('restore'); p.add_argument('bundle'); p.add_argument('--sha256'); p.add_argument('--overwrite', action='store_true')
    p = sub.add_parser('cleanup'); p.add_argument('--directory', default='storage/archives'); p.add_argument('--apply', action='store_true')
    args = parser.parse_args(); root = Path(args.root).resolve()
    if args.command == 'archive': result = archive_seasons(root, root / args.directory, from_year=settings(root).get('from_year',1950), years=args.years)
    elif args.command == 'freeze': result=freeze_website(root,root/args.output,root/args.directory)
    elif args.command == 'build': result = build_site(root, root / args.output, from_year=args.from_year if args.from_year is not None else settings(root).get('from_year',1950))
    elif args.command == 'verify': result = verify_site(root / args.site)
    elif args.command == 'compare': result=compare_pages(root,root/args.site)
    elif args.command == 'restore': result = restore_bundle(args.bundle, root, args.sha256, args.overwrite)
    else: result = cleanup(root, root / args.directory, args.apply, settings(root)['cache_retention_days'])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
