# Step 3 Canonical Starting-World Data

## Scope

This stage establishes authoritative input data for the playable `2000.1.1` world. Technology, the first-pass economy/reserve setup, and bilateral diplomacy are now written into EU4 history; international organizations and individual army/navy formations remain data-only.

The three canonical datasets are:

- `data/country_setup_2000.csv`
- `data/diplomacy_2000.csv`
- `data/forces_2000.csv`

They are bootstrapped and validated by `scripts/generate_starting_world.py`.

## Commands

Validate without modifying data:

```powershell
python scripts/generate_starting_world.py --check
```

Create missing canonical files:

```powershell
python scripts/generate_starting_world.py generate
```

Intentionally discard manual edits and rebuild all three CSVs from the current baseline rules:

```powershell
python scripts/generate_starting_world.py generate --rebuild-data
```

Ordinary generation and checks treat existing CSVs as authoritative. Use `--rebuild-data` only when changing bootstrap rules and review the resulting diff.

## Country setup

`country_setup_2000.csv` contains exactly one record for each of the 188 active countries. It records:

- ADM, DIP, and MIL technology baselines
- A documented 1-5 technology tier
- Embraced institution metadata
- Treasury, inflation, stability, prestige, and corruption
- Legitimacy or republican-tradition baseline
- Manpower and sailors
- Army, navy, economy, and infrastructure tiers
- Source and verification status

The first pass is deterministic and uses country technology region, explicit major-power overrides, owned development, manpower development, and coastal access. Technology capacity is deliberately separate from political stability: for example, Yugoslavia and Iraq may start unstable without being assigned medieval technology.

The financial and reserve values are integrated into the generated country
snapshots. Starting treasury is inverse to total owned development: countries
with at least 500 development receive 50 ducats, countries with 150-499 receive
200, and countries below 150 receive 600. Treasury uses bounded subtraction
loops before adding the canonical reserve; this avoids the extreme negative
balances caused by a large negative additive reset. Manpower is converted from recorded
people to EU4's thousands, and sailors use EU4's individual-sailor scale.
Stability, prestige, inflation, corruption, and legitimacy or republican
tradition are reset before the canonical value is applied. Formation quantity
remains the intended number of EU4 regiments or ships.

Economic and infrastructure tiers are also stored as stable country flags
(`eu4_2k_economic_tier_1` through `_5` and
`eu4_2k_infrastructure_tier_1` through `_5`) for later buildings, events, and
missions. They currently have no passive modifier by themselves.

## Diplomacy

`diplomacy_2000.csv` contains:

- A deliberately small set of historically grounded bilateral alliances and guarantees effective on `2000.1.1`
- Historical treaty dates for documentation; generated gameplay relationships are anchored to the scenario start date
- Initial opinion baselines
- Source and verification notes
- Metadata-only NATO, EU, CIS, and UN membership records

Organization membership does not create ordinary EU4 alliances. This prevents NATO and EU membership from consuming diplomatic slots or automatically creating global wars before dedicated organization mechanics exist.

Eleven curated bilateral relationships are integrated into
`history/diplomacy/00_eu4_2k_diplomacy.txt`: ten alliances and one guarantee.
The generator also applies the recorded initial opinion in both
directions through scenario-start opinion modifiers. The mod replaces vanilla
diplomatic history so medieval and early-modern relationships cannot leak into
the 2000 bookmark.

All 229 NATO, EU, CIS, and UN membership rows remain canonical metadata only.
They generate no alliances, guarantees, country flags, opinion modifiers, or
other gameplay effects and are reserved for a separate organization system.

The first membership baseline contains:

- 19 NATO members
- 15 European Union members
- 12 CIS members
- 183 United Nations members

Switzerland, Taiwan, Yugoslavia, Tuvalu, and Palestine are excluded from the UN-member list at the exact starting date according to the scenario's first-pass status model. These records require a manual source audit before public release.

## Forces

`forces_2000.csv` contains a mechanically bounded first-pass force model:

- One army record for every active country
- One navy record for every country with an owned province adjacent to an ET sea zone
- Valid owned starting locations
- Formation name, branch, unit category, quantity, and quality tier

Coastal provinces are detected deterministically from `provinces.bmp` and `sea_starts`. Formation quantities are scaled from development, coastal extent, and technology tier. They are not claims of exact historical order of battle.

The initial dataset contains 188 army formations and 148 fleet formations.

The formation rows are canonical order-of-battle metadata and are not yet
written as individual regiments or ships. EU4 currently creates its normal
starting forces from force limit. All modern technology groups therefore use a
level-5 through level-9 variants so the engine has valid infantry types and
applies each country's CSV technology directly during initialization.

Starting technology is integrated into the generated country histories. The
current first-pass scale is level 5 for tier 1 through level 9 for tier 5. Each
of the nine regional families has internal tier variants with identical
research costs; the starting differences represent the scenario snapshot
rather than permanent regional penalties.

The vanilla institution sequence has been replaced by eight future-facing
institutions beginning with Globalized Economy on `2000.4.1`. No institution is
embraced at the bookmark. See `docs/modern_institutions.md` for the complete
fifty-year schedule, bonuses, and internal compatibility mapping.

## Validation

The non-mutating check rejects:

- Missing or duplicate country setup records
- Unknown country tags
- Invalid technology, institution, financial, or tier fields
- Starting treasury that does not match the 50/200/600 size rule
- Diplomacy with inactive or self-referencing endpoints
- Duplicate or inactive-at-start relationships
- Malformed organization membership
- Organization records appearing in generated bilateral diplomacy
- Missing or stale bilateral diplomacy and starting-opinion output
- Forces located outside their owner's territory
- Invalid formation quantities or quality tiers
- Active countries without an army record

## Economy and development baseline

The 3,521 land provinces initialize `base_tax`, `base_production`, and
`base_manpower` from the ET-derived `2000.1.1` snapshot after a deterministic
EU4-focused balance curve. Values up to 30 are preserved, extreme metropolitan
values are compressed to a maximum of 50, and the most underrepresented Balkan
capitals receive explicit floors. A national-target pass controls major-power
totals without imposing identical averages on maps with different province
density. National treasury and reserve values are recalculated from the
balanced province data.

A later historical audit can refine the balance with modern population, GDP,
and urban-economic evidence, beginning with Europe, the United States, China,
and Russia.

## Next integration task

Integrate `data/forces_2000.csv` as clean starting army and navy history while
preventing duplicate engine-generated forces. International organizations stay
outside that pass and will be implemented as a separate system.
