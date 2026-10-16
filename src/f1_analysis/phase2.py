"""Compact, reproducible driver profiles and observed pit-cycle comparisons.

No causal tyre effects, attempted-undercut claims, or fabricated missing data.
Retained World Championship races from 1950, with per-parameter coverage.
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
LEGACY_DEFINITION_VERSION='matched-teammates-v1/paired-pit-cycles-v1/driver-qualities-v1/start-distribution-v1'
LAP_DEFINITION_VERSION=LEGACY_DEFINITION_VERSION+'/lap-metronome-v1'
DEFINITION_VERSION=LAP_DEFINITION_VERSION+'/pace-overlap-v2'
MAX_EXTRA_BYTES=64_000_000
DEFAULT_YEARS=None  # all retained seasons, from the start of the championship
FIRST_YEAR=1950
MIN_MATCHED_LAPS=6
AGE_TOLERANCE=2


def finite(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)


def identity(name):
    from .driver_identity import identity as canonical_identity
    return canonical_identity(name)


def quantile(values, fraction):
    values=sorted(values)
    if not values:return None
    index=(len(values)-1)*fraction;lo=int(index);hi=min(lo+1,len(values)-1)
    return round(values[lo]+(values[hi]-values[lo])*(index-lo),5)


def compare_teammates(payload):
    from .pace_comparison import analyse
    return analyse(payload,min_laps=MIN_MATCHED_LAPS,age_tolerance=AGE_TOLERANCE)


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



def finish_evidence(driver):
    """Require an explicit result status; classification or completed distance alone
    cannot prove an on-track finish (including a retirement on the final lap).
    """
    result=driver.get('result') or {}
    status=driver.get('status') or result.get('status') or result.get('status_text')
    status=status.strip() if isinstance(status,str) else None
    dnf=result.get('dnf',driver.get('dnf'))
    if any(result.get(k) is True or driver.get(k) is True for k in ('dnf','dns','dsq')):
        finished=False
    elif status and re.fullmatch(r'(?:Finished|Lapped|\+\d+\s+Laps?)',status,re.I):
        finished=True
    elif status and status.casefold() not in ('unknown','n/a','-'):
        finished=False
    elif dnf is False:
        finished=True
    else:
        finished=None
    value=result.get('number_of_laps',driver.get('completed_laps'))
    try:
        laps=int(value) if not isinstance(value,bool) and float(value).is_integer() and float(value)>=0 else None
    except (TypeError,ValueError,OverflowError):
        laps=None
    return {'finished_on_track':finished,'finish_status':status,'finish_laps':laps}


def pitlane_start_numbers(payload, run):
    """Recognise explicit pit-lane starts, including retained F1DB PL labels.

    Historical dashboards sometimes assigned PL entries the last numeric slot.
    That display slot must never become a normal grid start in driver research.
    """
    from .io import read_json
    numbers={d['driver_number'] for d in payload.get('drivers',[]) if d.get('pitlane_start')}
    source=Path(run)/'data/raw/historical/f1db.json'
    if source.exists() or source.with_name(source.name+'.gz').exists():
        sessions=read_json(source).get('sessions',{})
        for session, field in [('race-results','gridPositionText'),('starting-grid-positions','positionText')]:
            for item in sessions.get(session,[]):
                if str(item.get(field,'')).strip().upper() in ('PL','PIT','PIT LANE','PITLANE'):
                    try:numbers.add(int(item['driverNumber']))
                    except (KeyError,TypeError,ValueError):continue
    return numbers


def collapse_shared_entries(profiles):
    """Keep all source entries, but never score an unassigned car handover twice."""
    for profile in profiles.values():
        groups=defaultdict(list)
        for row in profile['races']:groups[row['race']].append(row)
        rows=[]
        for race, entries in groups.items():
            if len(entries)==1:
                rows.append(entries[0]);continue
            first=entries[0]
            rows.append({'race':race,'year':first['year'],'team':first.get('team'),
                         'number':first['number'],'color':first['color'],
                         'grid':None,'finish':None,'lap1_position':None,'start_gain':None,
                         'dnf':None,'comparison':None,'qualities':{},'quality_coverage':{},
                         'finished_on_track':None,'finish_status':None,'finish_laps':None,
                         'lap_rankings':[],'shared_car_ambiguous':True,
                         'shared_car_entries':entries})
        profile['races']=rows


def build(root, *, end_year=None, years=DEFAULT_YEARS, max_bytes=MAX_EXTRA_BYTES):
    root=Path(root).resolve();end_year=end_year or datetime.now(timezone.utc).year
    if years is None:years=end_year-FIRST_YEAR+1
    if isinstance(years,bool) or not isinstance(years,int) or not 1<=years<=end_year-FIRST_YEAR+1:
        raise ValueError(f'Driver profiles support one to {end_year-FIRST_YEAR+1} seasons (from {FIRST_YEAR})')
    from .publication import site_html
    catalog={};refs={};previous_races={};previous_traits={};previous_cycles=defaultdict(list)
    from . import lap_rankings, pit_programmes, pace_comparison
    from .driver_identity import ALIASES, display_name, merge_profiles
    previous_page=root/'analysis-lab.html'
    if previous_page.exists():
        previous_match=re.search(r'<script[^>]*id=["\']phase2-data["\'][^>]*>(.*?)</script>',site_html(previous_page,root),re.S)
        if previous_match:
            previous=merge_profiles(json.loads(previous_match[1]))
            if previous.get('definition_version') in (DEFINITION_VERSION,LAP_DEFINITION_VERSION,LEGACY_DEFINITION_VERSION):
                previous_races={r['id']:r for r in previous.get('races',[])}
                previous_traits={(r['race'],r['number']):r for driver in previous.get('drivers',[]) for r in driver['races']}
                for cycle in previous.get('cycles',[]):previous_cycles[cycle['race']].append(cycle)

    catalogue_page = next((root/name for name in ('races.html','index.html') if (root/name).exists()), None)
    if catalogue_page:
        text=site_html(catalogue_page,root);m=re.search(r'<script[^>]*id=["\']catalogue-data["\'][^>]*>(.*?)</script>',text,re.S)
        if m:
            data=json.loads(m[1]);catalog={str((root/'analyses'/r['path']/'overzicht.html').resolve()):r for r in data['races'] if r.get('path')};refs=data.get('search_drivers',{})
    profiles={};races=[];cycles=[];skipped=[]
    for year in range(end_year-years+1,end_year+1):
        for page,payload,sha in extract(root,year):
            meta=catalog.get(str(page.resolve()),{});key=meta.get('circuitId') or identity(payload.get('race','unknown'));race_id=str(year)+'-'+str(meta.get('round') or page.parents[2].name)
            if not payload.get('drivers'):
                skipped.append({'race':race_id,'reason':'no driver results'});continue
            from .early_driver_history import apply_retained as apply_early
            payload,early_source=apply_early(root,year,meta.get('round') or 0,payload)
            if year<1996:
                # Historical fastest-lap records are isolated measurements, not a
                # lap-by-lap timing series. Keep them in the source archive; only
                # broad measured runs can enter pace/rank analyses.
                time_counts=defaultdict(int);position_counts=defaultdict(int)
                for row in payload.get('all_laps',[]):time_counts[row['driver']]+=1
                for row in payload.get('positions',[]):
                    if row['lap']>0:position_counts[row['driver']]+=1
                timed={n for n,count in time_counts.items() if count>=5 and count>=.5*position_counts[n]}
                payload=dict(payload,all_laps=[r for r in payload.get('all_laps',[]) if r['driver'] in timed])
            from .driver_qualities import analyse as analyse_qualities
            from .io import read_json
            normalized=page.parent/'data/normalized/input.json'
            historical=page.parent/'data/normalized/driver-history.json'
            has_normalized=normalized.exists() or normalized.with_name('input.json.gz').exists()
            has_historical=historical.exists() or historical.with_name('driver-history.json.gz').exists()
            # Hash the dashboard before enrichment so a compact rebuild can verify
            # retained observations without downloading the historical feeds again.
            quality_input_sha=hashlib.sha256(json.dumps({k:payload.get(k) for k in ('drivers','all_laps','tyres','explorer')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
            cached=previous_races.get(race_id,{})
            raw=read_json(normalized) if has_normalized else read_json(historical) if has_historical else {}
            enrichment=None
            if has_historical and not has_normalized:
                from .driver_history import enrich
                payload=enrich(payload,raw);enrichment=raw['format']
            pit_starters=pitlane_start_numbers(payload,page.parent) | {d['driver_number'] for d in payload['drivers'] if previous_traits.get((race_id,d['driver_number']),{}).get('pitlane_start')}
            for d in payload['drivers']:
                if d['driver_number'] in pit_starters:d['pitlane_start']=True
            reuse=not(has_normalized or has_historical) and cached.get('quality_input_sha256')==quality_input_sha and all((race_id,d['driver_number']) in previous_traits for d in payload['drivers'])
            pair,excluded=compare_teammates(payload)
            if reuse:
                traits={d['driver_number']:previous_traits[race_id,d['driver_number']].get('qualities',{}) for d in payload['drivers']}
                trait_coverage={d['driver_number']:previous_traits[race_id,d['driver_number']].get('quality_coverage',{}) for d in payload['drivers']}
                enrichment=cached.get('profile_enrichment_source')
                if cached.get('pace_comparison_version')==pace_comparison.VERSION:
                    pair={d['driver_number']:previous_traits[race_id,d['driver_number']]['comparison'] for d in payload['drivers'] if previous_traits[race_id,d['driver_number']].get('comparison')}
                    excluded=cached.get('excluded_pairs',{})
            else:
                traits,trait_coverage=analyse_qualities(payload,raw)
            reuse_laps=(reuse and cached.get('lap_rankings_version')==lap_rankings.VERSION
                        and all('lap_rankings' in previous_traits[race_id,d['driver_number']] for d in payload['drivers']))
            # During the one-time migration, use verified old per-lap context only;
            # sector ranks themselves never become lap ranks.
            retained_context={}
            if reuse and not reuse_laps:
                for d in payload['drivers']:
                    previous_row=previous_traits[race_id,d['driver_number']]
                    for points in previous_row.get('sector_rankings',{}).values():
                        for lap,_,_,compound,flags in points:
                            retained_context[d['driver_number'],lap]=(compound,flags)
            lap_data=({d['driver_number']:previous_traits[race_id,d['driver_number']]['lap_rankings'] for d in payload['drivers']}
                      if reuse_laps else lap_rankings.analyse(payload,raw,retained_context))
            if not has_normalized and not has_historical:
                for d in payload['drivers']:
                    n=d['driver_number'];prior=previous_traits.get((race_id,n),{}).get('lap_rankings',[])
                    lap_data[n]=lap_rankings.preserve_retained_context(lap_data.get(n,[]),prior)
            source=normalized if has_normalized else historical
            raw_source=source if source.exists() else source.with_name(source.name+'.gz')
            raw_sha=hashlib.sha256(raw_source.read_bytes()).hexdigest() if raw_source.exists() else cached.get('quality_source_sha256') if reuse else None
            retained_pits=cached.get('pit_programmes',{})
            reuse_pits=(retained_pits.get('version')==pit_programmes.VERSION and cached.get('source_sha256')==sha
                        and (not raw_source.exists() or raw_sha==cached.get('quality_source_sha256')))
            pit_data=retained_pits if reuse_pits else pit_programmes.analyse(payload,raw)
            del raw
            href=page.relative_to(root).as_posix();races.append({'id':race_id,'year':year,'round':meta.get('round'),'name':meta.get('name') or payload.get('race'),'circuit':meta.get('circuit') or payload.get('race'),'circuit_id':key,'date':meta.get('date'),'href':href,'source_sha256':sha,'timing_source':payload.get('timing_source'),'matched_drivers':len(pair),'drivers':len(payload['drivers']),'excluded_pairs':excluded,'quality_source_sha256':raw_sha,'quality_input_sha256':quality_input_sha,'quality_source_mode':'retained-summary' if reuse else 'normalized-input' if has_normalized else 'historical-timing' if has_historical else 'unavailable','profile_enrichment_source':enrichment})
            races[-1]['lap_rankings_version']=lap_rankings.VERSION
            races[-1]['pace_comparison_version']=pace_comparison.VERSION
            if early_source:races[-1]['early_timing_source']=early_source
            races[-1]['pit_programmes']=pit_data
            identities={};styles=payload.get('styles',{})
            for d in payload['drivers']:
                name=display_name(d['name']);matched={ALIASES.get(i,i) for i,v in refs.items() if identity(v.get('name',''))==identity(name)};driver_id=next(iter(matched)) if len(matched)==1 else identity(name);identities[d['driver_number']]=driver_id
                colour=(styles.get(str(d['driver_number'])) or styles.get(d['driver_number']) or {}).get('color','#51d6dd')
                p=profiles.setdefault(driver_id,{'id':driver_id,'name':name,'code':d['code'],'number':d.get('display_number',d['driver_number']),'color':colour,'races':[]})
                # Iteration is chronological; the profile badge follows the latest
                # appearance, while every race retains its own number/team colour.
                p.update(code=d['code'],number=d.get('display_number',d['driver_number']),color=colour)
                result=d.get('result') or {};retired=result.get('dnf');retired=retired if isinstance(retired,bool) else None
                p['races'].append({'race':race_id,'year':year,'team':d.get('team'),'number':d['driver_number'],'color':colour,'grid':d.get('grid'),'finish':d.get('finish'),'lap1_position':d.get('lap1_position'),'start_gain':d.get('lap1_net_gain') if d.get('lap1_net_gain') is not None else (d['grid']-d['lap1_position'] if finite(d.get('grid')) and d['grid']>0 and finite(d.get('lap1_position')) else None),'dnf':retired,'comparison':({k:v for k,v in pair[d['driver_number']].items() if k not in ('matched_lap_numbers','teammate_code')} if d['driver_number'] in pair else None),'qualities':{k:v for k,v in traits.get(d['driver_number'],{}).items() if k!='metronome'},'quality_coverage':trait_coverage.get(d['driver_number'],{})})
                p['races'][-1].update(finish_evidence(d))
                if d['driver_number'] in pit_starters:
                    p['races'][-1].update(pitlane_start=True,start_gain=None)
                    p['races'][-1]['qualities']['start']=[]
                p['races'][-1]['lap_rankings']=lap_data.get(d['driver_number'],[])
            if reuse and enrichment:
                retained=previous_cycles.get(race_id,[]);cycles.extend(retained)
                races[-1]['cycle_exclusions']=cached.get('cycle_exclusions',{});races[-1]['candidate_cycles']=len(retained)
                continue
            found,cycle_excluded=candidate_cycles(payload);races[-1]['cycle_exclusions']=cycle_excluded;races[-1]['candidate_cycles']=len(found)
            for i,c in enumerate(found):cycles.append(dict(c,id=f'{race_id}-{i}',race=race_id,year=year,circuit_id=key,driver=identities[c['driver']],opponent=identities[c['opponent']]))
    collapse_shared_entries(profiles)
    race_metadata={r['id']:r for r in races}
    for p in profiles.values():p['races'].sort(key=lambda r:(r['year'],race_metadata[r['race']].get('date') or '',race_metadata[r['race']].get('round') or 0))
    data={'schema':SCHEMA,'definition_version':DEFINITION_VERSION,'period':[end_year-years+1,end_year],'races':races,'drivers':sorted(profiles.values(),key=lambda p:p['name']),'cycles':cycles,'skipped':skipped,'settings':{'min_matched_laps':MIN_MATCHED_LAPS,'max_tyre_age_difference':AGE_TOLERANCE,'max_stop_gap':8,'max_initial_position_gap':3},'generated_at':datetime.now(timezone.utc).isoformat()}
    data['settings']['race_progression']={'version':1,'origin':'lap1_position','outcome':'finish','require_confirmed_finish':True,'reference_finishers_only':True}
    data['settings']['pace_comparison']={'version':pace_comparison.VERSION,'mean_fallback':True,'retirement_overlap':True}
    data['settings']['shared_cars']={'ambiguous_multi_entries':'retained_separately_not_scored'}
    data['settings']['lap_rankings']={'version':lap_rankings.VERSION,'columns':lap_rankings.POINT_COLUMNS,'compounds':lap_rankings.COMPOUNDS,'flags':{'first':1,'pit':2,'flag':4,'quality':8,'wet':16,'unknown_tyre':32,'not_free':64,'traffic':128}}
    from .incidents import attach_retained
    merge_profiles(data)
    attach_retained(data,root)
    encoded=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('</','<\\/')
    src=Path(__file__).parent;assets=root/'assets';assets.mkdir(exist_ok=True)
    asset_names=['driver-card-art.css','highlights.css','site-header.css','driver-profile-sidebar.css','site-branding.js','site-branding.css','driver-period.js','driver-period.css','preseason-testing.js','preseason-testing.css','pit-programmes.js','pace-timeline.js','phase2.js','phase2.css','phase2-entry.js','driver-qualities.js','driver-field.js','driver-names.js','lap-rankings.js','site-navigation.js','site-navigation.css','site-theme.css']
    intro_assets=['preseason-testing-v1.webp','preseason-testing-v1.prompt.txt','drivers.webp','goat-winter-break-v1.webp','races.webp']
    card_assets=['driver-starter-v1.webp','driver-clear-air-v1.webp','driver-metronome-v1.webp','driver-tyre-whisperer-v1.webp','driver-warm-up-v1.webp','driver-pitwindow-v1.webp','driver-quality-prompts-v1.json']
    card_bytes=sum((src/'assets/cards'/name).stat().st_size for name in card_assets)
    intro_bytes=sum((src/'assets/home'/name).stat().st_size for name in intro_assets)
    saved_metrics_bytes=sum((assets/name).stat().st_size for name in ('starter-metrics.json','starter-metrics.csv') if (assets/name).exists())
    from .driver_sidebar import CSS as driver_sidebar_css
    extra=len(driver_sidebar_css.encode())+len(encoded.encode())+sum((src/name).stat().st_size for name in asset_names)+intro_bytes+card_bytes+saved_metrics_bytes+50_000
    if extra>max_bytes:raise ValueError(f'Phase two exceeds its {max_bytes:,}-byte budget: {extra:,}')
    for name in asset_names:
        if name=='driver-profile-sidebar.css':
            (assets/name).write_text(driver_sidebar_css+(src/name).read_text())
        elif name=='highlights.css':
            (assets/name).write_text('\n'.join(line for line in (src/name).read_text().split('\n') if '--highlight-image:url(' not in line))
        else:shutil.copyfile(src/name,assets/name)
    (assets/'cards').mkdir(exist_ok=True)
    for name in card_assets:shutil.copyfile(src/'assets/cards'/name,assets/'cards'/name)
    (assets/'home').mkdir(exist_ok=True)
    for name in intro_assets:shutil.copyfile(src/'assets/home'/name,assets/'home'/name)
    from .branding import branding,hero_style
    page='<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Coureurs · Overtake It Away</title><link rel="stylesheet" href="assets/phase2.css"><link rel="stylesheet" href="assets/highlights.css"><link rel="stylesheet" href="assets/driver-card-art.css"><link rel="stylesheet" href="assets/driver-period.css"><link rel="stylesheet" href="assets/driver-profile-sidebar.css">'+hero_style('assets/f1-banner-v3.png')+'</head><body><div class="race-hero" data-header-section="drivers">'+branding('assets/f1-banner-v3.png',seasons_url='races.html' if (root/'races.html').exists() else 'index.html').replace('data-site-link="races"','id="home-link" data-site-link="races"',1)+'<h1 id="lab-title">Coureurs</h1><p id="lab-subtitle"></p></div><div class="lab-layout"><aside id="lab-controls"></aside><main id="lab-main"><nav id="lab-tabs" role="tablist" aria-label="Analyseonderwerpen"></nav><section id="lab-filters" class="lab-filters"></section><div id="lab-content" role="tabpanel"></div></main></div><script id="phase2-data" type="application/json">'+encoded+'</script><script src="assets/driver-qualities.js"></script><script src="assets/phase2.js"></script></body></html>'
    page=page.replace('</head>','<link rel="stylesheet" href="assets/preseason-testing.css"><link rel="preload" as="image" href="assets/home/preseason-testing-v1.webp"></head>')
    page=page.replace('</body>','<script src="assets/preseason-testing.js"></script></body>')
    from .branding import back_to_top
    page=page.replace('<script src="assets/driver-qualities.js">','<script src="assets/pit-programmes.js"></script><script src="assets/pace-timeline.js"></script><script src="assets/lap-rankings.js"></script><script src="assets/driver-field.js"></script><script src="assets/driver-qualities.js">')
    page=page.replace('</body>',back_to_top()+'</body>')
    page=page.replace('<script src="assets/phase2.js">','<script src="assets/driver-names.js"></script><script src="assets/driver-period.js"></script><script src="assets/phase2.js">')
    (root/'analysis-lab.html').write_text(page)
    from .site_navigation import without_legacy_entry
    for catalog_page in (catalogue_page,root/'analyses/index.html'):
        if catalog_page is not None and catalog_page.exists():
            text=catalog_page.read_text()
            cleaned=without_legacy_entry(text)
            if cleaned!=text:
                text=cleaned
                catalog_page.write_text(text)
    report={'schema':SCHEMA,'period':data['period'],'races':len(races),'drivers':len(profiles),'candidate_cycles':len(cycles),'matched_driver_races':sum(bool(r['comparison']) for p in profiles.values() for r in p['races']),'extra_bytes_upper_bound':extra,'max_extra_bytes':max_bytes,'qualities':{k:sum(bool(r.get('qualities',{}).get(k)) for p in profiles.values() for r in p['races']) for k in ('free','metronome','tyres','warmup','pitwindow','start')},'page':'analysis-lab.html'}
    report['lap_rankings']=sum(len(r['lap_rankings']) for p in profiles.values() for r in p['races'])
    report['driver_races']=sum(len(p['races']) for p in profiles.values())
    report['shared_car_ambiguous']=sum(bool(r.get('shared_car_ambiguous')) for p in profiles.values() for r in p['races'])
    report['qualities']['metronome']=sum(bool(r['lap_rankings']) for p in profiles.values() for r in p['races'])
    report['pit_programmes']={'races':sum(len(r['pit_programmes']['entries'])>=2 for r in races),'drivers':sum(len(r['pit_programmes']['entries']) for r in races),'lap_observations':sum(len(e[2]) for r in races for e in r['pit_programmes']['entries'])}
    (assets/'phase2-build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    # The collection page is opt-in once created; refresh its driver layer here.
    if (root/'data-collection.html').exists():
        from .data_collection import build as build_collection
        build_collection(root)
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--end-year',type=int);parser.add_argument('--years',type=int,default=DEFAULT_YEARS);args=parser.parse_args();print(json.dumps(build(args.root,end_year=args.end_year,years=args.years),indent=2))

if __name__=='__main__':main()
