# Offline world map sources

Retrieved on 11 October 2026.

- `circuits.json`: Jolpica F1 circuit catalogue, https://api.jolpi.ca/ergast/f1/circuits/?limit=100 . Coordinates, names and location metadata. The UI includes circuits with championship races present in the local archive (1950–2025), including the Indianapolis 500 championship rounds. Unused/future catalogue entries are excluded.
- `land.geojson`: Natural Earth, 1:110m land, https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson . Public domain: https://www.naturalearthdata.com/about/terms-of-use/ . Equirectangular projection rendered as local SVG.

These files are embedded into the generated index pages. Browsing the catalogue or map makes no external API requests.
