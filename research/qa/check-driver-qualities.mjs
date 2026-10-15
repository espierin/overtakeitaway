import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
import {parseHTML,HTMLSelectElement,HTMLElement} from '../../storage/phase2-qa/linkedom-worker.mjs';
const {document}=parseHTML(fs.readFileSync('analysis-lab.html','utf8'));
Object.defineProperty(HTMLSelectElement.prototype,'value',{get(){return [...this.querySelectorAll('option')].find(o=>o.hasAttribute('selected'))?.getAttribute('value')||this.querySelector('option')?.getAttribute('value')||'';},set(v){for(const o of this.querySelectorAll('option'))o.toggleAttribute('selected',o.getAttribute('value')===String(v));}});
const storage=new Map(),location={hash:'',href:'file:///analysis-lab.html'},window={},context={document,window,location,URLSearchParams,localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},history:{replaceState:(_a,_b,h)=>{location.hash=h;}},navigator:{clipboard:{writeText:async()=>{}}},console};
for(const file of ['pit-programmes.js','pace-timeline.js','lap-rankings.js','driver-names.js','driver-qualities.js','phase2.js'])vm.runInNewContext(fs.readFileSync('assets/'+file,'utf8'),context,{timeout:20000});
assert.equal(document.querySelectorAll('[data-quality]').length,6);
for(const kind of ['free','metronome','tyres','warmup','pitwindow','start']){
 document.querySelector('[data-quality="'+kind+'"]').onclick();
 assert.equal(window.phase2Lab.state.quality,kind);assert.ok(document.querySelector('#quality-detail .quality-method'));assert.ok(document.querySelector('#quality-detail .quality-evidence'));assert.ok(!document.getElementById('quality-detail').innerHTML.includes('NaN'));
}
const total=document.querySelectorAll('#driver option').length;const orderedDriverIds=[...document.querySelectorAll('#driver option')].map(o=>o.value);assert.ok(orderedDriverIds.indexOf('lewis-hamilton')<orderedDriverIds.indexOf('kimi-raikkonen'),'Hamilton precedes Räikkönen by surname');assert.ok(orderedDriverIds.indexOf('giedo-van-der-garde')<orderedDriverIds.indexOf('lewis-hamilton'),'Surname particles do not sort van der Garde under V');assert.equal(document.querySelectorAll('[data-profile]').length,0);assert.ok(!document.getElementById('lab-content').textContent.includes('Alle rijders als referentie'));
document.getElementById('quality-compound').value='HARD';document.getElementById('quality-compound').onchange();assert.equal(document.querySelectorAll('#driver option').length,total);
assert.ok(document.getElementById('quality-detail').textContent.includes('compoundfilter geldt niet'));
document.getElementById('language-toggle').onclick();
assert.match(document.getElementById('quality-detail').textContent,/The starter/);assert.doesNotMatch(document.getElementById('quality-detail').textContent,/Berekening|Onvoldoende|Ruwe winst|Waarnemingen/);
const selected=window.phase2Lab.data.drivers.find(d=>d.races.some(r=>r.qualities?.tyres?.length));assert.ok(selected);
window.phase2Lab.state.driver=selected.id;window.phase2Lab.state.compound='';window.phase2Lab.state.quality='tyres';window.phase2Lab.state.qualityrace='';window.phase2Lab.render();
const point=document.querySelector('#quality-detail [data-quality-race]');assert.ok(point);point.onclick({preventDefault(){}});assert.ok(document.querySelector('#quality-detail svg line[stroke="#51d6dd"]'));assert.ok(location.hash.includes('qualityrace='));
document.querySelector('[data-tab="strategy"]').onclick();document.querySelector('[data-tab="profiles"]').onclick();assert.equal(window.phase2Lab.state.quality,'tyres');
window.phase2Lab.state.circuit='nonexistent';window.phase2Lab.render();assert.equal(document.querySelectorAll('[data-quality]').length,6);assert.match(document.getElementById('quality-detail').textContent,/Insufficient comparable data/);assert.ok(!document.getElementById('quality-detail').innerHTML.includes('NaN'));
const stats=window.driverQualities;assert.equal(stats.interval([1,2,3,4]),null);assert.deepEqual([...stats.interval([0,0,0,0,0])],[0,0]);
console.log(JSON.stringify({qualities:6,checks:['six modules','all compounds','starts compound independent','NL/EN','evidence and methods','tyre trace drilldown','state and hash','unknown coverage','zero vs missing','reference section removed; driver choices retained'],visualBrowserTest:false},null,2));
