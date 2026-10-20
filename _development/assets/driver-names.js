/* Display order only: never reorder the underlying observations or rankings. */
(()=>{'use strict';
const collator=new Intl.Collator('nl',{sensitivity:'base',numeric:true});
function display(name){return String(name||'').trim().replace(/\S+/gu,word=>{if(word.length<2||word!==word.toLocaleUpperCase()||word===word.toLocaleLowerCase()||/^(?:[IVX]+|(?:\p{L}\.)+)$/u.test(word))return word;return word.toLocaleLowerCase().replace(/(^|[-'’])\p{L}/gu,letter=>letter.toLocaleUpperCase());});}
function apply(data){for(const driver of data?.drivers||[])driver.name=display(driver.name);}
function key(driver){const name=String(driver.surname||driver.family_name||driver.last_name||(driver.id==='guanyu-zhou'?'Zhou':driver.name)||'').trim(),parts=name.replace(/(?:,?\s+(?:jr\.?|jnr\.?|sr\.?|ii|iii|iv))$/i,'').split(/\s+/);return parts.at(-1)||name;}
function compare(a,b){return collator.compare(key(a),key(b))||collator.compare(a.name||'',b.name||'')||collator.compare(a.id||'',b.id||'');}
window.driverNames={key,compare,display,apply,sort:drivers=>[...drivers].sort(compare)};apply(window.phase2Data);
})();
