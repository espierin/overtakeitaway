from pathlib import Path
import json
import pytest
from f1_analysis.visitors import build,settings


def test_stats_page_uses_private_provider_without_access_tokens(tmp_path):
    (tmp_path/'config').mkdir()
    (tmp_path/'config/visitors.json').write_text(json.dumps({'site':'https://overtakeitaway.goatcounter.com'}))
    page=build(tmp_path).read_text()
    assert 'Stats4me' in page and '<iframe' in page
    assert 'https://overtakeitaway.goatcounter.com' in page
    assert 'access-token' not in page and 'api-token' not in page
    assert 'alleen ingelogde gebruikers' in page
    assert (tmp_path/'assets/visitors.js').is_file()


def test_settings_reject_any_token_or_unrelated_endpoint(tmp_path):
    (tmp_path/'config').mkdir()
    for site in ['https://example.net/count','https://foo.goatcounter.com?access-token=secret','http://foo.goatcounter.com','https://foo.goatcounter.com/count']:
        (tmp_path/'config/visitors.json').write_text(json.dumps({'site':site}))
        with pytest.raises(ValueError):settings(tmp_path)
