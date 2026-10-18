"""Walk-forward pre-weekend baseline research, never a retrospective forecast.

All features use earlier races. Weights are chosen on 2021–2023 only; 2024+
is held out. Forecasts remain research until a prospective check also passes.
"""
from collections import defaultdict, deque
from datetime import datetime, timezone
import numpy as np
from pathlib import Path
import json
import math


def evaluate(races, records):
    grouped = defaultdict(list)
    for row in records:
        if row.get('started') and row.get('classification_order') and not row.get('shared'):
            grouped[row['race']].append(row)
    team = defaultdict(lambda: deque(maxlen=30))
    driver = defaultdict(lambda: deque(maxlen=12))
    circuit = defaultdict(lambda: deque(maxlen=5))
    experiments = []
    for race in sorted(races, key=lambda r: r['date']):
        rows = grouped.get(race['id'], [])
        if len(rows) < 5:
            continue
        n = len(rows)
        ordering = {id(row):i+1 for i,row in enumerate(sorted(rows,key=lambda r:r['classification_order']))}
        for row in rows:
            if len(team[row['team_id']]) < 6 or len(driver[row['driver']]) < 3:
                continue
            features = [float(np.mean(team[row['team_id']])), float(np.mean(driver[row['driver']])),
                        float(np.mean(circuit[row['driver'], race['layout']]))
                        if circuit[row['driver'], race['layout']] else float(np.mean(driver[row['driver']]))]
            experiments.append({'race': race['id'], 'year': race['year'], 'date': race['date'],
                                'driver': row['driver'], 'features': features,
                                'target': (ordering[id(row)]-1)/(n-1)})
        # Update after EVERY driver's prediction; no same-race result can leak.
        for row in rows:
            outcome = (ordering[id(row)]-1)/(n-1)
            team[row['team_id']].append(outcome)
            driver[row['driver']].append(outcome)
            circuit[row['driver'], race['layout']].append(outcome)
    validation = [e for e in experiments if 2021 <= e['year'] <= 2023]
    test = [e for e in experiments if e['year'] >= 2024]
    weights = [(1., 0., 0.), (.75, .25, 0.), (.5, .5, 0.), (.5, .25, .25), (.25, .5, .25)]
    loss = lambda rows, w: float(np.mean([abs(np.dot(e['features'], w)-e['target']) for e in rows])) if rows else None
    best = min(weights, key=lambda w: loss(validation, w) if validation else float('inf'))
    mae, baseline = loss(test, best), loss(test, weights[0])
    return {'definition': 'prior-results-walk-forward-v1', 'weights': best,
            'validation_years': [2021, 2023], 'test_years': [2024, max([r['year'] for r in races], default=2024)],
            'validation_races': len({e['race'] for e in validation}), 'test_races': len({e['race'] for e in test}),
            'test_observations': len(test), 'test_mae': mae, 'baseline_mae': baseline,
            'passes_retrospective': mae is not None and len({e['race'] for e in test}) >= 20 and mae < baseline,
            'passes_prospective': False, 'public_forecast_enabled': False,
            'reason': 'prospective_validation_pending',
            'experiments': experiments,
            'features': 'Only earlier main-race classified results; no current grid, weather or future result.',
            'candidate_generator': {'teams': {k: float(np.mean(v)) for k, v in team.items() if v},
                                    'drivers': {k: float(np.mean(v)) for k, v in driver.items() if v}}}


def candidate(model, upcoming, roster, issued_at=None):
    """Archive a joint research scenario before a future event; never overwrite it."""
    if not upcoming:
        return None
    state = model['candidate_generator']; w = model['weights']; means = []
    for r in roster:
        t, d = state['teams'].get(r['team_id']), state['drivers'].get(r['driver'])
        if t is not None and d is not None:
            means.append((r['driver'], w[0]*t+(w[1]+w[2])*d))
    if len(means) < 5:
        return None
    rng = np.random.default_rng(172026)
    # Scenario spread is calibrated to validation errors, not an assertion of car-independent skill.
    residuals = [e['target']-float(np.dot(e['features'], w)) for e in model['experiments'] if 2021 <= e['year'] <= 2023]
    draws = np.array([m for _, m in means])[None, :]+rng.choice(residuals, (10000, len(means)))
    orders = np.argsort(np.argsort(draws, axis=1), axis=1)+1
    return {'event': upcoming, 'issued_at': issued_at or datetime.now(timezone.utc).isoformat(),
            'stage': 'pre-weekend-research', 'roster_assumption': 'last completed main-race entrants',
            'weather_used': False, 'qualifying_used': False,
            'public_forecast_enabled': False, 'validation': model['reason'],
            'drivers': [{'driver': d, 'win': float(np.mean(orders[:, i] == 1)),
                         'podium': float(np.mean(orders[:, i] <= 3)),
                         'median_position': float(np.median(orders[:, i])),
                         'interval': np.quantile(orders[:, i], [.1, .9]).tolist()}
                        for i, (d, _) in enumerate(means)]}


def score_archive(directory, records):
    """Evaluate only forecasts genuinely issued before the now-completed event."""
    grouped = defaultdict(list)
    for row in records:
        if row.get('started') and not row.get('shared'):
            grouped[row['race']].append(row)
    evaluated=[];pending=[]
    for path in sorted(Path(directory).glob('*-pre-weekend.json')):
        forecast=json.loads(path.read_text());event=forecast['event'];rid=event['year']+'-'+event['round']
        actual=grouped.get(rid,[])
        if not actual:
            pending.append({'race':rid,'reason':'race_not_in_retained_results'});continue
        start=event['date']+'T'+event['time']+':00+00:00' if event.get('time') else None
        if not start or datetime.fromisoformat(forecast['issued_at']) >= datetime.fromisoformat(start):
            pending.append({'race':rid,'reason':'not_a_verified_pre_race_snapshot'});continue
        expected={r['driver']:r for r in forecast['drivers']}
        if set(expected)!={r['driver'] for r in actual}:
            pending.append({'race':rid,'reason':'roster_assumption_did_not_match'});continue
        if sum(r.get('position')==1 for r in actual)!=1:
            pending.append({'race':rid,'reason':'winner_not_confirmed'});continue
        n=len(actual);win=[];podium=[]
        for row in actual:
            prediction=expected[row['driver']]
            win.append((prediction['win']-int(row.get('position')==1))**2)
            podium.append((prediction['podium']-int(row.get('position') in (1,2,3)))**2)
        winner=next(r['driver'] for r in actual if r.get('position')==1)
        result={'race':rid,'win_brier':float(np.mean(win)),'podium_brier':float(np.mean(podium)),
                'uniform_win_brier':(n-1)/n**2,'uniform_podium_brier':3*(n-3)/n**2,
                'winner_log_loss':-math.log(max(1e-12,expected[winner]['win'])),
                'forecast_file':path.name,'forecast_issued_at':forecast['issued_at']}
        evaluation=path.with_name(path.stem+'-evaluation.json')
        if not evaluation.exists():evaluation.write_text(json.dumps(result,indent=2)+'\n')
        evaluated.append(result)
    passes=len(evaluated)>=10 and np.mean([r['win_brier'] for r in evaluated])<np.mean([r['uniform_win_brier'] for r in evaluated])
    return {'evaluated':evaluated,'pending':pending,'minimum_prospective_races':10,
            'passes':bool(passes),'calibration_status':'insufficient_prospective_events' if len(evaluated)<10 else 'evaluate_probability_bins'}
