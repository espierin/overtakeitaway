"""Bilingual entry page for races, driver research and the GOAT design workspace."""
from pathlib import Path
import shutil
from .branding import branding, with_hero_flag


def render_home(drivers_available=True):
    header = branding('assets/f1-banner-v3.png', seasons_url='races.html')
    drivers_tag = 'a href="analysis-lab.html#tab=profiles"' if drivers_available else 'article aria-disabled="true"'
    drivers_close = 'a' if drivers_available else 'article'
    page = '''<!doctype html><html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Ontdek Formula 1 via raceanalyses, rijdersprofielen en strategie. Overtake It Away.">
<title>Overtake It Away: Geen fabels maar feiten</title>
<link rel="stylesheet" href="assets/homepage.css"></head><body class="home-page">
<a class="skip-link" href="#explore" data-nl="Naar de onderwerpen" data-en="Skip to topics">Naar de onderwerpen</a>
<div class="home-shell"><div class="race-hero home-hero">'''+header+'''
<div class="home-intro"><span class="home-eyebrow">FORMULA 1 · OVERTAKE IT AWAY</span>
<h1 data-nl="Elke race een verhaal. Elke rijder een perspectief." data-en="Every race a story. Every driver a perspective.">Elke race een verhaal. Elke rijder een perspectief.</h1>
<p data-nl="Volg de actie. Vergelijk de rijders. Ontdek wat de cijfers vertellen." data-en="Follow the action. Compare the drivers. Discover what the numbers reveal.">Volg de actie. Vergelijk de rijders. Ontdek wat de cijfers vertellen.</p></div></div>
<main id="explore" class="home-choices" aria-label="Races, Drivers &amp; GOAT">
<a class="home-tile races-tile" href="races.html" aria-labelledby="races-title">
<img src="assets/home/races.webp" width="1536" height="1024" alt="" fetchpriority="high">
<div class="tile-copy"><span class="tile-kicker" data-nl="HET RACEARCHIEF" data-en="THE RACE ARCHIVE">HET RACEARCHIEF</span>
<h2 id="races-title">Races</h2>
<p data-nl="Van de start tot de finish. Inhaalacties, pitstops en de momenten die een Grand Prix bepalen." data-en="From lights out to the finish. Overtakes, pit stops and the moments that shape a Grand Prix.">Van de start tot de finish. Inhaalacties, pitstops en de momenten die een Grand Prix bepalen.</p>
<span class="tile-cta"><span data-nl="Verken de races" data-en="Explore the races">Verken de races</span><span aria-hidden="true">↗</span></span></div></a>
<'''+drivers_tag+''' class="home-tile drivers-tile" aria-labelledby="drivers-title">
<img src="assets/home/drivers.webp" width="1536" height="1024" alt="" decoding="async">
<div class="tile-copy"><span class="tile-kicker" data-nl="ACHTER HET VIZIER" data-en="BEHIND THE VISOR">ACHTER HET VIZIER</span>
<h2 id="drivers-title" data-nl="Coureurs" data-en="Drivers">Coureurs</h2>
<p data-nl="Kijk voorbij de uitslag. Vergelijk teamgenoten, onderzoek het racetempo en ontdek de strategie." data-en="Look beyond the result. Compare teammates, investigate race pace and explore strategy.">Kijk voorbij de uitslag. Vergelijk teamgenoten, onderzoek het racetempo en ontdek de strategie.</p>
<span class="tile-status" data-nl="PRE-SEASON TESTING · IN OPBOUW" data-en="PRE-SEASON TESTING · IN DEVELOPMENT">PRE-SEASON TESTING · IN OPBOUW</span>
<span class="tile-cta"><span data-nl="'''+('Ontdek de rijders' if drivers_available else 'Binnenkort beschikbaar')+'" data-en="'+('Explore the drivers' if drivers_available else 'Coming soon')+'">'+('Ontdek de rijders' if drivers_available else 'Binnenkort beschikbaar')+'''</span><span aria-hidden="true">↗</span></span></div></'''+drivers_close+'''>
<a class="home-tile goat-tile" href="goat.html" aria-labelledby="goat-title">
<img src="assets/home/goat-winter-break-v1.webp" width="1536" height="1024" alt="" decoding="async">
<div class="tile-copy"><span class="tile-kicker">GREATEST OF ALL TIME</span>
<h2 id="goat-title">GOAT</h2>
<p data-nl="Wie is de beste, voorbij de auto en het tijdperk? Een nieuwe blik op alle rijders, ook als ze nooit tegen elkaar raceten." data-en="Who is the best, beyond the car and the era? A new look at all drivers, even those who never raced each other.">Wie is de beste, voorbij de auto en het tijdperk? Een nieuwe blik op alle rijders, ook als ze nooit tegen elkaar raceten.</p>
<span class="tile-status" data-nl="WINTER BREAK · IN ONTWERP" data-en="WINTER BREAK · IN DESIGN">WINTER BREAK · IN ONTWERP</span>
<span class="tile-cta"><span data-nl="Ontdek het idee" data-en="Explore the idea">Ontdek het idee</span><span aria-hidden="true">↗</span></span></div></a>
</main><footer class="home-footer"><span>Overtake It Away</span><a href="stijlgids.html" data-nl="Stijlgids" data-en="Style guide">Stijlgids</a><span>A reality check on heroic stories.</span></footer></div>
<script defer src="assets/homepage.js"></script></body></html>'''
    from .site_navigation import with_navigation
    return with_navigation(page,'assets/',drivers_available)


def build(root):
    root = Path(root)
    source = Path(__file__).parent
    from .site_navigation import ensure_assets
    ensure_assets(root)
    assets = root/'assets'
    (assets/'home').mkdir(parents=True, exist_ok=True)
    for name in ('homepage.css', 'homepage.js'):
        shutil.copyfile(source/name, assets/name)
    for image in (source/'assets/home').glob('*.webp'):
        shutil.copyfile(image, assets/'home'/image.name)
    page = render_home((root/'analysis-lab.html').exists())
    page = with_hero_flag(page, root/'index.html', root)
    (root/'index.html').write_text(page)
    from .goat import build as build_goat
    build_goat(root)
    from .style_guide import build as build_style_guide
    build_style_guide(root)
    return root/'index.html'
