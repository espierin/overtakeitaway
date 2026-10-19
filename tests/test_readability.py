import json
import re
import shutil
import subprocess
from pathlib import Path

from f1_analysis.readability import asset_text, decorate, OLD_CONVERT
from f1_analysis.help import render

NODE=shutil.which('node') or '/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


def test_reviewed_copy_preserves_meaning_units_and_settles_in_both_languages():
    script=asset_text()+r'''
const assert=require('node:assert/strict'),api=window.readableCopy;
assert.equal(api.text('Metronoom · vast veldpercentiel'),'Metronoom · veldscore (0–100)');
assert.equal(api.text('PCA-parameters kiezen · 4'),'Kenmerken voor de profielkaart · 4');
assert.equal(api.text('Mediane tijdwinst per race','en'),'Typical time gained per race');
assert.equal(api.text('Waarde: -0,852 s · 200 cycli'),'Waarde: -0,852 s · 200 cycli');
assert.equal(api.text('Gemiddelde rondetijd'),'Gemiddelde rondetijd'); // Never turn a mean into a median.
for(const lang of ['nl','en'])for(const rule of catalog)for(const source of rule){const result=api.text(source,lang);assert.equal(api.text(result,lang),result);}
'''
    # The catalog is intentionally closed in the module: test its complete source list separately.
    rules=json.loads((Path(__file__).resolve().parents[1]/'src/f1_analysis/assets/plain-language.json').read_text())['rules']
    script=script.replace('for(const rule of catalog)', 'for(const rule of '+json.dumps(rules,ensure_ascii=False)+')')
    subprocess.run([NODE,'-'],input='global.window={};'+script,text=True,check=True,timeout=15)


def test_copy_decoration_is_repeatable_and_does_not_touch_recorded_json():
    payload=json.dumps({'label':'mediaan','recorded_source':OLD_CONVERT,'places':[1,2,3]})
    original='<html><head></head><body><script id="dashboard-data" type="application/json">'+payload+'</script><script>window.siteLanguage={};'+OLD_CONVERT+'</script></body></html>'
    after=decorate(original,'../../assets/')
    assert re.search(r'id="dashboard-data"[^>]*>(.*?)</script>',after,re.S)[1]==payload
    assert 'window.readableCopy.lookup' in after
    assert after.count('data-readable-copy')==1
    assert '../../uitleg.html' in after
    assert decorate(after,'../../assets/')==after


def test_guide_explains_median_uncertainty_and_limits_of_driver_comparison():
    page=render()
    assert '2,5 seconden' in page and '6,5 seconden' in page
    assert 'geen percentages rijvaardigheid' in page
    assert 'sign(t) × ln(1 + |t|)' in page
    assert 'een empirisch percentiel' in page
    assert '#goat' in page and 'href="uitleg-start-en-raceonderzoek.html"' in page
