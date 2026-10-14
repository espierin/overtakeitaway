from copy import deepcopy
import gzip
import json

from bs4 import BeautifulSoup

from f1_analysis.driver_history import VERSION, enrich, guard_tyre_updates
from f1_analysis.driver_qualities import analyse, traffic_evidence
from f1_analysis.phase2 import build
from test_driver_qualities import race


def test_invalid_stint_messages_do_not_destroy_other_driver_timing():
    import pandas as pd
    from types import SimpleNamespace
    frame=pd.DataFrame({'Driver':['3','3'],'Stint':[0,5]})
    def broken(frame,splits):raise IndexError('stint bracket')
    session=SimpleNamespace(_Session__fix_tyre_info=broken)
    rejected=guard_tyre_updates(session)
    assert session._Session__fix_tyre_info(frame,[]).empty
    assert rejected==['3'] and len(frame)==2


def historical_input():
    payload, original = race()
    raw = {'format': VERSION, 'clock': 'session-seconds', 'laps': [],
           'position': [], 'intervals': [], 'stints': deepcopy(payload['tyres']['stints'])}
    for source in original['laps']:
        lap = next(r for r in payload['all_laps'] if r['driver']==source['driver_number'] and r['lap']==source['lap_number'])
        start = source['lap_number']*110+source['driver_number']
        raw['laps'].append(dict(source, time_start=start, compound='SUPERSOFT', age=lap['tyre']['age'],
                                accurate=True, deleted=False, track_status='1', pit_in=False, pit_out=False))
        for fraction in (.25,.5,.75):
            raw['intervals'].append({'driver_number':source['driver_number'],'time':start+source['lap_duration']*fraction,'interval':5})
    for stint in raw['stints']:stint['compound']='SUPERSOFT'
    for lap in payload['all_laps']:lap['tyre']={'compound':'UNKNOWN','age':None}
    payload['tyres']['stints']=[]
    return payload,raw


def test_relative_timing_preserves_evidence_without_inventing_utc():
    payload, raw = historical_input()
    for row in raw['laps']:row.pop('date_start')
    assert all(traffic_evidence(payload,raw).values())
    raw.pop('clock')
    assert not traffic_evidence(payload,raw)


def test_historical_enrichment_uses_verified_age_quality_and_dry_compounds():
    payload,raw=historical_input();before=deepcopy(payload)
    enriched=enrich(payload,raw)
    traits,coverage=analyse(enriched,raw)
    assert payload==before
    assert traits[1]['free'] and traits[1]['metronome']
    assert traits[1]['free'][0]['compound']=='SUPERSOFT'
    raw['laps'][0]['lap_duration']+=1
    assert 'historical timing mismatch' in enrich(payload,raw)['all_laps'][0]['reasons']
    for lap in raw['laps']:lap['accurate']=False
    assert not analyse(enrich(payload,raw),raw)[0][1]['metronome']
    raw['laps']=[]
    assert not analyse(enrich(payload,raw),raw)[0][1]['free']


def test_compact_history_rebuild_retains_enriched_comparisons_and_cycles(tmp_path):
    payload,raw=historical_input();payload.update(race='Historic circuit',laps=48)
    payload['positions']=[{'driver':n,'lap':lap,'position':n} for n in (1,2) for lap in range(1,49)]
    for d in payload['drivers']:d.setdefault('code',str(d['driver_number']))
    event=tmp_path/'analyses/2018/circuit';run=event/'runs/one';(run/'data/normalized').mkdir(parents=True)
    (event/'latest.json').write_text(json.dumps({'run':'runs/one'}))
    page=run/'overzicht.html'
    def write():page.write_text('<script id="dashboard-data" type="application/json">'+json.dumps(payload)+'</script>')
    def data():return json.loads(BeautifulSoup((tmp_path/'analysis-lab.html').read_text(),'html.parser').find(id='phase2-data').string)
    write();supplement=run/'data/normalized/driver-history.json.gz';supplement.write_bytes(gzip.compress(json.dumps(raw).encode()))
    build(tmp_path,end_year=2026);before=data()
    assert before['races'][0]['quality_source_mode']=='historical-timing'
    assert next(d for d in before['drivers'] if d['number']==1)['races'][0]['comparison']
    supplement.unlink();build(tmp_path,end_year=2026);after=data()
    assert before['drivers']==after['drivers'] and before['cycles']==after['cycles']
    assert after['races'][0]['quality_source_mode']=='retained-summary'
    assert before['races'][0]['quality_source_sha256']==after['races'][0]['quality_source_sha256']
    payload['all_laps'][2]['duration']+=2;write();build(tmp_path,end_year=2026)
    changed=data();assert changed['races'][0]['quality_source_mode']=='unavailable'
    comparison=next(d for d in changed['drivers'] if d['number']==1)['races'][0]['comparison']
    assert comparison['method']=='overlap-mean' and comparison['delta_q25'] is None
    assert comparison!=next(d for d in before['drivers'] if d['number']==1)['races'][0]['comparison']
