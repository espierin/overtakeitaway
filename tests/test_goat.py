from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from f1_analysis.homepage import build
from f1_analysis.goat import render_goat


def test_goat_design_page_is_bilingual_and_does_not_claim_a_ranking():
    soup=BeautifulSoup(render_goat(),'html.parser')
    assert soup.select_one('#goat-plan')
    assert soup.select_one('[data-open-winter]')['aria-controls']=='winter-dialog'
    assert 'nog geen ranglijst' in soup.select_one('.goat-design-note').get_text()
    assert len(soup.select('.goat-questions article'))==3
    assert soup.select_one('.site-home-link')['href']=='index.html'
    for node in soup.select('[data-nl]'):
        assert node['data-nl'] and node['data-en']
    assert soup.select_one('script[src="assets/goat.js"]')
    assert not soup.select_one('script[src="assets/preseason-testing.js"]')


def test_entry_builder_delivers_goat_and_its_shared_local_assets(tmp_path):
    (tmp_path/'analysis-lab.html').write_text('Existing driver analyses')
    build(tmp_path)
    soup=BeautifulSoup((tmp_path/'goat.html').read_text(),'html.parser')
    for node in soup.select('img,link[rel=stylesheet],script[src]'):
        url=node.get('src') or node['href']
        # Branding is provided by the full publication step, just as on index.
        if url in ('assets/overtake-wordmark-v2.png',):continue
        assert (tmp_path/unquote(urlsplit(url).path)).is_file(),url
    assert (tmp_path/'assets/home/goat-winter-break-v1.webp').stat().st_size<100_000
    assert (tmp_path/'assets/home/goat-winter-break-v1.prompt.txt').is_file()
    assert (tmp_path/'analysis-lab.html').read_text()=='Existing driver analyses'
