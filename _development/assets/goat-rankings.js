/* Descriptive rankings: one explicit yardstick, no invented overall GOAT score. */
(()=>{'use strict';
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const measures=[
 {id:'win_rate',nl:'Zeges per start',en:'Wins per start',key:'wins',rate:true},
 {id:'podium_rate',nl:'Podia per start',en:'Podiums per start',key:'podiums',rate:true},
 {id:'pole_rate',nl:'Poles per start',en:'Poles per start',key:'poles',rate:true},
 {id:'wins',nl:'Aantal zeges',en:'Total wins',key:'wins'},
 {id:'titles',nl:'Aantal wereldtitels',en:'World titles',key:'titles'},
 {id:'starts',nl:'Aantal starts',en:'Race starts',key:'starts'}
];
function calculate({data,facts,ids,state}){
 const measure=measures.find(m=>m.id===state.rankingMetric)||measures[0],minimum=state.rankingMinimum??20;
 const records=data.drivers.map(driver=>{
  const seasons=(facts.drivers[driver.id]?.seasons||[]).filter(s=>s.year>=state.from&&s.year<=state.to);
  const sum=key=>seasons.length&&seasons.every(s=>finite(s[key]))?seasons.reduce((n,s)=>n+s[key],0):null;
  const starts=sum('starts'),count=measure.key==='titles'?(seasons.length?seasons.filter(s=>s.champion&&!s.provisional).length:null):sum(measure.key);
  return{id:driver.id,starts,count,value:finite(starts)&&starts>0&&finite(count)?(measure.rate?100*count/starts:count):null};
 });
 const measured=records.filter(r=>finite(r.value)),eligible=measured.filter(r=>r.starts>=minimum),pool=state.rankingScope==='all'?eligible:eligible.filter(r=>ids.includes(r.id));
 pool.sort((a,b)=>b.value-a.value||a.id.localeCompare(b.id));
 for(let i=0;i<pool.length;i++)pool[i].rank=i&&Math.abs(pool[i].value-pool[i-1].value)<1e-10?pool[i-1].rank:i+1;
 return{measure,minimum,records,measured:measured.length,pool,omitted:records.filter(r=>ids.includes(r.id)&&(!finite(r.value)||r.starts<minimum))};
}
function render(options){
 const {data,state,badge,lang}=options,R=window.phase2Research,t=(nl,en)=>lang==='en'?en:nl,fmt=v=>R.fmt(v,lang,2),result=calculate(options),{measure,minimum,pool,omitted}=result,page=Math.min(state.rankingPage||0,Math.max(0,Math.ceil(pool.length/25)-1)),rows=pool.slice(page*25,page*25+25);
 return`<section class="research-panel" id="goat-rankings"><h2>${t('Ranglijst per eigenschap','Rankings by measure')}</h2><p>${t('Kies waarop je wilt vergelijken. De volgorde volgt dat ene cijfer in de gekozen periode. Auto, betrouwbaarheid en tijdperk tellen hierin mee; dit is geen totaaloordeel over rijvaardigheid.','Choose what to compare. The order follows that one figure within the selected period. Car, reliability and era affect it; it is not an overall judgement of driving skill.')}</p><div class="research-toolbar"><label>${t('Vergelijk op','Compare by')}<select id="goat-ranking-metric">${measures.map(m=>`<option value="${m.id}" ${m.id===measure.id?'selected':''}>${m[lang==='en'?'en':'nl']}</option>`).join('')}</select></label><label>${t('Toon','Show')}<select id="goat-ranking-scope"><option value="selected">${t('Geselecteerde rijders','Selected drivers')}</option><option value="all" ${state.rankingScope==='all'?'selected':''}>${t('Alle rijders met gegevens','All drivers with data')}</option></select></label><label>${t('Minimaal aantal starts','Minimum race starts')}<select id="goat-ranking-minimum">${[0,10,20,50,100].map(n=>`<option value="${n}" ${minimum===n?'selected':''}>${n||t('Geen minimum','No minimum')}</option>`).join('')}</select></label></div><p class="research-note">${result.measured} / ${data.drivers.length} ${t('rijders met een bekend cijfer in deze periode, vóór het minimumaantal starts. Standaard tellen minimaal 20 starts mee om heel korte loopbanen apart te houden.','drivers have a known figure in this period, before the minimum-start filter. At least 20 starts are required by default to keep very short careers separate.')}</p>${rows.length?R.table([t('Plaats','Rank'),t('Coureur','Driver'),measure[lang==='en'?'en':'nl'],t('Starts','Starts')],rows.map(r=>[r.rank,badge(r.id),fmt(r.value)+(measure.rate?'%':''),r.starts])):`<p class="research-empty">${t('Geen rijders met voldoende gegevens voor deze keuze.','No drivers have enough data for this choice.')}</p>`}${pool.length>25?`<div class="research-toolbar"><button data-ranking-page="-1" ${page===0?'disabled':''}>${t('Vorige','Previous')}</button><span>${page*25+1}–${Math.min(pool.length,page*25+25)} / ${pool.length}</span><button data-ranking-page="1" ${(page+1)*25>=pool.length?'disabled':''}>${t('Volgende','Next')}</button></div>`:''}${omitted.length?`<div class="research-note">${t('Geselecteerd, maar buiten deze ranglijst door ontbrekende gegevens of te weinig starts:','Selected but outside this ranking due to missing data or too few starts:')} ${omitted.map(r=>badge(r.id)).join(' ')}</div>`:''}<p class="research-note">${t('Het aantal starts is geen onzekerheidsmarge. Ook 20 starts maken een percentage nog niet precies. Gelijke ongeronde waarden delen een plaats. Titels tellen alleen uit afgeronde seizoenen; poles volgen de brondefinitie.','The number of starts is not an uncertainty interval. Even 20 starts do not make a percentage precise. Equal unrounded values share a rank. Titles count completed seasons only; poles follow the source definition.')}</p><a class="research-link" href="uitleg.html#ranglijsten">${t('Hoe lees je deze ranglijst?','How to read this ranking?')} ↗</a></section>`;
}
function bind(root,options,rerender){
 for(const[id,key]of[['metric','rankingMetric'],['scope','rankingScope'],['minimum','rankingMinimum']]){
  const control=root.querySelector('#goat-ranking-'+id);if(control)control.onchange=()=>{options.state[key]=id==='minimum'?Number(control.value):control.value;options.state.rankingPage=0;rerender();};
 }
 root.querySelectorAll('[data-ranking-page]').forEach(b=>b.onclick=()=>{options.state.rankingPage=Math.max(0,(options.state.rankingPage||0)+Number(b.dataset.rankingPage));rerender();});
}
window.goatRankings={calculate,render,bind,measures};
})();
