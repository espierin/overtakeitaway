import shutil
from pathlib import Path
from f1_analysis.io import read_json,write_json
from f1_analysis.publication import archive_sources,storage_entries,verify_bundle
from f1_analysis.github_storage import restore_years
from test_github_storage import MemoryReleases


def test_source_supplements_are_bounded_incremental_and_restore_in_order(tmp_path):
    root=tmp_path/'root';(root/'config').mkdir(parents=True)
    write_json(root/'config/publication.yaml',{'archive_tag_prefix':'f1-data-'})
    folder=root/'analyses/sources';folder.mkdir(parents=True)
    a=folder/'a.json';b=folder/'b.json';a.write_text('old');b.write_text('B'*10)
    store=root/'storage/archives';reg={'schema':1,'seasons':{}}
    archive_sources(root,[a,b],store,reg,max_chunk_bytes=12)
    assert len(reg['source_supplements'])==1
    base=reg['sources']['asset'];a.write_text('new')
    archive_sources(root,[a,b],store,reg,max_chunk_bytes=12)
    assert reg['sources']['asset']==base and len(reg['source_supplements'])==2
    latest=verify_bundle(store/reg['source_supplements'][-1]['asset'])
    assert set(latest['files'])=={'analyses/sources/a.json'}
    count=len(reg['source_supplements']);archive_sources(root,[a,b],store,reg,max_chunk_bytes=12)
    assert len(reg['source_supplements'])==count
    remote=tmp_path/'remote';remote.mkdir();github=MemoryReleases(remote)
    for entry in storage_entries(reg):github.upload(entry['tag'],store/entry['asset'])
    restored=tmp_path/'restored';write_json(restored/'_storage/index.json',reg)
    # Request a season to trigger restoration of its shared evidence archives.
    restore_years(restored,github,[2026])
    assert (restored/'analyses/sources/a.json').read_text()=='new'
    assert (restored/'analyses/sources/b.json').read_text()=='B'*10


def test_metadata_rebuild_preserves_only_matching_measured_lap_context():
    from f1_analysis.lap_rankings import preserve_retained_context
    prior=[[1,2,20,4,65],[2,3,20,4,64],[3,1,19,6,64]]
    new=[[1,2,20,0,97],[2,4,20,0,96],[3,1,19,5,64]]
    assert preserve_retained_context(new,prior)==[prior[0],new[1],new[2]]


def test_on_demand_restore_applies_deltas_but_keeps_existing_local_source_edits(tmp_path):
    from test_publication import project
    from f1_analysis.publication import archive_seasons,materialize_run
    root=tmp_path/'root';root.mkdir();run=project(root)
    source=root/'analyses/sources/review.json';source.parent.mkdir(parents=True)
    source.write_text('old');store=root/'storage/archives'
    registry=archive_seasons(root,store)
    source.write_text('reviewed')
    archive_sources(root,[source],store,registry)
    write_json(root/'_storage/index.json',registry)
    source.unlink();materialize_run(root,run)
    assert source.read_text()=='reviewed'
    source.write_text('new local evidence')
    materialize_run(root,run)
    assert source.read_text()=='new local evidence'
