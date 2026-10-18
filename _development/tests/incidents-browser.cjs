const {chromium}=require('playwright');const fs=require('node:fs'),assert=require('node:assert/strict');
const base='http://127.0.0.1:8798/',out='storage/incident-recheck-20261017';
(async()=>{const browser=await chromium.launch({headless:true}),report=[];
async function run(driver,from,to,{width=1440,lang='nl',local=false}={}){
 console.log('Start',driver,from,width,lang,local);
 const ctx=await browser.newContext({viewport:{width,height:1100},reducedMotion:'reduce'}),p=await ctx.newPage(),errors=[],failed=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400)failed.push(r.url())});
 await p.addInitScript(l=>localStorage.setItem('overtake-it-away-language',l),lang);
 const url=(local?'file://'+process.cwd()+'/':base)+'coureurs_2.html#driver='+driver+'&yearMin='+from+'&yearMax='+to+'&lang='+lang;
 p.setDefaultTimeout(30000);await p.goto(url);console.log('Navigated',driver);await p.waitForFunction(()=>!!window.phase2Lab&&!!document.querySelector('#driver-incidents'),{},{timeout:120000});
 await p.locator('#preseason-enter').click({timeout:1500}).catch(()=>{});await p.evaluate(()=>document.querySelectorAll('dialog[open]').forEach(x=>x.close()));console.log('Ready',driver);
 const summary=await p.evaluate(()=>{const state=phase2Lab.state,driver=phase2Data.drivers.find(d=>d.id===state.driver),s=phase2Research.incidentSummary({driver,rows:driver.races,state});return{
 driver:driver.id,from:state.yearMin,to:state.yearMax,retirements:s.retired.length,counts:s.counts,unknown:s.unknown.length,
 events:s.retired.map(r=>({race:r.race,reason:r.reason,status:r.status})),
 penalties:s.penalties.map(d=>({id:d.id,race:d.race,seconds:d.time_penalty_seconds})),
 decisions:s.decisions.map(d=>({id:d.id,race:d.race,role:d.role,outcome:d.effective_outcome,review:d.reviewed_responsibility?.degree,rows:d.sanction_rows})),
 responsible:s.responsible.length,classificationPenalties:s.classified.length,notStarted:s.notStarted.length,disqualified:s.disqualified.length};});
 assert.equal(summary.driver,driver);assert.equal(summary.from,from);assert.equal(summary.to,to);
 await p.locator('#driver-incidents').scrollIntoViewIfNeeded();
 if(driver==='nico-rosberg'&&from===2016){assert.equal(summary.retirements,1);assert.equal(summary.counts.incident,1);assert.equal(summary.classificationPenalties,3);const doc=summary.decisions.find(d=>d.id==='fia-410c4679b7dceb49e8aa');assert.equal(doc.outcome,'no_further_action');assert.equal(doc.review,'neither_predominant');assert.ok(!summary.penalties.some(d=>d.id===doc.id));await p.locator('#driver-incidents > details').first().evaluate(x=>x.open=true);assert.ok((await p.locator('#driver-incidents').innerText()).includes('2016'));}
 if(driver==='nico-rosberg'&&from===1950)assert.equal(summary.retirements,32);
 if(driver==='lewis-hamilton'&&from===2016){assert.ok(summary.events.some(r=>r.race==='2016-5'));assert.ok(summary.events.some(r=>r.race==='2016-16'&&r.reason==='Engine'));}
 if(driver==='daniel-ricciardo'){const doc=summary.decisions.find(d=>d.id==='fia-1177c73c1df084e84bd3');assert.equal(doc.role,'involved');assert.ok(!summary.penalties.some(d=>d.id===doc.id));}
 if(driver==='esteban-ocon'){const doc=summary.penalties.find(d=>d.id==='fia-17bc9c0f66437cc9af57');assert.equal(doc.seconds,30);}
 if(driver==='juan-fangio')assert.equal(summary.penalties.length,0);
 const overflow=await p.evaluate(()=>document.documentElement.scrollWidth-innerWidth);assert.ok(overflow<=2,'No page overflow');assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 await p.screenshot({path:out+'/'+driver+'-'+from+'-'+width+'-'+lang+(local?'-file':'')+'.png'});
 report.push({...summary,local,width,lang,errors,failed,overflow});await ctx.close();
}
await run('nico-rosberg',2016,2016);await run('nico-rosberg',1950,2026);await run('lewis-hamilton',2016,2016,{lang:'en'});
await run('daniel-ricciardo',2024,2024);await run('esteban-ocon',2023,2023,{lang:'en'});
await run('juan-fangio',1950,2026);await run('nico-rosberg',2016,2016,{width:390,lang:'en'});await run('nico-rosberg',2016,2016,{local:true});
fs.writeFileSync(out+'/browser-report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report.map(({events,penalties,decisions,...r})=>({...r,penalties:penalties.length,decisions:decisions.length})),null,2));
})().catch(e=>{console.error(e);process.exit(1)});
