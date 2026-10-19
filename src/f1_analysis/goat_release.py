"""Promote the reviewed GOAT workspace and retain the exact former page."""
import gzip
import hashlib
import json
from pathlib import Path
import re
from .driver_release import version_assets

MARKER = '<meta name="overtake-goat-release" content="phase2">'
BASELINE = '_development/source/legacy-goat.html.gz'
BACKUP = 'goat-backup-20261019.html'
RECORD = '_development/source/goat-release.json'


def is_promoted(root):
    from .publication import site_html
    try:
        return MARKER in site_html(Path(root)/'goat.html', Path(root))
    except FileNotFoundError:
        return False


def render(root):
    from .publication import site_html
    root = Path(root)
    template=root/'_development/templates/goat.html.txt'
    text = site_html(template if template.exists() else root/'goat_2.html', root)
    text = re.sub(r'<meta\b(?=[^>]*\bname=["\']robots["\'])[^>]*>', '', text)
    text = text.replace('</head>', MARKER+'</head>', 1)
    for old, new in [('coureurs_2.html', 'analysis-lab.html'),
                     ('races_2.html', 'races.html'), ('goat_2.html', 'goat.html')]:
        text = text.replace('href="'+old, 'href="'+new)
    from .production import without_development_intro
    return version_assets(without_development_intro(text), root)


def promote(root):
    from .publication import site_html
    root = Path(root)
    if not is_promoted(root):
        original = site_html(root/'goat.html', root).encode()
        baseline, backup = root/BASELINE, root/BACKUP
        if baseline.exists() or backup.exists():
            raise ValueError('The former GOAT page is already archived; do not overwrite it')
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_bytes(gzip.compress(original, compresslevel=9, mtime=0))
        backup.write_bytes(original)
        (root/RECORD).write_text(json.dumps({
            'source': 'goat_2.html', 'backup': BACKUP,
            'baseline': BASELINE,
            'original_sha256': hashlib.sha256(original).hexdigest(),
        }, indent=2)+'\n')
    record = json.loads((root/RECORD).read_text())
    if hashlib.sha256(gzip.decompress((root/BASELINE).read_bytes())).hexdigest() != record['original_sha256']:
        raise ValueError('The former GOAT evidence differs from its recorded hash')
    (root/'goat.html').write_text(render(root))
    return {'page': 'goat.html', 'source': 'goat_2.html', 'backup': BACKUP}
