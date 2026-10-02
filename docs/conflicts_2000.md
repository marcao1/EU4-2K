# Conflicts Active on 2000.1.1

## Scope

The bookmark starts with the wars that were being fought on 1 January 2000
already running, and with the de facto authorities that held territory in
them. Kosovo, where fighting had ended, is represented by a UN-administration
modifier instead of a war.

Wars that began after the start date (Afghanistan 2001, Iraq 2003, and later)
belong to the event-driven war layer and are not part of this stage. Sri Lanka,
Somalia, and the frozen post-Soviet conflicts are not yet represented.

## Conflict factions

Four new active tags are listed in `CONFLICT_ENTITIES` in
`scripts/generate_country_snapshot.py`. They are exempt from the minimum
national-development rule because they hold only a few provinces.

| Tag | Faction | Leader on 2000.1.1 | Territory |
|---|---|---|---|
| `AFG` | Taliban Islamic Emirate of Afghanistan (theocracy) | Mullah Mohammed Omar | 14 of 16 Afghan provinces, including Kabul and Kandahar |
| `ISA` | Northern Alliance (UN-recognized Islamic State of Afghanistan) | Burhanuddin Rabbani | Badakhshan (452) and Kunduz (2227, standing in for Takhar) |
| `ICK` | Chechen Republic of Ichkeria | Aslan Maskhadov | Chechnya (2198, Grozny) |
| `RCD` | Rally for Congolese Democracy (Rwanda-backed RCD-Goma) | Emile Ilunga | Kivu, Bukavu, Maniema, Kisangani, Kalemie, Kasongo, Kama |
| `FLC` | Movement for the Liberation of Congo (Uganda-backed MLC) | Jean-Pierre Bemba | Zongo, Uele, Ituri |

`AFG` stays the Afghan state tag so the existing 2001 ultimatum event remains
correct and the tag can continue as post-Taliban Afghanistan. Afghanistan's UN
seat moves to `ISA`. Both Afghan factions hold cores on all 16 Afghan
provinces. Rebel and secessionist provinces keep the recognized state's core
(`RUS` on Chechnya, `DRC` on the Congolese rebel areas). Uganda-aligned RCD-ML
areas are folded into `FLC`; the two merged as the FLC in January 2001.

Chechnya uses a new `chechen` culture (`CUSTOM_CULTURES` in the country
generator). Province 2198 was renamed from Khundzia to Chechnya.

Russia's national development target of 2000 includes Chechnya through its
core, so Russia's total is unchanged when Grozny returns.

## Wars

Wars are defined in `data/wars_2000.csv` and generated into `history/wars/`.
The descriptor replaces `history/wars`, so vanilla early-modern wars no longer
appear in the war history of a 2000 game.

| War | Attackers (leader first) | Defenders (leader first) | War goal |
|---|---|---|---|
| Afghan Civil War (1996) | AFG | ISA | Take core: Badakhshan |
| Second Chechen War (1999) | RUS | ICK | Take core: Chechnya |
| Eritrean-Ethiopian War (1998) | ERT | ETH | Mutual superiority |
| Second Congo War (1998) | RWA, RCD, BUU | DRC, AGL, GZI, NMB | Mutual superiority |
| Second Congo War, Northern Front (1998) | UGA, FLC | DRC, GZI | Mutual superiority |

The Congo war is split into two wars so each foreign withdrawal can end one war
through a white peace between the two war leaders.

## Scripted endings

Endings follow the historical dates. Each one checks that the war still exists
and offers the player an alternative. AI weights favor the historical choice.

| Date | Event | Historical outcome | Alternative |
|---|---|---|---|
| 2000.6.18 | Algiers Ceasefire (Ethiopia) | White peace with Eritrea; both get a ten-year Temporary Security Zone modifier | Continue the offensive; Defied International Mediation modifier |
| When Russia controls Grozny | Fall of Grozny (Russia, polled) | Russia absorbs Ichkeria; the Chechen insurgency modifier activates | Negotiated settlement: white peace, Ichkeria survives |
| 2009.4.16 | End of the Counter-Terrorism Operation (Russia) | Insurgency modifier ends | — |
| 2002.7.30 | Pretoria Agreement (Congo) | White peace with Rwanda, ending the RCD front | Fight on |
| 2002.9.6 | Luanda Agreement (Congo) | White peace with Uganda, ending the northern front | Fight on |
| 2003.6.30 | Transitional Government (Congo) | RCD and MLC are invited to rejoin; accepting merges them into Congo | Govern without the rebels; each movement may also refuse |

If the AI ends a war earlier through a normal peace, the matching event does
not fire. If Russia annexes Ichkeria by peace, the Fall of Grozny event still
activates the insurgency.

The Afghan civil war has no scripted ending here. It continues until the
2001 intervention layer handles it.

## Province modifiers

Province triggered modifiers are attached once at the start and switch on or
off through their triggers.

- **UN Interim Administration (UNSCR 1244)** on Kosovo (1766): no tax,
  production, or manpower for Yugoslavia or Serbia, and reduced unrest. All
  three outcomes of the Yugoslav "Address Kosovo" mission event set
  `eu4_2k_unmik_mandate_ended`, which ends it.
- **Northern Alliance Mountain Strongholds** on Badakhshan and Kunduz while
  `ISA` owns them: fort level 1, +50% local defensiveness, and +2 hostile
  attrition, so the Northern Alliance is harder to destroy before 2001.
- **Chechen Insurgency** on Chechnya while Russia owns it and the insurgency
  flag is set: +4 unrest, -50% tax and manpower, +1 hostile attrition.

## Diplomacy

Added to `CURATED_BILATERAL_RELATIONSHIPS` in
`scripts/generate_starting_world.py`:

- Alliances: Rwanda–RCD, Uganda–MLC.
- Hostile: Taliban–Northern Alliance, Russia–Ichkeria, Congo–RCD, Congo–MLC,
  Taliban–United States, Taliban–Iran.
- Friendly: Taliban–Pakistan; Northern Alliance with Russia, Iran, India, and
  Tajikistan.

## Flags

`scripts/generate_conflicts.py` draws five flags into `assets/flags/`, and the
country generator copies them through the `mod:` flag source.

- `AFG`: the plain white Taliban flag of 1996–1997. The later shahada needs
  Arabic text shaping, which the asset pipeline does not provide.
- `ISA`: green, white, and black tricolour without its central emblem.
- `ICK`: green with white, red, and white stripes, without the wolf emblem.
- `RCD`, `FLC`: placeholders until verified flags are sourced.

## Generation and validation

Run from the repository root:

```powershell
python scripts/generate_conflicts.py generate
python scripts/generate_conflicts.py --check
```

Generate conflicts before the country snapshot, because the country generator
copies the flag assets. Validation rejects inactive or duplicate participants,
countries on both sides, wars starting on or after the bookmark, unsupported
war goals, target provinces the defender does not hold or the attacker has no
core on, conflict factions without a war, scripted dates outside 2000–2010,
modifiers attached to provinces not held by the expected country, and stale
outputs.

## Known limits and in-game checks

- EU4 lets a winner demand provinces in any war, so the AI may still take
  territory before a scripted ending fires (for example Rwanda in eastern
  Congo).
- The Taliban may destroy the Northern Alliance before 2001 despite the
  stronghold modifier.
- Leader ratings and Emile Ilunga's birth date (unknown; placeholder) need a
  sourcing pass.

Checks for the next test campaign:

1. All five wars are listed under each participant's wars at game start.
2. Kosovo shows the UN administration modifier.
3. The Algiers ceasefire fires for Ethiopia on 18 June 2000.
4. The Fall of Grozny fires once Russia holds Grozny.
5. `error.log` has no entries for `eu4_2k_conflicts`, the new tags, or `history/wars`.
