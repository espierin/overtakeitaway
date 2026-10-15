from bs4 import BeautifulSoup
from f1_analysis.site_navigation import with_navigation
from f1_analysis.branding import with_wordmark_text
from f1_analysis.homepage import render_home


def test_original_wordmark_pixels_and_home_link_are_retained_with_real_subtitle():
    original = '<html><head><title>Overtake It Away</title></head><body><header class="site-brand"><a class="site-home-link" href="old.html"><img class="site-wordmark" src="assets/overtake-wordmark-v2.png" alt=""></a><p class="site-tagline">A reality check on heroic stories.</p><div class="header-actions"></div></header><script id="dashboard-data" type="application/json">{"laps":[1,2,3]}</script></body></html>'
    page = with_navigation(original, 'assets/')
    assert with_navigation(page, 'assets/') == page
    soup = BeautifulSoup(page, 'html.parser')
    assert soup.select_one('.site-wordmark-window img')['src'] == 'assets/overtake-wordmark-v2.png'
    assert soup.select_one('.site-home-link')['href'] == 'index.html'
    assert not soup.select('a a')
    assert soup.select_one('.site-home-link > .site-tagline').text == 'Geen fabels maar feiten'
    assert len(soup.select('.site-tagline')) == 1
    assert soup.title.text == 'Overtake It Away: Geen fabels maar feiten'
    assert soup.select_one('#dashboard-data').string == '{"laps":[1,2,3]}'
    assert soup.select_one('[data-site-branding-script]')['src'] == 'assets/site-branding.js'


def test_home_title_and_footer_use_the_same_dutch_slogan():
    page = render_home()
    assert with_wordmark_text(page) == page
    soup = BeautifulSoup(page, 'html.parser')
    assert soup.title.text == 'Overtake It Away: Geen fabels maar feiten'
    assert {n.text for n in soup.select('[data-brand-tagline]')} == {'Geen fabels maar feiten'}


def test_shared_header_roles_preserve_section_content():
    from f1_analysis.goat import render_goat
    for text, role in [(render_home(), 'home'), (render_goat(), 'greatest')]:
        soup = BeautifulSoup(text, 'html.parser')
        assert soup.select_one('.race-hero')['data-header-section'] == role
        assert len(soup.select('[data-site-header-style]')) == 1
        assert soup.select_one('[data-site-header-style]')['href'] == 'assets/site-header.css'
        assert with_navigation(text, 'assets/') == text
    driver = '<html><head></head><body><div class="race-hero"><header class="site-brand"><img class="site-wordmark" src="assets/overtake-wordmark-v2.png"><div class="header-actions"></div></header><h1>Coureurs</h1></div><script id="phase2-data" type="application/json">{"drivers":[]}</script></body></html>'
    page = with_navigation(driver, 'assets/')
    soup = BeautifulSoup(page, 'html.parser')
    assert soup.select_one('.race-hero')['data-header-section'] == 'drivers'
    assert soup.select_one('#phase2-data').string == '{"drivers":[]}'
    assert with_navigation(page, 'assets/') == page
