/* Driver-workspace introduction. Shown once per page load, for eight seconds. */
(()=>{'use strict';
if(window.preseasonTesting)return;
const script=document.currentScript,asset=script?.src?new URL('home/preseason-testing-v1.webp',script.src).href:'assets/home/preseason-testing-v1.webp';
const words={
 nl:{title:'De eerste rijdersanalyses staan op de baan.',intro:'Het rijdersgedeelte is nog in opbouw. De eerste shakedowns zijn gedaan. De komende tijd volgen de lange runs: analyses controleren, grafieken verfijnen en nieuwe inzichten uitproberen.',invitation:'Je kunt alvast rondkijken. Houd er rekening mee dat berekeningen, onderdelen en presentatie nog kunnen veranderen.',signoff:'De stopwatch loopt. Het ontwikkelwerk ook.',enter:'Neem alvast een kijkje',races:'Naar de races',close:'Sluiten',timer:'Sluit automatisch na 8 seconden'},
 en:{title:'The first driver analyses are out on track.',intro:'The driver section is still under construction. The first shakedowns are complete. Next come the long runs: checking analyses, refining charts and trying out new insights.',invitation:'You are welcome to take a look around. Please keep in mind that calculations, features and presentation may still change.',signoff:'The stopwatch is running. So is development.',enter:'Take a look',races:'Go to races',close:'Close',timer:'Closes automatically after 8 seconds'}
};
let dialog,timer,started=false,cleaned=true,opener,previousOverflow='';
const language=()=>document.documentElement.lang.toLowerCase().startsWith('en')?'en':'nl';
function translate(){if(!dialog)return;const text=words[language()];dialog.querySelectorAll('[data-preseason-copy]').forEach(el=>{el.textContent=text[el.dataset.preseasonCopy];});document.getElementById('preseason-close').setAttribute('aria-label',text.close);}
function cleanup(){if(cleaned)return;cleaned=true;clearTimeout(timer);document.body.style.overflow=previousOverflow;if(opener?.isConnected)opener.focus?.({preventScroll:true});}
function dismiss(reason='button'){if(!dialog?.open)return;dialog.dataset.dismissedBy=reason;dialog.close();cleanup();}
function start(){if(started)return;started=true;if(document.querySelector('dialog[open]'))return;
 dialog=document.createElement('dialog');dialog.id='preseason-dialog';dialog.className='preseason-dialog';dialog.setAttribute('aria-labelledby','preseason-title');dialog.setAttribute('aria-describedby','preseason-intro preseason-invitation');dialog.setAttribute('aria-modal','true');
 dialog.innerHTML=`<div class="preseason-scene" aria-hidden="true"><img class="preseason-art" alt="" width="1536" height="1024" decoding="async"></div><button type="button" class="preseason-close" id="preseason-close" aria-label="Sluiten"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button><div class="preseason-content"><p class="preseason-eyebrow">PRE-SEASON TESTING</p><h2 id="preseason-title" data-preseason-copy="title"></h2><p id="preseason-intro" data-preseason-copy="intro"></p><p id="preseason-invitation" data-preseason-copy="invitation"></p><p class="preseason-signoff"><em data-preseason-copy="signoff"></em></p><div class="preseason-actions"><button type="button" class="preseason-enter" id="preseason-enter" data-preseason-copy="enter" autofocus></button><a class="button preseason-races" id="preseason-races" href="races.html" data-preseason-copy="races"></a></div><p class="preseason-timer" data-preseason-copy="timer"></p></div><div class="preseason-countdown" aria-hidden="true"><span></span></div>`;
 dialog.querySelector('.preseason-art').src=asset;document.body.append(dialog);translate();
 document.getElementById('preseason-enter').onclick=()=>dismiss('enter');document.getElementById('preseason-close').onclick=()=>dismiss('close');document.getElementById('preseason-races').onclick=()=>dismiss('races');
 dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const box=dialog.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)dismiss('backdrop');});
 dialog.addEventListener('cancel',event=>{event.preventDefault();dismiss('escape');});dialog.addEventListener('close',cleanup);
 opener=document.activeElement;previousOverflow=document.body.style.overflow||'';cleaned=false;dialog.showModal();document.body.style.overflow='hidden';document.getElementById('preseason-enter').focus?.({preventScroll:true});timer=setTimeout(()=>dismiss('timeout'),8000);
 if(typeof MutationObserver==='function')new MutationObserver(translate).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
}
window.preseasonTesting={dismiss,translate};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
