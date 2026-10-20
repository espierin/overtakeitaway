import json

import pytest

from f1_analysis.goat_ai import generate, normalize_request, request_from_event, validate_result, quality_weights, DEFAULT_DRIVERS


IDS = ['max-verstappen', 'lewis-hamilton']


def result():
    return {'schema_version': 'goat-comparison-v2', 'input_status': 'complete', 'selected_drivers': IDS,
        'context': {'source_revision': 'test-revision', 'facts_period': [1950, 2026], 'circuits': [], 'curve_years': 'career'},
        'summary': 'Voorzichtige vergelijking.', 'comparisons': [
        {'driver': id, 'strength': 'Gemeten resultaat', 'limitation': 'Auto verschilt', 'evidence': ['career.wins']} for id in IDS],
        'domains': [{'id': id, 'included_in_verdict': id=='pace', 'weight': 1 if id=='pace' else 0, 'leaders': [], 'explanation': 'Alleen gemeenschappelijke gegevens.'} for id in ['career','qualifying','start','progression','pace','pit_balance']],
        'ranking': [{'driver': id, 'position': i+1, 'reason': 'Voorlopig oordeel'} for i,id in enumerate(IDS)],
        'winner': IDS[0], 'runner_up': IDS[1], 'conclusion': 'Voorlopige voorkeur.',
        'confidence': 'low', 'assumptions': ['Dezelfde weging'], 'limitations': ['Onvolledige dekking'],
        'infographic': {'template': 'oia-goat-comparison-v1', 'title': 'Vergelijking', 'subtitle': 'Op basis van de bron', 'metric_ids': ['career.titles','career.wins','features.qualifying_position','features.start_score'], 'takeaway': 'Voorzichtige conclusie.'}}


def test_request_accepts_empty_circuit_input_and_rejects_unknown_shape():
    assert normalize_request({'drivers': ','.join(IDS), 'circuits': ''})['circuits'] == []
    for raw in [{'drivers': ['../../secret', IDS[0]]}, {'drivers': [IDS[0], IDS[0]]},
                {'drivers': IDS, 'circuits': {'path': 'secret'}}, {'drivers': IDS, 'from': 2027, 'to': 2026}]:
        with pytest.raises(ValueError):
            normalize_request(raw)


def test_public_issue_cannot_spend_key_quota_without_maintainer_role():
    issue = {'author_association': 'NONE', 'body': '<!-- goat-ai-request-v1\n'+json.dumps({'drivers': IDS})+'\n-->'}
    with pytest.raises(ValueError, match='beheerder'):
        request_from_event('issues', {'issue': issue})
    issue['author_association'] = 'OWNER'
    assert request_from_event('issues', {'issue': issue})['drivers'] == IDS


def test_model_cannot_introduce_driver_or_duplicate_comparison():
    value = result()
    value['winner'] = 'invented-driver'
    with pytest.raises(ValueError):
        validate_result(value, IDS)
    value = result()
    value['comparisons'][1]['driver'] = IDS[0]
    with pytest.raises(ValueError):
        validate_result(value, IDS)
    value = result()
    value['winner'] = value['runner_up'] = None
    for row in value['ranking']:
        row['position'] = None
    assert validate_result(value, IDS)['winner'] is None


def test_api_key_is_only_in_header_and_response_is_checked():
    seen = {}

    class Response:
        status_code = 200

        def json(self):
            return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(result())}]}}]}

    def post(url, **kwargs):
        seen.update(url=url, **kwargs)
        return Response()

    actual = generate('frozen measured data', IDS, 'test-secret-not-real', 'gemini-3.8-flash', post)
    assert actual['winner'] == IDS[0]
    assert seen['headers']['x-goog-api-key'] == 'test-secret-not-real'
    assert 'test-secret-not-real' not in seen['url']
    assert 'test-secret-not-real' not in json.dumps(seen['json'])
    assert 'Authorization' not in seen['headers']
    assert seen['json']['generationConfig']['thinkingConfig']['thinkingLevel']=='low'


def test_provider_error_does_not_echo_secret_or_retry_paid_model():
    calls = []

    class Response:
        status_code = 429
        text = 'private provider detail: do not print'

    def post(*args, **kwargs):
        calls.append(args)
        return Response()

    with pytest.raises(RuntimeError, match='HTTP 429') as error:
        generate('data', IDS, 'test-secret-not-real', 'gemini-3.8-flash', post)
    assert 'private provider' not in str(error.value)
    assert len(calls) == 1


def test_structured_output_cannot_omit_selected_driver_or_invent_design_values():
    value = result()
    value['comparisons'].pop()
    with pytest.raises(ValueError):
        validate_result(value, IDS)
    value = result()
    value['infographic']['metric_ids'][0] = 'invented.goat_score'
    with pytest.raises(ValueError):
        validate_result(value, IDS)
    value = result()
    value['infographic']['colour'] = 'red'
    with pytest.raises(ValueError):
        validate_result(value, IDS)


def test_import_checks_source_and_period_and_same_weighting():
    brief = {'source_revision': 'test-revision', 'controls': {'facts_period': [1950,2026], 'chosen_circuits': [], 'curve_years': 'career'}}
    assert validate_result(result(), IDS, brief)['schema_version'] == 'goat-comparison-v2'
    value = result()
    value['context']['facts_period'] = [2020,2026]
    with pytest.raises(ValueError, match='periode'):
        validate_result(value, IDS, brief)
    value = result()
    value['domains'][0]['weight'] = .8
    with pytest.raises(ValueError, match='weging'):
        validate_result(value, IDS)


def test_incomplete_input_must_keep_all_drivers_and_must_not_choose_a_winner():
    value = result()
    value['input_status'] = 'incomplete'
    with pytest.raises(ValueError):
        validate_result(value, IDS)
    value['winner'] = value['runner_up'] = None
    for row in value['ranking']:
        row['position'] = None
    for d in value['domains']:
        d.update(included_in_verdict=False, weight=0)
    assert validate_result(value, IDS)['selected_drivers'] == IDS


def test_default_selection_and_quality_first_weights():
    assert DEFAULT_DRIVERS == ['lewis-hamilton', 'max-verstappen', 'sebastian-vettel', 'michael-schumacher']
    weights = quality_weights(['career','qualifying','start','progression','pace','pit_balance'])
    assert weights == pytest.approx({'career': .05, 'qualifying': .2, 'start': .15, 'progression': .25, 'pace': .3, 'pit_balance': .05})
    value = result()
    for domain in value['domains']:
        domain.update(included_in_verdict=True, weight=weights[domain['id']])
    assert validate_result(value, IDS)['winner'] == IDS[0]
    assert quality_weights(['career','pit_balance']) == dict.fromkeys(weights, 0)
    sparse = quality_weights(['career','start'])
    assert sparse['career'] == .05
    assert sparse['start'] == .95
    assert sum(sparse.values()) == pytest.approx(1)
    value['domains'][0]['weight'] = .5
    with pytest.raises(ValueError, match='weging'):
        validate_result(value, IDS)


def test_ranking_must_cover_every_driver_and_match_winner():
    for mutate in [lambda v: v['ranking'].pop(), lambda v: v['ranking'][0].update(position=2), lambda v: v['ranking'][0].update(driver=IDS[1])]:
        value = result()
        mutate(value)
        with pytest.raises(ValueError):
            validate_result(value, IDS)


@pytest.mark.parametrize('cache_kind',['result','response'])
def test_cached_result_is_reused_without_gemini_key_and_repairs_missing_index(tmp_path, monkeypatch, cache_kind):
    import hashlib
    from types import SimpleNamespace
    from f1_analysis import goat_ai
    prompt = 'same canonical combination'
    key = hashlib.sha256(prompt.encode()).hexdigest()
    request = tmp_path/'request.json'
    request.write_text(json.dumps({'drivers': list(reversed(IDS))}))
    work = tmp_path/'work'
    value = result()
    envelope = {'prompt_sha256': key, 'generated_at': '2026-10-20T12:00:00Z', 'result': value}
    class Store:
        writes = []
        def __init__(self, *args): pass
        def ensure_branch(self): pass
        def read(self, path):
            if cache_kind=='result' and path.startswith('results/'):return envelope,'sha'
            if cache_kind=='response' and path.startswith('responses/'):return {'prompt_sha256':key,'finish_reason':'STOP','text':json.dumps(value),'model':'gemini-3.8-flash'},'sha'
            return None,None
        def write(self, path, body): self.writes.append((path, body))
    def prepare(*args, **kwargs):
        (work/'prompt.txt').write_text(prompt)
        (work/'request.json').write_text(json.dumps({'prompt_sha256':key}))
        (work/'brief.json').write_text(json.dumps({'source_revision':'test-revision','controls':{'facts_period':[1950,2026],'chosen_circuits':[],'curve_years':'career'}}))
    monkeypatch.setattr(goat_ai.subprocess, 'run', prepare)
    monkeypatch.setattr(goat_ai, 'ResultStore', Store)
    def no_generation(*args, **kwargs): pytest.fail('Cached comparison must not call Gemini')
    monkeypatch.setattr(goat_ai, 'generate', no_generation)
    monkeypatch.setenv('GITHUB_REPOSITORY','example/site')
    monkeypatch.setenv('GITHUB_TOKEN','test-token-not-real')
    for name in ['GEMINI_API_KEY','GITHUB_EVENT_PATH','GITHUB_EVENT_NAME']:
        monkeypatch.delenv(name,raising=False)
    goat_ai.run(SimpleNamespace(request=str(request),output=str(work),node='node',site='.',dry_run=False))
    assert json.loads((work/'result.json').read_text())['result'] == value
    index=next(body for path,body in Store.writes if path=='index.json')
    assert key in index['results']


def test_provider_uses_simple_shape_but_full_contract_still_rejects_missing_fields():
    from f1_analysis.goat_ai import api_schema,output_schema
    simple=api_schema(IDS)
    assert simple['required'] == output_schema(IDS)['required']
    text=json.dumps(simple)
    assert 'enum' not in text and 'maxItems' not in text and 'maxLength' not in text
    invalid=result();invalid['ranking'].pop()
    with pytest.raises(ValueError):validate_result(invalid,IDS)


def test_incomplete_output_records_reason_and_safe_metadata_without_publishing():
    captured=[]
    class Response:
        status_code=200
        def json(self):return {'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'thought':True,'text':'private reasoning'},{'text':'{"partial":'}]}}], 'usageMetadata':{'thoughtsTokenCount':9800,'totalTokenCount':12000}}
    with pytest.raises(ValueError,match='MAX_TOKENS'):
        generate('data',IDS,'test-secret-not-real','gemini-3.8-flash',lambda *a,**kw:Response(),capture=captured.append)
    assert captured[0]['finish_reason']=='MAX_TOKENS'
    assert captured[0]['usage']['thoughtsTokenCount']==9800
    assert 'private reasoning' not in json.dumps(captured)
    assert 'test-secret-not-real' not in json.dumps(captured)


def test_shared_data_plan_blocks_missing_metric_penalties():
    value=result()
    for row in value['comparisons']:row['evidence']=['features.teammate_pace']
    brief={'source_revision':'test-revision','controls':{'facts_period':[1950,2026],'chosen_circuits':[],'curve_years':'career'},'assessment_plan':{'domains':[{k:d[k] for k in ['id','included_in_verdict','weight']} for d in value['domains']],'allowed_evidence':['features.teammate_pace']}}
    assert validate_result(value,IDS,brief)
    value['comparisons'][0]['evidence']=['features.metronome']
    with pytest.raises(ValueError,match='gezamenlijk'):validate_result(value,IDS,brief)
    value=result()
    for row in value['comparisons']:row['evidence']=['features.teammate_pace']
    for d in value['domains']:
        if d['id']=='qualifying':d.update(included_in_verdict=True,weight=.4)
        if d['id']=='pace':d['weight']=.6
    with pytest.raises(ValueError,match='alle rijders'):validate_result(value,IDS,brief)
