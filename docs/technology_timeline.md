# Technology Timeline

EU4 2K retains the complete vanilla EU4 1.37.5 administrative, diplomatic, and
military technology definitions. Technology effects, costs, building unlocks,
unit unlocks, combat modifiers, and all other gameplay commands are unchanged.

Only three presentation/timeline elements are generated differently:

- The `year` of every technology level.
- The displayed English technology name.
- The source-file header comment identifying the new title.

Level 9 represents the leading technology standard on `2000.1.1`. Levels 10
through 16 are dated every five years from 2005 through 2035. Later vanilla
levels remain mechanically unchanged and receive increasing future dates through
2250 so the technology sequence never returns to an obsolete year.

The canonical mapping is `data/technology_years_titles.csv`. Generate it with:

```powershell
python scripts/generate_technology_timeline.py generate
```

Validate without modifying files:

```powershell
python scripts/generate_technology_timeline.py --check
```

Vanilla technology descriptions are intentionally retained for now because the
current scope changes only years and titles.

The name overrides use EU4's `localisation/replace` directory so they replace
the original vanilla technology-name keys without ambiguous localization load
order.
