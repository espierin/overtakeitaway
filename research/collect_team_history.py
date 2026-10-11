"""Retain constructor-history research and original team/museum corroboration."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse, unquote
import csv, hashlib, io, json, time, zipfile
import requests
from bs4 import BeautifulSoup
from f1_analysis.io import write_json, utcnow

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'analyses/sources/historical/team-history'
PRIMARY = [
 'https://www.formula1.com/en/latest/article/mclaren-liveries-through-the-years.3M1dkzZe78TyKvRN0ZAsht',
 'https://www.williamsf1.com/articles/f66fc017-8278-4ecd-9747-cfcd187ca2f6/the-different-shades-of-williams-racing-world-heritage-day',
 'https://classicteamlotus.co.uk/en/news/posts/2019/black-gold-for-black-white/',
 'https://www.ferrari.com/en-BE/formula1/1000-gp-mexican-1964',
 'https://www.ferrari.com/en-CA/formula1/158-f1',
 'https://www.maserati.com/us/en/news/f-tributo-special-edition',
 'https://newsroom.porsche.com/en/press-kits/Porsche-Museum/Porsche-Typ-804.html',
 'https://theoriginals.renault.com/en/f1-rs-01',
 'https://www.renault-trucks.com/en/newsroom/press-releases/t-high-renault-sport-racing-new-renault-trucks-limited-series',
 'https://legacy.allamericanracers.com/wp/eagle-f1-story/',
 'https://www.brabham.co.uk/history',
 'https://www.christies.com/en/lot/lot-2470837',
]


def fetch(url, retrieval=None, teams=()):
    STORE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest(); meta = STORE / (key + '.json')
    if meta.exists():
        return json.loads(meta.read_text())
    item = {'url': url, 'retrieval_url': retrieval or url, 'team_ids': list(teams), 'retrieved_at': utcnow(),
            'type': 'constructor-history-reference' if retrieval else 'primary-colour-corroboration'}
    try:
        r = requests.get(retrieval or url, timeout=(15, 60)); item['status'] = r.status_code
        if r.status_code == 200:
            path = STORE / (key + '.html'); path.write_bytes(r.content)
            s = BeautifulSoup(r.content, 'html.parser')
            for el in s.select('script,style'):
                el.decompose()
            text = s.get_text(' ', strip=True)
            import re
            excerpts = [text[max(0, m.start() - 100):m.end() + 160] for m in re.finditer(r'\b(?:livery|colour|color|painted|racing green|dark blue)\b', text, re.I)]
            item.update(file=path.name, sha256=hashlib.sha256(r.content).hexdigest(), color_contexts=excerpts[:40])
    except requests.RequestException as exc:
        item.update(status='request-failed', error=str(exc))
    write_json(meta, item); time.sleep(.4)
    return item


def main():
    package = next((ROOT / 'analyses/sources/jolpica').glob('*.zip'))
    with zipfile.ZipFile(package) as z:
        teams = list(csv.DictReader(io.TextIOWrapper(z.open('formula_one_team.csv'))))
    urls = {}
    for team in teams:
        if int(team['id']) > 208 or not team['wikipedia']:
            continue
        urls.setdefault(team['wikipedia'], []).append(team['id'])
    result = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch, url, 'https://newikis.com/en/' + unquote(urlparse(url).path.removeprefix('/wiki/')), ids) for url, ids in urls.items()]
        futures += [pool.submit(fetch, url) for url in PRIMARY]
        for f in as_completed(futures):
            result.append(f.result())
            if len(result) % 20 == 0:
                print('team sources', len(result), '/', len(futures), flush=True)
    write_json(STORE / 'inventory.json', {'sources': result})
    print('complete', len(result), sum(r['status'] == 200 for r in result), flush=True)


if __name__ == '__main__':
    main()
