(()=>{
const button=document.getElementById('back-to-top');
if(!button)return;
let scheduled=false;
const sync=()=>{button.hidden=window.scrollY<300;scheduled=false;};
window.addEventListener('scroll',()=>{if(!scheduled){scheduled=true;requestAnimationFrame(sync);}},{passive:true});
button.addEventListener('click',()=>window.scrollTo({top:0,left:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));
sync();
})();
