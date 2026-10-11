"""Recover original FIA documents with capture timestamps and byte hashes.

CDX is discovery only. A downloaded response must be a real PDF, and its
printed event/year is checked by the normalization step before any join.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
import hashlib, json, re, time, subprocess
import requests
from f1_analysis.io import utcnow, write_json

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'analyses/sources/historical/wayback'
STORE.mkdir(parents=True, exist_ok=True)


def query(year):
    params = [('url', 'fia.com/en-GB/mediacentre/f1_media/Documents/*'),
              ('output', 'json'), ('filter', 'statuscode:200'),
              ('filter', 'mimetype:application/pdf'), ('filter', 'original:.*(?:race[-_]|circuit).*'),
              ('collapse', 'digest'), ('from', str(year)), ('to', str(year)), ('limit', '10000')]
    url = 'https://web.archive.org/cdx/search/cdx?' + urlencode(params)
    key = hashlib.sha256(url.encode()).hexdigest()
    saved = STORE / (key + '.json')
    if saved.exists():
        meta = json.loads(saved.read_text())
        if meta['status'] == 200:
            return json.loads((STORE / meta['file']).read_text())
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=(15, 60))
            if response.status_code == 200: break
        except requests.RequestException:
            response = None
        time.sleep(2 + attempt)
    if response is None: return []
    name = key + '.body'; (STORE / name).write_bytes(response.content)
    write_json(saved, {'request_url': url, 'status': response.status_code, 'file': name,
                      'retrieved_at': utcnow(), 'sha256': hashlib.sha256(response.content).hexdigest()})
    print('CDX', year, response.status_code, len(response.content), flush=True)
    return response.json() if response.status_code == 200 else []


def download(row):
    original = row['original']; capture = row['timestamp']
    url = 'https://web.archive.org/web/' + capture + 'id_/' + original
    key = hashlib.sha256(url.encode()).hexdigest(); saved = STORE / (key + '.json')
    if saved.exists():
        meta = json.loads(saved.read_text())
        if meta.get('file', '').endswith('.pdf') and meta.get('url') and meta.get('title') and (STORE / meta['file']).exists(): return meta
    meta = {'url': original, 'archive_url': url, 'capture_timestamp': capture,
            'retrieved_at': utcnow(), 'publisher': 'FIA', 'archive_publisher': 'Internet Archive',
            'cdx_digest': row['digest'], 'kind': 'pdf'}
    for attempt in range(2):
        try:
            response = requests.get(url, timeout=(12, 45))
            meta['status'] = response.status_code
            if response.status_code == 200 and response.content.startswith(b'%PDF-'):
                name = key + '.pdf'; (STORE / name).write_bytes(response.content)
                meta.update(file=name, bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest())
                break
            if response.status_code == 200: meta['status'] = 'not-pdf'
            if response.status_code in (403, 404): break
        except requests.RequestException as exc:
            meta.update(status='request-failed', error=str(exc))
            # An ordinary curl request can recover transient protocol/connection
            # failures. Access-denied HTTP responses are never retried this way.
            if isinstance(exc, requests.ConnectionError):
                result = subprocess.run(['curl','--silent','--show-error','--fail','--location','--max-time','45',url], capture_output=True)
                if result.returncode == 0 and result.stdout.startswith(b'%PDF-'):
                    name = key + '.pdf'; (STORE / name).write_bytes(result.stdout)
                    meta.update(status=200,file=name,bytes=len(result.stdout),sha256=hashlib.sha256(result.stdout).hexdigest(),access_method='ordinary-curl-after-connection-failure')
                    meta.pop('error',None)
                    break
        time.sleep(2)
    name = original.rsplit('/', 1)[-1].lower()
    titles = {'analysis':'Lap analysis', 'chart':'Lap chart', 'classification':'Classification',
              'grid':'Starting grid', 'history':'Race history', 'laps':'Fastest laps',
              'sectors':'Best sector times', 'speeds':'Maximum speeds', 'summary':'Pit stop summary',
              'trap':'Speed trap', 'circuit':'Circuit map', 'drivers':'Driver standings', 'constructors':'Constructor standings'}
    meta['title'] = next((title for token, title in titles.items() if name.endswith('-' + token + '.pdf') or name.endswith('_' + token + '.pdf')), 'Official document')
    write_json(saved, meta)
    return meta


def main():
    captures = {}
    # Reuse the broad CDX result already obtained, including URLs whose later
    # capture lookup might temporarily fail.
    for path in STORE.glob('*.json'):
        meta = json.loads(path.read_text())
        if 'body' not in meta or '/cdx/' not in meta.get('request_url', '') or meta.get('status') != 200: continue
        rows = json.loads(meta['body'])
        for row in rows[1:]:
            item = dict(zip(rows[0], row))
            if re.search(r'/(?:[^/]*race[-_]|[^/]*circuit)', item['original'], re.I):
                captures[(item['original'], item['digest'])] = item
    with ThreadPoolExecutor(max_workers=2) as pool:
        for rows in pool.map(query, range(2008, 2013)):
            if not rows: continue
            for row in rows[1:]:
                item = dict(zip(rows[0], row)); captures.setdefault((item['original'], item['digest']), item)
    documents = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(download, row) for row in captures.values()]
        for future in as_completed(futures):
            documents.append(future.result())
            if len(documents) % 20 == 0:
                write_json(STORE / 'inventory.json', {'documents': documents})
                print('Wayback documents', len(documents), '/', len(captures), 'PDFs', sum(d.get('file', '').endswith('.pdf') for d in documents), flush=True)
    write_json(STORE / 'inventory.json', {'documents': documents})
    print('Wayback complete', len(documents), 'PDFs', sum(d.get('file', '').endswith('.pdf') for d in documents), flush=True)


if __name__ == '__main__': main()
