"""Compact measured lap clocks for descriptive, driver-specific pit comparisons.

A packed observation is duration_ms * 100 + position (0 = missing position).
No inferred pit stop, compound, missing time, or counterfactual is exported.
The browser can evaluate both a whole pit programme and individual stop laps
without duplicating an opponent-pair matrix for every driver.
"""
from collections import Counter, defaultdict
import math
import re

VERSION = 'registered-pit-programmes-v1'
PACK = 100


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def integer(x):
    return finite(x) and int(x) == x


def finished(driver):
    result = driver.get('result') or {}
    if any(result.get(k) is True for k in ('dnf', 'dns', 'dsq')):
        return False
    if result.get('dnf') is False:
        return True
    status = str(driver.get('status') or '').strip()
    return status == 'Finished' or bool(re.fullmatch(r'\+\d+ Laps?', status))


def analyse(payload, raw=None):
    raw = raw or {}
    explorer = payload.get('explorer') or {}
    entries, excluded = [], {}
    stops, bad_pits = defaultdict(set), set()
    drivers = {d['driver_number']: d for d in payload.get('drivers', [])}
    records = explorer.get('pit')
    has_feed = isinstance(records, list) and bool(records)
    for record in records or []:
        n, lap = record.get('driver'), record.get('lap')
        if n not in drivers:
            continue
        if not integer(lap) or lap < 1:
            bad_pits.add(n)
        else:
            stops[n].add(int(lap))
    # Disagreement is unknown coverage, never silently the smaller stop count.
    raw_stops = defaultdict(set)
    if isinstance(raw.get('pit'), list) and raw['pit']:
        for record in raw['pit']:
            n, lap = record.get('driver_number'), record.get('lap_number')
            if n not in drivers:
                continue
            if integer(lap) and lap >= 1:
                raw_stops[n].add(int(lap))
            else:
                bad_pits.add(n)
        for n in drivers:
            if raw_stops[n] != stops[n]:
                bad_pits.add(n)
    # Zero is accepted only with an explicitly complete historical register or
    # an available modern pit feed that agrees with the dashboard register.
    allow_zero = (payload.get('strategy_detection') or {}).get('complete') is True or bool(raw.get('pit'))
    times, positions, conflicts = {}, {}, set()
    for row in payload.get('all_laps', []):
        n, lap, duration = row.get('driver'), row.get('lap'), row.get('duration')
        if n not in drivers or not integer(lap) or lap < 1 or not finite(duration) or duration <= 0:
            continue
        key = n, int(lap)
        ms = round(duration * 1000)
        if key in times and times[key] != ms:
            conflicts.add(n)
        times[key] = ms
    for row in payload.get('positions', []):
        n, lap, position = row.get('driver'), row.get('lap'), row.get('position')
        if n in drivers and integer(lap) and lap >= 1 and integer(position) and 1 <= position < PACK:
            key = n, int(lap)
            if key in positions and positions[key] != position:
                conflicts.add(n)
            positions[key] = int(position)
    flags = defaultdict(int)
    for row in explorer.get('neutral', []):
        if integer(row.get('lap')):
            flags[int(row['lap'])] |= 1
    for lap in explorer.get('red', []):
        if integer(lap):
            flags[int(lap)] |= 2
    context_known = bool(explorer.get('neutral') or explorer.get('red'))
    for row in raw.get('laps', []):
        lap, status = row.get('lap_number'), str(row.get('track_status') or '')
        if not integer(lap):
            continue
        context_known |= bool(status)
        if any(code in status for code in ('4', '6', '7')):
            flags[int(lap)] |= 1
        if '5' in status:
            flags[int(lap)] |= 2
    for row in payload.get('all_laps', []):
        reasons = ' '.join(str(x).lower() for x in row.get('reasons') or [])
        if any(x in reasons for x in ('neutral', 'safety car', 'vsc')) and integer(row.get('lap')):
            flags[int(row['lap'])] |= 1
    for n, d in drivers.items():
        result = d.get('result') or {}
        laps = result.get('number_of_laps')
        reason = None
        if not finished(d):
            reason = 'not_confirmed_finisher'
        elif d.get('pitlane_start') or not finite(d.get('grid')) or d['grid'] <= 0:
            reason = 'start_clock'
        elif not has_feed or n in bad_pits or (not stops[n] and not allow_zero):
            reason = 'pit_coverage'
        elif not integer(laps) or laps < 2 or n in conflicts or any((n, l) not in times for l in range(1, int(laps) + 1)):
            reason = 'timing_coverage'
        elif any(l > laps for l in stops[n]):
            reason = 'pit_coverage'
        if reason:
            excluded[str(n)] = reason
            continue
        packed = [times[n, l] * PACK + positions.get((n, l), 0) for l in range(1, int(laps) + 1)]
        entries.append([n, sorted(stops[n]), packed])
    return {'version': VERSION, 'entries': entries, 'excluded': excluded,
            'flags': sorted([lap, mask] for lap, mask in flags.items()),
            'flag_context_known': context_known,
            'coverage': dict(Counter(excluded.values()))}
