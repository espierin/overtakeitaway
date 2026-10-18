# Bannernavigatie en Over mij

Lokale wijziging; geen commit, upload of publicatie.

Naast de bestaande seizoenenknop en de NL/EN-taalkeuze staan drie extra knoppen: **Races**, **Drivers**, **Over mij / About me**. Races verwijst naar `races.html`, Drivers naar `analysis-lab.html#tab=profiles`. De oorspronkelijke seizoenenknop verwijst eveneens naar de verplaatste raceverkenner.

De navigatie is geplaatst op 1.170 lokale pagina's: startpagina, raceverkenner, rijdersanalyse, de index onder analyses en 1.166 racepagina's. Alle nieuwe interne verwijzingen zijn gecontroleerd. De generatie en compacte publicatie gebruiken dezelfde gedeelde component, zodat latere builds de knoppen behouden.

Het dialoogvenster vertelt in de eerste persoon dat Eric Spierings Overtake It Away voor de lol maakt, vanuit zijn plezier in data, analyseren en presenteren. Het benoemt expliciet dat toegang gratis blijft zolang de gebruikte gratis middelen gratis blijven. Wie waardering financieel wil uiten, wordt verwezen naar zijn andere hobby: het mede oprichten en runnen van Stichting De Blauwe Hut.

Gecontroleerde verwijzingen op 14 oktober 2026:

- Werk en cv: https://espierin.github.io/cv/ — bereikbaar, HTTP 200.
- Stichting en steun: https://blauwehut.nl/steun-ons/.
- Donatiemogelijkheid waar die pagina naar verwijst: https://blauwehut.nl/donatie-formulier/.

De donatieknop opent het formulier van de stichting. Er wordt op deze website geen betaling gestart of verwerkt. Externe links openen in een nieuw tabblad; de analyse blijft behouden.

De popup volgt de gekozen taal, ook wanneer die verandert terwijl hij openstaat. Sluiten kan via de sluitknop, Escape of de achtergrond. De popup gebruikt de bestaande donkere stijl, cyaan kader en paarse accenten. De knoppenrij krijgt op kleinere schermen een eigen regel en kan op mobiel omslaan.

Controles: de lokale DOM-tests voor navigatie, NL/EN, popup openen/sluiten/hergebruiken, cv-link, donatielink en gratis-toegankelijkheidstekst slagen. De audit vond op alle 1.170 pagina's de volledige navigatie en geen ontbrekende interne verwijzingen. Visuele browsercontrole blijft open vanwege de eerder vastgestelde verbindingsfout van de browseromgeving.
