"""Historical driver badges and season-specific SVG references."""
from pathlib import Path
import json,math,html,re
from functools import lru_cache
from .io import slug
NEUTRAL_TEAM_COLORS=['#c6cedb','#a9bdcf','#c5b8cd','#aac4be','#cfc5ac','#b7c4d4']
SOURCE='https://github.com/MisterSix2295/f1-circuits-svg'

def enrich_drivers(data,raw):
 originals={r['sessionentry']['id']:r['driver'] for r in raw['entries']};teams=list(dict.fromkeys(d['team_id'] for d in data['drivers']))
 for d in data['drivers']:
  driver=originals[d['id']];d['code']=(driver.get('abbreviation') or slug(driver['surname']).replace('-','')[:3]).upper()[:3]
  historical_team=data.get('timing',{}).get('drivers',{}).get(str(d.get('number')),{})
  season_color=historical_team.get('TeamColour','').lstrip('#')
  confirmed='#'+season_color if re.fullmatch(r'[0-9a-fA-F]{6}',season_color) else None
  d['display_color']=confirmed or d.get('color') or NEUTRAL_TEAM_COLORS[teams.index(d['team_id'])%len(NEUTRAL_TEAM_COLORS)]
 if data.get('timing',{}).get('drivers'):
  data['warnings']=[w.replace('Historische teamkleuren zijn niet bevestigd; neutrale lijnen, met verschillende lijnpatronen per team, voorkomen dat moderne kleuren als historische feiten verschijnen.','Teamkleuren voor dit seizoen zijn overgenomen uit het oorspronkelijke timingarchief.') for w in data.get('warnings',[])]
 return data

@lru_cache(maxsize=2)
def registry(root):
 root=Path(root);return (json.loads((root/'assets/maps/circuits.json').read_text())['MRData']['CircuitTable']['Circuits'],json.loads((root/'assets/maps/historical/circuits.json').read_text()))

def in_seasons(year,ranges):
 for token in ranges.split(','):
  part=token.strip().split('-');first=int(part[0]);last=int(part[-1]);
  if first<=year<=last:return True
 return False

def circuit_reference(root,data):
 try:circuits,layouts=registry(str(root))
 except FileNotFoundError:return None
 c=next((c for c in circuits if c['circuitName']==data['circuit'] or c['url'].replace('http:','https:')==data.get('circuit_wikipedia','').replace('http:','https:')),None)
 if not c:return None
 distance=lambda l:math.hypot(float(c['Location']['lat'])-l['latitude'],(float(c['Location']['long'])-l['longitude'])*math.cos(math.radians(float(c['Location']['lat']))))
 match=min(layouts,key=distance)
 if distance(match)>.06:return None
 # The source lists 1995 for Aintree; the race calendar establishes 1955.
 candidates=[l for l in match['layouts'] if in_seasons(data['year'],l['seasons']) or (match['id']=='aintree' and data['year']==1955)]
 if len(candidates)!=1:return None
 variant=candidates[0];target=Path(root)/'assets/maps/historical'/(variant['layoutId']+'.svg')
 if not target.exists():return None
 return {'layout':variant['layoutId'],'seasons':variant['seasons'],'source_url':SOURCE,'path':'../../../../../assets/maps/historical/'+target.name,'status':'illustrative-season-reference'}

def circuit_section(reference):
 if not reference:return ''
 return '<section class="card historical-circuit" id="section-mapchart"><h2>Circuitkaart</h2><img src="'+html.escape(reference['path'])+'" alt="Circuitkaart" loading="lazy"><p>Historische circuitvariant · '+html.escape(reference['layout'])+'</p><p class="muted">Schematische lay-out voor dit seizoen; geen gekoppelde baanlocaties van inhaalacties.</p><p class="source-note"><a href="'+SOURCE+'">SVG-circuitarchief · ROY Jules</a></p></section>'

def presentation_style():return '<style id="historical-presentation-style">'+Path(__file__).with_name('historical_presentation.css').read_text()+'</style>'
