from bs4 import BeautifulSoup
from f1_analysis.site_navigation import with_navigation,ensure_assets
from f1_analysis.branding import branding


def test_banner_navigation_preserves_language_and_existing_seasons():
    text=branding('../../../../../assets/f1-banner-v3.png',seasons_url='../../../../../index.html')
    s=BeautifulSoup(text,'html.parser');buttons=s.select_one('.header-actions')
    assert buttons.select_one('.all-seasons-button')['href']=='../../../../../races.html'
    assert buttons.select_one('[data-site-link=races]')['href']=='../../../../../races.html'
    assert buttons.select_one('[data-site-link=drivers]')['href']=='../../../../../analysis-lab.html#tab=profiles'
    assert buttons.select_one('[data-site-about]')['aria-haspopup']=='dialog'
    assert buttons.select_one('[data-language-toggle]')['id']=='language-toggle'
    assert s.select_one('[data-site-navigation-script]')['src']=='../../../../../assets/site-navigation.js'
    assert with_navigation(text,'../../../../../assets/')==text


def test_legacy_header_upgrade_is_idempotent_and_leaves_race_data_intact():
    payload='{"race":"Example","samples":[1,2,3]}'
    old='<html><body><header class="site-brand"><div class="header-actions"><a class="all-seasons-button" href="index.html">Alle seizoenen</a><button id="language-toggle"><span>NL</span></button></div></header><script id="dashboard-data" type="application/json">'+payload+'</script></body></html>'
    updated=with_navigation(old,'assets/')
    assert with_navigation(updated,'assets/')==updated
    s=BeautifulSoup(updated,'html.parser')
    assert s.find(id='dashboard-data').string==payload
    assert len(s.select('[data-site-about]'))==1
    assert len(s.select('[data-site-navigation-script]'))==1
    assert s.select_one('.all-seasons-button')['href']=='races.html'


def test_unavailable_driver_workspace_has_no_broken_link(tmp_path):
    ensure_assets(tmp_path)
    text=with_navigation(branding('assets/f1-banner-v3.png'),'assets/',False)
    button=BeautifulSoup(text,'html.parser').select_one('[data-site-link=drivers]')
    assert button.name=='button' and button.has_attr('disabled') and not button.has_attr('href')
    assert (tmp_path/'assets/site-navigation.css').exists()
