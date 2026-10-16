# Elections and Political Blocs

## Why

EU4's built-in republic elections fired every four years in every republic,
including authoritarian ones, and replaced leaders with random names. In the
2000–2011 test this produced 230 ruler changes in democracies and 55 in other
countries. Putin, Bush, Merkel, and even Hu Jintao were replaced on four-year
marks.

This layer models political *direction* rather than individual parties:
democracies hold scripted elections on their own cycle, and the winning bloc
sets a small, readable policy direction. Authoritarian systems hold no
elections.

## Blocs

| Bloc | Direction | Modifiers |
|---|---|---|
| Left | Welfare state, sceptical of military spending | unrest −1, development cost −5%, land maintenance +10% |
| Centre-Left | Social democracy, international cooperation | stability cost −5%, improve relations +10% |
| Liberal | Markets, trade, openness | trade efficiency +5%, production efficiency +5% |
| Centre-Right | Fiscal discipline, defence | interest −0.5, national tax +5% |
| National-Conservative | Sovereignty, security | land morale +5%, manpower +10%, improve relations −15% |
| Governing Coalition | Neutral placeholder | none |

Bloc modifiers are country triggered modifiers keyed on the flag
`eu4_2k_bloc_<bloc>`. Each competitive country also has one
`eu4_2k_opposition_<bloc>` flag and an `eu4_2k_terms` variable counting the
governing bloc's consecutive terms.

## Data

- `data/political_blocs_2000.csv`: one row per country with elections:
  opposition bloc on 2000.1.1, cycle (4 or 5 years), first scripted election,
  and whether elections run from the start.
  - About 50 audited countries (Europe and the major democracies) use real
    election dates. Where the leadership timeline covers a country, the first
    scripted election follows the last timeline event.
  - About 95 other democracies use the neutral Governing Coalition on a
    deterministic staggered calendar, marked for manual verification.
  - Yugoslavia starts without elections; the historical outcome of the
    October 2000 transition event starts them.
- `data/party_blocs.csv`: maps every governing party in the country data and
  the leadership timeline to a bloc. `*` applies a mapping to all countries.

## Election cycle

1. **Campaign (three months before):** choose a theme.
   - Economy: a bonus without loans.
   - Security: a bonus at war or with an army at 90% of the force limit.
   - Unity: costs 50 diplomatic power for a bonus.
2. **Hidden resolution:** the incumbent threshold starts at 55, of which the
   first 5 are a protest-surge share.

   | Condition | Incumbent | Surge |
   |---|---|---|
   | Stability ≥ 2 | +15 | |
   | Stability ≤ −1 | −15 | |
   | War exhaustion ≥ 5 | −15 | |
   | Any loan | −10 | |
   | Corruption ≥ 5 | −10 | |
   | Two or more consecutive terms | −15 | |
   | Campaign bonus applies | +10 | |
   | Average unrest ≥ 2, corruption ≥ 10, or war exhaustion ≥ 8 (each) | | +10 |

   A roll from 0 to 95 in steps of 5 decides the result: below the surge share
   a protest surge wins, below the threshold the incumbent is re-elected, and
   otherwise the opposition takes power.
3. **Outcome:**
   - Re-election keeps the leader, unless the bloc has already served two
     terms, in which case it renews its leadership.
   - An opposition or surge victory brings a new leader, and the previous
     governing bloc becomes the opposition.
   - A protest surge brings National-Conservatives to power, or the Left if
     National-Conservatives already govern.
4. The next campaign is scheduled one cycle later.

EU4's own term elections are disabled with `has_term_election = no` on every
generated executive reform. Leaders now change only through elections,
leadership-timeline events, or death.

## Leadership timeline

`scripts/generate_political_events.py` reads the party mapping, so every
historical or alternate leader also brings their bloc to power.
`DEMOCRATIZING_OUTCOMES` lists the outcomes that start elections; currently
only the historical result of the Yugoslav transition is listed.

## Generation and validation

```powershell
python scripts/generate_elections.py generate
python scripts/generate_elections.py --check
```

Validation checks that:
- the countries with elections at the start match the competitive countries in
  the country data
- every governing and timeline party maps to a bloc
- the starting opposition differs from the governing bloc
- first elections fall after the leadership timeline and before 2011
- outputs are current

`scripts/analyze_save.py` now also reports the bloc distribution, ruler
changes in democracies and other countries, and the leaders of key countries
since 2000.
