# Zes rijderskwaliteiten — lokale eerste versie

De zes onderdelen staan op `analysis-lab.html`, in het tabblad **Rijdersprofielen**, onder de bestaande tempografiek. Ze volgen de onderzochte rijder, seizoen- en circuitselectie. Een afzonderlijk compoundfilter geldt alleen voor deze zes onderdelen; starts zijn onafhankelijk van compound. De bestaande raceverkenner en strategieatlas blijven beschikbaar. De sectie “Alle rijders als referentie” en de berekening van die overzichtstabel zijn op verzoek verwijderd. Ook de algemene tabel “Onderliggende races / Underlying races” is op verzoek verwijderd. De bronnen per afzonderlijke kwaliteit blijven toegankelijk. De compacte gegevens voor het kiezen en onderzoeken van andere rijders blijven nodig; voor de vervallen tabel bestond geen aparte dataset. Ongebruikte vergelijkingsvelden (de oude verschilspreiding, teamgenootcode en de lijst met gekoppelde ronden) worden niet meer naar de pagina geëxporteerd.

**Nog niet gepubliceerd.** Upload naar GitHub blijft wachten op expliciete toestemming na lokale controle.

## Wat de zes onderdelen meten

| Onderdeel | Waarde en teken | Vereiste metingen |
|---|---|---|
| De vrije-baan-specialist | Symmetrisch rondetijdverschil in procenten tegenover de teamgenoot; negatief = sneller. | Minstens zes passende vrije ronden per stintpaar; zelfde raceronde en compound, maximaal twee ronden leeftijdsverschil, beide banden minstens drie ronden oud. |
| De metronoom | Robuuste spreiding van eigen rondetijden rondom de eigen stinttrend, gedeeld door het stinttempo; lager = regelmatiger. | Minstens acht vrije ronden per set, minstens zes ronden bereik. Theil–Sen-lijn, 1,4826 × MAD van restfouten. Eigen stinttempo staat bij de onderliggende race. |
| De bandenfluisteraar | Groei van het relatieve tempovoordeel per tien extra ronden bandenleeftijd, in procenten van rondetempo; positief = beter behoud. | Minstens acht passende vrije ronden met minstens tien ronden leeftijdsbereik. Robuuste helling van het teamgenootverschil; aparte analyse per setpaar. |
| De opwarmer | Extra rondetijd bij leeftijd 1–3 tegenover de teruggetrokken eigen trend bij leeftijd 4–10, als percentage van referentietempo; lager = minder vroeg verlies. | Bekende nieuwe set na geregistreerde stop, minstens twee vroege en vier referentieronden. Leeftijd vier moet gemeten zijn, minstens vier ronden referentiebereik. Outlap uitgesloten. |
| De pitwindow-specialist | Voordeel tegenover de eigen stinttrends in twee volledige ronden vóór de inlap en twee volledige ronden na de outlap; positief = sneller dan trend. | Alle vier ronden bruikbaar, groene stopcyclus, verschillende bandensets, minstens zes referentieronden per set buiten pitvensters; extrapolatie maximaal vier ronden. |
| De starter | Eigen positie na ronde één, gegroepeerd per eigen gridpositie. Verticale violin met mediaan en 25%/75%-kwartielen; losse punten per race. | Bekend integer grid en eerste doorkomst, geen pitlane, DNS of expliciet nul voltooide ronden. Geen referentiecorrectie en geen minimumaantal andere starters. Violin bij minstens vijf starts en twee uitkomsten; anders punten en kwartielen. |

Compounds zijn voorlopig SOFT, MEDIUM en HARD. Afzonderlijke sets met dezelfde compound worden afzonderlijk gehouden. Leeftijd is de bronleeftijd **vóór** de lopende ronde. Unknown is geen nul.

## Vrije lucht en uitsluitingen

Voor de vijf tempometingen is positieve verkeersinformatie vereist: op 25%, 50% en 75% van de ronde een interval van minstens drie seconden (niet ouder dan tien seconden), of de laatst gemelde positie is die van de leider. Positiewijzigingen zijn gebeurtenissen; een ongewijzigde gemelde leiderspositie vereist geen voortdurend nieuw positiebericht. Geen interval of positie betekent niet automatisch vrije lucht. Achterblijvers en alle verkeerssituaties zijn hiermee niet gegarandeerd uitgesloten.

Bronwaarschuwingen, bekende verkeersmarkeringen, pit-/uitronden, eerste ronde, natte/onbekende compounds, onbekende set/leeftijd en neutralisaties worden uitgesloten. Setidentificatie vereist een unieke match met de geregistreerde stint en leeftijd. De opwarmer gebruikt expliciet een bekende nieuwe set. De pitwindow-specialist beoordeelt rondetijduitvoering, geen pitcrewduur of oorzaak van een geslaagde undercut.

## Aggregatie en grafieken

Eerst de mediaan van geaccepteerde sets/vensters binnen één race, vervolgens de mediaan over races. Geen algemene ranglijst of samengesteld rapportcijfer. Bij minstens vijf bruikbare races: een reproduceerbaar percentielinterval uit 800 bootstrap-hersteekproeven van volledige races. Dit beschrijft onzekerheid binnen de geobserveerde steekproef; herhaalde circuits, tegenstanders en omstandigheden kunnen afhankelijkheid geven.

Alle zes kaarten blijven zichtbaar, inclusief onvoldoende dekking. Elke kaart opent de eigen grafiek, methode en bronraces. Een race kan apart worden bekeken; de bandenfluisteraar toont gemeten leeftijd/tempo-punten en de robuuste lijn binnen het gemeten bereik. De metronoom toont stintrestfouten, de opwarmer vroege en referentieronden, de pitwindow-specialist de vier gemeten vensterronden. Starts tonen ruwe winst naast de referentie.

De teamgenootcontext bij metronoom, opwarmer en pitvenster gebruikt dezelfde race en compound, maar kan een andere racefase betreffen. De vrije-baan-specialist en bandenfluisteraar vereisen juist gekoppelde raceronden. Deze verschillen staan in de methode. Snelheid, strategie, auto, schade, opdrachten en omgeving zijn geen volledig geïsoleerde factoren.

## Reproduceerbaarheid en opslag

Definitie `driver-qualities-v1/start-distribution-v1`, gegevensschema 2. De bestaande dashboardhash blijft behouden; per race is ook de hash van de aanvullende genormaliseerde invoer vastgelegd. Alleen compacte afgeleide waarnemingen worden naar de analysepagina geschreven, geen intervalreeksen of telemetry. Het onafhankelijke budget van 20 MB en maximaal vijf kalenderseizoenen blijven gehandhaafd.

## Lokale controle

Alle 151 tests slagen. Gerichte rekenproeven controleren onder meer: ontbrekende/stale verkeersdata, bevestigde leider, basissnelheid versus bandenbehoud, eigen spreiding en echte nulwaarden, gebruikte versus nieuwe sets, gescheiden identieke compounds, maximale opwarmextrapolatie, groene pitvensters, compoundverschillen en pitlanestarts. De interactiecontrole omvat zes onderdelen, NL/EN, compoundfilter, bronraces, grafiekdetails, behoud van selectie en onbekende dekking. Deze controle gebruikt een lokale DOM en vervangt geen browserweergave.

De browserverbinding start niet op (`BROWSER_USE_SECURITY_MODE`-fout). Er is geen voltooide visuele controle van desktop- en mobiele weergave geclaimd; die blijft onderdeel van de lokale review.

## Starter: verdeling per gridpositie

Op verzoek vervangt een verticale startverdeling de eerdere vergelijking met nabijgelegen starters. De x-as bevat alle daadwerkelijk waargenomen startposities van de onderzochte rijder binnen de seizoen-/circuitselectie. De y-as is de positie bij de eerste eigen doorkomst; P1 staat bovenaan. De gestippelde cyaan markering toont de eigen beginpositie. Elk groen/cyaan/rood punt is een race met netto winst/gelijke positie/verlies; hover toont de race en klikken opent de racepagina.

De mediaan is wit; de verticale paarse balk loopt van Q25 tot Q75. Kwartielen gebruiken lineaire interpolatie en zijn geen betrouwbaarheidsintervallen. De violin toont een gladde, per groep op maximale breedte genormaliseerde dichtheid; aantallen staan als n onder de kolom. Er is geen violin bij minder dan vijf starts of één unieke uitkomst. Alle geobserveerde races worden wel getoond. De tabel onder de grafiek vermeldt n, Q25, mediaan en Q75 per startpositie.

De dichtheidskromme gebruikt een Gauss-kern, h=max(0,4; 0,9 × robuuste spreiding × n^-0,2), 81 punten, en wordt begrensd tot geldige posities en maximaal een halve positie buiten de geobserveerde uitersten. Posities zijn discreet: de violin is een visuele samenvatting, geen gemeten continue positieverdeling. Bij veel startposities is de grafiek horizontaal scrollbaar. Referentie voor de betekenis van medianen en kwartielen: [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/boxplot.htm).
