/* Cold-cache browser checks; optional source overlay isolates a repair before release.
 * NODE_PATH must contain Playwright. Usage: node ... URL [--source-overlay]
 */
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch(),base=process.argv[2]||'https://espierin.github.io/overtakeitaway/',overlay=process.argv.includes('--source-overlay'),report={base,overlay,checks:[],errors:[]};
 try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 if(overlay)await context.route('**/assets/site-navigation.js*',r=>r.fulfill({contentType:'text/javascript',body:fs.readFileSync('src/f1_analysis/site-navigation.js','utf8')}));
 const page=await context.newPage();page.setDefaultTimeout(15000);page.on('pageerror',e=>report.errors.push(e.message));
 page.on('response',r=>{if(r.status()>=400)report.errors.push(r.status()+' '+r.url())});
 const open=async path=>{const start=Date.now();await page.goto(new URL(path,base).href,{waitUntil:'domcontentloaded'});await page.waitForSelector('#race-frame',{timeout:20000});const frame=await page.locator('#race-frame').elementHandle().then(e=>e.contentFrame());assert.equal(await frame.locator('html').evaluate(e=>e.style.visibility),'');await frame.waitForFunction(()=>document.readyState==='complete');report.checks.push({page:path,ms:Date.now()-start});return frame};
 await page.goto(base,{waitUntil:'load'});await page.locator('.races-tile').click();await page.waitForSelector('#race-cards');assert.match(page.url(),/races\.html/);report.checks.push({home_to_races:true});
 let frame=await open('analyses/2018/01-australian-grand-prix/runs/20261011T034231.206255Z-050009/overzicht.html');
 await frame.locator('[data-site-about]').click();await frame.waitForSelector('#about-dialog[open]');await frame.locator('#about-close').click();
 await frame.locator('#language-toggle').click();await frame.waitForFunction(()=>document.documentElement.lang==='en');await frame.locator('[data-site-about]').click();await frame.locator('#about-close').click();await frame.locator('#language-toggle').click();await frame.waitForFunction(()=>document.documentElement.lang==='nl');report.checks.push({about_and_language:'en/nl'});
 await frame.locator('#section-positions').scrollIntoViewIfNeeded();
 for(const index of [3,2,1,0]){const old=page.url(),start=Date.now();frame=await page.locator('#race-frame').elementHandle().then(e=>e.contentFrame());const link=frame.locator('.race-navigation a').nth(index);const expected=await link.getAttribute('href');assert.ok(expected);await link.click();await page.waitForURL(url=>url.href!==old,{timeout:20000});frame=await page.locator('#race-frame').elementHandle().then(e=>e.contentFrame());await frame.waitForFunction(()=>document.documentElement.dataset.raceNavigationReady==='true');assert.equal(await page.locator('iframe').count(),1);report.checks.push({navigation:index,target:page.url(),ms:Date.now()-start});}
 const beforeBack=page.url();await page.goBack();await page.waitForURL(url=>url.href!==beforeBack);await page.waitForSelector('#race-frame');report.checks.push({history:true});
 // Slow data must keep the current race visible and the UI responsive.
 await context.route('**/_documents/*.html.gz',async r=>{await new Promise(resolve=>setTimeout(resolve,1800));await r.continue()});
 frame=await page.locator('#race-frame').elementHandle().then(e=>e.contentFrame());const previous=page.url();await frame.locator('.race-navigation a').nth(1).click();await page.waitForSelector('#race-preload',{state:'attached'});assert.equal(await page.locator('#race-frame').count(),1);assert.equal(await page.locator('#race-loading').isVisible(),true);await page.waitForURL(url=>url.href!==previous,{timeout:20000});await context.unroute('**/_documents/*.html.gz');report.checks.push({slow_navigation_keeps_current_race:true});
 frame=await open('analyses/2022/melbourne/runs/20261010T222623.376987Z-c66ab3/overzicht.html');
 const manifest=await frame.evaluate(async()=>{const response=await fetch('manifest.json');return {status:response.status,year:(await response.json()).input.year}});assert.equal(manifest.status,200);assert.equal(manifest.year,2022);report.checks.push({data_download:manifest});
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(200);assert.ok(await frame.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));report.checks.push({mobile_width:true});
 // A second fresh session must not depend on the first session's cookies/cache.
 const fresh=await browser.newContext({viewport:{width:390,height:844}});if(overlay)await fresh.route('**/assets/site-navigation.js*',r=>r.fulfill({contentType:'text/javascript',body:fs.readFileSync('src/f1_analysis/site-navigation.js','utf8')}));const mobile=await fresh.newPage();mobile.on('pageerror',e=>report.errors.push(e.message));await mobile.goto(new URL('analyses/2018/01-australian-grand-prix/runs/20261011T034231.206255Z-050009/overzicht.html',base).href);await mobile.waitForSelector('#race-frame',{timeout:20000});report.checks.push({fresh_mobile_session:true});
 assert.deepEqual(report.errors,[]);console.log(JSON.stringify(report,null,2));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
