"""Install reviewed site copy without changing embedded race data or calculations."""
from pathlib import Path
import argparse
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import json
import os
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from f1_analysis.readability import decorate,install
from f1_analysis.publication import site_html


def digest(text):return hashlib.sha256(text.encode()).hexdigest()


def data_nodes(text):
    return {m[1]:digest(m[2]) for m in re.finditer(r'<script\b[^>]*\bid=["\']([^"\']*(?:data|manifest)[^"\']*)["\'][^>]*>(.*?)</script>',text,re.S)}


def review(root=ROOT,apply=False,restore=None):
    root=Path(root).resolve();timestamp=datetime.now(timezone.utc).isoformat()
    report={'version':'plain-copy-v1','at':timestamp,'applied':apply,'changes':[], 'restored_assets':[], 'data_unchanged':True,'unpatched_language':[]}
    if apply:install(root)
    # Published static presentation is recoverable locally; never replace an existing file.
    if restore:
        restore=Path(restore)
        for directory in ['assets','_shared','_data','_media','_documents']:
            for source in (restore/directory).rglob('*'):
                if not source.is_file():continue
                target=root/source.relative_to(restore)
                if target.exists():continue
                report['restored_assets'].append(str(target.relative_to(root)))
                if apply:target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    paths={p.relative_to(root):p for p in root.glob('*.html') if 'backup' not in p.name}
    for p in (root/'analyses').rglob('*.html'):
        rel=p.relative_to(root)
        if 'data' not in rel.parts and 'sources' not in rel.parts:paths[rel]=p
    for name in ['_development/data-collection.html']:
        if (root/name).exists():paths[Path(name)]=root/name
    if restore:
        for p in (restore/'analyses').rglob('*.html'):
            rel=p.relative_to(restore)
            if 'data' not in rel.parts and 'sources' not in rel.parts:paths.setdefault(rel,p)
    manifests=defaultdict(list)
    for rel,source in sorted(paths.items()):
        text=site_html(source,root if source.is_relative_to(root) and not (restore and source.is_relative_to(restore)) else restore)
        target=root/rel
        prefix=os.path.relpath(root/'assets',target.parent).replace(os.sep,'/')+'/'
        technical=rel.name=='bronnen-en-methode.html'
        after=text if technical else decorate(text,prefix)
        assert data_nodes(text)==data_nodes(after),str(rel)
        if 'window.siteLanguage=' in after and 'window.readableCopy.lookup' not in after and not technical:report['unpatched_language'].append(str(rel))
        if after==text and source==target:continue
        record={'file':str(rel),'before_sha256':digest(text),'after_sha256':digest(after),'restored':source!=target}
        report['changes'].append(record)
        if apply:target.parent.mkdir(parents=True,exist_ok=True);target.write_text(after)
        if 'runs' in rel.parts:
            i=rel.parts.index('runs');run=root/Path(*rel.parts[:i+2]);manifests[run].append(record)
    if apply:
        for run,changes in manifests.items():
            path=run/'manifest.json'
            if not path.exists():continue
            data=json.loads(path.read_text());data.setdefault('presentation_history',[]).append({'type':'plain-language-copy','at':timestamp,'data_unchanged':True,'changes':changes})
            for c in changes:
                name=str((root/c['file']).relative_to(run));data.setdefault('file_hashes',{})[name]=c['after_sha256']
                if name not in data.setdefault('files',[]):data['files'].append(name)
            path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    report['counts']={'pages_changed':len(report['changes']),'pages_reviewed':len(paths),'restored_pages':sum(c['restored'] for c in report['changes']),'restored_assets':len(report['restored_assets'])}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--restore-presentation',type=Path);parser.add_argument('--output',type=Path,default=ROOT/'storage/readability-20261019/site-review.json');args=parser.parse_args()
    result=review(apply=args.apply,restore=args.restore_presentation);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result['counts']));print('Unpatched language controllers:',len(result['unpatched_language']))
