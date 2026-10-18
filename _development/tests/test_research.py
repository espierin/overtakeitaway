from copy import deepcopy
from datetime import date, timedelta
import numpy as np
import pytest

from metrics import annotate_context, trend_regularity, network_model, pca_profiles, standardize
from forecast import evaluate, score_archive
import json


def starts():
    return [{'phase':'start','layout':'monza-1','field':20,'origin':2,'outcome':2,
             'driver':'peer-'+str(i%3),'race':'ref-'+str(i),'year':2000+i%5} for i in range(12)]


def test_reference_excludes_driver_even_with_many_extreme_starts():
    rows=starts()+[{'phase':'start','layout':'monza-1','field':20,'origin':2,'outcome':1,
                   'driver':'own','race':'own-'+str(i),'year':2002} for i in range(20)]
    annotate_context(rows)
    own=rows[-1]['reference']
    assert own['expected']==2
    assert own['advantage']==1
    assert own['superiority']==100
    assert own['n']==12


@pytest.mark.parametrize('change',[{'field':22},{'layout':'monza-2'},{'phase':'race'},{'origin':1},{'year':2030}])
def test_incompatible_context_is_not_filled(change):
    own=dict(starts()[0],driver='own',race='own')
    own.update(change);rows=starts()+[own];annotate_context(rows)
    assert own['reference'] is None


def test_common_weights_remove_the_advantage_of_different_career_opportunities():
    observations=[]
    for driver,counts,values in [('a',[18,2],[.4,1.2]),('b',[2,18],[.2,1.])]:
        for context,(n,value) in enumerate(zip(counts,values)):
            observations.extend({'driver':driver,'context':str(context),'race':f'{driver}-{context}-{i}',
                                 'reference':{'advantage':value}} for i in range(n))
    own={d:np.mean([o['reference']['advantage'] for o in observations if o['driver']==d]) for d in ['a','b']}
    assert own['a']<own['b']
    result=standardize(observations,['a','b'])
    assert result[0]['advantage']==pytest.approx(.8)
    assert result[1]['advantage']==pytest.approx(.6)
    assert result[0]['contexts']==result[1]['contexts']==2


def test_many_lap_points_from_one_race_do_not_supply_two_independent_races():
    observations=[{'driver':d,'context':'same','race':'single-'+d,'reference':{'advantage':1}}
                  for d in ['a','b'] for _ in range(100)]
    assert all(r['advantage'] is None for r in standardize(observations,['a','b']))


def test_regular_trend_does_not_count_gradual_degradation_as_inconsistency():
    linear=[(i,90+.2*i) for i in range(3,20)]
    assert trend_regularity(linear)['value'] == 0
    noisy=[(i,t+[-1,0,1,2,-2][i%5]) for i,t in linear]
    assert trend_regularity(noisy)['value'] > .1
    assert trend_regularity(linear[:5]) is None


def edges(n=60):
    start=date(2000,1,1)
    return [{'a':'a' if i%2 else 'c','b':'b' if i%2 else 'd',
             'delta':1.,'weight':1.,'date':(start+timedelta(days=i)).isoformat(),
             'race':str(i),'year':2000} for i in range(n)]


def test_network_does_not_rank_disconnected_components():
    model=network_model(edges())
    assert model['components']==2
    assert model['drivers']['a']['component']!=model['drivers']['c']['component']
    assert model['drivers']['a']['effect']>model['drivers']['b']['effect']


def test_future_connection_is_not_used_to_identify_heldout_pair():
    rows=edges()
    for row in rows[48:]:row.update(a='b',b='c')
    model=network_model(rows)
    assert model['components']==1
    assert model['validation']['test_pairs']==0
    assert model['validation']['passes'] is False


def test_pca_is_exploratory_with_block_stability_and_no_imputation():
    rows=[{'driver':str(i),'year':2000+i//4,'values':[i,np.sin(i),i%4]} for i in range(20)]
    result=pca_profiles(rows)
    assert result['available'] is True
    assert result['status']=='exploratory-descriptive-not-ranking'
    assert result['stability']['draws']==200
    assert pca_profiles(rows[:5])['available'] is False


def test_future_profiles_do_not_change_pca_training_scale_or_axes():
    rows=[{'driver':str(i),'year':2000+i//4,'values':[i,np.sin(i),i%4]} for i in range(20)]
    first=pca_profiles(rows)
    changed=deepcopy(rows)
    for row in changed:
        if row['year']==2004:row['values']=[x*1000 for x in row['values']]
    second=pca_profiles(changed)
    assert first['training']['through']==2003
    assert first['training']==second['training']
    assert first['loadings']==second['loadings']


def test_forecast_features_are_unchanged_by_the_race_being_predicted():
    races=[{'id':str(i),'date':f'2024-{i//28+1:02d}-{i%28+1:02d}','year':2024,'layout':'x'} for i in range(12)]
    records=[{'race':str(i),'started':True,'classification_order':j+1,'shared':False,'driver':str(j),
              'team_id':str(j//2)} for i in range(12) for j in range(8)]
    first=evaluate(races,records)
    changed=deepcopy(records)
    for row in changed:
        if row['race']=='11':row['classification_order']=9-row['classification_order']
    second=evaluate(races,changed)
    a=[e['features'] for e in first['experiments'] if e['race']=='11']
    b=[e['features'] for e in second['experiments'] if e['race']=='11']
    assert a==b
    assert all(0<=e['target']<=1 for e in first['experiments'])
    assert first['public_forecast_enabled'] is False


def test_shared_drives_are_not_normalized_into_personal_forecasts():
    races=[{'id':str(i),'date':f'2024-01-{i+1:02d}','year':2024,'layout':'x'} for i in range(10)]
    records=[{'race':str(i),'started':True,'classification_order':j+1,'shared':j==2,'driver':str(j),
              'team_id':str(j//2)} for i in range(10) for j in range(8)]
    result=evaluate(races,records)
    assert all(e['driver']!='2' for e in result['experiments'])
    assert all(0<=e['target']<=1 for e in result['experiments'])


def test_prospective_archive_preserves_snapshot_and_scores_only_pre_race(tmp_path):
    event={'year':'2026','round':'18','date':'2026-10-25','time':'20:00'}
    forecast={'event':event,'issued_at':'2026-10-17T04:00:00+00:00',
              'drivers':[{'driver':str(i),'win':.2,'podium':.6} for i in range(5)]}
    path=tmp_path/'2026-18-pre-weekend.json'
    path.write_text(json.dumps(forecast));original=path.read_bytes()
    assert score_archive(tmp_path,[])['pending'][0]['reason']=='race_not_in_retained_results'
    records=[{'race':'2026-18','started':True,'shared':False,'driver':str(i),'position':i+1} for i in range(5)]
    result=score_archive(tmp_path,records)
    assert result['evaluated'][0]['win_brier']==pytest.approx(.16)
    assert result['passes'] is False
    assert path.read_bytes()==original
    forecast['issued_at']='2026-10-25T21:00:00+00:00';path.write_text(json.dumps(forecast))
    assert score_archive(tmp_path,records)['pending'][0]['reason']=='not_a_verified_pre_race_snapshot'


def test_prospective_archive_rejects_unmatched_roster(tmp_path):
    forecast={'event':{'year':'2026','round':'18','date':'2026-10-25','time':'20:00'},
              'issued_at':'2026-10-17T04:00:00+00:00','drivers':[{'driver':'a','win':1,'podium':1}]}
    (tmp_path/'2026-18-pre-weekend.json').write_text(json.dumps(forecast))
    records=[{'race':'2026-18','started':True,'shared':False,'driver':'b','position':1}]
    assert score_archive(tmp_path,records)['pending'][0]['reason']=='roster_assumption_did_not_match'
