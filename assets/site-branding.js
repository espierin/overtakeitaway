/* One unchanged bitmap wordmark, plus an accessible subtitle in the site language. */
(()=>{'use strict';if(window.siteBranding)return;
const name='Overtake It Away',copy={nl:'Geen fabels maar feiten',en:'A reality check on heroic stories.'},brandPattern=/Overtake It Away(?:: (?:Geen fabels maar feiten|A reality check on heroic stories\.))?/g;
function translate(){const lang=document.documentElement.lang.toLowerCase().startsWith('en')?'en':'nl',tagline=copy[lang],full=name+': '+tagline;
 document.querySelectorAll('[data-brand-tagline]').forEach(el=>{if(el.textContent!==tagline)el.textContent=tagline;});
 document.querySelectorAll('.site-home-link,.logo-link:has(.site-wordmark-window)').forEach(el=>{const value=full+' · Home';if(el.getAttribute('aria-label')!==value)el.setAttribute('aria-label',value);});
 const title=document.title.replace(brandPattern,full);if(document.title!==title)document.title=title;
}
window.siteBranding={translate};new MutationObserver(translate).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});window.addEventListener('pageshow',translate);translate();
})();
