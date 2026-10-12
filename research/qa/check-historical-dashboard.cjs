const {chromium}=require('/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const root=process.argv[2],base=process.argv[3]||'http://127.0.0.1:8794/';
(async()=>{
 const browser=await chromium.launch(),context=await browser.newContext({viewport:{width:1500,height:1100}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&!/race-updates/.test(r.url()))errors.push(r.status()+' '+r.url())});
 const cases=[[1950,'01-british-grand-prix'],[1982,'05-belgian-grand-prix'],[1995,'05-monaco-grand-prix'],[2016,'20-brazilian-grand-prix'],[2018,'01-australian-grand-prix'],[2019,'06-monaco-grand-prix'],[2022,'melbourne']];
 for(const [year,gp] of cases){
  const folder=path.join(root,'analyses',String(year),gp,'runs');if(!fs.existsSync(folder)){console.log('SKIP PATH',folder);continue}
  const run=fs.readdirSync(folder)[0],url='analyses/'+year+'/'+gp+'/runs/'+run+'/overzicht.html?f1-frame=1';
  await page.goto(base+url);await page.waitForFunction(()=>typeof D!=='undefined'&&document.querySelector('#kpis .highlight'));
  await page.waitForTimeout(200);
  const data=await page.evaluate(()=>({historical:D.historical,heat:D.explorer.heat_available,parts:D.explorer.sector_count,cycles:D.cycles.length,sections:[...document.querySelectorAll('.chart-grid>section')].map(e=>e.id),left:[...document.querySelectorAll('#firstlap .race-gain-panels>div:first-child .highlight-code')].map(e=>e.textContent),right:[...document.querySelectorAll('#firstlap .race-gain-panels>div:last-child .highlight-code')].map(e=>e.textContent),expected:D.drivers.slice().sort((a,b)=>(a.finish??Infinity)-(b.finish??Infinity)||a.driver_number-b.driver_number).map(d=>d.code),expectedFirst:D.drivers.slice().sort((a,b)=>(a.lap1_position||Infinity)-(b.lap1_position||Infinity)||(a.grid||Infinity)-(b.grid||Infinity)||a.driver_number-b.driver_number).map(d=>d.code),gain:[...document.querySelectorAll('[data-position-gain]')].map(e=>+e.dataset.positionGain),up:document.querySelectorAll('[data-position-gain-direction="up"]').length,down:document.querySelectorAll('[data-position-gain-direction="down"]').length}));
  assert.deepEqual(data.right,data.expected);assert.deepEqual(data.left,data.expectedFirst);assert.equal(data.up,data.gain.filter(n=>n>0).length);assert.equal(data.down,data.gain.filter(n=>n<0).length);
  if(year<2020){assert.equal(data.historical,true);assert.ok(!data.sections.includes('section-mapchart'));assert.equal(await page.locator('.rex-heat').count(),data.heat?1:0);if(data.parts===1&&data.heat)assert.equal(await page.locator('[data-rex-sector="2"]').count(),0);}
  await page.evaluate(()=>siteLanguage.set('en'));await page.waitForTimeout(100);
  if(data.heat&&data.parts===1)assert.equal(await page.locator('.rex-heat h3').evaluate(e=>e.childNodes[0].textContent.trim()),'Relative lap pace');
  const driver=page.locator('#driver-picker .driver-row').first();const selected=await driver.getAttribute('data-value');await driver.click();assert.equal(await page.locator('#firstlap .race-gain-panels>div:first-child .highlight-code').count(),1);await page.locator('#select-all').click();
  if(year<2020){await page.locator('#section-events summary').click();await page.locator('#event-search').fill('test-no-match');assert.equal(await page.locator('#event-table tbody tr').count(),0);await page.locator('#event-search').fill('');const event=page.locator('#driverchart [data-action="action-map"]').first();if(await event.count()){await event.dispatchEvent('click');assert.match(await page.locator('#event-detail h2').innerText(),/Reconstructed/);await page.locator('#close-dialog').click();}}
  await page.locator('#section-firstlap').scrollIntoViewIfNeeded();await page.screenshot({path:'/tmp/history-'+year+'-positions.png'});
  await page.locator('#section-positions').scrollIntoViewIfNeeded();await page.screenshot({path:'/tmp/history-'+year+'-explorer.png'});
  await page.locator('[data-rex-play]').click();await page.waitForTimeout(900);await page.locator('[data-rex-play]').click();
  await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.body.scrollWidth<=innerWidth+2));await page.setViewportSize({width:1500,height:1100});
  console.log('PASS',year,gp,JSON.stringify({heat:data.heat,parts:data.parts,cycles:data.cycles,sections:data.sections,up:data.up,down:data.down}));
 }
 // A saved old year must never be the default on a fresh visit.
 await context.addInitScript(()=>localStorage.setItem('catalogue-year','1982'));await page.goto(base);await page.waitForFunction(()=>document.querySelector('#year-strip [aria-pressed="true"]'));
 const year=await page.locator('#year-strip [aria-pressed="true"]').getAttribute('data-year');assert.match(year,new RegExp(String(new Date().getFullYear())));console.log('PASS front page defaults to current year despite saved choice');
 assert.deepEqual(errors,[]);await browser.close();console.log('PASS all browser checks and no page errors');
})().catch(e=>{console.error(e);process.exit(1)});
