from f1_analysis.catalogue_search import race_entries, race_direction, fold, load_reference


def test_reference_matches_date_and_preserves_official_pole():
    reference = {'drivers': {}, 'races': {'2021-1': {'date': '2021-03-28', 'entries': [['max-verstappen', False, False, True, False]]}}}
    row = {'year': 2021, 'round': 1, 'date': '2021-03-28'}
    assert race_entries(row, {}, reference)[0][3] is True
    assert race_entries({**row, 'date': '2021-04-01'}, {}, reference) == []
    reference['races']['2021-1']['circuit'] = 'bahrain'
    assert race_entries({**row, 'date': '2021-04-01', 'circuitId': 'bahrain'}, {}, reference)[0][3] is True


def test_new_data_participation_retirement_and_fastest_lap():
    normalized = {
        'drivers': [{'driver_number': n, 'full_name': name, 'name_acronym': name[:3].upper()} for n, name in [(1, 'Winner'), (2, 'Retired'), (3, 'No Start'), (4, 'Disqualified')]],
        'session_result': [{'driver_number': 1, 'position': 1}, {'driver_number': 2, 'position': 2, 'dnf': True}, {'driver_number': 4, 'dnf': True}],
        'jolpica_results': [{'number': str(n), 'status': status, 'grid': '1', 'FastestLap': {'rank': '1' if n == 1 else '2'}} for n, status in [(1, 'Finished'), (2, 'Engine'), (3, 'Did not start'), (4, 'Disqualified')]]}
    # A scheduled entry in F1DB must not hide results that have just arrived.
    entries = race_entries({'year': 2027, 'round': 1, 'date': '2027-03-01'}, normalized, {'drivers': {}, 'races': {'2027-1': {'date': '2027-03-01', 'entries': []}}})
    assert len(entries) == 3
    assert entries[0][1:] == [True, False, False, True]  # Grid 1 alone does not establish an official pole.
    assert entries[1][2] is True
    assert entries[2][2] is False


def test_historical_reference_has_pre_2004_fastest_laps_and_excludes_dns():
    ref = load_reference('.')
    assert any(e[0] == 'michael-schumacher' and e[4] for e in ref['races']['1994-4']['entries'])
    assert fold('Bélgië') == 'belgie'


def test_direction_uses_historical_layout_and_does_not_confuse_rounds():
    ref = load_reference('.')
    assert race_direction({'year': 1950, 'round': 3, 'date': '1950-05-30'}, {}, ref) == 'anti-clockwise'
    assert race_direction({'year': 2005, 'round': 9, 'date': '2005-06-19'}, {}, ref) == 'clockwise'
    assert race_direction({'year': 1985, 'round': 15, 'date': '1985-10-19'}, {}, ref) == 'clockwise'
    assert race_direction({'year': 1993, 'round': 1, 'date': '1993-03-14'}, {}, ref) == 'anti-clockwise'
    assert race_direction({'year': 2021, 'round': 16, 'date': '2021-10-10', 'circuitId': 'istanbul'}, {}, ref) == 'anti-clockwise'
    assert race_direction({'year': 2021, 'round': 16, 'date': '2021-10-10', 'circuitId': 'unknown-track'}, {}, ref) is None


def test_query_parser_combines_locations_years_and_the_same_driver():
    import subprocess
    from pathlib import Path
    js = Path('src/f1_analysis/catalogue.js').read_text()
    functions = js[js.index('const normalizeSearch='):js.index('function renderSearchHelp()')]
    fixture = r'''
const assert=require('assert');
const countryCodes={Monaco:'MC',Belgium:'BE',Spain:'ES'};
const data={circuits:[
 {circuitId:'monaco',circuitName:'Circuit de Monaco',Location:{locality:'Monte Carlo',country:'Monaco'}},
 {circuitId:'spa',circuitName:'Spa-Francorchamps',Location:{locality:'Spa',country:'Belgium'}},
 {circuitId:'barcelona',circuitName:'Circuit de Catalunya',Location:{locality:'Barcelona',country:'Spain'}}],
 search_drivers:{max:{name:'Max Verstappen',code:'VER'},jos:{name:'Jos Verstappen',code:'VER'},sparken:{name:'Mike Sparken',code:'SPA'}},
 races:[{id:1,year:1995,circuitId:'monaco',direction:'clockwise',search_entries:[['jos',false,true,false,false]]},
 {id:2,year:2021,circuitId:'monaco',direction:'clockwise',search_entries:[['max',true,false,true,true]]},
 {id:3,year:1995,circuitId:'spa',direction:'anti-clockwise',search_entries:[['jos',false,false,false,false]]},
 {id:4,year:1995,circuitId:'barcelona',search_entries:[['jos',false,false,false,false]]}]};
'''
    assertions = r'''
const ids=q=>data.races.filter(compileRaceSearch(q)).map(r=>r.id);
assert.deepEqual(ids('monaco 95'),[1]);
assert.deepEqual(ids('monaco 1995'),[1]);
assert.deepEqual(ids('monaco ver+'),[2]);
assert.deepEqual(ids('monaco verstappen+'),[2]);
assert.deepEqual(ids('jos verstappen+'),[]);
assert.deepEqual(ids('max verstappen'),[2]);
assert.deepEqual(ids('verstappen-'),[1]);
assert.deepEqual(ids('verstappen#'),[2]);
assert.deepEqual(ids('verstappen@'),[2]);
assert.deepEqual(ids('#max verstappen'),[2]);
assert.deepEqual(ids('spa 95'),[3]); // Not SPA the driver, nor Spain.
assert.deepEqual(ids('belgie 1995'),[3]);
assert.deepEqual(ids('belgium 1995'),[3]);
assert.deepEqual(ids('catalun 95'),[4]);
assert.deepEqual(ids('unknown+'),[]);
assert.deepEqual(ids('rechtsom'),[1,2]);
assert.deepEqual(ids('clockwise'),[1,2]);
assert.deepEqual(ids('linksom'),[3]);
assert.deepEqual(ids('anti-clockwise'),[3]);
assert.deepEqual(ids('anti clockwise'),[3]);
assert.deepEqual(ids('counterclockwise'),[3]);
assert.deepEqual(ids('ver+ clockwise'),[2]);
assert.deepEqual(ids('ver+ linksom'),[]);
assert.deepEqual(ids('clockwise linksom'),[]);
'''
    subprocess.run(['node', '-e', fixture + functions + assertions], check=True)
