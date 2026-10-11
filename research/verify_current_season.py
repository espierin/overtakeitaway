"""Verify every current-season result, readiness gate, export and stored hash."""
import argparse
import hashlib
from pathlib import Path
from f1_analysis.analysis import Context, make_events, apply_corrections, count_events
from f1_analysis.io import read_json, write_json
from f1_analysis.render import check_links
from f1_analysis.updater import readiness

p = argparse.ArgumentParser()
p.add_argument('--year', type=int, required=True)
args = p.parse_args()
root = Path(__file__).resolve().parent.parent
state = read_json(root / 'analyses' / str(args.year) / 'season-manifest.json')
assert state['status'] == 'bijgewerkt' and not state['season_complete']
rows = [r for r in read_json(root / 'analyses/index.json') if r['year'] == args.year]
assert len(rows) == len(state['races']) == state['available_races']
checked = []
for row in rows:
    run = root / 'analyses' / row['path']
    m = read_json(run / 'manifest.json')
    b = read_json(run / 'data/derived/analysis.json')
    data = b['data']
    ready, missing = readiness(data)
    assert ready, (row['gp'], missing)
    official = data['jolpica_results']
    winner = next(r for r in official if r['position'] == '1')
    actual = next(r for r in data['session_result'] if r['position'] == 1)
    assert actual['driver_number'] == int(winner['number'])
    assert actual['number_of_laps'] == int(winner['laps'])
    assert {r['driver_number'] for r in data['session_result']} == {int(r['number']) for r in official}
    for d in data['session_result']:
        source = next(r for r in official if int(r['number']) == d['driver_number'])
        assert d['position'] == int(source['position']), (row['gp'], d, source)
    ctx = Context(data, b['config'])
    import json
    stats = json.loads(json.dumps(count_events(apply_corrections(make_events(ctx), m['corrections']), ctx.lap_count, b['config'])))
    assert {k: stats[k] for k in b['stats']} == b['stats']
    assert sum(stats['per_lap'].values()) == sum(stats['made'].values()) == sum(stats['received'].values()) == stats['analytical']
    assert (run / 'reports/bronnen-en-methode.md').is_file()
    assert (run / 'reports/bronnen-en-methode.html').is_file()
    assert (run / 'interactive/circuitkaart.html').is_file()
    assert (run / 'exports/gebeurtenissen.csv').is_file()
    assert (run / 'exports/pitstopstrategie.csv').is_file()
    assert read_json(run.parent.parent / 'latest.json')['run'] == 'runs/' + run.name
    for name, sha in m['file_hashes'].items():
        assert hashlib.sha256((run / name).read_bytes()).hexdigest() == sha, name
    check_links(run)
    checked.append({'race': row['gp'], 'winner': winner['Driver']['familyName'], 'drivers': len(official),
                    'analytical_actions': stats['analytical'], 'ready': True, 'hashes_verified': True})
write_json(root / 'research/qa' / f'{args.year}-integration.json', {'races': len(checked), 'results': checked})
print(f'{len(checked)} races: uitslagen, winnaarafstand, deelnemers, tellingen, links en hashes gecontroleerd')
