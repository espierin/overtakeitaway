from base64 import b64decode
from pathlib import Path
from bs4 import BeautifulSoup
from f1_analysis.style_guide import build, render_style_guide


def test_standalone_guide_keeps_original_logo_and_has_complete_navigation():
    soup=BeautifulSoup(render_style_guide(),'html.parser')
    assert not soup.select('script[src],link[rel=stylesheet],img:not([src^="data:"])')
    source=Path(__file__).parents[1]/'src/f1_analysis/assets/overtake-wordmark-v2.png'
    assert b64decode(soup.select_one('.guide-wordmark')['src'].split(',',1)[1])==source.read_bytes()
    assert len(soup.select('main>section'))==8
    for link in soup.select('.contents a'):
        assert soup.select_one(link['href'])
    for node in soup.select('[data-nl]'):
        assert node['data-en'] and node['data-nl']
    frame=soup.select_one('.chart-frame')
    assert frame.select_one('.chart-axis').parent==frame
    assert not frame.select_one('.chart-scroll').select_one('.chart-axis')
    assert soup.select_one('dialog#guide-dialog')


def test_builder_adds_only_the_standalone_document(tmp_path):
    (tmp_path/'analysis-lab.html').write_text('Existing driver data')
    (tmp_path/'races.html').write_text('Existing races')
    target=build(tmp_path)
    assert target.name=='stijlgids.html'
    assert (tmp_path/'analysis-lab.html').read_text()=='Existing driver data'
    assert (tmp_path/'races.html').read_text()=='Existing races'
    assert BeautifulSoup(target.read_text(),'html.parser').select_one('a[href="analysis-lab.html#tab=profiles"]')


def test_unavailable_driver_destination_is_disabled():
    soup=BeautifulSoup(render_style_guide(False),'html.parser')
    assert not soup.select_one('a[href^="analysis-lab.html"]')
    assert soup.select_one('.tools button[disabled]')
