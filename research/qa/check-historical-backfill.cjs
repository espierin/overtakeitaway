const fs=require('fs');
const {chromium}=require('/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const base=process.argv[2]||'http://127.0.0.1:8775/';
const audit=JSON.parse(fs.readFileSync('analyses/sources/historical/coverage-audit.json','utf8'));
const examples=[[1950,1],[1982,5],[1994,2],[2013,3],[2019,11]];
(async()=>{
 const browser=await chromium.launch({headless:true}); const results=[];
 for(const [year,round] of examples){
  const record=audit.coverage.find(r=>r.year===year&&r.round===round);
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(new URL(record.path,base).href,{waitUntil:'networkidle'});
  await page.locator('#historical-additional-data').waitFor();
  const qualification=page.locator('[data-history-section="qualifying-results"]');
  await qualification.locator('summary').click();
  const before=await qualification.locator('tbody tr').count();
  await page.locator('#drivers [data-entry-filter]').first().click();
  await page.waitForTimeout(200);
  const filtered=await qualification.locator('tbody tr').count();
  if(filtered!==1||before<2)throw Error(`${year}: driver filter ${before} -> ${filtered}`);
  await page.locator('#language-toggle').click();await page.waitForTimeout(300);
  if(await page.locator('html').getAttribute('lang')!=='en')throw Error('English language switch failed');
  if(!(await page.locator('#historical-additional-data').innerText()).includes('Additional historical race archive'))throw Error('Historical English heading missing');
  if((await page.locator('#history-coverage-notes').innerText()).includes('Historische'))throw Error('Dutch coverage in English context');
  await page.locator('#all').click();
  await page.locator('#historical-additional-data').scrollIntoViewIfNeeded();
  await page.screenshot({path:`/tmp/historical-${year}-desktop.png`});
  await page.setViewportSize({width:390,height:844});
  await page.waitForTimeout(200);
  const width=await page.evaluate(()=>({body:document.body.scrollWidth,viewport:innerWidth}));
  await page.screenshot({path:`/tmp/historical-${year}-mobile.png`});
  if(width.body>width.viewport+2)throw Error(`${year}: page horizontal overflow ${JSON.stringify(width)}`);
  if(errors.length)throw Error(`${year}: ${errors.join('; ')}`);
  results.push({year,round,qualifying_rows:before,filtered_rows:filtered,english:true,mobile:width,errors});await page.close();
 }
 await browser.close();fs.writeFileSync('storage/historical-research/browser-qa.json',JSON.stringify(results,null,2)); console.log(JSON.stringify(results));
})().catch(e=>{console.error(e);process.exit(1)});
