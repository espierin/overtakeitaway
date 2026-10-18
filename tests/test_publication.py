import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

from bs4 import BeautifulSoup
from PIL import Image
import pytest

from f1_analysis.io import read_json, write_json
from f1_analysis.publication import (archive_seasons, build_site, bundle, cleanup, digest,
    restore_bundle, verify_bundle, verify_site, site_html, compare_pages)
from f1_analysis.updater import plan, readiness, parse_date


def project(root):
    (root/'config').mkdir()
    (root/'config/publication.yaml').write_text('max_site_bytes: 900000000\narchive_tag_prefix: f1-data-\nsnapshot_tag: f1-site-state\n')
    run=root/'analyses/2025/test/runs/one'
    (run/'data/raw').mkdir(parents=True)
    (run/'data/normalized').mkdir()
    (run/'figures/png').mkdir(parents=True)
    (run/'figures/svg').mkdir(parents=True)
    Image.new('RGB',(50,40),'#123456').save(run/'figures/png/plot.png')
    (run/'figures/svg/plot.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>Test</text></svg>')
    write_json(run/'data/raw/input.json',{'source':'original'})
    write_json(run/'data/normalized/input.json',{'analysis':[1,2,3]})
    write_json(run/'manifest.json',{'status':'gedeeltelijk','input':{'year':2025,'gp':'Test'},'session':{'year':2025,'session_key':42},'created_at':'2025-01-01'})
    write_json(run.parent.parent/'latest.json',{'run':'runs/one'})
    page='''<html><head><style>body{color:red}</style></head><body><h1>Zelfde dashboard</h1><img src="figures/png/plot.png"><a href="figures/png/plot.png">PNG</a><a href="figures/svg/plot.svg">SVG</a><a href="data/normalized/input.json">Data</a><script id="dashboard-data" type="application/json">{"x":42}</script><script>window.value=42;</script></body></html>'''
    (run/'overzicht.html').write_text(page)
    (root/'index.html').write_text('<a href="analyses/2025/test/runs/one/overzicht.html">Race</a>')
    return run


def test_compact_site_preserves_pixels_payload_scripts_and_visible_content(tmp_path):
    root=tmp_path/'project';root.mkdir();run=project(root)
    out=tmp_path/'site';report=build_site(root,out)
    assert report['races']==1 and report['media']==2
    original=BeautifulSoup((run/'overzicht.html').read_text(),'html.parser')
    published=BeautifulSoup(site_html(out/run.relative_to(root)/'overzicht.html',out),'html.parser')
    assert published.get_text()==original.get_text()
    assert published.find(id='dashboard-data').string==original.find(id='dashboard-data').string
    script=published.find_all('script')[-1]
    assert (out/run.relative_to(root)/script['src']).resolve().read_text()=='window.value=42;'
    image=published.find('img')
    with Image.open(run/'figures/png/plot.png') as a, Image.open((out/run.relative_to(root)/image['src']).resolve()) as b:
        assert a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes()
    assert not (out/run.relative_to(root)/'data/raw').exists()
    assert (out/run.relative_to(root)/'data/normalized/input.json.gz').exists()
    assert verify_site(out)['races']==1
    assert compare_pages(root,out)['pages']==2
    # Compact snapshot is itself a valid source, so subsequent updates are idempotent.
    second=tmp_path/'site-two';again=build_site(out,second,max_bytes=900000000)
    assert again['media']==2
    assert site_html(second/run.relative_to(root)/'overzicht.html',second)==site_html(out/run.relative_to(root)/'overzicht.html',out)


def test_archived_dashboards_receive_shared_components_without_changing_race_data(tmp_path):
    from f1_analysis.publication import with_dashboard_components
    root=tmp_path/'project';root.mkdir();run=project(root);(root/'assets').mkdir()
    for name in ['race-explorer','circuit-map','strategy-popup','overtake-popup']:
        (root/'assets'/f'{name}.js').write_text('// shared component')
    original=(run/'overzicht.html').read_text().replace('<body>','<body><script data-race-explorer src="old-explorer.js"></script>')
    updated=with_dashboard_components(original,run/'overzicht.html',root)
    soup=BeautifulSoup(updated,'html.parser')
    assert soup.find(id='dashboard-data').string=='{"x":42}'
    assert len(soup.select('script[data-race-explorer]'))==1
    from urllib.parse import urlsplit
    explorer_url=urlsplit(soup.select_one('script[data-race-explorer]')['src'])
    assert explorer_url.path.endswith('/assets/race-explorer.js')
    assert explorer_url.query.startswith('v=')
    assert not soup.select_one('script[data-race-explorer]').has_attr('defer')
    for attribute in ['data-circuit-map','data-strategy-popup','data-overtake-popup']:
        assert len(soup.select(f'script[{attribute}]'))==1
        assert soup.select_one(f'script[{attribute}]').has_attr('defer')
    assert with_dashboard_components(updated,run/'overzicht.html',root)==updated
    assert with_dashboard_components('<html><body>Archive</body></html>',run/'overzicht.html',root)=='<html><body>Archive</body></html>'


def test_phase2_pages_and_dynamic_chunks_survive_automatic_republication(tmp_path):
    root=tmp_path/'project';root.mkdir();project(root)
    assets=root/'_development/assets';assets.mkdir(parents=True)
    (assets/'profile.js').write_text('window.profileReady=true;')
    data=root/'_development/data/details';data.mkdir(parents=True)
    (data/'max.js').write_text('window.detail={laps:[1,2,3]};')
    compressed=gzip.compress(b'{"laps":[1,2,3]}',mtime=0)
    (data/'max.json.gz').write_bytes(compressed)
    page='<html><head></head><body><a data-site-link="drivers" href="coureurs_2.html">Coureurs</a><script src="_development/assets/profile.js"></script></body></html>'
    for name in ('coureurs_2.html','goat_2.html','races_2.html'):
        (root/name).write_text(page)
    # No static link points at max.*: the runtime requests these chunks lazily.
    first=tmp_path/'first';second=tmp_path/'second'
    build_site(root,first)
    build_site(first,second,max_bytes=900000000)
    for site in (first,second):
        assert (site/'_development/data/details/max.json.gz').read_bytes()==compressed
        assert (site/'_development/data/details/max.js').read_text()=='window.detail={laps:[1,2,3]};'
        for name in ('coureurs_2.html','goat_2.html','races_2.html'):
            soup=BeautifulSoup(site_html(site/name,site),'html.parser')
            assert soup.select_one('[data-site-link="drivers"]')['href']=='coureurs_2.html'
            assert soup.select_one('script[data-f1-reader]') is not None
        assert verify_site(site)['races']==1


def test_fastf1_offline_inputs_survive_season_restore(tmp_path):
    root=tmp_path/'project';root.mkdir();run=project(root)
    cache=root/'cache/history/2025-01-v1'
    write_json(cache/'bundle.json',{'data':{'timing_source':'FastF1'}})
    (cache/'locations.json.gz').write_bytes(gzip.compress(b'{"63":[]}'))
    (cache/'raw').mkdir();(cache/'raw/timing.body').write_bytes(b'original timing')
    write_json(run/'data/normalized/input.json',{'history_cache':'cache/history/2025-01-v1'})
    registry=archive_seasons(root,root/'storage/archives')
    entry=registry['seasons']['2025'];restored=tmp_path/'restored'
    restore_bundle(root/'storage/archives'/entry['asset'],restored,entry['sha256'])
    for filename in ['bundle.json','locations.json.gz','raw/timing.body']:
        assert (restored/cache.relative_to(root)/filename).read_bytes()==(cache/filename).read_bytes()


def test_archive_restores_exact_originals_and_cleanup_refuses_unarchived_changes(tmp_path):
    root=tmp_path/'project';root.mkdir();run=project(root)
    store=tmp_path/'archives'
    registry=archive_seasons(root,store)
    entry=registry['seasons']['2025'];archive=store/entry['asset']
    target=tmp_path/'restored';restore_bundle(archive,target,entry['sha256'])
    assert (target/run.relative_to(root)/'overzicht.html').read_bytes()==(run/'overzicht.html').read_bytes()
    preview=cleanup(root,store)
    assert preview['files']==1 and (run/'data/raw/input.json').exists()
    cleanup(root,store,apply=True)
    assert not (run/'data/raw/input.json').exists()
    assert (run/'data/normalized/input.json').exists() # linked data stays readable
    assert (run/'overzicht.html').exists() and (run/'figures/png/plot.png').exists()
    write_json(run/'data/raw/input.json',{'changed':True})
    with pytest.raises(ValueError,match='Geen gelijk archief'):cleanup(root,store,apply=True)
    assert (run/'data/raw/input.json').exists()


def test_bundle_detects_corruption_and_prevents_path_traversal(tmp_path):
    root=tmp_path/'source';root.mkdir();(root/'a.json').write_text('original')
    entry=bundle(root,[root/'a.json'],tmp_path/'store','fixture')
    path=tmp_path/'store'/entry['asset']
    with pytest.raises(ValueError,match='Archiefhash'):verify_bundle(path,'0'*64)
    target=tmp_path/'target';target.mkdir();(target/'a.json').write_text('existing')
    with pytest.raises(ValueError,match='afwijkend'):restore_bundle(path,target,entry['sha256'])
    assert (target/'a.json').read_text()=='existing'
    malicious=tmp_path/'bad.tar.gz'
    with tarfile.open(malicious,'w:gz') as tar:
        data=b'bad';member=tarfile.TarInfo('../escape');member.size=len(data);tar.addfile(member,io.BytesIO(data))
    with pytest.raises(ValueError,match='Onveilig'):restore_bundle(malicious,target)
    assert not (tmp_path/'escape').exists()


def test_site_budget_and_broken_links_fail_before_publication(tmp_path):
    root=tmp_path/'source';root.mkdir();run=project(root);out=tmp_path/'site'
    with pytest.raises(ValueError,match='budget'):build_site(root,out,max_bytes=1)
    assert not out.exists()
    (run/'overzicht.html').write_text('<a href="missing.json">Data</a>')
    with pytest.raises(ValueError,match='Ontbrekende bronlink'):build_site(root,out)
    assert not out.exists()


def test_readiness_requires_final_timing_but_not_overtakes_or_pits():
    data={'drivers':[{'driver_number':1},{'driver_number':2}],
          'session_result':[{'driver_number':1,'position':1,'number_of_laps':50},{'driver_number':2,'position':2,'number_of_laps':49}],
          'laps':[{'driver_number':1,'lap_number':50}], 'position':[{}],'stints':[{}],'race_control':[{'message':'SESSION FINISHED'}], 'pit':[], 'overtakes':[]}
    assert readiness(data)==(True,[])
    data['laps']=[{'driver_number':1,'lap_number':49}]
    assert not readiness(data)[0]
    data['session_result'].pop()
    assert 'uitslag voor alle deelnemers' in readiness(data)[1]


def test_schedule_delays_live_races_retries_missing_data_and_refreshes_recent():
    now=parse_date('2026-10-11T12:00:00Z')
    def race(key,end):return {'session_key':key,'session_name':'Race','date_start':end,'date_end':end}
    sessions=[race(1,'2026-10-11T11:30:00Z'),race(2,'2026-10-10T12:00:00Z'),race(3,'2026-01-01T12:00:00Z'),race(4,'2026-01-02T12:00:00Z')]
    config={'minimum_delay_minutes':45,'settle_days':14,'retry_hours':6,'max_races_per_update':3}
    selected=plan(sessions,{'2':True,'3':True},{},now,config)
    assert [s['session_key'] for s in selected]==[4,2]
    state={'4':{'last_attempt':'2026-10-11T11:00:00Z'}}
    assert [s['session_key'] for s in plan(sessions,{'2':True,'3':True},state,now,config)]==[2]


def test_materialize_recovers_cleaned_input_and_preserves_dashboard(tmp_path):
    from f1_analysis.publication import materialize_run
    root=tmp_path/'project';root.mkdir();run=project(root)
    store=root/'storage/archives';archive_seasons(root,store)
    original=(run/'overzicht.html').read_bytes()
    cleanup(root,store,apply=True)
    assert not (run/'data/raw/input.json').exists()
    materialize_run(root,run)
    assert read_json(run/'data/raw/input.json')=={'source':'original'}
    assert (run/'overzicht.html').read_bytes()==original


def test_source_cache_is_archived_and_restored_with_the_run(tmp_path):
    from f1_analysis.publication import materialize_run
    root=tmp_path/'project';root.mkdir();run=project(root)
    url='https://example.org/timing';key=hashlib.sha256(url.encode()).hexdigest()
    cache=root/'cache';cache.mkdir()
    body=cache/(key+'.body');body.write_bytes(b'{"input":42}')
    write_json(cache/(key+'.meta.json'),{'url':url,'sha256':digest(body)})
    m=read_json(run/'manifest.json');m['sources']=[{'url':url,'sha256':digest(body)}];write_json(run/'manifest.json',m)
    registry=archive_seasons(root,root/'storage/archives')
    archived=verify_bundle(root/'storage/archives'/registry['seasons']['2025']['asset'])
    assert body.relative_to(root).as_posix() in archived['files']
    body.unlink();(cache/(key+'.meta.json')).unlink()
    materialize_run(root,run)
    assert body.read_bytes()==b'{"input":42}'


def test_planner_prioritizes_new_races_over_recent_refreshes():
    now=parse_date('2026-10-11T12:00:00Z')
    sessions=[{'session_key':i,'session_name':'Race','date_start':'2026-10-10T12:00:00Z','date_end':'2026-10-10T14:00:00Z'} for i in [1,2,3,4]]
    config={'minimum_delay_minutes':45,'settle_days':14,'retry_hours':6,'max_races_per_update':2}
    assert [s['session_key'] for s in plan(sessions,{'1':True,'2':True},{},now,config)]==[3,4]


def test_year_selection_filters_catalogue_without_changing_local_index(tmp_path):
    from f1_analysis.render import update_index
    import shutil
    root=tmp_path/'project';root.mkdir();run=project(root)
    old=root/'analyses/1950/example/runs/one';old.parent.mkdir(parents=True);shutil.copytree(run,old)
    m=read_json(old/'manifest.json');m['input']['year']=1950;m['session']['year']=1950;write_json(old/'manifest.json',m)
    write_json(old.parent.parent/'latest.json',{'run':'runs/one'})
    update_index(root)
    original=(root/'index.html').read_bytes()
    out=tmp_path/'site';report=build_site(root,out,from_year=2000)
    assert report['races']==1
    assert not (out/'analyses/1950').exists()
    assert [r['year'] for r in read_json(out/'analyses/index.json')]==[2025]
    assert (root/'index.html').read_bytes()==original


def test_cleanup_of_compact_snapshot_does_not_require_remote_only_archives(tmp_path):
    root=tmp_path/'project';root.mkdir();project(root)
    archive_seasons(root,root/'storage/archives')
    out=tmp_path/'compact';build_site(root,out)
    # On a runner only the active season is restored; historic data stays compact.
    assert cleanup(out,tmp_path/'no-local-archives')['files']==0


def test_packed_page_corruption_is_detected(tmp_path):
    root=tmp_path/'project';root.mkdir();project(root);out=tmp_path/'site';build_site(root,out)
    packed=next((out/'_documents').glob('*.html.gz'))
    packed.write_bytes(gzip.compress(b'<h1>changed</h1>'))
    with pytest.raises(ValueError,match='Paginahash'):verify_site(out)


def test_inline_variable_background_keeps_document_url_base(tmp_path):
    root=tmp_path/'project';root.mkdir();project(root)
    page=root/'index.html'
    css='.race-card{background-image:linear-gradient(black,transparent),var(--circuit-background)}'
    page.write_text('<style>'+css+'</style><div class="race-card" style="--circuit-background:url(assets/circuit.webp)"></div>')
    out=tmp_path/'site';build_site(root,out)
    published=BeautifulSoup(site_html(out/'index.html',out),'html.parser')
    assert published.style.string==css
    assert not published.find('link',rel='stylesheet')


def test_cleanup_does_not_interpret_raw_source_html_as_site_links(tmp_path):
    root=tmp_path/'project';root.mkdir();run=project(root)
    (run/'data/raw/source.html').write_text('<link href="/w/load.php"><a href="/wiki/Test">Original source</a>')
    archive_seasons(root,root/'storage/archives')
    report=cleanup(root,root/'storage/archives',apply=False)
    assert report['files']>0


def test_notifier_is_installed_on_catalogue_and_report_pages(tmp_path):
    root=tmp_path/'project';root.mkdir();run=project(root)
    (root/'assets').mkdir();(root/'assets/race-updates.js').write_text('window.notifier=true;')
    (root/'race-updates.json').write_text('{"races":[]}')
    out=tmp_path/'site';build_site(root,out)
    for source in [out/'index.html',out/run.relative_to(root)/'overzicht.html']:
        assert 'data-race-updates' in site_html(source,out)
    assert (out/'race-updates.json.gz').is_file()
    assert compare_pages(root,out)['pages']==2


def test_restored_catalogue_uses_current_shared_season_selector(tmp_path):
    from f1_analysis.publication import with_race_notifications
    (tmp_path/'assets').mkdir();(tmp_path/'_shared').mkdir()
    (tmp_path/'assets/catalogue.js').write_text('let year=new Date().getFullYear();')
    (tmp_path/'_shared/old-catalogue.js').write_text("const data=document.getElementById('catalogue-data');function compileRaceSearch(){}let year=+store.get('catalogue-year');")
    text='<html><head></head><body><script id="catalogue-data" type="application/json">{}</script><script src="_shared/old-catalogue.js"></script></body></html>'
    updated=with_race_notifications(text,tmp_path/'index.html',tmp_path)
    soup=BeautifulSoup(updated,'html.parser')
    assert soup.select_one('script[data-catalogue]')['src']=='assets/catalogue.js'
    assert not soup.select('script[src="_shared/old-catalogue.js"]')
    assert soup.find(id='catalogue-data').string=='{}'
    assert with_race_notifications(updated,tmp_path/'index.html',tmp_path)==updated


def test_homepage_and_moved_catalogue_survive_compact_publication(tmp_path):
    from f1_analysis.branding import ensure_banner
    from f1_analysis.homepage import build as build_homepage
    root=tmp_path/'project';root.mkdir();project(root)
    (root/'races.html').write_text((root/'index.html').read_text())
    ensure_banner(root);build_homepage(root)
    out=tmp_path/'site';build_site(root,out)
    home=BeautifulSoup(site_html(out/'index.html',out),'html.parser')
    assert home.select_one('.races-tile')['href']=='races.html'
    assert home.select_one('.goat-tile')['href']=='goat.html'
    assert (out/'goat.html').is_file()
    assert 'assets/goat.js' in site_html(out/'goat.html',out)
    assert home.select_one('a[href="stijlgids.html"]')
    assert (out/'stijlgids.html').is_file()
    assert 'data-style-guide' in site_html(out/'stijlgids.html',out)
    assert (out/'races.html').is_file()
    assert 'Race' in site_html(out/'races.html',out)
    assert verify_site(out)['races']==1
