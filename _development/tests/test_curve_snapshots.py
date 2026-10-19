from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
NODE='/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


def test_curve_snapshots_preserve_selection_uncertainty_and_unclipped_observations():
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),zlib=require('node:zlib');const ctx={window:{}};vm.createContext(ctx);
for(const name of ['driver-qualities','qualifying-years','driver-curve-snapshots'])vm.runInContext(fs.readFileSync('_development/assets/'+name+'.js','utf8'),ctx);
const rows=Array.from({length:18},(_,i)=>({race:'race-'+i,year:i<9?2020:2021,lap1_position:2+i%6,finish:1+i%6,finished_on_track:true,finish_laps:50,result_outcome:'finished',qualities:{start:[{grid:1+i%6,lap1:2+i%6}]}}));
rows[0].pitlane_start=true;rows[1].source_pitlane_start=true;rows[2].start_eligible=false;rows[3].dnf=true;rows[4].finish_laps=1;rows[5].race_eligible=false;
const data={period:[2020,2021],races:rows.map(r=>({id:r.race,year:r.year,starters:20,drivers:22}))},driver={id:'fixture',name:'Fixture Driver',code:'FIX',number:1,color:'#b45cff',races:rows};
const records=rows.map((r,i)=>({race:r.race,year:r.year,qualifying:1+i%10,qualifying_ms:{q3Millis:i===13?79000:70000+i*100}})),poles=Object.fromEntries(rows.map(r=>[r.race,['q3Millis',70000,'pole']])),bridges={'race-6':[null,[5,-1000]]};records[6].qualifying_ms={q2Millis:73000};records.push({race:'not-entered',year:2020,qualifying:1,qualifying_ms:{q3Millis:70000}});
const before=JSON.stringify({data,driver,records}),snapshot=ctx.window.driverCurveSnapshots.build({data,driver,records,poles,bridges});
assert.deepEqual(Object.keys(snapshot.curves),['start','race','qualifying_position','gap_to_pole']);assert.equal(snapshot.curves.start.measured,15);assert.equal(snapshot.curves.race.measured,15);
const starts=snapshot.curves.start.groups.flatMap(g=>g.observations).map(o=>o[0]),race=snapshot.curves.race.groups.flatMap(g=>g.observations).map(o=>o[0]);assert.ok(!starts.includes('race-0')&&!starts.includes('race-1')&&!starts.includes('race-2'));assert.ok(race.includes('race-0')&&race.includes('race-1')&&!race.includes('race-3')&&!race.includes('race-4')&&!race.includes('race-5'));
for(const key of ['start','race']){const curve=snapshot.curves[key];assert.equal(curve.axis.x.max,22);assert.equal(curve.field_size,20);assert.ok(curve.fit.runs.flat().every(p=>p[0]<=20&&p[2]<=p[3]));assert.ok(curve.fit.runs.flat().some(p=>p[5]));}
assert.equal(snapshot.curves.qualifying_position.measured,18);assert.equal(snapshot.curves.gap_to_pole.estimated,1);assert.equal(snapshot.curves.gap_to_pole.axis.y.max,4);const gaps=snapshot.curves.gap_to_pole.groups.flatMap(g=>g.observations);assert.equal(gaps.find(o=>o.race==='race-13').value,9);assert.equal(gaps.find(o=>o.race==='race-6').value,2);assert.equal(gaps.find(o=>o.race==='race-6').estimated,true);
const filtered=ctx.window.driverCurveSnapshots.build({data,driver,records,poles,bridges,state:{yearMin:2020,yearMax:2020}});assert.equal(filtered.curves.qualifying_position.measured,9);assert.equal(filtered.curves.qualifying_position.groups.length,1);assert.equal(filtered.curves.qualifying_position.groups[0].year,2020);
assert.equal(JSON.stringify({data,driver,records}),before);const json=JSON.stringify(snapshot),decoded=JSON.parse(zlib.gunzipSync(zlib.gzipSync(json)).toString());assert.equal(JSON.stringify(decoded),json);assert.equal(JSON.stringify(ctx.window.driverCurveSnapshots.build({data,driver,records,poles,bridges})),json);
console.log('Four production curves, exact selections, confidence bands, field support, signed/raw values, periods, determinism and lossless round trip: passed');
"""
    result=subprocess.run([NODE,'-e',script],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
