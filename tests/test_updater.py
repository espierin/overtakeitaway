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
