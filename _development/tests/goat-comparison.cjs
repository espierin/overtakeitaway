const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),vm=require('node:vm'),zlib=require('node:zlib');
const context={window:{},URLSearchParams,Map,Set,Number,Math};vm.createContext(context);
for(const file of ['_development/data/profiles.js','_development/data/facts.js','_development/data/models.js','_development/data/goat-metrics.js','_development/assets/driver-field.js','_development/assets/goat-parameters.js','_development/assets/goat-rankings.js','_development/assets/goat-ai.js'])vm.runInContext(fs.readFileSync(file,'utf8'),context);
const w=context.window,D=w.phase2Data;if(D.driver_race_columns)for(const d of D.drivers)d.races=d.races.map(row=>Object.fromEntries(D.driver_race_columns.map((k,i)=>[k,row[i]])));
const ids=['max-verstappen','lewis-hamilton','juan-fangio','ayrton-senna'],drivers=new Map(D.drivers.map(d=>[d.id,d]));
for(const id of ids)w.goatParameters.cache.set(id,JSON.parse(zlib.gunzipSync(fs.readFileSync(w.phase2GoatMetrics.delivery+id+'.json.gz'))));
const options={data:D,facts:w.phase2Facts,models:w.phase2Models,ids,drivers,state:{from:1950,to:2026,curveyears:'career',circuitdetail:'hungaroring-3',cohort:'shared'},lang:'nl'};
test('curve domain clips both ends and retains interior estimates without mutating saved fit',()=>{
 const c={groups:[{position:2,n:1},{position:10,n:3},{position:13,n:0}],fit:{runs:[Array.from({length:14},(_,i)=>[i+1,i,0,i+2])]}};
 const before=JSON.stringify(c),run=w.goatParameters.boundedCurveRuns(c,'start').flat();assert.equal(run[0][0],2);assert.equal(run.at(-1)[0],10);assert.ok(run.some(p=>p[0]===5));assert.equal(JSON.stringify(c),before);
 assert.equal(w.goatParameters.boundedCurveRuns({groups:[],fit:c.fit},'race').length,0);
});
test('real exported curves stay within measured origin range and exact archived values',()=>{
 const before=JSON.stringify([...w.goatParameters.cache]),brief=w.goatAI.snapshot({...options,complete:true});
 for(const d of brief.drivers)for(const key of ['start','race']){
  const c=d.curves[key],source=w.goatParameters.cache.get(d.id).curves[key];if(!c.observed_position_range)continue;
  for(const point of c.displayed_fit_runs.flat()){assert.ok(point[0]>=c.observed_position_range[0]&&point[0]<=c.observed_position_range[1]);assert.ok(source.fit.runs.flat().some(p=>JSON.stringify(p)===JSON.stringify(point)));}
 }
 assert.equal(JSON.stringify([...w.goatParameters.cache]),before);
});
test('circuit metronome uses every retained lap rank and is independent of selected peers',()=>{
 const e=w.goatParameters.circuitEntries(ids,'hungaroring-3'),single=w.goatParameters.circuitEntries([ids[0]],'hungaroring-3')[0];assert.equal(JSON.stringify(e[0]),JSON.stringify(single));
 const circuit=w.goatParameters.cache.get(ids[0]).record.circuits.find(c=>c.layout==='hungaroring-3');assert.equal(e[0].n,circuit.races.reduce((n,r)=>n+r.laps.length,0));assert.equal(e[0].median,circuit.summary.median_rank);assert.equal(e.find(x=>x.id==='juan-fangio').n,0);
});
test('AI brief preserves periods, missing historical measurements and failed network validation',()=>{
 const brief=w.goatAI.snapshot({...options,state:{...options.state,from:2022,to:2026}}),fangio=brief.drivers.find(d=>d.id==='juan-fangio');
 assert.equal(fangio.career_totals.starts,null);assert.equal(fangio.debut,1950);assert.equal(brief.network_validation.passes,false);assert.equal(brief.drivers.length,4);
 const text=w.goatAI.prompt(options);assert.ok(text.includes('voorlopige winnaar'));assert.ok(text.includes('nooit nul'));assert.ok(text.includes('dezelfde onderdelen en gewichten'));
});
test('rankings expose measured coverage and do not treat zero wins as missing',()=>{
 const result=w.goatRankings.calculate(options);assert.equal(result.measured,786);assert.equal(result.pool.length,4);assert.ok(result.pool.every(r=>r.starts>=20));assert.ok(result.pool[0].value>=result.pool.at(-1).value);
 const wallard=w.goatRankings.calculate({...options,ids:['lee-wallard']});assert.equal(wallard.pool.length,0);assert.equal(wallard.omitted[0].id,'lee-wallard');
 const all=w.goatRankings.calculate({...options,state:{...options.state,rankingScope:'all',rankingMinimum:0}});assert.ok(all.pool.some(r=>r.value===0));assert.equal(all.pool.length,786);
});
