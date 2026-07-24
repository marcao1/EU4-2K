# EU4 2K Province Snapshot

## Implemented baseline

The clean world snapshot is effective on `2000.1.1` and contains all 3,521 land provinces defined by the Extended Timeline map:

- 3,482 owned provinces.
- 39 unowned or uncolonized provinces.
- 188 distinct active owners, matching the country foundation exactly.
- Owner, controller, and one starting owner core for every owned province.
- Effective culture, vanilla religion, settlement name, trade good, development, city status, HRE status, centers of trade, and native population values.
- English province names and adjectives for every land province.
- Discovery-only history for every sea, ocean, and lake zone, exposing all water through normal fog of war rather than terra incognita.
- No dated province-history blocks and no pre-2000 ownership timeline.

The five dormant successor tags own no territory at the starting date.

## Canonical data and generation

`data/provinces_2000.csv` is the source of truth after its initial bootstrap. Generate or validate from the repository root:

```powershell
python scripts/generate_province_snapshot.py generate
python scripts/generate_province_snapshot.py --check
```

To intentionally rebuild the CSV from Extended Timeline's effective history on `2000.1.1`:

```powershell
python scripts/generate_province_snapshot.py generate --rebuild-data
```

The rebuild reads every ET province history chronologically, applies only entries effective by the starting date, and writes one clean undated row per land province. Subsequent ordinary generation treats the CSV as authoritative.

## Normalization policy

- Controllers are reset to the sovereign owner so the scenario does not inherit wars or occupations.
- Each owned province begins with its owner as a core. Historical claims and disputed cores will be added during diplomacy and regional-content work.
- `secularism` and `irreligious` are replaced with the last applicable conventional vanilla religion in that province's ET history.
- ET-only modern trade goods are temporary mapped to vanilla goods because the modern economy has not been imported:
  - oil to coal
  - cars to iron
  - electronics to glass
  - aluminum and uranium to copper
- Undefined ET goods fall back to grain. The original source file is recorded in the CSV for later economic reconstruction.
- Every land and water province is discovered by the major vanilla and all nine modern technology groups at the modern start. This removes terra incognita while retaining normal country-specific fog of war.

## Capital corrections

The province audit found four obsolete capital IDs in ET country history. The canonical country dataset now uses provinces actually owned by the country in 2000:

- Benin: Porto-Novo (`1141`).
- Burkina Faso: Ouagadougou (`1137`).
- The Gambia: Banjul (`3006`).
- Zambia: Lusaka (`4106`).

## Validation results

The generator verifies:

- Exact coverage of all ET land IDs and exclusion of seas and lakes.
- Unique IDs between 1 and 4941.
- Only active starting tags own territory.
- Every active country owns at least one province.
- Every active country's capital is owned by that country.
- Owner, controller, and generated core agree.
- Every owned province has a culture and vanilla religion.
- Trade goods are defined by vanilla EU4.
- Development values are non-negative.
- Generated history contains no dated blocks.
- Generated files are byte-identical to the canonical CSV inputs.

An EU4 `1.37.5` smoke test remained responsive through full initialization and reached the menu. It produced no new crash dump, `setup_error.log` remained empty, and the fresh logs contained zero province-history, invalid-owner, unknown-trade-good, country-history, or country-database errors.

## Deferred work

This is a mechanically clean ownership baseline, not the final geopolitical audit. Later passes should add disputed cores and claims, dependent territories, autonomy, infrastructure, final modern trade goods, balanced development, centers of trade, and province-level manual accuracy reviews—starting with Europe, the United States, China, and Russia.
