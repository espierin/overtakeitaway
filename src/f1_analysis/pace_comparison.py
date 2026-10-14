"""Observed teammate pace on common numbered laps, with explicit mean fallback.

A retirement does not discard previously completed common laps. Missing or
excluded timings are never filled; relaxed tyre matching is always identified.
"""
from collections import defaultdict
from statistics import mean, median
import math
import re

VERSION = 'teammate-overlap-pace-v2.1'


def valid(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def percentile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    x = (len(ordered)-1)*fraction
    lo = int(x)
    hi = min(lo+1, len(ordered)-1)
    return round(ordered[lo]+(ordered[hi]-ordered[lo])*(x-lo), 5)


def retired(driver):
    result = driver.get('result') or {}
    if result.get('dns') or result.get('dsq'):
        return False
    if isinstance(result.get('dnf'), bool):
        return result['dnf']
    status = str(driver.get('status') or '').strip()
    if not status:
        return None
    if status == 'Finished' or re.fullmatch(r'\+\d+ Laps?', status):
        return False
    if status.lower() in ('disqualified', 'did not start', 'did not qualify', 'did not prequalify', 'excluded', 'withdrawn'):
        return False
    return True


def analyse(payload, min_laps=6, age_tolerance=2):
    teams = defaultdict(list)
    for driver in payload.get('drivers', []):
        teams[driver.get('team')].append(driver)
    laps, conflicts = {}, set()
    for row in payload.get('all_laps', []):
        lap, duration = row.get('lap'), row.get('duration')
        if not valid(lap) or lap < 1 or int(lap) != lap or not valid(duration) or duration <= 0:
            continue
        key = row.get('driver'), int(lap)
        if key in laps and round(laps[key]['duration'], 3) != round(duration, 3):
            conflicts.add(key)
        laps[key] = row
    for key in conflicts:
        laps.pop(key, None)
    by_driver = defaultdict(set)
    for driver, lap in laps:
        by_driver[driver].add(lap)
    pits = {(r.get('driver'), r.get('lap')) for r in payload.get('explorer', {}).get('pit', [])}
    neutral = {r['lap'] for r in payload.get('explorer', {}).get('neutral', [])} | set(payload.get('explorer', {}).get('red', []))
    neutral.update(r['lap'] for r in payload.get('all_laps', []) if any(
        any(word in str(reason).lower() for word in ('neutral', 'vlag'))
        for reason in r.get('reasons') or []))
    output, exclusions = {}, defaultdict(int)
    for team, drivers in teams.items():
        if not team or len(drivers) != 2:
            exclusions['team_identity_or_pair'] += len(drivers)
            continue
        a, b = drivers
        na, nb = a['driver_number'], b['driver_number']
        if any((d.get('result') or {}).get('dns') for d in (a, b)):
            exclusions['did_not_start'] += 1
            continue
        common = sorted(by_driver[na] & by_driver[nb])
        clean, matched = [], []
        for lap in common:
            ra, rb = laps[na, lap], laps[nb, lap]
            if lap == 1 or lap in neutral or any((n, k) in pits for n in (na, nb) for k in (lap, lap-1)):
                exclusions['start_pit_or_neutral'] += 1
                continue
            if ra.get('reasons') or rb.get('reasons'):
                exclusions['source_quality_or_traffic'] += 1
                continue
            clean.append(lap)
            ta, tb = ra.get('tyre') or {}, rb.get('tyre') or {}
            if not ta.get('compound') or ta['compound'] == 'UNKNOWN' or ta['compound'] != tb.get('compound'):
                exclusions['compound'] += 1
                continue
            if not valid(ta.get('age')) or not valid(tb.get('age')) or min(ta['age'], tb['age']) < 0 or abs(ta['age']-tb['age']) > age_tolerance:
                exclusions['age'] += 1
                continue
            matched.append(lap)
        if len(matched) >= min_laps:
            used, method = matched, 'matched-median'
        elif matched:
            used, method = matched, 'matched-mean'
        elif clean:
            used, method = clean, 'overlap-mean'
        else:
            exclusions['insufficient_pair'] += 1
            continue
        own_mean = mean(laps[na, l]['duration'] for l in used)
        mate_mean = mean(laps[nb, l]['duration'] for l in used)
        deltas = [200*(laps[na, l]['duration']-laps[nb, l]['duration'])/(laps[na, l]['duration']+laps[nb, l]['duration']) for l in used]
        center = median(deltas) if method == 'matched-median' else 200*(own_mean-mate_mean)/(own_mean+mate_mean)
        distances = []
        for d in (a, b):
            n = d['driver_number']
            completed = (d.get('result') or {}).get('number_of_laps')
            extent = max(by_driver[n], default=0)
            confirmed = valid(completed) and completed > 0 and int(completed) == completed
            # Available paired timing, not an inconsistent classification, sets
            # the usable extent. Claim completed race distance only if it agrees.
            distances.append((d, extent, confirmed and int(completed) == extent))
        limiting_laps = min(count for _, count, _ in distances)
        limiting = [d['name'] for d, count, _ in distances if count == limiting_laps]
        retirements = [d['name'] for d in (a, b) if retired(d) is True]
        for d, other, sign, avg, other_avg in ((a, b, 1, own_mean, mate_mean), (b, a, -1, mate_mean, own_mean)):
            output[d['driver_number']] = {
                'teammate': other['name'], 'teammate_code': other['code'],
                'pace_delta_pct': round(sign*center, 5), 'matched_laps': len(used),
                'matched_lap_numbers': used, 'lap_range': [min(used), max(used)],
                'common_timed_laps': len(common), 'method': method,
                'mean_lap_seconds': round(avg, 3), 'teammate_mean_lap_seconds': round(other_avg, 3),
                'retirement_limited': bool(retirements), 'retired_drivers': retirements,
                'limiting_drivers': limiting, 'limiting_laps': limiting_laps,
                'limiting_basis': 'race-distance' if all(known for _, _, known in distances) else 'timing-extent',
                'delta_q25': percentile([sign*x for x in deltas], .25) if method == 'matched-median' else None,
                'delta_q75': percentile([sign*x for x in deltas], .75) if method == 'matched-median' else None,
            }
        if method != 'matched-median':
            exclusions['mean_fallback'] += 1
    return output, dict(exclusions)
