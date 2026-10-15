"""The retained translator and shared header must settle instead of starving paint/load."""
import subprocess


def test_language_and_about_menu_observers_settle():
    fixture = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function run(override){
 const observers=[],records=[];let lang='en',text='About me',writes=0;
 const root={};Object.defineProperty(root,'lang',{get:()=>lang,set:value=>{lang=value;records.push({target:root,type:'attributes',attributeName:'lang'});}});
 const body={},about={addEventListener(){},getAttribute:name=>name==='data-about-en'?'About me':'Over mij'};
 Object.defineProperty(about,'textContent',{get:()=>text,set:value=>{text=value;writes++;records.push({target:body,type:'childList'});}});
 class Observer{constructor(callback){this.callback=callback;observers.push(this)}observe(target,options){this.target=target;this.options=options}disconnect(){this.target=null}}
 const document={documentElement:root,body,getElementById:()=>null,querySelector:s=>s==='[data-site-about]'?about:null,querySelectorAll:s=>s==='[data-about-nl][data-about-en]'?[about]:[],createTreeWalker:()=>({nextNode:()=>null})};
 const context=vm.createContext({document,location:{pathname:'/race/overzicht.html'},MutationObserver:Observer,localStorage:{getItem:()=>lang},NodeFilter:{SHOW_TEXT:4},console});context.window=context;
 let navigation=fs.readFileSync('src/f1_analysis/site-navigation.js','utf8'),language=fs.readFileSync('src/f1_analysis/language.js','utf8');
 if(override==='old-navigation'||override==='both-old')navigation=navigation.replace("const text=node.getAttribute(en?'data-about-en':'data-about-nl');if(node.textContent!==text)node.textContent=text;","node.textContent=node.getAttribute(en?'data-about-en':'data-about-nl');");
 if(override==='old-language'||override==='both-old')language=language.replace("if(document.documentElement.lang!==lang)document.documentElement.lang=lang;","document.documentElement.lang=lang;");
 vm.runInContext(navigation,context);vm.runInContext(language,context);
 function settle(){let rounds=0;while(records.length){assert.ok(++rounds<20,'Observer feedback loop blocks race rendering');const batch=records.splice(0),callbacks=observers.filter(o=>o.target&&batch.some(r=>o.target===r.target&&o.options[r.type]&&(r.type!=='attributes'||!o.options.attributeFilter||o.options.attributeFilter.includes(r.attributeName))));for(const o of callbacks)o.callback(batch);}return rounds}
 settle();context.siteLanguage.set('nl');settle();assert.equal(lang,'nl');assert.equal(text,'Over mij');context.siteLanguage.set('en');settle();assert.equal(text,'About me');
 for(let i=0;i<20;i++)context.siteNavigation.translate();settle();assert.ok(writes<30);
}
// Either corrected side stops the loop, including cached older counterparts.
run();run('old-navigation');run('old-language');
assert.throws(()=>run('both-old'),/Observer feedback loop/);
'''
    subprocess.run(['node', '-e', fixture], check=True, timeout=15)
