"""Lossless public data storage; working copies and original archives stay readable."""
import gzip
import hashlib
import json
from pathlib import Path


def checksum(body):
    return hashlib.sha256(body).hexdigest()


def pack_data(root):
    root = Path(root)
    records = verify_data(root)
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix not in ('.json', '.csv'):
            continue
        relative = path.relative_to(root)
        # Operational pointers must also work before the browser/Python loader starts.
        if relative.parts[0] in ('_storage', '_media', '_data') or path.name == 'latest.json':
            continue
        body = path.read_bytes()
        compressed = gzip.compress(body, compresslevel=9, mtime=0)
        if gzip.decompress(compressed) != body:
            raise ValueError(f'Verliesloze datacontrole mislukt: {relative}')
        packed = path.with_name(path.name + '.gz')
        packed.write_bytes(compressed)
        records[relative.as_posix()] = {'sha256': checksum(body), 'bytes': len(body),
                                      'stored_sha256': checksum(compressed), 'stored_bytes': len(compressed)}
        path.unlink()
    directory = root / '_data'
    directory.mkdir(exist_ok=True)
    body = json.dumps(records, ensure_ascii=False, separators=(',', ':')).encode()
    (directory / 'index.json').write_bytes(body)
    (directory / 'index.json.gz').write_bytes(gzip.compress(body, compresslevel=9, mtime=0))
    (directory / 'reader.js').write_text(Path(__file__).with_name('data_reader.js').read_text())
    (directory / 'view.html').write_text(Path(__file__).with_name('data_view.html').read_text())
    return {'files': len(records), 'original_bytes': sum(r['bytes'] for r in records.values()),
            'stored_bytes': sum(r['stored_bytes'] for r in records.values())}


def verify_data(root):
    root = Path(root).resolve()
    index = root / '_data/index.json'
    if not index.exists():
        return {}
    records = json.loads(index.read_bytes())
    if gzip.decompress((root / '_data/index.json.gz').read_bytes()) != index.read_bytes():
        raise ValueError('Dataregister wijkt af')
    for name, record in records.items():
        original = (root / name).resolve()
        if not original.is_relative_to(root):
            raise ValueError(f'Datapad buiten publicatie: {name}')
        packed = original.with_name(original.name + '.gz')
        stored = packed.read_bytes()
        if checksum(stored) != record['stored_sha256']:
            raise ValueError(f'Gecomprimeerde datahash wijkt af: {name}')
        body = gzip.decompress(stored)
        if len(body) != record['bytes'] or checksum(body) != record['sha256']:
            raise ValueError(f'Datahash wijkt af: {name}')
    return records


def materialize_data(root):
    """Restore exact data bytes for the normal updater without inflating the Pages artifact."""
    root = Path(root)
    records = verify_data(root)
    for name, record in records.items():
        original = root / name
        packed = original.with_name(original.name + '.gz')
        # A restored season archive/new update takes precedence over its old snapshot.
        if not original.exists():
            original.parent.mkdir(parents=True, exist_ok=True)
            original.write_bytes(gzip.decompress(packed.read_bytes()))
        packed.unlink()
    if records:
        (root / '_data/index.json').unlink()
        (root / '_data/index.json.gz').unlink()
    return len(records)
