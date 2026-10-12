/* Two isolated race documents: keep the current race visible until its replacement is ready. */
(()=>{'use strict';
 const bootstrap=document.currentScript,packed=bootstrap.dataset.f1Document;
 const parameters=new URLSearchParams(location.search);
 if(!bootstrap.hasAttribute('data-f1-shell')||parameters.has('f1-frame')||location.protocol==='file:'){
  (async()=>{try{const r=await fetch(new URL(packed,location.href));if(!r.ok)throw Error('Pagina ontbreekt / Page unavailable');
   const content=await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text();
   document.open();document.write(content);document.close();
  }catch(e){document.body.textContent=e.message;}})();return;
 }
 const style=document.createElement('style');style.textContent='html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#080b12}#race-frame,#race-preload{position:fixed;inset:0;width:100%;height:100%;border:0;background:#080b12}#race-preload{visibility:hidden;pointer-events:none}#race-loading{position:fixed;right:24px;bottom:24px;z-index:3;padding:10px 16px;border:1px solid #51d6dd;border-top:3px solid #51d6dd;border-radius:4px;background:#080b12eF;color:#fff;font:600 13px system-ui}';document.head.append(style);
 let current=null,pending=null,generation=0;
 const language=()=>{try{return localStorage.getItem('overtake-it-away-language')==='en';}catch{return false;}};
 const indicator=document.createElement('div');indicator.id='race-loading';indicator.role='status';document.body.append(indicator);
 const status=text=>{indicator.textContent=text;indicator.hidden=!text;};
 const clean=url=>{url=new URL(url,location.href);url.searchParams.delete('f1-frame');return url;};
 const frameURL=url=>{url=new URL(url);url.searchParams.set('f1-frame','1');return url.href;};
 const ready=async frame=>{
  const win=frame.contentWindow,doc=frame.contentDocument;
  // load includes linked scripts/images; web fonts and two paints complete the graphs and scroll restoration.
  await doc.fonts.ready;await new Promise(resolve=>win.requestAnimationFrame(()=>win.requestAnimationFrame(resolve)));
  if(!doc.querySelector('[data-f1-reader]'))throw Error(language()?'Race could not be loaded':'Race kon niet worden geladen');
  if(doc.documentElement.style.visibility==='hidden')await new Promise(resolve=>win.requestAnimationFrame(resolve));
 };
 const navigate=async(input,historyMode='push')=>{
  const url=clean(input);if(url.origin!==location.origin){location.assign(url);return;}
  const token=++generation;if(pending)pending.remove();
  const frame=document.createElement('iframe');frame.id='race-preload';frame.title=language()?'Race dashboard':'Racedashboard';pending=frame;
  status(language()?'Loading race…':'Race laden…');
  const timer=setTimeout(()=>fail(new Error(language()?'Loading took too long. Please try again.':'Het laden duurt te lang. Probeer opnieuw.')),60000);
  const fail=error=>{if(token!==generation)return;clearTimeout(timer);frame.remove();pending=null;status(error.message);};
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
