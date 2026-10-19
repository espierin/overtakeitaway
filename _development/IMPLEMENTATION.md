# Fase 2 · uitvoering en controle

**Oorspronkelijke ontwikkeloplevering: 17 oktober 2026.** De drie ontwikkelpagina’s zijn op 18 oktober gepubliceerd. Daarna is op verzoek de coureursmodule gepromoveerd tot de reguliere `analysis-lab.html`, inclusief de herstelde veldvergelijking bij De metronoom. Races en GOAT houden hun afzonderlijke ontwikkelroutes. De vroegere coureursgegevens blijven verliesloos bewaard en op de oorspronkelijke kloonhash gecontroleerd. Dit verslag vervangt het onderzoeksplan niet.

## Wat er per planstap staat

| Stap | Lokale uitvoering | Grens aan de conclusie |
|---|---|---|
| A · definities en dekking | Gedeeld versie- en parameterregister, echte startersaantallen, circuitvarianten, duidelijke uitsluitingen, expliciete referentievensters | Bekende bronhiaten blijven zichtbaar; een kalenderregel bewijst geen resultaat |
| B · eigen feiten | Gekoppelde seizoensstanden, punten, starts, zeges, podia, poles, snelste ronden, sprinttotalen, eigen WK- en kwalificatieverloop, historische teams | Afzonderlijke officiële WK-notering kan ontbreken bij nul punten; lopend seizoen is voorlopig |
| C · eigen profiel | Zes kaarten en eigen detailfiguren; starter en ronde-één-tot-finish; teamgenootduel behouden; metronoom-veldvergelijking op verzoek hersteld; afzonderlijke robuuste regelmaat | Tempo en regelmaat zijn verschillende maten; bevestigde finishers vormen een geselecteerde groep |
| D · incidenten | Uitvaloorzaken, bronstatus, sancties, classificatietijdstraffen en gelezen verantwoordelijkheid afzonderlijk | Besluitenarchief is onvolledig; zeven besluiten inhoudelijk beoordeeld; waaronder één gezamenlijke uitspraak zonder volledig of overwegend verantwoordelijke; overige tekstherkenning bewijst geen schuld |
| E · beschrijvende GOAT | Vraag, periode, maximaal vier detailrijders, veldoverzicht en carrièrefeiten; standaard dezelfde races, eigen carrièrekansen apart selecteerbaar | Beschrijvende verschillen zijn geen geïsoleerde rijvaardigheid; per maat kan meetdekking verschillen |
| F · gedeelde context | Gelijke contextgewichten, echte overlap, referentie zonder eigen bijdrage, gezamenlijk gewogen racebootstrap inclusief referenties | Alleen ondersteunde context; ongekende weers- en autocondities niet stilzwijgend gecorrigeerd |
| G · tijdperkonderzoek | Verbonden kwalificatienetwerk, componentgrenzen, minimumparen, regulering en tijdgescheiden toets; conditionele racegeclusterde marges | Toets haalt prestatiedrempel niet: geen definitieve of algemene GOAT-ranglijst. Dynamische autocorrectie is nog geen gevalideerd product |
| H · strategie | Atlas met gunstige én ongunstige kandidaatcycli, fase/positie/compound, racegeclusterde marges; eigen pitprogramma’s voor gelijke/meer/minder stops; concrete episodes | Geen bewezen teamintentie of causaal effect. Alternatieve stop is een transparante tijdsbalans met gevoeligheid voor aannames, geen geleerd tegenreactiemodel |
| I · bevindingen en profielkaart | Tweetalige racebevindingen uit dezelfde meetlaag met bronraceverwijzingen; verkennende PCA op complete coureur-seizoenen | Geen nieuwe oorzaken toegevoegd. PCA leert schaling/assen uitsluitend uit eerdere trainingsjaren en projecteert latere jaren; geen kwaliteitsrangorde |
| J · vooruitblikonderzoek | Walk-forward terugtest, simpele teamreferentie, vooraf opgeslagen gezamenlijk onderzoeksscenario, afzonderlijke latere evaluatie met Brier-score en logverlies; gedateerde weersbron | Nog geen afgeronde prospectieve kalibratie. Openbare winst- en podiumkansen blijven uitgeschakeld |

De conditionele onderdelen uit hoofdstuk 9 van het plan zijn geen ongemerkt afgeronde functies: kansen bij aanvallen/verdedigen, systematische nat/droog- of temperatuurcorrectie, dynamische team-/autocorrectie en een geïntegreerde causaal onderbouwde racesimulatie vragen nog geschikte invoer en validatie. Ze zijn niet vervangen door verzonnen scores. De bestaande eigen grafieken en het afzonderlijke netwerk-/profielonderzoek leveren wel de controleerbare bouwbasis.

## Reikwijdte en behoud

- **1950–2026**, 1.166 races en 817 profielen blijven in de gedeelde ontwikkelbasis.
- **26.157 coureur-raceregels** en **639.012 oorspronkelijke ronderangen** zijn behouden. Alle rangwaarden/noemers/context blijven bestaan. Een aanvullende dekkingsvlag sluit 4.295 ronderangen uit bij onvoldoende aantoonbaar gemeten veld; dit verwijdert de waarnemingen niet.
- **27.441 bronuitslagregels** zijn gekoppeld. Dit zijn bronregistraties, niet hetzelfde als aantallen starts of onafhankelijke races. Het volledige ZIP is op SHA-256 gecontroleerd.
- **1.766 coureur-races** bevatten een berekenbare robuuste eigen regelmaat uit behouden pitklokken. Overige regels krijgen geen geschatte regelmaat.
- **1.850 start-/vervolgwaarnemingen** hebben een passende eigen contextreferentie; **37.074** niet. Onvoldoende referentie betekent onbekend, niet neutraal.
- **16 profielen** missen gekoppelde seizoensfeiten; hun eigen beschikbare racewaarnemingen blijven zichtbaar. De identiteitstekorten staan in het bouwrapport.
- Alle oorspronkelijke kandidaat-pitcycli en pitklokken zijn exact gereconstrueerd en vergeleken. De gedeelde gegevens groeien niet door een duplicaat per module.

## Vastgelegde keuzes

De vergelijking tussen de twee bewaarde bronnen vindt **481 afwijkende gridposities** en **45 afwijkende eindposities**. Beide waarden blijven beschikbaar; de betrokken start- of vervolgfase wordt uitgesloten totdat verificatie een verschil kan verklaren. Wijziging van grid na terugtrekkingen of latere besluiten kan een verklaring zijn, maar wordt niet zonder broncontrole als oorzaak vastgelegd. De eigen profielpagina toont de betreffende regels in het dekkingsblok.

Voor de velddekkingscontrole moet de afgelegde afstand voor minstens 90% van de raceprofielen bekend zijn. Ronderangen vereisen minstens vijf gemeten volledige rondetijden en minstens 80% van het aantoonbaar nog rijdende veld. Vrije lucht moet aantoonbaar zijn; onbekend verkeer geldt niet als vrij.

Er zijn **66 aanvullende pitlanevlaggen** uit F1DB herkend. Deze vullen de oudere markeringen aan; alle bekende pitlanestarts blijven buiten de Starter. De eigenlijke ronde-één-tot-finishanalyse mag hun latere raceverloop wel beschrijven als die waarneming verder geldig is.

Een start- of vervolgreferentie gebruikt dezelfde circuitvariant, beginpositie en werkelijke veldgrootte. Waar latere diskwalificaties de grid-/afstandkolommen in de bron leeg laten, kan bewaarde ronde-evidentie bevestigen dat een auto daadwerkelijk startte; een diskwalificatie wordt niet gelijkgesteld aan DNS. Gedeelde bronauto’s leveren geen individuele fasescore. De beoordeelde rijder ontbreekt. Eerst zoeken we binnen vijf jaar, anders binnen tien jaar aan weerszijden; minimaal acht andere races en twee andere coureurs. De eigen periode begrenst de eigen waarnemingen, niet willekeurig het lokale referentievenster.

Interne negatieve identificatienummers worden niet als startnummer afgebeeld: een onbekend nummer krijgt een vraagteken; de oorspronkelijke bronwaarde blijft bewaard.

De bestaande curvebalans, startscore en winstgrens blijven eigen maten met vastgelegde definitie en dekking, afzonderlijk van het nieuwe gemiddelde voordeel in posities. De waarden zijn voor alle profielen naar JSON en CSV geëxporteerd. Een beperkte score is geen universele rangorde.

Gedeelde-contextvergelijkingen geven iedere gedekte context hetzelfde gewicht voor alle gekozen rijders. De onzekerheid gebruikt gezamenlijk herwogen complete races, ook voor de referentie. Ronderangen blijven individuele punten; de bootstrap behandelt ronden niet als onafhankelijke races.

## Onderzoeksresultaten die publicatie blokkeren

Het kwalificatienetwerk bevat **12.524 gemeten paren**. In de onafhankelijke toets: 185 races en 472 paren. Gemiddelde absolute fout model **0,5117** tegenover **0,5091** voor nulverschil; de 95%-marge van verbetering is **−0,0268 tot +0,0175**. Er is dus geen aangetoonde prestatieverbetering. Dit wordt op GOAT zichtbaar gemeld.

Een prospectieve voorspelling moet vóór de race zijn opgeslagen, dezelfde aantoonbare deelnemers hebben en later afzonderlijk worden beoordeeld. Resultaten vervangen de oorspronkelijke voorspelling niet. Een nog niet gereden race kan vandaag geen afgeronde prospectieve toets opleveren. Ook een gunstige terugtest schakelt openbare kansvoorspellingen niet automatisch in.

## Opslag en laden

De analytische gegevenslaag bedraagt circa **63,0 MB ongecomprimeerd**, onder de grens van **64 MB**; de bijbehorende verliesloze downloads circa **10,0 MB**. Het precieze aantal bytes staat in `build-report.json`. De oorspronkelijke websitegrens van 900 MB is niet gewijzigd.

Details en bronfeiten laden per benodigde profielgroep. Pitklokken/cycli laden pas bij het strategieonderdeel; GOAT-modellen alleen op GOAT. HTTP gebruikt de gecomprimeerde detailbestanden. Lokaal openen heeft een gelijkwaardige scriptfallback. Zowel compressie/decompressie als alle gehashte downloads worden inhoudelijk gecontroleerd.

De lokale browsermeting bewaart per pagina tijd tot gereed, verzoeken en overgedragen bytes in `storage/phase2-clones-20261017/final-browser-report.json`. In de aanvullende desktopproef gebruikte de geselecteerde Max-pagina circa 47,4 MB JavaScript-heap; dit is geen meting van het volledige browsergeheugen. Dit is geen garantie voor dezelfde laadtijd op een telefoon of externe verbinding. Een uiteindelijke publicatiebundel en netwerkmeting volgen bij een afzonderlijke publicatieopdracht.

## Controles en herhaling

De volledige reken- en gegevenscontrole sluit af met **302 geslaagde tests**, inclusief bronconflicten, aanvullende pitlanevlaggen, gedeelde auto’s en latere diskwalificaties. De desktop-/mobielproeven en het rechtstreeks openen van lokale bestanden zijn geslaagd; de afzonderlijke visuele controle omvat ook badges, uitlijning van vaste assen, eigen specialismegrafieken en het openen van een pitcyclus-episode.

De rekencontroles behandelen referentie-uitsluiting, incompatibele context, regelmaat tegenover een echte trend, losse netwerkcomponenten, toekomstige verbindingen, training zonder toekomstige PCA-/race-informatie, gedeelde auto’s en vooraf opgeslagen voorspellingsarchieven.

De gegevenscontroles reconstrueren alle bewaarde profielwaarnemingen, elke oorspronkelijke pitcyclus en pitklok, alle verliesloos gecomprimeerde downloads en de hashes van ongewijzigde bronpagina’s/assets.

De browsercontrole behandelt moderne en historische profielen, Sainz-identiteit, Jos Verstappens nulpuntenseizoen met onbekende WK-positie, jaarfilters, één actieve rijder, vaststaande assen, aanvullende strategiegegevens, GOAT-selecties en meetlatten, racebevindingen, scenario, NL/EN, desktop en mobiel tot 320 pixels breed. Foutmeldingen, ontbrekende bestanden en pagina-overloop moeten ontbreken.

Herhaal de opdrachten uit [README](README.md). De daadwerkelijke uitkomsten staan in het controlelog en het browserrapport; veranderende brongegevens vragen een nieuwe bouw en controle.


## Aanvullende hercontrole van uitval en besluiten

De [uitgebreide verantwoording](INCIDENT-CHECK.md) beschrijft de fouten en herstelgevallen. Alle 27.441 gekoppelde bronregistraties zijn opnieuw op uitkomst geclassificeerd; de ontbrekende oude DNF-vlag verbergt 9.185 uitvalregistraties niet langer. Er zijn 9.611 bevestigde uitvalregistraties, 170 onzekere uitkomsten en 120 gedeelde-autoregistraties. Niet gestarte deelnemers en diskwalificaties blijven afzonderlijk. Deze aantallen betreffen bronregistraties; gedeelde inschrijvingen zijn geen onafhankelijke persoonlijke races.

Van de 6.013 opnieuw ingelezen documenten hebben 415 een wijziging in de herkende inhoud of ontvangers. Alle oorspronkelijke pdf’s zijn op SHA-256 gecontroleerd zonder afwijkingen. De koppelingen bevatten 5.342 ontvangerrollen en 371 rollen als andere betrokkene; die tweede groep erft geen persoonlijke straf. Het archief blijft onvolledig, vooral vóór 2007.

Alle 282 in F1DB vastgelegde tijdstraftoevoegingen zijn gekoppeld. Dit herstelt 23 eerder niet gekoppelde registraties: twaalf vóór 2007 en elf door de correcte identiteitskoppeling. Ze zijn geen volledige telling van tijdens races uitgevoerde straffen en worden niet bij het aantal strafbesluiten opgeteld.

Een expliciete uitvalreden met een afwijkende oude finishvlag blijft in 58 gevallen als bronverschil geregistreerd. Voor de ronde-één-tot-finishanalyse vallen de betrokken uitvallers buiten de populatie: 15.392 geschikte waarnemingen blijven over, 57 minder dan vóór deze hercontrole. De Starter, oorspronkelijke ronderangen, pitklokken en bronwaarden zijn behouden.

De afzonderlijke incidentbrowserproef behandelt acht combinaties van rijder, periode, taal, schermbreedte en lokaal/HTTP openen. De algemene browserproef controleert daarnaast Coureurs, GOAT, Races en datacollectie. Uitvoer staat onder `storage/incident-recheck-20261017/`.


## Jaaroverzichten kwalificatie · 18 oktober 2026

Bij de eigen kwalificatieresultaten staan twee gezamenlijke jaarfiguren in de visuele stijl van het startonderzoek: kwalificatiepositie en afstand tot pole. Beide tonen individuele kwalificaties, mediaan, kwartielen en — bij voldoende verschillende waarnemingen — violins. Eén horizontale scrollcontainer houdt de jaren exact boven elkaar; de assen blijven staan.

De positie-as gebruikt alleen gehele positielabels en een niet-lineaire verdeling, met P1 bovenaan. De tijd-as gebruikt ln(1 + seconden), altijd van 0 tot 4 seconden met nul bovenaan. Waarden boven 4 seconden worden uitsluitend visueel afgekapt: de oorspronkelijke waarneming, kwartielen, mediaan en hover blijven behouden. De twee figuren hebben geen beter/slechter-pijlen.

De pole-referentie is de geregistreerde P1 in de kwalificatie, niet automatisch de startpositie na straffen of de sprintwinnaar. Tijden worden alleen binnen dezelfde beslissende fase vergeleken; Q1/Q2 worden niet stilzwijgend van een Q3-pole afgetrokken. Voor historische formats geldt dezelfde geregistreerde sessie- of totaaltijd. De bronmetadata bevat 1.166 compacte pole-referenties; er zijn geen oorspronkelijke uitslagen gewijzigd.

Het afzonderlijke blok “Eigen seizoenen en WK-verloop”, inclusief de seizoentabel en de twee WK-tijdlijnen, is verwijderd. De loopbaankerncijfers en de kwalificatiedetails blijven behouden.

De volledige controle telt nu 310 geslaagde tests. De aanvullende browserproef behandelt Nederlands en Engels, Max en Hamilton, historische jaren met gaten, jaarfilters, gezamenlijk scrollen, vaste assen, de bovengrens van vier seconden, mobiel tot 320 pixels en rechtstreeks lokaal openen. Uitvoer: `storage/qualifying-years-20261018/`. De analytische gegevenslaag blijft onder 64 MB. Deze wijzigingen zijn uitsluitend lokaal.

### Kwalificatieoverzicht en vaste coureurvermelding

De zes profielcards beginnen nu met Kwalificaties, gevolgd door Starter, Vrije-baan-specialist, Metronoom, Bandenfluisteraar en Opwarmer. Alleen de pitwindow-card is uit dit overzicht verwijderd; de bestaande detailanalyse en brongegevens blijven beschikbaar. De kwalificatiecard toont de mediaan van de werkelijk gekoppelde kwalificatieresultaten binnen de geselecteerde periode en springt naar de twee jaarfiguren. Die staan standaard volledig zichtbaar als eerste blok direct onder de cards.

De witte best-fitcurve volgt de jaarmedianen met vormbehoudende kubische interpolatie. Zij loopt door de mediane punten en bewaart lokale stijgingen en dalingen. De puntgewijze grijze 95%-bootstrapband gebruikt 400 herhaalde trekkingen van kwalificatiewaarden binnen ieder jaar. Ook bij weinig waarnemingen blijft een lijn zichtbaar: dun bezette stukken zijn onderbroken, een losstaand jaar heeft een korte medianelijn en lege jaren worden met een gestippelde verbinding zonder band overbrugd. Bij één waarneming wordt geen interval getekend. Oorspronkelijke seconden en posities blijven de rekenbasis; de assentransformatie is uitsluitend visueel.

Alleen de positiefiguur heeft subtiele groene Q3-, goudgele Q2-uitval- en rode Q1-uitvalzones. De compacte racegrenzen volgen F1DB-formatmetadata en aantallen kwalificatie-inschrijvingen, met controle tegen de geregistreerde segmentresultaten. Dit behandelt ook de twee afwijkende eliminatiesessies in 2016. De achtergrond gebruikt nu doorlopende zones per seizoen, met de meest voorkomende betrouwbare grenzen van dat jaar over alle beschikbare kwalificaties. Dit voorkomt lege stroken door ontbrekende sessies van één rijder. Afwijkende individuele sessies kunnen andere grenzen hebben; de zones zijn expliciet seizoenscontext, geen classificatie van elke afzonderlijke kwalificatie. Seizoenen zonder betrouwbare knock-outgrenzen blijven ongekleurd. Referentie voor de veldafhankelijke normale eliminatiegrenzen: FIA Sporting Regulations 2015, artikel 33.1; de afwijkende 2016-sessies zijn ook in de officiële F1-resultaten gecontroleerd.

De geselecteerde coureur staat rechts in de bestaande vaste paarse jaarselectiebalk: nummer, teamkleur, code en volledige paarse naam. Deze vermelding blijft binnen de balk bij scrollen, volgt een andere coureur of periode en blijft ook in de strategieatlas bestaan. Op kleine schermen krijgt de vermelding een eigen regel boven de jaarbediening.

De nieuwe achtergrond `assets/cards/driver-qualifying-v1.webp` is met de ingebouwde imagegen-tool gemaakt: een donker fysiek P1-pitbord aan een F1-pitstraat bij schemering. De volledige generatieprompt staat in het gelijknamige JSON-bestand. Het oorspronkelijke gegenereerde bestand is behouden; de lokale website gebruikt de compacte WebP-versie van circa 115 KiB.

Controle: **312 tests geslaagd**, zes aanvullende kwalificatiebrowsergevallen en acht algemene browsergevallen zonder scriptfouten, ontbrekende bestanden of pagina-overloop. Apart gecontroleerd: alle zes cards naast elkaar, laden van het nieuwe beeld, standaard zichtbare kwalificaties, George Russell → Max Verstappen en de vaste coureurvermelding bij verticaal scrollen. Schermafbeeldingen en rapporten staan onder `storage/qualifying-years-20261018/` en `storage/phase2-clones-20261017/`. De analytische gegevenslaag is 63.046.638 bytes. Productiepagina's en productie-assets zijn ongewijzigd; er is niets gepubliceerd.

De twee introductiezinnen over beschrijvende metingen en de gedateerde periode-totalen zijn verwijderd in NL en EN. De Starter-card heeft alleen de drie uitkomstpercentages. Alle zes cards hebben een unieke vaste accentkleur en geen geselecteerde klasse of toggle-status.


## Kwalificaties: mediane sessiebruggen en de definitieve tekenvolgorde

Ontbrekende Q3-tijden worden uitsluitend als herkenbare schattingen aangevuld. Per kwalificatie gebruiken we de mediane verandering van alle rijders met geldige tijden in beide opeenvolgende fasen: Q1→Q2 en Q2→Q3. Elke stap vereist minstens vijf brugrijders. Vanuit Q2 wordt één mediane verandering toegepast; vanuit Q1 beide. Een rechtstreeks gemeten, bruikbare eindfasetijd houdt voorrang. Ontbrekende of strijdige bronnoteringen worden niet overschreven. Open goudgele ruitjes tonen schattingen, met hun oorsprong, correcties en brugrijderaantallen in de hover.

De toets verbergt per Q3-deelnemer diens Q3 en verwijdert de rijder uit alle brugmedianen; voor een Q1-toets wordt ook diens Q2 verborgen. Deze leave-one-driver-out reconstructie omvat **4.023 rijderkwalificaties uit 415 races**, afzonderlijk voor Q2- en Q1-oorsprong. De gemiddelde absolute fout is respectievelijk **0,398456 s** en **0,519587 s**, tegenover **0,939336 s** en **1,593811 s** zonder sessiecorrectie. Het 90e percentiel van de absolute fout is **0,781 s** en **1,0604 s**. Dezelfde races leveren meerdere toetsgevallen; de toets bewijst geen nauwkeurigheid voor echte Q1/Q2-afvallers. Volledige reconstructies staan in `storage/qualifying-bridges-20261018/validation.json`; de compacte resultaten en definities worden uit hetzelfde bronarchief herbouwd.

Op uitdrukkelijk verzoek tellen **alle waarden, ook schattingen**, mee in violins, kwartielen, jaarmedianen en de witte curves. Ze blijven in de bron en in de losse punten als schatting herkenbaar. Het getoonde bootstrapinterval is **conditioneel op de puntschattingen** en rekent de aanvullende sessievertalingsfout niet mee; de uitleg vermeldt dat en geeft de toetsfouten afzonderlijk. Dit interval mag daarom niet als de volledige onzekerheid over geschatte Q3-prestaties worden gelezen.

De tijdas blijft 0–4 seconden. Waarden boven vier seconden staan als **v** op de onderrand: rood voor gemeten waarden, gestreept goud voor schattingen. Negatieve schattingen blijven numeriek behouden en krijgen een omgekeerd pijltje op de bovenrand; de grafiek maakt er geen echte pole van. De hover, medianen en andere berekeningen gebruiken de onbegrensde waarden.

De jaarkolommen zijn verbreed van 84 naar 144 pixels; gridkolommen van 66 naar 112, circuitkolommen van 152 naar 210 en pitbalanskolommen van 112 naar 156. Horizontaal scrollen blijft binnen de grafiek; vaste assen en gezamenlijke kwalificatiescroll blijven behouden. Violinvlakken liggen vóór de contextkleuren maar achter de overige gegevens. Daarna volgen modelbanden, curves en bredere witte medianen; losse punten liggen vooraan. Rekenwaarden en bronwaarnemingen van start-, racevervolg-, ronde- en pitgegevens zijn behouden.

Het blok **Gecorrigeerd startvoordeel per gridpositie** en het overeenkomstige **Gecorrigeerd racevoordeel per positie na ronde één** zijn uit het coureursprofiel verwijderd, samen met hun berekenings- en interpretatieblokken. De uitleg is volledig bewaard op `uitleg-start-en-raceonderzoek.html`, in NL en EN, met een link vanaf Datacollectie. Hoofdgrafieken en samenvattende scores blijven staan.

Controle: **317 tests geslaagd**; de aanvullende browserproef behandelt Max Verstappen, Romain Grosjean (inclusief het lege interval 2010–2011), Jack Aitken met één kwalificatie, desktop, mobiel, NL/EN en rechtstreeks lokaal openen. Jaarmedianen en witte curves zijn tegen alle ruwe gemengde waarden gecontroleerd; ook tekenvolgorde, bredere medianen, cap-pijlen en ongewijzigde starterscores zijn getest. Het analytische pakket is **63.080.348 bytes**, onder de lokale grens van 64.000.000 bytes. Uitsluitend de ontwikkelomgeving is aangepast; er is niets gepubliceerd.

## 19 oktober 2026 · eigen startfeiten en pitbalans per seizoen (lokaal)

De drie kaarten boven het startonderzoek tonen nu gemeten/geregistreerde starts, de aantallen en percentages gewonnen/behouden/verloren, en de mediane positiewinst met Q25–Q75. Bekende niet-starts zijn uitgesloten van de noemer; pitstraatstarts blijven geregistreerde racestarts maar zijn geen bruikbare gridstarts. Ontbrekende metingen zijn geen nul. De startgrafiek, onderliggende scores/export en het racevervolg zijn ongewijzigd. De helpdocumentatie beschrijft de nieuwe kaarten; oudere gecorrigeerde maten blijven als onderzoeksdocumentatie bewaard.

De pitbalans start met seizoenkolommen. Elk punt is een racemediaan, elk seizoen toont mediaan en kwartielen van die races. Elke race telt eenmaal; tegenstanderaantallen veroorzaken geen extra racegewicht. Het totaal blijft de mediaan van alle bruikbare racemedianen, geen som van tijdwinsten of mediaan van seizoensmedianen. Seizoenen zonder meting tonen geen nul. Racevergelijkingen en bronpopups blijven bereikbaar in de verdieping en via klikken op een racepunt. De tijdas blijft staan bij horizontaal scrollen.

Naast het standaard afgeronde hele pitprogramma is er een apart meetvenster voor afzonderlijke afgeronde stopcycli. Alleen bij gelijk totaal stopaantal; venster van vóór de vroegste van de twee gelijkgenummerde stops tot na de laatste. Andere stops in hetzelfde venster worden geweigerd, zodat overlappende strategie-episodes geen extra punten worden. De bestaande controles op finishers, klokken, rondeverschil, rode vlaggen, SC/VSC, dekking en uitschieters blijven gelden. Lokale cycli en hele programma's worden nooit in één samenvatting vermengd. Meerdere tegenstanders en cycli uit dezelfde race zijn afhankelijke waarnemingen. Dit beschrijft tijdsverloop inclusief tempo en verkeer en is geen geïsoleerd causaal pitstopeffect.

De uitklapbare tabel ‘Alle kwalificaties per race’ is van de coureurspagina verwijderd; jaargrafieken en brongegevens blijven behouden.

## 19 oktober 2026 · Pitwall briefing, P22 en chronologische kwalificatiecurve (lokaal)

Secties en grafieken van de coureursmodule hebben een herbruikbaar vector-info-icoon. De modal toont Pitwall briefing, een nieuwe gegenereerde pitwallachtergrond en één gedeelde tekstbron met de helppagina. Het definitieve circuit op het scherm is gebaseerd op de officiële FIA-kaart van Zandvoort, geen fictieve baan. De popup heeft geen timer, is met toetsenbord bedienbaar, houdt de bediening vast en herstelt de focus en paginascroll bij sluiten. Uitleg en voorbeelden worden pas bij openen ingeladen.

Elf onderwerpen hebben reproduceerbare grafische voorbeelden met twee coureurs. Kwalificaties heeft afzonderlijke voorbeelden voor positie en afstand tot pole, inclusief aantallen geschatte tijden. De perioden, bronhashes en gebruikte races zijn vastgelegd. Het pitbalansduel bevat dezelfde 26 races in 2021–2024; mediane verschuiving +3,1315 s voor Verstappen en −3,1315 s voor Pérez beschrijft één gespiegeld verschil, geen twee onafhankelijke effecten. Tempo, auto, banden en verkeer worden niet causaal uit elkaar gehaald. De startillustratie vergelijkt Massa en Ricciardo vanaf P5, met expliciete beperking dat races en omstandigheden niet gelijkgemaakt zijn. Bij vijf bruikbare pitvensterraces wordt geen betrouwbaar kwaliteitsverschil geclaimd.

Positie- en rangassen op de x-as stoppen bij P22. Het start- en racevervolgmodel en de samenvattingen behouden oorspronkelijke waarden; onzichtbare kolommen boven P22 worden vermeld. De veldgrafiek markeert rangen boven P22 aan de rand en behoudt hun waarden in de statistiek.

De kwalificatiecurve volgt een Gaussisch gewogen voortschrijdend gemiddelde op de chronologische racewaarnemingen, met vaste schaal vijf kwalificaties en een symmetrisch venster van vijftien. Het is een retrospectieve, gladde beschrijving, geen voorspelling. Binnen een jaar verandert uitsluitend de interne tijdpositie van de curve; punten, jaarmedianen, kwartielen en violins blijven gelijk. Onzekerheidsbanden gebruiken blokbootstrap over volledige opeenvolgende kwalificaties; ontbrekende jaren krijgen geen band. De rekencontrole onderscheidt gelijke jaarverdelingen met tegengestelde racevolgorde en controleert dat invoervolgorde de uitkomst niet verandert.

## 19 oktober 2026 · uitval- en incidentcontext in race-inhaaltellingen (lokaal)

`Context.retirement_context` vereist een bevestigde DNF, een bekend aantal voltooide ronden en niet-tegenstrijdige ronde-/sectortiming. De laatst gemeten voortgang vormt een onzekerheidsgrens, geen geschat exact crash- of uitvalmoment. Een volgordewisseling daarna wordt als onzeker bewaard en niet als race-inhaalactie geteld. Een latere uitval verwijdert geen eerdere passes. Expliciet bronbevestigde inhaalacties en onderbouwde handcorrecties behouden voorrang.

`Context.incident_context` geldt ook voor coureurs die verder rijden. Drie voorwaarden moeten tegelijk gelden: een nabije botsingsmelding waarin deze coureur expliciet genoemd wordt, een gelijktijdige gele vlag en een gemeten sector die minstens 50% én minstens acht seconden trager is dan zijn eigen recente sectorreferentie. Die referentie vereist minimaal drie metingen in de vorige vijf ronden. Een lokale gele vlag alleen, een incidentmelding alleen of een trage sector alleen is onvoldoende. Ook deze combinatie is context, geen bewijs van een exacte fysieke manoeuvre: de registratie wordt onzeker, niet als bewezen crashpass hernoemd.

Austin 2025 is in de bestaande lokale racepagina en de bijbehorende exports bijgewerkt: 56 → 30 analytisch getelde acties. Dertien registraties tegenover Sainz na zijn laatste gemeten sector in ronde zes en dertien tegenover Antonelli tijdens zijn vertraagde sector met gele vlag en botsingsmelding staan apart als onzeker. Alle 186 gebeurtenissen, bronregistraties, IDs en kaartcoördinaten blijven bewaard. De oorspronkelijke bestanden staan verliesloos in `storage/racing-overtakes-20261019/austin-before.tar.gz`; analyse, export, methodepagina en manifest zijn consistent bijgewerkt. Het manifest bevat methoden, uitgesloten IDs en classifierhash.

Daarna is de controle op alle 1.166 actuele races uitgevoerd: 148 met gedetailleerde timing en 1.018 historische pagina’s met gereconstrueerde positiewisselingen. Bij 59 actuele races daalde de analytische telling; over de actuele timingraces samen van 7.862 naar 7.422. Austin stond daarbij al op 30 na de eerdere lokale correctie. Alle 149 beschikbare timinguitvoeringen zijn gesynchroniseerd, inclusief één oudere Singapore-uitvoering naast de actuele. De oudste, vervangen Singapore-uitvoering heeft geen oorspronkelijke lokale analyse meer en staat ook niet in de beschikbare seizoenarchieven; deze is expliciet als niet herberekend opgenomen. De actuele Singapore-uitvoering is wel volledig meegenomen. Historische rondevolgordes blijven correct gelabelde reconstructies; zonder nauwkeurige incidenttiming is geen schijnbaar exacte crashcorrectie toegevoegd.

`python -m f1_analysis.race_event_refresh --apply` controleert bestaande uitvoeringen zonder opnieuw te renderen, brongegevens op te halen of te publiceren. Een gewone aanroep zonder `--apply` maakt alleen een controleplan. Elke gewijzigde uitvoering krijgt een revisie in het manifest en nieuwe bestandshashes. Pagina, losse interactieve circuitkaart, JSON/CSV-gebeurtenissen, kerncijfers, bronvergelijking, kaartdekking en methodepagina zijn gesynchroniseerd. Oorspronkelijke event-ID’s, bronregels, bewijzen, handcorrecties, kaartcoördinaten en alle ruwe data blijven gelijk. Bestaande scripts, stijlen en opmaak zijn niet opnieuw opgebouwd. Een tweede toepassing zonder nieuwe gegevens wijzigt niets.

De verliesloze back-up staat in `storage/racing-overtakes-all-20261019/all-races-before.tar.gz`. `report.json` geeft per uitvoering de oude/nieuwe telling en afzonderlijke uitval-/incidentcontext; `verification.json` en `browser-report.json` leggen de controles vast. Deze bestanden en racewijzigingen zijn lokaal, niet gepubliceerd.

Zonder exact incident-/stopmoment kan het verlies in het ongemeten slotdeel van een uitvalronde niet als bewezen crashpass of bewezen echte inhaalactie worden bestempeld. Incidenten zonder voldoende sector-, vlag- of meldingsdekking blijven een beperking; een volledig gegarandeerde telling van fysieke race-inhaalmanoeuvres is uit alleen timing niet mogelijk.

De standaardconfiguratie sluit ook reeds als technisch positieverlies geclassificeerde gebeurtenissen uit van de analytische inhaaltelling. De volledige bron-/positieadministratie behoudt ze. Dit is ook in de lokale Austin-configuratie vastgelegd.

## 19 oktober 2026 · echte voorbeeldgrafieken, info bij alle onderdelen en robuuste trend (lokaal)

Het dubbele drietal kaarten onder De starter is verwijderd; de bestaande topkaart blijft. Hoofdtitels, afzonderlijke statistiekkaarten, zes specialismekaarten en grafiektitels hebben een infoknop. De topkaartknop en infoknop zijn afzonderlijke elementen: uitleg openen wijzigt geen selectie. Vijftien onderwerpen zijn beschikbaar, inclusief profiel, loopbaanfeiten, uitval/straffen en dekking.

De eerdere afzonderlijke histogramillustraties zijn vervangen door de werkelijke productie-renderers via `driver-example-charts.js`. De voorbeelden behouden volledige race-/jaar-/circuitverbanden en echte individuele waarnemingen. Starter en racevervolg tonen dezelfde P1–P22-as, symmetrische niet-lineaire ±10-schaal, afkappijlen, modelcurve en band. Kwalificatievoorbeelden gebruiken dezelfde twee gekoppelde jaarplots, logtransformatie, Q-zones en schattingssymbolen. Ook de overige voorbeelden gebruiken hun eigen bestaande grafiekfuncties. Gelijksoortige voorbeelden scrollen samen met vaste assen. Het voorbeeldbestand groeit naar circa 1,7 MB, uitsluitend bij uitleg opgevraagd; het bevat echte begrensde rijen en bronhashes, geen uitbreiding van de hoofdgegevens.

Alle twaalf voorbeeldmeetsets zijn opnieuw gecontroleerd met de productie-selecties, inclusief finishers, pitstraatstarts, individuele vrije ronden en directe pitduels. De popup- en helppaginatekst zijn voor alle vijftien onderwerpen identiek getest op 1440 px Nederlands, 390 px Engels en 320 px lokaal via file://. Geen horizontale pagina-overloop of scriptfouten. De stijlgids en README leggen de infoknop en de eisen aan toekomstige voorbeelden vast.

De kwalificatiecurve behoudt het Gaussische chronologische venster maar gebruikt een robuuste Huber-locatie. Zeldzame zeer trage Q3-waarnemingen domineren daardoor niet meer een groot dal tijdens de winter. De invloed wordt verkleind in de curve, niet door de race uit de waarnemingen te verwijderen. Dezelfde schatter wordt in de blokbootstrap gebruikt. Gewogen medianen middelen de twee centrale waarden bij exact gelijke halve gewichten, zodat dun bezette symmetrische voorbeelden geen voorkeurskant krijgen. De regressiecontrole bewaart expliciet een echt datapunt van 18 seconden en laat een aanhoudende verslechtering wel doorwerken.

Bij Verstappen rond 2022–2023 daalde de kunstmatige curve-uitslag van ongeveer 1,7–1,8 seconde naar ongeveer 0,05 seconde. Het verschil is rechtstreeks naast de eerdere gewogen-gemiddeldeberekening gecontroleerd. Alle 489 kwalificatiepunten, 24 violins, 24 mediaanstreepjes, 24 kwartielbalken en de asopmaak bleven bytegelijk. Bewijs en schermbeelden: `storage/pitwall-examples-v2-20261019/`. Alleen lokaal; niet gepubliceerd.
