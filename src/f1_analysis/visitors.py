"""Production visitor counting and a private, provider-authenticated owner view."""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
import re


def settings(root):
    path=Path(root)/'config/visitors.json'
    config=json.loads(path.read_text()) if path.exists() else {}
    site=config.get('site','').rstrip('/')
    if site and not re.fullmatch(r'https://[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.goatcounter\.com',site):
        raise ValueError('Gebruik het openbare GoatCounter-adres zonder sleutel of extra pad')
    origin=config.get('origin','https://espierin.github.io')
    base=config.get('base_path','/overtakeitaway/')
    if not re.fullmatch(r'https://[a-z0-9.-]+',origin) or not re.fullmatch(r'/[a-zA-Z0-9/_-]*/',base):
        raise ValueError('Ongeldig websiteadres voor de bezoekersteller')
    return {'site':site,'origin':origin,'base_path':base}


def install_assets(root):
    root=Path(root);assets=root/'assets';assets.mkdir(parents=True,exist_ok=True)
    text='window.oiaVisitorsConfig = '+json.dumps(settings(root))+';\n'+Path(__file__).with_suffix('.js').read_text()
    (assets/'visitors.js').write_text(text)
    return assets/'visitors.js'


def build(root):
    root=Path(root)
    from .site_navigation import ensure_assets,with_navigation
    from .branding import branding
    ensure_assets(root)
    config=settings(root);site=config['site'];embed=config['origin']+config['base_path']+'stats4me.html'
    view=(f'<div class="stats4me-actions"><a class="stats4me-link" href="{escape(site)}" target="_blank" rel="noopener noreferrer">Open mijn privédashboard ↗</a><button type="button" id="visitor-exclude" aria-pressed="false">Mijn eigen bezoeken niet meetellen</button></div>'
          '<p>De cijfers zijn alleen zichtbaar nadat je bij GoatCounter bent ingelogd. De telling begint na het online plaatsen van de teller; eerdere bezoeken kunnen we niet terughalen.</p>'
          f'<iframe class="stats4me-frame" src="{escape(site)}" title="Mijn bezoekersstatistieken bij GoatCounter" loading="lazy" referrerpolicy="origin"></iframe>'
          '<details><summary>Geen dashboard zichtbaar?</summary><p>Open je privédashboard in een nieuw tabblad en log in. Sta daarna in Settings → Sites that can embed GoatCounter dit adres toe:</p>'
          f'<p><code>{escape(embed)}</code></p><p>Laat Dashboard viewable by op alleen ingelogde gebruikers staan. Er staat geen toegangssleutel in deze pagina.</p></details>') if site else '<p>De teller is nog niet gekoppeld. Maak eerst een account aan bij <a href="https://www.goatcounter.com/signup">GoatCounter</a>.</p>'
    page='''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="description" content="Mijn bezoekersstatistieken voor Overtake It Away." data-nl="Mijn bezoekersstatistieken voor Overtake It Away." data-en="My visitor statistics for Overtake It Away."><title>Stats4me · Overtake It Away</title><link rel="stylesheet" href="assets/homepage.css"><style>body{margin:0;padding:20px;background:#0e131d;color:#f3f6fb;font:15px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.stats4me-shell{max-width:1600px;margin:auto}.stats4me-card{padding:24px;border:1px solid #344053;border-top:3px solid #b45cff;background:#111824;border-radius:10px}.stats4me-card h1{margin:0 0 10px}.stats4me-actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center}.stats4me-actions a,.stats4me-actions button{font:inherit;color:#f3f6fb;border:1px solid #596273;border-top:3px solid #b45cff;border-radius:5px;background:#0b1019;padding:9px 14px;text-decoration:none;cursor:pointer}.stats4me-card a{color:#51d6dd}.stats4me-frame{display:block;width:100%;height:1050px;border:1px solid #344053;border-radius:8px;background:#fff;margin:20px 0}.stats4me-card code{overflow-wrap:anywhere}.stats4me-card details{border-top:1px solid #344053;padding-top:16px}.stats4me-card summary{cursor:pointer;color:#d9b3ff}@media(max-width:600px){body{padding:12px}.stats4me-card{padding:16px}.stats4me-frame{height:900px}}</style></head><body class="home-page"><div class="stats4me-shell"><div class="race-hero">'''+branding('assets/f1-banner-v3.png',seasons_url='races.html')+'</div><main class="stats4me-card"><h1>Stats4me</h1><p>Bezoekers, bekeken pagina’s en waar je bezoekers vandaan komen.</p>'+view+'</main></div><script defer data-site-visitors src="assets/visitors.js"></script><script defer src="assets/homepage.js"></script></body></html>'
    (root/'stats4me.html').write_text(with_navigation(page,'assets/'))
    return root/'stats4me.html'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');args=parser.parse_args();print(build(args.root))


if __name__=='__main__':main()
