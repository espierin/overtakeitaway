"""Publieke sitebestanden, geen veronderstelde of afgeschermde API."""
import json,re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .io import write_json


def discover(client,page,url,raw,drivers,year,round_number):
    soup=BeautifulSoup(page,'html.parser')
    island=next((x for x in soup.find_all('astro-island') if 'RaceWeekend' in x.get('component-url','')),None)
    if island is None:raise ValueError('F1gures: racecomponent niet aangetroffen; import nodig.')
    module_url=urljoin(url,island['component-url'])
    script=client.fetch(module_url,kind='bytes',publisher='F1gures',title='F1gures: openbare weergavedefinitie On-track passes')
    (raw/'f1gures'/'weergavedefinitie.js').write_bytes(script)
    text=script.decode()
    # Discover precisely the template used by the public page, instead of guessing an endpoint.
    match=re.search(r'`(/data/fastf1/\$\{\w+\}/\$\{\w+\}/\$\{\w+\}\.json)`',text)
    if not match:raise ValueError('F1gures: openbaar JSON-pad niet vastgesteld; import nodig.')
    props=json.loads(island['props']);available=[row[1] for row in props['weekend'][1]['available'][1]]
    if 'race' not in available:raise ValueError('F1gures: hoofdracegegevens ontbreken.')
    template=match[1]
    path=template
    for replacement in [str(year),str(round_number),'race']:path=re.sub(r'\$\{\w+\}',replacement,path,count=1)
    data_url=urljoin(url,path)
    payload=client.fetch(data_url,publisher='F1gures',title='F1gures: openbare FastF1-racegegevens',claims=['Brondata voor On-track passes'])
    write_json(raw/'f1gures'/'race.json',payload)
    rows=derive_passes(payload,drivers,data_url,module_url)
    write_json(raw/'f1gures'/'on-track-passes.json',rows)
    return rows


def derive_passes(payload,drivers,url,module_url):
    """Netto omkering op ronde-einden; only explicit positions. Missing positions cannot be invented."""
    if payload.get('type')!='race':raise ValueError('F1gures-JSON is geen hoofdrace.')
    laps=payload.get('laps',{});grid={d['code']:d.get('grid') for d in payload['drivers']}
    neutral=set(n for band in payload.get('trackStatus',[]) for n in range(band['from'],band['to']+1))
    # Conservative gate: this version requires explicit end-of-lap positions and no restart-extension calculation.
    if neutral:raise ValueError('F1gures: neutralisatie-uitbreiding van de site is niet gevalideerd; import nodig.')
    positions={};lookup={d['name_acronym']:d['driver_number'] for d in drivers}
    for code,rows in laps.items():
        if any(len(row)<9 or row[2] is None for row in rows):raise ValueError('F1gures: ontbrekende ronde-eindposities; sitefallback niet gereconstrueerd.')
        positions[code]=[grid.get(code)]+[row[2] for row in rows]
        if positions[code][0] is None:positions[code][0]=positions[code][1]
    result=[]
    for code,rows in laps.items():
        if code not in lookup:continue
        for i,row in enumerate(rows):
            n=i+1;before=positions[code][n-1];after=positions[code][n]
            if row[6] or row[7] or before is None or after is None or after>=before:continue
            for rival,other in laps.items():
                if rival==code or rival not in lookup or i>=len(other) or other[i][6]:continue
                if positions[rival][n-1]<before and positions[rival][n]>after:
                    result.append({'lap_number':n,'overtaking_driver_number':lookup[code],'overtaken_driver_number':lookup[rival],
                                   'source_url':url,'source_title':'F1gures On-track passes','definition':'Netto passages uit ronde-eindposities; ronde 1 inbegrepen, pit- en neutralisatieronden uitgesloten',
                                   'definition_url':module_url,'access_method':'automatisch opgehaalde openbare sitebestanden','compound':row[3]})
    return result
