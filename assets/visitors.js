window.oiaVisitorsConfig = {"site": "https://overtakeitaway.goatcounter.com", "origin": "https://espierin.github.io", "base_path": "/overtakeitaway/"};
/* A single production-only page view. No query strings, hashes or click events. */
(()=>{'use strict';if(window.oiaVisitors)return;
const config=window.oiaVisitorsConfig,key='overtake-visitors-exclude';
function excluded(){try{return localStorage.getItem(key)==='1';}catch{return false;}}
function allowed(){return!!config.site&&location.protocol==='https:'&&location.origin===config.origin&&location.pathname.startsWith(config.base_path)&&!/(?:^|\/)(?:stats4me\.html|_development)(?:\/|$)/.test(location.pathname)&&!excluded()&&navigator.doNotTrack!=='1'&&navigator.globalPrivacyControl!==true;}
function toggle(){try{if(excluded())localStorage.removeItem(key);else localStorage.setItem(key,'1');}catch{}update();}
function update(){const button=document.getElementById('visitor-exclude');if(button){button.textContent=excluded()?'Eigen bezoeken worden niet meegeteld':'Mijn eigen bezoeken niet meetellen';button.setAttribute('aria-pressed',String(excluded()));button.onclick=toggle;}}
window.oiaVisitors={config,allowed,excluded,toggle};update();
if(!allowed())return;
const referrer=()=>{try{return document.referrer?new URL(document.referrer).origin:'';}catch{return'';}};
window.goatcounter={path:()=>location.pathname,title:document.title,referrer,no_events:true};
const script=document.createElement('script');script.async=true;script.src='https://gc.zgo.at/count.js';script.setAttribute('data-goatcounter',config.site+'/count');script.dataset.siteVisitCounter='true';document.head.append(script);
})();
