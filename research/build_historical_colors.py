"""Extract dated livery colour evidence, expanding actual HTML row spans.

The resulting hexadecimal palette is illustrative, not a claim that historical
paint had an official digital specification. Primary timing-feed colours take
precedence in the renderer. Constructor references are not privateer liveries.
"""
from collections import defaultdict
from pathlib import Path
import csv, hashlib, io, json, re, zipfile
from bs4 import BeautifulSoup
from f1_analysis.historical_backfill import folded
from f1_analysis.io import write_json, utcnow

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://en.wikipedia.org/wiki/Formula_One_sponsorship_liveries'
MIRROR = 'https://newikis.com/en/Formula_One_sponsorship_liveries'
ALIASES = {'BRM': 'British Racing Motors', 'Team Lotus': 'Lotus (1958–1994)', 'Lotus': 'Lotus (2010–2011)',
           'Lotus F1': 'Lotus (2012–2015)', 'Brawn': 'Brawn GP', 'BAR': 'British American Racing',
           'Dallara': 'BMS Scuderia Italia', 'Lola': 'BMS Scuderia Italia', 'MF1': 'Midland', 'Spyker MF1': 'Midland',
           'Haas F1 Team': 'Haas', 'Embassy Hill': 'Hill', 'Euro Brun': 'EuroBrun', 'Red Bull': 'Red Bull Racing',
           'Theodore': 'Theodore Racing', 'Manor Marussia': 'Manor', 'Iso Marlboro': 'Frank Williams Racing Cars',
           'Politoys': 'Frank Williams Racing Cars', 'Mercedes': 'Mercedes-Benz', 'March': 'March Engineering',
           'Footwork': 'Arrows', 'Lambo': 'Modena', 'Leyton House': 'March Engineering'}
BASES = ('Cooper', 'Brabham', 'McLaren', 'Lotus', 'Shadow', 'Matra', 'BRM', 'March')
HEX = {'red': '#E52B36', 'rosso corsa': '#D40000', 'white': '#E4E9EF', 'black': '#171A20',
       'blue': '#287AC5', 'navy blue': '#183563', 'dark blue': '#24467A', 'light blue': '#71C7E5',
       'sky blue': '#71C7E5', 'french blue': '#287AC5', 'silver': '#B8C4CE', 'chrome': '#B8C4CE',
       'green': '#278F58', 'british racing green': '#176D49', 'light green': '#88C956',
       'dark green': '#176D49', 'yellow': '#F2D54C', 'fluorescent yellow': '#D8F232',
       'fluorescent green': '#AAE64D', 'orange': '#F28B27', 'gold': '#D3B46B', 'pink': '#EF94C4',
       'grey': '#A0AAB7', 'gray': '#A0AAB7', 'gray-green': '#667F70', 'dark metallic gray-green': '#536D60',
       'metallic gray': '#A0AAB7', 'dark grey': '#626C78', 'dark gray': '#626C78', 'purple': '#A889CF',
       'burgundy': '#A24D65', 'brown': '#A57754', 'dark red': '#AF3442', 'light yellow': '#F2D54C',
       'dark metallic green': '#176D49', 'dark orange': '#D57220', 'bright red': '#E52B36',
       'gray green': '#667F70', 'fluorescent red': '#F14750', 'pale blue': '#82B8D5',
       'deep blue': '#24467A', 'aqua green': '#56BDB1', 'pale green': '#92CA9A'}


def expanded(table):
    active = {}; result = []
    for tr in table.find_all('tr'):
        row = {col: value for col, (left, value) in active.items()}
        new = {}; col = 0
        for cell in tr.find_all(['th', 'td'], recursive=False):
            while col in row:
                col += 1
            value = cell.get_text(' ', strip=True)
            for offset in range(int(cell.get('colspan', 1))):
                row[col + offset] = value
                if int(cell.get('rowspan', 1)) > 1:
                    new[col + offset] = (int(cell['rowspan']) - 1, value)
            col += int(cell.get('colspan', 1))
        active = {c: (n - 1, v) for c, (n, v) in active.items() if n > 1}
        active.update(new)
        if row:
            result.append([row.get(i, '') for i in range(max(row) + 1)])
    return result


def years(value):
    found = re.findall(r'\b(19\d\d|20\d\d)\b', value)
    if not found:
        return []
    first, last = int(found[0]), int(found[-1])
    short = re.search(r'(19\d\d)\s*[–-]\s*(\d\d)\b', value)
    if short:
        last = int(short[1][:2] + short[2])
    return range(first, min(2019, last) + 1)


def main():
    source = ROOT / 'analyses/sources/historical/liveries/wikipedia-mirror.html'
    soup = BeautifulSoup(source.read_bytes(), 'html.parser')
    evidence = defaultdict(list)
    for table in soup.select('table'):
        rows = expanded(table)
        if not rows or not any('Main colour' in col for col in rows[0]):
            continue
        title = table.find_previous(['h2', 'h3']).get_text(' ', strip=True).replace('[edit]', '').strip()
        headers = rows[0]; color_col = next(i for i, c in enumerate(headers) if 'Main colour' in c)
        for row in rows[1:]:
            if len(row) <= color_col:
                continue
            for year in years(row[0]):
                evidence[title].append({'year': year, 'main': row[color_col], 'row': row,
                                        'driver': row[1] if headers[1].startswith('Driver') else None})
    package = next((ROOT / 'analyses/sources/jolpica').glob('*.zip'))
    with zipfile.ZipFile(package) as archive:
        teams = list(csv.DictReader(io.TextIOWrapper(archive.open('formula_one_team.csv'))))
        drivers = list(csv.DictReader(io.TextIOWrapper(archive.open('formula_one_driver.csv'))))
    records = []; unavailable = []; ambiguous = []; unrecognised = []
    for team in teams:
        name = team['name']; base = name
        for prefix in BASES:
            if name.startswith(prefix + '-'):
                base = 'Team Lotus' if prefix == 'Lotus' else prefix
                break
        label = ALIASES.get(base, base)
        groups = defaultdict(list)
        for e in evidence.get(label, []):
            groups[e['year']].append(e)
        for year, rows in groups.items():
            colors = {r['main'] for r in rows if r['main']}
            if len(colors) != 1:
                ambiguous.append({'team_id': team['id'], 'team': name, 'year': year, 'colors': sorted(colors)})
                # Some constructors fielded differently painted private entries.
                # Apply only a driver's independently unambiguous dated colour.
                for driver in drivers:
                    fullname = folded(driver['forename'] + ' ' + driver['surname'])
                    observed = {r['main'] for r in rows if r.get('driver') and fullname in folded(r['driver'])}
                    if len(observed) != 1: continue
                    main = next(iter(observed))
                    if re.search(r' or |Various', main, re.I): continue
                    first = re.split(r',| and |/| & | \(', main.lower())[0].strip(); value = HEX.get(first)
                    if not value: continue
                    records.append({'team_ids': [team['id']], 'driver_ids': [driver['id']], 'team': name,
                                    'from_year': year, 'to_year': year, 'main_colors': main,
                                    'primary_hex': value, 'display_hex': '#8994A3' if value == '#171A20' else value,
                                    'hex_method': 'illustrative-digital-palette', 'scope': 'documented-driver-entry-livery',
                                    'evidence': 'documented-secondary-livery-table', 'source_url': SOURCE + '#' + label.replace(' ', '_'),
                                    'retrieval_url': MIRROR, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
                continue
            color = next(iter(colors))
            first = re.split(r',| and |/| & | or | \(', color.lower())[0].strip()
            if first.startswith('white '):
                first = 'white'
            if first.startswith('black '):
                first = 'black'
            value = HEX.get(first)
            if not value:
                unrecognised.append({'team': name, 'year': year, 'color': color})
                continue
            # A livery row from modern ATS or Scuderia Italia does not describe
            # the unrelated 1963 ATS or earlier privateer Lola entrants.
            if (name == 'ATS' and year < 1977) or (name == 'Lola' and year != 1993):
                continue
            records.append({'team_ids': [team['id']], 'team': name, 'from_year': year, 'to_year': year,
                            'main_colors': color, 'primary_hex': value,
                            'display_hex': '#8994A3' if value == '#171A20' else value,
                            'hex_method': 'illustrative-digital-palette', 'scope': 'constructor-livery-reference',
                            'evidence': 'documented-secondary-livery-table', 'source_url': SOURCE + '#' + label.replace(' ', '_'),
                            'retrieval_url': MIRROR, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
        if not groups:
            unavailable.append({'team_id': team['id'], 'team': name, 'source_url': team['wikipedia'], 'status': 'no-dated-uniform-colour-in-livery-source'})
    curated_file = ROOT / 'research/historical-color-review.json'
    if curated_file.exists():
        for record in json.loads(curated_file.read_text())['records']:
            record = dict(record)
            team_names = record.pop('teams')
            record['team_ids'] = [t['id'] for t in teams if t['name'] in team_names]
            record.update(priority=10, hex_method='illustrative-digital-palette', scope=record.get('scope', 'constructor-livery-reference'))
            source_key = hashlib.sha256(record['source_url'].split('#')[0].encode()).hexdigest()
            metadata = ROOT / 'analyses/sources/historical/team-history' / (source_key + '.json')
            if metadata.exists():
                saved = json.loads(metadata.read_text())
                if saved.get('sha256'): record['source_sha256'] = saved['sha256']
                for key in ('archive_url','capture_timestamp'):
                    if saved.get(key): record[key] = saved[key]
            if record['source_url'].startswith(SOURCE):
                record.update(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),retrieval_url=MIRROR)
            records.append(record)
    output = {'schema': 1, 'created_at': utcnow(), 'source_url': SOURCE, 'retrieval_url': MIRROR,
              'method_nl': 'Historische hoofdkleur uit gedateerde kleurstellingen; hexwaarden zijn een schematisch palet. Donkere kleuren worden lichter getoond voor leesbaarheid. De referentie beschrijft de constructeur; privé-inschrijvingen kunnen afwijken. Oorspronkelijke timingkleuren gaan voor.',
              'method_en': 'Historical main colour from dated liveries; hex values form an illustrative palette. Dark colours are lightened for readability. The reference describes the constructor; private entrants may differ. Original timing colours take precedence.',
              'records': records, 'unavailable': unavailable, 'ambiguous': ambiguous, 'unrecognised': unrecognised}
    write_json(ROOT / 'assets/historical-team-colors.json', output)
    write_json(ROOT / 'analyses/sources/historical/liveries/extracted-evidence.json', dict(evidence))
    print('colors', len(records), 'teams', len({r['team_ids'][0] for r in records}), 'unavailable', len(unavailable), 'ambiguous', len(ambiguous), 'unrecognised', unrecognised)


if __name__ == '__main__':
    main()
