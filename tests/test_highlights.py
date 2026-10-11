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
