"""GitHub-hosted Gemini comparisons. Keys are used only inside Actions."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time

import requests

DEFAULT_DRIVERS = ['lewis-hamilton', 'max-verstappen', 'sebastian-vettel', 'michael-schumacher']
BRANCH = 'goat-ai-results'
MARKER = 'goat-ai-request-v1'


def normalize_request(raw):
    def items(value):
        return [v.strip() for v in value.split(',') if v.strip()] if isinstance(value, str) else value
    ids = items(raw.get('drivers', DEFAULT_DRIVERS))
    circuits = items(raw.get('circuits', []))
    if not isinstance(ids, list) or not all(isinstance(v, str) for v in ids) or not 2 <= len(ids) <= 4 or len(set(ids)) != len(ids):
        raise ValueError('Kies twee tot vier verschillende rijders')
    if not isinstance(circuits, list) or len(circuits)>100:
        raise ValueError('Ongeldige circuitselectie')
    for value in ids + circuits:
        if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
            raise ValueError('Ongeldige rijder- of circuitcode')
    start, end = int(raw.get('from', 1950)), int(raw.get('to', 2026))
    if not 1950 <= start <= end <= 2100:
        raise ValueError('Ongeldige periode')
    lang, axis = raw.get('lang', 'nl'), raw.get('curveyears', 'career')
    if lang not in ('nl', 'en') or axis not in ('career', 'calendar'):
        raise ValueError('Ongeldige taal of tijdas')
    return {'drivers': ids, 'from': start, 'to': end, 'circuits': circuits, 'lang': lang, 'curveyears': axis}


def request_from_event(event_name, event):
    if event_name == 'issues':
        issue = event.get('issue', {})
        if issue.get('author_association') not in ('OWNER', 'MEMBER', 'COLLABORATOR'):
            raise ValueError('Alleen de beheerder of een medewerker kan AI-aanvragen uitvoeren')
        match = re.search(r'<!-- '+MARKER+r'\s+(\{[^\n]+\})\s*-->', issue.get('body') or '')
        if not match:
            raise ValueError('Geen geldige GOAT-aanvraag')
        return normalize_request(json.loads(match[1]))
    return normalize_request(event.get('inputs') or {})


def contract():
    path = Path(__file__).resolve().parents[2]/'_development/assets/goat-ai-contract.js'
    return json.loads(path.read_text().split('=', 1)[1].strip().removesuffix(';'))


def output_schema(ids):
    def visit(value):
        if value == '__COUNT__':
            return len(ids)
        if isinstance(value, list):
            result = []
            for item in value:
                result.extend(ids if item == '__DRIVER__' else [visit(item)])
            return result
        if isinstance(value, dict):
            return {key: visit(v) for key, v in value.items()}
        return value
    return visit(contract()['schema'])


def check_schema(value, schema, path='$'):
    types = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
    actual = 'null' if value is None else 'boolean' if isinstance(value, bool) else 'number' if isinstance(value, (int, float)) else 'string' if isinstance(value, str) else 'array' if isinstance(value, list) else 'object' if isinstance(value, dict) else 'invalid'
    if actual not in types and not ('integer' in types and actual == 'number' and float(value).is_integer()):
        raise ValueError(path+': onjuist veldtype')
    if actual == 'number' and not math.isfinite(value):
        raise ValueError(path+': ongeldig getal')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(path+': ongeldige keuze')
    if actual == 'string' and not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 10**9):
        raise ValueError(path+': onjuiste tekstlengte')
    if actual == 'number' and not schema.get('minimum', -math.inf) <= value <= schema.get('maximum', math.inf):
        raise ValueError(path+': getal buiten bereik')
    if actual == 'array':
        if not schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', 10**9):
            raise ValueError(path+': onjuist aantal onderdelen')
        for i, item in enumerate(value):
            check_schema(item, schema['items'], path+'/'+str(i))
    if actual == 'object':
        if not set(schema.get('required', [])) <= value.keys():
            raise ValueError(path+': verplicht veld ontbreekt')
        for key, item in value.items():
            if key not in schema['properties']:
                if schema.get('additionalProperties') is False:
                    raise ValueError(path+'/'+key+': onverwacht veld')
            else:
                check_schema(item, schema['properties'][key], path+'/'+key)


def quality_weights(included):
    base = contract()['quality_weights']
    primary = ['qualifying', 'start', 'progression', 'pace']
    total = sum(base[id] for id in primary if id in included)
    weights = dict.fromkeys(base, 0)
    if not total:
        return weights
    for id in ['career', 'pit_balance']:
        if id in included:
            weights[id] = base[id]
    share = 1-weights['career']-weights['pit_balance']
    for id in primary:
        if id in included:
            weights[id] = share*base[id]/total
    return weights


def validate_result(result, ids, brief=None):
    check_schema(result, output_schema(ids))
    if set(result['selected_drivers']) != set(ids) or len({r['driver'] for r in result['comparisons']}) != len(ids):
        raise ValueError('Het antwoord moet iedere geselecteerde rijder eenmaal bevatten')
    if result['winner'] is not None and result['winner'] == result['runner_up']:
        raise ValueError('Winnaar en nummer twee zijn gelijk')
    if result['winner'] is None and result['runner_up'] is not None:
        raise ValueError('Geen nummer twee zonder winnaar')
    domains = result['domains']
    if len({d['id'] for d in domains}) != 6:
        raise ValueError('Elk onderdeel moet eenmaal voorkomen')
    included = [d for d in domains if d['included_in_verdict']]
    weights = quality_weights([d['id'] for d in included])
    for domain in domains:
        if abs(domain['weight']-weights[domain['id']]) > 1e-5 or (domain['included_in_verdict'] and not domain['weight']) or len(set(domain['leaders'])) != len(domain['leaders']):
            raise ValueError('Onjuiste weging voor racekwaliteiten of dubbele rijder')
    if (result['input_status'] == 'incomplete' or not included) and (result['winner'] is not None or result['runner_up'] is not None or included):
        raise ValueError('Onvolledige vergelijking mag geen winnaar opleveren')
    if len(set(result['infographic']['metric_ids'])) != len(result['infographic']['metric_ids']):
        raise ValueError('Dubbele infographicparameter')
    ranking = result['ranking']
    if len({r['driver'] for r in ranking}) != len(ids):
        raise ValueError('Iedere rijder moet eenmaal in de klassering staan')
    ranked = {r['position']: r['driver'] for r in ranking if r['position'] is not None}
    if result['winner'] is None:
        if ranked:
            raise ValueError('Geen klassering zonder onderbouwde winnaar')
    elif len(ranked) != len(ids) or ranked.get(1) != result['winner'] or ranked.get(2) != result['runner_up']:
        raise ValueError('Klassering en conclusie moeten overeenkomen')
    if brief:
        controls = brief['controls']
        expected = {'source_revision': brief['source_revision'], 'facts_period': controls['facts_period'], 'circuits': controls['chosen_circuits'], 'curve_years': controls['curve_years']}
        if result['context'] != expected:
            raise ValueError('Het antwoord hoort bij een andere selectie of bronperiode')
        plan = brief.get('assessment_plan')
        if plan and result['input_status'] == 'complete':
            for domain in domains:
                prescribed = next(d for d in plan['domains'] if d['id'] == domain['id'])
                if domain['included_in_verdict'] != prescribed['included_in_verdict'] or abs(domain['weight']-prescribed['weight']) > 1e-5:
                    raise ValueError('Een onderdeel zonder vergelijkbare gegevens voor alle rijders mag niet meetellen')
            if any(key not in plan['allowed_evidence'] for row in result['comparisons'] for key in row['evidence']):
                raise ValueError('Niet gezamenlijk gemeten parameter gebruikt als bewijs')
    return result


def api_schema(ids):
    # Gemini's constrained decoder can reject a large combination of enums and
    # bounds. Guide it with the shape; the prompt and local checks keep the full
    # shared contract, including all selection, count and weighting constraints.
    def simplify(value):
        if isinstance(value, dict):
            return {key: simplify(item) for key, item in value.items()
                    if key not in {'enum', 'minimum', 'maximum', 'minLength', 'maxLength', 'minItems', 'maxItems'}}
        if isinstance(value, list):
            return [simplify(item) for item in value]
        return value
    return simplify(output_schema(ids))


def generate(prompt, ids, api_key, model, post=requests.post, capture=None):
    if not re.fullmatch(r'gemini-[a-z0-9.-]+', model):
        raise ValueError('Ongeldige modelnaam')
    for attempt in range(3):
        response = post('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',
        headers={'x-goog-api-key': api_key, 'Content-Type': 'application/json'},
        json={'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
              'generationConfig': {'maxOutputTokens': 10000, 'thinkingConfig': {'thinkingLevel': 'low'}, 'responseFormat': {'text': {
                  'mimeType': 'APPLICATION_JSON', 'schema': api_schema(ids)}}}}, timeout=(20, 240))
        if response.status_code not in (500, 502, 503, 504) or attempt == 2:
            break
        print('Google tijdelijk niet beschikbaar; dezelfde aanvraag wordt opnieuw geprobeerd.')
        time.sleep(5 * (attempt + 1))
    # Never echo provider responses or headers into public Actions logs.
    if response.status_code != 200:
        reason = ''
        if response.status_code == 400:
            try:
                message = str(response.json().get('error', {}).get('message', '')).lower()
                if 'schema' in message or 'states' in message:
                    reason = '; Google accepteerde het antwoordformaat niet'
            except (ValueError, AttributeError):
                pass
        raise RuntimeError(f'Gemini-aanvraag gestopt (HTTP {response.status_code}){reason}; geen betaald terugvalmodel gebruikt')
    payload = response.json()
    candidates = payload.get('candidates') or []
    reason = candidates[0].get('finishReason') if candidates else 'NO_CANDIDATE'
    reason = reason if reason in {'STOP','MAX_TOKENS','SAFETY','RECITATION','LANGUAGE','BLOCKLIST','PROHIBITED_CONTENT','SPII','OTHER','NO_CANDIDATE'} else 'UNKNOWN'
    parts = candidates[0].get('content', {}).get('parts', []) if candidates else []
    text = ''.join(p.get('text', '') for p in parts if not p.get('thought'))
    if capture:
        usage = {key:value for key,value in payload.get('usageMetadata', {}).items()
                 if key in {'promptTokenCount','candidatesTokenCount','thoughtsTokenCount','totalTokenCount'} and isinstance(value,int)}
        capture({'finish_reason':reason,'text':text,'usage':usage})
    if reason != 'STOP':
        raise ValueError('Gemini gaf geen afgerond antwoord ('+reason+'); niets gepubliceerd')
    return validate_result(json.loads(text), ids)


class ResultStore:
    def __init__(self, repository, token):
        if not re.fullmatch(r'[\w.-]+/[\w.-]+', repository):
            raise ValueError('Ongeldige repository')
        self.api = 'https://api.github.com/repos/'+repository
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})

    def read(self, name):
        response = self.session.get(self.api+'/contents/'+name, params={'ref': BRANCH}, timeout=60)
        if response.status_code == 404:
            return None, None
        response.raise_for_status()
        payload = response.json()
        return json.loads(base64.b64decode(payload['content'])), payload['sha']

    def ensure_branch(self):
        response = self.session.get(self.api+'/git/ref/heads/'+BRANCH, timeout=60)
        if response.status_code == 404:
            main = self.session.get(self.api+'/git/ref/heads/main', timeout=60)
            main.raise_for_status()
            response = self.session.post(self.api+'/git/refs', json={'ref': 'refs/heads/'+BRANCH, 'sha': main.json()['object']['sha']}, timeout=60)
        response.raise_for_status()

    def write(self, name, value):
        _, sha = self.read(name)
        payload = {'message': 'Bewaar gecontroleerde Gemini-vergelijking', 'branch': BRANCH,
                   'content': base64.b64encode((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()).decode()}
        if sha:
            payload['sha'] = sha
        response = self.session.put(self.api+'/contents/'+name, json=payload, timeout=60)
        response.raise_for_status()


def index_result(store, key, envelope):
    index, _ = store.read('index.json')
    index = index or {'schema': 'goat-ai-index-v1', 'results': {}}
    entry = {'file': 'results/'+key+'.json', 'drivers': envelope['result']['selected_drivers'], 'generated_at': envelope['generated_at']}
    if index['results'].get(key) != entry:
        index['results'][key] = entry
        store.write('index.json', index)


def run(args):
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()) if os.environ.get('GITHUB_EVENT_PATH') else {}
    request = request_from_event(os.environ.get('GITHUB_EVENT_NAME', 'workflow_dispatch'), event)
    if args.request:
        request = normalize_request(json.loads(Path(args.request).read_text()))
    work = Path(args.output)
    work.mkdir(parents=True, exist_ok=True)
    request_path = work/'controls.json'
    request_path.write_text(json.dumps(request))
    subprocess.run([args.node, '_development/research/goat-ai-brief.cjs', str(Path(args.site).resolve()), str(request_path.resolve()), str(work.resolve())], check=True)
    prepared = json.loads((work/'request.json').read_text())
    prompt = (work/'prompt.txt').read_text()
    key = hashlib.sha256(prompt.encode()).hexdigest()
    if key != prepared['prompt_sha256']:
        raise ValueError('Aanvraaghash komt niet overeen')
    brief = json.loads((work/'brief.json').read_text())
    if args.dry_run:
        print('Aanvraag gecontroleerd; geen gegevens verstuurd en geen API-tegoed gebruikt.')
        return
    store = ResultStore(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_TOKEN'])
    store.ensure_branch()
    existing, _ = store.read('results/'+key+'.json')
    if existing and existing.get('prompt_sha256') == key:
        validate_result(existing['result'], request['drivers'], brief)
        index_result(store, key, existing)
        (work/'result.json').write_text(json.dumps(existing, ensure_ascii=False, indent=2)+'\n')
        print('Dezelfde vergelijking is al bewaard; Gemini niet opnieuw aangeroepen.')
        return
    model = os.environ.get('GEMINI_MODEL') or 'gemini-3.8-flash'
    response_path = 'responses/'+key+'.json'
    saved_response, _ = store.read(response_path)
    if saved_response and saved_response.get('prompt_sha256') == key and saved_response.get('finish_reason') == 'STOP':
        print('Volledig ontvangen antwoord hergebruikt; Gemini niet opnieuw aangeroepen.')
        model = saved_response['model']
        result = validate_result(json.loads(saved_response['text']), request['drivers'], brief)
    else:
        api_key = os.environ.get('GEMINI_API_KEY', '').strip()
        if not api_key:
            raise ValueError('GitHub-secret GEMINI_API_KEY ontbreekt')
        def capture(value):
            saved = {'schema':'goat-ai-provider-response-v1','prompt_sha256':key,'model':model,
                     'generated_at':datetime.now(timezone.utc).isoformat(),**value}
            (work/'provider-output.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2)+'\n')
            if value['finish_reason'] == 'STOP':
                store.write(response_path,saved)
        result = generate(prompt, request['drivers'], api_key, model, capture=capture)
    validate_result(result, request['drivers'], brief)
    envelope = {'schema': 'goat-ai-result-v2', 'prompt_sha256': key, 'generated_at': datetime.now(timezone.utc).isoformat(),
                'model': model, 'request': prepared, 'result': result}
    (work/'result.json').write_text(json.dumps(envelope, ensure_ascii=False, indent=2)+'\n')
    store.write('results/'+key+'.json', envelope)
    index_result(store, key, envelope)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as f:
            f.write('## Gemini-vergelijking gereed\n\n'+result['conclusion']+'\n\nBronhash: `'+key+'`\n')
    print('Gemini-antwoord gecontroleerd en opgeslagen voor precies deze selectie en bronversie.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', default='.site')
    parser.add_argument('--output', default='storage/goat-ai-run')
    parser.add_argument('--request')
    parser.add_argument('--node', default='node')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, RuntimeError, requests.RequestException) as error:
        # Error text is controlled above; do not print request headers or tokens.
        print('Vergelijking niet gepubliceerd:', str(error) if not isinstance(error, requests.RequestException) else 'GitHub-verbinding niet geslaagd')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
