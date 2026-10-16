import json
from pathlib import Path
from f1_analysis.early_driver_history import parse_atlas, apply_retained, match_driver
from f1_analysis.phase2 import build, collapse_shared_entries


def test_atlas_headers_missing_sentinels_and_unique_names():
    drivers = [{'driver_number': 5, 'name': 'Michael Schumacher', 'code': 'MSC'},
               {'driver_number': 6, 'name': 'Ralf Schumacher', 'code': 'RSC'}]
    body = '<title>Atlas 1995</title><table><form><tr><td>Driver</td><td>Lap 1</td><td></td><td>Lap 2</td></tr><tr><td>Schumacher, M</td><td>1:20.001</td><td>MSC</td><td>999:999</td></tr></form></table>'
    result = parse_atlas(body, drivers)
    assert result['laps'] == [{'driver': 5, 'lap': 1, 'duration': 80.001}]
    assert result['missing_cells'] == 1
    assert match_driver('Schumacher', drivers) is None


def test_retained_overlay_does_not_mutate_original_or_guess_tyres(tmp_path):
    target = tmp_path/'analyses/sources/driver-history-expansion/1971-09.json'
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({'year': 1971, 'round': 9, 'source': {'url': 'https://example.test'},
                                  'accepted_laps': [{'driver': 1, 'lap': 2, 'duration': 84.2}]}))
    payload = {'all_laps': []}
    result, source = apply_retained(tmp_path, 1971, 9, payload)
    assert payload['all_laps'] == []
    assert result['all_laps'][0]['tyre'] == {'compound': 'UNKNOWN', 'age': None}
    assert source['accepted_laps'] == 1


def test_1950_positions_without_times_are_usable_but_no_pace_is_invented(tmp_path):
    event = tmp_path/'analyses/1950/example'; run = event/'runs/one'; run.mkdir(parents=True)
    (event/'latest.json').write_text('{"run":"runs/one"}')
    drivers = [{'driver_number': i, 'name': 'Driver '+str(i), 'code': 'AAA', 'team': 'Team',
                'grid': i, 'lap1_position': i, 'finish': i, 'status': 'Finished',
                'result': {'number_of_laps': 10}} for i in (1, 2)]
    payload = {'drivers': drivers, 'all_laps': [{'driver': 1, 'lap': 5, 'duration': 100}],
               'positions': [{'driver': i, 'lap': lap, 'position': i} for i in (1, 2) for lap in range(1, 11)],
               'race': 'Example', 'laps': 10}
    (run/'overzicht.html').write_text('<script id="dashboard-data">'+json.dumps(payload)+'</script>')
    report = build(tmp_path, end_year=2026)
    assert report['races'] == 1 and report['qualities']['start'] == 2
    assert report['lap_rankings'] == 0 and report['matched_driver_races'] == 0
    assert report['period'] == [1950, 2026]


def test_shared_car_multi_entries_are_preserved_but_never_double_scored():
    entries=[{'race':'1950-7','year':1950,'number':n,'color':'#fff',
              'grid':1,'finish':2,'lap1_position':1,'finished_on_track':True,
              'qualities':{'start':[{'grid':1,'lap1':1}]}} for n in (2, 16)]
    profiles={'a':{'races':entries}}
    collapse_shared_entries(profiles)
    row=profiles['a']['races'][0]
    assert len(profiles['a']['races'])==1
    assert row['shared_car_entries']==entries
    assert row['grid'] is None and row['finished_on_track'] is None
    assert row['qualities']=={} and row['shared_car_ambiguous']
