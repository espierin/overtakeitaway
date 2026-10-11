"""Offline linked exploration of the same stored analysis used by static reports."""
from pathlib import Path
import json
from .analysis import Context,ts
from .driver_style import driver_styles
from .location import display_point
from .map_labels import annotations


def dashboard(run,b,archive_body):
    from .highlights import facts,script as highlight_script,style as highlight_style
    from .render import page
    from .driver_sidebar import sidebar
    from .round_menu import toolbar
    from .branding import branding,language_script,ensure_banner,race_metadata,race_title
    from .race_navigation import navigation
    from .strategy_detail import detail_cycles
    from .race_explorer import explorer_data
    ensure_banner(run.parents[4])
    reference=b['data'].get('circuit_reference',{});track=[display_point(p,reference) for p in b['track']]
    ctx=Context(b['data'],b['config']);positions=[]
    for driver in b['drivers']:
        number=driver['driver_number']
        if driver['grid']:positions.append({'driver':number,'lap':0,'position':driver['grid']})
        for lap in ctx.laps.get(number,[]).rows:
            if lap.get('date_start') and lap.get('lap_duration'):
                position=ctx.position(number,ts(lap['date_start'])+lap['lap_duration']-.001)
                if position:positions.append({'driver':number,'lap':lap['lap_number'],'position':position})
    exclusions={(r['driver'],r['lap']):r['reasons'] for r in b['tyres']['excluded_laps']}
    all_laps=[{'driver':r['driver_number'],'lap':r['lap_number'],'duration':r['lap_duration'],'tyre':ctx.tyre(r['driver_number'],r['lap_number']),'reasons':exclusions.get((r['driver_number'],r['lap_number']),[])} for r in b['data']['laps'] if r.get('lap_duration')]
    events=[{**e,'location':display_point(e['location'],reference) if e.get('location') else None} for e in b['events']]
    payload={'explorer':explorer_data(b['data']),'highlights':facts(b['data'],root=run.parents[4]),'drivers':b['drivers'],'styles':driver_styles(b['data']['drivers']),'events':events,'positions':positions,
             'all_laps':all_laps,'track':track,'labels':annotations(track,reference),'reference':reference,'tyres':b['tyres'],'cycles':detail_cycles(b['cycles'],b['data']['laps']),
             'laps':b['stats']['lap_count'],'late_start':b['stats']['late_start'],'stats':b['stats'],'warnings':b['warnings'],'sources':b['sources'],
             'race':b['data']['session']['circuit_short_name'],'year':b['data']['session']['year'],'f1gures_available':bool(b['data'].get('f1gures')),
             'timing_source':b['data'].get('timing_source','OpenF1')}
    sections=[('lapchart','Wanneer de actie plaatsvond','Klik op een ronde; sleep over de grafiek om een rondereeks te kiezen.'),
              ('driverchart','Wie zorgde voor de actie',''),
              ('mapchart','Waar de actie plaatsvond','Hover of focus voor details. Klik op een marker voor gebeurtenissen en bronnen.'),
              ('positions','Hoe de race zich ontvouwde',''),
              ('firstlap','Start en race: positiewinst',''),
              ('cycles','Waar strategie het verschil maakte','')]
    strategy_sections=[row for row in sections if row[0] in ('cycles','cycledetail')]
    sections=[row for row in sections if row[0] not in ('cycles','cycledetail')]
    map_index=next(i for i,row in enumerate(sections) if row[0]=='mapchart')
    sections[map_index+1:map_index+1]=strategy_sections
    originals={d['driver_number']:d for d in b['data']['drivers']}
    menu=[{**d,'surname':originals.get(d['driver_number'],{}).get('last_name') or d['name'].split(' ')[-1],'color':payload['styles'][d['driver_number']]['color']} for d in b['drivers']]
    body='<script>'+Path(__file__).with_name('race_explorer.js').read_text()+'</script>'+highlight_style()+highlight_script()+sidebar(menu)+'<div class="race-hero">'+branding(seasons_url='../../../../../index.html')+'''<link rel="stylesheet" href="interactive/dashboard.css"><div class="dash-header"><h1>'''+race_title(b['data'])+'''</h1>'''+race_metadata(b['data'])+'''</div></div>
'''+navigation(run)+toolbar(payload['laps'])+'''
<div id="kpis" class="kpi-grid"></div>
<div class="chart-grid">'''
    for id,title,hint in sections:
        body+=f'<section class="interactive-card" id="section-{id}"><h2>{title}</h2>'
        if hint:body+=f'<p class="muted">{hint}</p>'
        if id=='pace':body+='<label><input id="show-excluded" type="checkbox"> Toon ook uitgesloten ronden</label>'
        body+=f'<div id="{id}" class="chart"></div></section>'
    body+='''</div><details class="interactive-card" id="section-events"><summary>Gebeurtenissen in de selectie</summary><label>Zoeken <input id="event-search" type="search" placeholder="Coureur, nummer, type of ID"></label><div id="event-table" class="table-scroll"></div></details>
<dialog id="event-dialog"><button id="close-dialog">Sluiten</button><div id="event-detail"></div></dialog><div id="dash-tooltip" role="tooltip" hidden></div>
<details class="interactive-card"><summary>Bronnen, dekking en beperkingen</summary><div id="source-register"></div></details>
<p><a href="reports/bronnen-en-methode.html">Bronnen en methode</a> · <a href="exports/gebeurtenissen.csv">Gebeurtenissen CSV</a> · <a href="exports/gebeurtenissen.json">Gebeurtenissen JSON</a> · <a href="exports/kerncijfers.json">Kerncijfers</a> · <a href="exports/pitstopstrategie.csv">Pitstopcycli CSV</a></p>
<script id="dashboard-data" type="application/json">'''+json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')+'''</script><script src="interactive/dashboard.js"></script>'''
    target=run/'interactive';target.mkdir(exist_ok=True)
    for ext in ['js','css']:(target/f'dashboard.{ext}').write_text(Path(__file__).with_name(f'dashboard.{ext}').read_text())
    body+=language_script()
    (run/'overzicht.html').write_text(page('Overtake It Away · '+race_title(b['data']),body))
