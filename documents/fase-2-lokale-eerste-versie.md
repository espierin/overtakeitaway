# Fase twee — lokale eerste versie

**Datum:** 13 oktober 2026. **Status:** lokaal, voor beoordeling; geen GitHub-upload of deployment uitgevoerd. Deze versie bouwt de eerste rijdersprofielen en beschrijvende strategieanalyses uit het onderzoeksplan. Geavanceerde modellen en voorspellingen vallen buiten deze eerste oplevering.

Open [de analyseomgeving](../analysis-lab.html), of gebruik de nieuwe link **Rijders & strategie · Analyseomgeving** op de lokale voorpagina.

## Wat er werkt

- Een gezamenlijke selectie van seizoen en circuit voor beide werkruimten.
- Rijdersprofielen: tempo ten opzichte van de eigen teamgenoot, ontwikkeling per race, spreiding van passende rondeverschillen, startwinst en doorklikbare racegegevens.
- De oude referentietabel is op verzoek verwijderd, inclusief ongebruikte exportvelden. Alle rijders blijven via de profielkeuze bereikbaar. De zes nieuwe rijderskwaliteiten staan beschreven in [de lokale documentatie](rijderskwaliteiten-lokale-versie.md). Vergelijkingen met eigen teamgenoten zijn geen ranglijst van absolute snelheid.
- Strategieatlas: gemeten kandidaat-pitcycli per circuit en type, inclusief ongunstige uitkomsten; uitsplitsing naar positie vóór de cyclus.
- Per cyclus een pop-up met het tijdsverloop, stopmomenten, bekende compounds en een link naar de oorspronkelijke racepagina en bronnen.
- Dezelfde selectie bij wisselen van werkruimte; deelbare URL; Nederlandstalige en Engelstalige bediening.
- Compacte gegevens, geen volledige autotelemetrie of trainingscache in het openbare bestand.

## Dekking en definities

De scope is **2022–2026**: 109 races en 33 rijders op basis van de lokaal bewaarde laatste race-uitvoeringen. Dit is geen claim dat ieder onderdeel voor iedere rijder complete dekking heeft.

Tempovergelijking vereist dezelfde raceronde, dezelfde bekende compound, maximaal twee ronden verschil in bekende bandenleeftijd en minimaal zes passende rondes per race. Eerste ronde, pit-/uitronden, neutralisaties en bestaande kwaliteits-/verkeersuitsluitingen vallen buiten die vergelijking. Het procentverschil is symmetrisch: `200 × (rijdertijd − teamgenoottijd) / (rijdertijd + teamgenoottijd)`; negatief betekent sneller. Iedere race telt eenmaal in de getoonde mediaan. Spreidingsstrepen zijn de middelste 50% van de passende rondeverschillen, geen betrouwbaarheidsinterval.

De strategieatlas bevat **kandidaat-pitcycli**. De intentie van teams is niet bekend. De noemer betreft geaccepteerde vergelijkbare pitparen, niet alle denkbare kansen of bewezen undercutpogingen. Een positieomkering is een geobserveerde uitkomst, geen bewezen causaal voordeel van banden of strategie.

Voor een cyclus zijn volledige opeenvolgende rondetijden vanaf de race-start nodig. Stops liggen maximaal acht ronden uit elkaar; de oorspronkelijke afstand is maximaal drie posities. Extra stops, neutralisaties, inconsistente volgorde/klokmetingen, grote timinguitschieters en pitlanestarters worden uitgesloten. Het meetmoment ligt één ronde na de latere stop. Het ontbreken van een geaccepteerde cyclus betekent geen bewezen nul undercuts of overcuts.

## Opslag en toekomstige publicatie

De uitbreiding heeft een harde eigen bouwlimiet van **20 MB**. De huidige ruwe uitbreiding blijft onder **4 MB**. Het bestaande totale websitebudget van **900 MB** blijft actief. De bouwopdracht weigert een te grote uitbreiding en ondersteunt maximaal vijf seizoenen in deze eerste versie.

Brondata en caches worden niet aan de analysepagina toegevoegd. De publicatiebouw herberekent de compacte gegevens wanneer deze analyseomgeving expliciet in het bronproject aanwezig is. De HTML-pagina en gedeelde bestanden worden meegenomen bij een latere gecontroleerde publicatie.

**Publiceren is uitsluitend toegestaan na expliciete toestemming van de gebruiker na lokale beoordeling.** Een geslaagde lokale bouw is geen toestemming voor commit, push, upload van Release-bestanden of Pages-deployment.

## Lokale controle

De berekeningstests controleren ook negatieve pitcyclusuitkomsten, ontbrekende rondegegevens, onbekende bandenleeftijd/compound, neutralisaties, verkeersuitsluitingen en opslag-/periodegrenzen. Een lokale DOM-controle toetst selectie, taalwisseling, uitlichten zonder verbergen, paginering, pop-ups en behoud van context.

De interactieve browserverbinding kon niet worden gestart. Daarom is nog geen volledige visuele browsertest van de nieuwe pagina uitgevoerd. De gebruiker controleert de lokale weergave vóór toestemming voor publicatie.

Let bij beoordeling vooral op:

1. Desktop en smalle schermen: leesbaarheid, overloop, badges en menuhoogte.
2. Wisselen van seizoen, circuit en rijder; blijven beide werkruimten bij dezelfde selectie?
3. Onvoldoende vergelijking: verschijnt een uitleg in plaats van een verzonnen nul?
4. Cyclusgrafiek en bronrace: zijn de betekenis van de tijdsverschillen en het meetvenster begrijpelijk?
5. Nederlands/Engels en deelbare links.

## Reproduceren

```bash
.venv/bin/python -m f1_analysis.phase2 --root .
.venv/bin/python -m pytest -q
```

Het controlebestand staat in [phase2-build-report.json](../assets/phase2-build-report.json). De berekening en definities zijn versiegebonden, zodat uitbreiding later controleerbaar blijft.
