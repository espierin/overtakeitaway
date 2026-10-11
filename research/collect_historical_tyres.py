"""One-time archive of Pirelli's public historical race/strategy releases."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import hashlib, json, re, time, xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from f1_analysis.io import write_json, utcnow

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'analyses/sources/historical/pirelli'
STORE.mkdir(parents=True, exist_ok=True)


def fetch(url):
    key = hashlib.sha256(url.encode()).hexdigest(); meta = STORE / (key + '.json')
    if meta.exists():
        return json.loads(meta.read_text())
    item = {'url': url, 'publisher': 'Pirelli', 'retrieved_at': utcnow()}
    try:
        r = requests.get(url, timeout=(15, 50)); item['status'] = r.status_code
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            ld = soup.select_one('script[type="application/ld+json"]')
            schema = json.loads(ld.string) if ld and ld.string else {}
            date = schema.get('datePublished', '')
            if not date:
                match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', r.text)
                date = match[1] if match else ''
            item['published_at'] = date
            item['title'] = soup.h1.get_text(' ', strip=True) if soup.h1 else ''
            # Keep pre-2020 race originals; avoid archiving irrelevant modern
            # releases merely because the URL mentions the same circuit.
            if date and 2011 <= int(date[:4]) <= 2019:
                file = key + '.html'; (STORE / file).write_bytes(r.content)
                main = soup.select_one('#pp-main') or soup
                for el in main.select('script,style,.pp_sharethis,.pp_newsroom'):
                    el.decompose()
                article = main.get_text(' ', strip=True)
                (STORE / (key + '.txt')).write_text(article)
                item.update(file=file, text_file=key + '.txt', sha256=hashlib.sha256(r.content).hexdigest(),
                            pdf_links=list(dict.fromkeys(a['href'] for a in main.select('a[href]') if '.pdf' in a['href'])),
                            has_tyre_summary=bool(re.search(r'pit stop summary|tyre strategies|race strategies|race strategy|pits from|pitstop strategy', article, re.I)))
    except Exception as exc:
        item.update(status='request-failed', error=str(exc))
    write_json(meta, item); time.sleep(.3)
    return item


def main():
    sitemap = STORE / 'sitemap.xml'
    if not sitemap.exists():
        r = requests.get('https://press.pirelli.com/sitemap.xml', timeout=60); r.raise_for_status(); sitemap.write_bytes(r.content)
    root = ET.fromstring(sitemap.read_bytes()); urls = []
    for node in root.findall('{*}url'):
        url = node.findtext('{*}loc'); path = urlparse(url).path.strip('/')
        if '/' in path or not re.search(r'grand-prix|race|racing|victor|wins?|vettel|hamilton|rosberg|ricciardo|raikkonen|pit-stop|tyre-strateg', path, re.I):
            continue
        years = re.findall(r'\b(20\d\d)\b', path)
        if years and not any(2011 <= int(y) <= 2019 for y in years):
            continue
        urls.append(url)
    print('candidates', len(urls), flush=True)
    result = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch, url) for url in urls]
        for f in as_completed(futures):
            result.append(f.result())
            if len(result) % 50 == 0:
                print('pirelli', len(result), '/', len(urls), 'historical', sum(bool(r.get('file')) for r in result), flush=True)
                write_json(STORE / 'inventory.json', {'sources': result})
    write_json(STORE / 'inventory.json', {'sources': result})
    print('complete', len(result), 'historical', sum(bool(r.get('file')) for r in result), flush=True)


if __name__ == '__main__':
    main()
