from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from f1_analysis.homepage import build, render_home
from f1_analysis.branding import branding


def test_entry_page_separates_races_and_driver_profiles():
    soup=BeautifulSoup(render_home(), 'html.parser')
    assert soup.select_one('.races-tile')['href']=='races.html'
    assert soup.select_one('.drivers-tile')['href']=='analysis-lab.html#tab=profiles'
    assert soup.select_one('.goat-tile')['href']=='goat.html'
    assert soup.select_one('.all-seasons-button')['href']=='races.html'
    assert soup.select_one('.site-home-link')['href']=='index.html'
    assert soup.select_one('.site-wordmark')['src']=='assets/overtake-wordmark-v2.png'
    assert not soup.find(id='catalogue-data')
    for node in soup.select('[data-nl]'):
        assert node['data-nl'] and node['data-en']
    assert all(not img.get('alt') for img in soup.select('.home-tile img'))


def test_build_preserves_catalogue_and_delivers_small_local_assets(tmp_path):
    (tmp_path/'races.html').write_text('Existing full catalogue')
    (tmp_path/'analysis-lab.html').write_text('Existing driver workspace')
    build(tmp_path)
    assert (tmp_path/'races.html').read_text()=='Existing full catalogue'
    assert (tmp_path/'analysis-lab.html').read_text()=='Existing driver workspace'
    soup=BeautifulSoup((tmp_path/'index.html').read_text(),'html.parser')
    for node in soup.select('.home-tile img,link[rel=stylesheet],script[src]'):
        assert (tmp_path/urlsplit(node.get('src') or node['href']).path).is_file()
    assert sum(p.stat().st_size for p in (tmp_path/'assets/home').glob('*'))<500_000
    build(tmp_path)
    assert len(BeautifulSoup((tmp_path/'index.html').read_text(),'html.parser').select('.home-tile'))==3
    assert (tmp_path/'goat.html').is_file()


def test_disabled_drivers_do_not_link_to_nonexistent_page(tmp_path):
    build(tmp_path)
    soup=BeautifulSoup((tmp_path/'index.html').read_text(),'html.parser')
    assert soup.select_one('.drivers-tile')['aria-disabled']=='true'
    assert not soup.select_one('.drivers-tile').has_attr('href')


def test_home_logo_retains_correct_root_for_nested_race_page():
    soup=BeautifulSoup(branding('../../../../../assets/f1-banner-v3.png'),'html.parser')
    assert soup.select_one('.site-home-link')['href']=='../../../../../index.html'
