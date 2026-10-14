from copy import deepcopy
from f1_analysis.pit_programmes import analyse, VERSION, PACK
from f1_analysis.phase2 import build


def fixture():
    data={'drivers':[], 'all_laps':[], 'positions':[], 'explorer':{'pit':[], 'neutral':[], 'red':[]}, 'laps':10}
    for n,stop in [(1,3),(2,5)]:
        data['drivers'].append({'driver_number':n,'name':f'Driver {n}','code':f'DR{n}','team':str(n),'grid':n,'finish':n,'result':{'number_of_laps':10,'dnf':False}})
        data['explorer']['pit'].append({'driver':n,'lap':stop})
        for lap in range(1,11):
            data['all_laps'].append({'driver':n,'lap':lap,'duration':90+(20 if lap==stop else 0),'reasons':[]})
            data['positions'].append({'driver':n,'lap':lap,'position':n})
    return data


def test_pack_reconstructs_measured_times_positions_and_distinct_stops():
    p=fixture();p['explorer']['pit'] += [{'driver':1,'lap':3},{'driver':1,'lap':7}]
    out=analyse(p)
    assert out['version']==VERSION and len(out['entries'])==2
    assert out['entries'][0][:2]==[1,[3,7]]
    assert out['entries'][0][2][2]//PACK==110_000
    assert out['entries'][0][2][2]%PACK==1
    assert out['entries'][1][2][2]//PACK==90_000


def test_retirements_are_not_treated_as_fewer_stop_strategies():
    p=fixture();p['drivers'][0]['result']['dnf']=True
    out=analyse(p);assert len(out['entries'])==1
    assert out['excluded']['1']=='not_confirmed_finisher'
    p['drivers'][0]['classified']=True
    assert '1' in analyse(p)['excluded']


def test_historical_finisher_requires_finished_status_or_plus_laps():
    p=fixture();p['drivers'][0]['result'].pop('dnf');p['drivers'][0]['status']='+1 Lap'
    assert len(analyse(p)['entries'])==2
    p['drivers'][0]['status']='Accident'
    assert analyse(p)['excluded']['1']=='not_confirmed_finisher'


def test_unknown_stop_count_is_not_zero_and_raw_disagreements_are_rejected():
    p=fixture();p['explorer']['pit']=p['explorer']['pit'][1:]
    assert analyse(p)['excluded']['1']=='pit_coverage'
    p['strategy_detection']={'complete':True}
    assert analyse(p)['entries'][0][1]==[]
    raw={'pit':[{'driver_number':1,'lap_number':4},{'driver_number':2,'lap_number':5}]}
    assert analyse(p,raw)['excluded']['1']=='pit_coverage'
    p=fixture();p['explorer']['pit'][0]['lap']=None
    assert analyse(p)['excluded']['1']=='pit_coverage'


def test_missing_and_conflicting_laps_are_unknown_not_interpolated():
    p=fixture();p['all_laps']=p['all_laps'][1:]
    assert analyse(p)['excluded']['1']=='timing_coverage'
    p=fixture();duplicate=deepcopy(p['all_laps'][0]);duplicate['duration']=91;p['all_laps'].append(duplicate)
    assert analyse(p)['excluded']['1']=='timing_coverage'
    p=fixture();p['drivers'][0]['pitlane_start']=True
    assert analyse(p)['excluded']['1']=='start_clock'


def test_missing_position_is_explicit_and_flags_are_retained():
    p=fixture();p['positions']=p['positions'][1:];p['explorer']['neutral']=[{'lap':4,'kind':'SC'}];p['explorer']['red']=[6]
    out=analyse(p)
    assert out['entries'][0][2][0]%PACK==0
    assert out['flags']==[[4,1],[6,2]]
    assert out['flag_context_known'] is True
    assert analyse(fixture())['flag_context_known'] is False
    assert analyse(fixture(),{'laps':[{'driver_number':1,'lap_number':1,'track_status':'1'}]})['flag_context_known'] is True


def test_compact_rebuild_preserves_pit_register_without_normalized_inputs(tmp_path):
    import json,re,gzip
    event=tmp_path/'analyses/2026/test';run=event/'runs/test';run.mkdir(parents=True)
    (event/'latest.json').write_text(json.dumps({'run':'runs/test'}))
    p=fixture();p['race']='Test';(run/'overzicht.html').write_text('<script id="dashboard-data">'+json.dumps(p)+'</script>')
    normalized=run/'data/normalized/input.json.gz';normalized.parent.mkdir(parents=True)
    normalized.write_bytes(gzip.compress(json.dumps({'pit':[{'driver_number':1,'lap_number':3},{'driver_number':2,'lap_number':5}]}).encode()))
    def data():return json.loads(re.search(r'id="phase2-data"[^>]*>(.*?)</script>',(tmp_path/'analysis-lab.html').read_text(),re.S)[1])
    report=build(tmp_path,end_year=2026,years=1);first=data()
    assert report['pit_programmes']['drivers']==2
    normalized.unlink();build(tmp_path,end_year=2026,years=1);second=data()
    assert first['races'][0]['pit_programmes']==second['races'][0]['pit_programmes']
    assert 'assets/pit-programmes.js' in (tmp_path/'analysis-lab.html').read_text()
    # Changed source data cannot retain a stale stop programme.
    p['explorer']['pit'][0]['lap']=4;(run/'overzicht.html').write_text('<script id="dashboard-data">'+json.dumps(p)+'</script>')
    build(tmp_path,end_year=2026,years=1)
    assert data()['races'][0]['pit_programmes']['entries'][0][1]==[4]
