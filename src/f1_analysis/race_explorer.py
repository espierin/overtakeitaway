"""Race explorer presentation data: measured sectors and race-control windows."""
from datetime import datetime
from statistics import median
from bisect import bisect_right

def stamp(value):
    return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()

def explorer_data(data):
    laps=data.get('laps',[]);flags=[];neutral=[];active={};sc=None;red_start=None;red_windows=[]
    for r in sorted(data.get('race_control',[]),key=lambda r:r.get('date','')):
        if not r.get('date'):continue
        t=stamp(r['date']);flag=r.get('flag');key=(r.get('scope'),r.get('sector'));msg=r.get('message','').upper()
        if flag=='RED':red_start=t
        if red_start is not None and (flag in ('GREEN','CLEAR') or 'SESSION RESUMED' in msg):red_windows.append((red_start,t));red_start=None
        if flag in ('YELLOW','DOUBLE YELLOW'):active.setdefault(key,t)
        if flag in ('CLEAR','GREEN'):
            keys=list(active) if r.get('scope')=='Track' else [key]
            for k in keys:
                if k in active:flags.append((active.pop(k),t,k[1]))
        if 'DEPLOYED' in msg and 'SAFETY CAR' in msg:sc=(t,'VSC' if 'VIRTUAL' in msg else 'SC')
        if sc and ('SAFETY CAR IN THIS LAP' in msg or 'VIRTUAL SAFETY CAR ENDING' in msg):neutral.append((sc[0],t,sc[1]));sc=None
    end=max((stamp(r['date_start'])+(r.get('lap_duration') or 0) for r in laps if r.get('date_start')),default=0)
    flags.extend((t,end,k[1]) for k,t in active.items())
    if red_start is not None:red_windows.append((red_start,end))
    if sc:neutral.append((sc[0],end,sc[1]))
    sectors=[];medians={}
    for r in laps:
        for i in (1,2,3):
            v=r.get('duration_sector_'+str(i))
            if isinstance(v,(int,float)) and v>0:medians.setdefault((r['lap_number'],i),[]).append(v)
    medians={k:median(v) for k,v in medians.items()}
    lap_flags=[];neutral_laps={};starts={};red_laps=set()
    for r in laps:
        if not r.get('date_start'):continue
        start=stamp(r['date_start']);finish=start+(r.get('lap_duration') or 0);n=r['lap_number'];d=r['driver_number'];starts[(d,n)]=start
        if any(a<finish and b>start for a,b in red_windows):red_laps.add(n)
        affected=[s for a,b,s in flags if a<finish and b>start]
        if affected:lap_flags.append({'driver':d,'lap':n,'track_sectors':affected})
        for a,b,kind in neutral:
            if a<finish and b>start:neutral_laps.setdefault(n,set()).add(kind)
        for i in (1,2,3):
            v=r.get('duration_sector_'+str(i))
            if isinstance(v,(int,float)) and v>0:sectors.append({'driver':d,'lap':n,'sector':i,'duration':v,'relative_speed':100*(medians[(n,i)]/v-1)})
    clocks={};sector_clocks={};finishes={};streams={};snapshots=[];frames=[]
    for r in laps:
        if not r.get('date_start') or not r.get('lap_duration'):continue
        finish=stamp(r['date_start'])+r['lap_duration'];n=r['lap_number'];d=r['driver_number']
        checkpoint=stamp(r['date_start'])
        for sector in (1,2,3):
            duration=r.get('duration_sector_'+str(sector))
            if not isinstance(duration,(int,float)) or duration<=0:break
            checkpoint+=duration;step=(n-1)*3+sector
            sector_clocks[step]=min(sector_clocks.get(step,checkpoint),checkpoint)
        clocks[n]=min(clocks.get(n,finish),finish);finishes[d]=max(finishes.get(d,0),finish)
    for r in data.get('position',[]):
        if r.get('date') and r.get('position'):streams.setdefault(r['driver_number'],[]).append((stamp(r['date']),r['position']))
    for d,stream in streams.items():
        stream.sort();times=[t for t,_ in stream]
        last_position=None;last_change=None;delta=0
        for step,t in sorted(sector_clocks.items()):
            i=bisect_right(times,t)-1
            if i<0:continue
            position=stream[i][1]
            if last_position is not None and position!=last_position:delta=last_position-position;last_change=step
            frames.append({'step':step,'driver':d,'position':position,'inactive':finishes.get(d,t)<t-1,'delta':delta if last_change is not None and step-last_change<3 else 0})
            last_position=position
        for n,t in sorted(clocks.items()):
            i=bisect_right(times,t)-1
            if i>=0:snapshots.append({'lap':n,'driver':d,'position':stream[i][1],'inactive':finishes.get(d,t)<t-1})
    first_laps=[r for r in laps if r.get('lap_number')==1 and r.get('date_start') and r.get('lap_duration')]
    first_positions=[]
    if first_laps:
        race_start=min(stamp(r['date_start']) for r in first_laps)
        race_finish=min(stamp(r['date_start'])+r['lap_duration'] for r in first_laps)
        for d,stream in streams.items():
            previous=None
            for t,position in stream:
                if t<race_start:previous=position;continue
                if t>race_finish:break
                if position!=previous:
                    own=next((r for r in first_laps if r['driver_number']==d),None)
                    sector=None
                    if own:
                        elapsed=t-stamp(own['date_start']);a=own.get('duration_sector_1');b=own.get('duration_sector_2')
                        if a and b:sector=1 if elapsed<=a else 2 if elapsed<=a+b else 3
                    first_positions.append({'driver':d,'fraction':max(0,min(1,(t-race_start)/max(1,race_finish-race_start))),'position':position,'sector':sector,'time':t})
                previous=position
    return {'start_positions':first_positions,'red':sorted(red_laps),'sector_standings':frames,'standings':snapshots,'sectors':sectors,'yellow':lap_flags,'neutral':[{'lap':n,'kind':'/'.join(sorted(k))} for n,k in sorted(neutral_laps.items())], 'pit':[{'driver':r['driver_number'],'lap':r['lap_number']} for r in data.get('pit',[])], 'resolution':'sector','yellow_resolution':'lap-time-window'}
