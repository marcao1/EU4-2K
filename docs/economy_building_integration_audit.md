# EU4 2K Economy and Building Integration Audit

## Scope

This audit covers the modern production, energy, transportation and fortification chains, their technology unlock dates, their AI weights, and their interaction with the late-age economy. No balance values were changed during the audit.

## Technology and building timeline

| Year | Tech | Unlock |
|---:|---:|---|
| 1820 | DIP 76 | Highway |
| 1835 | ADM 77 | Factory |
| 1835 | DIP 77 | Railroad |
| 1910 | MIL 81 | Modern Fortification (level 9) |
| 1930 | ADM 82 | Coal Plant |
| 1960 | ADM 84 | Nuclear Plant |
| 1960 | DIP 84 | Mass Transit System |
| 1960 | MIL 84 | Hardened Bunker (level 10) |
| 2005 | MIL 87 | Integrated Defence Network (level 11) |
| 2065 | ADM 91 | Fusion Reactor |
| 2100 | MIL 94 | Orbital Defence Complex (level 12) |
| 2150 | DIP 96 | Quantum Logistics Network |

Countries starting in 1836 at modern technology have factories and railroads available immediately. Road and highway remain prerequisite history but are already obsolete at this bookmark.

## Production chain

The production chain is coherent:

- Workshop: 150 ducats, +75% local production efficiency.
- Counting House: 400 ducats, +100% local production efficiency.
- Factory: 700 ducats, +110% local production efficiency, -5% local development cost and a possible production-development reward.

Factory replaces Counting House, so its apparent +110% is only a ten-point improvement over the previous tier. It is not an unintended additional +110% stack.

Manufactories remain a separate chain and can coexist with factories. This is correct because one improves production efficiency while the other increases goods produced.

## Energy chain

| Building | Cost | Effects | Replaces |
|---|---:|---|---|
| Coal Plant | 1,000 | +15% production, +10% tax, +0.15 goods, -5% development cost | Nothing |
| Nuclear Plant | 1,800 | +25% production, +15% tax, +0.25 goods, -10% development cost | Coal Plant |
| Fusion Reactor | 2,600 | +35% production, +20% tax, +0.40 goods, -15% development cost | Nuclear Plant |

Findings:

- The chain is non-stacking after Coal Plant and progresses consistently.
- Coal Plant intentionally coexists with Factory; energy is not part of the production-building chain.
- The 1930–1960 Coal Plant window is only 30 years. Broad coal construction immediately before Nuclear Plant becomes available may waste AI funds.
- AI weights rise from 1 to 1.25 to 1.5 but have no explicit treasury or income guard.
- Costs are high but reasonable for strategic late-game buildings if national income scales adequately.
- Development rewards are conditional on ET's `improve_development_on_buildings_built` country flag and correctly distinguish new construction from upgrades.

## Transportation chain

| Building | Cost | Movement | Institution spread | Other |
|---|---:|---:|---:|---|
| Road | 80 | +15% | +10% | +1 building slot |
| Highway | 150 | +30% | +20% | +1 building slot |
| Railroad | 300 | +25% | +15% | +10% trade power, +1 building slot, possible +1 production development |
| Mass Transit | 600 | +30% | +20% | +20% tax, +10% trade power, +1 building slot |
| Quantum Logistics | 1,200 | +40% | +25% | +25% tax, +20% trade power, +1 building slot |

Confirmed defect: Railroad replaces Highway but reduces movement speed from 30% to 25% and institution spread from 20% to 15%.

The later tiers technically recover these values, but Mass Transit only returns to Highway strength in both categories. This makes the progression feel flat across 140 years.

Recommended monotonic values:

| Building | Movement | Institution spread |
|---|---:|---:|
| Road | 15% | 10% |
| Highway | 25% | 15% |
| Railroad | 35% | 20% |
| Mass Transit | 45% | 25% |
| Quantum Logistics | 55% | 30% |

The +1 building-slot modifier should remain on every tier. Since each replacement removes the previous tier, it provides one net infrastructure-supported slot rather than stacking unlimited slots.

AI behavior is inconsistent:

- Road and Highway use artificial weights above 100 and affordability checks.
- Railroad uses weight 40 and an affordability check.
- Mass Transit and Quantum Logistics use ordinary weights of 1 and 1.25 without affordability checks.

Recommended AI policy: use ordinary weights for all currently relevant tiers, with a treasury reserve and positive-income guard for Railroad and later upgrades. Historical Road and Highway logic can remain because they are obsolete in 1836.

## Fortification chain

| Year | Tier | Cost | Fort level |
|---:|---|---:|---:|
| 1910 | Modern Fortification | 1,000 | 9 |
| 1960 | Hardened Bunker | 1,500 | 10 |
| 2005 | Integrated Defence Network | 2,200 | 11 |
| 2100 | Orbital Defence Complex | 3,200 | 12 |

The cost and power progression is consistent. These buildings have ordinary AI weight 1 and no explicit affordability guard. Because forts also generate continuing maintenance, observer testing must verify that medium powers do not cover every province with unaffordable modern forts.

## Era-wide economic modifiers

ET applies large age-specific modifiers rather than relying only on buildings. By the Information and Future Ages these include:

- +30% technology cost.
- -30% development cost.
- +30% land maintenance.
- +75% regiment cost.
- -45% land force limit.
- +50% aggressive expansion.
- -45% land morale.

The Future Age now preserves the Information Age baseline, preventing an abrupt reset in 2100. These values are deliberate ET scaling, but they mean raw building costs cannot be evaluated independently from army size, state income and technology cost.

## Priority implementation batch

1. Make transportation movement and institution spread strictly increase by tier.
2. Normalize AI affordability logic for Railroad, Mass Transit and Quantum Logistics.
3. Add treasury safeguards to Coal, Nuclear and Fusion AI construction.
4. Leave current production and energy effects unchanged until observer data shows excessive growth or insolvency.
5. Run observer samples from 1836 for 10, 50 and 100 years and record:
   - treasury, loans and monthly balance of the top 20 powers;
   - number of factories, energy plants, transport buildings and modern forts;
   - total development and force limits;
   - whether AI countries replace obsolete infrastructure.

## Decision

The economy does not require a broad rewrite. The first implementation should be a narrow transportation-progression and AI-affordability correction, followed by observer testing. Energy yields and costs should only be changed using those results.

## Implemented in 1.2.1

- Transportation now progresses monotonically from Road through Quantum Logistics.
- Railroad, Mass Transit and Quantum Logistics use normalized AI weights.
- Modern transportation requires a 20% treasury reserve and at least 1 ducat of monthly income before the AI considers construction.
- Coal, Nuclear and Fusion plants use the same affordability policy.
- Production and energy yields remain unchanged pending observer results.
