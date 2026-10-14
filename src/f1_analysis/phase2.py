"""Compact, reproducible driver profiles and observed pit-cycle comparisons.

No causal tyre effects, attempted-undercut claims, or fabricated missing data.
Only retained main-race dashboards from the latest five calendar seasons.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import html
from itertools import combinations
import json
import math
from pathlib import Path
import re
import shutil
from statistics import median
import unicodedata

SCHEMA=2
DEFINITION_VERSION='matched-teammates-v1/paired-pit-cycles-v1/driver-qualities-v1/start-distribution-v1'
MAX_EXTRA_BYTES=20_000_000
MIN_MATCHED_LAPS=6
AGE_TOLERANCE=2


def finite(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)


def identity(name):
    text=unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower()
    text=re.sub(r'\b(jnr|jr|junior)\b','',text)
    return re.sub(r'[^a-z0-9]+','-',text).strip('-')


def quantile(values, fraction):
    values=sorted(values)
    if not values:return None
    index=(len(values)-1)*fraction;lo=int(index);hi=min(lo+1,len(values)-1)
    return round(values[lo]+(values[hi]-values[lo])*(index-lo),5)


def compare_teammates(payload):
    """Equal race lap, measured equal compound, similar known age, clean laps."""
    teams=defaultdict(list)
    for d in payload.get('drivers',[]):teams[d.get('team')].append(d)
    lap_index={(r['driver'],r['lap']):r for r in payload.get('all_laps',[]) if finite(r.get('duration')) and r['duration']>0}
    pits={(p['driver'],p['lap']) for p in payload.get('explorer',{}).get('pit',[])}
    neutral={r['lap'] for r in payload.get('explorer',{}).get('neutral',[])}|set(payload.get('explorer',{}).get('red',[]))
    neutral.update(r['lap'] for r in payload.get('all_laps',[]) if any('neutral' in str(reason).lower() or 'vlag' in str(reason).lower() for reason in (r.get('reasons') or [])))
    result={};exclusions=defaultdict(int)
    for team,drivers in teams.items():
        if not team or len(drivers)!=2:
            exclusions['team_identity_or_pair']+=len(drivers);continue
        a,b=drivers;na,nb=a['driver_number'],b['driver_number'];delta=[];lap_numbers=[]
        common=sorted({l for n,l in lap_index if n==na}&{l for n,l in lap_index if n==nb})
        for lap in common:
            ra,rb=lap_index[na,lap],lap_index[nb,lap]
            if lap==1 or lap in neutral or any((n,k) in pits for n in (na,nb) for k in (lap,lap-1)):
                exclusions['start_pit_or_neutral']+=1;continue
            if ra.get('reasons') or rb.get('reasons'):
                exclusions['source_quality_or_traffic']+=1;continue
            ta,tb=ra.get('tyre') or {},rb.get('tyre') or {}
            if not ta.get('compound') or ta['compound']=='UNKNOWN' or ta['compound']!=tb.get('compound'):
                exclusions['compound']+=1;continue
            if not finite(ta.get('age')) or not finite(tb.get('age')) or ta['age']<0 or tb['age']<0 or abs(ta['age']-tb['age'])>AGE_TOLERANCE:
                exclusions['age']+=1;continue
            # Symmetric percent difference; signs invert exactly for the teammate.
            delta.append(200*(ra['duration']-rb['duration'])/(ra['duration']+rb['duration']));lap_numbers.append(lap)
        if len(delta)<MIN_MATCHED_LAPS:
            exclusions['insufficient_pair']+=1;continue
        center=median(delta)
        for d,other,sign in ((a,b,1),(b,a,-1)):
            result[d['driver_number']]={'teammate':other['name'],'teammate_code':other['code'],'pace_delta_pct':round(center*sign,5),'matched_laps':len(delta),'matched_lap_numbers':lap_numbers,'delta_q25':quantile([x*sign for x in delta],.25),'delta_q75':quantile([x*sign for x in delta],.75)}
    return result,dict(exclusions)


def candidate_cycles(payload):
    """Observe outcomes of comparable paired stops, including negative outcomes.

    This is not a register of driver/team intent or unchosen opportunities.
    Require consecutive elapsed timing, consistent position/gap ordering,
    no neutralisation, no extra stops, and an initial gap of at most 3 positions.
    """
    laps={(r['driver'],r['lap']):r for r in payload.get('all_laps',[]) if finite(r.get('duration')) and r['duration']>0}
    positions={(r['driver'],r['lap']):r['position'] for r in payload.get('positions',[]) if finite(r.get('position'))}
    elapsed={}
    for d in payload.get('drivers',[]):
        n=d['driver_number'];total=0
        for lap in range(1,int(payload.get('laps',0))+1):
            if (n,lap) not in laps:break
            total+=laps[n,lap]['duration'];elapsed[n,lap]=total
    stops=list({(r['driver'],int(r['lap'])):dict(r,lap=int(r['lap'])) for r in payload.get('explorer',{}).get('pit',[]) if finite(r.get('lap')) and r['lap']>=1 and int(r['lap'])==r['lap']}.values())
    neutral={r['lap'] for r in payload.get('explorer',{}).get('neutral',[])}|set(payload.get('explorer',{}).get('red',[]))
    neutral.update(r['lap'] for r in payload.get('all_laps',[]) if any('neutral' in str(reason).lower() or 'vlag' in str(reason).lower() for reason in (r.get('reasons') or [])))
    pitlane={d['driver_number'] for d in payload.get('drivers',[]) if d.get('pitlane_start')}
    out=[];excluded=defaultdict(int)
    for first,second in combinations(stops,2):
        if first['driver']==second['driver'] or not 1<=abs(first['lap']-second['lap'])<=8:continue
        early,late=sorted((first,second),key=lambda s:s['lap']);n,m=early['driver'],late['driver'];before=max(1,early['lap']-1);after=late['lap']+1
        if n in pitlane or m in pitlane:
            excluded['pitlane_clock']+=1;continue
        if any(l in neutral for l in range(before,after+1)):
            excluded['neutralisation']+=1;continue
        if any(s not in (early,late) and s['driver'] in (n,m) and before<s['lap']<=after for s in stops):
            excluded['additional_stop']+=1;continue
        if any((d,l) not in elapsed for d in (n,m) for l in range(before,after+1)):
            excluded['timing_gap']+=1;continue
        old=[positions.get((d,before)) for d in (n,m)];new=[positions.get((d,after)) for d in (n,m)]
        if not all(old+new) or old[0]==old[1] or abs(old[0]-old[1])>3:
            excluded['position_context']+=1;continue
        durations=[laps[d,l]['duration'] for d in (n,m) for l in range(before,after+1)]
        if max(durations)>2*median(durations):
            excluded['timing_outlier']+=1;continue
        early_gap=elapsed[n,before]-elapsed[m,before];end_gap=elapsed[n,after]-elapsed[m,after]
        if (early_gap>0)!=(old[0]>old[1]) or (end_gap>0)!=(new[0]>new[1]):
            excluded['lap_or_order_mismatch']+=1;continue
        beneficiary=n if old[0]>old[1] else m;opponent=m if beneficiary==n else n
        sign=1 if beneficiary==n else -1
        trace=[{'lap':l,'gap':round(sign*(elapsed[n,l]-elapsed[m,l]),3)} for l in range(before,after+1)]
        own_before=old[0] if beneficiary==n else old[1];own_after=new[0] if beneficiary==n else new[1];opponent_after=new[1] if beneficiary==n else new[0]
        def compound(driver,lap):return (laps.get((driver,lap),{}).get('tyre') or {}).get('compound','UNKNOWN')
        out.append({'type':'undercut' if beneficiary==n else 'overcut','driver':beneficiary,'opponent':opponent,'early_stop':early['lap'],'late_stop':late['lap'],'baseline_lap':before,'completed_lap':after,'position_before':own_before,'position_after':own_after,'gap_before':round(sign*early_gap,3),'gap_after':round(sign*end_gap,3),'gain_seconds':round(sign*(early_gap-end_gap),3),'success':own_after<opponent_after,'race_fraction':round(early['lap']/max(1,payload.get('laps',1)),4),'start_compound':compound(beneficiary,before),'end_compound':compound(beneficiary,after),'trace':trace,'inferred':True})
    return out,dict(excluded)


def extract(root,year):
    from .publication import site_html
    for pointer in sorted((root/'analyses'/str(year)).glob('*/latest.json')):
        run=pointer.parent/json.loads(pointer.read_text())['run'];page=run/'overzicht.html'
        if not page.exists():continue
        text=site_html(page,root)
        match=re.search(r'<script\b[^>]*id=["\']dashboard-data["\'][^>]*>(.*?)</script>',text,re.S)
        if match:yield page,json.loads(match[1]),hashlib.sha256(match[1].encode()).hexdigest()


def build(root, *, end_year=None, years=5, max_bytes=MAX_EXTRA_BYTES):
    root=Path(root).resolve();end_year=end_year or datetime.now(timezone.utc).year
    if not 1<=years<=5:raise ValueError('First release is restricted to at most five seasons')
    from .publication import site_html
    catalog={};refs={};previous_races={};previous_traits={}
    previous_page=root/'analysis-lab.html'
    if previous_page.exists():
        previous_match=re.search(r'<script[^>]*id=["\']phase2-data["\'][^>]*>(.*?)</script>',site_html(previous_page,root),re.S)
        if previous_match:
            previous=json.loads(previous_match[1])
            if previous.get('definition_version')==DEFINITION_VERSION:
                previous_races={r['id']:r for r in previous.get('races',[])}
                previous_traits={(r['race'],r['number']):(r.get('qualities',{}),r.get('quality_coverage',{})) for driver in previous.get('drivers',[]) for r in driver['races']}

    catalogue_page = next((root/name for name in ('races.html','index.html') if (root/name).exists()), None)
    if catalogue_page:
        text=site_html(catalogue_page,root);m=re.search(r'<script[^>]*id=["\']catalogue-data["\'][^>]*>(.*?)</script>',text,re.S)
        if m:
            data=json.loads(m[1]);catalog={str((root/'analyses'/r['path']/'overzicht.html').resolve()):r for r in data['races'] if r.get('path')};refs=data.get('search_drivers',{})
    profiles={};races=[];cycles=[];skipped=[]
    for year in range(end_year-years+1,end_year+1):
        for page,payload,sha in extract(root,year):
            meta=catalog.get(str(page.resolve()),{});key=meta.get('circuitId') or identity(payload.get('race','unknown'));race_id=str(year)+'-'+str(meta.get('round') or page.parents[2].name)
            if not payload.get('drivers') or not payload.get('all_laps'):
                skipped.append({'race':race_id,'reason':'no measured laps'});continue
            pair,excluded=compare_teammates(payload)
            from .driver_qualities import analyse as analyse_qualities
            from .io import read_json
            normalized=page.parent/'data/normalized/input.json'
            has_normalized=normalized.exists() or normalized.with_name('input.json.gz').exists()
            raw=read_json(normalized) if has_normalized else {}
            quality_input_sha=hashlib.sha256(json.dumps({k:payload.get(k) for k in ('drivers','all_laps','tyres','explorer')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
            cached=previous_races.get(race_id,{})
            reuse=not has_normalized and cached.get('quality_input_sha256')==quality_input_sha and all((race_id,d['driver_number']) in previous_traits for d in payload['drivers'])
            if reuse:
                traits={d['driver_number']:previous_traits[race_id,d['driver_number']][0] for d in payload['drivers']}
                trait_coverage={d['driver_number']:previous_traits[race_id,d['driver_number']][1] for d in payload['drivers']}
            else:
                traits,trait_coverage=analyse_qualities(payload,raw)
            raw_source=normalized if normalized.exists() else normalized.with_name('input.json.gz')
            raw_sha=hashlib.sha256(raw_source.read_bytes()).hexdigest() if raw_source.exists() else cached.get('quality_source_sha256') if reuse else None
            del raw
            href=page.relative_to(root).as_posix();races.append({'id':race_id,'year':year,'round':meta.get('round'),'name':meta.get('name') or payload.get('race'),'circuit':meta.get('circuit') or payload.get('race'),'circuit_id':key,'date':meta.get('date'),'href':href,'source_sha256':sha,'timing_source':payload.get('timing_source'),'matched_drivers':len(pair),'drivers':len(payload['drivers']),'excluded_pairs':excluded,'quality_source_sha256':raw_sha,'quality_input_sha256':quality_input_sha,'quality_source_mode':'retained-summary' if reuse else 'normalized-input' if has_normalized else 'unavailable'})
            identities={};styles=payload.get('styles',{})
            for d in payload['drivers']:
                name=d['name'];matched=[i for i,v in refs.items() if identity(v.get('name',''))==identity(name)];driver_id=matched[0] if len(matched)==1 else identity(name);identities[d['driver_number']]=driver_id
                colour=(styles.get(str(d['driver_number'])) or styles.get(d['driver_number']) or {}).get('color','#51d6dd')
                p=profiles.setdefault(driver_id,{'id':driver_id,'name':name,'code':d['code'],'number':d.get('display_number',d['driver_number']),'color':colour,'races':[]})
                result=d.get('result') or {};retired=result.get('dnf');retired=retired if isinstance(retired,bool) else None
                p['races'].append({'race':race_id,'year':year,'team':d.get('team'),'number':d['driver_number'],'color':colour,'grid':d.get('grid'),'finish':d.get('finish'),'lap1_position':d.get('lap1_position'),'start_gain':d.get('lap1_net_gain') if d.get('lap1_net_gain') is not None else (d['grid']-d['lap1_position'] if finite(d.get('grid')) and d['grid']>0 and finite(d.get('lap1_position')) else None),'dnf':retired,'comparison':({k:v for k,v in pair[d['driver_number']].items() if k not in ('matched_lap_numbers','teammate_code')} if d['driver_number'] in pair else None),'qualities':traits.get(d['driver_number'],{}),'quality_coverage':trait_coverage.get(d['driver_number'],{})})
            found,cycle_excluded=candidate_cycles(payload);races[-1]['cycle_exclusions']=cycle_excluded;races[-1]['candidate_cycles']=len(found)
            for i,c in enumerate(found):cycles.append(dict(c,id=f'{race_id}-{i}',race=race_id,year=year,circuit_id=key,driver=identities[c['driver']],opponent=identities[c['opponent']]))
    race_metadata={r['id']:r for r in races}
    for p in profiles.values():p['races'].sort(key=lambda r:(r['year'],race_metadata[r['race']].get('date') or '',race_metadata[r['race']].get('round') or 0))
    data={'schema':SCHEMA,'definition_version':DEFINITION_VERSION,'period':[end_year-years+1,end_year],'races':races,'drivers':sorted(profiles.values(),key=lambda p:p['name']),'cycles':cycles,'skipped':skipped,'settings':{'min_matched_laps':MIN_MATCHED_LAPS,'max_tyre_age_difference':AGE_TOLERANCE,'max_stop_gap':8,'max_initial_position_gap':3},'generated_at':datetime.now(timezone.utc).isoformat()}
    encoded=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('</','<\\/')
    src=Path(__file__).parent;assets=root/'assets';assets.mkdir(exist_ok=True)
    extra=len(encoded.encode())+sum((src/name).stat().st_size for name in ['phase2.js','phase2.css','phase2-entry.js','driver-qualities.js','site-navigation.js','site-navigation.css'])+50_000
    if extra>max_bytes:raise ValueError(f'Phase two exceeds its {max_bytes:,}-byte budget: {extra:,}')
    for name in ['phase2.js','phase2.css','phase2-entry.js','driver-qualities.js','site-navigation.js','site-navigation.css']:shutil.copyfile(src/name,assets/name)
    from .branding import branding,hero_style
    page='<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Analyseomgeving · Overtake It Away</title><link rel="stylesheet" href="assets/phase2.css">'+hero_style('assets/f1-banner-v3.png')+'</head><body><div class="race-hero">'+branding('assets/f1-banner-v3.png',seasons_url='races.html' if (root/'races.html').exists() else 'index.html').replace('<a class="all-seasons-button"','<a id="home-link" class="all-seasons-button"')+'<h1 id="lab-title">Rijders &amp; strategie</h1><p id="lab-subtitle"></p></div><div class="lab-layout"><aside id="lab-controls"></aside><main id="lab-main"><nav id="lab-tabs" role="tablist" aria-label="Analyseonderwerpen"></nav><div id="lab-content" role="tabpanel"></div></main></div><script id="phase2-data" type="application/json">'+encoded+'</script><script src="assets/driver-qualities.js"></script><script src="assets/phase2.js"></script></body></html>'
    from .branding import back_to_top
    page=page.replace('</body>',back_to_top()+'</body>')
    (root/'analysis-lab.html').write_text(page)
    for catalog_page,href,prefix in [(catalogue_page,'analysis-lab.html','assets/'),(root/'analyses/index.html','../analysis-lab.html','../assets/')]:
        if catalog_page is not None and catalog_page.exists():
            text=catalog_page.read_text()
            if 'data-phase2-entry' not in text:
                text=text.replace('<div class="catalogue-tools">',entry_link(href,prefix)+'<div class="catalogue-tools">',1)
                catalog_page.write_text(text)
    report={'schema':SCHEMA,'period':data['period'],'races':len(races),'drivers':len(profiles),'candidate_cycles':len(cycles),'matched_driver_races':sum(bool(r['comparison']) for p in profiles.values() for r in p['races']),'extra_bytes_upper_bound':extra,'max_extra_bytes':max_bytes,'qualities':{k:sum(bool(r.get('qualities',{}).get(k)) for p in profiles.values() for r in p['races']) for k in ('free','metronome','tyres','warmup','pitwindow','start')},'page':'analysis-lab.html'}
    (assets/'phase2-build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def entry_link(href, asset_prefix):
    return '<nav style="margin:0 0 18px"><a class="accent-button" data-phase2-entry href="'+html.escape(href,quote=True)+'">Rijders &amp; strategie · Analyseomgeving</a></nav><script defer src="'+html.escape(asset_prefix,quote=True)+'phase2-entry.js"></script>'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--end-year',type=int);parser.add_argument('--years',type=int,default=5);args=parser.parse_args();print(json.dumps(build(args.root,end_year=args.end_year,years=args.years),indent=2))

if __name__=='__main__':main()
