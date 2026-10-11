from copy import deepcopy
from datetime import datetime, timedelta, timezone
import pytest
import yaml
from f1_analysis.analysis import Context, make_events, count_events, apply_corrections, pit_cycles
from f1_analysis.location import estimate_zone, map_counts
from f1_analysis.io import select_race
from f1_analysis.acquire import import_passes

BASE=datetime(2025,1,1,tzinfo=timezone.utc)
def date(seconds):return (BASE+timedelta(seconds=seconds)).isoformat()
@pytest.fixture
def config():
    return yaml.safe_load(open('config/defaults.yaml'))
@pytest.fixture
def data():
    return {'session':{'session_key':1,'year':2025,'circuit_short_name':'Test'},
            'drivers':[{'driver_number':d} for d in [1,2]],
            'laps':[{'driver_number':d,'lap_number':n,'date_start':date((n-1)*100+delay),'lap_duration':100} for d,delay in [(1,0),(2,2)] for n in range(1,7)],
            'position':[{'driver_number':d,'date':date(t),'position':p} for d,t,p in [(1,0,2),(2,0,1),(1,150,1),(2,150,2)]],
            'overtakes':[{'overtaking_driver_number':1,'overtaken_driver_number':2,'date':date(150),'position':1}],
            'session_result':[{'driver_number':1,'number_of_laps':6,'position':1},{'driver_number':2,'number_of_laps':6,'position':2}],
            'race_control':[{'date':date(0),'message':'SESSION STARTED'}], 'pit':[], 'stints':[], 'intervals':[], 'weather':[], 'evidence':[]}

def test_same_event_multiple_sources_is_one(data,config):
    data['f1gures']=[{'overtaking_driver_number':1,'overtaken_driver_number':2,'lap_number':2,'source_url':'https://example.org/','definition':'net passes'}]
    events=make_events(Context(data,config));stats=count_events(events,6,config)
    assert len(events)==1 and stats['analytical']==1 and stats['source_matches']==1
    assert len(events[0]['source_records'])==2

def test_historical_pair_reversal_survives_asynchronous_rank_ties():
    from f1_analysis.history import inversions
    rows=[{'date':date(t),'driver_number':d,'position':p} for t,d,p in [(0,1,2),(0,2,1),(150,1,1),(151,2,2),(152,2,2)]]
    result=inversions(rows)
    assert len(result)==1
    assert result[0]['date']==date(151)
    assert (result[0]['overtaking_driver_number'],result[0]['overtaken_driver_number'])==(1,2)

def test_historical_source_is_not_mislabelled_openf1(data,config):
    data['timing_source']='FastF1'
    events=make_events(Context(data,config));stats=count_events(events,6,config)
    assert events[0]['source_records'][0]['source']=='FastF1'
    assert stats['timing_original']==1 and stats['openf1_original']==0
    assert stats['analytical']==1

def test_historical_location_query_without_offset_is_utc():
    from f1_analysis.history import Locations
    source=object.__new__(Locations)
    source.rows={'1':[{'date':date(150),'x':1,'y':2}]};source.times={'1':[BASE.timestamp()+150]}
    assert source.api('location',driver_number=1,**{'date>':'2025-01-01T00:02:20','date<':'2025-01-01T00:02:40'})==source.rows['1']

def test_missing_pit_coverage_cannot_confirm_on_track_pass(data,config):
    data['pit_coverage_unknown']=True
    events=make_events(Context(data,config))
    assert events[0]['type']=='onzeker'
    assert count_events(events,6,config)['analytical']==0

def test_double_race_at_same_circuit_matches_full_canonical_name():
    races=[{'session_name':'Race','country_name':'Bahrain','location':'Sakhir','circuit_short_name':'Sakhir — '+name} for name in ['Bahrain','Sakhir']]
    assert select_race(races,'Sakhir — Sakhir') is races[1]
    with pytest.raises(ValueError):select_race(races,'Bahrain')

def test_red_flag_and_restart_are_neutralised(data,config):
    data['race_control'] += [{'date':date(120),'flag':'RED','scope':'Track','message':'RED FLAG'},
                             {'date':date(220),'message':'SESSION STARTED'}]
    ctx=Context(data,config)
    assert make_events(ctx)[0]['type']=='neutralisatie'
    assert ctx.neutral(BASE.timestamp()+310)
    assert not ctx.neutral(BASE.timestamp()+330)

def test_classified_distance_takes_precedence_over_observed_countback_laps(data,config):
    data['session_result'][0]['number_of_laps']=1
    ctx=Context(data,config)
    assert ctx.observed_lap_count==6 and ctx.lap_count==1
    assert count_events(make_events(ctx),ctx.lap_count,config)['denominator']==0

def test_missing_lap_total_for_disqualified_driver_uses_measured_laps(data,config):
    data['session_result'][0]['number_of_laps']=None
    assert Context(data,config).lap_count==6

def test_canonical_hyphenated_circuit_name_matches_calendar():
    race={'session_name':'Race','country_name':'Belgium','location':'Spa-Francorchamps','circuit_short_name':'Spa-Francorchamps'}
    assert select_race([race],'Spa-Francorchamps') is race
    assert select_race([race],'Spa Francorchamps') is race
    assert select_race([race],'België') is race

def test_missing_first_lap_times_does_not_discard_later_race_events(data,config):
    data['session']['date_start']=date(0)
    for lap in data['laps']:
        if lap['lap_number']==1:lap['date_start']=None
    ctx=Context(data,config)
    assert ctx.start_confirmed and ctx.start==BASE.timestamp()
    assert make_events(ctx)[0]['type']=='inhaalactie'
    data['race_control']=[]
    assert make_events(Context(data,config))[0]['type']=='onzeker'

def test_virtual_safety_car_ending_closes_each_neutralisation(data,config):
    data['race_control'] += [{'date':date(t),'message':m} for t,m in [(10,'VIRTUAL SAFETY CAR DEPLOYED'),(20,'VIRTUAL SAFETY CAR ENDING'),(200,'VIRTUAL SAFETY CAR DEPLOYED'),(210,'VIRTUAL SAFETY CAR ENDING')]]
    ctx=Context(data,config)
    assert ctx.neutral(BASE.timestamp()+30)
    assert not ctx.neutral(BASE.timestamp()+150)
    assert ctx.neutral(BASE.timestamp()+230)
    assert not ctx.neutral(BASE.timestamp()+350)
    assert make_events(ctx)[0]['type']=='inhaalactie'

def test_calendar_match_handles_local_night_race_date_and_country_alias():
    from f1_analysis.acquire import calendar_match
    races=[{'date':'2025-11-22','Circuit':{'Location':{'country':'USA'}}}]
    assert calendar_match(races,{'date_start':'2025-11-23T04:00:00+00:00','country_name':'United States'})==races
    assert not calendar_match(races,{'date_start':'2025-11-23T04:00:00+00:00','country_name':'Qatar'})

def test_duplicates_preserve_original_count(data,config):
    data['overtakes'].append({**data['overtakes'][0],'date':date(150.5)})
    events=make_events(Context(data,config));stats=count_events(events,6,config)
    assert len(events)==1 and stats['openf1_original']==2 and stats['analytical']==1

def test_pit_exchange_is_not_overtake(data,config):
    data['pit']=[{'driver_number':2,'date':date(170),'lane_duration':25,'lap_number':2}]
    e=make_events(Context(data,config));s=count_events(e,6,config)
    assert e[0]['type']=='pitstopwisseling' and s['analytical']==0

def test_first_lap_is_separate(data,config):
    data['overtakes'][0]['date']=date(50)
    events=make_events(Context(data,config));stats=count_events(events,6,config)
    assert events[0]['type']=='startactie' and stats['lap1_changes']==1 and stats['analytical']==0

def test_start_finish_boundary_not_lapping(data,config):
    data['overtakes'][0]['date']=date(201)
    data['position'][2]['date']=date(201);data['position'][3]['date']=date(201)
    e=make_events(Context(data,config))[0]
    assert e['lap']==3 and e['overtaken_lap']==2 and e['type']=='inhaalactie'

def test_lapped_driver_is_excluded(data,config):
    for l in data['laps']:
        if l['driver_number']==2:l['date_start']=date((l['lap_number']-1)*100+100)
    e=make_events(Context(data,config))[0]
    assert e['type']=='dubbelen_of_terugronden'

def test_correction_is_reproducible_and_keeps_original(data,config):
    events=make_events(Context(data,config));change={'events':[{'event_id':events[0]['event_id'],'reason':'Bron bevestigt teamwissel','source_url':'https://example.org/','set':{'type':'mogelijke_teamorder'}}]}
    one=apply_corrections(deepcopy(events),change);two=apply_corrections(deepcopy(events),change)
    assert one==two and one[0]['corrections'][0]['original']=='inhaalactie'
    s=count_events(one,6,config);assert s['on_track']==1 and s['analytical']==0
    with pytest.raises(ValueError):apply_corrections(events,{'events':[{'event_id':'verkeerd','reason':'test','source_url':'https://example.org','set':{'type':'onzeker'}}]})

def test_totals_and_denominators(data,config):
    events=make_events(Context(data,config));s=count_events(events,6,config)
    assert sum(s['per_lap'].values())==s['analytical']==sum(s['made'].values())==sum(s['received'].values())
    assert s['laps_with']+s['laps_without']==5 and s['late_start']==5
    assert s['mean']==.2

def test_incomplete_pit_cycle_not_assessed(data,config):
    data['pit']=[{'driver_number':1,'lap_number':2,'date':date(190),'lane_duration':25},{'driver_number':2,'lap_number':6,'date':date(590),'lane_duration':25}]
    assert pit_cycles(Context(data,config))==[]

def test_cycle_after_both_outlaps(data,config):
    data['pit']=[{'driver_number':1,'lap_number':2,'date':date(190),'lane_duration':25},{'driver_number':2,'lap_number':4,'date':date(390),'lane_duration':25}]
    cs=pit_cycles(Context(data,config));assert len(cs)==1 and cs[0]['completed_lap']==5 and cs[0]['baseline_lap']==1

def test_missing_location_does_not_create_points(data,config):
    assert estimate_zone([], [[],[]],0,config) is None
    events=make_events(Context(data,config));count_events(events,6,config)
    m=map_counts(events,config);assert m['located']==0 and m['unknown']==1 and sum(m['bins'])==0

def test_heatmap_uses_progress_not_xy(config):
    events=[{'counts':{'analytical':True},'location_confidence':'geschatte zone','location':{'progress':.1,'x':0,'y':0}}, {'counts':{'analytical':True},'location_confidence':'geschatte zone','location':{'progress':.6,'x':0,'y':0}}]
    m=map_counts(events,config);assert m['bins'][10]==1 and m['bins'][60]==1 and sum(m['bins'])==2

def test_alias_and_ambiguity():
    session={'session_name':'Race','country_name':'Netherlands','location':'Zandvoort','circuit_short_name':'Zandvoort'}
    for query in ['Nederland','Dutch GP','Zandvoort']:assert select_race([session],query)==session
    with pytest.raises(ValueError):select_race([session,session],'Nederland')
    assert select_race([session,{**session,'session_name':'Sprint'}],'Nederland')['session_name']=='Race'

def test_import_requires_provenance(tmp_path):
    p=tmp_path/'passes.json';p.write_text('[{"lap_number":2}]')
    with pytest.raises(ValueError):import_passes(p,2025,1)

def test_reversal_noise_not_counted(data,config):
    data['overtakes'].append({'overtaking_driver_number':2,'overtaken_driver_number':1,'date':date(150.2),'position':1})
    events=make_events(Context(data,config));stats=count_events(events,6,config)
    assert stats['analytical']==0 and stats['types']['timingfluctuatie']==2

def test_neutral_exchange_not_counted(data,config):
    data['race_control'] += [{'date':date(130),'message':'SAFETY CAR DEPLOYED','category':'SafetyCar'},{'date':date(190),'message':'SAFETY CAR IN THIS LAP','category':'SafetyCar'}]
    events=make_events(Context(data,config));stats=count_events(events,6,config)
    assert events[0]['type']=='neutralisatie' and stats['analytical']==0

def test_zero_actions_has_no_invented_busiest_lap(data,config):
    data['overtakes']=[]
    stats=count_events(make_events(Context(data,config)),6,config)
    assert stats['busiest_laps']==[] and stats['late_fraction'] is None and stats['laps_without']==5

def test_pit_timestamp_is_exit_regression(data,config):
    # The FIA entry / OpenF1 exit comparison must not shift a pit window AFTER the exit.
    data['pit']=[{'driver_number':2,'date':date(172),'lane_duration':25,'lap_number':2}]
    events=make_events(Context(data,config));assert events[0]['type']=='pitstopwisseling'

def test_location_dates_match_supported_api_syntax():
    from f1_analysis.location import iso
    assert '+' not in iso(BASE.timestamp()) and iso(BASE.timestamp()).endswith('.000')

def test_source_algorithm_uses_explicit_positions():
    from f1_analysis.f1gures import derive_passes
    payload={'type':'race','drivers':[{'code':'AAA','grid':2},{'code':'BBB','grid':1}],
             'laps':{'AAA':[[1,100,1,'SOFT',0,1,False,False,True]],'BBB':[[1,102,2,'MEDIUM',0,1,False,False,True]]},'trackStatus':[]}
    drivers=[{'name_acronym':'AAA','driver_number':1},{'name_acronym':'BBB','driver_number':2}]
    events=derive_passes(payload,drivers,'https://example.org/data.json','https://example.org/display.js')
    assert len(events)==1 and events[0]['lap_number']==1 and events[0]['access_method'].startswith('automatisch')
    payload['laps']['BBB'][0][6]=True
    assert derive_passes(payload,drivers,'https://example.org/data.json','https://example.org/display.js')==[]
    payload['laps']['BBB'][0][2]=None
    with pytest.raises(ValueError):derive_passes(payload,drivers,'https://example.org/data.json','https://example.org/display.js')

def test_ambiguous_nearby_track_sections_stay_unknown(config):
    # Two geometrically coincident sections separated along the lap cannot be silently merged.
    import math
    track=[{'x':math.cos(i/200*2*math.pi)*1000,'y':math.sin(i/200*2*math.pi)*1000,'progress':i/400} for i in range(401)]
    rows=[{'x':1000,'y':0,'date':date(t)} for t in [148,150,152]]
    assert estimate_zone(track,[rows,rows],BASE.timestamp()+150,config) is None

def test_official_layout_requires_available_year_source_and_matching_basis():
    from f1_analysis.location import official_reference
    track=[{'x':i*10,'y':0} for i in range(100)]
    data={'session':{'year':2025},'circuit':{'year':2023,'corners':[{'number':1,'trackPosition':{'x':50,'y':0}}]},'evidence':[]}
    assert not official_reference(data,track)
    source={'year':2025,'available':True,'url':'https://fia.com/map.pdf','title':'FIA','verified_facts':{'circuit_layout':{'corners':1,'compatible_basis_year':2023}}}
    data['evidence']=[source]
    assert official_reference(data,track)['coordinate_basis_year']==2023
    assert data['circuit']['year']==2023  # source year is never rewritten
    source['available']=False
    assert not official_reference(data,track)
    source['available']=True;source['year']=2024
    assert not official_reference(data,track)
    source['year']=2025;source['verified_facts']['circuit_layout']['corners']=19
    assert not official_reference(data,track)

def test_wikipedia_name_tables_do_not_confuse_roads_and_turns():
    from bs4 import BeautifulSoup
    from f1_analysis.circuit_info import table_names
    html='<table><tr><th>Turn</th><th>Name</th></tr><tr><td>1</td><td>Sheares[1]</td></tr><tr><td>5–7</td><td>Raffles Boulevard</td></tr><tr><td>2</td><td>—</td></tr></table>'
    assert table_names(BeautifulSoup(html,'html.parser'))==[{'number':1,'name':'Sheares','status':'kandidaat; jaarvariant nog controleren'}]


def test_circuit_annotations_require_matching_year_names_and_pit_source():
    from f1_analysis.circuit_info import annotate_reference
    track=[{'x':i,'y':0,'progress':i/100} for i in range(101)]
    reference={'reference_corners':[{'number':1,'progress':.1,'x':10,'y':0},{'number':2,'progress':.2,'x':20,'y':0}]}
    variant={'first_year':2025,'last_year':2025,'corner_count':2,'names':[{'number':1,'name':'Sheares'},{'number':2,'name':'Verzonnen'}],
             'pit_zones':[{'label':'Pit-out','after_turn':1,'before_turn':2,'fraction':.5,'note':'Zone'}],'pit_source_url':'https://fia.com/pit.pdf','pit_source_title':'FIA'}
    data={'session':{'year':2025},'wikipedia_circuit':{'url':'https://en.wikipedia.org/wiki/Test','available':True,'text':'Sheares'},'circuit_annotation_config':{'variants':[variant]},'evidence':[]}
    r=annotate_reference(data,track,reference,[])
    assert r['reference_corners'][0]['name']=='Sheares' and 'name' not in r['reference_corners'][1] and not r['pit_markers']
    data['evidence']=[{'url':variant['pit_source_url'],'available':True,'year':2025}]
    assert annotate_reference(data,track,reference,[])['pit_markers'][0]['x']==15
    data['session']['year']=2026
    r=annotate_reference(data,track,reference,[])
    assert not r['pit_markers'] and all('name' not in c for c in r['reference_corners'])

def test_wikipedia_reads_article_body_instead_of_coordinate_box(tmp_path):
    from f1_analysis.circuit_info import acquire_wikipedia
    class Client:
        def fetch(self,*args,**kwargs):
            return b'<h1>Circuit</h1><div class="mw-parser-output">Coordinates: 1,2</div><div class="mw-parser-output"><p>Turn 1 was named Sheares. Turn 7 was named Memorial.</p></div>'
    data={'session':{'circuit_short_name':'Test'},'jolpica_circuit':{'url':'http://en.wikipedia.org/wiki/Test'}}
    acquire_wikipedia(Client(),data,tmp_path,{},[])
    assert data['wikipedia_circuit']['url']=='https://en.wikipedia.org/wiki/Test'
    assert 'Sheares' in data['wikipedia_circuit']['text']
    assert (tmp_path/'supplementary/wikipedia-circuit.html').exists()

def test_map_label_rectangles_avoid_entire_track_and_each_other():
    from f1_analysis.map_labels import place_labels,segment_hits_box,boxes_overlap
    import numpy as np
    track=[{'x':0,'y':0},{'x':800,'y':0},{'x':800,'y':100},{'x':0,'y':100},{'x':0,'y':0}]
    items=[{'x':400,'y':0,'text':'Lang bochtlabel dat niet over de parallelle baan mag vallen'},
           {'x':410,'y':0,'text':'Pit-in ≈'},{'x':420,'y':0,'text':'12'}]
    labels=place_labels(track,items)
    assert len(labels)==3
    for i,label in enumerate(labels):
        assert not any(segment_hits_box([a['x'],a['y']],[b['x'],b['y']],label['box']) for a,b in zip(track[:-1],track[1:]))
        assert all(not boxes_overlap(label['box'],p['box']) for p in labels[:i])

def test_team_styles_use_race_colours_and_stable_teammate_pattern():
    from f1_analysis.driver_style import driver_styles
    rows=[{'driver_number':63,'name_acronym':'RUS','team_name':'Mercedes','team_colour':'00D7B6'},
          {'driver_number':12,'name_acronym':'ANT','team_name':'Mercedes','team_colour':'00D7B6'}]
    a=driver_styles(rows);b=driver_styles(list(reversed(rows)))
    assert a==b and a[12]['color']==a[63]['color']=='#00D7B6'
    assert a[12]['linestyle']=='-' and a[63]['linestyle']==':'
    assert a[63]['label']=='63 RUS'

def test_index_shows_only_latest_success_per_race(tmp_path):
    from f1_analysis.render import update_index
    from f1_analysis.io import write_json
    base=tmp_path/'analyses/2025/test'
    for name,date in [('old','2026-01-01'),('new','2026-02-01')]:
        run=base/'runs'/name;run.mkdir(parents=True)
        write_json(run/'manifest.json',{'input':{'year':2025,'gp':'Test'},'session':{'circuit_short_name':'Test','date_start':'2025-03-16'},'created_at':date,'status':'gedeeltelijk'})
        (run/'overzicht.html').write_text('report')
    write_json(base/'latest.json',{'run':'runs/new'})
    update_index(tmp_path)
    rows=__import__('json').loads((tmp_path/'analyses/index.json').read_text())
    assert len(rows)==1 and rows[0]['path']=='2025/test/runs/new'
    assert 'runs/old' not in (tmp_path/'index.html').read_text()


def test_track_uses_another_complete_lap_when_lap_five_is_pit_out(data,config,tmp_path):
    import math
    from f1_analysis.location import fetch_locations
    next(l for l in data['laps'] if l['driver_number']==1 and l['lap_number']==5)['is_pit_out_lap']=True
    queries=[]
    class Source:
        def api(self,endpoint,**query):
            queries.append(query)
            return [{'date':date(100+i),'x':1000*math.cos(i/100*2*math.pi),'y':1000*math.sin(i/100*2*math.pi)} for i in range(101)]
    track,_=fetch_locations(Source(),Context(data,config),[],tmp_path,[])
    assert len(track)==401
    assert data['track_reference_lap']=={'driver_number':1,'lap_number':2}
    assert len(queries)==1
