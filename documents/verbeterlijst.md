# Verbeterlijst voor coureursanalyses en GOAT

Bijgewerkt op 17 oktober 2026. Deze lijst is de gedetailleerde werklijst bij het [totaalplan voor fase 2](fase-2-onderzoeks-en-ontwikkelplan.md). Het totaalplan bepaalt de samenhang, module-indeling en bouwvolgorde; deze lijst bevat de nadere analyses, broninventaris en verbeterpunten. Bij een verschil gaat het totaalplan voor en worden beide documenten bijgewerkt. De ontwerpkeuzes blijven leidend. Op 17 oktober 2026 zijn ze lokaal uitgewerkt op de afzonderlijke ontwikkelpagina’s; de bestaande website is daarbij niet gewijzigd. Zie het [uitvoerings- en controleverslag](../_development/IMPLEMENTATION.md) voor de gebouwde onderdelen, controles en nog niet behaalde onderzoekspoorten. Een beschreven ambitie is geen bewijs dat het bijbehorende model al gevalideerd is.

De coureurspagina verklaart wat één coureur tijdens zijn eigen carrière heeft laten zien: zowel gewone loopbaanfeiten zoals WK-punten, kampioenschapsposities en kwalificatieresultaten als de verdiepende specialismen. GOAT onderzoekt hoe verschillende coureurs presteren wanneer hun omstandigheden vergelijkbaar worden gemaakt. Beide gebruiken dezelfde waarnemingen en definities, maar beantwoorden verschillende vragen. **De rechtstreekse teamgenootvergelijking blijft bewust bij Coureurs.**

## 1. De scheiding: eigen profiel tegenover onderlinge vergelijking

**Coureurs vraagt: wat laat deze rijder zien, hoe verandert dat, en wat betekent het getal? GOAT vraagt: wie presteert op deze eigenschap beter, binnen hetzelfde veld of over tijdperken heen?**

De plaats van een analyse wordt bepaald door de vraag en de presentatie, niet door de herkomst van de gegevens. Een eigen startscore mag uit andere starts worden afgeleid. Een eigen rondetijdrang heeft het veld nodig als rekenkundige referentie. Dat maakt de eigen figuur nog geen GOAT-vergelijking. De bezoeker hoeft op de coureurspagina geen grafieken of scores van andere coureurs te bekijken om de gekozen rijder te begrijpen.

| Beslisregel | Coureurs | GOAT |
|---|---|---|
| Geselecteerde personen | Eén profiel tegelijk; teamgenoot als expliciete uitzondering | Meerdere coureurs of een vergelijkingsgroep |
| Hoofduitkomst | Eigen getal, verdeling, ontwikkeling en omstandigheden | Verschillen, overeenkomsten en rangorde tussen coureurs |
| Gebruik van het veld | Referentie in de berekening, uitgelegd in gewone taal | Deelnemers aan de zichtbare vergelijking |
| Teamgenoten | Eigen ontwikkeling en direct duel binnen teamperioden | Eventueel bouwsteen voor een breder vergelijkingsmodel |
| Betekenis van een profielgemiddelde | Beschrijft de werkelijk gereden carrière of gekozen periode | Niet rechtstreeks overnemen als eerlijke vergelijkingsscore |
| Overkoepelend oordeel | Geen algemeen rapportcijfer of positie op een coureursranglijst | Eerst meerdere dimensies; totaalscore alleen na modelvalidatie |

**Uitzondering teamgenoot:** een herkenbare vergelijking binnen hetzelfde team is bruikbaar om de eigen prestaties te duiden en blijft zichtbaar bij Coureurs. Dat is geen bewijs van een identieke auto, strategie of opdracht. Een vergelijking met willekeurige tegenstanders, het volledige veld of historische grootheden wordt vanuit Coureurs gelinkt naar GOAT; er komt geen verborgen vergelijkingsmodus op de coureurspagina.

### Drie lagen die we gescheiden houden

1. **Waarneming:** bijvoorbeeld P8 bij de start en P6 na ronde één, of rang 4 van 20 gemeten rondetijden.
2. **Eigen contextmaat:** bijvoorbeeld gemiddeld 0,4 positie beter dan verwacht bij vergelijkbare starts. De referentie wordt berekend, maar de eigen uitkomst en uitleg staan centraal.
3. **Vergelijkingsmaat:** bijvoorbeeld het verschil tussen twee coureurs na weging naar dezelfde startposities en circuits. Deze laag hoort bij GOAT.

Een getal in laag 2 hoeft geen geïsoleerde rijvaardigheid te meten. Auto, team en omstandigheden blijven invloed houden. Schrijf daarom over *gemeten prestaties* en benoem per eigenschap wat wel en niet wordt gecorrigeerd.

## 2. Kritische beoordeling van de bestaande onderdelen

Deze inventarisatie is gebaseerd op de huidige opbouw in `phase2.js`, `driver-qualities.js`, `driver-field.js`, `lap-rankings.js`, `pace-timeline.js` en de bestaande GOAT-ontwerppagina. Het is een controle van wat nu wordt aangeboden, geen aanname dat oudere ontwerpdocumenten nog de huidige website beschrijven.

| Bestaand onderdeel | Besluit | Concrete aanpassing in het bouwplan |
|---|---|---|
| Coureursprofiel met zes specialismen | Bij Coureurs behouden | Alle kaarten tonen uitsluitend een zelfstandig uit te leggen maat van de gekozen rijder; Starter blijft de eerste kaart |
| Bewaarde WK-standen, punten, kwalificatie- en carrièregegevens | Als eigen feiten aan Coureurs toevoegen | Bronarchief is veel rijker dan de huidige profieluitvoer; per onderdeel koppelen en dekking zichtbaar maken, niet opnieuw alles ophalen |
| Startonderzoek: eigen violins, curve en onzekerheidsband | Bij Coureurs behouden | Eigen starts blijven de waarnemingen; de eventuele veldreferentie krijgt uitleg, geen rij van andere coureurs |
| Gecorrigeerd startvoordeel per gridpositie | Bij Coureurs behouden | Getal en figuur uitleggen als eigen voordeel boven een referentie; bestaande definities versieerbaar houden |
| Raceontwikkeling van ronde 2 tot finish | Bij Coureurs behouden | Dezelfde figuurtaal als het startonderzoek; finisherselectie zichtbaar en uitval apart rapporteren |
| Het teamgenootduel / Tempo door de tijd | Bij Coureurs behouden | Expliciete uitzondering: werkelijk betrokken teamgenoten, teamperioden, gedeelde ronden en beperkingen blijven zichtbaar |
| Vrije-baan-specialist | Bij Coureurs behouden | Eigen tempokenmerk, met de teamgenoot als toegestane referentie; overlap met het teamgenootduel beperken |
| Metronoom: eigen individuele rondetijdrangen per circuit | Bij Coureurs behouden en naar voren halen | Iedere bruikbare ronde blijft een datapunt; de eigen violin is de hoofdfiguur, geen verborgen detail onder een veldvergelijking |
| Metronoom: alle coureurs naast elkaar op rondetijdrang | Naar GOAT | Huidige veldgrafiek als verkenning hergebruiken; dezelfde races betekent nog niet dezelfde bruikbare ronden of omstandigheden |
| Pitwindow-specialist: eigen uitvoering tegenover eigen stinttrend | Bij Coureurs behouden | Eigen vensters, mediaan, spreiding en ontwikkeling worden de hoofdweergave |
| Pitwindow-specialist: grafiek met de uitkomsten van alle coureurs | Naar GOAT | Referentie en selectie opnieuw beoordelen voordat deze een vergelijkende kwaliteitsscore wordt |
| Opwarmer: eigen vroege ronden tegenover eigen stabiele stintfase | Bij Coureurs behouden | Eigen opwarmverlies en verdeling per set/circuit; geen andere coureurs nodig in de figuur |
| Opwarmer: alle coureurs naast elkaar | Naar GOAT | Eenzelfde race en compound zijn onvoldoende om bandenleeftijd, weer en racefase gelijk te stellen |
| Bandenfluisteraar: eigen tempobehoud, nu tegenover teamgenoot gemeten | Bij Coureurs behouden | Referentie benoemen; geen absolute slijtage claimen en geen losse ranglijst toevoegen |
| Strategieatlas: circuit- en racecontext | Zelfstandig strategieonderdeel; relevante eigen uitkomsten bij Coureurs | Een strategische keuze, pitcrewprestatie en uitvoering door de rijder afzonderlijk houden; atlas niet integraal als GOAT-vaardigheid gebruiken |
| Opgeslagen Starter-metrieken voor alle coureurs | Gedeelde rekenlaag behouden | Bij Coureurs alleen eigen waarden uitlezen; in GOAT pas vergelijken na controle van definitie, context en dekking |
| GOAT-pagina met Winter break-status | Ontwerpstatus behouden | Pas een inhoudelijke vergelijking tonen wanneer de bijbehorende meetlat gecontroleerd is |

**Belangrijk inhoudelijk aandachtspunt:** de huidige zichtbare Metronoom gaat over rondetijdrangen. Dat is relatief tempo, geen zuivere constantheid. In de rekenlaag bestaat ook een maat voor spreiding rond de eigen stinttrend. Behoud de gevraagde rangverdelingen onder De metronoom, maar maak twee duidelijk benoemde aspecten: **tempo in het veld** en, waar berekenbaar, **regelmaat van het eigen tempo**. Gebruik nooit dezelfde kaartwaarde of titel voor deze twee verschillende grootheden zonder verdere aanduiding.

## 3. Opzet voor de module Coureurs

### Volgorde op de pagina

1. **Het coureursprofiel.** Nummer–teamkleur–code plus volledige naam, gekozen periode, eigen basisstatistieken en zes compacte specialismekaarten. Bij de feiten horen WK-punten, kampioenschapsposities, kwalificatieresultaten, titels, starts, zeges, podia en poles. Een compact carrièreoverzicht geeft toegang tot eigen seizoen- en kwalificatiedetails, zonder de zes specialismen tot een grote verzameling extra kaarten uit te breiden. Geen veldranglijst. De vaste kaartvolgorde wordt: Starter, vrije-baan-specialist, metronoom, bandenfluisteraar, pitwindow-specialist, opwarmer.
2. **De starter.** Eigen prestaties van grid tot eerste doorkomst. Behoud de huidige violins voor gewonnen/verloren posities, medianen, kwartielen, curve, onzekerheidsband en gecorrigeerd voordeel. Het taartdiagram met winst/behoud/verlies blijft alleen in de samenvattingskaart.
3. **Het vervolg van de race.** Positieontwikkeling vanaf de eerste doorkomst tot de finish, met dezelfde analysetaal. Alleen bevestigde rijdende finishers in deze analyse; daarnaast de aantallen uitgesloten en ontbrekende gevallen vermelden.
4. **Het teamgenootduel — Tempo door de tijd.** De bestaande tijdlijn en passende tempometingen blijven. De vrije-baan-specialist kan hier verdiepen, zodat niet tweemaal dezelfde hoofdgrafiek verschijnt.
5. **De metronoom.** Eigen rondetijdrangen per circuit, alle jaren binnen de periode samengevoegd; iedere geaccepteerde ronde is één punt. Waar beschikbaar een afzonderlijk deel voor eigen regelmaat.
6. **De bandenfluisteraar.** Verloop van eigen tempobehoud bij ouder wordende sets, met de gebruikte teamgenootreferentie uitgelegd.
7. **De pitwindow-specialist.** Eigen uitvoering vóór en na stops, per race en over de tijd. Details van een duel blijven bereikbaar via de betreffende race.
8. **De opwarmer.** Eigen verlies of voordeel in de eerste bruikbare ronden op een nieuwe set.
9. **Uitval, incidenten en straffen.** Een volwaardig feitelijk onderdeel van het eigen profiel: hoeveel keer, welke oorzaak, welke vastgestelde verantwoordelijkheid en welke straf? Eigen aantallen, aandelen en gebeurtenissen, zonder andere coureurs in beeld.
10. **Beschikbaarheid en methode.** Compact overzicht van gebruikte races, ronden en uitsluitingen. Brondetails per analyse via het bestaande uitklapmenu; geen herintroductie van de verwijderde algemene tabel Onderliggende races.

De eerste versie houdt zes specialismekaarten. Raceontwikkeling krijgt een eigen onderzoeksblok direct onder Starter, zonder hiervoor alvast een zevende specialismekaart te forceren. Uitval, incidenten en straffen zijn vaste feiten in de carrièrecontext én krijgen het eigen detailblok hierboven; ze worden niet afhankelijk gemaakt van een toekomstige kwaliteitsscore.

### Basisstatistieken: wat is al beschikbaar?

**Controle uitgevoerd op 17 oktober 2026, op de lokaal bewaarde bronbestanden.** Er is geen nieuwe online bronopvraging gedaan voor deze inventarisatie. Het oorspronkelijke F1DB-archief `analyses/sources/historical/f1db/1c5c07d064e2988cb31a44206cc679662e0523a9bde0c191eed8ffc22831eec6.zip` is opnieuw gelezen; de SHA-256 komt overeen met `source.json`. Dit is de bewaarde release `v2026.17.0`. Het archief bevat gegevens voor 1950–2026; de uitslagen, kwalificaties en WK-standen lopen voor 2026 tot en met ronde 17. Latere kalenderregels zijn geen gereden races. Deze controle zegt wat in deze momentopname beschikbaar is, niet dat iedere waarde actueel of volledig is.

| Gegeven | Werkelijk lokaal aangetroffen | Nog te doen voor de coureurspagina |
|---|---|---|
| WK-stand en punten na een race | `races-driver-standings`: 21.588 regels over 1.166 races, jaren 1950–2026; 21.588 ingevulde puntenwaarden en 21.587 numerieke posities | Per rijder koppelen en als eigen punten-/positietijdlijn ontsluiten; ontbrekende rijders en gelijkstanden controleren |
| Seizoensstand en WK-titels | `seasons-driver-standings`: 1.681 regels, waarvan 1.680 met numerieke positie; punten en titelindicator aanwezig | Definitieve historische eindstand onderscheiden van de tussenstand van een lopend seizoen; ontbrekende seizoensnoteringen controleren |
| Kwalificatieresultaat | `races-qualifying-results`: 27.083 regels over 1.166 races, 1950–2026; 26.947 numerieke posities | Eigen kwalificatieverdeling en ontwikkeling bouwen; niet uit de startgrid terugrekenen |
| Kwalificatietijden en segmenten | In dezelfde tabel: 18.182 ingevulde `timeMillis`, 8.657 `q1Millis`, 6.363 `q2Millis` en 4.033 `q3Millis` | Beschikbare sessietijd en segmenttijd onderscheiden; de velden vullen elkaar deels aan en zijn geen aantallen onafhankelijke kwalificaties |
| Race-uitslagen, starts en toegekende racepunten | `races-race-results`: 27.665 inschrijvings-/resultaatregels over 1.166 races, met grid, uitslagstatus, puntenveld en indicators voor pole/snelste ronde | Racefeiten koppelen, unieke starts vaststellen en de betekenis van lege puntenvelden controleren; uitslagpositie is niet voor iedere uitvaller numeriek ingevuld |
| Seizoens- en carrièretotalen | `seasons-drivers`: 3.416 regels; `drivers`: 917 identiteiten met onder meer titels, starts, zeges, podia, punten, poles en snelste ronden | Totalen vergelijken met gebeurtenisgegevens en voor de gekozen periode opnieuw samenstellen; 917 bronidentiteiten zijn niet hetzelfde als de 817 huidige analyseprofielen |
| Snelste ronden | `races-fastest-laps`: 17.214 individuele regels over 1.165 races, 1950–2026 | Persoonlijke snelste ronde onderscheiden van de snelste ronde van de gehele race en van eventueel daarvoor toegekende punten |
| Sprintresultaten | `races-sprint-race-results`: 612 regels over 30 sprints, 2021–2026 | Apart registreren; sprintpunten bij het officiële WK-totaal betrekken zonder sprintzeges als Grand Prix-zeges te tellen |
| Sprintkwalificatie | `races-sprint-qualifying-results`: 488 regels, 2023–2026 | Apart van Grand Prix-kwalificatie tonen en veranderde weekendformats meenemen |

De aantallen hierboven zijn **bronregels en ingevulde velden**, geen garanties dat alle deelnemende coureurs of alle reglementaire situaties compleet vertegenwoordigd zijn. De WK-tabellen bevatten bijvoorbeeld 388 verschillende rijderidentiteiten, tegenover 860 in de race-uitslagentabel. Dat verschil vraagt een dekkingscontrole; een ontbrekende WK-notering wordt geen verzonnen numerieke positie.

Een concreet voorbeeld is Jos Verstappen: de bron bevat acht seizoensregels, maar slechts vijf regels in de afzonderlijke WK-standentabel. Voor 1995, 1997 en 1998 staan in `seasons-drivers` nul punten en een lege kampioenschapspositie. Die nul punten zijn wel een beschikbaar eigen feit; een exacte WK-positie is met deze regels niet aangetoond. Zoek zo'n ontbrekende positie gericht in aanvullende bronnen, met behoud van de oorspronkelijke lege waarde en de herkomst van de aanvulling.

**Belangrijk verschil tussen opslaglagen:** `historical.sqlite` bevat de eerder ingelezen subset 1950–2019. Het oorspronkelijke ZIP-archief bevat daarnaast 2020–2026 en moet dus voor deze uitbreiding worden hergebruikt. De huidige uitvoer naar `analysis-lab.html` bevat al onder meer grid, finish, ronde-éénpositie, team, uitvalstatus en verdiepende metingen, maar nog geen eigen WK-punten, volledige WK-standen of kwalificatievelden per profielrace. De constatering is daarom: **grotendeels verzameld, nog niet als volledig coureursfeitenblok gekoppeld of getoond**. De brondata hoeven niet integraal naar de browser; compacte eigen race-/seizoensfeiten volstaan.

### Welke basisfeiten horen bij Coureurs, en hoe komen ze terug bij GOAT?

| Onderdeel | Coureurs: het eigen feitenoverzicht | GOAT: mogelijke vergelijkingsvraag |
|---|---|---|
| WK-punten | Officieel meegetelde punten per seizoen, eigen puntenverloop, waar bekend onderscheid met behaalde maar geschrapte punten | Hoe verschillen prestaties na correctie voor puntensysteem, aantal kansen en sprintformat? Ruwe carrièretotalen zijn geen eerlijke tijdperkmaat |
| WK-positie en titels | Eindpositie per afgerond seizoen, actuele tussenpositie met peildatum, aantal titels en beste eindpositie | Prestaties tegenover verschillende velden en autocondities; een titel blijft ook een team-/autocontext hebben |
| Kwalificatie | Eigen uitslag per Grand Prix, mediaan, spreiding, beste resultaat en poles; tijden en Q1/Q2/Q3 waar beschikbaar | Kwalificatietempo of positie tegenover andere coureurs onder vergelijkbare sessie-, weer-, banden- en formateisen |
| Startopstelling | Werkelijke gridpositie en wijzigingen tegenover kwalificatie, inclusief bekende gridstraffen en pitlanestarts | Pas vergelijken na onderscheid tussen kwalificatieprestatie en uiteindelijke startpositie |
| Deelname | Inschrijvingen, daadwerkelijk gestarte races, actieve seizoenen, debuut en laatste deelname binnen het vastgelegde bereik | Vergelijken per kans en carrière-/leeftijdsfase; een langere carrière levert niet vanzelf hogere kwaliteit |
| Uitslagen | Zeges, podia, puntenfinishes, beste resultaat, verdeling van eindposities en rijdende finishes | Resultaatkansen bij vergelijkbare uitgangspositie, auto, veld en tijdperk |
| Snelste ronden | Aantal officiële snelste ronden van de race, persoonlijke snelste rondetijden als apart detail | Alleen met context voor banden, pitkeuzes, vrije lucht en historische registratie; geen automatisch zuivere snelheidsmaat |
| Afstand en leiding | Gereden ronden; eventueel ronden aan de leiding of afstand waar de dekking dit ondersteunt | Kansen en raceomvang gelijkstellen; onvolledige rondekaarten geven geen exacte loopbaantotalen voor leiding |
| Teams en tijdvakken | Eigen teams en seizoenen, startnummers en bekende loopbaanperioden | Auto- en teamcontext in vergelijking en eventuele verbinding tussen tijdperken |
| Uitval, incidenten en straffen | Eigen aantallen, oorzaken, verantwoordelijkheid en sancties zoals hieronder uitgewerkt | Vergelijking van betrouwbaarheid, bevestigde incidenten en sancties met passende noemer en context |

De eigen kampioenschapspositie is een feit op de coureurspagina, ook al is een kampioenschap naar zijn aard relatief. Het tonen van “P4 in 2026, stand na ronde 17” is iets anders dan een dashboard dat meerdere coureurs op hun kampioensloopbaan rangschikt. Dat laatste hoort bij GOAT. Hetzelfde geldt voor aantallen titels, podia en poles: eigen totalen bij Coureurs; de onderlinge vergelijking daarvan bij GOAT.

### Presentatie en definities van de basisfeiten

- **Carrière of selectie expliciet.** Bovenaan staan feiten voor de gekozen jaarperiode. Eventuele carrièretotalen krijgen een apart label en bereik, zodat bijvoorbeeld een periodefilter niet ongemerkt alleen de grafieken verandert.
- **Eigen seizoensoverzicht.** Per seizoen: team(s), starts, zeges/podia, punten, WK-positie en kwalificatiesamenvatting. De eigen WK-positie en punten krijgen een tijdlijn; kwalificaties krijgen een eigen verdeling of tijdlijn. Geen volledige WK-tabel van alle coureurs op de coureurspagina.
- **Puntensystemen respecteren.** Officiële WK-punten niet blind reconstrueren door racepunten op te tellen: historische schrapresultaten, gedeelde punten, halve punten, extra punten, sprints en besluiten achteraf kunnen verschil maken. `totalPoints` en `totalChampionshipPoints` niet zonder gecontroleerde definitie als synoniemen gebruiken.
- **Geen nieuwe uitslagregels verzinnen.** Numerieke posities, tekstuele uitslagstatus en rangorde bij gelijke punten blijven afzonderlijk. DNS, DNQ, DNPQ, DSQ, uitval en een rijdende finish hebben verschillende betekenissen. Pole, beste kwalificatietijd en gridpositie 1 zijn niet automatisch hetzelfde; gebruik de officiële betekenis voor dat weekend.
- **Kwalificatieformats onderscheiden.** Losse historische eerste/tweede kwalificatiesessies zijn niet hetzelfde als moderne knock-outsegmenten Q1/Q2/Q3. Sprintformats en veranderingen in wat de Grand Prix-grid bepaalde krijgen een eigen sessietype.
- **Voorlopig of definitief.** Bij een lopend seizoen alleen een tussenstand tonen. Bewaar bronversie, beslis-/peildatum en eventuele latere correcties; benoem dat de huidige bronmomentopname voor 2026 tot ronde 17 loopt.
- **Geen dubbele telling.** Gedeelde auto’s, meerdere inschrijvingen, herstarts en dubbele bronregels worden gecontroleerd voordat starts, zeges, podia of punten worden opgeteld. Een primaire bronnotering blijft bewaard ook als individuele toerekening niet betrouwbaar mogelijk is.

### Welke getallen maken ieder onderdeel zelfstandig begrijpelijk?

Onderstaande waarden zijn de beoogde inhoud van de uiteindelijke onderdelen. Bestaande en voorgestelde berekeningen worden bij uitvoering apart geversioneerd; een bestaand label krijgt niet stilzwijgend een andere formule.

| Onderdeel | Eigen hoofdgetal en betekenis | Eigen figuur | Benodigde context bij het getal |
|---|---|---|---|
| Starter | Ruwe mediane positiewinst en aandeel winst/behoud/verlies; daarnaast voordeel boven vergelijkbare starts in posities | Eigen violins per gridpositie, fit en gecorrigeerde curve | Grid tot eerste doorkomst; pitlane uitgesloten; referentiepopulatie en nulbetekenis |
| Raceontwikkeling | Mediane positiewinst vanaf eerste doorkomst; daarnaast voordeel boven vergelijkbare vervolgtrajecten | Dezelfde twee onderzoeksgrafieken, gevoed met ronde 1 → finish | Alleen rijdende finishers; geen telling van zuivere inhaalacties |
| Vrije-baan-specialist / teamgenootduel | Mediane procentuele tempoafwijking tegenover de teamgenoot; negatief = sneller | Eigen tempoafwijking per race en teamperiode | Gedeelde ronden, compounds en bandenleeftijd; terugval op gemiddelden apart markeren |
| Metronoom — tempo in het veld | Mediane rondetijdrang, kwartielen en aantal individuele ronden; eventueel later een afzonderlijke genormaliseerde maat bij wisselende veldgrootte | Eigen rangen per circuit, violin en punten | Rang 1 = snelste gemeten rondetijd op dezelfde raceronde; geen racepositie; aantal geldige tijden in de referentie |
| Metronoom — regelmaat | Robuuste spreiding van afwijkingen rond de eigen stinttrend, als percentage van rondetempo; lager = regelmatiger | Eigen restafwijkingen rond nul, verdeling en ontwikkeling | Verwachte trend vangt geleidelijk tempoverloop op; een trage maar constante rijder kan hier goed scoren |
| Bandenfluisteraar | Verandering van relatief tempovoordeel per tien ronden bandenleeftijd; positief = beter behoud tegenover de gebruikte teamgenoot | Eigen gemeten leeftijd/tempoverloop per set en samenvatting per race | Zelfde compound en passend leeftijdsbereik; relatieve tempodegradatie is geen directe slijtagemeting |
| Pitwindow-specialist | Procentueel voordeel tegenover de eigen stinttrends in het afgebakende stopvenster; positief = sneller dan trend | Eigen vensters per race, verdeling en tijdlijn | Twee volledige ronden vóór inlap en twee na outlap; geen pitcrewduur of bewijs dat de strategie optimaal was |
| Opwarmer | Extra rondetijd bij bandenleeftijd 1–3 tegenover de eigen trend uit leeftijd 4–10, in procenten; lager = minder vroeg verlies | Eigen afwijking per bandenleeftijd en verdeling over nieuwe sets | Outlap uitgesloten; geen gemeten bandentemperatuur; gebruikte en nieuwe sets gescheiden |
| Uitval, incidenten en straffen | Aantallen en aandelen met technische, incident- of onbekende oorzaak; bevestigde straffen afzonderlijk | Eigen verdeling en tijdlijn | Bronstatus, finishdefinitie en verantwoordelijkheid gescheiden; straf niet automatisch oorzaak van uitval |

### De uitleg direct naast iedere kaart en grafiek

Gebruik voor alle onderdelen hetzelfde leespatroon:

1. **Wat is gemeten?** Bijvoorbeeld het behoud van tempo in een pitvenster, niet de snelheid van de monteurs.
2. **Wat betekent de waarde?** Eenheid, teken en nulpunt of referentie in één zin. Een 0–100-score krijgt een expliciete betekenis; geen onbenoemd rapportcijfer.
3. **Hoe ziet de verdeling eruit?** Eigen punten, mediaan en spreiding. Een gemiddelde zonder verdeling kan uitzonderlijke races verbergen.
4. **Waarop is dit gebaseerd?** Aantal ronden/starts/sets én aantal onafhankelijke races, periode, dekking en belangrijkste uitsluitingen.
5. **Wat weten we niet?** Alleen de beperkingen die de interpretatie van deze maat daadwerkelijk raken. Details blijven uitklapbaar.

Illustratieve tekst voor De metronoom: “Mediane rondetijdrang 4; de middelste helft van zijn ronden ligt tussen rang 2 en 7. Rang 1 is de snelste gemeten volledige ronde op dezelfde raceronde. Dit beschrijft zijn relatieve tempo met deze auto, niet zijn positie in de wedstrijd.” De voorbeeldcijfers zijn geen uitgerekende coureursresultaten. De werkelijke figuur vermeldt ook hoeveel tijden per ronde beschikbaar waren.

Illustratie voor regelmaat: bij een representatieve rondetijd van 100 seconden komt een robuuste spreiding van 0,3% overeen met ongeveer 0,3 seconde rond de eigen verwachte trend. Dit is geen maximumafwijking en geen garantie dat een bepaald percentage binnen 0,3 seconde valt. De uitleg werkt zonder een waarde van een andere coureur te tonen.

### Uitval, incidenten en straffen: vaste eigen feiten

Dit onderdeel hoort bij Coureurs, ook als de gegevens later een GOAT-vergelijking voeden. Het toont feiten over de geselecteerde rijder en diens periode, zonder een oordeel over andere coureurs nodig te hebben.

| Feitenblok | Wat zichtbaar wordt | Afbakening |
|---|---|---|
| Starts en finishes | Aantal race-starts, rijdende finishes en uitvalbeurten | DNS apart; een geklasseerde coureur die vóór de finish stilviel is niet automatisch een rijdende finisher; DSQ is een afzonderlijke uitslagstatus |
| Technische uitval | Aantallen en waar bekend onderdelen/oorzaken: motor, transmissie, ophanging enzovoort | Bronoorzaak behouden; schade na een botsing niet zonder bewijs als zelfstandig technisch defect behandelen |
| Uitval door ongeluk of incident | Botsing, zelfstandig ongeval en overige bevestigde incidentoorzaken | Oorzaak en verantwoordelijkheid apart; een zelfstandige crash bewijst op zichzelf geen rijderfout |
| Verantwoordelijkheid | Eigen verantwoordelijkheid vastgesteld, verantwoordelijkheid van een ander vastgesteld, gedeelde verantwoordelijkheid vastgesteld, of niet vastgesteld | Officiële beslissing en reikwijdte vermelden. Een besluit over overwegende verantwoordelijkheid letterlijk in betekenis behouden; niet omzetten naar exclusieve schuld |
| Straffen | Aantal beslissingen, type, reden en opgelegde sanctie: tijd, drive-through, stop-go, gridstraf, diskwalificatie en strafpunten waar bekend | Tijdstraffen, gridplaatsen en strafpunten blijven verschillende eenheden; opgelegd en daadwerkelijk verwerkt onderscheiden waar de bron dat ondersteunt |
| Verband straf–incident–uitval | Welke bevestigde straf bij welk incident en eventueel welke uitval hoort | Alleen koppelen als de beslissing of andere controleerbare bron het verband ondersteunt; tijdsnabijheid of deelname aan dezelfde race is onvoldoende |
| Onbekend en dekking | Uitval met onbekende oorzaak, incidenten zonder vastgestelde verantwoordelijkheid en races zonder volledige strafdocumentatie | Geen gevonden straf betekent alleen nul bij voldoende volledige registratie; anders onbekend of onvolledig |

De presentatie bestaat uit compacte eigen totalen, een verdeling naar uitvaloorzaak en een eigen tijdlijn. Een uitklapbaar incident- of straffenlog geeft per gebeurtenis race, datum/ronde waar bekend, betrokken rijder, oorzaak, bron, beslissing en eventuele gekoppelde uitval. Dit is een gericht feitenlog, geen terugkeer van de verwijderde algemene tabel Onderliggende races.

Tel unieke uitvalbeurten één keer in het uitvaltotaal. Een uitval kan daarnaast gekoppeld zijn aan een incident en een straf; die feiten mogen niet worden opgeteld als drie uitvalbeurten. Meerdere besluiten over één gebeurtenis blijven als besluiten herkenbaar en worden niet ongemerkt meerdere bestrafte races. Races, gebeurtenissen, besluiten en sancties krijgen daarom ieder een eigen teldefinitie. Geef bij percentages steeds de noemer: bijvoorbeeld technische uitval per gestarte race of per uitvalbeurt.

Ook een straf die de geselecteerde rijder ontving nadat een ander uitviel, is een eigen feit. Een straf voor een ander kan als broncontext bij een incident van de geselecteerde rijder verschijnen, zonder de pagina tot een onderlinge vergelijking te maken. Overgenomen bronbeschrijvingen en modelmatig afgeleide classificaties blijven onderscheiden; onbevestigde verantwoordelijkheid wordt niet als feit gepresenteerd.

GOAT kan vervolgens uitvalrisico en bevestigde incidentverantwoordelijkheid tussen coureurs onderzoeken, met correctie voor bijvoorbeeld de technische betrouwbaarheid van auto en tijdperk. De eigen aantallen en gebeurtenissen blijven altijd bij Coureurs staan; ze verhuizen niet mee met die vergelijkende analyse.

### Referentie, weging en bereik bij Coureurs

- De eigen waarnemingen blijven altijd herkenbaar. Referentiewaarden mogen voor een score worden gebruikt, maar worden uitgelegd als een meetlat, niet als extra profielen in beeld. De teamgenoot blijft de expliciete uitzondering.
- De huidige Metronoom houdt alle individuele ronderangen. Langere races leveren meer punten. Benoem daarom een samenvatting als *over alle bruikbare ronden*; een samenvatting die eerst per race weegt krijgt een ander label en wordt apart berekend.
- Voor maten op set- of stopniveau: leg de tussenstappen vast, bijvoorbeeld eerst een mediaan per race, daarna over races. Verwar het aantal rondes niet met het aantal onafhankelijke races.
- Een ruwe rang 4 van 12 gemeten tijden is iets anders dan rang 4 van 22. Behoud beide getallen. Onderzoek een genormaliseerde rang met vastgelegde behandeling van gelijke tijden, zonder de bestaande ruwe rangen te vervangen of te doen alsof alle starters een tijd hebben geleverd.
- Definieer vóór gebruik een minimale dekking van het gemeten veld per ronde. Een rang uit een onvolledige timingtabel krijgt geen volledige-veldbetekenis. Rapporteer de gebruikte drempel en uitgesloten ronden.
- Geen gegevens geeft onbekend, geen nul. Geen geschikte referentie geeft wel een ruwe eigen uitkomst waar mogelijk, maar geen verzonnen gecorrigeerde score.
- Extrapolatie blijft als model herkenbaar en beperkt tot verdedigbare veldgrootten en context. Assen mogen P23/P24 tonen zonder data of curve voor een rijder die nooit in zo’n veld reed.

## 4. Opzet voor de module GOAT

### Volgorde en functies

1. **De vergelijkingsvraag.** Kies eerst een eigenschap: starts, raceontwikkeling, tempo, regelmaat, bandenbehoud, pitvenster of opwarming. Daarna de vergelijking: binnen hetzelfde veld, in een gedeelde periode, of tussen tijdperken. Begin niet met één ongedefinieerde totaalranglijst.
2. **Coureurs en bereik.** Een overzicht kan alle voldoende onderbouwde coureurs bevatten; een detailvergelijking toont een klein aantal tegelijk. Keuze uit hele carrière, een vooraf gedefinieerde piekperiode of leeftijdsfase. Deze keuzes zijn zichtbaar en worden niet door elkaar gebruikt.
3. **De gemeenschappelijke meetlat.** Toon welke omstandigheden gelijkgetrokken zijn, welke werkelijk overlappen en welke door een model worden overbrugd. Laat de beschikbare dekking bepalen of de vergelijking mogelijk is.
4. **Het vergelijkingsbord.** Tabel of punten met score/eenheid, interval, bruikbare races, dekking en status gemeten/modelafhankelijk. De huidige veldfiguren van Metronoom, pitwindow en opwarmer kunnen hiervoor als eerste verkenning dienen.
5. **Verdieping per eigenschap.** Dezelfde figuurtaal als bij Coureurs, nu met meerdere coureurs op gelijke assen en met dezelfde referentie. Startprofielen per beginpositie, eigen rondeverdelingen, pitvensters en opwarmcurven worden hier onderling vergelijkbaar gemaakt.
6. **Van feit naar vergelijking.** Laat zien wat verandert tussen ruwe carrière-uitkomst, contextcorrectie en eventuele autocorrectie. Verschillen door data of weging mogen niet ongemerkt als vaardigheid verschijnen.
7. **Over de generaties heen.** Toon waar teamgenootrelaties en overlappende carrières informatie leveren en waar de verbinding zwak is of ontbreekt. Een onbekende relatie blijft onbekend; het model bewijst geen fictief rechtstreeks duel.
8. **Hoe robuust is de conclusie?** Effect van andere redelijke gewichten, perioden, selecties en aannames. Geen stellige winnaar als kleine verschillen binnen grote onzekerheid vallen.

Een koppeling bij een eigen specialisme kan naar GOAT gaan met rijder, periode en eigenschap meegenomen. Terug naar het eigen profiel behoudt die context. De pagina’s delen rekenwerk en definities; GOAT krijgt een eigen vergelijkingsselectie en verandert niet ongemerkt de selectie van Coureurs.

Een afzonderlijke vergelijkingsingang kan de basisfeiten — titels, WK-posities, punten, kwalificaties, zeges, podia en poles — naast elkaar zetten. Label dit als een vergelijking van prestaties en loopbanen. Het wordt pas onderdeel van een kwaliteitsoordeel na de relevante contextcorrectie. De eigen feiten blijven bij Coureurs beschikbaar, ook als een tijdperkcorrectie voor GOAT niet mogelijk is.

### Drie vergelijkingsniveaus, in deze volgorde bouwen

| Niveau | Vraag | Voorwaarde | Wat nog niet geclaimd wordt |
|---|---|---|---|
| Veldcontext | Hoe verschillen de geobserveerde prestaties van deelnemers in dezelfde races? | Overeenkomende meetdefinities, expliciete bruikbare ronden/sets en dekkingsrapportage | Geen volledige correctie voor auto of verschillende gereden omstandigheden |
| Gedeelde omstandigheden | Wie presteert beter onder dezelfde verdeling van beginposities, circuits en relevante context? | Voldoende overlap, vaste gemeenschappelijke gewichten en referentie zonder eigen bijdrage | Geen zekere uitspraak over omstandigheden buiten die overlap |
| Vergelijking over tijdperken | Wat schat het model wanneer tegenstanders, auto’s, reglement en circuits veranderen? | Gevalideerde verbindingen tussen perioden, gevoeligheidsanalyse en zichtbaar bredere onzekerheid | Geen aanname dat alle generaties met beschikbare timing automatisch vergelijkbaar zijn |

Voor een tijdperkvergelijking is een rondetijdrang alleen onvoldoende: een rang hangt ook af van de kracht en samenstelling van het veld. Ook een teamgenootketen kan auto en rijder niet volledig uit elkaar halen. Schattingen krijgen daarom een expliciete modelstatus; ontbrekende oude bandengegevens worden geen slechte bandenbeheerscore. Een eventuele totaalscore gebruikt voor iedereen dezelfde beschikbare dimensies of verschijnt niet voor die vergelijking.

### Wat juist niet naar GOAT hoeft

De eigen violins, eigen tijdlijn, zelfstandig uitlegbare score en teamgenootduels verdwijnen niet bij Coureurs omdat dezelfde feiten ook GOAT kunnen voeden. Verplaatsen betreft de **vergelijkende presentatie**. Bronwaarnemingen en rekenfuncties worden gedeeld en niet als een tweede los onderhouden databestand gekopieerd.

## 5. Uitvoering van deze herindeling

- [ ] **Definities vastleggen.** Maak per maat één specificatie met vraag, eenheid, teken, referentie, selectieregels, weging, minimumdekking en definitieversie. Benoem de twee aspecten van Metronoom afzonderlijk. Leg ook de huidige Starter-score, curvebalans en winstgrens vast voordat een opvolger wordt berekend.
- [ ] **Basisfeiten uit de bewaarde bron ontsluiten.** Hergebruik het complete F1DB-archief voor WK-punten/standen, kwalificatie en loopbaanfeiten, naast de reeds gekoppelde racegegevens. Controleer ontbrekende WK-noteringen, nulpuntenseizoenen en recentere races. Maak een compacte race-/seizoenslaag per coureur; stuur geen volledige bronarchieven naar de browser.
- [ ] **Feitentotalen toetsen.** Controleer eigen seizoentotalen tegen de bronnoteringen, officiële WK-punten tegen geldende telregels, kwalificatie tegenover werkelijke grid en gedeelde deelnames op dubbeltellingen. Leg per parameter en jaar vast wat beschikbaar, gekoppeld, getoond en nog te verifiëren is op de datacollectiepagina zodra dit wordt gebouwd.
- [ ] **De eigen pagina eerst herstellen.** Maak de eigen figuren bij Metronoom, pitwindow en opwarmer de hoofdweergave. Behoud de start- en vervolgonderzoeken, de zes kaarten en het teamgenootduel. Verwijder de zichtbare volledige-veldvergelijkingen uit het coureursprofiel.
- [ ] **Zelfstandige uitleg toevoegen.** Iedere kaart en figuur voldoet aan het vijfdelige leespatroon hierboven. Geen percentile zonder benoemde referentie, geen andere coureur nodig om de eigen waarde te begrijpen. Nummer–teamkleur–code en volledige paarse naam blijven de profielidentiteit.
- [ ] **Eigen feiten over uitval en straffen uitwerken.** Maak de brongebonden indeling hierboven, met technische versus incidentoorzaken, vastgestelde verantwoordelijkheid en controleerbare koppelingen. Toon eigen aantallen en noemers, onderscheid nul en ontbrekende registratie en voorkom dubbeltellingen.
- [ ] **GOAT-verkenning bouwen.** Hergebruik de drie verplaatste veldweergaven, zichtbaar als beschrijvende vergelijking. Verhuis geen onbekritische ranglijst als reeds gevalideerde kwaliteitsscore.
- [ ] **Gemeenschappelijke vergelijking bouwen.** Voer de verbeteringen voor start- en raceontwikkeling hieronder uit: werkelijke veldgrootte, passende referentie, uitsluiting van eigen referentiebijdrage, gedeelde gewichten en controle op overlap. Pas dezelfde ontwerpprincipes per andere eigenschap inhoudelijk aan.
- [ ] **Validatie en tijdperkmodel.** Controleer selectie-effecten en intervallen met volledige races als eenheid; duizenden ronden maken geen duizenden onafhankelijke races. Houd toetsraces apart. Onderzoek periode- en teamafhankelijkheid en pas daarna verbindingen over generaties.
- [ ] **Koppelingen en onderhoud.** Deel brondata en berekeningen, laad vergelijkingsgegevens pas waar nodig en houd definitie/filters in verwijzingen consistent. Werk de datacollectiepagina bij zodra gegevens, selectieregels of afgeleide parameters veranderen.

### Acceptatiecriteria voor de scheiding

- Bij Coureurs staat precies één rijder centraal. Alleen in het expliciete teamgenootonderdeel en bij benoemde teamgenootreferenties verschijnt de werkelijke teamgenoot; geen volledig veld in een vergelijkingsgrafiek.
- Elk specialisme heeft een eigen maat met eenheid, richting, betekenis, verdeling en dekking, of een concrete melding dat de benodigde data ontbreken. De waarde is zonder de getallen van andere coureurs te begrijpen.
- Het eigen feitenblok omvat WK-punten, seizoens-/tussenstand, kwalificatie en gecontroleerde basisstatistieken. Periode en peildatum zijn zichtbaar; een ontbrekende WK-positie wordt niet uit nul punten of een lege bronregel verzonnen. Officiële punten en een eventuele genormaliseerde GOAT-maat krijgen verschillende labels.
- Metronoom toont iedere geaccepteerde individuele ronde van de gekozen rijder per circuit. Ronderang en regelmaat hebben afzonderlijke labels en worden niet als dezelfde eigenschap uitgelegd.
- Uitvaloorzaken, vastgestelde verantwoordelijkheid en straffen zijn als eigen feiten bij Coureurs beschikbaar voor zover onderbouwd. Onbekende oorzaken of ontbrekende documenten worden niet omgezet in eigen schuld of een nulwaarde.
- Bij GOAT zijn onderlinge vergelijking, gemeenschappelijke meetlat, onzekerheid en beperkingen direct zichtbaar. Bestaande profielgemiddelden worden niet zonder standaardisatie tot GOAT-score verheven.
- Een gedeelde maat levert voor dezelfde rijder, definitieversie en selectie dezelfde bronuitkomst in beide modules. Extra GOAT-correcties zijn een afzonderlijke stap met een eigen label.
- Grafieken houden de stijlgids aan: paars voor Coureurs, goud voor GOAT, teamkleuren voor rijderidentiteit; vaste y-as en beter/slechter-pijlen bij horizontaal scrollen, informatieve hover zonder onbedoelde selectiewijziging. Groen/rood blijft functioneel voor gunstig/ongunstig.
- NL en EN beschrijven dezelfde meetlat. Verwijderde algemene onderdelen zoals Onderliggende races en Alle rijders als referentie keren niet terug op de coureurspagina.

De bestaande detailpunten hieronder blijven gelden als verdieping van dit plan. Waar sprake is van een zichtbare vergelijking met andere coureurs, hoort die bij GOAT, behalve de expliciet behouden teamgenootvergelijking.

## Positiewinst en positieverlies

### Twee afzonderlijke racefasen

| Onderdeel | Beginpositie S | Resultaatpositie E | Huidige selectie |
|---|---|---|---|
| De starter | Werkelijke gridpositie | Positie bij eerste doorkomst na ronde één | Bekende gridstart en doorkomst; pitlanestarts uitgesloten |
| Raceontwikkeling | Positie bij eerste doorkomst na ronde één | Eindklassering | Alleen bevestigde rijdende finishers met beide posities bekend |

In beide fasen is de ruwe positiewinst **S − E**. Die is begrijpelijk en blijft zichtbaar. Verschillende fasen krijgen eigen referenties: een start vanaf P8 is geen uitwisselbare waarneming met een doorkomst op P8 na ronde één.

### Verdeling over Coureurs en GOAT

| Analyse | Coureursgedeelte | GOAT gedeelte |
|---|---|---|
| Eigen winst en verlies per beginpositie | Hoofdonderdeel: violins, losse races, mediaan, kwartielen en modelcurve | Achtergrond bij een vergelijking, met identieke filters |
| Eigen ontwikkeling per seizoen of teamperiode | Hoofdonderdeel: wanneer veranderde het patroon? | Gebruiken om carrièrepieken en leeftijdsfasen zorgvuldig te vergelijken |
| Resultaat tegenover vergelijkbare starts | Context bij de eigen prestaties, inclusief afwijking in posities | Basis voor onderlinge vergelijking, na standaardisatie van omstandigheden |
| Positie behouden vanaf P1 | Tonen hoe vaak het lukte en hoe gebruikelijk behoud in die context is | Belonen ten opzichte van dezelfde referentie; geen automatische maximumscore |
| Verhouding S/E | Eventueel aanvullend beschrijvend cijfer, met de beperkingen uitgelegd | Geen primaire kwaliteitsscore of rangschikking |
| Gemeenschappelijke verdeling van beginposities en circuits | Geen onderlinge vergelijkingsmodus; alleen uitleg bij de eigen referentiemaat | Vereist voor een vergelijkbare totaalscore |
| Correctie voor auto, tijdperk en startomstandigheden | Uitleg bij een gemeten verandering; ruwe uitkomsten blijven beschikbaar | Afzonderlijke modelstap met aannames en onzekerheid |
| Uitval en incidenten | Apart carrièreprofiel naast resultaten bij finish | Apart beoordelingsonderdeel; betrouwbaarheid niet laten verdwijnen door alleen finishers te vergelijken |
| Ontbrekende beginposities | Lege gemeten kolommen; modelvoorspelling duidelijk onderscheiden | Beperken tot gedeelde onderbouwing of de extra modelafhankelijkheid expliciet tonen |
| Totale ranglijst | Geen standaardonderdeel van het individuele profiel | Pas na validatie en met zichtbare dekking, intervallen en gekozen gewichten |

## Verbeteringen voor het coureursgedeelte

- [ ] **Behoud de eigen verdelingen.** Laat per beginpositie alle bruikbare races van de gekozen coureur zien. Behoud de huidige violins, medianen, kwartielen, vaste niet-lineaire weergaveschaal en y-as die bij horizontaal scrollen blijft staan.
- [ ] **Voeg resultaat boven verwachting toe.** Bereken per race de verwachte resultaatpositie uit vergelijkbare waarnemingen en trek de werkelijke positie daarvan af. Een positieve waarde betekent beter dan verwacht, uitgedrukt in posities.
- [ ] **Toon uitzonderlijkheid naast omvang.** Een vergelijking met de volledige referentieverdeling laat zien hoe gebruikelijk de uitkomst is. De huidige score telt slechtere referentieresultaten volledig en gelijke resultaten voor de helft. Dat is geen winstkans of percentage persoonlijke vaardigheid.
- [ ] **Maak de eigen context zichtbaar.** Toon welke beginposities, circuits, jaren en weersomstandigheden bijdragen. Een eigen carrièregemiddelde beschrijft de gereden carrière; het heeft niet vanzelf dezelfde betekenis als het gemiddelde van een andere coureur.
- [ ] **Onderzoek veranderingen binnen de carrière.** Vergelijk perioden bij voorkeur binnen gedeelde omstandigheden, zodat een verschuiving van achterhoede naar voorhoede niet ongemerkt als verandering in startvaardigheid verschijnt.
- [ ] **Maak raceontwikkeling uitlegbaar.** Positiewinst na ronde één kan ontstaan door baanacties, pitcycli, uitval van anderen en straffen. Splits alleen oorzaken uit die de bron ondersteunt. Onbekende oorzaken blijven onbekend.
- [ ] **Scheid finishprestaties en uitval.** Het huidige tweede onderzoek beschrijft positieontwikkeling bij uitgereden races. Voeg daarnaast een afzonderlijk overzicht toe van technische uitval, incidenten en onbekende oorzaken. Een botsing of straf bewijst niet automatisch persoonlijke schuld.

### Rekenvoorbeeld voor resultaat boven verwachting

De cijfers hieronder zijn illustratief en geen berekende coureursresultaten.

| Begin | Verwachte positie na ronde één | Werkelijk resultaat | Ruwe winst | Voordeel boven verwachting |
|---|---:|---:|---:|---:|
| P1 | 1,5 | P1 | 0 | +0,5 |
| P20 | 16,0 | P17 | +3 | −1,0 |
| P6 | 6,8 | P4 | +2 | +2,8 |

Een verwachting van 1,5 is een gemiddelde van mogelijke posities. P1 behouden kan daarmee een goede prestatie zijn. Drie plaatsen winnen achteraan kan juist minder zijn dan vergelijkbare starters gemiddeld bereiken.

Bij de verdelingsscore scoort P1 behouden 60/100 als 80% van de referentie P1 behoudt en 20% plaatsen verliest: 20 + ½ × 80. Als slechts 20% P1 behoudt, wordt dat 90/100: 80 + ½ × 20. Behoud krijgt dus betekenis vanuit de context.

## Verbeteringen voor GOAT

- [ ] **Leg één vergelijkingsvraag vast.** Beoordeel starts en raceontwikkeling afzonderlijk. Kies expliciet tussen een carrièrebeschrijving, een vergelijking op gedeelde omstandigheden en een modelmatige vergelijking over tijdperken.
- [ ] **Controleer de werkelijke veldgrootte.** De huidige vergelijkingscode gebruikt een benadering op basis van het deelnemersaantal met een minimum van twintig. Dat is vooral voor oude races onvoldoende precies. Maak een gecontroleerd startersaantal apart van inschrijvingen, niet-starters, de grootste gridpositie en de lengte van de getekende as.
- [ ] **Verfijn de referentie.** Gebruik beginpositie, bevestigde veldgrootte, circuitvariant, periode en waar bekend droog/nat en starttype. Houd normale gridstarts, pitlanestarts, herstarts en starts achter de safetycar gescheiden.
- [ ] **Sluit de eigen referentiebijdrage uit.** De te beoordelen coureur mag zijn eigen referentie niet naar zijn prestaties trekken. Houd ook rekening met de afhankelijkheid tussen waarnemingen uit dezelfde race.
- [ ] **Standaardiseer naar dezelfde omstandigheden.** Gebruik voor alle vergeleken coureurs dezelfde vooraf vastgelegde verdeling van beginposities, circuits en overige context. Het aantal eigen starts is een maat voor precisie, niet automatisch het juiste gewicht voor een gemeenschappelijke meetlat.
- [ ] **Controleer gedeelde onderbouwing.** Laat zien welke contexten bij alle betrokken coureurs voldoende ondersteund zijn en welk deel van hun carrières daardoor meetelt. Een vergelijking op alleen overlap heeft een smallere doelgroep dan een uitspraak over de volledige carrière.
- [ ] **Behandel dun bezette contexten voorzichtig.** Onderzoek een hiërarchisch model dat informatie uit verwante situaties beperkt deelt. Onderscheid gemeten vergelijking en modelschatting. Een ontbrekende start vanaf P1 wordt geen waargenomen start; extrapoleer niet naar een veldgrootte waarin de coureur nooit reed.
- [ ] **Onderzoek autocorrectie afzonderlijk.** Gebruik team en seizoen, teamgenootrelaties en vóór de betreffende race beschikbare informatie over competitiviteit. Gebruik niet dezelfde einduitslag als correctiefactor voor het resultaat dat beoordeeld wordt. Een keten van teamgenoten over generaties maakt auto en coureur niet volledig identificeerbaar.
- [ ] **Rapporteer onzekerheid en dekking.** Toon een voordeel in posities, een gestandaardiseerde verdelingsscore en bijbehorende onzekerheid. Onderzoek resampling per race en afhankelijkheid tussen seizoenen. Een betrouwbaarheidsinterval vangt niet automatisch ontbrekende context of verkeerde modelaannames op.
- [ ] **Valideer vóór een ranglijst.** Controleer uitkomsten op apart gehouden races, gevoeligheid voor referentieperiode, andere gewichten en definities van uitval. Een kleine voorsprong met veel onzekerheid rechtvaardigt geen stellige nummer één.
- [ ] **Beoordeel uitval apart.** Een finisherselectie is bruikbaar voor positieontwikkeling, maar kan een coureur met veel uitval te gunstig laten lijken. Onderzoek gezamenlijke modellen of een afzonderlijke uitvaldimensie. Technische uitval niet willekeurig op nul zetten en incidentuitval niet automatisch als eigen fout behandelen.

### Waarom dezelfde gewichten noodzakelijk zijn

Illustratief voorbeeld met twee groepen omstandigheden. In de echte analyse wordt deze indeling verfijnd naar de gekozen contexten.

| Coureur | Voordeel vooraan | Voordeel achteraan | Eigen verdeling vooraan en achteraan | Eigen gewogen gemiddelde | Gemeenschappelijke verdeling 50/50 |
|---|---:|---:|---|---:|---:|
| A | +0,4 | +1,2 | 90% en 10% | +0,48 | +0,80 |
| B | +0,2 | +1,0 | 10% en 90% | +0,92 | +0,60 |

A presteert in beide groepen beter, maar B krijgt met zijn eigen omstandigheden toch het hoogste gemiddelde. De gemeenschappelijke verdeling maakt de vergelijking inhoudelijk beter passend. Alleen alle gridvakken even zwaar wegen is nog onvoldoende wanneer circuits en omstandigheden blijven verschillen.

### Aanbevolen presentatie voor GOAT

Een overzichtstabel toont per coureur de gestandaardiseerde score, voordeel in posities, onzekerheidsinterval, aantal races en dekking van de gemeenschappelijke referentie. Daarnaast komt een vergelijking van twee tot vier coureurs per beginpositie, met dezelfde assen en dezelfde referentiecurve. Maak de verandering door correctie zichtbaar: eigen ruwe uitkomst, contextcorrectie en eventuele autocorrectie. Laat uitval als afzonderlijke dimensie zien.

Publiceer geen overkoepelend GOAT-cijfer zonder een expliciete keuze voor de gewichten van start, raceontwikkeling, tempo en overige eigenschappen. Toon hoe de volgorde verandert bij redelijke alternatieve gewichten.

## Verhouding van posities als aanvullende index

De eerder voorgestelde voorbeelden beschrijven **S/E**, niet positiewinst gedeeld door de beginpositie. P2 naar P1 geeft 2, P1 naar P2 geeft 0,5 en behoud geeft 1.

Leg vóór gebruik vast of de index het gemiddelde van individuele verhoudingen is, of per beginpositie S gedeeld door de gemiddelde resultaatpositie met daarna weging naar aantallen. Die twee berekeningen zijn niet gelijk. Een rekenkundig gemiddelde van 2 en 0,5 is 1,25; een geometrisch gemiddelde is 1. Een geometrisch gemiddelde behandelt deze omgekeerde bewegingen symmetrischer, maar corrigeert nog steeds niet voor verschillende kansen vanaf verschillende posities of circuits.

Bewaar de ratio daarom hoogstens als aanvullend beschrijvend cijfer op de coureurspagina. Gebruik voor GOAT bij voorkeur de contextvergelijking en gemeenschappelijke meetlat hierboven.

## Uitvoeringsvolgorde en oplevercriteria

1. Verifieer startersaantallen, circuitvarianten en relevante start- en weerscontext. Registreer dekking in de datacollectiepagina.
2. Voeg verwacht resultaat en afwijking in posities toe aan de individuele analyses, met dezelfde definitie voor kaart, grafiek en opgeslagen tabel.
3. Bouw een eerste GOAT-vergelijking op gedeelde contexten en vaste gewichten. Houd de gemeten vergelijking en modelmatige uitbreiding afzonderlijk herkenbaar.
4. Valideer intervallen en gevoeligheid, inclusief selectie op finishers en verschillen tussen tijdperken.
5. Overweeg pas daarna autocorrectie en een overkoepelende vergelijking van meerdere kwaliteiten.

Een wijziging is gereed wanneer de selectieregels vastliggen, de voorbeelden reproduceerbaar kloppen, bestaande waarnemingen behouden blijven, de dekking zichtbaar is en Nederlands en Engels dezelfde betekenis hebben. De huidige grafieken en opgeslagen Starter-metrieken blijven de bestaande definitieversie gebruiken totdat een nieuwe versie expliciet is gebouwd en gecontroleerd.

Methodologische achtergrond bij het vergelijken op een gemeenschappelijke doelpopulatie: [Li en Li, Propensity Score Weighting for Causal Inference with Multiple Treatments](https://arxiv.org/abs/1808.05339). De hierboven beschreven toepassing op coureurs is een ontwerpkeuze voor deze site; standaardisatie alleen bewijst geen causale rijvaardigheid.
