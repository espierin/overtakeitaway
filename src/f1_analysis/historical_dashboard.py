"""Adapt retained historical observations to the same dashboard as recent races.

Rank reversals are reconstructed position changes, never confirmed track overtakes.
Pit-stop cycles require complete, consecutive measured lap times for both drivers.
"""
from collections import Counter
from itertools import combinations
import json
import math
from pathlib import Path
import re
from statistics import median

from .io import write_json, write_csv


def measured(value):
    return isinstance(value,(float,int)) and math.isfinite(value) and value>0


def historical_payload(data):
    entries=data['drivers'];numbers=Counter(d.get('number') for d in entries)
    keys={d['id']:d['number'] if d.get('number') and numbers[d['number']]==1 else -(i+1) for i,d in enumerate(entries)}
    rounds=max([1,data.get('scheduled_laps') or 0]+[l['lap'] for d in entries for l in d['laps']])
    drivers=[];positions=[];all_laps=[];styles={};timing={};pits=[];sectors=[];flags=set();neutral=set();red=set()
    for lap in data.get('timing',{}).get('laps',[]):timing[(lap['number'],lap['lap'])]=lap
    for d in entries:
        n=keys[d['id']];laps={l['lap']:l for l in d['laps']};first=laps.get(1,{}).get('position')
        drivers.append({'driver_number':n,'display_number':d.get('number'),'name':d['name'],'code':d['code'],'team':d['team'],
                        'grid':d.get('grid'),'finish':d.get('position'),'lap1_position':first,
                        'entry_id':d['id'],'classified':bool(d.get('classified')),'status':d.get('status'),
                        'net_gain':d['grid']-d['position'] if d.get('grid') and d.get('position') else None,
                        'result':{'position':d.get('position'),'number_of_laps':d.get('completed_laps'),'duration':d.get('time')}})
        styles[n]={'color':d.get('display_color') or d.get('color') or '#B3BECE','label':str(d.get('number') or '?')+' '+d['code'],'linestyle':'-'}
        if d.get('grid'):positions.append({'driver':n,'lap':0,'position':d['grid']})
        for l in sorted(laps.values(),key=lambda l:l['lap']):
            if measured(l.get('position')):positions.append({'driver':n,'lap':l['lap'],'position':l['position']})
            t=timing.get((d.get('number'),l['lap']),{})
            compound=str(t.get('compound') or 'UNKNOWN').upper()
            if compound not in ('SOFT','MEDIUM','HARD','WET','INTERMEDIATE'):compound='UNKNOWN'
            if measured(l.get('seconds')):
                all_laps.append({'driver':n,'lap':l['lap'],'duration':l['seconds'],'tyre':{'compound':compound,'age':None},'reasons':[]})
            for sector,duration in enumerate(t.get('sectors',[]),1):
                if measured(duration):sectors.append({'driver':n,'lap':l['lap'],'sector':sector,'duration':duration})
            status=str(t.get('track_status') or '')
            if '2' in status:flags.add((n,l['lap']))
            if '4' in status:neutral.add((l['lap'],'SC'))
            if '6' in status or '7' in status:neutral.add((l['lap'],'VSC'))
            if '5' in status:red.add(l['lap'])
        pits.extend({'driver':n,'lap':p['lap'],'duration':p.get('duration'),'stop':p.get('stop')} for p in d['pitstops'] if measured(p.get('lap')))
    indexed={(p['driver'],p['lap']):p['position'] for p in positions};events=[]
    pit_index={(p['driver'],p['lap']):p for p in pits}
    for lap in range(1,rounds+1):
        for a,b in combinations(drivers,2):
            na,nb=a['driver_number'],b['driver_number'];old=[indexed.get((n,lap-1)) for n in (na,nb)];new=[indexed.get((n,lap)) for n in (na,nb)]
            if not all(old+new) or (old[0]-old[1])*(new[0]-new[1])>=0:continue
            winner,other=(na,nb) if new[0]<new[1] else (nb,na)
            context=[{'driver_number':n,'lap_number':l,'source_duration':pit_index[n,l].get('duration')} for n in (na,nb) for l in (lap-1,lap) if (n,l) in pit_index]
            events.append({'event_id':f'historical-{data["year"]}-{data["round"]}-{lap}-{winner}-{other}',
                'lap':lap,'overtaker':winner,'overtaken':other,'type':'pitstopwisseling' if context else 'gereconstrueerde_positiewisseling',
                'counts':{'analytical':True,'on_track':False,'lap1':lap==1},'location':None,'location_confidence':'onbekend',
                'date':None,'pit_context':context,'reason':'Volgorde omgekeerd tussen twee opeenvolgende rondewaarnemingen; exacte oorzaak en baanlocatie niet vastgesteld.',
                'tyre_overtaker':{'compound':'UNKNOWN','age':None},'tyre_overtaken':{'compound':'UNKNOWN','age':None},
                'source_records':[{'source':'historische rondekaart','lap':lap,'position_before':old,'position_after':new}],
                'evidence':[{'source':'Bewaarde rondegegevens','url':'data/normalized/historical-supplement.json','claim':'Posities aan opeenvolgende ronde-einden'}] if data.get('historical_supplement') else []})
    expected=sum(d.get('completed_laps') or len(d['laps']) for d in entries)
    position_coverage=sum(len([l for l in d['laps'] if measured(l.get('position'))]) for d in entries)/max(1,expected)
    lap_coverage=len(all_laps)/max(1,expected)
    if not sectors and lap_coverage>=.7:
        sectors=[{'driver':l['driver'],'lap':l['lap'],'sector':1,'duration':l['duration']} for l in all_laps]
        heat_resolution='lap';sector_count=1
    else:heat_resolution='sector';sector_count=3
    groups={}
    for row in sectors:groups.setdefault((row['lap'],row['sector']),[]).append(row['duration'])
    for row in sectors:row['relative_speed']=100*(median(groups[row['lap'],row['sector']])/row['duration']-1)
    snapshot=[];frames=[]
    for d in entries:
        n=keys[d['id']];last=None;last_change=None;delta=0
        for p in sorted((p for p in positions if p['driver']==n and p['lap']>0),key=lambda p:p['lap']):
            if last is not None and last!=p['position']:delta=last-p['position'];last_change=p['lap']
            snapshot.append(dict(p,inactive=False))
            frames.append({'driver':n,'step':p['lap']*3,'position':p['position'],'inactive':False,'delta':delta if last_change==p['lap'] else 0})
            last=p['position']
        if not d.get('classified') and last is not None:
            last_lap=max((p['lap'] for p in positions if p['driver']==n),default=0)
            if last_lap<rounds:
                frames.append({'driver':n,'step':(last_lap+1)*3,'position':last,'inactive':True,'delta':0})
    highlights=json.loads(json.dumps(data.get('highlights',{})))
    for value in highlights.values():
        for item in value if isinstance(value,list) else [value]:
            if isinstance(item,dict) and str(item.get('id')) in keys:item['id']=keys[str(item['id'])]
    payload={'historical':True,'drivers':drivers,'styles':styles,'positions':positions,'all_laps':all_laps,'events':events,
             'cycles':[],'tyres':{'stints':[],'excluded_laps':[]},'track':[],'labels':[],'reference':{},'highlights':highlights,
             'laps':rounds,'late_start':False,'race':data['circuit'],'year':data['year'],'f1gures_available':False,
             'stats':{'timing_original':0,'lap_count':rounds},'warnings':data.get('warnings',[]),'sources':[],
             'timing_source':'Bewaarde historische rondekaarten',
             'historical_coverage':{'positions':position_coverage,'lap_times':lap_coverage},
             'explorer':{'resolution':'lap','heat_resolution':heat_resolution,'sector_count':sector_count,'heat_available':bool(sectors) and (lap_coverage>=.7 or len(sectors)>=expected*2),
                         'start_positions':[{'driver':p['driver'],'fraction':1,'position':p['position'],'sector':None} for p in positions if p['lap']==1],
                         'standings':snapshot,'sector_standings':frames,'pit':pits,'sectors':sectors,
                         'yellow':[{'driver':n,'lap':l,'track_sectors':[]} for n,l in sorted(flags)],
                         'neutral':[{'lap':l,'kind':k} for l,k in sorted(neutral)],'red':sorted(red)}}
    payload['cycles']=pit_cycles(payload)
    payload['historical_reference']=None
    return payload


def pit_cycles(payload):
    laps={(l['driver'],l['lap']):l for l in payload['all_laps']};elapsed={};positions={(p['driver'],p['lap']):p['position'] for p in payload['positions']}
    for d in payload['drivers']:
        n=d['driver_number'];total=0
        for lap in range(1,payload['laps']+1):
            row=laps.get((n,lap))
            if not row:break
            total+=row['duration'];elapsed[n,lap]=total
    cycles=[];seen=set();stops=payload['explorer']['pit'];neutral={r['lap'] for r in payload['explorer']['neutral']}|set(payload['explorer']['red'])
    for a,b in combinations(stops,2):
        if a['driver']==b['driver'] or not 0<abs(a['lap']-b['lap'])<=8:continue
        early,late=sorted((a,b),key=lambda p:p['lap']);n,m=early['driver'],late['driver'];lo=max(1,early['lap']-1);end=late['lap']+1
        if end>payload['laps'] or any(l in neutral for l in range(lo,end+1)):continue
        # Additional stops/restarts in the window invalidate a simple two-stop duel.
        if any(p not in (early,late) and p['driver'] in (n,m) and lo<p['lap']<=end for p in stops):continue
        if any((d,l) not in elapsed for d in (n,m) for l in range(lo,end+1)):continue
        before=[positions.get((d,lo)) for d in (n,m)];after=[positions.get((d,end)) for d in (n,m)]
        if not all(before+after) or abs(before[0]-before[1])>3 or (before[0]-before[1])*(after[0]-after[1])>=0:continue
        measured_laps=[laps[d,l]['duration'] for d in (n,m) for l in range(lo,end+1)]
        if max(measured_laps)>median(measured_laps)*2:continue
        trace=[{'lap':l,'gap':elapsed[n,l]-elapsed[m,l]} for l in range(lo,end+1)]
        if trace[0]['gap']*trace[-1]['gap']>=0:continue
        winner=n if after[0]<after[1] else m;identifier=f'history-{n}-{m}-{early["lap"]}-{late["lap"]}'
        if identifier in seen:continue
        seen.add(identifier)
        cycles.append({'cycle_id':identifier,'status':'Afgeleid','inferred':True,'order_changed':True,'beneficiary':winner,
                       'strategy':'undercutsituatie' if winner==n else 'overcutsituatie','early_driver':n,'late_driver':m,
                       'early_stop_lap':early['lap'],'late_stop_lap':late['lap'],'baseline_lap':lo,'completed_lap':end,
                       'gain_early_driver':trace[0]['gap']-trace[-1]['gap'],'trace':trace,
                       'lap_details':[{'driver':d,'lap':l,'duration':laps[d,l]['duration'],'tyre':laps[d,l]['tyre']} for d in (n,m) for l in range(lo,end+1)],
                       'attribution':'Afgeleid uit complete rondetijden en geregistreerde stops; oorzaak, verkeer en bandenvoordeel niet bevestigd.'})
    return cycles


def modernize(text,source,root):
    source=Path(source)
    if source.name!='overzicht.html':return text
    match=re.search(r'<script\b[^>]*id=["\']archive-data["\'][^>]*>(.*?)</script>',text,re.S)
    if not match:return text
    data=json.loads(match[1]);payload=historical_payload(data)
    from .historical_presentation import circuit_reference
    payload['historical_reference']=circuit_reference(root,data)
    run=source.parent
    from .dashboard import write_dashboard
    sections=[];coverage=payload['historical_coverage']['positions']
    if coverage>=.7 and payload['events']:
        sections.extend([('lapchart','Wanneer de actie plaatsvond','Gereconstrueerde positiewisselingen op basis van rondewaarnemingen; geen bevestigde inhaalregistraties.'),
                         ('driverchart','Wie zorgde voor de actie','')])
    if payload['cycles']:sections.append(('cycles','Waar strategie het verschil maakte','Afgeleide pitstopcycli op basis van gemeten rondetijden en stops. Bandenvoordeel en oorzaak zijn niet bevestigd.'))
    if coverage>=.5:sections.append(('positions','Hoe de race zich ontvouwde',''))
    first=sum(bool(d['grid'] and d['lap1_position']) for d in payload['drivers'])/max(1,len(payload['drivers']))
    if first>=.7:sections.append(('firstlap','Start en race: positiewinst',''))
    menu=[dict(d,color=payload['styles'][d['driver_number']]['color']) for d in payload['drivers']]
    # Retain the full enriched archive payload for provenance and future rebuilds.
    extra='<script id="archive-data" type="application/json">'+match[1]+'</script><script defer data-historical-dashboard src="../../../../../assets/historical-dashboard.js"></script><script defer data-historical-data src="../../../../../assets/historical-data.js"></script>'
    exports=run/'exports';write_json(exports/'historical-events.json',payload['events']);write_csv(exports/'historical-events.csv',payload['events'])
    write_json(exports/'historical-facts.json',payload['highlights']);write_csv(exports/'historical-pit-cycles.csv',payload['cycles'])
    result=write_dashboard(run,payload,data,menu,sections,extra,write=False)
    for old,new in [('gebeurtenissen','historical-events'),('kerncijfers','historical-facts'),('pitstopstrategie','historical-pit-cycles')]:result=result.replace('exports/'+old+'.','exports/'+new+'.')
    # Insufficient data removes the entire event module, not a misleading empty graph.
    if coverage<.7 or not payload['events']:
        result=re.sub(r'<details class="interactive-card" id="section-events">.*?</details>','',result,flags=re.S)
    return result
