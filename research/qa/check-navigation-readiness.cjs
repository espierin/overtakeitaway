const {chromium}=require('/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch(),context=await browser.newContext({viewport:{width:1500,height:1100}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 // Reproduce browsers that do not schedule paints for a hidden prepared document.
 await context.addInitScript(()=>{if(window.frameElement?.id==='race-preload')window.requestAnimationFrame=()=>0;});
 const base=process.argv[2]||'http://127.0.0.1:8795/';await page.goto(base+'analyses/2022/mexico-city/runs/20261010T222718.981007Z-18c061/overzicht.html').catch(()=>{});
 if(!await page.locator('#race-frame').count()){
  const fs=require('fs'),root=process.argv[3];const run=fs.readdirSync(root+'/analyses/2022/mexico-city/runs')[0];await page.goto(base+'analyses/2022/mexico-city/runs/'+run+'/overzicht.html');
 }
 await page.waitForSelector('#race-frame');let frame=await page.locator('#race-frame').elementHandle().then(e=>e.contentFrame());
 await frame.locator('#section-positions').scrollIntoViewIfNeeded();await frame.evaluate(()=>scrollBy(0,200));
 const previous=page.url(),start=Date.now();await frame.locator('.race-navigation a').nth(2).click();await page.waitForFunction(url=>location.href!==url,previous,{timeout:15000});
 assert.equal(await page.locator('iframe').count(),1);frame=await page.locator('#race-frame').elementHandle().then(e=>e.contentFrame());
 assert.equal(await frame.evaluate(()=>document.documentElement.style.visibility),'');assert.equal(await frame.evaluate(()=>document.documentElement.dataset.raceNavigationReady),'true');
 console.log('PASS hidden-frame animation callbacks disabled, navigation restores and completes',Date.now()-start,'ms');
 const old=page.url();await context.route('**/overzicht.html?f1-frame=1*',r=>r.fulfill({status:503,contentType:'text/html',body:'Unavailable'}));
 await frame.locator('.race-navigation a').first().click();await page.waitForFunction(()=>document.querySelector('#race-loading').textContent.includes('geladen')||document.querySelector('#race-loading').textContent.includes('loaded'));
 assert.equal(page.url(),old);assert.equal(await page.locator('#race-frame').count(),1);assert.equal(await page.locator('#race-preload').count(),0);console.log('PASS network failure keeps previous race visible');
 assert.deepEqual(errors,[]);await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
