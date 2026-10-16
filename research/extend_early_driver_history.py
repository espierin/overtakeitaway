"""One-time Atlas Classics discovery and conservative timing preservation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import time
import requests
from f1_analysis.early_driver_history import parse_atlas
from f1_analysis.phase2 import extract

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT/'analyses/sources/driver-history-expansion'


def fetch(url):
    STORE.mkdir(parents=True, exist_ok=True)
    path = STORE/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if path.exists():
        return json.loads(path.read_text())
    record = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=(12, 35))
        sha = hashlib.sha256(response.content).hexdigest()
        (STORE/(sha+'.body')).write_bytes(response.content)
        record.update(status=response.status_code, sha256=sha, file=sha+'.body', bytes=len(response.content))
    except requests.RequestException as exc:
        record['error'] = str(exc)
    path.write_text(json.dumps(record, indent=2)+'\n')
    time.sleep(.4)
    return record


def main():
    index = fetch('https://www.atlasf1.com/0000/season.html')
    from bs4 import BeautifulSoup
    soup = BeautifulSoup((STORE/index['file']).read_bytes(), 'html.parser')
    ids = sorted({int(m[1]) for a in soup.select('a[href]')
                  if (m := re.search(r'raceid=(\d+)', a['href']))})
    calendar = {'1971 Italian': (1971, 9), '1983 USA-West': (1983, 2), '1984 Monaco': (1984, 6),
                '1993 European': (1993, 3), '1994 Brazilian': (1994, 1), '1995 Belgian': (1995, 11)}
    report = []
    for item_id in ids:
        source = fetch(f'https://www.atlasf1.com/0000/laptimes.html?raceid={item_id}')
        if source.get('status') != 200:
            report.append(source); continue
        body = (STORE/source['file']).read_bytes()
        title_soup = BeautifulSoup(body, 'html.parser')
        title = title_soup.title.get_text(' ', strip=True) if title_soup.title else ''
        matches = [value for name, value in calendar.items() if name in re.sub(r'\s+', ' ', title)]
        if len(matches) != 1:
            report.append({'url': source['url'], 'title': title, 'status': 'event-not-confirmed'}); continue
        year, round_number = matches[0]
        races = [(p, d) for p, d, _ in extract(ROOT, year)
                 if json.loads((p.parent/'data/normalized/archive.json').read_text())['round'] == round_number]
        if len(races) != 1:
            raise ValueError('Event not uniquely present locally')
        page, payload = races[0]
        parsed = parse_atlas(body, payload['drivers'])
        old = {(r['driver'], r['lap']): r['duration'] for r in payload.get('all_laps', [])}
        completed = {d['driver_number']: (d.get('result') or {}).get('number_of_laps') for d in payload['drivers']}
        accepted = []; conflicts = []; seen = set()
        for row in parsed['laps']:
            key = row['driver'], row['lap']
            if key in seen:
                raise ValueError('Duplicate Atlas observation')
            seen.add(key)
            if completed.get(key[0]) is not None and key[1] > completed[key[0]]:
                conflicts.append(dict(row, reason='beyond-classified-distance')); continue
            if key in old and abs(old[key]-row['duration']) > .11:
                conflicts.append(dict(row, reason='retained-time-disagrees', retained=old[key])); continue
            accepted.append(row)
        fastest_checks = []
        for key, duration in old.items():
            new = next((r['duration'] for r in accepted if (r['driver'], r['lap']) == key), None)
            if new is not None:
                fastest_checks.append({'driver': key[0], 'lap': key[1], 'difference_seconds': round(new-duration, 3)})
        winner=next((d for d in payload['drivers'] if d.get('finish')==1),None)
        winner_check=None
        if winner:
            rows=[r for r in accepted if r['driver']==winner['driver_number']]
            clock=(winner.get('result') or {}).get('duration')
            if isinstance(clock,str) and re.fullmatch(r'\d+:\d+:\d+(?:\.\d+)?',clock) and len(rows)==completed[winner['driver_number']]:
                h,m,s=map(float,clock.split(':'));elapsed=h*3600+m*60+s
                difference=round(sum(r['duration'] for r in rows)-elapsed,3)
                winner_check={'summed_laps':len(rows),'reported_seconds':elapsed,'difference_seconds':difference,
                              'status':'agrees_within_0.11s' if abs(difference)<=.11 else 'elapsed_discrepancy_retained_for_review'}
        saved = {'schema': 1, 'year': year, 'round': round_number, 'title': title,
                 'source': source, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                 'accepted_laps': accepted, 'conflicts': conflicts,
                 'unmatched': parsed['unmatched'], 'missing_cells': parsed['missing_cells'],
                 'fastest_lap_crosschecks': fastest_checks,
                 'winner_elapsed_crosscheck':winner_check,
                 'context': 'No verified tyre set, tyre age or clear-air observations. Single-race samples are not whole-season coverage.'}
        (STORE/f'{year}-{round_number:02}.json').write_text(json.dumps(saved, indent=2)+'\n')
        row = {k: saved[k] for k in ('year', 'round', 'title', 'unmatched', 'missing_cells', 'fastest_lap_crosschecks')}
        row.update(accepted_laps=len(accepted), conflicts=len(conflicts), source_url=source['url'])
        report.append(row); print(json.dumps(row), flush=True)
    (STORE/'atlas-audit.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
