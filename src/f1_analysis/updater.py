"""Scheduled incremental races: fresh discovery, readiness gates and bounded retries."""
from __future__ import annotations
import argparse
import hashlib
import os
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

from .cli import load_config, code_hash
from .io import Client, read_json, write_json, utcnow
from .publication import latest_runs, settings


def parse_date(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)


def readiness(data):
    """An empty overtake or pit feed can be valid, so neither is a readiness gate."""
    missing = [name for name in ['drivers', 'laps', 'position', 'stints', 'race_control'] if not data.get(name)]
    finished=any(r.get('message','').upper() in ('SESSION FINISHED','SESSION ENDED') or r.get('flag','') in ('CHEQUERED','CHECKERED') for r in data.get('race_control',[]))
    if not finished:missing.append('bevestigd race-einde')
    results = data.get('session_result', [])
    winner = next((r for r in results if r.get('position') == 1 and r.get('number_of_laps')), None)
    if winner is None: missing.append('winnaar en definitieve raceafstand')
    else:
        driver = winner.get('driver_number'); distance = int(winner['number_of_laps'])
        recorded = {r.get('lap_number') for r in data['laps'] if r.get('driver_number') == driver}
        if distance not in recorded: missing.append('timing van laatste winnaarsronde')
    # Require result entries for the participant list; DSQ/DNF entries still count.
    drivers = {r['driver_number'] for r in data.get('drivers', [])}
    classified = {r['driver_number'] for r in results}
    if not drivers.issubset(classified): missing.append('uitslag voor alle deelnemers')
    return not missing, missing


def plan(sessions, known, state, now, config):
    chosen = []
    for session in sorted(sessions, key=lambda s: s['date_start']):
        if session.get('session_name') != 'Race' or session.get('is_cancelled'): continue
        end = session.get('date_end')
        if not end or parse_date(end) + timedelta(minutes=config['minimum_delay_minutes']) > now: continue
        key = str(session['session_key']); record = state.get(key, {})
        recent = parse_date(end) >= now - timedelta(days=config['settle_days'])
        if key in known and not recent: continue
        last = record.get('last_attempt')
        interval=config.get('refresh_hours',config['retry_hours']) if key in known else config['retry_hours']
        if last and parse_date(last) + timedelta(minutes=config.get('retry_minutes', interval * 60) if key not in known or record.get('status') in ('wacht_op_data', 'mislukt') else interval * 60) > now: continue
        # New and waiting races remain eligible even after the settlement window.
        chosen.append(session)
    chosen.sort(key=lambda s: (str(s['session_key']) in known, s['date_start']))
    return chosen[:config['max_races_per_update']]


def discover_calendar(client, years, known, now, config):
    """The season calendar leads discovery; OpenF1 is an optional timing adapter."""
    from .history import calendar
    from .acquire import calendar_match
    sessions = []
    calendars = {}
    for year in years:
        agenda = calendar(client, year)
        calendars[str(year)] = agenda
        try:
            available = [s for s in client.api('sessions', year=year) if s.get('session_name') == 'Race']
        except ValueError:
            available = []
        for race in agenda:
            previous = next((item for item in known.values() if item[2]['input']['year'] == year
                             and int(item[2].get('race_round') or item[2].get('session', {}).get('round') or -1) == race['round']), None)
            match = next((s for s in available if calendar_match([race['jolpica_race']], s)), None)
            # Keep the timing source of an existing dashboard when refreshing it.
            fast = previous and previous[2].get('session', {}).get('session_key') == race['session_key']
            session = dict(race)
            if match and not fast:
                session.update(match)
                session['timing_source'] = 'openf1'
            else:
                session['timing_source'] = 'fastf1'
                # This is a conservative screening time, never proof of completion.
                session['date_end'] = (parse_date(race['date_start']) + timedelta(hours=config.get('race_screen_after_hours', 3))).isoformat()
            sessions.append(session)
    write_json(client.root / '_storage/season-calendar.json', {'checked_at': now.isoformat(), 'seasons': calendars})
    return sessions


def fastf1_probe(client, session, root):
    """Wait for published results, then verify the complete public timing archive."""
    from .history import acquire
    import yaml
    result = client.fetch(f'https://api.jolpi.ca/ergast/f1/{session["year"]}/{session["round"]}/results.json', publisher='Jolpica')
    races = result['MRData']['RaceTable']['Races']
    if not races or not races[0].get('Results'):
        return None, ['definitieve raceuitslag']
    try:
        data, _ = acquire(client, session['year'], session['circuit_short_name'],
                          Path(root) / 'storage/probes' / str(session['session_key']),
                          yaml.safe_load((Path(root) / 'config/sources.yaml').read_text()))
        ready, missing = readiness(data)
        return (data if ready else None), missing
    except (ValueError, IndexError, KeyError) as exc:
        return None, ['volledige timinggegevens: ' + str(exc)]


def recipe_hash(root, previous=None):
    h=hashlib.sha256(code_hash(root).encode())
    for p in sorted((Path(root)/'config').glob('*.yaml')):h.update(p.name.encode());h.update(p.read_bytes())
    if previous:
        for p in sorted((previous[0].parent/'corrections').glob('*.yaml')):h.update(p.read_bytes())
    return h.hexdigest()


def optional_probe(client,session,drivers,root):
    """Watch delayed results and independent passes without assuming a private API."""
    from .acquire import calendar_match
    from .f1gures import discover
    result={'jolpica':'unknown','f1gures':'unknown'}
    try:
        races=client.fetch(f'https://api.jolpi.ca/ergast/f1/{session["year"]}.json',publisher='Jolpica')['MRData']['RaceTable']['Races']
        match=calendar_match(races,session)
        if len(match)!=1:return result
        number=int(match[0]['round'])
        reply=client.fetch(f'https://api.jolpi.ca/ergast/f1/{session["year"]}/{number}/results.json',publisher='Jolpica')
        result['jolpica']=reply['MRData']['RaceTable']['Races'][0]['Results']
        url=f'https://www.f1gures.app.hellowebdesign.co.uk/races/{session["year"]}/{number}/'
        page=client.fetch(url,kind='bytes',publisher='F1gures')
        raw=Path(root)/'storage/probes'/str(session['session_key']);(raw/'f1gures').mkdir(parents=True,exist_ok=True)
        result['f1gures']=discover(client,page,url,raw,drivers,session['year'],number)
    except (ValueError,KeyError,IndexError,TypeError):pass
    return result


def update(root, years=None, now=None, dry_run=False):
    root = Path(root).resolve(); now = now or datetime.now(timezone.utc); config = settings(root)
    years = years or [now.year - 1, now.year]
    if any(year < 2023 for year in years): raise ValueError('Automatische OpenF1-updates beginnen in 2023')
    # Discovery and probes always bypass historical cache, including cached empty lists.
    client = Client(root, load_config(root, root / 'config/history.yaml'), refresh=True)
    known = {str(m['session']['session_key']): (pointer, run, m)
             for pointer, run, m in latest_runs(root) if m['input']['year']>=2023 and m.get('session', {}).get('session_key')}
    sessions = discover_calendar(client, years, known, now, config)
    state_path = root / '_storage/update-state.json'
    state = read_json(state_path) if state_path.exists() else {'schema': 1, 'sessions': {}}
    queue = plan(sessions, known, state['sessions'], now, config)
    report = {'checked_at': now.isoformat(), 'planned': [s['session_key'] for s in queue],
              'planned_years': sorted({s['year'] for s in queue}), 'updated': [], 'unchanged': [], 'waiting': [], 'failed': []}
    if dry_run: return report
    for session in queue:
        key = str(session['session_key']); record = state['sessions'].setdefault(key, {})
        record.update(last_attempt=now.isoformat(), year=session['year'])
        try:
            if session.get('timing_source') == 'fastf1':
                data, missing = fastf1_probe(client, session, root)
                ready = data is not None
            else:
                try:
                    data = {ep: client.api(ep, session_key=session['session_key'])
                            for ep in ['drivers', 'session_result', 'laps', 'position', 'stints', 'race_control']}
                    ready, missing = readiness(data)
                except ValueError as exc:
                    ready, missing = False, ['OpenF1: ' + str(exc)]
                if not ready and session.get('timing_source') == 'openf1':
                    alternative, absent = fastf1_probe(client, session, root)
                    if alternative is not None:
                        data, ready = alternative, True
                        session['timing_source'] = 'fastf1'
                    else:
                        missing.extend(absent)
            if not ready:
                record.update(status='wacht_op_data', missing=missing)
                report['waiting'].append({'session_key': key, 'missing': missing})
            else:
                if session.get('timing_source') != 'fastf1':
                    for ep in ['overtakes','pit','intervals','weather','team_radio','starting_grid']:
                        try:data[ep]=client.api(ep,session_key=session['session_key'])
                        except ValueError:data[ep]='unknown'
                optional=optional_probe(client,session,data['drivers'],root)
                probe_sha=hashlib.sha256(json.dumps({'data':data,'optional':optional,'recipe':recipe_hash(root,known.get(key))},sort_keys=True,separators=(',',':')).encode()).hexdigest()
                if key in known and record.get('probe_sha256')==probe_sha:
                    record.update(status='ongewijzigd');report['unchanged'].append(session['session_key'])
                    write_json(state_path,state);continue
                # Analysis runs in another directory. The published latest pointer only
                # changes after readiness, rendering and link checks all succeed.
                command=[sys.executable, '-m', 'f1_analysis', '--root', str(root), 'analyse',
                    '--year', str(session['year']), '--gp', session['circuit_short_name'],
                    '--session-key', key, '--require-ready', '--refresh', '--config', str(root / 'config/history.yaml')]
                if session.get('timing_source') == 'fastf1':
                    command.extend(['--timing-source', 'fastf1'])
                    command.remove('--refresh')  # Reuse the freshly verified probe instead of fetching twice.
                if key in known and known[key][2].get('f1gures_import'):
                    imported=known[key][1]/'data/raw/f1gures/import.json'
                    if not imported.is_file():raise ValueError('Handmatige inhaalimport ontbreekt; bestaande analyse behouden')
                    command.extend(['--f1gures-import',str(imported)])
                result = subprocess.run(command,cwd=root, check=False)
                if result.returncode: raise ValueError(f'Analyse faalde (code {result.returncode})')
                record.update(status='bijgewerkt', completed_at=utcnow(),probe_sha256=probe_sha)
                record.pop('missing', None); record.pop('error', None)
                report['updated'].append(session['session_key'])
        except Exception as exc:
            record.update(status='mislukt', error=str(exc)); report['failed'].append({'session_key': key, 'error': str(exc)})
        write_json(state_path, state)
    return report


def main():
    parser = argparse.ArgumentParser(description='Voeg voltooide races automatisch toe')
    parser.add_argument('--root', default='.')
    parser.add_argument('--years', nargs='+', type=int)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(); report = update(args.root, args.years, dry_run=args.dry_run)
    write_json(Path(args.root) / '_storage/update-report.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('changed='+str(bool(report['updated'])).lower()+'\n'+'planned='+str(bool(report['planned'])).lower()+'\n')
    if report['failed']: sys.exit(1)


if __name__ == '__main__': main()
