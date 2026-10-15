"""Apply explicit chart selections to retained local race pages; keep observations intact."""
from pathlib import Path
import hashlib,json,re
from f1_analysis.publication import with_dashboard_components
from f1_analysis.io import write_json,utcnow
root=Path(__file__).resolve().parents[1];report={'updated_at':utcnow(),'pages':0,'changed':0,'championship_defaults':0}
for page in sorted((root/'analyses').glob('*/*/runs/*/overzicht.html')):
    old=page.read_text()
    if 'id="dashboard-data"' not in old:continue
    before=json.loads(re.search(r'<script\b[^>]*id="dashboard-data"[^>]*>(.*?)</script>',old,re.S)[1])
    new=with_dashboard_components(old,page,root)
    for name in ['dashboard-core.js','dashboard.css','race-explorer.js','positions-gained.js']:
        asset=root/'assets'/name;version=hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        new=re.sub(r'((?:src|href)=["\'])([^"\'?]*assets/'+re.escape(name)+r')(?:\?[^"\']*)?(["\'])',lambda m:m[1]+m[2]+'?v='+version+m[3],new)
    after=json.loads(re.search(r'<script\b[^>]*id="dashboard-data"[^>]*>(.*?)</script>',new,re.S)[1])
    # Existing measured playback remains unchanged as well as all other observations.
    before.pop('championship_before',None);after.pop('championship_before',None)
    assert before==after,page
    report['pages']+=1;report['championship_defaults']+='"championship_before"' in new
    if new!=old:
        page.write_text(new);report['changed']+=1
        manifest=page.parent/'manifest.json'
        if manifest.exists():
            meta=json.loads(manifest.read_text());meta.setdefault('presentation_history',[]).append({'updated_at':report['updated_at'],'change':'Explicit chart-local replay selection, informational hover, sidebar-only start highlights, pre-race championship defaults','previous_hashes':{'overzicht.html':hashlib.sha256(old.encode()).hexdigest()}});meta.setdefault('file_hashes',{})['overzicht.html']=hashlib.sha256(new.encode()).hexdigest();write_json(manifest,meta)
work=root/'storage/race-interaction-20261015';work.mkdir(exist_ok=True,parents=True);write_json(work/'refresh.json',report);print(json.dumps(report),flush=True)
