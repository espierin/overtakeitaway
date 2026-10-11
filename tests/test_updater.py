import pytest
from pathlib import Path
from types import SimpleNamespace

from f1_analysis import updater
from f1_analysis.io import write_json
from test_publication import project


def test_unchanged_sources_skip_reanalysis_but_late_overtakes_trigger_update(tmp_path,monkeypatch):
    root=tmp_path/'project';root.mkdir();project(root)
    (root/'config/publication.yaml').write_text('settle_days: 14\nretry_hours: 1\nrefresh_hours: 6\nminimum_delay_minutes: 45\nmax_races_per_update: 3\n')
    (root/'config/defaults.yaml').write_text('slotfase_fractie: 0.25\n')
    (root/'config/history.yaml').write_text('{}')
    session={'session_key':42,'session_name':'Race','year':2025,'circuit_short_name':'Test','country_name':'United Kingdom',
             'date_start':'2025-10-10T12:00:00Z','date_end':'2025-10-10T14:00:00Z'}
    source={'sessions':[session],'drivers':[{'driver_number':1}],
            'session_result':[{'driver_number':1,'position':1,'number_of_laps':50}],
            'laps':[{'driver_number':1,'lap_number':50}],'position':[{}],'stints':[{}],
            'race_control':[{'message':'SESSION FINISHED'}]}
    class FakeClient:
        def __init__(self,*args,**kwargs):assert kwargs.get('refresh') is True
        def api(self,ep,**params):return source.get(ep,[])
    calls=[]
    monkeypatch.setattr(updater,'Client',FakeClient)
    monkeypatch.setattr(updater,'discover_calendar',lambda *args:[session])
    monkeypatch.setattr(updater,'recipe_hash',lambda *args:'recipe')
    monkeypatch.setattr(updater,'optional_probe',lambda *args:{'f1gures':'unknown'})
    monkeypatch.setattr(updater.subprocess,'run',lambda *args,**kwargs:(calls.append(args) or SimpleNamespace(returncode=0)))
    first=updater.update(root,[2025],updater.parse_date('2025-10-11T12:00:00Z'))
    assert first['updated']==[42] and len(calls)==1
    again=updater.update(root,[2025],updater.parse_date('2025-10-11T18:00:00Z'))
    assert again['unchanged']==[42] and len(calls)==1
    source['overtakes']=[{'overtaking_driver_number':1,'overtaken_driver_number':2}]
    later=updater.update(root,[2025],updater.parse_date('2025-10-12T00:00:00Z'))
    assert later['updated']==[42] and len(calls)==2


def test_failed_analysis_keeps_retry_eligible(tmp_path,monkeypatch):
    # A failed render must not mark a new session as known/settled.
    config={'minimum_delay_minutes':45,'settle_days':14,'retry_hours':1,'refresh_hours':6,'max_races_per_update':3}
    session={'session_key':99,'session_name':'Race','date_start':'2025-01-01T12:00:00Z','date_end':'2025-01-01T14:00:00Z'}
    state={'99':{'last_attempt':'2025-10-11T12:00:00Z','status':'mislukt'}}
    now=updater.parse_date('2025-10-11T13:00:00Z')
    assert updater.plan([session],{},state,now,config)==[session]


def test_half_hour_retries_waiting_known_race_and_excludes_future():
    config={'minimum_delay_minutes':0,'settle_days':14,'retry_minutes':30,'retry_hours':.5,'refresh_hours':6,'max_races_per_update':3}
    race={'session_key':99,'session_name':'Race','date_start':'2026-10-11T12:00:00Z','date_end':'2026-10-11T14:00:00Z'}
    future={**race,'session_key':100,'date_end':'2026-10-12T14:00:00Z'}
    state={'99':{'last_attempt':'2026-10-11T14:00:00Z','status':'wacht_op_data'}}
    assert updater.plan([race,future],{'99':True},state,updater.parse_date('2026-10-11T14:29:00Z'),config)==[]
    assert updater.plan([race,future],{'99':True},state,updater.parse_date('2026-10-11T14:30:00Z'),config)==[race]


def test_calendar_discovery_survives_openf1_unavailable_and_preserves_existing_source(tmp_path,monkeypatch):
    from f1_analysis import history
    race={'year':2026,'session_key':202601,'round':1,'session_name':'Race','date_start':'2026-03-08T04:00:00Z','circuit_short_name':'Melbourne',
          'jolpica_race':{'date':'2026-03-08','Circuit':{'Location':{'country':'Australia'}}}}
    monkeypatch.setattr(history,'calendar',lambda *args:[race])
    class Client:
        root=tmp_path
        def api(self,*args,**kwargs):raise ValueError('OpenF1 niet beschikbaar')
    found=updater.discover_calendar(Client(),[2026],{},updater.parse_date('2026-03-08T08:00:00Z'),{})
    assert found[0]['timing_source']=='fastf1'
    assert updater.parse_date(found[0]['date_end'])==updater.parse_date('2026-03-08T07:00:00Z')
    assert (tmp_path/'_storage/season-calendar.json').exists()
    class Available(Client):
        def api(self,*args,**kwargs):return [{'year':2026,'session_key':42,'session_name':'Race','date_start':race['date_start'],'date_end':'2026-03-08T06:00:00Z','country_name':'Australia'}]
    assert updater.discover_calendar(Available(),[2026],{},updater.parse_date('2026-03-08T08:00:00Z'),{})[0]['session_key']==42
    known={'202601':(None,None,{'input':{'year':2026},'race_round':1,'session':{'session_key':202601}})}
    assert updater.discover_calendar(Available(),[2026],known,updater.parse_date('2026-03-08T08:00:00Z'),{})[0]['session_key']==202601


def test_no_results_waits_without_loading_timing(tmp_path):
    class Client:
        def fetch(self,*args,**kwargs):return {'MRData':{'RaceTable':{'Races':[]}}}
    data,missing=updater.fastf1_probe(Client(),{'year':2026,'round':1},tmp_path)
    assert data is None and missing==['definitieve raceuitslag']


def test_inaccessible_openf1_uses_verified_fastf1_data(tmp_path,monkeypatch):
    root=tmp_path/'project';root.mkdir();project(root)
    (root/'config/publication.yaml').write_text('settle_days: 14\nretry_minutes: 30\nretry_hours: .5\nrefresh_hours: 6\nminimum_delay_minutes: 0\nmax_races_per_update: 3\n')
    (root/'config/defaults.yaml').write_text('slotfase_fractie: 0.25\n')
    (root/'config/history.yaml').write_text('{}')
    session={'session_key':99,'session_name':'Race','year':2026,'round':1,'timing_source':'openf1','circuit_short_name':'Test',
             'date_start':'2026-01-01T12:00:00Z','date_end':'2026-01-01T14:00:00Z'}
    class FakeClient:
        def __init__(self,*args,**kwargs):pass
        def api(self,*args,**kwargs):raise ValueError('timing niet beschikbaar')
    calls=[]
    monkeypatch.setattr(updater,'Client',FakeClient)
    monkeypatch.setattr(updater,'discover_calendar',lambda *args:[session])
    monkeypatch.setattr(updater,'fastf1_probe',lambda *args:({'drivers':[{'driver_number':1}],'timing_source':'FastF1'},[]))
    monkeypatch.setattr(updater,'optional_probe',lambda *args:{})
    monkeypatch.setattr(updater,'recipe_hash',lambda *args:'recipe')
    monkeypatch.setattr(updater.subprocess,'run',lambda command,**kwargs:(calls.append(command) or SimpleNamespace(returncode=0)))
    report=updater.update(root,[2026],updater.parse_date('2026-01-01T15:00:00Z'))
    assert report['updated']==[99] and not report['failed']
    assert '--timing-source' in calls[0] and 'fastf1' in calls[0] and '--refresh' not in calls[0]


def test_delayed_fastf1_session_is_waiting_not_failure(tmp_path,monkeypatch):
    from f1_analysis import history
    from fastf1._api import SessionNotAvailableError
    (tmp_path/'config').mkdir();(tmp_path/'config/sources.yaml').write_text('{}')
    class Client:
        def fetch(self,*args,**kwargs):return {'MRData':{'RaceTable':{'Races':[{'Results':[{'position':'1'}]}]}}}
    def unavailable(*args):raise SessionNotAvailableError('Timing nog niet beschikbaar')
    monkeypatch.setattr(history,'acquire',unavailable)
    data,missing=updater.fastf1_probe(Client(),{'year':2026,'round':1,'session_key':202601,'circuit_short_name':'Test'},tmp_path)
    assert data is None and 'Timing nog niet beschikbaar' in missing[0]


def test_progress_measures_observed_checks_without_invented_progress():
    assert updater.data_progress({})==0
    data={'drivers':[{'driver_number':1}],'laps':[{'driver_number':1,'lap_number':50}],'position':[{}], 'stints':[{}],
          'race_control':[{'message':'SESSION FINISHED'}],'session_result':[{'driver_number':1,'position':1,'number_of_laps':50}]}
    assert updater.data_progress(data)==100
    data['laps']=[]
    assert 0<updater.data_progress(data)<100


@pytest.fixture(autouse=True)
def offline_search_reference(monkeypatch):
    monkeypatch.setattr('f1_analysis.catalogue_search.refresh_reference', lambda root: None)
