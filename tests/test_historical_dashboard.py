import json
from pathlib import Path
from f1_analysis.historical_dashboard import historical_payload, modernize


def race():
    return {'year':1995,'round':1,'name':'Test Grand Prix','date':'1995-03-26','circuit':'Test','scheduled_laps':7,'warnings':[],
            'drivers':[{'id':str(n),'number':n,'name':name,'code':name[:3].upper(),'team':'Team '+str(n),'grid':grid,'position':finish,'classified':True,'completed_laps':7,'status':'Finished','color':'#CC0000',
                        'laps':[{'lap':lap,'position':grid if lap<5 else finish,'seconds':100+extra.get(lap,0)} for lap in range(1,8)],
                        'pitstops':[{'stop':1,'lap':stop,'duration':22}]}
                       for n,name,grid,finish,stop,extra in [(1,'Driver A',2,1,3,{1:2,3:20}),(2,'Driver B',1,2,5,{5:25})]]}


def test_reversals_are_never_confirmed_track_overtakes():
    payload=historical_payload(race())
    assert payload['events']
    assert all(e['counts']['analytical'] and not e['counts']['on_track'] and e['location'] is None for e in payload['events'])
    event=next(e for e in payload['events'] if e['lap']==5)
    assert event['type']=='pitstopwisseling' and event['pit_context'][0]['source_duration']==22
    assert 'lane_duration' not in event['pit_context'][0]
    assert payload['explorer']['sector_count']==1
    assert payload['explorer']['heat_resolution']=='lap'
    assert len(payload['explorer']['sectors'])==14


def test_pit_cycle_requires_complete_times_and_clean_window():
    source=race();payload=historical_payload(source)
    assert len(payload['cycles'])==1 and payload['cycles'][0]['inferred']
    source['drivers'][0]['laps'][1]['seconds']=None
    assert historical_payload(source)['cycles']==[]
    source=race();source['drivers'][0]['laps'][2]['seconds']=1500
    assert historical_payload(source)['cycles']==[]
    source=race();source['timing']={'laps':[{'number':1,'lap':4,'track_status':'4'}]}
    assert historical_payload(source)['cycles']==[]


def test_shared_car_numbers_do_not_merge_drivers():
    source=race();source['drivers'][1]['number']=1
    payload=historical_payload(source)
    assert len({d['driver_number'] for d in payload['drivers']})==2
    assert [d['display_number'] for d in payload['drivers']]==[1,1]
    assert len({p['driver'] for p in payload['positions']})==2


def test_missing_times_do_not_create_a_synthetic_heatmap():
    source=race()
    for d in source['drivers']:
        for row in d['laps']:row['seconds']=None
    payload=historical_payload(source)
    assert payload['explorer']['heat_available'] is False
    assert payload['all_laps']==[] and payload['explorer']['sectors']==[]
    assert payload['cycles']==[]


def test_sparse_history_omits_entire_unsupported_modules(tmp_path):
    source=race()
    for d in source['drivers']:d['laps']=d['laps'][:1]
    run=tmp_path/'analyses/1995/test/runs/one';run.mkdir(parents=True)
    text='<script id="archive-data" type="application/json">'+json.dumps(source)+'</script>'
    output=modernize(text,run/'overzicht.html',tmp_path)
    assert 'id="section-mapchart"' not in output
    assert 'id="section-positions"' not in output
    assert 'id="section-lapchart"' not in output
    assert 'id="section-firstlap"' in output
    assert 'id="archive-data"' in output
    assert 'data-historical-dashboard' in output
    assert (run/'exports/historical-events.json').exists()
    assert source==json.loads(output.split('<script id="archive-data" type="application/json">')[1].split('</script>')[0])


def test_retired_driver_ends_at_last_observation():
    source=race();driver=source['drivers'][1];driver['classified']=False;driver['laps']=driver['laps'][:3];driver['completed_laps']=3
    payload=historical_payload(source)
    assert max(p['lap'] for p in payload['positions'] if p['driver']==2)==3
    assert next(f for f in payload['explorer']['sector_standings'] if f['driver']==2 and f['step']==12)['inactive']
