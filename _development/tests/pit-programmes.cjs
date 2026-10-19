const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const scope={window:{}};vm.createContext(scope);vm.runInContext(fs.readFileSync('_development/assets/pit-programmes.js','utf8'),scope);const api=scope.window.pitProgrammes;
function clocks(n,stops,delay){let total=0;const elapsed=[0],times=[null],positions=[null];for(let lap=1;lap<=24;lap++){const ms=90000+(stops.includes(lap)?delay:0);times.push(ms);elapsed.push(total+=ms);positions.push(n);}return{n,stops,elapsed,times,positions,lapTime:90000,laps:24};}
test('local completed cycles preserve a valid early measurement when a later SC invalidates the programme',()=>{
 const a=clocks(1,[5,17],20000),b=clocks(2,[6,18],24000);b.elapsed=b.elapsed.map(t=>t+30000);
 const race={pit_programmes:{flags:[[17,1]]}};assert.equal(api.compare(race,a,b).reason,'neutralisation');const cycles=api.pairedCycles(race,a,b);assert.equal(cycles[0].gain,4);assert.equal(cycles[0].before,4);assert.equal(cycles[0].after,7);assert.equal(cycles[1].reason,'neutralisation');
 const marked=api.pairedCycles(race,a,b,true);assert.equal(marked[1].gain,4);assert.equal(marked[1].neutral,true);
});
test('cycles reject overlapping stops and unequal full-race programmes',()=>{
 const a=clocks(1,[5,8],20000),b=clocks(2,[9,15],24000);b.elapsed=b.elapsed.map(t=>t+30000);
 assert.equal(api.pairedCycles({pit_programmes:{}},a,b)[0].reason,'overlapping_cycles');assert.equal(api.pairedCycles({pit_programmes:{}},a,clocks(2,[6],24000))[0].reason,'stop_count_mismatch');
});
test('red flags, missing endpoints and lap differences remain excluded in cycle mode',()=>{
 const a=clocks(1,[5],20000),b=clocks(2,[6],24000);b.elapsed=b.elapsed.map(t=>t+30000);
 assert.equal(api.pairedCycles({pit_programmes:{flags:[[6,2]]}},a,b,true)[0].reason,'red_flag');assert.equal(api.pairedCycles({pit_programmes:{}},{...a,laps:5},b)[0].reason,'window_coverage');b.elapsed=b.elapsed.map(t=>t+90000);assert.equal(api.pairedCycles({pit_programmes:{}},a,b)[0].reason,'lap_or_clock');
});
test('season and overall aggregation give each race one observation, independent of its opponent count',()=>{
 const rows=[{race:{year:2020},median:10,points:Array(20).fill({gain:10})},{race:{year:2020},median:-2,points:[{gain:-2}]},{race:{year:2020},median:null,points:[]},{race:{year:2021},median:null,points:[]}],s=api.seasons(rows);
 assert.equal(s.length,2);assert.equal(s[0].median,4);assert.equal(s[0].measured.length,2);assert.equal(s[0].comparisons,21);assert.equal(s[0].rows.length,3);assert.equal(s[1].median,null);assert.equal(s[1].measured.length,0);
});
test('season axis is symmetric and nonlinear while retaining every signed second',()=>{
 const axis=api.seasonAxis([-47,0,.01,13]);
 assert.equal(axis.min,-100);assert.equal(axis.max,100);
 assert.equal(api.seasonScale(0,100),0);
 assert.equal(api.seasonScale(100,100),1);assert.equal(api.seasonScale(-100,100),-1);
 assert.equal(api.seasonScale(-3,100),-api.seasonScale(3,100));
 assert.ok(api.seasonScale(1,100)>api.seasonScale(31,100)-api.seasonScale(30,100));
 const values=[-47,0,.01,13];assert.ok(values.every((v,i)=>!i||api.seasonScale(v,100)>api.seasonScale(values[i-1],100)));
});
test('archived pit curve preserves the exact production trend, race values and missing years',()=>{
 vm.runInContext(fs.readFileSync('_development/assets/qualifying-years.js','utf8'),scope);
 const rows=[2019,2020,2022].flatMap(year=>Array.from({length:7},(_,i)=>({race:{id:year+'-'+i,year,date:year+'-06-'+String(i+1).padStart(2,'0'),name:'Example'},median:year===2020?i-3:i/2,points:[{gain:i}]})));
 rows.push({race:{id:'missing',year:2021},median:null,points:[]});
 const before=JSON.stringify(rows),snapshot=api.seasonSnapshot(rows),direct=api.seasonTrend(rows);
 assert.equal(snapshot.measured,21);assert.equal(snapshot.fit.runs.length,2);
 assert.equal(snapshot.groups.find(g=>g.year===2021).n,0);
 assert.equal(JSON.stringify(snapshot.fit.runs),JSON.stringify(direct.map(run=>run.map(p=>[p.year,p.value,p.lo,p.hi,p.sparse]))));
 assert.equal(JSON.stringify(rows),before);
 assert.deepEqual(Array.from(snapshot.groups.flatMap(g=>g.observations.map(o=>o.value))).sort((a,b)=>a-b),rows.filter(r=>r.median!==null).map(r=>r.median).sort((a,b)=>a-b));
 assert.equal(JSON.stringify(api.completeSeasonSnapshot(api.seasonSnapshot(rows,{includeFit:false}))),JSON.stringify(snapshot));
 const html=api.seasonChart(rows,'nl');assert.ok(html.includes('data-y-scale="signed_log1p"'));assert.ok(!html.includes('NaN'));
});
