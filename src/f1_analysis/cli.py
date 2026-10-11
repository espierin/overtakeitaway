from __future__ import annotations
import argparse, hashlib, json, shutil, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
import yaml
from . import __version__
from .io import Client, read_json, write_json, write_csv, slug, utcnow
from .acquire import acquire, import_passes
from .analysis import Context, make_events, apply_corrections, count_events, grid_and_result, tyre_analysis, pit_cycles
from .location import fetch_locations, map_counts


def load_config(root,path):
    base=yaml.safe_load((root/'config/defaults.yaml').read_text())
    if path:base.update(yaml.safe_load(Path(path).read_text()) or {})
    if not 0<base['slotfase_fractie']<=1:raise ValueError('slotfase_fractie moet tussen 0 en 1 liggen.')
    return base


def analyse(args):
    from .render import render, update_index, check_links
    root=Path(args.root).resolve();config=load_config(root,args.config)
    client=Client(root,config,offline=args.offline or bool(args.from_run),refresh=args.refresh)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:6]
    initial=root/'analyses'/str(args.year)/slug(args.gp)/'runs'/run_id
    initial.mkdir(parents=True,exist_ok=False);run=initial
    manifest={'code_sha256':code_hash(root),'version':__version__,'created_at':utcnow(),'input':{'year':args.year,'gp':args.gp},'configuration':config,'status':'bezig','warnings':[]}
    write_json(run/'manifest.json',manifest)
    try:
        if args.from_run:
            old=Path(args.from_run).resolve()
            from .publication import materialize_run
            materialize_run(root,old)
            data=read_json(old/'data/normalized/input.json')
            if data['session']['year']!=args.year:raise ValueError('Jaar komt niet overeen met eerdere uitvoering.')
            from .io import select_race
            select_race([data['session']],args.gp)
            shutil.copytree(old/'data/raw',run/'data/raw',dirs_exist_ok=True)
            parent=read_json(old/'manifest.json');warnings=list(parent.get('warnings',[]));client.sources=parent.get('sources',[])
            manifest['parent_run']=str(old)
        else:
            if args.year<2023:
                from .history import acquire as acquire_history
                data,warnings=acquire_history(client,args.year,args.gp,run/'data/raw',yaml.safe_load((root/'config/sources.yaml').read_text()))
            else:
                data,warnings=acquire(client,args.year,args.gp,run/'data/raw',yaml.safe_load((root/'config/sources.yaml').read_text()),session_key=getattr(args,'session_key',None))
        if getattr(args,'require_ready',False):
            from .updater import readiness
            ready,missing=readiness(data)
            if not ready:raise ValueError('Race nog niet publiceerbaar: '+', '.join(missing))
        canonical=root/'analyses'/str(args.year)/slug(data['session']['circuit_short_name'])
        target=canonical/'runs'/run_id
        if target!=run:target.parent.mkdir(parents=True,exist_ok=True);run.rename(target);run=target
        corrections=canonical/'corrections'/'overrides.yaml'
        corrections.parent.mkdir(parents=True,exist_ok=True)
        if not corrections.exists():corrections.write_text('# Elke wijziging vereist event_id, reden, bron-URL en set-velden.\nevents: []\n')
        overrides=yaml.safe_load(corrections.read_text()) or {'events':[]}
        if args.f1gures_import:
            data['f1gures']=import_passes(args.f1gures_import,args.year,data['session']['session_key'])
            write_json(run/'data/raw/f1gures/import.json',data['f1gures'])
            manifest['f1gures_import']={'path':str(Path(args.f1gures_import).resolve()),'sha256':hashlib.sha256(Path(args.f1gures_import).read_bytes()).hexdigest()}
        ctx=Context(data,config);events=apply_corrections(make_events(ctx),overrides)
        if ctx.observed_lap_count>ctx.lap_count:
            warnings.append(f'Officiële winnaarclassificatie telt {ctx.lap_count} ronden; timing bevat records tot ronde {ctx.observed_lap_count}. Records buiten de geclassificeerde afstand blijven bewaard en worden niet in de standaardtelling of noemer opgenomen.')
        missing_first=[d for d in ctx.drivers if not any(r['lap_number']==1 and r.get('date_start') for r in data['laps'] if r['driver_number']==d)]
        if missing_first:warnings.append(f'Ronde-1-timing ontbreekt voor {len(missing_first)} coureurs. Startmelding kan wel beschikbaar zijn; ontbrekende rondecontext en eindposities worden niet ingevuld.')
        missing_laps=0
        for d in ctx.drivers:
            recorded={r['lap_number'] for r in data['laps'] if r['driver_number']==d and r.get('lap_number')}
            if recorded:missing_laps+=len(set(range(1,max(recorded)+1))-recorded)
        if missing_laps:warnings.append(f'{missing_laps} ronde-records ontbreken binnen de waargenomen coureursreeksen. Inhaal- en tempotellingen kunnen daardoor onvolledig zijn; ontbrekende ronden worden niet gereconstrueerd.')
        stats=count_events(events,ctx.lap_count,config)
        track,_=fetch_locations(client,ctx,events,run/'data/raw',warnings)
        mapping=map_counts(events,config)
        table=grid_and_result(ctx);tyres=tyre_analysis(ctx);cycles=pit_cycles(ctx)
        if not ctx.start_confirmed:warnings.append('Racestart niet onafhankelijk bevestigd door sessiestatus; eigen ronde-1-start als benadering gebruikt.')
        if not data.get('f1gures'):warnings.append('F1gures-gebeurtenissen ontbreken: onafhankelijke brontelling en vergelijking zijn onbekend, niet nul.')
        if mapping['unknown']:warnings.append(f'{mapping["unknown"]} analytisch getelde acties hebben geen bruikbare kaartlocatie.')
        if not data.get('circuit'):warnings.append('Officiële circuitgeometrie niet toegankelijk; gemeten ronde als baanvorm, zonder geografische oriëntatie of bochtnummerankers.')
        warnings.append('Bandenbijdrage aan strategie niet causaal geïsoleerd; brandstof, auto, verkeer en baanontwikkeling beïnvloeden tempo.')
        if not data.get('evidence'):warnings.append('Geen aanvullende racespecifieke bronverificatie; generieke timinganalyse blijft gedeeltelijk.')
        bundle={'data':data,'events':events,'stats':stats,'drivers':table,'tyres':tyres,'cycles':cycles,'track':track,'mapping':mapping,
                'start':ctx.start,'start_confirmed':ctx.start_confirmed,'warnings':list(dict.fromkeys(warnings)),'config':config,'sources':client.sources}
        write_json(run/'data/normalized/input.json',data)
        write_json(run/'data/normalized/events.json',events)
        write_json(run/'data/derived/analysis.json',bundle)
        write_json(run/'data/derived/tyre-exclusions.json',tyres['excluded_laps'])
        write_json(run/'exports/gebeurtenissen.json',events);write_csv(run/'exports/gebeurtenissen.csv',events)
        write_json(run/'exports/kerncijfers.json',stats);write_json(run/'exports/bronvergelijking.json',stats['f1gures_comparison']);write_csv(run/'exports/pitstopstrategie.csv',cycles)
        write_json(run/'data/derived/corrections.json',overrides)
        manifest.update(session=data['session'],meeting=data['meeting'],sources=client.sources,warnings=bundle['warnings'],
                        coverage={ep:len(data.get(ep,[])) for ep in ['drivers','laps','overtakes','pit','stints','position','intervals','starting_grid','session_result','f1gures']},
                        corrections=overrides,counting_rules={'lap_convention':'eigen lopende ronde inhalende coureur','standard_from_lap':2,'slotfase':[stats['late_start'],stats['late_end']]},
                        status='gedeeltelijk')
        # Full only when all mandatory coverage gates pass; version 1 intentionally does not certify full causal/location reconstruction.
        render(run,bundle,manifest)
        check_links(run)
        manifest['files']=[str(p.relative_to(run)) for p in sorted(run.rglob('*')) if p.is_file()]
        manifest['file_hashes']={str(p.relative_to(run)):hashlib.sha256(p.read_bytes()).hexdigest() for p in run.rglob('*') if p.is_file() and p.name!='manifest.json'}
        write_json(run/'manifest.json',manifest)
        write_json(canonical/'latest.json',{'run':str(run.relative_to(canonical)),'status':manifest['status'],'created_at':manifest['created_at']})
        update_index(root)
        print('Analyse voltooid ('+manifest['status']+'): '+str(run/'overzicht.html'))
        print(f"{data.get('timing_source','OpenF1')}: {stats['timing_original']} registraties; op de baan vanaf ronde 2: {stats['on_track']}; analytisch: {stats['analytical']}.")
        return 0
    except Exception as exc:
        manifest.update(status='mislukt',error=str(exc));write_json(run/'manifest.json',manifest)
        update_index(root)
        raise


def code_hash(root):
    h=hashlib.sha256()
    for p in sorted((root/'src/f1_analysis').iterdir()):
        if p.suffix in ['.py','.js','.css']:h.update(p.name.encode());h.update(p.read_bytes())
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description='Lokale, controleerbare Formula 1-analyse in het Nederlands.')
    parser.add_argument('--root',default='.',help='Projectmap met config/ en analyses/')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('analyse',help='Verzamel gegevens en genereer alle rapporten en figuren')
    p.add_argument('--year',type=int,required=True);p.add_argument('--gp',required=True)
    p.add_argument('--session-key',type=int,help='Exacte OpenF1-hoofdrace voor automatische verwerking')
    p.add_argument('--require-ready',action='store_true',help='Publiceer pas als uitslag en timing beschikbaar zijn')
    p.add_argument('--offline',action='store_true',help='Gebruik uitsluitend cache')
    p.add_argument('--refresh',action='store_true',help='Haal brondata bewust opnieuw op')
    p.add_argument('--from-run',help='Heranalyseer opgeslagen input van eerdere uitvoering')
    p.add_argument('--config',help='Aanvullende YAML-instellingen');p.add_argument('--f1gures-import',help='CSV of JSON met bronvermelding')
    p=sub.add_parser('races',help='Toon beschikbare hoofdraces')
    p.add_argument('--year',type=int,required=True);p.add_argument('--offline',action='store_true')
    p=sub.add_parser('render',help='Render eerder opgeslagen analyse naar een nieuwe uitvoering')
    p.add_argument('--run',required=True)
    args=parser.parse_args()
    try:
        if args.command=='analyse':
            if args.year<1950:raise ValueError('Het wereldkampioenschapsarchief begint in 1950.')
            if args.year<2020:
                if args.from_run or args.f1gures_import:raise ValueError('Historische uitslagenoverzichten gebruiken geen timingheranalyse of inhaalimport.')
                if args.offline and args.refresh:raise ValueError('--offline en --refresh kunnen niet samen.')
                from .archive import Archive,generate
                from .io import select_race
                archive=Archive(Path(args.root).resolve(),offline=args.offline,refresh=args.refresh)
                sessions=archive.calendar(args.year)
                candidates=[]
                for session in sessions:
                    r=archive.tables['round'][session['round_id']];c=archive.tables['circuit'][r['circuit_id']]
                    candidates.append({'session_name':'Race','session_key':int(session['id']),'circuit_short_name':c['name'],'country_name':c['country'],'location':c['locality'],'meeting_name':r['name']})
                chosen=select_race(candidates,args.gp)
                session=next(r for r in sessions if int(r['id'])==chosen['session_key'])
                run=generate(archive,session);print('Historisch overzicht: '+str(run/'overzicht.html'));return 0
            if args.offline and args.refresh:raise ValueError('--offline en --refresh kunnen niet samen.')
            return analyse(args)
        if args.command=='races':
            root=Path(args.root).resolve();c=Client(root,load_config(root,None),offline=args.offline)
            if args.year<2023:
                from .history import calendar
                sessions=calendar(c,args.year)
            else:sessions=c.api('sessions',year=args.year,session_name='Race')
            for s in sessions:
                if not s.get('is_cancelled'):print(s['date_start'][:10],s['circuit_short_name'],s['location'],'sessie',s['session_key'])
        elif args.command=='render':
            from .render import render, check_links, update_index
            old=Path(args.run).resolve();m=read_json(old/'manifest.json')
            from .publication import materialize_run
            materialize_run(Path(args.root).resolve(),old)
            if m.get('analysis_kind')=='historisch-overzicht':
                from .archive import Archive,generate
                archive=Archive(Path(args.root).resolve(),offline=True)
                run=generate(archive,archive.races[str(m['session']['session_key'])]);print('Historisch overzicht: '+str(run/'overzicht.html'));return 0
            b=read_json(old/'data/derived/analysis.json')
            if m['status'] not in ['volledig','gedeeltelijk']:raise ValueError('Render vereist een geslaagde uitvoering; gebruik --from-run om een mislukte uitvoering te heranalyseren.')
            run=old.parent/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:6])
            shutil.copytree(old,run);m.update(created_at=utcnow(),parent_run=str(old),parent_code_sha256=m.get('code_sha256'),code_sha256=code_hash(Path(args.root).resolve()));render(run,b,m);check_links(run)
            m['files']=[str(p.relative_to(run)) for p in sorted(run.rglob('*')) if p.is_file()]
            m['file_hashes']={str(p.relative_to(run)):hashlib.sha256(p.read_bytes()).hexdigest() for p in run.rglob('*') if p.is_file() and p.name!='manifest.json'}
            write_json(run/'manifest.json',m)
            write_json(run.parent.parent/'latest.json',{'run':str(run.relative_to(run.parent.parent)),'status':m['status'],'created_at':m['created_at']})
            update_index(Path(args.root).resolve());print('Nieuwe render: '+str(run/'overzicht.html'))
    except (ValueError,FileNotFoundError,KeyError) as exc:
        print('Analyse niet voltooid: '+str(exc),file=sys.stderr);sys.exit(1)
