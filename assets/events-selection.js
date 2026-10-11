function eventSearchMatches(e,query){
 const terms=query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
 return terms.every(term=>{
  // A recognised driver code or number is a driver filter, not an ID/type substring.
  const exact=D.drivers.filter(d=>String(d.driver_number)===term||String(d.code||code(d.driver_number).split(' ').at(-1)).toLocaleLowerCase()===term);
  const drivers=exact.length?exact:D.drivers.filter(d=>String(d.name||'').toLocaleLowerCase().includes(term));
  if(drivers.length)return drivers.some(d=>+d.driver_number===+e.overtaker||+d.driver_number===+e.overtaken);
  return `${full(e.overtaker)} ${code(e.overtaker)} ${full(e.overtaken)} ${code(e.overtaken)} ${e.type} ${e.event_id}`.toLocaleLowerCase().includes(term);
 });
}
function drawEvents(){const rows=currentEvents.filter(e=>eventSearchMatches(e,S.search));$('event-table').innerHTML=`<p>${rows.length} zichtbare regels van ${currentEvents.length} geselecteerde gebeurtenissen. Zoeken verandert alleen deze tabel.</p><table><thead><tr><th>Ronde</th><th>Inhaler</th><th>Gepasseerd</th><th>Type</th><th>Locatie</th><th>Bewijs</th></tr></thead><tbody>${rows.map(e=>`<tr ${hit('events',e.event_id,eventTip(e),e.overtaker)}><td>${esc(e.lap)}</td><td style="color:${color(e.overtaker)}">${esc(code(e.overtaker))}</td><td style="color:${color(e.overtaken)}">${esc(code(e.overtaken))}</td><td>${esc(e.type.replaceAll('_',' '))}</td><td>${esc(e.location_confidence)}</td><td><button data-action="events" data-value="${e.event_id}">Details en bronnen</button></td></tr>`).join('')}</tbody></table>`;}
(function(){
 const section=document.getElementById('section-events');if(!section)return;
 if(section.tagName!=='DETAILS'){
  const details=document.createElement('details');details.className=section.className;details.id=section.id;
  const heading=section.querySelector('h2'),summary=document.createElement('summary');summary.textContent=heading?.textContent||'Gebeurtenissen in de selectie';heading?.remove();details.append(summary);while(section.firstChild)details.append(section.firstChild);section.replaceWith(details);
 }
 drawEvents();
})();
