"""One-time, resumable retrieval of original historical FIA timing documents.

Only public pages and links supplied by FIA are followed. Failed requests and
unavailable pages are retained in the inventory as well as successful downloads.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin
import hashlib, json, re, threading, time
import requests
from bs4 import BeautifulSoup
from f1_analysis.io import utcnow

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'analyses/sources/historical/fia'
STORE.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()


def fetch(url, kind='page'):
    key = hashlib.sha256(url.encode()).hexdigest()
    meta = STORE / (key + '.json')
    if meta.exists():
        saved = json.loads(meta.read_text())
        if saved.get('status') != 200 or (STORE / saved['file']).exists():
            return saved
    item = {'url': url, 'publisher': 'FIA', 'retrieved_at': utcnow(), 'kind': kind}
    try:
        for attempt in range(3):
            response = requests.get(url, timeout=(15, 60))
            if response.status_code not in (429, 500, 502, 503, 504):
                break
            time.sleep(min(20, 2 ** (attempt + 2)))
        item.update(status=response.status_code, final_url=response.url)
        if response.status_code == 200:
            pdf = response.content.startswith(b'%PDF-')
            if kind == 'pdf' and not pdf:
                item['status'] = 'not-pdf'
            else:
                name = key + ('.pdf' if pdf else '.html')
                (STORE / name).write_bytes(response.content)
                item.update(file=name, bytes=len(response.content),
                            sha256=hashlib.sha256(response.content).hexdigest())
    except requests.RequestException as exc:
        item['status'] = 'request-failed'
        item['error'] = str(exc)
    meta.write_text(json.dumps(item, ensure_ascii=False, indent=2) + '\n')
    time.sleep(.4)
    return item


def page_task(year, suffix, championship='fia-formula-one-world-championship'):
    url = f'https://www.fia.com/events/{championship}/season-{year}/{suffix}'
    item = fetch(url)
    item['year'] = year
    if item['status'] != 200:
        return item
    soup = BeautifulSoup((STORE / item['file']).read_bytes(), 'html.parser')
    item['title'] = soup.title.get_text(' ', strip=True) if soup.title else ''
    item['headings'] = [h.get_text(' ', strip=True) for h in soup.select('h1,h2,h3')]
    documents = {}
    for link in soup.select('a[href]'):
        href = urljoin(url, link['href'])
        title = link.get_text(' ', strip=True)
        if not title or ('/sites/default/files/' not in href and '/file/' not in href):
            continue
        # Only timing, race context and circuit geometry; exclude administrative
        # correspondence and press-transcript copyright material.
        if re.search(r'lap|sector|speed|pit stop|starting grid|classification|circuit|tyre|weather|race control', title, re.I):
            documents.setdefault(href, title)
    item['documents'] = [{'url': u, 'title': t} for u, t in documents.items()]
    return item


def main():
    rows = json.loads((ROOT / 'analyses/index.json').read_text())
    jobs = [(r['year'], f"{r['year']}-" + re.sub(r'[^a-z0-9]+', '-', r['meeting'].lower()).strip('-') + '-event-information')
            for r in rows if 2012 <= r['year'] <= 2013]
    # Drupal retained numbered event pages, whose suffix is not necessarily the
    # championship round. The actual event headings remain in the inventory.
    for year in range(2014, 2020):
        jobs.extend((year, 'eventtiming-information' + (f'-{n}' if n else '')) for n in range(25))
    jobs.extend((r['year'], re.sub(r'[^a-z0-9]+', '-', r['meeting'].lower()).strip('-') + '-event-information')
                for r in rows if r['year'] == 2014)
    jobs.extend((2015, 'event-timing-information' + (f'-{n}' if n else ''), 'fia-formula-1-world-championship') for n in range(25))
    pages = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(page_task, *job): job for job in jobs}
        for future in as_completed(futures):
            item = future.result(); pages.append(item)
            print('page', item['year'], item['status'], item.get('title', ''), len(item.get('documents', [])), flush=True)
            (STORE / 'inventory.json').write_text(json.dumps({'pages': pages}, ensure_ascii=False, indent=2))
    docs = {}
    for page in pages:
        for document in page.get('documents', []):
            docs.setdefault(document['url'], {**document, 'year': page['year'], 'event_headings': page.get('headings', [])})
    documents = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch, url, 'pdf'): d for url, d in docs.items()}
        for future in as_completed(futures):
            item = {**futures[future], **future.result()}; documents.append(item)
            if len(documents) % 25 == 0:
                print('documents', len(documents), '/', len(docs), 'saved', sum(d['status'] == 200 for d in documents), flush=True)
                (STORE / 'inventory.json').write_text(json.dumps({'pages': pages, 'documents': documents}, ensure_ascii=False, indent=2))
    (STORE / 'inventory.json').write_text(json.dumps({'pages': pages, 'documents': documents}, ensure_ascii=False, indent=2) + '\n')
    print('complete', len(pages), len(documents), flush=True)


if __name__ == '__main__':
    main()
