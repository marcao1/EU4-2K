# Modern Institutions

EU4 2K replaces the eight vanilla institutions while retaining their internal
identifiers for engine, interface, icon, and technology-table compatibility.
No country has an institution embraced at the `2000.1.1` bookmark.

| Order | Institution | Expected emergence | Embracement bonus |
|---:|---|---|---|
| 1 | Globalized Economy | `2000.4.1` | +1 merchant |
| 2 | Advanced Automation | `2050.4.1` | -5% development cost, -5% construction cost |
| 3 | Drone Technology | `2100.4.1` | +1 leader without upkeep |
| 4 | Social Media | `2150.4.1` | -5% stability cost |
| 5 | Renewable Energy | `2200.4.1` | +10% goods produced |
| 6 | Artificial Intelligence | `2250.4.1` | +10% provincial trade power |
| 7 | Mars Economy | `2300.4.1` | +15% national tax |
| 8 | Space Marines | `2350.4.1` | +25% national manpower |

Each institution becomes eligible in April of its target year, fifty years
after the previous institution. Origins are selected from developed state
capitals. After the first institution, the origin province must already contain
the preceding institution. Spread occurs through friendly neighboring/coastal
provinces, developed capitals, and countries that have embraced it.

When an institution emerges, its origin event saves the actual province as the
institution origin, provides a clickable go-to location, and adds a permanent
birthplace marker with `+25%` local institution spread. This applies to all
eight institutions, including the first Globalized Economy origin.

The interface also receives vanilla-style historical origin metadata: New
York, Tokyo, Washington, San Francisco, Copenhagen, Beijing, Houston, and
Moscow respectively. These are interface reference locations; the actual
origin remains the eligible province selected when the institution emerges.

The internal mappings are:

- `feudalism` -> Globalized Economy
- `renaissance` -> Advanced Automation
- `new_world_i` -> Drone Technology
- `printing_press` -> Social Media
- `global_trade` -> Renewable Energy
- `manufactories` -> Artificial Intelligence
- `enlightenment` -> Mars Economy
- `industrialization` -> Space Marines
