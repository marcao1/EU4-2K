# Political events and leadership

## Scope

The first event-driven political timeline covers `2000.1.1` through
`2005.12.31`. It focuses on Europe, the United States, China, Russia, India,
Japan, Taiwan, Israel, Georgia, Ukraine, and Yugoslavia. International
organizations are intentionally excluded.

`data/leadership_events_2000_2005.csv` is the canonical leadership source. It
records 24 elections, cabinet changes, party successions, and political
transitions with exact dates, historical and alternate leaders, birth dates,
ruling groups, ADM/DIP/MIL ratings, sources, and verification notes.

## Event behavior

Every leadership event offers two choices:

- A historical result with a 90% AI weight.
- A plausible contemporary alternative with a 10% AI weight.

Choosing an alternate result sets `eu4_2k_political_timeline_diverged`. Later
leadership events for that country no longer overwrite the alternate political
path. Historical results leave the remaining timeline active. Each event also
clears known ruling-group flags before setting the new stable party flag.

The timeline is scheduled once from the `2000.1.1` bookmark. Persistent country
flags prevent duplicate scheduling or repeated events after loading a save.
Scripted transitions replace the current executive on the event date. Deeper
election mechanics and changes to vanilla election cycles remain a later phase.

## Initial leadership coverage

The timeline includes transitions in Croatia, Austria, Japan, Italy, Russia,
Taiwan, Yugoslavia, the United States, Israel, Poland, Portugal, the
Netherlands, China, Georgia, Greece, Spain, India, Ukraine, and Germany. Japan,
Italy, Croatia, and Portugal have multiple sequential events.

The initial bespoke international-crisis layer contains:

- The September 11 attacks and the United States response.
- Counterterrorism responses for the United Kingdom, France, Germany, Russia,
  and China.
- The American ultimatum to Afghanistan and the intervention/containment path.
- United Nations Security Council Resolution 1441 and Iraq's response.
- The 2003 United States regime-change or containment decision.

The crisis events record paths through flags and political/diplomatic effects.
They do not force wars. Later war and peace systems can consume those flags
without making a historical conflict inevitable in a divergent campaign.

## Generation and validation

Run:

```powershell
python scripts/generate_political_events.py generate
python scripts/generate_political_events.py --check
```

Validation rejects duplicate or reserved IDs, inactive tags, invalid dates,
leaders born after their event, out-of-range ratings, nonchronological national
timelines, and missing or stale event, schedule, opinion, or localization
output. Generation is deterministic.

## Next extension

Extend the same dataset and generator from 2006 onward, then add country-specific
political consequences such as reform changes, protest movements, impeachments,
coups, and formation or dissolution events. International organizations remain
a separate project layer.
