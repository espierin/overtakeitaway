"""Website identity and offline language switch for index and race dashboards."""
from pathlib import Path

def branding(asset_url="../../../../../assets/f1-banner-v3.png",seasons_url=None):
    from html import escape
    wordmark_url=escape(asset_url.rsplit('/',1)[0]+'/overtake-wordmark-v3.svg',quote=True)
    return hero_style(asset_url)+rounded_number_style()+header_actions_style()+'''<style>.site-brand{position:relative;padding:12px 120px 24px 0}.site-brand h2{border:0;margin:0;padding:0;font-size:clamp(24px,3vw,40px);font-weight:900;letter-spacing:-.03em}.site-tagline{margin:3px 0 0;color:#b3bece;font-size:15px;font-style:italic}.language-toggle{position:absolute;right:0;top:14px;background:#080a10;color:#fff;border:1px solid #596273;border-top:3px solid #ff4b56;border-radius:2px;padding:8px 12px;font-weight:900;cursor:pointer}.language-toggle span{opacity:.4}.language-toggle span.active{opacity:1;color:#51d6dd}</style><header class="site-brand"><img class="site-wordmark" src="WORDMARK_URL" alt="" aria-hidden="true"><h2>Overtake It Away</h2><p class="site-tagline">A reality check on heroic stories.</p><div class="header-actions">SEASONS_BUTTON<button type="button" class="language-toggle" id="language-toggle" data-language-toggle aria-label="Switch to English"><span data-lang="en">EN</span> / <span data-lang="nl" class="active">NL</span></button></div></header>'''.replace('WORDMARK_URL',wordmark_url).replace('SEASONS_BUTTON','<a class="all-seasons-button" href="'+escape(seasons_url,quote=True)+'">Alle seizoenen</a>' if seasons_url else '')


def language_controls():
    return '<button id="language-toggle" data-language-toggle class="language-toggle" type="button"><span data-lang="en">EN</span> / <span data-lang="nl">NL</span></button>'


def language_script():
    return back_to_top()+'<script>'+Path(__file__).with_name('language.js').read_text()+'</script>'


def ensure_banner(root):
    """Install the bundled decorative asset once for offline dashboards."""
    import shutil
    for name in ['f1-banner-v3.png','overtake-wordmark-v3.svg']:
        target=Path(root)/'assets'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            shutil.copyfile(Path(__file__).parent/'assets'/name,target)


    for source in list((Path(__file__).parent/'assets/cards').glob('*.png'))+list((Path(__file__).parent/'assets/charts').glob('*.png')):
        target=Path(root)/'assets'/source.parent.name/source.name
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            shutil.copyfile(source,target)


def hero_style(asset_url):
    from html import escape
    return '<style>'+HERO_CSS.replace('BANNER_URL',escape(asset_url,quote=True))+'</style>'


HERO_CSS = """
.race-hero{position:relative;isolation:isolate;overflow:hidden;min-height:280px;padding:24px 28px 30px;margin-bottom:24px;border:1px solid #343945;border-bottom:3px solid #ed2435;border-radius:10px 10px 3px 3px;background:#080a0e;color:#fff;box-shadow:0 12px 36px #0005}
.race-hero::before{content:"";position:absolute;inset:0;z-index:-1;background-image:linear-gradient(90deg,#05070bee 0%,#05070bbb 45%,#05070b22 100%),url('BANNER_URL');background-position:center,right center;background-size:100% 100%,min(1200px,160%) auto;background-repeat:no-repeat}
.race-hero .site-brand{position:relative;padding:0 100px 20px 0;min-height:104px;box-sizing:content-box}
.site-wordmark{display:block;width:600px;max-width:100%;height:auto;aspect-ratio:6.4;object-fit:contain;object-position:center;filter:drop-shadow(0 2px 3px #0008)}
.race-hero .site-brand h2,.race-hero .site-tagline{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
.race-hero .language-toggle{position:absolute;top:0;right:0;background:#080a10eb}
.race-hero h1,.race-hero .dash-header h1{position:relative;max-width:100%;margin:12px 0 8px;font-size:48px;line-height:1.12;letter-spacing:-.035em;font-weight:900;color:#fff;text-wrap:balance;text-shadow:0 2px 6px #000,0 4px 20px #000}
.race-hero p{color:#d4dbe6;text-shadow:0 2px 8px #000}.race-hero nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}.race-hero nav a{color:#fff;background:#080a10cc;border:1px solid #657084;padding:5px 9px;border-radius:3px;text-decoration:none;font-size:12px}
.race-hero nav a:hover,.race-hero nav a:focus-visible{background:#812331;border-color:#ff5261}.race-hero .language-toggle:focus-visible{outline:2px solid white;outline-offset:4px}
@media(max-width:850px){.race-hero{padding:20px;min-height:250px}.race-hero .site-brand{padding:36px 0 16px;min-height:0}.site-wordmark{width:440px}.race-hero h1,.race-hero .dash-header h1{font-size:36px}.race-hero::before{background-size:100% 100%,min(1000px,160%) auto}}
@media(max-width:520px){.race-hero{padding:16px 12px}.site-wordmark{width:320px}.race-hero h1,.race-hero .dash-header h1{font-size:28px}}
"""

HERO_CSS += """
.race-hero h1,.race-hero .dash-header h1{margin-left:16px;max-width:calc(100% - 16px);text-align:left}
@media(max-width:850px){.race-hero h1,.race-hero .dash-header h1{margin-left:12px;max-width:calc(100% - 12px)}}
@media(max-width:520px){.race-hero h1,.race-hero .dash-header h1{margin-left:8px;max-width:calc(100% - 8px)}}
"""


def race_title(data):
    from html import escape
    session=data.get('session',{})
    race=session.get('jolpica_race',{})
    name=race.get('raceName') or data.get('name') or data.get('meeting',{}).get('meeting_name') or session.get('meeting_name') or session.get('circuit_short_name','')
    return escape(str(session.get('year',data.get('year','')))+' · '+str(name))


def race_metadata(data):
    """Circuit name and calendar race date below the official GP title."""
    from html import escape
    session=data.get('session',{})
    race=session.get('jolpica_race',{})
    circuit=data.get('circuit');name=race.get('Circuit',{}).get('circuitName') or data.get('jolpica_circuit',{}).get('circuitName') or (circuit if isinstance(circuit,str) else '') or session.get('circuit_short_name')
    date=race.get('date') or data.get('date') or (session.get('date_start') or '')[:10]
    return '<div class="race-metadata">'+('<p class="race-gp-name">'+escape(str(name))+'</p>' if name else '')+('<time data-race-date datetime="'+escape(str(date),quote=True)+'">'+escape(str(date))+'</time>' if date else '')+'</div><style>.race-metadata{position:relative;z-index:1;margin:8px 0 0 16px;text-align:left;text-shadow:0 2px 5px #000;color:#d4dbe5;font-size:16px;line-height:1.5}.race-metadata .race-gp-name{margin:0;font-size:18px;font-weight:600}.race-metadata time{display:block;font-size:15px}.race-hero{height:auto;min-height:310px;padding-bottom:24px}@media(max-width:850px){.race-metadata{margin-left:12px}}@media(max-width:520px){.race-metadata{margin-left:8px}}</style>'


def rounded_number_style():
    return '<style id="driver-number-style">.driver-number,.driver-num,.highlight-number,.rex-badge>i,.driver-axis-badge>span{border-radius:4px!important;font-variant-numeric:tabular-nums}.driver-axis-badge>span{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;width:24px;min-width:24px;height:18px;padding:0!important;flex:none}#driverchart .driver-axis-badge{display:grid;grid-template-columns:24px 3px 28px;gap:4px;width:63px;height:20px;line-height:1;font-size:11px}#driverchart .driver-axis-badge>b{width:28px;white-space:nowrap}</style>'


def back_to_top():
    return '''<style id="back-to-top-style">#back-to-top{position:fixed;right:max(22px,env(safe-area-inset-right));bottom:max(22px,env(safe-area-inset-bottom));z-index:900;width:58px;height:54px;padding:0;border:0;border-radius:0;background:transparent;color:#fff;isolation:isolate;cursor:pointer;filter:drop-shadow(0 5px 12px #0009);transition:filter .18s,transform .18s}#back-to-top[hidden]{display:none!important}#back-to-top::before,#back-to-top::after{content:"";position:absolute;inset:0;z-index:-1;clip-path:polygon(12px 0,100% 0,100% calc(100% - 12px),calc(100% - 12px) 100%,0 100%,0 12px)}#back-to-top::before{background:#b445ff}#back-to-top::after{inset:2px;background:linear-gradient(135deg,#351647,#0c0e17 75%);border-top:3px solid #b445ff}#back-to-top svg{width:25px;height:28px;display:block;margin:auto;max-height:none}#back-to-top:hover,#back-to-top:focus-visible{color:#51d6dd;outline:none;filter:drop-shadow(0 0 7px #51d6dd66);transform:translateY(-2px)}#back-to-top:hover::before,#back-to-top:focus-visible::before{background:#51d6dd}#back-to-top:active{transform:translateY(0)}@media(max-width:520px){#back-to-top{right:14px;bottom:14px;width:52px;height:48px}}@media(prefers-reduced-motion:reduce){#back-to-top{transition:none}}</style><button id="back-to-top" type="button" title="Naar boven" aria-label="Naar boven" hidden><svg viewBox="0 0 28 30" aria-hidden="true"><path d="M5 15L14 6l9 9M5 24l9-9 9 9" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="square" stroke-linejoin="miter"/></svg></button>'''+'<script data-back-to-top>'+Path(__file__).with_name('back_to_top.js').read_text()+'</script>'


def header_actions_style():
    return '<style id="header-actions-style">.site-brand .header-actions{position:absolute;top:0;right:0;display:flex;align-items:stretch;gap:8px;z-index:2}.race-hero .header-actions .language-toggle,.header-actions .language-toggle{position:static;top:auto;right:auto;margin:0}.header-actions .language-toggle,.header-actions .all-seasons-button{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;gap:4px;background:#080a10eb;color:#fff;border:1px solid #596273;border-top:3px solid #ff4b56;border-radius:2px;padding:8px 12px;font:900 13px system-ui;line-height:20px;white-space:nowrap;text-decoration:none}.header-actions .all-seasons-button:hover,.header-actions .all-seasons-button:focus-visible{border-color:#51d6dd;outline:2px solid #51d6dd}@media(max-width:850px){.race-hero .site-brand{padding-top:48px}}</style>'
