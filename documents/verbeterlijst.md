# Verbeterlijst voor coureursanalyses en GOAT

Bijgewerkt op 16 oktober 2026. Deze lijst bouwt voort op het [fase 2 onderzoeksplan](fase-2-onderzoeks-en-ontwikkelplan.md). De onderstaande verbeteringen aan scores zijn ontwerpwerk; ze veranderen de huidige berekeningen nog niet.

De coureurspagina verklaart wat één coureur tijdens zijn eigen carrière heeft laten zien. GOAT onderzoekt hoe verschillende coureurs presteren wanneer hun omstandigheden vergelijkbaar worden gemaakt. Beide gebruiken dezelfde waarnemingen en definities, maar beantwoorden verschillende vragen.

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
| Gemeenschappelijke verdeling van beginposities en circuits | Alleen indien de bezoeker expliciet een vergelijking kiest | Vereist voor een vergelijkbare totaalscore |
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
