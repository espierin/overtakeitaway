/* Neighbours in the same two-dimensional, fixed-career PCA as GOAT. */
(()=>{'use strict';
const selected=['grid','classification','wins','finished','start_gain_boundary','qualifying_position'],cache=new WeakMap();
function nearest(model,driver,count=3){
 const origin=model.available&&model.points.find(p=>p.driver===driver);if(!origin)return[];
 return model.points.filter(p=>p.driver!==driver).map(p=>({driver:p.driver,distance:Math.hypot(p.x-origin.x,p.y-origin.y)})).sort((a,b)=>a.distance-b.distance||a.driver.localeCompare(b.driver)).slice(0,count);
}
function model(data){let saved=cache.get(data);if(!saved){saved=window.goatCareerPCA.analyze(data,{archive:window.phase2GoatMetrics,selected});cache.set(data,saved);}return saved;}
function render({data,driver,lang='nl'}){
 const t=(nl,en)=>lang==='en'?en:nl,esc=window.phase2Research.esc,result=model(data),peers=nearest(result,driver.id),byId=new Map(data.drivers.map(d=>[d.id,d]));
 if(!peers.length)return`<section class="card driver-pca-neighbours"><h2>${t('Vergelijkbare loopbanen','Similar careers')}</h2><p class="muted">${t('Er zijn voor deze rijder niet genoeg gegevens voor een plek in de profielkaart. We schatten daarom geen vergelijkbare rijders.','This driver lacks enough data for a place on the profile map. Similar drivers are therefore not estimated.')}</p></section>`;
 const ids=[driver.id,...peers.map(p=>p.driver)],url='goat.html#'+new URLSearchParams({drivers:ids.join(','),pcafeatures:selected.join(',')});
 return`<section class="card driver-pca-neighbours"><h2>${t('Vergelijkbare loopbanen','Similar careers')}</h2><p>${t('Deze drie rijders staan het dichtst bij '+driver.name+' in de profielkaart op GOAT.','These three drivers are closest to '+driver.name+' on the GOAT profile map.')}</p><ol>${peers.map(p=>{const d=byId.get(p.driver),row=d.races.at(-1),number=row?.number??d.number,color=row?.color||d.color;return`<li><button type="button" class="interactive-card" data-pca-peer="${esc(d.id)}"><span class="badge" style="--driver-color:${esc(color)}"><span class="number">${esc(Number(number)>=0?number:'?')}</span><span class="stripe"></span>${esc(d.code)}</span><span class="profile-full-name">${esc(d.name)}</span></button></li>`;}).join('')}</ol><p class="muted">${t('Dit vergelijkt volledige loopbanen op dezelfde zes kenmerken als de standaardkaart op GOAT. Het is een overeenkomst in die kaart, geen ranglijst van beste rijders.','This compares complete careers using the same six traits as the default GOAT map. It describes similarity on that map, not a ranking of the best drivers.')}</p><a href="${esc(url)}">${t('Bekijk deze rijders in de profielkaart','View these drivers on the profile map')} ↗</a></section>`;
}
window.driverPCANeighbours={model,render,selected,nearest};
})();
