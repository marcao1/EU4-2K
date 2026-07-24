# EU4 2K Year-2000 Country Foundation

## Status

The generated country foundation targets EU4 `1.37.5` and contains:

- 188 active countries derived from Extended Timeline ownership on `2000.1.1`.
- Five dormant successor tags: East Timor (`ETI`), Kosovo (`KOS`), Montenegro (`MON`), Serbia (`SER`), and South Sudan (`SSU`).
- 193 generated country definitions, flags, history snapshots, names, and adjectives.
- 898 inert history stubs for registered vanilla compatibility tags, for a total of 1,091 history files.
- One bookmark at `2000.1.1` and an engine end date of `9999.12.31`.
- Nine equal-cost regional technology groups.
- Seventeen neutral modern government reforms across executive, state-structure, and political-competition dimensions.
- A minimal generated subset of the 45 Extended Timeline culture identifiers required by the snapshot.
- Vanilla religions only.

Province ownership is now supplied by the clean generated `2000.1.1` province snapshot. Diplomacy, armed forces, starting technology levels, detailed claims, and manual province balancing remain deferred.

## Source of truth

`data/countries_2000.csv` is the canonical editable dataset. It records tag identity, names, capital, cultures, religion, political framework, executive and head of state, ratings, regional technology group, graphics, colors, asset sources, and verification status.

The initial CSV was bootstrapped from the effective Extended Timeline state on `2000.1.1`. Priority records for Europe, the United States, China, and Russia received a manual first-pass executive audit. Records marked as first-pass ET baselines still require manual historical sourcing before a public accuracy milestone.

The five successor tags are definitions, not active states. They have no ruler or territory in the starting snapshot. Later formation events must assign their contemporary leadership and territory.

## Generator

From the repository root:

```powershell
python scripts/generate_country_snapshot.py generate
python scripts/generate_country_snapshot.py --check
```

`generate` treats the existing CSV as authoritative and updates the controlled mod outputs. It also deletes stale generated country, history, and flag files. `--check` is non-mutating and fails if an output is missing, stale, invalid, or non-deterministic with respect to the current inputs.

Only use the bootstrap option when intentionally replacing the canonical dataset from the ET baseline:

```powershell
python scripts/generate_country_snapshot.py generate --rebuild-data
```

That command rewrites `data/countries_2000.csv`; review the diff carefully afterward.

## Ruler-rating rubric

ADM, DIP, and MIL use the same conservative 1-6 scale:

- `1`: clearly ineffective in the relevant field.
- `2`: weak performance or very limited demonstrated capacity.
- `3`: ordinary or mixed performance.
- `4`: capable, with meaningful successes.
- `5`: exceptional and unusually effective.
- `6`: era-defining performance with sustained, extraordinary results.

ADM covers domestic administration, reform, and economic management. DIP covers coalition-building, negotiation, and foreign policy. MIL covers defense, security policy, command judgment, and crisis management. Ratings describe demonstrated governing performance by the start date, not morality or later reputation.

Real birth dates remain in the CSV and as generated history comments. EU4 assigns undated history entries to its internal earliest date; placing a twentieth-century `birth_date` inside an undated ruler produces a false "history entry before birth" error. The ruler is therefore created without a mechanical birth date so the generated history can remain undated as required. Later event-driven leaders should use dated events and may set their full historical data there.

## Generated layout

The generator owns these outputs under `MillenniumDawnEU4/`:

- `common/countries/`
- `common/country_tags/00_countries.txt`
- `common/cultures/00_eu4_2k_cultures.txt`
- `common/government_reforms/00_eu4_2k_government_reforms.txt`
- `common/technology.txt`
- `common/defines/zz_eu4_2k_dates.lua`
- `common/bookmarks/00_eu4_2k_2000.txt`
- `history/countries/`
- `history/provinces/` through the province snapshot generator
- `gfx/flags/`
- `localisation/eu4_2k_*_l_english.yml` for new framework keys
- `localisation/replace/eu4_2k_*_l_english.yml` for country and province overrides

Country definitions retain only color, graphical culture, and the name pools EU4 requires. They do not import obsolete ideas, historical units, governments, or score data. Country histories contain one undated snapshot and no diplomacy, wars, armies, treasury, province ownership, or scheduled successors.

## Validation

The static check verifies the active/dormant counts, unique tags, land capitals in the ET province range, vanilla religions, defined cultures and government values, valid pre-start executive dates in the canonical data, equal technology-group costs, valid required assets, undated generated history, and byte-exact generated output.

A repeated generation/hash comparison was also run successfully.

The EU4 `1.37.5` smoke test through the existing mod junction reached a responsive main window. At the end of the test:

- `setup_error.log` was empty.
- No tag was missing a country history file.
- No generated country reported an undefined culture, invalid ruler history, missing name pool, unknown reform, or unknown technology group.
- The launcher configuration was restored to its original Extended Timeline selection after testing.

Two classes of log noise remain outside this phase's acceptance criteria:

1. EU4 emits checksum-only `version.cpp` and `virtualfilesystem_physfs.cpp` messages for files below replaced subdirectories. The same files are subsequently loaded and validated by the relevant content databases.
2. A small amount of underlying ET map localization/bitmap warning noise remains. Vanilla province history is explicitly blocked because applying it to ET province IDs caused an access-violation crash during scenario initialization.

The crash fix and generated ownership were verified together: EU4 remained responsive through full initialization, produced no new crash dump, logged no invalid province-owner assignments or province-history errors, and left `setup_error.log` empty.

## Next phase

Build starting diplomacy, technology, institutions, armies, navies, autonomy, disputed claims, and the first regional manual accuracy audit on top of the synchronized country and province snapshots.
