# EU4 2K Institution Review

## Current structure

Extended Timeline defines 27 institutions:

- 14 early institutions from Writing through Medicine.
- 7 vanilla-era institutions from Feudalism through Enlightenment.
- 6 modern institutions: Imperialism, Industrialization, Nationalism,
  Electrification, Globalization and Internet.

The early institutions must remain internally because technologies, province
history, events and later institution prerequisites reference them. They should
not be removed merely because campaigns begin in 1836.

## Modern timeline audit

| Institution | Current earliest date | Current gate | Embracement bonus | Finding |
|---|---:|---|---|---|
| Imperialism | 1750 | European-connected capital; 50 cities | -20% core-creation cost | Should already exist in 1836; bonus is very strong |
| Industrialization | 1800 | Developed capital area; Manufactories and Enlightenment | +25% manpower, +15% tax | Appropriate at the start, but bonus is excessive |
| Nationalism | 1850 | Imperialism; culturally mixed country | +10% land morale, +5 years nationalism | Positive nationalism years are harmful and likely unintended |
| Electrification | 1900 | Industrialization; developed state/factory | -20% development cost | Correct era, but bonus is unusually strong |
| Globalization | 1950 | ADM 86 | +20% foreign trade power | ADM 86 is now dated 1975, so the displayed date is misleading |
| Internet | 2000 | ADM 90 | +10% tax | ADM 90 is now dated 2035, delaying the institution by 35 years |

## Technology penalty alignment

Modern technologies expect institutions gradually rather than applying the full
penalty immediately:

- Level 78 (1835): Imperialism 100%, Industrialization 50%.
- Level 79 (1850): Industrialization reaches 100%.
- Levels 80–83 (1870–1930): Nationalism rises from 15% to 100%.
- Levels 84–87 (1945–1990): Electrification rises from 15% to 100%.
- Levels 89–91 (2020–2050): Globalization rises from 25% to 100%.
- Levels 91–93 (2050–2080): Internet rises from 15% to 100%.

This staged structure is sound. The institution dates and gates should be
aligned to it instead of rewriting every technology penalty.

## Proposed modern timeline

| Institution | Proposed date | Proposed technology gate |
|---|---:|---:|
| Imperialism | 1750 | Existing historical gate |
| Industrialization | 1800 | Existing historical gate |
| Nationalism | 1850 | Existing historical gate |
| Electrification | 1900 | Existing historical gate |
| Globalization | 1975 | ADM 86 |
| Internet | 2005 | ADM 88 |

No additional institution should be added yet. The six existing modern
institutions already cover the redesigned technology sequence through 2080.
Post-2000 institutions should only be introduced after spread and AI behavior
are stable.

## Proposed bonus balance

- Imperialism: reduce core-creation cost from -20% to -10%.
- Industrialization: reduce manpower from +25% to +10% and tax from +15% to
  +10%; add +10% production efficiency to preserve its economic identity.
- Nationalism: keep +10% morale but change nationalism years from +5 to -5.
- Electrification: reduce development-cost reduction from -20% to -10% and add
  +10% production efficiency.
- Globalization: reduce foreign trade power from +20% to +10% and add one
  diplomatic relation.
- Internet: replace the generic +10% tax bonus with +10% trade efficiency and
  -5% technology cost.

## Proposed spread changes

1. Retain coastal and foreign-neighbour spread.
2. Increase same-country neighbour spread to prevent large countries taking
   centuries to reach remote provinces.
3. Give capitals, high-development provinces, centres of trade, factories and
   universities meaningful spread bonuses.
4. Preserve DLC-safe fallback conditions for Industrialization.
5. Avoid instant nationwide adoption; geography and infrastructure should still
   matter.

## Recommended implementation batch

Implement only the six modern institutions:

1. Correct Globalization and Internet dates and technology gates.
2. Apply the proposed embracement bonus reductions.
3. Improve internal spread moderately.
4. Validate that Imperialism and Industrialization exist in a new 1836 game.
5. Observer-test 1836–2100 before adding any future institution.

## Implementation status

Implemented in version `1.1.0-modern-institutions`:

- Globalization starts in 1975 at ADM 86.
- Internet starts in 2005 at ADM 88.
- Modern institution bonuses were reduced and specialized as proposed.
- Nationalism now reduces separatism duration instead of increasing it.
- Domestic post-embracement spread increased from 2.0 to 2.5 for Imperialism,
  Nationalism, Electrification, Globalization and Internet.
- Domestic Industrialization spread increased from 1.0 to 1.5 while its slower
  overseas spread remains unchanged.
- ET's gradual institution expectation values in technology were preserved.
