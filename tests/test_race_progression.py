import subprocess
import pytest
from f1_analysis.phase2 import finish_evidence


@pytest.mark.parametrize('status',['Finished','finished','+1 Lap','+3 Laps','Lapped'])
def test_explicit_finish_includes_lapped_finishers(status):
    assert finish_evidence({'status':status,'result':{'number_of_laps':54}})=={'finished_on_track':True,'finish_status':status,'finish_laps':54}


@pytest.mark.parametrize('driver',[
    {'status':'Engine','classified':True,'result':{'position':15,'number_of_laps':60}},
    {'status':'Finished','result':{'dnf':True,'number_of_laps':60}},
    {'result':{'dnf':False,'dsq':True}},
    {'result':{'dnf':False,'dns':True}},
])
def test_classification_and_final_lap_retirements_do_not_prove_a_finish(driver):
    assert finish_evidence(driver)['finished_on_track'] is False


def test_missing_status_is_unknown_even_with_a_classification_and_full_distance():
    assert finish_evidence({'classified':True,'result':{'position':10,'number_of_laps':60}})['finished_on_track'] is None
    assert finish_evidence({'status':'Unknown'})['finished_on_track'] is None
    assert finish_evidence({'result':{'dnf':False,'number_of_laps':59}})['finished_on_track'] is True


def test_race_phase_uses_lap_one_origins_finishers_only_and_the_same_estimators():
    script=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),window={};
vm.runInNewContext(fs.readFileSync('src/f1_analysis/driver-qualities.js','utf8'),{window});
const Q=window.driverQualities,row=(race,origin,finish,extra={})=>({race,grid:1,lap1_position:origin,finish,finished_on_track:true,finish_laps:55,...extra});
assert.equal(Q.raceObservation(row('x',8,6,{pitlane_start:true})).grid,8);
for(const extra of [{finished_on_track:false},{finished_on_track:null},{finished_on_track:undefined},{dnf:true},{dsq:true},{dns:true},{finish_laps:1},{finish:0},{lap1_position:null}])assert.equal(Q.raceObservation(row('x',8,6,extra)),null);
const own={id:'own',name:'Own',code:'OWN',races:[row('one',8,6),row('retired',8,2,{dnf:true,finished_on_track:false}),row('unknown',8,1,{finished_on_track:null})]},b={id:'b',races:[row('two',8,8,{grid:15}),row('three',8,5,{grid:20}),row('bad',8,20,{finished_on_track:false}),row('unclear',8,20,{finished_on_track:null}),row('different-position',12,20,{grid:8}),row('different-circuit',8,20),row('different-field',8,20),row('one',8,20)]};
const ids=[...own.races,...b.races].map(r=>r.race),data={drivers:[own,b],races:[...new Set(ids)].map(id=>({id,year:2020,circuit_id:id==='different-circuit'?'other':'track',drivers:id==='different-field'?22:20,href:'race.html',name:id}))};
const options={data,driver:own,rows:own.races,state:{},iterations:40,minReference:2,minStarts:1,observation:Q.raceObservation},a=Q.startComparison(options);
assert.equal(a.own,1);assert.equal(a.matched.length,1);assert.equal(a.referenceRaces,2);assert.equal(a.score,50);assert.equal(a.matched[0].obs.grid,8);assert.equal(a.matched[0].obs.lap1,6);
// Transform a fixture only: the same observations through the original Starter
// estimator must produce numerically identical scores, curves and bootstrap bands.
const mapped={...data,drivers:data.drivers.map(d=>({...d,races:d.races.map(r=>({...r,pitlane_start:false,qualities:{start:Q.raceObservation(r)?[Q.raceObservation(r)]:[]}}))}))};
const legacy=Q.startComparison({...options,data:mapped,driver:mapped.drivers[0],rows:mapped.drivers[0].races,observation:undefined});
for(const key of ['score','interval','gridNodes','adjustedCurve'])assert.equal(JSON.stringify(a[key]),JSON.stringify(legacy[key]));
assert.equal(Q.startComparison({...options,state:{yearMin:2021}}).own,0);
const groups=Q.startGroups(own.races,Q.raceObservation);assert.equal(groups.length,1);assert.equal(groups[0].grid,8);assert.equal(groups[0].median,6);
'''
    subprocess.run(['node','-e',script],check=True,timeout=20)
