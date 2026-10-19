# Fase 2 · lokale ontwikkelomgeving

Deze omgeving voert het [totaalplan](../documents/fase-2-onderzoeks-en-ontwikkelplan.md) uit op afzonderlijke ontwikkelpagina’s. De oorspronkelijke brongegevens en scripts blijven behouden. Publicatie van deze afzonderlijke pagina’s is op 18 oktober 2026 expliciet toegestaan.

| Pagina | Inhoud |
|---|---|
| [Coureurs](../coureurs_2.html) | Eigen carrièrefeiten, zes specialismen, start en racevervolg, teamgenootduel, regelmaat, incidenten en dekking |
| [GOAT](../goat_2.html) | Beschrijvende vergelijking, gedeelde context, netwerkonderzoek, profielkaart en modeltoetsen |
| [Races](../races_2.html#phase2-race-research) | Bestaande catalogus plus racebevindingen, strategieatlas, rekenscenario en gedateerde weersbron |
| [Rekenuitleg](uitleg-start-en-raceonderzoek.html) | Berekening en interpretatie van alle coureursanalyses, inclusief de bewaarde start-/racescores, in NL en EN |
| [Datacollectie](data-collection.html) | Parameters, aantallen, herkomst, koppeling, werkwijze en controles |

## Afzonderlijk ontwikkelen

De pagina’s hebben eigen scripts en stijlen in `assets/`. Afbeeldingen, lettertypen en oorspronkelijke raceverslagen worden alleen gelezen. Home en individuele raceverslagen verwijzen naar de bestaande site; de drie ontwikkelmodules verwijzen onderling naar elkaar.

`clone-manifest.json` bevat de oorspronkelijke hashes van bronpagina’s en bronassets. De regressietest controleert dat deze bestanden onveranderd zijn. De publicatiebouwer bewaart de drie ontwikkelpagina’s, hun eigen assets, rekenuitleg en alle dynamisch geladen gegevens bij volgende automatische race-updates. De gegenereerde gegevens staan in de gecontroleerde GitHub Release-momentopname; code, methoden en tests staan in de repository. Op verzoek is de coureursmodule vervolgens de reguliere `analysis-lab.html` geworden. De Races- en GOAT-ontwikkelroutes blijven afzonderlijk.

## Gegevens en opbouw

Aanvulling bij de promotie op 18 oktober: bij De metronoom staat opnieuw de veldvergelijking met horizontale violins voor alle deelnemers aan de geselecteerde races. Iedere geschikte schone ronde in vrije lucht telt mee. De bijbehorende detailgroepen worden geladen voordat het overzicht verschijnt; bij een andere coureur of periode worden ontbrekende groepen aangevuld. Het eigen circuitoverzicht blijft daaronder uitklapbaar. Deze aanvulling hoort bij de reguliere coureursmodule.

De bouw leest de bestaande coureurswaarnemingen en het al bewaarde volledige F1DB-archief, controleert de archiefhash en voegt gecontroleerde basisfeiten en afgeleide lagen toe. Er is geen tweede onafhankelijk onderhouden coureursdatabase.

- `data/profiles.js`: gedeelde kern, compacte kolomtabellen, eigen startwaarnemingen en referenties.
- `data/details/`: individuele ronderangen, teamgenootmetingen en specialismemetingen in kleine groepen. Alleen benodigde groepen worden geladen.
- `data/facts/`: racefeiten en besluiten, eveneens op aanvraag.
- `data/strategy.js`: pitcycli en behouden pitklokken; pas laden wanneer de strategie wordt geopend.
- `data/models.js`: uitsluitend voor GOAT, zonder dat ieder coureursprofiel dit moet downloaden.
- `data/findings.js` en `atlas.js`: compacte vooraf berekende racebevindingen en atlascellen.
- `data/registry.json.gz`, `build-report.json`: versies, regels, hashes, aantallen, budget en opleverstatus.
- `data/starter-metrics.csv`: de drie vastgelegde Starter-maten voor alle 817 profielen, inclusief ontbrekende dekking en definitieversie. Een lege maat is geen nul.

Alle gegevensbestanden hebben een overeenkomstige verliesloze JSON.gz-versie. Via HTTP gebruikt de detaillezer deze gecomprimeerde bestanden; bij lokaal openen of ontbrekende browserondersteuning gebruikt hij de bijbehorende scriptversie. Beide bevatten dezelfde waarden. Alle 639.012 bewaarde ronderangen blijven aanwezig; een extra vlag bepaalt alleen de geschiktheid bij onvoldoende velddekking.

Afwijkende bekende grid- en eindposities uit de twee bronnen worden afzonderlijk geregistreerd. De betrokken fase blijft tot verificatie buiten scores en referenties. Timingbewijs vult ontbrekende startregistraties bij een latere diskwalificatie aan; gedeelde auto’s blijven buiten individuele fasescores.

De gedeelde analytische gegevens blijven onder **64.000.000 ongecomprimeerde bytes**. Compressie, export en reconstructie worden getest. Dit is een ontwikkelbudget; de uiteindelijke websitebundel moet bij publicatie opnieuw aan de afzonderlijke grens van 900.000.000 bytes worden getoetst.

## Reproduceerbaar bouwen

Vanaf de projectmap, met Python/Numpy en Node beschikbaar:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=src \
  .venv/bin/python _development/research/build.py
.venv/bin/python -m pytest tests _development/tests -q
python3 -m http.server 8798 --bind 127.0.0.1
node _development/tests/browser.cjs
```

Als Node of Playwright niet op het standaardpad staat: stel `PHASE2_NODE` in op de Node-runtime en `NODE_PATH` op de bijbehorende modules. De browsercontrole verwacht de lokale server op poort 8798. Controlebestanden staan onder `storage/phase2-clones-20261017/`.

De bouw is lokaal en publiceert niets. Weer wordt als afzonderlijke gedateerde momentopname bewaard; ontbrekende verwachtingen worden niet ingevuld. Voorspellingsarchieven in `forecast-archive/` worden niet achteraf overschreven.

## Onderzoek is geen gevalideerde eindconclusie

Het netwerkmodel heeft zijn onafhankelijke prestatietoets nog niet gehaald. Daarom verschijnt geen algemene of tijdperkonafhankelijke GOAT-score. De profielkaart is verkennend. Het vooruitblikmodel heeft een terugtest en een vooraf opgeslagen onderzoeksscenario, maar nog geen afgeronde prospectieve kalibratie. Er zijn geen gevalideerde openbare winstkansen.

De strategieatlas beschrijft gemeten kandidaatcycli, inclusief ongunstige uitkomsten. Het rekenscenario toont een tijdsbalans onder expliciete aannames, geen bewezen causale tegenstrategie. Aanvullende analyses van aanvalskansen, weer en dynamische autocorrectie blijven afhankelijk van de in het plan gestelde gegevens- en validatievoorwaarden.

Zie [uitvoering en resterende onderzoekspoorten](IMPLEMENTATION.md) voor het overzicht per planstap.


## Hercontrole uitval en incidenten

Zie [de volledige verantwoording](INCIDENT-CHECK.md) en het [wijzigingsregister](incident-audit.json). De normalisatie onderscheidt uitval, finish, niet gestart, diskwalificatie, onzekerheid en gedeelde auto’s. Gezamenlijke besluiten, andere betrokkenen en echte strafontvangers zijn afzonderlijk vastgelegd. Besluiten gebruiken een gedeeld kolomschema; de compressie en reconstructie blijven verliesloos.

Voer na het afronden van de bouw ook `node _development/tests/incidents-browser.cjs` uit. Deze controle behandelt Rosberg en Hamilton in 2016, verschillende strafrollen, collectieve tijdstraffen, oudere profielen, periodefilters, NL/EN, mobiel en lokaal openen. Wacht met gegevenscontroles tot de bouw gereed is, zodat gegevens en hashregister bij dezelfde bouw horen.

## Reguliere coureursmodule

`f1_analysis.driver_release.promote` maakt de gecontroleerde coureursmodule beschikbaar via `analysis-lab.html`; bestaande links en bladwijzers blijven werken. De productienavigatie verwijst naar Home, Races en GOAT op hun reguliere routes. De coureursmodule behoudt de eigen gedeelde scripts en analytische bestanden onder `_development/`, zodat de andere modules hun eigen presentatie houden. De pagina heeft een expliciete releasemarker en geen `noindex`-instructie.

De oorspronkelijke coureurspagina is verliesloos bewaard als `_development/source/legacy-drivers.html.gz` en wordt tegen de oorspronkelijke SHA-256 in `clone-manifest.json` gecontroleerd. Deze archiefkopie wordt gebruikt door de integriteitscontroles, de datacollectie en de onderzoeksbouwer; de lege bootstrap van de nieuwe pagina is geen gegevensbron. Het archief reist met de gecontroleerde Release-momentopname en wordt niet als tweede werkdatabase geladen in de browser.

Automatische publicaties behouden de nieuwe presentatie en alle dynamische detailgroepen. Ze bouwen de oude coureursinterface niet opnieuw over de nieuwe heen. De analytische fase 2-momentopname wordt afzonderlijk vernieuwd met de onderzoeksbouwer; reguliere race-updates zijn geen herberekening van alle onderzoeksmodellen.

## Lokale uitlegpagina · 19 oktober 2026

De onderdelen **Berekening en interpretatie** zijn van de reguliere coureurspagina naar `uitleg-start-en-raceonderzoek.html` verplaatst. De pagina bevat negen onderwerpen: start, racevervolg, kwalificatie, vrije-baantempo, rondetijdrang, regelmaat, bandenbehoud, pitvensters en opwarming. De oorspronkelijke plekken verwijzen rechtstreeks naar het passende onderwerp. Rijder- en periodegebonden datadekking blijft in het profiel. De kwalificatietoets leest de actuele bewaarde metadata op aanvraag; de hulp laadt geen individuele coureursdetails. De analyse- en rekenfuncties zijn ongewijzigd. Deze verplaatsing is alleen lokaal uitgevoerd.

## Pitwall briefing · contextuele uitleg

De info-iconen naast sectie- en grafiektitels openen een blijvende, scrollbare popup. Sluiten kan met de sluitknop, Escape, de knop onderaan of een klik buiten het venster; er is geen afteltimer. De kop en bediening blijven staan terwijl alleen de uitleg scrolt. De achtergrond is een gegenereerde pitwallfoto met de moderne Zandvoort-vorm uit de officiële FIA-kaart als referentie. Prompt en herkomst staan in `assets/help/pitwall-briefing-v1.json` en het bijbehorende promptbestand.

`assets/driver-briefings.js` rendert dezelfde tekst en voorbeelden in de popup en op de uitlegpagina. Elf onderwerpen zijn beschikbaar, inclusief het teamgenootduel en de pitbalans. De eerder bewaarde model- en scoreuitleg staat afzonderlijk in `assets/driver-help-archive.js` en wordt alleen bij het openen van uitleg geladen. De popupbesturing is `assets/driver-info.js`; vormgeving staat in `assets/driver-info.css`.

De compacte voorbeeldverdelingen in `assets/help/examples.js` zijn echte waarnemingen uit vaste, expliciet vermelde perioden. Ze veranderen niet met de paginaselectie. Bronhashes, gebruikte races en eventuele schattingen zijn bewaard. Voorbeelden zijn lesmateriaal, geen GOAT-ranglijst; bij minder dan tien gedeelde races wordt onvoldoende zekerheid expliciet vermeld. Massa/Ricciardo tonen het startvoorbeeld vanaf P5; de meeste andere voorbeelden gebruiken Verstappen/Pérez op dezelfde races in 2021–2024. Hun pitbalansvoorbeeld is een rechtstreeks duel, met gespiegeld teken en zonder dubbele telling. Herbouw met `node _development/research/build_help_examples.cjs`.

De kwalificatiecurve gebruikt een Gaussisch gewogen gemiddelde in racevolgorde (schaal vijf races, maximaal vijftien aan elke kant). Alleen de curve gebruikt een interne tijdpositie; de jaarpunten, medianen en violins blijven op hun oorspronkelijke plaats. De indicatieve puntgewijze 95%-band gebruikt 400 bootstrapherhalingen van blokken van drie kwalificaties. Geschatte Q3-tijden tellen als punten mee, zonder hun extra schattingsfout in deze band. De positie-assen op de x-as stoppen bij P22; verborgen historische waarnemingen blijven beschikbaar voor de berekeningen en samenvattingen.

Praktijkcontroles: `node _development/tests/pitwall-browser.cjs`, `node _development/tests/qualifying-bridges-browser.cjs` en de kwalificatierekencontroles in `_development/tests/test_qualifying_years.py`.

### Vast concept: uitleg bij iedere analyse (19 oktober 2026)

Iedere analysekaart, sectie en grafiek heeft een paars-cyaan infoknop bij de titel. Deze opent **Pitwall briefing**, zonder timer. Alleen de inhoud scrollt; kop en sluit-/terugknoppen blijven staan. Sluiten kan ook via Escape en de achtergrond, waarna focus en paginascroll worden hersteld. De knop naast een topkaart staat buiten de kaartknop en verandert de selectie niet.

Popup en helppagina delen `driver-briefings.js`. Beschrijf betekenis, eenheid, noemer, selectie, berekening, interpretatie, dekking en beperkingen. Voeg een controleerbaar voorbeeld toe met echte coureurs, expliciete periode en aantallen. Vergelijkingen leggen een specifieke uitkomst uit; dekking of uitvalcategorie bewijst geen rijvaardigheid of schuld. Onbekend blijft onbekend. Dezelfde regels staan in de zelfstandige stijlgids.

Voorbeelden hergebruiken via `driver-example-charts.js` de bestaande productie-renderers, inclusief asrichting, transformatie, afkapping, punten, violins, curve, modelband en legenda. Geen afzonderlijke histogramtekening, verzonnen illustratie of zelfbedachte as. Bewaar race-, jaar- en circuitverbanden. Assen blijven vaststaan; de twee vergelijkbare voorbeeldgrafieken scrollen samen. Alle voorbeeldgegevens worden pas bij het openen van uitleg geladen. De oorspronkelijke filters van het profiel blijven intact.

`_development/research/build_help_examples.cjs` bouwt de vast begrensde voorbeelden uit bewaarde gegevens. Het voorbeeldbestand bewaart bronhashes, echte rijen, racecontext en seizoensfeiten. Test bij nieuwe onderwerpen zowel echte data/assen als gelijkheid van popup- en helppaginatekst, mobiel gedrag, scrollen en sluitbediening. Een nieuw analyseonderdeel is pas klaar met deze uitleg op beide plaatsen.

De kwalificatietrend gebruikt een Gaussisch venster op de chronologische racevolgorde (sigma vijf waarnemingen, maximaal vijftien aan weerszijden) met robuuste lokale Huber-locatie. De gewogen mediaan initialiseert de locatie; de gewogen MAD bepaalt de schaal met ondergrens 0,05 seconde of 0,5 positie. Huber-afkapping gebruikt 1,5 maal de robuuste schaal en zes iteraties. De blokbootstrap past dezelfde robuuste schatter toe. Dit voorkomt dat één extreem trage kwalificatie een kunstmatige winterdip domineert. Alle oorspronkelijke punten, violins, kwartielen en jaarmedianen blijven ongewijzigd; een verslechtering over veel races blijft zichtbaar. Het is een beschrijvende trend, geen causale of voorspellende analyse.
