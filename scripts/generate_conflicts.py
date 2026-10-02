#!/usr/bin/env python3
"""Generate and validate the conflicts active on the 2000.1.1 bookmark.

This stage owns the war history, the scripted war endings, the conflict
province and country modifiers, the conflict-faction flag assets, and their
localisation. Territory, tags, and diplomacy remain in the canonical country,
province, and diplomacy datasets.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw

import generate_country_snapshot as countries


ROOT = countries.ROOT
MOD = countries.MOD
DATA = ROOT / "data" / "wars_2000.csv"
WAR_OUTPUT_DIR = MOD / "history" / "wars"
EVENT_OUTPUT = MOD / "events" / "eu4_2k_conflict_events.txt"
ON_ACTION_OUTPUT = MOD / "common" / "on_actions" / "zz_eu4_2k_conflicts.txt"
EVENT_MODIFIER_OUTPUT = MOD / "common" / "event_modifiers" / "eu4_2k_conflict_modifiers.txt"
TRIGGERED_MODIFIER_OUTPUT = (
    MOD / "common" / "province_triggered_modifiers" / "eu4_2k_conflict_modifiers.txt"
)
OPINION_OUTPUT = MOD / "common" / "opinion_modifiers" / "eu4_2k_conflict_opinions.txt"
LOCALISATION_OUTPUT = MOD / "localisation" / "eu4_2k_conflicts_l_english.yml"
FLAG_OUTPUT_DIR = countries.ASSETS / "flags"

FIELDS = [
    "war_id", "name", "start_date", "attackers", "defenders", "war_goal",
    "casus_belli", "target_province", "source", "verification_notes",
]

START = date(2000, 1, 1)
LAST_SCRIPTED_DATE = date(2010, 12, 31)
NAMESPACE = "eu4_2k_conflicts"

WAR_GOALS = {
    # war goal type: (casus belli, needs a target province)
    "take_core": ("cb_core", True),
    "superiority_insult_mutual": ("cb_insult", False),
}

# Horizontal bands (first row, end row, RGB) on a 128x128 EU4 flag. The two
# rebel-movement designs are placeholders until verified flags are sourced.
GREEN = (0, 122, 61)
WHITE = (255, 255, 255)
FLAG_BANDS = {
    # The plain white Taliban flag used in 1996-1997; the later shahada needs
    # Arabic text shaping that the asset pipeline does not provide.
    "AFG": ((0, 128, WHITE),),
    # Islamic State of Afghanistan tricolour without its central emblem.
    "ISA": ((0, 43, GREEN), (43, 85, WHITE), (85, 128, (0, 0, 0))),
    # Ichkeria: green field with white, red, and white stripes near the base.
    "ICK": (
        (0, 80, GREEN), (80, 88, WHITE), (88, 104, (206, 17, 38)),
        (104, 112, WHITE), (112, 128, GREEN),
    ),
    "RCD": (
        (0, 128, (0, 127, 255)), (48, 80, (247, 209, 23)), (54, 74, (206, 17, 38)),
    ),
    "FLC": ((0, 128, (46, 150, 96)), (52, 76, WHITE)),
}

# Event modifiers applied by the scripted war endings.
EVENT_MODIFIERS = {
    "eu4_2k_temporary_security_zone": {
        "name": "Temporary Security Zone",
        "desc": "United Nations peacekeepers separate the armies along a demilitarized border zone while a boundary commission settles the frontier.",
        "modifiers": ("land_maintenance_modifier = 0.1", "global_unrest = -1"),
    },
    "eu4_2k_defied_mediation": {
        "name": "Defied International Mediation",
        "desc": "We rejected an internationally mediated ceasefire and continued the war.",
        "modifiers": ("diplomatic_reputation = -1", "stability_cost_modifier = 0.1"),
    },
}

# Province triggered modifiers. Each is attached once at the start by the
# listed country and switches itself on or off through its trigger.
TRIGGERED_MODIFIERS = {
    "eu4_2k_unmik_administration": {
        "attach_tag": "YUG",
        "provinces": (1766,),
        "trigger": (
            "NOT = { has_global_flag = eu4_2k_unmik_mandate_ended }",
            "owner = { OR = { tag = YUG tag = SER } }",
        ),
        "modifiers": (
            "local_tax_modifier = -1",
            "local_production_efficiency = -1",
            "local_manpower_modifier = -1",
            "local_unrest = -5",
        ),
        "name": "UN Interim Administration (UNSCR 1244)",
        "desc": "Under Security Council Resolution 1244, Kosovo remains formally part of Yugoslavia but is governed by the United Nations Interim Administration Mission and secured by the NATO-led KFOR. Belgrade collects no revenue or recruits here until the mandate ends.",
    },
    "eu4_2k_northern_alliance_stronghold": {
        "attach_tag": "ISA",
        "provinces": (452, 2227),
        "trigger": ("owner = { tag = ISA }",),
        "modifiers": (
            "fort_level = 1",
            "local_defensiveness = 0.5",
            "local_hostile_attrition = 2",
        ),
        "name": "Northern Alliance Mountain Strongholds",
        "desc": "The valleys of the Hindu Kush and Badakhshan give the United Front defensible positions that Taliban offensives have repeatedly failed to break.",
    },
    "eu4_2k_chechen_insurgency": {
        "attach_tag": "RUS",
        "provinces": (2198,),
        "trigger": (
            "has_global_flag = eu4_2k_chechen_insurgency_active",
            "owner = { tag = RUS }",
        ),
        "modifiers": (
            "local_unrest = 4",
            "local_tax_modifier = -0.5",
            "local_manpower_modifier = -0.5",
            "local_hostile_attrition = 1",
        ),
        "name": "Chechen Insurgency",
        "desc": "Separatist and Islamist fighters continue a guerrilla campaign from the mountains of southern Chechnya under a federal counter-terrorism regime.",
    },
}

# Where each attached triggered modifier must be held at the start.
TRIGGERED_MODIFIER_START_OWNERS = {
    "eu4_2k_unmik_administration": "YUG",
    "eu4_2k_northern_alliance_stronghold": "ISA",
    "eu4_2k_chechen_insurgency": "ICK",
}

OPINION_MODIFIERS = {
    "eu4_2k_rejected_transition": (-50, "Rejected the Transitional Government"),
    "eu4_2k_chechen_settlement": (25, "Negotiated Chechen Settlement"),
}

# Scripted endings. "date" events are scheduled from the 2000 bookmark,
# "mtth_days" events are polled, and the rest are fired by other events.
EVENTS = (
    {
        "id": 1, "tags": ("ETH",), "date": "2000.6.18",
        "picture": "DIPLOMACY_eventPicture",
        "title": "The Algiers Ceasefire",
        "description": "Two years of trench warfare along the Badme front have cost tens of thousands of lives. Mediators from the Organization of African Unity have produced a cessation-of-hostilities agreement, with United Nations peacekeepers to patrol a temporary security zone between the two armies.",
        "trigger": ("war_with = ERT",),
        "options": (
            {
                "text": "Sign the cessation of hostilities", "ai": 90,
                "effects": (
                    "white_peace = ERT",
                    "add_country_modifier = { name = eu4_2k_temporary_security_zone duration = 3650 }",
                    "ERT = { add_country_modifier = { name = eu4_2k_temporary_security_zone duration = 3650 } country_event = { id = eu4_2k_conflicts.2 } }",
                    "set_global_flag = eu4_2k_algiers_ceasefire",
                ),
            },
            {
                "text": "Continue the offensive", "ai": 10,
                "effects": (
                    "add_prestige = 5",
                    "add_war_exhaustion = 2",
                    "add_country_modifier = { name = eu4_2k_defied_mediation duration = 1825 }",
                    "set_global_flag = eu4_2k_algiers_ceasefire_rejected",
                ),
            },
        ),
    },
    {
        "id": 2, "tags": ("ERT",),
        "picture": "DIPLOMACY_eventPicture",
        "title": "The Algiers Ceasefire",
        "description": "Ethiopia has signed the cessation of hostilities. United Nations peacekeepers will patrol the temporary security zone, and a boundary commission is to settle the disputed border.",
        "trigger": (),
        "options": (
            {"text": "Accept the ceasefire", "ai": 100, "effects": ()},
        ),
    },
    {
        "id": 10, "tags": ("RUS",), "mtth_days": 15,
        "picture": "SIEGE_eventPicture",
        "title": "The Fall of Grozny",
        "description": "Federal forces hold Grozny after a long siege that left much of the city in ruins. Organized separatist resistance has been driven into the southern mountains, but an insurgency is likely to continue for years.",
        "trigger": (
            "NOT = { has_global_flag = eu4_2k_grozny_resolved }",
            "OR = { AND = { exists = ICK war_with = ICK 2198 = { controlled_by = ROOT } } AND = { NOT = { exists = ICK } owns = 2198 } }",
        ),
        "options": (
            {
                "text": "Restore federal control", "ai": 95,
                "trigger": ("exists = ICK",),
                "effects": (
                    "white_peace = ICK",
                    "inherit = ICK",
                    "add_prestige = 10",
                    "set_global_flag = eu4_2k_chechen_insurgency_active",
                    "set_global_flag = eu4_2k_grozny_resolved",
                ),
            },
            {
                "text": "Seek a negotiated settlement", "ai": 5,
                "trigger": ("exists = ICK",),
                "effects": (
                    "white_peace = ICK",
                    "add_prestige = -10",
                    "ICK = { add_opinion = { who = ROOT modifier = eu4_2k_chechen_settlement } }",
                    "add_opinion = { who = ICK modifier = eu4_2k_chechen_settlement }",
                    "set_global_flag = eu4_2k_ichkeria_negotiated",
                    "set_global_flag = eu4_2k_grozny_resolved",
                ),
            },
            {
                "text": "Begin counter-terrorism operations", "ai": 100,
                "trigger": ("NOT = { exists = ICK }",),
                "effects": (
                    "set_global_flag = eu4_2k_chechen_insurgency_active",
                    "set_global_flag = eu4_2k_grozny_resolved",
                ),
            },
        ),
    },
    {
        "id": 11, "tags": ("RUS",), "date": "2009.4.16",
        "picture": "MILITARY_CAMP_eventPicture",
        "title": "End of the Counter-Terrorism Operation",
        "description": "Moscow has formally lifted the counter-terrorism regime in Chechnya. The republic's own authorities now carry out security operations, although attacks continue across the North Caucasus.",
        "trigger": ("has_global_flag = eu4_2k_chechen_insurgency_active",),
        "options": (
            {
                "text": "Hand security to the republic's authorities", "ai": 100,
                "effects": ("clr_global_flag = eu4_2k_chechen_insurgency_active",),
            },
        ),
    },
    {
        "id": 20, "tags": ("DRC",), "date": "2002.7.30",
        "picture": "DIPLOMACY_eventPicture",
        "title": "The Pretoria Agreement",
        "description": "Under South African mediation, Kinshasa and Kigali have agreed that Rwandan forces will withdraw from Congolese territory in exchange for action against the armed groups that threaten Rwanda from the east.",
        "trigger": ("war_with = RWA",),
        "options": (
            {
                "text": "Sign the agreement", "ai": 95,
                "effects": (
                    "white_peace = RWA",
                    "add_stability = 1",
                    "set_global_flag = eu4_2k_pretoria_agreement",
                ),
            },
            {
                "text": "Fight on to expel the invaders", "ai": 5,
                "effects": ("add_prestige = 5", "add_war_exhaustion = 2", "add_stability = -1"),
            },
        ),
    },
    {
        "id": 21, "tags": ("DRC",), "date": "2002.9.6",
        "picture": "DIPLOMACY_eventPicture",
        "title": "The Luanda Agreement",
        "description": "Angola has brokered an agreement for the withdrawal of Ugandan forces from the northeast and the creation of a pacification commission for Ituri.",
        "trigger": ("war_with = UGA",),
        "options": (
            {
                "text": "Sign the agreement", "ai": 95,
                "effects": (
                    "white_peace = UGA",
                    "add_stability = 1",
                    "set_global_flag = eu4_2k_luanda_agreement",
                ),
            },
            {
                "text": "Fight on to expel the invaders", "ai": 5,
                "effects": ("add_prestige = 5", "add_war_exhaustion = 2", "add_stability = -1"),
            },
        ),
    },
    {
        "id": 22, "tags": ("DRC",), "date": "2003.6.30",
        "picture": "DIPLOMACY_eventPicture",
        "title": "The Transitional Government",
        "description": "The Global and All-Inclusive Agreement provides for a transitional government in which the president shares power with four vice-presidents drawn from the government, the main rebel movements, and the unarmed opposition. The rebel administrations are to be reunited with the state and their fighters merged into a new national army.",
        "trigger": (
            "OR = { AND = { exists = RCD NOT = { war_with = RCD } } AND = { exists = FLC NOT = { war_with = FLC } } }",
        ),
        "options": (
            {
                "text": "Form the transitional government", "ai": 95,
                "effects": (
                    "if = { limit = { exists = RCD NOT = { war_with = RCD } } RCD = { country_event = { id = eu4_2k_conflicts.23 } } }",
                    "if = { limit = { exists = FLC NOT = { war_with = FLC } } FLC = { country_event = { id = eu4_2k_conflicts.23 } } }",
                    "set_global_flag = eu4_2k_congo_transitional_government",
                ),
            },
            {
                "text": "Govern without the rebel movements", "ai": 5,
                "effects": ("add_stability = -1", "add_prestige = 5"),
            },
        ),
    },
    {
        "id": 23, "tags": ("RCD", "FLC"),
        "picture": "DIPLOMACY_eventPicture",
        "title": "Joining the Transitional Government",
        "description": "Kinshasa invites our movement to take its seats in the transitional government and to merge our forces into a new national army. Our foreign backers have already committed to withdraw.",
        "trigger": ("exists = DRC",),
        "options": (
            {
                "text": "Join the transitional government", "ai": 95,
                "effects": ("FROM = { inherit = ROOT }",),
            },
            {
                "text": "Keep our separate administration", "ai": 5,
                "effects": (
                    "FROM = { add_opinion = { who = ROOT modifier = eu4_2k_rejected_transition } }",
                    "add_prestige = -10",
                ),
            },
        ),
    },
)


def parse_date(value: str) -> date:
    year, month, day = (int(part) for part in value.split("."))
    return date(year, month, day)


def loc_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def load_rows() -> list[dict[str, str]]:
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise RuntimeError("War data columns do not match the canonical schema")
        return list(reader)


def participants(row: dict[str, str], side: str) -> list[str]:
    return [tag for tag in row[side].split("|") if tag]


def war_history(row: dict[str, str]) -> str:
    _, needs_province = WAR_GOALS[row["war_goal"]]
    lines = [
        "# Generated by scripts/generate_conflicts.py from data/wars_2000.csv",
        f'name = "{row["name"]}"',
        "",
        "war_goal = {",
        f"\ttype = {row['war_goal']}",
        f"\tcasus_belli = {row['casus_belli']}",
    ]
    if needs_province:
        lines.append(f"\tprovince = {row['target_province']}")
    lines.extend(["}", "", f"{row['start_date']} = {{"])
    lines.extend(f"\tadd_attacker = {tag}" for tag in participants(row, "attackers"))
    lines.extend(f"\tadd_defender = {tag}" for tag in participants(row, "defenders"))
    lines.extend(["}", ""])
    return "\n".join(lines)


def event_tags(event: dict) -> tuple[str, ...]:
    return tuple(event["tags"])


def events_text() -> str:
    lines = ["# Generated by scripts/generate_conflicts.py", f"namespace = {NAMESPACE}", ""]
    for event in EVENTS:
        event_id = event["id"]
        lines.extend([
            "country_event = {",
            f"\tid = {NAMESPACE}.{event_id}",
            f"\ttitle = {NAMESPACE}.{event_id}.t",
            f"\tdesc = {NAMESPACE}.{event_id}.d",
            f"\tpicture = {event['picture']}",
        ])
        if "mtth_days" in event:
            lines.extend([
                "\tfire_only_once = yes",
                f"\tmean_time_to_happen = {{ days = {event['mtth_days']} }}",
            ])
        else:
            lines.append("\tis_triggered_only = yes")
        lines.extend([
            "\ttrigger = {",
            "\t\tOR = { " + " ".join(f"tag = {tag}" for tag in event_tags(event)) + " }",
        ])
        lines.extend(f"\t\t{trigger}" for trigger in event["trigger"])
        lines.append("\t}")
        for index, option in enumerate(event["options"]):
            suffix = chr(ord("a") + index)
            lines.extend(["\toption = {", f"\t\tname = {NAMESPACE}.{event_id}.{suffix}"])
            if option.get("trigger"):
                lines.append("\t\ttrigger = { " + " ".join(option["trigger"]) + " }")
            lines.append(f"\t\tai_chance = {{ factor = {option['ai']} }}")
            lines.extend(f"\t\t{effect}" for effect in option["effects"])
            lines.append("\t}")
        lines.extend(["}", ""])
    return "\n".join(lines)


def schedule_text() -> str:
    actions: dict[str, list[str]] = {}
    for event in EVENTS:
        if "date" not in event:
            continue
        delay = (parse_date(event["date"]) - START).days
        for tag in event_tags(event):
            actions.setdefault(tag, []).append(
                f"country_event = {{ id = {NAMESPACE}.{event['id']} days = {delay} }}"
            )
    for name, modifier in TRIGGERED_MODIFIERS.items():
        for province in modifier["provinces"]:
            actions.setdefault(modifier["attach_tag"], []).append(
                f"{province} = {{ add_province_triggered_modifier = {name} }}"
            )
    lines = [
        "# Generated by scripts/generate_conflicts.py",
        "# Schedule scripted war endings and attach conflict province modifiers once.",
        "on_startup = {",
        "\tif = {",
        "\t\tlimit = {",
        "\t\t\tis_year = 2000",
        "\t\t\tNOT = { is_year = 2001 }",
        "\t\t\tNOT = { has_country_flag = eu4_2k_conflicts_scheduled }",
        "\t\t}",
    ]
    for tag, tag_actions in sorted(actions.items()):
        lines.extend(["\t\tif = {", f"\t\t\tlimit = {{ tag = {tag} }}"])
        lines.extend(f"\t\t\t{action}" for action in tag_actions)
        lines.append("\t\t}")
    lines.extend([
        "\t\tset_country_flag = eu4_2k_conflicts_scheduled",
        "\t}",
        "}",
        "",
    ])
    return "\n".join(lines)


def event_modifiers_text() -> str:
    lines = ["# Generated by scripts/generate_conflicts.py", ""]
    for name, modifier in EVENT_MODIFIERS.items():
        lines.append(f"{name} = {{")
        lines.extend(f"\t{line}" for line in modifier["modifiers"])
        lines.extend(["}", ""])
    return "\n".join(lines)


def triggered_modifiers_text() -> str:
    lines = ["# Generated by scripts/generate_conflicts.py", ""]
    for name, modifier in TRIGGERED_MODIFIERS.items():
        provinces = " ".join(f"province_id = {province}" for province in modifier["provinces"])
        lines.extend([
            f"{name} = {{",
            f"\tpotential = {{ OR = {{ {provinces} }} }}",
            "\ttrigger = {",
        ])
        lines.extend(f"\t\t{trigger}" for trigger in modifier["trigger"])
        lines.append("\t}")
        lines.extend(f"\t{line}" for line in modifier["modifiers"])
        lines.extend(["\ton_activation = { }", "\ton_deactivation = { }", "}", ""])
    return "\n".join(lines)


def opinion_modifiers_text() -> str:
    lines = ["# Generated by scripts/generate_conflicts.py"]
    for name, (value, _) in OPINION_MODIFIERS.items():
        lines.append(f"{name} = {{ opinion = {value} }}")
    return "\n".join(lines) + "\n"


def localisation_text() -> str:
    lines = ["l_english:"]
    for event in EVENTS:
        event_id = event["id"]
        lines.extend([
            f' {NAMESPACE}.{event_id}.t:0 "{loc_text(event["title"])}"',
            f' {NAMESPACE}.{event_id}.d:0 "{loc_text(event["description"])}"',
        ])
        for index, option in enumerate(event["options"]):
            suffix = chr(ord("a") + index)
            lines.append(f' {NAMESPACE}.{event_id}.{suffix}:0 "{loc_text(option["text"])}"')
    for name, modifier in [*EVENT_MODIFIERS.items(), *TRIGGERED_MODIFIERS.items()]:
        lines.extend([
            f' {name}:0 "{loc_text(modifier["name"])}"',
            f' desc_{name}:0 "{loc_text(modifier["desc"])}"',
        ])
    for name, (_, label) in OPINION_MODIFIERS.items():
        lines.append(f' {name}:0 "{loc_text(label)}"')
    lines.append(
        ' eu4_2k_unmik_mandate_ends_tt:0 "The UN Interim Administration in Kosovo ends."'
    )
    return "\n".join(lines) + "\n"


def flag_bytes(tag: str) -> bytes:
    image = Image.new("RGB", (128, 128), WHITE)
    draw = ImageDraw.Draw(image)
    for top, bottom, color in FLAG_BANDS[tag]:
        draw.rectangle((0, top, 127, bottom - 1), fill=color)
    buffer = io.BytesIO()
    image.save(buffer, format="TGA", compression="tga_rle")
    return buffer.getvalue()


def outputs(rows: Sequence[dict[str, str]]) -> dict[Path, bytes]:
    result: dict[Path, bytes] = {
        WAR_OUTPUT_DIR / f"{row['war_id']}.txt": war_history(row).encode("cp1252")
        for row in rows
    }
    result.update({
        EVENT_OUTPUT: events_text().encode("cp1252"),
        ON_ACTION_OUTPUT: schedule_text().encode("cp1252"),
        EVENT_MODIFIER_OUTPUT: event_modifiers_text().encode("cp1252"),
        TRIGGERED_MODIFIER_OUTPUT: triggered_modifiers_text().encode("cp1252"),
        OPINION_OUTPUT: opinion_modifiers_text().encode("cp1252"),
        LOCALISATION_OUTPUT: ("\ufeff" + localisation_text()).encode("utf-8"),
    })
    for tag in FLAG_BANDS:
        result[FLAG_OUTPUT_DIR / f"{tag}.tga"] = flag_bytes(tag)
    return result


def validate(rows: Sequence[dict[str, str]], check_outputs: bool = True) -> None:
    errors: list[str] = []
    manifest = {row["tag"]: row for row in countries.load_manifest()}
    active = {tag for tag, row in manifest.items() if row["active_2000"] == "yes"}
    with countries.PROVINCE_DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        provinces = {int(row["province_id"]): row for row in csv.DictReader(handle)}

    war_ids: set[str] = set()
    at_war: set[str] = set()
    for row in rows:
        war_id = row["war_id"]
        if war_id in war_ids:
            errors.append(f"duplicate war id: {war_id}")
        war_ids.add(war_id)
        attackers, defenders = participants(row, "attackers"), participants(row, "defenders")
        if not attackers or not defenders:
            errors.append(f"{war_id}: both sides need a war leader")
            continue
        if set(attackers) & set(defenders):
            errors.append(f"{war_id}: a country is on both sides")
        for tag in [*attackers, *defenders]:
            if tag not in active:
                errors.append(f"{war_id}: inactive participant {tag}")
        at_war.update(attackers + defenders)
        try:
            if parse_date(row["start_date"]) >= START:
                errors.append(f"{war_id}: war must start before 2000.1.1")
        except ValueError:
            errors.append(f"{war_id}: invalid start date")
        goal = WAR_GOALS.get(row["war_goal"])
        if not goal or goal[0] != row["casus_belli"]:
            errors.append(f"{war_id}: unsupported war goal or casus belli")
            continue
        if goal[1]:
            province = provinces.get(int(row["target_province"] or 0))
            if not province or province["owner"] != defenders[0]:
                errors.append(f"{war_id}: target province is not held by the defending leader")
            elif attackers[0] not in province["core"].split("|"):
                errors.append(f"{war_id}: attacking leader has no core on the target province")
        elif row["target_province"]:
            errors.append(f"{war_id}: war goal does not take a target province")
    for tag in sorted(countries.CONFLICT_ENTITIES - at_war):
        errors.append(f"conflict entity {tag} is not at war at the start")

    event_ids: set[int] = set()
    for event in EVENTS:
        if event["id"] in event_ids:
            errors.append(f"duplicate event id: {event['id']}")
        event_ids.add(event["id"])
        for tag in event_tags(event):
            if tag not in active:
                errors.append(f"event {event['id']}: inactive country {tag}")
        if "date" in event and not START < parse_date(event["date"]) <= LAST_SCRIPTED_DATE:
            errors.append(f"event {event['id']}: date outside the scripted horizon")
        if any(option["ai"] <= 0 for option in event["options"]):
            errors.append(f"event {event['id']}: every option needs a positive AI weight")

    for name, modifier in TRIGGERED_MODIFIERS.items():
        expected_owner = TRIGGERED_MODIFIER_START_OWNERS[name]
        for province in modifier["provinces"]:
            if provinces.get(province, {}).get("owner") != expected_owner:
                errors.append(f"{name}: province {province} is not held by {expected_owner}")

    for tag in FLAG_BANDS:
        if manifest.get(tag, {}).get("flag_source") != f"mod:flags/{tag}.tga":
            errors.append(f"{tag}: country flag_source must be mod:flags/{tag}.tga")

    if check_outputs:
        expected = outputs(rows)
        for path, content in expected.items():
            if not path.exists() or path.read_bytes() != content:
                errors.append(f"missing or stale generated output: {path.relative_to(ROOT)}")
        if WAR_OUTPUT_DIR.exists():
            for path in WAR_OUTPUT_DIR.glob("*.txt"):
                if path not in expected:
                    errors.append(f"unexpected war history file: {path.name}")
    if errors:
        raise RuntimeError("Conflict validation failed:\n- " + "\n- ".join(errors[:100]))


def write_outputs(rows: Sequence[dict[str, str]]) -> None:
    expected = outputs(rows)
    if WAR_OUTPUT_DIR.exists():
        for path in WAR_OUTPUT_DIR.glob("*.txt"):
            if path not in expected:
                path.unlink()
    for path, content in expected.items():
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
    print(
        f"{action} {len(rows)} wars active at 2000.1.1, {len(EVENTS)} scripted ending events, "
        f"{len(TRIGGERED_MODIFIERS)} conflict province modifiers, and {len(FLAG_BANDS)} flags."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
