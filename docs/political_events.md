# Political events and leadership

## Scope

The real leadership list covers `2000.1.1` through `2025.12.31`.
`data/leadership_events.csv` is the canonical source. It records 147 elections,
cabinet changes, and successions in 27 countries, with exact dates, the
historical leader, an alternative leader, birth dates, parties, ADM/DIP/MIL
ratings, sources, and verification notes. International organizations are
intentionally excluded.

These countries are covered through 2025:

- **Balkans:** Yugoslavia/Serbia, Croatia, North Macedonia, Albania, Bulgaria,
  Romania, Greece, Slovenia
- **Europe:** Germany, France, United Kingdom, Italy, Spain, Poland, Ukraine,
  Turkey
- **Rest of the world:** United States, Russia, China, Japan, India, Israel

Austria, the Netherlands, Portugal, Taiwan, and Georgia have short lists that
end in the early 2000s.

The alternative in each event is a real contemporary politician, usually the
principal or most famous opponent: for example Seselj, Nikolic, and Tadic in
Serbia, Le Pen in France, and Zyuganov and Navalny in Russia. Rows added for
2006–2025 are marked for a manual source check before release.

## Event behaviour

Every leadership event offers two choices:

- The historical result, with a 90% AI weight.
- The alternative leader, with a 10% AI weight.

Choosing the alternative sets `eu4_2k_political_timeline_diverged`, and later
events for that country no longer fire. Each event also clears known
ruling-group flags before setting the new party flag. Yugoslavia's events also
fire for Serbia (`SER`) after a tag change.

## Leaders and EU4 elections

Countries in the list receive the government reform
`eu4_2k_scripted_leadership`, which sets `has_term_election = no`. While a
country follows its list, its leaders change only through the dated events or
death. Re-elections are not needed, so long-serving leaders such as Xi, Putin,
and Rama simply stay in office.

The country returns to EU4's normal elections when:

- the player or AI chooses an alternative leader (history has diverged), or
- the list ends: on 1 January 2026 for the fully covered countries, or at the
  last listed event for the five early-2000s lists.

Countries outside the list use EU4's normal elections throughout.

The timeline is scheduled once from the `2000.1.1` bookmark. Persistent country
flags prevent duplicate scheduling or repeated events after loading a save.

## International-crisis layer

- The September 11 attacks and the United States response.
- Counterterrorism responses for the United Kingdom, France, Germany, Russia,
  and China.
- The American ultimatum to Afghanistan and the intervention/containment path.
- United Nations Security Council Resolution 1441 and Iraq's response.
- The 2003 United States regime-change or containment decision.

The crisis events record paths through flags and political/diplomatic effects.
They do not force wars.

## Generation and validation

```powershell
python scripts/generate_political_events.py generate
python scripts/generate_political_events.py --check
```

Validation rejects:
- duplicate IDs, or IDs that collide with the crisis events (100–105) or the
  handover event (900)
- inactive tags and invalid dates
- leaders born after their event and out-of-range ratings
- national timelines out of chronological order
- missing or stale event, schedule, opinion, or localisation output

Generation is deterministic.
