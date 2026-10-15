/* Display order only: never reorder the underlying observations or rankings. */
(()=>{'use strict';
const collator=new Intl.Collator('nl',{sensitivity:'base',numeric:true});
function key(driver){const name=String(driver.surname||driver.family_name||driver.last_name||driver.name||'').trim(),parts=name.replace(/(?:,?\s+(?:jr\.?|jnr\.?|sr\.?|ii|iii|iv))$/i,'').split(/\s+/);return parts.at(-1)||name;}
function compare(a,b){return collator.compare(key(a),key(b))||collator.compare(a.name||'',b.name||'')||collator.compare(a.id||'',b.id||'');}
window.driverNames={key,compare,sort:drivers=>[...drivers].sort(compare)};
})();
