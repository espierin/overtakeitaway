"""Historical timing adapter. Rank inversions are derived candidates, not official overtakes."""
from pathlib import Path
from itertools import combinations
from bisect import bisect_left, bisect_right
import gzip, hashlib, json, shutil, math
from .io import write_json, read_json, utcnow, select_race

SCHEMA = 1


def pit_fallback(client,data,raw,warnings):
    """Fill missing OpenF1 pit coverage from archived in/out timing, with UTC telemetry clock."""
    import fastf1, pandas as pd
    from fastf1 import api
    import requests
    year=data['session']['year'];round_=data['round']
    path=client.root/'cache/history-pit'/f'{year}-{round_:02}.json'
    if path.exists() and not client.refresh:
        saved=read_json(path);data['pit']=saved['pit'];client.sources.extend(saved['sources'])
        write_json(raw/'fastf1/pit-fallback.json',saved)
        for item in saved['sources']:
            body=client.root/item['local_archive'];target=raw/'f1-timing'/body.name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(body,target)
    else:
        if client.offline:raise ValueError('Historische pitbron ontbreekt in cache.')
        cache=client.root/'cache/fastf1';cache.mkdir(parents=True,exist_ok=True);fastf1.Cache.enable_cache(str(cache))
        s=fastf1.get_session(year,round_,'R')
        laps=api.timing_data(s.api_path)[0];positions=api.position_data(s.api_path)
        s._calculate_t0_date(positions);offset=s.t0_date
        if offset is None:raise ValueError('Geen historische klokreferentie voor pitregistraties.')
        pit=[]
        for driver,part in laps.groupby('Driver'):
            exits=sorted(t for t in part['PitOutTime'] if not pd.isna(t))
            for r in part.to_dict('records'):
                entry=r['PitInTime']
                if pd.isna(entry):continue
                exit_=next((t for t in exits if t>entry),None)
                if exit_ is None:continue
                pit.append({'driver_number':int(driver),'lap_number':int(r['NumberOfLaps']),
                            'date':(offset+exit_).isoformat()+'Z','entry_date':(offset+entry).isoformat()+'Z',
                            'lane_duration':float((exit_-entry).total_seconds()),'pit_duration':None,'stop_duration':None,
                            'source':'FastF1','method':'archived PitInTime → next PitOutTime; stationary time unknown'})
        if not pit:raise ValueError('Historische bron levert geen gekoppelde pit-in/out-registraties.')
        sources=[];http=fastf1.Cache._requests_session_cached
        for host in [api.base_url,api.base_url_mirror]:
            for page in [api.pages['timing_data'],api.pages['position']]:
                url=host+s.api_path+page;request=http.prepare_request(requests.Request('GET',url,headers=api.headers))
                response=http.cache.get_response(http.cache.create_key(request))
                if response is None or response.status_code!=200:continue
                body=client.root/'cache/history-pit'/(hashlib.sha256(url.encode()).hexdigest()+'.body')
                body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(response.content)
                target=raw/'f1-timing'/body.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(body,target)
                sources.append({'url':url,'title':'Historische pitregistraties: '+page,'publisher':'Formula 1 timingarchief / FastF1',
                                'status':'opgehaald','fetched_at':response.created_at.isoformat(),
                                'sha256':hashlib.sha256(response.content).hexdigest(),'local_archive':str(body.relative_to(client.root)),
                                'access_method':'openbaar archief, verwerkt met FastF1 '+fastf1.__version__})
        saved={'pit':pit,'sources':sources};write_json(path,saved);write_json(raw/'fastf1/pit-fallback.json',saved)
        client.sources.extend(sources);data['pit']=pit
    data['pit_source']='FastF1'
    warnings.append('OpenF1-pitregistraties ontbreken; pitvensters zijn aangevuld met historische FastF1 PitInTime/PitOutTime. Stilstandduur is onbekend. De inhaalkandidaten blijven afkomstig uit OpenF1.')


def calendar(client, year):
    obj=client.fetch(f'https://api.jolpi.ca/ergast/f1/{year}.json',publisher='Jolpica',title='Jolpica: historische racekalender')
    races=obj['MRData']['RaceTable']['Races']; counts={}
    for r in races:
        key=r['Circuit']['circuitId'];counts[key]=counts.get(key,0)+1
    short={'red_bull_ring':'Spielberg','silverstone':'Silverstone','bahrain':'Sakhir','yas_marina':'Abu Dhabi','americas':'Austin','albert_park':'Melbourne','catalunya':'Barcelona','marina_bay':'Singapore','villeneuve':'Montreal','rodriguez':'Mexico City','interlagos':'Interlagos','hungaroring':'Hungaroring','spa':'Spa-Francorchamps','monza':'Monza','imola':'Imola','portimao':'Portimao','mugello':'Mugello','nurburgring':'Nürburgring','istanbul':'Istanbul','sochi':'Sochi','ricard':'Le Castellet','monaco':'Monte Carlo','jeddah':'Jeddah','zandvoort':'Zandvoort','baku':'Baku','losail':'Lusail','miami':'Miami'}
    return [{'year':year,'session_key':year*100+int(r['round']),'meeting_key':year*100+int(r['round']),
             'session_name':'Race','circuit_short_name':short.get(r['Circuit']['circuitId'],r['Circuit']['circuitName'])+((' — '+r['raceName'].replace(' Grand Prix','')) if counts[r['Circuit']['circuitId']]>1 else ''),
             'country_name':{'UK':'United Kingdom','USA':'United States','UAE':'United Arab Emirates'}.get(r['Circuit']['Location']['country'],r['Circuit']['Location']['country']),'location':r['Circuit']['Location']['locality'],
             'meeting_name':r['raceName'],'date_start':r['date']+'T'+r.get('time','13:00:00Z'),
             'round':int(r['round']),'jolpica_race':r} for r in races]


def inversions(rows):
    """Remember strict pair order across ties and asynchronous timing updates."""
    positions={};order={};result=[]
    for r in sorted(rows,key=lambda r:r['date']):
        d=r['driver_number'];positions[d]=r['position']
        for a,b in combinations(sorted(positions),2):
            if d not in (a,b) or positions[a]==positions[b]:continue
            sign=positions[a]<positions[b];previous=order.get((a,b));order[(a,b)]=sign
            if previous is None or previous==sign:continue
            ahead,behind=(a,b) if sign else (b,a)
            result.append({'date':r['date'],'overtaking_driver_number':ahead,'overtaken_driver_number':behind,
                           'position':positions[ahead],'method':'strict pair-order inversion in processed FastF1 timing stream'})
    return result


def acquire(client,year,gp,raw,source_config):
    import fastf1
    from fastf1 import api
    import pandas as pd
    session=select_race(calendar(client,year),gp);round_=session['round']
    store=client.root/'cache/history'/f'{year}-{round_:02}-v{SCHEMA}'
    stored=store/'bundle.json';archive=store/'raw'
    if stored.exists() and not client.refresh:
        saved=read_json(stored)
        if any(s['publisher']=='Formula 1 timingarchief / FastF1' for s in saved['sources']):
            client.sources.extend(saved['sources'])
            shutil.copytree(archive,raw,dirs_exist_ok=True)
            return saved['data'],saved['warnings']
    if client.offline:raise ValueError('Historische timing ontbreekt in cache: '+str(store))
    cache=client.root/'cache/fastf1';cache.mkdir(parents=True,exist_ok=True)
    fastf1.Cache.enable_cache(str(cache))
    s=fastf1.get_session(year,round_,'R');s.load(telemetry=False)
    pos=api.position_data(s.api_path)
    # Same documented clock-offset rule as FastF1, using only location telemetry.
    s._calculate_t0_date(pos)
    if s.t0_date is None:raise ValueError('Geen historische klokreferentie beschikbaar.')
    offset=s.t0_date
    iso=lambda value:None if pd.isna(value) else pd.Timestamp(value).isoformat()+'Z'
    date=lambda value:iso(offset+value) if not pd.isna(value) else None
    scalar=lambda value:None if pd.isna(value) else value.item() if hasattr(value,'item') else value
    seconds=lambda value:None if pd.isna(value) else float(value.total_seconds())
    number=lambda value:None if pd.isna(value) else int(value)
    data={'session':session,'meeting':{'meeting_name':session['meeting_name']},'round':round_,
          'jolpica_circuit':session['jolpica_race']['Circuit'],'timing_source':'FastF1',
          'timing_method':'Gereconstrueerde kandidaatwisselingen uit de verwerkte F1-timingfeed; geen officiële inhaalfeed.',
          'history_cache':str(store.relative_to(client.root)),'history_version':SCHEMA,
          'circuit':{},'evidence':[],'f1gures':[],'team_radio':[],'intervals':[]}
    result=client.fetch(f'https://api.jolpi.ca/ergast/f1/{year}/{round_}/results.json',publisher='Jolpica',title='Jolpica: startopstelling en uitslag')
    write_json(raw/'supplementary/jolpica-results.json',result)
    data['jolpica_results']=result['MRData']['RaceTable']['Races'][0]['Results']
    data['drivers']=[];data['session_result']=[];data['starting_grid']=[]
    for r in s.results.to_dict('records'):
        d=int(r['DriverNumber'])
        data['drivers'].append({'driver_number':d,'full_name':r['FullName'],'name_acronym':r['Abbreviation'],
                                'team_name':r['TeamName'],'team_colour':r['TeamColor']})
        data['session_result'].append({'driver_number':d,'position':number(r['Position']),
                                      'number_of_laps':number(r['Laps']),'status':str(r['Status']),
                                      'dnf':r['Status'] not in ('Finished','Lapped') and not str(r['Status']).startswith('+')})
        data['starting_grid'].append({'driver_number':d,'position':number(r['GridPosition']) or None})
    valid={d['driver_number'] for d in data['drivers']}
    data['laps']=[];data['pit']=[];data['stints']=[]
    for driver,frame in s.laps.groupby('DriverNumber'):
        d=int(driver)
        exits=sorted([t for t in frame['PitOutTime'] if not pd.isna(t)])
        for r in frame.to_dict('records'):
            # FastF1 can synthesize a retirement lap; never treat it as observed timing.
            if r.get('FastF1Generated') or pd.isna(r['LapStartTime']):continue
            lap=number(r['LapNumber'])
            data['laps'].append({'driver_number':d,'lap_number':lap,'date_start':date(r['LapStartTime']),
                                 'lap_duration':seconds(r['LapTime']),'is_pit_out_lap':not pd.isna(r['PitOutTime']),
                                 'duration_sector_1':seconds(r['Sector1Time']),'duration_sector_2':seconds(r['Sector2Time']),
                                 'duration_sector_3':seconds(r['Sector3Time']),'fastf1_is_accurate':bool(r['IsAccurate'])})
            entry=r['PitInTime']
            if not pd.isna(entry):
                exit_=next((t for t in exits if t>entry),None)
                if exit_ is not None:
                    data['pit'].append({'driver_number':d,'lap_number':lap,'date':date(exit_),
                                        'lane_duration':seconds(exit_-entry),'pit_duration':None,'stop_duration':None,
                                        'entry_date':date(entry),'method':'FastF1 PitInTime → next PitOutTime; stationary time unknown'})
        for stint,part in frame.groupby('Stint'):
            first=part.iloc[0]
            data['stints'].append({'driver_number':d,'stint_number':int(stint),'lap_start':int(part['LapNumber'].min()),
                                  'lap_end':int(part['LapNumber'].max()),'compound':scalar(first['Compound']),
                                  'tyre_age_at_start':max(0,int(first['TyreLife'])-1) if not pd.isna(first['TyreLife']) else None})
    stream=api.timing_data(s.api_path)[1]
    data['position']=[]
    for r in stream.sort_values('Time').to_dict('records'):
        d=int(r['Driver']);p=number(r['Position'])
        if d not in valid or not p or pd.isna(r['Time']):continue
        data['position'].append({'driver_number':d,'position':p,'date':date(r['Time'])})
        def gap(v):
            try:
                value=float(v);return value if math.isfinite(value) else None
            except (TypeError,ValueError):return None
        data['intervals'].append({'driver_number':d,'date':date(r['Time']),'interval':gap(r['IntervalToPositionAhead']),
                                  'gap_to_leader':gap(r['GapToLeader'])})
    data['overtakes']=inversions(data['position'])
    data['race_control']=[{'date':iso(r['Time']),'message':r['Message'],'flag':scalar(r['Flag']),
                           'scope':scalar(r['Scope']),'sector':number(r['Sector']),
                           'driver_number':number(r['RacingNumber'])} for r in s.race_control_messages.to_dict('records') if not pd.isna(r['Time'])]
    data['race_control'] += [{'date':date(r['Time']),'message':'SESSION STARTED'} for r in s.session_status.to_dict('records') if r['Status']=='Started']
    data['weather']=[{'date':date(r['Time']),'rainfall':bool(r['Rainfall']),'air_temperature':scalar(r['AirTemp']),
                      'track_temperature':scalar(r['TrackTemp'])} for r in s.weather_data.to_dict('records')]
    warnings=['Historische bron: FastF1 '+fastf1.__version__+'. Positiewisselingen zijn gereconstrueerde kandidaten uit verwerkte timing; geen officiële inhaaltelling. Timingbewerking en klokreferentie kunnen registraties verschuiven.',
              'Synthetische FastF1-ronden zijn uitgesloten. Stilstandtijd tijdens pitstops is onbekend; pitlane-tijd komt uit in- en uitregistraties.']
    from .circuit_info import acquire_wikipedia
    acquire_wikipedia(client,data,raw,source_config,warnings)
    # Retain actual downloaded archive bodies and their true URL and timestamp.
    import requests
    http=fastf1.Cache._requests_session_cached
    responses=[]
    for host in [api.base_url,api.base_url_mirror]:
        for page in api.pages.values():
            request=http.prepare_request(requests.Request('GET',host+s.api_path+page,headers=api.headers))
            response=http.cache.get_response(http.cache.create_key(request))
            if response is not None:responses.append(response)
    for response in responses:
        # URLs in the cache are percent-encoded (e.g. São Paulo); requests were already selected by exact key.
        if response.status_code!=200:continue
        payload=response.content;key=hashlib.sha256(response.url.encode()).hexdigest()
        target=raw/'f1-timing'/(key+'.body');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
        client.sources.append({'url':response.url,'publisher':'Formula 1 timingarchief / FastF1',
                               'title':'Historische timing: '+response.url.rsplit('/',1)[-1],
                               'fetched_at':response.created_at.isoformat(),'status':'opgehaald',
                               'sha256':hashlib.sha256(payload).hexdigest(),'access_method':'openbaar archief, verwerkt met FastF1 '+fastf1.__version__})
    locations={}
    for driver,frame in pos.items():
        if int(driver) not in valid:continue
        part=frame[(frame['Status']=='OnTrack') & ((frame['X']!=0)|(frame['Y']!=0))].sort_values('Date')
        locations[driver]=[{'date':iso(t),'x':int(x),'y':int(y),'driver_number':int(driver)} for t,x,y in part[['Date','X','Y']].itertuples(index=False,name=None)]
    store.mkdir(parents=True,exist_ok=True)
    with gzip.open(store/'locations.json.gz','wt',encoding='utf-8') as f:json.dump(locations,f,separators=(',',':'))
    write_json(raw/'fastf1/processed-input.json',data)
    shutil.copytree(raw,archive,dirs_exist_ok=True)
    write_json(stored,{'data':data,'warnings':warnings,'sources':list(client.sources),'saved_at':utcnow()})
    return data,warnings


class Locations:
    def __init__(self,client,data):
        from .analysis import ts
        with gzip.open(client.root/data['history_cache']/'locations.json.gz','rt',encoding='utf-8') as f:self.rows=json.load(f)
        self.times={d:[ts(r['date']) for r in rows] for d,rows in self.rows.items()}
    def api(self,endpoint,**params):
        from datetime import datetime,timezone
        if endpoint!='location':raise ValueError('Historische locatieadapter ondersteunt alleen location.')
        d=str(params['driver_number']);rows=self.rows.get(d,[]);times=self.times.get(d,[])
        def utc(value):
            parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
            return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp()
        return rows[bisect_right(times,utc(params['date>'])):bisect_left(times,utc(params['date<']))]
