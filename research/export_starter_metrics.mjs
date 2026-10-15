/** Rebuild the saved Starter table from the same functions as the browser cards.
 * Run from the project root: node research/export_starter_metrics.mjs
 * Optional first argument: another project root. No network or dependencies.
 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {createHash} from 'node:crypto';

const root=path.resolve(process.argv[2]||'.');
const page=fs.readFileSync(path.join(root,'analysis-lab.html'),'utf8');
const match=page.match(/<script\b[^>]*id=["']phase2-data["'][^>]*>(.*?)<\/script>/s);
if(!match)throw new Error('No phase2-data in analysis-lab.html');
const data=JSON.parse(match[1]);
const code=fs.readFileSync(path.join(root,'assets/driver-qualities.js'),'utf8');
const window={};vm.runInNewContext(code,{window});
const rows=data.drivers.map(driver=>window.driverQualities.starterMetrics({data,driver}));
if(new Set(rows.map(r=>r.driver_id)).size!==data.drivers.length)throw new Error('Missing or duplicate driver metrics');
const checksum=text=>createHash('sha256').update(text).digest('hex');
const result={schema:'starter-driver-metrics-v1',method:'starter-curve-comparison-v3',generated_at:new Date().toISOString(),period:data.period,filters:{year:null,circuit:null,compound:'not_applicable'},source:'analysis-lab.html#phase2-data',source_sha256:checksum(match[1]),analysis_sha256:checksum(code),driver_count:rows.length,definitions:{corrected_curve_balance_pp:{nl:'Kansgecorrigeerde curvebalans in procentpunten boven de neutrale referentiescore 50, over de vermelde onderbouwde gridvakken.',en:'Opportunity-adjusted curve balance in percentage points above neutral reference score 50, across the stated supported grid intervals.'},start_score:{nl:'Vergelijkingsscore 0–100 vanaf dezelfde startpositie, hetzelfde circuit en dezelfde veldgrootte. 50 is neutraal.',en:'Comparison score 0–100 from the same grid position, circuit and field size. 50 is neutral.'},gain_boundary_grid:{nl:'Eerste van twee opeenvolgende gridposities met minstens 0,5 positie winst in de centrale mediaanfit. Een verkennende drempel, geen statistisch breekpunt.',en:'First of two consecutive grid positions with at least 0.5 positions gained in the central median fit. Exploratory threshold, not a statistical change point.'},missing:{nl:'null betekent niet beschikbaar of geen winstgrens gevonden; zie het bijbehorende statusveld. Ontbrekend is geen nul.',en:'null means unavailable or no gain boundary found; see the corresponding status field. Missing is not zero.'},coverage:{nl:'De drie uitkomsten gebruiken verschillende dekking. Geen algemene ranglijst zonder gedeelde startposities en contexten. Pitlanestarts zijn uitgesloten.',en:'The three outcomes have different coverage. No overall ranking without shared grid positions and contexts. Pit-lane starts are excluded.'}},rows};
const columns=[['rijder_id',r=>r.driver_id],['rijder',r=>r.driver_name],['code',r=>r.driver_code],['gecorrigeerde_curvebalans_pp',r=>r.corrected_curve_balance_pp],['startscore_0_100',r=>r.start_score],['winstgrens_gridpositie',r=>r.gain_boundary_grid],['curvebalans_95_laag_pp',r=>r.curve_balance_interval_pp?.[0]],['curvebalans_95_hoog_pp',r=>r.curve_balance_interval_pp?.[1]],['startscore_95_laag',r=>r.start_score_interval?.[0]],['startscore_95_hoog',r=>r.start_score_interval?.[1]],['gemeten_starts',r=>r.measured_starts],['vergelijkbare_starts',r=>r.matched_starts],['uitgesloten_pitlanestarts',r=>r.pitlane_starts_excluded],['curve_gridbereik',r=>r.curve_grid_ranges.map(([a,b])=>`P${a}–P${b}`).join(', ')],['score_gridposities',r=>r.score_grid_positions.map(g=>'P'+g).join(', ')],['curvebalans_status',r=>r.curve_balance_status],['startscore_status',r=>r.start_score_status],['winstgrens_status',r=>r.gain_boundary_status],['winstgrens_methode',r=>r.gain_boundary_method]];
const cell=value=>{if(value===null||value===undefined)return'';const text=typeof value==='number'?String(value).replace('.',','):String(value);return/[;"\r\n]/.test(text)?'"'+text.replaceAll('"','""')+'"':text;};
const csv='\ufeff'+[columns.map(([name])=>name).join(';'),...rows.map(r=>columns.map(([,get])=>cell(get(r))).join(';'))].join('\r\n')+'\r\n';
fs.mkdirSync(path.join(root,'assets'),{recursive:true});
fs.writeFileSync(path.join(root,'assets/starter-metrics.json'),JSON.stringify(result,null,2)+'\n');
fs.writeFileSync(path.join(root,'assets/starter-metrics.csv'),csv);
console.log(JSON.stringify({drivers:rows.length,period:data.period,available:{curve_balance:rows.filter(r=>r.corrected_curve_balance_pp!==null).length,start_score:rows.filter(r=>r.start_score!==null).length,gain_boundary:rows.filter(r=>r.gain_boundary_grid!==null).length},json:'assets/starter-metrics.json',csv:'assets/starter-metrics.csv'},null,2));
