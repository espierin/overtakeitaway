"""Reproducible LOCAL build of phase-two pages; never touches live source pages.

Run from the project root with PYTHONPATH=src and the project's Python runtime.
Original sources, definitions and validation are registered with every build.
"""
from collections import defaultdict, Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import median
import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import sys
import subprocess
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from f1_analysis.incidents import retirement_category
from f1_analysis.driver_identity import identity as canonical_identity
from metrics import VERSION, RULES, annotate_context, trend_regularity, network_model, pca_profiles, number
from forecast import evaluate as evaluate_forecast, candidate as forecast_candidate
from forecast import score_archive
from weather import snapshot as weather_snapshot
from incident_audit import (VERSION as INCIDENT_VERSION, result_outcome, repair_documents,
                            decision_rosters, decision_targets, cause)
from qualifying import pole_references, stage_references, qualifying_bridges, DEFINITION as QUALIFYING_DEFINITION, METHOD as QUALIFYING_METHOD

DATA = ROOT/'_development/data'


def compact(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('</', '<\\/')


def folded(s):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().casefold())


def integer(x):
    n = number(x)
    return int(n) if n is not None and n == int(n) else None


def write(name, value, variable):
    body = compact(value)
    (DATA/name).parent.mkdir(parents=True, exist_ok=True)
    (DATA/(name+'.js')).write_text('window.'+variable+'='+body+';\n')
    (DATA/(name+'.json.gz')).write_bytes(gzip.compress(body.encode(), mtime=0))
    return {'name': name, 'bytes': len(body.encode()),
            'compressed_bytes': (DATA/(name+'.json.gz')).stat().st_size,
            'sha256': hashlib.sha256(body.encode()).hexdigest()}


def partition_profiles(data):
    """Keep exact observations once; load details by small driver-name groups."""
    columns = ['race','year','team','number','color','grid','finish','lap1_position','start_gain',
               'dnf','finish_laps','finish_status','finished_on_track','pitlane_start',
               'shared_car_ambiguous','source_shared_car','source_pitlane_start','start_eligible','race_eligible','result_outcome','source_conflicts','start_reference','race_reference','qualities']
    groups = defaultdict(dict)
    for d in data['drivers']:
        group = re.sub('[^a-z0-9]', '_', d['id'][:2]); d['detail_group'] = group
        base, detail = [], []
        for r in d['races']:
            basic = {k:r.get(k) for k in columns}
            basic['qualities'] = {'start':r.get('qualities',{}).get('start',[])}
            base.append([basic[k] for k in columns])
            extra = {k:v for k,v in r.items() if k not in columns}
            extra['qualities'] = {k:v for k,v in r.get('qualities',{}).items() if k != 'start'}
            detail.append([r['race'], extra])
        d['races'] = base; groups[group][d['id']] = detail
    data['driver_race_columns'] = columns
    programs = {}
    for race in data['races']:
        program = race.get('pit_programmes', {})
        programs[race['id']] = program.pop('entries', [])
    strategy = {'programs': programs, 'cycles':data['cycles']}
    data['cycles'] = []
    files = [write('details/'+key, value, 'phase2Group_'+key) for key,value in sorted(groups.items())]
    files.append(write('strategy', strategy, 'phase2Strategy'))
    return files


def partition_facts(facts, data):
    grouped = defaultdict(dict)
    # Repeated field names need not be shipped thousands of times. Preserve
    # every value, with one shared column dictionary for lossless unpacking.
    columns = list(dict.fromkeys(k for f in facts['drivers'].values()
                                for d in f['decisions'] for k in d))
    facts['decision_columns'] = columns
    for d in data['drivers']:
        record = facts['drivers'][d['id']]
        record['decisions'] = [[decision.get(k) for k in columns] for decision in record['decisions']]
        grouped[d['detail_group']][d['id']] = {k:v for k,v in record.items() if k != 'seasons'}
        facts['drivers'][d['id']] = {'seasons':record['seasons']}
    return [write('facts/'+key, records, 'phase2FactGroup_'+key) for key,records in sorted(grouped.items())]


def collection_ledger(tables, data, registry, weather):
    old = json.loads((ROOT/'assets/data-collection.json').read_text())
    parameters = [dict(row, layer='retained snapshot · '+row['layer']) for row in old['parameters']]
    for table, records in tables.items():
        if not records:
            continue
        for field in records[0]:
            known = sum(row[field] not in ('',None) for row in records)
            parameters.append({'layer':'F1DB complete retained ZIP','parameter':table+'.'+field,
                               'slots':len(records),'values':known,'missing':len(records)-known})
    from f1_analysis.data_collection import count_parameters
    for field, values in count_parameters(data).items():
        parameters.append(dict(values,layer='phase 2 derived before column packing',parameter=field))
    ledger = {'generated_at':registry['generated_at'],'version':VERSION,'rules':RULES,
              'source_sha256':registry['facts_source_sha256'],'parameters':parameters,
              'retained_checks':old['checks'],'rank_coverage':registry['rank_coverage'],
              'references':registry['context_references'],'regularity':registry['regularity_driver_races'],
              'source_conflicts':registry['unresolved_source_conflicts'],
              'entry_checks':registry['source_entry_checks'],
              'weather':weather,
              'methods':[
                  ['Bronarchief / retained archive','CSV rows in the retained F1DB ZIP; SHA-256 verified. No blanket recollection. Exact table and column counts; empty and zero remain distinct.'],
                  ['Identiteiten / identities','Canonical profile identity, full names and explicit source identifiers. No join on a three-letter code alone. Multiple shared-car entries remain excluded from personal scoring.'],
                  ['Referentie / reference','Separate race phases; exact layout, actual started field and origin. Exclude focal driver; at least eight other races and two other drivers, first within five and otherwise ten years.'],
                  ['Ronderangen / lap ranks','Every retained rank remains stored; eligible clean clear-air observations additionally require five measured times and at least 80% of the evidenced active field. Unknown field coverage is excluded, not assumed complete.'],
                  ['Uitval / retirements','Explicit result status and cause, supplemented by retained evidence; a missing legacy DNF flag never means zero. Numeric classification can coexist with retirement; NC alone does not prove retirement. Non-starts, DSQ, unknown outcomes and shared cars remain separate. Source disagreements are retained.'],
                  ['Besluiten / decisions','Every retained FIA document text is re-read, including old N°/Driver forms and collective penalty tables. Match recipients within the recorded weekend session; other collision participants do not inherit the sanction. Competitor fines, summons, reviews, replaced decisions, classification time added and personally reviewed responsibility remain separate. Incomplete coverage never establishes zero.'],
                  ['Kwalificatie / qualifying',QUALIFYING_METHOD],
                  ['Netwerk / network','Join teammates by verified entrant and round, not constructor alone. Use a common measured qualifying segment. Date-held-out evaluation excludes pairs not connected in the training network. Intervals cluster by race.'],
                  ['PCA','Complete driver-season feature rows only. Standardized exploratory components, whole-year block stability checks; no skill ranking.'],
                  ['Vooruitblik / outlook','Pre-weekend features from earlier main-race results only. Weights selected on 2021–2023 and tested on 2024+. A dated prospective candidate is immutable and is not a validated public forecast.'],
                  ['Weer / weather',weather.get('request_url','No request: coordinates or upcoming event missing.')+'; original response hash retained, forecast-valid time UTC, retrieval time distinct from unknown model-run issuance.']
              ]}
    return ledger


def main():
    DATA.mkdir(exist_ok=True)
    original = (ROOT/'analysis-lab.html').read_text()
    payload = re.search(r'<script[^>]*id=["\']phase2-data["\'][^>]*>(.*?)</script>', original, re.S)[1]
    data = json.loads(payload)
    package = next((ROOT/'analyses/sources/historical/f1db').glob('*.zip'))
    sha = hashlib.sha256(package.read_bytes()).hexdigest()
    source = json.loads(package.with_name('source.json').read_text())
    assert sha == source['sha256']
    with zipfile.ZipFile(package) as z:
        tables = {n.removeprefix('f1db-').removesuffix('.csv'):
                  list(csv.DictReader(io.TextIOWrapper(z.open(n)))) for n in z.namelist() if n.endswith('.csv')}
    races = {r['id']: r for r in data['races']}
    by_id = {d['id']: d for d in data['drivers']}
    names = defaultdict(set)
    for d in data['drivers']:
        names[folded(d['name'])].add(d['id']); names[folded(d['id'])].add(d['id'])
    identities = {}; unmatched = []
    for d in tables['drivers']:
        matches = set()
        for label in [d['id'], d['name'], d['fullName'], canonical_identity(d['name'])]:
            matches.update(names.get(folded(label), set()))
        if len(matches) == 1:
            identities[d['id']] = next(iter(matches))
        elif d['id'] in by_id:
            identities[d['id']] = d['id']
        else:
            unmatched.append(d['id'])
    # A different historical forename must not erase an otherwise verified career.
    # Require at least two consistent race/car/grid signatures; never use code alone.
    by_car = defaultdict(list)
    named_profiles = set(identities.values())
    for profile in data['drivers']:
        for row in profile['races']:
            if not row.get('shared_car_ambiguous'):
                by_car[row['race'], row['number']].append((profile['id'], row))
    votes = defaultdict(Counter); vote_races = defaultdict(set)
    for row in tables['races-race-results']:
        if row['driverId'] in identities or row['sharedCar'] == 'true':
            continue
        rid = row['year']+'-'+row['round']; matches = by_car.get((rid, integer(row['driverNumber'])), [])
        if len(matches) != 1:
            continue
        did, own = matches[0]
        if did in named_profiles:
            continue
        if integer(row['gridPositionNumber']) and own.get('grid') and integer(row['gridPositionNumber']) != own['grid']:
            continue
        votes[row['driverId']][did] += 1; vote_races[row['driverId'], did].add(rid)
    signature_links = []
    for source_id, counts in votes.items():
        if len(counts) == 1:
            did = next(iter(counts)); evidence = sorted(vote_races[source_id,did])
            if len(evidence) >= 2 and sum(did in v for v in votes.values()) == 1:
                identities[source_id] = did
                signature_links.append({'source':source_id,'profile':did,'matched_races':evidence})
    unmatched = [d['id'] for d in tables['drivers'] if d['id'] not in identities]
    f1race = {f"{r['year']}-{r['round']}": r for r in tables['races']}
    for rid, r in races.items():
        raw = f1race.get(rid)
        r['layout'] = raw.get('circuitLayoutId') if raw else None
        r['race_laps'] = integer(raw.get('laps')) if raw else None
        r['qualifying_format'] = raw.get('qualifyingFormat') if raw else None
        r['start_utc'] = raw['date']+'T'+raw['time']+':00Z' if raw and raw['time'] else None
    grouped_results = defaultdict(list)
    for row in tables['races-race-results']:
        grouped_results[f"{row['year']}-{row['round']}"].append(row)
    non_starts = {'DNS', 'DNQ', 'DNPQ', 'WD', 'EX', 'DNP'}
    retained_rows = {(d['id'], r['race']):r for d in data['drivers'] for r in d['races']}
    def started(row):
        own = retained_rows.get((identities.get(row['driverId']),row['year']+'-'+row['round']),{})
        timing_evidence = (own.get('lap1_position') or 0)>0 or (own.get('finish_laps') or 0)>0
        return row['positionText'].upper() not in non_starts and (
            integer(row['gridPositionNumber']) is not None or row['gridPositionText'].upper() in ('PL', 'PIT', 'PIT LANE')
            or (integer(row['laps']) or 0) > 0 or timing_evidence)
    for rid, rows in grouped_results.items():
        cars = {(r['driverNumber'], r['constructorId']) for r in rows if started(r)}
        if rid in races:
            races[rid]['starters'] = len(cars)
            races[rid]['field_count_source'] = 'Distinct started car/constructor; retained lap evidence supplements missing DSQ grid/distance; explicit DNS/DNQ excluded'
    qualifying = defaultdict(list)
    for row in tables['races-qualifying-results']:
        qualifying[f"{row['year']}-{row['round']}", row['driverId']].append(row)
    standings = {(f"{r['year']}-{r['round']}", r['driverId']): r for r in tables['races-driver-standings']}
    finals = {(integer(r['year']), r['driverId']): r for r in tables['seasons-driver-standings']}
    sprint = defaultdict(list)
    for row in tables['races-sprint-race-results']:
        sprint[f"{row['year']}-{row['round']}", row['driverId']].append(row)
    entrant_by_round = defaultdict(set)
    for row in tables['seasons-entrants-drivers']:
        if row['testDriver'] == 'true':
            continue
        for round_number in row['rounds'].split(';'):
            if round_number.isdigit():
                entrant_by_round[row['year'], round_number, row['driverId'], row['constructorId']].add(row['entrantId'])
    row_index = {(d['id'], r['race']): r for d in data['drivers'] for r in d['races']}
    last_source_year = max(integer(r['year']) for r in tables['races-race-results'])
    facts = {'definition': VERSION, 'source': source, 'rules': RULES, 'drivers': {},
             'qualifying_poles':pole_references(tables['races-qualifying-results'], set(races)),
             'qualifying_stages':stage_references(tables['races-qualifying-results'], tables['races'], set(races)),
             'qualifying_definition':QUALIFYING_DEFINITION,
             'source_cutoff': {'year': last_source_year,
                              'round': max(integer(r['round']) for r in tables['races-race-results']
                                           if integer(r['year']) == last_source_year)},
             'unmatched_source_identities': unmatched, 'race_signature_identity_links':signature_links}
    bridge_models,bridge_validation,_ = qualifying_bridges(tables['races-qualifying-results'], facts['qualifying_poles'], set(races))
    facts['qualifying_bridges'] = bridge_models
    facts['qualifying_bridge_validation'] = bridge_validation
    for d in data['drivers']:
        facts['drivers'][d['id']] = {'seasons': [], 'races': [], 'decisions': [], 'classification_penalties': []}
    records = []; source_rows = defaultdict(list)
    for rid, results in grouped_results.items():
        if rid not in races:
            continue
        for row in results:
            if row['driverId'] in identities:
                source_rows[identities[row['driverId']], rid].append(row)
    for (did, rid), rows in source_rows.items():
        raw = rows[0]; r = races[rid]
        # Multiple entries/shared drives are not silently collapsed into a personal result.
        shared = len(rows) != 1 or any(x.get('sharedCar') == 'true' for x in rows)
        qs = qualifying[rid, raw['driverId']]
        q = qs[0] if len(qs) == 1 else {}
        standing = standings.get((rid, raw['driverId']), {})
        known = row_index.get((did, rid), {})
        fact = {'race': rid, 'year': r['year'], 'driver': did, 'source_driver': raw['driverId'],
                'team_id': raw['constructorId'], 'number': integer(raw['driverNumber']),
                'started': started(raw) and not shared, 'shared': shared,
                'position': integer(raw['positionNumber']) if not shared else None,
                'classification_order': integer(raw['positionDisplayOrder']), 'status': raw['positionText'],
                'grid': integer(raw['gridPositionNumber']), 'laps': integer(raw['laps']),
                'pitlane_start': raw['gridPositionText'].upper() in ('PL','PIT','PIT LANE'),
                'reason': raw['reasonRetired'] or None, 'category': retirement_category(raw['reasonRetired']),
                'pole': raw['polePosition'] == 'true' and not shared,
                'fastest': raw['fastestLap'] == 'true' and not shared,
                'points_reported': number(raw['points']),
                'qualifying': integer(q.get('positionNumber')), 'qualifying_status': q.get('positionText'),
                'qualifying_ms': {k: integer(q.get(k)) for k in ('timeMillis','q1Millis','q2Millis','q3Millis')},
                'standing_position': integer(standing.get('positionNumber')),
                'standing_points': number(standing.get('points')),
                'finished': known.get('finished_on_track'), 'date': r['date']}
        entrants = entrant_by_round[raw['year'], raw['round'], raw['driverId'], raw['constructorId']]
        fact['entrant'] = next(iter(entrants)) if len(entrants) == 1 else None
        records.append(fact); facts['drivers'][did]['races'].append(fact)
        if known:
            known['fact'] = fact
    for row in tables['seasons-drivers']:
        did = identities.get(row['driverId'])
        if not did:
            continue
        year = integer(row['year']); end = finals.get((year, row['driverId']), {})
        facts['drivers'][did]['seasons'].append({
            'year': year, 'position': integer(end.get('positionNumber') or row.get('positionNumber')),
            'points': number(end.get('points')), 'earned_points': number(row['totalPoints']),
            'champion': end.get('championshipWon') == 'true',
            'starts': integer(row['totalRaceStarts']), 'entries': integer(row['totalRaceEntries']),
            'wins': integer(row['totalRaceWins']), 'podiums': integer(row['totalPodiums']),
            'poles': integer(row['totalPolePositions']), 'fastest': integer(row['totalFastestLaps']),
            'sprint_starts': integer(row['totalSprintRaceStarts']), 'sprint_wins': integer(row['totalSprintRaceWins']),
            'laps': integer(row['totalRaceLaps']), 'provisional': year == max(x['year'] for x in data['races'])})
    print('Facts joined', len(records), 'source-only identities', len(unmatched), flush=True)

    incident_file = ROOT/'assets/driver-incidents.json.gz'
    incidents = json.loads(gzip.decompress(incident_file.read_bytes()))
    reviewed = json.loads(Path(__file__).with_name('responsibility-reviewed.json').read_text())['decisions']
    roster = defaultdict(dict)
    for d in data['drivers']:
        for row in d['races']:
            roster[row['race']].setdefault(row['number'], []).append(d['id'])
    documents, incident_audit = repair_documents(incidents, ROOT)
    document_rosters = decision_rosters(tables, identities)
    # Retained timing is useful where an old weekend table has no car number.
    for race, cars in roster.items():
        for n, ids in cars.items():
            document_rosters[race, 'Race'][n].update(ids)
    links = Counter(); unlinked_documents = []
    verified_links = json.loads((ROOT/'analyses/sources/incidents/verified-links.json').read_text())
    for dec in documents:
        targets = decision_targets(dec, document_rosters)
        if not targets:
            unlinked_documents.append(dec['id'])
        source_ref = incidents['sources'].get(dec['source'], {})
        out = {k: dec.get(k) for k in ('id','race','year','session','title','outcome','effective_outcome','sanction_types',
               'time_penalty_seconds','grid_places','penalty_points','fact','offence','decision','reason',
               'blame_evidence','requires_review','published','is_collision','lap','document_number',
               'driver_number','subject_numbers','involved_numbers','fine_text','sanction_recipient')}
        out['url'] = source_ref.get('url'); out['source_file'] = source_ref.get('local_file')
        for did, n, role in targets:
            item = dict(out, role=role)
            # Amounts in a collective document belong to that driver's rows.
            if dec.get('table_sanctions'):
                own = [x for x in dec['table_sanctions'] if x['number'] == n]
                item['time_penalty_seconds'] = sum(x['seconds'] for x in own) if own else None
                item['sanction_rows'] = own
            if dec.get('deleted_laps_by_number'):
                item['deleted_laps'] = dec['deleted_laps_by_number'].get(n)
            checked = reviewed.get(dec['id'])
            if checked and (checked.get('driver') == did or did in checked.get('drivers', [])):
                item['reviewed_responsibility'] = checked
            item['retirement_links'] = [v for v in verified_links if v['document'] == dec['id'] and v['driver_id'] == did]
            if checked and did in checked.get('retirement_confirmed_drivers', []):
                item['retirement_links'].append({'document':dec['id'], 'driver_id':did,
                    'causation_confirmed':True, 'role':role, 'reviewed_on':checked['reviewed_at'],
                    'source_url':checked['corroborating_url'],
                    'confirmation_scope':'Official F1 race report confirms the opening-lap collision ended both drivers races; the joint FIA ruling establishes no sole or predominant fault.'})
            facts['drivers'][did]['decisions'].append(item); links[role] += 1
    for dec in incidents['classification_penalties']:
        did = dec['driver_id']
        if did in facts['drivers']:
            facts['drivers'][did]['classification_penalties'].append(dec)
    # The old document registry starts in 2007; the retained result archive
    # also records earlier time additions. Do not impose that artificial cutoff.
    penalty_keys = {(did,p['race']) for did,f in facts['drivers'].items()
                    for p in f['classification_penalties']}
    added_historical_penalties = 0
    for raw in tables['races-race-results']:
        did = identities.get(raw['driverId']); rid = raw['year']+'-'+raw['round']
        if (not did or rid not in races or (did,rid) in penalty_keys
                or not (raw['timePenalty'] or raw['timePenaltyMillis'])):
            continue
        facts['drivers'][did]['classification_penalties'].append({
            'id':'f1db-'+raw['raceId']+'-'+raw['driverId'], 'race':rid,'year':integer(raw['year']),
            'driver_id':did,'driver_number':integer(raw['driverNumber']), 'session':'Race',
            'time_penalty':raw['timePenalty'] or None,'time_penalty_millis':integer(raw['timePenaltyMillis']),
            'detail_coverage':'classification_time_added_only','reason':None,
            'source_url':source['url']})
        penalty_keys.add((did,rid)); added_historical_penalties += 1
    # Earlier registry entries do not store a year; period filtering still must.
    for f in facts['drivers'].values():
        for penalty in f['classification_penalties']:
            penalty['year'] = races[penalty['race']]['year']
    facts['incident_coverage'] = incidents['coverage']
    facts['incident_definition'] = INCIDENT_VERSION
    for ret in incidents['retirements']:
        row = row_index.get((ret['driver_id'], ret['race']))
        if row and row.get('fact'):
            row['fact']['retirement_evidence'] = {k:ret.get(k) for k in
                ('id','source_conflict','evidence')}

    outcomes = Counter(); by_year = defaultdict(Counter); legacy_omitted = []; conflicts = []
    for record in records:
        own = row_index.get((record['driver'], record['race']), {})
        record['outcome'] = result_outcome(record, own)
        if own: own['result_outcome'] = record['outcome']
        outcomes[record['outcome']] += 1; by_year[record['year']][record['outcome']] += 1
        if record.get('finish_evidence_conflict'):
            conflicts.append({'driver':record['driver'],'race':record['race'],
                              'retained_finished':own.get('finished_on_track'),
                              'source_status':record['status'],'source_reason':record['reason']})
        if record['outcome'] == 'retired' and own and own.get('dnf') is not True:
            legacy_omitted.append({'driver':record['driver'],'race':record['race'],'reason':record['reason']})
    # Unmatched old entries remain visible in the audit without manufacturing
    # an F1DB result or changing the inputs to any driver-quality calculation.
    fallback_count = 0
    for (did,rid), own in row_index.items():
        if own.get('fact'): continue
        label = str(own.get('finish_status') or '').lower()
        status = ('DNS' if label in {'did not start','withdrew','withdrawn'} else
                  'DNQ' if label in {'did not qualify','did not prequalify'} else
                  'DSQ' if cause(label) == 'disqualified' else '')
        fallback = {'race':rid,'year':own['year'],'status':status,'reason':own.get('finish_status'),
                    'started':bool(own.get('lap1_position') or own.get('finish_laps')),
                    'shared':bool(own.get('shared_car_ambiguous')), 'retained_only':True}
        fallback['outcome'] = result_outcome(fallback, own)
        own['result_outcome'] = fallback['outcome']
        facts['drivers'][did].setdefault('incident_fallback', []).append(fallback)
        fallback_count += 1
    incident_audit['document_outcomes'] = incident_audit['outcomes']
    incident_audit.update(outcomes=dict(outcomes), outcomes_by_year={str(y):dict(c) for y,c in sorted(by_year.items())},
        restored_missing_legacy_dnf=legacy_omitted, finish_evidence_conflicts=conflicts,
        linked_decision_roles=dict(links), unlinked_documents=unlinked_documents,
        recovered_classification_penalties=added_historical_penalties,
        classification_penalties=sum(len(f['classification_penalties']) for f in facts['drivers'].values()),
        retained_only_entries=fallback_count,
        archive_sha256=hashlib.sha256(incident_file.read_bytes()).hexdigest(),
        scope='All 817 development profiles, 1950–2026. Documents remain a partial archive, not a complete sanction history.')
    (ROOT/'_development/incident-audit.json').write_text(json.dumps(incident_audit,ensure_ascii=False,indent=2)+'\n')

    observations = []; regularity_count = 0; rank_counts = Counter(); source_conflicts = Counter()
    for race in data['races']:
        rows = [(d, row_index[d['id'], race['id']]) for d in data['drivers'] if (d['id'], race['id']) in row_index]
        distances = {d['id']: row.get('finish_laps') or (row.get('fact') or {}).get('laps') for d, row in rows}
        complete_distances = sum(x is not None for x in distances.values()) >= .9*len(rows)
        for d, row in rows:
            row['start_eligible'] = False; row['race_eligible'] = False
            row['source_conflicts'] = {}
            fact = row.get('fact')
            row['source_shared_car'] = bool(fact and fact['shared'])
            row['source_pitlane_start'] = bool(fact and fact['pitlane_start'])
            if fact and not fact['shared']:
                for original, linked in [('grid','grid'),('finish','position')]:
                    a,b = row.get(original),fact.get(linked)
                    if (number(a) is not None and number(b) is not None and a>0 and b>0
                            and a!=b and not (original=='grid' and row.get('pitlane_start'))):
                        row['source_conflicts'][original] = {'retained':a,'f1db':b}
                        source_conflicts[original] += 1
            for point in row.get('lap_rankings', []):
                active = sum(n >= point[0] for n in distances.values() if n is not None)
                valid_field = complete_distances and point[2] >= RULES['rank_min_field'] and point[2] >= .8*active
                if not valid_field:
                    point[4] |= 256; rank_counts['excluded_field_coverage'] += 1
                else:
                    rank_counts['field_coverage_accepted'] += 1
            # Recover regularity from actual retained clocks, in separate pit intervals.
            program = race.get('pit_programmes', {})
            entry = next((x for x in program.get('entries', []) if x[0] == row['number']), None)
            regularity = []
            if entry:
                clear = {p[0]: p for p in row.get('lap_rankings', []) if not (p[4] & (1|2|4|8|16|64|128|256))}
                sections = defaultdict(list)
                for lap, packed in enumerate(entry[2], 1):
                    if lap not in clear or packed <= 0:
                        continue
                    stop = max([s for s in entry[1] if s < lap] or [0])
                    if lap <= stop+2:
                        continue
                    sections[stop, clear[lap][3]].append((lap, (packed//100)/1000))
                for (stop, compound), points in sections.items():
                    reg = trend_regularity(points)
                    if reg:
                        regularity.append(dict(reg, compound=data['settings']['lap_rankings']['compounds'][compound], stop=stop))
            row['qualities']['regularity'] = regularity; regularity_count += bool(regularity)
            if not race.get('layout') or not race.get('starters') or row.get('shared_car_ambiguous'):
                continue
            if fact and (fact['shared'] or not fact['started']):
                continue
            for phase, origin, outcome in [('start', row.get('grid'), row.get('lap1_position')),
                                           ('race', row.get('lap1_position'), row.get('finish'))]:
                if ('grid' if phase=='start' else 'finish') in row['source_conflicts']:
                    continue
                if phase == 'start' and (row.get('pitlane_start') or row['source_pitlane_start']):
                    continue
                if phase == 'race' and (row.get('result_outcome') != 'finished'
                        or row.get('finished_on_track') is not True or (row.get('finish_laps') or 0) < 2):
                    continue
                if not isinstance(origin, (int, float)) or not isinstance(outcome, (int, float)) or not 1 <= origin <= race['starters'] or not 1 <= outcome <= race['starters']:
                    continue
                observations.append({'driver': d['id'], 'race': race['id'], 'year': race['year'],
                                     'layout': race['layout'], 'field': race['starters'],
                                     'origin': origin, 'outcome': outcome, 'phase': phase})
                row[phase+'_eligible'] = True
    reference_counts = annotate_context(observations)
    for o in observations:
        row_index[o['driver'], o['race']][o['phase']+'_reference'] = o['reference']
    data['settings']['lap_rankings']['flags']['insufficient_field_coverage'] = 256
    print('References', reference_counts, 'regularity driver/races', regularity_count, flush=True)

    edges = []; roster_results = defaultdict(list)
    for fact in records:
        if not fact['shared'] and fact['entrant']:
            roster_results[fact['race'], fact['entrant']].append(fact)
    for (rid, team), rows in roster_results.items():
        pairs = list(combinations(rows, 2))
        for a, b in pairs:
            if a['driver'] == b['driver']:
                continue
            common = next((key for key in ('q3Millis','q2Millis','q1Millis','timeMillis')
                           if a['qualifying_ms'].get(key) and b['qualifying_ms'].get(key)), None)
            if not common:
                continue
            ta, tb = a['qualifying_ms'][common], b['qualifying_ms'][common]
            # Invalid/very slow non-comparable times do not establish a speed edge.
            delta = 100*math.log(ta/tb)
            if abs(delta) > 10:
                continue
            edges.append({'a': a['driver'], 'b': b['driver'], 'delta': round(delta, 6),
                          'race': rid, 'year': races[rid]['year'], 'date': races[rid]['date'],
                          'session': common, 'team': team, 'weight': 1/max(1, len(pairs))})
    network = network_model(edges)
    print('Network', len(edges), 'pairs;', network.get('validation'), flush=True)
    pca_rows = []
    for d in data['drivers']:
        for year in range(data['period'][0], data['period'][1]+1):
            rows = [r for r in d['races'] if r['year'] == year]
            starts = [r['start_gain'] for r in rows if r.get('start_reference')]
            pace = [r['comparison']['pace_delta_pct'] for r in rows if r.get('comparison') and r['comparison']['method'] == 'matched-median']
            ranks = [(p[1]-1)/(p[2]-1) for r in rows for p in r.get('lap_rankings', []) if not p[4] & (1|2|4|8|16|64|128|256) and p[2]>1]
            if len(starts) >= 5 and len(pace) >= 5 and len(ranks) >= 30:
                pca_rows.append({'driver': d['id'], 'year': year, 'values': [median(starts), median(pace), median(ranks)]})
    pca = pca_profiles(pca_rows)
    forecast = evaluate_forecast(data['races'], records)
    dates = sorted([r for r in f1race.values() if r['date'] > max(x['date'] for x in data['races'])], key=lambda r: r['date'])
    next_race = dates[0] if dates else None
    weather = weather_snapshot(ROOT/'_development/weather', next_race, tables['circuits'])
    latest_id = max(data['races'], key=lambda r: r['date'])['id']
    candidate = forecast_candidate(forecast, next_race, [r for r in records if r['race'] == latest_id])
    if candidate:
        # Immutable prospective research record. Rebuilds do not replace an issued forecast.
        archive = ROOT/'_development/forecast-archive'; archive.mkdir(exist_ok=True)
        path = archive/(candidate['event']['year']+'-'+candidate['event']['round']+'-pre-weekend.json')
        if not path.exists():
            path.write_text(compact(candidate)+'\n')
        candidate = json.loads(path.read_text())
    prospective=score_archive(ROOT/'_development/forecast-archive', records)
    forecast['prospective']=prospective
    forecast['passes_prospective']=prospective['passes']
    # Further probability calibration is required before promoting a research candidate.
    forecast['public_forecast_enabled']=False
    models = {'definition': VERSION, 'rules': RULES,
              'network': network, 'pca': pca, 'forecast': {k:v for k,v in forecast.items() if k != 'candidate_generator'},
              'candidate': candidate}
    models['forecast']['experiments'] = [e for e in forecast['experiments'] if e['year'] >= 2024]

    findings = {}
    for race in data['races']:
        os_ = [o for o in observations if o['race'] == race['id']]
        start = [o for o in os_ if o['phase'] == 'start']; finish = [o for o in os_ if o['phase'] == 'race']
        cycles = [c for c in data['cycles'] if c['race'] == race['id']]
        winner = next((r for r in records if r['race'] == race['id'] and r['position'] == 1), None)
        findings[race['id']] = {'race': race['id'], 'year': race['year'], 'name': race['name'],
            'href': race['href'], 'winner': winner['driver'] if winner else None,
            'starts': len(start), 'progression': len(finish),
            'best_start': max(start, key=lambda o:o['origin']-o['outcome']) if start else None,
            'best_progression': max(finish, key=lambda o:o['origin']-o['outcome']) if finish else None,
            'candidate_cycles': len(cycles), 'order_reversed': sum(c['success'] for c in cycles),
            'cycle_median_gain': median(c['gain_seconds'] for c in cycles) if cycles else None,
            'definition': VERSION, 'layout': race.get('layout'), 'circuit': race.get('circuit'),
            'driver_names': {did: by_id[did]['name'] for did in {
                winner['driver'] if winner else None,
                max(start, key=lambda o:o['origin']-o['outcome'])['driver'] if start else None,
                max(finish, key=lambda o:o['origin']-o['outcome'])['driver'] if finish else None} if did}}
    # Atlas observations retain race clustering and every unsuccessful accepted cycle.
    atlas = {'definition': VERSION, 'weather': weather, 'cells': [],
             'interpretation': 'accepted candidate cycles only; order reversal is not proven strategic intent'}
    cells = defaultdict(list)
    for c in data['cycles']:
        r = races[c['race']]
        if not r.get('layout'):
            continue
        key = (r['layout'], c['type'], min(3, int(c['race_fraction']*4)),
               min(4, int((c['position_before']-1)//5)), c['start_compound'], c['end_compound'])
        cells[key].append(c)
    import numpy as np
    for key, cycles in cells.items():
        blocks = defaultdict(list)
        for c in cycles:
            blocks[c['race']].append(c)
        block_values = [(len(v), sum(c['success'] for c in v)) for v in blocks.values()]
        interval = None
        if len(block_values) >= 5:
            rng = np.random.default_rng(31917); a = np.array(block_values)
            draws = a[rng.integers(0,len(a),(400,len(a)))].sum(axis=1)
            interval = np.quantile(draws[:,1]/draws[:,0],[.025,.975]).tolist()
        atlas['cells'].append({'layout': key[0], 'type': key[1], 'phase': key[2], 'position_band': key[3],
                               'before': key[4], 'after': key[5], 'n':len(cycles),'races':len(blocks),
                               'successes':sum(c['success'] for c in cycles),
                               'median_gain':median(c['gain_seconds'] for c in cycles), 'interval':interval})
    registry = {'version': VERSION, 'generated_at': datetime.now(timezone.utc).isoformat(),
                'rules': RULES, 'facts_source_sha256': sha, 'rank_coverage': dict(rank_counts),
                'context_references': reference_counts, 'regularity_driver_races': regularity_count,
                'source_counts': {k:len(v) for k,v in tables.items()},
                'unresolved_source_conflicts':dict(source_conflicts),
                'scope': data['period'], 'definitions': {
                    'start': 'grid-to-first-crossing; no pitlane; exact field/layout; leave-driver-out reference',
                    'race': 'first-crossing-to-finish; confirmed on-track finishers only',
                    'regularity': '1.4826*MAD of residuals around Theil-Sen pit-interval trend / median lap time *100',
                    'network': 'within-team common qualifying segment log-time ratio, driver network ridge; cluster intervals',
                    'forecast': 'pre-weekend prior-result model; validation 2021-2023, test 2024+; prospectively unvalidated'},
                'files': []}
    registry['delivery'] = {
        'A_definitions':'implemented', 'B_basic_facts':'implemented_with_explicit_source_gaps',
        'C_own_profiles':'implemented', 'D_incidents':'implemented_with_partial_document_coverage',
        'E_observed_GOAT':'implemented', 'F_common_support':'implemented_with_race_weighted_intervals',
        'G_cross_era_network':'experimental_validation_gate_not_passed',
        'H_strategy':'observed_atlas_and_assumption_time_balance; no causal opponent-response model',
        'I_race_findings':'implemented_from_shared_measured_ledger',
        'J_forecast':'walk_forward_and_immutable_prospective_archive; prospective_validation_pending'}
    registry['basic_fact_rows'] = len(records)
    registry['incident_audit'] = {k:incident_audit[k] for k in
        ('version','documents','reparsed','outcomes','linked_decision_roles','retained_only_entries')}
    registry['incident_audit']['restored_missing_legacy_dnf'] = len(legacy_omitted)
    registry['incident_audit']['finish_evidence_conflicts'] = len(conflicts)
    registry['incident_audit']['changed_documents'] = len(incident_audit['changed_documents'])
    all_rows = [row for driver in data['drivers'] for row in driver['races']]
    registry['source_entry_checks'] = {
        'pitlane_records':sum(row['source_pitlane_start'] for row in all_rows),
        'additional_pitlane_flags':sum(row['source_pitlane_start'] and not row.get('pitlane_start') for row in all_rows),
        'shared_car_records':sum(row['source_shared_car'] for row in all_rows),
        'measured_start_observations':sum(row['start_eligible'] for row in all_rows),
        'measured_progression_observations':sum(row['race_eligible'] for row in all_rows)}
    registry['profiles_without_season_facts'] = [did for did,f in facts['drivers'].items() if not f['seasons']]
    registry['identity_signature_links'] = signature_links
    # Lossless column tables eliminate repeated property names, not observations.
    # Profiles and GOAT share these files; consumers unpack only where needed.
    fact_columns = list(dict.fromkeys(k for r in records for k in r))
    facts['race_columns'] = fact_columns
    for d in data['drivers']:
        for row in d['races']:
            row.pop('fact', None)
        fd = facts['drivers'][d['id']]
        fd['races'] = [[r.get(k) for k in fact_columns] for r in fd['races']]
    cycle_columns = list(data['cycles'][0]) if data['cycles'] else []
    data['cycles'] = {'columns': cycle_columns, 'rows': [[r.get(k) for k in cycle_columns] for r in data['cycles']]}
    data['development_version'] = VERSION
    data['retained_definition_version'] = data['definition_version']
    data['definition_version'] = data['definition_version']+'/development-exact-layout-fields-v1/verified-source-entry-exclusions-v1'
    collection = collection_ledger(tables, data, registry, weather)
    registry['files'].extend(partition_profiles(data))
    registry['files'].extend(partition_facts(facts, data))
    for name, value, variable in [('profiles',data,'phase2Data'),('facts',facts,'phase2Facts'),
                                  ('models',models,'phase2Models'),('findings',findings,'phase2Findings'),
                                  ('atlas',atlas,'phase2Atlas')]:
        registry['files'].append(write(name,value,variable))
    registry['files'].append(write('collection',collection,'phase2Collection'))
    subprocess.run([os.environ.get('PHASE2_NODE','node'), str(Path(__file__).with_name('export-metrics.cjs'))],
                   cwd=ROOT, check=True)
    metric_data = json.loads((DATA/'starter-metrics.json').read_text())
    registry['files'].append(write('starter-metrics',metric_data,'phase2StarterMetrics'))
    registry['bytes'] = sum(r['bytes'] for r in registry['files'])
    if registry['bytes'] > 64_000_000:
        raise ValueError('Development shared research payload exceeds its 64 MB limit')
    write('registry',registry,'phase2Registry')
    (ROOT/'_development/build-report.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    print('Built shared bytes', registry['bytes'], flush=True)
    patch_pages()


def patch_pages():
    for filename in ['coureurs_2.html','goat_2.html','races_2.html']:
        p = ROOT/filename; text = p.read_text()
        text = re.sub(r'<script[^>]*data-phase2-research[^>]*>.*?</script>', '', text, flags=re.S)
        text = re.sub(r'<link[^>]*data-phase2-research[^>]*>', '', text)
        text = re.sub(r'<script[^>]*src=["\']_development/assets/research-profile.js["\'][^>]*>.*?</script>', '', text)
        common = '<link rel="stylesheet" data-phase2-research href="_development/assets/research.css">'
        # The retained race document has an implicit head, so inserting after title works everywhere.
        text = text.replace('</title>', '</title>'+common, 1)
        if filename == 'coureurs_2.html':
            text = re.sub(r'(<script[^>]*id=["\']phase2-data["\'][^>]*>).*?(</script>)', r'\1{}\2', text, flags=re.S)
            boot = ''.join('<script data-phase2-research src="_development/data/'+f+'.js"></script>' for f in ('profiles','facts','registry'))
            boot += '<script data-phase2-research src="_development/assets/qualifying-years.js"></script>'
            boot += '<script data-phase2-research src="_development/assets/research-loader.js"></script>'
            text = text.replace('<script src="_development/assets/pit-programmes.js">', boot+'<script data-phase2-research src="_development/assets/research-profile.js"></script><script src="_development/assets/pit-programmes.js">', 1)
        elif filename == 'goat_2.html':
            text = re.sub(r'<script[^>]*src=["\']_development/assets/goat.js["\'][^>]*>.*?</script>', '', text)
            text = re.sub(r'(<main\b[^>]*id=["\']goat-plan["\'][^>]*>).*?(</main>)',
                          r'\1<section class="research-panel"><h2 data-nl="De vergelijking wordt voorbereid" data-en="Preparing the comparison">De vergelijking wordt voorbereid</h2></section>\2', text, flags=re.S)
            text = text.replace('data-en="GOAT · Winter break','data-en="GOAT · Research').replace('GOAT · Winter break','GOAT · Onderzoek')
            text = text.replace('Deze vergelijking is nog in de ontwerpfase.','Vergelijk feiten, gedeelde context en onderzoeksmodellen.')
            text = text.replace('This comparison is still in the design phase.','Compare facts, common contexts and research models.')
            boot = ''.join('<script data-phase2-research src="_development/data/'+f+'.js"></script>' for f in ('profiles','facts','models','registry'))
            boot += '<script data-phase2-research src="_development/assets/research-loader.js"></script>'
            text = text.replace('</body>', boot+'<script data-phase2-research src="_development/assets/research-profile.js"></script><script data-phase2-research src="_development/assets/goat-research.js"></script></body>')
        else:
            boot = ''.join('<script data-phase2-research src="_development/data/'+f+'.js"></script>' for f in ('findings','atlas','registry'))
            text = text.replace('</body>', boot+'<script data-phase2-research src="_development/assets/race-research.js"></script></body>')
        p.write_text(text)


if __name__ == '__main__':
    main()
