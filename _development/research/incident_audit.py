"""Evidence-preserving incident repairs for the development pages only.

Raw observations and the retained incident archive are never rewritten. Result
status, physical retirement, personal responsibility and sanctions are separate.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
import re

from f1_analysis.incidents import extract_decision, retirement_category

VERSION = 'incident-outcomes-and-document-subjects-v2'
NON_STARTS = {'DNS', 'DNQ', 'DNPQ', 'WD', 'EX', 'DNP'}


def cause(reason):
    category = retirement_category(reason)
    value = (reason or '').strip().casefold()
    if value == 'spin':
        return 'incident'
    if value in {'axle', 'axle shaft', 'drive shaft'}:
        return 'technical'
    if value in {'fire', 'damage', 'debris'}:
        return 'ambiguous'
    return category


def result_outcome(fact, retained=None):
    """No DNF flag required. Numeric classification does not prove a finish.

    NC alone does not prove retirement either. Shared cars and absent evidence
    remain unresolved. Explicit non-start / DSQ statuses take precedence.
    """
    old = retained or {}
    status = str(fact.get('status') or '').upper()
    reason = fact.get('reason')
    legacy = old.get('finish_status')
    source_category, old_category = cause(reason), cause(legacy)
    if not reason and legacy and old_category != 'finished':
        fact['reason'] = reason = legacy
    fact['category'] = source_category if source_category != 'unknown' else old_category
    if fact['category'] == 'finished':
        fact['category'] = 'unknown'
    if (reason and legacy and source_category not in {'unknown', 'finished'}
            and old_category not in {'unknown', 'finished'} and source_category != old_category
            and old_category != 'disqualified' and source_category != 'disqualified'):
        fact['category'] = 'conflicting_sources'
    if fact.get('shared'):
        return 'shared'
    if status in NON_STARTS:
        return 'not_started'
    if status == 'DSQ':
        return 'disqualified'
    explicit_reason = bool(reason and cause(reason) not in {'finished', 'disqualified'}
                           and str(reason).casefold() not in {'not classified', 'unknown'})
    if fact.get('started') and (status == 'DNF' or explicit_reason
                               or old.get('dnf') is True):
        if old.get('finished_on_track') is True:
            fact['finish_evidence_conflict'] = True
        return 'retired'
    if old.get('finished_on_track') is True:
        return 'finished'
    if old.get('finished_on_track') is False:
        return 'unknown'
    if status.isdigit() and not reason:
        return 'finished'
    return 'unknown'


def prepare_text(text):
    """Normalize old N°/Nº headings and true standalone form labels.

    Narrative 'Decision in Document 34' is not an operative Decision field.
    Preserve all body wording; only fix form separators passed to the parser.
    """
    text = text.replace('\xa0', ' ').replace('\u00ad', '-').replace('\u2011', '-')
    text = re.sub(r'(?im)^(\s*)N[°ºo]\s*/\s*Driver\b', r'\1No / Driver', text)
    labels = r'No\s*/\s*Driver|Driver|Competitor|Session|Facts?|Offence|Infringement|Decision|Reasons?'
    lines = []
    for line in text.splitlines():
        if re.fullmatch(r'\s*(?:' + labels + r')\s*:?\s*', line, re.I):
            line = line.rstrip().rstrip(':') + '  '
        elif re.match(r'^\s*(?:Decision|Reason)\s+\S', line, re.I) and not re.match(
                r'^\s*(?:Decision|Reason)\s{2,}', line, re.I):
            # Make a narrative heading invisible to the form-section matcher.
            line = '\u200b' + line
        lines.append(line)
    return '\n'.join(lines)


def parse_document(record, text):
    updated = deepcopy(record)
    parsed = extract_decision(record['title'], prepare_text(text))
    updated.update(parsed)
    # A shared No/Driver field is a joint subject, not the first named driver.
    label = parsed.get('driver_label') or ''
    subjects = sorted(set(int(n) for n in re.findall(
        r'(?:^|\s)(\d{1,3})\s*[-–—]\s*[A-Za-zÀ-ž]', label)))
    if subjects:
        updated['subject_numbers'] = subjects
        updated['driver_number'] = subjects[0] if len(subjects) == 1 else None
        updated['involved_numbers'] = sorted(set(subjects + parsed['involved_numbers']))
    elif parsed.get('driver_number') is not None:
        updated['subject_numbers'] = [parsed['driver_number']]
    else:
        updated['subject_numbers'] = []
    decision = updated.get('decision') or ''
    # Formal reviews, protest fees and references to earlier penalties do not
    # themselves impose a new personal sanction.
    if (re.search(r'right of review|request for.*review|protest', record['title'] + ' ' + text[:1500], re.I)
            and not updated['subject_numbers'] and updated['outcome'] != 'overturned'):
        updated.update(outcome='review', sanction_types=[], time_penalty_seconds=None,
                       grid_places=None, penalty_points=None)
    if re.search(r'\bDeletion of (?:the )?lap times\b', decision, re.I):
        updated.update(outcome='penalty', sanction_types=['lap_deletion'])
    # Words such as 'ten' occur in operative penalties in later templates.
    words = {'five':5, 'ten':10, 'twenty':20}
    if updated['outcome'] == 'penalty':
        seconds = re.search(r'\b(five|ten|twenty)[ -]second(?:s)?\s+(?:time\s+)?penalty', decision, re.I)
        if seconds and updated['time_penalty_seconds'] is None:
            updated['time_penalty_seconds'] = words[seconds[1].lower()]
        # Suspending a stop/go or fine is not a suspension of the driver.
        if 'ban' in updated['sanction_types'] and not re.search(
                r'super\s*licen[cs]e.{0,120}suspend|driver.{0,60}suspend.{0,50}(?:competition|race)|race ban', decision, re.I):
            updated['sanction_types'].remove('ban')
    # Old effective version decisions remain authoritative until reconciled.
    updated['effective_outcome'] = (record['effective_outcome']
        if record['effective_outcome'] in {'superseded', 'overturned'} else updated['outcome'])
    updated['sanction_recipient'] = ('competitor' if re.search(
        r'\bcompetitor\b.{0,100}\bfined\b', decision, re.I) else 'driver_or_car')
    updated['table_sanctions'] = []
    if re.search(r'No\s+No\s*/\s*Driver\s+Competitor\s+Penalty', decision, re.I):
        # One document can contain several separate penalties for one driver.
        pattern = r'\b(\d+)\s+(\d{1,3})\s*[-–—]\s+(.+?)\s+(\d+)\s+second\s+time\s+penalty'
        for item in re.finditer(pattern, decision, re.I):
            updated['table_sanctions'].append({'row':int(item[1]), 'number':int(item[2]),
                                               'seconds':int(item[4])})
        if updated['table_sanctions']:
            updated['subject_numbers'] = sorted({s['number'] for s in updated['table_sanctions']})
    # Explicit car columns in collective deletion/warning forms, never arbitrary
    # numbers mentioned in a reason or another driver's earlier incident.
    if (updated['outcome'] == 'penalty' and ('lap_deletion' in updated['sanction_types'] or re.search(
            r'Decision\s+Car\s+Driver\s+Competitor', text, re.I))):
        deletion = 'lap_deletion' in updated['sanction_types']
        pattern = (r'^\s*(\d+)\s+\d+\s+(\d{1,3})\s+[A-Za-zÀ-ž].*?\d{1,2}:\d{2}:\d{2}'
                   if deletion else r'^\s*(\d+)\s+(\d{1,3})\s+[A-Za-zÀ-ž]')
        cells = list(re.finditer(pattern,text,re.M))
        if cells:
            updated['subject_numbers'] = sorted({int(s[2]) for s in cells})
            if deletion:
                updated['deleted_laps_by_number'] = dict(Counter(int(s[2]) for s in cells))
                # The table is a separate form element, not part of the Fact
                # paragraph. Its own-driver values and original PDF are kept.
                updated['fact'] = re.split(r'\bNo\.?\s+Turn\s+Car\s+Driver\s+Competitor\b',
                                           updated.get('fact') or '', maxsplit=1, flags=re.I)[0].strip()
                updated['fact'] = re.split(r'\bNo\.?\s+Tur\b|\s+\d+\s+\d+\s+\d+\s+[A-Za-zÀ-ž]',
                                           updated['fact'], maxsplit=1)[0].strip()
    return updated


def repair_documents(archive, root):
    """Re-read every available retained text and register every changed field."""
    records, changes, unavailable = [], [], []
    for original in archive['decisions']:
        source = archive['sources'].get(original['source'], {})
        path = root / source.get('local_file', '__missing__')
        text_file = path.with_suffix('.txt')
        if not text_file.exists():
            unavailable.append(original['id'])
            updated = deepcopy(original)
            updated['subject_numbers'] = ([original['driver_number']] if original.get('driver_number') is not None else [])
        else:
            updated = parse_document(original, text_file.read_text(errors='replace'))
        changed = {k:{'old':original.get(k), 'new':updated.get(k)} for k in
                   ['driver_number','involved_numbers','session','fact','decision','outcome','sanction_types',
                    'time_penalty_seconds','grid_places','penalty_points'] if original.get(k) != updated.get(k)}
        prior_subjects = [original['driver_number']] if original.get('driver_number') is not None else []
        if prior_subjects != updated['subject_numbers']:
            changed['recipient_numbers'] = {'old':prior_subjects,'new':updated['subject_numbers']}
        if changed:
            changes.append({'id':original['id'], 'race':original['race'], 'changes':changed})
        records.append(updated)
    return records, {'version':VERSION, 'documents':len(records), 'reparsed':len(records)-len(unavailable),
                     'unavailable_text':unavailable, 'changed_documents':changes,
                     'outcomes':dict(Counter(d['effective_outcome'] for d in records))}


def decision_rosters(tables, identities):
    result = defaultdict(lambda: defaultdict(set))
    for table, rows in tables.items():
        if not (table in {'races-race-results','races-qualifying-results','races-sprint-race-results',
                          'races-sprint-qualifying-results','races-sprint-shootout-results'}
                or table.startswith('races-free-practice-')):
            continue
        session = ({'races-race-results':'Race','races-qualifying-results':'Qualifying',
                    'races-sprint-race-results':'Sprint','races-sprint-qualifying-results':'Sprint Qualifying',
                    'races-sprint-shootout-results':'Sprint Shootout'}.get(table)
                   or 'Practice ' + table.split('-')[-2])
        for row in rows:
            did = identities.get(row['driverId'])
            number = row.get('driverNumber', '')
            if did and number.isdigit():
                result[(row['year']+'-'+row['round'],session)][int(number)].add(did)
    return result


def decision_targets(decision, rosters):
    """Subjects receive their sanction; other involved drivers get involvement.

    Session-specific rosters prevent FP1 substitutes being attributed to the
    race driver who used the same car number. Unknown/multi-driver matches stay
    unresolved rather than guessed.
    """
    session = (decision.get('session') or '').strip()
    if session.startswith('Qualifying and '): session = 'Qualifying'
    session = re.sub(r'(?i)^(?:FP|Free Practice|Practice)\s*(\d)$', r'Practice \1', session)
    race = decision['race']
    roster = rosters.get((race,session), {})
    if not roster:
        combined = defaultdict(set)
        for (rid,_), cars in rosters.items():
            if rid == race:
                for n, drivers in cars.items(): combined[n].update(drivers)
        roster = combined
    subjects = set(decision.get('subject_numbers') or [])
    # Involved numbers in unresolved general documents can be unrelated numeric
    # references. Only a concrete ruling/summons establishes an incident link.
    involved = set(decision.get('involved_numbers') or []) if (
        decision.get('is_collision') and decision.get('effective_outcome') in {
        'penalty','no_further_action','summons','review','superseded','overturned'}) else set()
    targets = []
    for n in sorted(subjects | involved):
        ids = roster.get(n,set())
        if len(ids) == 1:
            targets.append((next(iter(ids)),n,'subject' if n in subjects else 'involved'))
    return targets
