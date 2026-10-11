"""Retain the available 2018-2019 timing context without inventing UTC offsets."""
from pathlib import Path
import hashlib, json, logging, math
import fastf1, numpy as np, pandas as pd, requests
from datetime import datetime, timedelta
from fastf1 import api
from f1_analysis.io import utcnow, write_json

ROOT = Path(__file__).resolve().parents[1]
fastf1.Cache.enable_cache(str(ROOT / 'cache/fastf1'))
logging.getLogger('fastf1').setLevel(logging.ERROR)


def value(v):
    if isinstance(v, pd.DataFrame):
        return [value(r) for r in v.to_dict('records')]
    if isinstance(v, dict):
        return {str(k): value(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)):
        return [value(x) for x in v]
    if v is None or pd.isna(v):
        return None
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.isoformat()
    if isinstance(v, (pd.Timedelta, timedelta)):
        return v.total_seconds()
    if isinstance(v, np.generic):
        return value(v.item())
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def main():
    summary = []
    for row in json.loads((ROOT / 'analyses/index.json').read_text()):
        if row['year'] not in (2018, 2019):
            continue
        run = ROOT / 'analyses' / row['path']
        p = run / 'data/raw/fastf1/historical-timing.json'
        if not p.exists():
            continue
        timing = json.loads(p.read_text()); target = run / 'data/normalized/historical-context.json'
        if target.exists():
            summary.append({'year': row['year'], 'round': timing['round'], 'cached': True}); continue
        path = timing['api_path']
        saved = {'year': row['year'], 'round': timing['round'], 'api_path': path, 'parser_version': fastf1.__version__,
                 'clock': 'Time durations are API session-relative seconds; race-control timestamp strings retain their original clock.',
                 'retained_at': utcnow(), 'sources': [], 'errors': {}}
        endpoints = {'race_control': api.race_control_messages, 'weather': api.weather_data,
                     'track_status': api.track_status_data, 'session_status': api.session_status_data,
                     'tyre_updates': api.timing_app_data}
        for key, method in endpoints.items():
            try:
                saved[key] = value(method(path))
            except Exception as exc:
                saved['errors'][key] = str(exc)
        try:
            saved['position_updates'] = value(api.timing_data(path)[1])
        except Exception as exc:
            saved['errors']['position_updates'] = str(exc)
        http = fastf1.Cache._requests_session_cached
        responses = []
        for host in (api.base_url, api.base_url_mirror):
            for page in api.pages.values():
                request = http.prepare_request(requests.Request('GET', host + path + page, headers=api.headers))
                response = http.cache.get_response(http.cache.create_key(request))
                if response is not None and response.status_code == 200:
                    responses.append(response)
        for response in responses:
            sha = hashlib.sha256(response.content).hexdigest()
            raw = ROOT / 'analyses/sources/fastf1' / (sha + '.body'); raw.parent.mkdir(parents=True, exist_ok=True)
            if not raw.exists():
                raw.write_bytes(response.content)
            saved['sources'].append({'url': response.url, 'sha256': sha, 'local_path': raw.relative_to(ROOT).as_posix(),
                                     'fetched_at': response.created_at.isoformat(), 'publisher': 'Formula 1 timing archive / FastF1'})
        write_json(target, saved)
        stats = {'year': row['year'], 'round': timing['round'], 'position_updates': len(saved.get('position_updates', [])),
                 'weather': len(saved.get('weather', {}).get('Time', [])), 'messages': len(saved.get('race_control', {}).get('Time', [])),
                 'sources': len(saved['sources']), 'errors': saved['errors']}
        summary.append(stats); print(stats, flush=True)
    write_json(ROOT / 'analyses/sources/historical/timing-context-audit.json', summary)


if __name__ == '__main__':
    main()
