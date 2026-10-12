import hashlib
from pathlib import Path
import shutil

from f1_analysis.github_storage import publish_state, load_state, prune
from f1_analysis.io import read_json, write_json
from f1_analysis.publication import archive_seasons, build_site, digest
from test_publication import project


class MemoryReleases:
    def __init__(self,root):self.root=root;self.tags={};self.counter=0;self.uploaded=[]
    def release(self,tag,create=False):
        if tag not in self.tags:
            if not create:return None
            self.tags[tag]={'tag':tag,'assets':[]}
        return self.tags[tag]
    def assets(self,release):return release['assets']
    def upload(self,tag,path):
        release=self.release(tag,True)
        old=next((a for a in release['assets'] if a['name']==path.name),None)
        if old:
            assert old['digest']=='sha256:'+digest(path)
            return old
        self.counter+=1;stored=self.root/(str(self.counter)+'-'+path.name);shutil.copyfile(path,stored)
        asset={'id':self.counter,'name':path.name,'digest':'sha256:'+digest(path),'stored':stored}
        release['assets'].append(asset);self.uploaded.append(path.name);return asset
    def download(self,asset,target,expected=None):
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(asset['stored'],target)
        if expected:assert digest(target)==expected
        return target
    def delete(self,asset):
        for release in self.tags.values():
            release['assets'][:]=[a for a in release['assets'] if a['id']!=asset['id']]
        asset['stored'].unlink()


def test_retry_state_does_not_duplicate_large_site_snapshot_and_can_resume(tmp_path):
    root=tmp_path/'project';root.mkdir();project(root)
    archives=root/'storage/archives';archive_seasons(root,archives)
    write_json(root/'_storage/update-state.json',{'schema':1,'sessions':{'42':{'last_attempt':'2026-10-11T12:00:00Z'}}})
    site=tmp_path/'site';build_site(root,site)
    remote=tmp_path/'remote';remote.mkdir();github=MemoryReleases(remote)
    first=publish_state(root,github,site,archives)
    write_json(site/'_storage/update-state.json',{'schema':1,'sessions':{'42':{'last_attempt':'2026-10-11T18:00:00Z'}}})
    second=publish_state(root,github,site,archives)
    assert first['sha256']==second['sha256']
    assert len([name for name in github.uploaded if name.startswith('site-')])==1
    assert len([name for name in github.uploaded if name.startswith('state-')])==2
    restored=tmp_path/'restored';(restored/'config').mkdir(parents=True)
    shutil.copyfile(root/'config/publication.yaml',restored/'config/publication.yaml')
    load_state(restored,github)
    assert read_json(restored/'_storage/update-state.json')['sessions']['42']['last_attempt']=='2026-10-11T18:00:00Z'
    assert (restored/'index.html').exists()
    assert (restored/'analyses/2025/test/runs/one/data/normalized/input.json').exists()
    compact=tmp_path/'compact';(compact/'config').mkdir(parents=True)
    shutil.copyfile(root/'config/publication.yaml',compact/'config/publication.yaml')
    load_state(compact,github,compact=True)
    assert not (compact/'analyses/2025/test/runs/one/data/normalized/input.json').exists()
    assert (compact/'analyses/2025/test/runs/one/data/normalized/input.json.gz').exists()


def test_retention_preserves_current_and_fallback_references(tmp_path):
    root=tmp_path/'project';root.mkdir();run=project(root)
    store=root/'storage/archives';remote=tmp_path/'remote';remote.mkdir();github=MemoryReleases(remote)
    for i in range(5):
        write_json(run/'data/raw/input.json',{'source':i})
        archive_seasons(root,store)
        site=tmp_path/f'site-{i}';build_site(root,site)
        publish_state(root,github,site,store)
    report=prune(root,github)
    assert report['deleted']>0
    states=github.assets(github.release('f1-site-state'))
    assert len([a for a in states if a['name'].startswith('state-')])==3
    state_assets={a['name'] for a in states}
    for a in states:
        if not a['name'].startswith('state-'):continue
        state=read_json(a['stored'])
        assert state['asset'] in state_assets
        for entry in state['archive_refs']:
            assets=github.assets(github.release(entry['tag']))
            assert entry['asset'] in {x['name'] for x in assets}
    # After pruning the newest state can still be restored independently.
    restored=tmp_path/'restore';(restored/'config').mkdir(parents=True)
    shutil.copyfile(root/'config/publication.yaml',restored/'config/publication.yaml')
    load_state(restored,github)
    assert read_json(restored/'_storage/index.json')==read_json(root/'_storage/index.json')


def test_frozen_presentation_survives_archive_restore_without_rolling_back_new_runs(tmp_path):
    from f1_analysis.publication import freeze_website, restore_presentation, compare_pages
    from f1_analysis.github_storage import restore_years
    root=tmp_path/'project';root.mkdir();run=project(root)
    archives=root/'storage/archives';archive_seasons(root,archives)
    page=run/'overzicht.html';page.write_text(page.read_text().replace('Zelfde dashboard','Nieuwe tekst'))
    corrections=run.parent.parent/'corrections';corrections.mkdir();write_json(corrections/'manual.json',{'note':'current correction'})
    frozen=tmp_path/'frozen';freeze_website(root,frozen,archives)
    site=tmp_path/'site';build_site(frozen,site)
    remote=tmp_path/'remote';remote.mkdir();github=MemoryReleases(remote)
    publish_state(root,github,site,archives)
    restored=tmp_path/'restored';(restored/'config').mkdir(parents=True)
    shutil.copyfile(root/'config/publication.yaml',restored/'config/publication.yaml')
    load_state(restored,github)
    restore_years(restored,github,[])
    assert compare_pages(frozen,build_output(restored,tmp_path/'without-restore'))['pages']==2
    restore_years(restored,github,[2025])
    assert read_json(restored/corrections.relative_to(root)/'manual.json')=={'note':'current correction'}
    assert 'Nieuwe tekst' in (restored/run.relative_to(root)/'overzicht.html').read_text()
    assert compare_pages(frozen,build_output(restored,tmp_path/'rebuilt'))['pages']==2
    # An old overlay must never overwrite a newer analysis run or its pointer.
    old=restored/run.relative_to(root);new=old.parent/'two';shutil.copytree(old,new)
    (new/'overzicht.html').write_text('newer')
    write_json(new.parent.parent/'latest.json',{'run':'runs/two'})
    entry=read_json(frozen/'_storage/index.json')['presentation']
    restore_presentation(archives/entry['asset'],restored,entry['sha256'])
    assert (new/'overzicht.html').read_text()=='newer'


def build_output(root,output):
    build_site(root,output)
    return output


def test_new_archive_absorbs_old_presentation_overlay(tmp_path):
    from f1_analysis.publication import freeze_website
    root=tmp_path/'project';root.mkdir();run=project(root)
    archives=root/'storage/archives';archive_seasons(root,archives)
    (run/'overzicht.html').write_text('first change')
    frozen=tmp_path/'frozen';freeze_website(root,frozen,archives)
    shutil.copyfile(frozen/'_storage/index.json',root/'_storage/index.json')
    (run/'overzicht.html').write_text('second change')
    registry=archive_seasons(root,archives)
    assert 'presentation' not in registry
    restored=tmp_path/'restored';restored.mkdir()
    from f1_analysis.publication import restore_bundle
    restore_bundle(archives/registry['seasons']['2025']['asset'],restored)
    assert (restored/run.relative_to(root)/'overzicht.html').read_text()=='second change'


def test_incremental_restore_keeps_other_seasons_compact(tmp_path):
    from f1_analysis.publication import freeze_website, compare_pages
    from f1_analysis.github_storage import restore_years
    root=tmp_path/'project';root.mkdir();run=project(root)
    older=root/'analyses/2024/test';shutil.copytree(run.parent.parent,older)
    manifest=read_json(older/'runs/one/manifest.json');manifest['input']['year']=2024;manifest['session']['year']=2024
    write_json(older/'runs/one/manifest.json',manifest)
    (root/'index.html').write_text('<a href="analyses/2024/test/runs/one/overzicht.html">Old</a><a href="analyses/2025/test/runs/one/overzicht.html">New</a>')
    archives=root/'storage/archives';archive_seasons(root,archives)
    for page in root.glob('analyses/*/*/runs/*/overzicht.html'):
        page.write_text(page.read_text().replace('Zelfde dashboard','Gewijzigd dashboard'))
    frozen=tmp_path/'frozen';freeze_website(root,frozen,archives)
    site=tmp_path/'site';build_site(frozen,site)
    remote=tmp_path/'remote';remote.mkdir();github=MemoryReleases(remote)
    publish_state(root,github,site,archives)
    restored=tmp_path/'restored';(restored/'config').mkdir(parents=True)
    shutil.copyfile(root/'config/publication.yaml',restored/'config/publication.yaml')
    load_state(restored,github);restore_years(restored,github,[2025])
    assert not (restored/'analyses/2024/test/runs/one/figures/png/plot.png').exists()
    assert compare_pages(frozen,build_output(restored,tmp_path/'rebuilt'))['pages']==3
