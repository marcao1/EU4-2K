# Step 3 Canonical Starting-World Data

## Scope

This stage establishes authoritative input data for the playable `2000.1.1` world. It does not yet write technology, finances, diplomacy, armies, or navies into EU4 history.

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

The values are planning inputs until the Step 3 integration generator defines exact EU4 unit conversions. Manpower is recorded as people; formation quantity is recorded as intended EU4 regiments or ships.

## Diplomacy

`diplomacy_2000.csv` contains:

- ET alliances, guarantees, subjects, unions, dependencies, and royal marriages effective on `2000.1.1`, limited to active starting tags
- Start and end dates
- Initial opinion baselines
- Source and verification notes
- Metadata-only NATO, EU, CIS, and UN membership records

Organization membership does not create ordinary EU4 alliances. This prevents NATO and EU membership from consuming diplomatic slots or automatically creating global wars before dedicated organization mechanics exist.

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

## Validation

The non-mutating check rejects:

- Missing or duplicate country setup records
- Unknown country tags
- Invalid technology, institution, financial, or tier fields
- Diplomacy with inactive or self-referencing endpoints
- Duplicate or inactive-at-start relationships
- Malformed organization membership
- Forces located outside their owner's territory
- Invalid formation quantities or quality tiers
- Active countries without an army record

## Next integration task

Extend `scripts/generate_starting_world.py` so these canonical inputs generate clean EU4 country setup, diplomacy, and unit history. File ownership between generators must remain explicit: the country and province generators continue to own their current outputs, while the starting-world generator owns only new integration outputs or clearly defined generated sections.
