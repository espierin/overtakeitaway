from f1_analysis.incidents import retirement_category, extract_decision, retirement_links, reconcile_decisions, attach_retained


def test_retirement_causes_do_not_assign_component_damage_to_driver_fault():
    for status in ('Collision','Collision damage','Accident','Spun off'):
        assert retirement_category(status)=='incident'
    for status in ('Engine','Gearbox','Power Unit','Electrical','Hydraulics'):
        assert retirement_category(status)=='technical'
    for status in ('Suspension','Puncture','Tyre','Front wing','Undertray'):
        assert retirement_category(status)=='ambiguous'
    assert retirement_category('Retired')=='unknown'
    assert retirement_category(None)=='unknown'
    assert retirement_category('Disqualified')=='disqualified'
    assert retirement_category('Lapped')=='finished'
    assert retirement_category('+2 Laps')=='finished'


def test_decision_number_does_not_swallow_penalty_amount_or_prior_points_total():
    text='''Document 37
No / Driver     22 - Example Driver
Session         Race
Fact            Collision with car 10 at turn 3 on lap 12.
Offence         Breach of the sporting regulations.
Decision        5 second time penalty.
                2 penalty points (total of 8 for the 12 month period).
Reason          Car 22 was predominantly to blame for the collision.
Competitors are reminded that they have the right to appeal.
'''
    d=extract_decision('Doc 37 - Offence - Car 22 - Causing a collision',text)
    assert d['time_penalty_seconds']==5
    assert d['penalty_points']==2
    assert d['penalty_points_total_at_decision']==8
    assert d['document_number']==37
    assert d['driver_number']==22
    assert d['involved_numbers']==[10,22]
    assert d['outcome']=='penalty'
    assert d['session']=='Race'
    assert d['lap']==12
    assert d['blame_evidence']=='stewards_explicit_blame'
    assert d['requires_review'] is True


def test_no_further_action_is_not_a_penalty_and_summons_is_not_a_verdict():
    d=extract_decision('Decision - Car 4 - Alleged causing a collision','''Session Race
Fact Collision with Car 2.
Decision No further action.
Reason A racing incident. A previous penalty is mentioned here only for context.
''')
    assert d['outcome']=='no_further_action'
    assert not d['sanction_types']
    assert extract_decision('Summons - Car 4 - Causing a collision','Attend the hearing about an alleged penalty.')['outcome']=='summons'


def test_explicit_review_removes_penalty_without_erasing_the_original_event():
    d=extract_decision('Doc 47 - Right of Review','''Decision 1: The petition is admissible.
Reason: New evidence is available.
Decision 2: As a result the penalty on Car 12 in Document number 43 is removed.
Reason: The original decision is reversed.
''')
    assert d['outcome']=='overturned'
    assert not d['sanction_types']
    assert d['time_penalty_seconds'] is None


def test_sprint_decisions_and_unrelated_penalties_do_not_link_to_race_retirement():
    row={'finished_on_track':False,'number':10,'category':'incident'}
    d={'id':'fia-test','session':'Race','involved_numbers':[10,22],'driver_number':22,
       'is_collision':True,'outcome':'penalty','reason':'Car 10 was unable to continue after the collision.'}
    links=retirement_links(row,[d])
    assert len(links)==1
    assert links[0]['role']=='other_involved_driver'
    assert links[0]['relation']=='explicit_retirement_mention'
    assert links[0]['causation_confirmed'] is False
    assert retirement_links(row,[dict(d,session='Sprint')])==[]
    assert retirement_links(row,[dict(d,is_collision=False)])==[]
    assert retirement_links(dict(row,finished_on_track=True),[d])==[]
    assert retirement_links(dict(row,category='technical'),[d])==[]


def test_grid_and_fine_details_are_not_interpreted_as_time_penalties():
    d=extract_decision('Decision - Car 9','''No / Driver 9 - Driver
Session Qualifying
Decision A drop of 3 grid positions at the next race and a fine of EUR 10,000.
Reason A qualifying infringement.
''')
    assert d['outcome']=='penalty'
    assert d['grid_places']==3
    assert d['fine_text']=='EUR 10,000'
    assert d['time_penalty_seconds'] is None


def test_unstructured_or_scanned_decision_does_not_claim_no_penalties():
    d=extract_decision('FIA Stewards Decision - Document No. 55','Unreadable scan, further research needed.')
    assert d['outcome']=='unresolved'
    assert d['requires_review'] is True
    assert d['sanction_types']==[]


def test_body_document_number_wins_over_reference_to_old_decision_in_title():
    d=extract_decision('Replacement for Document 47 - Offence - Car 44','''Document 55
No / Driver 44 - Driver
Session Race
Decision 5 second time penalty.
Reason We replace document 47 and remove the penalty points.
''')
    assert d['document_number']==55
    assert d['time_penalty_seconds']==5
    assert d['penalty_points'] is None


def test_incident_clock_does_not_use_document_publication_time_or_table_text():
    d=extract_decision('Decision','''Document 9
Time 18:45
No / Driver 18 - Driver
Competitor Team
Time 15:51
Session Race
Decision 10 second time penalty.
''')
    assert d['incident_time_local']=='15:51'
    assert extract_decision('Classification','Time 18:45\nA long classification table follows.')['incident_time_local'] is None


def test_replacements_and_overturns_remain_distinct_and_do_not_double_count():
    records=[
        dict(id='original',race='2020-10',title='Offence - Car 44',document_number=47,outcome='penalty',published='Published on 27.09.20 14:16 CET',decision='5 second time penalty. 2 penalty points.',reason=''),
        dict(id='replacement',race='2020-10',title='Replacement for Document 47',document_number=55,outcome='penalty',published='Published on 27.09.20 18:04 CET',decision='5 second time penalty.',reason='We replace document 47 and remove penalty points.'),
        dict(id='old',race='2025-1',title='Offence',document_number=43,outcome='penalty',published='',decision='5 second time penalty.',reason=''),
        dict(id='review',race='2025-1',title='Review',document_number=47,outcome='overturned',published='',decision='The penalty in Document number 43 is removed.',reason='')]
    reconcile_decisions(records)
    assert records[0]['effective_outcome']=='superseded'
    assert records[0]['superseded_by']=='replacement'
    assert records[1]['effective_outcome']=='penalty'
    assert records[2]['effective_outcome']=='overturned'
    assert sum(d['effective_outcome']=='penalty' for d in records)==1


def test_retained_evidence_survives_a_future_rebuild_without_embedding_documents(tmp_path):
    import gzip,json
    p=tmp_path/'assets';p.mkdir()
    registry={'retirements':[{'race':'2024-5','driver_id':'driver','id':'r:d','reason':'Collision','category':'incident'}],
              'recovered_finishers':[{'race':'2026-1','driver':'lapped'}]}
    packed=gzip.compress(json.dumps(registry).encode());(p/'driver-incidents.json.gz').write_bytes(packed)
    data={'drivers':[{'id':'driver','races':[{'race':'2024-5','finished_on_track':False,'finish':12}]},
                     {'id':'lapped','races':[{'race':'2026-1','finished_on_track':False,'dnf':True,'finish_status':None,'finish':9}]}]}
    assert attach_retained(data,tmp_path)==1
    assert data['drivers'][0]['races'][0]['finish']==12
    assert data['drivers'][0]['races'][0]['retirement_evidence']['reason']=='Collision'
    assert data['drivers'][1]['races'][0]['finished_on_track'] is True
    assert data['drivers'][1]['races'][0]['dnf'] is False
    assert data['settings']['incident_evidence']['embedded'] is False
    assert 'decisions' not in data
