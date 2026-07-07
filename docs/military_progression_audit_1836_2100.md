# EU4 2K Military Progression Audit (1836–2100)

## Scope

This audit reviews land-unit, naval-unit and combat-modifier progression against the revised technology timeline. It also identifies what EU4 can and cannot represent directly. No unit balance was changed during this audit.

## Technology numbering

The technology files use a Tech 0 baseline block. Consequently, a file block commented `Tech 94` is the effect applied when the UI advances to displayed technology level 95. The 2100 block therefore correctly satisfies the Future Age's `adm_tech = 95` gate.

The generated 2150 block commented `Tech 96` is likewise displayed as technology level 96. There is no missing technology level.

## Land progression

| Year | Displayed MIL | Principal unlocks |
|---:|---:|---|
| 1835 | 78 | Field howitzer |
| 1850 | 79 | Percussion-cap musket |
| 1870 | 80 | Armstrong gun |
| 1890 | 81 | Needle gun, Chassepot, lever-action rifle, modern cavalry |
| 1910 | 82 | Bolt-action rifle, machine gun, modern fortification |
| 1930 | 83 | French 75, early tank families |
| 1945 | 84 | WWII tanks, assault rifle, rocket artillery |
| 1960 | 85 | AK-47, M16, hardened bunker |
| 1975 | 86 | Main battle tank families |
| 1990 | 87 | Modern self-propelled and rocket artillery |
| 2005 | 88 | Land Warrior, integrated defence network |
| 2020 | 89 | Armata and M1A3 abstractions |
| 2080 | 93 | Robot Soldier and Mecha Warrior |
| 2100 | 95 | Orbital defence complex and final modern combat scaling |

Findings:

- Infantry, armour-as-cavalry and artillery all have valid modern upgrade paths.
- Unit pips generally increase from 8–10 in the nineteenth century to 10–11 in the modern/future period.
- Armour is represented by EU4's cavalry category. This is mechanically appropriate because it preserves a distinct mobile front-line unit without engine changes.
- Rocket artillery remains in the artillery category, which is also appropriate.
- Technologies without a new unit still provide fire, shock, tactics, supply or fortification improvements, so progression does not stop.
- Future repeatable MIL technologies continue supply scaling and periodically add tactics and morale.

No clearly broken land-unit reference or missing unit file was found.

## Combat scaling

The modern technology sequence adds:

- infantry, cavalry and artillery fire/shock at staged intervals;
- military tactics at major doctrinal transitions;
- supply-limit growth;
- negative combat-width adjustments during industrial mass warfare;
- escalating fort levels from 9 through 12.

The negative combat-width changes are intentional ET abstractions that counterbalance the very large accumulated combat width from the extended ancient-to-modern timeline. They should not be changed without an observer battle comparison.

The Information and Future Age triggered modifiers reduce land morale and force limits while increasing regiment and maintenance costs. These era modifiers are part of the military balance and must be included in any combat test.

## Naval progression

| Year | Heavy ship | Light ship | Galley abstraction | Transport |
|---:|---|---|---|---|
| 1850 | Ironclad | Existing frigates | Existing galley | Existing transport |
| 1910 | Destroyer / Dreadnought | Cruiser | Torpedo Boat | Troopship |
| 1945 | Battleship | Cruiser | Torpedo Boat | Troopship |
| 1975 | Missile Destroyer | Missile Cruiser | Torpedo Boat | Troopship |
| 2100 | Missile Destroyer | Missile Cruiser | Torpedo Boat | Troopship |

Confirmed gap:

- Heavy and light ship models stop in 1975.
- Galley-category coastal combat ships and transports stop in 1910.
- No post-2100 naval units exist despite repeatable technology continuing to 9950.

EU4 has only four normal ship categories. A practical modern mapping is:

- Heavy ship: blue-water destroyer/cruiser or future capital combatant.
- Light ship: patrol frigate and trade-protection combatant.
- Galley: coastal missile craft, corvette or littoral combat ship.
- Transport: amphibious assault and strategic sealift ship.

## Aircraft limitation

EU4 has no aircraft unit category, air map layer, air bases or air-combat phase. Aircraft should not be forced into ordinary regiments because that would produce misleading occupation and siege behavior.

Recommended later abstraction:

- technology and country modifiers for reconnaissance, fire damage, movement and siege ability;
- province air-base buildings only if they have a clear economic or military modifier role;
- event/decision-based strategic air campaigns for major wars;
- drones represented through intelligence, artillery and combat modifiers.

This should be a separate system after conventional warfare is stable.

## Recommended implementation batch

Add two naval generations while reusing existing ship-category graphics:

### 2020 generation

- Guided Missile Cruiser — heavy ship.
- Modern Frigate — light ship.
- Littoral Combat Ship — galley.
- Amphibious Assault Ship — transport.

### 2100 generation

- Autonomous Arsenal Ship — heavy ship.
- Unmanned Oceanic Frigate — light ship.
- Autonomous Coastal Defence Ship — galley.
- Advanced Strategic Sealift — transport.

Each generation should replace only the previous unit in the same category, use moderate stat increases, and avoid multiplying naval maintenance beyond the existing age scaling.

## Validation requirements

1. Confirm every new unit is enabled by exactly one technology.
2. Confirm all four ship categories have a selectable unit at 1836, 1910, 1975, 2020 and 2100.
3. Confirm AI countries upgrade their preferred ship types.
4. Compare equal-cost fleets from 1910, 1975, 2020 and 2100.
5. Verify transport capacity and naval attrition remain functional.
6. Run an observer test to ensure AI nations still build balanced fleets rather than only one category.

## Decision

Land warfare should remain unchanged until battle data is available. The next contained implementation should fill the naval unit gaps at 2020 and 2100, with aircraft deferred to a dedicated abstraction milestone.

## Implemented in 1.3.0

- Added complete heavy, light, galley and transport generations at 2020.
- Added complete successor generations at 2100.
- Reused existing late-game ship models through `sprite_level` to avoid missing graphics.
- Left land combat and aircraft abstractions unchanged pending dedicated testing.
