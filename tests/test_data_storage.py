import gzip
import json

import pytest

from f1_analysis.data_storage import pack_data, materialize_data, verify_data


def test_compression_and_restore_preserve_every_byte_and_keep_operational_pointers(tmp_path):
    original={
        'data/input.json': b'{\n "driver": "P\xc3\xa9rez", "laps": [1, 2, 3], "unknown": null\n}\n',
        'exports/laps.csv': b'\xef\xbb\xbfdriver,comment\r\n11,"comma, quote ""and newline\r\ninside"\r\n',
    }
    for name, body in original.items():
        path=tmp_path/name;path.parent.mkdir(exist_ok=True);path.write_bytes(body)
    (tmp_path/'latest.json').write_text('{"source": "untouched"}')
    report=pack_data(tmp_path)
    records=verify_data(tmp_path)
    assert report['files']==2
    assert (tmp_path/'latest.json').read_text()=='{"source": "untouched"}'
    for name, body in original.items():
        assert not (tmp_path/name).exists()
        assert gzip.decompress((tmp_path/(name+'.gz')).read_bytes())==body
        assert records[name]['bytes']==len(body)
    materialize_data(tmp_path)
    for name, body in original.items():assert (tmp_path/name).read_bytes()==body
    assert not (tmp_path/'_data/index.json').exists()


def test_restore_respects_new_data_and_rejects_damaged_snapshot(tmp_path):
    path=tmp_path/'race.json';path.write_text('{"position":2}')
    pack_data(tmp_path)
    packed=tmp_path/'race.json.gz';good=packed.read_bytes()
    packed.write_bytes(good+b'corruption')
    with pytest.raises(ValueError,match='datahash'):materialize_data(tmp_path)
    assert not path.exists()
    packed.write_bytes(good)
    path.write_text('{"position":1}')
    materialize_data(tmp_path)
    assert json.loads(path.read_text())=={'position':1}
