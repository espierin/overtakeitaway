"""Replay independently retained early timing, without changing race dashboards.

Atlas's numeric URL is not a season/round. The collector verifies its printed
event title, joins driver names within that event, and retains disagreements.
"""
from copy import deepcopy
from pathlib import Path
import re
import unicodedata


def folded(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower())


def match_driver(label, drivers):
    aliases = {'verstapen': 'josverstappen', 'schumacherm': 'michaelschumacher',
               'mschumacher': 'michaelschumacher', 'decesaris': 'andreadecesaris',
               'deangelis': 'eliodeangelis', 'lehto': 'jyrkijarvilehto'}
    key = folded(label)
    key = aliases.get(key, key)
    matches = []
    for driver in drivers:
        name = driver['name']; surname = name.split()[-1]
        names = {folded(name), folded(surname), folded(name[0]+surname), folded(surname+name[0])}
        if key in names or key == folded(driver.get('code', '')):
            matches.append(driver)
    return matches[0] if len(matches) == 1 else None


def parse_atlas(body, drivers):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, 'html.parser')
    records = []; unmatched = []; missing = 0
    for table in soup.select('table'):
        # Legacy HTML wraps the rows in a form inside the table.
        rows = [r for r in table.find_all('tr') if r.find_parent('table') is table]
        if not rows:
            continue
        header = rows[0].find_all(['td', 'th'], recursive=False)
        columns = {i: int(m[1]) for i, cell in enumerate(header)
                   if (m := re.fullmatch(r'Lap\s+(\d+)', cell.get_text(' ', strip=True)))}
        if not columns:
            continue
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'], recursive=False)
            if not cells:
                continue
            label = cells[0].get_text(' ', strip=True)
            driver = match_driver(label, drivers)
            if driver is None:
                unmatched.append(label); continue
            for i, lap in columns.items():
                text = cells[i].get_text(' ', strip=True) if i < len(cells) else ''
                match = re.fullmatch(r'(\d+):(\d{2}(?:\.\d+)?)', text)
                if not match or float(match[2]) >= 60 or int(match[1]) >= 999:
                    missing += 1; continue
                seconds = int(match[1])*60+float(match[2])
                if seconds > 0:
                    records.append({'driver': driver['driver_number'], 'lap': lap, 'duration': round(seconds, 3)})
    return {'title': soup.title.get_text(' ', strip=True) if soup.title else '',
            'laps': records, 'unmatched': unmatched, 'missing_cells': missing}


def apply_retained(root, year, round_number, payload):
    from .io import read_json
    path = Path(root)/'analyses/sources/driver-history-expansion'/f'{year}-{round_number:02}.json'
    if not path.exists():
        return payload, None
    saved = read_json(path)
    if saved['year'] != year or saved['round'] != round_number:
        raise ValueError('Early timing calendar mismatch')
    result = deepcopy(payload)
    existing = {(r['driver'], r['lap']): r for r in result.get('all_laps', [])}
    for row in saved['accepted_laps']:
        key = row['driver'], row['lap']
        if key not in existing:
            existing[key] = dict(row, tyre={'compound': 'UNKNOWN', 'age': None}, reasons=[])
        elif abs(existing[key]['duration']-row['duration']) > .11:
            raise ValueError('Previously reviewed early timing has changed')
    result['all_laps'] = list(existing.values())
    return result, {'source': saved['source'], 'accepted_laps': len(saved['accepted_laps']),
                    'conflicts': len(saved.get('conflicts', [])), 'method': 'retained-atlas-table-v1'}
