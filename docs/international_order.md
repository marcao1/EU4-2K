# Modern International Order

## Why

In the first 2000–2011 observer run, the AI started 31 wars of its own. All of
them used the `cb_conquest` casus belli built on claims its diplomats had
fabricated, and the attacker won every war that finished. The 2000 setup
contains no claims, so claim fabrication was the single source of these wars.

This layer keeps conquest possible but rare and costly. Historical wars from
`docs/conflicts_2000.md` are history entries rather than declarations, so they
are unaffected.

## Rules

### AI claim fabrication

The vanilla `fabricate_claim` diplomatic action gains a condition: an AI country
may fabricate claims only if it has the country flag `eu4_2k_revisionist_power`.
No country has the flag at the start. Later political or event content can set
it to create deliberate revisionist powers. The player is not restricted.

Claims granted by scripted content still work. The Yugoslav restoration
mission, for example, adds permanent claims and may lead to conquest wars.

### Modern International Order

A country triggered modifier applies to every country, including countries
released later:

| Modifier | Value |
|---|---|
| Claim fabrication cost | +100% |
| Aggressive expansion impact | +50% |
| Unjustified demands | +50% |
| Province warscore cost | +25% |
| Core creation cost | +25% |

### UN Charter violation

When a country declares a war as attacker leader with `cb_conquest`, the vanilla
`declarewar` effect calls `eu4_2k_apply_charter_violation`.

- The aggressor receives **Condemned for Aggression** for ten years:
  diplomatic reputation −2, improve relations −25%, aggressive expansion impact
  +25%, global trade power −10%. It also loses 10 prestige.
- Every country that is not the aggressor's ally or subject gains the opinion
  modifier **Violated the UN Charter** (−50, decaying by 5 per year, stacking to
  −150 for repeat aggression).
- The defending war leader receives **Rallying Against Aggression** for five
  years: land morale +10%, manpower recovery +20%, unrest −1, and monthly war
  exhaustion −0.02.
- Both sides receive an explanation event (`eu4_2k_order.1` and `.2`).

Wars without a casus belli are not covered: vanilla already stops the AI from
declaring them, and the player pays the normal stability cost.

## Implementation

`scripts/generate_international_order.py` reproduces the vanilla
`common/diplomatic_actions/00_diplomatic_actions.txt` with exactly two inserted
blocks, each marked `EU4 2K`. The script fails if either anchor is missing or
ambiguous. `--check` confirms that the file differs from vanilla only by those
blocks and that every output is current.

The other outputs are the scripted effect, the triggered modifier, the event
and opinion modifiers, the two events, and their English localisation.

```powershell
python scripts/generate_international_order.py generate
python scripts/generate_international_order.py --check
```

## Measuring AI behaviour

`scripts/analyze_save.py` is a read-only report for observer runs. It lists the
scripted 2000 wars and how they ended, and groups every war started since 2000
by casus belli, with attacker, defender, and outcome.

```powershell
python scripts/analyze_save.py
python scripts/analyze_save.py "path/to/save.eu4" --since 2000
```

Without a path it reads the autosave. The pre-change baseline at 2011.1.1 was
31 AI wars, all `cb_conquest`, all won by the attacker.
