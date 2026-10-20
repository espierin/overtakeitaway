> Website: https://espierin.github.io/overtakeitaway/
> Repository: https://github.com/espierin/overtakeitaway

# Formula 1 Statistics

Er is één productieversie: [Coureurs](https://espierin.github.io/overtakeitaway/analysis-lab.html), [GOAT](https://espierin.github.io/overtakeitaway/goat.html) en [Races](https://espierin.github.io/overtakeitaway/races.html). Oude `_2.html`-adressen sturen door en behouden de selectie uit de URL. De ontwikkelintroducties zijn verwijderd; de uitlegvensters blijven beschikbaar. Zie [_development/README.md](_development/README.md) voor opbouw, methoden, tests en het gegevensbudget.

## Historisch archief / Historical archive

De races van 1950–2019 zijn eenmalig aangevuld met F1DB (CC BY 4.0), de f1resultsdatabase-compilatie (ODbL 1.0; STATS F1, Formula1.com en MotorsportStats), oorspronkelijke FIA-documenten, Pirelli-verslagen en gedateerde kleurreferenties. Verdwenen FIA-documenten zijn waar beschikbaar via de Wayback Machine opgeslagen met oorspronkelijke URL, opnamedatum en SHA-256. Bronbestanden, supplementen, controlelogs en de historische database staan in `analyses/sources/historical/` en het gedeelde GitHub-bronarchief. `historical_backfill.apply_retained` hergebruikt deze gegevens bij latere builds zonder ze opnieuw op te halen.

The 1950–2019 races have been supplemented once using F1DB (CC BY 4.0), the f1resultsdatabase compilation (ODbL 1.0; STATS F1, Formula1.com and MotorsportStats), original FIA documents, Pirelli releases and dated colour references. Available Wayback copies retain the original URL, capture timestamp and SHA-256. Original source files, supplements, audit logs and the historical database are retained in `analyses/sources/historical/` and the shared GitHub source archive. Future builds reuse them through `historical_backfill.apply_retained` without retrieving them again.

`coverage-report.html` beschrijft de werkelijke dekking in beide talen. Bestaande uitslagen en metingen blijven behouden; bronverschillen staan in het controlelog. Gedeelde auto’s zonder vastgelegde rijderwissel, onbekende privé-inschrijvingskleuren en ontbrekende telemetrie worden niet ingevuld met schattingen. Rondeposities zijn geen inhaaltelling.

`coverage-report.html` documents actual coverage in both languages. Existing results and measurements are retained; source disagreements remain in the audit log. Untimestamped shared-car handovers, unknown private-entry colours and missing telemetry are not replaced by estimates. Lap positions are not overtaking counts.

Lokaal Python-programma voor controleerbare Grand Prix-analyses in het Nederlands, vanaf 2023. Geen websitehosting, accounts of betaalde AI-API nodig. OpenF1 is de timingbron; openbare aanvullende bronnen worden geregistreerd. F1gures biedt openbare sitebestanden, geen door ons vastgestelde gedocumenteerde API; bij onbereikbaarheid werkt de rest en is expliciete import mogelijk.

## Installatie

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
```

In deze workspace is dit al uitgevoerd. Start vanuit de projectmap. Met een geactiveerde virtualenv kan `python` worden gebruikt; zonder activeren gebruik je `.venv/bin/python`.

## Via Codex

Zeg bijvoorbeeld: “Analyseer de Grand Prix van Nederland van 2025 en genereer alle rapporten en infographics.” Codex voert dan uit:

```bash
.venv/bin/python -m f1_analysis analyse --year 2025 --gp Nederland
```

“Nederland”, “Dutch GP” en “Zandvoort” verwijzen naar dezelfde hoofdrace. Bij meerdere passende evenementen volgt een duidelijke foutmelding. Sprintgegevens worden afzonderlijk gehouden en niet in deze versie geanalyseerd.

Singapore opnieuw analyseren met cache:

```bash
.venv/bin/python -m f1_analysis analyse --year 2025 --gp Singapore
```

Andere opdrachten:

```bash
.venv/bin/python -m f1_analysis races --year 2025
.venv/bin/python -m f1_analysis analyse --year 2025 --gp Singapore --offline
.venv/bin/python -m f1_analysis analyse --year 2025 --gp Singapore --refresh
.venv/bin/python -m f1_analysis analyse --year 2025 --gp Singapore --from-run analyses/2025/singapore/runs/UITVOERING
.venv/bin/python -m f1_analysis render --run analyses/2025/singapore/runs/UITVOERING
.venv/bin/python -m pytest -q
```

`--from-run` analyseert opgeslagen genormaliseerde input opnieuw, met de huidige regels en correcties; locatievragen gebruiken alleen cache. `render` tekent dezelfde opgeslagen analyse opnieuw. Beide maken een nieuwe map. `--root /absoluut/projectpad` is een globale optie vóór het subcommando. `--refresh` vernieuwt bewust bronnen; zonder deze optie worden historische bestanden hergebruikt. Offline ontbrekende bronnen blijven zichtbaar als beperking.

Open `analyses/index.html` in een browser. Iedere uitvoering heeft `overzicht.html`, zeven rapporten in Markdown én HTML, PNG/SVG-grafieken en een interactieve kaart die offline werkt. `latest.json` verwijst naar de laatste geslaagde uitvoering, die ook gedeeltelijk mag zijn. Mislukte uitvoeringen behouden hun manifest en wijzigen deze verwijzing niet.

## Instellingen en tellingen

`config/defaults.yaml` bevat onder meer de slotfase (laatste 25%, naar boven afgerond), pitmarge, timingvensters, verkeersfilter en locatiegrenzen. Met `--config eigen.yaml` overschrijf je specifieke instellingen.

OpenF1 `overtakes` bevat ook pitstop- en andere positiewisselingen en kan onvolledig zijn. De oorspronkelijke feedtelling, de geclassificeerde basistelling op de baan vanaf ronde 2 en een aanvullende analytische telling blijven gescheiden. Teamwisselingen worden in de aanvullende telling standaard uitgesloten; technisch positieverlies blijft standaard in de basis én aanvullende telling. Incidentwisselingen worden apart bewaard. De telling is timinggebaseerd en geen videoverificatie van elke manoeuvre.

Voor een expliciete alternatieve selectie:

```yaml
analytisch_technisch_verlies_uitsluiten: true
```

Alle gebeurtenissen, bronregistraties, uitsluitingen en correcties staan in `exports/gebeurtenissen.json` en `.csv`. Ronde 1 krijgt altijd een apart rapport. Pitlanestarters krijgen geen verzonnen numerieke gridpositie. De rondeconventie gebruikt de eigen lopende ronde van de inhaler; de andere coureursronde blijft in de export.

## F1gures en aanvullende bronnen

De downloader ontdekt het openbare racecomponent en het daarin gebruikte JSON-pad op de pagina zelf. Alleen expliciete ronde-eindposities in een bekende gegevensvorm worden geanalyseerd; bij ontbrekende posities, onbekende schema's of nog niet gevalideerde neutralisatie-uitbreiding blijft import nodig. OpenF1 en FastF1 zijn geen volledig onafhankelijke oorspronkelijke timingmetingen.

Importeer een CSV of JSON-lijst:

```bash
.venv/bin/python -m f1_analysis analyse --year 2025 --gp Singapore --f1gures-import mijn-passes.csv
```

Verplichte velden per rij: `lap_number`, `overtaking_driver_number`, `overtaken_driver_number`, `source_url`, `source_title`, `definition`. Optioneel: `year`, `session_key`, `date`, `compound`. Bron-URL moet HTTPS zijn. De import blijft als handmatig aangeleverd herkenbaar. Er is een schema-voorbeeld in `config/f1gures-import.example.csv` met alleen de kolomkoppen; het bevat geen verzonnen gebeurtenissen.

`config/sources.yaml` is het uitbreidbare bronregister. Voor volgende GP's voeg je relevante officiële verslagen en gecontroleerde claims toe met `year`, `gp`, titel, URL en uitgever. Gecontroleerde claimregels zijn expliciete onderzoeksaantekeningen, geen automatisch uit een artikel geraden oorzaken. Ze worden alleen toegepast als de bron lokaal opgehaald is en de gebeurteniscontext past. Afwezigheid van specifieke bronnen blijft een beperking.

## Correcties en reproduceerbaarheid

Correcties staan per GP in `analyses/JAAR/GP/corrections/overrides.yaml`. Elke correctie vereist gebeurtenis-ID, reden, bron-URL en gewijzigde velden:

```yaml
events:
  - event_id: bestaande-ID-uit-export
    reason: Onderbouwing van de wijziging
    source_url: https://betreffende-bron.example/document
    set:
      type: mogelijke_teamorder
```

Oorspronkelijke en gewijzigde waarden worden samen opgeslagen. Een onbekende ID of ongeoorloofd veld faalt expliciet. Manifesten bevatten configuratie, sessies, bron-URL's, ophaaltijden, code-identificatie, hashes, dekking, status, correcties en bestandsoverzicht. Cachebestanden worden door de exacte URL geïdentificeerd. De index toont per race uitsluitend de nieuwste geslaagde uitvoering. De jaarverwerking verwijdert oudere uitvoeringen na een geslaagde vervanging; broncache en correcties blijven behouden.

## Grenzen van versie 0.1

- Geen garantie op volledigheid van de overtakes-feed. Startregistraties zijn geen bewezen afzonderlijke manoeuvres.
- F1gures is in Singapore automatisch opgehaald: de vergelijking staat in het inhaalrapport en `exports/bronvergelijking.json`. Gegevens kunnen bij andere uitvoeringen ontbreken wanneer het openbare JSON-bestand onbereikbaar is. Dan is geen onafhankelijke telling beschikbaar.
- Strategie vergelijkt afgeronde pitstopcycli van nabije tegenstanders; brandstof, verkeer, banden en baanontwikkeling worden niet causaal gescheiden. Een rondetijdtrend is geen zuivere degradatie.
- Locaties gebruiken beide coureurs in een tijdvenster en blijven meestal geschatte zones. Geen geografische oriëntatie of schaal in meters uit arbitraire OpenF1-coördinaten. Ontbrekende punten worden niet ingevuld.
- Teamradio: audiolinkregister, geen automatische transcriptie. Geen afzonderlijke remtelemetrie- of DRS-oorzaakanalyse.
- De eerste proef wordt als gedeeltelijk gemarkeerd. Het jaarendpoint voor circuitgeometrie geeft een basiskaart uit 2023 terug; de baanvariant is visueel gecontroleerd aan de officiële FIA-kaart van 2025 (19 bochten). Benaderde bochtlabels zijn zichtbaar; dit bevestigt geen manoeuvrecoördinaten. De oude tunnelpassage bij The Float behoort tot de variant tot en met 2022. De baanvorm is gemeten in de race van 2025. Voor andere races zonder geregistreerde officiële jaarcontrole meldt het programma dit expliciet. Het programma geeft ontbrekende datasets en verificatieonderdelen expliciet weer; nooit een geforceerde telling van 27.

De tests gebruiken kleine stabiele fixtures. De echte Singapore-uitvoering controleert bronopslag, alle rapporten en figuren, optellingen, kaartdekking en lokale HTML-links. De hoofdinfographic is exact 3840 × 2160 pixels.

Circuitkaarten zoeken bij elke nieuwe analyse het circuit op Wikipedia op (bij voorkeur via de circuitlink in Jolpica). Het artikel en de bronmetadata worden gecachet en opgeslagen. Offline analyses gebruiken dezelfde bron. `config/sources.yaml` bevat onder `circuit_annotations` de gecontroleerde koppeling van bochtnamen, historische namen en pit-in/out-zones aan een racejaar. Breid deze koppeling na broncontrole uit voor een volgende circuitvariant; gevonden tabelnamen zonder jaarcontrole blijven kandidaten. Niet elke bocht heeft een naam: het nummer blijft dan zichtbaar. Bij onbereikbare bronnen meldt het programma de ontbrekende dekking.

PNG-, SVG- en interactieve kaarten tonen bochtnummers/namen, start/finish en rijrichtingspijlen. Paarse markeringen met ≈ geven de indicatieve pit-in/out-zone op de hoofdbaan aan; ze tekenen geen exacte pitlane of snelheidslimietlijn. Voor Singapore 2025 zijn Sheares, Memorial en de historische naam Singapore Sling gekoppeld aan Wikipedia, en de pit-in/out-zones aan de FIA-pitlanetekening.

Grafiekstijl: aantallen acties en heatmaptellingen hebben uitsluitend gehele aswaarden; rondetijden en tijdsverschillen behouden passende decimalen. Coureurs gebruiken `team_colour` uit de OpenF1-racegegevens van het gekozen jaar. Teamgenoten hebben dezelfde kleur: het laagste startnummer is doorgetrokken, de andere coureur gestippeld. Startnummer en afkorting staan in de labels; aslabels krijgen een cursief, vet nummerlabel met een kader in teamkleur. De stijl is geïnspireerd op F1-weergaven en gebruikt de beschikbare lokale lettertypen. Bij staafdiagrammen onderscheidt gevuld versus gestippeld kader uitgevoerd en ondergaan. Banden blijven in compoundkleuren. De gebruikte kleuren en lijnstijlen staan in `data/derived/driver-styles.json`.

De interactieve circuitkaart toont bij hover, toetsenbordfocus of een tik op een inhaalmarker een popup met ronde, inhalende coureur en ingehaalde coureur, inclusief startnummers en teamkleuren. Acties die dezelfde kaartzone delen worden samen weergegeven. Filters bepalen welke acties de popup toont; de popup blijft binnen het venster en sluit met Escape. In de actie-staafdiagrammen staan startnummer en achternaam boven de balkgroepen.

Het analyseoverzicht is nu een volledig offline interactief dashboard met tien gekoppelde grafieken: acties per ronde, acties per coureur, inhaler/ingehaalde-paren, circuitkaart, posities, bandenstints, rondetijden, ronde 1, pitstopcyclusoverzicht en cyclusdetails. Coureur- en teamselectie, rondereeks en compound koppelen de grafieken. Gebeurtenisfilters voor type, locatie en teldefinitie gelden voor actiegegevens; de andere grafieken vermelden hun eigen context. Hover benadrukt zonder tellingen te wijzigen. Klikken kiest een ronde, coureur, paar of stint; slepen op een lege plotachtergrond kiest een rondereeks. Rondevelden vormen het toetsenbordalternatief. Pitcycli blijven beoordeeld op de volledige cyclus na beide stops; ronde 1 houdt een vaste begin/eindvergelijking.

Vanuit kaartmarkers en tabelregels opent een dialoog met ronde, beide coureurs, banden, classificatie, onzekerheid, bronclaims en oorspronkelijke bronregistraties. De huidige selectie is als CSV te downloaden en in de adresbalk te bewaren. `Alles herstellen` verwijdert alle filters. De vaste verslagen en alle PNG/SVG-exports staan onderaan in een uitklapbaar archief. Inhaler/ingehaalde-labels staan verticaal, met beide startnummers en namen. De interactieve onderdelen gebruiken lokale JavaScript en CSS; er is geen server of hosting nodig.

Validatie van het dashboard staat in `research/qa/check-dashboard.cjs`: de echte gegenereerde JavaScript draait met een DOM-testadapter. Deze controle toetst tellingen, gekoppelde selecties, details, lege selecties, CSV en bewaarde filters. Los gerenderde SVG-grafieken worden visueel gecontroleerd. Dit vervangt geen volledige browserrendercontrole als de app-browserverbinding niet beschikbaar is.

Alle 24 hoofdraces van 2025 genereren en oudere uitvoeringen opruimen:

```bash
.venv/bin/python -u research/generate_2025.py
```

De hervatbare jaarverwerking schrijft `analyses/2025/season-manifest.json` en houdt één nieuwste uitvoering per race aan. Open `index.html` voor het raceoverzicht. De jaarconfiguratie haalt locatiegegevens per coureur op en gebruikt daaruit dezelfde lokale gebeurtenisvensters. Een onbruikbare vijfde ronde voor de baanvorm valt terug op een andere volledige gemeten ronde. Alle pitstopvergelijkingen blijven beschikbaar in het dashboard en de gegevens; maximaal twintig vergelijkingen met de grootste absolute tijdwinst krijgen daarnaast een losse PNG/SVG-detailgrafiek.

Bij de coureurselectie staan **Alles selecteren** en **Niets selecteren**. Niets selecteren geeft nul geselecteerde coureurs en gebeurtenissen in alle gekoppelde grafieken. Daarna kan één coureur of team worden toegevoegd. Alles selecteren kiest alle coureurs en wist een eventueel paarfilter; de andere filters blijven behouden. Deze keuze wordt ook in de bewaarde selectie opgenomen.

Historische seizoenen vanaf 2020 kunnen met dezelfde opdrachten worden verwerkt. Voor 2020–2022 gebruikt het programma het openbare F1-timingarchief via FastF1 3.8.3 en Jolpica voor kalender, werkelijke grid en uitslag. Positiewisselingen worden uit de verwerkte timing gereconstrueerd en als kandidaten gecontroleerd; dit is geen officiële gebeurtenissenfeed. Synthetische FastF1-ronden worden uitgesloten. De originele archiefbestanden, verwerkt model en bronhashes blijven lokaal bewaard. Ontbrekende gegevens blijven zichtbaar als onbekend.

Alle hoofdraces van meerdere jaren genereren en alleen de nieuwste uitvoering per race behouden:

```bash
.venv/bin/python research/generate_seasons.py --years 2024 2023 2022 2021 2020
```

De kalender omvat respectievelijk 24, 22, 22, 22 en 17 races. Dubbele races op één circuit blijven afzonderlijke evenementen. De voortgang wordt per jaar opgeslagen in `analyses/<jaar>/season-manifest.json`; een herstart gebruikt broncache en slaat actuele geslaagde uitvoeringen over. Dashboardfilters, bronpopups, rijdernummers en Alles/Niets selecteren gelden voor alle jaren. Parallelle seizoenbouwers delen de aanvraagbegrenzing voor OpenF1.

## Historisch archief 1950–2019

Het overzicht is uitgebreid tot het eerste wereldkampioenschapsseizoen, **1950**. De 1.018 races van 1950–2019 hebben elk een historisch raceoverzicht; samen met de 131 bestaande uitgebreide timinganalyses van 2020–2025 zijn dit **1.149 races in 76 seizoenen**. Indianapolis telt mee in de jaren waarin deze race onderdeel van het wereldkampioenschap was. De hoofdindex en `analyses/index.html` groeperen races per decennium en seizoen, nieuwste eerst. Zoeken op jaar, race, circuit of datadekking opent de passende groepen; Alles uitklappen/inklappen helpt bij navigatie.

De historische overzichten gebruiken de publieke Jolpica CSV-databasedump, die veertien dagen vertraagd beschikbaar is. De originele ZIP staat onveranderd onder `analyses/sources/jolpica/<sha256>.zip`; de downloadhash is gecontroleerd tegen de broncatalogus. Iedere race bewaart de bijbehorende originele bronrecords, een genormaliseerd model, exports, zeven rapporten en een 3840 × 2160 infographic in PNG plus SVG. Manifesten tonen bron, ophaaltijd, hash en dekking. De opgeslagen database maakt de bestaande overzichten volledig offline bruikbaar.

Uitslagen en startposities zijn beschikbaar vanaf 1950. Afzonderlijke rondegegevens beginnen in deze dump in 1996, pitstopregistraties in 2011; de feitelijke dekking staat per race vermeld. Posities aan het ronde-einde zijn **geen inhaalfeed**. Inhaalacties, bandencompounds, neutralisaties, pit-in/out en circuitlocaties zijn in deze historische overzichten onbekend. Ook 2018–2019 gebruikt in deze uitbreiding het uitslagenarchief; de uitgebreidere FastF1-timingbron is daarvoor niet automatisch verwerkt. Ontbrekende pitregistraties betekenen geen bevestigde nul stops. Historische teamkleuren zijn niet uit actuele databasekleuren afgeleid; neutrale lijnen met lijnpatronen voorkomen een onbevestigde historische kleurclaim. Startnummers komen uit de race zelf. Gedeelde auto's met meerdere coureurs blijven afzonderlijke bronentries met hetzelfde nummer.

De historische dashboards hebben Alles/Niets selecteren, teamfilter, coureursselectie, zoekveld, sorteerbare uitslag, klikbare brongegevens, rondebereik en hoverinformatie bij posities en rondetijden. Bronwaarden zijn niet gefilterd voor pitstops of neutralisaties; er wordt geen bandenstrategie uit afgeleid.

Een historische race opnieuw ophalen of uit cache bekijken:

```bash
.venv/bin/python -m f1_analysis analyse --year 1950 --gp 'British Grand Prix' --offline
.venv/bin/python -m f1_analysis analyse --year 1996 --gp Monaco --offline
```

Alle historische overzichten opbouwen of hervatten:

```bash
.venv/bin/python research/generate_archive.py --from-year 1950 --through-year 2019 --offline
```

Laat `--offline` weg om de publieke download op te halen als die nog niet in de cache staat. Iedere race behoudt één nieuwste geslaagde uitvoering. Het programma verwerkt uitsluitend daadwerkelijke, niet geannuleerde hoofdraces uit de brondatabase; ontbrekende feiten worden niet aangevuld.

Controle van het uitgebreide archief:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python research/verify_archive.py
.venv/bin/python research/verify_seasons.py --years 2020 2021 2022 2023 2024 2025
node research/qa/check-archive.cjs
node research/qa/check-season.cjs
```

De JavaScript-controles voeren de werkelijke dashboardscripts uit in een NodeVM met een eenvoudige DOM; dit is geen visuele browsertest. Integratiecontroles controleren bronrecords, dekking, bestandshashes, links, PNG-afmetingen en één nieuwste uitvoering per race. Bewijsbestanden staan onder `research/qa/`.

Het standaard rijdersfilter staat als vaste timingtoren links naast ieder dashboard. Rijders staan alfabetisch op achternaam, met hun startnummer, drielettercode en een teamkleurstrook. Klikken schakelt uitsluitend die rijder aan/uit; de andere selecties blijven behouden. Alles/Niets staat onderaan. Het menu blijft op dezelfde plaats tijdens het scrollen; bij een lang deelnemersveld kan alleen de lijst binnen het menu scrollen. Historische overzichten gebruiken broncodes wanneer beschikbaar en anders een afkorting voor de weergave; onbevestigde historische teamkleuren blijven neutraal.

De bovenbalk met racefilters schuift met de pagina mee tot hij de bovenrand bereikt en blijft daar vervolgens staan. De rondekeuze gebruikt twee verschuifbare bolletjes op één balk, van ronde 1 tot de laatste ronde, met directe updates van de grafieken en een zichtbaar van–tot-label. De bolletjes kruisen elkaar niet. Reset herstelt de volledige race en alle rijders. Reeks vooruit/achteruit behoudt de lengte van de selectie; knoppen zijn uitgeschakeld aan de grenzen en beide grijs bij selectie van de hele race. Telling, type en banden zijn uit de bovenbalk verwijderd; de onderliggende telmethode en aparte ronde-1-analyse blijven vermeld in de rapportage.

Teams selecteren staat in- en uitklapbaar onder de rijders in het linker filtermenu, in NL en EN. De eerste teamklik na een individuele selectie of Alles/Niets vervangt de rijdersselectie door dat team. Volgende teamklikken voegen alle rijders van het team toe of verwijderen ze; andere geselecteerde teams blijven behouden. Het laatste team uitzetten geeft een lege selectie. Een individuele rijderklik hervat de individuele selectiemodus; de volgende teamklik begint opnieuw met alleen dat team. Rondebereik en overige grafiekcontext blijven behouden.

De highlightkaarten tonen beschikbare racefeiten (winnaar, P1 op de startopstelling, officiële snelste ronde, winsttijd en grootste opmars) en aantallen voor de gekozen rondereeks, onafhankelijk van de geselecteerde rijders (inhaalacties, succesvolle undercuts/overcuts en de actiefste inhaler). Succesvolle strategiegevallen vereisen de bestaande beoordeling `Geslaagd` met positiewinst na een complete pitstopcyclus. Gelijke maxima blijven gezamenlijk zichtbaar; ontbrekende highlights worden volledig weggelaten, vastgestelde nulwaarden blijven staan. Rijders gebruiken dezelfde nummer–kleurstrook–afkorting als het zijmenu, met volledige naam als hovertekst. Historische overzichten leiden geen overtakes of strategie uit alleen rondeposities af.

## Compacte GitHub-publicatie en automatische verwerking

De bestaande lokale website, analyseberekeningen en dashboardbediening blijven hetzelfde. De nieuwe modules vormen een aparte opslag- en publicatielaag. De lokale `index.html` blijft rechtstreeks te openen. De compacte publicatie is voor HTTP/HTTPS bedoeld, inclusief GitHub Pages.

### Opslagindeling

- `src/`, `config/`, `tests/`, installatiebestanden en `.github/` gaan in de coderepository. Grote uitvoer, cache en lokale omgevingen staan in `.gitignore`.
- `storage/archives/` bevat onveranderlijke, gecomprimeerde seizoenarchieven van de nieuwste geslaagde uitvoering van elke race. Dat omvat oorspronkelijke invoer, tussenmodellen, correcties, manifesten, originele PNG/SVG-bestanden en beschikbare oorspronkelijke HTTP-cachebestanden die bij de geregistreerde bronhash passen. De historische Jolpica-dump en zijn aanvraagcache worden afzonderlijk gedeeld opgeslagen.
- `_storage/index.json` registreert archiefnamen, SHA-256, omvang en toekomstige GitHub Release-tags. Bestandsnamen bevatten een inhoudshash. Een bestaand archief wordt nooit stilzwijgend vervangen.
- `dist/pages/` bevat alleen de gepubliceerde website en daadwerkelijk gelinkte gegevens. Identieke scripts en stijlen worden één keer opgeslagen, zonder hun inhoud te veranderen. Paginabestanden worden verliesloos met gzip bewaard; een onzichtbare lader pakt het volledige oorspronkelijke document uit voordat de dashboardscripts starten. Dashboard-JSON, bediening en uiteindelijke DOM blijven identiek. JSON/CSV-downloads blijven rechtstreeks beschikbaar.
- Grafieken worden verliesloos opgeslagen: PNG-pixels als WebP, SVG-bytes als gzip. Afbeeldingen in dashboards hebben dezelfde pixels en afmetingen. De bestaande PNG/SVG-links openen via de technische medialader weer het oorspronkelijke formaat. Een service worker bewaart daarbij de oorspronkelijke URL en bestandsnaam; oudere browsers gebruiken een blob-weergave. PNG wordt uit dezelfde pixels opnieuw gecodeerd; originele PNG-bytes en metadata blijven in het seizoenarchief. De service worker werkt ook onder een GitHub Pages-projectpad. Voor deze compacte publicatie zijn moderne browsers met WebP, Canvas en DecompressionStream nodig.
- GitHub Releases bewaren de oorspronkelijke archieven én een geverifieerde compacte website-snapshot. Een nieuwe statusreferentie wordt pas geüpload nadat de bestanden en GitHub-opslaghashes zijn gecontroleerd. Er is geen externe opslagdienst nodig.

### Voorbereiden vanuit deze projectmap

```bash
.venv/bin/python -m f1_analysis.publication archive
.venv/bin/python -m f1_analysis.publication build
.venv/bin/python -m f1_analysis.publication verify
.venv/bin/python -m f1_analysis.publication compare
```

Als je ondertussen aan de website werkt, gebruik dan een vaste bronkopie:

```bash
.venv/bin/python -m f1_analysis.publication freeze --output storage/frozen-source-next
.venv/bin/python -m f1_analysis.publication --root storage/frozen-source-next build --output ../../dist/pages-next
.venv/bin/python -m f1_analysis.publication --root storage/frozen-source-next compare --site ../../dist/pages-next
```

`freeze` vereist eerst volledige seizoenarchieven. Gewijzigde dashboardbestanden worden apart verliesloos gearchiveerd als presentatieaanvulling; bij herstel komt deze na het seizoenarchief. De kopie schrijft niets terug naar de website. Voor grotere herhalingen kan de bestaande `storage/media-cache` naar de bronkopie worden gekopieerd; dit bespaart uitsluitend verwerkingstijd. Rond websitewijzigingen af en maak een nieuwe gecontroleerde publicatie voordat je GitHub activeert.

`build` verwacht een lege uitvoermap. Gebruik bij een volgende proef bijvoorbeeld `--output dist/pages-next`, of verwijder uitsluitend de vorige publicatie-uitvoer. De publicatiestap schrijft eerst naar een tijdelijke map en vervangt de uitvoermap pas na controle van links, SVG-hashes, PNG-pixels en het ruimtebudget. De standaard publicatie omvat 1950–heden; `--from-year` beperkt de selectie. De primaire index wordt dan met dezelfde bestaande vormgeving beperkt tot de gekozen jaren; de standaard gebruikt het volledige archief.

Instellingen staan in `config/publication.yaml`: maximaal 900 miljoen websitebytes, drie races per update, minimaal 45 minuten na het geregistreerde sessie-einde, een uur tussen pogingen voor ontbrekende races, zes uur tussen heranalyses van reeds gepubliceerde recente races en veertien dagen waarin recente races opnieuw worden verwerkt. Alle data worden eerst opgehaald; alleen na controle wordt een nieuw `latest.json` gepubliceerd. Een lege inhaal- of pitstopfeed wordt niet automatisch als fout behandeld. Bevestigd race-einde, uitslag voor alle deelnemers, definitieve winnaarafstand, laatste winnaarsronde, ronden, posities, stints en race control zijn wel voorwaarden. Deze technische dekking vervangt geen handmatige bronverificatie: analyses blijven terecht als gedeeltelijk gemarkeerd.

### Gecontroleerde momentopname

Op 11 oktober 2026 is een vaste kopie gecontroleerd terwijl de lokale website verder werd bewerkt. De publicatie bevat alle 1.149 beschikbare races uit 1950–2025: 647.816.526 bytes (circa 648 MB), 9.248 unieke grafiekbestanden en 63.341 gecontroleerde links. De actieve oorspronkelijke seizoen- en bronarchieven plus de presentatieaanvulling bedragen samen 2.534.235.447 bytes (circa 2,53 GB); het grootste afzonderlijke archief is circa 378 MB. Deze archieven komen in Releases en tellen niet als websitebestanden. De 69 tests zijn geslaagd. Alle 9.325 pagina’s hebben dezelfde zichtbare tekst, bediening, scripts, dashboardgegevens en opmaak als de vaste bronkopie. De browsercontrole van een historisch en een modern dashboard leverde identieke screenshots op; selectie en taalwisseling werken. De kopie staat in `storage/frozen-source`, de openbare uitvoer in `dist/pages`. De live website en lokale brongegevens blijven beschikbaar. De codebundel is eveneens een momentopname; herhaal de voorbereiding na verdere wijzigingen.

### Eenmalig activeren op GitHub

1. Maak een openbare repository en plaats alleen de code, configuratie, tests, installatiebestanden en `.github/` daarin. De voorbereide codebundel staat na de controle in `storage/github-ready-code.zip`.
2. Kies bij **Settings → Pages → Build and deployment** als bron **GitHub Actions**. Geef de workflow schrijfrechten voor repository-inhoud, Pages en de deployment-identiteit; de workflow vraagt die rechten zelf aan. Organisatiebeleid of branchbeveiliging moet de maandelijkse onderhoudscommit toestaan.
3. Meld lokaal de GitHub CLI aan met een account dat in de repository mag schrijven. Exporteer een token alleen voor deze opdracht, niet in bestanden of Git. Vul de echte eigenaar/repository in:

```bash
GH_TOKEN="$(gh auth token)" .venv/bin/python -m f1_analysis.github_storage \
  --repository EIGENAAR/REPOSITORY bootstrap
```

De Pages-instellingen en workflow volgen de [officiële GitHub Pages-handleiding](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Deze expliciete opdracht uploadt de bestaande, gecontroleerde seizoenarchieven en de eerste website-snapshot naar Releases. Zij maakt geen repository en publiceert nog geen Pages-site. Het GitHub-account en de repository zijn niet in dit project vastgelegd.

4. Start in **Actions** de workflow **Races bijwerken en website publiceren** eenmalig handmatig. Daarna controleert deze elk uur op minuut 17 automatisch nieuwe data. De computer thuis hoeft niet aan te blijven.

De workflow herstelt de compacte snapshot, ontdekt kandidaten met verse bronaanvragen, herstelt alleen de benodigde volledige seizoenen, analyseert beschikbare races, archiveert/verifieert ze en publiceert Pages. Onbeschikbare races worden later opnieuw geprobeerd. Gelijke timingfeeds, uitslagen en onafhankelijke gegevens worden via inhoudshashes herkend: een controle zonder inhoudelijke verandering maakt geen nieuwe analyse of groot seizoenarchief. Alleen kleine retry-statussen worden bijgewerkt. Problemen bij één race laten bestaande geslaagde uitvoeringen staan; geslaagde races kunnen worden gepubliceerd terwijl de workflow de fout zichtbaar meldt. Een mislukte archivering of publicatiecontrole blokkeert publicatie en opruimen.

Een kleine maandelijkse onderhoudscommit houdt de planning actief, ook tijdens de winterstop: openbare GitHub-workflows kunnen anders na 60 dagen zonder repositoryactiviteit worden uitgeschakeld. Verbied je automatische commits op de standaardbranch, dan moet je deze planning zelf actief houden. Na geslaagde publicatie worden oude beheerde Release-bestanden opgeruimd. Er blijven minimaal twee seizoenversies en drie herstelstatussen beschikbaar, plus ieder archief waar die statussen naar verwijzen. De huidige status en zijn bronarchieven worden nooit verwijderd. Instellingen: `archive_versions` en `snapshot_versions`. Onbekende bestanden en oudere statussen zonder referentiegraaf blokkeren automatische verwijdering.

### Opruimen en herstellen

```bash
# Eerst alleen tonen wat veilig kan worden verwijderd:
.venv/bin/python -m f1_analysis.publication cleanup
# Na controle van de geverifieerde archieven daadwerkelijk opruimen:
.venv/bin/python -m f1_analysis.publication cleanup --apply
```

Opruimen verwijdert alleen geverifieerd gearchiveerde interne rungegevens en oude gearchiveerde HTTP-cachebestanden. Bestanden waar lokale HTML-rapporten naar linken blijven staan. Dashboards, figuren, correcties, de nieuwste verwijzingen en seizoenarchieven blijven staan. Een gewijzigd bestand zonder exact overeenkomende archiefhash blokkeert het opruimen. Het standaard cachevenster is 21 dagen. Lokale originelen worden tijdens het voorbereiden niet automatisch verwijderd; de GitHub-workflow ruimt pas na gecontroleerde opslag en publicatie op. Het wegvallen van de tijdelijke GitHub-runner is veilig omdat de invoer al in Releases staat.

`--from-run` en `render` kunnen ontbrekende invoer automatisch uit de lokaal aanwezige seizoenarchieven herstellen. Een volledig seizoen terughalen van GitHub:

```bash
GH_TOKEN="$(gh auth token)" .venv/bin/python -m f1_analysis.github_storage \
  --repository EIGENAAR/REPOSITORY restore-years --years 2025
```

Voor deze opdracht moet `_storage/index.json` beschikbaar zijn; zo nodig eerst `github_storage load`. Volledige archieven kunnen ook onafhankelijk worden hersteld:

```bash
.venv/bin/python -m f1_analysis.publication restore \
  storage/archives/season-JAAR-INHOUDSHASH.tar.gz --sha256 VOLLEDIGE_SHA256
```

Afwijkende bestaande bestanden worden standaard niet overschreven. `--overwrite` is expliciet nodig voor vervanging. Download-, archief- en bestandsverificatie vinden vóór herstel plaats; absolute paden, symlinks, dubbele archiefpaden en paden buiten het project worden geweigerd.

### Grenzen en controle

Dit project heeft lokaal opslag-/hersteltests en websitecontroles. De daadwerkelijke GitHub-rechten, eerste upload en Pages-deployment kunnen pas worden getoetst wanneer een repository is gekozen en geactiveerd. De geplande verwerking gebruikt geen AI-API of Codex-abonnement. Zij maakt geen automatische causale bronclaims, bochtverificaties of handmatige correcties. GitHub-planning is geen realtimegarantie; er kunnen vertragingen zijn. Het websitebudget houdt ruimte over onder de Pages-limiet van 1 GB, maar bij toekomstige groei blijft een controle nodig.

### Verliesloze databestanden en racewissels — 12 oktober 2026

De publicatie bewaart JSON en CSV als gzip, met controle van alle oorspronkelijke bytes en SHA-256-hashes in `_data/index.json`. De browser pakt gegevens automatisch uit; CSV-downloads en de JSON-viewer leveren het oorspronkelijke bestand met zijn oorspronkelijke naam. Kleine operationele verwijzingen en de opslagregisters blijven direct leesbaar. `github_storage load` herstelt gewone bestanden voor automatische verwerking; `load --compact` behoudt de gecomprimeerde bestanden voor Pages. Seizoen- en bronarchieven worden hierdoor niet gewijzigd. `publication verify` controleert zowel de opgeslagen gzip als iedere uitgepakte inhoud.

Race- en jaarnavigatie laadt de nieuwe pagina in een afzonderlijk document terwijl de huidige pagina zichtbaar blijft. De wissel vindt plaats na laden, lettertypen, grafiekweergave en herstel van de modulepositie. Alleen het actieve racedocument blijft bestaan. Bij een laadfout blijft de huidige race beschikbaar. Terug/vooruit en herladen blijven werken met de echte race-URL.

Verborgen documenten kunnen tekenmomenten uitstellen. De gereedmelding en het herstel van de modulepositie gebruiken daarom geen animatiecallback. De voorpagina opent bij ieder nieuw bezoek met het huidige kalenderjaar; tijdens het bezoek blijft ieder ander seizoen gewoon te kiezen.

### Historische dashboards in dezelfde vorm — 12 oktober 2026

De publicatie zet bewaarde historische rondekaarten om naar dezelfde dashboardonderdelen en rijdersbadges als recente races. Onvoldoende gedekte onderdelen worden volledig weggelaten. Volgordewisselingen tussen gemeten ronde-einden worden als **gereconstrueerde positiewisselingen** aangeduid, nooit als bevestigde inhaalacties op de baan. Geregistreerde stops kunnen context geven; een bijbehorende stop bewijst de oorzaak niet. Afgeleide pitstopcycli vereisen complete opeenvolgende rondetijden, een omgekeerde volgorde en een omgekeerd tijdsverschil, zonder bekende neutralisatie of uitzonderlijk lange ronde in het venster. Onbekende compounds worden niet ingevuld.

De raceontwikkeling gebruikt gemeten rondeposities. De heatmap gebruikt sectortijden wanneer die voldoende beschikbaar zijn, anders complete rondetijden; ontbrekende timing levert geen synthetische heatmap op. Starthelden sorteert op positie na ronde 1, De lange race op de einduitslag. Positiewinst en -verlies krijgen respectievelijk een groen opwaarts en rood neerwaarts driehoekje. Originele brongegevens, gedeelde-auto-inschrijvingen, bronverwijzingen en oorspronkelijke CSV's blijven behouden. Historische circuit-SVG's zijn schematische referenties, zonder afgeleide inhaallocaties.

Gedeelde scripts en stijlbladen voorkomen dat de website voor iedere race dezelfde presentatiebestanden opslaat. Herstelde seizoenarchieven krijgen deze presentatie bij iedere publicatie opnieuw, zodat oudere opgeslagen pagina's toekomstige correcties niet terugdraaien.

### Actuele publicatie — 11 oktober 2026

De actuele bundel bevat alle 1.149 races en de laatste gecontroleerde dashboard- en indexopmaak, inclusief de 77 circuitachtergronden. De upload bewaart de bronarchieven en presentatieaanvulling in GitHub Releases; de website wordt gepubliceerd via GitHub Pages onder `/overtakeitaway/`. De workflow **Gecontroleerde website publiceren** herstelt en publiceert de gecontroleerde snapshot zonder vooraf nieuwe racegegevens te verwerken. **Races bijwerken en website publiceren** verzorgt de bestaande periodieke gegevensverwerking.


### Lopend seizoen 2026

Ook een lopend seizoen kan worden verwerkt. Het programma voegt alleen hoofdraces met een beschikbare uitslag toe; toekomstige races en races zonder uitslag blijven in het seizoenmanifest als wachtend vermeld. `status: bijgewerkt` betekent dat de beschikbare races zijn verwerkt, niet dat het seizoen is afgelopen.

Tijdens een live sessie kan OpenF1 ook historische openbare aanvragen tijdelijk afsluiten. De expliciete alternatieve bron gebruikt het openbare F1-timingarchief via FastF1, met dezelfde timinganalyses en bronopslag als de eerdere FastF1-seizoenen:

```bash
.venv/bin/python -m f1_analysis analyse --year 2026 --gp Melbourne --timing-source fastf1 --require-ready --config config/history.yaml
.venv/bin/python research/generate_current_season.py --year 2026
.venv/bin/python research/verify_current_season.py --year 2026
```

De inhaalregistraties uit FastF1 zijn gereconstrueerde kandidaten uit timing en blijven als zodanig herkenbaar; dit is geen officiële inhaalfeed. De controles vereisen een bevestigd race-einde, volledige deelnemersuitslag en timing tot de laatste winnaarsronde. Het lopende seizoen houdt eigen bronbestanden, correcties, exports en een `analyses/2026/season-manifest.json` bij.


Op 11 oktober 2026 zijn de zestien beschikbare hoofdraces van 2026 toegevoegd, van Australië tot de verplaatste Bahrain Grand Prix in Maleisië. Het lokale overzicht bevat daarmee 1.165 races in 77 seizoenen. Singapore en de latere races blijven wachtend zolang de uitslag ontbreekt. De nieuwe pagina’s volgen de actuele interactieve website, met bron- en methoderapport, circuitkaart en CSV/JSON-exports. Madring gebruikt een indicatieve baanvorm uit de opgeslagen 2026-racetiming; de kalender gebruikt daar geen lay-out van Jarama. Wisselen van FastF1 naar OpenF1 behoudt dezelfde raceverwijzing en maakt geen tweede racekaart voor dezelfde kampioenschapsronde.

### Automatische racecontrole

GitHub Actions haalt elk half uur (op minuut 17 en 47, UTC) de agenda van het huidige en vorige seizoen opnieuw op. Alleen afgelopen races worden onderzocht. Waar OpenF1 een eindtijd levert begint de controle na dat tijdstip; anders begint de controle drie uur na de geplande start. Een definitieve uitslag, bevestigd race-einde en volledige laatste winnaarsronde zijn altijd vereist voordat een pagina wordt gepubliceerd.

Ontbrekende gegevens en mislukte analyses worden na 30 minuten opnieuw geprobeerd. Bestaande analyses blijven behouden. OpenF1 wordt gebruikt waar beschikbaar, met het openbare F1-timingarchief via FastF1 als alternatief. Nieuwe pagina’s komen automatisch in de index, navigatie en wereldkaart. De eerste 14 dagen worden reeds gepubliceerde races elke zes uur gecontroleerd op aanvullingen. Zonder werk worden geen pagina’s opnieuw opgebouwd. GitHub kan geplande uitvoeringen vertragen; de planning is geen garantie op exacte starttijden.

### Agenda en meldingen voor bezoekers

De frontpagina toont voor het actuele kalenderjaar ook de geplande races. Races zonder gepubliceerde analyse zijn grijs en niet aanklikbaar. Een balk toont de vorige, meest recente en eerstvolgende race. Voor andere jaren ontbreekt deze balk.

Elke gepubliceerde HTML-pagina controleert eenmaal per minuut het gedeelde `race-updates.json`-overzicht. De eerste keer wordt lokaal een uitgangspunt opgeslagen. Bij latere bezoeken of tijdens een open bezoek verschijnt een paarse kaart voor nieuwe of bijgewerkte racegegevens, inclusief de winnaar waar bekend. Sluiten markeert de getoonde updates als gezien. Deze voorkeur geldt per browser; de pagina wordt niet automatisch herladen.

De draaiende paarse band tijdens racewissels gebruikt de ongewijzigde SVG
[F1 tire Pirelli PZero Purple](https://commons.wikimedia.org/wiki/File:F1_tire_Pirelli_PZero_Purple.svg)
van MiniPictures, onder [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
De animatie staat uit bij de browservoorkeur voor minder beweging.


### Races en rijdersprofielen (oktober 2026)

De startpagina `index.html` biedt drie ingangen: `races.html` voor het racearchief, `analysis-lab.html` voor rijdersanalyses en strategie, en `goat.html` voor het ontwerp van een vergelijking tussen generaties. Alle banners bevatten Races, Drivers en Over mij / About me naast de taalkeuze. Het originele logo opent de startpagina.

De GOAT-tegel gebruikt een eigen donkere afbeelding met racehelmen uit verschillende tijdperken en een trofee, plus een champagnegoud accent. De GOAT-pagina is uitdrukkelijk in de ontwerpfase: **Winter break**. De tweetalige popup opent bij ieder paginabezoek, sluit met knop, Escape, achtergrond of na acht seconden, en kan via de statusknop opnieuw worden geopend. De pagina schetst de vragen rond rijder, auto/context en generaties, zonder al een ranglijst of berekende GOAT-score te tonen. Afbeelding en generatieprompt staan bij de lokale bronassets. De startpaginabouwer genereert ook de GOAT-pagina en de publicatiestap bewaart beide.

Het rijdersgedeelte opent met de tweetalige introductie **Pre-season testing**, inclusief een eigen gegenereerde garageafbeelding. De popup sluit met de primaire knop, via de achtergrond, Escape of automatisch na acht seconden. De tweede knop opent het raceoverzicht. De introductie wordt niet op de racepagina’s getoond.

De rijdersomgeving gebruikt standaard alle bewaarde WK-seizoenen vanaf 1950 (momenteel 1950–2026). De lokale bouwlimiet is 64 MB voor de ongecomprimeerde analyseomgeving; dit is een afzonderlijke werkgrens, geen GitHub-limiet. De uitbreiding van 16 oktober 2026 telt 1.166 races en 817 profielen: ongeveer 52 MB ongecomprimeerd en 7,3 MB gecomprimeerde profielgegevens. Alle 8.366 eerder gebruikte coureur-racerecords uit 2007–2026 zijn inhoudelijk ongewijzigd behouden. De totale publicatiegrens blijft 900 MB. De oudere jaren ondersteunen vooral starts, rondetijdrangen, teamgenootvergelijkingen op overlappende ronden en pitstopcycli; ontbrekende bandenset- en leeftijdgegevens worden niet ingevuld. Zes beschrijvende onderdelen onderzoeken vrije-luchttempo, rondetijdrangen per circuit, relatief tempobehoud op oudere banden, vroeg tempo op nieuwe sets, uitvoering rond pitvensters en starts. De starter groepeert de eigen positiewinst of het positieverlies na ronde één per startpositie. Eén gecombineerde grafiek bevat verticale violins (bij voldoende gegevens), mediaan, kwartielen, individuele races en de witte modelcurve met grijze 95%-modelband. Boven nul is winst, onder nul verlies; de startpositie blijft op de x-as. Kwartielen zijn naar winst/verlies omgezet met omkering van de volgorde: Q25(winst)=grid−Q75(positie), Q75(winst)=grid−Q25(positie). De schaalwijziging verandert de onderliggende berekeningen niet. De drie opgeslagen Starter-metrieken worden opnieuw berekend wanneer de historische selectie wordt uitgebreid. De x-as begint altijd bij P1 en toont iedere positie tot de volledige veldgrootte van de geselecteerde races (minimaal P20); posities zonder eigen starts houden hun asmarkering en krijgen geen verzonnen meetpunten. Ontbrekende data zijn geen nulscore; er is geen algemeen rijderrapportcijfer of geïsoleerde causale vaardigheidsschatting.

Het lokale Starter-onderzoek (`starter-curve-comparison-v3`) toont een volledige witte mediaantrend op het grid, ook waar maar één start beschikbaar is. Een Gaussisch proces modelleert de mediane positiewinst ten opzichte van y=x, met een neutrale voorafverwachting en vaste RBF-kern (lengte 2 gridposities, amplitude 4 posities), gelijk voor alle rijders. De benaderde mediaanruis is π/2 maal lokale residuele variantie gedeeld door n. Minstens 30 nabije starts leveren die variantie waar beschikbaar; een expliciete ondergrens van 1 positie² voorkomt schijnzekerheid bij één of identieke waarnemingen. Minstens tien eigen gridstarts over drie startposities zijn vereist.

De grijze band is een indicatieve puntgewijze 95%-modelband (Bayesiaans geloofwaardigheidsinterval), gegeven de gekozen kern en benaderde ruis. Er is nog geen kalibratie van frequentistische dekking, onzekerheid over modelkeuze/ruisschatting of causale interpretatie. Curve en band zijn begrensd tot geldige posities. Bij ontbrekende nabije data trekt de fit geleidelijk terug naar y=x, met meer onzekerheid. Dun bezette posities, gaten en extrapolatie worden met onderbroken lijn getoond; alle gemeten punten blijven onveranderd, behoudens expliciet uitgesloten pitlanestarts. De metrieken onderscheiden centrale afstand ≤0,5 positie van een band die de diagonaal omvat; dat laatste is onzekerheid en geen bewijs van gelijkwaardigheid. De winstgrenzen zijn vaste verkennende drempels, geen formeel geschatte breekpunten.

De grafiek gebruikt een vaste symmetrische niet-lineaire weergaveschaal van −10 tot +10: 0, ±1, ±3, ±6 en ±10 staan op gelijke visuele afstand. Overige gehele posities krijgen kleine streepjes. De y-as met groene Beter-pijl omhoog en rode Slechter-pijl omlaag staat in een apart, vast SVG-vak buiten de horizontale scroller. Races buiten ±10 blijven als aanklikbare punten met een pijltje aan de rand zichtbaar, met de echte waarde in de hover; ook curve, band en violins worden op die weergavegrens begrensd. Deze transformatie verandert geen observaties of statistieken.

De curve en violins delen dezelfde winst/verliesschaal; de horizontale nullijn vervangt de vroegere y=x-diagonaal van de absolute positiegrafiek. Er is geen dubbele vormgrafiek meer. De vormtabel beschrijft uitsluitend de geselecteerde rijder. De tabel middelt diens modelwinst op gehele posities in P1–P5, P6–P10, P11–P15 en P16–P20, plus eventuele hogere veldposities. Modelmarges gebruiken 800 gezamenlijke trekkingen van de gecorreleerde curve; puntmarges worden niet onafhankelijk gemiddeld. Aantallen en dun bezette bereiken zijn expliciet zichtbaar. Circuitmix, auto en tijdperk zijn in deze ruwe vormanalyse niet gelijkgetrokken.

`assets/starter-metrics.json` legt voor iedere beschikbare rijder de drie samenvattingswaarden vast: `corrected_curve_balance_pp`, `start_score` en `gain_boundary_grid`. De tabel gebruikt rechtstreeks dezelfde functies als de kaarten. Per rijder worden 95%-marges, aantallen, uitgesloten pitlanestarts, griddekking en afzonderlijke beschikbaarheidsstatussen bewaard. Een niet gevonden winstgrens is onderscheiden van onvoldoende data; ontbrekende waarden zijn `null`, geen nul. Bron- en codehash, periode en filterinstellingen maken de momentopname herleidbaar. `assets/starter-metrics.csv` bevat dezelfde tabel voor handmatig gebruik (UTF-8 met BOM, puntkomma als scheiding, decimale komma). Na een herbouw van de rijdersdata zijn de tabellen opnieuw te maken met `node research/export_starter_metrics.mjs`. Er is geen algemene ranglijst toegevoegd.

De Startscore corrigeert al voor startpositie: iedere eigen start wordt vergeleken met andere rijders vanaf exact dezelfde gridpositie, op hetzelfde circuit en met dezelfde veldgrootte in de actieve jaar-/circuitselectie. De gekozen rijder ontbreekt in de volledige referentie, en de eigen race wordt uitgesloten. Minstens vijf andere races per eigen start en tien geschikte eigen starts zijn nodig. Betere eerste doorkomst telt 1, gelijk 0,5, slechter 0; het gemiddelde per eigen start maal 100 geeft de score. Referentiegroepen met meer races krijgen niet automatisch extra gewicht. Dubbele gridinschrijvingen per referentierace worden uitgesloten. De score van 50 is neutraal, geen percentage races met positiewinst. De score vermeldt gemeten en vergelijkbare startposities, aantallen en uitgevallen dekking.

Een tweede grafiek fit de gemiddelde vergelijkingskansen per gridpositie (minstens vijf vergelijkbare eigen starts per positie), gecentreerd rond de neutrale score 50. Dit kan behoud vanaf P1 belonen terwijl gebruikelijke winst vanaf P20 neutraal blijft. De gecorrigeerde netto AUC integreert de fit minus 50 in pp·gridvakken; gedeeld door gedekte breedte geeft dat de kansgecorrigeerde curvebalans in procentpunten. De oppervlakte weegt gedekte gridvakken gelijk; de fit gebruikt frequentiegewichten. Deze balans en de racegewogen Startscore hebben verschillende weging en zijn geen onafhankelijke bewijsbronnen. De indicatieve percentielmarges van score en gecorrigeerde curve gebruiken 600 herhalingen van hele raceblokken binnen circuit/veldgrootte, met hetzelfde racegewicht voor alle gridcellen en de eigen rijder; minimaal 90% moet bruikbaar zijn. Ook onzekerheid in de referentie telt mee.

Voor de gecorrigeerde scores betekenen ontbrekende startposities onbekend, niet nul. Modelinschattingen uit de volledige curve tellen niet als scorewaarnemingen. Scores gelden voor hun vermelde steun. Vergelijk rijders alleen op gezamenlijke voldoende bezette posities en contexten; een ranglijst vereist een vaste vergelijkingspopulatie. Team/auto, weer, tijdperk en starttype zijn niet gecorrigeerd, en uitval vóór de eerste gemeten doorkomst ontbreekt. Dit blijft een onderzoeksmaat voor waargenomen startuitkomsten, geen geïsoleerde vaardigheidsschatting. Alle berekeningen gebruiken bestaande compacte data; geen extra racebestanden. De build bewaart expliciete pitlanestatus uit actuele dashboardvlaggen en uit behouden F1DB-race- of gridlabels `PL`. Historische PL-starts die ooit als het laatste numerieke gridvak waren weergegeven, worden uitgesloten uit startwaarnemingen en referenties; de status blijft ook bij bronloze herbouw behouden.

Tempo door de tijd behoudt alle races van de rijder op de chronologische x-as. Ontbrekende vergelijkingen krijgen een grijs kruis in een aparte rij onder de grafiek, niet een 0%-waarde. De achtergrond markeert opeenvolgende teamgenootperiodes, onafhankelijk van de beschikbaarheid van tempometingen; het nummer-kleur-code-label gebruikt de teamgenoot en diens nummer/kleur bij aanvang van de periode. Periodes worden vóór de seizoen- en circuitfilters bepaald. Negatieve afwijkingen betekenen sneller en staan boven nul, met een groene pijl omhoog; positieve afwijkingen betekenen trager en staan onder nul, met een rode pijl omlaag. Bronbevestigde tijdelijke invallers krijgen een open symbool. Korte vaste stoelenwissels worden niet als tijdelijke invalbeurt afgeleid. De bronverwijzingen voor invalbeurten staan bij de grafiek. Datapunten worden niet met lijnen verbonden. De procentas en de rode/groene richtingpijlen staan buiten het horizontaal scrollende grafiekdeel en blijven dus zichtbaar. De procentas blijft vast op −10% tot +10%, met een symmetrische, stuksgewijs lineaire transformatie: 0, ±1, ±3, ±6 en ±10 liggen op gelijke visuele afstand. Alleen deze hoofdwaarden krijgen labels; overige gehele procenten krijgen kleine streepjes. Werkelijke metingen veranderen niet. Metingen buiten het bereik staan aan de schaalrand met een extra uitwaarts pijltje en hun werkelijke waarde in de hover. Puntkleuren worden waar nodig richting wit opgelicht tot voldoende helderheid; de echte teamkleur in de badges blijft behouden.

De tempovergelijking gebruikt voor beide teamgenoten dezelfde genummerde raceronden. Vanaf zes schone ronden met dezelfde bekende compound en maximaal twee ronden verschil in bandenleeftijd blijft de eerdere mediaan van symmetrische procentuele tijdsverschillen behouden. Bij één tot vijf passende ronden worden de twee gemiddelde rondetijden vergeleken. Zonder passende bandencombinatie worden de beschikbare schone overlapronden als afzonderlijk benoemde gemiddeldevergelijking gebruikt; compound en leeftijd zijn dan niet gecontroleerd. Gemiddeldevergelijkingen krijgen één symbool zonder kwartielstreep. Start-, pit-/uit-, neutralisatie- en door de bron afgekeurde ronden worden niet alsnog ingevuld.

Een uitval verwijdert geen eerder gemeten gedeelde ronden: de beschikbare overlap wordt gebruikt en het punt wordt een driehoek. De hover noemt de vergeleken rondetijden, het aantal gebruikte ronden, de gebruikte rondereeks, bekende uitvallers en wie de overlap qua voltooide raceafstand of timingomvang begrenst. Beide tekenrichtingen gebruiken exact dezelfde rondes. De nieuwe definitieversie en bronhash bewaken hergebruik bij een bronloze herbouw.

Voor 2018–2019 bewaart `driver_history` de beschikbare F1-timing, bandenleeftijden en intervallen als compacte lokale `data/normalized/driver-history.json.gz`. Het gebruikt uitsluitend sessierelatieve klokken en haalt geen auto- of locatietelemetrie op. Onbevestigde, synthetische, pit- en vlagronden worden niet gebruikt voor tempokwaliteiten. De oorspronkelijke racedashboards blijven behouden. De droge compounds van vóór 2019 blijven onder hun eigen namen beschikbaar; onbekende setleeftijden worden niet als nieuwe banden behandeld. Voor 2017 blijven detailkwaliteiten zonder voldoende timing onbekend.

Een gecomprimeerde snapshot bewaart de gecontroleerde compacte rijderswaarnemingen. Bij een latere bouw zonder genormaliseerde broninvoer worden die alleen hergebruikt als de definitieversie en de hash van de relevante brongegevens overeenkomen. Gewijzigde of beschikbare brongegevens worden opnieuw verwerkt. Zo vereist een automatische update van het actuele seizoen geen herdownload van alle telemetrie uit eerdere jaren.

De metronoom bewaart precies één rang per gemeten volledige rondetijd, ten opzichte van alle gemeten volledige rondetijden op dezelfde raceronde van dezelfde race. Sectorwaarnemingen worden niet meer in de rijdersanalyse opgeslagen of getoond. Gelijke millisecondetijden delen een rang; daarna worden plaatsen overgeslagen. Ontbrekende tijden krijgen geen verzonnen rang. De veldgrootte, compound en context blijven per ronde bewaard.

De x-as toont alle circuits waarop de gekozen rijder gereden heeft. Alle races en jaren op hetzelfde circuit worden samengevoegd. Iedere gemeten ronde is één afzonderlijk punt; mediaan en kwartielen zijn rechtstreeks gebaseerd op die individuele rangen. Bij voldoende verschillende metingen toont een verticale violin de verdeling. P1 staat bovenaan. Alles, schone raceronden en schone ronden met gemeten vrije baan zijn selecteerbaar. Filters op seizoen, circuit en compound blijven werken, maar herberekenen het oorspronkelijke referentieveld niet. Punten verwijzen naar de bronrace en vermelden race, ronde, rang, veldgrootte en context. Lege circuitgroepen blijven expliciet zonder meting.

De eerdere aparte kaart De sectorspecialist en de oude variantiemeting van De metronoom zijn vervangen; het overzicht bevat weer zes specialismen, met De starter vooraan. De compacte ronderangen worden bij bronloze herbouw behouden als bronhash en definitie gelijk zijn. Eenmalige migratie gebruikt eventueel gecontroleerde context van eerdere ranggegevens, maar leidt nooit een rondetijdrang af uit sectorrangen.

De strategieatlas bevat **De pitbalans** voor de gekozen rijder: per race een verticale violin met één punt per vergelijkbare tegenstander, mediaan en kwartielen. Standaard worden alleen finishers met hetzelfde aantal geregistreerde pitbezoeken vergeleken. De tijdwinst is het onderlinge tijdsverschil vóór de vroegste stop van het paar min dat verschil één ronde na hun laatste stop. Positieve tijdwinst telt ook zonder positiewisseling. Iedere race telt eenmaal in de overkoepelende mediaan. Bij minder dan vijf tegenstanders of minder dan twee verschillende uitkomsten blijven de punten en kwartielen staan zonder geschatte dichtheid. Acht races per grafiekblad houden alle seizoenen bereikbaar zonder onleesbaar smalle kolommen.

De vergelijking met werkelijk gereden strategieën met méér of minder stops staat apart. Een ander meetvenster toont uitsluitend de eigen in- en uitronde, inclusief het normale pitverlies. Klikken op een tegenstander opent de gemeten gaten en posities, beide volledige stopreeksen, eindklassering en de tijdwinst per eigen stopronde, inclusief uitronde en na de gelijkgenummerde stop van de tegenstander. Die vensters kunnen overlappen en worden niet opgeteld. Dit is beschrijvende timing, geen geïsoleerd strategie-effect of voorspelling van een niet gekozen alternatief; tempo, verkeer, banden, schade en straffen kunnen eveneens bijdragen.

`pit_programmes` bewaart eenmalig per bevestigde finisher de gemeten milliseconden en rondeposities als compacte gehele getallen, plus de geregistreerde stopronden en neutralisaties. Er wordt geen matrix met alle rijdersparen opgeslagen. Onvolledige timing, onzekere pitregistraties, pitstraatstarts en niet-bevestigde finishers blijven expliciet uitgesloten. Zonder voldoende dekking wordt nul stops niet aangenomen. Rode vlaggen en onverenigbare tijd-/positievolgordes worden uitgesloten; SC/VSC is standaard uitgesloten en optioneel gemarkeerd. Onbekende neutralisatiecontext blijft vermeld. Bronloze herbouw hergebruikt deze waarnemingen alleen bij dezelfde bronhash en definitieversie. De uitbreiding blijft binnen de totale analysebegroting van 32 MB.

```bash
.venv/bin/python -m f1_analysis.phase2 --root .
```

Eenmalige aanvullende historische invoer ophalen of hergebruiken:

```bash
.venv/bin/python -m f1_analysis.driver_history --root . --years 2018 2019 --report storage/driver-history-collection.json
```

De pagina's zijn gegenereerde uitvoer en staan in Releases, niet in de coderepository. De gedeelde broncode en compacte fotografische WebP-bestanden worden wel meegeleverd.

De zelfstandige, tweetalige **stijlgids** staat op `stijlgids.html`, bereikbaar via de footer van de startpagina. `style_guide.py` bouwt het document met ingebouwde CSS, SVG-voorbeelden, taalbediening en de ongewijzigde originele logoafbeelding. Het kan daardoor ook los van de site worden geopend. De publicatie- en snapshotbouw nemen het document automatisch mee. De gids legt het basispalet rood `#FF4758`, paars `#B45CFF`, cyaan `#51D6DD` en goud `#E5BF78` vast, plus functionele accenten, teamkleuren, componenten, grafiekschalen en de regels voor scrollen, kaartzoom, popups, laden en afbeeldingsbeweging. Het document is een ontwerpreferentie; het wijzigt niet alle bestaande schermen of gegevens tegelijk.

De gedeelde header heeft op alle pagina’s precies zes onderdelen: **Home · Races · Drivers · Greatest · About me · EN/NL**. site_navigation.py vervangt oudere varianten en verwijdert de vervallen losse analyseknop. site-theme.css beheert het gezamenlijke interfacepalet en componentvormen; team-, banden- en wetenschappelijke kleurcoderingen behouden hun betekenis. De zelfstandige stijlgids neemt dezelfde navigatie en stijllaag ingebouwd mee. Rijdersdropdowns gebruiken driver-names.js om een kopie van de opties op achternaam te ordenen, zonder observaties of grafiekranglijsten te herschikken.


De uitbreiding vóór 2007 hergebruikt het bewaarde Jolpica/F1DB/StatsF1-racearchief. Starts en positieontwikkeling gaan terug tot 1950; brede rondetijdreeksen beginnen in 1996. `research/extend_early_driver_history.py` bewaart bovendien zes Atlas F1 Classics-tabellen (Italië 1971, USA-West 1983, Monaco 1984, Europa 1993, Brazilië 1994 en België 1995). Titel, deelnemers en overlappende snelste ronden bevestigen de koppeling. `999:999`, lege cellen en ronden voorbij de classificatieafstand worden niet als tijden geïmporteerd. Losse snelste ronden vóór 1996 zijn geen volledige reeks en worden uitgesloten van tempo- en ranganalyses. Onbekende banden, setleeftijd en vrije lucht blijven onbekend.

`data-collection.html` is de zelfstandige tweetalige collectiepagina, met een subtiele footerlink op de startpagina. De pagina toont per parameter de ingevulde, ontbrekende en expliciet onbekende waarden, de afzonderlijke gegevenslagen, jaardekking, brondatabasetabellen, bronmethoden, werkelijk vastgelegde zoektermen en controles. Bronkopieën en afgeleide resultaten worden niet opgeteld als onafhankelijke feiten. De volledige telling staat in `assets/data-collection.json`. Het controleerbare zoek- en methodenlogboek is `config/data-collection-journal.json`; oudere exacte zoektermen die niet bewaard zijn worden niet achteraf verzonnen. Nieuwe collectieactiviteiten voegen hier hun echte zoekopdrachten en bevindingen toe.

De startpaginabouwer ververst de collectiepagina; een coureursbuild doet dat ook zodra deze pagina bestaat. Los bijwerken kan met `.venv/bin/python -m f1_analysis.data_collection --root .`. Een lokale telcache in `storage/data-collection/` voorkomt herhaald uitpakken van ongewijzigde bronbestanden. De telling bevat inputhashes en controleert unieke profiel-ID’s, racereferenties, dubbelen, ranggrenzen en SQLite-integriteit. Dit is een herhaalbare momentopname; geen achtergrondmonitor en geen claim dat oude banden- of strafgeschiedenis volledig is.


Het [totaalplan voor fase 2](documents/fase-2-onderzoeks-en-ontwikkelplan.md) bepaalt de module-indeling, meetlatten en bouwvolgorde voor Coureurs, GOAT en de latere strategie- en voorspellende analyses. Het [verbeterlijstje](documents/verbeterlijst.md) bevat de detailkeuzes en broninventaris. Coureurs toont eigen loopbaanfeiten, verdelingen, ontwikkeling en het teamgenootduel; GOAT vergelijkt coureurs met een gemeenschappelijke referentie, vaste contextgewichten, dekking en onzekerheid. Deze plannen veranderen de huidige website of scores nog niet.

Nieuwe onderzoeksbronnen worden als aanvullende, onveranderlijke bronarchieven opgeslagen. Het bestaande basisarchief blijft behouden; `source_supplements` worden op volgorde hersteld en meegenomen in de referentiegraaf voor publicatie en bewaarbeleid. Nieuwe archiefdelen bevatten maximaal 1,4 GB ongecomprimeerde invoer en worden volledig met SHA-256 gecontroleerd. Zo blijven grote originele PDF-verzamelingen buiten Pages en onder de [bestandsgrens voor GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases). Bij een metadataherbouw blijft eerder geverifieerde bandencontext van rondetijdrangen behouden wanneer rondenummer, rang en gemeten veldgrootte exact overeenkomen.

### GOAT: bewaarde AI-vergelijkingen en infographic

`goat.html` opent zonder rijderkeuze met Hamilton, Verstappen, Vettel en Michael Schumacher. Een expliciete selectie blijft leidend; de infographic gebruikt precies die rijders. `_development/assets/goat-ai-contract.js` bevat het gedeelde antwoordcontract `goat-comparison-v2`, de toegestane bronparameters en de basisweging: tempo 30%, racevervolg 25%, kwalificaties 20%, starts 15%, loopbaanresultaten 5% en pitbalans 5%. Alleen voor iedere rijder bruikbare onderdelen tellen mee. Loopbaanresultaten en pitbalans houden elk maximaal 5%; het restant wordt naar verhouding over de beschikbare rijkwaliteiten verdeeld. Zonder bruikbare rijkwaliteiten volgt geen klassering. Deze prioriteiten zijn een gekozen beoordeling, geen geschatte modelcoëfficiënten of bewezen totaalscore. De metronoom meet rondetijdrang, geen regelmaat; autovoordeel is niet volledig geïsoleerd.

De browser en GitHub bouwen dezelfde vraag via `goat-ai.js`; `goat-ai-format.js` en `src/f1_analysis/goat_ai.py` controleren hetzelfde JSON-contract. Alle geselecteerde rijders zijn verplicht, ook bij ontbrekende gegevens. De bronversie, feitenperiode, circuitkeuze en tijdas moeten overeenkomen. Een volledige voorlopige klassering bevat iedere rijder eenmaal op P1–Pn en moet passen bij winnaar en nummer twee. Zonder verdedigbare volledige volgorde blijven de posities onbekend. Technische details, aannames, ontbrekende onderdelen en de gebruikte gewichten blijven apart beschikbaar.

`goat-infographic.js` tekent een vast SVG-ontwerp in de websitestijl: grote kop, voorlopige klassering, alle kolommen in die volgorde, broncijfers, bestaande curves en korte toelichting. Zonder AI-antwoord blijft het een herkenbaar gegevensvoorbeeld zonder verzonnen klassering. Teamkleuren, lijnpatronen, asschalen, ontbrekende waarden en gemeten curvegrenzen komen uit de bestaande weergave. `goat-infographic-brand.js` bevat de oorspronkelijke bytes van `assets/overtake-wordmark-v2.png` en `assets/home/goat-winter-break-v1.webp`; het logo wordt niet opnieuw getekend, bijgekleurd of bijgesneden. De ingebouwde afbeeldingen maken SVG- en PNG-export ook onder `file://` zelfstandig bruikbaar. Gemini levert tekst en bronparametercodes; de website haalt de cijfers zelf op.

De vraag zet rijdercodes in een vaste volgorde en circuitcodes in een vaste volgorde voordat de aanvraaghash wordt berekend. Dezelfde combinatie en instellingen hergebruiken daardoor hetzelfde gecontroleerde antwoord op de branch `goat-ai-results`, ook na een andere aanklikvolgorde. Wijzigingen aan bron, periode, circuits, taal, tijdas of beoordelingsvraag geven een andere hash. De GitHub-workflow voert aanvragen na elkaar uit, controleert het bewaarde antwoord vóór het gebruik van de Gemini-sleutel en herstelt een ontbrekende indexverwijzing zonder nieuwe modelaanroep. Een infographic opnieuw tekenen of downloaden roept Gemini niet aan. Automatisch gegenereerde antwoorden blijven op GitHub bewaard.

Onder de GOAT-selectie staat de navigatiebalk in dezelfde volgorde als de secties. **The Answer to the Ultimate Question** staat voorop, met SVG- en PNG-download rechts. Bij een ontbrekend antwoord opent **Stel de vraag** de vooraf ingevulde GitHub-aanvraag; na versturen controleert de zichtbare pagina maximaal 25 minuten iedere 30 seconden alleen de bewaarde resultaten. Dat start geen nieuwe modelaanroepen. Een afgerond antwoord stopt die controle en werkt uitleg, P1–Pn en infographic vanzelf bij. Handmatige JSON-invoer en de oude vraagknoppen zijn verwijderd. De websitefonts worden voor alle infographictekst gebruikt; het logo behoudt zijn oorspronkelijke pixels. De voetnoot noemt Gemini AI en de bron-URL zodra werkelijk een AI-antwoord gebruikt is.

De rijderspagina toont **Vergelijkbare loopbanen** met de drie andere coureurs op de kleinste Euclidische afstand in de bestaande PC1/PC2-kaart, bij dezelfde zes standaardkenmerken als GOAT. `driver-pca-neighbours.js` hergebruikt het ongewijzigde PCA-model en bewaart het model tijdens de geopende pagina; de jaarselectie blijft alleen een rijderfilter. Ontbreekt een berekende PCA-positie, dan wordt geen buur geschat. De links wisselen het rijderprofiel met behoud van die selectieperiode.

Metronoomviolins worden gesorteerd op de ongeronde mediane rang en bij gelijke mediaan op de kleinste 95%-marge rond die mediaan. `driver-field.js` berekent deze marge met 400 reproduceerbare bootstrapsteekproeven van complete races; alle oorspronkelijke ronderangen van een getrokken race blijven bijeen en tellen als ronden mee. Eén bruikbare race krijgt geen geschatte marge en komt bij een gelijke mediaan na bekende marges. De gekleurde kwartielstreep blijft de middelste 50% van de ronden voorstellen en wordt niet als betrouwbaarheidsinterval aangeduid. Dezelfde sorteervolgorde geldt in het veld op de rijderspagina en bij de gekozen circuits op GOAT. Deze sorteermarge verandert geen bewaarde curves, loopbaancijfers of PCA-posities.

De GOAT-dropdown toont de drielettercode vóór de naam en sorteert eerst op die code, daarna bij gelijke code op naam. De rijderspagina houdt de bestaande sortering op achternaam, met een expliciete familienaam voor Zhou Guanyu. Alle 817 bewaarde profielen blijven in de lijst staan, inclusief gekozen rijders die als ‘al gekozen’ zijn uitgeschakeld. `driver-names.js` zet volledig in hoofdletters aangeleverde naamdelen alleen voor de presentatie om naar de gewone schrijfwijze; drielettercodes, initialen, bronbestanden, rijder-ID’s en racemetingen blijven behouden. Browser en GitHub gebruiken dezelfde naampresentatie, zodat hun aanvraaghash gelijk blijft.

### Bezoekers en Stats4me

`config/visitors.json` bevat alleen het openbare GoatCounter-adres en het productieadres van de site. `visitors.py` bouwt `assets/visitors.js` en `stats4me.html`. Het gedeelde navigatiescript laadt de teller op alle bestaande pagina's; alleen HTTPS op `espierin.github.io/overtakeitaway/` telt mee. Lokale bestanden, testservers, ontwikkelmappen en `stats4me` tellen niet mee. De teller stuurt uitsluitend het paginapad zonder zoektekst of fragment; verwijzingen worden tot hun herkomstdomein beperkt. Er worden geen rijderselecties, queryteksten of klikgebeurtenissen vastgelegd. De eigen uitschakelvoorkeur, Do Not Track en Global Privacy Control worden gerespecteerd.

`stats4me.html` staat buiten het publieke hoofdmenu en toont het dashboard via GoatCounter. Toegang tot de cijfers verloopt via de eigen GoatCounter-login; een onvindbare paginanaam is geen toegangsbeveiliging. De eigenaar moet in GoatCounter het dashboard op ingelogde gebruikers houden en `https://espierin.github.io/overtakeitaway/stats4me.html` toestaan onder Settings → Sites that can embed GoatCounter. Er staat geen API-sleutel, dashboardtoegangstoken of bezoekerslog in de website of repository. De rechtstreekse dashboardlink werkt ook wanneer een browser een ingesloten dashboard blokkeert. Tellingen beginnen zodra de teller online staat; eerdere bezoekers worden niet achteraf verzonnen. Opnieuw bouwen kan met `PYTHONPATH=src .venv/bin/python -m f1_analysis.visitors --root .`.

Gemini krijgt voor de technische decoder een vereenvoudigd objectschema; de volledige antwoordregels blijven in de vraag en in de browser/Python-controle staan. De uitvoering gebruikt een lage redeneerinstelling om ruimte voor het eindantwoord te houden binnen het totale uitvoerbudget. Volledig ontvangen antwoorden worden vóór de vormcontrole zonder gedachten of headers bewaard onder `responses/<aanvraaghash>.json`; ook na een controlefout kan diezelfde ontvangen tekst opnieuw worden gecontroleerd zonder nieuwe modelaanroep of aanwezige Gemini-sleutel. Afgebroken antwoorden worden niet als afgeronde analyse gepubliceerd; de werkbijlage bevat alleen de uitvoertekst, afsluitreden en aantallen tokens voor diagnose.

De gedeelde vraag bevat bovendien een vooraf berekend `assessment_plan`. Een parameter mag alleen in het eindoordeel meetellen als die voor iedere geselecteerde rijder werkelijk beschikbaar is; ontbreekt bijvoorbeeld Schumachers startscore, dan gebruiken we die score voor niemand in de klassering. Ontbreekt bij één rijder de metronoom, dan kan gezamenlijk beschikbaar teamgenoottempo nog wel het tempodomein vormen. De broncode berekent de identieke aangepaste gewichten en begrenst de toegestane bewijsparameters; Python en browser weigeren antwoorden die daarvan afwijken. Ontbrekende cijfers blijven zichtbaar als ontbrekend in eigen grafieken, maar leveren geen minpunten op. Een aanvankelijk ontvangen antwoord dat dit schond is uit de actieve resultatenindex verwijderd en blijft alleen als controlebewijs bewaard.
