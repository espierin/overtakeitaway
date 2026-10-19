/* Archive exactly measured driver features; resumable CPU workers for intervals. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),zlib=require('node:zlib'),crypto=require('node:crypto'),{Worker,isMainThread,parentPort,workerData}=require('node:worker_threads');
const root=path.resolve(__dirname,'../..'),hash=b=>crypto.createHash('sha256').update(b).digest('hex'),engines=['qualifying-years','driver-qualities','lap-rankings','pit-programmes','driver-goat-metrics','goat-pca'];
function runtime(){const c={window:{}};vm.createContext(c);for(const name of engines)vm.runInContext(fs.readFileSync(path.join(root,'_development/assets/'+name+'.js'),'utf8'),c);return c.window;}
if(!isMainThread){const W=runtime(),D=workerData.data;parentPort.on('message',job=>{try{
 job.pit_curve=W.pitProgrammes.completeSeasonSnapshot(job.pit_curve);
 const driver=D.drivers.find(d=>d.id===job.driver),comparison=W.driverQualities.startComparison({data:D,driver,rows:driver.races,state:{yearMin:D.period[0],yearMax:D.period[1]},observation:W.driverQualities.raceObservation});
 const metric=(value,unit,status,interval=null)=>({value:value??null,unit,status,interval,n:comparison.matched.length,races:comparison.own,reference_races:comparison.referenceRaces});
 Object.assign(job.features,{
  race_score:metric(comparison.score,'score_0_100',comparison.score===null?'insufficient_matched_finishes':'available',comparison.interval),
  race_curve_balance:metric(comparison.adjustedCurve.balance,'percentage_points',comparison.adjustedCurve.balance===null?'insufficient_adjacent_matched_positions':'available',comparison.adjustedCurve.interval),
  race_gain_boundary:{value:job.boundary,unit:'lap_one_position',status:job.boundary!==null?'found':job.curve_status==='available'?'not_found':'insufficient_data',method:'exact frozen production race curve gain boundary; two consecutive positions with modeled gain ≥ 0.5'}
 });
 job.race_score_context={measured_positions:comparison.gridNodes.map(g=>g.grid),matched:comparison.matched.length,finishes:comparison.own,reference_races:comparison.referenceRaces,bootstrap:comparison.iterations,valid_draws:comparison.bootstrapValid};delete job.boundary;delete job.curve_status;
 const bytes=Buffer.from(JSON.stringify(job)+'\n'),compressed=zlib.gzipSync(bytes,{level:9}),file=job.driver+'.json.gz';fs.writeFileSync(path.join(workerData.output,file),compressed);parentPort.postMessage({driver:job.driver,file,sha256:hash(compressed),bytes:compressed.length,record:job});
 }catch(e){parentPort.postMessage({error:e.stack})}});
}else main().catch(e=>{console.error(e);process.exitCode=1});
async function main(){
 const inputs={},read=name=>{const p='_development/data/'+name+'.json.gz',bytes=fs.readFileSync(path.join(root,p));inputs[p]=hash(bytes);return JSON.parse(zlib.gunzipSync(bytes));},D=read('profiles'),strategy=read('strategy'),W=runtime();
 for(const d of D.drivers)d.races=d.races.map(r=>Object.fromEntries(D.driver_race_columns.map((k,i)=>[k,r[i]])));delete D.driver_race_columns;
 D.cycles=strategy.cycles.rows.map(r=>Object.fromEntries(strategy.cycles.columns.map((k,i)=>[k,r[i]])));for(const r of D.races)if(strategy.programs[r.id])r.pit_programmes.entries=strategy.programs[r.id];
 const indexPath='_development/data/driver-curves/'+D.period.join('-')+'/index.json',curveIndex=JSON.parse(fs.readFileSync(path.join(root,indexPath))),curveDir=path.join(root,path.dirname(indexPath),path.dirname(curveIndex.manifest));inputs[indexPath]=hash(fs.readFileSync(path.join(root,indexPath)));inputs[path.relative(root,path.join(curveDir,'manifest.json'))]=hash(fs.readFileSync(path.join(curveDir,'manifest.json')));
 const startPath='_development/data/starter-metrics.json',start=JSON.parse(fs.readFileSync(path.join(root,startPath))),startMap=new Map(start.rows.map(r=>[r.driver_id,r]));inputs[startPath]=hash(fs.readFileSync(path.join(root,startPath)));
 const jobs=[];
 for(const group of [...new Set(D.drivers.map(d=>d.detail_group))].sort()){
  const details=read('details/'+group);
  for(const driver of D.drivers.filter(d=>d.detail_group===group)){
   const rows=new Map(driver.races.map(r=>[r.race,r]));for(const[id,extra]of details[driver.id]||[]){const row=rows.get(id);if(row){const qualities={...row.qualities,...extra.qualities};Object.assign(row,extra);row.qualities=qualities;}}
   const job=W.driverGoatMetrics.build({data:D,driver,includePitCurveFit:false}),curveBytes=fs.readFileSync(path.join(curveDir,driver.id+'.json.gz')),snapshot=JSON.parse(zlib.gunzipSync(curveBytes)),curve=snapshot.curves.race,sm=startMap.get(driver.id);inputs[path.relative(root,path.join(curveDir,driver.id+'.json.gz'))]=hash(curveBytes);
   for(const[key,curveKey,unit]of[['qualifying_position','qualifying_position','position'],['gap_to_pole','gap_to_pole','seconds']]){const part=snapshot.curves[curveKey],values=part.groups.flatMap(g=>g.observations.map(o=>o.value)),value=W.pitProgrammes.quantile(values,.5);job.features[key]={value,unit,status:values.length?'available':'no_measurements',n:values.length,races:values.length,estimated:part.estimated||0,method:'Median of all original production curve observations; pole gap includes marked session estimates'};}
   job.source_curves={index:indexPath,revision:curveIndex.revision,file:path.relative(root,path.join(curveDir,driver.id+'.json.gz'))};
   job.boundary=curve.fit.gain_boundary??null;job.curve_status=curve.status;
   if(sm)for(const[key,field,status,unit]of[['start_score','start_score','start_score_status','score_0_100'],['start_curve_balance','corrected_curve_balance_pp','curve_balance_status','percentage_points'],['start_gain_boundary','gain_boundary_grid','gain_boundary_status','grid_position']])job.features[key]={value:sm[field]??null,status:sm[status],unit,n:sm.matched_starts,races:sm.measured_starts,reference_races:sm.reference_races};
   jobs.push(job);
   // Keep only the compact positional reference rows after extracting own timing.
   for(const row of driver.races){delete row.lap_rankings;delete row.comparison;delete row.samples;delete row.qualities;}
  }
 }
 const baselineRecords=W.goatCareerPCA.summarize(D),baseline=W.goatCareerPCA.project(baselineRecords),coordinates=new Map(baseline.points.map(p=>[p.driver,{x:p.x,y:p.y}]));for(const job of jobs){const record=baselineRecords.find(r=>r.driver===job.driver);job.career={starts:record.n,coverage:record.coverage,values:Object.fromEntries(W.goatCareerPCA.features.slice(0,4).map((f,i)=>[f.id,record.values[i]])),pca:coordinates.get(job.driver)||{status:'unplaced',reason:record.reason||'missing_features'}};}
 for(const name of engines){const p='_development/assets/'+name+'.js';inputs[p]=hash(fs.readFileSync(path.join(root,p)));}inputs['_development/research/export-goat-metrics.cjs']=hash(fs.readFileSync(__filename));
 const revision=hash(Buffer.from(JSON.stringify({inputs,period:D.period}))),base=path.join(root,'_development/data/goat-metrics/'+D.period.join('-')),output=path.join(base,revision.slice(0,16));fs.mkdirSync(output,{recursive:true});
 const compactData={period:D.period,races:D.races.map(r=>Object.fromEntries(['id','year','layout','starters','circuit_id'].map(k=>[k,r[k]]))),drivers:D.drivers.map(d=>({id:d.id,races:d.races}))};
 const records=new Map(),pending=[];
 for(const j of jobs){const file=path.join(output,j.driver+'.json.gz');if(fs.existsSync(file)){try{records.set(j.driver,JSON.parse(zlib.gunzipSync(fs.readFileSync(file))));continue}catch{}}pending.push(j)}
 let cursor=0,finished=records.size;console.log(JSON.stringify({revision,pending:pending.length,total:jobs.length}));
 await Promise.all(Array.from({length:Math.min(4,pending.length)},()=>new Promise((resolve,reject)=>{const worker=new Worker(__filename,{workerData:{data:compactData,output}});worker.on('error',reject);const next=()=>{if(cursor>=pending.length){worker.terminate().then(resolve,reject);return}worker.postMessage(pending[cursor++]);};worker.on('message',r=>{if(r.error){worker.terminate();reject(Error(r.error));return;}records.set(r.driver,r.record);if(++finished%25===0||finished===jobs.length)console.log(JSON.stringify({completed:finished,total:jobs.length,driver:r.driver}));next();});next();})));
 const ordered=[...records.values()].sort((a,b)=>a.driver.localeCompare(b.driver)),manifest={schema:'goat-driver-metrics-v1',revision,period:D.period,definition:D.definition_version,selection:'Each driver uses their own career; no selected-driver or shared-selected-race cohort',baseline_pca:{definition:W.goatCareerPCA.VERSION,features:baseline.features,center:baseline.center,scale:baseline.scale,loadings:baseline.loadings,explained:baseline.explained,points:baseline.points.length,unplaced:baseline.unplaced.length},inputs,drivers:ordered.map(r=>{const file=r.driver+'.json.gz',bytes=fs.readFileSync(path.join(output,file));return{driver:r.driver,file,sha256:hash(bytes),bytes:bytes.length}})};
 const payload={schema:manifest.schema,revision,period:D.period,manifest:path.relative(root,path.join(output,'manifest.json')),features:ordered.map(r=>({driver:r.driver,features:r.features}))},text=JSON.stringify(payload);
 const delivery=path.join(output,'delivery');fs.mkdirSync(delivery,{recursive:true});for(const record of ordered){const source=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(curveDir,record.driver+'.json.gz')))),curves=Object.fromEntries(Object.entries(source.curves).map(([key,c])=>[key,{...c,groups:c.groups.map(g=>Object.fromEntries(Object.entries(g).filter(([key])=>key!=='observations')))}])),content=Buffer.from(JSON.stringify({record,curves:{...curves,pit_balance:record.pit_curve}})),compressed=zlib.gzipSync(content,{level:9});fs.writeFileSync(path.join(delivery,record.driver+'.json.gz'),compressed);fs.writeFileSync(path.join(delivery,record.driver+'.js'),'window.goatPayloads=window.goatPayloads||{};window.goatPayloads['+JSON.stringify(record.driver)+']='+JSON.stringify(compressed.toString('base64'))+';\n');}
 manifest.delivery={directory:'delivery',files:manifest.drivers.map(d=>{const gzip=fs.readFileSync(path.join(delivery,d.driver+'.json.gz')),script=fs.readFileSync(path.join(delivery,d.driver+'.js'));return{driver:d.driver,gzip_sha256:hash(gzip),script_sha256:hash(script),gzip_bytes:gzip.length,script_bytes:script.length};})};
 fs.writeFileSync(path.join(output,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 fs.writeFileSync(path.join(base,'index.json'),JSON.stringify({schema:manifest.schema,revision,manifest:path.relative(base,path.join(output,'manifest.json')),drivers:ordered.length,period:D.period},null,2)+'\n');
 payload.delivery=path.relative(root,delivery)+'/';const deliveredText=JSON.stringify(payload);
 fs.writeFileSync(path.join(root,'_development/data/goat-metrics.js'),'window.phase2GoatMetrics='+deliveredText+';\n');fs.writeFileSync(path.join(root,'_development/data/goat-metrics.json.gz'),zlib.gzipSync(deliveredText,{level:9}));
 console.log(JSON.stringify({complete:true,drivers:ordered.length,available:Object.fromEntries(Object.keys(ordered[0].features).map(k=>[k,ordered.filter(r=>r.features[k]?.value!==null).length])),manifest:path.relative(root,path.join(output,'manifest.json'))}));
}
