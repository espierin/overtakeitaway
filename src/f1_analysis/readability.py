"""Shared, bilingual presentation copy; never rewrites recorded race JSON."""
from pathlib import Path
import hashlib
import json
import re
import shutil

MARKER = 'data-readable-copy'


def asset_text():
    source = Path(__file__).parent
    catalog = json.loads((source/'assets/plain-language.json').read_text())
    return (source/'readable-copy.js').read_text().replace('/*COPY_CATALOG*/[]', json.dumps(catalog['rules'], ensure_ascii=False, separators=(',', ':')))


def script(asset_prefix):
    version = hashlib.sha256(asset_text().encode()).hexdigest()[:12]
    return f'<script defer {MARKER} src="{asset_prefix}readable-copy.js?v={version}"></script>'


def install(root):
    root = Path(root)
    for directory in [root/'assets', root/'_development/assets']:
        directory.mkdir(parents=True, exist_ok=True)
        (directory/'readable-copy.js').write_text(asset_text())
    # Restore the shared homepage controller used by both language versions.
    shutil.copyfile(Path(__file__).with_name('homepage.js'), root/'assets/homepage.js')

OLD_CONVERT = "const next=lang==='en'?lead+english(saved.source.trim())+tail:lead+dutch(saved.source.trim())+tail;"
NEW_CONVERT = "const direct=window.readableCopy&&!window.readableCopy.technical(node)?window.readableCopy.lookup(saved.source,lang):undefined;const translated=direct!==undefined?lead+direct+tail:lang==='en'?lead+english(saved.source.trim())+tail:lead+dutch(saved.source.trim())+tail;const next=window.readableCopy&&!window.readableCopy.technical(node)?window.readableCopy.text(translated,lang):translated;"


def decorate(text, asset_prefix):
    """Add shared copy once and retain every embedded data/script payload byte."""
    def language_node(match):
        opening,body,closing=match.groups()
        if 'window.siteLanguage=' not in body or re.search(r'type=["\']application/json',opening):return match[0]
        return opening+body.replace(OLD_CONVERT,NEW_CONVERT)+closing
    text=re.sub(r'(<script\b[^>]*>)(.*?)(</script>)',language_node,text,flags=re.S)
    snippet=script(asset_prefix)
    pattern=r'<script\b(?=[^>]*\bdata-readable-copy\b)[^>]*>\s*</script>'
    if re.search(pattern,text):
        text=re.sub(pattern,lambda _:snippet,text)
    elif '</head>' in text:
        text=text.replace('</head>',snippet+'</head>',1)
    elif '</body>' in text:
        text=text.replace('</body>',snippet+'</body>',1)
    else:
        text+=snippet
    if '</body>' in text and 'class="readable-help-link"' not in text:
        href=asset_prefix.removesuffix('assets/')+'uitleg.html'
        link='<p class="readable-help-link" style="font-size:12px;color:#a7b5c8"><a href="'+href+'">Uitleg bij de grafieken</a></p>'
        text=text.replace('</body>',link+'</body>',1)
    return text
