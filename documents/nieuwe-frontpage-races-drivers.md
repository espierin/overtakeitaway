# Nieuwe lokale startpagina: Races en Drivers

De startpagina is `index.html`. De eerdere, volledige raceverkenner staat nu in `races.html`, op hetzelfde mapniveau zodat de bestaande relatieve links blijven werken. De grote Drivers-tegel opent `analysis-lab.html#tab=profiles`.

Beide tegels zijn volledig aanklikbaar, met toetsenbordfocus, rustige hoverbeweging zonder inzoomen en een mobiele indeling onder elkaar. De startpagina gebruikt het originele pixellogo op zwart en dezelfde opgeslagen NL/EN-taalkeuze als de andere pagina's. De raceverkenner behoudt zoeken, seizoenen, wereldkaart en alle racegegevens. Het logo op de raceverkenner en in de analyseomgeving opent de nieuwe startpagina. ‘Alle seizoenen’ in de analyseomgeving opent de raceverkenner.

De opbouw van de catalogus, de analyseomgeving en de compacte publicatie zijn aangepast aan de nieuwe bestandsindeling. De beelden worden als compacte WebP-bestanden opgeslagen; samen circa 220 kB. De generatiebestanden zijn opgenomen zodat een volgende lokale opbouw dezelfde indeling behoudt.

Alles blijft lokaal. Geen commit, upload of publicatie zonder expliciete toestemming na lokale controle door de eigenaar.

## Nieuwe beelden

Gemaakt met de ingebouwde imagegen-tool; geen CLI/API-fallback. De originele gegenereerde PNG's blijven bewaard. WebP-kopieën voor de website:

- `assets/home/races.webp` (1536 × 1024)
- `assets/home/drivers.webp` (1536 × 1024)

Dezelfde WebP-bestanden staan in `src/f1_analysis/assets/home/` voor herhaalbare builds.

### Gebruikte prompt: Races

Use case: photorealistic-natural. Asset type: large photographic navigation tile on the existing Overtake It Away Formula 1 analytics website. Generate a cinematic, realistic motorsport photograph, wide landscape 3:2. Subject: a group of modern open wheel Formula 1 racing cars speeding through a circuit bend, low trackside camera, leading car in three-quarter front view, others following deeper in shot, recognizable racing context. Dark luxurious black and charcoal palette with restrained cool cyan reflections and small red kerb accents, late dusk, subtle mist, detailed carbon fiber and wet tarmac. Cars occupy middle and upper right. Keep the lower quarter naturally very dark for white HTML text overlay. Black edges blend gently into a pure black website. Consistent editorial motorsport photography, high quality, rich detail, no logos, no legible lettering, no typography, no watermark. Not an illustration, not a UI mockup.

### Gebruikte prompt: Drivers

Use case: photorealistic-natural. Asset type: large photographic navigation tile for Drivers on Overtake It Away Formula 1 analytics website. Create a wide landscape 3:2 high-end editorial motorsport photograph. Extreme close-up of a Formula 1 driver's helmet, cropped three-quarter front profile, visor reflects subtle pit lane lights, detailed carbon and glossy near-black shell with restrained purple and cool cyan accents, anonymous design, no identifiable person or team. Helmet fills the upper and right two thirds, lower quarter and left edge naturally dissolve into rich pure black to support white HTML overlay. Very dark cinematic low-key dusk light, controlled luminous visor highlights, sharp material detail, same black charcoal cool-cyan mood as dark F1 race photography. No lettering, no logos, no typography, no watermarks, no UI, no illustration.

## Controle

Alle 142 tests slagen. De twee gemaakte foto's zijn bekeken. Links, de taalkeuze (ook zonder beschikbare browseropslag), het behoud van het racearchief en de analyseomgeving zijn lokaal gecontroleerd. De compacte publicatie wordt op een klein testproject gecontroleerd op het behoud van de nieuwe startpagina en `races.html`. De browserverbinding faalt bij het opstarten; er is daarom geen voltooide visuele controle van de pagina op desktop en mobiel geclaimd. Deze controle blijft onderdeel van de lokale beoordeling door de eigenaar.
