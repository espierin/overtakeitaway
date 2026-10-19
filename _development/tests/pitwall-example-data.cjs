const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const context={window:{}};vm.createContext(context);for(const file of ['help/examples','driver-qualities','pit-programmes','qualifying-years','lap-rankings'])vm.runInContext(fs.readFileSync('_development/assets/'+file+'.js','utf8'),context);
const E=context.window.driverHelpExamples,Q=context.window.driverQualities,P=context.window.pitProgrammes,K=context.window.qualifyingYears,L=context.window.lapRankings,D=E.graphData,sort=a=>[...a].sort((a,b)=>a-b),same=(a,b)=>assert.equal(JSON.stringify(sort(a)),JSON.stringify(sort(b)));
for(const[name,hash]of Object.entries(E.inputs))assert.equal(crypto.createHash('sha256').update(fs.readFileSync(name)).digest('hex'),hash);
for(const[topic,e]of Object.entries(E.topics))for(const series of e.series){const driver=D.drivers.find(d=>d.id===series.id),ids=new Set(e.races.flat()),rows=driver.races.filter(r=>r.year>=e.period[0]&&r.year<=e.period[1]&&(['start','race'].includes(topic)||ids.has(r.race)));let values;
 if(['start','race'].includes(topic))values=Q.startGroups(rows,topic==='race'?Q.raceObservation:undefined).find(g=>g.grid===e.grid).starts.map(s=>s.obs.grid-s.obs.lap1);
 else if(topic==='metronome')values=rows.flatMap(r=>L.pointsFor(r,'free','',D.settings.lap_rankings.compounds)).map(p=>p.rank);
 else if(topic==='pitbalance')values=P.model({data:D,driver,rows,state:e.filters}).map(r=>r.median).filter(Number.isFinite);
 else if(topic==='teammate')values=rows.filter(r=>Number.isFinite(r.comparison?.pace_delta_pct)).map(r=>r.comparison.pace_delta_pct);
 else if(topic==='qualifying')values=E.qualifying.records[driver.id].filter(r=>ids.has(r.race)).map(r=>r.qualifying);
 else if(topic==='qualifyinggap')values=K.summarize(E.qualifying.records[driver.id],E.qualifying.poles,{},E.qualifying.bridges).groups.flatMap(g=>g.gaps).filter(p=>ids.has(p.record.race)).map(p=>p.value);
 else values=Q.observations(rows,topic).map(o=>o.value);
 same(values,series.values);
}
console.log('All 12 example datasets reproduce from production selectors; source hashes, individual laps, start eligibility, confirmed finishers, estimated Q3 gaps and direct pit duels verified.');
