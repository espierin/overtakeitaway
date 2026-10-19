"""One public route per module, retaining bookmarks and editable source templates."""
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit

ROUTES = {
    'coureurs_2.html': 'analysis-lab.html',
    'goat_2.html': 'goat.html',
    'races_2.html': 'races.html',
    '_development/uitleg-start-en-raceonderzoek.html': 'uitleg-start-en-raceonderzoek.html',
    '_development/data-collection.html': 'data-collection.html',
}


def links(text):
    """Change navigation attributes only; embedded observations remain byte-identical."""
    def change(match):
        url = match[2]
        for old, new in ROUTES.items():
            url = url.replace(old, new)
        return match[1]+url+match[3]
    return re.sub(r'((?:href|data-help-href)=["\'])([^"\']+)(["\'])', change, text)


def without_development_intro(text):
    text = re.sub(r'<script\b[^>]*src=["\'][^"\']*assets/(?:preseason-testing|goat)\.js(?:\?[^"\']*)?["\'][^>]*>.*?</script>', '', text, flags=re.S)
    text = re.sub(r'<button\b[^>]*data-open-(?:preseason|winter)[^>]*>.*?</button>', '', text, flags=re.S)
    return links(text)


def redirect(destination):
    return '<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><link rel="canonical" href="'+destination+'"><title>Overtake It Away</title></head><body><p><a href="'+destination+'">Open de pagina / Open the page</a></p><script>location.replace('+repr(destination)+'+location.search+location.hash);</script></body></html>'


def prepare(root):
    root=Path(root)
    templates=root/'_development/templates';templates.mkdir(parents=True,exist_ok=True)
    for old, name in [('coureurs_2.html','drivers.html.txt'),('goat_2.html','goat.html.txt'),('races_2.html','race-research.html.txt')]:
        target=templates/name
        if not target.exists():target.write_text(without_development_intro((root/old).read_text()))
    help_source=root/'_development/uitleg-start-en-raceonderzoek.html'
    help_target=root/'uitleg-start-en-raceonderzoek.html'
    if not help_target.exists():
        # The shared help is now served one directory higher; keep its assets in place.
        import posixpath
        def rebase(match):
            url=urlsplit(match[2])
            if url.scheme or url.netloc or not url.path:return match[0]
            path=posixpath.normpath(posixpath.join('_development',url.path))
            return match[1]+urlunsplit(('', '', path, url.query, url.fragment))+match[3]
        text=re.sub(r'((?:href|src)=["\'])([^"\']+)(["\'])',rebase,help_source.read_text())
        help_target.write_text(links(text))
    for old,new in ROUTES.items():
        destination=('../' if old.startswith('_development/') else '')+new
        (root/old).write_text(redirect(destination))
    from .driver_release import promote as drivers
    from .goat_release import promote as goat
    drivers(root);goat(root)
