(() => {
  'use strict';
  const app = window.archiveApp;
  const supplement = app?.data?.historical_supplement;
  if (!supplement) return;
  const esc = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const language = () => document.documentElement.lang === 'en' ? 'en' : 'nl';
  const tr = (nl, en) => language() === 'en' ? en : nl;
  const time = v => v == null || v === '' ? '—' : esc(String(v).replace('.', language() === 'nl' ? ',' : '.'));
  let host = document.getElementById('historical-additional-data');
  if (!host) {
    host = document.createElement('section'); host.id = 'historical-additional-data'; host.className = 'card';
    document.getElementById('results').closest('section').after(host);
  }
  const style = document.createElement('style');
  style.textContent = '#historical-additional-data{margin-top:24px}#historical-additional-data details{border:1px solid #344254;border-radius:10px;margin:12px 0;background:#0a101888}#historical-additional-data summary{cursor:pointer;padding:14px 16px;font-weight:700}#historical-additional-data .history-content{padding:0 16px 16px}#historical-additional-data .history-table{overflow:auto}#historical-additional-data table{width:100%;min-width:550px}#historical-additional-data td,#historical-additional-data th{padding:7px 9px;text-align:left;border-bottom:1px solid #344254}#historical-additional-data .source-note{color:#a9b8ca;font-size:13px;line-height:1.6}#historical-additional-data ul{line-height:1.8}#historical-additional-data .history-count{color:#51d6dd;font-weight:500;margin-left:8px}';
  document.head.append(style);
  const labels = {
    'qualifying-results': ['Kwalificatie', 'Qualifying'],
    'fastest-laps': ['Snelste ronden', 'Fastest laps'],
    'free-practice-1-results': ['Vrije training 1', 'Free practice 1'],
    'free-practice-2-results': ['Vrije training 2', 'Free practice 2'],
    'free-practice-3-results': ['Vrije training 3', 'Free practice 3'],
    'free-practice-4-results': ['Vrije training 4', 'Free practice 4'],
    'warming-up-results': ['Warm-up', 'Warm-up'],
    'pre-qualifying-results': ['Prekwalificatie', 'Pre-qualifying'],
    'qualifying-1-results': ['Kwalificatiesessie 1', 'Qualifying session 1'],
    'qualifying-2-results': ['Kwalificatiesessie 2', 'Qualifying session 2']
  };
  function render() {
    document.querySelectorAll('[data-history-note]').forEach(e => {
      const value = e.dataset[language()];
      if (value && e.textContent !== value) e.textContent = value;
    });
    const opened = new Set([...host.querySelectorAll('details[open]')].map(e => e.dataset.historySection));
    const chosen = app.selected();
    const badge = r => {
      const candidates = chosen.filter(d => supplement.entry_drivers[d.id] === r.driverId && d.number === Number(r.driverNumber));
      return candidates.length ? app.badge(candidates[0]) : esc(r.driverId);
    };
    const details = (key, name, html, count) => `<details data-history-section="${key}"${opened.has(key) ? ' open' : ''}><summary>${esc(name)}${count == null ? '' : '<span class="history-count">'+count+'</span>'}</summary><div class="history-content">${html}</div></details>`;
    let html = '<h2>' + tr('Aanvullend historisch racearchief', 'Additional historical race archive') + '</h2>';
    html += '<p class="source-note">' + tr('Beschikbare brongegevens voor deze race. Tabellen volgen de coureurselectie; — betekent onbekend.', 'Available source observations for this race. Tables follow the driver selection; — means unknown.') + '</p>';
    for (const [key, names] of Object.entries(labels)) {
      const all = supplement.sessions[key]; if (!all?.length) continue;
      const rows = all.filter(r => chosen.some(d=>supplement.entry_drivers[d.id]===r.driverId && (!r.driverNumber || d.number===Number(r.driverNumber))));
      const q = key.includes('qualifying') && all.some(r => r.q1 || r.q2 || r.q3);
      const fastest = key === 'fastest-laps';
      const headers = [tr('Positie', 'Position'), tr('Coureur', 'Driver'), ...(q ? ['Q1','Q2','Q3'] : [tr('Tijd', 'Time')]), ...(fastest ? [tr('Ronde', 'Lap')] : [])];
      const body = rows.map(r => '<tr><td>'+esc(r.positionText)+'</td><td>'+badge(r)+'</td>'+ (q ? ['q1','q2','q3'].map(k => '<td>'+time(r[k])+'</td>').join('') : '<td>'+time(r.time)+'</td>') + (fastest ? '<td>'+esc(r.lap || null)+'</td>' : '')+'</tr>').join('');
      html += details(key, tr(...names), '<div class="history-table"><table><thead><tr>'+headers.map(h=>'<th>'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+body+'</tbody></table></div>', rows.length);
    }
    const best = supplement.fia?.best_sectors || [];
    if (best.length) {
      const rows = best.filter(r => chosen.some(d => d.number === r.number));
      const body = rows.map(r => '<tr><td>'+app.badge(chosen.find(d=>d.number===r.number))+'</td><td>'+r.sector+'</td><td>'+time(r.seconds.toFixed(3))+' s</td></tr>').join('');
      html += details('best-sectors', tr('Beste sectortijden in de race', 'Best race sector times'), '<p class="source-note">'+tr('Persoonlijk beste tijd per sector over de hele race. Dit zijn geen sectortijden per ronde en ze vormen samen geen gemeten ronde.', 'Personal best for each sector across the whole race. These are not per-lap sector times and their sum is not a measured lap.')+'</p><div class="history-table"><table><thead><tr><th>'+tr('Coureur','Driver')+'</th><th>Sector</th><th>'+tr('Tijd','Time')+'</th></tr></thead><tbody>'+body+'</tbody></table></div>', rows.length);
    }
    const speedRows = supplement.historical_chart?.maximum_speeds?.length ? supplement.historical_chart.maximum_speeds : (supplement.fia?.maximum_speeds || []).map(r=>({...r,point:['Intermediate 1','Intermediate 2','Finishing Line'][r.location-1]}));
    if (speedRows.length) {
      const rows = speedRows.filter(r => chosen.some(d=>d.number===r.number && (!r.entry_id || d.id===r.entry_id)));
      const point = p => ({'Intermediate 1':tr('Meetpunt 1','Intermediate 1'),'Intermediate 2':tr('Meetpunt 2','Intermediate 2'),'Finishing Line':tr('Finishlijn','Finishing line'),'Speed Trap':tr('Snelheidsmeting','Speed trap')})[p] || p;
      const body = rows.map(r=>'<tr><td>'+app.badge(chosen.find(d=>d.number===r.number))+'</td><td>'+esc(point(r.point))+'</td><td>'+time(Number(r.kph).toFixed(1))+' km/h</td></tr>').join('');
      html += details('maximum-speeds',tr('Maximumsnelheden per meetpunt','Maximum speeds by timing point'),'<p class="source-note">'+tr('De hoogste gemeten snelheid van de rijder bij ieder meetpunt over de race. Dit is geen doorlopende snelheidstelemetrie.','The driver’s highest measured speed at each timing point during the race. This is not continuous speed telemetry.')+'</p><div class="history-table"><table><thead><tr><th>'+tr('Coureur','Driver')+'</th><th>'+tr('Meetpunt','Timing point')+'</th><th>'+tr('Snelheid','Speed')+'</th></tr></thead><tbody>'+body+'</tbody></table></div>',rows.length);
    }
    const historicWeather = supplement.historical_chart?.weather_description;
    if (historicWeather) html += details('weather-description',tr('Historische weersbeschrijving','Historical weather description'),'<p>'+esc(historicWeather)+'</p><p class="source-note">'+tr('Oorspronkelijke beschrijving uit STATS F1, in het Engels; geen gemeten weerreeks.','Original STATS F1 description in English; not a measured weather time series.')+'</p>');
    const tyre = supplement.tyre_changes || [];
    if (tyre.length) {
      const rows = tyre.filter(r => chosen.some(d => d.id === r.entry_id));
      const body = rows.map(r => '<tr><td>'+app.badge(chosen.find(d=>d.id===r.entry_id))+'</td><td>'+r.lap+'</td><td>'+esc(r.from)+'</td><td>'+esc(r.to)+'</td></tr>').join('');
      html += details('tyre-changes', tr('Geregistreerde bandenwissels', 'Recorded tyre changes'), '<div class="history-table"><table><thead><tr><th>'+tr('Coureur','Driver')+'</th><th>'+tr('Ronde','Lap')+'</th><th>'+tr('Van','From')+'</th><th>'+tr('Naar','To')+'</th></tr></thead><tbody>'+body+'</tbody></table></div><p class="source-note">'+tr('Bandengegevens uit Pirelli-verslagen; alleen expliciet genoemde wissels. Een ontbrekende wissel betekent niet dat er geen stop was.', 'Tyre observations from Pirelli releases; only explicitly reported changes. A missing change does not mean there was no stop.')+'</p>', rows.length);
    }
    const context = supplement.timing_context;
    if (context) {
      const weather = context.weather;
      const rows = (weather.Time || []).map((t,i) => '<tr><td>'+time(Number(t).toFixed(1))+' s</td><td>'+time(weather.AirTemp[i])+' °C</td><td>'+time(weather.TrackTemp[i])+' °C</td><td>'+time(weather.Humidity[i])+'%</td><td>'+(weather.Rainfall[i]==null?'—':tr(weather.Rainfall[i]?'Ja':'Nee',weather.Rainfall[i]?'Yes':'No'))+'</td></tr>').join('');
      html += details('weather', tr('Weerwaarnemingen','Weather observations'), '<p class="source-note">'+tr('Tijd in seconden vanaf het begin van de oorspronkelijke timingsessie.','Time in seconds from the beginning of the original timing session.')+'</p><div class="history-table"><table><thead><tr><th>'+tr('Sessietijd','Session time')+'</th><th>'+tr('Lucht','Air')+'</th><th>'+tr('Baan','Track')+'</th><th>'+tr('Vochtigheid','Humidity')+'</th><th>'+tr('Regen','Rain')+'</th></tr></thead><tbody>'+rows+'</tbody></table></div>', weather.Time?.length);
      const control = context.race_control;
      const messages = (control.Time || []).map((t,i) => '<tr><td>'+esc(t)+'</td><td>'+esc(control.Lap?.[i])+'</td><td>'+esc(control.Flag?.[i])+'</td><td>'+esc(control.Message?.[i])+'</td></tr>').join('');
      html += details('race-control', tr('Wedstrijdleiding en vlagsituaties','Race control and flags'), '<p class="source-note">'+tr('Oorspronkelijke berichten van de wedstrijdleiding, in het Engels. De brontijd is behouden; er is geen tijdzone afgeleid.','Original race-control messages in English. The source clock is retained; no timezone is inferred.')+'</p><div class="history-table"><table><thead><tr><th>'+tr('Brontijd','Source time')+'</th><th>'+tr('Ronde','Lap')+'</th><th>'+tr('Vlag','Flag')+'</th><th>'+tr('Oorspronkelijk bericht','Original message')+'</th></tr></thead><tbody>'+messages+'</tbody></table></div>',control.Time?.length);
    }
    const colourSources = [...new Map(chosen.filter(d=>d.color_source).map(d=>[d.color_source.source_url,d.color_source])).values()];
    const sources = '<p><a href="'+esc(supplement.source.url)+'" target="_blank" rel="noopener">F1DB · CC BY 4.0</a></p>'+
      (supplement.historical_chart?.source ? '<p><a href="'+esc(supplement.historical_chart.source.url)+'" target="_blank" rel="noopener">mclarenmp4-22/f1resultsdatabase · ODbL 1.0</a> · STATS F1 / Formula1.com / MotorsportStats</p><p class="source-note">'+tr('Rondekaarten bevatten bronposities per gereden ronde. Gedeelde auto’s worden alleen aan een rijder gekoppeld als de bron die koppeling ondubbelzinnig maakt.','Lap charts contain source positions for each completed lap. Shared cars are assigned to a driver only when that assignment is unambiguous in the source.')+'</p>' : '') +
      '<p class="source-note">'+tr('Oorspronkelijke uitslagen blijven bewaard. Aanvullingen hebben een bronverwijzing; verschillen tussen bronnen staan in het controlelog. Teamkleuren zijn historische kleurreferenties; hexwaarden zijn schematisch. Privé-inschrijvingen kunnen afwijken. Oorspronkelijke timingkleuren gaan voor.', 'Original results are retained. Additions have source provenance; disagreements remain in the audit log. Team colours are historical colour references; hex values are illustrative. Private entrants may differ. Original timing colours take precedence.')+'</p>'+
      '<p class="source-note">'+tr('Snelste-ronderecords vullen geen ontbrekende rondeposities in. Pitstopduur is de geregistreerde bronduur en wordt niet als stilstandtijd geïnterpreteerd.', 'Fastest-lap records do not fill missing lap positions. A pit-stop duration is the source-reported duration and is not interpreted as stationary time.')+'</p>'+
      (supplement.fia?.documents?.length ? '<ul>'+supplement.fia.documents.map(d=>'<li><a href="'+esc(d.archive_url || d.url)+'" target="_blank" rel="noopener">FIA · '+esc(d.label?.[language()] || d.title)+'</a>'+(d.archive_url?' · <span>'+tr('Archiefkopie','Archived copy')+' '+esc(d.capture_timestamp.slice(0,4)+'-'+d.capture_timestamp.slice(4,6)+'-'+d.capture_timestamp.slice(6,8))+'</span>':'')+'</li>').join('')+'</ul>' : '') +
      (supplement.pirelli_sources?.length ? '<ul>'+supplement.pirelli_sources.map(d=>'<li><a href="'+esc(d.url)+'" target="_blank" rel="noopener">Pirelli · '+tr('Raceverslag','Race report')+'</a></li>').join('')+'</ul>' : '') +
      (colourSources.length?'<p>'+tr('Gedateerde kleurreferenties voor de geselecteerde teams','Dated colour references for the selected teams')+'</p><ul>'+colourSources.map(c=>'<li><a href="'+esc(c.archive_url || c.source_url)+'" target="_blank" rel="noopener">'+esc(c.team || '')+' · '+esc(c.from_year)+(c.to_year!==c.from_year?'–'+esc(c.to_year):'')+'</a></li>').join('')+'</ul>':'')+
      '<p><a href="data/normalized/historical-supplement.json">'+tr('Aanvullende brongegevens en controlelog','Additional source data and audit log')+'</a> · <a href="../../../../../analyses/sources/historical/coverage-report.html">'+tr('Dekking van het historische archief','Historical archive coverage')+'</a></p>';
    html += details('sources', tr('Bronnen en historische datadekking', 'Sources and historical data coverage'), sources);
    host.innerHTML = html;
  }
  render();
  let queued = false;
  const update = () => { if (queued) return; queued = true; queueMicrotask(() => {queued=false; render();}); };
  document.addEventListener('click', e => { if (!host.contains(e.target) && e.target.closest('button')) update(); });
  document.addEventListener('input', e => { if (!host.contains(e.target)) update(); });
  let lastLanguage = language();
  new MutationObserver(() => {
    const next = language();
    if (next !== lastLanguage) { lastLanguage = next; update(); }
  }).observe(document.documentElement, {attributes:true,attributeFilter:['lang']});
})();
