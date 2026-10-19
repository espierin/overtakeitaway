"""Promote the reviewed driver module while retaining its original evidence."""
import gzip
import hashlib
import json
from pathlib import Path
import re

MARKER = '<meta name="overtake-driver-release" content="phase2">'
BASELINE = '_development/source/legacy-drivers.html.gz'


def version_assets(text, root):
    """Invalidate previously cached development scripts after a reviewed release."""
    def replace(match):
        path=Path(root)/match[2]
        if not path.is_file():return match[0]
        version=hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        return match[1]+match[2]+'?v='+version+match[3]
    return re.sub(r'((?:src|href)=["\'])(_development/assets/[^"\'?]+\.(?:js|css))(?:\?[^"\']*)?(["\'])',replace,text)


def is_promoted(root):
    from .publication import site_html
    page = Path(root)/'analysis-lab.html'
    return page.exists() and MARKER in site_html(page, root)


def source_html(root):
    """Read the frozen pre-promotion observations, never an empty UI bootstrap."""
    from .publication import site_html
    root = Path(root)
    if not is_promoted(root):
        return site_html(root/'analysis-lab.html', root)
    body = gzip.decompress((root/BASELINE).read_bytes())
    from .io import read_json
    manifest = read_json(root/'_development/clone-manifest.json')
    expected = manifest['pages']['coureurs_2.html']['source_sha256']
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError('Original driver evidence differs from the clone manifest')
    return body.decode()


def render(root):
    from .publication import site_html
    template=Path(root)/'_development/templates/drivers.html.txt'
    text = site_html(template if template.exists() else Path(root)/'coureurs_2.html', root)
    text = re.sub(r'<meta\b(?=[^>]*\bname=["\']robots["\'])[^>]*>', '', text)
    text = text.replace('</head>', MARKER+'</head>', 1)
    # Only menu destinations change; the reviewed module keeps its own assets.
    for old, new in [('coureurs_2.html','analysis-lab.html'),
                     ('races_2.html','races.html'),('goat_2.html','goat.html')]:
        text = text.replace('href="'+old, 'href="'+new)
    notifications=Path(root)/'assets/race-updates.js'
    if notifications.is_file() and 'data-race-updates' not in text:
        version=hashlib.sha256(notifications.read_bytes()).hexdigest()[:12]
        script=f'<script defer data-race-updates src="assets/race-updates.js?v={version}"></script>'
        text=text.replace('</body>',script+'</body>',1)
    from .production import without_development_intro
    return version_assets(without_development_intro(text),root)


def promote(root):
    root = Path(root)
    if not is_promoted(root):
        original = (root/'analysis-lab.html').read_bytes()
        manifest = json.loads((root/'_development/clone-manifest.json').read_text())
        expected = manifest['pages']['coureurs_2.html']['source_sha256']
        if hashlib.sha256(original).hexdigest() != expected:
            raise ValueError('Archive the exact original driver page before promotion')
        target = root/BASELINE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gzip.compress(original, compresslevel=9, mtime=0))
    (root/'analysis-lab.html').write_text(render(root))
    return {'page':'analysis-lab.html', 'presentation':'phase2',
            'source':'coureurs_2.html', 'retained_evidence':BASELINE,
            'data_refresh':'retained phase-two dataset; independent research build'}
