#!/usr/bin/env python3
"""Generate the modern vanilla-style random event pool."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "MillenniumDawnEU4"
DATA = ROOT / "data" / "generic_events_2000.csv"
EVENT_OUTPUT = MOD / "events" / "eu4_2k_generic_events.txt"
ON_ACTION_OUTPUT = MOD / "common" / "on_actions" / "zz_eu4_2k_generic_events.txt"
MODIFIER_OUTPUT = MOD / "common" / "event_modifiers" / "eu4_2k_generic_event_modifiers.txt"
LOC_OUTPUT = MOD / "localisation" / "eu4_2k_generic_events_l_english.yml"

CATEGORIES = (
    "government", "economy", "society", "infrastructure",
    "technology", "military", "diplomacy", "environment",
)
PICTURES = {
    "DIPLOMACY_eventPicture", "BIG_BOOK_eventPicture", "CITY_VIEW_eventPicture",
    "ECONOMY_eventPicture", "TRADEGOODS_eventPicture", "UNIVERSITY_eventPicture",
    "BATTLE_eventPicture",
}

DIRECT_EFFECTS = {
    "income": "add_years_of_income",
    "adm": "add_adm_power",
    "dip": "add_dip_power",
    "mil": "add_mil_power",
    "prestige": "add_prestige",
    "stability": "add_stability",
    "corruption": "add_corruption",
    "inflation": "add_inflation",
    "army_tradition": "add_army_tradition",
    "navy_tradition": "add_navy_tradition",
}

MODIFIERS: dict[str, tuple[str, str, tuple[tuple[str, str], ...]]] = {
    "eu4_2k_generic_event_cooldown": (
        "Recent Domestic Event", "Another major domestic event is unlikely during this period.", (),
    ),
    "eu4_2k_accountable_government": (
        "Accountable Government", "Oversight and transparency are strengthening public institutions.",
        (("yearly_corruption", "-0.05"), ("stability_cost_modifier", "-0.05")),
    ),
    "eu4_2k_government_pressure": (
        "Government Under Pressure", "Political pressure is making public administration more difficult.",
        (("global_unrest", "1"), ("global_tax_modifier", "0.03")),
    ),
    "eu4_2k_social_compromise": (
        "Social Compromise", "A negotiated settlement has reduced immediate social tensions.",
        (("global_unrest", "-1"), ("production_efficiency", "-0.02")),
    ),
    "eu4_2k_social_tension": (
        "Social Tension", "Unresolved political and economic grievances are increasing unrest.",
        (("global_unrest", "1"), ("manpower_recovery_speed", "0.05")),
    ),
    "eu4_2k_economic_confidence": (
        "Economic Confidence", "Investment and commercial activity are expanding.",
        (("production_efficiency", "0.05"), ("trade_efficiency", "0.05")),
    ),
    "eu4_2k_economic_adjustment": (
        "Economic Adjustment", "Short-term restraint is helping stabilize the wider economy.",
        (("global_tax_modifier", "-0.03"), ("global_unrest", "-0.5")),
    ),
    "eu4_2k_infrastructure_upgrade": (
        "Infrastructure Upgrade", "Modern infrastructure is reducing development and construction costs.",
        (("development_cost", "-0.03"), ("build_cost", "-0.05")),
    ),
    "eu4_2k_deferred_maintenance": (
        "Deferred Maintenance", "Short-term savings are creating a growing infrastructure backlog.",
        (("build_cost", "0.10"), ("production_efficiency", "0.03")),
    ),
    "eu4_2k_innovation_program": (
        "Innovation Program", "Public and private research networks are accelerating innovation.",
        (("technology_cost", "-0.03"), ("global_institution_spread", "0.10")),
    ),
    "eu4_2k_digital_security": (
        "Digital Security Program", "Stronger networks are improving resistance to espionage and disruption.",
        (("global_spy_defence", "0.20"), ("advisor_cost", "0.03")),
    ),
    "eu4_2k_digital_risk": (
        "Digital Vulnerability", "Rapid digitization without safeguards has exposed important systems.",
        (("global_spy_defence", "-0.15"), ("trade_efficiency", "0.03")),
    ),
    "eu4_2k_military_readiness": (
        "Heightened Military Readiness", "Training and preparedness have improved operational readiness.",
        (("land_morale", "0.08"), ("land_maintenance_modifier", "0.08")),
    ),
    "eu4_2k_military_reform": (
        "Military Reform Program", "The armed forces are adopting more effective standards and procedures.",
        (("discipline", "0.02"), ("global_regiment_cost", "0.05")),
    ),
    "eu4_2k_military_strain": (
        "Military Personnel Strain", "Lower standards have increased recruitment at the expense of quality.",
        (("global_manpower_modifier", "0.10"), ("discipline", "-0.02")),
    ),
    "eu4_2k_diplomatic_engagement": (
        "Diplomatic Engagement", "Active cooperation is strengthening the country's international position.",
        (("diplomatic_reputation", "1"), ("improve_relation_modifier", "0.10")),
    ),
    "eu4_2k_diplomatic_friction": (
        "Diplomatic Friction", "A confrontational policy is complicating foreign relations.",
        (("diplomatic_reputation", "-1"), ("trade_efficiency", "0.04")),
    ),
    "eu4_2k_environmental_resilience": (
        "Environmental Resilience", "Investment is improving the country's ability to withstand environmental pressure.",
        (("global_trade_goods_size_modifier", "0.03"), ("build_cost", "0.03"), ("global_unrest", "-0.5")),
    ),
    "eu4_2k_environmental_neglect": (
        "Environmental Neglect", "Relaxed standards raise output while increasing public dissatisfaction.",
        (("global_trade_goods_size_modifier", "0.05"), ("global_unrest", "0.5")),
    ),
}

REQUIRED_COLUMNS = {
    "id", "category", "title", "description", "picture",
    "option_a", "option_a_effects", "option_a_ai",
    "option_b", "option_b_effects", "option_b_ai",
}


def load_rows() -> list[dict[str, str]]:
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise SystemExit(f"Unexpected columns in {DATA}")
        rows = list(reader)
    if len(rows) != 40:
        raise SystemExit(f"Expected 40 generic events, found {len(rows)}")
    ids = [int(row["id"]) for row in rows]
    if ids != list(range(1, 41)):
        raise SystemExit("Generic event IDs must be exactly 1 through 40 in order.")
    counts = Counter(row["category"] for row in rows)
    if counts != Counter({category: 5 for category in CATEGORIES}):
        raise SystemExit(f"Expected five events per category, found {dict(counts)}")
    for row in rows:
        if row["picture"] not in PICTURES:
            raise SystemExit(f"Invalid event picture for event {row['id']}: {row['picture']}")
        if int(row["option_a_ai"]) + int(row["option_b_ai"]) != 100:
            raise SystemExit(f"AI weights must total 100 for event {row['id']}")
        parse_effects(row["option_a_effects"], row["id"])
        parse_effects(row["option_b_effects"], row["id"])
    return rows


def parse_effects(raw: str, event_id: str) -> list[tuple[str, str | tuple[str, int]]]:
    parsed: list[tuple[str, str | tuple[str, int]]] = []
    for token in raw.split("|"):
        if "=" not in token:
            raise SystemExit(f"Malformed effect in event {event_id}: {token}")
        key, value = token.split("=", 1)
        if key == "modifier":
            try:
                name, duration_text = value.split(":", 1)
                duration = int(duration_text)
            except ValueError as exc:
                raise SystemExit(f"Malformed modifier effect in event {event_id}: {token}") from exc
            if name not in MODIFIERS or name == "eu4_2k_generic_event_cooldown" or duration <= 0:
                raise SystemExit(f"Invalid modifier effect in event {event_id}: {token}")
            parsed.append((key, (name, duration)))
        elif key in DIRECT_EFFECTS:
            try:
                float(value)
            except ValueError as exc:
                raise SystemExit(f"Non-numeric effect in event {event_id}: {token}") from exc
            parsed.append((key, value))
        else:
            raise SystemExit(f"Unknown effect key in event {event_id}: {key}")
    return parsed


def effect_lines(raw: str, event_id: str) -> list[str]:
    lines: list[str] = []
    for key, value in parse_effects(raw, event_id):
        if key == "modifier":
            name, duration = value  # type: ignore[misc]
            lines.extend([
                "\t\tadd_country_modifier = {",
                f"\t\t\tname = {name}",
                f"\t\t\tduration = {duration}",
                "\t\t}",
            ])
        else:
            lines.append(f"\t\t{DIRECT_EFFECTS[key]} = {value}")
    lines.extend([
        "\t\tadd_country_modifier = {",
        "\t\t\tname = eu4_2k_generic_event_cooldown",
        "\t\t\tduration = 365",
        "\t\t}",
    ])
    return lines


def event_text(rows: list[dict[str, str]]) -> str:
    lines = ["# Generated by scripts/generate_generic_events.py", "namespace = eu4_2k_generic", ""]
    for row in rows:
        event_id = row["id"]
        lines.extend([
            "country_event = {",
            f"\tid = eu4_2k_generic.{event_id}",
            f"\ttitle = eu4_2k_generic.{event_id}.t",
            f"\tdesc = eu4_2k_generic.{event_id}.d",
            f"\tpicture = {row['picture']}",
            "\tis_triggered_only = yes",
            "\ttrigger = {",
            "\t\tis_year = 2000",
            "\t\tNOT = { has_country_modifier = eu4_2k_generic_event_cooldown }",
            "\t}",
            "\toption = {",
            f"\t\tname = eu4_2k_generic.{event_id}.a",
            f"\t\tai_chance = {{ factor = {row['option_a_ai']} }}",
            *effect_lines(row["option_a_effects"], event_id),
            "\t}",
            "\toption = {",
            f"\t\tname = eu4_2k_generic.{event_id}.b",
            f"\t\tai_chance = {{ factor = {row['option_b_ai']} }}",
            *effect_lines(row["option_b_effects"], event_id),
            "\t}",
            "}",
            "",
        ])
    return "\n".join(lines)


def on_action_text(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Generated by scripts/generate_generic_events.py",
        "# A 50 percent yearly roll gives a player roughly one modern event every two years.",
        "on_yearly_pulse_5 = {",
        "\trandom_events = {",
    ]
    lines.extend(f"\t\t100 = eu4_2k_generic.{row['id']}" for row in rows)
    lines.extend(["\t\t4000 = 0", "\t}", "}", ""])
    return "\n".join(lines)


def modifier_text() -> str:
    lines = ["# Generated by scripts/generate_generic_events.py", ""]
    for name, (_, _, effects) in MODIFIERS.items():
        if not effects:
            lines.extend([f"{name} = {{ }}", ""])
            continue
        lines.append(f"{name} = {{")
        lines.extend(f"\t{key} = {value}" for key, value in effects)
        lines.extend(["}", ""])
    return "\n".join(lines)


def quote_loc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def localization_text(rows: list[dict[str, str]]) -> str:
    lines = ["l_english:"]
    for row in rows:
        event_id = row["id"]
        lines.extend([
            f' eu4_2k_generic.{event_id}.t:0 "{quote_loc(row["title"])}"',
            f' eu4_2k_generic.{event_id}.d:0 "{quote_loc(row["description"])}"',
            f' eu4_2k_generic.{event_id}.a:0 "{quote_loc(row["option_a"])}"',
            f' eu4_2k_generic.{event_id}.b:0 "{quote_loc(row["option_b"])}"',
        ])
    for name, (title, desc, _) in MODIFIERS.items():
        lines.extend([
            f' {name}:0 "{quote_loc(title)}"',
            f' {name}_desc:0 "{quote_loc(desc)}"',
        ])
    return "\n".join(lines) + "\n"


def expected(rows: list[dict[str, str]]) -> dict[Path, tuple[str, str]]:
    return {
        EVENT_OUTPUT: (event_text(rows), "cp1252"),
        ON_ACTION_OUTPUT: (on_action_text(rows), "cp1252"),
        MODIFIER_OUTPUT: (modifier_text(), "cp1252"),
        LOC_OUTPUT: (localization_text(rows), "utf-8-sig"),
    }


def generate(rows: list[dict[str, str]]) -> None:
    for path, (content, encoding) in expected(rows).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding, newline="\n")


def check(rows: list[dict[str, str]]) -> None:
    errors: list[str] = []
    for path, (content, encoding) in expected(rows).items():
        if not path.exists():
            errors.append(f"missing: {path.relative_to(ROOT)}")
        elif path.read_text(encoding=encoding) != content:
            errors.append(f"stale: {path.relative_to(ROOT)}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("generate",), default="generate")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = load_rows()
    if args.check:
        check(rows)
        print("Validated 40 modern generic events across eight categories.")
    else:
        generate(rows)
        print("Generated 40 modern generic events across eight categories.")


if __name__ == "__main__":
    main()
