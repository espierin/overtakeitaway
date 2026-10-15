import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {parseHTML} from '../../storage/phase2-qa/linkedom-worker.mjs';

const window={};
for(const file of ['lap-rankings','pace-timeline','driver-qualities'])vm.runInNewContext(fs.readFileSync('assets/'+file+'.js','utf8'),{window});
const S=window.driverQualities;
for(let v=-20;v<=20;v+=.1)assert.ok(Math.abs(S.starterScalePosition(v)-window.paceTimeline.scalePosition(v))<1e-12);
for(const [i,v]of[0,1,3,6,10].entries()){
 assert.equal(S.starterScalePosition(v),i/4);
 assert.equal(S.starterScalePosition(-v),-i/4);
}
const data=JSON.parse(fs.readFileSync('analysis-lab.html','utf8').match(/<script id="phase2-data" type="application\/json">(.*?)<\/script>/s)[1]);
const {document}=parseHTML('<html><body></body></html>');
for(const id of ['max-verstappen','lewis-hamilton'])for(const lang of ['nl','en']){
 const driver=data.drivers.find(d=>d.id===id),groups=S.startGroups(driver.races),starts=groups.flatMap(g=>g.starts);
 document.body.innerHTML=S.render({data,driver,rows:driver.races,lang,state:{quality:'start'}});
 const frame=document.querySelector('.starter-frame'),axis=frame.querySelector('.starter-axis'),scroll=frame.querySelector('.starter-scroll'),plot=scroll.querySelector('.starter-gain-plot');
 assert.equal(axis.parentElement,frame);assert.equal(scroll.parentElement,frame);assert.equal(scroll.querySelector('.starter-axis'),null);
 assert.equal(plot.dataset.gainMin,'-10');assert.equal(plot.dataset.gainMax,'10');
 const ticks=[...axis.querySelectorAll('.starter-y-tick')];
 assert.deepEqual(ticks.map(t=>+t.dataset.value),[-10,-6,-3,-1,0,1,3,6,10]);
 assert.equal(scroll.querySelectorAll('.starter-y-tick,.starter-direction').length,0);
 assert.equal(axis.querySelector('.starter-better text').textContent,lang==='nl'?'Beter':'Better');
 assert.equal(axis.querySelector('.starter-worse text').textContent,lang==='nl'?'Slechter':'Worse');
 const y=v=>+ticks.find(t=>+t.dataset.value===v).getAttribute('y')-4;
 for(const [a,b]of[[0,1],[1,3],[3,6],[6,10]])assert.equal(y(a)-y(b),60.25);
 assert.deepEqual([...axis.querySelectorAll('.starter-minor-tick')].map(t=>+t.dataset.value),[-9,-8,-7,-5,-4,-2,2,4,5,7,8,9]);
 assert.equal(plot.querySelectorAll('.starter-observation').length,starts.length);
 assert.equal(plot.querySelectorAll('.starter-offscale').length,starts.filter(s=>Math.abs(s.obs.grid-s.obs.lap1)>10).length);
 const outliers=[...plot.querySelectorAll('.starter-observation')].filter(c=>Math.abs(+c.dataset.gain)>10);
 for(const c of outliers){assert.equal(+c.getAttribute('cy'),+c.dataset.gain>0?38:520);assert.ok(c.textContent.includes(String(c.dataset.gain)));}
 assert.equal(new Set(outliers.map(c=>c.getAttribute('cx')+','+c.getAttribute('cy'))).size,outliers.length,'Off-scale points must remain individually visible');
 for(const p of plot.querySelectorAll('.starter-curve,.starter-curve-band,.starter-violin')){
  assert.ok(!/NaN|Infinity/.test(p.getAttribute('d')));
  for(const point of p.getAttribute('d').matchAll(/[ML]([\d.+-]+),([\d.+-]+)/g))assert.ok(+point[2]>=38&&+point[2]<=520);
 }
 assert.equal(axis.getAttribute('height'),plot.getAttribute('height'));
}
const css=fs.readFileSync('assets/phase2.css','utf8');
assert.match(css,/\.starter-frame\{[^}]*grid-template-columns:130px minmax\(0,1fr\)/);
assert.match(css,/\.starter-frame>\.starter-scroll\{[^}]*overflow-x:auto/);
console.log('Verified teammate-equivalent non-linear scale, fixed axis outside scroller, NL/EN arrows, all starts retained, distinct outliers and consistent curve/violin/band coordinates.');
