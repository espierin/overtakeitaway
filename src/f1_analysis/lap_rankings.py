"""One measured whole-lap rank per driver and numbered race lap.

The field is ranked before any own-driver context filter. Retain every measured
lap, its measured field size and source context; never synthesize sector times.
"""
from bisect import bisect_right
from collections import defaultdict
import math

from .driver_qualities import traffic_evidence, stamp

VERSION = 'lap-field-ranks-v1'
COMPOUNDS = ('UNKNOWN','HYPERSOFT','ULTRASOFT','SUPERSOFT','SOFT','MEDIUM','HARD','SUPERHARD','INTERMEDIATE','WET')
FIRST, PIT, FLAG, QUALITY, WET, UNKNOWN_TYRE, NOT_FREE, TRAFFIC = (1,2,4,8,16,32,64,128)
POINT_COLUMNS = ('lap','rank','field_size','compound','context_flags')


def valid(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def unique_times(rows, driver_key, lap_key):
    observed={};conflicting=set()
    for row in rows:
        driver=row.get(driver_key);lap=row.get(lap_key);duration=row.get('duration')
        if not valid(lap) or lap<1 or int(lap)!=lap or not valid(duration) or duration<=0:
            continue
        key=(driver,int(lap))
        # Timing is measured in milliseconds. Equal measurements share a rank.
        duration=round(duration,3)
        if key in observed and observed[key]!=duration:conflicting.add(key)
        observed[key]=duration
    return {k:v for k,v in observed.items() if k not in conflicting}


def ranked(index):
    groups=defaultdict(list)
    for key,duration in index.items():groups[key[1:]].append((key[0],duration))
    out={}
    for group,rows in groups.items():
        ordered=sorted(rows,key=lambda r:r[1]);rank_by_time={}
        for i,(_,duration) in enumerate(ordered,1):rank_by_time.setdefault(duration,i)
        for driver,duration in rows:out[(driver,*group)]=(rank_by_time[duration],len(rows))
    return out


def analyse(payload, raw=None, retained_context=None):
    raw=raw or {};explorer=payload.get('explorer',{});drivers={d['driver_number'] for d in payload.get('drivers',[])}
    lap_rows={(r['driver'],r['lap']):r for r in payload.get('all_laps',[])}
    laps=unique_times(payload.get('all_laps',[]),'driver','lap')
    laps={key:value for key,value in laps.items() if key[0] in drivers}
    lap_ranks=ranked(laps)
    free=traffic_evidence(payload,raw)
    raw_laps={(r.get('driver_number'),r.get('lap_number')):r for r in raw.get('laps',[])}
    pits={(r.get('driver'),r.get('lap')) for r in explorer.get('pit',[])}
    flagged={r['lap'] for r in explorer.get('neutral',[])}|set(explorer.get('red',[]))
    flagged.update(r['lap'] for r in explorer.get('yellow',[]))
    weather=sorted((stamp(r.get('date')),bool(r.get('rainfall'))) for r in raw.get('weather',[]) if stamp(r.get('date')) is not None)
    weather_times=[t for t,_ in weather]
    def context(driver,lap):
        if retained_context and (driver,lap) in retained_context:return retained_context[driver,lap]
        row=lap_rows.get((driver,lap),{});source=raw_laps.get((driver,lap),{});reasons=row.get('reasons') or []
        compound=str((row.get('tyre') or {}).get('compound') or 'UNKNOWN').upper()
        flags=FIRST if lap==1 else 0
        if (driver,lap) in pits or (driver,lap-1) in pits or source.get('is_pit_out_lap') or source.get('pit_in') or source.get('pit_out'):
            flags|=PIT
        status=str(source.get('track_status') or '')
        if lap in flagged or any(code in status for code in ('2','4','5','6','7')):flags|=FLAG
        if not row or source.get('fastf1_is_accurate') is False or source.get('accurate') is False or source.get('deleted'):
            flags|=QUALITY
        for reason in reasons:
            text=str(reason).lower()
            if any(word in text for word in ('verkeer','traffic')):flags|=TRAFFIC
            elif any(word in text for word in ('vlag','neutral','flag','safety car')):flags|=FLAG
            elif any(word in text for word in ('pit','uitronde')):flags|=PIT
            elif any(word in text for word in ('startprocedure',)):flags|=FIRST
            else:flags|=QUALITY
        if compound in ('WET','INTERMEDIATE'):flags|=WET
        start=stamp(source.get('date_start'));duration=source.get('lap_duration')
        if start is not None and valid(duration) and weather:
            lo=bisect_right(weather_times,start)-1;hi=bisect_right(weather_times,start+duration)
            if any(rain for _,rain in weather[max(0,lo):hi]):flags|=WET
        if compound not in COMPOUNDS or compound=='UNKNOWN':flags|=UNKNOWN_TYRE
        if not free.get((driver,lap),False):flags|=NOT_FREE
        return COMPOUNDS.index(compound) if compound in COMPOUNDS else 0,flags
    output={n:[] for n in drivers}
    for (driver,lap),(rank,size) in sorted(lap_ranks.items()):
        compound,flags=context(driver,lap)
        output[driver].append([lap,rank,size,compound,flags])
    return output
