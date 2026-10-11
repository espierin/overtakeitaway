"""Build completed current-season races from the public F1 timing archive."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

from f1_analysis.cli import load_config
from f1_analysis.history import calendar
from f1_analysis.io import Client, read_json, write_json, slug, utcnow
from f1_analysis.render import update_index, check_links

parser = argparse.ArgumentParser()
parser.add_argument('--year', type=int, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
client = Client(root, load_config(root, root / 'config/history.yaml'), refresh=True)
races = calendar(client, args.year)
base = root / 'analyses' / str(args.year)
checkpoint = base / 'season-manifest.json'
state = {'year': args.year, 'status': 'bezig', 'started_at': utcnow(),
         'season_complete': False, 'timing_source': 'FastF1', 'races': [], 'waiting': []}
for race in races:
    if datetime.fromisoformat(race['date_start'].replace('Z', '+00:00')) > datetime.now(timezone.utc):
        state['waiting'].append({'round': race['round'], 'gp': race['meeting_name'], 'reason': 'nog niet verreden'})
        continue
    reply = client.fetch(f'https://api.jolpi.ca/ergast/f1/{args.year}/{race["round"]}/results.json', publisher='Jolpica')
    classified = reply['MRData']['RaceTable']['Races']
    if not classified or not classified[0].get('Results'):
        state['waiting'].append({'round': race['round'], 'gp': race['meeting_name'], 'reason': 'uitslag nog niet beschikbaar'})
        continue
    gp = race['circuit_short_name']
    record = {'session_key': race['session_key'], 'round': race['round'], 'gp': gp, 'date': race['date_start']}
    state['races'].append(record)
    pointer = base / slug(gp) / 'latest.json'
    print(f'{args.year} ronde {race["round"]}: {gp}', flush=True)
    try:
        if not pointer.exists():
            subprocess.run([sys.executable, '-m', 'f1_analysis', 'analyse', '--year', str(args.year),
                            '--gp', gp, '--timing-source', 'fastf1', '--config', str(root / 'config/history.yaml'),
                            '--require-ready'], cwd=root, check=True)
        run = pointer.parent / read_json(pointer)['run']
        manifest = read_json(run / 'manifest.json')
        check_links(run)
        assert manifest['coverage']['session_result'] == len(classified[0]['Results'])
        record.update(status=manifest['status'], run=str(run.relative_to(root)), coverage=manifest['coverage'])
    except Exception as exc:
        record.update(status='mislukt', error=str(exc))
    write_json(checkpoint, state)
state.update(status='bijgewerkt' if all(r['status'] != 'mislukt' for r in state['races']) else 'onvolledig',
             available_races=len(state['races']), scheduled_races=len(races), checked_at=utcnow())
write_json(checkpoint, state)
update_index(root)
print(state['status'], state['available_races'], 'beschikbare races', flush=True)
sys.exit(1 if state['status'] == 'onvolledig' else 0)
