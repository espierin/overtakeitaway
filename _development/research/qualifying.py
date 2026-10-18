"""The actual qualifying P1 time, with its recorded session/format intact."""
from collections import defaultdict
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import zipfile
import math
from statistics import median

DEFINITION = 'qualifying-year-violin-bridged-pole-v2'
METHOD = 'Annual qualifying distributions: one recorded result per main-race qualifying. Pole gap uses qualifying P1 and the same recorded Q3/Q2/Q1 or historic aggregate time field; missing Q3 times may receive separately labelled estimates from median Q1-Q2 and Q2-Q3 changes with at least five paired drivers per step; other missing or incompatible times remain missing. Estimated points enter the pooled violins, quartiles, medians and trend/band while retaining distinct markers and provenance. The bootstrap band conditions on point estimates and does not propagate translation error; held-out validation reports that error separately. Leave-one-driver-out Q3 reconstructions are retained with errors and an uncorrected baseline. Positions use a nonlinear integer axis, time gaps log1p(seconds) on a fixed 0–4 second display; larger values are clipped visually but retained in observations and summaries. Both year plots share one scroll container. Position-only stage shading uses continuous season-level zones with the modal reliable recorded knockout cutoffs across all races of that season, independent of driver coverage. Individual sessions may differ; seasons without reliable knockout boundaries remain unshaded. White best-fit display curves use shape-preserving cubic interpolation through annual medians; pointwise 95% race bootstrap bands use 400 within-year resamples, Sparse years retain dashed lines, a lone year has a median stub, and empty-year connections are dotted without a confidence band; one observed value has no bootstrap band.'


def positive_integer(value):
    try:
        n = int(value)
        return n if n > 0 else None
    except (ValueError, TypeError):
        return None


def pole_references(qualifying_rows, race_ids=None):
    grouped = defaultdict(list)
    for row in qualifying_rows:
        rid = row['year']+'-'+row['round']
        if race_ids is None or rid in race_ids:
            grouped[rid].append(row)
    result = {}
    for rid, rows in grouped.items():
        first = [r for r in rows if positive_integer(r.get('positionNumber')) == 1]
        if len(first) != 1:
            continue
        # A faster earlier phase is not the pole time from the deciding phase.
        key = next((key for key in ['q3Millis','q2Millis','q1Millis','timeMillis']
                    if any(positive_integer(r.get(key)) for r in rows)), None)
        value = positive_integer(first[0].get(key)) if key else None
        if value:
            result[rid] = [key, value, first[0]['driverId']]
    return result



def stage_references(qualifying_rows, race_rows, race_ids=None):
    """Rank zones only for recorded knockout formats with verified field cutoffs.

    FIA 2015 sporting rules art. 33.1: (eligible cars - 10)/2 eliminated
    in each phase. The two 2016 elimination sessions instead kept 15 then 8.
    Odd/incomplete fields and cancelled final phases remain unshaded.
    """
    formats = {r['year']+'-'+r['round']: r.get('qualifyingFormat') for r in race_rows}
    grouped = defaultdict(list)
    for row in qualifying_rows:
        rid = row['year']+'-'+row['round']
        if race_ids is None or rid in race_ids:
            grouped[rid].append(row)
    result = {}
    for rid, rows in grouped.items():
        fmt = formats.get(rid)
        if fmt not in {'KNOCKOUT', 'SPRINT_RACE', 'ELIMINATION'}:
            continue
        n = len({r['driverId'] for r in rows})
        if n not in {18,20,22,24,26}:
            continue
        q3, q2 = (8,15) if fmt == 'ELIMINATION' else (10,(n+10)//2)
        observed = {key: [positive_integer(r.get('positionNumber')) for r in rows
                          if positive_integer(r.get(key))] for key in ['q2Millis','q3Millis']}
        # A driver who reached Q3 but set no time must still occupy a Q3 slot.
        # Reject uncertain boundaries rather than infer cutoffs from valid times only.
        if not all(observed.values()) or any(p and p > limit for key,limit in [('q2Millis',q2),('q3Millis',q3)] for p in observed[key]):
            continue
        result[rid] = [q3,q2,n]
    return result


BRIDGE_DEFINITION = 'qualifying-session-median-bridge-loo-v1'
MIN_BRIDGES = 5


def percentile(values, p):
    a = sorted(values)
    if not a:
        return None
    index = (len(a)-1)*p
    lo = math.floor(index)
    hi = math.ceil(index)
    return a[lo]+(a[hi]-a[lo])*(index-lo)


def bridge_step(rows, before, after, exclude=None):
    pairs = [(r['driverId'], positive_integer(r.get(before)), positive_integer(r.get(after)))
             for r in rows if r['driverId'] != exclude and positive_integer(r.get('positionNumber'))]
    changes = [b-a for _,a,b in pairs if a and b]
    if len(changes) < MIN_BRIDGES:
        return None
    return [len(changes), median(changes), percentile(changes,.25), percentile(changes,.75)]


def qualifying_bridges(qualifying_rows, poles, race_ids=None):
    """Contemporaneous session adjustment, with driver-held-out Q3 reconstruction.

    A candidate's hidden Q3 is never in either training step. For Q1 tests their
    Q2 is hidden as well. No rescaled/estimated time overwrites an observation.
    """
    grouped = defaultdict(list)
    for row in qualifying_rows:
        rid = row['year']+'-'+row['round']
        if race_ids is None or rid in race_ids:
            grouped[rid].append(row)
    models, checks = {}, []
    for rid, rows in grouped.items():
        reference = poles.get(rid)
        if not reference or reference[0] != 'q3Millis':
            continue
        if len({r['driverId'] for r in rows}) != len(rows):
            continue
        first = bridge_step(rows,'q1Millis','q2Millis')
        second = bridge_step(rows,'q2Millis','q3Millis')
        if first or second:
            models[rid] = [first,second]
        for candidate in rows:
            actual = positive_integer(candidate.get('q3Millis'))
            if not actual or actual < reference[1] or not positive_integer(candidate.get('positionNumber')):
                continue
            driver = candidate['driverId']
            # Both steps exclude the same held-out driver (including their Q2).
            held_first = bridge_step(rows,'q1Millis','q2Millis',exclude=driver)
            held_second = bridge_step(rows,'q2Millis','q3Millis',exclude=driver)
            for origin,key in [('Q2','q2Millis'),('Q1','q1Millis')]:
                own = positive_integer(candidate.get(key))
                steps = [held_second] if origin == 'Q2' else [held_first,held_second]
                if not own or not all(steps):
                    continue
                predicted = own+sum(step[1] for step in steps)
                checks.append({'race':rid,'year':int(candidate['year']),'driver':driver,
                               'origin':origin,'actual_gap_ms':actual-reference[1],
                               'estimated_gap_ms':predicted-reference[1],
                               'error_ms':predicted-actual,'uncorrected_error_ms':own-actual,
                               'bridge_counts':[step[0] for step in steps]})

    def metrics(records):
        if not records:
            return {'n':0,'races':0}
        errors = [r['error_ms'] for r in records]
        absolute = [abs(v) for v in errors]
        return {'n':len(records),'races':len({r['race'] for r in records}),
                'mae_ms':round(sum(absolute)/len(absolute),3),
                'median_abs_ms':round(median(absolute),3),
                'bias_ms':round(sum(errors)/len(errors),3),
                'rmse_ms':round(math.sqrt(sum(v*v for v in errors)/len(errors)),3),
                'p90_abs_ms':round(percentile(absolute,.90),3),
                'uncorrected_mae_ms':round(sum(abs(r['uncorrected_error_ms']) for r in records)/len(records),3)}
    validation = {'definition':BRIDGE_DEFINITION,'minimum_bridges':MIN_BRIDGES,
                  'protocol':'Leave one driver out within the same qualifying; hide Q3 and, for Q1-origin tests, hide Q2 too; exclude the held-out driver from every paired-session median. Q3 finishers only; not independent race-level test cases and not validation on actual Q1/Q2 eliminations.',
                  'summary':{origin:metrics([r for r in checks if r['origin']==origin]) for origin in ['Q2','Q1']},
                  'years':{str(year):{origin:metrics([r for r in checks if r['year']==year and r['origin']==origin]) for origin in ['Q2','Q1']}
                           for year in sorted({r['year'] for r in checks})}}
    return models,validation,checks


def refresh(root):
    """Refresh only unchanged source metadata, without recalculating race models."""
    data = root/'_development/data'
    with zipfile.ZipFile(next((root/'analyses/sources/historical/f1db').glob('*.zip'))) as archive:
        rows = list(csv.DictReader(io.TextIOWrapper(archive.open('f1db-races-qualifying-results.csv'))))
        races = list(csv.DictReader(io.TextIOWrapper(archive.open('f1db-races.csv'))))
    metadata = json.loads((data/'facts.js').read_text().split('=',1)[1].rstrip(';\n'))
    profiles = json.loads((data/'profiles.js').read_text().split('=',1)[1].rstrip(';\n'))
    metadata['qualifying_poles'] = pole_references(rows, {r['id'] for r in profiles['races']})
    metadata['qualifying_stages'] = stage_references(rows, races, {r['id'] for r in profiles['races']})
    models,validation,checks = qualifying_bridges(rows, metadata['qualifying_poles'], {r['id'] for r in profiles['races']})
    metadata['qualifying_bridges'] = models
    metadata['qualifying_bridge_validation'] = validation
    metadata['qualifying_definition'] = DEFINITION
    audit = root/'storage/qualifying-bridges-20261018'
    audit.mkdir(parents=True,exist_ok=True)
    (audit/'validation.json').write_text(json.dumps({'validation':validation,'predictions':checks},ensure_ascii=False,indent=2)+'\n')
    registry = json.loads((root/'_development/build-report.json').read_text())

    def write(name, value, variable):
        body = json.dumps(value, ensure_ascii=False, separators=(',',':'), allow_nan=False).replace('</',r'<\/')
        packed = body.encode()
        (data/(name+'.js')).write_text('window.'+variable+'='+body+';\n')
        compressed = gzip.compress(packed,mtime=0)
        (data/(name+'.json.gz')).write_bytes(compressed)
        entry = next((f for f in registry['files'] if f['name']==name), None)
        if entry is not None:
            entry.update(bytes=len(packed), compressed_bytes=len(compressed), sha256=hashlib.sha256(packed).hexdigest())

    write('facts',metadata,'phase2Facts')
    collection = json.loads((data/'collection.js').read_text().split('=',1)[1].rstrip(';\n'))
    collection['methods'] = [m for m in collection['methods'] if m[0] != 'Kwalificatie / qualifying']
    collection['methods'].append(['Kwalificatie / qualifying',METHOD])
    write('collection',collection,'phase2Collection')
    registry['bytes'] = sum(f['bytes'] for f in registry['files'])
    assert registry['bytes'] <= 64_000_000
    write('registry',registry,'phase2Registry')
    (root/'_development/build-report.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    return {'pole_references':len(metadata['qualifying_poles']), 'bytes':registry['bytes'], 'bridge_races':len(models), 'validation':validation['summary']}


if __name__ == '__main__':
    print(json.dumps(refresh(Path(__file__).resolve().parents[2])))
