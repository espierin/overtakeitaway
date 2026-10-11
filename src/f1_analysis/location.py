from datetime import datetime, timezone
import numpy as np
from .analysis import ts
from .io import write_json


def iso(time):return datetime.fromtimestamp(time,timezone.utc).replace(tzinfo=None).isoformat(timespec='milliseconds')


def fetch_locations(client,ctx,events,raw,warnings):
    if ctx.data.get('timing_source')=='FastF1':
        from .history import Locations
        client=Locations(client,ctx.data)
    points={};track=[]
    winner=next((r['driver_number'] for r in ctx.data['session_result'] if r['position']==1),None)
    laps=[r for r in ctx.data['laps'] if r['driver_number']==winner and r['lap_number']>=2 and r.get('date_start') and r.get('lap_duration') and not r.get('is_pit_out_lap')]
    laps.sort(key=lambda r:(r['lap_number']!=5,r['lap_duration']))
    for lap in laps[:5]:
        try:
            rows=client.api('location',session_key=ctx.data['session']['session_key'],driver_number=winner,**{'date>':iso(ts(lap['date_start'])),'date<':iso(ts(lap['date_start'])+lap['lap_duration'])})
            write_json(raw/('fastf1' if ctx.data.get('timing_source')=='FastF1' else 'openf1')/'location-track.json',rows)
            track=build_track(rows)
            if track:
                ctx.data['track_reference_lap']={'driver_number':winner,'lap_number':lap['lap_number']}
                break
        except ValueError as exc:warnings.append(str(exc))
    if not track:
        warnings.append('Geen betrouwbare circuitgeometrie uit een gemeten volledige ronde. Kaarten tonen ontbrekende dekking.');return [],{}
    ctx.data['validated_corners']=validated_corners(track,ctx.data.get('circuit',{}),ctx.data['session']['year'])
    reference=official_reference(ctx.data,track)
    from .circuit_info import annotate_reference
    ctx.data['circuit_reference']=annotate_reference(ctx.data,track,reference,warnings)
    if not reference:
        warnings.append('Geen gecontroleerde officiële circuitkaart voor dit racejaar; baanvorm en oriëntatie zijn uitsluitend gemeten benaderingen.')
    # A focused request per driver and time window. Cache makes offline analysis identical.
    candidates=[e for e in events if e.get('date') and (e.get('counts',{}).get('on_track') or e['type']=='startactie')]
    bulk={}
    if ctx.config.get('locatie_ophalen')=='per_coureur':
        from collections import defaultdict
        from bisect import bisect_left,bisect_right
        windows=defaultdict(list)
        for e in candidates:
            for d in [e['overtaker'],e['overtaken']]:windows[d].append(ts(e['date']))
        for d,times in sorted(windows.items()):
            try:
                width=ctx.config['locatie_venster_seconden']
                rows=client.api('location',session_key=ctx.data['session']['session_key'],driver_number=d,**{'date>':iso(min(times)-width),'date<':iso(max(times)+width)})
                rows=sorted(rows,key=lambda row:ts(row['date']))
                bulk[d]=([ts(row['date']) for row in rows],rows)
                write_json(raw/('fastf1' if ctx.data.get('timing_source')=='FastF1' else 'openf1')/f'location-driver-{d}.json',rows)
            except ValueError as exc:warnings.append(str(exc));bulk[d]=([],[])
    for e in candidates:
        time=ts(e['date']);width=ctx.config['locatie_venster_seconden'];pair=[]
        for d in [e['overtaker'],e['overtaken']]:
            try:
                if d in bulk:
                    times,all_rows=bulk[d];rows=all_rows[bisect_right(times,time-width):bisect_left(times,time+width)]
                else:
                    rows=client.api('location',session_key=ctx.data['session']['session_key'],driver_number=d,**{'date>':iso(time-width),'date<':iso(time+width)})
                key=f'{e["event_id"]}-{d}';points[key]=rows;write_json(raw/('fastf1' if ctx.data.get('timing_source')=='FastF1' else 'openf1')/('location-'+key+'.json'),rows);pair.append(rows)
            except ValueError as exc:warnings.append(str(exc));pair.append([])
        location=estimate_zone(track,pair,time,ctx.config)
        if location:
            if ctx.data.get('timing_source')=='FastF1':location['coordinate_system']='F1-archiefcoördinaten via FastF1; booglengtezone, zonder geografische oriëntatie'
            e['location']=location;e['location_confidence']='geschatte zone'
            e['location_note']='Beide coureurs in tijdvenster; registratievertraging niet gekalibreerd.'
        if e.get('confirmed_turn'):
            corner=next((c for c in ctx.data.get('validated_corners',[]) if c['number']==e['confirmed_turn']),None)
            if corner:
                e['estimated_location']=e.get('location')
                e['location']={**corner,'spread_progress':.01,'method':'Bronbevestigde bochtzone, gekoppeld aan gevalideerde circuitgeometrie; geen exact manoeuvrepunt'}
                e['location_confidence']='bevestigde zone'
            e['confirmed_location_label']='Bocht '+str(e['confirmed_turn'])+' bevestigd door aanvullende bron; kaart toont een bochtzone, geen exact manoeuvrepunt.'
    return track,points


def build_track(rows):
    ordered=sorted(rows,key=lambda r:ts(r['date']))
    points=np.array([[r['x'],r['y']] for r in ordered if r.get('x') is not None and r.get('y') is not None],dtype=float)
    if len(points)<50:return []
    # Remove repeated samples, preserve sequential track progression rather than nearby spatial aggregation.
    keep=np.r_[True,np.linalg.norm(np.diff(points,axis=0),axis=1)>1]
    points=points[keep]
    steps=np.linalg.norm(np.diff(points,axis=0),axis=1)
    if not len(steps) or np.max(steps)>15*np.median(steps):return []
    if np.linalg.norm(points[0]-points[-1])>0.08*np.sum(steps):return []
    points=np.vstack([points,points[0]])
    distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    target=np.linspace(0,distance[-1],401)
    x=np.interp(target,distance,points[:,0]);y=np.interp(target,distance,points[:,1])
    return [{'x':float(a),'y':float(b),'progress':i/400} for i,(a,b) in enumerate(zip(x,y))]


def estimate_zone(track,pair,time,config):
    if not track or len(pair)!=2 or not all(pair):return None
    xy=np.array([[p['x'],p['y']] for p in track[:-1]])
    indices=[]
    for rows in pair:
        usable=[r for r in rows if r.get('x') is not None and r.get('y') is not None]
        if len(usable)<3:return None
        # Require measurements both before and after the registration.
        if not any(ts(r['date'])<time for r in usable) or not any(ts(r['date'])>time for r in usable):return None
        for r in usable:
            distances=np.linalg.norm(xy-[r['x'],r['y']],axis=1);i=int(np.argmin(distances))
            if distances[i]>config['locatie_max_afstand']:return None
            near=np.flatnonzero(distances<=distances[i]+50)
            separation=np.minimum(abs(near-i),len(xy)-abs(near-i))
            if np.any(separation>12):return None # nearby distinct track sections remain ambiguous
            indices.append(i)
    # unwrap on the circle across start/finish; wide/noncontiguous zones stay unknown.
    angles=np.array(indices)/len(xy)*2*np.pi
    center=np.arctan2(np.mean(np.sin(angles)),np.mean(np.cos(angles)))
    unwrapped=(angles-center+np.pi)%(2*np.pi)-np.pi
    width=float(np.ptp(unwrapped)/(2*np.pi))
    if width>config['locatie_max_spreiding_segmenten']/100:return None
    progress=float((center/(2*np.pi))%1)
    index=int(round(progress*len(xy)))%len(xy)
    return {'progress':progress,'segment_index':index,'x':float(xy[index,0]),'y':float(xy[index,1]),'spread_progress':width,
            'method':'Booglengtepositie uit beide tijdvensters; geen exact inhaalpunt','coordinate_system':'OpenF1 arbitraire coördinaten; geen geografische oriëntatie of meters'}


def map_counts(events,config):
    selected=[e for e in events if e['counts']['analytical']]
    located=[e for e in selected if e.get('location')]
    bins=[0]*config['heatmap_segmenten']
    for e in located:bins[min(len(bins)-1,int(e['location']['progress']*len(bins)))]+=1
    assert sum(bins)==len(located)
    return {'included':len(selected),'located':len(located),'unknown':len(selected)-len(located),'confirmed':sum(e['location_confidence']=='bevestigde zone' for e in located),'estimated':sum(e['location_confidence']=='geschatte zone' for e in located),'bins':bins,'density':'aantal per booglengtesegment; geen ruimtelijke smoothing'}


def validated_corners(track,circuit,year):
    if not track or circuit.get('year')!=year or not circuit.get('corners'):return []
    xy=np.array([[p['x'],p['y']] for p in track[:-1]])
    output=[]
    for corner in circuit['corners']:
        position=corner.get('trackPosition',{});x=position.get('x');y=position.get('y')
        if x is None or y is None:return []
        distances=np.linalg.norm(xy-[x,y],axis=1);index=int(np.argmin(distances))
        if distances[index]>450:return []
        output.append({'number':corner['number'],'progress':index/len(xy),'segment_index':index,'x':float(xy[index,0]),'y':float(xy[index,1])})
    return output


def official_reference(data,track):
    """Separate year/layout verification from approximate coordinates and event evidence."""
    year=data['session']['year'];circuit=data.get('circuit',{})
    for source in data.get('evidence',[]):
        layout=source.get('verified_facts',{}).get('circuit_layout')
        if not (layout and source.get('available') and source.get('year')==year):continue
        if circuit.get('year') not in [year,layout.get('compatible_basis_year')]:continue
        if len(circuit.get('corners',[]))!=layout['corners']:continue
        # Compatibility is explicitly curated after inspection of the official map.
        # The original basis year is retained; this does not confirm manoeuvre coordinates.
        anchors=validated_corners(track,{**circuit,'year':year},year)
        if len(anchors)!=layout['corners']:continue
        return {**layout,'source_url':source['url'],'source_title':source['title'],
                'year':year,'coordinate_basis_year':circuit['year'],'reference_corners':anchors,
                'coordinate_status':'Benaderde bochtankers; geen officiële coördinaten'}
    return {}


def display_point(point,reference):
    angle=np.deg2rad(reference.get('display_rotation_degrees',0))
    return {**point,'x':float(point['x']*np.cos(angle)-point['y']*np.sin(angle)),
            'y':float(point['x']*np.sin(angle)+point['y']*np.cos(angle))}
