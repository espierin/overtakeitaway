/* Keep the current race visible until its replacement is ready; colour loading tyres by destination. */
(()=>{'use strict';
 const bootstrap=document.currentScript,packed=bootstrap.dataset.f1Document;
 const parameters=new URLSearchParams(location.search),nested=parameters.has('f1-frame');
 const shell=bootstrap.hasAttribute('data-f1-shell')&&!nested&&location.protocol!=='file:';
 const sectionFor=input=>{
  const path=new URL(input,location.href).pathname,name=path.split('/').pop();
  if(name==='analysis-lab.html')return {section:'drivers',colour:'purple',source:'Purple',glow:'#b45cff40'};
  if(name==='goat.html')return {section:'greatest',colour:'yellow',source:'Yellow',glow:'#e5bf7840'};
  if(name==='races.html'||name==='overzicht.html'||path.includes('/analyses/'))return {section:'races',colour:'red',source:'Red',glow:'#ff475840'};
  return null;
 };
 const language=()=>{try{return localStorage.getItem('overtake-it-away-language')==='en';}catch{return false;}};
 let indicator,wheel,tire,errorMessage;
 const setWheel=input=>{const choice=sectionFor(input);if(!indicator||!choice)return;
  indicator.dataset.section=choice.section;indicator.dataset.colour=choice.colour;
  indicator.style.setProperty('--loading-glow',choice.glow);
  wheel.href='https://commons.wikimedia.org/wiki/File:F1_tire_Pirelli_PZero_'+choice.source+'.svg';
  tire.src=new URL('../assets/tire-'+choice.colour+'.svg',bootstrap.src).href;
 };
 const status=(text,error=false)=>{if(!indicator)return;indicator.setAttribute('aria-label',text);indicator.dataset.error=String(error);errorMessage.textContent=error?text:'';indicator.hidden=!text;};
 if(!nested&&sectionFor(location.href)){
 const style=document.createElement('style');style.textContent=(shell?'html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#080b12}#race-frame,#race-preload{position:fixed;inset:0;width:100%;height:100%;border:0;background:#080b12}#race-preload{visibility:hidden;pointer-events:none}':'')+'#race-loading{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:3;color:#fff;font:600 13px system-ui}#race-loading[hidden]{display:none}.race-loading-wheel{display:block;width:140px;height:140px;filter:drop-shadow(0 8px 22px #000c) drop-shadow(0 0 12px var(--loading-glow,#b45cff40));animation:race-tire-spin 1.4s linear infinite}.race-loading-wheel img{display:block;width:100%;height:100%}.race-loading-error{margin:0}#race-loading[data-error="true"]{max-width:min(420px,85vw);padding:14px 18px;border:1px solid #ff4655;border-radius:6px;background:#080b12ef}#race-loading[data-error="true"] .race-loading-wheel{display:none}@keyframes race-tire-spin{to{transform:rotate(360deg)}}@media(prefers-reduced-motion:reduce){.race-loading-wheel{animation:none}}';document.head.append(style);
  indicator=document.createElement('div');indicator.id='race-loading';indicator.role='status';indicator.hidden=true;
  wheel=document.createElement('a');wheel.className='race-loading-wheel';wheel.target='_blank';wheel.rel='noopener';wheel.title='MiniPictures · CC BY-SA 4.0';wheel.setAttribute('aria-label','Pirelli · MiniPictures · CC BY-SA 4.0');
  tire=document.createElement('img');tire.alt='';wheel.append(tire);
  errorMessage=document.createElement('p');errorMessage.className='race-loading-error';indicator.append(wheel,errorMessage);document.body.append(indicator);setWheel(location.href);
 }
 if(!shell){
  status(language()?'Loading data…':'Gegevens laden…');
  (async()=>{try{const r=await fetch(new URL(packed,location.href));if(!r.ok)throw Error('Pagina ontbreekt / Page unavailable');
   const content=await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text();
   document.open();document.write(content);document.close();
  }catch(e){if(indicator)status(e.message,true);else document.body.textContent=e.message;}})();return;
 }
 let current=null,pending=null,generation=0;
 const clean=url=>{url=new URL(url,location.href);url.searchParams.delete('f1-frame');return url;};
 const frameURL=url=>{url=new URL(url);url.searchParams.set('f1-frame','1');return url.href;};
 const ready=async frame=>{
  const doc=frame.contentDocument;
  // Hidden frames can suspend animation callbacks. Readiness must not depend on a paint.
  await Promise.race([doc.fonts.ready,new Promise(resolve=>setTimeout(resolve,1500))]);
  if(!doc.querySelector('[data-f1-reader]'))throw Error(language()?'Race could not be loaded':'Race kon niet worden geladen');
  for(let i=0;i<100&&(doc.documentElement.style.visibility==='hidden'||doc.querySelector('.race-navigation')&&doc.documentElement.dataset.raceNavigationReady!=='true');i++)await new Promise(resolve=>setTimeout(resolve,20));
  if(doc.documentElement.style.visibility==='hidden')throw Error(language()?'Race view could not be restored':'Racebeeld kon niet worden hersteld');
  // Force layout once before exposing the prepared document.
  doc.documentElement.getBoundingClientRect();
 };
 const navigate=async(input,historyMode='push')=>{
  const url=clean(input);if(url.origin!==location.origin){location.assign(url);return;}
  const token=++generation;if(pending)pending.remove();
  const frame=document.createElement('iframe');frame.id='race-preload';frame.title=language()?'Race dashboard':'Racedashboard';pending=frame;
  setWheel(url);status(language()?'Loading race…':'Race laden…');
  const timer=setTimeout(()=>fail(new Error(language()?'Loading took too long. Please try again.':'Het laden duurt te lang. Probeer opnieuw.')),30000);
  const fail=error=>{if(token!==generation)return;clearTimeout(timer);frame.remove();pending=null;status(error.message,true);};
  frame.onload=async()=>{try{
    if(token!==generation)return;
    if(frame.contentDocument.querySelector('script[data-f1-document]'))return; // The gzip bootstrap replaces its own document.
    await ready(frame);if(token!==generation)return;
    clearTimeout(timer);document.title=frame.contentDocument.title;
    if(historyMode==='push')history.pushState({race:true},'',url);
    else if(historyMode==='replace')history.replaceState({race:true},'',url);
    const old=current;current=frame;pending=null;frame.id='race-frame';frame.style.visibility='visible';
    status('');if(old)old.remove();
    frame.contentWindow.focus();
  }catch(e){fail(e);}};
  frame.src=frameURL(url);document.body.append(frame);
 };
 window.overtakeNavigation={navigate};
 window.addEventListener('popstate',()=>navigate(location.href,'none'));
 navigate(location.href,'replace');
})();
