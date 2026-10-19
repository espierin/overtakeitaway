from f1_analysis.production import links, without_development_intro, redirect


def test_production_navigation_preserves_relative_paths_queries_and_selection():
    original='<a href="../../coureurs_2.html?x=1#driver=max-verstappen">Driver</a><a href="goat_2.html#drivers=max-verstappen">GOAT</a><a href="_development/uitleg-start-en-raceonderzoek.html#start">Help</a><script type="application/json">{"href":"coureurs_2.html","value":0.125}</script>'
    page=links(original)
    assert '../../analysis-lab.html?x=1#driver=max-verstappen' in page
    assert 'href="goat.html#drivers=max-verstappen"' in page
    assert 'href="uitleg-start-en-raceonderzoek.html#start"' in page
    assert '{"href":"coureurs_2.html","value":0.125}' in page
    assert links(page)==page


def test_only_the_development_introductions_are_removed():
    original='<script src="_development/assets/preseason-testing.js?v=123"></script><script src="assets/goat.js"></script><script src="_development/assets/goat-research.js"></script><button data-open-winter>Winter break</button><button data-driver-info="start">Info</button>'
    page=without_development_intro(original)
    assert 'preseason-testing.js' not in page and 'src="assets/goat.js"' not in page
    assert 'data-open-winter' not in page
    assert 'goat-research.js' in page and 'data-driver-info="start"' in page


def test_old_bookmarks_keep_their_query_and_hash():
    page=redirect('goat.html')
    assert "location.replace('goat.html'+location.search+location.hash)" in page
    assert 'rel="canonical" href="goat.html"' in page
