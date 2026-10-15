import json
from pathlib import Path
from f1_analysis.championship import before_reference, with_defaults, decorate


def test_before_race_uses_previous_final_and_previous_round_not_current_result():
    tables={'races':[{'year':'2025','round':'1','date':'2025-03-16'},{'year':'2025','round':'2','date':'2025-03-23'}],
            'seasons-driver-standings':[{'year':'2024','driverId':d,'positionDisplayOrder':str(i)} for i,d in enumerate(['max','lando','charles'],1)],
            'races-driver-standings':[{'year':'2025','round':'1','driverId':d,'positionDisplayOrder':str(i),'points':'25'} for i,d in enumerate(['lando','max','george'],1)]}
    result=before_reference(lambda key:tables.get(key,[]))
    assert result['2025-03-16']['drivers']==['max','lando','charles']
    assert result['2025-03-23']['drivers']==['lando','max','george']


def test_sprint_points_are_included_before_the_grand_prix():
    tables={'races':[{'year':'2025','round':'2','date':'2025-03-23'}],
            'races-driver-standings':[{'year':'2025','round':'1','driverId':d,'positionDisplayOrder':str(i),'points':str(p)} for i,(d,p) in enumerate([('a',20),('b',18),('c',15),('d',14)],1)],
            'races-sprint-race-results':[{'year':'2025','round':'2','driverId':'d','points':'8'}]}
    result=before_reference(lambda key:tables.get(key,[]))['2025-03-23']
    assert result['drivers']==['d','a','b']
    assert result['source_stage']=='after-sprint'


def test_stored_defaults_preserve_all_observations_and_resolve_driver_names(tmp_path):
    assets=tmp_path/'assets';assets.mkdir()
    ref={'source':'https://github.com/f1db/f1db','drivers':{'max':{'name':'Max Verstappen','code':'VER'},'charles':{'name':'Charles Leclerc','code':'LEC'}},
         'championship_before':{'2025-03-16':{'year':2025,'round':1,'source_year':2024,'source_round':None,'drivers':['max','charles']}}}
    (assets/'catalogue-search-reference.json').write_text(json.dumps(ref))
    payload={'year':2025,'drivers':[{'driver_number':1,'name':'Max VERSTAPPEN','code':'VER'},{'driver_number':16,'name':'Charles LECLERC','code':'LEC'}],'explorer':{'sectors':[{'lap':1,'duration':23.5}]}}
    updated=with_defaults(payload,'2025-03-16',tmp_path)
    assert updated['championship_before']['drivers']==[1,16]
    assert {k:v for k,v in updated.items() if k!='championship_before'}==payload
    page='<time datetime="2025-03-16" data-race-date></time><script id="dashboard-data" type="application/json">'+json.dumps(payload)+'</script>'
    result=decorate(page,tmp_path)
    assert decorate(result,tmp_path)==result
    assert json.dumps(23.5) in result
    assert with_defaults(payload,'1900-01-01',tmp_path)==payload
