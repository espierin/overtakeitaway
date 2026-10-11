from f1_analysis.historical_backfill import augment, color_for, supplemental_facts, HistoricalDatabase, HistoricalChartDatabase, apply_retained
from collections import defaultdict
import json, importlib.util
from types import SimpleNamespace


def driver(entry='a', number=7):
    return {'id':entry,'driver_id':'old-a','number':number,'name':'Driver A','code':'AAA','team_id':'t','team':'Team',
            'grid':None,'position':2,'completed_laps':60,'classified':True,'color':None,'laps':[], 'pitstops':[]}


def supplement():
    return {'entry_drivers':{'a':'driver-a'},'source':{'url':'https://example.org/data'},'sessions':{
        'race-results':[{'driverId':'driver-a','driverNumber':'7','gridPositionNumber':'3','polePosition':'false'}],
        'fastest-laps':[{'driverId':'driver-a','driverNumber':'7','positionNumber':'1','lap':'42','time':'1:20.123','timeMillis':'80123'}],
        'pit-stops':[{'driverId':'driver-a','driverNumber':'7','stop':'1','lap':'20','timeMillis':'24123'}]}}


def test_backfill_retains_originals_and_does_not_invent_lap_positions():
    original={'year':1995,'round':1,'drivers':[driver()]}
    result=augment(original,supplement())
    d=result['drivers'][0]
    assert original['drivers'][0]['laps']==[] and original['drivers'][0]['grid'] is None
    assert d['grid']==3
    assert d['laps']==[{'lap':42,'position':None,'seconds':80.123,'deleted':False,'source':'F1DB','observation':'personal-fastest-lap-only'}]
    assert d['pitstops'][0]['duration']==24.123
    assert d['pitstops'][0]['duration_kind']=='source-reported-pit-duration'
    assert 'overtakes' not in result


def test_existing_pit_observations_and_results_win_over_conflicting_supplement():
    original={'year':2012,'round':1,'drivers':[driver()]}
    original['drivers'][0].update(grid=5,pitstops=[{'stop':1,'lap':21,'duration':22.4}])
    result=augment(original,supplement())
    assert result['drivers'][0]['grid']==5
    assert result['drivers'][0]['pitstops']==original['drivers'][0]['pitstops']


def test_shared_cars_do_not_duplicate_pit_records_or_fastest_laps_on_wrong_car():
    s=supplement();s['entry_drivers']['b']='driver-a'
    original={'year':1957,'round':1,'drivers':[driver(),driver('b',8)]}
    result=augment(original,s)
    assert result['pit_records']==0
    assert result['drivers'][1]['laps']==[] and 'fastest_lap' not in result['drivers'][1]


def test_livery_reference_uses_year_round_and_specific_driver_without_leaking():
    registry={'records':[
        {'team_ids':['t'],'from_year':1964,'to_year':1964,'display_hex':'#f00'},
        {'team_ids':['t'],'from_year':1964,'to_year':1964,'rounds':[9,10],'display_hex':'#00f'},
        {'team_ids':['t'],'from_year':1964,'to_year':1964,'driver_ids':['a'],'display_hex':'#fff'}]}
    assert color_for(registry,'t',1964,8)['display_hex']=='#f00'
    assert color_for(registry,'t',1964,9)['display_hex']=='#00f'
    assert color_for(registry,'t',1964,9,'a')['display_hex']=='#fff'
    assert color_for(registry,'t',1965) is None


def test_official_pole_and_fastest_fact_are_separate_from_grid_one():
    d=driver();other=driver('b',8);s=supplement();s['entry_drivers']['b']='driver-b'
    s['sessions']['race-results']=[{'driverId':'driver-b','driverNumber':'8','polePosition':'true'}]
    result=supplemental_facts({'drivers':[d,other],'historical_supplement':s},{'pole':{'id':'a'}})
    assert result['pole']['id']=='b'
    assert result['fastest']['id']=='a' and result['fastest']['fastest_time']=='1:20.123'


def test_equal_fastest_times_do_not_make_one_driver_the_only_record_holder():
    s=supplement();s['sessions']['fastest-laps'].append({**s['sessions']['fastest-laps'][0],'driverId':'driver-b','driverNumber':'8'})
    result=supplemental_facts({'drivers':[driver(),driver('b',8)],'historical_supplement':s},{})
    assert 'fastest' not in result


def test_driver_birth_date_alone_cannot_join_different_people():
    db=object.__new__(HistoricalDatabase)
    db.drivers={};db.names={};db.birthdays={'1900-01-01':[{'id':'someone-else','lastName':'Else','dateOfBirth':'1900-01-01'}]}
    assert db.match_driver({'forename':'Another','surname':'Person','date_of_birth':'1900-01-01','reference':'another'}) is None


def test_lap_chart_fills_positions_without_overwriting_measured_times_or_inventing_overtakes():
    original={'year':1995,'round':1,'drivers':[driver()]}
    original['drivers'][0]['laps']=[{'lap':1,'position':2,'seconds':89.2,'deleted':False}]
    s=supplement();s['historical_chart']={'lap_chart':[
        {'entry_id':'a','lap':1,'position':3,'seconds':90.0},
        {'entry_id':'a','lap':2,'position':1,'seconds':None}]}
    result=augment(original,s)
    assert result['drivers'][0]['laps'][0]==original['drivers'][0]['laps'][0]
    assert result['drivers'][0]['laps'][1]['position']==1
    assert result['drivers'][0]['laps'][1]['seconds'] is None
    assert result['historical_supplement']['added']['lap_positions']==1
    assert 'overtakes' not in result


def test_untimestamped_shared_car_chart_is_not_assigned_wholly_to_one_driver():
    chart=object.__new__(HistoricalChartDatabase)
    chart.races={(1950,1):{'ID':1,'DateInDateTime':'1950-05-13','Weather':'Sunny'}}
    chart.careers={1:'driver-a',2:'driver-b'}
    chart.charts=defaultdict(list,{1:[{'DriverID':1,'Lap':1,'Position':3,'TimeInSeconds':None}]})
    chart.pits=defaultdict(list);chart.speeds=defaultdict(list)
    s=supplement();s['entry_drivers']['b']='driver-b'
    out=chart.supplement({'year':1950,'round':1,'date':'1950-05-13','drivers':[driver(),driver('b',7)]},s)
    assert out['lap_chart']==[]
    assert out['ambiguous_entries'][0]['reason']=='shared-car-driver-not-timestamped'


def test_wayback_capture_year_is_not_used_as_the_race_year(monkeypatch):
    path=__import__('pathlib').Path(__file__).parents[1]/'research/normalize_historical_sources.py'
    spec=importlib.util.spec_from_file_location('historical_normalizer_wayback_test',path)
    normalizer=importlib.util.module_from_spec(spec);spec.loader.exec_module(normalizer)
    normalizer.DB=SimpleNamespace(races={(2012,6):{'grandPrixId':'monaco','officialName':'Monaco Grand Prix'}})
    normalizer.GP={'monaco':{'fullName':'Monaco Grand Prix'}}
    item={'capture_timestamp':'20150601000000'}
    text='Race Best Sector Times\nFORMULA 1 GRAND PRIX DE MONACO 2012 - Monte-Carlo\n© 2012 Formula One World Championship Ltd.'
    assert normalizer.race_key(item,text)==(2012,6)
    assert normalizer.race_key({**item,'year':2011},text) is None
    assert normalizer.race_key(item,text.replace('© 2012','© 2011')) is None


def test_retained_supplement_and_timing_can_be_rebuilt_without_network(tmp_path):
    data={'year':1995,'round':1,'date':'1995-03-26','drivers':[driver()]}
    s=supplement();s['race']={'date':data['date']}
    folder=tmp_path/'analyses/sources/historical'
    (folder/'supplements').mkdir(parents=True);(folder/'timing').mkdir()
    (folder/'supplements/1995-01.json').write_text(json.dumps(s))
    (folder/'timing/1995-01.json').write_text(json.dumps({'laps':[{'number':7,'lap':1,'sectors':[30.2,None,31.8]}]}))
    result=apply_retained(data,{},tmp_path)
    assert result['timing']['laps'][0]['sectors'][1] is None
    assert result['drivers'][0]['laps'][0]['seconds']==80.123


def parser():
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('historical_parser',Path(__file__).parents[1]/'research/normalize_historical_sources.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_pirelli_partial_compound_statement_retains_unknown_destination():
    p=parser()
    rows=p.explicit_tyre_changes('Lap 24: Vettel pits from soft tyre to hard tyre. Lap 42: Alonso pits from soft tyre.')
    assert [(r['lap'],r['from'],r['to']) for r in rows]==[(24,'SOFT','HARD'),(42,'SOFT',None)]


def test_fia_layout_blank_sector_column_does_not_shift_adjacent_sector():
    p=parser()
    text='2015 AUSTRALIAN GRAND PRIX\nRace\n     SECTOR 1                         SECTOR 2                         SECTOR 3\n1    33 M. VERSTAPPEN  31.602          33 M. VERSTAPPEN  24.874          33 M. VERSTAPPEN  37.586\n2                                    8 R. GROSJEAN  25.432\n'
    rows=p.column_rows(text,'best_sectors')
    assert [(r['number'],r['sector']) for r in rows]==[(33,1),(33,2),(33,3),(8,2)]
