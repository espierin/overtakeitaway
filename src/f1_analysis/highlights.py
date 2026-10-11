"""Verified race facts, separate from interactive event selection."""
from pathlib import Path
import math

def _int(v):
    try:return int(v)
    except (TypeError,ValueError):return None

def _seconds(v):
    if not v:return None
    try:
        parts=str(v).lstrip('+').split(':');total=0.
        for part in parts:total=total*60+float(part)
        return total if math.isfinite(total) else None
    except ValueError:return None

def facts(data,archive_raw=None,root=None):
    rows=[]
    if archive_raw is not None:
        for r in archive_raw['entries']:
            e=r['sessionentry'];d=r['driver']
            from .io import slug
            rows.append({'code':d.get('abbreviation') or slug(d['surname']).replace('-','')[:3].upper(),'color':'#B3BECE','id':e['id'],'number':_int(r['roundentry']['car_number']),'name':d['forename']+' '+d['surname'],'grid':_int(e['grid']),'position':_int(e['position']),'classified':e['is_classified']=='t','laps':_int(e['laps_completed']),'time':e['time'],'fastest':_int(e['fastest_lap_rank'])})
    else:
        for r in data.get('jolpica_results',[]):
            d=r['Driver'];f=r.get('FastestLap',{})
            source=next((x for x in data.get('drivers',[]) if x['driver_number']==_int(r['number'])),{})
            color=source.get('team_colour','').lstrip('#')
            rows.append({'code':source.get('name_acronym') or d.get('code') or d['familyName'][:3].upper(),'color':'#'+color if len(color)==6 else '#B3BECE','id':_int(r['number']),'number':_int(r['number']),'name':d['givenName']+' '+d['familyName'],'grid':_int(r.get('grid')),'position':_int(r.get('position')),'classified':r.get('positionText','').isdigit(),'laps':_int(r.get('laps')),'time':r.get('Time',{}).get('time'),'millis':_int(r.get('Time',{}).get('millis')),'fastest':_int(f.get('rank')),'fastest_time':f.get('Time',{}).get('time'),'fastest_lap':_int(f.get('lap'))})
    out={}
    for key,predicate in [('pole',lambda r:r['grid']==1),('winner',lambda r:r['position']==1),('fastest',lambda r:r['fastest']==1)]:
        matches=[r for r in rows if predicate(r)]
        if len(matches)==1:out[key]=matches[0]
    gains=[{**r,'gain':r['grid']-r['position']} for r in rows if r['classified'] and r['grid'] and r['grid']>0 and r['position']]
    if gains:
        best=max(r['gain'] for r in gains)
        if best>0:out['gainers']=[r for r in gains if r['gain']==best]
    winner=out.get('winner');second=next((r for r in rows if r['position']==2),None)
    if winner and second and winner['laps']==second['laps']:
        gap=None
        if winner.get('millis') is not None and second.get('millis') is not None:gap=(second['millis']-winner['millis'])/1000
        elif (second.get('time') or '').startswith('+'):gap=_seconds(second['time'])
        else:
            a=_seconds(winner['time']);b=_seconds(second['time'])
            if a is not None and b is not None:gap=b-a
        if gap is not None and gap>=0:out['margin']=gap
    if root and out.get('pole'):
        source=next((Path(root)/'analyses/sources/jolpica').glob('*.zip'),None)
        year=data.get('year',data.get('session',{}).get('year'));round_number=data.get('round')
        if not isinstance(round_number,(str,int)):round_number=data.get('session',{}).get('round')
        if source and _int(round_number):
            q=qualifying_facts(str(source)).get((int(year),int(round_number)))
            if q and q['number']==out['pole']['number']:out['pole_margin']=q['margin'];out['pole_margin_source']={'path':str(source.relative_to(root)),'session_id':q['session_id']}
    return out

def script():return '<script>'+Path(__file__).with_name('highlights.js').read_text()+'</script>'

def style():return '<style>'+Path(__file__).with_name('highlights.css').read_text()+'</style>'

from functools import lru_cache
@lru_cache(maxsize=1)
def qualifying_facts(source):
    import csv,io,zipfile
    from collections import defaultdict
    z=zipfile.ZipFile(source)
    def table(name):return list(csv.DictReader(io.TextIOWrapper(z.open('formula_one_'+name+'.csv'))))
    seasons={r['id']:int(r['year']) for r in table('season')}
    rounds={r['id']:(seasons[r['season_id']],int(r['number'])) for r in table('round') if r['number'].isdigit()}
    sessions={r['id']:r for r in table('session') if r['type'] in ['Q','Q1','Q2','Q3'] and r['is_cancelled']=='f'}
    entries={r['id']:r for r in table('sessionentry') if r['session_id'] in sessions}
    cars={r['id']:r['car_number'] for r in table('roundentry')}
    times={}
    for lap in csv.DictReader(io.TextIOWrapper(z.open('formula_one_lap.csv'))):
        if lap['session_entry_id'] in entries and lap['is_deleted']=='f':
            t=_seconds(lap['time'])
            if t is not None:times[lap['session_entry_id']]=min(t,times.get(lap['session_entry_id'],t))
    groups=defaultdict(list)
    for e in entries.values():groups[e['session_id']].append(e)
    result={};by_round=defaultdict(list)
    for sid,session in sessions.items():by_round[session['round_id']].append((sid,session))
    for rid,choices in by_round.items():
        if rid not in rounds:continue
        types={s['type'] for _,s in choices};wanted='Q3' if 'Q3' in types else 'Q' if 'Q' in types else 'Q1' if types=={'Q1'} else None
        if not wanted:continue
        candidates=[(sid,s) for sid,s in choices if s['type']==wanted]
        if len(candidates)!=1:continue
        sid,session=candidates[0];first=next((e for e in groups[sid] if e['position']=='1'),None);second=next((e for e in groups[sid] if e['position']=='2'),None)
        if first and second and first['id'] in times and second['id'] in times:
            gap=times[second['id']]-times[first['id']]
            if gap>=0:result[rounds[rid]]={'margin':gap,'number':_int(cars[first['round_entry_id']]),'session_id':sid}
    return result
