# EU4 2K Age Audit (1836–9999)

## Scope

This audit reviews the active late-game ages against EU4 2K's revised technology dates, institutions, buildings, and open-ended end date. It does not change gameplay files.

## Current age sequence

| Age | Scripted start | Additional gate | Effective start in EU4 2K | End |
|---|---:|---|---:|---:|
| Industrial Age | 1800 | Industrialization enabled | 1800 | Great War Age begins |
| Great War Age | 1890 | Any country reaches MIL 82 | about 1910 | Information Age begins |
| Information Age | 1980 | Any country reaches ADM 86 | 1980 | 9999 |

The 1836 bookmark therefore begins in the Industrial Age. The Great War label is misleading because its date says 1890 while the revised MIL 82 gate normally delays it until 1910. The Information Age is aligned with ADM 86 (1975) and starts in 1980 as intended.

## Confirmed dependencies

- Industrialization, Globalization, and Internet institution references exist.
- Nuclear weapons, nuclear decisions, and the `nuclear_weapons_allowed` flag exist.
- The first Moon landing flag is set by ET's space events.
- Oil trading bonuses, political factions, fusion reactors, and natural-scientist advisers exist.
- The European Union modifier used by one Information Age country ability exists, but it couples the age to ET's organization mechanics.

## Defect

The Great War objective `obj_greatwar_win_battles` checks the variable `num_of_battles_won`. EU4's battle on-action increments `num_of_battles_won_var`. As written, the objective cannot normally complete.

Required correction:

```txt
check_variable = {
    which = num_of_battles_won_var
    value = 25
}
```

## Objective review

### Industrial Age

- Twenty factories and ten manufactories strongly favor large countries.
- African colonies and ownership on four continents remain ET/colonial-era objectives and are poorly suited to a modern-focused campaign.
- Ten provinces at 50 development is an extreme requirement for most countries.
- Japan and technology-superiority objectives are functional but geographically or structurally restrictive.

Recommended replacement targets:

- 10 factories instead of 20.
- 5 manufactories instead of 10.
- 5 provinces at 40 development instead of 10 at 50.
- Replace the African-colony objective with a general industrial-economy objective.
- Replace the four-continent objective with a trade or infrastructure objective that does not require conquest.

### Great War Age

- Great-power, oil, ideology, nuclear, and battle objectives fit the period.
- The Moon landing is a valid late-age stretch objective because this age runs until 1980.
- The battle objective is broken by the variable mismatch described above.
- “More nuclear weapons than every rival” may complete trivially when a country has no rivals; its trigger should require at least one rival.

### Information Age

- Requiring Internet in every owned province heavily penalizes large and colonial countries.
- Twenty fusion reactors cannot be pursued until ADM 92 (2065), decades after this age begins, and is excessive even then.
- Six allies exceeds practical diplomatic capacity for many countries.
- Requiring the nationalist-party faction excludes countries whose government does not expose that faction.
- Every province at 12 development is achievable but scales badly with territorial expansion.
- A level-3 natural scientist is suitable and functional.

Recommended replacement targets:

- 5 fusion reactors instead of 20.
- 4 allies instead of 6.
- Broaden the political objective to support several modern government/faction paths.
- Require widespread Internet adoption rather than every province, if EU4 scripting can express the threshold reliably.
- Replace the all-provinces development test with a fixed number of developed provinces or an average-development approximation.

## Ability balance

Several abilities exceed normal age-ability power:

- Industrial country discipline: 7.5% should be 5%.
- Industrial build and development discounts: 15% should be 10%.
- Great War USA goods produced: 25% should be 15%.
- Information Age regional goods produced: 25% should be 15%.
- Information Age India development discount: 20% should be 10%.
- Information Age EU diplomatic reputation: +2 should be +1, or be deferred until organization mechanics are reviewed.

The generic abilities are otherwise coherent, although permanent -10% technology cost and -2 interest become unusually strong because the Information Age currently lasts almost 8,000 years.

## Recommended timeline

Use four late-game ages:

| Age | Start | Gate | Purpose |
|---|---:|---|---|
| Industrial Age | 1800 | Industrialization | Industrialization and infrastructure |
| Great War Age | 1910 | MIL 82 | Mass warfare, ideology, oil, nuclear development |
| Information Age | 1980 | ADM 86 | Internet, globalization, advanced economy |
| Future Age | 2100 | ADM 95 | Permanent final age for the open-ended campaign |

The Future Age should be the final permanent age through 9999. Repeating ages would repeatedly reset splendor and abilities and would add unnecessary instability. The final age can use broad, repeatable objectives that remain meaningful at any future date.

## Recommended implementation batch

1. Correct the battle variable and set the Great War scripted start to 1910.
2. Rebalance the existing objectives and abilities listed above.
3. Add a permanent Future Age beginning in 2100, gated by ADM 95.
4. Give the Future Age generic long-term objectives based on technology, development, infrastructure, trade, and military capacity.
5. Reuse Information Age artwork initially; custom art can be added after functional testing.
6. Test bookmarks in 1836, 1910, 1980, and 2100, then run an observer campaign across each transition.

Organization-specific abilities should remain unchanged until organizations are reviewed separately, except where they prevent an age from functioning.
