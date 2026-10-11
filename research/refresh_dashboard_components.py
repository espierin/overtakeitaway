"""Apply shared presentation fixes to local timing pages; retain all race inputs."""
import argparse
from pathlib import Path
from f1_analysis.io import read_json, write_json
from f1_analysis.publication import with_dashboard_components, digest, site_html

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('.'));args=parser.parse_args();root=args.root.resolve();changed=0
    for pointer in (root/'analyses').glob('*/*/latest.json'):
        run=pointer.parent/read_json(pointer)['run'];page=run/'overzicht.html';text=site_html(page,root)
        if 'dashboard-data' not in text:continue
        updated=with_dashboard_components(text,page,root)
        if updated==text:continue
        page.write_text(updated);manifest=read_json(run/'manifest.json');manifest.setdefault('file_hashes',{})['overzicht.html']=digest(page);write_json(run/'manifest.json',manifest);changed+=1
    print(f'{changed} timing dashboards use the shared presentation components.')
