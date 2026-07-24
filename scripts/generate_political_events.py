#!/usr/bin/env python3
"""Generate and validate the event-driven 2000-2005 political timeline."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Sequence

import generate_country_snapshot as countries


ROOT = countries.ROOT
MOD = countries.MOD
DATA = ROOT / "data" / "leadership_events_2000_2005.csv"
EVENT_OUTPUT = MOD / "events" / "eu4_2k_political_events.txt"
ON_ACTION_OUTPUT = MOD / "common" / "on_actions" / "zz_eu4_2k_political_events.txt"
OPINION_OUTPUT = MOD / "common" / "opinion_modifiers" / "eu4_2k_political_opinions.txt"
LOCALISATION_OUTPUT = MOD / "localisation" / "eu4_2k_political_events_l_english.yml"

FIELDS = [
    "event_id", "tag", "date", "title", "description",
    "historical_leader", "historical_birth", "historical_party",
    "historical_adm", "historical_dip", "historical_mil", "historical_option",
    "alternate_leader", "alternate_birth", "alternate_party",
    "alternate_adm", "alternate_dip", "alternate_mil", "alternate_option",
    "source", "verification_notes",
]

START = date(2000, 1, 1)
END = date(2005, 12, 31)
NAMESPACE = "eu4_2k_politics"

CRISIS_EVENTS = (
    {
        "id": 100, "tag": "USA", "date": "2001.9.11",
        "title": "The September 11 Attacks",
        "description": "Coordinated terrorist attacks have struck New York and Washington. The government must respond while the country confronts a profound national shock.",
        "options": (
            ("A global campaign against terrorism", 90, (
                "set_global_flag = eu4_2k_september_11_attacks",
                "set_country_flag = eu4_2k_war_on_terror_path",
                "add_stability = -1", "add_prestige = 5", "add_mil_power = 25",
            )),
            ("A restrained security response", 10, (
                "set_global_flag = eu4_2k_september_11_attacks",
                "set_country_flag = eu4_2k_restrained_counterterrorism_path",
                "add_stability = -1", "add_republican_tradition = 3",
            )),
        ),
        "trigger": (),
    },
    {
        "id": 101, "tag": "AFG", "date": "2001.9.20",
        "title": "The American Ultimatum",
        "description": "Washington demands that Afghanistan surrender al-Qaeda's leadership and close its training network. Compliance could avert war but fracture the ruling coalition.",
        "options": (
            ("Reject the ultimatum", 90, (
                "set_country_flag = eu4_2k_afghanistan_rejected_ultimatum",
                "add_stability = 1", "add_prestige = -5",
            )),
            ("Cooperate with the United States", 10, (
                "set_country_flag = eu4_2k_afghanistan_accepted_ultimatum",
                "add_stability = -1", "add_prestige = 5",
                "add_opinion = { who = USA modifier = eu4_2k_counterterrorism_cooperation }",
            )),
        ),
        "trigger": ("has_global_flag = eu4_2k_september_11_attacks",),
    },
    {
        "id": 102, "tag": "USA", "date": "2001.10.7",
        "title": "The Afghanistan Decision",
        "description": "The Afghan authorities have rejected American demands. The administration must choose between military intervention and a longer campaign of diplomatic pressure.",
        "options": (
            ("Authorize military intervention", 85, (
                "set_country_flag = eu4_2k_afghanistan_intervention_authorized",
                "add_prestige = 10", "add_mil_power = 50",
                "add_opinion = { who = AFG modifier = eu4_2k_security_confrontation }",
            )),
            ("Maintain sanctions and diplomatic pressure", 15, (
                "set_country_flag = eu4_2k_afghanistan_containment_path",
                "add_dip_power = 50",
                "add_opinion = { who = AFG modifier = eu4_2k_security_disagreement }",
            )),
        ),
        "trigger": (
            "has_global_flag = eu4_2k_september_11_attacks",
            "AFG = { has_country_flag = eu4_2k_afghanistan_rejected_ultimatum }",
        ),
    },
    {
        "id": 103, "tag": "IRQ", "date": "2002.11.8",
        "title": "Resolution 1441 and the Inspectors",
        "description": "A new international inspection regime demands immediate and unrestricted Iraqi cooperation. Baghdad must decide how to answer.",
        "options": (
            ("Accept unrestricted inspections", 35, (
                "set_global_flag = eu4_2k_iraq_resolution_1441",
                "set_country_flag = eu4_2k_iraq_cooperates_with_inspections",
                "add_stability = -1", "add_prestige = 5",
            )),
            ("Obstruct and delay the inspectors", 65, (
                "set_global_flag = eu4_2k_iraq_resolution_1441",
                "set_country_flag = eu4_2k_iraq_obstructs_inspections",
                "add_stability = 1", "add_prestige = -10",
                "add_opinion = { who = USA modifier = eu4_2k_security_confrontation }",
            )),
        ),
        "trigger": (),
    },
    {
        "id": 104, "tag": "USA", "date": "2003.3.17",
        "title": "The Iraq Crisis",
        "description": "The inspection crisis has reached its decisive point. The United States must choose between regime change and continued containment.",
        "options": (
            ("Pursue regime change", 80, (
                "set_country_flag = eu4_2k_iraq_regime_change_path",
                "add_mil_power = 50", "add_prestige = 5",
                "add_opinion = { who = IRQ modifier = eu4_2k_security_confrontation }",
            )),
            ("Continue containment", 20, (
                "set_country_flag = eu4_2k_iraq_containment_path",
                "add_dip_power = 50", "add_republican_tradition = 2",
                "add_opinion = { who = IRQ modifier = eu4_2k_security_disagreement }",
            )),
        ),
        "trigger": ("has_global_flag = eu4_2k_iraq_resolution_1441",),
    },
    {
        "id": 105, "tags": ("GBR", "FR2", "GER", "RUS", "CHN"),
        "date": "2001.9.12", "title": "The International Response to September 11",
        "description": "The attacks in the United States have triggered demands for international security cooperation. Our government must define its response.",
        "options": (
            ("Support counterterrorism cooperation", 85, (
                "set_country_flag = eu4_2k_counterterrorism_cooperation_path",
                "add_dip_power = 10",
                "add_opinion = { who = USA modifier = eu4_2k_counterterrorism_cooperation }",
            )),
            ("Keep an independent distance", 15, (
                "set_country_flag = eu4_2k_independent_security_path",
                "add_prestige = 2",
                "add_opinion = { who = USA modifier = eu4_2k_security_disagreement }",
            )),
        ),
        "trigger": ("has_global_flag = eu4_2k_september_11_attacks",),
    },
)


def parse_date(value: str) -> date:
    year, month, day = (int(part) for part in value.split("."))
    return date(year, month, day)


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def loc_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def party_flag(tag: str, party: str) -> str:
    return f"eu4_2k_ruling_group_{tag.lower()}_{countries.slug(party)}"


def load_rows() -> list[dict[str, str]]:
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise RuntimeError("Leadership timeline columns do not match the canonical schema")
        return list(reader)


def known_party_flags(rows: Sequence[dict[str, str]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for row in countries.load_manifest():
        result[row["tag"]].add(party_flag(row["tag"], row["ruling_group"]))
    for row in rows:
        result[row["tag"]].update({
            party_flag(row["tag"], row["historical_party"]),
            party_flag(row["tag"], row["alternate_party"]),
        })
    return result


def ruler_effect(row: dict[str, str], prefix: str, flags: dict[str, set[str]]) -> list[str]:
    event_date = parse_date(row["date"])
    birth_date = parse_date(row[f"{prefix}_birth"])
    age = event_date.year - birth_date.year - (
        (event_date.month, event_date.day) < (birth_date.month, birth_date.day)
    )
    lines = [f"clr_country_flag = {flag}" for flag in sorted(flags[row["tag"]])]
    lines.extend([
        "define_ruler = {",
        f"\tname = {quote(row[f'{prefix}_leader'])}",
        f"\tadm = {row[f'{prefix}_adm']}",
        f"\tdip = {row[f'{prefix}_dip']}",
        f"\tmil = {row[f'{prefix}_mil']}",
        f"\tage = {age}",
        "\tclaim = 95",
        "}",
        f"set_country_flag = {party_flag(row['tag'], row[f'{prefix}_party'])}",
    ])
    return lines


def leadership_events(rows: Sequence[dict[str, str]]) -> str:
    flags = known_party_flags(rows)
    lines = ["# Generated from data/leadership_events_2000_2005.csv", f"namespace = {NAMESPACE}", ""]
    for row in rows:
        event_id = row["event_id"]
        lines.extend([
            "country_event = {",
            f"\tid = {NAMESPACE}.{event_id}",
            f"\ttitle = {NAMESPACE}.{event_id}.t",
            f"\tdesc = {NAMESPACE}.{event_id}.d",
            "\tpicture = ELECTION_REPUBLICAN_eventPicture",
            "\tis_triggered_only = yes",
            "\ttrigger = {",
            f"\t\ttag = {row['tag']}",
            "\t\tNOT = { has_country_flag = eu4_2k_political_timeline_diverged }",
            f"\t\tNOT = {{ has_country_flag = eu4_2k_political_event_{event_id}_resolved }}",
            "\t}",
            "\toption = {",
            f"\t\tname = {NAMESPACE}.{event_id}.a",
            "\t\tai_chance = { factor = 90 }",
        ])
        lines.extend(f"\t\t{line}" for line in ruler_effect(row, "historical", flags))
        lines.extend([
            f"\t\tset_country_flag = eu4_2k_political_event_{event_id}_resolved",
            "\t\tadd_prestige = 2",
            "\t}",
            "\toption = {",
            f"\t\tname = {NAMESPACE}.{event_id}.b",
            "\t\tai_chance = { factor = 10 }",
        ])
        lines.extend(f"\t\t{line}" for line in ruler_effect(row, "alternate", flags))
        lines.extend([
            "\t\tset_country_flag = eu4_2k_political_timeline_diverged",
            f"\t\tset_country_flag = eu4_2k_political_event_{event_id}_resolved",
            "\t\tadd_prestige = 2",
            "\t}",
            "}",
            "",
        ])
    return "\n".join(lines)


def crisis_events() -> str:
    lines = ["# Generated post-2000 crisis paths", ""]
    for event in CRISIS_EVENTS:
        event_id = event["id"]
        tags = event.get("tags", (event.get("tag"),))
        lines.extend([
            "country_event = {",
            f"\tid = {NAMESPACE}.{event_id}",
            f"\ttitle = {NAMESPACE}.{event_id}.t",
            f"\tdesc = {NAMESPACE}.{event_id}.d",
            "\tpicture = DIPLOMACY_eventPicture",
            "\tis_triggered_only = yes",
            "\ttrigger = {",
            "\t\tOR = { " + " ".join(f"tag = {tag}" for tag in tags if tag) + " }",
            f"\t\tNOT = {{ has_country_flag = eu4_2k_political_event_{event_id}_resolved }}",
        ])
        lines.extend(f"\t\t{trigger}" for trigger in event["trigger"])
        lines.append("\t}")
        for index, (option, weight, effects) in enumerate(event["options"]):
            suffix = chr(ord("a") + index)
            lines.extend([
                "\toption = {",
                f"\t\tname = {NAMESPACE}.{event_id}.{suffix}",
                f"\t\tai_chance = {{ factor = {weight} }}",
            ])
            lines.extend(f"\t\t{effect}" for effect in effects)
            lines.extend([
                f"\t\tset_country_flag = eu4_2k_political_event_{event_id}_resolved",
                "\t}",
            ])
        lines.extend(["}", ""])
    return "\n".join(lines)


def schedule(rows: Sequence[dict[str, str]]) -> str:
    schedules: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for row in rows:
        schedules[row["tag"]].append((int(row["event_id"]), (parse_date(row["date"]) - START).days))
    for event in CRISIS_EVENTS:
        tags = event.get("tags", (event.get("tag"),))
        delay = (parse_date(event["date"]) - START).days
        for tag in tags:
            if tag:
                schedules[tag].append((event["id"], delay))
    lines = [
        "# Schedule the clean 2000-2005 political timeline once per country.",
        "on_startup = {",
        "\tif = {",
        "\t\tlimit = {",
        "\t\t\tis_year = 2000",
        "\t\t\tNOT = { is_year = 2001 }",
        "\t\t\tNOT = { has_country_flag = eu4_2k_political_timeline_scheduled }",
        "\t\t}",
    ]
    for tag, events in sorted(schedules.items()):
        lines.extend(["\t\tif = {", f"\t\t\tlimit = {{ tag = {tag} }}"])
        for event_id, delay in sorted(events, key=lambda item: (item[1], item[0])):
            lines.append(f"\t\t\tcountry_event = {{ id = {NAMESPACE}.{event_id} days = {delay} }}")
        lines.append("\t\t}")
    lines.extend([
        "\t\tset_country_flag = eu4_2k_political_timeline_scheduled",
        "\t}",
        "}",
        "",
    ])
    return "\n".join(lines)


def opinion_modifiers() -> str:
    return """# Political-event opinion effects.
eu4_2k_counterterrorism_cooperation = { opinion = 25 }
eu4_2k_security_disagreement = { opinion = -15 }
eu4_2k_security_confrontation = { opinion = -75 }
"""


def localisation(rows: Sequence[dict[str, str]]) -> str:
    lines = ["l_english:"]
    for row in rows:
        event_id = row["event_id"]
        lines.extend([
            f' {NAMESPACE}.{event_id}.t:0 "{loc_text(row["title"])}"',
            f' {NAMESPACE}.{event_id}.d:0 "{loc_text(row["description"])}"',
            f' {NAMESPACE}.{event_id}.a:0 "{loc_text(row["historical_option"])}"',
            f' {NAMESPACE}.{event_id}.b:0 "{loc_text(row["alternate_option"])}"',
        ])
    for event in CRISIS_EVENTS:
        event_id = event["id"]
        lines.extend([
            f' {NAMESPACE}.{event_id}.t:0 "{loc_text(event["title"])}"',
            f' {NAMESPACE}.{event_id}.d:0 "{loc_text(event["description"])}"',
        ])
        for index, (option, _, _) in enumerate(event["options"]):
            suffix = chr(ord("a") + index)
            lines.append(f' {NAMESPACE}.{event_id}.{suffix}:0 "{loc_text(option)}"')
    lines.extend([
        ' eu4_2k_counterterrorism_cooperation:0 "Counterterrorism Cooperation"',
        ' eu4_2k_security_disagreement:0 "Security Policy Disagreement"',
        ' eu4_2k_security_confrontation:0 "Security Confrontation"',
    ])
    return "\n".join(lines) + "\n"


def outputs(rows: Sequence[dict[str, str]]) -> dict[Path, tuple[bytes, str]]:
    events = leadership_events(rows) + "\n" + crisis_events()
    return {
        EVENT_OUTPUT: (events.encode("cp1252"), "events"),
        ON_ACTION_OUTPUT: (schedule(rows).encode("cp1252"), "schedule"),
        OPINION_OUTPUT: (opinion_modifiers().encode("cp1252"), "opinions"),
        LOCALISATION_OUTPUT: (("\ufeff" + localisation(rows)).encode("utf-8"), "localisation"),
    }


def validate(rows: Sequence[dict[str, str]], check_outputs: bool = True) -> None:
    errors: list[str] = []
    active = {row["tag"] for row in countries.load_manifest() if row["active_2000"] == "yes"}
    ids: set[int] = set()
    dates_by_tag: dict[str, list[date]] = defaultdict(list)
    for row in rows:
        try:
            event_id = int(row["event_id"])
        except ValueError:
            errors.append(f"invalid event id: {row['event_id']}")
            continue
        if event_id in ids or event_id >= 100:
            errors.append(f"duplicate or reserved event id: {event_id}")
        ids.add(event_id)
        if row["tag"] not in active:
            errors.append(f"inactive event country: {row['tag']}")
        try:
            event_date = parse_date(row["date"])
            historical_birth = parse_date(row["historical_birth"])
            alternate_birth = parse_date(row["alternate_birth"])
            if not START <= event_date <= END:
                errors.append(f"event outside 2000-2005: {event_id}")
            if historical_birth >= event_date or alternate_birth >= event_date:
                errors.append(f"leader born after event: {event_id}")
            dates_by_tag[row["tag"]].append(event_date)
        except ValueError:
            errors.append(f"invalid event or birth date: {event_id}")
        for prefix in ("historical", "alternate"):
            for stat in ("adm", "dip", "mil"):
                try:
                    if not 1 <= int(row[f"{prefix}_{stat}"]) <= 6:
                        raise ValueError
                except ValueError:
                    errors.append(f"invalid {prefix} {stat}: {event_id}")
            if not row[f"{prefix}_leader"] or not row[f"{prefix}_party"]:
                errors.append(f"missing {prefix} leader or party: {event_id}")
    for tag, event_dates in dates_by_tag.items():
        if event_dates != sorted(event_dates):
            errors.append(f"events for {tag} are not chronological")
    if check_outputs:
        for path, (expected, _) in outputs(rows).items():
            if not path.exists() or path.read_bytes() != expected:
                errors.append(f"missing or stale generated output: {path.name}")
    if errors:
        raise RuntimeError("Political-event validation failed:\n- " + "\n- ".join(errors[:100]))


def write_outputs(rows: Sequence[dict[str, str]]) -> None:
    for path, (content, _) in outputs(rows).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != content:
            path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=("generate",), default="generate")
    parser.add_argument("--check", action="store_true", help="validate without writing")
    args = parser.parse_args()
    rows = load_rows()
    validate(rows, check_outputs=args.check)
    if not args.check:
        write_outputs(rows)
        validate(rows)
    action = "Validated" if args.check else "Generated"
    scheduled = len(rows) + sum(len(event.get("tags", (event.get("tag"),))) for event in CRISIS_EVENTS)
    print(f"{action} {len(rows)} leadership events and {scheduled - len(rows)} crisis event deliveries.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
