"""Loading indicators follow the destination, including GitHub Pages subpaths."""
import subprocess


def test_section_loading_tyres_and_nested_frames():
    fixture=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('src/f1_analysis/document_loader.js','utf8');
function open(path,shell=false){
 function node(tag){return {tag,children:[],dataset:{},style:{setProperty(name,value){this[name]=value}},append(...items){this.children.push(...items)},remove(){},setAttribute(name,value){this[name]=value}}}
 const href='https://example.test/overtakeitaway/'+path,bootstrap={src:'https://example.test/overtakeitaway/_documents/loader.js?v=123',dataset:{f1Document:'document.html.gz'},hasAttribute:()=>shell};
 const document={currentScript:bootstrap,head:node('head'),body:node('body'),createElement:node};
 const context=vm.createContext({document,location:{href,search:new URL(href).search,protocol:'https:',origin:'https://example.test'},URL,URLSearchParams,localStorage:{getItem:()=>null},fetch:()=>new Promise(()=>{}),setTimeout:()=>0,clearTimeout(){}});context.window=context;context.addEventListener=()=>{};
 vm.runInContext(code,context);return {document,context,indicator:document.body.children.find(n=>n.id==='race-loading')};
}
for(const [path,section,colour] of [
 ['races.html','races','red'],
 ['analyses/index.html','races','red'],
 ['analyses/2018/australia/runs/one/overzicht.html','races','red'],
 ['analysis-lab.html#tab=profiles&driver=max-verstappen','drivers','purple'],
 ['analysis-lab.html#tab=strategy','drivers','purple'],
 ['goat.html?lang=en','greatest','yellow']
]){
 const {indicator}=open(path,path.includes('overzicht'));
 assert.equal(indicator.dataset.section,section);assert.equal(indicator.dataset.colour,colour);assert.equal(indicator.hidden,false);
 const wheel=indicator.children[0];assert.equal(wheel.children[0].src,'https://example.test/overtakeitaway/assets/tire-'+colour+'.svg');assert.ok(wheel.href.endsWith('_'+colour[0].toUpperCase()+colour.slice(1)+'.svg'));assert.equal(wheel.rel,'noopener');
}
const race=open('analyses/2026/test/runs/a/overzicht.html',true);race.context.overtakeNavigation.navigate('https://example.test/overtakeitaway/analyses/2025/test/runs/a/overzicht.html');assert.equal(race.indicator.dataset.colour,'red');
assert.equal(open('analyses/2026/test/runs/a/overzicht.html?f1-frame=1',true).indicator,undefined);
assert.equal(open('index.html').indicator,undefined);
'''
    subprocess.run(['node', '-e', fixture], check=True, timeout=15)
