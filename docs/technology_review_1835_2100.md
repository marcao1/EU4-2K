# EU4 2K Technology Review: 1835–2100

This document audits Extended Timeline technology levels 78–95 before any
gameplay changes are made. Levels 1–77 remain outside the current scope.

## Current timeline

| Level | Year | Administrative | Diplomatic | Military |
|---:|---:|---|---|---|
| 78 | 1835 | Electricity; factory | Railroad | Percussion Cap; field howitzer |
| 79 | 1848 | Religious Pluralism | Ironclad; railroad | Breech-Loading Rifled Guns; percussion-cap musket |
| 80 | 1855 | Replaceable Parts | Telephone; naval base; ironclad | Needle Gun; Armstrong gun |
| 81 | 1867 | Universal Suffrage | Steam Powered Ships; stock exchange | Bolt Action; rifles and modern cavalry |
| 82 | 1885 | Assembly Line | Radio; destroyer, cruiser, torpedo boat and troopship | Artillery Recoil Mechanism; bolt-action rifle |
| 83 | 1897 | Communism | Dreadnought | Early Tanks; French 75 artillery |
| 84 | 1915 | Fascism | Radar; dreadnought | Aerial Warfare; machine gun and early tanks |
| 85 | 1930 | Electrification | Mass Media | Gun Turret |
| 86 | 1936 | Parliamentary System; coal plant | Battleships | Rocket Artillery; WWII tanks and assault rifle |
| 87 | 1940 | Nuclear Power | International System of Units; battleship | Nuclear Bomb; rocket artillery and Italian tank |
| 88 | 1946 | Plastics; nuclear plant | Civil Aviation | Modern Assault Rifle |
| 89 | 1960 | Computers | Naval Missiles; mass transit | Main Battle Tanks; AK-47 and M16 |
| 90 | 1980 | Renewable Energy | Internet; missile ships | Missile Guidance; modern tanks |
| 91 | 1995 | Fusion Power | Nanotechnology | Advanced Main Battle Tanks; modern artillery |
| 92 | 2025 | General AI; fusion reactor | Naval Coilguns | Future Soldier; Armata and M1A3 |
| 93 | 2040 | Deep Space Mining | Orbital Trade Hubs | Powered Exoskeletons; Land Warrior |
| 94 | 2080 | Future Administration 1 | Space Colonization | Applied Lasers |
| 95 | 2120 | Future Administration 2 | Future Diplomacy 1 | Military Robots |

## Confirmed problems

1. Names and effects are frequently disconnected. Electricity unlocks the
   factory, Railroad does not unlock railroads until the following level, and
   Early Tanks unlocks artillery rather than tanks.
2. Several technologies are dated too early. Practical electrification is at
   1835, early tanks at 1897, nuclear power at 1940 and fusion power at 1995.
3. Unit unlocks lag behind their technology names. Dreadnoughts, battleships,
   assault rifles and several artillery types appear one level after the name
   that implies them.
4. Administrative levels rely heavily on repeated governing-capacity,
   production-efficiency and development-efficiency increases.
5. Diplomatic technology mixes naval engineering, communications, trade and
   transport without a consistent progression.
6. Technology gaps expand from 15 years to 30–40 years after 1995.
7. Levels after 2040 are mostly placeholders. Progression currently ends at
   level 100 in 2320, leaving the rest of an open-ended campaign static.

## Proposed synchronized timeline

| Level | Year | Administrative theme | Diplomatic theme | Military theme |
|---:|---:|---|---|---|
| 78 | 1835 | Industrial administration | Rail transport | Percussion warfare |
| 79 | 1850 | Professional civil service | Steam navigation | Rifled weapons |
| 80 | 1870 | Industrial standardization | Telegraph networks | Breech-loading artillery |
| 81 | 1890 | Mass politics | Wireless communication | Bolt-action and machine-gun warfare |
| 82 | 1910 | Mass production | Global shipping | Industrial warfare |
| 83 | 1930 | Managed economy | Radio and civil aviation | Mechanized warfare |
| 84 | 1945 | Post-war administration | Radar and modern fleets | Combined arms |
| 85 | 1960 | Computerized administration | Containerization and mass media | Jet and missile warfare |
| 86 | 1975 | Regulatory state | Satellite communications | Main battle tanks |
| 87 | 1990 | Digital administration | Global supply chains | Precision-guided weapons |
| 88 | 2005 | Electronic government | Internet economy | Network-centric warfare |
| 89 | 2020 | Data governance | Automated logistics | Drones and modern combined arms |
| 90 | 2035 | AI-assisted administration | AI logistics | Autonomous warfare |
| 91 | 2050 | Climate-resilient state | Orbital commerce | Directed-energy systems |
| 92 | 2065 | Fusion economy | Cislunar logistics | Powered combat systems |
| 93 | 2080 | Planetary administration | Space trade networks | Military robotics |
| 94 | 2090 | Post-scarcity governance | Interplanetary logistics | Autonomous armies |
| 95 | 2100 | Mature space-age state | Interplanetary diplomacy | Orbital defence |

## Implementation constraints

- Existing country history must continue resolving to sensible technology
  levels at every historical bookmark.
- Every existing unit and building unlock must be moved with its matching
  technology rather than deleted.
- Events, institutions, ages, decisions and scripted triggers referencing
  technology levels must be audited before levels are moved.
- Levels 96–100 and post-2100 repeatable progression should be handled only
  after this 1835–2100 sequence is stable.

## Recommended first implementation batch

Implement levels 78–84 (1835–1945) first. This is a bounded historical period,
contains the most obvious naming and unlock errors, and can be tested from the
1836 bookmark through the end of the Second World War before modern and future
technology is changed.

## Implementation status

Implemented in version `0.6.0-tech-1835-1945`:

- Levels 78–84 renamed and redated to the proposed 1835–1945 sequence.
- Later year fields synchronized through level 95 in 2100 so progression
  remains chronological.
- Railroad, ironclad, dreadnought and battleship unlocks moved to matching
  diplomatic technologies.
- Machine guns, interwar tanks and Second World War equipment moved to matching
  military technologies.
- Coal plants moved to Managed Economy in 1930.
- English names and descriptions replaced for all implemented levels.

Implemented in version `0.7.0-tech-2100`:

- Levels 85–95 renamed for a coherent 1960–2100 progression.
- Nuclear plants and mass transit moved to their appropriate modern levels.
- Missile ships, Cold War rifles, main battle tanks, modern artillery, future
  tanks, powered combat equipment and robotic units moved to matching levels.
- Information Age activation moved from ADM 89 (now 2020) to ADM 86 (1975),
  retaining its 1980 minimum start.
- English names and descriptions added for every level through 2100.

Implemented in version `0.8.0-future-tech`:

- Replaced ET's five post-2100 placeholders with levels 96–252.
- Future technology advances every 50 years from 2150 through 9950.
- Administrative levels add 25 governing capacity, with 1% production
  efficiency every fourth level.
- Diplomatic levels add 0.5% trade efficiency, with 10 trade range every
  fourth level.
- Military levels add 1% supply limit, with 0.025 tactics and 2% land morale
  every fourth level.
- Added all 942 localization entries required for 471 generated technology
  levels across the three branches.
