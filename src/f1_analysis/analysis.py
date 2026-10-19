from __future__ import annotations
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime
import hashlib, math, re, statistics
import numpy as np


def ts(value):
    return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp() if value else None


def number(value):
    return float(value) if isinstance(value,(float,int)) and math.isfinite(value) else None


class Timeline:
    def __init__(self, rows, date_field='date'):
        self.rows=sorted([r for r in rows if r.get(date_field)],key=lambda r:ts(r[date_field]))
        self.times=[ts(r[date_field]) for r in self.rows]
    def at(self, time):
        i=bisect_right(self.times,time)-1
        return self.rows[i] if i>=0 else None
    def window(self, time, width):
        a=bisect_right(self.times,time-width);b=bisect_right(self.times,time+width)
        return self.rows[a:b]


class Context:
    def __init__(self,data,config):
        self.data=data;self.config=config
        self.drivers={d['driver_number']:d for d in data['drivers']}
        self.laps={d:Timeline([r for r in data['laps'] if r['driver_number']==d],'date_start') for d in self.drivers}
        self.positions={d:Timeline([r for r in data['position'] if r['driver_number']==d]) for d in self.drivers}
        self.intervals={d:Timeline([r for r in data['intervals'] if r['driver_number']==d]) for d in self.drivers}
        self.weather=Timeline(data['weather'])
        lap1=[ts(r['date_start']) for r in data['laps'] if r['lap_number']==1 and r.get('date_start')]
        started=[ts(r['date']) for r in data['race_control'] if r.get('message')=='SESSION STARTED']
        candidates=[t for t in started if lap1 and abs(t-min(lap1))<20]
        if not lap1 and data['session'].get('date_start'):
            scheduled=ts(data['session']['date_start'])
            candidates=[t for t in started if scheduled-60<=t<=scheduled+1200]
        self.start=min(candidates) if candidates else (min(lap1) if lap1 else None)
        self.start_confirmed=bool(candidates)
        self.observed_lap_count=max([r.get('lap_number') or 0 for r in data['laps']]+[0])
        winner_laps=next((r.get('number_of_laps') for r in data['session_result'] if r.get('position')==1),None)
        self.lap_count=winner_laps if winner_laps else max([r.get('number_of_laps') or 0 for r in data['session_result']]+[self.observed_lap_count])
        self.end=max([ts(r['date_start'])+(r.get('lap_duration') or 0) for r in data['laps'] if r.get('date_start')]+[self.start or 0])
        self.flag_windows=[];self.neutral_windows=[]
        active={};neutral=None;red=None
        for r in sorted(data['race_control'],key=lambda r:ts(r['date'])):
            t=ts(r['date']);m=r.get('message','').upper();f=r.get('flag')
            if not self.start or t<self.start:continue
            scope=r.get('scope');key=(scope,r.get('sector'))
            if f in ['YELLOW','DOUBLE YELLOW','RED']:active[key]=t
            elif f in ['CLEAR','GREEN'] and key in active:self.flag_windows.append((active.pop(key),t))
            if f=='RED' and red is None:red=t
            if red is not None and (f=='GREEN' or m=='SESSION STARTED'):
                self.neutral_windows.append((red,t+100));red=None
            if neutral is None and 'DEPLOYED' in m and ('SAFETY CAR' in m or 'VIRTUAL SAFETY CAR' in m):neutral=t
            if neutral is not None and ('SAFETY CAR IN THIS LAP' in m or 'VSC ENDING' in m or 'VIRTUAL SAFETY CAR ENDING' in m or 'VIRTUAL SAFETY CAR ENDED' in m):
                # Conservatively add one race lap: restart transition is not clean tyre pace.
                self.neutral_windows.append((neutral,t+100));neutral=None
        self.flag_windows.extend((v,self.end) for v in active.values())
        if neutral is not None:self.neutral_windows.append((neutral,self.end))
        if red is not None:self.neutral_windows.append((red,self.end))
    def lap(self,driver,time):
        row=self.laps.get(driver,Timeline([])).at(time)
        if row is None:return None
        duration=row.get('lap_duration')
        if duration and time>ts(row['date_start'])+duration+3:return None
        return row
    def position(self,driver,time):
        row=self.positions.get(driver,Timeline([])).at(time)
        return row['position'] if row else None
    def stint(self,driver,lap):
        if lap is None:return None
        for s in self.data['stints']:
            if s['driver_number']==driver and (s.get('lap_start') or 999)<=lap<=(s.get('lap_end') or -1):return s
        return None
    def tyre(self,driver,lap):
        s=self.stint(driver,lap)
        if not s:return {'compound':None,'age':None}
        age=s.get('tyre_age_at_start')
        return {'compound':s.get('compound'),'age':age+lap-s['lap_start'] if age is not None else None}
    def pit(self,driver,time):
        margin=self.config['pit_marge_seconden']
        return [p for p in self.data['pit'] if p['driver_number']==driver and ts(p['date'])-(p.get('lane_duration') or p.get('pit_duration') or 0)-margin<=time<=ts(p['date'])+margin]
    def neutral(self,time):return any(a<=time<=b for a,b in self.neutral_windows)

    def retirement_context(self, driver, time):
        """Flag terminal, unsupported exchanges without claiming a crash time.

        A DNF alone never invalidates earlier racing passes. Only exchanges after
        the driver's last measured progress are ambiguous. Keep original records
        and the timing boundary; the retirement's exact time is not inferred.
        """
        result=next((r for r in self.data['session_result'] if r.get('driver_number')==driver),None)
        if not result or result.get('dnf') is not True or result.get('dns') is True:return None
        completed=number(result.get('number_of_laps'))
        if completed is None or completed<0 or int(completed)!=completed:return None
        rows=self.laps.get(driver,Timeline([])).rows
        # Conflicting completed-lap evidence cannot establish a terminal boundary.
        if any((r.get('lap_number') or 0)>completed and number(r.get('lap_duration')) and r['lap_duration']>0 for r in rows):return None
        progress=[]
        for row in rows:
            lap=row.get('lap_number')
            if not lap or lap>completed+1:continue
            start=ts(row['date_start']);duration=number(row.get('lap_duration'))
            if duration is not None and duration>0 and lap<=completed:
                progress.append((start+duration,lap,'lap_end'))
            elif lap==completed+1:
                seconds=0
                for sector in (1,2,3):
                    duration=number(row.get(f'duration_sector_{sector}'))
                    if duration is None or duration<=0:break
                    seconds+=duration;progress.append((start+seconds,lap,f'sector_{sector}'))
        if not progress:return None
        last,lap,basis=max(progress)
        if time<=last:return None
        return {'driver_number':driver,'completed_laps':int(completed),
                'last_progress_time':last,'last_progress_lap':lap,
                'last_progress_basis':basis,'exact_retirement_time_known':False,
                'method':'confirmed-dnf-last-measured-progress-v1'}

    def incident_context(self, driver, time):
        """Corroborate ambiguity around an incident, including drivers who resume.

        Neither a local yellow alone nor a slow lap alone excludes a pass. Require
        a named-driver collision report, concurrent yellow and a substantially
        delayed measured sector of that same driver at the event time.
        """
        if not any(a-1<=time<=b+1 for a,b in self.flag_windows):return None
        reports=[]
        for row in self.data['race_control']:
            message=row.get('message','').upper();reported=ts(row.get('date'))
            if reported is None or not -30<=reported-time<=300:continue
            if 'INCIDENT' not in message or 'COLLISION' not in message:continue
            named={int(n) for n in re.findall(r'\b(\d+)\s*\([A-Z]{2,4}\)',message)}
            named.update(int(n) for n in re.findall(r'\bCAR\s+(\d+)\b',message))
            if row.get('driver_number') is not None:named.add(row['driver_number'])
            if driver in named:reports.append({'date':row['date'],'message':row['message']})
        if not reports:return None
        row=self.lap(driver,time)
        if not row:return None
        start=ts(row['date_start']);lap=row['lap_number']
        for sector in (1,2,3):
            duration=number(row.get(f'duration_sector_{sector}'))
            if duration is None or duration<=0:break
            end=start+duration
            if start<=time<=end:
                prior=[r.get(f'duration_sector_{sector}') for r in self.laps[driver].rows
                       if lap-5<=r['lap_number']<lap and number(r.get(f'duration_sector_{sector}'))
                       and r[f'duration_sector_{sector}']>0]
                if len(prior)<3:return None
                reference=statistics.median(prior)
                if duration<max(reference*1.5,reference+8):return None
                return {'driver_number':driver,'lap':lap,'sector':sector,
                        'sector_duration':duration,'reference_sector_duration':reference,
                        'reports':reports,'exact_incident_time_known':False,
                        'method':'named-collision-yellow-delayed-sector-v1'}
            start=end
        return None


def exclude_incident_exchanges(ctx, events):
    """Reclassify only unsupported passes; retain sources, IDs and coordinates.

    This also works on retained analyses without reconstructing their event list.
    Explicit source confirmations and sourced manual type corrections take priority.
    """
    for event in events:
        if event['type']!='inhaalactie' or event.get('classification_confidence')=='bevestigd':continue
        if any(c.get('field')=='type' for c in event.get('corrections',[])):continue
        if not event.get('date'):continue
        time=ts(event['date']);b=event['overtaken']
        retirement=ctx.retirement_context(b,time)
        if retirement:
            event['type']='onzeker'
            event['reason']='Uitvalcontext: registratie na de laatste gemeten voortgang van een bevestigde uitvaller; een race-inhaalactie is niet te onderscheiden van positiewinst door uitval. Het exacte uitvalmoment is niet vastgesteld.'
            event['classification_confidence']='onzekere uitvalcontext'
            event['retirement_context']=retirement
        else:
            incident=ctx.incident_context(b,time)
            if incident:
                event['type']='onzeker'
                event['reason']='Incidentcontext: genoemde coureur in een gemeld botsingsincident, gelijktijdige gele vlag en sterk vertraagde sector. Een race-inhaalactie is niet te onderscheiden van winst door het incident.'
                event['classification_confidence']='onzekere incidentcontext'
                event['incident_context']=incident
    return events


def event_id(session,a,b,date,lap):
    token=f'{session}|{a}|{b}|{date or "ronde="+str(lap)}'
    return hashlib.sha256(token.encode()).hexdigest()[:16]


def make_events(ctx):
    data=ctx.data;config=ctx.config;session=data['session'];events=[]
    raw=sorted(data['overtakes'],key=lambda r:ts(r['date']))
    for i,r in enumerate(raw):
        a=r['overtaking_driver_number'];b=r['overtaken_driver_number'];time=ts(r['date'])
        la=ctx.lap(a,time);lb=ctx.lap(b,time)
        lap=la['lap_number'] if la else None;lapb=lb['lap_number'] if lb else None
        typ='onzeker';reason='Onvoldoende timingcontext';confidence='onzeker'
        pits=ctx.pit(a,time)+ctx.pit(b,time)
        before=[ctx.position(d,time-config['registratievenster_seconden']) for d in [a,b]]
        after=[ctx.position(d,time+config['registratievenster_seconden']) for d in [a,b]]
        opposite=[j for j,x in enumerate(raw) if j!=i and x['overtaking_driver_number']==b and x['overtaken_driver_number']==a and abs(ts(x['date'])-time)<0.5]
        if ctx.start is None:typ='onzeker';reason='Racestart ontbreekt; racecontext niet vast te stellen'
        elif time<ctx.start:typ='buiten_race';reason='Registratie vóór gecontroleerde racestart'
        elif time>ctx.end+3:typ='straf_of_na_race';reason='Registratie na laatste gemeten finish; oorzaak niet automatisch vastgesteld'
        elif pits:typ='pitstopwisseling';reason='Binnen pitlane-tijdvenster van betrokken coureur';confidence='timingcontext'
        elif ctx.neutral(time):typ='neutralisatie';reason='Positiewisseling in neutralisatievenster';confidence='timingcontext'
        elif lap==1:typ='startactie';reason='Positiewisseling tijdens eigen ronde 1; geen bewijs van afzonderlijke geslaagde manoeuvre';confidence='timingcontext'
        elif opposite:typ='timingfluctuatie';reason='Tegengestelde registratie binnen 0,5 seconde; geen afzonderlijke manoeuvre bevestigd'
        elif data.get('pit_coverage_unknown'):reason='Pitregistraties ontbreken; wisseling buiten pitcontext niet vast te stellen'
        elif la and lb:
            # A one-lap difference can be a start/finish boundary. Compare crossing times of SAME lap.
            same=[l for l in ctx.laps[b].rows if l['lap_number']==lap]
            delta=abs(ts(la['date_start'])-ts(same[0]['date_start'])) if same else None
            typical=statistics.median([l['lap_duration'] for l in ctx.laps[a].rows if number(l.get('lap_duration'))]) if ctx.laps[a].rows else 100
            if lap!=lapb and (delta is None or delta>0.6*typical):
                typ='dubbelen_of_terugronden';reason='Rondeverschil met onvoldoende nabijheid op dezelfde raceronde';confidence='timingcontext'
            elif before[0] is not None and before[1] is not None and after[0] is not None and after[1] is not None and before[0]>before[1] and after[0]<after[1]:
                typ='inhaalactie';reason='Duurzame volgordewisseling buiten pitlane en neutralisatie';confidence='timingcontext'
            else:reason='Geen duurzame omkering van de volgorde in het controlevenster'
        event={'event_id':event_id(session['session_key'],a,b,r['date'],lap),'year':session['year'],'race':session['circuit_short_name'],
               'session_key':session['session_key'],'type':typ,'overtaker':a,'overtaken':b,'position_before':before,'position_after':after,
               'source_position':r.get('position'),'lap':lap,'overtaken_lap':lapb,'lap_convention':'lopende eigen ronde inhalende coureur; starttijd benaderd',
               'date':r['date'],'time_window':[time-config['registratievenster_seconden'],time+config['registratievenster_seconden']],
               'tyre_overtaker':ctx.tyre(a,lap),'tyre_overtaken':ctx.tyre(b,lapb),'pit_context':pits,'neutralisation':ctx.neutral(time),
               'location':None,'location_confidence':'onbekend','classification_confidence':confidence,
               'source_records':[{'source':data.get('timing_source','OpenF1'),'record_index':i,'record':r}], 'evidence':[], 'reason':reason,'corrections':[]}
        # Supplemental claims apply only to unique, compatible in-race exchanges and only if source fetched.
        for source in data.get('evidence',[]):
            if not source.get('available'):continue
            facts=source.get('verified_facts',{})
            for claim in facts.get('passes',[]):
                stint=ctx.stint(a,lap)
                if a==claim['overtaker'] and b==claim['overtaken'] and typ=='inhaalactie' and (not claim.get('stint') or stint and stint['stint_number']==claim['stint']):
                    event['evidence'].append({'source':source['id'],'url':source['url'],'claim':claim['explanation']})
                    event['confirmed_turn']=claim['turn'];event['classification_confidence']='bevestigd'
            for claim in facts.get('incidents',[]):
                control=[r for r in data['race_control'] if 'INCIDENT' in r.get('message','') and f'TURN {claim["turn"]} ' in r.get('message','') and f' {b} (' in r.get('message','') and abs(ts(r['date'])-time)<70]
                if b==claim['driver'] and lapb==claim['lap'] and typ=='inhaalactie' and control:
                    event['type']='incident_positiewisseling';event['reason']=claim['explanation'];event['classification_confidence']='brononderbouwde context'
                    event['evidence'].append({'source':source['id'],'url':source['url'],'claim':claim['explanation'],'race_control':control})
            for claim in facts.get('swaps',[]):
                if a==claim['overtaker'] and b==claim['overtaken'] and lap and lap>=claim['min_lap'] and typ=='inhaalactie':
                    event['type']=claim['type'];event['reason']=claim['explanation'];event['classification_confidence']='brononderbouwd'
                    event['evidence'].append({'source':source['id'],'url':source['url'],'claim':claim['explanation']})
        exclude_incident_exchanges(ctx,[event])
        events.append(event)
    # Exact/near duplicate in same direction; preserve original source records.
    merged=[]
    for e in events:
        match=next((x for x in reversed(merged) if x['overtaker']==e['overtaker'] and x['overtaken']==e['overtaken'] and x['lap']==e['lap'] and abs(ts(x['date'])-ts(e['date']))<=config['deduplicatie_seconden']),None)
        if match:match['source_records'].extend(e['source_records'])
        else:merged.append(e)
    for r in data.get('f1gures',[]):
        a=r['overtaking_driver_number'];b=r['overtaken_driver_number'];lap=r['lap_number']
        matches=[e for e in merged if e['overtaker']==a and e['overtaken']==b and e['lap']==lap]
        if len(matches)==1:matches[0]['source_records'].append({'source':'F1gures','record':r})
        else:
            merged.append({'event_id':event_id(session['session_key'],a,b,None,lap),'year':session['year'],'race':session['circuit_short_name'],'session_key':session['session_key'],
                           'type':'onzeker','overtaker':a,'overtaken':b,'lap':lap,'overtaken_lap':None,'date':None,
                           'position_before':[None,None],'position_after':[None,None],'source_position':None,'time_window':None,
                           'lap_convention':'ronde volgens geïmporteerde F1gures-registratie; timing niet vastgesteld',
                           'tyre_overtaker':ctx.tyre(a,lap),'tyre_overtaken':{'compound':None,'age':None},'pit_context':[], 'neutralisation':None,
                           'location':None,'location_confidence':'onbekend','classification_confidence':'onzeker','evidence':[],
                           'source_records':[{'source':'F1gures','record':r}], 'possible_matches':[e['event_id'] for e in matches], 'reason':'F1gures zonder eenduidige match; niet automatisch als bewezen actie geteld','corrections':[]})
    # Final classification can differ from the on-track finishing order. Only supported penalty evidence permits classification.
    for source in data.get('evidence',[]):
        if not source.get('available') or source.get('id')!='singapore-fia-resultaat':continue
        for result in data['session_result']:
            d=result['driver_number'];last=ctx.laps[d].rows[-1] if ctx.laps.get(d) and ctx.laps[d].rows else None
            if not last or not last.get('lap_duration'):continue
            final_time=ts(last['date_start'])+last['lap_duration'];running=ctx.position(d,final_time-.001)
            if d!=44 or running is None or running>=result['position']:continue
            rival=next((r['driver_number'] for r in data['session_result'] if r['position']==running),None)
            if rival is None:continue
            merged.append({'event_id':event_id(session['session_key'],rival,d,'final-classification',None),'year':session['year'],'race':session['circuit_short_name'],
                           'session_key':session['session_key'],'type':'straf','overtaker':rival,'overtaken':d,'lap':None,'overtaken_lap':None,'date':None,
                           'time_window':None,'lap_convention':'na de race; geen raceronde','position_before':[result['position'],running],'position_after':[running,result['position']],
                           'source_position':None,'tyre_overtaker':{'compound':None,'age':None},'tyre_overtaken':{'compound':None,'age':None},'pit_context':[],
                           'neutralisation':False,'location':None,'location_confidence':'onbekend','classification_confidence':'bevestigd',
                           'source_records':[{'source':'FIA','record':result,'source_url':source['url']}],
                           'evidence':[{'source':source['id'],'url':source['url'],'claim':'De definitieve classificatie past Hamiltons vijfsecondenstraf voor baanlimieten toe.'}],
                           'reason':'Classificatiewisseling na de race door bronbevestigde straf; geen inhaalactie op de baan','corrections':[]})
    return merged


def apply_corrections(events,overrides):
    lookup={e['event_id']:e for e in events}
    allowed={'type','reason','classification_confidence','location','location_confidence','lap','overtaken_lap','confirmed_turn'}
    for change in overrides.get('events',[]):
        if not change.get('reason') or not change.get('source_url'):raise ValueError('Elke correctie vereist reden en bron-URL.')
        if change['event_id'] not in lookup:raise ValueError('Correctie verwijst naar onbekende gebeurtenis: '+change['event_id'])
        e=lookup[change['event_id']]
        for k,v in change['set'].items():
            if k not in allowed:raise ValueError('Niet toegestaan correctieveld: '+k)
            e['corrections'].append({'field':k,'original':e.get(k),'updated':v,'reason':change['reason'],'source_url':change['source_url']});e[k]=v
    return events


def count_events(events,lap_count,config):
    for e in events:
        valid=bool(e.get('lap') and 2<=e['lap']<=lap_count)
        base=valid and e['type'] in ['inhaalactie','technisch_positieverlies','mogelijke_teamorder']
        analytic=base and not (e['type']=='mogelijke_teamorder' and config['analytisch_teamorders_uitsluiten']) and not (e['type']=='technisch_positieverlies' and config['analytisch_technisch_verlies_uitsluiten'])
        e['counts']={'openf1_original':sum(r['source']=='OpenF1' for r in e['source_records']),
                     'timing_original':sum(r['source'] in ['OpenF1','FastF1'] for r in e['source_records']),
                     'f1gures_original':sum(r['source']=='F1gures' for r in e['source_records']), 'on_track':base, 'analytical':analytic,'lap1':e.get('lap')==1 and e['type']=='startactie'}
        e['exclusion_reason']=None if analytic else e['reason']
    selected=[e for e in events if e['counts']['analytical']]
    perlap={str(n):sum(e['lap']==n for e in selected) for n in range(2,lap_count+1)}
    late=max(2,lap_count-math.ceil(lap_count*config['slotfase_fractie'])+1)
    late_count=sum(e['lap']>=late for e in selected)
    made=Counter(e['overtaker'] for e in selected);received=Counter(e['overtaken'] for e in selected)
    result={'openf1_original':sum(e['counts']['openf1_original'] for e in events),'f1gures_original':sum(e['counts']['f1gures_original'] for e in events),
            'timing_original':sum(e['counts']['timing_original'] for e in events),
            'on_track':sum(e['counts']['on_track'] for e in events),'analytical':len(selected),'lap1_changes':sum(e['counts']['lap1'] for e in events),
            'lap_count':lap_count,'per_lap':perlap,'laps_with':sum(v>0 for v in perlap.values()),'laps_without':sum(v==0 for v in perlap.values()),
            'denominator':max(0,lap_count-1),'mean':len(selected)/(lap_count-1) if lap_count>1 else None,
            'late_start':late,'late_end':lap_count,'late_count':late_count,'late_fraction':late_count/len(selected) if selected else None,
            'made':dict(made),'received':dict(received),'types':dict(Counter(e['type'] for e in events)),
            'compound_pairs':dict(Counter(str(e['tyre_overtaker']['compound'])+' → '+str(e['tyre_overtaken']['compound']) for e in selected)),
            'busiest_laps':[int(k) for k,v in perlap.items() if v==max(perlap.values(),default=0) and v>0],
            'source_matches':sum(any(r['source']=='OpenF1' for r in e['source_records']) and any(r['source']=='F1gures' for r in e['source_records']) for e in events)}
    f1records=[(e,r['record']) for e in events for r in e['source_records'] if r['source']=='F1gures']
    f1race=[(e,r) for e,r in f1records if 2<=r['lap_number']<=lap_count]
    corrected=[(e,r) for e,r in f1race if e['type']!='technisch_positieverlies']
    result['f1gures_comparison']={'lap1':sum(r['lap_number']==1 for e,r in f1records),'from_lap2':len(f1race),
        'late_count':sum(r['lap_number']>=late for e,r in f1race),'excluding_technical':len(corrected),
        'excluding_technical_late':sum(r['lap_number']>=late for e,r in corrected),
        'excluding_technical_late_fraction':sum(r['lap_number']>=late for e,r in corrected)/len(corrected) if corrected else None,
        'excluded_event_ids':[e['event_id'] for e,r in f1race if e['type']=='technisch_positieverlies'],
        'per_lap':{str(n):sum(r['lap_number']==n for e,r in f1race) for n in range(2,lap_count+1)},
        'note':'Afzonderlijke bronvariant; behoudt de oorspronkelijke netto-ronde-einddefinitie van F1gures en sluit uitsluitend brononderbouwd technisch positieverlies uit.'}
    assert sum(perlap.values())==len(selected)
    assert result['laps_with']+result['laps_without']==result['denominator']
    return result


def grid_and_result(ctx):
    grid={r['driver_number']:r['position'] for r in ctx.data['starting_grid']}
    for r in ctx.data.get('jolpica_results',[]):grid[int(r['number'])]=int(r['grid']) or None
    pitlane=set()
    for source in ctx.data.get('evidence',[]):
        if source.get('available'):pitlane.update(source.get('verified_facts',{}).get('pitlane_starters',[]))
    result={r['driver_number']:r for r in ctx.data['session_result']};rows=[]
    for d,driver in ctx.drivers.items():
        start=None if d in pitlane else grid.get(d)
        # Own lap 2 begins at that driver's lap-1 finish. Take last position just before crossing.
        lap2=next((l for l in ctx.laps[d].rows if l['lap_number']==2),None)
        lap1=next((l for l in ctx.laps[d].rows if l['lap_number']==1),None)
        t=ts(lap2['date_start'])-0.001 if lap2 else ts(lap1['date_start'])+lap1['lap_duration'] if lap1 and number(lap1.get('lap_duration')) else None
        end1=ctx.position(d,t) if t else None
        final=result.get(d,{}).get('position')
        rows.append({'driver_number':d,'name':driver['full_name'],'code':driver['name_acronym'],'team':driver['team_name'],
                     'grid':start,'pitlane_start':d in pitlane or d in grid and grid[d] is None,'lap1_position':end1,
                     'lap1_net_gain':start-end1 if start and end1 else None,'finish':final,'net_gain':start-final if start and final else None,
                     'start_compound':ctx.tyre(d,1)['compound'],'result':result.get(d,{})})
    return sorted(rows,key=lambda r:r['finish'] or 99)


def tyre_analysis(ctx):
    rows=[];excluded=[];clean=[]
    for d in ctx.drivers:
        for stint in [s for s in ctx.data['stints'] if s['driver_number']==d]:
            samples=[]
            for l in ctx.laps[d].rows:
                n=l['lap_number']
                if not (stint.get('lap_start') and stint.get('lap_end') and stint['lap_start']<=n<=stint['lap_end']):continue
                reasons=[];t=ts(l['date_start']);duration=number(l.get('lap_duration'))
                end=t+(duration or 0)
                if n==1:reasons.append('startprocedure')
                if not duration or duration<30 or duration>300:reasons.append('timingprobleem')
                if l.get('is_pit_out_lap'):reasons.append('outlap')
                if any(p['driver_number']==d and p['lap_number']==n for p in ctx.data['pit']):reasons.append('inlap')
                if any(a<=end and b>=t for a,b in ctx.neutral_windows):reasons.append('neutralisatie of herstart')
                if any(a<=end and b>=t for a,b in ctx.flag_windows):reasons.append('relevante vlagronde (conservatief gehele veld)')
                wet=ctx.weather.at(t)
                if wet and wet.get('rainfall'):reasons.append('regen')
                traffic=ctx.intervals[d].at(t+(duration or 0)/2)
                if traffic and number(traffic.get('interval')) is not None and 0<traffic['interval']<ctx.config['verkeer_grens_seconden']:reasons.append('herkenbaar verkeer op halverwege gemeten interval')
                control=[r for r in ctx.data['race_control'] if r.get('driver_number')==d and ('TIME' in r.get('message','') or 'INCIDENT' in r.get('message','')) and f'LAP {n} ' in r.get('message','')]
                if control:reasons.append('race-controlmelding over deze ronde')
                if reasons:excluded.append({'driver':d,'lap':n,'reasons':reasons})
                elif duration:samples.append((n,duration));clean.append({'driver':d,'lap':n,'duration':duration,'stint':stint['stint_number']})
            trend=None
            if len(samples)>=6:
                slopes=[(y2-y1)/(x2-x1) for i,(x1,y1) in enumerate(samples) for x2,y2 in samples[i+1:] if x2!=x1]
                trend=float(np.median(slopes))
            times=[v for n,v in samples];parts=np.array_split(times,3) if times else [[],[],[]]
            medians=[float(np.median(p)) if len(p) else None for p in parts]
            rows.append({**stint,'length':stint['lap_end']-stint['lap_start']+1 if stint.get('lap_end') and stint.get('lap_start') else None,
                         'clean_laps':len(samples),'robust_trend_seconds_per_lap':trend,'phase_medians':medians,
                         'new_or_used':'nieuw' if stint.get('tyre_age_at_start')==0 else 'gebruikt' if number(stint.get('tyre_age_at_start')) else 'onbekend'})
    return {'stints':rows,'excluded_laps':excluded,'clean_laps':clean}


def crossing(ctx,d,n):
    lap=next((l for l in ctx.laps[d].rows if l['lap_number']==n),None)
    if not lap or number(lap.get('lap_duration')) is None:return None
    return ts(lap['date_start'])+lap['lap_duration']


def pit_cycles(ctx):
    """Compare SAME completed lap at crossings, after both outlaps; no temporary positions as success."""
    pits=sorted(ctx.data['pit'],key=lambda p:ts(p['date']));rows=[];seen=set()
    for i,p in enumerate(pits):
        a=p['driver_number'];n=p['lap_number'];t=ts(p['date'])
        for q in pits[i+1:]:
            b=q['driver_number'];m=q['lap_number']
            if a==b or m<=n or m-n>ctx.config['strategie_max_stopafstand_ronden']:continue
            key=(a,b,n,m)
            if key in seen:continue
            seen.add(key)
            baseline=n-1;complete=m+1
            pre=[crossing(ctx,d,baseline) for d in [a,b]];post=[crossing(ctx,d,complete) for d in [a,b]]
            if any(v is None for v in pre+post):continue
            gap_before=pre[0]-pre[1];gap_after=post[0]-post[1]
            if abs(gap_before)>ctx.config['strategie_gap_grens_seconden']:continue
            # Both cars must finish this cycle without another intervening stop.
            extra=[x for x in pits if x is not p and x is not q and x['driver_number'] in [a,b] and n<=x['lap_number']<=complete]
            disrupted=bool(extra) or any(x<=max(post) and y>=min(pre) for x,y in ctx.neutral_windows)
            gain=gap_before-gap_after
            success=gap_before>0 and gap_after<0 or gap_before<0 and gap_after>0
            strategy='undercutsituatie' if gap_before>0 else 'overcutsituatie'
            beneficiary=a if gap_before>0 else b
            beneficiary_gain=gain if beneficiary==a else -gain
            status='Verstoord door externe omstandigheden' if disrupted else 'Geslaagd' if success else 'Tijd gewonnen zonder positiewinst' if beneficiary_gain>0 else 'Mislukt'
            trace=[]
            for lap in range(max(1,n-3),min(ctx.lap_count,m+5)+1):
                c1=crossing(ctx,a,lap);c2=crossing(ctx,b,lap)
                if c1 is not None and c2 is not None:trace.append({'lap':lap,'gap':c1-c2})
            detail=[]
            for d in [a,b]:
                for l in ctx.laps[d].rows:
                    if n<=l['lap_number']<=complete:
                        detail.append({'driver':d,'lap':l['lap_number'],'duration':l.get('lap_duration'),'outlap':l.get('is_pit_out_lap'), 'tyre':ctx.tyre(d,l['lap_number'])})
            rows.append({'cycle_id':f'{a}-{b}-{n}-{m}','early_driver':a,'late_driver':b,'early_stop_lap':n,'late_stop_lap':m,
                         'baseline_lap':baseline,'completed_lap':complete,'gap_before':gap_before,'gap_after':gap_after,
                         'gain_early_driver':gain,'strategy':strategy,'beneficiary':beneficiary,'status':status,'order_changed':success,
                         'pit_lane_early':p.get('lane_duration',p.get('pit_duration')),'pit_lane_late':q.get('lane_duration',q.get('pit_duration')),
                         'stationary_early':p.get('stop_duration'),'stationary_late':q.get('stop_duration'),
                         'trace':trace,'lap_details':detail,'attribution':'Waargenomen nettoresultaat inclusief pituitvoering, tempo en verkeer; bandenbijdrage niet geïsoleerd; intentie onbekend.'})
    return rows
