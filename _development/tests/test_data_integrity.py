"""Build regressions: preserve real source observations across the new loading layout."""
from pathlib import Path
import hashlib
import json
import re
import gzip

ROOT=Path(__file__).resolve().parents[2]


def read_script(path):
    return json.loads(path.read_text().split('=',1)[1].rstrip(';\n'))


def test_all_original_driver_observations_survive_partitioning():
    from f1_analysis.driver_release import source_html
    source=source_html(ROOT)
    old=json.loads(re.search(r'<script[^>]*id=["\']phase2-data["\'][^>]*>(.*?)</script>',source,re.S)[1])
    new=read_script(ROOT/'_development/data/profiles.js')
    assert {d['id'] for d in old['drivers']}=={d['id'] for d in new['drivers']}
    columns=new['driver_race_columns'];groups={}
    for d in new['drivers']:
        if d['detail_group'] not in groups:
            groups[d['detail_group']]=read_script(ROOT/'_development/data/details'/f"{d['detail_group']}.js")
        extras=dict(groups[d['detail_group']][d['id']]);rows=[]
        for packed in d['races']:
            row=dict(zip(columns,packed));extra=extras[row['race']]
            q={**row['qualities'],**extra.get('qualities',{})};row.update(extra);row['qualities']=q;rows.append(row)
        d['races']=rows
    current={d['id']:d for d in new['drivers']}
    count=0;ranks=0
    for d in old['drivers']:
        rows={r['race']:r for r in current[d['id']]['races']}
        assert len(rows)==len(d['races'])
        for original in d['races']:
            rebuilt=rows[original['race']];count+=1
            for key,value in original.items():
                if key=='qualities':
                    for kind,observations in value.items():assert rebuilt[key][kind]==observations
                elif key=='lap_rankings':
                    assert len(value)==len(rebuilt[key])
                    for a,b in zip(value,rebuilt[key]):
                        assert a[:4]==b[:4]
                        assert a[4]==b[4]&~256
                        ranks+=1
                else:
                    assert rebuilt.get(key)==value,(d['id'],original['race'],key)
    assert count==26157
    assert ranks==639012


def test_strategy_clocks_and_every_original_cycle_survive():
    from f1_analysis.driver_release import source_html
    source=source_html(ROOT)
    old=json.loads(re.search(r'<script[^>]*id=["\']phase2-data["\'][^>]*>(.*?)</script>',source,re.S)[1])
    strategy=read_script(ROOT/'_development/data/strategy.js')
    cols=strategy['cycles']['columns'];new=[dict(zip(cols,row)) for row in strategy['cycles']['rows']]
    assert len(new)==len(old['cycles'])
    for a,b in zip(old['cycles'],new):
        for key,value in a.items():assert b[key]==value
    for race in old['races']:
        assert strategy['programs'][race['id']]==race.get('pit_programmes',{}).get('entries',[])


def test_original_pages_and_assets_are_unchanged():
    manifest=json.loads((ROOT/'_development/clone-manifest.json').read_text())
    for source in list(manifest['pages'].values())+list(manifest['assets'].values()):
        from f1_analysis.driver_release import is_promoted, render, source_html
        if source['source']=='analysis-lab.html' and is_promoted(ROOT):
            assert (ROOT/'analysis-lab.html').read_text()==render(ROOT)
            body=source_html(ROOT).encode()
        else:body=(ROOT/source['source']).read_bytes()
        assert hashlib.sha256(body).hexdigest()==source['source_sha256']


def test_delivery_stays_within_budget_and_does_not_enable_unvalidated_forecasts():
    registry=json.loads((ROOT/'_development/build-report.json').read_text())
    assert registry['bytes']<=64_000_000
    model=read_script(ROOT/'_development/data/models.js')
    assert model['forecast']['public_forecast_enabled'] is False
    assert model['forecast']['passes_prospective'] is False
    assert all(0<=e['target']<=1 for e in model['forecast']['experiments'])


def test_every_compressed_download_is_lossless_and_matches_its_ledger_hash():
    registry=json.loads((ROOT/'_development/build-report.json').read_text())
    for record in registry['files']:
        base=ROOT/'_development/data'/record['name']
        payload=gzip.decompress(base.with_suffix('.json.gz').read_bytes())
        assert len(payload)==record['bytes']
        assert hashlib.sha256(payload).hexdigest()==record['sha256']
        assert json.loads(payload)==read_script(base.with_suffix('.js'))


def test_unresolved_grid_and_finish_disagreements_never_enter_phase_scores():
    data=read_script(ROOT/'_development/data/profiles.js')
    counts={'grid':0,'finish':0}
    for driver in data['drivers']:
        for packed in driver['races']:
            row=dict(zip(data['driver_race_columns'],packed))
            for key,value in row.get('source_conflicts',{}).items():
                counts[key]+=1
                assert row[key]==value['retained']
                assert value['retained']!=value['f1db']
                assert row['start_eligible' if key=='grid' else 'race_eligible'] is False
    assert counts=={'grid':481,'finish':45}
    registry=json.loads((ROOT/'_development/build-report.json').read_text())
    assert registry['unresolved_source_conflicts']==counts


def test_shared_source_car_does_not_become_an_individual_skill_observation():
    data=read_script(ROOT/'_development/data/profiles.js');n=0
    for driver in data['drivers']:
        for packed in driver['races']:
            row=dict(zip(data['driver_race_columns'],packed))
            if row['source_shared_car']:
                n+=1
                assert row['start_eligible'] is False
                assert row['race_eligible'] is False
    assert n>0


def test_confirmed_pitlane_starts_cannot_be_scored_as_grid_starts():
    data=read_script(ROOT/'_development/data/profiles.js');n=0
    for driver in data['drivers']:
        for packed in driver['races']:
            row=dict(zip(data['driver_race_columns'],packed))
            if row['pitlane_start'] or row['source_pitlane_start']:
                n+=1
                assert row['start_eligible'] is False
    assert n>0


def test_missing_old_pitlane_flag_is_recovered_from_explicit_source_record():
    data=read_script(ROOT/'_development/data/profiles.js')
    driver=next(d for d in data['drivers'] if d['id']=='alexander-albon')
    rows=[dict(zip(data['driver_race_columns'],row)) for row in driver['races']]
    row=next(r for r in rows if r['race']=='2024-10')
    assert row['pitlane_start'] is not True  # The original missing flag remains intact.
    assert row['source_pitlane_start'] is True
    assert row['start_eligible'] is False


def test_post_race_disqualification_is_not_misreported_as_not_starting():
    data=read_script(ROOT/'_development/data/profiles.js')
    driver=next(d for d in data['drivers'] if d['id']=='martin-brundle')
    facts=read_script(ROOT/'_development/data/facts'/f"{driver['detail_group']}.js")
    columns=read_script(ROOT/'_development/data/facts.js')['race_columns']
    row=next(dict(zip(columns,r)) for r in facts['martin-brundle']['races'] if r[columns.index('race')]=='1984-1')
    assert row['status']=='DSQ'
    assert row['started'] is True  # Retained lap evidence confirms participation.
