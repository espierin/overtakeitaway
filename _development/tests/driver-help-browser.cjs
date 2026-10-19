const{chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
const output='storage/driver-help-20261019';fs.mkdirSync(output,{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true}),report=[];
for(const[width,lang,local]of[[1440,'nl',false],[390,'en',false],[320,'nl',true]]){
 const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'}),page=await context.newPage(),errors=[],failures=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failures.push(r.url())});await page.addInitScript(l=>{if(!localStorage.getItem('overtake-it-away-language'))localStorage.setItem('overtake-it-away-language',l)},lang);
 const base=local?'file://'+process.cwd()+'/':'http://127.0.0.1:8798/';await page.goto(base+'analysis-lab.html#driver=max-verstappen');await page.waitForFunction(()=>!!window.phase2Lab,{},{timeout:120000});await page.locator('#preseason-enter').click({timeout:1000}).catch(()=>{});await page.evaluate(()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close()));
 await page.evaluate(async()=>{Object.assign(phase2Lab.state,{extra_free:true,extra_tyres:true,metronomedetail:true});await phase2Lab.render()});
 assert.equal(await page.locator('summary').filter({hasText:/^(Berekening en interpretatie|Calculation and interpretation)$/}).count(),0);
 assert.ok(await page.locator('#quality-start .starter-plot').count());assert.ok(await page.locator('#quality-raceprogression .starter-plot').count());assert.equal(await page.locator('[data-qualifying-years] .qualifying-year-plot').count(),2);assert.ok(await page.locator('#quality-metronome .field-row').count()>10);assert.ok(await page.locator('.quality-coverage').count()>0);
 const links=await page.locator('[data-driver-help]').evaluateAll(xs=>xs.map(x=>x.getAttribute('href').split('#')[1]));
 for(const topic of['qualifying','free','metronome','regularity','tyres','pitwindow','warmup'])assert.ok(links.includes(topic),topic);
 await page.locator('#quality-metronome [data-driver-help]').first().click();await page.locator('#pitwall-briefing [data-pitwall-help]').click();await page.waitForFunction(()=>window.driverMethods?.phase==='metronome');assert.ok((await page.locator('#method-content').innerText()).includes(lang==='nl'?'Exact gelijke millisecondetijden':'Equal millisecond times'));
 assert.equal(await page.locator('[data-site-link=drivers]').getAttribute('href'),'../analysis-lab.html');
 await page.screenshot({path:output+'/help-metronome-'+width+'-'+lang+'.png'});
 const checks={start:/Gaussisch proces|Gaussian process/,race:/Pitlanestarters mogen hier meedoen|Pit-lane starters can be included/,qualifying:/400/,free:/zes gekoppelde|six paired/,metronome:/Iedere gemeten ronde|Each measured lap/,regularity:/Theil–Sen/,tyres:/acht gekoppelde|eight paired/,pitwindow:/zes vrije referentieronden|six clear-air reference laps/,warmup:/leeftijd 1–3|ages 1–3/};
 for(const[topic,pattern]of Object.entries(checks)){
  await page.locator('#method-'+topic).click();await page.waitForFunction(p=>window.driverMethods?.phase===p,topic);assert.match(await page.locator('#method-content').textContent(),pattern,topic);
  if(topic==='qualifying'){await page.waitForSelector('.qualifying-validation tbody tr');assert.equal(await page.locator('.qualifying-validation tbody tr').count(),2);assert.ok((await page.locator('.qualifying-validation').innerText()).includes('4023'));await page.screenshot({path:output+'/help-qualifying-'+width+'-'+lang+'.png'})}
 }
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));await page.locator('#method-language').click();assert.equal(await page.locator('html').getAttribute('lang'),lang==='nl'?'en':'nl');assert.equal(await page.evaluate(()=>driverMethods.phase),'warmup');
 await page.reload();await page.waitForFunction(()=>window.driverMethods?.phase==='warmup');assert.equal(await page.locator('html').getAttribute('lang'),lang==='nl'?'en':'nl');
 await page.locator('#method-warmup').focus();await page.keyboard.press('Home');await page.waitForFunction(()=>driverMethods.phase==='start');assert.equal(await page.evaluate(()=>document.activeElement.id),'method-start');
 assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);report.push({width,lang,local,profileMethodsMoved:true,chartsPresent:true,helpTopics:9,qualifyingValidation:true,languageAndKeyboard:true,errors,failures});await context.close();
}
fs.writeFileSync(output+'/browser-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();})().catch(e=>{console.error(e);process.exit(1)});
