"""Measured sector checkpoints for the presentation of pit-stop duels."""
from datetime import datetime

def detail_cycles(cycles, laps):
    indexed={(r['driver_number'],r['lap_number']):r for r in laps}
    result=[]
    for cycle in cycles:
        c=dict(cycle);points=[]
        for row in c['trace']:
            lap=row['lap'];a=indexed.get((c['early_driver'],lap));b=indexed.get((c['late_driver'],lap))
            if a and b and a.get('date_start') and b.get('date_start'):
                sectors=[[r.get('duration_sector_'+str(i)) for i in (1,2,3)] for r in (a,b)]
                if all(all(isinstance(v,(int,float)) and v>0 for v in ss) and r.get('lap_duration') and abs(sum(ss)-r['lap_duration'])<.5 for ss,r in zip(sectors,(a,b))):
                    starts=[datetime.fromisoformat(r['date_start'].replace('Z','+00:00')).timestamp() for r in (a,b)]
                    for sector in (1,2):
                        points.append({'lap':lap-1+sector/3,'race_lap':lap,'sector':sector,'gap':starts[0]+sum(sectors[0][:sector])-starts[1]-sum(sectors[1][:sector])})
            points.append({'lap':lap,'race_lap':lap,'sector':3,'gap':row['gap']})
        c['detail_trace']=points;result.append(c)
    return result
