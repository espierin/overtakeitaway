# Fase 2 · uitvoering en controle

**Lokale ontwikkeloplevering, 17 oktober 2026.** Dit verslag hoort bij de drie `_2`-pagina’s en vervangt het onderzoeksplan niet. Er is geen upload uitgevoerd. De oorspronkelijke pagina’s en scripts zijn op hun kloonhash gecontroleerd.

## Wat er per planstap staat

| Stap | Lokale uitvoering | Grens aan de conclusie |
|---|---|---|
| A · definities en dekking | Gedeeld versie- en parameterregister, echte startersaantallen, circuitvarianten, duidelijke uitsluitingen, expliciete referentievensters | Bekende bronhiaten blijven zichtbaar; een kalenderregel bewijst geen resultaat |
| B · eigen feiten | Gekoppelde seizoensstanden, punten, starts, zeges, podia, poles, snelste ronden, sprinttotalen, eigen WK- en kwalificatieverloop, historische teams | Afzonderlijke officiële WK-notering kan ontbreken bij nul punten; lopend seizoen is voorlopig |
| C · eigen profiel | Zes kaarten en eigen detailfiguren; starter en ronde-één-tot-finish; teamgenootduel behouden; veldtabellen verwijderd; afzonderlijke robuuste regelmaat | Tempo en regelmaat zijn verschillende maten; bevestigde finishers vormen een geselecteerde groep |
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
