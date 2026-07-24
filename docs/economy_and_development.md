# Economy and Development Baseline

## Implemented starting values

Every one of the 188 active countries now receives its canonical `2000.1.1`
starting values from `data/country_setup_2000.csv`:

- treasury and inflation
- stability, prestige, and corruption
- legitimacy, republican tradition, or devotion as appropriate
- manpower and sailors
- economic and infrastructure tier flags

The generator resets EU4's automatically derived starting values before adding
the scenario value. This makes the CSV the source of truth instead of treating
it as a bonus on top of the vanilla starting calculation.

Manpower is stored in the CSV as people and divided by 1,000 when written to
EU4 history. Sailors are written as individual sailors. Economic and
infrastructure tiers are metadata flags reserved for later building, mission,
and event mechanics; they deliberately grant no hidden research modifier.

## Province development

Province history starts from ET's effective values on `2000.1.1`, then applies
an EU4-focused balance curve. Development up to 30 is retained. Above 30,
diminishing returns compress extreme metropolitan values, with a hard cap of
60. The current snapshot totals:

- 16,620 base tax
- 16,606 base production
- 13,775 base manpower
- 47,001 total development

Singapore is the sole 60-development province. New York, Los Angeles, and Tokyo
start at 58; Berlin at 47; London and Paris at 46. Balkan capital floors repair
the sharpest ET underrepresentation: Athens and Bucharest start at 38, Belgrade
and Sofia at 32, Zagreb at 30, Sarajevo at 28, and Tirana and Skopje at 25.

The proportional tax/production/manpower mix of each source province is
preserved. These values remain a gameplay baseline rather than a precise GDP or
population model.

## Trade routes

EU4 2K does not override `common/tradenodes`. The base game therefore supplies
the complete vanilla network of 80 trade nodes, 159 connections, and its
original route geometry. This choice does not affect the mod's borders,
ownership, province history, or balanced development.

## Generation and validation

```powershell
python scripts/generate_starting_world.py --check
python scripts/generate_starting_world.py generate --rebalance-economy
python scripts/generate_country_snapshot.py generate
python scripts/generate_country_snapshot.py --check
python scripts/generate_province_snapshot.py generate --rebalance-development
python scripts/generate_province_snapshot.py --check
```

Country generation rejects missing setup records, invalid ranges, unequal
starting technology levels, and invalid economy/infrastructure tiers. Generated
country history remains undated; future changes belong in events.
