/* Export exactly the same starter metrics as the development profile, not a GOAT score. */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),context={window:{},console,Math,Map,Set,WeakMap,Number,Array,Object,String};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'_development/data/profiles.js'),'utf8'),context);
const data=context.window.phase2Data;
for(const d of data.drivers)d.races=d.races.map(row=>Object.fromEntries(data.driver_race_columns.map((k,i)=>[k,row[i]])));
vm.runInContext(fs.readFileSync(path.join(root,'_development/assets/driver-qualities.js'),'utf8'),context);
const rows=data.drivers.map(driver=>context.window.driverQualities.starterMetrics({data,driver,state:{yearMin:data.period[0],yearMax:data.period[1]}}));
const output={definition:data.definition_version,development_version:data.development_version,period:data.period,rows};
fs.writeFileSync(path.join(root,'_development/data/starter-metrics.json'),JSON.stringify(output));
const columns=['driver_id','driver_name','driver_code','corrected_curve_balance_pp','start_score','gain_boundary_grid','measured_starts','matched_starts','reference_races','curve_balance_status','start_score_status','gain_boundary_status'];
const csv=v=>v===null||v===undefined?'':typeof v==='string'?'"'+v.replaceAll('"','""')+'"':String(v);
fs.writeFileSync(path.join(root,'_development/data/starter-metrics.csv'),columns.join(',')+'\n'+rows.map(row=>columns.map(k=>csv(row[k])).join(',')).join('\n')+'\n');
console.log(JSON.stringify({starter_metrics:rows.length,definition:output.definition}));
