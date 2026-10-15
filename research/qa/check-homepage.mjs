import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
import {parseHTML} from '../../storage/phase2-qa/linkedom-worker.mjs';
const code=fs.readFileSync('assets/homepage.js','utf8');
for(const stored of ['nl','en','unrecognised','blocked']){
 const {document,window}=parseHTML(fs.readFileSync('index.html','utf8'));
 const storage=new Map([['overtake-it-away-language',stored]]);
 vm.runInNewContext(code,{document,window,localStorage:{getItem:k=>{if(stored==='blocked')throw Error('blocked');return storage.get(k);},setItem:(k,v)=>{if(stored==='blocked')throw Error('blocked');storage.set(k,v);}}});
 assert.equal(document.documentElement.lang,stored==='en'?'en':'nl');
 assert.equal(document.querySelector('.races-tile').getAttribute('href'),'races.html');
 assert.equal(document.querySelector('.drivers-tile').getAttribute('href'),'analysis-lab.html#tab=profiles');
 assert.equal(document.querySelector('.goat-tile').getAttribute('href'),'goat.html');assert.match(document.querySelector('.goat-tile .tile-status').textContent,/WINTER BREAK/);document.querySelector('[data-language-toggle]').click();
 assert.equal(document.documentElement.lang,stored==='en'?'nl':'en');
 assert.equal(document.querySelector('.all-seasons-button').textContent,'Races');
 assert.match(document.querySelector('.drivers-tile .tile-cta').textContent,stored==='en'?/Ontdek de rijders/:/Explore the drivers/);
}
const race=fs.readFileSync('races.html','utf8'),match=race.match(/<script[^>]*id="catalogue-data"[^>]*>(.*?)<\/script>/s);assert.ok(match);assert.ok(JSON.parse(match[1]).races.length>=1166);assert.ok(race.includes('id="catalog-search"'));assert.ok(race.includes('id="world-dialog"'));
console.log(JSON.stringify({languageCases:4,tiles:3,catalogueRaces:JSON.parse(match[1]).races.length,visualBrowserTest:false}));
