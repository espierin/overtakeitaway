from collections import defaultdict
import pytest
from f1_analysis.archive import Archive, seconds
from f1_analysis.io import write_json,read_json
from f1_analysis.render import update_index


def test_duration_null_and_fractional_seconds():
    assert seconds('') is None
    assert seconds('00:01:16.290') == pytest.approx(76.29)
    assert seconds('02:13:23.6') == pytest.approx(8003.6)


def archive_fixture():
    a=object.__new__(Archive)
    a.tables={'season':{'s':{'year':'1950'}},'round':{'r':{'season_id':'s','circuit_id':'c','number':'1','name':'British Grand Prix','date':'1950-05-13','wikipedia':'https://example.org/r'}},
              'circuit':{'c':{'name':'Silverstone','wikipedia':'https://example.org/c'}},'roundentry':{},'teamdriver':{},'driver':{},'team':{'t':{'id':'t','name':'Example','primary_color':'#FF0000'}}}
    session={'id':'q','round_id':'r','scheduled_laps':'70'}
    a.entries=defaultdict(list);a.laps=defaultdict(list);a.pits=defaultdict(list)
    for i in ['a','b']:
        a.tables['roundentry'][i]={'car_number':'10','team_driver_id':i}
        a.tables['teamdriver'][i]={'driver_id':i,'team_id':'t'}
        a.tables['driver'][i]={'id':i,'forename':i,'surname':'Driver','wikipedia':'https://example.org/d'}
        a.entries['q'].append({'id':i,'round_entry_id':i,'grid':'0','position':'10','is_classified':'t','detail':'+6 Laps','laps_completed':'64','points':'0','time':''})
    return a,session


def test_shared_car_entries_stay_separate_and_unknown_values_stay_unknown():
    a,s=archive_fixture();data=a.race(s)
    assert len(data['drivers'])==2
    assert len({d['id'] for d in data['drivers']})==2
    assert [d['number'] for d in data['drivers']]==[10,10]
    assert all(d['grid'] is None and d['color'] is None for d in data['drivers'])
    assert data['lap_records']==0 and data['coverage_label']=='Uitslagenarchief'
    assert any('meermaals' in w for w in data['warnings'])


def test_lap_timing_and_pit_durations_are_not_overtakes():
    a,s=archive_fixture()
    a.laps['a']=[{'number':'1','position':'2','time':'00:01:16.2','is_deleted':'f'}]
    a.pits['a']=[{'number':'1','lap_number':1,'local_timestamp':'15:01:00','duration':'00:00:24.4'}]
    data=a.race(s)
    assert data['lap_records']==1 and data['pit_records']==1
    assert data['drivers'][0]['laps'][0]['seconds']==76.2
    assert 'overtakes' not in data
    assert 'pitstops' in data['coverage_label']


def test_index_catalogue_has_seasons_and_keeps_latest_pointer_only(tmp_path):
    for y in [1950,1951,2025]:
        base=tmp_path/'analyses'/str(y)/'example';run=base/'runs/new';run.mkdir(parents=True)
        (run/'overzicht.html').write_text('ok')
        write_json(run/'manifest.json',{'input':{'year':y,'gp':'Example'},'session':{'date_start':f'{y}-05-13'},'created_at':'now','status':'gedeeltelijk'})
        write_json(base/'latest.json',{'run':'runs/new'})
    update_index(tmp_path)
    rows=read_json(tmp_path/'analyses/index.json');assert len(rows)==3
    root=(tmp_path/'index.html').read_text();inner=(tmp_path/'analyses/index.html').read_text()
    import re,json
    payload=json.loads(re.search(r'<script id="catalogue-data" type="application/json">(.*?)</script>',root,re.S)[1])
    assert sorted({r['year'] for r in payload['races']})==[1950,1951,2025]
    assert 'id="year-select"' in root and 'id="world-dialog"' in root
    assert 'analyses/1950/example/runs/new/overzicht.html' in root
    assert '"href": "1950/example/runs/new/overzicht.html"' in inner
    assert 'id="catalog-search"' in root
