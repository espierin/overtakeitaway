"""GitHub-hosted Gemini comparisons. Keys are used only inside Actions."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import requests

DEFAULT_DRIVERS = ['max-verstappen', 'lewis-hamilton', 'juan-fangio', 'ayrton-senna']
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


def output_schema(ids):
    text = {'type': 'string'}
    return {'type': 'object', 'properties': {
        'summary': text, 'comparisons': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'driver': {'type': 'string', 'enum': ids}, 'strength': text, 'limitation': text},
            'required': ['driver', 'strength', 'limitation']}},
        'winner': {'type': ['string', 'null'], 'enum': ids+[None]},
        'runner_up': {'type': ['string', 'null'], 'enum': ids+[None]},
        'conclusion': text, 'confidence': {'type': 'string', 'enum': ['low', 'medium', 'high']},
        'assumptions': {'type': 'array', 'items': text}, 'limitations': {'type': 'array', 'items': text}},
        'required': ['summary', 'comparisons', 'winner', 'runner_up', 'conclusion', 'confidence', 'assumptions', 'limitations']}


def validate_result(result, ids):
    if not isinstance(result, dict) or not set(output_schema(ids)['required']) <= result.keys():
        raise ValueError('Gemini gaf geen volledige vergelijking terug')
    rows = result['comparisons']
    if not isinstance(rows, list) or len(rows) != len(ids) or {r.get('driver') for r in rows} != set(ids):
        raise ValueError('Het antwoord wijkt af van de geselecteerde rijders')
    for key in ('winner', 'runner_up'):
        if result[key] is not None and result[key] not in ids:
            raise ValueError('Onbekende rijder in de conclusie')
    if result['winner'] is not None and result['winner'] == result['runner_up']:
        raise ValueError('Winnaar en nummer twee zijn gelijk')
    if result['confidence'] not in ('low', 'medium', 'high'):
        raise ValueError('Ongeldige zekerheid')
    for key in ('summary', 'conclusion'):
        if not isinstance(result[key], str) or not result[key].strip():
            raise ValueError('Lege conclusie')
    for row in rows:
        if any(not isinstance(row.get(k), str) for k in ('strength', 'limitation')):
            raise ValueError('Ongeldige rijdertekst')
    for key in ('assumptions', 'limitations'):
        if not isinstance(result[key], list) or not all(isinstance(v, str) for v in result[key]):
            raise ValueError('Ongeldige toelichting')
    return result


def generate(prompt, ids, api_key, model, post=requests.post):
    if not re.fullmatch(r'gemini-[a-z0-9.-]+', model):
        raise ValueError('Ongeldige modelnaam')
    response = post('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',
        headers={'x-goog-api-key': api_key, 'Content-Type': 'application/json'},
        json={'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
              'generationConfig': {'maxOutputTokens': 10000, 'responseFormat': {'text': {
                  'mimeType': 'APPLICATION_JSON', 'schema': output_schema(ids)}}}}, timeout=(20, 240))
    # Never echo provider responses or headers into public Actions logs.
    if response.status_code != 200:
        raise RuntimeError(f'Gemini-aanvraag gestopt (HTTP {response.status_code}); geen betaald terugvalmodel gebruikt')
    candidates = response.json().get('candidates') or []
    if not candidates or candidates[0].get('finishReason') != 'STOP':
        raise ValueError('Gemini gaf geen afgerond antwoord; niets gepubliceerd')
    parts = candidates[0].get('content', {}).get('parts', [])
    text = ''.join(p.get('text', '') for p in parts if not p.get('thought'))
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
    if args.dry_run:
        print('Aanvraag gecontroleerd; geen gegevens verstuurd en geen API-tegoed gebruikt.')
        return
    store = ResultStore(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_TOKEN'])
    store.ensure_branch()
    existing, _ = store.read('results/'+key+'.json')
    if existing and existing.get('prompt_sha256') == key:
        validate_result(existing['result'], request['drivers'])
        print('Dezelfde vergelijking is al bewaard; Gemini niet opnieuw aangeroepen.')
        return
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not api_key:
        raise ValueError('GitHub-secret GEMINI_API_KEY ontbreekt')
    model = os.environ.get('GEMINI_MODEL') or 'gemini-3.8-flash'
    result = generate(prompt, request['drivers'], api_key, model)
    envelope = {'schema': 'goat-ai-result-v1', 'prompt_sha256': key, 'generated_at': datetime.now(timezone.utc).isoformat(),
                'model': model, 'request': prepared, 'result': result}
    (work/'result.json').write_text(json.dumps(envelope, ensure_ascii=False, indent=2)+'\n')
    store.write('results/'+key+'.json', envelope)
    index, _ = store.read('index.json')
    index = index or {'schema': 'goat-ai-index-v1', 'results': {}}
    index['results'][key] = {'file': 'results/'+key+'.json', 'drivers': request['drivers'], 'generated_at': envelope['generated_at']}
    store.write('index.json', index)
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
