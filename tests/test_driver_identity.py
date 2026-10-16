from copy import deepcopy
import pytest
from f1_analysis.driver_identity import identity, display_name, merge_profiles


def test_known_name_orders_share_one_id_without_merging_unrelated_drivers():
    for name in ('Guanyu Zhou','ZHOU Guanyu','Zhou Guanyu','guanyu-zhou','zhou-guanyu'):
        assert identity(name)=='guanyu-zhou'
    assert display_name('Guanyu Zhou')=='Zhou Guanyu'
    assert identity('Michael Schumacher')!=identity('Mick Schumacher')
    assert identity('Alexander Wurz')=='alexander-wurz'


def data():
    return {'drivers':[
        {'id':'guanyu-zhou','name':'Guanyu Zhou','number':24,'code':'ZHO','color':'old','races':[{'race':'2022-1','year':2022,'number':24,'color':'old','lap_rankings':[[1,8,20]],'finish':16}]},
        {'id':'zhou-guanyu','name':'ZHOU Guanyu','number':24,'code':'ZHO','color':'new','races':[{'race':'2024-1','year':2024,'number':24,'color':'new','finish':11,'retirement_evidence':{'id':'2024-1:zhou-guanyu'}}]},
        {'id':'valtteri-bottas','name':'Valtteri Bottas','races':[{'race':'2024-1','year':2024,'comparison':{'teammate':'ZHOU Guanyu','retired_drivers':['Guanyu Zhou']}}]}
    ],'races':[{'id':'2022-1','date':'2022-03-20'},{'id':'2024-1','date':'2024-03-02'}],
        'cycles':[{'driver':'zhou-guanyu','opponent':'valtteri-bottas'}]}


def test_merge_preserves_observations_and_updates_references_and_old_links():
    d=data();before=deepcopy(d);merge_profiles(d)
    p=next(p for p in d['drivers'] if p['id']=='guanyu-zhou')
    assert len(d['drivers'])==2
    assert p['name']=='Zhou Guanyu' and p['color']=='new'
    assert [r['race'] for r in p['races']]==['2022-1','2024-1']
    assert p['races'][0]==before['drivers'][0]['races'][0]
    assert p['races'][1]['finish']==11
    assert p['races'][1]['retirement_evidence']['id']=='2024-1:guanyu-zhou'
    assert d['cycles'][0]['driver']=='guanyu-zhou'
    other=next(p for p in d['drivers'] if p['id']=='valtteri-bottas')
    assert other['races'][0]['comparison']['teammate']=='Zhou Guanyu'
    assert d['driver_aliases']['zhou-guanyu']=='guanyu-zhou'
    once=deepcopy(d);merge_profiles(d);assert d==once


def test_duplicate_race_is_counted_once_and_conflicting_measurements_raise():
    d=data();duplicate=deepcopy(d['drivers'][0]['races'][0]);d['drivers'][1]['races'].append(duplicate)
    merge_profiles(d)
    assert len(next(p for p in d['drivers'] if p['id']=='guanyu-zhou')['races'])==2
    d=data();duplicate=deepcopy(d['drivers'][0]['races'][0]);duplicate['finish']=2;d['drivers'][1]['races'].append(duplicate)
    with pytest.raises(ValueError,match='Conflicting observations'):merge_profiles(d)
