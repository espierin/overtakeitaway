from bs4 import BeautifulSoup
from f1_analysis.data_collection import count_parameters, render, build
from f1_analysis.homepage import render_home


def test_parameter_counts_preserve_zero_false_and_separate_unknowns():
    rows = [{'x': 0, 'ok': False}, {'x': None}, {'x': ''}, {'x': 'UNKNOWN'}, {'x': 3}]
    result = count_parameters({'rows': rows})
    assert result['rows[].x'] == {'slots': 5, 'values': 2, 'numeric': 2, 'missing': 2, 'unknown': 1}
    assert result['rows[].ok']['values'] == 1
    assert result['rows[].ok']['boolean'] == 1
    ranks = count_parameters({'drivers': [{'races': [{'lap_rankings': [[1, 2, 20, 0, 32]]}]}]})
    assert ranks['drivers[].races[].lap_rankings[].rank']['values'] == 1
    sources=count_parameters({'sources':{'src-001':{'url':'a'},'src-002':{'url':'b'}}})
    assert sources['sources.*.url']['values']==2


def test_collection_page_and_home_link_are_bilingual(tmp_path):
    report = build(tmp_path)
    assert report['parameters'] == 0 and report['failures'] == []
    soup = BeautifulSoup((tmp_path/'data-collection.html').read_text(), 'html.parser')
    assert soup.select_one('#collection-data')
    assert soup.select_one('#parameter-search')
    for node in soup.select('[data-nl]'):
        assert node['data-en']
    home = BeautifulSoup(render_home(), 'html.parser')
    assert home.select_one('footer a[href="data-collection.html"]')['data-en'] == 'Data collection'
