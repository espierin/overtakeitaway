const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
const output='storage/metronome-field-20261018';fs.mkdirSync(output,{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true}),report=[];
for(const [driver,width,lang,local]of[['max-verstappen',1440,'nl',false],['romain-grosjean',390,'en',false],['fernando-alonso',320,'nl',true]]){
 const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'}),page=await context.newPage(),errors=[],failures=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failures.push(r.url())});
 await page.addInitScript(l=>localStorage.setItem('overtake-it-away-language',l),lang);
 await page.goto((local?'file://'+process.cwd()+'/':'http://127.0.0.1:8798/')+'coureurs_2.html#driver='+driver);
 await page.waitForFunction(()=>!!window.phase2Lab&&!!document.querySelector('#quality-metronome .field-table'),{},{timeout:120000});
 await page.locator('#preseason-enter').click({timeout:1000}).catch(()=>{});await page.evaluate(()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close()));
 async function check(){return page.evaluate(()=>{const {data,state}=phase2Lab,driver=data.drivers.find(d=>d.id===state.driver),races=new Map(data.races.map(r=>[r.id,r])),rows=driver.races.filter(r=>driverPeriod.matches(races.get(r.race),state)),participants=driverField.participants({data,rows}),ranks=rows.flatMap(r=>lapRankings.pointsFor(r,'free','',data.settings?.lap_rankings?.compounds)).map(p=>p.rank).sort((a,b)=>a-b),median=ranks.length?(ranks[Math.floor((ranks.length-1)/2)]+ranks[Math.ceil((ranks.length-1)/2)])/2:null,profile=document.querySelector('#quality-metronome .field-row.is-profile');return{participants:participants.length,loaded:participants.every(d=>phase2Loader.loaded.has(d.id)),displayed:document.querySelectorAll('#quality-metronome [data-field-driver]').length,points:ranks.length,actualPoints:+profile.dataset.fieldN,median,actualMedian:+profile.dataset.fieldMedian,ownCollapsed:!document.querySelector('[data-metronome-detail]').open,overflow:document.documentElement.scrollWidth-innerWidth}})}
 const initial=await check();assert.ok(initial.loaded);assert.equal(initial.displayed,initial.participants);assert.ok(initial.displayed>10);assert.equal(initial.points,initial.actualPoints);assert.equal(initial.median,initial.actualMedian);assert.equal(initial.ownCollapsed,true);assert.ok(initial.overflow<=2);
 await page.locator('#quality-metronome').scrollIntoViewIfNeeded();await page.screenshot({path:output+'/'+driver+'-'+width+'.png'});
 await page.locator('[data-metronome-detail]').evaluate(x=>x.open=true);await page.waitForSelector('.lap-rank-plot');assert.ok(await page.locator('.lap-rank-point').count()>0);
 if(driver==='max-verstappen'){
  await page.locator('#year-min').evaluate(x=>{x.value='2021';x.dispatchEvent(new Event('change',{bubbles:true}))});
  await page.waitForFunction(()=>phase2Lab.state.yearMin===2021&&document.querySelector('#quality-metronome .field-row.is-profile')?.dataset.fieldN===String(phase2Data.drivers.find(d=>d.id==='max-verstappen').races.filter(r=>driverPeriod.matches(phase2Data.races.find(x=>x.id===r.race),phase2Lab.state)).flatMap(r=>lapRankings.pointsFor(r,'free','',phase2Data.settings?.lap_rankings?.compounds)).length));
  const filtered=await check();assert.ok(filtered.loaded);assert.equal(filtered.displayed,filtered.participants);assert.equal(filtered.points,filtered.actualPoints);assert.ok(filtered.points<initial.points);
  await page.locator('[data-driver-profile="lando-norris"]').click();await page.waitForFunction(()=>document.querySelector('[data-driver-profile="lando-norris"][aria-current=true]')&&document.querySelector('#quality-metronome .field-row.is-profile')?.dataset.fieldDriver==='lando-norris');const switched=await check();assert.ok(switched.loaded);assert.equal(switched.actualPoints,switched.points);
 }
 assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);report.push({driver,width,lang,local,...initial,errors,failures});await context.close();
}
fs.writeFileSync(output+'/browser-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();})().catch(e=>{console.error(e);process.exit(1)});
