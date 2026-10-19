/* One measured career profile per driver. No missing-value imputation and no
   selected-driver dependency: highlighting must never move the background. */
(()=>{'use strict';
const VERSION='career-facts-pca-v1';
const features=[
 {id:'grid',nl:'Gemiddelde relatieve gridpositie',en:'Mean relative grid position'},
 {id:'classification',nl:'Gemiddelde relatieve raceklassering',en:'Mean relative race classification'},
 {id:'wins',nl:'Zeges per racestart',en:'Wins per race start'},
 {id:'finished',nl:'Rijdend gefinisht per bekende finishstatus',en:'Running finishes per known finish status'},
 {id:'start_score',nl:'Gecorrigeerde startscore',en:'Adjusted start score'},
 {id:'start_curve_balance',nl:'Gecorrigeerde startcurvebalans',en:'Adjusted start curve balance'},
 {id:'start_gain_boundary',nl:'Winstgrens startcurve',en:'Start curve gain boundary'},
 {id:'race_score',nl:'Racescore · vergelijkbare finishes',en:'Race score · comparable finishes'},
 {id:'race_curve_balance',nl:'Gecorrigeerde racecurvebalans',en:'Adjusted race curve balance'},
 {id:'race_gain_boundary',nl:'Winstgrens racevervolg',en:'Race progression gain boundary'},
 {id:'teammate_pace',nl:'Tempoverschil met teamgenoot',en:'Pace difference to teammate'},
 {id:'metronome',nl:'Metronoom · vast veldpercentiel',en:'Metronome · fixed field percentile'},
 {id:'pit_race_gain',nl:'Pitbalans · mediane tijdwinst per race',en:'Pit balance · median time gained per race'},
 {id:'pit_cycle_gain',nl:'Mediane tijdwinst per kandidaatcyclus',en:'Median time gained per candidate cycle'},
 {id:'qualifying_position',nl:'Mediane kwalificatiepositie',en:'Median qualifying position'},
 {id:'gap_to_pole',nl:'Mediane afstand tot pole',en:'Median gap to pole'},
 {id:'free',nl:'Vrije-baantempo',en:'Clear-air pace'},
 {id:'tyres',nl:'Bandenfluisteraar',en:'Tyre management'},
 {id:'warmup',nl:'Opwarming',en:'Warm-up'},
 {id:'pitwindow',nl:'Pitwindow-specialist',en:'Pit-window specialist'},
 {id:'regularity',nl:'Regelmaat eigen tempo',en:'Own pace consistency'}
];
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const mean=a=>a.length?a.reduce((s,v)=>s+v,0)/a.length:null;

// Jacobi rotations for a small real symmetric covariance matrix.
function eigen(matrix){
 const n=matrix.length,a=matrix.map(r=>[...r]),v=Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>+(i===j)));
 for(let step=0;step<200*n*n;step++){
  let p=0,q=1,max=0;
  for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)if(Math.abs(a[i][j])>max){max=Math.abs(a[i][j]);p=i;q=j;}
  if(max<1e-12)break;
  const angle=.5*Math.atan2(2*a[p][q],a[q][q]-a[p][p]),c=Math.cos(angle),s=Math.sin(angle),app=a[p][p],aqq=a[q][q],apq=a[p][q];
  for(let k=0;k<n;k++)if(k!==p&&k!==q){const x=a[k][p],y=a[k][q];a[k][p]=a[p][k]=c*x-s*y;a[k][q]=a[q][k]=s*x+c*y;}
  a[p][p]=c*c*app-2*s*c*apq+s*s*aqq;a[q][q]=s*s*app+2*s*c*apq+c*c*aqq;a[p][q]=a[q][p]=0;
  for(let k=0;k<n;k++){const x=v[k][p],y=v[k][q];v[k][p]=c*x-s*y;v[k][q]=s*x+c*y;}
 }
 return Array.from({length:n},(_,i)=>{
  const axis=v.map(r=>r[i]),pivot=axis.reduce((best,x,j)=>Math.abs(x)>Math.abs(axis[best])?j:best,0),sign=axis[pivot]<0?-1:1;
  return {value:Math.max(0,a[i][i]),axis:axis.map(x=>sign*x),index:i};
 }).sort((a,b)=>b.value-a.value||a.index-b.index);
}

function summarize(data,{from=data.period[0],to=data.period[1],archive=null}={}){
 const races=new Map(data.races.map(r=>[r.id,r]));
 const archived=new Map((archive?.features||[]).map(r=>[r.driver,r.features]));
 return [...data.drivers].sort((a,b)=>a.id.localeCompare(b.id)).map(driver=>{
  const rows=driver.races.filter(r=>r.year>=from&&r.year<=to),measurements=features.slice(0,4).map(()=>[]);let starts=0,shared=0;
  for(const row of rows){
   const race=races.get(row.race);if(!race)continue;
   // Positive distance/starting-grid evidence is required; DNS/DNQ/withdrawals
   // must not turn an entry or a classification placeholder into a race start.
   if(row.result_outcome==='not_started'||!((finite(row.grid)&&row.grid>0)||row.finish_laps>0||row.finished_on_track===true||row.pitlane_start===true))continue;
   if(row.shared_car_ambiguous||row.source_shared_car){shared++;continue;}
   starts++;
   if(race.starters>1){
    if(finite(row.grid)&&row.grid>=1&&row.grid<=race.starters&&!row.pitlane_start&&!row.source_pitlane_start&&!row.source_conflicts?.grid)measurements[0].push((row.grid-1)/(race.starters-1));
    if(finite(row.finish)&&row.finish>=1&&row.finish<=race.starters&&!row.source_conflicts?.finish&&!['disqualified','not_started'].includes(row.result_outcome))measurements[1].push((row.finish-1)/(race.starters-1));
   }
   // An unknown/conflicting classification cannot establish a win or non-win.
   if(!row.source_conflicts?.finish&&finite(row.finish)&&row.finish>=1)measurements[2].push(+(row.finish===1&&row.result_outcome!=='disqualified'));
   if(typeof row.finished_on_track==='boolean')measurements[3].push(+row.finished_on_track);
  }
  const extra=archived.get(driver.id)||{},matchingPeriod=archive?.period?.[0]===from&&archive?.period?.[1]===to;
  const values=[...measurements.map(mean),...features.slice(4).map(f=>matchingPeriod&&finite(extra[f.id]?.value)?extra[f.id].value:null)],reason=!rows.length?'outside_period':!starts?'no_unambiguous_start':null;
  return {driver:driver.id,values,n:starts,coverage:measurements.map(a=>a.length),entries:rows.length,shared,reason,
   years:[...new Set(rows.map(r=>r.year))].sort((a,b)=>a-b)};
 });
}

function project(records,selected=features.slice(0,4).map(f=>f.id)){
 const indices=selected.map(id=>features.findIndex(f=>f.id===id)).filter(i=>i>=0),chosen=indices.map(i=>features[i]);
 if(indices.length<2)return {available:false,features:chosen,points:[],unplaced:records,reason:'select_two_features'};
 const complete=records.filter(r=>indices.every(i=>finite(r.values[i]))&&!r.reason),included=new Set(complete),unplaced=records.filter(r=>!included.has(r));
 if(complete.length<3)return {available:false,points:[],unplaced:records,reason:'insufficient_profiles'};
 const center=indices.map(j=>mean(complete.map(r=>r.values[j]))),scale=indices.map((j,i)=>Math.sqrt(mean(complete.map(r=>(r.values[j]-center[i])**2))));
 const varying=scale.map((s,i)=>s>1e-12?i:-1).filter(i=>i>=0);
 if(varying.length<2)return {available:false,points:[],unplaced:records,reason:'constant_features'};
 const z=complete.map(r=>varying.map(j=>(r.values[indices[j]]-center[j])/scale[j]));
 const covariance=varying.map((_,i)=>varying.map((_,j)=>mean(z.map(r=>r[i]*r[j])))),axes=eigen(covariance),total=axes.reduce((s,a)=>s+a.value,0);
 return {available:true,version:VERSION,features:chosen,center,scale,constant:chosen.filter((_,i)=>!varying.includes(i)).map(f=>f.id),
  explained:axes.slice(0,2).map(a=>a.value/total),
  loadings:axes.slice(0,2).map(a=>chosen.map((_,j)=>varying.includes(j)?a.axis[varying.indexOf(j)]:0)),
  points:complete.map((r,i)=>({...r,x:z[i].reduce((s,v,j)=>s+v*axes[0].axis[j],0),y:z[i].reduce((s,v,j)=>s+v*axes[1].axis[j],0)})),unplaced};
}
function analyze(data,options={}){return project(summarize(data,options),options.selected);}
window.goatCareerPCA={VERSION,features,eigen,summarize,project,analyze};
})();
