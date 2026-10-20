"""Check the career PCA against NumPy and the archived feature provenance."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which('node') or '/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


def run_js(code):
    script="const fs=require('node:fs'),vm=require('node:vm'),c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync('_development/assets/goat-pca.js','utf8'),c);const api=c.window.goatCareerPCA;"+code
    return json.loads(subprocess.check_output([NODE, '-e', script], cwd=ROOT, text=True))


def test_standardized_pca_matches_numpy_and_is_order_invariant():
    result=run_js("const rows=Array.from({length:27},(_,i)=>({driver:'d'+i,values:[Math.sin(i),i%7,Math.cos(i/3),i*i],n:i+1}));console.log(JSON.stringify({rows,a:api.project(rows),b:api.project([...rows].reverse())}));")
    matrix=np.array([r['values'] for r in result['rows']])
    z=(matrix-matrix.mean(axis=0))/matrix.std(axis=0)
    _,s,vt=np.linalg.svd(z,full_matrices=False)
    model=result['a']
    np.testing.assert_allclose(model['explained'],(s*s/(s*s).sum())[:2],atol=1e-10)
    for i in range(2):
        assert abs(float(np.dot(model['loadings'][i],vt[i])))>1-1e-10
    by_id={p['driver']:p for p in result['b']['points']}
    for point in model['points']:
        np.testing.assert_allclose([point['x'],point['y']],[by_id[point['driver']]['x'],by_id[point['driver']]['y']],atol=1e-10)


def test_missing_is_not_imputed_and_zero_remains_measured():
    result=run_js("const rows=Array.from({length:10},(_,i)=>({driver:'d'+i,values:[i,i*i,i%3,Math.sin(i)],n:i+1}));rows.push({driver:'missing',values:[null,1,1,1],n:2});console.log(JSON.stringify(api.project(rows)));")
    assert len(result['points'])==10
    assert result['unplaced'][0]['driver']=='missing'
    assert result['points'][0]['values'][0]==0


def test_real_roster_has_one_representation_per_driver_and_no_season_points():
    result=run_js("const d=JSON.parse(require('node:zlib').gunzipSync(fs.readFileSync('_development/data/profiles.json.gz')));for(const x of d.drivers)x.races=x.races.map(r=>Object.fromEntries(d.driver_race_columns.map((k,i)=>[k,r[i]])));const a=JSON.parse(require('node:zlib').gunzipSync(fs.readFileSync('_development/data/goat-metrics.json.gz'))),records=api.summarize(d,{archive:a}),m=api.project(records);console.log(JSON.stringify({total:d.drivers.length,records,points:m.points,unplaced:m.unplaced}));")
    assert len(result['records'])==result['total']==817
    ids=[r['driver'] for r in result['points']+result['unplaced']]
    assert len(ids)==len(set(ids))==817
    assert all('year' not in p for p in result['points'])
    max_profile=next(r for r in result['records'] if r['driver']=='max-verstappen')
    assert max_profile['values'][7]==68.93518518518518
    assert max_profile['values'][9]==3
    assert max_profile['values'][10]==-.40569
    assert max_profile['values'][11]==93.75
    assert max_profile['values'][8] is None  # Unsupported curve balance is not zero.


def test_archive_has_817_lossless_records_and_verified_sources():
    directory=ROOT/'_development/data/goat-metrics/1950-2026'
    index=json.loads((directory/'index.json').read_text())
    manifest_path=directory/index['manifest']
    manifest=json.loads(manifest_path.read_text())
    assert len(manifest['drivers'])==817
    for entry in manifest['drivers']:
        compressed=(manifest_path.parent/entry['file']).read_bytes()
        assert hashlib.sha256(compressed).hexdigest()==entry['sha256']
        row=json.loads(gzip.decompress(compressed))
        assert row['driver']==entry['driver'] and row['period']==[1950,2026]
        for metric in row['features'].values():
            assert metric['value'] is None or np.isfinite(metric['value'])
    for filename,expected in manifest['inputs'].items():
        assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==expected,filename


def test_archived_pit_curves_and_delivery_keep_original_values_and_pca_parameters():
    directory=ROOT/'_development/data/goat-metrics/1950-2026'
    index=json.loads((directory/'index.json').read_text())
    manifest_path=directory/index['manifest']
    manifest=json.loads(manifest_path.read_text())
    delivery={d['driver']:d for d in manifest['delivery']['files']}
    assert len(delivery)==817
    for entry in manifest['drivers']:
        record=json.loads(gzip.decompress((manifest_path.parent/entry['file']).read_bytes()))
        curve=record['pit_curve']
        measured=[o['value'] for g in curve['groups'] for o in g['observations']]
        assert len(measured)==curve['measured']==record['features']['pit_race_gain']['races']
        if measured:
            np.testing.assert_allclose(record['features']['pit_race_gain']['value'],np.median(measured),rtol=1e-14,atol=1e-12)
            assert curve['fit']['runs']
        else:
            assert curve['fit']['runs']==[]
        assert curve['axis']['y']['transform']=='signed_log1p'
        path=manifest_path.parent/'delivery'
        compressed=(path/(record['driver']+'.json.gz')).read_bytes()
        script=(path/(record['driver']+'.js')).read_bytes()
        hashes=delivery[record['driver']]
        assert hashlib.sha256(compressed).hexdigest()==hashes['gzip_sha256']
        assert hashlib.sha256(script).hexdigest()==hashes['script_sha256']
        payload=json.loads(gzip.decompress(compressed))
        assert payload['record']==record
        assert payload['curves']['pit_balance']==curve
        if record['driver']=='george-russell':
            assert record['features']['pit_race_gain']['value']==3.50325
            assert record['features']['pit_cycle_gain']['value']==.0605
            assert record['features']['pit_cycle_gain']['n']==200


def test_three_nearest_use_actual_pca_distance_exclude_self_and_keep_ties_stable():
    result=run_js("vm.runInContext(fs.readFileSync('_development/assets/driver-pca-neighbours.js','utf8'),c);const near=c.window.driverPCANeighbours.nearest;const m={available:true,points:[{driver:'own',x:0,y:0},{driver:'far',x:9,y:1},{driver:'b',x:1,y:0},{driver:'a',x:0,y:1},{driver:'overlap',x:0,y:0}]};const before=JSON.stringify(m);console.log(JSON.stringify({rows:near(m,'own'),missing:near(m,'unknown'),unavailable:near({...m,available:false},'own'),unchanged:before===JSON.stringify(m)}));")
    assert [r['driver'] for r in result['rows']] == ['overlap','a','b']
    assert [r['distance'] for r in result['rows']] == [0,1,1]
    assert result['missing'] == result['unavailable'] == []
    assert result['unchanged']
