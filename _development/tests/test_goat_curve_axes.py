"""The career view shifts only the time axis of the archived seasonal fits."""
import shutil
import subprocess


def test_career_years_align_debuts_preserve_breaks_and_leave_archives_untouched():
    node=shutil.which('node') or '/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    script=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const window={phase2Research:{esc:String,fmt:String},
 qualifyingYears:{positionAnchors:()=>[1,22],positionScale:v=>(v-1)/21,timeScale:v=>v/4,smoothPath:ps=>ps.map(p=>p.join(',')).join('L')},
 driverQualities:{starterScalePosition:v=>v/10},pitProgrammes:{seasonAxis:()=>({max:100,ticks:[-100,0,100]}),seasonScale:v=>v/100}};
vm.runInNewContext(fs.readFileSync('_development/assets/goat-parameters.js','utf8'),{window});
const api=window.goatParameters,ids=['max','fangio'],drivers=new Map(ids.map((id,i)=>[id,{id,name:id,code:id,number:1,color:'#3366cc',races:[{year:i?1950:2015},{year:i?1953:2018}]}]));
for(const id of ids){const first=id==='max'?2015:1950,annual={axis:{y:{max:22}},groups:[],fit:{runs:[[[first,2,1,3,false],[first+.4,3,2,4,false]],[[first+3,4,3,5,false]]]}},position={fit:{runs:[[[1,0,-1,1,false],[2,1,0,2,false]]]}};api.cache.set(id,{curves:{start:position,race:position,qualifying_position:annual,gap_to_pole:annual,pit_balance:annual}});}
const archived=JSON.stringify([...api.cache]),options={ids,drivers,lang:'nl'},calendar=api.curves({...options,state:{curveyears:'calendar'}}),career=api.curves({...options,state:{curveyears:'career'}});
const paths=(html,key)=>[...html.matchAll(new RegExp('data-goat-curve="'+key+'" data-driver="([^"]+)" d="([^"]*)"','g'))].map(m=>({id:m[1],d:m[2]}));
for(const key of ['start','race'])assert.deepEqual(paths(calendar,key),paths(career,key));
for(const key of ['qualifying_position','gap_to_pole','pit_balance']){
 const rows=paths(career,key),max=rows.filter(p=>p.id==='max'),fangio=rows.filter(p=>p.id==='fangio');
 assert.equal(max.length,2);assert.equal(fangio.length,2); // The three-year gap stays split.
 for(let i=0;i<max.length;i++){const a=max[i].d.split(/[L,]/).map(Number),b=fangio[i].d.split(/[L,]/).map(Number);assert.equal(a.length,b.length);assert.ok(a.every((v,j)=>Math.abs(v-b[j])<1e-8));}
 assert.notEqual(paths(calendar,key)[0].d,paths(calendar,key).find(p=>p.id==='fangio').d);
}
assert.equal(JSON.stringify([...api.cache]),archived);
assert.ok(career.includes('data-curve-years="career" aria-pressed="true"'));
assert.ok(calendar.includes('data-curve-years="calendar" aria-pressed="true"'));
const patterns=api.curvePatterns(['max','ham','ric'],id=>({color:{max:'#3671c6',ham:'#e8002d',ric:'#6692ff'}[id]}));
assert.equal(patterns.get('max'),'');assert.equal(patterns.get('ham'),'');assert.equal(patterns.get('ric'),'7 4');
'''
    subprocess.run([node,'-'],input=script,text=True,check=True,timeout=15)
