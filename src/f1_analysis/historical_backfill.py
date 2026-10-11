"""Persistent historical supplements, with field provenance and conservative joins.

Original Jolpica entries are never rewritten. Shared cars keep entry IDs, and
conflicting observations stay in an audit instead of being silently replaced.
"""
from collections import defaultdict, Counter
from pathlib import Path
import argparse, csv, hashlib, io, json, re, sqlite3, unicodedata, zipfile
from .io import read_json, write_json, utcnow
from functools import lru_cache

F1DB_URL = 'https://github.com/f1db/f1db/releases/tag/v2026.17.0'
LIVERY_URL = 'https://en.wikipedia.org/wiki/Formula_One_sponsorship_liveries'
CHART_URL = 'https://github.com/mclarenmp4-22/f1resultsdatabase/releases/tag/v2.10.1%2B20260921'


def folded(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower())


def numeric(value):
    try:
        return int(value) if value not in ('', None) else None
    except (TypeError, ValueError):
        return None


def millis(value):
    value = numeric(value)
    return value / 1000 if value is not None else None


class HistoricalDatabase:
    def __init__(self, package):
        self.package = Path(package)
        self.sha256 = hashlib.sha256(self.package.read_bytes()).hexdigest()
        self.tables = {}
        with zipfile.ZipFile(self.package) as archive:
            for name in archive.namelist():
                self.tables[name.removeprefix('f1db-').removesuffix('.csv')] = list(csv.DictReader(io.TextIOWrapper(archive.open(name))))
        self.drivers = {d['id']: d for d in self.tables['drivers']}
        self.birthdays = defaultdict(list)
        self.names = defaultdict(set)
        for driver in self.drivers.values():
            self.birthdays[driver['dateOfBirth']].append(driver)
            for key in ('name', 'fullName'):
                self.names[folded(driver[key])].add(driver['id'])
        self.races = {(int(r['year']), int(r['round'])): r for r in self.tables['races'] if int(r['year']) <= 2019}
        self.sessions = defaultdict(dict)
        for name, rows in self.tables.items():
            if not name.startswith('races-'):
                continue
            for row in rows:
                if int(row['year']) <= 2019:
                    self.sessions[row['raceId']].setdefault(name.removeprefix('races-'), []).append(row)

    def match_driver(self, raw_driver):
        name = folded(raw_driver['forename'] + ' ' + raw_driver['surname'])
        aliases = {'princebira': 'birabongse-bhanudej', 'yvescabantous': 'yves-giraud-cabantous'}
        if name in aliases:
            driver = self.drivers.get(aliases[name])
            if driver and driver['dateOfBirth'] == raw_driver.get('date_of_birth'):
                return driver['id']
        choices = list(self.names.get(name, ()))
        if len(choices) == 1:
            return choices[0]
        # A date of birth alone is not a join key: also require a surname match
        # or the explicit Jolpica career reference (e.g. JJ Lehto / Järvilehto).
        birthday = raw_driver.get('date_of_birth')
        surname = folded(raw_driver['surname'])
        reference = folded(raw_driver.get('reference', ''))
        choices = [d for d in self.birthdays.get(birthday, [])
                   if surname == folded(d['lastName']).removesuffix('jr') or reference == folded(d['id'])
                   or reference == folded(d['lastName'])]
        return choices[0]['id'] if len(choices) == 1 else None

    def supplement(self, data, raw):
        race = self.races.get((data['year'], data['round']))
        if not race:
            return None
        # Calendar disagreement needs review rather than an unchecked join.
        if race['date'] != data['date']:
            raise ValueError(f"Race date differs: {data['year']}/{data['round']}: {data['date']} / {race['date']}")
        sessions = self.sessions[race['id']]
        matches = {}; unmatched = []; conflicts = []
        originals = {entry['sessionentry']['id']: entry for entry in raw['entries']}
        for driver in data['drivers']:
            source = originals[driver['id']]
            career = self.match_driver(source['driver'])
            if career is None:
                unmatched.append({'entry_id': driver['id'], 'name': driver['name']})
                continue
            matches[driver['id']] = career
            for key, column in [('position', 'positionNumber'), ('grid', 'gridPositionNumber'), ('completed_laps', 'laps')]:
                choices = [r for r in sessions.get('race-results', []) if r['driverId'] == career and numeric(r.get('driverNumber')) == driver['number']]
                if len(choices) == 1:
                    value = numeric(choices[0].get(column))
                    if driver.get(key) is not None and value is not None and driver[key] != value:
                        conflicts.append({'entry_id': driver['id'], 'field': key, 'Jolpica': driver[key], 'F1DB': value})
            for pit in sessions.get('pit-stops', []):
                if pit['driverId'] != career or numeric(pit.get('driverNumber')) != driver['number']: continue
                existing = [p for p in driver['pitstops'] if p['stop'] == numeric(pit['stop'])]
                if len(existing) != 1: continue
                for field, value in [('lap', numeric(pit['lap'])), ('duration', millis(pit['timeMillis']))]:
                    original = existing[0].get(field)
                    if original is not None and value is not None and abs(original-value) > .001:
                        conflicts.append({'entry_id':driver['id'], 'field':f"pitstop.{pit['stop']}.{field}", 'Jolpica':original, 'F1DB':value})
        return {'schema': 1, 'source': {'publisher': 'F1DB', 'url': F1DB_URL, 'sha256': self.sha256, 'license': 'CC BY 4.0'},
                'race': race, 'entry_drivers': matches, 'unmatched_entries': unmatched, 'conflicts': conflicts,
                'sessions': dict(sessions)}

    def sqlite(self, destination):
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_suffix('.partial')
        temp.unlink(missing_ok=True)
        with sqlite3.connect(temp) as db:
            for name, rows in self.tables.items():
                if not rows:
                    continue
                table = name.replace('-', '_')
                columns = list(rows[0])
                if 'year' in columns:
                    rows = [r for r in rows if numeric(r['year']) is not None and int(r['year']) <= 2019]
                db.execute(f'CREATE TABLE "{table}" (' + ','.join(f'"{c}" TEXT' for c in columns) + ')')
                db.executemany(f'INSERT INTO "{table}" VALUES (' + ','.join('?' for c in columns) + ')',
                               ([row[c] for c in columns] for row in rows))
                for column in ('id', 'raceId', 'year', 'driverId', 'constructorId'):
                    if column in columns:
                        db.execute(f'CREATE INDEX "{table}_{column}" ON "{table}" ("{column}")')
            db.execute('CREATE TABLE provenance (publisher TEXT, url TEXT, sha256 TEXT, retained_at TEXT)')
            db.execute('INSERT INTO provenance VALUES (?, ?, ?, ?)', ('F1DB', F1DB_URL, self.sha256, utcnow()))
            db.commit()
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Historical database integrity check failed')
        temp.replace(destination)


class HistoricalChartDatabase:
    """Retained StatsF1/F1/MotorsportStats compilation; never inferred positions."""
    def __init__(self, path, reference):
        self.db = sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro', uri=True)
        self.db.row_factory = sqlite3.Row
        self.races = {(r['Season'], r['RoundNumber']): dict(r) for r in self.db.execute('SELECT * FROM GrandsPrix WHERE Season<=2019')}
        self.careers = {}
        for r in self.db.execute('SELECT ID,Name,Birthdate FROM Drivers'):
            parts = r['Name'].rsplit(' ', 1)
            raw = {'forename':parts[0], 'surname':parts[-1], 'date_of_birth':r['Birthdate'], 'reference':r['Name']}
            self.careers[r['ID']] = reference.match_driver(raw)
        self.charts = defaultdict(list); self.pits = defaultdict(list); self.speeds = defaultdict(list)
        for r in self.db.execute("SELECT GrandPrixID,DriverID,Lap,Position,TimeInSeconds FROM LapByLap WHERE Session='Race'"):
            self.charts[r['GrandPrixID']].append(dict(r))
        for r in self.db.execute("SELECT * FROM PitStopSummary WHERE SessionName='Race'"):
            self.pits[r['GrandPrixID']].append(dict(r))
        for r in self.db.execute("SELECT * FROM MaxSpeeds WHERE SessionName='Race'"):
            self.speeds[r['GrandPrixID']].append(dict(r))

    def supplement(self, data, primary):
        race = self.races.get((data['year'], data['round']))
        if not race: return {}
        if race['DateInDateTime'] != data['date']: raise ValueError('Retained lap-chart calendar mismatch')
        by_career = defaultdict(list)
        for d in data['drivers']: by_career[primary['entry_drivers'].get(d['id'])].append(d)
        car_entries = Counter(d['number'] for d in data['drivers'])
        observed = []; ambiguous = []; conflicts = []; seen = set()
        for r in self.charts[race['ID']]:
            career = self.careers.get(r['DriverID']); candidates = by_career.get(career, []) if career else []
            if len(candidates) != 1:
                ambiguous.append({'source_driver_id':r['DriverID'], 'lap':r['Lap'], 'reason':'entry-not-unique'})
                continue
            d = candidates[0]; key = (d['id'], r['Lap'])
            if car_entries[d['number']] != 1:
                ambiguous.append({'source_driver_id':r['DriverID'], 'lap':r['Lap'], 'reason':'shared-car-driver-not-timestamped'})
                continue
            if r['Lap'] <= 0 or r['Position'] is None or r['Position'] <= 0: continue
            if key in seen: raise ValueError('Duplicate retained lap-chart observation')
            seen.add(key)
            observed.append({'entry_id':d['id'], 'career_id':career, 'number':d['number'], 'lap':r['Lap'], 'position':r['Position'], 'seconds':r['TimeInSeconds']})
            original = next((l for l in d['laps'] if l['lap']==r['Lap']), None)
            if original and original.get('position') is not None and original['position'] != r['Position']:
                conflicts.append({'entry_id':d['id'], 'lap':r['Lap'], 'field':'lap.position', 'Jolpica':original['position'], 'StatsF1':r['Position']})
        pits = []
        for r in self.pits[race['ID']]:
            career = self.careers.get(r['DriverID']); candidates = by_career.get(career, []) if career else []
            candidates = [d for d in candidates if d['number']==r['Number']]
            if len(candidates) != 1: continue
            pits.append({'entry_id':candidates[0]['id'], 'career_id':career, 'number':r['Number'], 'stop':r['StopNumber'],
                         'lap':r['Lap'], 'duration':r['TimeInSeconds'], 'local_time':r['TimeOfDayStopped'] or None})
        speeds = []
        for r in self.speeds[race['ID']]:
            career = self.careers.get(r['DriverID']); candidates = by_career.get(career, []) if career else []
            if len(candidates)==1:
                speeds.append({'entry_id':candidates[0]['id'],'career_id':career,'number':candidates[0]['number'], 'position':r['Position'], 'point':r['TimingPoint'], 'kph':r['SpeedKph']})
        return {'source':{'publisher':'mclarenmp4-22/f1resultsdatabase', 'url':CHART_URL, 'license':'ODbL 1.0',
                          'sha256':'27b0e561ecd7e9466e390abcb66dd03160629e7481edfd9ad2cddcea87b07fc3',
                          'origins':{'positions':'STATS F1 lap charts', 'pitstops':'Formula1.com results', 'maximum_speeds':'MotorsportStats'}},
                'weather_description':race['Weather'] or None, 'lap_chart':observed, 'pitstops':pits, 'maximum_speeds':speeds,
                'ambiguous_entries':[{'source_driver_id':driver,'reason':reason,'observations':count}
                                     for (driver,reason),count in Counter((r['source_driver_id'],r['reason']) for r in ambiguous).items()], 'conflicts':conflicts}


def augment(data, supplement, colors=None):
    """Add individually traceable observations; leave existing race results intact."""
    out = json.loads(json.dumps(data))
    out['historical_supplement'] = supplement
    by_career = defaultdict(list)
    for driver in out['drivers']:
        by_career[supplement['entry_drivers'].get(driver['id'])].append(driver)
    added = {'pitstops': 0, 'lap_times': 0, 'lap_positions':0, 'additional_lap_times':0, 'grid': 0, 'colors': 0}
    for driver in out['drivers']:
        if colors:
            choice = color_for(colors, driver['team_id'], data['year'], data['round'], driver.get('driver_id'))
            if choice:
                driver['color'] = choice['display_hex']; driver['color_source'] = choice; added['colors'] += 1
        career = supplement['entry_drivers'].get(driver['id'])
        if not career:
            continue
        results = [r for r in supplement['sessions'].get('race-results', []) if r['driverId'] == career and numeric(r.get('driverNumber')) == driver['number']]
        if len(results) == 1 and driver.get('grid') is None:
            grid = numeric(results[0]['gridPositionNumber'])
            if grid is not None and grid > 0:
                driver['grid'] = grid; added['grid'] += 1
        fastest = [r for r in supplement['sessions'].get('fastest-laps', []) if r['driverId'] == career and numeric(r.get('driverNumber')) == driver['number']]
        if len(fastest) == 1:
            driver['fastest_lap'] = {**fastest[0], 'seconds': millis(fastest[0]['timeMillis']), 'source': 'F1DB'}
        for pit in supplement['sessions'].get('pit-stops', []):
            if pit['driverId'] != career or numeric(pit.get('driverNumber')) != driver['number'] or len(by_career[career]) != 1:
                continue
            stop, lap = numeric(pit['stop']), numeric(pit['lap'])
            existing = [p for p in driver['pitstops'] if p['stop'] == stop]
            if not existing:
                driver['pitstops'].append({'stop': stop, 'lap': lap, 'local_time': None,
                                          'duration': millis(pit['timeMillis']), 'source': 'F1DB', 'duration_kind': 'source-reported-pit-duration'})
                added['pitstops'] += 1
            elif len(existing) == 1 and existing[0]['lap'] == lap and existing[0].get('duration') is None:
                existing[0]['duration'] = millis(pit['timeMillis']); existing[0]['duration_source'] = 'F1DB'
        driver['pitstops'].sort(key=lambda p: p['stop'] or 999)
        # A race-wide fastest lap is a genuine lap observation, not a complete
        # lap chart. Never assign its finishing-line position from final results.
        if not driver['laps'] and len(fastest) == 1 and numeric(fastest[0]['lap']) and millis(fastest[0]['timeMillis']):
            driver['laps'].append({'lap': numeric(fastest[0]['lap']), 'position': None,
                                   'seconds': millis(fastest[0]['timeMillis']), 'deleted': False,
                                   'source': 'F1DB', 'observation': 'personal-fastest-lap-only'})
            added['lap_times'] += 1
    chart = supplement.get('historical_chart', {})
    by_id = {d['id']:d for d in out['drivers']}
    for row in chart.get('lap_chart', []):
        d = by_id.get(row['entry_id'])
        if not d: continue
        existing = next((l for l in d['laps'] if l['lap']==row['lap']), None)
        if existing is None:
            d['laps'].append({'lap':row['lap'],'position':row['position'],'seconds':row['seconds'], 'deleted':False,
                             'position_source':'STATS F1 via retained compilation', 'source':'historical-lap-chart'})
            added['lap_positions'] += 1
            if row['seconds'] is not None: added['additional_lap_times'] += 1
        elif existing.get('position') is None:
            existing['position'] = row['position']; existing['position_source'] = 'STATS F1 via retained compilation'
            added['lap_positions'] += 1
        if existing and existing.get('seconds') is None and row['seconds'] is not None:
            existing['seconds'] = row['seconds']; existing['time_source'] = 'retained timing compilation'
            added['additional_lap_times'] += 1
    for row in chart.get('pitstops', []):
        d = by_id.get(row['entry_id'])
        if not d: continue
        existing = [p for p in d['pitstops'] if p['stop']==row['stop']]
        if not existing:
            d['pitstops'].append({k:row[k] for k in ('stop','lap','duration','local_time')} | {'source':'Formula1.com via retained compilation','duration_kind':'source-reported-pit-duration'})
            added['pitstops'] += 1
        elif len(existing)==1 and existing[0]['lap']==row['lap'] and existing[0].get('local_time') is None and row['local_time']:
            existing[0]['local_time'] = row['local_time']; existing[0]['local_time_source'] = 'Formula1.com via retained compilation'
    for driver in out['drivers']:
        driver['laps'].sort(key=lambda r:r['lap']); driver['pitstops'].sort(key=lambda r:r['stop'] or 999)
    out['lap_records'] = sum(len(d['laps']) for d in out['drivers'])
    out['pit_records'] = sum(len(d['pitstops']) for d in out['drivers'])
    out['coverage_label'] = ('Uitslag + rondegegevens' + (' + pitstops' if out['pit_records'] else '')) if out['lap_records'] else 'Uitslagenarchief'
    warnings = []
    for warning in out.get('warnings', []):
        if warning.startswith('Geen afzonderlijke pitstopregistraties') and out['pit_records']: continue
        if warning.startswith('Geen afzonderlijke rondetijden') and out['lap_records']:
            warning = 'Historische rondekaarten en gemeten persoonlijke snelste ronden zijn toegevoegd waar beschikbaar; ontbrekende rondetijden blijven onbekend.'
        if warning.startswith('Historische teamkleuren zijn niet bevestigd') and added['colors']:
            warning = 'Historische teamkleuren volgen gedateerde kleurreferenties. Hexwaarden zijn schematisch; privé-inschrijvingen kunnen afwijken en onbekende kleuren blijven neutraal.'
        if warning.startswith('Inhaalacties, bandencompounds, neutralisaties'):
            warning = 'Inhaalregistraties en gekoppelde baanlocaties ontbreken. Aanvullende sessie-, sector-, band- en wedstrijdleidingsgegevens zijn beschikbaar waar de oorspronkelijke bronnen ze vastleggen.'
        warnings.append(warning)
    out['warnings'] = warnings
    out['historical_supplement']['added'] = added
    return out


def color_for(registry, team_id, year, round_number=None, driver_id=None):
    choices = [r for r in registry.get('records', []) if str(team_id) in r['team_ids'] and r['from_year'] <= year <= r['to_year']
               and (not r.get('rounds') or round_number in r['rounds'])
               and (not r.get('driver_ids') or str(driver_id) in r['driver_ids'])]
    if not choices:
        return None
    return max(choices, key=lambda r: (bool(r.get('driver_ids')), bool(r.get('rounds')), r.get('priority', 0), -(r['to_year'] - r['from_year'])))


@lru_cache(maxsize=2)
def retained_database(root):
    packages = list((Path(root) / 'analyses/sources/historical/f1db').glob('*.zip'))
    return HistoricalDatabase(packages[0]) if len(packages) == 1 else None


def apply_retained(data, raw, root):
    """Reuse the one-time archive during future rebuilds, without HTTP requests."""
    root = Path(root)
    saved = root / 'analyses/sources/historical/supplements' / f"{data['year']}-{data['round']:02}.json"
    if not saved.exists(): return data
    supplement = read_json(saved)
    if supplement['race']['date'] != data['date']: raise ValueError('Historical supplement calendar mismatch')
    database = retained_database(str(root))
    if database:
        primary = database.supplement(data, raw)
        for key in ('entry_drivers', 'unmatched_entries', 'conflicts'): supplement[key] = primary[key]
    else:
        entries = {d['id'] for d in data['drivers']}
        if set(supplement['entry_drivers']) - entries: raise ValueError('Historical entry identity changed; restore the retained source package')
    colors_path = root / 'assets/historical-team-colors.json'
    colors = read_json(colors_path) if colors_path.exists() else None
    for key in ('lap_chart','pitstops','maximum_speeds'):
        for row in supplement.get('historical_chart', {}).get(key, []):
            candidates = [d for d in data['drivers'] if supplement['entry_drivers'].get(d['id'])==row.get('career_id') and d['number']==row.get('number')]
            if len(candidates) != 1: raise ValueError('Retained observation entry identity is no longer unique')
            row['entry_id'] = candidates[0]['id']
    result = augment(data, supplement, colors)
    timing_file = root / 'analyses/sources/historical/timing' / f"{data['year']}-{data['round']:02}.json"
    if timing_file.exists(): result['timing'] = read_json(timing_file)
    for change in supplement.get('tyre_changes', []):
        matches = [d for d in result['drivers'] if supplement['entry_drivers'].get(d['id']) == change.get('career_id') and d['number'] == change.get('number')]
        if len(matches) == 1: change['entry_id'] = matches[0]['id']
    return result


def supplemental_facts(data, original_facts):
    facts = json.loads(json.dumps(original_facts))
    supplement = data.get('historical_supplement', {})
    matches = supplement.get('entry_drivers', {})
    sessions = supplement.get('sessions', {})
    drivers = {d['id']: d for d in data['drivers']}
    # Official pole is explicitly recorded. Grid P1 can differ after penalties.
    pole_rows = [r for r in sessions.get('race-results', []) if r.get('polePosition') == 'true']
    fastest_rows = [r for r in sessions.get('fastest-laps', []) if r.get('positionNumber') == '1']
    def badge(row):
        candidates = [d for id_, d in drivers.items() if matches.get(id_) == row['driverId'] and d['number'] == numeric(row.get('driverNumber'))]
        if len(candidates) != 1:
            return None
        d = candidates[0]
        return {'id': d['id'], 'number': d['number'], 'name': d['name'], 'code': d.get('code'), 'color': d.get('display_color') or d.get('color') or '#B3BECE', 'fact_source': 'F1DB'}
    if len(pole_rows) == 1:
        value = badge(pole_rows[0])
        if value:
            facts['pole'] = value
    if len(fastest_rows) == 1:
        value = badge(fastest_rows[0])
        if value:
            value.update(fastest_time=fastest_rows[0]['time'] or None, fastest_lap=numeric(fastest_rows[0]['lap']), fastest=1)
            facts['fastest'] = value
    pole = facts.get('pole')
    q = sessions.get('qualifying-results', [])
    # 2003-2005 aggregate formats and 2006+ knockout sessions cannot compare
    # different phases. Q3 is comparable only when both drivers reached Q3.
    first = next((r for r in q if r['positionNumber'] == '1'), None)
    second = next((r for r in q if r['positionNumber'] == '2'), None)
    if pole and first and second and matches.get(pole['id']) == first['driverId']:
        column = 'q3Millis' if first.get('q3Millis') and second.get('q3Millis') else 'timeMillis'
        a, b = millis(first.get(column)), millis(second.get(column))
        if a is not None and b is not None and b >= a:
            facts['pole_margin'] = round(b - a, 3); facts['pole_margin_source'] = supplement.get('source')
    gains = [d for d in drivers.values() if d.get('classified') and d.get('grid') and d['grid'] > 0 and d.get('position')]
    if gains:
        highest = max(d['grid']-d['position'] for d in gains)
        if highest > 0:
            facts['gainers'] = [{**d, 'gain':highest, 'color':d.get('display_color') or d.get('color') or '#B3BECE'} for d in gains if d['grid']-d['position'] == highest]
            # Fact cards need driver identity, not complete lap/pit arrays.
            for d in facts['gainers']:
                for key in ('laps','pitstops','fastest_lap','color_source'): d.pop(key,None)
    for value in facts.values():
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, dict) and item.get('id') in drivers:
                d = drivers[item['id']]; item['color'] = d.get('display_color') or d.get('color') or '#B3BECE'
    return facts


def coverage_notes():
    return [
        ('Uitslagen en startopstellingen blijven gekoppeld aan de oorspronkelijke bronentries. Onbekende waarden blijven onbekend.', 'Results and grids retain their original source entry identities. Unknown values remain unknown.'),
        ('Rondeposities zijn momentopnamen aan de finishlijn; positiewisselingen worden niet als inhaalacties geteld.', 'Lap positions are finish-line snapshots; position changes are not counted as overtaking events.'),
        ('Historische kleuren volgen gedateerde kleurreferenties. Privé-inschrijvingen kunnen afwijken; niet bevestigde kleuren blijven neutraal.', 'Historical colours follow dated livery references. Private entrants may differ; unconfirmed colours remain neutral.'),
        ('Snelste ronden zijn afzonderlijke metingen, geen volledige rondehistorie. Pitstopduur is de bronduur, niet automatisch stilstandtijd.', 'Fastest laps are individual observations, not complete lap histories. Pit-stop durations are source durations, not automatically stationary times.'),
        ('Het aanvullende archief hieronder bevat de beschikbare sessiegegevens en verwijzingen naar originele documenten.', 'The additional archive below contains available session observations and links to original documents.')]


def write_method_report(run, data, manifest):
    """Keep historical source documentation consistent with the enriched data."""
    import html, os
    from .branding import language_controls, language_script
    from .render import page
    run = Path(run)
    texts = [
        ('Bronnen en methode', 'Sources and methodology'),
        ('Jolpica levert de oorspronkelijke uitslagen, bronentries, ronde- en pitregistraties. Het originele CSV-archief en de downloadmetadata zijn bewaard en met SHA-256 gecontroleerd.', 'Jolpica supplies the original results, source entries, lap and pit records. The original CSV archive and download metadata are retained and verified with SHA-256.'),
        ('F1DB vult ontbrekende startposities, pitregistraties en persoonlijke snelste ronden aan en levert kwalificatie-, trainings-, warm-up- en kampioenschapsgegevens waar beschikbaar. Een persoonlijke snelste ronde vult geen ontbrekende rondetijden of posities in.', 'F1DB supplements missing grid positions, pit records and personal fastest laps, and supplies qualifying, practice, warm-up and championship observations where available. A personal fastest lap does not fill missing lap times or positions.'),
        ('De bewaarde f1resultsdatabase-compilatie levert rondekaarten van STATS F1, pitregistraties van Formula1.com en maximumsnelheden van MotorsportStats. Gedeelde auto’s worden alleen gekoppeld bij een ondubbelzinnige rijderidentiteit. De oorspronkelijke bestanden blijven ongewijzigd.', 'The retained f1resultsdatabase compilation supplies STATS F1 lap charts, Formula1.com pit records and MotorsportStats maximum speeds. Shared cars are assigned only when the driver identity is unambiguous. The original files remain unchanged.'),
        ('FIA-documenten en Pirelli-verslagen leveren aanvullende sector-, snelheid-, circuit- en bandengegevens. Voor verdwenen FIA-pagina’s worden bruikbare Wayback-kopieën bewaard met de oorspronkelijke URL, opnamedatum en bestandshash. Alleen het evenement dat in het document zelf is bevestigd wordt gekoppeld.', 'FIA documents and Pirelli reports supply additional sector, speed, circuit and tyre observations. Usable Wayback copies of unavailable FIA pages are retained with the original URL, capture timestamp and file hash. A document is assigned only to the event confirmed in its own content.'),
        ('FastF1-context en de oorspronkelijke timingberichten worden hergebruikt waar beschikbaar. Persoonlijk beste sectoren zijn geen sectortijden per ronde. Lokale pitstoptijden worden zonder bevestigde tijdzone niet naar UTC omgezet.', 'FastF1 context and original timing messages are reused where available. Personal best sectors are not per-lap sector times. Local pit times are not converted to UTC without a confirmed time zone.'),
        ('Teamkleuren volgen gedateerde kleurreferenties. Digitale hexwaarden zijn schematisch, privé-inschrijvingen kunnen afwijken en onbevestigde kleuren blijven neutraal. Oorspronkelijke timingkleuren hebben voorrang.', 'Team colours follow dated livery references. Digital hex values are illustrative, private entrants may differ, and unconfirmed colours remain neutral. Original timing colours take precedence.'),
        ('Bronverschillen blijven in het controlelog; bestaande uitslagen en metingen worden niet stilzwijgend overschreven. Positiewisselingen zijn geen bevestigde inhaalacties. Ontbrekende gegevens blijven onbekend.', 'Source disagreements remain in the audit log; existing results and measurements are not silently overwritten. Position changes are not confirmed overtaking events. Missing observations remain unknown.')]
    archive = manifest.get('source_archive')
    dump = Path(os.path.relpath(archive, run / 'reports')).as_posix() if archive else None
    links = [(F1DB_URL, 'F1DB · CC BY 4.0'), (CHART_URL, 'f1resultsdatabase · ODbL 1.0'),
             ('../data/normalized/historical-supplement.json', 'JSON'), ('../manifest.json', 'Manifest')]
    if dump: links.insert(0, (dump, 'Jolpica · CSV'))
    body = '<style>html[lang="nl"] .history-en,html[lang="en"] .history-nl{display:none}article{max-width:1000px;margin:auto;padding:24px}</style>' + language_controls() + '<article>'
    for i, (nl, en) in enumerate(texts):
        tag = 'h1' if i == 0 else 'p'
        body += f'<{tag} class="history-nl">{html.escape(nl)}</{tag}><{tag} class="history-en">{html.escape(en)}</{tag}>'
    body += '<p>' + ' · '.join('<a href="' + html.escape(url, quote=True) + '">' + html.escape(label) + '</a>' for url, label in links) + '</p></article>'
    (run / 'reports').mkdir(exist_ok=True)
    (run / 'reports/bronnen-en-methode.html').write_text(page('Overtake It Away · Sources', body + language_script()))
    markdown = '\n\n'.join(('# ' if i == 0 else '') + nl + '\n\n' + en for i, (nl, en) in enumerate(texts))
    markdown += '\n\n' + ' · '.join('[' + label + '](' + url + ')' for url, label in links) + '\n'
    (run / 'reports/bronnen-en-methode.md').write_text(markdown)
