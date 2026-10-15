"""Refresh current local pages only; preserve all embedded data and input files."""
from pathlib import Path
import hashlib
import json
import os
import re
from f1_analysis.io import utcnow,write_json
from f1_analysis.site_navigation import ensure_assets,with_navigation
from f1_analysis.homepage import build as build_homepage

root=Path(__file__).resolve().parents[1]
ensure_assets(root)
build_homepage(root)
pattern=re.compile(r'<script\b[^>]*\btype=["\']application/json["\'][^>]*>(.*?)</script>',re.S)
sha=lambda text:hashlib.sha256(text.encode()).hexdigest()
pages=[root/name for name in ['index.html','races.html','goat.html','analysis-lab.html','analyses/index.html','stijlgids.html'] if (root/name).is_file()]
pages.extend(pointer.parent/json.loads(pointer.read_text())['run']/'overzicht.html' for pointer in sorted((root/'analyses').glob('[0-9][0-9][0-9][0-9]/*/latest.json')))
report={'updated_at':utcnow(),'menu':['Home','Races','Drivers','Greatest','About me','EN/NL'],'pages':[],'unchanged_embedded_data':True}
for path in pages:
    if not path.exists():raise ValueError(f'Missing current page: {path}')
    before=path.read_text();prefix=os.path.relpath(root/'assets',path.parent).replace(os.sep,'/')+'/'
    after=with_navigation(before,prefix,(root/'analysis-lab.html').exists())
    if pattern.findall(before)!=pattern.findall(after):raise ValueError(f'Embedded data changed: {path}')
    changed=before!=after
    if changed:
        path.write_text(after)
        manifest=path.parent/'manifest.json'
        if manifest.exists() and path.name=='overzicht.html':
            meta=json.loads(manifest.read_text())
            meta.setdefault('presentation_history',[]).append({'updated_at':report['updated_at'],'change':'Unified six-button header and shared style-guide palette; embedded race data unchanged','previous_hashes':{'overzicht.html':sha(before)}})
            meta.setdefault('file_hashes',{})['overzicht.html']=sha(after)
            write_json(manifest,meta)
    report['pages'].append({'path':path.relative_to(root).as_posix(),'changed':changed,'embedded_json_sha256':[sha(s) for s in pattern.findall(after)]})
destination=root/'storage/site-style-20261015';destination.mkdir(parents=True,exist_ok=True)
write_json(destination/'refresh.json',report)
print(json.dumps({'pages':len(pages),'changed':sum(p['changed'] for p in report['pages']),'embedded_data':'unchanged','report':str(destination/'refresh.json')},indent=2))
