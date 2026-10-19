"""Audit/refresh retained race pages locally without rerendering their presentation.

Usage: python -m f1_analysis.race_event_refresh [--apply]
No acquisition, publishing, raw-data edits or new incident-time estimates.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import re
import tarfile

from .analysis import Context, count_events, exclude_incident_exchanges
from .location import map_counts

VERSION='race-incident-refresh-v1'
FILES=('overzicht.html','data/derived/analysis.json','data/normalized/events.json',
       'exports/gebeurtenissen.json','exports/gebeurtenissen.csv',
       'exports/kerncijfers.json','exports/bronvergelijking.json',
       'interactive/circuitkaart.html','reports/bronnen-en-methode.md',
       'reports/bronnen-en-methode.html','logs/waarschuwingen.txt','manifest.json')
EVENT_FIELDS=('type','reason','classification_confidence','counts','exclusion_reason',
              'retirement_context','incident_context')
MARKER='[race-incident-refresh-v1]'


def json_bytes(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()


def node(text, identifier):
    match=re.search(r'(<script\b[^>]*\bid=["\']'+re.escape(identifier)+r'["\'][^>]*>)(.*?)(</script>)',text,re.S)
    if not match:raise ValueError('Embedded data missing: '+identifier)
    return match,json.loads(match[2])


def sync_payload(text, identifier, events, stats=None, warnings=None):
    match,payload=node(text,identifier);lookup={e['event_id']:e for e in events}
    if [e['event_id'] for e in payload['events']]!=[e['event_id'] for e in events]:
        raise ValueError('Page and retained analysis have different event IDs')
    for event in payload['events']:
        for key in EVENT_FIELDS:
            if key in lookup[event['event_id']]:event[key]=lookup[event['event_id']][key]
    if stats is not None:payload['stats']=stats
    if warnings is not None:payload['warnings']=warnings
    encoded=json.dumps(payload,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    return text[:match.start(2)]+encoded+text[match.end(2):]


def refresh_bundle(original):
    bundle=deepcopy(original);ctx=Context(bundle['data'],bundle['config'])
    exclude_incident_exchanges(ctx,bundle['events'])
    bundle['config']['analytisch_technisch_verlies_uitsluiten']=True
    bundle['stats']=json.loads(json.dumps(count_events(bundle['events'],ctx.lap_count,bundle['config'])))
    bundle['mapping']=map_counts(bundle['events'],bundle['config'])
    # The complete event/source register and measured geography must be invariant.
    for key in ('event_id','source_records','location'):
        assert [e.get(key) for e in original['events']]==[e.get(key) for e in bundle['events']]
    assert original['data']==bundle['data']
    return bundle


def note_for(bundle, before):
    retirement=sum(bool(e.get('retirement_context')) for e in bundle['events'])
    incident=sum(bool(e.get('incident_context')) for e in bundle['events'])
    technical=sum(e['type']=='technisch_positieverlies' for e in bundle['events'])
    return (f'{MARKER} Hercontrole race-inhaaltelling: {before} → {bundle["stats"]["analytical"]}. '
            f'{retirement} registraties met onzekere uitvalcontext en {incident} met onzekere incidentcontext '
            f'zijn apart bewaard; {technical} registraties van technisch positieverlies tellen analytisch niet mee. '
            'Een bevestigde uitval sluit eerdere echte passes niet uit. Incidentcontext vereist een genoemde '
            'botsingsmelding, gelijktijdige gele vlag en een sterk vertraagde sector. '
            'Exacte incident- en uitvaltijden worden niet geschat. Bronbevestigde inhaalacties en onderbouwde '
            'handcorrecties behouden voorrang. Alle oorspronkelijke bronregistraties, IDs en kaartcoördinaten '
            'blijven behouden. Onvoldoende context wordt niet als bewezen crashpass geclassificeerd.')


def csv_bytes(events):
    keys=list(dict.fromkeys(k for e in events for k in e));output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=keys);writer.writeheader()
    writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in e.items()} for e in events)
    return output.getvalue().encode('utf-8-sig')


def stage_run(run, original, bundle, classifier_hash, timestamp):
    """Build every replacement before any file is written."""
    note=note_for(bundle,original['stats']['analytical'])
    def coverage(text):
        mapping=bundle['mapping']
        return re.sub(r'Kaartdekking: \d+ van \d+ analytische gebeurtenissen, \d+ onbekend\.',
            f'Kaartdekking: {mapping["located"]} van {mapping["included"]} analytische gebeurtenissen, {mapping["unknown"]} onbekend.',text)
    bundle['warnings']=[w for w in bundle.get('warnings',[]) if MARKER not in w]+[note]
    content={'data/derived/analysis.json':json_bytes(bundle),
             'data/normalized/events.json':json_bytes(bundle['events']),
             'exports/gebeurtenissen.json':json_bytes(bundle['events']),
             'exports/gebeurtenissen.csv':csv_bytes(bundle['events']),
             'exports/kerncijfers.json':json_bytes(bundle['stats']),
             'exports/bronvergelijking.json':json_bytes(bundle['stats']['f1gures_comparison'])}
    content['overzicht.html']=sync_payload((run/'overzicht.html').read_text(),'dashboard-data',bundle['events'],bundle['stats'],bundle['warnings']).encode()
    circuit=run/'interactive/circuitkaart.html'
    if circuit.exists():content['interactive/circuitkaart.html']=sync_payload(circuit.read_text(),'gegevens',bundle['events']).encode()
    for name in ('reports/bronnen-en-methode.md','logs/waarschuwingen.txt'):
        path=run/name
        if path.exists():
            text='\n'.join(line for line in path.read_text().splitlines() if MARKER not in line)
            content[name]=(coverage(text).rstrip()+'\n\n'+note+'\n').encode()
    report=run/'reports/bronnen-en-methode.html'
    if report.exists():
        text=coverage(re.sub(r'<section data-race-incident-refresh="1">.*?</section>','',report.read_text(),flags=re.S))
        section='<section data-race-incident-refresh="1"><h2>Hercontrole race-inhaalacties</h2><p>'+html.escape(note)+'</p></section>'
        # Some retained documents omit the optional closing body tag.
        text=text.replace('</body>',section+'</body>') if '</body>' in text else text+section
        content['reports/bronnen-en-methode.html']=text.encode()
    manifest=json.loads((run/'manifest.json').read_bytes())
    manifest.setdefault('configuration',{})['analytisch_technisch_verlies_uitsluiten']=True
    manifest.setdefault('counting_rules',{}).update(retirement_context='confirmed-dnf-last-measured-progress-v1',incident_context='named-collision-yellow-delayed-sector-v1')
    if manifest.get('classification_revision') and manifest['classification_revision'].get('refresh_version')!=VERSION:
        manifest.setdefault('classification_history',[]).append(manifest['classification_revision'])
    manifest['classification_revision']={'refresh_version':VERSION,'created_at':timestamp,
        'before':original['stats']['analytical'],'after':bundle['stats']['analytical'],
        'excluded_uncertain_event_ids':[e['event_id'] for e in bundle['events'] if e.get('retirement_context') or e.get('incident_context')],
        'raw_records_preserved':True,'classifier_sha256':classifier_hash}
    for name,body in content.items():manifest.setdefault('file_hashes',{})[name]=hashlib.sha256(body).hexdigest()
    content['manifest.json']=json_bytes(manifest)
    return content


def run_audit(root, output, apply=False):
    root=Path(root).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    timestamp=datetime.now(timezone.utc).isoformat()
    classifier_hash=hashlib.sha256(Path(__file__).with_name('analysis.py').read_bytes()).hexdigest()
    rows=[];candidates=[]
    for page in sorted((root/'analyses').glob('*/*/runs/*/overzicht.html')):
        run=page.parent;text=page.read_text();_,payload=node(text,'dashboard-data')
        row={'run':str(run.relative_to(root)),'year':payload['year'],'race':payload['race'],
             'retained_events':len(payload['events'])}
        if payload.get('historical'):
            # Lap-end inversions have no measured manoeuvre/incident time.
            assert all(not e.get('counts',{}).get('on_track') for e in payload['events'])
            assert all(e['type'] in ('pitstopwisseling','gereconstrueerde_positiewisseling') for e in payload['events'])
            row.update(kind='historical',status='reconstructed-position-changes-not-confirmed-overtakes')
        elif not (run/'data/derived/analysis.json').exists():
            # Never substitute a newer dataset into an older snapshot. Every
            # current race must have its own input; superseded snapshots are
            # listed explicitly if their original local archive is unavailable.
            pointer=run.parents[1]/'latest.json'
            latest=run.parents[1]/json.loads(pointer.read_bytes())['run']
            if latest==run:raise ValueError('Current race input missing: '+str(run))
            row.update(kind='superseded-input-unavailable',status='unchanged-no-original-timing',current_run=str(latest.relative_to(root)))
        else:
            original=json.loads((run/'data/derived/analysis.json').read_bytes());bundle=refresh_bundle(original)
            differences=[e['event_id'] for e,old in zip(bundle['events'],original['events']) if e['type']!=old['type']]
            row.update(kind='timing',before=original['stats']['analytical'],after=bundle['stats']['analytical'],
                retirement=sum(bool(e.get('retirement_context')) for e in bundle['events']),
                incident=sum(bool(e.get('incident_context')) for e in bundle['events']),
                technical=sum(e['type']=='technisch_positieverlies' for e in bundle['events']),
                new_uncertain_event_ids=differences)
            needs=bundle!=original
            row['status']='updated' if apply and needs else 'update-needed' if needs else 'checked-unchanged'
            if needs:
                # Fail preflight before any backup or mutation if a page/export
                # has diverged from its retained analysis.
                stage_run(run,original,bundle,classifier_hash,timestamp)
                candidates.append(run)
        rows.append(row)
        if len(rows)%100==0:print(f'Gecontroleerd: {len(rows)}',flush=True)
    backup=output/'all-races-before.tar.gz'
    if apply and candidates:
        if backup.exists():raise ValueError('Backup already exists; choose a new output directory')
        with tarfile.open(backup,'w:gz') as archive:
            for run in candidates:
                for name in FILES:
                    path=run/name
                    if path.exists():archive.add(path,arcname=path.relative_to(root).as_posix(),recursive=False)
        # Reopen and verify the backup before writing local analyses.
        with tarfile.open(backup,'r:gz') as archive:
            for member in archive:
                assert archive.extractfile(member).read()==(root/member.name).read_bytes()
        for index,run in enumerate(candidates,1):
            original=json.loads((run/'data/derived/analysis.json').read_bytes());bundle=refresh_bundle(original)
            content=stage_run(run,original,bundle,classifier_hash,timestamp)
            for name,body in content.items():
                path=run/name;path.parent.mkdir(parents=True,exist_ok=True)
                temporary=path.with_name(path.name+'.refresh-tmp');temporary.write_bytes(body);temporary.replace(path)
            if index%10==0:print(f'Bijgewerkt: {index}/{len(candidates)}',flush=True)
    timed=[r for r in rows if r['kind']=='timing']
    current={str((p.parent/json.loads(p.read_bytes())['run']).relative_to(root))
             for p in (root/'analyses').glob('*/*/latest.json')}
    assert current.issubset({r['run'] for r in rows}), 'Current race missing from audit'
    current_timing=[r for r in timed if r['run'] in current]
    summary={'created_at':timestamp,'applied':apply,'published':False,'pages':len(rows),
        'timing_pages':len(timed),'historical_pages':sum(r['kind']=='historical' for r in rows),
        'superseded_without_original_input':sum(r['kind']=='superseded-input-unavailable' for r in rows),'updated_pages':len(candidates),
        'races_with_lower_count':sum(r['after']<r['before'] for r in timed),
        'before':sum(r['before'] for r in timed),'after':sum(r['after'] for r in timed),
        'retirement_context':sum(r['retirement'] for r in timed),'incident_context':sum(r['incident'] for r in timed),
        'retained_events':sum(r['retained_events'] for r in rows),'classifier_sha256':classifier_hash}
    summary.update(current_races=len(current),current_timing_races=len(current_timing),
        current_historical_races=sum(r['kind']=='historical' and r['run'] in current for r in rows),
        current_races_with_lower_count=sum(r['after']<r['before'] for r in current_timing),
        current_before=sum(r['before'] for r in current_timing),current_after=sum(r['after'] for r in current_timing))
    (output/('report.json' if apply else 'plan.json')).write_bytes(json_bytes({'summary':summary,'races':rows}))
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--output',type=Path,default=Path('storage/racing-overtakes-all-20261019'))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();run_audit(args.root,args.output,args.apply)
