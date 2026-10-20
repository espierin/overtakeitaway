const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),vm=require('node:vm'),zlib=require('node:zlib');
const context={window:{},URLSearchParams,Map,Set,Number,Math};vm.createContext(context);
for(const file of ['_development/data/profiles.js','_development/data/facts.js','_development/data/models.js','_development/data/goat-metrics.js','_development/assets/driver-names.js','_development/assets/driver-field.js','_development/assets/goat-parameters.js','_development/assets/goat-rankings.js','_development/assets/goat-ai-contract.js','_development/assets/goat-ai-format.js','_development/assets/goat-ai.js'])vm.runInContext(fs.readFileSync(file,'utf8'),context);
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

test('circuit picker combines Barcelona variants and all-circuit default includes every own lap',()=>{
 const all=w.goatParameters.circuitSelection({...options,state:{...options.state,circuitdetail:''}});assert.equal(all.selected.length,0);assert.equal(all.choices.filter(c=>c.key==='catalunya').length,1);
 const variants=w.goatParameters.cache.get(ids[0]).record.circuits.filter(c=>c.circuit_id==='catalunya');assert.ok(variants.length>1);
 const combined=w.goatParameters.circuitEntries([ids[0]],['catalunya'])[0];assert.equal(combined.n,variants.reduce((n,c)=>n+c.summary.laps,0));
 const legacy=w.goatParameters.circuitSelection({...options,state:{...options.state,circuitdetail:'imola-3'}});assert.equal(legacy.selected.join(','),'imola');
 assert.equal(w.goatParameters.circuitEntries([ids[0]])[0].n,w.goatParameters.cache.get(ids[0]).record.features.metronome_rank.n);
});

test('Gemini reuses the exact prompt for the same combination in another order',()=>{
 const text=w.goatAI.prompt(options),reverse=w.goatAI.prompt({...options,ids:[...ids].reverse()});assert.equal(text,reverse);
 assert.notEqual(text,w.goatAI.prompt({...options,state:{...options.state,from:2000}}));
 assert.notEqual(text,w.goatAI.prompt({...options,lang:'en'}));
 assert.ok(text.includes('tempo 30%'));assert.ok(!text.includes('gelijke gewichten voor vergelijkbare onderdelen'));
 const a=w.goatAI.prompt({...options,state:{...options.state,circuitdetail:'imola,catalunya'}}),b=w.goatAI.prompt({...options,state:{...options.state,circuitdetail:'catalunya,imola'}});assert.equal(a,b);
});

test('simplified AI section keeps only downloads and the requested title',()=>{
 const html=w.goatAI.render(options);assert.ok(html.includes('The Answer to the Ultimate Question'));assert.ok(html.includes('goat-info-svg'));assert.ok(html.includes('goat-info-png'));assert.ok(html.includes('Stel de vraag'));assert.ok(html.includes('42'));
 for(const removed of ['goat-ai-import','goat-ai-copy','goat-ai-refresh','textarea','Maak een vraag'])assert.ok(!html.includes(removed));
});

test('median uncertainty resamples whole races and breaks median ties by interval width',()=>{
 const api=w.driverField,one=[{race:'one',values:[1,2,3]}];assert.equal(api.medianInterval(one),null);
 const repeated=Array.from({length:20},(_,i)=>({race:'r'+i,values:Array(30).fill(2)}));assert.equal(JSON.stringify(api.medianInterval(repeated)),'[2,2]');
 const broad=[{race:'a',values:Array(200).fill(1)},{race:'b',values:Array(200).fill(5)}],before=JSON.stringify(broad),interval=api.medianInterval(broad);assert.equal(JSON.stringify(interval),'[1,5]');assert.equal(JSON.stringify(broad),before);
 const rows=[{id:'unknown',median:3,median_interval:null},{id:'broad',median:3,median_interval:[1,5]},{id:'narrow',median:3,median_interval:[2.5,3.5]},{id:'fast',median:2,median_interval:[1,8]}];rows.sort(api.medianOrder);assert.equal(rows.map(r=>r.id).join(','),'fast,narrow,broad,unknown');
});

test('driver display names normalize uppercase surnames and preserve initials',()=>{
 assert.equal(w.driverNames.display('Kimi ANTONELLI'),'Kimi Antonelli');assert.equal(w.driverNames.display('Oscar PIASTRI'),'Oscar Piastri');assert.equal(w.driverNames.display("Pat O’BRIEN"),'Pat O’Brien');assert.equal(w.driverNames.display('A.J. Foyt III'),'A.J. Foyt III');
 assert.equal(w.driverNames.key({id:'guanyu-zhou',name:'Zhou Guanyu'}),'Zhou');
 const sorted=w.driverNames.sort(D.drivers);assert.equal(sorted.length,817);assert.equal(new Set(sorted.map(d=>d.id)).size,817);assert.ok(sorted.every(d=>!d.name.split(/\s+/).some(part=>part.length>2&&part===part.toUpperCase())));
});

test('shared assessment excludes missing Schumacher scores for everyone',()=>{
 const modern=['lewis-hamilton','max-verstappen','sebastian-vettel','michael-schumacher'];for(const id of modern)if(!w.goatParameters.cache.has(id))w.goatParameters.cache.set(id,JSON.parse(zlib.gunzipSync(fs.readFileSync(w.phase2GoatMetrics.delivery+id+'.json.gz'))));
 const brief=w.goatAI.snapshot({...options,ids:modern}),byId=new Map(brief.assessment_plan.domains.map(d=>[d.id,d]));assert.equal(byId.get('start').included_in_verdict,false);assert.equal(byId.get('progression').included_in_verdict,false);assert.ok(!brief.assessment_plan.allowed_evidence.includes('features.metronome'));assert.ok(brief.assessment_plan.allowed_evidence.includes('features.teammate_pace'));assert.ok(Math.abs(byId.get('pace').weight-.54)<1e-10);assert.ok(Math.abs(byId.get('qualifying').weight-.36)<1e-10);
});
