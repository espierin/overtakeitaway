"""Shared banner destinations and the bilingual personal introduction dialog."""
from pathlib import Path
from html import escape
import re
import shutil


def ensure_assets(root):
    directory=Path(root)/'assets';directory.mkdir(parents=True,exist_ok=True)
    for name in ('site-navigation.js','site-navigation.css'):
        shutil.copyfile(Path(__file__).with_name(name),directory/name)


def with_home_link(text,href):
    """Make both legacy bare logos and existing logo links return to the entry page."""
    image=r'<img\b(?=[^>]*\bclass=["\'][^"\']*\bsite-wordmark\b)[^>]*>'
    def header(match):
        inner=match[2]
        def linked(logo):
            return '<a class="site-home-link" data-site-home href="'+escape(href,quote=True)+'" aria-label="Overtake It Away · Home">'+logo+'</a>'
        existing=re.compile(r'<a\b[^>]*>\s*('+image+r')\s*</a>',re.S)
        if existing.search(inner):inner=existing.sub(lambda m:linked(m[1]),inner,count=1)
        else:inner=re.sub(image,lambda m:linked(m[0]),inner,count=1)
        return match[1]+inner+match[3]
    return re.sub(r'(<header\b[^>]*class=["\'][^"\']*\bsite-brand\b[^"\']*["\'][^>]*>)(.*?)(</header>)',header,text,count=1,flags=re.S)


def with_navigation(text,asset_prefix,drivers_available=True):
    """Decorate existing banners without parsing or changing race JSON/scripts."""
    site_prefix=asset_prefix.removesuffix('assets/')
    text=with_home_link(text,site_prefix+'index.html')
    if 'header-actions' not in text:return text
    def menu(match):
        inner=match[2]
        if 'data-site-link=' not in inner:
            links='<a class="site-nav-button" data-site-link="races" href="'+escape(site_prefix+'races.html',quote=True)+'">Races</a>'
            links+='<a class="site-nav-button" data-site-link="drivers" href="'+escape(site_prefix+'analysis-lab.html#tab=profiles',quote=True)+'">Drivers</a>'
            links+='<button type="button" class="site-nav-button" data-site-about aria-haspopup="dialog" aria-controls="about-dialog" data-about-nl="Over mij" data-about-en="About me">Over mij</button>'
            inner=re.sub(r'(?=<button\b[^>]*\b(?:data-language-toggle|id=["\']language-toggle))',lambda _:links,inner,count=1)
        # All seasons should still open the catalogue, now moved off index.html.
        inner=re.sub(r'(<a\b[^>]*class=["\'][^"\']*\ball-seasons-button\b[^"\']*["\'][^>]*href=["\'])[^"\']+(["\'])',lambda m:m[1]+escape(site_prefix+'races.html',quote=True)+m[2],inner)
        return match[1]+inner+match[3]
    text=re.sub(r'(<div\b[^>]*class=["\'][^"\']*\bheader-actions\b[^"\']*["\'][^>]*>)(.*?)(</div>)',menu,text,count=1,flags=re.S)
    if drivers_available:
        enabled='<a class="site-nav-button" data-site-link="drivers" href="'+escape(site_prefix+'analysis-lab.html#tab=profiles',quote=True)+'">Drivers</a>'
        text=re.sub(r'<button\b[^>]*data-site-link="drivers"[^>]*>Drivers</button>',lambda _:enabled,text)
    if not drivers_available:
        text=re.sub(r'<a\b[^>]*data-site-link="drivers"[^>]*>Drivers</a>','<button type="button" class="site-nav-button" data-site-link="drivers" disabled>Drivers</button>',text)
    if 'data-site-navigation-style' not in text:
        style='<link rel="stylesheet" data-site-navigation-style href="'+escape(asset_prefix+'site-navigation.css',quote=True)+'">'
        text=text.replace('</head>',style+'</head>',1) if '</head>' in text else style+text
    if 'data-site-navigation-script' not in text:
        script='<script defer data-site-navigation-script src="'+escape(asset_prefix+'site-navigation.js',quote=True)+'"></script>'
        text=text.replace('</body>',script+'</body>',1) if '</body>' in text else text+script
    return text
