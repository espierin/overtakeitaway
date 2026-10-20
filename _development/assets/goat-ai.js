/* Shared Gemini brief and GitHub-hosted comparison results. No browser secrets. */
(()=>{'use strict';
const answers=new Map();
const finite=v=>typeof v==='number'&&Number.isFinite(v),curveKeys=['start','race','qualifying_position','gap_to_pole','pit_balance'];
function snapshot({data,facts,models,ids,drivers,state,complete=false}){
 const archive=window.phase2GoatMetrics,api=window.goatParameters;
 return{
  schema:'goat-comparison-brief-v2',source:'Overtake It Away',source_period:archive.period,source_revision:archive.revision,source_manifest:archive.manifest,
  controls:{selected_drivers:[...ids],facts_period:[state.from,state.to],race_cohort:'career',curve_years:state.curveyears,chosen_circuits:api.circuitSelection({ids,state}).selected.sort(),all_circuits:!api.circuitSelection({ids,state}).selected.length},
  scope:'Career features and curves use the fixed source period. Career totals below use facts_period. The teammate network uses its full retained period. These scopes are different.',
  network_validation:models.network?.validation||null,
  drivers:ids.map(id=>{
   const driver=drivers.get(id),payload=api.cache.get(id),record=payload?.record,years=driver.races.map(r=>r.year),debut=years.length?Math.min(...years):null,seasons=(facts.drivers[id]?.seasons||[]).filter(s=>s.year>=state.from&&s.year<=state.to),sum=key=>seasons.length&&seasons.every(s=>finite(s[key]))?seasons.reduce((n,s)=>n+s[key],0):null;
   const curves=Object.fromEntries(curveKeys.map(key=>{
    const curve=payload?.curves[key];if(!curve)return[key,{status:'missing'}];
    const runs=api.boundedCurveRuns(curve,key),groups=(curve.groups||[]).map(({observations,...g})=>g),positional=['start','race'].includes(key),positions=groups.filter(g=>g.n>0&&finite(g.position)).map(g=>g.position);
    const samples=groups.map(g=>{
     const x=g.position??g.year,run=runs.find(r=>r.length&&r[0][0]<=x&&r.at(-1)[0]>=x);if(!run)return{x,point:null};
     const point=run.reduce((a,b)=>Math.abs(a[0]-x)<=Math.abs(b[0]-x)?a:b);
     return{x,career_year:positional?null:x-debut+1,point:[...point]};
    });
    return[key,{status:curve.status,unit:curve.unit,origin:curve.origin,result:curve.result,selection:curve.selection,measured:curve.measured,eligible_rows:curve.eligible_rows,estimated:curve.estimated,axis:curve.axis,observed_position_range:positions.length?[Math.min(...positions),Math.max(...positions)]:null,fit_method:curve.fit?.method,fit_band:curve.fit?.band,fit_columns:curve.fit?.columns,groups,samples,...(complete?{displayed_fit_runs:runs}:{})}];
   }));
   const circuit=api.circuitEntries([id],api.circuitSelection({ids,state}).selected)[0];
   return{id,name:driver.name,debut,last_season:years.length?Math.max(...years):null,career_totals:{starts:sum('starts'),wins:sum('wins'),podiums:sum('podiums'),poles:sum('poles'),points:sum('points'),titles:seasons.length?seasons.filter(s=>s.champion&&!s.provisional).length:null},fixed_career_features:record?.features||{},curves,teammate_network:models.network?.drivers?.[id]||null,circuit:{years:circuit.years,circuits:circuit.circuits,races:circuit.races,laps:circuit.n,median_rank:circuit.median,field_score:circuit.field_score}};
  })
 };
}
function prompt(options){
 // One stable request for the same combination, regardless of click order.
 options={...options,ids:[...options.ids].sort()};
 const en=options.lang==='en',brief=snapshot(options);
 const instructions=en?`Compare ONLY the selected Formula 1 drivers using the supplied Overtake It Away data. Write clearly for a general audience. Work toward a reasoned, provisional GOAT choice within this selection.

1. First check periods, usable races, missing values and the meaning of each measure. A null or missing curve is unknown, never zero or evidence of poor driving. Shared races may not exist across eras. Do not claim identical conditions.
2. Describe career achievements, qualifying and pole gap, starts, progression after lap one, clear-air pace/metronome, and pit balance separately. Include concrete numbers, observation counts and uncertainty where available. Compare both sustained performance and peaks without inventing a peak from sparse data.
3. The attached curve samples are existing stored fit points nearest each observed position/season, NOT a new fit or a full image. Read fit_columns. groups contain actual summaries, not model estimates; q25/q75 describe spread, not confidence. Interior estimates may be shown; never extrapolate beyond observed_position_range. Longer careers or more timing measurements are not automatically better. For seasonal comparisons use career_year when aligning debuts. Break years still count.
4. Starts/progression measure position gains, not overtakes or isolated skill. Progression includes only confirmed running finishers. Qualifying pole gaps can include labelled estimates; seconds are not automatically comparable across circuits or eras. Metronome means lap-time rank within the measured field, NOT consistency. Its archived field_percentile is a rescaled rank score, not an empirical percentile. Pit gains reflect an observed gap change, not isolated pit crew or driver skill.
5. Show the teammate-network result only as supporting exploratory evidence within the SAME connected component. Explain network_validation.passes. If false, state the model did not demonstrate better held-out prediction than the zero-gap baseline. Do not use it as a proven era adjustment. PCA axes are not quality ranks and must not determine the winner.
6. Prioritize measured driving qualities over trophies and finishing results. Fixed base weights: pace 30%, progression after lap one 25%, qualifying 20%, starts 15%, career achievements 5%, pit balance 5%. Career includes titles, wins, points, podiums and final classifications collectively: never count those again under pace or progression. Within pace prefer matched clear-air teammate comparisons; metronome ranks are supporting field-speed evidence, not consistency. Within progression prefer origin-adjusted scores/curves rather than raw finish positions. Pit balance is partly a team outcome, not pure driver skill. Include a domain only with adequate comparable evidence for EVERY selected driver. Keep career and pit balance each at 5% maximum when usable, otherwise 0. Redistribute the remaining share among usable qualifying/start/progression/pace domains in their base ratio 20:15:25:30. If none of those four is usable, exclude all six and give no ranking or winner. These are judgement priorities, not fitted coefficients or invented measured scores. Use the same set and weights for everyone; explicitly list included domains, excluded domains and why. Do not double-count correlated measures, invent numerical scores, fill missing data, or silently add outside knowledge. Explain any judgement beyond measured data as an assumption. Do not equate more wins with isolated skill.
7. Fill the JSON fields comparisons, domains, ranking, winner, runner_up, conclusion and confidence. Include the strongest case for every driver and why another reasonable weighting could change the conclusion. If insufficient common evidence prevents a defensible winner, say so plainly and give only explicitly conditional preferences. Do not claim the data prove a universal GOAT.

DATA (JSON):`:`Vergelijk UITSLUITEND de geselecteerde Formule 1-rijders met de meegeleverde gegevens van Overtake It Away. Schrijf in begrijpelijk Nederlands. Werk toe naar een beargumenteerde, voorlopige GOAT-keuze binnen deze selectie.

1. Controleer eerst de perioden, bruikbare races, ontbrekende waarden en betekenis van iedere maat. Null of een ontbrekende curve betekent onbekend, nooit nul of slecht rijden. Rijders uit andere tijdperken hebben mogelijk geen gezamenlijke races. Beweer niet dat omstandigheden gelijk waren.
2. Bespreek loopbaanprestaties, kwalificaties en afstand tot pole, starts, racevervolg na ronde één, vrije-baantempo/metronoom en pitbalans afzonderlijk. Geef concrete cijfers met aantallen en beschikbare onzekerheid. Bespreek langdurige prestaties en pieken, maar verzin geen piek uit heel weinig metingen.
3. De curvesamples zijn bestaande bewaarde fitpunten het dichtst bij iedere gemeten positie of ieder seizoen: GEEN nieuwe berekening en geen volledige afbeelding. Lees fit_columns. groups bevat echte samenvattingen, geen modeluitkomsten; q25/q75 is spreiding, geen betrouwbaarheidsinterval. Binnenliggende schattingen mogen meedoen, extrapoleer nooit buiten observed_position_range. Meer jaren of meer meetgegevens betekenen niet automatisch beter. Vergelijk seizoenscurves via career_year wanneer debuten gelijkgezet worden. Pauzejaren tellen mee.
4. Start en racevervolg meten positiewinst, geen inhaalacties of losstaande rijvaardigheid. Racevervolg telt alleen bevestigde rijdende finishes. De afstand tot pole kan herkenbaar geschatte tijden bevatten; seconden zijn niet vanzelf vergelijkbaar tussen circuits en tijdperken. De metronoom is de rondetijdrang in het gemeten veld, NIET regelmaat. De opgeslagen field_percentile is een herschaalde rangscore, geen empirisch percentiel. Pitwinst is een gemeten verandering van het gat, niet de afzonderlijke kwaliteit van rijder of pitcrew.
5. Gebruik het teamgenootnetwerk alleen als aanvullende, verkennende aanwijzing binnen HETZELFDE verbonden netwerkdeel. Leg network_validation.passes uit. Bij false heeft het model op apart gehouden races geen verbetering aangetoond ten opzichte van de aanname geen verschil. Gebruik het dan niet als bewezen tijdperkcorrectie. PCA-assen zijn geen kwaliteitsranglijst en mogen de winnaar niet bepalen.
6. Laat gemeten rijkwaliteiten zwaarder wegen dan prijzen en eindresultaten. Vaste basisweging: tempo 30%, racevervolg na ronde één 25%, kwalificaties 20%, starts 15%, loopbaanresultaten 5%, pitbalans 5%. Wereldtitels, zeges, punten, podia en eindklasseringen vallen samen onder loopbaanresultaten; tel die nooit nogmaals mee als tempo of racevervolg. Gebruik voor tempo bij voorkeur vergelijkbare vrije-baantijden tegenover teamgenoten; metronoomrangen ondersteunen alleen de snelheid binnen het gemeten veld en meten geen regelmaat. Gebruik bij racevervolg bij voorkeur scores/curves met correctie voor beginpositie, geen ruwe finishposities. Pitbalans is mede een teamresultaat, geen pure rijvaardigheid. Laat een onderdeel alleen meetellen als er voor ALLE geselecteerde rijders voldoende vergelijkbaar bewijs is. Houd loopbaanresultaten en pitbalans elk op maximaal 5% als ze bruikbaar zijn, anders 0. Verdeel het resterende gewicht over bruikbare kwalificatie/start/racevervolg/tempo-onderdelen in de basisverhouding 20:15:25:30. Is geen van die vier bruikbaar, laat dan alle zes onderdelen afvallen en geef geen klassering of winnaar. Deze gewichten zijn gekozen beoordelingsprioriteiten, geen berekende modelcoëfficiënten of gemeten totaalscore. Gebruik voor iedereen dezelfde onderdelen en gewichten. Benoem welke onderdelen meetellen en welke afvallen, met reden. Tel sterk samenhangende cijfers niet dubbel, verzin geen numerieke scores, vul ontbrekende gegevens niet in en voeg niet stilzwijgend externe kennis toe. Benoem oordelen buiten de gemeten gegevens als aanname. Meer zeges zijn geen bewijs van losstaande rijvaardigheid.
7. Vul de JSON-velden comparisons, domains, ranking, winner, runner_up, conclusion en confidence. Geef voor iedere rijder het sterkste argument en leg uit waarom een andere redelijke weging een andere voorlopige winnaar kan geven. Als er onvoldoende gezamenlijke basis is voor een verdedigbare winnaar, zeg dat eerlijk en geef alleen uitdrukkelijk voorwaardelijke voorkeuren. Beweer niet dat de gegevens een universele GOAT bewijzen.

GEGEVENS (JSON):`;
 return window.goatAIFormat.instructions(options.ids,options.lang)+'\n\n'+instructions+'\n'+JSON.stringify(brief)+'\nEND_OF_GOAT_INPUT '+JSON.stringify(options.ids);
}
function render(options){
 const t=(nl,en)=>options.lang==='en'?en:nl;
 return`<section class="research-panel" id="goat-ai"><div class="goat-ai-heading"><h2>The Answer to the Ultimate Question</h2><div class="research-toolbar goat-ai-downloads"><button type="button" id="goat-info-svg">${t('Download SVG','Download SVG')}</button><button type="button" id="goat-info-png">${t('Download PNG','Download PNG')}</button></div></div><div class="goat-ai-start"><a class="research-link" id="goat-ai-request" target="_blank" rel="noopener noreferrer">${t('Stel de vraag','Ask the question')}</a><p>${t('Geen paniek. Deze keer zoeken we een coureur, geen 42.','Don’t panic. This time we are looking for a driver, not 42.')}</p><small>${t('Verstuur de aanvraag op GitHub. Het antwoord verschijnt hier vanzelf.','Submit the request on GitHub. The answer will appear here automatically.')}</small></div><div class="goat-ai-result" aria-live="polite"></div><div class="goat-infographic-preview"></div><p class="goat-ai-status" role="status" aria-live="polite"></p></section>`;
}
function bind(root,options){
 const section=root.querySelector('#goat-ai');if(!section)return;
 bindInfographic(section,options);section.refreshInfographic();const start=section.querySelector('#goat-ai-request');start.href=issueURL(options);start.onclick=()=>watchResult(section,options,prompt(options));
 if(options.ids.length<2){section.querySelector('.goat-ai-start').hidden=true;section.querySelector('.goat-ai-result').textContent=options.lang==='en'?'Select at least two drivers for an AI comparison.':'Kies minstens twee rijders voor een AI-vergelijking.';return;}
 watchResult(section,options,prompt(options));
}
function request(options){return{drivers:[...options.ids],from:options.state.from,to:options.state.to,circuits:window.goatParameters.circuitSelection(options).selected,lang:options.lang,curveyears:options.state.curveyears};}
async function promptHash(text){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(n=>n.toString(16).padStart(2,'0')).join('');}
function issueURL(options){const r=request(options),body='Vergelijk deze selectie met Gemini. De aanvraag wordt uitgevoerd door GitHub Actions.\n\n<!-- goat-ai-request-v1\n'+JSON.stringify(r)+'\n-->';return 'https://github.com/espierin/overtakeitaway/issues/new?'+new URLSearchParams({title:'GOAT AI · '+options.ids.map(id=>options.drivers.get(id).name).join(' · '),body});}
function watchResult(section,options,text){
 clearTimeout(section.goatAITimer);const started=Date.now(),epoch=section.goatAIEpoch=(section.goatAIEpoch||0)+1;
 const check=async()=>{if(!section.isConnected||section.goatAIResult||section.goatAIEpoch!==epoch)return;const ready=document.hidden?false:await loadResult(section,options,text);if(!ready&&section.isConnected&&section.goatAIEpoch===epoch&&Date.now()-started<25*60*1000)section.goatAITimer=setTimeout(check,30000);};
 check();
}
async function loadResult(section,options,text){
 const target=section.querySelector('.goat-ai-result'),t=(nl,en)=>options.lang==='en'?en:nl,esc=window.phase2Research.esc;
 if(!target.textContent)target.textContent=t('Bewaarde vergelijking ophalen…','Loading saved comparison…');
 try{
  if(answers.has(text)){const saved=answers.get(text);showResult(section,options,saved.result,saved);return true;}
  const hash=await promptHash(text),base='https://raw.githubusercontent.com/espierin/overtakeitaway/goat-ai-results/',res=await fetch(base+'index.json?t='+Math.floor(Date.now()/60000),{cache:'no-store'});
  if(!res.ok&&res.status!==404)throw Error('Unavailable');const index=res.ok?await res.json():null;
  if(!index?.results?.[hash]){if(section.isConnected)target.textContent=t('Voor deze selectie is nog geen AI-vergelijking bewaard.','No AI comparison has been saved for this selection yet.');return;}
  const answer=await fetch(base+'results/'+hash+'.json');if(!answer.ok)throw Error('Unavailable');const envelope=await answer.json(),result=envelope.result;
  if(envelope.prompt_sha256!==hash)throw Error('Invalid answer');
  window.goatAIFormat.validate(result,snapshot(options));
  if(!section.isConnected)return;
  answers.set(text,envelope);if(answers.size>20)answers.delete(answers.keys().next().value);showResult(section,options,result,envelope);return true;

 }catch(error){if(section.isConnected)target.textContent=t('De bewaarde AI-vergelijking is nu niet op te halen.','The saved AI comparison cannot be loaded right now.');}
}
function showResult(section,options,result,envelope={}){
 const t=(nl,en)=>options.lang==='en'?en:nl,esc=window.phase2Research.esc,name=id=>options.badge?options.badge(id):esc(options.drivers.get(id)?.name||id);
 window.goatAIFormat.validate(result,snapshot(options));section.goatAIResult=result;section.querySelector('.goat-ai-start').hidden=true;
 const target=section.querySelector('.goat-ai-result');
 target.innerHTML=`<div class="goat-ai-answer"><span class="research-status">${t('GEMINI · INTERPRETATIE','GEMINI · INTERPRETATION')}</span><h3>${result.winner?t('Voorlopige keuze: ','Provisional choice: ')+name(result.winner):t('Geen voldoende onderbouwde winnaar','No sufficiently supported winner')}</h3><p>${esc(result.summary)}</p>${window.phase2Research.table([t('Coureur','Driver'),t('Sterkste argument','Strongest case'),t('Beperking','Limitation')],options.ids.map(id=>result.comparisons.find(r=>r.driver===id)).map(r=>[name(r.driver),esc(r.strength),esc(r.limitation)]))}<p class="goat-ai-conclusion">${esc(result.conclusion)}</p><p class="research-note">${t('Zekerheid van het AI-oordeel','Confidence of the AI judgement')}: ${esc(({low:t('laag','low'),medium:t('middelmatig','medium'),high:t('hoog','high')})[result.confidence])}${envelope.model?' · '+esc(envelope.model):''}${envelope.generated_at?' · '+esc(envelope.generated_at.slice(0,10)):''}</p><details class="research-details"><summary>${t('Weging, aannames en beperkingen','Weighting, assumptions and limitations')}</summary>${window.phase2Research.table([t('Onderdeel','Domain'),t('Gewicht','Weight'),t('Uitleg','Explanation')],result.domains.map(d=>[esc(({career:t('Loopbaan','Career'),qualifying:t('Kwalificaties','Qualifying'),start:t('Starts','Starts'),progression:t('Racevervolg','Progression'),pace:t('Tempo','Pace'),pit_balance:t('Pitbalans','Pit balance')})[d.id]),(d.weight*100).toLocaleString(options.lang==='en'?'en-GB':'nl-NL',{maximumFractionDigits:1})+'%',esc(d.explanation)]))}${[...result.assumptions,...result.limitations].map(v=>`<p>${esc(v)}</p>`).join('')}</details></div>`;

 section.refreshInfographic();
}
function bindInfographic(section,options){
 const status=section.querySelector('[role=status]'),t=(nl,en)=>options.lang==='en'?en:nl,container=section.querySelector('.goat-infographic-preview');
 const graphic=()=>window.goatInfographic.svg(options,section.goatAIResult||null);
 section.refreshInfographic=()=>{container.innerHTML=graphic();};

 const save=(content,type,ext)=>{const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download='overtake-goat-'+options.ids.join('-')+'.'+ext;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 section.querySelector('#goat-info-svg').onclick=()=>save(graphic(),'image/svg+xml;charset=utf-8','svg');
 section.querySelector('#goat-info-png').onclick=async()=>{
  const source=graphic(),url=URL.createObjectURL(new Blob([source],{type:'image/svg+xml;charset=utf-8'})),img=new Image();
  try{await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url;});const canvas=document.createElement('canvas');canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;canvas.getContext('2d').drawImage(img,0,0);const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(!blob)throw Error('PNG');save(blob,'image/png','png');status.textContent=t('Infographic als PNG opgeslagen.','Infographic saved as PNG.');}
  catch(error){status.textContent=t('PNG kon niet worden gemaakt. De SVG-download blijft beschikbaar.','Could not generate PNG. The SVG download is still available.');}finally{URL.revokeObjectURL(url);}
 };

}
window.goatAI={snapshot,prompt,render,bind,request,promptHash,issueURL,loadResult,showResult,watchResult};
})();
