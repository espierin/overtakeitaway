"""Offline bilingual race catalogue and geographical circuit chooser."""
from pathlib import Path
import json,html,math
from datetime import datetime, timezone
from .historical_presentation import in_seasons
from .branding import branding,language_script
from .driver_sidebar import CSS as sidebar_css

def catalogue_body(root,rows,prefix):
 root=Path(root);source=Path(__file__).parent
 map_assets=root/'assets/maps'
 if not (map_assets/'circuits.json').exists():map_assets=source.parent.parent/'assets/maps'
 circuits=json.loads((map_assets/'circuits.json').read_text())['MRData']['CircuitTable']['Circuits']
 byname={c['circuitName']:c for c in circuits}
 layouts=json.loads((map_assets/'historical/circuits.json').read_text()) if (map_assets/'historical/circuits.json').exists() else []
 asset_prefix='assets/' if prefix else '../assets/'
 previous={}
 previous_drivers={}
 catalogue_page = next((root/name for name in ('races.html','index.html') if (root/name).exists()), None)
 if catalogue_page:
  from bs4 import BeautifulSoup
  from .publication import site_html
  node=BeautifulSoup(site_html(catalogue_page,root),'html.parser').find(id='catalogue-data')
  if node:
   previous_data=json.loads(node.string)
   previous={r['path']:r for r in previous_data['races'] if r.get('path')}
   previous_drivers=previous_data.get('search_drivers',{})
 if (root/'race-updates.json').exists():
  previous.update({r['path']:r for r in json.loads((root/'race-updates.json').read_text())['races'] if r.get('path')})
 from .catalogue_search import load_reference, race_entries, race_direction
 search_reference=load_reference(root)
 search_reference['drivers']={**previous_drivers,**search_reference['drivers']}
 enriched=[]
 for row in rows:
  run=root/'analyses'/row['path'];archive=run/'data/normalized/archive.json';timing=run/'data/normalized/input.json'
  metadata=archive if archive.exists() else timing
  d=json.loads(metadata.read_text()) if metadata.exists() else {}
  if not d and row['path'] in previous:
   old=previous[row['path']]
   preserved={k:old[k] for k in ('name','circuit','circuitId','round','date','winner','winner_number','winner_colour','winner_code','search_entries','direction') if k in old}
   restored={**row,**preserved,'href':prefix+row['path']+'/overzicht.html'}
   restored['search_entries']=race_entries(restored,d,search_reference)
   enriched.append(restored)
   continue
  race=d.get('session',{}).get('jolpica_race',{})
  c=race.get('Circuit',d.get('jolpica_circuit',{}))
  name=d.get('circuit') if isinstance(d.get('circuit'),str) else c.get('circuitName',row['gp'])
  circuit=byname.get(name) or next((x for x in circuits if x['url'].replace('http:','https:')==str(d.get('circuit_wikipedia','')).replace('http:','https:')),None)
  if not circuit and c.get('circuitId'):circuit=next((x for x in circuits if x['circuitId']==c['circuitId']),None)
  winner=next((x for x in d.get('session_result',[]) if x.get('position')==1),{})
  driver=next((x for x in d.get('drivers',[]) if x.get('driver_number')==winner.get('driver_number')),{})
  enriched.append({**row,'winner':driver.get('full_name') or driver.get('name_acronym'),'winner_number':driver.get('driver_number'),'winner_colour':driver.get('team_colour'),'winner_code':driver.get('name_acronym'),'name':d.get('name') or race.get('raceName') or row['meeting'] or row['gp'],'circuit':name,'circuitId':circuit['circuitId'] if circuit else None,'round':d.get('round') or race.get('round'),'date':d.get('date') or race.get('date') or row['race_date'][:10],'href':prefix+row['path']+'/overzicht.html'})
  enriched[-1]['search_entries']=race_entries(enriched[-1],d,search_reference)
 current_year=datetime.now(timezone.utc).year
 calendar_file=root/'_storage/season-calendar.json'
 agenda=json.loads(calendar_file.read_text()).get('seasons',{}).get(str(current_year),[]) if calendar_file.exists() else []
 update_state=json.loads((root/'_storage/update-state.json').read_text()).get('sessions',{}) if (root/'_storage/update-state.json').exists() else {}
 for event in agenda:
  race=event['jolpica_race'];round_=int(event['round'])
  if any(r['year']==current_year and int(r.get('round') or 0)==round_ for r in enriched):continue
  record=next((v for k,v in update_state.items() if str(k)==str(event['session_key']) or (v.get('year')==current_year and v.get('round')==round_)),{})
  c=race['Circuit']
  enriched.append({'year':current_year,'name':race['raceName'],'gp':c['circuitName'],'circuit':c['circuitName'],'circuitId':c['circuitId'],
                   'round':round_,'date':race['date'],'start':event['date_start'],'scheduled':True,'progress':record.get('progress',0),'waiting':record.get('status')=='wacht_op_data','href':None,'path':None,'analysis_kind':'scheduled'})
 # Calendar timestamps identify the main race, never the sprint session.
 agenda_by_round={int(event['round']):event for event in agenda}
 for row in enriched:
  event=agenda_by_round.get(int(row.get('round') or 0)) if row['year']==current_year else None
  if event:
   row['start']=event['date_start']
  if row.get('scheduled'):
   completed=sorted((r for r in enriched if not r.get('scheduled') and r.get('circuitId')==row.get('circuitId')),key=lambda r:(r['year'],r['date']),reverse=True)
   row['previous_edition_href']=completed[0]['href'] if completed else None
  row.setdefault('start',row.get('race_date') or row['date']+'T13:00:00Z')
  if row['year']==current_year and not row.get('scheduled') and (not row.get('winner') or not row.get('winner_code')):
   from bs4 import BeautifulSoup
   from .publication import site_html
   overview=root/'analyses'/row['path']/'overzicht.html'
   node=BeautifulSoup(site_html(overview,root),'html.parser').find(id='dashboard-data') if overview.exists() else None
   if node:
    payload=json.loads(node.string);winner=next((x for x in payload.get('drivers',[]) if x.get('finish')==1),{})
    row.update(winner=winner.get('name') or row.get('winner'),winner_number=winner.get('driver_number') or row.get('winner_number'),winner_code=winner.get('code'),winner_colour=payload.get('styles',{}).get(str(winner.get('driver_number')),{}).get('color') or row.get('winner_colour'))
  c=next((c for c in circuits if c['circuitId']==row['circuitId']),None)
  row['direction']=race_direction(row,{},search_reference,c)
  if not c:continue
  row['country']=c['Location']['country']
  row['flag_background']=asset_prefix+'flags/'+row['country'].lower().replace(' ','-')+'.webp'
  background='circuits/'+c['circuitId']+'.webp'
  row['background']=asset_prefix+(background if (root/'assets'/background).exists() else 'f1-banner-v3.png')
  measured='maps/measured/'+str(row['year'])+'-'+c['circuitId']+'.svg'
  if (root/'assets'/measured).exists():row['track_image']=asset_prefix+measured
  if layouts:
   distance=lambda l:math.hypot(float(c['Location']['lat'])-l['latitude'],(float(c['Location']['long'])-l['longitude'])*math.cos(math.radians(float(c['Location']['lat']))))
   layout=next((l for l in layouts if l['id']==({'vegas':'las-vegas','las_vegas':'caesars-palace'}.get(c['circuitId'],c['circuitId']))),None) or min(layouts,key=distance)
   if layout['id']!=c['circuitId'] and distance(layout)>.01:continue
   variants=[l for l in layout['layouts'] if in_seasons(row['year'],l['seasons'])]
   # Bahrain's outer layout was used specifically for the 2020 Sakhir GP.
   if c['circuitId']=='bahrain' and row['year']==2020:
    variants=[l for l in layout['layouts'] if l['layoutId']==('bahrain-3' if 'sakhir' in row['name'].lower() else 'bahrain-1')]
   variant=(variants or layout['layouts'])[-1]
   layout_id=variant['layoutId']
   # The upstream modern Zandvoort entry omits the existing variant suffix.
   if layout_id=='zandvoort':layout_id='zandvoort-5'
   row['track_image']=asset_prefix+'maps/historical/'+layout_id+'.svg'
 missing=[r['circuit'] for r in enriched if not r['circuitId']]
 # In incomplete archives retain the race card even when geographical metadata is absent.
 used={r['circuitId'] for r in enriched};circuits=[c for c in circuits if c['circuitId'] in used]
 land=json.loads((map_assets/'land.geojson').read_text());paths=[]
 for feature in land['features']:
  geom=feature['geometry'];polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
  for poly in polys:
   for ring in poly:
    paths.append('M'+'L'.join(f'{(lon+180)*4:.1f},{(90-lat)*4:.1f}' for lon,lat,*_ in ring)+'Z')
 svg='<svg id="world-map" viewBox="0 0 1440 640" aria-label="Wereldkaart" role="img"><defs><pattern id="geo-grid" width="120" height="120" patternUnits="userSpaceOnUse"><path d="M120 0H0V120" fill="none" stroke="#51d6dd" stroke-opacity=".12"/></pattern></defs><rect width="1440" height="720" fill="#0b1019"/><g fill="#162a36" stroke="#51d6dd" stroke-opacity=".48" stroke-width=".7">'+''.join('<path d="'+p+'"/>' for p in paths)+'</g><rect width="1440" height="720" fill="url(#geo-grid)" pointer-events="none"/><g id="circuit-pins"></g></svg>'
 translations={'Zoek een race, circuit of coureur':'Search for a race, circuit or driver','Bijvoorbeeld Monaco 95 of Verstappen+':'For example Monaco 95 or Verstappen+','Zoekfilters':'Search filters','Zoekhulp':'Search help','Circuitlay-outs':'Circuit layouts','Ontdek de race achter de uitslag':'Discover the race behind the result','Kies een seizoen, zoek een race of verken de circuits op de wereldkaart.':'Choose a season, search for a race or explore circuits on the world map.','Zoek een race of circuit':'Search for a race or circuit','Bijvoorbeeld Monaco, Spa of 1967':'For example Monaco, Spa or 1967','◎ Wereldkaart':'◎ World map','Alle circuits':'All circuits','Geen races gevonden. Probeer een andere zoekterm.':'No races found. Try another search term.','Kies een circuit':'Choose a circuit','Alle WK-circuits in het archief · sleep om te verplaatsen, scroll om te zoomen.':'All championship circuits in the archive · drag to pan, scroll to zoom.','Geselecteerd circuit':'Selected circuit','Zoek een circuit':'Search for a circuit','Naam, plaats of land':'Name, location or country','Wereld passend in beeld':'Fit world map','Wereldkaart':'World map','WERELDWIJD CIRCUITNETWERK':'GLOBAL CIRCUIT NETWORK','SEIZOENEN':'SEASONS','2021–heden':'2021–present','Groepen uitklappen':'Expand groups','Groepen inklappen':'Collapse groups','UITKLAPPEN':'EXPAND','INKLAPPEN':'COLLAPSE'}
 language=language_script().replace('const exact={','const exact={'+','.join(json.dumps(k,ensure_ascii=False)+':'+json.dumps(v,ensure_ascii=False) for k,v in translations.items())+',')
 data=json.dumps({'races':enriched,'circuits':circuits,'current_year':current_year,'search_drivers':search_reference['drivers']},ensure_ascii=False).replace('</','<\\/')
 from .io import write_json
 updates=[{**r,'id':str(r['year'])+'-'+str(r.get('round') or r['gp']),'version':r.get('created_at',r['path']),
           'href':'analyses/'+r['path']+'/overzicht.html','background':r.get('background','').removeprefix('../'),
           'track_image':r.get('track_image','').removeprefix('../')} for r in enriched if not r.get('scheduled')]
 write_json(root/'race-updates.json',{'races':updates})
 year_label=str(min(r['year'] for r in rows))+'–'+str(max(r['year'] for r in rows)) if rows else '1950–heden'
 body='<style>'+sidebar_css+source.joinpath('catalogue.css').read_text()+'</style><aside class="driver-sidebar year-sidebar" aria-label="Seizoenen"><h2>SEIZOENEN</h2><div id="year-strip" class="driver-picker-list"></div><footer><button id="expand-years" title="Groepen uitklappen">UITKLAPPEN</button><button id="collapse-years" title="Groepen inklappen">INKLAPPEN</button></footer></aside><div class="race-hero catalogue-hero">'+branding('assets/f1-banner-v3.png' if prefix else '../assets/f1-banner-v3.png')+'''<div class="catalogue-intro"><span class="eyebrow">RACE EXPLORER</span><h1>Ontdek de race achter de uitslag</h1><p>Kies een seizoen, zoek een race of verken de circuits op de wereldkaart.</p><div id="catalogue-stats"></div></div></div><main>
<div class="catalogue-tools"><label class="search-label"><span class="search-heading"><span>Zoek een race, circuit of coureur</span><button id="search-help-toggle" type="button" aria-label="Zoekhulp" aria-expanded="false" aria-controls="search-help">?</button></span><input id="catalog-search" type="search" placeholder="Bijvoorbeeld Monaco 95 of Verstappen+"></label><button id="open-world" class="accent-button">◎ Wereldkaart</button></div>
<div id="search-help" hidden role="region" aria-label="Zoekhulp"></div><select id="year-select" aria-label="Seizoen" hidden></select><button id="clear-circuit" class="accent-button" hidden>Alle circuits</button>
<nav id="season-race-nav" class="season-race-nav" hidden></nav><div class="calendar-heading"><h2 id="calendar-title"></h2><span id="catalog-count" aria-live="polite"></span></div><div id="race-cards"></div><p id="empty-results" hidden>Geen races gevonden. Probeer een andere zoekterm.</p>
</main><footer class="catalogue-footer"><span>'''+year_label+''' · Formula 1 World Championship</span><span>Circuits: <a href="https://api.jolpi.ca/ergast/f1/circuits/">Jolpica</a> · <span>Zoekfilters</span>: <a href="https://github.com/f1db/f1db">F1DB</a> · Kaart: <a href="https://www.naturalearthdata.com/">Natural Earth</a> · <span>Circuitlay-outs</span>: <a href="https://github.com/MisterSix2295/f1-circuits-svg">ROY Jules</a></span></footer>
<dialog id="world-dialog"><div class="world-heading"><div><span class="eyebrow">WERELDWIJD CIRCUITNETWERK</span><h2>Kies een circuit</h2><p>Alle WK-circuits in het archief · sleep om te verplaatsen, scroll om te zoomen.</p></div><button id="close-world" aria-label="Sluiten">✕</button></div><div class="world-layout"><div class="world-canvas">'''+svg+'''<div class="world-controls"><button id="world-in" aria-label="Inzoomen">+</button><button id="world-out" aria-label="Uitzoomen">−</button><button id="world-fit" aria-label="Wereld passend in beeld">⛶</button></div><div id="map-tip" hidden></div><div class="map-key"><i></i><span>Geselecteerd circuit</span></div></div><aside class="circuit-sidebar"><label><span>Zoek een circuit</span><input id="circuit-search" type="search" placeholder="Naam, plaats of land"></label><div id="circuit-list"></div><div id="circuit-detail" hidden></div></aside></div></dialog>
<script id="catalogue-data" type="application/json">'''+data+'</script>'+language+'<script>'+source.joinpath('catalogue.js').read_text()+'</script>'

 return body
