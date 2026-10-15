"""Race-local defaults from the last published championship table before the race."""
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import json
import re
import unicodedata


def before_reference(table):
    """Keep only the three leaders; season openers use the previous final table."""
    standings=defaultdict(list);finals=defaultdict(list)
    for row in table('races-driver-standings'):
        standings[(int(row['year']),int(row['round']))].append(row)
    for row in table('seasons-driver-standings'):
        finals[int(row['year'])].append(row)
    def top(rows):
        return [r['driverId'] for r in sorted(rows,key=lambda r:int(r['positionDisplayOrder']))[:3]]
    sprints=defaultdict(list);finishes=defaultdict(list)
    for row in table('races-sprint-race-results'):
        sprints[(int(row['year']),int(row['round']))].append(row)
    for row in table('races-race-results'):
        if row.get('positionNumber'):
            finishes[int(row['year'])].append(row)
    result={}
    for race in table('races'):
        year,round_=int(race['year']),int(race['round'])
        rows=finals.get(year-1,[]) if round_==1 else standings.get((year,round_-1),[])
        leaders=top(rows);stage='previous-season-final' if round_==1 else 'previous-grand-prix'
        if round_>1 and rows and sprints.get((year,round_)):
            # Add the current weekend's sprint before selecting Grand Prix defaults.
            points={r['driverId']:float(r['points'] or 0) for r in rows}
            order={r['driverId']:int(r['positionDisplayOrder']) for r in rows}
            for row in sprints[year,round_]:
                identity=row['driverId'];points[identity]=points.get(identity,0)+float(row.get('points') or 0)
            counts=defaultdict(lambda:[0]*40)
            for row in finishes[year]:
                if int(row['round'])<round_ and 1<=int(row['positionNumber'])<=40:
                    counts[row['driverId']][int(row['positionNumber'])-1]+=1
            leaders=sorted(points,key=lambda d:(-points[d],tuple(-n for n in counts[d]),order.get(d,999)))[:3]
            stage='after-sprint'
        result[race['date']]={'year':year,'round':round_,'source_year':year-1 if round_==1 else year,
                              'source_round':None if round_==1 else round_ if stage=='after-sprint' else round_-1,
                              'source_stage':stage,'drivers':leaders}
    return result


@lru_cache(maxsize=4)
def _reference(path,mtime):
    return json.loads(Path(path).read_text())


def reference(root):
    for path in [Path(root)/'assets/catalogue-search-reference.json',Path(__file__).parent/'assets/catalogue-search-reference.json']:
        if path.exists():return _reference(str(path.resolve()),path.stat().st_mtime_ns)
    return {}


def fold(value):
    value=unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode().casefold()
    return re.sub('[^a-z0-9]','',value)


def defaults(payload,date,root):
    ref=reference(root);record=ref.get('championship_before',{}).get(date,{})
    if record.get('year')!=int(payload.get('year') or 0):return None
    drivers=payload.get('drivers',[]);selected=[]
    for identity in record['drivers']:
        driver=ref.get('drivers',{}).get(identity,{})
        matches=[d for d in drivers if fold(d.get('name'))==fold(driver.get('name'))]
        if not matches:
            matches=[d for d in drivers if d.get('code') and d['code']==driver.get('code')]
        if len(matches)==1:selected.append(matches[0]['driver_number'])
    return {**{k:v for k,v in record.items() if k!='drivers'},'drivers':selected,'source':ref.get('source','https://github.com/f1db/f1db')}


def with_defaults(payload,date,root):
    result=defaults(payload,date,root)
    if result is None:return payload
    return {**payload,'championship_before':result}


def decorate(text,root):
    """Update presentation metadata in retained pages, keeping original observations."""
    date=re.search(r'\bdata-race-date\b[^>]*\bdatetime=["\']([^"\']+)',text)
    if not date:
        date=re.search(r'\bdatetime=["\']([^"\']+)["\'][^>]*\bdata-race-date\b',text)
    if not date:return text
    def apply(match):
        original=json.loads(match[2]);updated=with_defaults(original,date[1],root)
        if updated==original:return match[0]
        return match[1]+json.dumps(updated,ensure_ascii=False).replace('<','\\u003c')+match[3]
    return re.sub(r'(<script\b[^>]*\bid=["\']dashboard-data["\'][^>]*>)(.*?)(</script>)',apply,text,flags=re.S)
