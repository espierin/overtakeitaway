from copy import deepcopy
import json
import pytest
from f1_analysis.pace_comparison import analyse, VERSION
from f1_analysis.phase2 import build


def race(a_laps=12,b_laps=12,a_dnf=False,b_dnf=False,tyres=True):
    p={'drivers':[{'driver_number':1,'name':'Driver A','code':'AAA','team':'Team','result':{'number_of_laps':a_laps,'dnf':a_dnf}}, {'driver_number':2,'name':'Driver B','code':'BBB','team':'Team','result':{'number_of_laps':b_laps,'dnf':b_dnf}}], 'all_laps':[], 'explorer':{'pit':[],'neutral':[],'red':[]}}
    for n,count in [(1,a_laps),(2,b_laps)]:
        for lap in range(1,count+1):p['all_laps'].append({'driver':n,'lap':lap,'duration':90 if n==1 else 92,'tyre':{'compound':'MEDIUM' if tyres else 'UNKNOWN','age':lap-1 if tyres else None},'reasons':[]})
    return p


def test_retirement_keeps_the_common_valid_overlap_and_identifies_limiting_driver():
    p=race(a_laps=8,a_dnf=True);original=deepcopy(p);r,_=analyse(p)
    assert p==original
    assert r[1]['method']=='matched-median' and r[1]['matched_laps']==7
    assert r[1]['lap_range']==[2,8]
    assert r[1]['retirement_limited'] is True
    assert r[1]['limiting_drivers']==['Driver A'] and r[1]['limiting_laps']==8
    assert r[2]['limiting_drivers']==r[1]['limiting_drivers']
    assert r[1]['pace_delta_pct']==-r[2]['pace_delta_pct']
    assert r[1]['mean_lap_seconds']==90 and r[1]['teammate_mean_lap_seconds']==92


def test_short_matching_overlap_compares_means_as_one_point_without_quartiles():
    p=race(a_laps=4,a_dnf=True);r,_=analyse(p)
    assert r[1]['method']=='matched-mean' and r[1]['matched_laps']==3
    assert r[1]['pace_delta_pct']==pytest.approx(200*(90-92)/(90+92),abs=1e-5)
    assert r[1]['delta_q25'] is None and r[1]['delta_q75'] is None
    assert r[1]['retirement_limited'] is True


def test_unknown_tyres_use_explicitly_labelled_common_clean_mean_not_other_laps():
    p=race(a_laps=5,b_laps=12,tyres=False)
    next(l for l in p['all_laps'] if l['driver']==2 and l['lap']==12)['duration']=9000
    r,_=analyse(p)
    assert r[1]['method']=='overlap-mean' and r[1]['matched_laps']==4
    assert r[1]['teammate_mean_lap_seconds']==92
    assert not r[1]['retirement_limited'] # Fewer laps alone is not proof of a DNF.


def test_no_overlap_and_excluded_laps_are_not_averaged_or_filled():
    p=race(a_laps=1,a_dnf=True);assert analyse(p)[0]=={}
    p=race(a_laps=4);p['explorer']['pit']=[{'driver':1,'lap':2}]
    p['explorer']['neutral']=[{'lap':4,'kind':'SC'}];assert analyse(p)[0]=={}
    p=race(a_laps=4);p['all_laps']=[l for l in p['all_laps'] if l['driver']!=1 or l['lap']==1]
    assert analyse(p)[0]=={}


def test_both_retirements_use_earliest_distance_and_historical_statuses():
    p=race(a_laps=7,b_laps=5,a_dnf=True,b_dnf=True);r,_=analyse(p)
    assert r[1]['limiting_drivers']==['Driver B'] and r[1]['retired_drivers']==['Driver A','Driver B']
    p=race(a_laps=8,a_dnf=True)
    for d,status in zip(p['drivers'],['Engine','Finished']):d['result'].pop('dnf');d['status']=status
    assert analyse(p)[0][1]['retirement_limited']
    p['drivers'][0]['status']='Disqualified'
    assert not analyse(p)[0][1]['retirement_limited']


def test_mean_fallback_is_ratio_of_means_and_not_mean_of_percentages():
    p=race(a_laps=3,b_laps=3)
    for r in p['all_laps']:
        if r['lap']>1:r['duration']=({1:[50,150],2:[100,100]})[r['driver']][r['lap']-2]
    r,_=analyse(p)
    assert r[1]['mean_lap_seconds']==r[1]['teammate_mean_lap_seconds']==100
    assert r[1]['pace_delta_pct']==0
    assert r[1]['delta_q25'] is None


def test_new_comparisons_survive_source_free_compact_rebuild(tmp_path):
    import re
    p=race(a_laps=4,a_dnf=True);p['race']='Test';event=tmp_path/'analyses/2026/test';run=event/'runs/test';run.mkdir(parents=True)
    (event/'latest.json').write_text(json.dumps({'run':'runs/test'}));(run/'overzicht.html').write_text('<script id="dashboard-data">'+json.dumps(p)+'</script>')
    def data():return json.loads(re.search(r'id="phase2-data"[^>]*>(.*?)</script>',(tmp_path/'analysis-lab.html').read_text(),re.S)[1])
    build(tmp_path,end_year=2026);first=data();build(tmp_path,end_year=2026);second=data()
    assert first['drivers']==second['drivers']
    assert second['races'][0]['pace_comparison_version']==VERSION
    assert second['drivers'][0]['races'][0]['comparison']['retirement_limited']


def test_missing_end_timing_identifies_the_actual_data_limit_not_an_unobserved_finish():
    p=race();p['all_laps']=[r for r in p['all_laps'] if r['driver']!=1 or r['lap']<=6]
    r,_=analyse(p)
    assert r[1]['limiting_drivers']==['Driver A']
    assert r[1]['limiting_laps']==6 and r[1]['limiting_basis']=='timing-extent'
    p['drivers'][0]['result']['dns']=True
    assert analyse(p)[0]=={}


def test_inconsistent_classified_lap_count_is_not_reported_as_the_timing_limit():
    p=race();p['drivers'][0]['result']['number_of_laps']=11
    r,_=analyse(p)
    assert r[1]['limiting_laps']==12 and r[1]['limiting_basis']=='timing-extent'
    assert r[1]['lap_range'][1]<=r[1]['limiting_laps']
