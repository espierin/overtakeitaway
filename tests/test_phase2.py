from copy import deepcopy
import pytest
from f1_analysis.phase2 import compare_teammates, candidate_cycles, build


def payload(a_pit=3,b_pit=5,a_loss=20,b_loss=25):
    data={'drivers':[{'driver_number':1,'name':'A','code':'AAA','team':'Team'},{'driver_number':2,'name':'B','code':'BBB','team':'Team'}],'laps':12,'all_laps':[],'positions':[],'explorer':{'pit':[{'driver':1,'lap':a_pit},{'driver':2,'lap':b_pit}],'neutral':[],'red':[]}}
    elapsed={1:0,2:0}
    for lap in range(1,13):
        for n,pit,loss in [(1,a_pit,a_loss),(2,b_pit,b_loss)]:
            duration=100+(2 if n==1 and lap==1 else 0)+(loss if lap==pit else 0)
            data['all_laps'].append({'driver':n,'lap':lap,'duration':duration,'tyre':{'compound':'MEDIUM','age':lap},'reasons':[]});elapsed[n]+=duration
        for n in (1,2):data['positions'].append({'driver':n,'lap':lap,'position':1 if elapsed[n]<elapsed[3-n] else 2})
    return data


def test_candidate_register_includes_success_and_failure():
    good,excluded=candidate_cycles(payload());assert len(good)==1 and good[0]['success'] and good[0]['type']=='undercut'
    bad,_=candidate_cycles(payload(a_loss=30));assert len(bad)==1 and not bad[0]['success'] and bad[0]['gain_seconds']<0


def test_pit_outcome_rejects_gaps_neutralisation_and_extra_stops():
    d=payload();d['all_laps']=[r for r in d['all_laps'] if not(r['driver']==1 and r['lap']==2)];assert candidate_cycles(d)[0]==[]
    d=payload();d['explorer']['neutral']=[{'lap':4,'kind':'SC'}];assert candidate_cycles(d)[0]==[]
    d=payload();d['all_laps'][6]['reasons']=['neutralisatie of herstart'];assert candidate_cycles(d)[0]==[]
    d=payload();d['drivers'][0]['pitlane_start']=True;assert candidate_cycles(d)[0]==[]


def test_teammates_require_measured_compounds_and_age():
    d=payload();result,_=compare_teammates(d);assert result[1]['matched_laps']==7;assert result[1]['pace_delta_pct']==-result[2]['pace_delta_pct']
    for row in d['all_laps']:row['tyre']['age']=None
    assert compare_teammates(d)[0][1]['method']=='overlap-mean'
    d=payload()
    for row in d['all_laps']:row['tyre']['compound']='UNKNOWN'
    assert compare_teammates(d)[0][1]['method']=='overlap-mean'


def test_unclean_traffic_laps_are_not_pace_comparisons():
    d=payload();d['all_laps'][-1]['reasons']=['traffic'];result,_=compare_teammates(d);assert 12 not in result[1]['matched_lap_numbers']


@pytest.mark.parametrize('years',[0,78,True,2.5])
def test_invalid_history_scope_is_rejected(tmp_path,years):
    with pytest.raises(ValueError,match='77 seasons'):build(tmp_path,end_year=2026,years=years)


def test_output_budget_rejects_before_writing(tmp_path):
    with pytest.raises(ValueError,match='budget'):build(tmp_path,end_year=2026,max_bytes=1)
    assert not (tmp_path/'analysis-lab.html').exists()


def test_builder_scope_data_relations_and_local_catalogue_link(tmp_path):
    import json
    from pathlib import Path
    root=tmp_path
    (root/'index.html').write_text('<html><div class="catalogue-tools"></div><script id="catalogue-data" type="application/json">{"races":[],"search_drivers":{}}</script></html>')
    for year in (2021,2022,2026):
        event=root/'analyses'/str(year)/'circuit';run=event/'runs/example';run.mkdir(parents=True)
        (event/'latest.json').write_text(json.dumps({'run':'runs/example'}))
        data=payload();data['race']='Test circuit';data['year']=year
        (run/'overzicht.html').write_text('<script id="dashboard-data" type="application/json">'+json.dumps(data)+'</script>')
    report=build(root,end_year=2026,years=5)
    assert report['period']==[2022,2026] and report['races']==2 and report['drivers']==2
    assert report['extra_bytes_upper_bound']<report['max_extra_bytes']
    page=(root/'analysis-lab.html').read_text()
    assert 'data-phase2-entry' not in (root/'index.html').read_text()
    assert '"year":2021' not in page
    assert 'variation_pct' not in page and 'matched_lap_numbers' not in page
    assert 'driver-qualities.js' in page
    assert '2022-circuit' in page and '2026-circuit' in page
    build(root,end_year=2026,years=5)
    assert 'data-phase2-entry' not in (root/'index.html').read_text()


def test_default_history_includes_pre_2007_and_preserves_latest_driver_badge(tmp_path):
    import json
    from bs4 import BeautifulSoup
    for year in (2006,2007,2012,2016,2017,2021,2026):
        event=tmp_path/'analyses'/str(year)/'circuit';run=event/'runs/one';run.mkdir(parents=True)
        (event/'latest.json').write_text(json.dumps({'run':'runs/one'}))
        data=payload();data['race']='Circuit';data['drivers'][0]['display_number']=33 if year<2026 else 1
        data['styles']={'1':{'color':'#111111' if year<2026 else '#222222'}}
        (run/'overzicht.html').write_text('<script id="dashboard-data" type="application/json">'+json.dumps(data)+'</script>')
    report=build(tmp_path,end_year=2026)
    assert report['period']==[1950,2026] and report['races']==7
    data=json.loads(BeautifulSoup((tmp_path/'analysis-lab.html').read_text(),'html.parser').find(id='phase2-data').string)
    driver=next(d for d in data['drivers'] if d['id']=='a')
    assert driver['number']==1 and driver['color']=='#222222'
    assert [r['year'] for r in driver['races']]==[2006,2007,2012,2016,2017,2021,2026]


def test_unmapped_stop_is_not_a_measured_cycle():
    d=payload();d['explorer']['pit']=[{'driver':1,'lap':None}]
    assert candidate_cycles(d)[0]==[]
    d=payload()
    for row in d['all_laps']:row['tyre']['age']=-1
    assert compare_teammates(d)[0][1]['method']=='overlap-mean'


def test_explicit_historical_pitlane_start_is_not_a_numeric_grid_slot(tmp_path):
    import json
    from f1_analysis.phase2 import pitlane_start_numbers
    source=tmp_path/'data/raw/historical/f1db.json';source.parent.mkdir(parents=True)
    source.write_text(json.dumps({'sessions':{'race-results':[
        {'driverNumber':'44','gridPositionText':'PL'},
        {'driverNumber':'33','gridPositionText':'20'}],
        'starting-grid-positions':[{'driverNumber':'3','positionText':'PL'}]}}))
    assert pitlane_start_numbers({'drivers':[{'driver_number':27,'pitlane_start':True}]},tmp_path)=={44,3,27}
    # Both retained gzip sources and current explicit flags carry the same meaning.
    import gzip
    source.with_name('f1db.json.gz').write_bytes(gzip.compress(source.read_bytes()));source.unlink()
    assert pitlane_start_numbers({'drivers':[]},tmp_path)=={44,3}
