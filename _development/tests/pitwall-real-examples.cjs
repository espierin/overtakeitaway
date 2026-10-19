const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
const output='storage/pitwall-examples-v2-20261019';
(async()=>{const browser=await chromium.launch({headless:true}),results=[];
for(const[width,lang,file]of[[1440,'nl',false],[390,'en',false],[320,'nl',true]]){
 const context=await browser.newContext({viewport:{width,height:1100},reducedMotion:'reduce'}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.addInitScript(l=>localStorage.setItem('overtake-it-away-language',l),lang);
 const base=file?'file://'+process.cwd()+'/':'http://127.0.0.1:8798/';await page.goto(base+'analysis-lab.html#driver=max-verstappen');await page.waitForFunction(()=>window.phase2Lab,{},{timeout:120000});await page.evaluate(()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close()));
 assert.equal(await page.locator('#quality-start .starter-facts-metrics').count(),0);assert.equal(await page.locator('.quality-grid .quality-tile').count(),6);assert.equal(await page.locator('.quality-grid .quality-info-wrap>[data-driver-help]').count(),6);assert.equal(await page.locator('#driver-incidents>h2 [data-driver-help]').count(),1);assert.equal(await page.locator('#driver-facts h3 [data-driver-help]').count(),1);
 const originalHash=await page.evaluate(()=>location.hash),texts={},topics=['profile','career','incidents','coverage','start','race','qualifying','teammate','free','metronome','regularity','tyres','pitwindow','warmup','pitbalance'];
 for(const topic of topics){await page.evaluate(topic=>driverInfo.open(topic),topic);await page.waitForSelector('#pitwall-briefing [data-help-example="'+topic+'"]',{timeout:120000});
  if(!['profile','career','incidents','coverage'].includes(topic)){assert.equal(await page.locator('#pitwall-briefing .briefing-real-driver').count(),2,topic);assert.ok(await page.locator('#pitwall-briefing .briefing-production-chart svg').count()>=2,topic);}
  if(topic==='start'){
   const values=await page.locator('#pitwall-briefing .starter-axis').first().locator('[data-value]').evaluateAll(xs=>xs.map(x=>+x.dataset.value));assert.ok(values.includes(-10)&&values.includes(0)&&values.includes(10));assert.ok(await page.locator('#pitwall-briefing .starter-observation').count()>100);
   assert.equal(await page.locator('#pitwall-briefing .starter-axis-position[data-grid="23"]').count(),0);
   const scrolling=await page.evaluate(()=>{const frames=[...document.querySelectorAll('#pitwall-briefing .starter-frame')],axes=frames.map(f=>f.querySelector('.starter-axis').getBoundingClientRect().left);frames[0].querySelector('.starter-scroll').scrollLeft=440;return axes;});await page.waitForTimeout(80);
   const after=await page.evaluate(()=>[...document.querySelectorAll('#pitwall-briefing .starter-frame')].map(f=>({left:f.querySelector('.starter-scroll').scrollLeft,axis:f.querySelector('.starter-axis').getBoundingClientRect().left})));assert.equal(after[0].left,after[1].left);assert.equal(after[0].left,440);assert.deepEqual(after.map(a=>a.axis),scrolling);
   await page.locator('.pitwall-scroll').evaluate(s=>s.scrollTop=550);await page.screenshot({path:output+'/start-'+width+'-'+lang+'.png'});
  }
  if(topic==='qualifying'){assert.equal(await page.locator('#pitwall-briefing .qualifying-years-frame').count(),2);assert.ok(await page.locator('#pitwall-briefing .qualifying-observation').count()>50);}
  texts[topic]=await page.locator('#pitwall-briefing .briefing-shared-content').textContent();await page.locator('.pitwall-close').click();
 }
 assert.equal(await page.evaluate(()=>location.hash),originalHash);
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
 const help=await context.newPage();help.on('pageerror',e=>errors.push(e.message));await help.goto(base+'_development/uitleg-start-en-raceonderzoek.html#start');await help.waitForFunction(()=>window.driverMethods);
 for(const topic of topics){await help.locator('#method-'+topic).click();await help.waitForFunction(topic=>driverMethods.phase===topic,topic);if(topic==='qualifying')await help.waitForSelector('.qualifying-validation tbody tr');assert.equal(await help.locator('.briefing-shared-content').textContent(),texts[topic],topic);}
 assert.ok(await help.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));assert.deepEqual(errors,[]);results.push({width,lang,file,topics:topics.length,realGraphs:true,sharedAxes:true,synchronizedScroll:true,helpParity:true,errors});await context.close();
}
await browser.close();fs.writeFileSync(output+'/browser.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));})().catch(e=>{console.error(e);process.exit(1)});
