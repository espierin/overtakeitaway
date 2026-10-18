"""Verify every retained FIA PDF against its immutable archive SHA-256."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def verify():
    packed = (ROOT/'assets/driver-incidents.json.gz').read_bytes()
    archive = json.loads(gzip.decompress(packed))
    checked, missing, mismatches = set(), [], []
    for decision in archive['decisions']:
        source = archive['sources'][decision['source']]
        name = source['local_file']
        if name in checked:
            continue
        checked.add(name)
        path = ROOT/name
        if not path.exists():
            missing.append(name)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            mismatches.append(name)
    result = {'checked_pdf_sources':len(checked), 'missing':missing,
              'hash_mismatches':mismatches,
              'registry_unchanged_sha256':hashlib.sha256(packed).hexdigest()}
    (ROOT/'_development/incident-source-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    if missing or mismatches:
        raise ValueError('Missing or changed incident evidence; inspect incident-source-validation.json')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(),indent=2))
