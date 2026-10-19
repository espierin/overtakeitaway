/* Single-profile combobox. Search changes presentation, never the year selection. */
(()=>{'use strict';
const fold=s=>String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase().trim();
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let cleanup=null;
function career(driver){const years=[...new Set(driver.races.map(r=>r.year).filter(Number.isInteger))].sort((a,b)=>a-b);return years.length?[years[0],years.at(-1)]:null;}
function roster(data){
 const aliases=new Map();for(const [alias,id]of Object.entries(data.driver_aliases||{})){if(!aliases.has(id))aliases.set(id,[]);aliases.get(id).push(alias.replaceAll('-',' '));}
 return window.driverNames.sort(data.drivers).map(driver=>{
  const last=driver.races.at(-1),years=career(driver),number=last?.number??driver.number,numbers=[...new Set([driver.number,...driver.races.map(r=>r.number)].filter(n=>Number(n)>=0).map(String))];
  return{driver,years,number,color:last?.color||driver.color,search:fold([driver.name,driver.code,driver.id.replaceAll('-',' '),...(aliases.get(driver.id)||[])].join(' ')),numbers};
 });
}
function search(roster,query){
 const q=fold(query);if(!q)return roster;
 const tokens=q.split(/\s+/),numeric=/^\d+$/.test(q);
 return roster.filter(r=>numeric?r.numbers.includes(String(Number(q))):tokens.every(token=>r.search.includes(token))).map((row,index)=>({row,index,rank:fold(row.driver.code)===q||numeric&&String(row.number)===String(Number(q))?0:1})).sort((a,b)=>a.rank-b.rank||a.index-b.index).map(x=>x.row);
}
function badge(driver,row){const number=row?.number??driver.number;return`<span class="badge profile-driver-badge" style="--driver-color:${esc(row?.color||driver.color)}"><span class="number">${esc(Number(number)>=0?number:'?')}</span><span class="stripe" aria-hidden="true"></span><span class="profile-driver-code">${esc(driver.code)}</span></span>`;}

function mount({data,state,lang,choose,change}){
 cleanup?.();const host=document.getElementById('driver-period');if(!host)return;
 host.dataset.profileSelector='true';host.classList.add('driver-selection-panel');host.setAttribute('aria-label',lang==='en'?'Driver selection and selection years':'Coureurkeuze en selectiejaren');
 const t=(nl,en)=>lang==='en'?en:nl,driver=data.drivers.find(d=>d.id===state.driver),all=roster(data).filter(r=>r.driver.races.some(row=>window.driverPeriod.matches(row,state))),years=career(driver),period=state.yearMin===state.yearMax?String(state.yearMin):state.yearMin+'–'+state.yearMax,own=driver.races.filter(r=>window.driverPeriod.matches(r,state)),last=driver.races.at(-1);
 const yearsText=years?years[0]===years[1]?String(years[0]):years.join('–'):'—';
 const yearControls=document.createElement('div');yearControls.className='driver-year-controls';while(host.firstChild)yearControls.append(host.firstChild);host.append(yearControls);const yearHeading=yearControls.querySelector('.range-heading');yearControls.prepend(yearHeading);yearControls.querySelector('.range-heading>span').textContent=t('SELECTIEJAREN','SELECTION YEARS');const yearNote=document.createElement('p');yearNote.className='driver-year-note';yearNote.textContent=t('Deze jaren beperken alleen de coureurkeuzelijst. Het profiel toont altijd de volledige beschikbare loopbaan.','These years only filter the driver list. The profile always shows the full available career.');host.append(yearNote);
 const picker=document.createElement('div');picker.className='driver-selection';
 picker.innerHTML=`<label class="driver-selection-label" for="driver-search">${t('COUREUR','DRIVER')}</label><div class="driver-selected-identity" aria-live="polite">${badge(driver,last)}<span class="profile-full-name">${esc(driver.name)}</span><span class="driver-career-years">${yearsText}</span></div><div class="driver-search-control"><input id="driver-search" type="search" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="driver-search-list" autocomplete="off" spellcheck="false" placeholder="${t('Zoek op naam, code of nummer','Search name, code or number')}"><button type="button" id="driver-search-toggle" aria-label="${t('Alle coureurs tonen','Show all drivers')}" aria-controls="driver-search-list" aria-expanded="false"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m5 7 5 5 5-5" fill="none" stroke="currentColor" stroke-width="2"/></svg></button><div class="driver-search-results" hidden><div class="driver-search-count" role="status" aria-live="polite"></div><div id="driver-search-list" role="listbox" aria-label="${t('Coureurs op achternaam','Drivers by surname')}"></div></div></div>`;
 host.prepend(picker);
 if(!own.length){const notice=document.createElement('div');notice.className='driver-period-empty';notice.setAttribute('role','status');notice.innerHTML=`<div><strong>${t('Deze coureur valt buiten de zoekperiode','This driver is outside the search period')}</strong><p>${esc(driver.name)} · ${period}. ${t('Geregistreerde loopbaan','Recorded career')}: ${yearsText}.</p></div><button type="button" id="driver-show-career" ${years?'':'disabled'}>${t('Gebruik loopbaanjaren','Use career years')}</button>`;host.append(notice);notice.querySelector('button').onclick=()=>{if(!years)return;Object.assign(state,{yearMin:years[0],yearMax:years[1],year:years[0]===years[1]?years[0]:0});change();};}
 document.getElementById('driver-compact')?.remove();const compact=document.createElement('section');compact.id='driver-compact';compact.className='driver-compact-bar';compact.hidden=true;compact.setAttribute('aria-label',t('Geselecteerde coureur en periode','Selected driver and period'));
 compact.innerHTML=`<div class="driver-compact-identity">${badge(driver,last)}<span class="profile-full-name" title="${esc(driver.name)}">${esc(driver.name)}</span></div><span class="driver-compact-period">${yearsText}</span><button type="button" class="driver-edit-selection" aria-label="${t('Coureur of periode wijzigen','Change driver or period')}"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8" cy="8" r="5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m12 12 5 5" stroke="currentColor" stroke-width="2"/></svg><span>${t('Wijzig selectie','Change selection')}</span></button>`;
 host.insertAdjacentElement('afterend',compact);
 const input=picker.querySelector('input'),toggle=picker.querySelector('button'),popup=picker.querySelector('.driver-search-results'),list=picker.querySelector('[role=listbox]'),count=picker.querySelector('[role=status]');
 let opened=false,options=[],active=-1,frame=0,selectTicket=0,disposed=false;
 function position(){if(!opened)return;const r=input.getBoundingClientRect(),height=Math.min(innerHeight,window.visualViewport?.height||innerHeight),below=height-r.bottom-18,above=r.top-18,up=below<180&&above>below;popup.classList.toggle('opens-up',up);popup.style.setProperty('--driver-popup-height',Math.max(140,Math.min(380,up?above:below))+'px');}
 function mark(index,scroll=true){active=index;list.querySelectorAll('[role=option]').forEach((el,i)=>el.classList.toggle('is-option-active',i===active));const option=list.children[active];if(option){input.setAttribute('aria-activedescendant',option.id);if(scroll)option.scrollIntoView({block:'nearest',inline:'nearest'});}else input.removeAttribute('aria-activedescendant');}
 function close(){opened=false;popup.hidden=true;input.setAttribute('aria-expanded','false');toggle.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');}
 async function select(id){close();input.value='';if(id===state.driver)return;const ticket=++selectTicket;picker.setAttribute('aria-busy','true');count.textContent=t('Profiel laden…','Loading profile…');try{await choose(id);}finally{if(!disposed&&ticket===selectTicket)picker.removeAttribute('aria-busy');document.getElementById('driver-search')?.focus({preventScroll:true});}}
 function draw(){
  options=search(all,input.value);count.textContent=options.length+' '+t('coureurs','drivers');
  list.innerHTML=options.map((r,i)=>{const d=r.driver,current=d.id===state.driver,dates=r.years?r.years[0]===r.years[1]?String(r.years[0]):r.years.join('–'):'—';return`<button type="button" role="option" tabindex="-1" id="driver-option-${i}" data-driver-option="${esc(d.id)}" aria-selected="${current}" aria-label="${esc(d.name+' · '+dates+' · '+d.code+' · '+r.number)}">${badge(d,{number:r.number,color:r.color})}<span class="driver-option-copy"><span class="driver-option-name">${esc(d.name)}</span><span class="driver-option-years">${dates}</span></span>${current?'<span class="driver-option-check" aria-hidden="true">✓</span>':''}</button>`;}).join('')||`<p class="driver-search-none">${t('Geen coureurs gevonden. Probeer een naam, code of nummer.','No drivers found. Try a name, code or number.')}</p>`;
  for(const [i,button]of [...list.querySelectorAll('[role=option]')].entries()){button.onpointerdown=e=>{if(e.pointerType!=='touch')e.preventDefault();};button.onclick=()=>select(button.dataset.driverOption);button.onmousemove=()=>mark(i,false);}
  list.scrollTop=0;mark(options.length?0:-1,false);
 }
 function open(){if(!opened){opened=true;popup.hidden=false;input.setAttribute('aria-expanded','true');toggle.setAttribute('aria-expanded','true');draw();}position();}
 input.onclick=open;input.oninput=()=>{open();draw();position();};toggle.onclick=()=>{input.focus({preventScroll:true});if(opened)close();else open();};
 input.onkeydown=e=>{if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(!opened){open();if(e.key==='ArrowUp')mark(options.length-1);return;}mark(Math.max(0,Math.min(options.length-1,active+(e.key==='ArrowDown'?1:-1))));}else if(e.key==='Enter'){e.preventDefault();if(!opened)open();else if(options[active])select(options[active].driver.id);}else if(e.key==='Escape'){e.preventDefault();close();}else if(e.key==='Tab')close();};
 const outside=e=>{if(!picker.contains(e.target))close();};document.addEventListener('pointerdown',outside);
 function update(){frame=0;if(disposed)return;const shown=host.getBoundingClientRect().bottom<=0;compact.hidden=!shown;if(shown&&opened)close();document.documentElement.style.setProperty('--driver-period-height',shown?compact.getBoundingClientRect().height+'px':'0px');if(opened)position();}
 const schedule=()=>{if(!frame)frame=requestAnimationFrame(update);};window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule);window.visualViewport?.addEventListener('resize',schedule);
 const observer=typeof ResizeObserver!=='undefined'?new ResizeObserver(schedule):null;observer?.observe(host);observer?.observe(compact);
 compact.querySelector('button').onclick=()=>{host.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});input.focus({preventScroll:true});open();};
 cleanup=()=>{disposed=true;if(frame)cancelAnimationFrame(frame);observer?.disconnect();document.removeEventListener('pointerdown',outside);window.removeEventListener('scroll',schedule);window.removeEventListener('resize',schedule);window.visualViewport?.removeEventListener('resize',schedule);};update();
}
window.driverSelector={career,roster,search,mount};
})();
