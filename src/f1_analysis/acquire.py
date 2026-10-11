from pathlib import Path
import csv, json
from .io import write_json, slug

ENDPOINTS=['drivers','session_result','laps','position','overtakes','pit','stints','race_control','weather','intervals','team_radio']


def acquire(client, year, gp, raw, source_config, session_key=None):
    warnings=[]; data={}
    sessions=client.api('sessions',year=year)
    from .io import select_race
    if session_key is None:
        session=select_race(sessions,gp)
    else:
        matches=[s for s in sessions if s['session_key']==session_key and s['session_name']=='Race']
        if len(matches)!=1:raise ValueError('Geen unieke hoofdrace voor opgegeven session-key.')
        session=dict(matches[0])
        duplicates=[s for s in sessions if s['session_name']=='Race' and s['circuit_short_name']==session['circuit_short_name']]
        if len(duplicates)>1:session['circuit_short_name']+=f' — {session_key}'
    write_json(raw/'openf1'/'sessions.json',sessions)
    meeting=client.api('meetings',meeting_key=session['meeting_key'])
    data['session']=session;data['meeting']=meeting[0] if meeting else {}
    write_json(raw/'openf1'/'meetings.json',meeting)
    for ep in ENDPOINTS:
        try:data[ep]=client.api(ep,session_key=session['session_key'])
        except ValueError as exc:data[ep]=[];warnings.append(str(exc))
        write_json(raw/'openf1'/(ep+'.json'),data[ep])
    # Starting_grid belongs to qualifying in some API seasons; never assume qualifying order is the actual grid.
    candidates=[session['session_key']]+[s['session_key'] for s in sessions if s['meeting_key']==session['meeting_key'] and s['session_name']=='Qualifying']
    data['starting_grid']=[]
    for key in candidates:
        try:
            rows=client.api('starting_grid',session_key=key)
            if rows:data['starting_grid']=rows;break
        except ValueError:pass
    write_json(raw/'openf1'/'starting_grid.json',data['starting_grid'])
    # Jolpica is a documented public fallback for the actual grid and final classification.
    data['jolpica_results']=[]
    try:
        calendar=client.fetch(f'https://api.jolpi.ca/ergast/f1/{year}.json',publisher='Jolpica',title='Jolpica: racekalender')
        races=calendar['MRData']['RaceTable']['Races']
        match=calendar_match(races,session)
        if len(match)==1:
            race=match[0];data['round']=int(race['round']);data['jolpica_circuit']=race['Circuit']
            result=client.fetch(f'https://api.jolpi.ca/ergast/f1/{year}/{race["round"]}/results.json',publisher='Jolpica',title='Jolpica: startopstelling en uitslag')
            write_json(raw/'supplementary'/'jolpica-results.json',result)
            data['jolpica_results']=result['MRData']['RaceTable']['Races'][0]['Results']
    except (ValueError,KeyError,IndexError) as exc:warnings.append(str(exc))
    if year==2023 and not data['pit'] and data.get('round'):
        try:
            from .history import pit_fallback
            pit_fallback(client,data,raw,warnings)
        except (ValueError,KeyError,IndexError) as exc:
            data['pit_coverage_unknown']=True
            warnings.append('Pitdekking onbekend; baanacties buiten pitcontext kunnen niet worden bevestigd: '+str(exc))
    data['circuit']={}
    if data['meeting'].get('circuit_info_url'):
        try:
            data['circuit']=client.fetch(data['meeting']['circuit_info_url'],publisher='MultiViewer',title='Circuitgeometrie voor gekozen jaar')
            write_json(raw/'supplementary'/'circuit.json',data['circuit'])
            if data['circuit'].get('year')!=year:warnings.append(f'Circuitendpoint voor {year} levert basisgeometrie uit {data["circuit"].get("year")}; basisjaar blijft zichtbaar. Bochtlabels vereisen daarnaast een gecontroleerde officiële jaarvariant; manoeuvreankers worden niet als jaarbevestigd gebruikt. Baanvorm komt uit gemeten racedata.')
        except ValueError as exc:warnings.append(str(exc))
    data['evidence']=[]
    for source in source_config.get('sources',[]):
        if source.get('year') not in [None,year]:continue
        if source.get('gp') and slug(source['gp'])!=slug(session['circuit_short_name']):continue
        record=dict(source)
        try:
            payload=client.fetch(source['url'],kind='bytes',title=source['title'],publisher=source['publisher'],claims=source.get('claims',[]))
            target=raw/'supplementary'/(source['id']+'.'+source.get('format','html'))
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
            record['available']=True
        except ValueError as exc:record['available']=False;warnings.append(str(exc))
        data['evidence'].append(record)
    from .circuit_info import acquire_wikipedia
    acquire_wikipedia(client,data,raw,source_config,warnings)
    # Inspect public page; no undocumented endpoint assumptions or access bypass.
    data['f1gures']=[]
    if data.get('round'):
        url=f'https://www.f1gures.app.hellowebdesign.co.uk/races/{year}/{data["round"]}/'
        try:
            page=client.fetch(url,kind='bytes',publisher='F1gures',title='F1gures: openbare racepagina')
            target=raw/'f1gures'/'racepagina.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(page)
            from .f1gures import discover
            try:data['f1gures']=discover(client,page,url,raw,data['drivers'],year,data['round'])
            except (ValueError,KeyError,TypeError) as exc:warnings.append(str(exc))
        except ValueError as exc:warnings.append(str(exc))
    return data,warnings


def calendar_match(races,session):
    """Match local race dates to UTC sessions, including the Las Vegas night race."""
    from datetime import date
    aliases={'united-kingdom':'great-britain','uk':'great-britain','united-states':'usa','united-states-of-america':'usa','united-arab-emirates':'uae'}
    country=lambda value:aliases.get(slug(value),slug(value))
    session_date=date.fromisoformat(session['date_start'][:10])
    return [r for r in races if abs((date.fromisoformat(r['date'])-session_date).days)<=1 and country(session['country_name'])==country(r['Circuit']['Location']['country'])]


def import_passes(path, year, session):
    path=Path(path)
    if path.suffix.lower()=='.csv':
        with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    else:
        obj=json.loads(path.read_text());rows=obj if isinstance(obj,list) else obj['events']
    allowed={'lap_number','overtaking_driver_number','overtaken_driver_number','source_url','source_title','definition'}
    for i,row in enumerate(rows):
        if not allowed<=row.keys():raise ValueError(f'F1gures-import rij {i+1}: verplichte velden ontbreken: '+', '.join(sorted(allowed-row.keys())))
        for key in ['lap_number','overtaking_driver_number','overtaken_driver_number']:row[key]=int(row[key])
        if row['lap_number']<1 or not row['source_url'].startswith('https://'):raise ValueError('Ongeldige ronde of bron-URL in import.')
        if row.get('year') and int(row['year'])!=year:raise ValueError('Importjaar komt niet overeen.')
        if row.get('session_key') and int(row['session_key'])!=session:raise ValueError('Importsessie komt niet overeen.')
        row['access_method']='handmatige import'
    return rows
