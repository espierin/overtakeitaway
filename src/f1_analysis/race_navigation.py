"""Season navigation and neighbouring editions on the same circuit."""
from pathlib import Path
from urllib.parse import unquote,urlparse
from html import escape
import os,json,re,unicodedata

def circuit_key(run,row):
    filename='archive.json' if row.get('analysis_kind')=='historisch-overzicht' else 'input.json'
    p=run/'data/normalized'/filename
    if p.exists():
        d=json.loads(p.read_text());race=d.get('session',{}).get('jolpica_race',{})
        url=d.get('circuit_wikipedia') or race.get('Circuit',{}).get('url') or d.get('jolpica_circuit',{}).get('url')
        if url:return unquote(urlparse(url).path).split('/')[-1].lower()
    return ''.join(c for c in unicodedata.normalize('NFKD',row.get('gp','').lower()) if c.isalnum())

def navigation(run,rows=None,keys=None):
    run=Path(run);root=run.parents[4];index=root/'analyses/index.json'
    if rows is None:rows=json.loads(index.read_text()) if index.exists() else []
    current=next((r for r in rows if (root/'analyses'/r['path']).resolve()==run.resolve()),None)
    if not current:
        timing=run/'data/normalized/input.json';history=run/'data/normalized/archive.json'
        if not timing.exists() and not history.exists():return ''
        data=json.loads((timing if timing.exists() else history).read_text());session=data.get('session',{})
        current={'path':str(run.relative_to(root/'analyses')),'year':session.get('year',data.get('year')),'gp':session.get('circuit_short_name',data.get('circuit','')),'meeting':session.get('meeting_name',data.get('name','')),'race_date':session.get('date_start',data.get('date','')),'analysis_kind':'timinganalyse' if timing.exists() else 'historisch-overzicht'}
        rows=[r for r in rows if not(r['year']==current['year'] and r.get('race_date','')[:10]==current['race_date'][:10] and r.get('meeting')==current['meeting'])]+[current]
    season=sorted((r for r in rows if r['year']==current['year']),key=lambda r:(r.get('race_date') or '',r['path']));i=season.index(current)
    if keys is None:keys={r['path']:circuit_key(root/'analyses'/r['path'],r) for r in rows}
    editions=sorted((r for r in rows if keys.get(r['path'])==keys.get(current['path']) and r['year']!=current['year']),key=lambda r:(r['year'],r.get('race_date') or ''))
    earlier=[r for r in editions if r['year']<current['year']];later=[r for r in editions if r['year']>current['year']]
    buttons=[('Vorige race',season[(i-1)%len(season)] if len(season)>1 else None),('Volgende race',season[(i+1)%len(season)] if len(season)>1 else None),('Vorig jaar',earlier[-1] if earlier else None),('Volgend jaar',later[0] if later else None)]
    markup='<nav class="race-navigation" aria-label="Racenavigatie">'
    for label,target in buttons:
        if target:
            href=os.path.relpath(root/'analyses'/target['path']/'overzicht.html',run)
            markup+=f'<a href="{escape(href,quote=True)}" title="{escape(str(target["year"])+" · "+target.get("meeting",target["gp"]),quote=True)}">{label}</a>'
        else:markup+=f'<button disabled>{label}</button>'
    return markup+'''</nav><style>.race-navigation{position:sticky;top:var(--race-navigation-top,48px);z-index:55;display:flex;justify-content:flex-end;gap:6px;padding:0 16px;margin:-54px 0 14px;min-height:36px;box-sizing:border-box;pointer-events:none}.race-navigation a,.race-navigation button{pointer-events:auto;box-sizing:border-box;height:var(--race-navigation-button-height,38px);text-decoration:none;font:800 13px system-ui;padding:9px 12px;border:1px solid #596273;border-top:3px solid #51d6dd;background:#080a10f5;color:#fff;border-radius:2px;white-space:nowrap}.race-navigation a:hover,.race-navigation a:focus-visible{border-color:#51d6dd;outline:2px solid #51d6dd}.race-navigation button:disabled{color:#626b79;border-color:#303743;border-top-color:#51d6dd;cursor:default}.race-hero{padding-bottom:80px!important}body .dash-controls{top:0!important;padding-right:var(--race-navigation-width,440px)!important}html{scroll-padding-top:150px}@media(max-width:850px){.race-navigation{top:0;flex-wrap:wrap;padding:6px;gap:4px}body .dash-controls{top:var(--race-navigation-height,48px)!important;padding-right:16px!important}}</style><script data-race-navigation>(()=>{const pending=new URLSearchParams(location.hash.slice(1));if(pending.has('race-module'))document.documentElement.style.visibility='hidden';const init=()=>{const nav=document.querySelector('.race-navigation');const controls=document.querySelector('.dash-controls');const inset=()=>Math.max((controls?.offsetHeight||0)+(parseFloat(controls?getComputedStyle(controls).top:0)||0),nav.offsetHeight+(parseFloat(getComputedStyle(nav).top)||0))+16;nav.addEventListener('click',event=>{const link=event.target.closest('a');if(!link||event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;const url=new URL(link.href,location.href),edge=inset(),modules=[...document.querySelectorAll('.chart-grid>section[id]')],module=modules.find(e=>{const r=e.getBoundingClientRect();return r.top<=edge&&r.bottom>edge;})||modules.find(e=>e.getBoundingClientRect().bottom>edge);if(module&&window.scrollY>100){const r=module.getBoundingClientRect();url.hash='race-module='+encodeURIComponent(module.id)+'&screen-top='+r.top.toFixed(2);}else url.hash='race-module=top';link.href=url.href;});const params=new URLSearchParams(location.hash.slice(1)),moduleId=params.get('race-module');if(moduleId){if('scrollRestoration' in history)history.scrollRestoration='manual';const restore=()=>requestAnimationFrame(()=>requestAnimationFrame(()=>{const module=document.getElementById(moduleId),screenTop=Number(params.get('screen-top')),y=module?window.scrollY+module.getBoundingClientRect().top-(Number.isFinite(screenTop)&&params.has('screen-top')?screenTop:inset()):0;window.scrollTo({top:Math.max(0,y),left:0,behavior:'instant'});document.documentElement.style.visibility='';try{history.replaceState(history.state,'',location.pathname+location.search);}catch{}}));if(document.readyState==='complete')restore();else window.addEventListener('load',restore,{once:true});}const sync=()=>{const root=document.documentElement,button=controls?.querySelector('#zoom-out,#reset');root.style.setProperty('--race-navigation-height',nav.getBoundingClientRect().height+'px');const width=[...nav.children].reduce((sum,e)=>sum+e.getBoundingClientRect().width,0)+Math.max(0,nav.children.length-1)*6+32;root.style.setProperty('--race-navigation-width',width+'px');if(button){root.style.setProperty('--race-navigation-top',(button.getBoundingClientRect().top-controls.getBoundingClientRect().top)+'px');root.style.setProperty('--race-navigation-button-height',button.getBoundingClientRect().height+'px');}};new ResizeObserver(sync).observe(nav);if(controls)new ResizeObserver(sync).observe(controls);window.addEventListener('resize',sync);sync();};if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();})();</script>'''
