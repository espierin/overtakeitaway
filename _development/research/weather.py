"""Dated forecast snapshots; never replace observations or a previous forecast."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import hashlib
import json


def snapshot(directory, race, circuits):
    if not race:
        return {'available': False, 'reason': 'no_upcoming_race'}
    directory = Path(directory); directory.mkdir(exist_ok=True)
    latest = directory/'latest.json'
    if latest.exists():
        old = json.loads(latest.read_text())
        age = (datetime.now(timezone.utc)-datetime.fromisoformat(old['retrieved_at'])).total_seconds()
        if old['race_id'] == race['id'] and age < 21600:
            return old
    circuit = next((c for c in circuits if c['id'] == race['circuitId']), {})
    result = {'race_id': race['id'], 'race_date': race['date'],
              'start_utc': race['date']+'T'+race['time']+':00Z' if race.get('time') else None,
              'retrieved_at': datetime.now(timezone.utc).isoformat(),
              'model': 'gfs_seamless', 'model_run_issued_at': None,
              'timezone': 'UTC', 'source': 'https://open-meteo.com/en/docs',
              'available': False, 'kind': 'forecast_not_observation'}
    params = {'latitude': circuit.get('latitude'), 'longitude': circuit.get('longitude'),
              'hourly': 'temperature_2m,precipitation_probability,precipitation,wind_speed_10m',
              'models': 'gfs_seamless', 'timezone': 'UTC', 'forecast_days': 16}
    if not params['latitude'] or not params['longitude']:
        result['reason'] = 'circuit_coordinates_unknown'
    else:
        url = 'https://api.open-meteo.com/v1/forecast?'+urlencode(params)
        result['request_url'] = url
        try:
            req = Request(url, headers={'User-Agent': 'OvertakeItAway-research/2'})
            with urlopen(req, timeout=25) as response:
                body = response.read()
            raw = json.loads(body); result['source_sha256'] = hashlib.sha256(body).hexdigest()
            target = result['start_utc'][:16] if result['start_utc'] else None
            times = raw.get('hourly', {}).get('time', [])
            indices = [i for i, t in enumerate(times) if t.startswith(race['date'])]
            if indices:
                i = min(indices, key=lambda i: abs(datetime.fromisoformat(times[i])-datetime.fromisoformat(target))) if target else indices[len(indices)//2]
                result['forecast_valid_at_utc'] = times[i]+':00Z'
                result['values'] = {k: values[i] for k, values in raw['hourly'].items() if k != 'time'}
                result['units'] = raw.get('hourly_units', {})
                result['available'] = True
            else:
                result['reason'] = 'event_outside_returned_forecast_horizon'
            raw_file = directory/(result['source_sha256']+'.json')
            if not raw_file.exists():
                raw_file.write_bytes(body)
        except Exception as exc:
            result['reason'] = type(exc).__name__+': '+str(exc)
    archive = directory/(result['retrieved_at'].replace(':','').replace('+','_')+'-'+race['id']+'.json')
    if not archive.exists():
        archive.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    latest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
