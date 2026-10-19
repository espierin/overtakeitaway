/* Driver calculation help; qualifying metadata is loaded only for its validation table. */
(()=>{'use strict';
const content=window.driverHelpArchive;
const topics=window.driverBriefings.topics;
let lang='nl';try{lang=localStorage.getItem('overtake-it-away-language')==='en'?'en':'nl'}catch{}
let validationRequest=null,validationFailed=false;
function loadValidation(){
 if(window.phase2Facts||validationRequest||validationFailed)return;
 validationRequest=new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='data/facts.js';script.onload=resolve;script.onerror=()=>reject(Error('Qualification metadata unavailable'));document.head.append(script)});
 validationRequest.then(()=>{if(location.hash==='#qualifying')render()}).catch(()=>{validationFailed=true;if(location.hash==='#qualifying')render()});
}
function render(){
 const t=(a,b)=>lang==='en'?b:a,requested=location.hash.slice(1),phase=topics[requested]?requested:'start',copy=content[lang][phase],nav=document.querySelector('.method-tabs'),focused=nav.contains(document.activeElement)?document.activeElement.id:null;
 document.documentElement.lang=lang;document.title=t('Uitleg en berekeningen','Help and calculations')+' · Overtake It Away';
 document.querySelector('h1').textContent=t('Uitleg en berekeningen','Help and calculations');
 document.getElementById('method-intro').textContent=t('Berekening, interpretatie en beperkingen van de coureursanalyses. Kies het onderwerp bij de grafiek die je wilt begrijpen. De eerder bewaarde uitleg van start- en racescores blijft hier ook beschikbaar.','Calculations, interpretation and limitations of the driver analyses. Choose the topic matching the chart you want to understand. Previously archived explanations of start and race scores remain available here.');
 nav.setAttribute('aria-label',t('Onderwerpen in de uitleg','Help topics'));
 nav.innerHTML=Object.entries(topics).map(([id,label])=>`<button type="button" id="method-${id}" data-method-phase="${id}" role="tab" aria-controls="method-content" aria-selected="${id===phase}" tabindex="${id===phase?0:-1}">${label[lang==='en'?1:0]}</button>`).join('');
 document.getElementById('collection-link').textContent=t('Datacollectie en controles','Data collection and checks');
 const toggle=document.getElementById('method-language');toggle.textContent='EN / NL';toggle.setAttribute('aria-label',t('Switch to English','Schakel naar Nederlands'));
 const host=document.getElementById('method-content');host.setAttribute('aria-labelledby','method-'+phase);
 host.innerHTML='<h2>'+topics[phase][lang==='en'?1:0]+'</h2>'+window.driverBriefings.render(phase,lang,window.phase2Facts?.qualifying_bridge_validation||{});
 if(phase==='qualifying'&&!window.phase2Facts){
  const note=document.createElement('p');note.id='help-loading';note.setAttribute('role','status');note.textContent=validationFailed?t('De toetsgegevens konden niet worden geladen. De methode staat hieronder; ontbrekende toetsgegevens zijn geen nul.','Validation figures could not be loaded. The method is shown below; unavailable validation data do not mean zero.'):t('Toetsgegevens laden…','Loading validation figures…');host.prepend(note);loadValidation();
 }

 window.driverBriefings.centerFigures(host);
 const first=host.querySelector('details');if(first)first.open=true;
 for(const link of host.querySelectorAll('a[target=_blank]'))link.rel='noopener noreferrer';
 window.driverMethods={lang,phase};
 if(focused)document.getElementById(focused)?.focus({preventScroll:true});
}
const nav=document.querySelector('.method-tabs');
nav.addEventListener('click',event=>{const button=event.target.closest('[data-method-phase]');if(button)location.hash=button.dataset.methodPhase});
nav.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;const buttons=[...nav.querySelectorAll('[data-method-phase]')],button=event.target.closest('[data-method-phase]');if(!button)return;event.preventDefault();const i=buttons.indexOf(button),target=event.key==='Home'?buttons[0]:event.key==='End'?buttons.at(-1):buttons[(i+(event.key==='ArrowRight'?1:-1)+buttons.length)%buttons.length];target.focus();target.click()});
document.getElementById('method-language').onclick=()=>{lang=lang==='nl'?'en':'nl';try{localStorage.setItem('overtake-it-away-language',lang)}catch{}render()};
addEventListener('hashchange',render);render();
})();
