# EU4 2K Building Review

## 1836 history audit

ET province history explicitly provides very little economic infrastructure at
the 1836 start. The detected active buildings are:

| Building | Provinces |
|---|---:|
| Fort 15th | 232 |
| Fort 16th | 39 |
| Fort 17th | 25 |
| Fort 18th | 41 |
| Shipyard | 1 |

Factories, railroads and later infrastructure are not assigned through province
history. Countries must construct them after the campaign begins.

## Corrected modern unlocks

| Building | Branch | Level | Year |
|---|---|---:|---:|
| Highway | Diplomatic | 77 | 1820 |
| Factory | Administrative | 78 | 1835 |
| Railroad | Diplomatic | 78 | 1835 |
| Modern Fortification | Military | 82 | 1910 |
| Coal Plant | Administrative | 83 | 1930 |
| Nuclear Plant | Administrative | 85 | 1960 |
| Hardened Bunker Complex | Military | 85 | 1960 |
| Mass Transit System | Diplomatic | 85 | 1960 |
| Integrated Defence Network | Military | 88 | 2005 |
| Fusion Reactor | Administrative | 92 | 2065 |
| Orbital Defence Complex | Military | 95 | 2100 |

## Fortification chain

The old chain ended with Fort 18th at Military level 70 (1715). It now continues
through four tiers:

1. Modern Fortification: fort level 9, 1,000 ducats.
2. Hardened Bunker Complex: fort level 10, 1,500 ducats.
3. Integrated Defence Network: fort level 11, 2,200 ducats.
4. Orbital Defence Complex: fort level 12, 3,200 ducats.

Each tier makes the preceding tier obsolete.

The macro builder and province building interface reuse the five available fort
slots for Fort 18th followed by the four modern tiers. Earlier fort tiers remain
valid in history but are intentionally omitted from construction menus because
the campaign cannot start before 1836.

Modern Fortification, Hardened Bunker and Integrated Defence Network reuse the
base game's graphical-culture-specific fort tiers 5, 6 and 7. Orbital Defence
Complex reuses ET's fusion-reactor artwork as a temporary futuristic icon.

## Industrial and energy balance

The factory and energy chain previously granted excessive development and local
economic multipliers. Costs, construction time and bonuses now rise more
gradually. Factory development gain was reduced from 4 to 3; coal from 2 to 1;
nuclear from 4 to 2; and fusion from 6 to 3. Coal, nuclear and fusion remain a
separate energy chain, while factories remain the main production upgrade.

## Transportation and future infrastructure

Transportation now follows one non-stacking upgrade chain:

1. Highway (1820; retained internally as the predecessor).
2. Railroad (1835; 300 ducats).
3. Mass Transit System (1960; 600 ducats).
4. Quantum Logistics Network (2150; 1,200 ducats).

Each tier makes the preceding tier obsolete and grants one building slot, so
transport infrastructure consumes a single net slot and cannot accumulate all
movement and economic bonuses. The 1836 construction interfaces display
Railroad and the two later relevant upgrades.

The future transport unlock is generated at Diplomatic level 96, ensuring
regeneration does not remove it.

AI factors and reserve thresholds were reduced for railroads and kept moderate
for later infrastructure. Fort construction remains primarily controlled by
EU4's hard-coded strategic fort AI, with high costs limiting excessive density.
