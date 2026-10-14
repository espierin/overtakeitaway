"""Retain small, replayable driver inputs from the historical F1 timing feed.

No car/location telemetry is downloaded. All clocks below are session-relative
seconds, not invented UTC timestamps. Existing race dashboards remain unchanged.
"""
from copy import deepcopy
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from .io import read_json, utcnow

VERSION = 'fastf1-driver-history-v1'


def guard_tyre_updates(session):
    """Isolate FastF1's known out-of-range stint-message failure (Monza 2018).

    A rejected driver's tyre messages become unavailable, never guessed. Other
    drivers and the measured lap feed remain loadable. No library is modified.
    """
    original = session._Session__fix_tyre_info
    rejected = []
    def guarded(frame, splits):
        try:
            return original(frame, splits)
        except IndexError:
            rejected.extend(str(n) for n in frame['Driver'].unique())
            return frame.iloc[:0].copy()
    session._Session__fix_tyre_info = guarded
    return rejected


def enrich(payload, raw):
    """Join verified set/age observations; never infer new sets from compounds."""
    if raw.get('format') != VERSION:
        raise ValueError('Unsupported driver-history input')
    result = deepcopy(payload)
    indexed = {(r['driver_number'], r['lap_number']): r for r in raw['laps']}
    for lap in result.get('all_laps', []):
        row = indexed.get((lap['driver'], lap['lap']))
        if row is None:
            lap['reasons'] = list(lap.get('reasons') or []) + ['historical timing not verified']
            continue
        # Do not combine a lap time from one source with a disagreeing timing row.
        if not isinstance(row.get('lap_duration'), (int, float)) or abs(row['lap_duration']-lap['duration']) > .1:
            lap['reasons'] = list(lap.get('reasons') or []) + ['historical timing mismatch']
            continue
        lap['tyre'] = {'compound': row.get('compound') or 'UNKNOWN', 'age': row.get('age')}
        reasons = list(lap.get('reasons') or [])
        if not row.get('accurate') or row.get('deleted'):
            reasons.append('historical lap quality')
        if row.get('track_status') != '1':
            reasons.append('historical track flag')
        if row.get('pit_in') or row.get('pit_out'):
            reasons.append('historical pit lap')
        lap['reasons'] = reasons
    result['tyres'] = dict(result.get('tyres', {}), stints=raw.get('stints', []))
    return result


def collect(root, years):
    import fastf1
    import pandas as pd
    from fastf1 import api
    from .phase2 import extract
    root = Path(root).resolve()
    cache = root/'cache/fastf1'; cache.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache))
    report = []
    def number(v):
        return None if pd.isna(v) else int(v)
    def seconds(v):
        return None if pd.isna(v) else float(v.total_seconds())
    def gap(v):
        try:
            result = float(v)
            return result if math.isfinite(result) else None
        except (TypeError, ValueError):
            return None
    for year in years:
        for page, payload, _ in extract(root, year):
            target = page.parent/'data/normalized/driver-history.json.gz'
            if target.exists():
                saved = read_json(target.with_suffix(''))
                report.append({'year': year, 'round': saved['round'], 'laps': len(saved['laps']), 'cached': True})
                continue
            timing = page.parent/'data/raw/fastf1/historical-timing.json'
            if not timing.exists():
                report.append({'year': year, 'race': payload['race'], 'status': 'no timing archive'})
                continue
            meta = read_json(timing)
            try:
                session = fastf1.get_session(year, meta['round'], 'R')
                rejected = guard_tyre_updates(session)
                session.load(telemetry=False, weather=False, messages=False)
                stream = api.timing_data(session.api_path)[1]
                saved = {'format': VERSION, 'clock': 'session-seconds', 'year': year, 'round': meta['round'],
                         'retained_at': utcnow(), 'parser_version': fastf1.__version__, 'api_path': session.api_path,
                         'sources': meta.get('source_urls', []), 'rejected_tyre_drivers': sorted(set(rejected)),
                         'laps': [], 'position': [], 'intervals': [], 'stints': []}
                for row in session.laps.to_dict('records'):
                    if row.get('FastF1Generated') or pd.isna(row['LapNumber']):
                        continue
                    age = gap(row['TyreLife'])
                    saved['laps'].append({'driver_number': int(row['DriverNumber']), 'lap_number': int(row['LapNumber']),
                        'time_start': seconds(row['LapStartTime']), 'lap_duration': seconds(row['LapTime']),
                        'compound': None if pd.isna(row['Compound']) else str(row['Compound']),
                        'age': age-1 if age is not None and age >= 1 else None,
                        'accurate': False if pd.isna(row['IsAccurate']) else bool(row['IsAccurate']),
                        'deleted': False if pd.isna(row['Deleted']) else bool(row['Deleted']),
                        'track_status': None if pd.isna(row['TrackStatus']) else str(row['TrackStatus']),
                        'pit_in': not pd.isna(row['PitInTime']), 'pit_out': not pd.isna(row['PitOutTime'])})
                for (driver, stint), part in session.laps.groupby(['DriverNumber', 'Stint']):
                    part = part.sort_values('LapNumber')
                    first = part.iloc[0]; age = gap(first['TyreLife'])
                    saved['stints'].append({'driver_number': int(driver), 'stint_number': int(stint),
                        'lap_start': int(part['LapNumber'].min()), 'lap_end': int(part['LapNumber'].max()),
                        'compound': None if pd.isna(first['Compound']) else str(first['Compound']),
                        'tyre_age_at_start': age-1 if age is not None and age >= 1 else None})
                for row in stream.sort_values('Time').to_dict('records'):
                    if pd.isna(row['Time']) or pd.isna(row['Driver']):
                        continue
                    time = seconds(row['Time']); driver = int(row['Driver']); position = number(row['Position'])
                    if position is not None:
                        saved['position'].append({'driver_number': driver, 'time': time, 'position': position})
                    saved['intervals'].append({'driver_number': driver, 'time': time, 'interval': gap(row['IntervalToPositionAhead'])})
                encoded = json.dumps(saved, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix('.tmp')
                temporary.write_bytes(gzip.compress(encoded, mtime=0)); temporary.replace(target)
                report.append({'year': year, 'round': meta['round'], 'laps': len(saved['laps']),
                               'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
            except Exception as exc:
                report.append({'year': year, 'round': meta['round'], 'error': str(exc)})
            print(json.dumps(report[-1]), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--years', type=int, nargs='+', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    rows = collect(args.root, args.years)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
