# EU4 2K Map Foundation

## Scope

The clean EU4 2K project uses the map package from Extended Timeline 1.18.2 as its geographic foundation.

Source:

```text
ExtendedTimeline 1.18.2/ExtendedTimeline/map/
```

Target:

```text
MillenniumDawnEU4/map/
```

The complete map package is kept together because its province bitmap, definition table, positions, terrain, climate, adjacencies, areas, regions, superregions, and graphical layers use the same province IDs and must remain synchronized.

Two source-data defects were corrected in the clean copy:

- Removed incomplete, unused `definition.csv` generator residue after the last valid province, ID 4941.
- Recolored four isolated unmapped pixels to their surrounding sea provinces: two in the Gulf of Zambeze and two in the Central Pacific.

These corrections do not change any valid province border or province ID.

## Included

- Province bitmap and province definitions
- Province positions
- Terrain, height, river, tree, and normal-map bitmaps
- Terrain textures and definitions
- Areas, regions, superregions, and continents
- Climate and trade winds
- Sea zones and lakes
- Canal definitions and canal graphics
- Adjacencies and ambient map objects

## Not included in the original map-only copy

The map-foundation step did not copy Extended Timeline gameplay or historical content. Later generated phases may now add narrowly selected definitions outside `map/` while keeping this package itself map-only:

- Country history
- Province history
- Diplomacy history
- Wars
- Events
- Decisions
- Missions
- Governments
- Religions
- Cultures
- Technologies
- Institutions
- Units
- Buildings
- Localisation
- Interface changes

No dated history is stored in the copied `map/` package, so it contains no pre-1444 historical setup.

## History policy

- Content dated before `1444.11.11` will not be imported into the clean project.
- The primary scenario will be built for `2000.1.1`.
- Historical data from 1444 onward will be imported only when it is needed for the modern scenario or a retained mechanic.
- New province and country history should use the Extended Timeline province IDs defined by this map.

## Descriptor policy

The generated foundation replaces `common/bookmarks`, `history/countries`, and `history/provinces`. The province path now contains the clean effective `2000.1.1` snapshot, preventing incompatible vanilla ownership from being applied to ET province IDs.

## Next step

Create the `2000.1.1` political map:

1. Establish the complete list of playable country tags.
2. Create clean country history files.
3. Create one clean province history file per land province.
4. Assign year-2000 ownership, control, cores, capitals, cultures, vanilla religions, development, and trade goods.
5. Begin with the Balkans, then complete Europe, the United States, Russia, and China.
