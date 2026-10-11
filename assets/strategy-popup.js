// A stint is a tyre set. Equal compounds must retain their separate boundaries.
function strategyTyreSegments(c,n,lo,hi){
 const stints=(D.tyres?.stints||[]).filter(s=>s.driver_number===n).sort((a,b)=>b.lap_start-a.lap_start),laps=new Map((c.lap_details||[]).filter(r=>r.driver===n).map(r=>[r.lap,r]));
 for(const r of D.all_laps||[])if(r.driver===n)laps.set(r.lap,r);
 const stops=new Set((D.explorer?.pit||[]).filter(p=>p.driver===n).map(p=>p.lap));
 stops.add(n===c.early_driver?c.early_stop_lap:c.late_stop_lap);
 const segments=[];let previous=null;
 for(let lap=lo+1;lap<=hi;lap++){
  const r=laps.get(lap),stint=stints.find(s=>s.lap_start<=lap&&s.lap_end>=lap),compound=r?.tyre?.compound||stint?.compound||'UNKNOWN',last=segments.at(-1);
  const newSet=previous&&(stint&&previous.stint?stint!==previous.stint:stops.has(lap-1)||Number.isFinite(r?.tyre?.age)&&Number.isFinite(previous.age)&&r.tyre.age<previous.age);
  if(last&&last.compound===compound&&!newSet)last.end=lap;
  else segments.push({start:lap-1,end:lap,compound,stint:stint?.stint_number??null});
  previous={stint,age:r?.tyre?.age};
 }
 return segments;
}
function showStrategyDetail(id){
 window.strategyPopupCycle=id;const T=(nl,en)=>window.siteLanguage?.language==='en'?en:nl;
 const c=D.cycles.find(c=>c.cycle_id===id);if(!c)return;const winner=c.beneficiary||(c.strategy==='undercutsituatie'?c.early_driver:c.late_driver),other=winner===c.early_driver?c.late_driver:c.early_driver,sign=winner===c.early_driver?1:-1,rows=(c.detail_trace||c.trace).map(p=>({...p,gap:p.gap*sign}));
 const fmt=x=>Number(x).toLocaleString(T('nl-NL','en-GB'),{maximumFractionDigits:3});
 const w=800,h=485,left=65,right=775,top=35,bottom=350,lo=Math.floor(Math.min(...rows.map(p=>p.lap))),hi=Math.ceil(Math.max(...rows.map(p=>p.lap))),low=Math.min(0,...rows.map(p=>p.gap)),high=Math.max(0,...rows.map(p=>p.gap)),step=high-low<=7?.5:Math.max(1,Math.ceil((high-low)/14)),min=Math.floor(low/step)*step-step,max=Math.ceil(high/step)*step+step,X=lap=>left+(lap-lo)/Math.max(1,hi-lo)*(right-left),Y=gap=>bottom-(gap-min)/(max-min)*(bottom-top);
 let svg=svgStart(w,h,T('Tijdsverschil pitstopcyclus','Pit-stop cycle time gap'));for(let n=min;n<=max+1e-8;n+=step)svg+=line([[left,Y(n)],[right,Y(n)]],n===0?'#fff':'#596273',n===0?2.5:.5)+text(left-10,Y(n)+4,fmt(n),'text-anchor="end"');for(let lap=lo;lap<=hi;lap++)svg+=text(X(lap),bottom+25,lap,'text-anchor="middle"');
 svg+=line(rows.map(p=>[X(p.lap),Y(p.gap)]),color(winner),2);
 for(const p of rows)svg+=`<circle cx="${X(p.lap)}" cy="${Y(p.gap)}" r="${p.sector===3||!p.sector?4:3}" fill="${color(winner)}" ${tip(`<b>${T('Ronde','Lap')} ${p.race_lap||p.lap} · ${T('sector','sector')} ${p.sector||3}</b><p>${fmt(p.gap)} s</p>`)}/>`;
 for(const [lap,n,label] of [[c.early_stop_lap,c.early_driver,'Eerste stop'],[c.late_stop_lap,c.late_driver,'Tweede stop'],[c.completed_lap,winner,'Beoordeling']]){
  svg+=line([[X(lap),top],[X(lap),bottom]],color(n),1,'stroke-dasharray="4 4"');
  if(label==='Beoordeling')svg+=text(X(lap)+5,top+10,T(label,'Assessment'),`transform="rotate(90 ${X(lap)+5} ${top+10})"`);
  else{const d=D.drivers.find(d=>d.driver_number===n),name=d?.code||code(n).split(' ').at(-1),badgeRight=c.strategy==='overcutsituatie'?label==='Eerste stop':label==='Tweede stop',badgeX=X(lap)+(badgeRight?29:-7);svg+=`<g data-strategy-stop="${lap}" data-driver="${n}" data-strategy-stop-side="${badgeRight?'right':'left'}" transform="translate(${badgeX} ${top+10}) rotate(90)"><title>${esc(T(label,label==='Eerste stop'?'First stop':'Second stop'))} · ${esc(d?.name||full(n))}</title><rect width="27" height="22" rx="3" fill="#f5f7fa"/><text x="13.5" y="16" text-anchor="middle" style="fill:#080c14;font-size:13px;font-weight:900;font-style:italic">${esc(n)}</text><rect x="33" y="1" width="4" height="20" fill="${color(n)}"/><text x="43" y="16" style="fill:#fff;font-size:14px;font-weight:700">${esc(name)}</text></g>`;}
 }

 svg+=text(w/2,bottom+45,T('Ronde','Lap'),'text-anchor="middle"')+text(16,(top+bottom)/2,T('Tijdsverschil (s)','Time gap (s)'),`transform="rotate(-90 16 ${(top+bottom)/2})" text-anchor="middle"`);
 for(const [index,n] of [winner,other].entries()){
  const y=bottom+66+index*36,segments=strategyTyreSegments(c,n,lo,hi);
  const driver=D.drivers.find(d=>d.driver_number===n),label=driver?.code||code(n).split(' ').at(-1);svg+=`<rect x="2" y="${y+3}" width="23" height="18" rx="3" fill="#f5f7fa"/>`+text(13.5,y+16,n,'text-anchor="middle" style="fill:#080c14;font-size:11px;font-weight:900;font-style:italic"')+`<rect x="29" y="${y+4}" width="3" height="16" fill="${color(n)}"/>`+text(36,y+16,label,'style="font-size:11px;font-weight:bold"');
  for(const seg of segments){const fullWidth=X(seg.end)-X(seg.start),gap=Math.min(3,fullWidth*.2),x=X(seg.start)+gap/2,width=fullWidth-gap,fill=C[seg.compound]||'#526179',label=seg.compound==='UNKNOWN'?'?':seg.compound[0];svg+=`<rect data-strategy-tyre="${n}" data-compound="${seg.compound}" data-stint="${seg.stint??''}" data-start-lap="${seg.start+1}" data-end-lap="${seg.end}" x="${x}" y="${y}" width="${width}" height="24" rx="3" fill="${fill}" stroke="#181f2c" ${tip(actionDriverBadge(n)+`<p>${esc(T(CN[seg.compound]||'onbekend',{SOFT:'soft',MEDIUM:'medium',HARD:'hard',INTERMEDIATE:'intermediate',WET:'wet'}[seg.compound]||'unknown'))} · ${seg.start+1}–${seg.end}</p>`)}/>`;if(width>18)svg+=text(x+width/2,y+16,label,`text-anchor="middle" style="font-size:12px;font-weight:bold;fill:${['MEDIUM','HARD'].includes(seg.compound)?'#080c14':'#fff'}"`);}
 }

 const battle=D.positions.find(p=>p.driver===other&&p.lap===c.baseline_lap)?.position;
 const delta=c.late_stop_lap-c.early_stop_lap;
 $('event-detail').innerHTML='<div class="strategy-popup-heading"><h2>'+(c.strategy==='undercutsituatie'?'Undercut':'Overcut')+'</h2>'+actionDriverBadge(winner)+'<span class="strategy-arrow">➜</span>'+actionDriverBadge(other)+'</div><div class="strategy-popup-summary">'+(battle?'<p><span>'+T('Strijd om positie','Battle for position')+'</span><strong>P'+battle+'</strong></p>':'')+'<p><span>'+T('Verschil in stopronde','Delta in pit-stop lap')+'</span><strong>'+delta+(delta===1?T(' ronde',' lap'):T(' ronden',' laps'))+(winner===c.early_driver?T(' eerder',' earlier'):T(' later',' later'))+'</strong></p><p><span>Netto tijdwinst</span><strong>'+fmt(c.gain_early_driver*sign)+' s</strong></p></div>'+svg+'</svg><p>'+T('Negatief: voor de tegenstander. Positief: achter de tegenstander.','Negative: ahead of the opponent. Positive: behind the opponent.')+'</p>' ;hideTip();if(!$('event-dialog').open)$('event-dialog').showModal();
}

(()=>{let previous=window.siteLanguage?.language||document.documentElement.lang;new MutationObserver(()=>{const language=window.siteLanguage?.language||document.documentElement.lang;if(language===previous)return;previous=language;if(document.querySelector('#event-dialog[open] .strategy-popup-summary')&&window.strategyPopupCycle)showStrategyDetail(window.strategyPopupCycle);}).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});})();
