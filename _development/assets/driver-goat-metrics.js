/* Fixed career features shared by the archived GOAT/PCA dataset. */
(()=>{'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x),median=a=>window.pitProgrammes.quantile(a,.5);
function build({data,driver,state={},includePitCurveFit=true}){
 const from=state.yearMin??data.period[0],to=state.yearMax??data.period[1],rows=driver.races.filter(r=>r.year>=from&&r.year<=to),compounds=data.settings?.lap_rankings?.compounds;
 const laps=rows.flatMap(row=>window.lapRankings.pointsFor(row,'free','',compounds)),normalized=laps.filter(p=>p.field>1).map(p=>100*(1-(p.rank-1)/(p.field-1))),pace=rows.filter(r=>finite(r.comparison?.pace_delta_pct));
 const pitState={pitmode:'equal',pitwindow:'programme',pitflags:'green'},pit=window.pitProgrammes.model({data,driver,rows,state:pitState}),cycles=data.cycles.filter(c=>c.driver===driver.id&&rows.some(r=>r.race===c.race)),stats=window.pitProgrammes.statistics(pit,cycles);
 const metric=(value,unit,n,races,method)=>({value:finite(value)?value:null,unit,n,races,status:finite(value)?'available':'no_measurements',method});
 const more={};for(const kind of ['free','tyres','warmup','pitwindow','regularity']){const points=window.driverQualities.observations(rows,kind);more[kind]=metric(median(points.map(p=>p.value)),kind==='tyres'?'percent_per_10_laps':'percent',points.length,points.length,'production driverQualities.observations; median of own race medians');}
 const raceMap=new Map(data.races.map(r=>[r.id,r])),circuits=new Map();
 for(const row of rows){const race=raceMap.get(row.race);if(!race)continue;const points=window.lapRankings.pointsFor(row,'free','',compounds),free=window.driverQualities.observations([row],'free')[0];if(!points.length&&!free&&!row.comparison)continue;
  const key=race.layout||race.circuit_id;if(!circuits.has(key))circuits.set(key,{layout:key,circuit_id:race.circuit_id,name:race.circuit||race.name,races:[]});
  const clock=row.shared_car_ambiguous||row.source_shared_car?null:window.pitProgrammes.entries(race).get(row.number);
  circuits.get(key).races.push({race:race.id,year:race.year,date:race.date,name:race.name,layout:race.layout,free_pace_pct:free?.value??null,free_observations:free?.obs||[],matched_pace_pct:row.comparison?.pace_delta_pct??null,matched_mean_lap_seconds:row.comparison?.mean_lap_seconds??null,matched_teammate:row.comparison?.teammate??null,lap_columns:['lap','rank','field','compound','flags','lap_milliseconds'],laps:points.map(p=>[p.lap,p.rank,p.field,p.compound,p.flags,finite(clock?.times[p.lap])?clock.times[p.lap]:null])});
 }
 const circuitRows=[...circuits.values()].map(c=>{const laps=c.races.flatMap(r=>r.laps),times=laps.map(p=>p[5]).filter(finite);return{...c,years:[...new Set(c.races.map(r=>r.year))].sort((a,b)=>a-b),summary:{races:c.races.length,laps:laps.length,timed_laps:times.length,median_lap_seconds:finite(median(times))?median(times)/1000:null,median_rank:median(laps.map(p=>p[1])),median_field_percentile:median(laps.filter(p=>p[2]>1).map(p=>100*(1-(p[1]-1)/(p[2]-1)))),median_free_pace_pct:median(c.races.map(r=>r.free_pace_pct))}};});
 return {driver:driver.id,period:[from,to],features:{...more,
  teammate_pace:metric(median(pace.map(r=>r.comparison.pace_delta_pct)),'percent',pace.length,pace.length,'production comparison.pace_delta_pct; median across own races, including labelled production fallbacks'),
  metronome:metric(median(normalized),'field_percentile',normalized.length,new Set(laps.filter(p=>p.field>1).map(p=>p.race)).size,'median of 100 × (1 − (rank − 1) / (field − 1)); every clean clear-air lap in own career; selection-independent'),
  metronome_rank:metric(median(laps.map(p=>p.rank)),'rank',laps.length,new Set(laps.map(p=>p.race)).size,'production lapRankings.pointsFor free; median of all own lap ranks'),
  pit_race_gain:metric(stats.race_gain_s,'seconds',stats.races,stats.races,'production pitProgrammes.model; median of race medians; equal stops, completed programmes, no recorded SC/VSC'),
  pit_comparison_gain:metric(stats.comparison_gain_s,'seconds',stats.comparisons,stats.races,'median of opponent-programme comparisons; observations within a race are dependent'),
  pit_cycle_gain:metric(stats.candidate_cycle_gain_s,'seconds',cycles.length,new Set(cycles.map(c=>c.race)).size,'median gain_seconds of all accepted candidate cycles; observations within a race are dependent')
 },pit_filters:pitState,pit_curve:window.pitProgrammes.seasonSnapshot(pit,{includeFit:includePitCurveFit}),pit_seasons:window.pitProgrammes.seasons(pit).map(g=>({year:g.year,races:g.values.length,comparisons:g.comparisons,median:g.median,q25:g.q25,q75:g.q75})),
 circuits:circuitRows,circuit_definition:'Own clean clear-air lap ranks with retained millisecond clocks where available. Layout, race, season, lap, field and compound are preserved. Missing absolute times remain null. Raw lap times from different layouts/seasons are not a fair skill comparison.',pace_methods:Object.fromEntries([...new Set(pace.map(r=>r.comparison.method))].map(method=>[method,pace.filter(r=>r.comparison.method===method).length]))};
}
window.driverGoatMetrics={version:'fixed-career-features-v1',build};
})();
