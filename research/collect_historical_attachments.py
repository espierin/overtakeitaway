"""Retain the actual downloadable Pirelli strategy charts and race PDFs."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
import hashlib, json, re, time
import requests
from bs4 import BeautifulSoup
from f1_analysis.io import write_json, utcnow

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'analyses/sources/historical/pirelli'

def fetch(url, article):
    key = hashlib.sha256(url.encode()).hexdigest()
    meta = STORE / (key + '.attachment.json')
    if meta.exists(): return json.loads(meta.read_text())
    result = {'url': url, 'article_url': article, 'retrieved_at': utcnow()}
    try:
        response = requests.get(url.replace('http://', 'https://'), timeout=(15, 50))
        result['status'] = response.status_code
        if response.status_code == 200:
            content = response.content
            ext = '.pdf' if content.startswith(b'%PDF') else '.jpg' if content.startswith(b'\xff\xd8') else '.png' if content.startswith(b'\x89PNG') else None
            if ext:
                (STORE / (key + ext)).write_bytes(content)
                result.update(file=key + ext, sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
            else: result['rejected'] = 'not-a-document-or-image'
    except requests.RequestException as exc: result.update(status='request-failed', error=str(exc))
    write_json(meta, result); time.sleep(.4)
    return result

def main():
    articles = json.loads((STORE / 'inventory.json').read_text())['sources']
    jobs = {}
    for article in articles:
        if not article.get('file') or not re.search(r'grand prix|formula 1|pirelli.*(?:debut|win)|(?:vettel|hamilton|rosberg).*win', article['title'], re.I): continue
        soup = BeautifulSoup((STORE / article['file']).read_text(), 'html.parser')
        for url in article.get('pdf_links', []): jobs[url] = article['url']
        for link in soup.select('a[data-sourcepath]'):
            title = link.get('data-title', '')
            if re.search(r'visual|strateg|race.*(?:en|english)|pit.*stop', title, re.I) and not re.search(r'quali|practice|preview', title, re.I):
                jobs[link['data-sourcepath']] = article['url']
    result = []
    print('attachments', len(jobs), flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch, url, article) for url, article in jobs.items()]
        for future in as_completed(futures):
            result.append(future.result())
            if len(result) % 25 == 0: print('saved', len(result), flush=True)
    write_json(STORE / 'attachments.json', {'sources': result})
    print('complete', len(result), sum(bool(r.get('file')) for r in result), flush=True)

if __name__ == '__main__': main()
