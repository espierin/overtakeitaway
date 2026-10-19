/* Same-race field references, calculated from retained summaries without extra timing data. */
(()=>{'use strict';
const finite=n=>typeof n==='number'&&Number.isFinite(n),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function percentile(values,p){const v=values.filter(finite).sort((a,b)=>a-b);if(!v.length)return null;const i=(v.length-1)*p,a=Math.floor(i),b=Math.ceil(i);return v[a]+(v[b]-v[a])*(i-a);}
const median=v=>percentile(v,.5);
function participants({data,rows}){
 const races=new Set(rows.map(r=>r.race));
 return data.drivers.filter(d=>d.races.some(r=>races.has(r.race)));
}
function compare({data,driver,rows,state,kind}){
 const shared=new Set(rows.map(r=>r.race)),groups=new Map(),entries=[];
 for(const d of data.drivers){
  const own=d.races.filter(r=>shared.has(r.race));if(!own.length)continue;
  const entry={driver:d,rows:own,points:[],available:own.length};entries.push(entry);
  for(const row of own){
   if(kind==='metronome'){
    const laps=window.lapRankings.pointsFor(row,'free',state.compound,data.settings?.lap_rankings?.compounds);
    for(const lap of laps)entry.points.push({race:row.race,lap:lap.lap,value:lap.rank,field:lap.field,n:1});continue;
   }
   const compounds=new Map();for(const obs of row.qualities?.[kind]||[]){if(!finite(obs.value)||state.compound&&obs.compound!==state.compound)continue;if(!compounds.has(obs.compound))compounds.set(obs.compound,[]);compounds.get(obs.compound).push(obs.value);}
   for(const [compound,values]of compounds){const key=row.race+'|'+compound;if(!groups.has(key))groups.set(key,[]);groups.get(key).push({entry,race:row.race,compound,value:median(values)});}
  }
 }
 if(kind!=='metronome'){
  const races=new Map();for(const group of groups.values()){
   // At least three distinct drivers are required for a meaningful field reference.
   if(group.length<3)continue;const center=median(group.map(o=>o.value));
   for(const obs of group){const key=obs.entry.driver.id+'|'+obs.race;if(!races.has(key))races.set(key,{entry:obs.entry,race:obs.race,values:[]});races.get(key).values.push(obs.value-center);}
  }
  for(const r of races.values())r.entry.points.push({race:r.race,value:median(r.values),n:r.values.length});
 }
 for(const row of entries){const values=row.points.map(p=>p.value);Object.assign(row,{n:values.length,races:new Set(row.points.map(p=>p.race)).size,median:median(values),q25:percentile(values,.25),q75:percentile(values,.75),min:values.length?Math.min(...values):null,max:values.length?Math.max(...values):null});}
 const sign=kind==='pitwindow'?-1:1;
 entries.sort((a,b)=>!a.n-!b.n||(a.n&&b.n?sign*(a.median-b.median):0)||a.driver.name.localeCompare(b.driver.name));
 return {entries,profile:entries.find(e=>e.driver.id===driver.id),races:shared.size};
}
function density(values,lo,hi){
 if(values.length<3||hi<=lo)return null;
 const mid=median(values),sd=Math.sqrt(values.reduce((s,v)=>s+(v-mid)**2,0)/values.length),band=Math.max((hi-lo)*.012,1.06*sd*Math.pow(values.length,-.2)),min=Math.max(lo,Math.min(...values)-band*2),max=Math.min(hi,Math.max(...values)+band*2);
 if(min>=max)return null;
 const counts=new Map();for(const value of values)counts.set(value,(counts.get(value)||0)+1);
 const points=Array.from({length:49},(_,i)=>{const x=min+(max-min)*i/48;return[x,[...counts].reduce((s,[v,n])=>s+n*Math.exp(-.5*((x-v)/band)**2),0)]}),peak=Math.max(...points.map(p=>p[1]));return peak?points.map(([x,d])=>[x,d/peak]):null;
}
function render(options){
 const {data,driver,rows,lang,state,kind,highlighted}=options,en=lang==='en',t=(nl,en)=>lang==='en'?en:nl,result=compare(options),measured=result.entries.filter(e=>e.n),values=measured.flatMap(e=>e.points.map(p=>p.value)),format=(v,d=2)=>finite(v)?v.toLocaleString(en?'en-GB':'nl-NL',{maximumFractionDigits:d}):'—',unit=kind==='metronome'?t('rang','rank'):t('procentpunt','percentage points'),score=v=>kind==='metronome'?'P'+format(v,1):(v>0?'+':'')+format(v,3),title=kind==='metronome'?t('Rondetijdrang tegenover het veld','Lap-time rank against the field'):kind==='pitwindow'?t('Pitvensters tegenover het veld','Pit windows against the field'):t('Opwarming tegenover het veld','Warm-up against the field');
 if(!values.length)return`<div class="field-benchmark" data-field-kind="${kind}"><h3>${title}</h3><div class="empty">${t('Onvoldoende gedeelde metingen voor deze veldvergelijking. Ontbrekend is geen nul.','Insufficient shared measurements for this field comparison. Missing does not mean zero.')}</div></div>`;
 let lo=kind==='metronome'?1:Math.min(0,...values),hi=values.reduce((max,v)=>Math.max(max,v),kind==='metronome'?2:0),ticks=[];
 if(kind==='metronome'){const step=Math.max(1,Math.ceil((Math.min(22,hi)-1)/4));hi=Math.min(22,1+4*step);ticks=Array.from({length:5},(_,i)=>1+i*step).filter(v=>v<=hi);if(ticks.at(-1)!==hi)ticks.push(hi);}
 else {if(hi===lo){lo-=.1;hi+=.1;}const raw=(hi-lo)/4,power=10**Math.floor(Math.log10(raw)),factor=[1,2,2.5,5,10].find(n=>n*power>=raw),step=factor*power;lo=Math.floor(lo/step)*step;hi=Math.ceil(hi/step)*step;for(let n=lo;n<=hi+step*.1;n+=step)ticks.push(Math.abs(n)<step*.001?0:n);}
 const L=12,R=708,X=v=>L+((kind==='metronome'?Math.max(lo,Math.min(hi,v)):v)-lo)/(hi-lo)*(R-L),axis=`<svg viewBox="0 0 720 32" role="img" aria-label="${esc(unit)}">${ticks.map(v=>`<line x1="${X(v)}" x2="${X(v)}" y1="19" y2="25" stroke="#7e8b9c"/><text x="${X(v)}" y="14" text-anchor="${v===lo?'start':v===hi?'end':'middle'}">${kind==='metronome'?'P':''}${format(v,kind==='metronome'?1:2)}</text>`).join('')}</svg>`;
 const profile=result.profile;
 return`<div class="field-benchmark" data-field-kind="${kind}"><h3>${title}</h3><p class="muted">${kind==='metronome'?t('Iedere schone ronde in vrije lucht is één datapunt, voor alle coureurs die in dezelfde races meededen. De viool, kwartielen en mediaan gebruiken alle individuele ronderangen samen. Lager is sneller in het gemeten veld.','Every clean lap in clear air is one data point for every driver who took part in the same races. The violin, quartiles and median use all individual lap ranks pooled together. Lower is faster within the measured field.'):t('Afwijking van de veldmediaan in dezelfde race en op dezelfde compound. Per coureur en compound telt de mediaan één keer; de veldreferentie vereist minstens drie coureurs. Daarna krijgt iedere race één waarde.','Difference from the field median in the same race on the same compound. Each driver and compound contributes one median; the field reference requires at least three drivers. Each race then contributes one value.')}</p><div class="chips"><span class="chip">${esc(driver.name)}: <b>${profile?.n?score(profile.median):'—'}</b> ${unit}</span><span class="chip">${profile?.races||0} / ${rows.length} ${t('bruikbare races','usable races')}${kind==='metronome'?' · '+(profile?.n||0)+' '+t('ronden','laps'):''}</span><span class="chip">${measured.length} / ${result.entries.length} ${t('coureurs met metingen','drivers with measurements')}</span></div><p class="note">${kind==='pitwindow'?t('Positief = gunstiger dan de veldmediaan.','Positive = better than the field median.'):kind==='warmup'?t('Negatief = minder vroeg tijdverlies dan de veldmediaan.','Negative = less early time loss than the field median.'):t('Alle geschikte ronden tellen mee. Langere races leveren meer waarnemingen; de dekking vermeldt ook het aantal races.','Every eligible lap counts. Longer races contribute more observations; coverage also reports the number of races.')} ${t('De auto, het verkeer en de omstandigheden zijn niet volledig geïsoleerd; dit is geen algemeen rapportcijfer voor de coureur.','Car, traffic and conditions are not fully isolated; this is not an overall driver rating.')}</p><div class="field-scroll" tabindex="0" role="region" aria-label="${esc(title)}"><div class="field-table"><div class="field-row field-axis"><span>${t('Coureur','Driver')}</span>${axis}<small>${kind==='metronome'?t('Mediaan · ronden','Median · laps'):t('Mediaan · races','Median · races')}</small></div>${result.entries.map(e=>{const own=e.driver.id===driver.id,emphasized=highlighted?highlighted.has(e.driver.id):own,last=e.rows.at(-1),colour=last?.color||e.driver.color||'#a1aab8',shape=e.n?density(e.points.map(p=>p.value),lo,hi):null,description=e.n?e.driver.name+' · '+score(e.median)+' '+unit+' · '+e.n+' '+(kind==='metronome'?t('ronden','laps'):t('races','races')):e.driver.name+' · '+t('Onbekend','Unknown');return`<div class="field-row ${own?'is-profile':''} ${emphasized?'is-highlighted':''} ${e.n?'':'is-missing'}" data-field-driver="${esc(e.driver.id)}" data-field-median="${e.median??''}" data-field-n="${e.n}" title="${esc(description)}"><span class="badge field-driver" style="--driver-color:${esc(colour)}"><span class="number">${esc(last?.number??e.driver.number??'?')}</span><span class="stripe"></span>${esc(e.driver.code)}</span><svg viewBox="0 0 720 38" aria-label="${esc(description)}" role="img">${kind!=='metronome'?`<line x1="${X(0)}" x2="${X(0)}" y1="0" y2="38" stroke="#51d6dd" stroke-dasharray="3 3" opacity=".55"/>`:''}${kind==='metronome'&&e.max>22?`<path class="field-capped-position" d="M700,12L708,19L700,26" fill="none" stroke="#e5bf78" stroke-width="2"><title>${t('Rangen boven P22 aan de rand; alle waarden blijven in de berekening.','Ranks above P22 at the edge; all values remain in calculations.')}</title></path>`:''}${shape?`<path d="M${shape.map(([v,d])=>X(v)+','+(19-d*14)).join('L')}L${shape.slice().reverse().map(([v,d])=>X(v)+','+(19+d*14)).join('L')}Z" fill="${colour}" fill-opacity="${own?0.35:0.15}" stroke="${own?'#b45cff':colour}" stroke-width="1"/>`:''}${e.n?`<line x1="${X(e.min)}" x2="${X(e.max)}" y1="19" y2="19" stroke="${colour}" opacity=".4"/><line x1="${X(e.q25)}" x2="${X(e.q75)}" y1="19" y2="19" stroke="${colour}" stroke-width="5"/><line x1="${X(e.median)}" x2="${X(e.median)}" y1="6" y2="32" stroke="#fff" stroke-width="3"/>`:''}</svg><small>${e.n?score(e.median)+' · n='+e.n:'—'}</small></div>`;}).join('')}</div></div><p class="note">${t('Viool: verdeling van alle meetpunten · dikke lijn: 25%–75% · wit: mediaan. Bij de metronoom telt iedere ronde; bij pitvensters en opwarming iedere bruikbare race. Geen meting blijft leeg. Alleen waargenomen races van de gekozen coureur vormen de referentie.','Violin: distribution of all observations · thick line: 25%–75% · white: median. The metronome uses every lap; pit windows and warm-up use every usable race. Missing measurements remain empty. Only observed races of the selected driver define the reference.')}</p></div>`;
}
window.driverField={compare,render,percentile,participants};
})();
