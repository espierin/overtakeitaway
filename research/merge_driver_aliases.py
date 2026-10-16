"""Apply explicit driver aliases to retained profiles without rebuilding timing."""
from pathlib import Path
import hashlib,json,re
from f1_analysis.driver_identity import merge_profiles

root=Path(__file__).resolve().parents[1]
page=root/'analysis-lab.html';text=page.read_text()
match=re.search(r'<script[^>]*id="phase2-data"[^>]*>(.*?)</script>',text,re.S)
data=json.loads(match[1]);before_drivers=len(data['drivers']);before_rows=sum(len(p['races']) for p in data['drivers']);before_cycles=len(data['cycles'])
backup=root/'storage/driver-aliases-20261016';backup.mkdir(parents=True,exist_ok=True)
if not (backup/'data-before.json').exists():(backup/'data-before.json').write_text(match[1])
merge_profiles(data)
after_rows=sum(len(p['races']) for p in data['drivers'])
assert after_rows==before_rows,'This migration must not drop any retained race observations'
assert len(data['cycles'])==before_cycles
encoded=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('</','<\\/')
text=text[:match.start(1)]+encoded+text[match.end(1):]
asset='phase2.js';sha=hashlib.sha256((root/'assets'/asset).read_bytes()).hexdigest()[:12]
text=re.sub(r'assets/'+re.escape(asset)+r'(?:\?v=[^"\'<> ]*)?','assets/'+asset+'?v='+sha,text)
page.write_text(text)
zhou=next(p for p in data['drivers'] if p['id']=='guanyu-zhou')
report={'drivers_before':before_drivers,'drivers_after':len(data['drivers']),'observations_before':before_rows,'observations_after':after_rows,'cycles_preserved':before_cycles,'merged_name':zhou['name'],'merged_races':len(zhou['races']),'period':[min(r['year'] for r in zhou['races']),max(r['year'] for r in zhou['races'])]}
(backup/'migration.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
