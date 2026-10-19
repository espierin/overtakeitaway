import gzip
import hashlib
import json

import pytest

from f1_analysis import goat_release


def test_promotion_retains_exact_old_page_and_survives_rebuild(tmp_path):
    original = '<html><head><title>Old</title></head><body>Winter break</body></html>'
    source = '<html><head><meta name="robots" content="noindex"></head><body><a href="goat_2.html">GOAT</a><a href="coureurs_2.html">Drivers</a></body></html>'
    (tmp_path/'goat.html').write_text(original)
    (tmp_path/'goat_2.html').write_text(source)
    goat_release.promote(tmp_path)
    backup = (tmp_path/goat_release.BACKUP).read_bytes()
    assert backup == original.encode()
    assert gzip.decompress((tmp_path/goat_release.BASELINE).read_bytes()) == backup
    record = json.loads((tmp_path/goat_release.RECORD).read_text())
    assert record['original_sha256'] == hashlib.sha256(backup).hexdigest()
    promoted = (tmp_path/'goat.html').read_text()
    assert 'noindex' not in promoted
    assert 'href="goat.html"' in promoted and 'href="analysis-lab.html"' in promoted
    assert goat_release.is_promoted(tmp_path)
    # The regular publisher must retain the promoted presentation on later builds.
    from f1_analysis.goat import build
    assert build(tmp_path) == tmp_path/'goat.html'
    assert (tmp_path/goat_release.BACKUP).read_bytes() == backup
    (tmp_path/goat_release.BASELINE).write_bytes(gzip.compress(b'tampered'))
    with pytest.raises(ValueError, match='recorded hash'):
        goat_release.promote(tmp_path)
