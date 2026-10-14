"""Conservative, descriptive driver traits; never impute missing tyre/traffic data.

Each exported observation belongs to one race and a verified stint/set. Aggregation
in the client weights races equally. Age is the feed's age BEFORE the current lap.
"""
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime
from statistics import median
import math

KINDS=('free','metronome','tyres','warmup','pitwindow','start')
DRY={'SOFT','MEDIUM','HARD'}


def valid(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)


def stamp(value):
    if not isinstance(value,str):return None
    try:return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    except (ValueError,TypeError):return None


def line(points):
    """Theil–Sen line; requires at least two distinct x values."""
    slopes=[(v-u)/(b-a) for i,(a,u) in enumerate(points) for b,v in points[i+1:] if b!=a]
    if not slopes:return None
    slope=median(slopes)
    return slope,median(y-slope*x for x,y in points)


def traffic_evidence(payload, raw):
    """Return explicit free-air evidence, not absence of a traffic exclusion.

    Require measurements at 25/50/75% of the lap, each <=10s old. A leader
    requires a contemporaneous position=1; a zero interval alone is not enough.
    """
    def timelines(rows):
        groups=defaultdict(list)
        for r in rows:
            t=stamp(r.get('date'))
            if t is not None:groups[r.get('driver_number')].append((t,r))
        return {n:(tuple(x[0] for x in sorted(rs,key=lambda x:x[0])),tuple(x[1] for x in sorted(rs,key=lambda x:x[0]))) for n,rs in groups.items()}
    intervals=timelines(raw.get('intervals',[]))
    positions=timelines(raw.get('position',[]))
    def at(index,n,t,max_age=10):
        times,rows=index.get(n,((),()));i=bisect_right(times,t)-1
        return rows[i] if i>=0 and t-times[i]<=max_age else None
    evidence={}
    for r in raw.get('laps',[]):
        n,l=r.get('driver_number'),r.get('lap_number');start=stamp(r.get('date_start'));duration=r.get('lap_duration')
        if start is None or not valid(duration) or duration<=0:continue
        samples=[]
        for fraction in (.25,.5,.75):
            t=start+duration*fraction;interval=at(intervals,n,t);position=at(positions,n,t,max_age=math.inf)
            gap=interval.get('interval') if interval else None
            leader=bool(position and position.get('position')==1)
            samples.append(bool(leader or (valid(gap) and gap>=3)))
        evidence[n,l]=all(samples)
    return evidence


def analyse(payload,raw=None):
    raw=raw or {};drivers=payload.get('drivers',[])
    output={d['driver_number']:{k:[] for k in KINDS} for d in drivers}
    coverage={d['driver_number']:{'timed_laps':0,'clean_laps':0,'free_laps':0,'paired_laps':0} for d in drivers}
    laps={(r.get('driver'),r.get('lap')):r for r in payload.get('all_laps',[]) if valid(r.get('duration')) and r['duration']>0 and valid(r.get('lap'))}
    stops=defaultdict(set)
    for p in payload.get('explorer',{}).get('pit',[]):
        if valid(p.get('lap')) and p['lap']>=1 and int(p['lap'])==p['lap']:stops[p['driver']].add(int(p['lap']))
    neutral={r['lap'] for r in payload.get('explorer',{}).get('neutral',[])}|set(payload.get('explorer',{}).get('red',[]))
    neutral.update(r['lap'] for r in laps.values() if any(any(w in str(reason).lower() for w in ('neutral','vlag','yellow','safety car','red flag')) for reason in r.get('reasons',[])))
    free=traffic_evidence(payload,raw)
    stints=defaultdict(list)
    for s in payload.get('tyres',{}).get('stints',[]):
        if s.get('compound') in DRY and valid(s.get('lap_start')) and valid(s.get('lap_end')) and valid(s.get('tyre_age_at_start')) and s['tyre_age_at_start']>=0:
            stints[s['driver_number']].append(s)
    # Raw stints are a fallback only when the retained dashboard has no set registry.
    for n in output:
        if not stints[n]:
            stints[n]=[s for s in raw.get('stints',[]) if s.get('driver_number')==n and s.get('compound') in DRY and all(valid(s.get(k)) for k in ('lap_start','lap_end','tyre_age_at_start')) and s['tyre_age_at_start']>=0]
    set_for={};clean={}
    for (n,l),r in laps.items():
        if n not in output:continue
        coverage[n]['timed_laps']+=1;tyre=r.get('tyre') or {};age=tyre.get('age');compound=tyre.get('compound')
        if l<=1 or l in neutral or l in stops[n] or l-1 in stops[n] or r.get('reasons') or compound not in DRY or not valid(age) or age<0:continue
        candidates=[(i,s) for i,s in enumerate(stints[n]) if s['lap_start']<=l<=s['lap_end'] and s['compound']==compound and abs(s['tyre_age_at_start']+l-s['lap_start']-age)<.01]
        if len(candidates)!=1:continue
        set_for[n,l]=candidates[0][0];clean[n,l]=r;coverage[n]['clean_laps']+=1
        if free.get((n,l)):coverage[n]['free_laps']+=1
    def usable(n,l):return (n,l) in clean and free.get((n,l),False)
    teams=defaultdict(list)
    for d in drivers:
        if d.get('team'):teams[d['team']].append(d)
    partners={}
    for team,ds in teams.items():
        if len(ds)!=2:continue
        a,b=ds;na,nb=a['driver_number'],b['driver_number'];partners[na]=b;partners[nb]=a
        groups=defaultdict(list)
        for n,l in sorted(clean):
            if n!=na or not usable(na,l) or not usable(nb,l):continue
            ra,rb=clean[na,l],clean[nb,l];ta,tb=ra['tyre'],rb['tyre']
            if ta['compound']!=tb['compound'] or abs(ta['age']-tb['age'])>2 or min(ta['age'],tb['age'])<3:continue
            groups[set_for[na,l],set_for[nb,l],ta['compound']].append((l,ra,rb))
        for (_,_,compound),samples in groups.items():
            if len(samples)<6:continue
            delta=[(a['duration']-b['duration'])*200/(a['duration']+b['duration']) for _,a,b in samples]
            ages=[(a['tyre']['age']+b['tyre']['age'])/2 for _,a,b in samples]
            for n,other,sign in ((na,b,1),(nb,a,-1)):
                output[n]['free'].append({'value':round(sign*median(delta),5),'compound':compound,'n':len(samples),'teammate':other['name']})
                coverage[n]['paired_laps']+=len(samples)
            if len(samples)<8 or max(ages)-min(ages)<10:continue
            trend=line(list(zip(ages,delta)))
            if not trend:continue
            for n,other,sign in ((na,b,1),(nb,a,-1)):
                output[n]['tyres'].append({'value':round(-sign*10*trend[0],5),'compound':compound,'n':len(samples),'teammate':other['name'],'age_min':min(ages),'age_max':max(ages),'trace':[[age,round(sign*v,4)] for age,v in zip(ages,delta)],'slope':round(sign*trend[0],6),'intercept':round(sign*trend[1],5)})
    for n in output:
        mate=partners.get(n)
        for i,s in enumerate(stints[n]):
            samples=[r for (d,l),r in clean.items() if d==n and set_for[d,l]==i and usable(d,l)]
            steady=[r for r in samples if r['tyre']['age']>=3]
            if len(steady)>=8 and max(r['lap'] for r in steady)-min(r['lap'] for r in steady)>=6:
                trend=line([(r['lap'],r['duration']) for r in steady])
                residual=[r['duration']-(trend[0]*r['lap']+trend[1]) for r in steady];center=median(residual);base=median(r['duration'] for r in steady)
                output[n]['metronome'].append({'value':round(100*1.4826*median(abs(v-center) for v in residual)/base,5),'compound':s['compound'],'n':len(steady),'pace_seconds':round(base,3),'trace':[[r['tyre']['age'],round(100*v/base,4)] for r,v in zip(steady,residual)]})
            # A known new set, following an observed stop, excluding the outlap.
            if s['tyre_age_at_start']==0 and s['lap_start']>1 and s['lap_start']-1 in stops[n]:
                early=[r for r in samples if 1<=r['tyre']['age']<=3]
                stable=[r for r in samples if 4<=r['tyre']['age']<=10]
                if len(early)>=2 and len(stable)>=4 and min(r['tyre']['age'] for r in stable)==4 and max(r['tyre']['age'] for r in stable)-min(r['tyre']['age'] for r in stable)>=4:
                    trend=line([(r['tyre']['age'],r['duration']) for r in stable]);base=median(r['duration'] for r in stable)
                    excess=[100*(r['duration']-trend[0]*r['tyre']['age']-trend[1])/base for r in early]
                    output[n]['warmup'].append({'value':round(median(excess),5),'compound':s['compound'],'n':len(early)+len(stable),'stop':s['lap_start']-1,'trace':[[r['tyre']['age'],round(100*(r['duration']-trend[0]*r['tyre']['age']-trend[1])/base,4)] for r in sorted(early+stable,key=lambda r:r['lap'])]})
        for pit in sorted(stops[n]):
            window=[pit-2,pit-1,pit+2,pit+3]
            if not all(usable(n,l) for l in window) or any(l in neutral for l in range(pit-2,pit+4)):continue
            before,after=set_for[n,pit-1],set_for[n,pit+2]
            if before==after:continue
            residuals=[];trace=[]
            for subset,indices in ((before,window[:2]),(after,window[2:])):
                training=[r for (d,l),r in clean.items() if d==n and set_for[d,l]==subset and usable(d,l) and all(not(p-2<=l<=p+3) for p in stops[n])]
                if len(training)<6 or max(r['lap'] for r in training)-min(r['lap'] for r in training)<5:break
                # Only a small extension outside the observed reference interval.
                if any(l<min(r['lap'] for r in training)-4 or l>max(r['lap'] for r in training)+4 for l in indices):break
                trend=line([(r['lap'],r['duration']) for r in training]);base=median(r['duration'] for r in training)
                for l in indices:
                    value=100*(clean[n,l]['duration']-trend[0]*l-trend[1])/base;residuals.append(value);trace.append([l-pit,round(-value,4)])
            if len(residuals)==4:
                output[n]['pitwindow'].append({'value':round(-median(residuals),5),'compound':stints[n][after]['compound'],'before_compound':stints[n][before]['compound'],'n':4,'stop':pit,'trace':trace})
        d=next(d for d in drivers if d['driver_number']==n);grid=d.get('grid');lap1=d.get('lap1_position')
        result=d.get('result') or {}
        if (valid(grid) and grid>=1 and int(grid)==grid and valid(lap1) and lap1>=1 and int(lap1)==lap1
                and not d.get('pitlane_start') and not result.get('dns') and result.get('number_of_laps')!=0):
            raw_gain=int(grid-lap1)
            output[n]['start'].append({'value':raw_gain,'raw_gain':raw_gain,'compound':'ALL','n':1,'grid':int(grid),'lap1':int(lap1)})
    # Second pass: both drivers' own observations must already exist.
    for n,mate in partners.items():
        for kind in ('metronome','warmup','pitwindow'):
            for obs in output[n][kind]:
                reference=[r['value'] for r in output[mate['driver_number']][kind] if r['compound']==obs['compound']]
                if reference:obs.update(reference=round(median(reference),5),teammate=mate['name'])
    return output,coverage
