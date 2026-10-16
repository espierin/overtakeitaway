"""GitHub Release transport. Only invoked explicitly or inside Actions, never on import."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import time

import requests

from .io import read_json, write_json
from .publication import bundle, digest, restore_bundle, settings, verify_bundle, storage_entries, restore_presentation


class Releases:
    def __init__(self, repository):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository or ''):
            raise ValueError('Geef --repository EIGENAAR/REPOSITORY op')
        self.repository = repository
        self.api = f'https://api.github.com/repos/{repository}'
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if token: self.session.headers['Authorization'] = 'Bearer ' + token

    def call(self, method, url, **kwargs):
        body=kwargs.get('data')
        position=body.tell() if hasattr(body,'tell') else None
        for attempt in range(5):
            if position is not None:body.seek(position)
            response = self.session.request(method, url, timeout=(20, 300), **kwargs)
            if response.status_code in (429, 500, 502, 503, 504) or (response.status_code == 403 and response.headers.get('Retry-After')):
                if attempt == 4: response.raise_for_status()
                time.sleep(min(60, int(response.headers.get('Retry-After', 2 ** (attempt + 2)))))
                continue
            response.raise_for_status()
            return response
        raise ValueError('GitHub-aanvraag niet geslaagd')

    def release(self, tag, create=False):
        response = self.session.get(self.api + '/releases/tags/' + tag, timeout=60)
        if response.status_code == 404:
            if not create: return None
            return self.call('POST', self.api + '/releases', json={'tag_name': tag, 'name': tag,
                'body': 'Gecontroleerde opslag voor Formula 1 Statistics.', 'make_latest': 'false'}).json()
        response.raise_for_status(); return response.json()

    def assets(self, release):
        results = []; page = 1
        while True:
            rows = self.call('GET', self.api + f'/releases/{release["id"]}/assets', params={'per_page': 100, 'page': page}).json()
            results.extend(rows)
            if len(rows) < 100: return results
            page += 1

    def download(self, asset, target, expected=None):
        target = Path(target); target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and expected and digest(target) == expected: return target
        temp = target.with_suffix(target.suffix + '.partial')
        try:
            response = self.call('GET', asset['url'], headers={'Accept': 'application/octet-stream'}, stream=True)
            with temp.open('wb') as f:
                for chunk in response.iter_content(1024 * 1024): f.write(chunk)
            if expected and digest(temp) != expected: raise ValueError(f'Downloadhash wijkt af: {asset["name"]}')
            os.replace(temp, target)
            return target
        finally: temp.unlink(missing_ok=True)

    def upload(self, tag, path):
        path = Path(path); sha = digest(path); release = self.release(tag, create=True)
        existing = next((a for a in self.assets(release) if a['name'] == path.name), None)
        if existing:
            if existing.get('state') == 'starter':
                self.call('DELETE', existing['url'])
                existing=None
        if existing:
            if existing.get('digest') != 'sha256:' + sha:
                raise ValueError(f'Bestaand releasebestand heeft andere/ontbrekende hash: {path.name}')
            return existing
        with path.open('rb') as f:
            asset = self.call('POST', release['upload_url'].split('{')[0], params={'name': path.name},
                 data=f, headers={'Content-Type': 'application/octet-stream', 'Content-Length': str(path.stat().st_size)}).json()
        if asset.get('digest') != 'sha256:' + sha: raise ValueError(f'GitHub-opslaghash wijkt af: {path.name}')
        # Stay comfortably below secondary content-creation rate limits.
        time.sleep(2)
        return asset

    def delete(self,asset):
        self.call('DELETE',asset['url'])
        time.sleep(2)


def load_state(root, github, compact=False):
    root = Path(root); release = github.release(settings(root)['snapshot_tag'])
    if release is None: raise ValueError('Nog geen bootstrap-opslag. Voer eerst github_storage bootstrap uit.')
    assets = github.assets(release)
    descriptors = sorted((a for a in assets if a['name'].startswith('state-') and a['name'].endswith('.json')), key=lambda a: a['id'])
    if not descriptors: raise ValueError('Geen complete publicatiestatus beschikbaar')
    pointer = github.download(descriptors[-1], root / 'storage/downloads' / descriptors[-1]['name'])
    state = read_json(pointer)
    asset = next(a for a in assets if a['name'] == state['asset'])
    package = github.download(asset, root / 'storage/downloads' / asset['name'], state['sha256'])
    restore_bundle(package, root, state['sha256'], overwrite=True)
    if not compact:
        from .data_storage import materialize_data
        materialize_data(root)
    if 'update_state' in state:write_json(root/'_storage/update-state.json',state['update_state'])
    return state


def restore_years(root, github, years):
    root = Path(root); registry = read_json(root / '_storage/index.json')
    years=list(years)
    if not years:return
    correction_dirs=[p.parent/'corrections' for year in years for p in (root/'analyses'/str(year)).glob('*/latest.json')]
    corrections={p:p.read_bytes() for year in years for p in (root/'analyses'/str(year)).glob('*/corrections/**/*') if p.is_file()}
    entries = [registry['seasons'][str(year)] for year in years if str(year) in registry['seasons']]
    if registry.get('sources'): entries.append(registry['sources'])
    entries.extend(registry.get('source_supplements',[]))
    if registry.get('presentation'): entries.append(registry['presentation'])
    for entry in entries:
        release = github.release(entry['tag'])
        if release is None: raise ValueError(f'Archiefrelease ontbreekt: {entry["tag"]}')
        asset = next((a for a in github.assets(release) if a['name'] == entry['asset']), None)
        if asset is None: raise ValueError(f'Archief ontbreekt: {entry["asset"]}')
        local = github.download(asset, root / 'storage/archives' / entry['asset'], entry['sha256'])
        if entry is registry.get('presentation'):
            restore_presentation(local,root,entry['sha256'],entry.get('covered_years',[]),selected_years=years)
        else:
            restore_bundle(local, root, entry['sha256'], overwrite=True)

    for directory in correction_dirs:
        for path in directory.rglob('*'):
            if path.is_file() and path not in corrections:path.unlink()
    for path,data in corrections.items():
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)


def publish_state(root, github, site, archives):
    root, site, archives = Path(root), Path(site), Path(archives)
    registry = read_json(site / '_storage/index.json')
    for entry in storage_entries(registry):
        local = archives / entry['asset']
        if local.exists():
            verify_bundle(local, entry['sha256']); github.upload(entry['tag'], local)
        else:
            release = github.release(entry['tag'])
            asset = next((a for a in github.assets(release) if a['name'] == entry['asset']), None) if release else None
            if asset is None or asset.get('digest') != 'sha256:' + entry['sha256']:
                raise ValueError(f'Onbevestigd bronarchief: {entry["asset"]}')
    # Retry timestamps travel in the tiny descriptor; they do not require uploading
    # a whole new website snapshot when no race content changed.
    excluded={'_storage/update-state.json','_storage/site-report.json'}
    package = bundle(site, [p for p in site.rglob('*') if p.is_file() and p.relative_to(site).as_posix() not in excluded], root / 'storage/snapshots', 'site')
    tag = settings(root)['snapshot_tag']; github.upload(tag, root / 'storage/snapshots' / package['asset'])
    descriptor_data=dict(package)
    descriptor_data['archive_refs']=[{key:entry[key] for key in ['tag','asset','sha256']}
        for entry in storage_entries(registry)]
    if (site/'_storage/update-state.json').exists():descriptor_data['update_state']=read_json(site/'_storage/update-state.json')
    import hashlib
    state_sha=hashlib.sha256(json.dumps(descriptor_data,sort_keys=True).encode()).hexdigest()
    descriptor = root / 'storage/snapshots' / f'state-{state_sha[:24]}.json'
    write_json(descriptor, descriptor_data)
    # Descriptor is the commit point: original bundles and site already verified on GitHub.
    github.upload(tag, descriptor)
    return package


def prune(root,github):
    """Prune only managed assets, preserving current and fallback reference graphs."""
    root=Path(root);config=settings(root);tag=config['snapshot_tag']
    release=github.release(tag)
    if not release:return {'deleted':0}
    assets=github.assets(release)
    descriptors=sorted((a for a in assets if re.fullmatch(r'state-[a-f0-9]{24}\.json',a['name'])),key=lambda a:a['id'],reverse=True)
    keep_count=max(2,config.get('snapshot_versions',3))
    kept=descriptors[:keep_count]
    if not kept:return {'deleted':0,'reason':'no-complete-publication'}
    protected=set();sites=set();expected={}
    for asset in kept:
        sha=asset.get('digest','').removeprefix('sha256:')
        if not re.fullmatch(r'[a-f0-9]{64}',sha):raise ValueError('Statushash ontbreekt; opruimen geblokkeerd')
        local=github.download(asset,root/'storage/downloads'/asset['name'],sha)
        state=read_json(local)
        if 'archive_refs' not in state:return {'deleted':0,'reason':'legacy-status-without-reference-graph'}
        sites.add(state['asset'])
        protected.update((entry['tag'],entry['asset']) for entry in state['archive_refs'])
        expected.update(((entry['tag'],entry['asset']),entry['sha256']) for entry in state['archive_refs'])
    registry=read_json(root/'_storage/index.json')
    entries=storage_entries(registry)
    # Preserve the local active registry as an extra guard, even during a rollback.
    protected.update((entry['tag'],entry['asset']) for entry in entries)
    expected.update(((entry['tag'],entry['asset']),entry['sha256']) for entry in entries)
    candidates=[]
    for archive_tag in sorted({tag for tag,_ in protected}):
        archive_release=github.release(archive_tag)
        if not archive_release:raise ValueError(f'Beschermd archief ontbreekt: {archive_tag}')
        archive_assets=github.assets(archive_release)
        for protected_tag,name in protected:
            if protected_tag!=archive_tag:continue
            asset=next((a for a in archive_assets if a['name']==name),None)
            if asset is None or asset.get('digest')!='sha256:'+expected[(protected_tag,name)]:
                raise ValueError(f'Beschermd archief niet bevestigd; opruimen geblokkeerd: {name}')
        managed=sorted((a for a in archive_assets if re.fullmatch(r'(season-\d{4}|sources|presentation)-[a-f0-9]{24}\.tar\.gz',a['name'])),key=lambda a:a['id'],reverse=True)
        backups={a['name'] for a in managed[:max(2,config.get('archive_versions',2))]}
        candidates.extend(a for a in managed if a['name'] not in backups and (archive_tag,a['name']) not in protected)
    keep_states={a['name'] for a in kept}
    candidates.extend(a for a in descriptors if a['name'] not in keep_states)
    candidates.extend(a for a in assets if re.fullmatch(r'site-[a-f0-9]{24}\.tar\.gz',a['name']) and a['name'] not in sites)
    # A concurrent publisher changes the newest state id. Do not delete its assets.
    current=github.assets(release)
    newest=max((a['id'] for a in current if re.fullmatch(r'state-[a-f0-9]{24}\.json',a['name'])),default=None)
    if newest!=(descriptors[0]['id'] if descriptors else None):return {'deleted':0,'reason':'concurrent-publication'}
    for asset in candidates:github.delete(asset)
    return {'deleted':len(candidates),'kept_statuses':len(kept),'protected_archives':len(protected)}


def heartbeat(github):
    """A monthly small commit prevents scheduled public workflows going dormant."""
    path='.github/automation-heartbeat.json'
    url=github.api+'/contents/'+path
    response=github.session.get(url,timeout=60)
    old=None
    if response.status_code!=404:
        response.raise_for_status();old=response.json()
        data=json.loads(base64.b64decode(old['content']))
        then=datetime.fromisoformat(data['updated_at'])
        if then+timedelta(days=30)>datetime.now(timezone.utc):return {'changed':False}
    data=json.dumps({'updated_at':datetime.now(timezone.utc).isoformat()},indent=2)+'\n'
    body={'message':'Onderhoud: automatische raceplanning actief houden',
          'content':base64.b64encode(data.encode()).decode()}
    if old:body['sha']=old['sha']
    github.call('PUT',url,json=body)
    return {'changed':True}


def main():
    parser = argparse.ArgumentParser(description='GitHub Release-opslag voorbereiden en herstellen')
    parser.add_argument('--root', default='.')
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY'))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('load').add_argument('--compact',action='store_true')
    sub.add_parser('heartbeat')
    sub.add_parser('prune')
    p = sub.add_parser('restore-years'); p.add_argument('--years', nargs='+', type=int, required=True)
    sub.add_parser('restore-planned')
    for command in ['bootstrap', 'publish']:
        p = sub.add_parser(command); p.add_argument('--site', default='dist/pages'); p.add_argument('--archives', default='storage/archives')
    args = parser.parse_args(); root = Path(args.root).resolve(); github = Releases(args.repository)
    if args.command == 'prune':result=prune(root,github)
    elif args.command == 'heartbeat': result = heartbeat(github)
    elif args.command == 'load': result = load_state(root, github, args.compact)
    elif args.command == 'restore-years': result = restore_years(root, github, args.years)
    elif args.command == 'restore-planned':
        report = read_json(root / '_storage/update-report.json')
        result = restore_years(root, github, report.get('planned_years', []))
    else: result = publish_state(root, github, root / args.site, root / args.archives)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
