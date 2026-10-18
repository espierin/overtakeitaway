# Overtake It Away totaalplan voor fase 2

**Versie 2 — 17 oktober 2026**

**Doel:** bouw een controleerbaar coureursprofiel en een afzonderlijke vergelijking tussen coureurs en tijdperken, op een gedeelde databasis. Verdiep daarna de strategieatlas, raceverslagen en vooruitblikken.

Dit is het leidende plan voor fase 2. Het vervangt de eerdere onderzoeksopzet en verwerkt de afspraken uit de [verbeterlijst](verbeterlijst.md). Die lijst blijft de gedetailleerde werklijst. De [vorige versie](fase-2-onderzoeks-en-ontwikkelplan-archief-20261017.md) blijft beschikbaar als onderzoeksarchief. Bij een verschil gaat dit totaalplan voor; nieuwe besluiten worden in beide actuele documenten bijgewerkt.

De volgende stap is de coureursmodule inhoudelijk ordenen en verrijken. Een volledige GOAT-ranglijst is een latere uitkomst van gecontroleerde vergelijkingen, geen startpunt. Dit plan beschrijft ontwikkelwerk; het is geen verslag van reeds uitgevoerde wijzigingen aan de website. De lokale uitvoering op de afzonderlijke `_2`-pagina’s en de resterende onderzoekspoorten staan in het [uitvoerings- en controleverslag](../_development/IMPLEMENTATION.md).

## 1 De productbelofte en de grenzen

Overtake It Away laat zien wat er op de baan gebeurde, wat een coureur zelf heeft laten zien en hoe prestaties zich onder vergelijkbare omstandigheden tot elkaar verhouden. Iedere analytische uitspraak moet terug te voeren zijn op waarnemingen, definities en een reproduceerbare berekening.

| Onderdeel | Centrale vraag | Hoofdinhoud |
|---|---|---|
| Races | Wat gebeurde er tijdens deze Grand Prix? | Uitslag, verloop, starts, posities, pitcycli en bekende gebeurtenissen |
| Coureurs | Wat laat deze rijder zien en hoe ontwikkelt dat zich? | Eigen loopbaanfeiten, verdelingen, specialismen en teamgenootduel |
| GOAT | Wie presteert beter op welke eigenschap, en hoe eerlijk is die vergelijking? | Vergelijkingen binnen velden, op gedeelde omstandigheden en later tussen tijdperken |
| Strategieatlas | Onder welke omstandigheden werkte eerder, later, meer of minder stoppen? | Kandidaat-pitcycli, eigen stopprogramma’s, tijd- en positiewinst, context |
| Verslag en vooruitblik | Wat kunnen we onderbouwd zeggen over deze en de volgende race? | Bevindingen met grafieken, later vooraf vastgelegde verwachtingen |

De strategieatlas blijft inhoudelijk verbonden met Races en Coureurs. Een aparte hoofdingang komt pas bij voldoende inhoud; fase 2 wijzigt daarvoor niet automatisch de bestaande hoofdnavigatie.

De website blijft statisch te publiceren, tweetalig en binnen de ingestelde opslaggrenzen. Bronarchieven en zware berekeningen blijven buiten de interactieve pagina’s. Uitvoering gebeurt eerst lokaal; nieuwe publicatie volgt pas op een expliciete opdracht daarvoor.

## 2 De huidige uitgangspositie

De cijfers hieronder zijn momentopnamen van de bewaarde bouw- en publicatiebestanden. Dekking wordt per analyse vastgesteld; het bestaan van een race of profiel betekent niet dat alle metingen beschikbaar zijn.

| Onderdeel | Aangetroffen uitgangspositie | Gevolg voor de bouw |
|---|---|---|
| Coureursomgeving | Bouwrapport met 1950–2026, 1.166 races, 817 profielen en 26.157 coureur-raceregels | Volledige historische reikwijdte behouden waar feiten beschikbaar zijn |
| Individuele ronderangen | 639.012 bewaarde ronderangen in het bouwrapport | Iedere geschikte ronde blijft een datapunt; niet terugbrengen tot één punt per race |
| Start en raceontwikkeling | Eigen verdelingen, modelcurven, onzekerheidsbanden en onderzoek van ronde 1 tot finish bestaan | Grafische aanpak behouden; definities en context verder controleren |
| Teamgenootduel | Tempo door de tijd met teamperioden, verschillende meetstatussen en vaste procentas bestaat | Binnen Coureurs behouden en zelfstandig uitleggen |
| Veldvergelijkingen | Metronoom, pitwindow en opwarming tonen ook andere coureurs | Vergelijkende presentaties naar GOAT verplaatsen; eigen figuren blijven bij Coureurs |
| Bandenspecialismen | Berekeningen bestaan, maar set-, leeftijds- en verkeersdekking is beperkt | Per specialisme tonen wat echt berekenbaar is |
| Incidenten en straffen | Bewaarde uitvalstatussen en aanvullend incidenten-/besluitenmateriaal | Feitenoverzicht ontsluiten; dekking en verantwoordelijkheid controleren |
| Basisfeiten | Rijk F1DB-bronarchief aanwezig; WK- en kwalificatiegegevens nog niet volledig in profieluitvoer | Eerst koppelen en controleren, niet opnieuw integraal verzamelen |
| GOAT | Ontwerppagina met Winter break-status, geen gevalideerde GOAT-score | Eerst vergelijking per eigenschap bouwen |
| Publicatie | Controlebestand van 16 oktober 2026: 281.252.427 websitebytes | Groei toetsen aan het eigen budget van 900.000.000 bytes |

Het actuele [bouwrapport](../assets/phase2-build-report.json) en de [datacollectiepagina](../data-collection.html) blijven de ingang naar dekking en herkomst. Oude documenten met een beperking tot vijf seizoenen of uitsluitend een lokale eerste versie beschrijven eerdere opleveringen en bepalen niet meer de totale historische scope.

## 3 De scherpe scheiding tussen Coureurs en GOAT

**Coureurs beschrijft één rijder. GOAT vergelijkt rijders. De rechtstreekse teamgenootvergelijking blijft een expliciete uitzondering binnen Coureurs.**

De plaats van een analyse hangt af van de vraag en de presentatie. Een eigen rondetijdrang gebruikt het veld als referentie. Een eigen startvoordeel kan uit vergelijkbare starts van andere coureurs worden berekend. De coureurspagina toont vervolgens de eigen waarde en verdeling, met voldoende uitleg om die zelfstandig te begrijpen.

Drie lagen blijven herkenbaar:

1. **Waarneming:** bijvoorbeeld P8 naar P6 in de eerste ronde, of rondetijdrang 4 van 20 gemeten tijden.
2. **Eigen contextmaat:** bijvoorbeeld 0,4 positie beter dan een passende startreferentie verwacht.
3. **Onderlinge vergelijking:** verschillende coureurs beoordeeld met dezelfde verdeling van omstandigheden en dezelfde meetlat.

De eerste twee passen bij Coureurs. De derde hoort bij GOAT. Een kampioenschapspositie blijft een eigen feit, ook al is een kampioenschap relatief. Een overzicht dat meerdere loopbanen daarop rangschikt is een GOAT-weergave.

Bij Coureurs is één profiel tegelijk geselecteerd. Andere coureurs verschijnen daar alleen als werkelijk betrokken teamgenoot of als noodzakelijke context bij een concrete gebeurtenis, zoals een incidentbesluit. Er komt geen volledige-veldgrafiek of verborgen vergelijkingsmodus op de coureurspagina.

Het teamgenootduel laat prestaties binnen teamperioden zien. Het is bruikbare context, maar geen bewijs van identieke auto’s, schade, strategie of opdrachten. GOAT kan dezelfde metingen later gebruiken voor een breder model.

## 4 De opbouw van Coureurs

### 4.1 De volgorde op de pagina

| Volgorde | Blok | Wat de bezoeker ermee begrijpt |
|---|---|---|
| 1 | Het coureursprofiel | Identiteit, gekozen periode, kernfeiten en zes specialismen |
| 2 | De starter | Winst en verlies van grid tot eerste doorkomst |
| 3 | Het vervolg van de race | Positieontwikkeling na ronde één tot finish |
| 4 | Het teamgenootduel | Relatief tempo en ontwikkeling binnen teamperioden |
| 5 | De metronoom | Eigen rondetijdrangen per circuit en afzonderlijk de regelmaat |
| 6 | De bandenfluisteraar | Behoud van relatief tempo bij ouder wordende banden |
| 7 | De pitwindow-specialist | Uitvoering in de ronden rond beslissende stops |
| 8 | De opwarmer | Tempo in de eerste bruikbare ronden op nieuwe sets |
| 9 | Uitval incidenten en straffen | Eigen gebeurtenissen, oorzaken, beslissingen en dekking |
| 10 | Bronnen en berekening | Selectieregels, herkomst, onzekerheid en betekenis |

Het profiel begint met nummer–teamkleur–code en de volledige naam in sectiepaars. De zes compacte kaarten blijven: **Starter, vrije-baan-specialist, metronoom, bandenfluisteraar, pitwindow-specialist en opwarmer**. Starter blijft de eerste kaart. Het vrije-baantempo wordt verdiept bij het teamgenootduel; dezelfde hoofdfiguur hoeft niet tweemaal te verschijnen.

Basisfeiten krijgen een compact carrièreoverzicht en eigen seizoen-/kwalificatiedetails. Ze worden geen nieuwe reeks gelijkwaardige specialismekaarten. Raceontwikkeling blijft een zelfstandig onderzoeksblok direct onder Starter.

### 4.2 De eigen basisfeiten

| Feitengroep | Eigen informatie | Belangrijke definitie |
|---|---|---|
| Kampioenschap | WK-punten, eigen puntenverloop, positie per seizoen, titels en beste eindpositie | Eindstand onderscheiden van tussenstand met peildatum |
| Kwalificatie | Resultaten, verdeling, mediaan, beste resultaat, poles en beschikbare tijden | Kwalificatie onderscheiden van uiteindelijke grid en sprintkwalificatie |
| Deelname | Inschrijvingen, starts, actieve seizoenen, debuut en laatste deelname | DNS, DNQ en DNPQ zijn geen gestarte races |
| Race-uitslagen | Zeges, podia, puntenfinishes, beste uitslag en positieontwikkeling | Officiële classificatie onderscheiden van rijdend finishen |
| Ronden | Gereden ronden, snelste ronden en waar gedekt ronden aan de leiding | Persoonlijke snelste ronde is niet de snelste ronde van de race |
| Loopbaancontext | Teams, teamperioden, nummers en relevante wisselingen | Identiteit hangt niet af van startnummer of drielettercode |
| Betrouwbaarheid en incidenten | Uitval, oorzaken, verantwoordelijkheid en straffen | Bronfeit onderscheiden van afgeleide classificatie |

Bovenaan gelden de gekozen jaren. Een aanvullend carrièretotaal krijgt expliciet het label en bereik van de hele carrière. Per seizoen komen team(s), starts, zeges/podia, punten, WK-positie en kwalificatiesamenvatting beschikbaar.

Officiële WK-punten worden niet blind gereconstrueerd door racepunten op te tellen. Historische schrapresultaten, gedeelde punten, halve punten, sprints, extra punten en latere besluiten kunnen verschil maken. Behaalde punten en meegetelde kampioenschapspunten blijven afzonderlijke begrippen.

### 4.3 Wat van die basisfeiten al is opgeslagen

De lokale controle van 17 oktober 2026 heeft de bewaarde F1DB-release v2026.17.0 opnieuw gelezen en de archiefhash gecontroleerd. Het oorspronkelijke ZIP bevat 1950–2026; uitslagen, kwalificaties en WK-standen lopen in die momentopname voor 2026 tot ronde 17. Latere kalenderregels zijn geen uitslagen.

| Brontabel | Regels | Wat hiermee beschikbaar is |
|---|---:|---|
| WK-standen na races | 21.588 | Punten en posities bij bewaarde tussenstanden |
| Seizoensstanden | 1.681 | Historische eindstanden of lopende seizoensstand, met titelindicator |
| Kwalificatieresultaten | 27.083 | 26.947 numerieke posities; tijden en segmenten gedeeltelijk |
| Race-uitslagen | 27.665 | Deelname, grid, uitslagstatus, puntenvelden en race-indicators |
| Coureur-seizoenen | 3.416 | Eigen seizoensdeelname en totalen |
| Coureuridentiteiten | 917 | Identiteit en bewaarde carrièretotalen; niet gelijk aan het aantal analyseprofielen |
| Persoonlijke snelste ronden | 17.214 | Beschikbare snelste rondetijden per coureur en race |
| Sprintuitslagen | 612 | Afzonderlijke sprintresultaten vanaf 2021 |
| Sprintkwalificaties | 488 | Afzonderlijke sprintkwalificaties vanaf 2023 |

Dit zijn bronregels, geen onafhankelijke races en geen volledigheidsgarantie. De WK-tabellen bevatten 388 verschillende rijderidentiteiten, tegenover 860 in de race-uitslagentabel. Controleer vooral ontbrekende noteringen bij coureurs zonder punten.

Voor Jos Verstappen zijn acht seizoensregels aanwezig, maar vijf afzonderlijke WK-standregels. Voor 1995, 1997 en 1998 bevat de seizoensbron nul punten en een lege kampioenschapspositie. Nul punten is een beschikbaar feit; een exacte positie is met die regels niet aangetoond.

De lokale historische SQLite-database bevat de oudere subset 1950–2019. Het complete ZIP bevat ook recentere jaren. De huidige profieluitvoer bevat nog geen volledige WK-/kwalificatielaag. De eerstvolgende datataak is daarom **ontsluiten, koppelen en gericht aanvullen**.

De [verbeterlijst](verbeterlijst.md) bevat de exacte tabel-/veldaantallen, archiefidentiteit en aanvullende controles. Ontbrekende waarden worden per veld onderzocht; niet het hele archief opnieuw binnenhalen.

## 5 De meetlat per specialisme

Iedere kaart en detailfiguur krijgt dezelfde uitleg: wat is gemeten, wat betekent de waarde, hoe ziet de eigen verdeling eruit, waarop is die gebaseerd en welke beperking verandert de interpretatie?

| Specialisme | Hoofdmaat | Eigen figuur | Richting en betekenis |
|---|---|---|---|
| Starter | Positiewinst en voordeel boven passende startreferentie | Eigen violins per gridpositie en gecorrigeerde curve | Positieve winst is hoger eindigen na ronde één |
| Vrije-baan-specialist | Procentueel tempoverschil met teamgenoot | Eigen verschil per race en teamperiode | Negatief tijdverschil betekent sneller |
| Metronoom tempo | Rondetijdrang op dezelfde raceronde | Alle eigen ronderangen per circuit, met violin en kwartielen | Rang 1 is de snelste gemeten rondetijd |
| Metronoom regelmaat | Robuuste spreiding rond eigen stinttrend als percentage van tempo | Eigen restafwijkingen, verdeling en ontwikkeling | Lager is regelmatiger; zegt op zichzelf niets over snelheid |
| Bandenfluisteraar | Verandering van relatief tempovoordeel per tien ronden leeftijd | Eigen gemeten leeftijd/tempoverloop | Positief betekent beter behoud tegenover de gebruikte referentie |
| Pitwindow-specialist | Procentueel voordeel tegenover eigen stinttrends | Eigen stopvensters, verdeling en tijdlijn | Positief betekent sneller dan de eigen trend verwacht |
| Opwarmer | Extra tijd bij leeftijd 1–3 tegenover eigen trend uit leeftijd 4–10 | Eigen afwijking per leeftijd en nieuwe set | Lager betekent minder vroeg tijdverlies |

De twee aspecten van Metronoom zijn verschillende metingen binnen één onderdeel. De bestaande rangverdeling blijft behouden; die wordt niet stilzwijgend hernoemd tot zuivere constantheid. De robuuste eigen-spreidingsberekening bestaat in de rekenlaag, maar moet als afzonderlijke profielmaat gecontroleerd en ontsloten worden.

### 5.1 Starter en het vervolg van de race

| Analyse | Beginpositie S | Resultaatpositie E | Selectie |
|---|---|---|---|
| Starter | Werkelijke gridpositie | Eerste doorkomst na ronde één | Bekende gridstart en doorkomst; pitlanestarts uitgesloten |
| Raceontwikkeling | Eerste doorkomst na ronde één | Eindklassering | Beide posities bekend en bevestigde rijdende finish |

Ruwe positiewinst is **S − E**. Iedere race levert één waarneming per analyse. Het tweede onderzoek begint bij de doorkomst na ronde één; het telt geen posities die al bij de start zijn gewonnen. Het beschrijft finishers en wordt daarom altijd naast het uitvaloverzicht geïnterpreteerd.

Behoud de eigen punten, violins, medianen, kwartielen, witte fit en grijze 95%-modelband. De curve blijft dicht bij de medianen, terwijl beperkte modelverlenging bij weinig gegevens herkenbaar blijft. Een modelpunt is geen extra gereden race. Geen extrapolatie naar een veldgrootte waarin de coureur nooit startte, ook als P23/P24 op de as staan.

De taartverdeling winst/behoud/verlies blijft uitsluitend in de Starter-kaart. De gecorrigeerde detailgrafiek blijft, met uitklapbare uitleg Berekening en interpretatie; de eerder verwijderde losse teksten en algemene tabellen keren niet terug.

Een aanvullende eigen maat wordt **verwachte resultaatpositie − werkelijke resultaatpositie**. De verwachting volgt uit dezelfde racefase, beginpositie, werkelijke veldgrootte, circuitvariant en passende periode; weer/starttype worden gebruikt waar onderbouwd. Sluit de beoordeelde coureur uit de referentie en leg de omgang met schaarse context vast.

Illustratieve voorbeelden: P1 behouden bij een verwachting van 1,5 geeft +0,5 positie boven verwachting. P20 naar P17 bij een verwachting van P16 geeft −1,0 ondanks drie plaatsen ruwe winst. Deze cijfers zijn uitlegvoorbeelden, geen nieuwe coureursuitkomsten.

De bestaande gecorrigeerde curvebalans, startscore en winstgrens krijgen een vastgelegde definitieversie. De winstgrens is een modelsamenvatting van waar voordeel ontstaat, met onzekerheid; geen harde fysieke vaardigheidsgrens. Pas een nieuwe score naast de oude toe na controle. De verhouding S/E blijft hoogstens aanvullend: zij corrigeert niet voor de kansen vanuit verschillende posities.

### 5.2 Teamgenootduel en basissnelheid

De tijdlijn Tempo door de tijd blijft bij Coureurs. Toon teamgenootperioden als lichte achtergrond, de juiste historische nummer–kleur–code, tijdelijke invallers als open punten en gemarkeerde overlap met uitvallers. Punten worden niet met lijnen verbonden.

De basisvergelijking gebruikt passende ronden van beide coureurs. Het symmetrische tijdverschil is **200 × (eigen tijd − teamgenoottijd) / (eigen tijd + teamgenoottijd)**. De mediaan wordt per race bepaald; aantallen passende ronden en beperkingen blijven zichtbaar.

Terugval op gemiddelde tijden of minder streng gekoppelde overlap wordt als andere meetstatus getoond, niet als even sterke meting. Een uitvaller sluit de hele race niet automatisch uit: gebruik de bruikbare gezamenlijke ronden en vermeld welke coureur de overlap begrensde.

### 5.3 Metronoom met iedere ronde als datapunt

Rangschik beschikbare volledige rondetijden binnen dezelfde race en dezelfde genummerde raceronde. Bewaar ruwe rang, aantal geldige tijden, race, ronde en contextvlaggen. Gelijke tijden krijgen de vastgelegde gelijke-rangbehandeling. Daarna selecteren we de eigen schone ronden in aantoonbare vrije lucht.

Alle geschikte ronden van de gekozen rijder verschijnen per circuit; jaren binnen de selectie worden standaard samengevoegd. Er komt geen sectoranalyse voor dit onderdeel. De kaart en figuur noemen de mediane rang, kwartielen, aantal ronden én aantal races. Langere races leveren meer rondepunten en dat staat bij de samenvatting.

De rang is een snelheidsrang, geen wedstrijdpositie. Rang 4 van 12 gemeten tijden is niet hetzelfde als rang 4 van 22. Leg vooraf een minimale velddekking vast. Een eventuele genormaliseerde rang wordt een aparte versie/maat en vervangt niet stilzwijgend de ruwe rangen.

Regelmaat wordt afzonderlijk berekend uit de afwijkingen rond de eigen verwachte stinttrend. De robuuste spreiding kan als percentage worden uitgelegd: 0,3% bij een representatief tempo van 100 seconden is ongeveer 0,3 seconde spreiding rond de trend. Het is geen maximale fout of automatisch een percentage ronden binnen die marge.

### 5.4 Banden en pitvensters

Bandenfluisteraar vergelijkt het verloop van gekoppeld relatief tempo over gemeten bandenleeftijd. Het getal is geen directe meting van fysieke slijtage. Opwarmer beoordeelt de vroege volledige ronden op een bevestigde nieuwe set tegenover de eigen latere trend; outlap telt niet mee.

Pitwindow-specialist beoordeelt de twee volledige ronden vóór de inlap en twee na de outlap tegenover eigen stinttrends. Het meet rondetijduitvoering, niet de snelheid van de monteurs of de optimaliteit van de stopkeuze.

Compounds, sets en leeftijd blijven afzonderlijk. Twee nieuwe sets van dezelfde compound blijven twee stints. Een bekende compoundvolgorde bewijst geen nieuwe set, gemeten leeftijd of vrije lucht. Ontbrekende gegevens blokkeren uitsluitend de betreffende maat, niet het hele profiel.

Bestaande selectiedrempels blijven gelden totdat ze expliciet worden herzien en geversioneerd. Elke wijziging krijgt een vergelijking met de eerdere uitkomsten.

## 6 Uitval incidenten en straffen als eigen feiten

Uitval, technische problemen, ongelukken, vastgestelde verantwoordelijkheid en straffen zijn vaste onderdelen van Coureurs. Ze hoeven niet op een GOAT-model te wachten.

| Aspect | Vast te leggen feiten |
|---|---|
| Finishstatus | Rijdend gefinisht, uitgevallen, niet gestart, gediskwalificeerd of onbekend; classificatie afzonderlijk |
| Uitvaloorzaak | Technisch, botsing/ongeval, overige bevestigde oorzaak of onbekend; nadere bronoorzaak behouden |
| Verantwoordelijkheid | Eigen, andere, gedeelde of niet vastgesteld, met precieze strekking van de beslissing |
| Straf | Besluit, reden, type, sanctie, betrokken coureur en waar bekend verwerking in uitslag |
| Verbanden | Onderbouwde koppeling tussen incident, straf en uitval |
| Herkomst | Bron, datum, oorspronkelijke tekst/status, normalisatie en onzekerheden |

Een zelfstandige crash bewijst niet automatisch een eigen fout. Een straf bewijst niet vanzelf de oorzaak van een uitval. Verantwoordelijkheid wordt alleen als vastgesteld weergegeven wanneer een controleerbare beslissing dat ondersteunt; “overwegend verantwoordelijk” wordt niet vertaald naar exclusieve schuld.

Toon eigen aantallen, een verdeling naar oorzaak en een gebeurtenistijdlijn. Een gericht uitklapbaar incidenten-/straffenlog bevat race, ronde indien bekend, feit, beslissing en bron. Dat is geen herintroductie van de verwijderde algemene tabel Onderliggende races.

Tel unieke uitvalbeurten één keer. Een gebeurtenis kan meerdere besluiten en sancties hebben; houd aantallen races, incidenten, besluiten en sancties uit elkaar. Tijdstraffen, gridplaatsen en licentiestrafpunten krijgen eigen eenheden. Een gecumuleerd strafpuntentotaal uit een besluit wordt niet opnieuw als toegekende straf opgeteld.

Een nulwaarde vraagt voldoende registratie. Geen gevonden document bij onvolledige dekking betekent onbekend. Vermeld bij ieder percentage de noemer: gestarte races, uitvalbeurten of races met voldoende gecontroleerde besluiten.

## 7 GOAT als afzonderlijke vergelijkingsmodule

### 7.1 De opbouw

1. **Kies de vraag.** Starts, raceontwikkeling, tempo, regelmaat, bandenbehoud, pitvenster, opwarming of beschrijvende loopbaanfeiten.
2. **Kies de coureurs en periode.** Overzicht van voldoende gedekte coureurs, met een beperkt aantal tegelijk in detail. Hele carrière, vooraf bepaalde piekperiode en leeftijdsfase zijn verschillende analyses.
3. **Bekijk de meetlat.** Welke omstandigheden zijn gelijkgesteld, welke overlappen werkelijk en welk deel is modelschatting?
4. **Vergelijk de uitkomsten.** Eenheid/score, interval, aantal races, dekking en modelstatus staan bij elkaar.
5. **Onderzoek de verschillen.** Verdelingen, beginposities, circuits, ontwikkeling en gevoeligheid van de conclusie.

Een link vanuit een specialisme neemt coureur, periode en eigenschap mee. Terugkeren behoudt die context. Coureurs en GOAT hebben een eigen selectie; een GOAT-vergelijking wijzigt niet stilzwijgend het individuele profiel.

### 7.2 Drie niveaus van vergelijking

| Niveau | Betekenis | Voorwaarde |
|---|---|---|
| Geobserveerd veld | Beschrijvende verschillen tussen deelnemers in dezelfde races | Dezelfde definitie, zichtbare selectie en dekkingsverschillen |
| Gedeelde omstandigheden | Vergelijking met dezelfde verdeling van beginposities, circuits en relevante context | Voldoende overlap en vooraf vastgelegde gewichten |
| Tijdperken | Modelmatige vergelijking tussen coureurs die niet rechtstreeks samen reden | Gevalideerde verbindingen, expliciete aannames en gevoeligheid |

De bestaande volledige-veldgrafieken van Metronoom, pitwindow en opwarming worden de eerste beschrijvende GOAT-weergaven. Ze zijn nog geen gecorrigeerde vaardigheidsranglijsten. Deelnemen aan dezelfde races garandeert geen identieke bruikbare ronden, compounds, leeftijd of omstandigheden.

De eigen feiten zoals titels, WK-posities, punten, zeges en poles kunnen hier naast elkaar staan. Benoem dat als loopbaanvergelijking. Ruwe puntentotalen, carrièrelengte of historische overwinningen worden niet rechtstreeks een tijdperk-onafhankelijke kwaliteitsscore.

### 7.3 Standaardiseren voor een eerlijke vergelijking

Een eigen gemiddelde beschrijft de werkelijk gereden carrière. GOAT moet een gemeenschappelijke doelverdeling gebruiken. Aantallen eigen starts bepalen de precisie; ze bepalen niet vanzelf de juiste weging van omstandigheden voor alle vergeleken coureurs.

Illustratief: A is vooraan +0,4 en achteraan +1,2 positie beter dan verwacht; B +0,2 en +1,0. Met eigen carrièreverdelingen 90/10 voor A en 10/90 voor B zijn de gemiddelden +0,48 en +0,92. Bij dezelfde verdeling 50/50 worden dat +0,80 en +0,60. De onderlinge conclusie kan dus omkeren door de verdeling van kansen.

Controleer beginpositie, werkelijk startersaantal, circuitvariant, periode en waar bekend weer/starttype. De huidige benadering van veldgrootte met een minimum van twintig moet voor zulke referenties worden vervangen door gecontroleerde startersaantallen. Een aslengte is geen veldgrootte.

Waar de context onvoldoende overlapt, volgt een beperkte vergelijking of een afzonderlijk gemarkeerde modelschatting. Een nooit waargenomen start vanaf P1 wordt geen eigen waarneming. Als het model onvoldoende onderbouwd is, verschijnt geen rangschikking.

### 7.4 Auto tijdperk en samenhang

Onderzoek een hiërarchisch model met coureur-, team-/autoperiode-, race-, circuit- en seizoenscontext, in een eenvoudiger uitvoering vóór een uitgebreid model. Gebruik informatie over autocondities die vóór het te beoordelen resultaat bekend was; corrigeer een uitslag niet met dezelfde uitslag.

Teamgenoten en overlappende loopbanen kunnen verbindingen leveren. Toon welke vergelijkingen goed, zwak of niet verbonden zijn. Een lange keten maakt auto en coureur niet volledig identificeerbaar. Controleer grote reglementsbreuken en veranderende veldsterkte afzonderlijk.

Tijdperken krijgen geen gemeenschappelijke bandenbeheerscore als de vereiste oude metingen ontbreken. Gebruik dezelfde dimensies voor alle deelnemers in een totaalanalyse, beperk de vergelijking of toon geen totaalscore.

Uitval wordt een aparte dimensie naast prestaties bij finish. Technische uitval krijgt niet willekeurig nul vaardigheidspunten en een incident krijgt niet automatisch eigen schuld.

### 7.5 Een eventuele totaalscore

Begin met een profiel van meerdere dimensies. Een algemeen GOAT-cijfer komt pas nadat de afzonderlijke maten gevalideerd zijn, dezelfde betekenis hebben voor de betrokken coureurs en de gewichten expliciet zijn gekozen.

Laat zien hoe redelijke andere gewichten de conclusie veranderen. Houd rekening met dubbel tellen: relatieve snelheid, rangtempo, regelmaat, punten en zeges kunnen samenhangen. Een PCA-as of een verzameling gecorreleerde maten is niet automatisch een verdedigbare kwaliteitsweging.

## 8 De strategieatlas en de koppeling met de rijder

De atlas onderzoekt **wat er gemeten gebeurde** en later welke alternatieve keuzes aannemelijk beter hadden kunnen werken. Er zijn drie aparte vragen.

### 8.1 Kandidaat-undercuts en overcuts

Bewaar gunstige én ongunstige vergelijkbare cycli. Definieer stopafstand, begincontext, betrokken rijders en meetmoment na beide stops. Rapporteer apart tijdwinst, omgekeerde onderlinge volgorde en eventueel behoud van dat resultaat.

Noem een cyclus zonder bekende intentie geen bewezen poging. Een succespercentage geldt alleen voor de vooraf gedefinieerde verzameling kandidaatcycli, niet voor alle denkbare kansen. Geen meetbare cycli is onbekend; een volledige geaccepteerde selectie met nul successen is nul.

Een warmtekaart kan racefase tegenover beginafstand tonen, met uitsplitsing naar positieklasse, compound en omstandigheden. Iedere cel vermeldt omvang en onzekerheid. De daadwerkelijke ronde blijft beschikbaar voor de gekozen race; relatieve racefase maakt circuits beter te vergelijken.

### 8.2 Het eigen stopprogramma

Bouw voort op de beschikbare pitprogramma’s. Onderzoek per race het tijd- en positieverloop van de gekozen rijder tegenover tegenstanders met hetzelfde aantal stops. Leg vooraf vast welke vensters en paren volledig genoeg zijn. Meerdere tegenstanders of cycli uit één race vormen geen onafhankelijke races.

Toon bij Coureurs de eigen verdeling en samenvatting. Een concreet duel kan als race-episode worden geopend. De vergelijking van de uitvoering van verschillende coureurs hoort bij GOAT.

Meer of minder stops is een afzonderlijke analyse. Een verschil in resultaat tussen één en twee stops bewijst niet dat het extra stoppen de oorzaak was. Verkeer, banden, neutralisaties, schade en racefase blijven relevant.

### 8.3 Alternatieven en scenario’s

Pas later simuleren: nu stoppen, later stoppen of een andere toegestane compound kiezen. Onderscheid pitverlies, opwarming, tempoverloop, verkeer en reacties van tegenstanders. Toon een bereik en de gevoeligheid voor aannames.

Waargenomen strategie is selectief: teams kiezen een stop op basis van hun informatie. Vergelijkbare geobserveerde groepen zijn daarom nog geen bewezen alternatief verloop. Een causaal effect vraagt een afzonderlijk onderzoeksontwerp.

## 9 Aanvullende analyses na de kern

De eerdere onderzoeksambitie blijft behouden, met een duidelijke plaats en volgorde.

| Onderwerp | Coureurs | GOAT of gedeelde verdieping | Startvoorwaarde |
|---|---|---|---|
| Aanvallen en verdedigen | Eigen acties en benutting van meetbare kansen | Vergelijking bij dezelfde blootstelling en context | Betrouwbare definitie van kans, actie en tijd nabij een tegenstander |
| Omstandigheden | Eigen patroon bij droog/nat, temperatuur of circuittype | Vergelijking na controle van auto, periode en selectie | Voldoende werkelijk gemeten omstandigheden |
| Circuitprofiel | Eigen prestaties op hetzelfde circuit of variant | Overdraagbaarheid naar vergelijkbare banen | Gecontroleerde circuitversies en kenmerken |
| Teamontwikkeling | Context bij eigen loopbaanontwikkeling | Dynamische autocorrectie en verwachtingen | Tijdgebonden teaminformatie en valide basismodel |
| PCA en profielgroepen | Later eventueel uitleg van het eigen profiel | Vergelijkbare profielen zonder automatische rangorde | Stabiele, voldoende gedekte en passend geschaalde kenmerken |
| Raceverslag | Eigen bijdrage aan onderbouwde racebevindingen | Gedeelde bevindingenlaag voor de racepagina | Gecontroleerde berekeningen en tekstsjablonen |
| Vooruitblik | Eigen verwachte prestatie onder scenario’s | Gezamenlijke consistente raceverwachting | Tijdgescheiden terugtest en vooraf opgeslagen voorspellingen |

PCA blijft verkennend. Het vat variatie in de gekozen kenmerken samen; een as is niet vanzelf kwaliteit of een oorzaak. Kies kenmerken per coureur-race of coureur-seizoen, behandel ontbrekende waarden en meetonzekerheid, en controleer de stabiliteit. Schaling en kenmerkselectie worden alleen op trainingsdata geleerd. Een vergelijkingskaart met andere profielen hoort bij GOAT.

Sectoren en volledige telemetrie vormen geen vereiste voor de Metronoom of de eerste GOAT-versie. FastF1 blijft een aanvullende bron waar bruikbare gegevens beschikbaar zijn; alleen de benodigde afgeleide kenmerken worden gepubliceerd. Uitgebreide telemetrie blijft gerichte latere verdieping.

## 10 Raceverslagen weer en voorspellingen

### 10.1 Een bevindingenregister vóór het verslag

Iedere bevinding krijgt een getal, eenheid, selectie, referentie, onzekerheid, dekking, bron, definitieversie en grafiekverwijzing. Kaarten, grafieken en tekst gebruiken hetzelfde resultaat.

Begin met vaste tweetalige sjablonen. Een eventueel taalmodel mag de formulering helpen, maar geen nieuwe uitslagen, aantallen of oorzaken toevoegen. Maak waarneembare veranderingen niet ongemerkt causaal: “sneller sinds dit moment” is niet automatisch “sneller door deze upgrade”.

Een raceverslag behandelt het kernbeeld, start en kantelpunten, tempo, pitcycli, incidenten, opvallende eigen rijderprestaties en beperkingen. Een vooruitblik verschijnt pas als de onderliggende verwachtingen betrouwbaar genoeg zijn.

### 10.2 Werkelijke omstandigheden en verwachtingen scheiden

Gemeten regen en temperatuur horen bij de terugblik. Een weersverwachting krijgt uitgiftetijd, modelrun, geldigheid, locatie/tijdzone en bron. UTC is de opslagbasis; de presentatie mag naar lokale tijd omrekenen.

Een opgeslagen verwachting voor een race mag achteraf niet worden vervangen door het werkelijk waargenomen weer. Bewaar zo nodig afzonderlijke versies vóór het weekend, na trainingen, na kwalificatie en vóór de hoofdrace.

### 10.3 Kwaliteit van vooruitblikken toetsen

Bewaar verwachtingen voordat de race begint. Gebruik voor winst/podium een gezamenlijke consistente race-uitkomst of duidelijke kansdefinitie. Toets kalibratie en een passende kansfoutmaat, niet alleen de gekozen winnaar.

Vergelijk met eenvoudige basismodellen voor teamsterkte en circuitgeschiedenis. Een ingewikkelder model krijgt pas een productplek als het buiten de trainingsperiode aantoonbaar iets toevoegt.

## 11 Eén gedeelde databasis

Dezelfde feiten voeden verschillende modules. Maak geen twee onafhankelijk bijgehouden databases voor Coureurs en GOAT.

| Laag | Inhoud | Gebruik |
|---|---|---|
| Bewaarde bronnen | Originele antwoorden, bestanden, bronversies en hashes | Herstel, controle en gerichte aanvulling |
| Gecontroleerde feiten | Identiteiten, sessies, uitslagen, punten, status, stints en besluiten | Basisstatistieken en traceerbare observaties |
| Afgeleide waarnemingen | Ronderangen, starts, vervolgtrajecten, pitvensters en eigen trends | Gedeelde analysebouwstenen |
| Profielmaten | Eigen getallen en verdelingen binnen periode en context | Coureurs |
| Vergelijkingsmaten | Gemeenschappelijke referentie, gewichten, model en onzekerheid | GOAT |
| Bevindingen en presentatie | Uitlegbare resultaten met bron- en grafiekverwijzingen | Kaarten, tekst, verslagen en downloads |

Gebruik duurzame sleutels voor coureur, team-/autoperiode, race, sessietype, circuitvariant, inschrijving, stint/set, incident en besluit. Startnummer en drielettercode zijn labels. Behoud de alias van Zhou Guanyu en de bestaande scheiding van verschillende coureurs met gelijke codes.

Iedere maat legt vraag, definitieversie, eenheid, richting, nulpunt/referentie, invoervereisten, uitsluitingen, weging en minimumdekking vast. Bewaar de eigen bronuitkomst apart van een GOAT-correctie. Gelijke selectie en definitie leveren in beide modules dezelfde basisuitkomst.

De datacollectiepagina wordt onderdeel van iedere inhoudelijke datalevering: parameter, aantal bruikbare waarden, jaren, bron, zoekmethode, controles, conflicten en ontbrekende dekking. Houd opgeslagen, gekoppelde, berekenbare en getoonde waarden uit elkaar.

Zoek aanvullingen gericht per ontbrekend veld en jaar. Hergebruik de al bewaarde bronnen eerst. Gebruik officiële resultaten/besluiten en gedocumenteerde gespecialiseerde datasets; onderzoek bij verdwenen materiaal ook webarchieven. Een gearchiveerde artikelpagina garandeert niet dat de oorspronkelijke afbeelding of tabel terughaalbaar is.

## 12 Statistische afspraken en controle

### 12.1 Wat een uitkomst wel meet

Beschrijving, referentiemaat, voorspelling en causale claim blijven aparte categorieën. Een goede fit bewijst geen rijvaardigheid los van auto en omstandigheden.

Bij Coureurs beschrijft een eigen carrièregemiddelde de eigen verzameling kansen. GOAT gebruikt gemeenschappelijke gewichten en verklaart naar welke situaties de conclusie generaliseert. Een referentiescore is geen percentage vaardigheid of winstkans tenzij die betekenis daadwerkelijk is gemodelleerd.

### 12.2 Weging en onzekerheid

Iedere geschikte ronde blijft zichtbaar waar dat de vraag is. Voor onzekerheid en algemene conclusies worden ronden niet als onafhankelijke races behandeld. Onderzoek bemonstering op race-/seizoensniveau en tijdsafhankelijkheid; gebruik voor gekoppelde vergelijkingen dezelfde gekoppelde steekproeven.

Mediaan, kwartielbereik, 95%-modelband en voorspellingsinterval krijgen verschillende labels. De huidige 95%-band wordt niet als bewezen gekalibreerde dekking over nieuwe races gepresenteerd. Controleer gevoeligheid voor uitsluitingen, weging en modelkeuze.

### 12.3 Ontbrekende gegevens en uitval

Onbekend is geen nul. Gedeelde auto’s met onbekende individuele toerekening blijven bewaard maar worden niet als individuele vaardigheidswaarneming gescoord. Gemeten en geschatte waarden blijven afzonderlijk.

Het vervolgonderzoek conditioneert op rijdend finishen. Leg die selectie naast uitval en onderzoek voor GOAT hoe die de vergelijking beïnvloedt. Incidentverantwoordelijkheid en technische betrouwbaarheid zijn geen inwisselbare uitvalcodes.

### 12.4 Validatie vóór conclusies

Controleer rekenregels met kleine bekende voorbeelden en bewaar vergelijking met eerdere versies. Houd complete races uit de modeltraining voor toetsing; voor toekomstige prestaties ook een latere periode. Schaling, invulling en parameterkeuze mogen geen informatie uit die toetsraces lekken.

Leg dekkingsdrempels vast voordat naar de gewenste winnaar of conclusie wordt gekeken. Toets ook nulresultaten, dunne steekproeven, veranderde formats, gedeelde auto’s, tijdperkbreuken en slecht verbonden teamgenootnetwerken.

## 13 Vormgeving bediening en laden

De [stijlgids](../stijlgids.html) blijft de visuele basis. Rood hoort bij Races, paars bij Coureurs, goud/geel bij GOAT en cyaan ondersteunt context en bediening. Teamkleuren houden hun feitelijke betekenis. Groen/rood mag functioneel gunstig/ongunstig aangeven.

Behoud de gedeelde header met Home, Races, Drivers/Coureurs, Greatest, About me en EN/NL. Het beeldmerk linkt naar de frontpage. Geen nieuwe losse navigatiestijl per module.

Bij Coureurs blijft de sidebar gelijk aan de race-uitstraling: nummer, teamkleur en drielettercode; sortering op code; één actieve rijder; geen teamselectie en geen alles/niets. Bij inactieve rijders wordt alleen het nummer grijs. De volledige profielnaam staat naast het identiteitselement om gelijke codes te onderscheiden.

De paarse jaarselector gebruikt het bereik van de werkelijk beschikbare dataset. Wisselen van rijder of jaren actualiseert alle relevante kaarten en grafieken, met de gekozen periode in beeld. Voeg de eerder verwijderde globale circuit-/compound-/deelbediening niet stilzwijgend opnieuw toe; noodzakelijke analysekeuzes blijven gericht en worden apart onderbouwd.

| Gedrag | Afspraak |
|---|---|
| Horizontale grafiek | Alleen de inhoud schuift; y-as, eenheden en beter/slechter-pijlen blijven staan |
| Starter en tempoverschil | Bestaande niet-lineaire schaal met ankers 0, 1, 3, 6 en 10 behouden; gunstig boven en ongunstig onder |
| Buiten de schaal | Randmarker met werkelijke waarde; onderliggende berekening niet afkappen |
| Hover | Informatie tonen; geen onverwachte selectie- of focuswisseling |
| Scrollwiel | Pagina scrollt normaal; kaartzoom alleen met Ctrl plus wiel |
| Afbeeldingen | Donkere consistente beelden; bestaande subtiele bewegingen, geen plotselinge zoom |
| Pop-ups | Zelfde vormtaal, bereikbare sluiting en focus; langere inhoud scrollt binnen de bedoelde zone |
| Laden | Laat de bestaande inhoud staan tot de nieuwe gegevens klaar zijn; laadindicator in sectiekleur; geen oude cijfers onder nieuwe naam |
| Mobiel | Geen pagina-overloop of overlappende badges; alleen bedoelde figuren mogen horizontaal scrollen |
| Toegankelijkheid | Zichtbare toetsenbordfocus, tekst naast kleurbetekenis en respect voor minder beweging |

De algemene referentietabel en Onderliggende races keren niet terug bij Coureurs. Bronraces blijven bereikbaar via eigen punten, gerichte logs en uitklapbare uitleg.

## 14 Opslag prestaties en onderhoud

De ingestelde websitegrens is **900.000.000 bytes**. De laatst bewaarde controle van 16 oktober 2026 kwam op **281.252.427 bytes**, ongeveer 281 MB. Dit is een eerdere publicatiemeting, geen nieuwe meting van de live website.

De huidige eigen bouwgrens voor de ongecomprimeerde coureursomgeving is **64.000.000 bytes**. Het bouwrapport vermeldt een bovengrens van **53.033.315 bytes**. De eerdere grens van 20 MB en maximaal vijf seizoenen geldt niet meer. Verhoog een grens niet automatisch omdat een nieuwe bundel te groot wordt.

Voor groei:

- Splits profielindex, eigen details en GOAT-uitvoer in compacte gegevensbestanden; laad alleen wat de actieve module nodig heeft.
- Bewaar iedere benodigde ronderang, maar exporteer niet opnieuw alle oorspronkelijke tijd-, sector- en telemetriereeksen.
- Dedupliceer gedeelde feiten en assets. Bronbestanden blijven via de bestaande archief-/herstelroute beschikbaar.
- Gebruik verliesloze compressie met de bestaande laad- en downloadondersteuning. Een download en decompressie moeten dezelfde gegevens opleveren.
- Meet uiteindelijke publicatiebytes, grootste bestanden, verzoeken, parse-/rekentijd en geheugengebruik. Alleen opslag meten is onvoldoende.
- Stel vóór een nieuwe gegevenslaag een gecontroleerd budget vast en controleer dat in de bouw. Behoud herstelbaarheid en betekenis bij verkleining.

De volledige historische reikwijdte blijft waar de feiten dat dragen. Zware nieuwe bandenanalyse of modellen mogen beginnen in een aantoonbaar voldoende gedekte recente subset. Dat beperkt de betreffende analyse, niet het hele coureursarchief.

Een geplande race-update is geen garantie op onmiddellijke verwerking. Nieuwe feiten krijgen bron-/peildatum, validatie en een gecontroleerde publicatie. Een uitbreiding mag latere bronaanvullingen of lokaal bewaarde aanvullingen niet overschrijven zonder conflictcontrole.

## 15 De bouwvolgorde en beslismomenten

| Stap | Oplevering | Afhankelijkheid | Gereed wanneer |
|---|---|---|---|
| A | Definities en dekkingsregister | Bestaande bronnen en bouwstatus | Kernmaten, telregels, veldgrootte en ontbrekende dekking vastliggen |
| B | Coureursfeiten | A | Punten, WK-stand, kwalificatie en basisfeiten correct gekoppeld en verklaard zijn |
| C | Herordend eigen profiel | A en bruikbare bestaande metingen | Zes kaarten, eigen figuren en teamgenootduel zelfstandig te begrijpen zijn; veldgrafieken verplaatst zijn |
| D | Incidenten en straffen | A en beschikbaar besluitenmateriaal | Feiten, verantwoordelijkheid, noemers en onbekende dekking controleerbaar zichtbaar zijn |
| E | GOAT als beschrijvende vergelijking | C en gedeelde definities | Meerdere coureurs met gelijke meetdefinities, dekking en duidelijke beschrijvende status vergeleken worden |
| F | GOAT op gedeelde omstandigheden | A tot E en voldoende overlap | Gemeenschappelijke gewichten, referentie zonder eigen bijdrage en onzekerheid gevalideerd zijn |
| G | Vergelijking tussen tijdperken | F en gecontroleerde verbindingen | Modelaannames, verbindingen, gevoeligheid en niet-vergelijkbare context zichtbaar zijn |
| H | Verdiepte strategieatlas | A en voldoende pit-/bandendekking | Kandidaatcycli, eigen programma’s en verschillende stopaantallen correct gescheiden zijn |
| I | Verslagen en aanvullende profielen | Stabiele kernmetingen | Bevindingen reproduceerbaar zijn en tekst dezelfde cijfers gebruikt |
| J | Scenario’s en vooruitblikken | Gevalideerde modellen en tijdgebonden verwachtingen | Terugtest en vooraf opgeslagen proefvoorspellingen bruikbaar blijken |

B en C vormen de eerste samenhangende productoplevering, met D als vast feitenonderdeel. Beschikbare incidentfeiten hoeven niet op volledige historische documentdekking te wachten. E kan zichtbaar worden vóór het modelonderzoek in F en G, mits het beschrijvende karakter duidelijk blijft.

H bouwt voort op bestaand werk en kan na de kern worden verdiept zonder op een totaalscore in GOAT te wachten. I en J zijn geen voorwaarden om Coureurs goed af te ronden. Bij onvoldoende modelonderbouwing kan G langer onderzoek blijven terwijl de andere onderdelen nuttig beschikbaar zijn.

De eerdere raming van 80–140 uur betrof een eerste oorspronkelijke oplevering. Deze is geen resterende raming voor dit uitgebreide plan. Begroot ieder blok pas na de inventarisatie van ontbrekende invoer en de gekozen modelomvang.

## 16 Controle en oplevercriteria

Een stap is inhoudelijk gereed wanneer definitie, herkomst, selectie, eenheid, dekking en relevante onzekerheid beschikbaar zijn. Een productoplevering vraagt daarnaast de volgende controles.

| Controle | Vereist resultaat |
|---|---|
| Identiteit | Geen dubbele profielen door aliassen; gedeelde auto’s correct uitgesloten of toegerekend |
| Basisfeiten | Eigen aantallen en seizoentotalen aansluiten op bronnoteringen en officiële telregels |
| Kwalificatie | Sessietype, uitslag, pole, grid en sancties niet door elkaar lopen |
| Eigen analyses | Alleen eigen waarnemingen in de hoofdfiguren; teamgenootuitzondering herkenbaar |
| Metronoom | Iedere geschikte ronde behouden, juiste rang/noemer, tempo en regelmaat gescheiden |
| Starter en vervolg | Pitlanestarts uitgesloten waar nodig; juiste begin/eindposities; alleen bevestigde finishers in vervolgonderzoek |
| Uitval en straffen | Oorzaak en verantwoordelijkheid gescheiden; nul versus onbekend; geen dubbeltellingen |
| GOAT | Gelijke definities en gemeenschappelijke context; ruwe en gecorrigeerde resultaten afzonderlijk |
| Onzekerheid | Kwartielen, modelband en voorspelling niet verward; race-/periodeafhankelijkheid onderzocht |
| Interface | Desktop en mobiel, badges, vaste assen, scrollen, pop-ups, toetsenbord, NL/EN en deelbare context gecontroleerd |
| Data-overgang | Geen verdwenen waarnemingen, verloren bandeninformatie of onbedoeld gewijzigde bestaande resultaten |
| Publicatie | Budget, compressie, downloads, interne links en herstel van archieven gecontroleerd |

Begin met gerichte rekenvoorbeelden en regressiecontroles voor gewijzigde definities. Voer de passende bestaande tests uit en controleer representatieve moderne én historische profielen in de browser, inclusief een nulpuntenseizoen, gedeelde auto, beperkte timing en een rijder met weinig starts.

Bouw eerst lokaal en leg de concrete oplevering ter beoordeling voor. Na expliciete publicatieopdracht: gecontroleerde bundel maken, uploaden, deployment volgen en de gepubliceerde pagina’s testen, inclusief laden, navigatie en downloads. Controleer ook de bestaande automatische race-update. Oude goed werkende publicatiegegevens blijven herstelbaar.

## 17 Besluiten voor de eerstvolgende uitvoering

De productkeuzes zijn vastgesteld:

- Coureurs bevat eigen feiten, zes specialismen, vervolgonderzoek, uitval/incidenten/straffen en het teamgenootduel.
- GOAT bevat de zichtbare vergelijking met het veld en tussen tijdperken.
- Metronoom behoudt de individuele ronderangen; regelmaat krijgt een afzonderlijke maat binnen dat onderdeel.
- De brongegevens voor basisfeiten worden eerst ontsloten voordat grootschalig opnieuw wordt verzameld.
- Nieuwe definities vervangen bestaande scores pas na een gecontroleerde versieovergang.

Tijdens stap A worden nog concreet vastgelegd: minimale velddekking per ronderang, referentievensters voor starts en vervolgonderzoek, gewichten van een gedeelde context, criteria voor modelmatige verbinding tussen tijdperken en prestatiebudgetten per nieuwe gegevenslaag. Deze keuzes worden onderbouwd vóór het bekijken van de gewenste rangorde. Gewichten voor een eventuele totaalscore zijn pas aan de orde na validatie van de afzonderlijke dimensies.

## 18 Documenten en projectbasis

| Document of bestand | Rol |
|---|---|
| [Verbeterlijst](verbeterlijst.md) | Detailkeuzes, broninventaris en uitvoerbare verbeterpunten |
| [Stijlgids](../stijlgids.html) | Kleuren, componenten, figuren en interactie |
| [Datacollectie](../data-collection.html) | Publieke uitleg over gegevens, aantallen, herkomst en controles |
| [Bouwrapport Coureurs](../assets/phase2-build-report.json) | Actuele lokale bouwtelling |
| [Projectdocumentatie](../README.md) | Uitvoering, publicatie, compressie en herstel |
| [Historische dekking](../analyses/sources/historical/coverage-report.html) | Historische aanvullingen en beperkingen |
| [Onderzoek banden 2010–2017](../research/tyres/README.md) | Gecontroleerde compoundstints en resterende conflicten |
| [Bronmetadata F1DB](../analyses/sources/historical/f1db/source.json) | Bewaarde release, licentie en archiefhash |
| [Bronregister incidenten](../analyses/sources/incidents/registry.json) | Bewaarde incident- en besluitenverzameling |
| [Oorspronkelijk onderzoeksplan](fase-2-onderzoeks-en-ontwikkelplan-archief-20261017.md) | Eerdere verkenning, bronverwijzingen en achtergrond |

De oudere lokale opleveringsnotities blijven historische documentatie. Dit totaalplan bepaalt de nieuwe samenhang en volgorde; de verbeterlijst werkt de afzonderlijke punten verder uit.
