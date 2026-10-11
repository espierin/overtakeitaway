import pytest
from f1_analysis.cli import canonical_race
from f1_analysis.io import write_json
from f1_analysis.race_navigation import circuit_key
from f1_analysis.catalogue import catalogue_body
from bs4 import BeautifulSoup
import json


def existing(root, label, round_, year=2026):
    base = root / 'analyses' / str(year) / label
    write_json(base / 'latest.json', {'run': 'runs/old'})
    write_json(base / 'runs/old/manifest.json', {'session': {'round': round_}})
    return base


def test_source_change_reuses_race_directory(tmp_path):
    original = existing(tmp_path, 'shanghai-international-circuit', 2)
    data = {'round': 2, 'session': {'year': 2026, 'circuit_short_name': 'Shanghai'}}
    assert canonical_race(tmp_path, data) == original


def test_distinct_rounds_at_same_circuit_do_not_merge(tmp_path):
    existing(tmp_path, 'first-sakhir-race', 1)
    data = {'round': 2, 'session': {'year': 2026, 'circuit_short_name': 'Sakhir — Second'}}
    assert canonical_race(tmp_path, data) == tmp_path / 'analyses/2026/sakhir-second'


def test_other_season_is_not_reused(tmp_path):
    existing(tmp_path, 'shanghai-international-circuit', 2, year=2025)
    data = {'round': 2, 'session': {'year': 2026, 'circuit_short_name': 'Shanghai'}}
    assert canonical_race(tmp_path, data) == tmp_path / 'analyses/2026/shanghai'


def test_duplicate_rounds_fail_explicitly(tmp_path):
    existing(tmp_path, 'shanghai', 2)
    existing(tmp_path, 'shanghai-international-circuit', 2)
    with pytest.raises(ValueError, match='Meerdere bestaande'):
        canonical_race(tmp_path, {'round': 2, 'session': {'year': 2026, 'circuit_short_name': 'Shanghai'}})


def test_same_circuit_across_timing_sources(tmp_path):
    url = 'https://en.wikipedia.org/wiki/Shanghai_International_Circuit'
    openf1 = tmp_path / 'openf1'
    fastf1 = tmp_path / 'fastf1'
    write_json(openf1 / 'data/normalized/input.json', {'jolpica_circuit': {'url': url}})
    write_json(fastf1 / 'data/normalized/input.json', {'session': {'jolpica_race': {'Circuit': {'url': url}}}})
    assert circuit_key(openf1, {'gp': 'Shanghai'}) == circuit_key(fastf1, {'gp': 'Shanghai International Circuit'})


def test_new_circuit_has_current_year_and_no_unrelated_layout(tmp_path):
    circuit={'circuitId':'madring','circuitName':'Madring','url':'https://en.wikipedia.org/wiki/Madring',
             'Location':{'lat':'40.46528','long':'-3.61528','locality':'Madrid','country':'Spain'}}
    write_json(tmp_path/'assets/maps/circuits.json', {'MRData':{'CircuitTable':{'Circuits':[circuit]}}})
    write_json(tmp_path/'assets/maps/land.geojson', {'features':[]})
    write_json(tmp_path/'assets/maps/historical/circuits.json',
               [{'id':'jarama','latitude':40.6171,'longitude':-3.58558,'layouts':[]}])
    row={'year':2026,'path':'2026/madring/runs/one','gp':'Madring','meeting':'Spanish Grand Prix','race_date':'2026-09-13'}
    write_json(tmp_path/'analyses'/row['path']/'data/normalized/input.json', {'jolpica_circuit':circuit})
    body=catalogue_body(tmp_path,[row],'analyses/')
    data=json.loads(BeautifulSoup(body,'html.parser').find(id='catalogue-data').string)
    assert '2026–2026 · Formula 1' in body
    assert data['races'][0]['background']=='assets/f1-banner-v3.png'
    assert 'track_image' not in data['races'][0]
