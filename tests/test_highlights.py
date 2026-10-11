from f1_analysis.highlights import facts

def row(number,position,grid,time=None,rank=None,laps='50'):
 r={'number':str(number),'position':str(position),'positionText':str(position),'grid':str(grid),'laps':laps,'Driver':{'givenName':'Driver','familyName':str(number)}}
 if time is not None:r['Time']={'time':time}
 if rank is not None:r['FastestLap']={'rank':str(rank),'lap':'20','Time':{'time':'1:20.123'}}
 return r

def test_facts_preserve_winner_fastest_and_margin():
 f=facts({'jolpica_results':[row(1,1,4,'1:10:00',2),row(2,2,1,'+2.345',1)]})
 assert f['winner']['number']==1 and f['pole']['number']==2
 assert f['fastest']['number']==2 and f['margin']==2.345
 assert f['gainers'][0]['gain']==3

def test_missing_facts_are_absent():
 assert facts({})=={}
 assert 'margin' not in facts({'jolpica_results':[row(1,1,0),row(2,2,0)]})

def test_lapped_runner_up_has_no_time_margin():
 assert 'margin' not in facts({'jolpica_results':[row(1,1,1,'1:10:00'),row(2,2,2,'+1 Lap',laps='49')]})

def test_equal_gains_show_all_and_pitlane_is_excluded():
 f=facts({'jolpica_results':[row(1,1,4),row(2,2,5),row(3,3,0)]})
 assert [d['number'] for d in f['gainers']]==[1,2]

def test_unknown_fastest_not_inferred_from_incomplete_laps():
 assert 'fastest' not in facts({'jolpica_results':[row(1,1,1)]})


def test_primary_classification_fills_race_facts_when_jolpica_is_delayed():
 data={'jolpica_results':[], 'drivers':[{'driver_number':1,'full_name':'One','name_acronym':'ONE','team_colour':'00ffff'}, {'driver_number':2,'full_name':'Two','name_acronym':'TWO','team_colour':'ff0000'}],
       'starting_grid':[{'driver_number':1,'position':3},{'driver_number':2,'position':1}],
       'session_result':[{'driver_number':1,'position':1,'number_of_laps':2,'duration':180.}, {'driver_number':2,'position':2,'number_of_laps':2,'duration':183.5}],
       'laps':[{'driver_number':n,'lap_number':lap,'lap_duration':v} for n,lap,v in [(1,1,91.),(1,2,89.),(2,1,90.),(2,2,93.5)]]}
 f=facts(data)
 assert f['winner']['number']==1 and f['pole']['number']==2 and f['gainers'][0]['gain']==2
 assert f['margin']==3.5 and f['fastest']['fastest_time']=='1:29.000'
 data['laps'].pop()
 assert 'fastest' not in facts(data)


def test_primary_results_do_not_override_supplementary_official_facts():
 data={'jolpica_results':[row(1,1,1,'1:10:00',1)],'session_result':[{'driver_number':1,'position':2,'number_of_laps':50}]}
 assert facts(data)['winner']['number']==1


def test_publication_fills_existing_dashboard_facts_without_replacing_known_values():
 import json,re
 from f1_analysis.publication import with_primary_race_facts
 payload={'drivers':[{'driver_number':1,'name':'One','code':'ONE','grid':2,'result':{'position':1,'number_of_laps':1,'duration':90.}}],
          'styles':{'1':{'color':'#abcdef'}},'all_laps':[{'driver':1,'lap':1,'duration':90.}],
          'highlights':{'pole_margin':0.25}}
 text='<script id="dashboard-data">'+json.dumps(payload)+'</script>'
 repaired=with_primary_race_facts(text)
 facts=json.loads(re.search(r'>(.*?)</script>',repaired)[1])['highlights']
 assert facts['winner']['number']==1 and facts['fastest']['fastest_lap']==1
 assert facts['gainers'][0]['gain']==1 and facts['pole_margin']==0.25
 assert with_primary_race_facts(repaired)==repaired
