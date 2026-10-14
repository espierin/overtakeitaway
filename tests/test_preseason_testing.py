from pathlib import Path
from bs4 import BeautifulSoup
from f1_analysis.phase2 import build


def test_driver_intro_is_generated_with_local_assets_and_within_budget(tmp_path):
    (tmp_path/'index.html').write_text('<html><body>Home</body></html>')
    (tmp_path/'races.html').write_text('<html><body><div class="catalogue-tools"></div></body></html>')
    report=build(tmp_path,end_year=2026,years=1)
    page=(tmp_path/'analysis-lab.html').read_text();soup=BeautifulSoup(page,'html.parser')
    assert len(soup.select('script[src="assets/preseason-testing.js"]'))==1
    assert soup.select_one('link[rel="stylesheet"][href="assets/preseason-testing.css"]')
    assert soup.select_one('link[rel="preload"][as="image"][href="assets/home/preseason-testing-v1.webp"]')
    assert (tmp_path/'assets/home/preseason-testing-v1.webp').stat().st_size<100_000
    assert (tmp_path/'assets/home/preseason-testing-v1.prompt.txt').exists()
    assert 'preseason-testing.js' not in (tmp_path/'races.html').read_text()
    assert 'preseason-testing.js' not in (tmp_path/'index.html').read_text()
    assert report['extra_bytes_upper_bound']<report['max_extra_bytes']
    build(tmp_path,end_year=2026,years=1)
    assert (tmp_path/'analysis-lab.html').read_text().count('src="assets/preseason-testing.js"')==1
