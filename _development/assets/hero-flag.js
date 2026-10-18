(()=>{'use strict';
 const hero=document.querySelector('.race-hero[data-hero-flag]');if(!hero||hero.querySelector('.hero-country-flag'))return;
 const style=document.createElement('style');style.id='hero-country-flag-style';style.textContent='.race-hero .hero-country-flag{position:absolute;left:0;bottom:0;z-index:-1;display:block;pointer-events:none;max-height:none;max-width:80%;width:auto;object-fit:contain;object-position:left bottom;opacity:.72;mix-blend-mode:screen}.race-hero .catalogue-intro{position:relative}';document.head.append(style);
 const image=document.createElement('img');image.className='hero-country-flag';image.src=hero.dataset.heroFlag;image.alt='';image.setAttribute('aria-hidden','true');hero.prepend(image);
 function align(){const anchor=hero.querySelector('.catalogue-intro .eyebrow')||hero.querySelector('.dash-header h1')||hero.querySelector('h1');if(!anchor)return;const box=hero.getBoundingClientRect();image.style.height=Math.max(0,box.bottom-anchor.getBoundingClientRect().top-3)+'px';}
 new ResizeObserver(align).observe(hero);image.addEventListener('load',align);align();
})();
