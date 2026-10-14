from copy import deepcopy
from datetime import datetime,timedelta,timezone
import pytest
from f1_analysis.driver_qualities import analyse,traffic_evidence


def race(a_base=0,a_deg=.02,b_deg=.04,a_noise=0,b_noise=.16,warm=0,execution=0):
    drivers=[{'driver_number':1,'name':'Driver A','code':'AAA','team':'Team','grid':3,'lap1_position':1}, {'driver_number':2,'name':'Driver B','code':'BBB','team':'Team','grid':4,'lap1_position':4}]
    drivers +=[{'driver_number':n,'name':str(n),'team':'Other'+str(n),'grid':g,'lap1_position':end} for n,g,end in [(3,1,3),(4,2,2),(5,5,5),(6,6,6)]]
    p={'drivers':drivers,'all_laps':[],'tyres':{'stints':[]},'explorer':{'pit':[{'driver':n,'lap':20} for n in (1,2)],'neutral':[],'red':[]}}
    raw={'laps':[],'intervals':[],'position':[]};start=datetime(2025,1,1,tzinfo=timezone.utc)
    for n,base,deg,noise in [(1,a_base,a_deg,a_noise),(2,0,b_deg,b_noise)]:
        for si,lo,hi in [(1,1,20),(2,21,48)]:p['tyres']['stints'].append({'driver_number':n,'stint_number':si,'lap_start':lo,'lap_end':hi,'compound':'MEDIUM','tyre_age_at_start':0})
        for lap in range(1,49):
            age=lap-1 if lap<=20 else lap-21
            duration=100+base+deg*age-.01*lap+(noise if lap%2 else -noise)
            if n==1 and lap>21 and age in (1,2,3):duration+=warm
            if n==1 and lap in (18,19,22,23):duration-=execution
            p['all_laps'].append({'driver':n,'lap':lap,'duration':duration,'tyre':{'compound':'MEDIUM','age':age},'reasons':[]})
            date=start+timedelta(seconds=lap*110+n)
            raw['laps'].append({'driver_number':n,'lap_number':lap,'date_start':date.isoformat(),'lap_duration':duration})
            for fraction in (.25,.5,.75):
                time=(date+timedelta(seconds=duration*fraction)).isoformat()
                raw['intervals'].append({'driver_number':n,'date':time,'interval':5})
        raw['position'].append({'driver_number':n,'date':start.isoformat(),'position':n})
    return p,raw


def test_missing_or_stale_traffic_does_not_mean_free_air():
    p,raw=race();raw['intervals']=[];raw['position']=[]
    traits,coverage=analyse(p,raw)
    assert not traits[1]['free'] and not traits[1]['metronome']
    assert coverage[1]['free_laps']==0 and traits[1]['start'][0]['value']==2
    p,raw=race();raw['position']=[]
    for interval in raw['intervals']:interval['date']='2024-01-01T00:00:00Z'
    assert not any(traffic_evidence(p,raw).values())


def test_confirmed_leader_does_not_need_changing_interval_messages():
    p,raw=race();raw['intervals']=[]
    evidence=traffic_evidence(p,raw)
    assert evidence[1,5] and not evidence[2,5]


def test_tyres_separate_baseline_speed_and_relative_pace_retention():
    p,raw=race(a_base=2,a_deg=.01,b_deg=.04,b_noise=0)
    traits,_=analyse(p,raw)
    assert traits[1]['free'][0]['value']>0 # A is slower overall.
    assert traits[1]['tyres'][0]['value']>0 # A still retains pace better.
    assert traits[1]['tyres'][0]['value']==-traits[2]['tyres'][0]['value']
    assert all(o['age_max']-o['age_min']>=10 for o in traits[1]['tyres'])


def test_metronome_uses_own_detrended_laps_and_retains_measured_zero():
    p,raw=race();traits,_=analyse(p,raw)
    assert len(traits[1]['metronome'])==2 # Same compound, two distinct tyre sets.
    assert traits[1]['metronome'][0]['value']==pytest.approx(0,abs=.00001)
    assert traits[2]['metronome'][0]['value']>traits[1]['metronome'][0]['value']
    assert 'reference' in traits[1]['metronome'][0]


def test_warmup_compares_known_new_sets_with_later_trend():
    p,raw=race(warm=.6);traits,_=analyse(p,raw)
    assert traits[1]['warmup'][0]['value']>0.5
    assert traits[1]['warmup'][0]['stop']==20
    p['tyres']['stints'][1]['tyre_age_at_start']=4
    for row in p['all_laps']:
        if row['driver']==1 and row['lap']>=21:row['tyre']['age']+=4
    assert not analyse(p,raw)[0][1]['warmup']


def test_pitwindow_execution_not_pit_lane_loss_or_strategy_result():
    p,raw=race(execution=.4);traits,_=analyse(p,raw)
    assert traits[1]['pitwindow'][0]['value']>0.3
    assert [v[0] for v in traits[1]['pitwindow'][0]['trace']]==[-2,-1,2,3]
    p['explorer']['neutral']=[{'lap':20,'kind':'SC'}]
    assert not analyse(p,raw)[0][1]['pitwindow']


def test_tyres_and_free_air_reject_mismatched_sets_and_flagged_laps():
    p,raw=race()
    for s in p['tyres']['stints']:
        if s['driver_number']==2:s['compound']='HARD'
    for r in p['all_laps']:
        if r['driver']==2:r['tyre']['compound']='HARD'
    traits,_=analyse(p,raw)
    assert not traits[1]['free'] and not traits[1]['tyres']
    p,raw=race()
    for r in p['all_laps']:r['reasons']=['traffic']
    traits,_=analyse(p,raw)
    assert not traits[1]['metronome'] and not traits[1]['warmup'] and not traits[1]['pitwindow']


def test_starter_unknown_or_pitlane_is_not_a_zero_performance():
    p,raw=race();assert analyse(p,raw)[0][1]['start'][0]['value']==2
    p['drivers'][0]['pitlane_start']=True;assert not analyse(p,raw)[0][1]['start']
    p['drivers'][0].pop('pitlane_start');p['drivers'][0]['lap1_position']=None
    assert not analyse(p,raw)[0][1]['start']


def test_warmup_does_not_extend_across_missing_reference_ages():
    p,raw=race(warm=.6)
    for row in p['all_laps']:
        if row['driver']==1 and row['lap']>21 and row['tyre']['age']==4:row['reasons']=['traffic']
    assert not analyse(p,raw)[0][1]['warmup']


def test_starter_uses_every_known_own_start_without_peer_requirement():
    p,raw=race()
    p['drivers']=p['drivers'][:1]
    observation=analyse(p,raw)[0][1]['start'][0]
    assert observation['grid']==3 and observation['lap1']==1
    assert observation['value']==2 and observation['n']==1
    assert 'benchmark' not in observation
    p['drivers'][0]['result']={'number_of_laps':0}
    assert not analyse(p,raw)[0][1]['start']


def test_compact_rebuild_keeps_verified_traits_without_normalized_inputs(tmp_path):
    import json
    from bs4 import BeautifulSoup
    from f1_analysis.phase2 import build
    p,raw=race();p.update(race='Example',year=2026,laps=48)
    for driver in p['drivers']:driver.setdefault('code',str(driver['driver_number']))
    event=tmp_path/'analyses/2026/example';run=event/'runs/one';(run/'data/normalized').mkdir(parents=True)
    (event/'latest.json').write_text(json.dumps({'run':'runs/one'}))
    page=run/'overzicht.html'
    def write_payload():page.write_text('<script id="dashboard-data" type="application/json">'+json.dumps(p)+'</script>')
    def data():return json.loads(BeautifulSoup((tmp_path/'analysis-lab.html').read_text(),'html.parser').find(id='phase2-data').string)
    write_payload();(run/'data/normalized/input.json').write_text(json.dumps(raw));build(tmp_path,end_year=2026)
    before=data();assert next(d for d in before['drivers'] if d['number']==1)['races'][0]['qualities']['metronome']
    (run/'data/normalized/input.json').unlink();p['highlights']={'updated':'presentation only'};write_payload();build(tmp_path,end_year=2026)
    after=data();assert after['races'][0]['quality_source_mode']=='retained-summary'
    assert [d['races'][0]['qualities'] for d in before['drivers']]==[d['races'][0]['qualities'] for d in after['drivers']]
    assert before['races'][0]['quality_source_sha256']==after['races'][0]['quality_source_sha256']
    p['all_laps'][8]['duration']+=5;write_payload();build(tmp_path,end_year=2026)
    assert data()['races'][0]['quality_source_mode']=='unavailable'
