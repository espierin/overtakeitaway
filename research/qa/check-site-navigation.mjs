import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
import {parseHTML,HTMLElement} from '../../storage/phase2-qa/linkedom-worker.mjs';
const code=fs.readFileSync('assets/site-navigation.js','utf8');
for(const file of ['index.html','races.html','analysis-lab.html']){
 const {document,window:domWindow}=parseHTML(fs.readFileSync(file,'utf8'));const window={};
 HTMLElement.prototype.showModal=function(){this.setAttribute('open','');};HTMLElement.prototype.close=function(){this.removeAttribute('open');this.dispatchEvent(new domWindow.Event('close'));};
 Object.defineProperty(HTMLElement.prototype,'open',{configurable:true,get(){return this.hasAttribute('open');}});
 const context={document,window,MutationObserver:domWindow.MutationObserver,location:{pathname:'/overtakeitaway/'+file}};
 vm.runInNewContext(code,context);assert.equal(document.querySelectorAll('[data-site-about]').length,1);
 assert.equal(document.querySelector('[data-site-link=races]').getAttribute('href'),'races.html');assert.equal(document.querySelector('.site-wordmark').parentElement.getAttribute('href'),'index.html');
 assert.equal(document.querySelector('[data-site-link=drivers]').getAttribute('href'),'analysis-lab.html#tab=profiles');
 document.querySelector('[data-site-about]').click();const dialog=document.getElementById('about-dialog');assert.ok(dialog.open);
 assert.match(dialog.textContent,/Ik maak Overtake It Away voor de lol/);assert.match(dialog.textContent,/gratis middelen/);assert.equal(dialog.querySelector('.donate').getAttribute('href'),'https://blauwehut.nl/donatie-formulier/');assert.ok(dialog.querySelector('a[href="https://espierin.github.io/cv/"]'));
 document.documentElement.lang='en';await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(document.querySelector('[data-site-about]').textContent,'About me');assert.match(dialog.textContent,/for fun/);assert.match(dialog.textContent,/remain free/);assert.doesNotMatch(dialog.textContent,/Wil je|Sluiten|kosteloos/);
 document.getElementById('about-close').click();assert.ok(!dialog.open);
 document.querySelector('[data-site-about]').click();assert.equal(document.querySelectorAll('#about-dialog').length,1);document.getElementById('about-close').click();
 vm.runInNewContext(code,context);assert.equal(document.querySelectorAll('#about-dialog').length,1);
}
console.log(JSON.stringify({pages:3,checks:['destinations','NL/EN','open and close','reuse dialog','CV link','donation form','free access policy','idempotent script'],visualBrowserTest:false},null,2));
