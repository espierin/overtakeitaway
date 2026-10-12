const {chromium}=require('/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch(),page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],start=Date.now();page.on('pageerror',e=>errors.push(e.message));
 page.on('framenavigated',f=>console.log('FRAME',Date.now()-start,f.url()));page.on('requestfailed',r=>console.log('FAIL',r.url(),r.failure()?.errorText));
 const base=process.argv[2]||'https://espierin.github.io/overtakeitaway/';
 await page.goto(base+'analyses/2022/melbourne/runs/20261010T222623.376987Z-c66ab3/overzicht.html');
 await page.waitForSelector('#race-frame',{timeout:65000});console.log('INITIAL',Date.now()-start);
 for(let i=0;i<3;i++){
  const frame=page.frames().find(f=>f.parentFrame()&&/f1-frame/.test(f.url()));const section=frame.locator('#section-positions');if(await section.count())await section.scrollIntoViewIfNeeded();
  const link=frame.locator('.race-navigation a').filter({hasText:i===2?'Next race':'Next year'}).first();
  const links=await frame.locator('.race-navigation a').allTextContents();console.log('LINKS',links);
  const actual=(await link.count())?link:frame.locator('.race-navigation a').filter({hasText:i===2?'Volgende race':'Volgend jaar'}).first();
  if(!await actual.count())break;
  const time=Date.now(),old=page.url();await actual.click();
  try{await page.waitForFunction(previous=>location.href!==previous,old,{timeout:65000});console.log('SWAP',Date.now()-time,page.url());}
  catch(e){console.log('TIMEOUT',await page.locator('#race-loading').textContent(),page.frames().map(f=>f.url()));throw e;}
 }
 console.log('ERRORS',errors);await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
