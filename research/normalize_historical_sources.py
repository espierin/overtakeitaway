"""Parse preserved FIA race summaries and explicit Pirelli tyre changes.

Document content identifies the race, never the arbitrary FIA URL suffix.
The parser retains unknowns and does not convert sector maxima into lap data.
"""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import json, re, subprocess
from f1_analysis.historical_backfill import HistoricalDatabase, folded
from f1_analysis.io import write_json

ROOT = Path(__file__).resolve().parents[1]
FIA = ROOT / 'analyses/sources/historical/fia'
WAYBACK = ROOT / 'analyses/sources/historical/wayback'
PIRELLI = ROOT / 'analyses/sources/historical/pirelli'
DB = None
GP = None

def document_text(item, directory=FIA):
    if not item.get('file'): return item, ''
    path = directory / (Path(item['file']).stem + '.txt')
    if not path.exists():
        result = subprocess.run(['pdftotext', '-layout', str(directory / item['file']), str(path)], capture_output=True)
        if result.returncode: return item, ''
    return item, path.read_text(errors='replace')

def race_key(item, text):
    # Use the document's own event heading, falling back to the retained FIA
    # event page only when a GP is not printed in the document.
    lines = [l for l in text.splitlines() if re.search(r'GRAND PRIX|GRAN(?:DE)? PREMIO|GROSSER PREIS', l, re.I) and re.search(r'20\d\d', l)]
    heading = ' '.join(lines) if lines else ' '.join(item.get('event_headings', []))
    key = folded(heading)
    years = set(re.findall(r'\b(20\d\d)\b', heading))
    year = int(next(iter(years))) if len(years) == 1 else item.get('year')
    if item.get('year') is not None and year != item['year']: return None
    # Footer copyright must agree with the event metadata.
    copyright_years = set(re.findall(r'©\s*(20\d\d)', text))
    if copyright_years and str(year) not in copyright_years: return None
    candidates = []
    for (y, r), race in DB.races.items():
        if y != year: continue
        names = [GP[race['grandPrixId']]['fullName'], race['officialName']]
        if race['grandPrixId'] == 'malaysia': names.append('Malaysia Grand Prix')
        if race['grandPrixId'] == 'united-states': names.extend(['United States Grand Prix', 'US Grand Prix'])
        aliases = {'monaco':['grandprixdemonaco'], 'spain':['granpremiodeespana'], 'italy':['granpremioditalia','granpremiosantanderditalia'],
                   'brazil':['grandepremiodobrasil'], 'germany':['grosserpreisvondeutschland'], 'france':['grandprixdefrance']}
        tokens = aliases.get(race['grandPrixId'], [])
        if any(folded(n) in key for n in names if n) or any(n in key for n in tokens): candidates.append((y, r))
    return candidates[0] if len(candidates) == 1 else None

def column_rows(text, kind):
    first = '\n'.join(text.splitlines()[:10]).lower()
    if not re.search(r'\brace\b', first) or re.search(r'qualifying|practice', first): return []
    labels = ('sector', 'intermediate', 'finish line')
    header = next((l for l in text.splitlines() if sum(l.lower().count(v) for v in labels) >= 3), '')
    starts = [m.start() for m in re.finditer(r'SECTOR\s*[123]|INTERMEDIATE\s*[12]|FINISH LINE', header, re.I)]
    if len(starts) != 3: return []
    rows = []
    for line in text.splitlines():
        rank = re.match(r'\s*(\d+)\s+', line)
        if not rank: continue
        for m in re.finditer(r'\b(\d{1,2})\s+([A-Za-z][A-Za-z.\-\x27 ]*?)\s{2,}(\d{1,3}\.\d{1,3})\b', line):
            col = min(range(3), key=lambda i: abs(m.start() - starts[i]))
            value = float(m[3])
            if (kind == 'best_sectors' and not 5 <= value <= 100) or (kind == 'maximum_speeds' and not 50 <= value <= 400): continue
            rows.append({'number': int(m[1]), 'driver_text': m[2].strip(), 'rank': int(rank[1]),
                         'sector' if kind == 'best_sectors' else 'location': col + 1,
                         'seconds' if kind == 'best_sectors' else 'kph': value})
    if len({(r['number'], r.get('sector', r.get('location'))) for r in rows}) != len(rows): return []
    return rows

def normalize_fia():
    inventory = json.loads((FIA / 'inventory.json').read_text())
    result = defaultdict(lambda: {'documents': [], 'best_sectors': [], 'maximum_speeds': []})
    audit = []
    documents = list(inventory['documents'])
    archive_inventory = WAYBACK / 'inventory.json'
    if archive_inventory.exists():
        documents.extend({**d,'directory':str(WAYBACK)} for d in json.loads(archive_inventory.read_text())['documents'] if d.get('file','').endswith('.pdf'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        for item, text in pool.map(lambda d:document_text(d,Path(d.get('directory',FIA))), documents):
            key = race_key(item, text)
            if not key:
                audit.append({'url': item['url'], 'status': 'race-not-uniquely-confirmed'}); continue
            title = item['title']; lower = title.lower()
            # Session disambiguation is printed in the PDF itself.
            top = '\n'.join(text.splitlines()[:12]).lower()
            session = 'race' if re.search(r'\brace\b', top) and not re.search(r'qualifying|practice', top) else 'other'
            if session == 'race' or 'circuit map' in lower or 'starting grid' in lower:
                translations = {'best sector times': ('Beste sectortijden', 'Best sector times'), 'maximum speeds': ('Maximumsnelheden', 'Maximum speeds'),
                                'pit stop summary': ('Pitstopoverzicht', 'Pit stop summary'), 'lap chart': ('Rondeposities', 'Lap chart'),
                                'lap analysis': ('Rondeanalyse', 'Lap analysis'), 'fastest laps': ('Snelste ronden', 'Fastest laps'),
                                'speed trap': ('Snelheidsmeting', 'Speed trap'), 'classification': ('Uitslag', 'Classification'),
                                'starting grid': ('Startopstelling', 'Starting grid'), 'circuit map': ('Circuitkaart', 'Circuit map')}
                label = next((v for k, v in translations.items() if k in lower), ('Officieel document', 'Official document'))
                result[key]['documents'].append({'url': item['url'], 'title': title, 'label': {'nl': label[0], 'en': label[1]},
                                               'sha256': item['sha256'], 'file': item['file'], 'session': session,
                                               **{k:item[k] for k in ('archive_url','capture_timestamp') if k in item}})
            kind = 'best_sectors' if 'best sector' in lower else 'maximum_speeds' if 'maximum speeds' in lower else None
            if kind:
                rows = column_rows(text, kind)
                valid_numbers = {int(r['driverNumber']) for r in DB.sessions[DB.races[key]['id']].get('race-results', []) if r['driverNumber']}
                if any(r['number'] not in valid_numbers for r in rows): rows = []
                for row in rows: row.update(source_url=item['url'], source_sha256=item['sha256'])
                # Multiple versions are retained as source documents, while the
                # last complete summary supplies one observation per car/sector.
                if rows and len(rows) >= len(result[key][kind]): result[key][kind] = rows
                audit.append({'url': item['url'], 'race': key, 'kind': kind, 'records': len(rows)})
    output = {f'{y}-{r:02}': value for (y, r), value in result.items()}
    write_json(FIA / 'normalized.json', {'races': output, 'audit': audit})
    print('FIA normalized', len(output), 'sectors', sum(len(r['best_sectors']) for r in output.values()), 'speed points', sum(len(r['maximum_speeds']) for r in output.values()), flush=True)

COMPOUNDS = {'soft': 'SOFT', 'medium': 'MEDIUM', 'hard': 'HARD', 'supersoft': 'SUPERSOFT', 'super-soft': 'SUPERSOFT',
             'ultrasoft': 'ULTRASOFT', 'hyper-soft': 'HYPERSOFT', 'hypersoft': 'HYPERSOFT', 'intermediate': 'INTERMEDIATE', 'wet': 'WET'}

def explicit_tyre_changes(text):
    # Only structured statements specifying the lap, driver and tyre. A partial
    # statement without a destination remains partial, never a guessed compound.
    compound = '|'.join(sorted(COMPOUNDS, key=len, reverse=True))
    expression = r'Lap\s*(\d+)\s*[:–-]?\s*([A-Za-z.\-\x27 ]{2,40}?)\s+pits?\s+from\s+(?:the\s+)?(' + compound + r')(?:\s+tyres?(?=\s+to))?(?:\s+to\s+(?:the\s+)?(' + compound + r'))?\s+tyres?\b'
    return [{'lap': int(m[1]), 'driver_text': m[2].strip(), 'from': COMPOUNDS[m[3].lower()],
             'to': COMPOUNDS.get((m[4] or '').lower()), 'source_statement': m[0]} for m in re.finditer(expression, text, re.I)]

def normalize_pirelli():
    result = defaultdict(lambda: {'sources': [], 'changes': []}); unresolved = []
    # Read completed per-article metadata; the crawler's progress inventory can
    # still contain only a partial set during a resumed download.
    articles = [json.loads(p.read_text()) for p in PIRELLI.glob('*.json') if re.fullmatch(r'[a-f0-9]{64}\.json', p.name)]
    for item in articles:
        if not item.get('text_file'): continue
        text = (PIRELLI / item['text_file']).read_text()
        published = date.fromisoformat(item['published_at'][:10])
        candidates = [(key, race) for key, race in DB.races.items() if 0 <= (published - date.fromisoformat(race['date'])).days <= 1]
        if len(candidates) != 1: continue
        key, race = candidates[0]
        title = item['title'].lower()
        if re.search(r'qualifying|practice|preview|superbike|cycling|gt world', title): continue
        if not re.search(r'grand prix|formula (?:one|1)|pirelli.*debut|wins?|victory|triumph', title): continue
        # Matching the calendar alone is insufficient: require F1 and either
        # the actual Grand Prix name or known winner in the report.
        gpname = GP[race['grandPrixId']]['name'].lower()
        winner = next((r['driverId'].split('-')[-1] for r in DB.sessions[race['id']].get('race-results', []) if r['positionNumber'] == '1'), '')
        if not (gpname in text.lower() or winner and winner in text.lower()) or not re.search(r'formula (?:one|1)|grand prix', text, re.I): continue
        changes = explicit_tyre_changes(text)
        result[key]['sources'].append({k: item[k] for k in ('url', 'title', 'published_at', 'sha256')})
        for row in changes: row.update(source_url=item['url'], source_sha256=item['sha256'])
        result[key]['changes'].extend(changes)
    output = {f'{y}-{r:02}': value for (y, r), value in result.items()}
    write_json(PIRELLI / 'normalized.json', {'races': output, 'unresolved': unresolved})
    print('Pirelli normalized', len(output), 'explicit changes', sum(len(v['changes']) for v in output.values()), flush=True)

if __name__ == '__main__':
    DB = HistoricalDatabase(ROOT / 'storage/search-data/f1db-csv.zip')
    GP = {g['id']: g for g in DB.tables['grands-prix']}
    normalize_fia(); normalize_pirelli()
