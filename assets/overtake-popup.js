/* Fixed map and independently scrolling event cards, including archived dashboards. */
(()=>{
 const dialog=document.getElementById('event-dialog'),detail=document.getElementById('event-detail');if(!dialog||!detail)return;
 const style=document.createElement('style');style.textContent=`
 #event-dialog.is-action-map-popup[open]{display:flex;flex-direction:column;box-sizing:border-box;height:min(92dvh,960px);max-height:92dvh;overflow:hidden}
 #event-dialog.is-action-map-popup #close-dialog{position:static;flex:0 0 auto;margin-bottom:8px}
 #event-dialog.is-action-map-popup #event-detail{display:flex;flex-direction:column;flex:1;min-height:0;overflow:hidden}
 #event-dialog.is-action-map-popup #event-detail>h2{flex:0 0 auto;margin:4px 0 12px}
 #event-dialog.is-action-map-popup #action-map-view{flex:0 0 auto;height:clamp(180px,43dvh,460px);min-height:0}
 #event-dialog.is-action-map-popup .action-location-map{height:100%;box-sizing:border-box;margin:0}
 #event-dialog.is-action-map-popup .action-location-map>svg{width:100%;height:100%;min-width:0}
 #action-info-scroll{flex:1;min-height:0;overflow:auto;overscroll-behavior:contain;padding:7px; margin:8px -7px -7px;scroll-padding:7px}
 #action-info-scroll .action-info-cards{margin:0;padding:0;align-content:start}
 #action-info-scroll [data-action-marker].action-card-selected{outline:2px solid #51d6dd;outline-offset:3px;box-shadow:0 0 0 5px #080c14!important}
 #action-map-view [data-action-location],#action-map-view [data-action-lap-label]{cursor:pointer}
 `;document.head.appendChild(style);
 function prepare(){
  const map=detail.querySelector('#action-map-view'),cards=detail.querySelector('.action-info-cards');dialog.classList.toggle('is-action-map-popup',Boolean(map&&cards));if(!map||!cards)return;
  let scroll=detail.querySelector('#action-info-scroll');if(!scroll){scroll=document.createElement('div');scroll.id='action-info-scroll';const heading=detail.querySelector('h2');for(const node of [...detail.childNodes])if(node!==heading&&node!==map)scroll.appendChild(node);if(heading)heading.after(map);else detail.prepend(map);detail.appendChild(scroll);dialog.scrollTop=0;}
  for(const marker of map.querySelectorAll('[data-action-location]')){if(marker.hasAttribute('tabindex'))continue;marker.setAttribute('tabindex','0');marker.setAttribute('role','button');const card=[...cards.querySelectorAll('[data-action-marker]')].find(c=>c.dataset.actionMarker===marker.dataset.actionLocation);if(card)marker.setAttribute('aria-label',card.innerText.trim().replace(/\s+/g,' '));}
 }
 function select(id,scrollToCard){const scroll=detail.querySelector('#action-info-scroll');if(!scroll)return;const cards=[...scroll.querySelectorAll('[data-action-marker]')],selected=cards.find(c=>c.dataset.actionMarker===id);if(!selected)return;for(const card of cards)card.classList.toggle('action-card-selected',card===selected);if(scrollToCard){const top=selected.getBoundingClientRect().top-scroll.getBoundingClientRect().top+scroll.scrollTop-7;scroll.scrollTo({top:Math.max(0,top),behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});} }
 function marker(event){return event.target.closest('#action-map-view [data-action-location],#action-map-view [data-action-lap-label]');}
 document.addEventListener('pointerdown',event=>{if(marker(event))event.stopImmediatePropagation();},true);
 document.addEventListener('click',event=>{const node=marker(event);if(node){event.preventDefault();event.stopImmediatePropagation();select(node.dataset.actionLocation||node.dataset.actionLapLabel,true);return;}const card=event.target.closest('#action-info-scroll [data-action-marker]');if(card)select(card.dataset.actionMarker,false);},true);
 document.addEventListener('keydown',event=>{if(!['Enter',' '].includes(event.key))return;const node=marker(event);if(node){event.preventDefault();event.stopImmediatePropagation();select(node.dataset.actionLocation||node.dataset.actionLapLabel,true);}},true);
 new MutationObserver(prepare).observe(detail,{childList:true,subtree:true});prepare();
})();
