/* Build exactly the same brief as the browser, without a browser or a secret. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),zlib=require('node:zlib'),crypto=require('node:crypto');
const [site,requestPath,output]=process.argv.slice(2),request=JSON.parse(fs.readFileSync(requestPath,'utf8')),c={window:{},URLSearchParams};vm.createContext(c);
const read=file=>fs.existsSync(file)?fs.readFileSync(file,'utf8'):zlib.gunzipSync(fs.readFileSync(file+'.gz')).toString('utf8');
for(const file of ['profiles','facts','models','goat-metrics'])vm.runInContext(read(path.join(site,'_development/data/'+file+'.js')),c);
for(const file of ['driver-names','driver-field','goat-parameters','goat-ai-contract','goat-ai-format','goat-ai'])vm.runInContext(read(path.join(__dirname,'../assets/'+file+'.js')),c);
const w=c.window,D=w.phase2Data;if(D.driver_race_columns)for(const d of D.drivers)d.races=d.races.map(row=>Object.fromEntries(D.driver_race_columns.map((key,i)=>[key,row[i]])));
const drivers=new Map(D.drivers.map(d=>[d.id,d])),ids=request.drivers;
if(!Array.isArray(ids)||ids.length<2||ids.length>4||new Set(ids).size!==ids.length||ids.some(id=>!drivers.has(id)))throw Error('Select 2–4 distinct known drivers');
if(request.from<D.period[0]||request.to>D.period[1]||request.from>request.to)throw Error('Period outside retained data');
for(const id of ids){const file=path.join(site,w.phase2GoatMetrics.delivery,id+'.json.gz');w.goatParameters.cache.set(id,JSON.parse(zlib.gunzipSync(fs.readFileSync(file))));}
const options={data:D,facts:w.phase2Facts,models:w.phase2Models,ids,drivers,lang:request.lang,state:{from:request.from,to:request.to,cohort:'career',curveyears:request.curveyears,circuitdetail:request.circuits.join(',')}};
const selection=w.goatParameters.circuitSelection(options);if(request.circuits.some(key=>!selection.choices.some(c=>c.key===key)))throw Error('Unknown circuit');
// The request does not depend on the descriptive shared-race control. The fixed
// archive is the common source both in the browser and in Actions.
const prompt=w.goatAI.prompt(options),brief=w.goatAI.snapshot(options),hash=crypto.createHash('sha256').update(prompt).digest('hex');
fs.mkdirSync(output,{recursive:true});fs.writeFileSync(path.join(output,'prompt.txt'),prompt);fs.writeFileSync(path.join(output,'brief.json'),JSON.stringify(brief));fs.writeFileSync(path.join(output,'request.json'),JSON.stringify({...request,prompt_sha256:hash,source_revision:brief.source_revision}));
console.log(JSON.stringify({prompt_sha256:hash,characters:prompt.length,drivers:ids}));
