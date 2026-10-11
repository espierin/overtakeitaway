"""Offline historical race summaries from a hashed public Jolpica database dump.

Lap-end positions are observations, never an overtaking event feed. Entries are
keyed by session-entry id: historic shared cars and reused numbers stay separate.
"""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
import csv, io, zipfile, hashlib, shutil, html, json, uuid, re
from .io import Client, read_json, write_json, write_csv, utcnow, slug


def integer(value):
    return int(value) if value not in ('', None) else None


def seconds(value):
    if not value:return None
    parts=value.split(':')
    return sum(float(v)*60**i for i,v in enumerate(reversed(parts)))


class Archive:
    def __init__(self, root, offline=False, refresh=False):
        self.root=Path(root)
        c=Client(root,{'request_interval_seconden':2.1},offline=offline,refresh=refresh)
        catalogue=c.fetch('https://api.jolpi.ca/data/dumps/download/',publisher='Jolpica',title='Historische databasedumps')
        # The delayed dump is the public download. The latest dump requires authentication.
        descriptor=catalogue['delayed_dumps']['csv']
        body=c.fetch(descriptor['download_url'],kind='bytes',publisher='Jolpica',title='Historische database CSV, publieke download')
        digest=hashlib.sha256(body).hexdigest()
        if digest!=descriptor['file_hash']:raise ValueError('Hash van historische database wijkt af van broncatalogus.')
        self.original=self.root/'analyses/sources/jolpica'/(digest+'.zip')
        self.original.parent.mkdir(parents=True,exist_ok=True)
        if not self.original.exists():self.original.write_bytes(body)
        self.sources=c.sources;self.descriptor=descriptor
        self.tables={};self.laps=defaultdict(list);self.pits=defaultdict(list);self.entries=defaultdict(list)
        z=zipfile.ZipFile(io.BytesIO(body))
        for name in ['season','round','session','sessionentry','roundentry','teamdriver','team','driver','circuit']:
            self.tables[name]={r['id']:r for r in csv.DictReader(io.TextIOWrapper(z.open('formula_one_'+name+'.csv')))}
        self.races={k:v for k,v in self.tables['session'].items() if v['type']=='R' and v['is_cancelled']=='f' and self.tables['round'][v['round_id']]['is_cancelled']=='f'}
        for r in self.tables['sessionentry'].values():
            if r['session_id'] in self.races:self.entries[r['session_id']].append(r)
        for r in csv.DictReader(io.TextIOWrapper(z.open('formula_one_lap.csv'))):
            self.laps[r['session_entry_id']].append(r)
        lap_numbers={r['id']:integer(r['number']) for rows in self.laps.values() for r in rows}
        for r in csv.DictReader(io.TextIOWrapper(z.open('formula_one_pitstop.csv'))):
            self.pits[r['session_entry_id']].append({**r,'lap_number':lap_numbers.get(r['lap_id'])})

    def year(self, session):
        round_=self.tables['round'][session['round_id']]
        return int(self.tables['season'][round_['season_id']]['year'])

    def calendar(self, year):
        return sorted([r for r in self.races.values() if self.year(r)==year],key=lambda r:int(self.tables['round'][r['round_id']]['number']))

    def race(self, session):
        t=self.tables;r=t['round'][session['round_id']];circuit=t['circuit'][r['circuit_id']];year=self.year(session)
        rows=[];raw=[]
        for e in self.entries[session['id']]:
            re_=t['roundentry'][e['round_entry_id']];td=t['teamdriver'][re_['team_driver_id']];d=t['driver'][td['driver_id']];team=t['team'][td['team_id']]
            color=team.get('primary_color','')
            # Current database colours are not evidence of historical season colours.
            historical_color=None
            raw.append({'sessionentry':e,'roundentry':re_,'teamdriver':td,'driver':d,'team':team,'laps':self.laps[e['id']],'pitstops':self.pits[e['id']]})
            lap_rows=[{'lap':integer(l['number']),'position':integer(l['position']),'seconds':seconds(l['time']),'deleted':l['is_deleted']=='t'} for l in self.laps[e['id']] if l['number']]
            rows.append({'id':e['id'],'driver_id':d['id'],'name':d['forename']+' '+d['surname'],'number':integer(re_['car_number']),
                         'team':team['name'],'team_id':team['id'],'color':historical_color,'grid':integer(e['grid']) if integer(e['grid']) not in (None,0) else None,
                         'position':integer(e['position']),'classified':e['is_classified']=='t','status':e['detail'] or 'Onbekend',
                         'completed_laps':integer(e['laps_completed']),'points':float(e['points']) if e['points'] else None,'time':e['time'] or None,
                         'laps':sorted(lap_rows,key=lambda l:l['lap']),
                         'pitstops':[{'stop':integer(p['number']),'lap':p['lap_number'],'local_time':p['local_timestamp'] or None,'duration':seconds(p['duration'])} for p in self.pits[e['id']]],
                         'wikipedia':d['wikipedia']})
        rows.sort(key=lambda d:(d['position'] is None,d['position'] or 999,d['name']))
        lap_count=sum(len(d['laps']) for d in rows);pit_count=sum(len(d['pitstops']) for d in rows)
        duplicate_numbers=Counter(d['number'] for d in rows if d['number'] is not None)
        warnings=['Inhaalacties, bandencompounds, neutralisaties en circuitlocaties ontbreken in deze uitslagenbron. Onbekend betekent niet nul.',
                  'Posities per ronde zijn momentopnamen aan het ronde-einde. Positiewisselingen kunnen ook door pitstops, uitval of terugronden ontstaan; ze worden niet als inhaalacties geteld.',
                  'Historische teamkleuren zijn niet bevestigd; neutrale lijnen, met verschillende lijnpatronen per team, voorkomen dat moderne kleuren als historische feiten verschijnen.',
                  'Pitstopduur is de geregistreerde bronduur; niet gelijkgesteld aan stilstandtijd. Pitstoptijden zijn lokale tijden zonder afgeleide UTC-tijd.']
        if not lap_count:warnings.append('Geen afzonderlijke rondetijden of posities per ronde beschikbaar voor deze race.')
        if not pit_count:warnings.append('Geen afzonderlijke pitstopregistraties beschikbaar; het aantal werkelijke stops is onbekend.')
        if any(n>1 for n in duplicate_numbers.values()):warnings.append('Startnummers komen meermaals voor. Coureurs blijven afzonderlijke bronentries; gedeelde auto’s worden niet samengevoegd of dubbel geïnterpreteerd als unieke auto’s.')
        result = {'year':year,'round':int(r['number']),'date':r['date'],'name':r['name'],'circuit':circuit['name'],'circuit_wikipedia':circuit['wikipedia'],
                'wikipedia':r['wikipedia'],'session_id':session['id'],'scheduled_laps':integer(session['scheduled_laps']),
                'drivers':rows,'lap_records':lap_count,'pit_records':pit_count,'warnings':warnings,
                'coverage_label':'Uitslag + rondegegevens'+(' + pitstops' if pit_count else '') if lap_count else 'Uitslagenarchief',
                'raw':{'round':r,'session':session,'circuit':circuit,'entries':raw}}
        from .historical_backfill import apply_retained
        return apply_retained(result, result['raw'], self.root)


def infographic(run, data):
    """A compact 4K race result infographic; no missing-event counts are invented."""
    from PIL import Image, ImageDraw, ImageFont
    image=Image.new('RGB',(3840,2160),'#10141d');draw=ImageDraw.Draw(image)
    regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    def font(size,strong=False):return ImageFont.truetype(bold if strong else regular,size)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3840 2160"><rect width="3840" height="2160" fill="#10141d"/>']
    def text(x,y,value,size=38,color='#f5f7fa',strong=False):
        draw.text((x,y),str(value),font=font(size,strong),fill=color)
        svg.append(f'<text x="{x}" y="{y+size}" fill="{color}" font-family="DejaVu Sans,sans-serif" font-size="{size}" font-weight="{700 if strong else 400}">{html.escape(str(value))}</text>')
    text(100,80,f"{data['year']} · {data['name']}",78,strong=True)
    text(100,200,f"{data['date']} · {data['circuit']}",42,'#b3bece')
    text(100,300,'Historische uitslag · '+data['coverage_label'],42,'#51d6dd')
    columns=2 if len(data['drivers'])>22 else 1;per=(len(data['drivers'])+columns-1)//columns
    step=min(65,1450/max(1,per));fs=min(34,int(step*.65))
    for i,d in enumerate(data['drivers']):
        col=i//per;row=i%per;x=100+col*1840;y=440+row*step
        position=str(d['position']) if d['position'] is not None else '—';number=str(d['number']) if d['number'] is not None else '?'
        text(x,y,position+'.',fs,'#ff4b56',True);text(x+95,y,'#'+number+'  '+d['name'],fs,strong=True)
        text(x+1000,y,(str(d['completed_laps']) if d['completed_laps'] is not None else '?')+' ronden',fs,'#b3bece')
        text(x+1320,y,d['status'][:24],fs,'#b3bece')
    text(100,1990,'Inhaalacties en baanlocaties: onbekend · geen reconstructie uit eindposities',36,'#b3bece')
    text(100,2070,'Bron: Jolpica · oorspronkelijke CSV-database opgeslagen met SHA-256',30,'#b3bece')
    for ext in ['png','svg']:(run/'figures'/ext).mkdir(parents=True,exist_ok=True)
    image.save(run/'figures/png/hoofdinformatie.png',compress_level=3)
    (run/'figures/svg/hoofdinformatie.svg').write_text(''.join(svg)+'</svg>')


def render_archive(run,data,manifest):
    from .highlights import facts,script as highlight_script,style as highlight_style
    from .render import page,markdown_html,table
    from .driver_sidebar import sidebar
    from .round_menu import toolbar
    from .branding import branding,language_script,ensure_banner,race_metadata,race_title
    from .race_navigation import navigation
    ensure_banner(run.parents[4])
    js=Path(__file__).with_name('archive.js').read_text()
    escape=html.escape
    raw = read_json(run/'data/raw/race.json')
    from .historical_backfill import apply_retained, supplemental_facts, coverage_notes, write_method_report
    data = apply_retained(data, raw, run.parents[4])
    highlight_facts=facts(data,raw,root=run.parents[4])
    from .historical_presentation import enrich_drivers,circuit_reference,circuit_section,presentation_style
    data=enrich_drivers(data,read_json(run/'data/raw/race.json'));reference=circuit_reference(run.parents[4],data)
    timing_file=run/'data/raw/fastf1/historical-timing.json'
    if timing_file.exists():
        data['timing']=read_json(timing_file);data=enrich_drivers(data,read_json(run/'data/raw/race.json'))
    highlight_facts=supplemental_facts(data,highlight_facts)
    if data.get('historical_supplement'):
        write_json(run/'data/normalized/historical-supplement.json', data['historical_supplement'])
    for value in highlight_facts.values():
        for item in value if isinstance(value,list) else [value]:
            if isinstance(item,dict) and 'id' in item:item['color']=next((d['display_color'] for d in data['drivers'] if d['id']==item['id']),item.get('color','#B3BECE'))
    payload=json.dumps({**{k:v for k,v in data.items() if k!='raw'},'highlights':highlight_facts},ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    originals={r['sessionentry']['id']:r['driver'] for r in read_json(run/'data/raw/race.json')['entries']}
    menu=sidebar([{**d,'color':d['display_color'],'surname':originals[d['id']]['surname'],'code':originals[d['id']].get('abbreviation')} for d in data['drivers']],all_id='all',none_id='none',archive=True)
    rounds=max([1]+[l['lap'] for d in data['drivers'] for l in d['laps']]+[d['completed_laps'] or 0 for d in data['drivers']])
    top=toolbar(rounds,archive=True)
    body=presentation_style()+highlight_style()+highlight_script()+menu+'<div class="race-hero">'+branding(seasons_url='../../../../../index.html')+f'''
<h1>{race_title(data)}</h1>{race_metadata(data)}
</div>{navigation(run)}{top}<div id="kpis" class="kpi-grid"></div><p class="muted">Historisch raceoverzicht. Inhaalacties, bandenstrategie en baanlocaties: onbekend.</p>
<section class="card"><label>Zoeken <input id="search" placeholder="Coureur of startnummer"></label><p id="summary" aria-live="polite"></p></section>
{circuit_section(reference)}
<section class="card"><h2>Gereden ronden per coureur</h2><p>Klik op een balk voor de brongegevens. Nummer en naam staan naast iedere balk.</p><div id="bars"></div></section>
<section class="card"><h2>Positie aan het ronde-einde</h2><p>Hover op een punt voor coureur, ronde, positie en rondetijd. Selecteer ronden om in te zoomen. Dit zijn geen inhaalregistraties.</p><div id="positions"></div></section>
<section class="card"><h2>Rondetijden</h2><p>Bronwaarden inclusief pit- en neutralisatieronden; geen gefilterde banden- of tempoanalyse.</p><div id="pace"></div></section>
<section class="card"><h2>Uitslag en startopstelling</h2><p>Klik op een kolomkop om te sorteren. — betekent onbekend.</p><div style="overflow:auto"><table id="results"></table></div></section>
<section class="card"><h2>Pitstopregistraties</h2><div id="pits"></div></section>
<dialog id="detail"><button id="close">Sluiten</button><h2 id="detailtitle"></h2><pre id="detailbody"></pre></dialog>
<h2>Datadekking</h2><ul>{''.join('<li>'+escape(w)+'</li>' for w in data['warnings'])}</ul>
<p><a href="{escape(data['wikipedia'],quote=True)}">Race op Wikipedia</a> · <a href="{escape(data['circuit_wikipedia'],quote=True)}">Circuit op Wikipedia</a></p>
<script id="archive-data" type="application/json">{payload}</script><script>{js}</script>'''
    css='''<style>.card{margin-top:24px}.choices{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}.choices label{font-size:14px}svg{max-height:none}.chart{min-width:700px}.chartwrap{overflow:auto}dialog{background:#181f2c;color:white;border:1px solid #596273;max-width:90vw;max-height:80vh}dialog::backdrop{background:#0009}button,label,a{cursor:pointer}input[type=number]{width:80px}th button{font-weight:bold}td button{padding:2px 6px}.muted{color:#b3bece}</style>'''
    if data.get('timing'):body=body.replace('Historisch raceoverzicht. Inhaalacties, bandenstrategie en baanlocaties: onbekend.','Historisch raceoverzicht met aanvullende sector- en bandentiming. Inhaalregistraties en baanlocaties zijn niet beschikbaar.')
    if data.get('historical_supplement'):
        body = re.sub(r'<h2>Datadekking</h2>\s*<ul>.*?</ul>', lambda m: '<h2>Datadekking</h2><ul id="history-coverage-notes">' + ''.join('<li data-history-note data-nl="' + escape(nl,quote=True) + '" data-en="' + escape(en,quote=True) + '">' + escape(nl) + '</li>' for nl,en in coverage_notes()) + '</ul>', body, count=1, flags=re.S)
        body += '<p><a href="data/normalized/historical-supplement.json" data-history-note data-nl="Aanvullende brongegevens en controlelog" data-en="Additional source data and audit log">Aanvullende brongegevens en controlelog</a> · <a href="../../../../../analyses/sources/historical/coverage-report.html" data-history-note data-nl="Dekking van het historische archief" data-en="Historical archive coverage">Dekking van het historische archief</a></p><script defer data-historical-data src="../../../../../assets/historical-data.js"></script>'
    (run/'overzicht.html').write_text(page('Overtake It Away · '+data['name']+' '+str(data['year']),css+body+language_script()))
    results=[[d['position'],d['number'],d['name'],d['team'],d['grid'],d['completed_laps'],d['points'],d['status']] for d in data['drivers']]
    classified=[d for d in data['drivers'] if d['classified']]
    winner=next((d for d in data['drivers'] if d['position']==1),None)
    narrative=f"# {data['name']} {data['year']}\n\nDatum: {data['date']}. Circuit: {data['circuit']}.\n\n"
    if winner:narrative+=f"De bron classificeert {winner['name']} als winnaar, met {winner['completed_laps']} ronden en {winner['points']} punten.\n\n"
    narrative+=f"De bron bevat {len(data['drivers'])} coureursentries, waarvan {len(classified)} geclassificeerd, {data['lap_records']} afzonderlijke ronde-records en {data['pit_records']} pitstopregistraties. Bronentries zijn niet noodzakelijk unieke auto's: historische gedeelde auto's blijven afzonderlijke records.\n\n"
    narrative+=table(['Positie','Nummer','Coureur','Team','Start','Ronden','Punten','Status'],results)
    common='\n\n[Interactief overzicht](../overzicht.html) · [Brongegevens](../data/normalized/archive.json)\n'
    reports={'raceanalyse':narrative,
             'ronde-1':'# Ronde 1\n\n'+('Posities aan het einde van ronde 1 zijn beschikbaar in het interactieve overzicht. Vergelijking met startposities is een nettoverandering, geen inhaaltelling.' if any(l['lap']==1 for d in data['drivers'] for l in d['laps']) else 'Posities na ronde 1 ontbreken in deze bron. Startposities en einduitslagen vullen deze ontbrekende gegevens niet in.'),
             'inhaalacties':'# Inhaalacties\n\nOnbekend. Deze historische bron heeft geen inhaalfeed of voldoende context om positiewisselingen als inhalen op de baan te certificeren. Geen fictieve nullen of kaartpunten.',
             'bandenstrategie':'# Bandenstrategie\n\nCompounds, bandenleeftijden en stints ontbreken. Beschikbare rondetijden omvatten ook pitstops, verkeer en neutralisaties; daaruit volgt geen bevestigde bandenstrategie.',
             'undercut-overcut':'# Undercut en overcut\n\nGeen bevestigde undercut- of overcutanalyse: pit-in/out, compounds, verkeerscontext en neutralisaties ontbreken. Pitstopregistraties zijn waar beschikbaar interactief inspecteerbaar.',
             'bronnen-en-methode':'# Bronnen en methode\n\nBron: Jolpica publieke CSV-databasedump (14 dagen vertraagd). De volledige originele ZIP is lokaal bewaard; SHA-256 is gecontroleerd tegen de downloadcatalogus. Elke bronentry en alle beschikbare ronde- en pitregistraties zijn ongewijzigd opgenomen in raw/race.json. Startnummers behoren tot deze race, niet automatisch tot een coureurcarrière.\n\nRondeposities zijn momentopnamen aan het einde van de ronde. Ontbrekende waarden blijven onbekend. Pitduur wordt niet geïnterpreteerd als stilstandtijd. De database geeft actuele teamkleuren; zonder historische verificatie gebruiken de oudere overzichten neutrale kleuren.\n\n'+f"[Originele databasedump]({Path(__import__('os').path.relpath(manifest['source_archive'],run/'reports')).as_posix()})\n\n[Bronmanifest](../manifest.json)",
             'datakwaliteit':'# Datakwaliteit\n\nStatus: gedeeltelijk.\n\n'+'\n'.join('- '+w for w in data['warnings'])}
    (run/'reports').mkdir(exist_ok=True)
    for name,report in reports.items():
        if name!='bronnen-en-methode':continue
        text=report+common;(run/'reports'/(name+'.md')).write_text(text);from .branding import language_controls,language_script
        (run/'reports'/(name+'.html')).write_text(page(name,language_controls()+markdown_html(text)+language_script()))
    if data.get('historical_supplement'): write_method_report(run, data, manifest)


def generate(archive,session,update=True):
    from .cli import code_hash
    from .render import check_links, update_index
    data=archive.race(session);root=archive.root
    base=root/'analyses'/str(data['year'])/(f"{data['round']:02}-"+slug(data['name']))
    pointer=base/'latest.json'
    if pointer.exists():
        previous=base/read_json(pointer)['run'];m=read_json(previous/'manifest.json')
        if m.get('archive_sha256')==archive.descriptor['file_hash'] and m.get('code_sha256')==code_hash(root):return previous
    run=base/'runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:6]);run.mkdir(parents=True)
    write_json(run/'data/raw/race.json',data.pop('raw'));write_json(run/'data/normalized/archive.json',data)
    export=[{k:v for k,v in d.items() if k not in ['laps','pitstops']} for d in data['drivers']];write_csv(run/'exports/uitslag.csv',export)
    write_csv(run/'exports/ronden.csv',[{'entry_id':d['id'],'coureur':d['name'],'nummer':d['number'],**l} for d in data['drivers'] for l in d['laps']])
    write_csv(run/'exports/pitstops.csv',[{'entry_id':d['id'],'coureur':d['name'],'nummer':d['number'],**p} for d in data['drivers'] for p in d['pitstops']])
    manifest={'created_at':utcnow(),'version':'0.1.0','code_sha256':code_hash(root),'input':{'year':data['year'],'gp':data['name']},
              'session':{'year':data['year'],'session_key':int(session['id']),'session_name':'Race','circuit_short_name':data['circuit'],'date_start':data['date']},
              'meeting':{'meeting_name':data['name']},'status':'gedeeltelijk','analysis_kind':'historisch-overzicht','coverage_label':data['coverage_label'],
              'coverage':{'session_result':len(data['drivers']),'laps':data['lap_records'],'pit':data['pit_records'],'overtakes':None,'location':None,'stints':None},
              'warnings':data['warnings'],'sources':archive.sources,'archive_sha256':archive.descriptor['file_hash'],'source_archive':str(archive.original),
              'counting_rules':{'overtakes':'onbekend; rondeposities niet als inhaalacties geteld','entries':'session-entry-id; gedeelde startnummers blijven apart'}}
    write_json(run/'manifest.json',manifest)
    render_archive(run,data,manifest);check_links(run)
    manifest['file_hashes']={str(p.relative_to(run)):hashlib.sha256(p.read_bytes()).hexdigest() for p in run.rglob('*') if p.is_file() and p.name!='manifest.json'};manifest['files']=list(manifest['file_hashes'])
    write_json(run/'manifest.json',manifest);write_json(pointer,{'run':str(run.relative_to(base)),'status':'gedeeltelijk','created_at':manifest['created_at']})
    if update:update_index(root)
    for old in (base/'runs').iterdir():
        if old!=run and old.is_dir():shutil.rmtree(old)
    return run
