"""Recompute race-dashboard pit cycles without replacing unrelated page changes.

Original analysis bundles stay immutable. Each updated export includes a separate
recalculation record with the exact original bundle hash and current parameters.
The verified site snapshot retains these records alongside the original archives.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from f1_analysis.analysis import Context, pit_cycles
from f1_analysis.cli import load_config
from f1_analysis.data_storage import materialize_data, pack_data
from f1_analysis.io import read_json, write_json, write_csv, utcnow
from f1_analysis.publication import site_html, pack_documents, verify_site
from f1_analysis.strategy_detail import detail_cycles


def refresh(source, site):
    source, site = Path(source).resolve(), Path(site).resolve()
    config = load_config(source, None)
    limit = config['strategie_max_stopafstand_ronden']
    materialize_data(site)
    report = {'max_stop_distance_laps': limit, 'updated': [], 'unavailable': []}
    pattern = re.compile(r'(<script\b[^>]*id=["\']dashboard-data["\'][^>]*>)(.*?)(</script>)', re.S)
    for page in sorted((site / 'analyses').glob('*/*/runs/*/overzicht.html')):
        relative = page.parent.relative_to(site)
        model = source / relative / 'data/derived/analysis.json'
        if not model.exists():
            continue
        text = site_html(page, site)
        match = pattern.search(text)
        if not match:
            continue
        original = read_json(model)
        params = dict(original['config'], strategie_max_stopafstand_ronden=limit)
        cycles = detail_cycles(pit_cycles(Context(original['data'], params)), original['data']['laps'])
        payload = json.loads(match[2])
        untouched = copy.deepcopy(payload)
        old_count = len(payload.get('cycles', []))
        payload['cycles'] = cycles
        evidence = {'computed_at': utcnow(), 'method': 'f1_analysis.analysis.pit_cycles',
                    'source_model': model.relative_to(source).as_posix(),
                    'source_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
                    'configuration': params}
        detection = dict(payload.get('strategy_detection') or {})
        detection.update(max_stop_distance_laps=limit,
                         initial_gap_seconds=params['strategie_gap_grens_seconden'])
        payload['strategy_detection'] = detection
        # Verify every other datum remains byte-for-byte equivalent as JSON values.
        for key, value in untouched.items():
            if key not in ('cycles', 'strategy_detection'):
                assert payload[key] == value, (relative, key)
        encoded = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
        page.write_text(text[:match.start(2)] + encoded + text[match.end(2):])
        export = page.parent / 'exports/pitstopstrategie.csv'
        write_csv(export, cycles)
        record = page.parent / 'exports/pitstopstrategie-analyse.json'
        write_json(record, dict(evidence, cycles=cycles))
        manifest_path = page.parent / 'manifest.json'
        manifest = read_json(manifest_path)
        manifest['strategy_recalculation'] = evidence
        hashes = manifest.setdefault('file_hashes', {})
        for path in (page, export, record):
            hashes[path.relative_to(page.parent).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest['files'] = sorted(set(manifest.get('files', [])) | {record.relative_to(page.parent).as_posix()})
        write_json(manifest_path, manifest)
        report['updated'].append({'page': page.relative_to(site).as_posix(),
                                  'before': old_count, 'after': len(cycles),
                                  'successful': sum(c['status'] == 'Geslaagd' for c in cycles)})
    assert report['updated'], 'No source-backed race dashboards found'
    pack_data(site)
    pack_documents(site)
    report['verification'] = verify_site(site)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=Path('.'))
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = refresh(args.source, args.site)
    write_json(args.report, result)
    print(json.dumps(result['verification'], indent=2))
    print('Updated race dashboards:', len(result['updated']))
