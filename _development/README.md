# Fase 2 · lokale ontwikkelomgeving

Deze omgeving voert het [totaalplan](../documents/fase-2-onderzoeks-en-ontwikkelplan.md) uit op afzonderlijke ontwikkelpagina’s. De oorspronkelijke brongegevens en scripts blijven behouden. Publicatie van deze afzonderlijke pagina’s is op 18 oktober 2026 expliciet toegestaan.

| Pagina | Inhoud |
|---|---|
| [Coureurs](../coureurs_2.html) | Eigen carrièrefeiten, zes specialismen, start en racevervolg, teamgenootduel, regelmaat, incidenten en dekking |
| [GOAT](../goat_2.html) | Beschrijvende vergelijking, gedeelde context, netwerkonderzoek, profielkaart en modeltoetsen |
| [Races](../races_2.html#phase2-race-research) | Bestaande catalogus plus racebevindingen, strategieatlas, rekenscenario en gedateerde weersbron |
| [Rekenuitleg](uitleg-start-en-raceonderzoek.html) | Bewaarde uitleg van modelcurve, onzekerheid en start-/racescores in NL en EN |
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
