"""Shared banner destinations and the bilingual personal introduction dialog."""
from pathlib import Path
from html import escape
import re
import shutil


def ensure_assets(root):
    directory=Path(root)/'assets';directory.mkdir(parents=True,exist_ok=True)
    for name in ('site-navigation.js','site-navigation.css','site-theme.css'):
        shutil.copyfile(Path(__file__).with_name(name),directory/name)
    # The per-race template sits six directories deeper than the shared CSS.
    # Keep image references relative to assets/ when updating the shared copy.
    dashboard=directory/'dashboard.css'
    if dashboard.exists():
        dashboard.write_text(Path(__file__).with_name('dashboard.css').read_text().replace('../../../../../../assets/',''))


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


def navigation_buttons(site_prefix='', drivers_available=True, language_button=None, races_id=False):
    """One ordered menu for every page, including the standalone design guide.

    Keep legacy hooks on the Races link for retained page language handlers.
    """
    links='<a class="site-nav-button" data-site-link="home" href="'+escape(site_prefix+'index.html',quote=True)+'">Home</a>'
    links+='<a class="site-nav-button all-seasons-button"'+(' id="home-link"' if races_id else '')+' data-site-link="races" href="'+escape(site_prefix+'races.html',quote=True)+'">Races</a>'
    links+=('<a class="site-nav-button" data-site-link="drivers" href="'+escape(site_prefix+'analysis-lab.html#tab=profiles',quote=True)+'">Drivers</a>' if drivers_available else '<button type="button" class="site-nav-button" data-site-link="drivers" disabled>Drivers</button>')
    links+='<a class="site-nav-button" data-site-link="greatest" href="'+escape(site_prefix+'goat.html',quote=True)+'">Greatest</a>'
    links+='<button type="button" class="site-nav-button" data-site-about aria-haspopup="dialog" aria-controls="about-dialog" data-about-nl="About me" data-about-en="About me">About me</button>'
    return links+(language_button or '<button type="button" class="language-toggle" id="language-toggle" data-language-toggle aria-label="Switch to English"><span data-lang="en">EN</span> / <span data-lang="nl" class="active">NL</span></button>')


def without_legacy_entry(text):
    """Drivers in the shared header replaces the old standalone analysis button."""
    text=re.sub(r'<nav\b[^>]*>\s*<a\b(?=[^>]*\bdata-phase2-entry\b)[^>]*>.*?</a>\s*</nav>','',text,flags=re.S)
    return re.sub(r'<script\b[^>]*\bsrc=["\'][^"\']*phase2-entry\.js(?:\?[^"\']*)?["\'][^>]*>.*?</script>','',text,flags=re.S)


def with_navigation(text,asset_prefix,drivers_available=True):
    """Decorate existing banners without parsing or changing race JSON/scripts."""
    text=without_legacy_entry(text)
    site_prefix=asset_prefix.removesuffix('assets/')
    text=with_home_link(text,site_prefix+'index.html')
    if 'header-actions' not in text:return text
    if 'catalogue-data' in text:
        from .driver_sidebar import CSS as sidebar_css
        catalogue_css=Path(__file__).with_name('catalogue.css').read_text()
        text=re.sub(r'<style\b([^>]*)>(.*?)</style>',lambda m:'<style'+m[1]+'>'+sidebar_css+catalogue_css+'</style>' if '#race-cards' in m[2] and '.year-sidebar' in m[2] else m[0],text,flags=re.S)
    def menu(match):
        inner=match[2]
        language=re.search(r'<button\b(?=[^>]*(?:\bdata-language-toggle\b|\bid=["\']language-toggle["\']))[^>]*>.*?</button>',inner,re.S)
        return match[1]+navigation_buttons(site_prefix,drivers_available,language[0] if language else None,bool(re.search(r'\bid=["\']home-link["\']',inner)))+match[3]
    text=re.sub(r'(<div\b[^>]*class=["\'][^"\']*\bheader-actions\b[^"\']*["\'][^>]*>)(.*?)(</div>)',menu,text,count=1,flags=re.S)
    if 'data-site-navigation-style' not in text:
        style='<link rel="stylesheet" data-site-navigation-style href="'+escape(asset_prefix+'site-navigation.css',quote=True)+'">'
        text=text.replace('</head>',style+'</head>',1) if '</head>' in text else style+text
    if 'data-site-navigation-script' not in text:
        script='<script defer data-site-navigation-script src="'+escape(asset_prefix+'site-navigation.js',quote=True)+'"></script>'
        text=text.replace('</body>',script+'</body>',1) if '</body>' in text else text+script
    if 'data-site-theme-style' not in text:
        theme='<link rel="stylesheet" data-site-theme-style href="'+escape(asset_prefix+'site-theme.css',quote=True)+'">'
        text=text.replace('</head>',theme+'</head>',1) if '</head>' in text else theme+text
    return text
