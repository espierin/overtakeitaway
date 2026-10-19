"""GOAT comparison design workspace; no ranking is claimed before validation."""
from pathlib import Path
import shutil
from .branding import branding, with_hero_flag
from .site_navigation import ensure_assets, with_navigation


def render_goat(drivers_available=True):
    header=branding('assets/f1-banner-v3.png',seasons_url='races.html')
    page='''<!doctype html><html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="GOAT: rijders vergelijken over generaties heen. Deze vergelijking is nog in de ontwerpfase." data-nl="GOAT: rijders vergelijken over generaties heen. Deze vergelijking is nog in de ontwerpfase." data-en="GOAT: comparing drivers across generations. This comparison is still in the design phase.">
<title data-nl="GOAT · Winter break · Overtake It Away" data-en="GOAT · Winter break · Overtake It Away">GOAT · Winter break · Overtake It Away</title>
<link rel="stylesheet" href="assets/homepage.css"><link rel="stylesheet" href="assets/preseason-testing.css"><link rel="stylesheet" href="assets/goat.css">
</head><body class="home-page goat-page"><a class="skip-link" href="#goat-plan" data-nl="Naar het ontwerp" data-en="Skip to the design">Naar het ontwerp</a>
<div class="home-shell"><div class="race-hero home-hero">'''+header+'''
<div class="home-intro"><span class="home-eyebrow">GREATEST OF ALL TIME</span><h1 data-nl="GOAT. Voorbij de auto. Voorbij het tijdperk." data-en="GOAT. Beyond the car. Beyond the era.">GOAT. Voorbij de auto. Voorbij het tijdperk.</h1>
<p data-nl="Een vergelijking van alle rijders, ook als ze nooit samen aan de start stonden. We beginnen met de vraag hoe je dat eerlijk kunt onderzoeken." data-en="A comparison of all drivers, even those who never lined up together. We begin by asking how to investigate that fairly.">Een vergelijking van alle rijders, ook als ze nooit samen aan de start stonden. We beginnen met de vraag hoe je dat eerlijk kunt onderzoeken.</p></div></div>
<main id="goat-plan"><section class="goat-design" aria-labelledby="goat-design-title"><div class="goat-design-art" aria-hidden="true"><img src="assets/home/goat-winter-break-v1.webp" width="1536" height="1024" alt=""></div><div class="goat-design-copy">
<button type="button" class="goat-status" data-open-winter aria-haspopup="dialog" aria-controls="winter-dialog"><span class="goat-status-light" aria-hidden="true"></span><span data-nl="WINTER BREAK · IN ONTWERP" data-en="WINTER BREAK · IN DESIGN">WINTER BREAK · IN ONTWERP</span></button>
<h2 id="goat-design-title" data-nl="De vergelijking staat nog op de tekentafel." data-en="The comparison is still on the drawing board.">De vergelijking staat nog op de tekentafel.</h2>
<p data-nl="De ambitie: uitzoeken wie uitzonderlijk presteerde, los van de kracht van de auto en de omstandigheden van een tijdperk. Ook rijders die nooit rechtstreeks tegen elkaar raceten willen we kunnen vergelijken." data-en="The ambition: understand who performed exceptionally, beyond the strength of their car and the circumstances of their era. We also want to compare drivers who never raced each other directly.">De ambitie: uitzoeken wie uitzonderlijk presteerde, los van de kracht van de auto en de omstandigheden van een tijdperk. Ook rijders die nooit rechtstreeks tegen elkaar raceten willen we kunnen vergelijken.</p>
<p class="goat-design-note" data-nl="Eerst de meetlat ontwerpen. Daarna de aannames toetsen. Pas dan een vergelijking met zichtbare onzekerheid. Er is hier nog geen ranglijst of berekende GOAT-score." data-en="First design the yardstick. Then test the assumptions. Only then compare, with uncertainty visible. There is no ranking or calculated GOAT score here yet.">Eerst de meetlat ontwerpen. Daarna de aannames toetsen. Pas dan een vergelijking met zichtbare onzekerheid. Er is hier nog geen ranglijst of berekende GOAT-score.</p>
<div class="goat-links"><a class="goat-button" href="analysis-lab.html#tab=profiles" data-nl="Bekijk de rijdersanalyses" data-en="Explore the driver analyses">Bekijk de rijdersanalyses</a><a class="goat-button secondary" href="races.html" data-nl="Naar de races" data-en="Go to races">Naar de races</a></div></div></section>
<section class="goat-questions" aria-label="GOAT"><article><span class="goat-step">01</span><h2 data-nl="De rijder" data-en="The driver">De rijder</h2><p data-nl="Tempo, starts, constantheid en het omgaan met banden: welke kwaliteiten kunnen we betrouwbaar meten?" data-en="Pace, starts, consistency and tyre management: which qualities can we measure reliably?">Tempo, starts, constantheid en het omgaan met banden: welke kwaliteiten kunnen we betrouwbaar meten?</p></article><article><span class="goat-step">02</span><h2 data-nl="De context" data-en="The context">De context</h2><p data-nl="Hoe onderscheiden we het aandeel van de rijder van auto, team, tegenstanders en raceomstandigheden?" data-en="How do we distinguish a driver's contribution from their car, team, opponents and race conditions?">Hoe onderscheiden we het aandeel van de rijder van auto, team, tegenstanders en raceomstandigheden?</p></article><article><span class="goat-step">03</span><h2 data-nl="De generaties" data-en="The generations">De generaties</h2><p data-nl="Kunnen teamgenoten en overlappende carrières een brug vormen tussen tijdperken? En hoe groot blijft de onzekerheid?" data-en="Can teammates and overlapping careers bridge eras? And how much uncertainty remains?">Kunnen teamgenoten en overlappende carrières een brug vormen tussen tijdperken? En hoe groot blijft de onzekerheid?</p></article></section>
<p class="goat-signoff" data-nl="De fabriek is stil. De ideeën draaien door." data-en="The factory is quiet. The ideas keep running.">De fabriek is stil. De ideeën draaien door.</p>
</main><footer class="home-footer"><a href="index.html" data-nl="Terug naar de startpagina" data-en="Back to the home page">Terug naar de startpagina</a><span>A reality check on heroic stories.</span></footer></div>
<script defer src="assets/homepage.js"></script><script defer src="assets/goat.js"></script></body></html>'''
    if not drivers_available:
        import re
        page=re.sub(r'<a class="goat-button" href="analysis-lab.html#tab=profiles".*?</a>', '<button type="button" class="goat-button" disabled data-nl="Rijdersanalyses binnenkort" data-en="Driver analyses coming soon">Rijdersanalyses binnenkort</button>',page,count=1)
    return with_navigation(page,'assets/',drivers_available)


def build(root):
    from .goat_release import is_promoted, promote
    if is_promoted(root):
        promote(root)
        return Path(root)/'goat.html'
    root=Path(root);source=Path(__file__).parent;ensure_assets(root)
    for name in ('homepage.css','homepage.js','goat.css','goat.js','preseason-testing.css'):
        shutil.copyfile(source/name,root/'assets'/name)
    (root/'assets/home').mkdir(parents=True,exist_ok=True)
    for name in ('goat-winter-break-v1.webp','goat-winter-break-v1.prompt.txt'):
        shutil.copyfile(source/'assets/home'/name,root/'assets/home'/name)
    page=render_goat((root/'analysis-lab.html').exists())
    page=with_hero_flag(page,root/'index.html',root)
    (root/'goat.html').write_text(page)
    return root/'goat.html'
