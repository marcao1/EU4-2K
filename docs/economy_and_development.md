# Economy and Development Baseline

## Implemented starting values

Every one of the 188 active countries now receives its canonical `2000.1.1`
starting values from `data/country_setup_2000.csv`:

- treasury and inflation
- stability, prestige, and corruption
- legitimacy, republican tradition, or devotion as appropriate
- manpower and sailors
- economic and infrastructure tier flags

Treasury follows a size-balancing rule based on total owned development:

- large countries (500 or more development): 50 ducats
- medium countries (150-499 development): 200 ducats
- small countries (below 150 development): 600 ducats

The generator applies treasury with `set_treasury`, making the CSV value exact.
Other bounded starting values are reset before adding the scenario value. This
makes the CSV the source of truth instead of treating it as a bonus on top of
the vanilla starting calculation.

Manpower is stored in the CSV as people and divided by 1,000 when written to
EU4 history. Sailors are written as individual sailors. Economic and
infrastructure tiers are metadata flags reserved for later building, mission,
and event mechanics; they deliberately grant no hidden research modifier.

## Province development

Province history starts from ET's effective values on `2000.1.1`, then applies
an EU4-focused balance curve. Development up to 30 is retained. Above 30,
diminishing returns compress extreme metropolitan values. A second national
pass rescales major-country totals while preserving province ordering and each
province's tax/production/manpower proportions. Owned provinces have a minimum
of 3 development and all provinces have a hard cap of 50. The current snapshot
totals:

- 13,953 base tax
- 13,612 base production
- 11,202 base manpower
- 38,767 total development, including 38,650 in owned provinces

The explicit major-country targets are 3,500 for the United States, 2,850 for
China, 2,550 for India, 1,500 for Russia, 1,400 for Germany, 1,150 for France,
1,125 for Japan, 1,100 for the United Kingdom, 950 for Italy, 920 for Indonesia,
915 for Brazil, and 845 for Mexico. Other countries retain their balanced ET
total within a 15-1,500 national band. This avoids forcing countries with very
different province counts toward the same average.

London starts at 45, Paris at 42, Tokyo at 38, and New York and Los Angeles at
28. Balkan capital floors repair the sharpest ET underrepresentation: Athens
and Bucharest start at 38, Belgrade and Sofia at 32, Zagreb at 30, Sarajevo at
28, and Tirana and Skopje at 25.

The proportional tax/production/manpower mix of each source province is
preserved. These values remain a gameplay baseline rather than a precise GDP or
population model.

## Trade routes

EU4 2K retains the complete vanilla network of 80 trade nodes and 159
connections. For the 141 connections also present in Extended Timeline, it uses
ET's path and control coordinates so the route arrows align with the imported
map instead of stretching and repeating across Italy, the Balkans, and nearby
seas. The remaining 18 connections retain their vanilla geometry.

The route shader itself is vanilla. This does not alter borders, ownership,
province history, or balanced development.

## Starting infrastructure

Every owned province receives a deterministic first-pass building set based on
its owner's canonical infrastructure tier, whether it is the national capital,
center-of-trade status, and its balanced tax, production, and manpower values.
The generator also limits assignments with a conservative building-slot budget.

The current global distribution is:

- 952 marketplaces
- 732 workshops
- 462 courthouses
- 197 temples
- 175 docks
- 59 barracks
- 38 shipyards
- 2,615 buildings across 1,010 provinces

Capitals receive administrative and economic priority. Centers of trade receive
marketplaces, productive provinces receive workshops, high-tax provinces
receive temples, and manpower centers receive barracks. Gold provinces do not
receive workshops because the vanilla building forbids them.

Naval buildings are restricted to provinces confirmed as coastal directly from
the province bitmap. Docks begin at infrastructure tier two in important ports;
shipyards begin at tier three and prioritize capitals, level-two or level-three
trade centers, and the strongest developed ports. No inland province receives a
naval building.

Forts remain deferred to a military infrastructure audit so starting
maintenance remains controllable.

## Modern centers of trade

The ET center-of-trade baseline is retained outside an explicit modern-hub
audit. Twelve global hubs start at level three: Amsterdam, Paris, London, Dubai,
Guangzhou, New York, Tokyo, Beijing, Shanghai, Frankfurt, Hong Kong, and
Singapore. Berlin, Brussels, Rome, Istanbul, Madrid, Moscow, Seoul, Los Angeles,
Washington, Sydney, Toronto, San Francisco, and Chicago are among the audited
level-two hubs.

Genoa, Venice, Chittagong, and Khambhat are reduced from ET level three to level
two. The final distribution is 12 level-three, 128 level-two, and 214 level-one
centers.

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
