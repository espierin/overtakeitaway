# Analysemodules · ontwikkeling en productie

## Productieversie — 19 oktober 2026

De publieke routes zijn `analysis-lab.html`, `goat.html` en `races.html`. De vroegere `_2.html`-routes zijn doorverwijzingen die query en fragment behouden. De bronopmaak voor Coureurs en GOAT staat nu in `templates/drivers.html.txt` en `templates/goat.html.txt`; `driver_release` en `goat_release` bouwen daarvan de reguliere pagina’s. Het onderzoeksbouwscript werkt deze templates bij. Technische bestanden onder `_development/assets` en `_development/data` blijven gedeelde afhankelijkheden; dit zijn geen aparte openbare versies.

De automatische ontwikkelintroducties zijn verwijderd. Inhoudelijke helpvensters blijven op aanvraag werken en verwijzen naar de reguliere `uitleg-start-en-raceonderzoek.html`. De oude help- en datacollectieroutes sturen door. De exacte voormalige GOAT-pagina blijft als backup behouden.

GOAT opent standaard met Verstappen, Hamilton, Fangio en Senna. Jaarcurves gebruiken standaard jaren sinds debuut; een expliciet opgeslagen kalenderjaarstand blijft behouden. De PCA staat direct onder de selectie en gebruikt standaard zes kenmerken, inclusief typische kwalificatiepositie en geschatte startplek voor positiewinst. Alle voldoende gemeten coureurs blijven de berekening bepalen. Ontbrekende profielen worden uitsluitend gemeld voor geselecteerde coureurs, met nummer, kleur en naam; de lijst met overige ontbrekende profielen wordt niet getoond. Opgeslagen persoonlijke URL-keuzes blijven leidend.

De onderstaande beschrijving van de afzonderlijke ontwikkelroutes is historische documentatie; de productieroutes hierboven vervangen deze navigatie.

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

`clone-manifest.json` bevat de oorspronkelijke hashes van bronpagina’s en bronassets. De regressietest controleert dat deze bestanden onveranderd zijn. De publicatiebouwer bewaart de drie ontwikkelpagina’s, hun eigen assets, rekenuitleg en alle dynamisch geladen gegevens bij volgende automatische race-updates. De gegenereerde gegevens staan in de gecontroleerde GitHub Release-momentopname; code, methoden en tests staan in de repository. Op verzoek is de coureursmodule vervolgens de reguliere `analysis-lab.html` geworden. De Races-ontwikkelroute blijft afzonderlijk; de nieuwe GOAT-module is op 19 oktober ook naar de reguliere route overgezet (zie hieronder).

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

De voorbeeldgrafieken in popup en helppagina worden op 40% weergegeven. De twee coureurs staan direct onder elkaar, met gelijke assen en gekoppeld horizontaal scrollen. Gedeelde legenda en schaalnotities staan pas onder de vergelijking. Bij kwalificaties staan eerst beide positiegrafieken bij elkaar en daarna beide afstand-tot-polegrafieken. De hoofdgrafieken behouden hun normale afmetingen.

De kwalificatiecurves krijgen aanvullend een Gaussische verzachting op de interne seizoen-as (sigma 0,3 seizoen, venster ±1,2 seizoen), afzonderlijk per aaneengesloten reeks gemeten jaren. Dezelfde bewerking wordt op elk van de 400 blokbootstrapfits toegepast voordat de 2,5%- en 97,5%-grenzen worden bepaald. Zo volgen lijn en band dezelfde vloeiende schatter, terwijl alle punten, jaarmedianen, kwartielen en violins intact blijven.

### Opgeslagen coureurcurves voor GOAT

`assets/driver-curve-snapshots.js` legt vier curves vast met de bestaande productie-engines, zonder een nieuwe kwaliteitsscore te berekenen:

| Sleutel | Begin / x-as | Uitkomst / y-as |
| --- | --- | --- |
| `start` | Startpositie | Positiewinst na ronde één |
| `race` | Positie na ronde één | Positiewinst tot de finish, alleen bevestigde finishers |
| `qualifying_position` | Seizoen | Kwalificatiepositie |
| `gap_to_pole` | Seizoen | Afstand tot pole in seconden, inclusief herkenbare sessieschattingen |

Herbouw met `node _development/research/export-driver-curves.cjs --workers 4`. De standaard is de volledige beschikbare datasetperiode. Met `--from-year 2021 --to-year 2024` ontstaat een afzonderlijke periodeversie. `--drivers max-verstappen,lewis-hamilton` maakt een afzonderlijke selectie; `--output` kan een andere map kiezen. Periode- of circuitselecties vereisen opnieuw berekenen: jaargemiddelden of delen van een bestaande loopbaancurve middelen levert niet dezelfde fit op.

De gegenereerde gegevens staan onder `data/driver-curves/<beginjaar>-<eindjaar>/`. `index.json` verwijst pas na een volledige generatie naar een onveranderlijke versie met `manifest.json` en één verliesloos gecomprimeerd JSON-bestand per coureur. Het manifest bevat bron- en codehashes, meetdekking, beschikbaarheid, bestandsgrootten en controlehashes. De export kan worden hervat en hergebruikt reeds gecontroleerde bestanden van dezelfde versie. Oude versies worden niet overschreven.

De bestanden bevatten curvepunten op de oorspronkelijke rekenschaal, 95%-banden, support-/extrapolatiemarkeringen, groepen met individuele racewaarnemingen, medianen en kwartielen, afkappingen en astransformaties. Positiewinstcurves bewaren uitsluitend zichtbare curvepunten tot en met P22; verborgen historische waarnemingen blijven in de groepen bewaard zoals bij de huidige berekeningen. Kwalificatieruns blijven gescheiden over lege jaren. Ontbrekende of onvoldoende onderbouwde curves krijgen een expliciete status, geen nulcurve. Een geschatte Q3-tijd blijft als schatting herkenbaar.

De GOAT-pagina tekent de opgeslagen `fit.runs` met gedeelde assen. Iedere rij in een run volgt de bijbehorende `fit.columns`; er wordt bij opslag niet afgerond. Browser en Node kunnen circa 10^-14 verschillen in elementaire berekeningen, zonder zichtbaar verschil. Controleer exports daarom op numerieke gelijkheid binnen 10^-10, terwijl observaties en selecties exact gelijk moeten zijn. De proefcontrole gebruikt Verstappen, Hamilton en Ricciardo tegenover de live berekening op de lokale rijderspagina. Het is geen tussen-tijdperken gecorrigeerde ranglijst: gelijke assen maken curves vergelijkbaar als beschrijving, maar maken auto, kalender en omstandigheden niet gelijk.

Bij start en racevervolg zijn de GP-grenzen analytische, puntgewijze modelgrenzen; de vermelde 800 trekkingen behoren tot de overige modelberekeningen. Bij de terugvalfit worden 600 bootstrapherhalingen gebruikt. De kwalificatieband wordt bepaald uit 400 blokbootstrapfits met dezelfde Gaussische verzachting als de witte curve. Deze verschillende onzekerheidsdefinities blijven in de snapshot benoemd.

Deze curvebestanden vallen onder de gegenereerde `_development/data`-opslag. Neem bij een publicatie de complete versie met haar `index.json` en manifest mee in de gecontroleerde website-/Releases-snapshot; alleen de broncode naar Git sturen publiceert de gegenereerde curves niet. De GOAT-interface leest een compacte verliesloze bezorgkopie van deze exacte fits; de oorspronkelijke waarnemingen blijven in dit archief bewaard.

Boven de curve van het racevervolg worden de drie kaarten met kansgecorrigeerde curvebalans, racescore en winstgrens niet meer getoond. Alleen die presentatie is verwijderd: de berekeningen, referentieselecties, onzekerheidsmarges en brongegevens blijven behouden voor GOAT via `driverQualities.startComparison` (met `raceObservation`), `starterCurve` en `starterModel`. De opgeslagen curvebestanden blijven ongewijzigd.

### Vaste interactiestijl voor knoppen en kaarten

Gebruik de gedeelde `site-theme.css` voor hover, klikfocus, toetsenbordfocus en bestaande geselecteerde toestanden: accentkleurige rand, lichtere buitenomlijning van 2 px en een subtiele gloed. Knoppen krijgen ook een donkere vulling in hun accentkleur. Interactieve kaarten behouden hun achtergrondbeeld en eigen accentkleur. Gewone informatiepanelen krijgen geen hoverselectie. Hover wijzigt nooit de selectie of de gegevens. Actieknoppen gebruiken focus; echte toggles gebruiken `aria-pressed` of `aria-selected` voor een blijvend herkenbare toestand. Maak geen kunstmatige toggle van een navigatiekaart. Behoud focus na opnieuw opbouwen van de aangeklikte coureur- of kwaliteitskaart. Compacte coureurrijen gebruiken een binnenomlijning zodat naburige rijen niet worden bedekt. Uitgeschakelde bediening krijgt geen hovergloed. De stijlgids bevat werkende voorbeelden; de drie gedeelde CSS-kopieën blijven gelijk.

### Vaste loopbaanparameters en PCA voor GOAT

De profielkaart op `goat_2.html` gebruikt één samengevoegd loopbaanprofiel per coureur. Seizoenen zijn geen losse stippen meer. `assets/goat-pca.js` berekent een gestandaardiseerde beschrijvende PCA op vier breed beschikbare feiten: gemiddelde relatieve gridpositie, gemiddelde relatieve raceklassering, zeges per bekende uitslag en rijdende finishes per bekende finishstatus. Posities zijn `(positie − 1) / (veldgrootte − 1)`. Elke race telt eenmaal binnen zijn loopbaan; elke coureur telt eenmaal bij het leren van de PCA-assen. Ontbrekende feiten, onzekere gedeelde auto’s, tegenstrijdige bronposities en niet-starts worden expliciet behandeld. Geen imputatie, geen opvullen met nul en geen voorgesteld universeel kwaliteitscijfer.

De volledige datasetperiode vormt de vaste loopbaanscope van deze PCA. De periode/raceset bovenaan blijft voor de overige GOAT-vergelijkingen gelden. Andere coureurs kiezen verandert alleen de nadruk: neutraalgrijze achtergrondpunten, uitsluitend de gekozen coureurs in hun laatste geregistreerde teamkleur en een verbindingslijn naar een nummer–kleur–code–naamlabel. De labels staan buiten de puntenwolk en worden verticaal uit elkaar gehouden. Niet te plaatsen profielen blijven eenmaal zichtbaar in een aparte strook die nadrukkelijk geen PCA-as is. Laat punten op hun echte positie, ook als ze samenvallen. Verander de assen niet bij alleen een andere highlightselectie.

Met ‘PCA-parameters kiezen’ kunnen opgeslagen specialismen worden toegevoegd. De kaart gebruikt uitsluitend complete profielen voor de gekozen parameters en toont hoeveel meetwaarden per parameter beschikbaar zijn. Een ander parameterpakket kan het cohort en de assen veranderen; de coureurselectie kan dat niet. Sterk gecorreleerde parameters tegelijk aanvinken kan één eigenschap extra gewicht geven. De basiskaart en de uitgebreide PCA blijven beschrijvend en corrigeren niet volledig voor auto, tijdperk, betrouwbaarheid of kansen.

Genereer alle vaste waarden met `node _development/research/export-goat-metrics.cjs`. `driver-goat-metrics.js` hergebruikt de productie-engines. De export bewaart per coureur startscore, gecorrigeerde startcurvebalans en startwinstgrens; racescore, gecorrigeerde racecurvebalans en racewinstgrens; mediaan van het teamgenoottempo; mediane vrije-lucht-ronderang en een vast veldpercentiel; mediane pitwinst per race, per tegenstandervergelijking en per kandidaatcyclus. Het veldpercentiel is `100 × (1 − (rang − 1) / (veldgrootte − 1))`, gepoold over alle eigen schone vrije-luchtronden. Het hangt niet af van welke andere rijder geselecteerd is. Het bestaande veldvergelijkingsblok in het profiel blijft bewust de races van de geselecteerde rijder volgen.

Pitwaarden voor GOAT gebruiken een vaste definitie: evenveel stops, afgeronde pitprogramma’s, zonder geregistreerde SC/VSC; de racewaarde is de mediaan van de racemedianen. De kandidaatcycluswaarde gebruikt alle geaccepteerde eigen kandidaatcycli en is een aparte parameter. Beide hebben seconden als eenheid, maar verschillende meeteenheden en dekking. Een onbekende grens of ontoereikende curvebalans krijgt `null` met status en wordt geen nulscore.

De export schrijft onveranderlijke versies onder `data/goat-metrics/<begin>-<eind>/<bronrevisie>/`, één gzip-JSON per coureur en een manifest met bron-/codehashes. Elk record bevat waarden, dekking, onzekerheidsmarges waar beschikbaar, methoden, pitseizoenen, de vier basiskenmerken en de coördinaten van de basis-PCA. `index.json` verwijst naar de afgeronde versie. De kleine `data/goat-metrics.js` en lossloze gzip-variant leveren dezelfde parameters aan de pagina. Gewijzigde brondata vereisen een nieuwe export; oude versies blijven bewijs. De racescore gebruikt exact `startComparison` met `raceObservation`, inclusief 600 race-bootstrapherhalingen. Winstgrenzen komen uit de eerder vastgelegde productiecurvebestanden. Bronbestanden en bestaande curve-exporten worden niet veranderd.

### Pitbalans binnen het coureursprofiel

Het coureursprofiel en de strategieatlas zijn samengevoegd. De pitbalans staat na de opwarmer als zelfstandig onderdeel van het profiel. Aanvullende kandidaatcycli staan er direct onder in een uitklapbaar blok; bestaande race- en stopvensters blijven bedienbaar. Oude `tab=strategy`-links openen het profiel en springen naar de pitbalans. De kaart ‘Mediane gemeten tijdwinst per kandidaatcyclus’ staat naast de mediane tijdwinst per race, met expliciet verschillende noemers.

De seizoensgrafiek behoudt alle racemedianen, jaarmedianen en violins. `pitProgrammes.seasonTrend` gebruikt exact `qualifyingYears.trend`: chronologische Gaussische weging met sigma vijf races, robuuste Huber-locatie, extra verzachting met sigma 0,3 seizoen en 400 blokbootstrapherhalingen van drie races. Ontbrekende meetjaren worden niet overbrugd. Dezelfde transformatie en verzachting gelden voor lijn en 95%-band. Methodetekst staat in de gedeelde Pitwall Briefing én op de helppagina; de grafiek zelf heeft een korte legenda. Een geselecteerde rijder wijzigt nooit de opgeslagen vaste waarden van een andere rijder.


### Coureurkeuze en volledige loopbaan (19 oktober 2026)

De doorzoekbare coureurkeuze staat links, de jaarbediening rechts; op smalle schermen staat de coureur boven de jaren. De koppen ‘Coureur’ en ‘Selectiejaren’ zijn boven uitgelijnd. De zoekbediening en jaarknoppen zijn even hoog en onder uitgelijnd. De selectie vervangt direct één profiel. De keuzelijst staat alfabetisch op achternaam en doorzoekt naam, aliassen, lettercode en geregistreerde nummers. De bestaande lettertypen blijven behouden, met de volledige loopbaanjaren direct achter de naam.

De selectieperiode filtert **uitsluitend de keuzelijst**, op werkelijk geregistreerde racejaren. Alle profielanalyses en totalen gebruiken steeds de volledige beschikbare loopbaan van de gekozen rijder. Een periodewijziging verwijdert de huidige selectie niet. Valt deze coureur buiten de zoekperiode, dan meldt de bediening dat expliciet; ‘Gebruik loopbaanjaren’ past alleen de zoekperiode aan. Zes kwaliteitskaarten blijven toegang geven tot de analyses. Bij scrollen blijft alleen de compacte coureurstrook met loopbaanjaren zichtbaar.

De gedeelde laadindicator toont de paarse bandenafbeelding ook tijdens het voorbereiden van grafieken. Bij de metronoom toont de veldvergelijking uitsluitend rijders met bruikbare metingen; ontbrekende rijen worden verborgen zonder berekeningen, referenties of volgorde van gemeten rijders te wijzigen. De dekking blijft het aantal gemeten deelnemers tegenover alle geregistreerde deelnemers noemen.

### GOAT als reguliere module en bruikbare circuitgegevens

`goat_2.html` is nu de bron voor de reguliere `goat.html`. De oorspronkelijke pagina staat exact bewaard als `goat-backup-20261019.html` en gecomprimeerd onder `source/legacy-goat.html.gz`, met SHA-256 in `source/goat-release.json`. `f1_analysis.goat_release.promote` controleert het archief, houdt de backup intact en werkt de reguliere pagina bij. Automatische websitebouw behoudt de promotie en neemt de backup mee.

De GOAT-module toont alle opgeslagen parameters met eenheid en dekking, vijf exacte bewaarde curves en eigen rondegegevens per circuitvariant. Alle vaste waarden gebruiken de volledige eigen loopbaan binnen de bronperiode. De aanvullende vergelijking met een gemeenschappelijke raceset blijft apart. De huidige PCA met één vertegenwoordiging per coureur blijft de standaard; extra opgeslagen kenmerken zijn als optionele PCA-parameters beschikbaar.

De PCA-bediening kiest bij een nieuwe opening standaard zes kenmerken: relatieve gridpositie, relatieve raceklassering, zeges per start, finishpercentage, geschatte startplek voor positiewinst en typische kwalificatiepositie. Een expliciete `pcafeatures`-keuze in een opgeslagen URL blijft behouden, ook als die afwijkt van de standaard of leeg is. De basisberekening en opgeslagen bronwaarden zijn ongewijzigd. Alleen coureurs met alle gekozen gegevens krijgen een berekende positie; de overige coureurs blijven afzonderlijk zichtbaar.

De export bewaart ook kwalificatiepositie, afstand tot pole (inclusief herkenbare schattingen), vrije-baantempo, bandenbehoud, opwarming, pitwindow en regelmaat. Per circuit blijven race, seizoen, variant, compound, veldgrootte, ronderang en beschikbare werkelijke milliseconden behouden. Ontbrekende klokken blijven `null`; absolute rondetijden uit verschillende jaren of auto's zijn geen eerlijke snelheidsranglijst. De compacte `delivery/`-kopie combineert per rijder parameters met de originele curvefits. HTTP gebruikt gzip; lokaal openen gebruikt dezelfde gzip-inhoud via een script. De beide kwalificatiecurves en beide positiecurves hebben gekoppeld horizontaal scrollen. Bronwaarnemingen worden niet verplaatst of opnieuw gefit.


### Bewaarde pitbalanscurve en niet-lineaire secondenas

De pitbalans per seizoen gebruikt een symmetrisch logaritmische as: `sign(t) × ln(1 + |t|)` met t in seconden, nul centraal en winst bovenaan. Positieve en negatieve waarden krijgen evenveel ruimte. Punten, kwartielen, curve en 95%-band gebruiken dezelfde omzetting; de bronwaarden en alle berekeningen blijven in echte seconden. De as omvat ook de modelband en kapt geen waarnemingen af. Dezelfde functie verzorgt de as bij de coureurs en bij GOAT.

De vaste GOAT-export bewaart vanaf deze versie ook `pit_curve`: iedere racemediaan met race-id en datum, jaarstatistieken, exacte vloeiende fit, bootstrapband, parameters, asspecificatie en beschikbaarheid. De standaardfilters zijn evenveel stops, afgeronde pitprogramma’s en zonder geregistreerde SC/VSC. De pitbalanscurve verschijnt als vijfde curvevergelijking bij GOAT. De twee aparte PCA-kenmerken blijven `pit_race_gain` (mediaan van racemedianen) en `pit_cycle_gain` (mediaan over geaccepteerde kandidaatcycli); ze hebben eigen dekking en krijgen geen dubbel toegevoegd duplicaat. Voor George Russell zijn de huidige ongeronde waarden respectievelijk `3.50325` s (70 races) en `0.0605` s (200 cycli in 81 races).

Het manifest controleert ook de gzip- en scriptbestanden voor browserbezorging. Iedere bezorgkopie bevat dezelfde ongeronde parameters en fitwaarden als het archief. De oorspronkelijke vier curvearchieven blijven ongewijzigd.

### GOAT: tijdas en herkenbare curvelabels

Bij ‘De bewaarde curves vergelijken’ schakelt de bezoeker tussen kalenderjaren en jaren sinds het debuut. Voor kwalificatiepositie, afstand tot pole en pitbalans wordt uitsluitend de x-coördinaat verschoven: `jaar − eerste geregistreerde loopbaanjaar + 1`. Verstappen 2015 en Fangio 1950 worden dus beide jaar 1. Pauzejaren tellen mee; een rijder die na een onderbreking terugkeert, begint niet opnieuw. Ontbrekende meetjaren blijven leeg. De start- en racecurves blijven per positie weergegeven. De gekozen stand staat in `curveyears=career|calendar` in de URL. Opgeslagen fits, onzekerheidsbanden, parameters en PCA-uitkomsten veranderen niet.

Nummer-kleur-naamlabels staan bij het begin als daar ruimte voor is. De plaatsing controleert vanaf 20 oktober ook de volledige getekende gebogen lijnen, inclusief de eigen curve en die van de andere coureurs. Afzonderlijke meetreeksen blijven afzonderlijk: over lege jaren wordt geen lijn verzonnen voor de botsingscontrole. Meerdere labelopstellingen worden samen beoordeeld, zodat een vroeg geplaatst label de volgende niet vastzet. Korte verbindingslijntjes, vrije beginplekken en weinig uitsteken voorbij de eigen curve hebben voorrang. Labels blijven binnen het tekenvlak; er komt geen extra labelkolom rechts. De spreiding is stabiel voor dezelfde selectie. Lijnen met dezelfde of sterk verwante kleurtint krijgen verschillende streeppatronen; dit geldt ook voor donker- en lichtblauw. Legenda en curve gebruiken hetzelfde patroon. Dit verandert geen opgeslagen curve, meetwaarde of PCA-positie.

De parameterlijst onder ‘Alle eigenschappen naast elkaar’ is standaard ingeklapt. De grafische vergelijking blijft zichtbaar; de oorspronkelijke tabel, meetdekking en toelichting zijn via ‘Parameterlijst’ te openen.

Een verbindingslijntje en eindbolletje worden uitsluitend getekend bij een herkenbaar eigen stuk curve, met minstens acht beeldpunten afstand tot andere curves. De zoekstap kan voorbij een gedeeld beginstuk verplaatsen. Vallen curves overal samen, dan blijven hun labels zichtbaar maar worden het misleidende lijntje en bolletje weggelaten.

### Begrijpelijke tekst en gedeelde uitleg

Gebruik op de website eerst de vraag, de eenheid, wat een hoger of lager getal betekent en de feitelijke dekking. Gebruik herkenbare voorbeelden. Een middelste waarde is geen gemiddelde; een meetresultaat bewijst geen oorzaak en een positie gewonnen door uitval is geen aangetoonde inhaalactie. Onzekerheid over de curve en de spreiding van racepunten zijn verschillende zaken. Technische definities, filters, formules en beperkingen horen bij de gedeelde Pitwall Briefing en uitlegpagina’s.

`src/f1_analysis/assets/plain-language.json` bevat de gecontroleerde tweetalige formuleringen. `f1_analysis.readability` bouwt één gedeelde presentatielaag; deze verandert alleen zichtbare tekst, nooit bronwaarden, formuliervelden of grafiekcoördinaten. Officiële broncitaten en technische uitleg worden behouden. `uitleg.html` biedt de algemene leeswijzer en verwijst naar de detailmethoden. Herbouw de leeswijzer via `f1_analysis.help.build` en voer `_development/research/review_site_copy.py --apply` uit voor bestaande pagina’s. Het controlerapport telt pagina’s, controleert ingebedde gegevens vóór en na de bewerking en houdt presentatiehashes bij. Bewaar historische backups ongewijzigd.

### Gemini via GitHub Actions

`goat-ai.js` en `_development/research/goat-ai-brief.cjs` gebruiken dezelfde aanvraagbouwer. De browser en Actions moeten voor dezelfde selectie exact dezelfde SHA-256 van de prompt produceren. De vaste loopbaanbron, verschillende perioden, ontbrekende gegevens, de niet-geslaagde netwerktoets, waarnemingsaantallen en begrensde curves reizen mee. De AI mag alleen een uitdrukkelijk voorlopige favoriet kiezen; ontbrekende data en PCA-assen mogen geen kwaliteitsscore worden.

De workflow `goat-gemini.yml` gebruikt uitsluitend het GitHub-secret `GEMINI_API_KEY`; er staat geen API-sleutel of GitHub-token in de website. Standaardmodel is `gemini-3.8-flash`, te wijzigen via repositoryvariabele `GEMINI_MODEL`. Gratis quota worden door Google bepaald; er is geen automatische overstap naar een ander model wanneer een limiet of fout optreedt. Alleen de bestaande bibliotheken en één begrensde modelaanvraag zijn nodig.

De standaardselectie wordt na een geslaagde publicatie gecontroleerd. De beheerder kan ook `workflow_dispatch` gebruiken of vanuit GOAT de vooraf ingevulde GitHub-aanvraag indienen. Issues van onbevoegde bezoekers worden niet uitgevoerd. Alleen gevalideerde rijdercodes, circuitcodes, periode en taal worden gelezen; vrije issue-tekst wordt nooit als code of extra prompt uitgevoerd.

Antwoorden worden op de aparte branch `goat-ai-results` onder `results/<prompt-sha256>.json` bewaard, met model, bronversie en datum. `index.json` maakt ze opvraagbaar. De website toont alleen een antwoord waarvan de prompt-hash exact overeenkomt; een andere selectie of gewijzigde bron krijgt geen oud oordeel. Dezelfde aanvraag gebruikt het bewaarde antwoord zonder nieuwe Gemini-aanroep. AI-tekst wordt als gewone tekst ontsmet weergegeven. Het antwoord is openbaar, net als de gebruikte F1-cijfers. De originele bronnen, fits en racearchieven worden niet aangepast.
