"""Versioned exploratory metrics for the isolated phase-two development pages.

Race is the uncertainty cluster. Missing observations never become zero results.
Only common measured contexts support standardized comparisons.
"""
from collections import defaultdict, Counter
from statistics import median
import math
import numpy as np

VERSION = 'phase2-research-20261017-v1'
RULES = {
    'rank_min_field': 5, 'rank_min_active_coverage': .8,
    'reference_min_races': 8, 'reference_min_other_drivers': 2,
    'reference_windows_years': [5, 10], 'common_context_min_races': 2,
    'regularity_min_laps': 8, 'regularity_min_span': 6,
    'network_min_pairs': 10, 'network_ridge_candidates': [.1, 1., 10.],
    'confidence': .95, 'bootstrap_races': 400,
}


def number(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def quantile(values, p):
    a = sorted(v for v in values if v is not None and math.isfinite(v))
    if not a:
        return None
    x = (len(a)-1)*p
    return a[int(x)] + (a[math.ceil(x)]-a[int(x)])*(x-int(x))


def summary(values, seed=317):
    a = np.asarray([v for v in values if v is not None and math.isfinite(v)], dtype=float)
    if not len(a):
        return {'n': 0, 'median': None, 'q25': None, 'q75': None, 'interval': None}
    result = {'n': len(a), 'median': float(np.median(a)),
              'q25': float(np.quantile(a, .25)), 'q75': float(np.quantile(a, .75)), 'interval': None}
    if len(a) >= 5:
        rng = np.random.default_rng(seed)
        draws = np.median(a[rng.integers(0, len(a), (RULES['bootstrap_races'], len(a)))], axis=1)
        result['interval'] = [float(v) for v in np.quantile(draws, [.025, .975])]
    return result


def trend_regularity(points):
    """Robust detrended spread; caller provides one measured pit/set interval."""
    if len(points) < RULES['regularity_min_laps']:
        return None
    points = sorted(points)
    x, y = np.array(points, dtype=float).T
    if x[-1]-x[0] < RULES['regularity_min_span']:
        return None
    slopes = [(y[j]-y[i])/(x[j]-x[i]) for i in range(len(x))
              for j in range(i+1, len(x)) if x[j] != x[i]]
    slope = median(slopes)
    intercept = float(np.median(y-slope*x))
    residual = y-(slope*x+intercept)
    base = float(np.median(y))
    if base <= 0:
        return None
    spread = 100*1.4826*float(np.median(abs(residual-np.median(residual))))/base
    return {'value': round(spread, 6), 'n': len(points), 'pace_seconds': round(base, 3),
            'trace': [[int(a), round(100*b/base, 5)] for a, b in zip(x, residual)],
            'definition': 'pit-interval-trend-v1'}


def annotate_context(observations):
    """Leave-driver-out reference within exact layout, grid, field and phase.

    Period windows are fixed before scores. No cross-circuit backfill is allowed.
    """
    groups = defaultdict(list)
    for o in observations:
        groups[o['phase'], o['layout'], o['field'], o['origin']].append(o)
    counts = Counter()
    for o in observations:
        group = groups[o['phase'], o['layout'], o['field'], o['origin']]
        o['reference'] = None
        for window in RULES['reference_windows_years']:
            peers = [p for p in group if p['driver'] != o['driver']
                     and abs(p['year']-o['year']) <= window]
            if len({p['race'] for p in peers}) < RULES['reference_min_races']:
                continue
            if len({p['driver'] for p in peers}) < RULES['reference_min_other_drivers']:
                continue
            # At most one observation per driver/race was admitted upstream.
            expected = sum(p['outcome'] for p in peers)/len(peers)
            score = 100*sum((p['outcome'] > o['outcome']) + .5*(p['outcome'] == o['outcome'])
                            for p in peers)/len(peers)
            o['reference'] = {'expected': round(expected, 5),
                              'advantage': round(expected-o['outcome'], 5),
                              'superiority': round(score, 4), 'n': len(peers), 'window': window}
            break
        # Common-support strata are exact; no width is silently chosen by outcomes.
        o['context'] = '|'.join(map(str, [o['layout'], o['field'], o['origin'], o['year']//10*10]))
        counts['reference' if o['reference'] else 'no_reference'] += 1
    return dict(counts)


def standardize(observations, drivers):
    """Identical equal context weights; race resampling is paired across contexts."""
    groups = defaultdict(lambda: defaultdict(list))
    selected = set(drivers)
    for o in observations:
        if o['driver'] in selected and o.get('reference'):
            groups[o['context']][o['driver']].append(o)
    common = {k: v for k, v in groups.items() if all(
        len({r['race'] for r in v.get(d, [])}) >= RULES['common_context_min_races'] for d in drivers)}
    results = []
    for d in drivers:
        measured = [o for v in common.values() for o in v[d]]
        value = float(np.mean([np.mean([o['reference']['advantage'] for o in v[d]])
                               for v in common.values()])) if common else None
        results.append({'driver': d, 'advantage': value, 'contexts': len(common),
                        'races': len({o['race'] for o in measured}), 'observations': measured})
    return results


def network_model(edges):
    """Within-team log-time margins on a ridge-regularized driver network.

    Components are never ranked against each other. Date-held-out predictive
    errors are measured before refitting. Cluster sandwich intervals condition
    on this network and its modelling assumptions; they are not causal intervals.
    """
    edges = sorted(edges, key=lambda e: (e['date'], e['race'], e['a'], e['b']))
    ids = sorted({e[k] for e in edges for k in ('a', 'b')})
    if not ids:
        return {'available': False, 'reason': 'no_paired_times', 'drivers': {}, 'edges': []}
    index = {d: i for i, d in enumerate(ids)}
    X = np.zeros((len(edges), len(ids))); y = np.zeros(len(edges)); weights = np.ones(len(edges))
    parent = {d: d for d in ids}
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    counts = Counter()
    for i, e in enumerate(edges):
        X[i, index[e['a']]] = 1; X[i, index[e['b']]] = -1
        y[i] = e['delta']; weights[i] = e.get('weight', 1.)
        parent[find(e['a'])] = find(e['b'])
        counts[e['a']] += 1; counts[e['b']] += 1
    # Split by race date, never separate paired observations from one race.
    dates = sorted({e['date'] for e in edges})
    train_end = dates[max(0, int(len(dates)*.6)-1)]
    validation_end = dates[max(0, int(len(dates)*.8)-1)]
    train = np.array([e['date'] <= train_end for e in edges])
    validation = np.array([train_end < e['date'] <= validation_end for e in edges])
    test = np.array([e['date'] > validation_end for e in edges])
    def fit(mask, ridge):
        xx, yy, ww = X[mask], y[mask], weights[mask]
        return np.linalg.solve(xx.T@(xx*ww[:, None])+np.eye(len(ids))*ridge, xx.T@(yy*ww))
    def connected_test(training, candidates):
        roots = {d:d for d in ids}
        def root(d):
            while roots[d] != d:
                roots[d] = roots[roots[d]]; d = roots[d]
            return d
        seen = set()
        for e, admitted in zip(edges, training):
            if admitted:
                roots[root(e['a'])] = root(e['b']); seen.update((e['a'],e['b']))
        return np.array([bool(ok and e['a'] in seen and e['b'] in seen and root(e['a']) == root(e['b']))
                         for e, ok in zip(edges, candidates)])
    tested = []
    for ridge in RULES['network_ridge_candidates']:
        coef = fit(train, ridge)
        mask = connected_test(train, validation)
        tested.append((float(np.mean(abs(X[mask]@coef-y[mask]))) if mask.any() else float('inf'), ridge))
    ridge = min(tested)[1]
    final_train = train | validation
    coef_test = fit(final_train, ridge)
    evaluated = connected_test(final_train, test)
    test_losses = defaultdict(list)
    for i in np.flatnonzero(evaluated):
        test_losses[edges[i]['race']].append((abs(float(X[i]@coef_test-y[i])), abs(float(y[i]))))
    loss_rows = np.array([np.mean(rows, axis=0) for rows in test_losses.values()])
    mae = float(loss_rows[:, 0].mean()) if len(loss_rows) else None
    baseline = float(loss_rows[:, 1].mean()) if len(loss_rows) else None
    improvement_interval = None
    if len(loss_rows) >= 20:
        improvements = loss_rows[:, 1]-loss_rows[:, 0]
        rng = np.random.default_rng(93817)
        draws = improvements[rng.integers(0, len(improvements), (800, len(improvements)))].mean(axis=1)
        improvement_interval = [float(v) for v in np.quantile(draws, [.025, .975])]
    coef = fit(np.ones(len(edges), dtype=bool), ridge)
    bread = np.linalg.inv(X.T@(X*weights[:, None])+np.eye(len(ids))*ridge)
    residual = y-X@coef; clustered = defaultdict(lambda: np.zeros(len(ids)))
    for i, e in enumerate(edges):
        clustered[e['race']] += X[i]*weights[i]*residual[i]
    score = np.stack(list(clustered.values()))
    influence = score@bread
    variance = np.sum(influence*influence, axis=0)
    if len(score) > 1:
        variance *= len(score)/(len(score)-1)
    components = {root: i+1 for i, root in enumerate(sorted({find(d) for d in ids}))}
    outputs = {d: {'effect': round(float(coef[index[d]]), 5),
                   'interval': [round(float(coef[index[d]]+s*1.96*np.sqrt(variance[index[d]])), 5) for s in (-1, 1)],
                   'component': components[find(d)], 'pairs': counts[d],
                   'eligible': counts[d] >= RULES['network_min_pairs']} for d in ids}
    return {'available': True, 'drivers': outputs, 'ridge': ridge, 'components': len(components),
            'validation': {'train_until': train_end, 'validation_until': validation_end,
                           'test_races': len({e['race'] for e, ok in zip(edges, evaluated) if ok}),
                           'test_pairs': int(evaluated.sum()), 'test_mae': mae, 'baseline_mae': baseline,
                           'improvement_interval': improvement_interval,
                           'passes': improvement_interval is not None and improvement_interval[0] > 0},
            'edges': edges, 'interval_type': 'race-cluster-sandwich-conditional'}


def pca_profiles(rows):
    """Exploratory standardized race summaries; complete cases only, no imputation."""
    if len(rows) < 12:
        return {'available': False, 'n': len(rows), 'reason': 'insufficient_complete_profiles'}
    years = sorted({r['year'] for r in rows})
    if len(years) < 3:
        return {'available': False, 'n': len(rows), 'reason': 'insufficient_training_years'}
    train_years = years[:max(2, int(len(years)*.8))]
    matrix = np.array([r['values'] for r in rows])
    train_indices = [i for i,r in enumerate(rows) if r['year'] in train_years]
    training = matrix[train_indices]
    if len(training) < 10:
        return {'available': False, 'n': len(rows), 'reason': 'insufficient_training_profiles'}
    center, scale = training.mean(axis=0), training.std(axis=0)
    if np.any(scale == 0):
        return {'available': False, 'n': len(rows), 'reason': 'constant_feature'}
    _, s, vt = np.linalg.svd((training-center)/scale, full_matrices=False)
    coordinates = ((matrix-center)/scale)@vt[:2].T
    rng = np.random.default_rng(17319)
    blocks = {year:[i for i,r in enumerate(rows) if r['year'] == year] for year in train_years}
    alignments = []
    for _ in range(200):
        idx = [i for year in rng.choice(train_years, len(train_years), replace=True) for i in blocks[int(year)]]
        a = matrix[idx]; sd = a.std(axis=0)
        if len(a) < 4 or np.any(sd == 0):
            continue
        _, _, axes = np.linalg.svd((a-a.mean(axis=0))/sd, full_matrices=False)
        alignments.append(abs(float(axes[0]@vt[0])))
    return {'available': True, 'n': len(rows),
            'features': ['start_gain', 'teammate_pace', 'normalized_lap_rank'],
            'explained': [float(x) for x in (s*s/(s*s).sum())[:2]],
            'loadings': vt[:2].tolist(),
            'training': {'from':train_years[0], 'through':train_years[-1], 'profiles':len(training),
                         'mean':center.tolist(), 'scale':scale.tolist(),
                         'projection_years':years[len(train_years):]},
            'points': [{'driver': r['driver'], 'year': r['year'], 'x': float(p[0]), 'y': float(p[1])}
                       for r, p in zip(rows, coordinates)],
            'stability': {'resampling': 'whole-calendar-year-blocks', 'draws':len(alignments),
                          'pc1_alignment_interval': [float(x) for x in np.quantile(alignments,[.025,.975])] if alignments else None},
            'status': 'exploratory-descriptive-not-ranking'}
