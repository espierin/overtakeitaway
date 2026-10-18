# Controle uitval, incidenten en straffen

Lokale ontwikkelversie · 17 oktober 2026 · scope: alle 817 profielen, 1950–2026. De oorspronkelijke website en het bronarchief zijn niet gewijzigd. Er is niets gepubliceerd.

## Uitkomsten van de volledige controle

| Onderdeel | Uitkomst |
|---|---:|
| Gekoppelde uitslagregistraties | 27.441 |
| Bevestigde uitvalregistraties | 9.611 |
| Door ontbrekende oude DNF-vlag verborgen herstelgevallen | 9.185 |
| Onzekere uitkomsten / gedeelde auto’s | 170 / 120 |
| Afwijkende oudere finishvlag bij expliciete uitvalreden | 58 |
| Opnieuw ingelezen en op pdf-hash gecontroleerde FIA-documenten | 6.013 |
| Documenten met herstelde inhoud of ontvangers | 415 |
| Gekoppelde ontvangerrollen / andere betrokkenen | 5.342 / 371 |
| Gekoppelde tijdstraftoevoegingen in de uitslag | 282 |
| Herstelde tijdstraftoevoegingen, waarvan vóór 2007 | 23, waarvan 12 |
| Geslaagde reken-, gegevens- en regressietests | 302 |
| Unieke analytische gegevenslaag / verliesloze downloads | 62.983.265 / 9.964.526 bytes |

Dit zijn registraties en koppelrollen, geen onderling optelbare aantallen onafhankelijke races of persoonlijke straffen. De historische sanctieverzameling blijft onvolledig.

## Gevonden fouten en herstel

1. De oude weergave eiste zowel `finished_on_track === false` als `dnf === true`. Bij veel historische races ontbreekt juist die tweede vlag. De uitslag en uitvalreden waren er wel. De nieuwe uitkomstclassificatie gebruikt de bewaarde bewijsstukken en verlangt die ontbrekende vlag niet meer.
2. Een numerieke eindklassering werd soms als rijdende finish behandeld, terwijl de bron een expliciete uitvalreden gaf. Geklasseerde uitvallers tellen nu mee bij uitval en vallen buiten de analyse van ronde één tot finish. De oorspronkelijke finishvlag en uitslag blijven bewaard; afwijkende bewijsstukken zijn gemarkeerd.
3. Gezamenlijke besluiten en oudere `N° / Driver`-koppen verloren hun coureurkoppeling. Ook zachte afbreekstreepjes, tabellen met meerdere ontvangers, ontbrekende of afgebroken tabelkoppen en de variant `No.` zijn nu afgevangen.
4. De ontvanger van een straf en een andere betrokken coureur waren onvoldoende gescheiden. Een incidentbesluit kan nu bij beiden zichtbaar zijn, maar een straf telt uitsluitend voor de expliciete ontvanger. Boetes voor de renstal staan apart van persoonlijke sancties.
5. Verwijzingen naar oudere straffen in een herzieningsbesluit konden een nieuwe straf suggereren. Oproep, onderzoek, herziening, geen verdere actie, straf, vervanging en herroeping zijn afzonderlijke uitkomsten. Een voorwaardelijk opgeschorte stop-and-go is geen schorsing van de coureur.
6. De uitslagbron bevat ook twaalf tijdstraftoevoegingen van vóór 2007. Die zijn toegevoegd; daarnaast worden varianten in coureuridentiteiten correct gekoppeld. Elke registratie heeft nu ook expliciet een jaar voor het periodefilter. Toegevoegde tijd is niet hetzelfde als alle tijdens de race uitgevoerde straffen.

## Gecontroleerde voorbeelden

| Voorbeeld | Uitkomst in de ontwikkelversie |
|---|---|
| Rosberg · Spanje 2016 | Uitval door botsing in de openingsronde; nul voltooide ronden is geen reden om de uitval weg te laten. |
| Hamilton · Spanje 2016 | Dezelfde botsing en uitval; het gezamenlijke FIA-besluit 33 is aan beiden gekoppeld. |
| Gezamenlijk FIA-besluit Spanje 2016 | Geen van beiden volledig of overwegend verantwoordelijk volgens de stewards; geen verdere actie. Dit zegt niets over verantwoordelijkheid in andere races. |
| Hamilton · Maleisië 2016 | Motorprobleem telt als technische uitval. |
| Ricciardo · China 2024 | Uitval door botsing; het gekoppelde strafbesluit betreft Stroll. Ricciardo erft die straf niet. Het causale verband is inhoudelijk beoordeeld. |
| Ocon · Oostenrijk 2023 | Vier afzonderlijke tijdstraffen van 5 + 10 + 5 + 10 seconden uit één collectief besluit; één besluit met totaal 30 seconden voor Ocon. |
| Magnussen / Räikkönen · Maleisië 2014 | Oud `N° / Driver`-formulier: Magnussen is de strafontvanger, Räikkönen een andere betrokkene. |
| Jos Verstappen · Australië 2001 | De bron bevat 25 seconden toegevoegd aan de uitslag; ook deze oudere registratie wordt nu gebruikt. |
| Collectieve rondeschrappingen 2025–2026 | Autonummer uit de autokolom, niet het bochtnummer of volgnummer; afzonderlijk aantal geschrapte ronden per coureur. |
| Tijdelijke trainingsrijder | Koppeling met de deelnemerslijst van de betreffende sessie; niet automatisch met de racedeelnemer in dezelfde auto. |

De officiële [F1-beschrijving van Spanje 2016](https://www.formula1.com/en/latest/article/mercedes-drivers-split-over-racing-incident.6Eg3YzwzWEflkpo6ZD29rL.6Eg3YzwzWEflkpo6ZD29rL) bevestigt de uitval van beide coureurs en publiceert de motivering van de stewards. Het originele FIA-besluit 33 is eveneens lokaal bewaard en op controlesom gecontroleerd.

## Methoden en reproduceerbaarheid

- De volledige bewaarde F1DB-versie is gekoppeld aan de bestaande profielen. Geen koppeling uitsluitend op drielettercode. Uitvaluitkomst en gemelde oorzaak blijven aparte velden.
- Alle 6.013 bewaarde FIA-documentteksten zijn opnieuw ingelezen. Het oorspronkelijke document blijft ongewijzigd bewaard. Het wijzigingsregister toont per document de oude en nieuwe herkende velden.
- De 6.013 bijbehorende pdf’s zijn opnieuw tegen de opgeslagen SHA-256 gecontroleerd: geen ontbrekende bestanden en geen afwijkende controlesommen.
- De controle omvat elke gekoppelde uitslagregel, niet alleen de races met genoeg rondedata voor een snelheids- of startanalyse. Ook niet gestarte deelnemers zijn afzonderlijk zichtbaar.
- De gekozen begin- en eindjaren begrenzen de eigen resultaten, besluiten en tijdstraftoevoegingen. Training, kwalificatie, sprint en hoofdrace worden voor de koppeling onderscheiden.
- Dezelfde ronde-één-tot-finishuitsluiting geldt voor Coureurs en GOAT. Ruwe uitslagen en oude vlaggen worden niet overschreven.
- Browserproeven omvatten Nederlands, Engels, desktop, mobiel en rechtstreeks lokaal openen. De algemene controles reconstrueren tevens alle oorspronkelijke racewaarnemingen, rondegegevens, pitcycli, downloads en de hashes van de oorspronkelijke pagina’s.

De broncontrole is te herhalen met `PYTHONPATH=src .venv/bin/python _development/research/verify_incident_sources.py`. Bouw en tests staan in [README](README.md). De specifieke browserproef staat in `tests/incidents-browser.cjs`; uitvoer onder `storage/incident-recheck-20261017/`.

## Grenzen die zichtbaar blijven

Een `NC`-uitslag zonder aanvullende finishinformatie bewijst geen uitval. Gedeelde auto’s leveren geen zekere individuele uitkomst. Banden, ophanging, vleugels en vergelijkbare schade bewijzen op zichzelf geen zuiver technisch defect of schuld van de coureur. Tegenstrijdige oorzaakcategorieën worden niet gladgestreken.

Vóór 2007 ontbreekt in deze verzameling een systematisch FIA-besluitenarchief. Ook daarna is het archief niet gegarandeerd volledig. Een gevonden nul uitval bij bekende uitkomsten kan een echte nul zijn; geen gevonden straf of schuldvaststelling bewijst geen nul. Alleen expliciet gelezen passages leveren een persoonlijke verantwoordelijkheidstoekenning. Een botsing, een oproep of een straf in hetzelfde weekend bewijst geen schuld aan die uitval.

## Controlebestanden

- [Volledig hercontrole- en wijzigingsregister](incident-audit.json): uitkomsten per jaar, herstelgevallen, bronconflicten, documentwijzigingen en koppelrollen.
- [Controle van oorspronkelijke FIA-pdf’s](incident-source-validation.json).
- [Bouwrapport en opslagbudget](build-report.json).
