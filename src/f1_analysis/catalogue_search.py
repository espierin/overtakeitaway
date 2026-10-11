"""Compact race-entry reference for the catalogue's structured search."""
from pathlib import Path
import csv, io, json, zipfile, re, unicodedata

REFERENCE = 'catalogue-search-reference.json'

def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(text or '').lower()) if not unicodedata.combining(c))

def reference_from_zip(body):
    archive = zipfile.ZipFile(io.BytesIO(body))
    def table(name):
        return list(csv.DictReader(io.StringIO(archive.read('f1db-'+name+'.csv').decode('utf-8-sig'))))
    drivers = {d['id']: {'name': d['name'], 'code': d['abbreviation']} for d in table('drivers')}
    races = {r['id']: {'date': r['date'], 'circuit': r['circuitId'], 'entries': []} for r in table('races')}
    for result in table('races-race-results'):
        # DNS and failed qualification are race entries, not race participation.
        if result['positionText'] in ('DNS', 'DNQ', 'DNPQ', 'DNP', 'EX'):
            continue
        races[result['raceId']]['entries'].append([
            result['driverId'], result['positionNumber'] == '1',
            result['positionText'] == 'DNF' or bool(result['reasonRetired']) and result['positionText'] != 'DSQ',
            result['polePosition'] == 'true', result['fastestLap'] == 'true'])
    keyed = {f"{r['year']}-{r['round']}": races[r['id']] for r in table('races')}
    return {'schema': 2, 'source': 'https://github.com/f1db/f1db', 'drivers': drivers, 'races': keyed}

def load_reference(root):
    for path in (Path(root)/'assets'/REFERENCE, Path(__file__).parent/'assets'/REFERENCE):
        if path.exists():
            return json.loads(path.read_text())
    return {'drivers': {}, 'races': {}}

def race_entries(row, normalized, reference):
    saved = reference['races'].get(f"{row['year']}-{int(row.get('round') or 0)}", {})
    if saved.get('date') == row.get('date') or saved.get('circuit') and saved['circuit'] == row.get('circuitId'):
        return saved['entries']
    # New race data remain searchable before the historical reference is updated.
    results = {str(r['driver_number']): r for r in normalized.get('session_result', [])}
    jolpica = {str(r['number']): r for r in normalized.get('jolpica_results', [])}
    entries = []
    for driver in normalized.get('drivers', []):
        number = str(driver.get('driver_number', driver.get('number')))
        result = results.get(number, {})
        official = jolpica.get(number, {})
        status = official.get('status') or driver.get('status') or ''
        if fold(status) in ('did not start', 'did not qualify', 'did not prequalify', 'withdrawn') or result.get('dns'):
            continue
        name = driver.get('full_name') or driver.get('name')
        if not name:
            continue
        identity = next((key for key, d in reference['drivers'].items() if fold(d['name']) == fold(name)), None)
        if identity is None:
            identity = fold(name).replace(' ', '-')
            reference['drivers'][identity] = {'name': name, 'code': driver.get('name_acronym') or driver.get('code') or name.split()[-1][:3].upper()}
        win = str(official.get('position', result.get('position', driver.get('position')))) == '1'
        retired = result.get('dnf') is True or bool(status) and not re.match(r'^(Finished|\+\d+ Lap)', status, re.I) and fold(status) not in ('disqualified', 'excluded', 'onbekend', 'unknown')
        if fold(status) in ('disqualified', 'excluded'):
            retired = False
        # Do not guess an official pole from grid 1 (penalties and sprints can differ).
        pole = official.get('polePosition') is True or driver.get('pole_position') is True
        fastest = str(official.get('FastestLap', {}).get('rank')) == '1'
        entries.append([identity, win, retired, pole, fastest])
    return entries or row.get('search_entries', [])

def refresh_reference(root):
    """Update the search reference at most daily; retain usable data on failure."""
    from datetime import datetime, timezone
    from urllib.request import Request, urlopen
    root = Path(root)
    state_path = root/'_storage/catalogue-search-reference-state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    today = datetime.now(timezone.utc).date().isoformat()
    if state.get('checked') == today:
        return
    def fetch(url):
        with urlopen(Request(url, headers={'User-Agent': 'OvertakeItAway/1.0'}), timeout=30) as response:
            return response.read()
    release = json.loads(fetch('https://api.github.com/repos/f1db/f1db/releases/latest'))
    reference = load_reference(root)
    if reference.get('release') != release['tag_name'] or reference.get('schema') != 2:
        asset = next(a for a in release['assets'] if a['name'] == 'f1db-csv.zip')
        body = fetch(asset['browser_download_url'])
        reference = reference_from_zip(body)
        reference['release'] = release['tag_name']
        target = root/'assets'/REFERENCE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(reference, ensure_ascii=False, separators=(',', ':')))
        original = root/'_storage/search-sources'/f"f1db-{release['tag_name']}.zip"
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(body)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({'checked': today, 'release': release['tag_name']}))
