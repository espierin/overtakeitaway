import json

import pytest

from f1_analysis.goat_ai import generate, normalize_request, request_from_event, validate_result


IDS = ['max-verstappen', 'lewis-hamilton']


def result():
    return {'summary': 'Voorzichtige vergelijking.', 'comparisons': [
        {'driver': id, 'strength': 'Gemeten resultaat', 'limitation': 'Auto verschilt'} for id in IDS],
        'winner': IDS[0], 'runner_up': IDS[1], 'conclusion': 'Voorlopige voorkeur.',
        'confidence': 'low', 'assumptions': ['Dezelfde weging'], 'limitations': ['Onvolledige dekking']}


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
