from copy import deepcopy
import json
from bs4 import BeautifulSoup
from f1_analysis.lap_rankings import analyse, PIT, FLAG, FIRST, NOT_FREE, VERSION
from f1_analysis.phase2 import build


def race(size=22):
    p={'race':'Example','drivers':[],'all_laps':[],'explorer':{'sectors':[],'pit':[],'neutral':[],'red':[]}}
    for n in range(1,size+1):
        p['drivers'].append({'driver_number':n,'name':f'Driver {n}','code':f'D{n}','team':f'Team {(n-1)//2}'})
        for lap in (1,2,3):
            p['all_laps'].append({'driver':n,'lap':lap,'duration':90+n if lap!=3 else 114-n,'tyre':{'compound':'SOFT','age':lap-1},'reasons':[]})
            p['explorer']['sectors'].append({'driver':n,'lap':lap,'sector':1,'duration':22-n/2})
    return p


def test_each_lap_is_ranked_in_its_own_race_lap_against_all_measured_drivers():
    p=race();original=deepcopy(p);r=analyse(p)
    assert p==original
    assert r[1][1][:3]==[2,1,22]
    assert r[1][2][:3]==[3,22,22]
    assert r[22][1][:3]==[2,22,22]
    assert len(r[1])==3 # Whole laps, even when sector times exist.
    p['all_laps']=[l for l in p['all_laps'] if not(l['driver']==22 and l['lap']==3)]
    assert analyse(p)[1][2][2]==21
    assert len(analyse(p)[22])==2


def test_tied_times_share_a_rank_and_missing_is_not_last_or_zero():
    p=race(4)
    next(l for l in p['all_laps'] if l['driver']==2 and l['lap']==2)['duration']=91
    r=analyse(p)
    assert r[1][1][1]==r[2][1][1]==1 and r[3][1][1]==3
    p['all_laps']=[l for l in p['all_laps'] if not(l['driver']==4 and l['lap']==2)]
    r=analyse(p);assert r[3][1][2]==3 and len(r[4])==2


def test_sector_data_never_affect_whole_lap_ranks():
    p=race(4);before=analyse(p)
    for s in p['explorer']['sectors']:s['duration']=999
    p['explorer'].update(heat_resolution='lap',sector_count=1)
    assert analyse(p)==before
    p['explorer']['sectors']=[]
    assert analyse(p)==before


def test_context_is_retained_without_dropping_or_reranking_the_field():
    p=race(4);p['explorer']['pit']=[{'driver':1,'lap':2}];p['explorer']['neutral']=[{'lap':3,'kind':'SC'}]
    r=analyse(p)
    assert len(r[1])==3
    assert r[1][0][4]&FIRST and r[1][1][4]&PIT and r[1][2][4]&FLAG
    assert r[2][1][1:3]==[2,4]
    assert r[2][1][4]&NOT_FREE # Unknown traffic is not clear-air evidence.
    raw={'laps':[{'driver_number':1,'lap_number':2,'track_status':'4'}]}
    assert analyse(race(4),raw)[1][1][4]&FLAG


def test_conflicting_duplicate_times_are_never_arbitrarily_ranked():
    p=race(4);duplicate=deepcopy(p['all_laps'][0]);duplicate['duration']+=1;p['all_laps'].append(duplicate)
    assert len(analyse(p)[1])==2
    assert analyse(p)[2][0][2]==3


def test_compact_rebuild_preserves_every_lap_rank_and_context(tmp_path):
    p=race(4);event=tmp_path/'analyses/2025/example';run=event/'runs/one';(run/'data/normalized').mkdir(parents=True)
    (event/'latest.json').write_text(json.dumps({'run':'runs/one'}));page=run/'overzicht.html'
    def write():page.write_text('<script id="dashboard-data">'+json.dumps(p)+'</script>')
    def data():return json.loads(BeautifulSoup((tmp_path/'analysis-lab.html').read_text(),'html.parser').find(id='phase2-data').string)
    raw={'laps':[{'driver_number':1,'lap_number':2,'fastf1_is_accurate':False}]}
    source=run/'data/normalized/input.json';source.write_text(json.dumps(raw));write();build(tmp_path,end_year=2026)
    before=data();assert before['races'][0]['lap_rankings_version']==VERSION
    assert 'sector_rankings' not in json.dumps(before)
    assert all('metronome' not in r['qualities'] for d in before['drivers'] for r in d['races'])
    source.unlink();build(tmp_path,end_year=2026);assert data()['drivers']==before['drivers']
    next(l for l in p['all_laps'] if l['driver']==4 and l['lap']==2)['duration']=1
    write();build(tmp_path,end_year=2026)
    one=next(d for d in data()['drivers'] if d['id']=='driver-4')
    assert one['races'][0]['lap_rankings'][1][1]==1
