"""Regression cases for missing legacy flags and incorrectly linked FIA forms."""
from pathlib import Path
import gzip
import json
import pytest
from incident_audit import result_outcome, parse_document, decision_targets, cause

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('status,reason,old,expected', [
    ('DNF','Collision',{'finished_on_track':False},'retired'),
    ('DNF','Engine',{},'retired'),
    ('17','Engine',{'finished_on_track':True},'retired'),
    ('17',None,{'finished_on_track':False,'dnf':True},'retired'),
    ('12',None,{'finished_on_track':False,'finish_status':'Gearbox'},'retired'),
    ('DNS','Accident',{'finished_on_track':False,'dnf':True},'not_started'),
    ('DNQ','Engine',{'finished_on_track':False},'not_started'),
    ('DSQ','Underweight',{'finished_on_track':False},'disqualified'),
    ('NC',None,{'finished_on_track':False,'finish_status':'Not classified'},'unknown'),
    ('NC',None,{'finished_on_track':True,'finish_status':'+7 Laps'},'finished'),
    ('NC',None,{'finished_on_track':False,'finish_status':'Accident'},'retired'),
    ('18',None,{'finished_on_track':True,'finish_status':'Lapped','dnf':False},'finished'),
    ('10',None,{},'finished'),
    ('',None,{},'unknown'),
])
def test_outcome_is_not_the_missing_old_dnf_flag(status,reason,old,expected):
    fact={'status':status,'reason':reason,'started':True,'shared':False}
    before=dict(old)
    assert result_outcome(fact,old)==expected
    assert old==before  # Raw observations must remain intact.


def test_shared_result_is_not_an_individual_retirement():
    assert result_outcome({'status':'DNF','reason':'Engine','started':False,'shared':True},{})=='shared'


@pytest.mark.parametrize('reason,category',[('Spin','incident'),('Axle','technical'),('Suspension','ambiguous'),('Fire','ambiguous')])
def test_cause_is_not_personal_fault(reason,category):
    assert cause(reason)==category


@pytest.fixture(scope='module')
def archive():
    return json.loads(gzip.decompress((ROOT/'assets/driver-incidents.json.gz').read_bytes()))


def document(archive,id):
    old=next(d for d in archive['decisions'] if d['id']==id)
    file=ROOT/archive['sources'][old['source']]['local_file']
    return parse_document(old,file.with_suffix('.txt').read_text())


def test_barcelona_2016_joint_decision_belongs_to_both_drivers(archive):
    d=document(archive,'fia-410c4679b7dceb49e8aa')
    assert d['subject_numbers']==[6,44]
    assert d['effective_outcome']=='no_further_action'
    assert d['sanction_types']==[]
    rosters={('2016-5','Race'):{6:{'nico-rosberg'},44:{'lewis-hamilton'}}}
    assert set(decision_targets(d,rosters))=={('nico-rosberg',6,'subject'),('lewis-hamilton',44,'subject')}


def test_unicode_number_heading_recovers_subject_without_penalising_opponent(archive):
    d=document(archive,'fia-11e28dfbe93abc07f7f9')
    assert d['subject_numbers']==[20]
    assert d['time_penalty_seconds']==5
    assert d['penalty_points']==2
    roster={('2014-2','Race'):{20:{'kevin-magnussen'},7:{'kimi-raikkonen'}}}
    assert set(decision_targets(d,roster))=={('kevin-magnussen',20,'subject'),('kimi-raikkonen',7,'involved')}


def test_review_of_earlier_penalties_is_not_a_new_penalty(archive):
    d=document(archive,'fia-c1e8322f3c3556585b16')
    assert d['effective_outcome']=='review'
    assert not d['sanction_types']
    assert 'no new significant' in d['decision']


def test_collective_austria_2023_penalties_are_split_by_recipient(archive):
    d=document(archive,'fia-17bc9c0f66437cc9af57')
    assert d['subject_numbers']==[2,10,21,22,23,31,44,55]
    assert len(d['table_sanctions'])==12
    assert [x['seconds'] for x in d['table_sanctions'] if x['number']==31]==[5,10,5,10]
    assert sum(x['seconds'] for x in d['table_sanctions'] if x['number']==21)==15


def test_collective_deleted_laps_use_car_column_not_turn_number(archive):
    d=document(archive,'fia-03c6bbea2a97a93c0920')
    assert d['subject_numbers']==[10,81]
    assert d['deleted_laps_by_number']=={10:1,81:1}


def test_2026_collective_deleted_laps_with_no_dot_heading(archive):
    d=document(archive,'fia-464ac4bb17a769114f11')
    assert d['subject_numbers']==[5,10,23,30,55]


def test_old_soft_hyphen_in_driver_header_is_not_a_missing_subject(archive):
    d=document(archive,'fia-9f0c817f47f22a342335')
    assert d['subject_numbers']==[1]
    assert d['grid_places']==5


def test_deleted_laps_can_be_read_when_the_table_heading_is_absent(archive):
    d=document(archive,'fia-3d5087bc7e368ae356b6')
    assert 18 in d['subject_numbers']
    assert 12 in d['subject_numbers']


def test_suspending_a_penalty_is_not_banning_a_driver(archive):
    old=next(d for d in archive['decisions'] if d['race']=='2026-5' and 'Doc 99 -' in d['title'])
    d=document(archive,old['id'])
    assert 'stop_go' in d['sanction_types']
    assert 'ban' not in d['sanction_types']


def test_collective_warning_lists_all_twelve_subjects(archive):
    d=document(archive,'fia-461dd273ab167b58c95f')
    assert d['effective_outcome']=='penalty'
    assert d['sanction_types']==['warning']
    assert len(d['subject_numbers'])==12
    assert 23 in d['subject_numbers']
    assert 10 not in d['subject_numbers']  # Narrative text has a different number.


def test_fp1_substitute_is_not_the_race_driver_of_the_same_car():
    rosters={('2015-18','Race'):{30:{'jolyon-palmer'}},
             ('2015-18','Practice 1'):{30:{'jolyon-palmer'},13:{'pastor-maldonado'}}}
    d={'race':'2015-18','session':'Practice 1','subject_numbers':[30],
       'effective_outcome':'penalty','is_collision':False,'involved_numbers':[13,30]}
    assert decision_targets(d,rosters)==[('jolyon-palmer',30,'subject')]
    d['session']=None
    rosters[('2015-18','Race')][30]={'other-driver'}
    assert decision_targets(d,rosters)==[]  # Unknown session plus ambiguous car.


def read_script(path):
    return json.loads(path.read_text().split('=',1)[1].rstrip(';\n'))


def built_facts(did):
    f=read_script(ROOT/'_development/data/facts.js')
    group=did[:2]
    d=read_script(ROOT/'_development/data/facts'/f'{group}.js')[did]
    d['races']=[dict(zip(f['race_columns'],r)) for r in d['races']]
    d['decisions']=[dict(zip(f['decision_columns'],r)) for r in d['decisions']]
    return d


def test_built_rosberg_and_hamilton_show_the_barcelona_retirement_and_no_penalty():
    for did in ['nico-rosberg','lewis-hamilton']:
        f=built_facts(did)
        r=next(r for r in f['races'] if r['race']=='2016-5')
        assert r['outcome']=='retired'
        assert r['category']=='incident'
        assert r['laps']==0
        decisions=[d for d in f['decisions'] if d['race']=='2016-5' and d['id']=='fia-410c4679b7dceb49e8aa']
        assert len(decisions)==1
        assert decisions[0]['role']=='subject'
        assert decisions[0]['effective_outcome']=='no_further_action'
        assert decisions[0]['reviewed_responsibility']['degree']=='neither_predominant'
        assert decisions[0]['retirement_links'][0]['causation_confirmed'] is True


def test_all_built_dnf_and_nonstart_statuses_are_accounted_for():
    meta=read_script(ROOT/'_development/data/facts.js');counts={}
    for file in (ROOT/'_development/data/facts').glob('*.js'):
        for driver in read_script(file).values():
            for values in driver['races']:
                row=dict(zip(meta['race_columns'],values))
                counts[row['outcome']]=counts.get(row['outcome'],0)+1
                if row['status']=='DNF' and not row['shared']:
                    assert row['outcome']=='retired'
                if row['status'] in {'DNS','DNQ','DNPQ','DNP','EX'} and not row['shared']:
                    assert row['outcome']=='not_started'
                if row['status']=='DSQ' and not row['shared']:
                    assert row['outcome']=='disqualified'
    audit=json.loads((ROOT/'_development/incident-audit.json').read_text())
    assert counts==audit['outcomes']
    assert audit['reparsed']==audit['documents']==6013
    assert not audit['unavailable_text']
    assert len(audit['restored_missing_legacy_dnf'])>9000


def test_ricciardo_china_2024_is_involved_but_not_the_penalty_recipient():
    ric=built_facts('daniel-ricciardo')
    doc=next(d for d in ric['decisions'] if d['id']=='fia-1177c73c1df084e84bd3')
    assert doc['role']=='involved'
    assert doc['retirement_links'][0]['causation_confirmed'] is True
    assert not doc.get('reviewed_responsibility')
    stroll=built_facts('lance-stroll')
    doc=next(d for d in stroll['decisions'] if d['id']=='fia-1177c73c1df084e84bd3')
    assert doc['role']=='subject'
    assert doc['reviewed_responsibility']['degree']=='predominant'


def test_source_confirmed_retirements_cannot_enter_finish_progression():
    data=read_script(ROOT/'_development/data/profiles.js')
    for d in data['drivers']:
        for packed in d['races']:
            row=dict(zip(data['driver_race_columns'],packed))
            if row['result_outcome']!='finished':
                assert row['race_eligible'] is False


def test_old_classification_penalties_are_retained_and_every_record_has_a_year():
    meta=read_script(ROOT/'_development/data/facts.js');total=0
    for file in (ROOT/'_development/data/facts').glob('*.js'):
        for record in read_script(file).values():
            for p in record['classification_penalties']:
                total+=1
                assert p['year']==int(p['race'].split('-')[0])
    assert total==282
    jos=built_facts('jos-verstappen')
    p=next(p for p in jos['classification_penalties'] if p['race']=='2001-1')
    assert p['time_penalty_millis']==25000


def test_retained_incident_sources_have_not_changed():
    from verify_incident_sources import verify
    result=verify()
    assert result['checked_pdf_sources']==6013
    assert not result['missing']
    assert not result['hash_mismatches']
