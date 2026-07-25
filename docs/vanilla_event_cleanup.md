# Vanilla Event Cleanup

EU4 2K selectively disables obsolete vanilla historical content without using
`replace_path="events"`. Generic economic, government, ruler, advisor, estate,
religious-mechanical, military, and random events remain available pending a
later manual content audit.

The disabled categories are:

- Medieval and early-modern country flavor.
- Events belonging to removed vanilla missions.
- Country-specific and early-modern historical disasters.
- Reformation and European religious-war history.
- Historical colonization and colonial-nation events.
- Holy Roman Empire history and imperial incidents.
- Early-modern dynastic and personal-union history.
- Vanilla eighteenth- and nineteenth-century revolutions.
- Obsolete ruler, conquest, institution, and state-system events.

The current EU4 1.37.5 audit disables 255 of the 370 vanilla event files and
34 associated historical disaster-definition files. The other 115 vanilla
event files remain available as the initial generic/mechanical allowlist.

Vanilla on-actions directly call many of these event IDs. Generated override
files therefore preserve every original ID as a hidden, triggered-only no-op.
This prevents missing-event references while removing the original triggers,
options, effects, historical characters, and text. Matching historical disaster
definitions are shadowed so countries cannot enter disasters whose event chains
have been disabled.

The classification rules and output generator are maintained in
`scripts/disable_obsolete_vanilla_events.py`.

Generate the overrides:

```powershell
python scripts/disable_obsolete_vanilla_events.py generate
```

Validate without changing files:

```powershell
python scripts/disable_obsolete_vanilla_events.py --check
```

This cleanup does not remove vanilla religions. Religion-specific mechanical
events remain unless they belong specifically to Reformation or European
religious-war history.
