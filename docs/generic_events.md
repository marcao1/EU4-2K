# Modern Generic Events

EU4 2K includes a pool of 40 recurring vanilla-style events divided evenly
between government, economy, society, infrastructure, technology, military,
diplomacy, and environment.

These are not fixed historical events. They represent recurring pressures that
can affect any modern country after the `2000.1.1` start. Each event provides two
choices with different immediate costs and temporary national modifiers.

The pool uses `on_yearly_pulse_5` with equal event weights and a no-event weight
of 4000. When events are eligible this produces a 50 percent yearly chance of one
modern generic event. A one-year shared cooldown prevents multiple generic events
from firing too close together. AI choice weights favor the more cautious option
without forcing it.

Canonical event text and choices are stored in `data/generic_events_2000.csv`.
The generated event script, pulse, modifiers, and English localization are
produced by `scripts/generate_generic_events.py`.

Generate:

```powershell
python scripts/generate_generic_events.py generate
```

Validate without writing:

```powershell
python scripts/generate_generic_events.py --check
```
