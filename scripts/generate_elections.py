#!/usr/bin/env python3
"""Generate and validate democratic elections and the five political blocs.

Competitive countries hold scripted elections on their own cycle. A campaign
event precedes each election; a hidden resolution scores the government's
record, rolls the result, and either re-elects the governing bloc, hands power
to the opposition, or produces a protest surge. Blocs carry small directional
modifiers. EU4's built-in term elections are switched off in the country
snapshot's executive reforms.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Sequence

import generate_country_snapshot as countries


ROOT = countries.ROOT
MOD = countries.MOD
BLOC_DATA = ROOT / "data" / "political_blocs_2000.csv"
PARTY_DATA = ROOT / "data" / "party_blocs.csv"
TIMELINE_DATA = ROOT / "data" / "leadership_events_2000_2005.csv"
EVENT_OUTPUT = MOD / "events" / "eu4_2k_election_events.txt"
ON_ACTION_OUTPUT = MOD / "common" / "on_actions" / "zz_eu4_2k_elections.txt"
EFFECT_OUTPUT = MOD / "common" / "scripted_effects" / "eu4_2k_elections.txt"
TRIGGERED_MODIFIER_OUTPUT = MOD / "common" / "triggered_modifiers" / "eu4_2k_political_blocs.txt"
LOCALISATION_OUTPUT = MOD / "localisation" / "eu4_2k_elections_l_english.yml"

BLOC_FIELDS = [
    "tag", "opposition_bloc", "cycle_years", "first_election",
    "competitive_at_start", "source", "verification_notes",
]
PARTY_FIELDS = ["tag", "party", "bloc"]
ANY_TAG = "*"

START = date(2000, 1, 1)
NAMESPACE = "eu4_2k_elections"
CAMPAIGN_LEAD_DAYS = 90
CYCLE_DAYS = {4: 1461, 5: 1826}
COMPETITIVE_SYSTEMS = {"multiparty", "dominant_party"}

BLOCS = {
    "left": {
        "name": "Left",
        "desc": "A left-wing government expands the welfare state and is sceptical of military spending.",
        "modifiers": ("global_unrest = -1", "development_cost = -0.05", "land_maintenance_modifier = 0.1"),
    },
    "centre_left": {
        "name": "Centre-Left",
        "desc": "A social-democratic government favours social cohesion and international cooperation.",
        "modifiers": ("stability_cost_modifier = -0.05", "improve_relation_modifier = 0.1"),
    },
    "liberal": {
        "name": "Liberal",
        "desc": "A liberal government favours open markets, trade, and private enterprise.",
        "modifiers": ("trade_efficiency = 0.05", "production_efficiency = 0.05"),
    },
    "centre_right": {
        "name": "Centre-Right",
        "desc": "A centre-right government favours fiscal discipline and a credible defence.",
        "modifiers": ("interest = -0.5", "global_tax_modifier = 0.05"),
    },
    "national_conservative": {
        "name": "National-Conservative",
        "desc": "A national-conservative government puts sovereignty and security first, at some cost to its foreign relations.",
        "modifiers": ("land_morale = 0.05", "global_manpower_modifier = 0.1", "improve_relation_modifier = -0.15"),
    },
    "coalition": {
        "name": "Governing Coalition",
        "desc": "A broad governing coalition without a clear ideological direction.",
        "modifiers": (),
    },
}
SURGE_BLOC = "national_conservative"
SURGE_FALLBACK = "left"

EVENTS = {
    1: {
        "title": "An Election Campaign",
        "desc": "National elections are three months away. Our governing bloc must decide what message to put before the voters.",
        "options": (
            "Campaign on the economy",
            "Campaign on security",
            "Campaign on national unity",
        ),
    },
    2: {"title": "Election Results Are Counted", "desc": "The votes are being counted.", "options": ("Continue",)},
    3: {
        "title": "The Government Is Re-elected",
        "desc": "Voters have returned the governing bloc to office for another term.",
        "options": ("The people have spoken",),
    },
    4: {
        "title": "A Change of Government",
        "desc": "The opposition has won the election. A new government takes office and sets a new political direction.",
        "options": ("We accept the verdict of the voters",),
    },
    5: {
        "title": "A Protest Vote",
        "desc": "Discontent with the established parties has carried an outsider movement into government.",
        "options": ("A new political era begins",),
    },
}


def parse_date(value: str) -> date:
    year, month, day = (int(part) for part in value.split("."))
    return date(year, month, day)


def loc_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def read_csv(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(fields):
            raise RuntimeError(f"{path.name}: columns do not match the canonical schema")
        return list(reader)


def load_bloc_rows() -> list[dict[str, str]]:
    return read_csv(BLOC_DATA, BLOC_FIELDS)


def load_party_blocs() -> dict[tuple[str, str], str]:
    return {(row["tag"], row["party"]): row["bloc"] for row in read_csv(PARTY_DATA, PARTY_FIELDS)}


def party_bloc(parties: dict[tuple[str, str], str], tag: str, party: str) -> str | None:
    return parties.get((tag, party)) or parties.get((ANY_TAG, party))


def timeline_rows() -> list[dict[str, str]]:
    with TIMELINE_DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def bloc_tooltips(prefix: str) -> list[str]:
    return [
        f"if = {{ limit = {{ has_country_flag = eu4_2k_bloc_{bloc} }} custom_tooltip = {prefix}_{bloc}_tt }}"
        for bloc in BLOCS
    ]


def scripted_effects_text() -> str:
    lines = [
        "# Generated by scripts/generate_elections.py",
        "",
        "eu4_2k_clear_ruling_bloc = {",
        *(f"\tclr_country_flag = eu4_2k_bloc_{bloc}" for bloc in BLOCS),
        "}",
        "",
        "eu4_2k_clear_opposition_bloc = {",
        *(f"\tclr_country_flag = eu4_2k_opposition_{bloc}" for bloc in BLOCS),
        "}",
        "",
    ]
    for bloc in BLOCS:
        lines.extend([
            "# The governing bloc stays in office or the previous one becomes the opposition.",
            f"eu4_2k_bloc_takes_power_{bloc} = {{",
            "\tif = {",
            f"\t\tlimit = {{ has_country_flag = eu4_2k_bloc_{bloc} }}",
            "\t\tchange_variable = { which = eu4_2k_terms value = 1 }",
            "\t}",
            "\telse = {",
            "\t\teu4_2k_clear_opposition_bloc = yes",
        ])
        lines.extend(
            f"\t\tif = {{ limit = {{ has_country_flag = eu4_2k_bloc_{other} }} set_country_flag = eu4_2k_opposition_{other} }}"
            for other in BLOCS
        )
        lines.extend([
            "\t\teu4_2k_clear_ruling_bloc = yes",
            f"\t\tset_country_flag = eu4_2k_bloc_{bloc}",
            "\t\tset_variable = { which = eu4_2k_terms value = 1 }",
            "\t}",
            "}",
            "",
        ])
    first, *rest = BLOCS
    lines.extend([
        "eu4_2k_opposition_takes_power = {",
        "\tif = {",
        f"\t\tlimit = {{ has_country_flag = eu4_2k_opposition_{first} }}",
        f"\t\teu4_2k_bloc_takes_power_{first} = yes",
        "\t}",
    ])
    for bloc in rest:
        lines.extend([
            "\telse_if = {",
            f"\t\tlimit = {{ has_country_flag = eu4_2k_opposition_{bloc} }}",
            f"\t\teu4_2k_bloc_takes_power_{bloc} = yes",
            "\t}",
        ])
    lines.extend([
        "}",
        "",
        "eu4_2k_surge_takes_power = {",
        "\tif = {",
        f"\t\tlimit = {{ has_country_flag = eu4_2k_bloc_{SURGE_BLOC} }}",
        f"\t\teu4_2k_bloc_takes_power_{SURGE_FALLBACK} = yes",
        "\t}",
        "\telse = {",
        f"\t\teu4_2k_bloc_takes_power_{SURGE_BLOC} = yes",
        "\t}",
        "}",
        "",
        "# The campaign event opens three months before the next election.",
        "eu4_2k_schedule_next_election = {",
        "\tif = {",
        "\t\tlimit = { has_country_flag = eu4_2k_election_cycle_5 }",
        f"\t\tcountry_event = {{ id = {NAMESPACE}.1 days = {CYCLE_DAYS[5] - CAMPAIGN_LEAD_DAYS} }}",
        "\t}",
        "\telse = {",
        f"\t\tcountry_event = {{ id = {NAMESPACE}.1 days = {CYCLE_DAYS[4] - CAMPAIGN_LEAD_DAYS} }}",
        "\t}",
        "}",
        "",
        "# Used when a country becomes a competitive democracy after the start.",
        "eu4_2k_begin_competitive_politics = {",
        "\tif = {",
        "\t\tlimit = { NOT = { has_country_flag = eu4_2k_competitive_politics } }",
        "\t\tset_country_flag = eu4_2k_competitive_politics",
        "\t\teu4_2k_schedule_next_election = yes",
        "\t}",
        "}",
        "",
    ])
    return "\n".join(lines)


def resolution_lines() -> list[str]:
    roll_entries = [
        f"\t\t\t5 = {{ set_variable = {{ which = eu4_2k_election_roll value = {value} }} }}"
        for value in range(0, 100, 5)
    ]
    return [
        "\t\t# Incumbent threshold = surge share + incumbent score; the rest is the opposition.",
        "\t\tset_variable = { which = eu4_2k_surge_score value = 5 }",
        "\t\tset_variable = { which = eu4_2k_incumbent_threshold value = 55 }",
        "\t\tif = { limit = { stability = 2 } change_variable = { which = eu4_2k_incumbent_threshold value = 15 } }",
        "\t\tif = { limit = { NOT = { stability = 0 } } change_variable = { which = eu4_2k_incumbent_threshold value = -15 } }",
        "\t\tif = { limit = { war_exhaustion = 5 } change_variable = { which = eu4_2k_incumbent_threshold value = -15 } }",
        "\t\tif = { limit = { num_of_loans = 1 } change_variable = { which = eu4_2k_incumbent_threshold value = -10 } }",
        "\t\tif = { limit = { corruption = 5 } change_variable = { which = eu4_2k_incumbent_threshold value = -10 } }",
        "\t\tif = { limit = { check_variable = { which = eu4_2k_terms value = 2 } } change_variable = { which = eu4_2k_incumbent_threshold value = -15 } }",
        "\t\tif = {",
        "\t\t\tlimit = {",
        "\t\t\t\tOR = {",
        "\t\t\t\t\tAND = { has_country_flag = eu4_2k_campaign_economy NOT = { num_of_loans = 1 } }",
        "\t\t\t\t\tAND = { has_country_flag = eu4_2k_campaign_security OR = { is_at_war = yes army_size_percentage = 0.9 } }",
        "\t\t\t\t\thas_country_flag = eu4_2k_campaign_unity",
        "\t\t\t\t}",
        "\t\t\t}",
        "\t\t\tchange_variable = { which = eu4_2k_incumbent_threshold value = 10 }",
        "\t\t}",
        *(
            "\t\tif = { limit = { %s } change_variable = { which = eu4_2k_surge_score value = 10 } change_variable = { which = eu4_2k_incumbent_threshold value = 10 } }" % trigger
            for trigger in ("average_unrest = 2", "corruption = 10", "war_exhaustion = 8")
        ),
        "\t\trandom_list = {",
        *roll_entries,
        "\t\t}",
        "\t\tif = {",
        "\t\t\tlimit = { NOT = { check_variable = { which = eu4_2k_election_roll which = eu4_2k_surge_score } } }",
        "\t\t\teu4_2k_surge_takes_power = yes",
        "\t\t\tset_variable = { which = eu4_2k_terms value = 1 }",
        "\t\t\tdefine_ruler = { }",
        f"\t\t\tcountry_event = {{ id = {NAMESPACE}.5 }}",
        "\t\t}",
        "\t\telse_if = {",
        "\t\t\tlimit = { NOT = { check_variable = { which = eu4_2k_election_roll which = eu4_2k_incumbent_threshold } } }",
        "\t\t\t# After two terms the governing bloc renews its leadership.",
        "\t\t\tif = { limit = { check_variable = { which = eu4_2k_terms value = 2 } } define_ruler = { } }",
        "\t\t\tchange_variable = { which = eu4_2k_terms value = 1 }",
        f"\t\t\tcountry_event = {{ id = {NAMESPACE}.3 }}",
        "\t\t}",
        "\t\telse = {",
        "\t\t\teu4_2k_opposition_takes_power = yes",
        "\t\t\t# Also covers generic countries where both sides are a governing coalition.",
        "\t\t\tset_variable = { which = eu4_2k_terms value = 1 }",
        "\t\t\tdefine_ruler = { }",
        f"\t\t\tcountry_event = {{ id = {NAMESPACE}.4 }}",
        "\t\t}",
        "\t\tclr_country_flag = eu4_2k_campaign_economy",
        "\t\tclr_country_flag = eu4_2k_campaign_security",
        "\t\tclr_country_flag = eu4_2k_campaign_unity",
        "\t\tclr_country_flag = eu4_2k_election_pending",
        "\t\teu4_2k_schedule_next_election = yes",
    ]


def events_text() -> str:
    lines = ["# Generated by scripts/generate_elections.py", f"namespace = {NAMESPACE}", ""]
    campaign_options = (
        ("eu4_2k_campaign_economy", "ai_chance = { factor = 40 modifier = { factor = 2 NOT = { num_of_loans = 1 } } }", ()),
        ("eu4_2k_campaign_security", "ai_chance = { factor = 20 modifier = { factor = 3 is_at_war = yes } }", ()),
        ("eu4_2k_campaign_unity", "ai_chance = { factor = 20 }", ("dip_power = 50",)),
    )
    lines.extend([
        "country_event = {",
        f"\tid = {NAMESPACE}.1",
        f"\ttitle = {NAMESPACE}.1.t",
        f"\tdesc = {NAMESPACE}.1.d",
        "\tpicture = ELECTION_REPUBLICAN_eventPicture",
        "\tis_triggered_only = yes",
        "\ttrigger = {",
        "\t\thas_country_flag = eu4_2k_competitive_politics",
        "\t\tNOT = { has_country_flag = eu4_2k_election_pending }",
        "\t}",
    ])
    for index, (flag, ai_chance, option_trigger) in enumerate(campaign_options):
        suffix = chr(ord("a") + index)
        lines.extend(["\toption = {", f"\t\tname = {NAMESPACE}.1.{suffix}"])
        if option_trigger:
            lines.append("\t\ttrigger = { " + " ".join(option_trigger) + " }")
        lines.extend([f"\t\t{ai_chance}", f"\t\tset_country_flag = {flag}"])
        if flag == "eu4_2k_campaign_unity":
            lines.append("\t\tadd_dip_power = -50")
        lines.extend([
            f"\t\tset_country_flag = eu4_2k_election_pending",
            f"\t\tcountry_event = {{ id = {NAMESPACE}.2 days = {CAMPAIGN_LEAD_DAYS} }}",
            "\t}",
        ])
    lines.extend(["}", ""])
    lines.extend([
        "country_event = {",
        f"\tid = {NAMESPACE}.2",
        f"\ttitle = {NAMESPACE}.2.t",
        f"\tdesc = {NAMESPACE}.2.d",
        "\tpicture = ELECTION_REPUBLICAN_eventPicture",
        "\thidden = yes",
        "\tis_triggered_only = yes",
        "\ttrigger = { has_country_flag = eu4_2k_competitive_politics }",
        "\toption = {",
        f"\t\tname = {NAMESPACE}.2.a",
        *resolution_lines(),
        "\t}",
        "}",
        "",
    ])
    for event_id in (3, 4, 5):
        lines.extend([
            "country_event = {",
            f"\tid = {NAMESPACE}.{event_id}",
            f"\ttitle = {NAMESPACE}.{event_id}.t",
            f"\tdesc = {NAMESPACE}.{event_id}.d",
            "\tpicture = ELECTION_REPUBLICAN_eventPicture",
            "\tis_triggered_only = yes",
            "\toption = {",
            f"\t\tname = {NAMESPACE}.{event_id}.a",
            *(f"\t\t{line}" for line in bloc_tooltips("eu4_2k_governing_bloc")),
            "\t}",
            "}",
            "",
        ])
    return "\n".join(lines)


def startup_text(rows: Sequence[dict[str, str]], parties: dict[tuple[str, str], str]) -> str:
    manifest = {row["tag"]: row for row in countries.load_manifest()}
    lines = [
        "# Generated by scripts/generate_elections.py",
        "# Set starting political blocs and schedule the first elections once.",
        "on_startup = {",
        "\tif = {",
        "\t\tlimit = {",
        "\t\t\tis_year = 2000",
        "\t\t\tNOT = { is_year = 2001 }",
        "\t\t\tNOT = { has_country_flag = eu4_2k_elections_initialized }",
        "\t\t}",
    ]
    for row in rows:
        tag = row["tag"]
        ruling = party_bloc(parties, tag, manifest[tag]["ruling_group"])
        lines.extend([
            "\t\tif = {",
            f"\t\t\tlimit = {{ tag = {tag} }}",
            f"\t\t\tset_country_flag = eu4_2k_election_cycle_{row['cycle_years']}",
            f"\t\t\teu4_2k_bloc_takes_power_{ruling} = yes",
            f"\t\t\tset_country_flag = eu4_2k_opposition_{row['opposition_bloc']}",
        ])
        if row["competitive_at_start"] == "yes":
            delay = (parse_date(row["first_election"]) - START).days - CAMPAIGN_LEAD_DAYS
            lines.extend([
                "\t\t\tset_country_flag = eu4_2k_competitive_politics",
                f"\t\t\tcountry_event = {{ id = {NAMESPACE}.1 days = {delay} }}",
            ])
        lines.append("\t\t}")
    lines.extend([
        "\t\tset_country_flag = eu4_2k_elections_initialized",
        "\t}",
        "}",
        "",
    ])
    return "\n".join(lines)


def triggered_modifiers_text() -> str:
    lines = ["# Generated by scripts/generate_elections.py", ""]
    for bloc, data in BLOCS.items():
        if not data["modifiers"]:
            continue
        lines.extend([
            f"eu4_2k_bloc_modifier_{bloc} = {{",
            f"\tpotential = {{ has_country_flag = eu4_2k_bloc_{bloc} }}",
            f"\ttrigger = {{ has_country_flag = eu4_2k_bloc_{bloc} }}",
            *(f"\t{line}" for line in data["modifiers"]),
            "}",
            "",
        ])
    return "\n".join(lines)


def localisation_text() -> str:
    lines = ["l_english:"]
    for event_id, event in EVENTS.items():
        lines.extend([
            f' {NAMESPACE}.{event_id}.t:0 "{loc_text(event["title"])}"',
            f' {NAMESPACE}.{event_id}.d:0 "{loc_text(event["desc"])}"',
        ])
        for index, option in enumerate(event["options"]):
            lines.append(f' {NAMESPACE}.{event_id}.{chr(ord("a") + index)}:0 "{loc_text(option)}"')
    for bloc, data in BLOCS.items():
        lines.append(f' eu4_2k_governing_bloc_{bloc}_tt:0 "Governing bloc: {loc_text(data["name"])}"')
        if data["modifiers"]:
            lines.extend([
                f' eu4_2k_bloc_modifier_{bloc}:0 "{loc_text(data["name"])} Government"',
                f' desc_eu4_2k_bloc_modifier_{bloc}:0 "{loc_text(data["desc"])}"',
            ])
    return "\n".join(lines) + "\n"


def outputs(rows: Sequence[dict[str, str]], parties: dict[tuple[str, str], str]) -> dict[Path, bytes]:
    return {
        EVENT_OUTPUT: events_text().encode("cp1252"),
        ON_ACTION_OUTPUT: startup_text(rows, parties).encode("cp1252"),
        EFFECT_OUTPUT: scripted_effects_text().encode("cp1252"),
        TRIGGERED_MODIFIER_OUTPUT: triggered_modifiers_text().encode("cp1252"),
        LOCALISATION_OUTPUT: ("﻿" + localisation_text()).encode("utf-8"),
    }


def validate(
    rows: Sequence[dict[str, str]],
    parties: dict[tuple[str, str], str],
    check_outputs: bool = True,
) -> None:
    errors: list[str] = []
    manifest = {row["tag"]: row for row in countries.load_manifest() if row["active_2000"] == "yes"}
    competitive = {tag for tag, row in manifest.items() if row["political_competition"] in COMPETITIVE_SYSTEMS}
    last_timeline: dict[str, date] = defaultdict(lambda: START)
    timeline_parties: dict[str, set[str]] = defaultdict(set)
    for event in timeline_rows():
        last_timeline[event["tag"]] = max(last_timeline[event["tag"]], parse_date(event["date"]))
        timeline_parties[event["tag"]].update({event["historical_party"], event["alternate_party"]})

    tags = [row["tag"] for row in rows]
    if len(tags) != len(set(tags)):
        errors.append("duplicate political bloc rows")
    starting = {row["tag"] for row in rows if row["competitive_at_start"] == "yes"}
    if starting != competitive:
        errors.append(
            "competitive bloc rows do not match the country data: "
            f"missing={sorted(competitive - starting)}, extra={sorted(starting - competitive)}"
        )
    for (tag, _), bloc in parties.items():
        if bloc not in BLOCS or (tag != ANY_TAG and tag not in manifest):
            errors.append(f"invalid party mapping: {tag} -> {bloc}")
    for row in rows:
        tag = row["tag"]
        if tag not in manifest:
            errors.append(f"{tag}: inactive country")
            continue
        if row["opposition_bloc"] not in BLOCS:
            errors.append(f"{tag}: invalid opposition bloc {row['opposition_bloc']}")
        if row["cycle_years"] not in {str(years) for years in CYCLE_DAYS}:
            errors.append(f"{tag}: election cycle must be 4 or 5 years")
        for party in {manifest[tag]["ruling_group"], *timeline_parties[tag]}:
            if not party_bloc(parties, tag, party):
                errors.append(f"{tag}: party without a bloc: {party}")
        # The opposition describes 2000.1.1; later timeline events swap it automatically.
        ruling = party_bloc(parties, tag, manifest[tag]["ruling_group"])
        if ruling == row["opposition_bloc"] and ruling != "coalition":
            errors.append(f"{tag}: starting opposition bloc equals the governing bloc {ruling}")
        if row["competitive_at_start"] == "yes":
            try:
                first = parse_date(row["first_election"])
            except ValueError:
                errors.append(f"{tag}: invalid first election date")
                continue
            if (first - START).days < CAMPAIGN_LEAD_DAYS or first.year > 2010:
                errors.append(f"{tag}: first election must fall between April 2000 and 2010")
            if first <= last_timeline[tag]:
                errors.append(f"{tag}: first election must follow the leadership timeline ({last_timeline[tag]})")
        elif row["first_election"]:
            errors.append(f"{tag}: countries that start without elections must not have a first election date")
    if check_outputs:
        for path, content in outputs(rows, parties).items():
            if not path.exists() or path.read_bytes() != content:
                errors.append(f"missing or stale generated output: {path.relative_to(ROOT)}")
    if errors:
        raise RuntimeError("Election validation failed:\n- " + "\n- ".join(errors[:100]))


def write_outputs(rows: Sequence[dict[str, str]], parties: dict[tuple[str, str], str]) -> None:
    for path, content in outputs(rows, parties).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != content:
            path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=("generate",), default="generate")
    parser.add_argument("--check", action="store_true", help="validate without writing")
    args = parser.parse_args()
    rows = load_bloc_rows()
    parties = load_party_blocs()
    validate(rows, parties, check_outputs=args.check)
    if not args.check:
        write_outputs(rows, parties)
        validate(rows, parties)
    action = "Validated" if args.check else "Generated"
    competitive = sum(row["competitive_at_start"] == "yes" for row in rows)
    print(
        f"{action} elections for {competitive} competitive countries "
        f"({len(rows) - competitive} awaiting democratization) across {len(BLOCS)} blocs."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
