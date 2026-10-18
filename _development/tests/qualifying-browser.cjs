const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
const output='storage/qualifying-years-20261018',report=[];
(async()=>{const browser=await chromium.launch({headless:true});
async function run({driver='max-verstappen',from=2013,to=2026,width=1440,lang='nl',local=false}={}){
 const context=await browser.newContext({viewport:{width,height:1200},reducedMotion:'reduce'}),page=await context.newPage(),errors=[],failed=[];
 page.setDefaultTimeout(30000);page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push(r.url())});
 await page.addInitScript(l=>localStorage.setItem('overtake-it-away-language',l),lang);
 await page.goto((local?'file://'+process.cwd()+'/':'http://127.0.0.1:8798/')+'coureurs_2.html#driver='+driver+'&yearMin='+from+'&yearMax='+to+'&lang='+lang);
 await page.waitForFunction(()=>!!window.phase2Lab&&!!document.querySelector('[data-qualifying-years]'),{},{timeout:120000});
 await page.locator('#preseason-enter').click({timeout:1500}).catch(()=>{});await page.evaluate(()=>document.querySelectorAll('dialog[open]').forEach(x=>x.close()));
 assert.ok(await page.locator('#quality-qualifying [data-qualifying-years]').isVisible());
 assert.equal(await page.locator('.quality-grid [data-quality]').count(),6);
 assert.deepEqual(await page.locator('.quality-grid [data-quality]').evaluateAll(xs=>xs.map(x=>x.dataset.quality)),['qualifying','start','free','metronome','tyres','warmup']);
 assert.equal(await page.locator('#driver-qualities').evaluate(el=>el.nextElementSibling.id),'quality-qualifying');
 await page.locator('.quality-grid [data-quality=qualifying]').click();
 assert.equal(await page.locator('.quality-grid [aria-pressed],.quality-grid .selected').count(),0);
 assert.equal(await page.evaluate(()=>phase2Lab.state.quality),'qualifying');
 assert.ok(!(await page.locator('#driver-facts').innerText()).includes('Eigen seizoenen en WK-verloop'));const frame=page.locator('.qualifying-years-frame'),scroller=frame.locator('.qualifying-shared-scroll');await frame.scrollIntoViewIfNeeded();
 assert.equal(await frame.locator('.qualifying-year-plot').count(),2);assert.equal(await frame.locator('.qualifying-shared-scroll').count(),1);
 const check=await page.evaluate(()=>{const frame=document.querySelector('.qualifying-years-frame'),plots=[...frame.querySelectorAll('.qualifying-year-plot')],axes=[...frame.querySelectorAll('.qualifying-fixed-axis')],scroller=frame.querySelector('.qualifying-shared-scroll');return{
  axes:axes.map(x=>({x:x.getBoundingClientRect().x,y:x.getBoundingClientRect().y,width:x.getBoundingClientRect().width})),
  plots:plots.map(x=>({x:x.getBoundingClientRect().x,y:x.getBoundingClientRect().y,width:x.getBoundingClientRect().width,years:[...x.querySelectorAll('.qualifying-year-group')].map(g=>({year:+g.dataset.year,x:+g.querySelector('.starter-grid-label').getAttribute('x')}))})),
  labels:[...axes[0].querySelectorAll('text')].map(x=>x.textContent).filter(x=>/^P\d/.test(x)),
  positions:document.querySelector('[data-qualifying-years]').dataset.positionCount,times:document.querySelector('[data-qualifying-years]').dataset.gapCount,
  overflow:document.documentElement.scrollWidth-innerWidth,scrollWidth:scroller.scrollWidth,clientWidth:scroller.clientWidth
 }});
 assert.deepEqual(check.plots[0].years,check.plots[1].years);assert.equal(check.plots[0].width,check.plots[1].width);
 for(let i=0;i<2;i++)assert.ok(Math.abs(check.plots[i].y-check.axes[i].y)<1,'Axis/plot y align');
 assert.ok(check.labels.length>=6&&check.labels.every(s=>/^P\d+$/.test(s)));assert.ok(check.overflow<=2);
 const firstBefore=await frame.locator('.qualifying-year-plot').first().boundingBox(),secondBefore=await frame.locator('.qualifying-year-plot').last().boundingBox();
 await scroller.evaluate(el=>el.scrollLeft=300);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 const firstAfter=await frame.locator('.qualifying-year-plot').first().boundingBox(),secondAfter=await frame.locator('.qualifying-year-plot').last().boundingBox(),axisAfter=await frame.locator('.qualifying-fixed-axis').first().boundingBox();
 assert.equal(firstAfter.x-firstBefore.x,secondAfter.x-secondBefore.x);assert.equal(axisAfter.x,check.axes[0].x);if(check.scrollWidth>check.clientWidth)assert.ok(firstAfter.x<firstBefore.x);
 assert.equal(await frame.locator('circle[cx="NaN"],circle[cy="NaN"]').count(),0);
 assert.equal(await frame.locator('.starter-direction').count(),0);
 const timeLabels=await frame.locator('.qualifying-fixed-axis[data-kind=gap] text:not(.axis-label)').allTextContents();assert.ok(timeLabels.includes('0')&&timeLabels.includes('4'));
 const capped=await frame.locator('.qualifying-year-plot[data-kind=gap] .qualifying-observation[data-capped=true]').evaluateAll(xs=>xs.map(x=>({raw:+x.dataset.value,y:+x.dataset.plotY,symbol:x.dataset.symbol,title:x.querySelector('title').textContent})));
 if(capped.length){assert.ok(capped.every(p=>p.raw>4&&p.y===312&&p.symbol==='chevron-down'));assert.ok(capped.every(p=>p.title.includes('4 s')))}
 assert.ok(await frame.locator('.qualifying-violin').count()>0);
 assert.ok(await frame.locator('[data-kind=position] .qualifying-trend').count()>0);assert.ok(await frame.locator('[data-kind=gap] .qualifying-trend').count()>0);
 assert.ok((await frame.locator('.qualifying-trend').first().getAttribute('d')).includes('C'));assert.ok(await frame.locator('.qualifying-confidence').count()>0);
 if(driver==='jos-verstappen')assert.equal(await frame.locator('.qualifying-stage-shadow').count(),0);else assert.ok(await frame.locator('.qualifying-stage-shadow').count()>0);
 assert.equal(await frame.locator('[data-kind=gap] .qualifying-stage-shadow').count(),0);
 const continuous=await frame.locator('[data-kind=position] .qualifying-stage-shadow').evaluateAll(xs=>{const groups=new Map();for(const r of xs){if(!groups.has(r.dataset.year))groups.set(r.dataset.year,[]);groups.get(r.dataset.year).push({x:+r.getAttribute('x'),w:+r.getAttribute('width'),y:+r.getAttribute('y'),h:+r.getAttribute('height')});}const years=[...groups.values()];return years.every(rs=>rs.length===3&&Math.abs(rs[0].y-64)<1e-8&&Math.abs(rs[2].y+rs[2].h-312)<1e-8&&rs.every(r=>r.x===rs[0].x&&r.w===rs[0].w)&&rs.slice(1).every((r,i)=>Math.abs(rs[i].y+rs[i].h-r.y)<1e-8))&&years.slice(1).every((rs,i)=>Math.abs(years[i][0].x+years[i][0].w-rs[0].x)<1e-8)});
 assert.ok(continuous,'Three continuous zones per year, with no gaps between years');
 const introduction=await page.locator('#driver-qualities').innerText();assert.ok(!introduction.includes('Beschrijvende metingen per specialisme')&&!introduction.includes('Alle totalen volgen de gekozen periode')&&!introduction.includes('Descriptive measurements by specialism')&&!introduction.includes('All totals follow the selected period'));

 const identity=page.locator('#driver-period .floating-driver-identity');assert.ok(await identity.isVisible());
 assert.ok((await identity.innerText()).includes(driver==='jos-verstappen'?'Jos Verstappen':driver==='lewis-hamilton'?'Lewis Hamilton':'Max Verstappen'));
 const fixed=await identity.boundingBox(),toolbar=await page.locator('#driver-period').boundingBox();assert.ok(toolbar.y>=-1&&toolbar.y<=1);assert.ok(fixed.y>=toolbar.y+3&&fixed.y+fixed.height<=toolbar.y+toolbar.height);
 await page.evaluate(()=>scrollBy(0,200));const after=await identity.boundingBox();assert.ok(Math.abs(after.y-fixed.y)<1);
 await page.locator('#driver-period').screenshot({path:output+'/'+driver+'-'+width+'-toolbar.png'});
assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 await scroller.evaluate(el=>el.scrollLeft=0);await frame.evaluate(el=>window.scrollTo(0,el.getBoundingClientRect().top+scrollY-300));await frame.screenshot({path:output+'/'+driver+'-'+width+'-'+lang+(local?'-file':'')+'.png'});
 if(driver==='max-verstappen'&&width===1440&&!local){
  const actual=await page.evaluate(()=>{const f=phase2Research.ownFacts('max-verstappen'),r=f.races.find(r=>r.race==='2025-1');return qualifyingYears.gap(r,phase2Facts.qualifying_poles)});assert.equal(actual.value,.385);
  await page.locator('#year-min').evaluate(x=>{x.value='2020';x.dispatchEvent(new Event('change',{bubbles:true}))});
  await page.locator('#year-max').evaluate(x=>{x.value='2023';x.dispatchEvent(new Event('change',{bubbles:true}))});
  await page.waitForFunction(()=>phase2Lab.state.yearMin===2020&&phase2Lab.state.yearMax===2023);
  assert.deepEqual(await page.locator('.qualifying-year-plot[data-kind=position] .qualifying-year-group').evaluateAll(xs=>xs.map(x=>+x.dataset.year)),[2020,2021,2022,2023]);
  await page.locator('#language-toggle').click();assert.equal(await page.locator('.qualifying-position-title').textContent(),'Qualifying position by year');
 }
 if(driver==='jos-verstappen')assert.equal(await page.locator('.qualifying-year-plot[data-kind=position] [data-year="1999"] circle').count(),0);
 report.push({driver,from,to,width,lang,local,...check,sharedScroll:true,errors,failed});await context.close();
}
await run();await run({driver:'lewis-hamilton',from:1950});await run({width:390,lang:'en'});await run({width:320});await run({driver:'jos-verstappen',from:1994,to:2003});await run({local:true});
fs.writeFileSync(output+'/browser-report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report.map(({plots,axes,...r})=>r),null,2));
})().catch(e=>{console.error(e);process.exit(1)});
