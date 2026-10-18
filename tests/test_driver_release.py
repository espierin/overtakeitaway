import gzip
import hashlib
import json

import pytest

from f1_analysis.driver_release import BASELINE, MARKER, is_promoted, promote, render, source_html
from f1_analysis.phase2 import build
from f1_analysis.publication import build_site, pack_documents, site_html


def setup_module_pages(root):
    original='<html><head></head><body><script id="phase2-data" type="application/json">{"drivers":[{"id":"original","races":[]}]}</script></body></html>'
    (root/'analysis-lab.html').write_text(original)
    (root/'index.html').write_text('<html><body><a href="analysis-lab.html">Drivers</a></body></html>')
    dev=root/'_development';dev.mkdir()
    (dev/'clone-manifest.json').write_text(json.dumps({'pages':{'coureurs_2.html':{'source_sha256':hashlib.sha256(original.encode()).hexdigest()}}}))
    (root/'coureurs_2.html').write_text('<html><head><meta name="robots" content="noindex,nofollow"></head><body><a href="coureurs_2.html#driver=max-verstappen">Drivers</a><script id="phase2-data" type="application/json">{}</script></body></html>')
    return original


def test_promoted_page_preserves_original_evidence_and_legacy_links(tmp_path):
    original=setup_module_pages(tmp_path)
    assert not is_promoted(tmp_path)
    report=promote(tmp_path)
    assert report['page']=='analysis-lab.html' and is_promoted(tmp_path)
    text=(tmp_path/'analysis-lab.html').read_text()
    assert MARKER in text and 'noindex' not in text
    assert 'href="analysis-lab.html#driver=max-verstappen"' in text
    assert source_html(tmp_path)==original
    assert gzip.decompress((tmp_path/BASELINE).read_bytes()).decode()==original
    # Future automatic calls keep the reviewed UI instead of the legacy renderer.
    assert build(tmp_path)['presentation']=='phase2'
    assert (tmp_path/'analysis-lab.html').read_text()==text
    (tmp_path/BASELINE).write_bytes(gzip.compress(b'corrupt evidence'))
    with pytest.raises(ValueError,match='evidence'):source_html(tmp_path)


def test_promoted_ui_and_evidence_survive_two_compact_builds(tmp_path):
    root=tmp_path/'root';root.mkdir();original=setup_module_pages(root);promote(root)
    assets=root/'assets';assets.mkdir();(assets/'phase2.js').write_text('// legacy renderer trigger')
    first=tmp_path/'first';second=tmp_path/'second'
    build_site(root,first,max_bytes=900000000)
    assert is_promoted(first) and source_html(first)==original
    build_site(first,second,max_bytes=900000000)
    assert is_promoted(second) and source_html(second)==original
    assert MARKER in site_html(second/'analysis-lab.html',second)
    assert 'href="analysis-lab.html#driver=max-verstappen"' in site_html(second/'analysis-lab.html',second)


def test_promotion_points_navigation_to_regular_modules(tmp_path):
    setup_module_pages(tmp_path)
    page=tmp_path/'coureurs_2.html'
    page.write_text(page.read_text().replace('</body>','<a href="races_2.html">Races</a><a href="goat_2.html">GOAT</a></body>'))
    text=render(tmp_path)
    assert 'href="races.html"' in text and 'href="goat.html"' in text


def test_promoted_scripts_change_cache_version_when_reviewed_asset_changes(tmp_path):
    setup_module_pages(tmp_path)
    asset=tmp_path/'_development/assets/phase2.js';asset.parent.mkdir()
    asset.write_text('window.revision=1;')
    page=tmp_path/'coureurs_2.html'
    page.write_text(page.read_text().replace('</body>','<script src="_development/assets/phase2.js"></script></body>'))
    first=render(tmp_path)
    assert '_development/assets/phase2.js?v=' in first
    asset.write_text('window.revision=2;')
    assert render(tmp_path)!=first
