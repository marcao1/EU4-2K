#!/usr/bin/env python3
"""Generate a clean, undated EU4 province snapshot effective on 2000.1.1."""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import generate_country_snapshot as countries


ROOT = countries.ROOT
MOD = countries.MOD
ET = countries.ET
DATA = countries.PROVINCE_DATA
START_NUMBER = countries.START_NUMBER

FIELDS = [
    "province_id", "name", "owner", "controller", "core", "culture", "religion",
    "capital", "trade_goods", "base_tax", "base_production", "base_manpower",
    "is_city", "hre", "center_of_trade", "native_size", "native_ferocity",
    "native_hostileness", "source", "verification_notes",
]

SCALAR_KEYS = {
    "owner", "controller", "culture", "capital", "trade_goods", "base_tax",
    "base_production", "base_manpower", "is_city", "hre", "center_of_trade",
    "native_size", "native_ferocity", "native_hostileness",
}

TRADE_GOOD_FALLBACKS = {
    "oil": "coal",
    "cars": "iron",
    "electronics": "glass",
    "aluminum": "copper",
    "uranium": "copper",
}

# ET's modern history contains several 100-216 development metropolitan
# provinces. EU4's economic and force-limit formulas make those values
# overpowering, so values above 30 use a diminishing-return curve. Explicit
# regional-capital floors repair the most compressed Balkan starting capitals.
DEVELOPMENT_SOFT_CAP = 30
DEVELOPMENT_EXPONENT = 0.65
DEVELOPMENT_HARD_CAP = 50
MINIMUM_OWNED_PROVINCE_DEVELOPMENT = 3

# Exact national totals for the major-country balance pass. These targets use
# average development only as a guardrail; the allocator preserves the existing
# urban/rural ordering and each province's tax/production/manpower proportions.
NATIONAL_DEVELOPMENT_TARGETS = {
    "USA": 3500,
    "CHN": 2850,
    "INI": 2550,
    "RUS": 1500,
    "GER": 1400,
    "JAP": 1125,
    "FR2": 1150,
    "GBR": 1100,
    "ITA": 950,
    "BRZ": 915,
    "IDN": 920,
    "MEX": 845,
}
MINIMUM_NATIONAL_DEVELOPMENT = 15
MAXIMUM_NON_TARGET_NATIONAL_DEVELOPMENT = 1500
BALKAN_CAPITAL_FLOORS = {
    4750: 25,  # Tirana
    3002: 28,  # Sarajevo
    1765: 32,  # Sofia
    131: 30,   # Zagreb
    146: 38,   # Athens
    3001: 25,  # Skopje
    4531: 38,  # Bucharest
    1769: 26,  # Slovenia's starting capital province
    4239: 32,  # Belgrade
}

MODERN_CENTER_OF_TRADE_OVERRIDES = {
    # Global financial, shipping, and commercial hubs.
    97: 3, 183: 3, 236: 3, 397: 3, 667: 3, 965: 3, 1028: 3,
    1816: 3, 1822: 3, 1876: 3, 3005: 3, 4815: 3,
    # Major national and regional hubs.
    50: 2, 92: 2, 118: 2, 151: 2, 217: 2, 295: 2, 735: 2,
    868: 2, 953: 2, 1090: 2, 2670: 2, 4637: 2, 4903: 2,
    # Former ET level-three centers retained as important regional markets.
    101: 2, 112: 2, 568: 2, 4457: 2,
}


@dataclass
class ProvinceState:
    values: dict[str, str] = field(default_factory=dict)
    cores: set[str] = field(default_factory=set)
    religion: str = ""
    last_conventional_religion: str = ""

    def apply(self, entries: Sequence[countries.Entry]) -> None:
        for key, value in entries:
            if not key or not isinstance(value, str):
                continue
            if key in SCALAR_KEYS:
                self.values[key] = value
            elif key == "religion":
                self.religion = value
                if value not in countries.REMOVED_RELIGIONS:
                    self.last_conventional_religion = value
            elif key == "add_core":
                self.cores.add(value)
            elif key == "remove_core":
                self.cores.discard(value)


def effective_state(path: Path) -> ProvinceState:
    state = ProvinceState()
    dated: list[tuple[int, list[countries.Entry]]] = []
    for key, value in countries.parse_file(path):
        number = countries.date_number(key or "")
        if number is not None and isinstance(value, list):
            if number <= START_NUMBER:
                dated.append((number, value))
        elif key is not None:
            state.apply([(key, value)])
    for _, entries in sorted(dated, key=lambda item: item[0]):
        state.apply(entries)
    return state


def province_sources() -> dict[int, Path]:
    result: dict[int, Path] = {}
    for path in sorted((ET / "history" / "provinces").glob("*.txt")):
        match = re.match(r"^(\d+)\s*-\s*", path.name)
        if match:
            result[int(match.group(1))] = path
    return result


def vanilla_religions(game: Path) -> set[str]:
    result: set[str] = set()
    for path in (game / "common" / "religions").glob("*.txt"):
        result.update(countries.collect_religions(path))
    return result


def vanilla_trade_goods(game: Path) -> set[str]:
    result: set[str] = {"unknown"}
    for path in (game / "common" / "tradegoods").glob("*.txt"):
        for key, value in countries.parse_file(path):
            if key and isinstance(value, list) and any(child == "color" for child, _ in value):
                result.add(key)
    return result


def normalized_religion(state: ProvinceState, vanilla: set[str]) -> str:
    candidate = state.last_conventional_religion or state.religion
    candidate = countries.RELIGION_FALLBACKS.get(candidate, candidate)
    return candidate if candidate in vanilla else "catholic"


def allocate_development(total: int, values: Sequence[float]) -> tuple[int, int, int]:
    """Distribute an integer total while preserving the original proportions."""
    source_total = sum(values)
    if source_total <= 0:
        return (total, 0, 0)
    raw = [total * value / source_total for value in values]
    result = [math.floor(value) for value in raw]
    remainder_order = sorted(
        range(3), key=lambda index: (raw[index] - result[index], -index), reverse=True
    )
    for index in remainder_order[: total - sum(result)]:
        result[index] += 1
    return tuple(result)  # type: ignore[return-value]


def balanced_development(row: dict[str, str]) -> tuple[int, int, int]:
    values = tuple(
        float(row[field])
        for field in ("base_tax", "base_production", "base_manpower")
    )
    original_total = sum(values)
    if original_total <= DEVELOPMENT_SOFT_CAP:
        target = round(original_total)
    else:
        target = round(
            DEVELOPMENT_SOFT_CAP
            + (original_total - DEVELOPMENT_SOFT_CAP) ** DEVELOPMENT_EXPONENT
        )
    target = max(target, BALKAN_CAPITAL_FLOORS.get(int(row["province_id"]), 0))
    target = min(target, DEVELOPMENT_HARD_CAP)
    return allocate_development(target, values)


def apply_development_balance(row: dict[str, str]) -> None:
    tax, production, manpower = balanced_development(row)
    row["base_tax"] = str(tax)
    row["base_production"] = str(production)
    row["base_manpower"] = str(manpower)
    row["verification_notes"] = (
        "Effective ET state on 2000.1.1; EU4 2K balanced development model."
    )


def national_development_target(tag: str, current_total: int) -> int:
    """Return the explicit major target or keep other states within tier bounds."""
    if tag in NATIONAL_DEVELOPMENT_TARGETS:
        return NATIONAL_DEVELOPMENT_TARGETS[tag]
    return min(
        max(current_total, MINIMUM_NATIONAL_DEVELOPMENT),
        MAXIMUM_NON_TARGET_NATIONAL_DEVELOPMENT,
    )


def constrained_province_totals(
    rows: Sequence[dict[str, str]], target_total: int
) -> list[int]:
    """Apportion an exact country total with province floors and a hard cap."""
    weights = [
        sum(float(row[field]) for field in (
            "base_tax", "base_production", "base_manpower"
        ))
        for row in rows
    ]
    floors = [
        max(
            MINIMUM_OWNED_PROVINCE_DEVELOPMENT,
            BALKAN_CAPITAL_FLOORS.get(int(row["province_id"]), 0),
        )
        for row in rows
    ]
    if target_total < sum(floors) or target_total > len(rows) * DEVELOPMENT_HARD_CAP:
        raise RuntimeError(
            f"National development target {target_total} is infeasible for "
            f"{len(rows)} provinces"
        )

    active = set(range(len(rows)))
    desired = [0.0] * len(rows)
    remaining = float(target_total)
    while active:
        weight_total = sum(weights[index] for index in active)
        changed = False
        for index in sorted(active):
            share = (
                remaining / len(active)
                if weight_total <= 0
                else remaining * weights[index] / weight_total
            )
            if share < floors[index]:
                desired[index] = float(floors[index])
            elif share > DEVELOPMENT_HARD_CAP:
                desired[index] = float(DEVELOPMENT_HARD_CAP)
            else:
                continue
            remaining -= desired[index]
            active.remove(index)
            changed = True
            break
        if not changed:
            for index in active:
                desired[index] = (
                    remaining / len(active)
                    if weight_total <= 0
                    else remaining * weights[index] / weight_total
                )
            break

    totals = [math.floor(value) for value in desired]
    remainder = target_total - sum(totals)
    order = sorted(
        range(len(rows)),
        key=lambda index: (desired[index] - totals[index], -int(rows[index]["province_id"])),
        reverse=True,
    )
    for index in order:
        if remainder <= 0:
            break
        if totals[index] < DEVELOPMENT_HARD_CAP:
            totals[index] += 1
            remainder -= 1
    if remainder:
        raise RuntimeError("Could not apportion exact national development target")
    return totals


def apply_national_development_balance(rows: Sequence[dict[str, str]]) -> None:
    owned: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if row["owner"]:
            owned.setdefault(row["owner"], []).append(row)
    for tag, provinces in sorted(owned.items()):
        current_total = round(sum(
            sum(float(row[field]) for field in (
                "base_tax", "base_production", "base_manpower"
            ))
            for row in provinces
        ))
        target = national_development_target(tag, current_total)
        if target == current_total:
            continue
        for row, province_total in zip(
            provinces, constrained_province_totals(provinces, target)
        ):
            values = tuple(float(row[field]) for field in (
                "base_tax", "base_production", "base_manpower"
            ))
            tax, production, manpower = allocate_development(province_total, values)
            row["base_tax"] = str(tax)
            row["base_production"] = str(production)
            row["base_manpower"] = str(manpower)
            row["verification_notes"] = (
                "Effective ET state on 2000.1.1; EU4 2K national-target "
                "development model."
            )


def apply_trade_center_balance(row: dict[str, str]) -> None:
    level = MODERN_CENTER_OF_TRADE_OVERRIDES.get(int(row["province_id"]))
    if level is not None:
        row["center_of_trade"] = str(level)


def bootstrap_rows(game: Path) -> list[dict[str, str]]:
    non_land = countries.non_land_provinces()
    active_tags = {
        row["tag"] for row in countries.load_manifest() if row["active_2000"] == "yes"
    }
    vanilla = vanilla_religions(game)
    trade_goods = vanilla_trade_goods(game)
    rows: list[dict[str, str]] = []
    for province_id, source in sorted(province_sources().items()):
        if province_id in non_land:
            continue
        state = effective_state(source)
        owner = state.values.get("owner", "")
        if owner in {"---", "NONE", "none"}:
            owner = ""
        if owner and owner not in active_tags:
            raise RuntimeError(f"Province {province_id} has unregistered 2000 owner {owner}")
        name_match = re.match(r"^\d+\s*-\s*(.+)\.txt$", source.name)
        name = name_match.group(1) if name_match else f"Province {province_id}"
        culture = state.values.get("culture", "")
        religion = normalized_religion(state, vanilla) if (owner or state.religion) else ""
        source_trade_good = state.values.get("trade_goods", "unknown")
        trade_good = TRADE_GOOD_FALLBACKS.get(source_trade_good, source_trade_good)
        if trade_good not in trade_goods:
            trade_good = "grain"
        row = {
            "province_id": str(province_id),
            "name": name,
            "owner": owner,
            "controller": owner,
            "core": owner,
            "culture": {"slovenian": "slovene"}.get(culture, culture),
            "religion": religion,
            "capital": state.values.get("capital", name),
            "trade_goods": trade_good,
            "base_tax": state.values.get("base_tax", "1"),
            "base_production": state.values.get("base_production", "1"),
            "base_manpower": state.values.get("base_manpower", "1"),
            "is_city": state.values.get("is_city", "yes" if owner else "no"),
            "hre": state.values.get("hre", "no"),
            "center_of_trade": state.values.get("center_of_trade", "0"),
            "native_size": state.values.get("native_size", "0"),
            "native_ferocity": state.values.get("native_ferocity", "0"),
            "native_hostileness": state.values.get("native_hostileness", "0"),
            "source": f"et:history/provinces/{source.name}",
            "verification_notes": "Effective ET state on 2000.1.1; clean generated baseline.",
        }
        apply_development_balance(row)
        apply_trade_center_balance(row)
        rows.append(row)
    apply_national_development_balance(rows)
    return rows


def write_manifest(rows: Sequence[dict[str, str]]) -> None:
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_manifest() -> list[dict[str, str]]:
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise RuntimeError("Province CSV columns do not match the generator schema")
        return list(reader)


def quote(value: str) -> str:
    return countries.quote(value)


def infrastructure_context() -> tuple[dict[str, int], dict[str, int]]:
    with countries.COUNTRY_SETUP_DATA.open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        tiers = {
            row["tag"]: int(row["infrastructure_tier"])
            for row in csv.DictReader(handle)
        }
    capitals = {
        row["tag"]: int(row["capital"])
        for row in countries.load_manifest()
        if row["active_2000"] == "yes"
    }
    return tiers, capitals


def starting_buildings(
    row: dict[str, str],
    tiers: dict[str, int],
    capitals: dict[str, int],
    coastal: set[int],
) -> list[str]:
    """Assign a restrained first-pass infrastructure set from canonical tiers."""
    owner = row["owner"]
    if not owner or owner not in tiers:
        return []
    tier = tiers[owner]
    province_id = int(row["province_id"])
    is_capital = capitals.get(owner) == province_id
    tax = int(float(row["base_tax"]))
    production = int(float(row["base_production"]))
    manpower = int(float(row["base_manpower"]))
    total = tax + production + manpower
    center_of_trade = int(row["center_of_trade"] or 0)
    has_port = province_id in coastal

    candidates: list[str] = []
    if is_capital or center_of_trade > 0 or total >= 34 - 4 * tier:
        candidates.append("marketplace")
    if tier >= 2 and row["trade_goods"] != "gold" and (
        is_capital or production >= 15 - 2 * tier
    ):
        candidates.append("workshop")
    if tier >= 2 and (is_capital or tax >= 15 - 2 * tier):
        candidates.append("temple")
    if tier >= 2 and (is_capital or manpower >= 15 - 2 * tier):
        candidates.append("barracks")
    if tier >= 3 and (is_capital or total >= 38 - 4 * tier):
        candidates.append("courthouse")
    if tier >= 2 and has_port and (
        is_capital or center_of_trade > 0 or production >= 13 - tier
    ):
        candidates.append("dock")
    if tier >= 3 and has_port and (
        is_capital or center_of_trade >= 2 or total >= 34 - 3 * tier
    ):
        candidates.append("shipyard")

    priority = {
        "marketplace": 0, "workshop": 1, "courthouse": 2,
        "dock": 3, "shipyard": 4, "temple": 5, "barracks": 6,
    }
    candidates.sort(key=priority.__getitem__)

    # Keep the starting set within a conservative approximation of available
    # building slots. Capitals receive one additional administrative slot.
    slot_budget = max(1, 1 + total // 10 + (1 if is_capital else 0))
    return candidates[:slot_budget]


def province_history(row: dict[str, str], buildings: Sequence[str] = ()) -> str:
    lines = ["# Generated effective snapshot for 2000.1.1; no earlier dated history retained."]
    owner = row["owner"]
    if owner:
        lines.extend([f"owner = {owner}", f"controller = {owner}", f"add_core = {row['core']}"])
    for key in ("culture", "religion"):
        if row[key]:
            lines.append(f"{key} = {row[key]}")
    if row["capital"]:
        lines.append(f"capital = {quote(row['capital'])}")
    lines.extend([
        f"trade_goods = {row['trade_goods']}",
        f"base_tax = {row['base_tax']}",
        f"base_production = {row['base_production']}",
        f"base_manpower = {row['base_manpower']}",
        f"is_city = {row['is_city']}",
        f"hre = {row['hre']}",
    ])
    if row["center_of_trade"] not in {"", "0"}:
        lines.append(f"center_of_trade = {row['center_of_trade']}")
    for building in buildings:
        lines.append(f"{building} = yes")
    if not owner and row["native_size"] not in {"", "0"}:
        lines.extend([
            f"native_size = {row['native_size']}",
            f"native_ferocity = {row['native_ferocity']}",
            f"native_hostileness = {row['native_hostileness']}",
        ])
    lines.extend(discovery_history_lines())
    return "\n".join(lines) + "\n"


def safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", name)


def water_province_ids() -> set[int]:
    text = (MOD / "map" / "default.map").read_text(encoding="cp1252")
    result: set[int] = set()
    for key in ("sea_starts", "lakes"):
        match = re.search(rf"(?s)\b{key}\s*=\s*\{{(.*?)\}}", text)
        if not match:
            raise RuntimeError(f"Missing {key} block in default.map")
        result.update(map(int, re.findall(r"\b\d+\b", match.group(1))))
    return result


def province_definition_names() -> dict[int, str]:
    result: dict[int, str] = {}
    with (MOD / "map" / "definition.csv").open("r", encoding="cp1252", newline="") as handle:
        for fields in csv.reader(handle, delimiter=";"):
            if fields and fields[0].isdigit() and int(fields[0]) > 0:
                result[int(fields[0])] = fields[4] if len(fields) > 4 and fields[4] else f"Province {fields[0]}"
    return result


def discovery_history_lines() -> list[str]:
    discovery_groups = (
        "western", "eastern", "muslim", "ottoman", "chinese", "indian", "sub_saharan",
        *countries.all_modern_technology_groups().keys(),
    )
    return [f"discovered_by = {group}" for group in discovery_groups]


def water_history() -> str:
    return "\n".join([
        "# Generated discovery-only water-zone snapshot for the modern start.",
        *discovery_history_lines(),
    ]) + "\n"


def render_script_entry(key: str | None, value: object, indent: int = 0) -> list[str]:
    prefix = "\t" * indent
    if isinstance(value, list):
        if all(child_key is None for child_key, _ in value):
            values = " ".join(str(child_value) for _, child_value in value)
            return [f"{prefix}{key} = {{ {values} }}"]
        lines = [f"{prefix}{key} = {{"]
        for child_key, child_value in value:
            lines.extend(render_script_entry(child_key, child_value, indent + 1))
        lines.append(f"{prefix}}}")
        return lines
    if key is None:
        return [f"{prefix}{value}"]
    return [f"{prefix}{key} = {value}"]


def aligned_vanilla_trade_nodes(game: Path) -> str:
    """Keep vanilla topology but use route geometry aligned to the ET map."""
    vanilla = countries.parse_file(
        game / "common" / "tradenodes" / "00_tradenodes.txt"
    )
    et_nodes = countries.parse_file(ET / "common" / "tradenodes" / "00_tradenodes.txt")
    et_geometry: dict[tuple[str, str], dict[str, object]] = {}
    for node, entries in et_nodes:
        if not node or not isinstance(entries, list):
            continue
        for key, value in entries:
            if key != "outgoing" or not isinstance(value, list):
                continue
            fields = {child_key: child_value for child_key, child_value in value if child_key}
            target = fields.get("name")
            if isinstance(target, str):
                et_geometry[(node, target)] = fields

    aligned: list[tuple[str | None, object]] = []
    for node, entries in vanilla:
        if not node or not isinstance(entries, list):
            aligned.append((node, entries))
            continue
        new_entries: list[countries.Entry] = []
        for key, value in entries:
            if key != "outgoing" or not isinstance(value, list):
                new_entries.append((key, value))
                continue
            fields = {child_key: child_value for child_key, child_value in value if child_key}
            target = fields.get("name")
            geometry = et_geometry.get((node, target)) if isinstance(target, str) else None
            if geometry:
                new_value = [
                    (child_key, geometry.get(child_key, child_value))
                    if child_key in {"path", "control"}
                    else (child_key, child_value)
                    for child_key, child_value in value
                ]
                new_entries.append((key, new_value))
            else:
                new_entries.append((key, value))
        aligned.append((node, new_entries))

    lines = [
        "# Vanilla EU4 trade topology with ET-map-aligned visual paths.",
        "# Generated by scripts/generate_province_snapshot.py.",
        "",
    ]
    for key, value in aligned:
        lines.extend(render_script_entry(key, value))
        lines.append("")
    return "\n".join(lines)


def outputs(rows: Sequence[dict[str, str]], game: Path) -> dict[Path, tuple[str, str]]:
    result: dict[Path, tuple[str, str]] = {}
    localization = ["l_english:"]
    tiers, capitals = infrastructure_context()
    import generate_starting_world as starting_world
    coastal = starting_world.coastal_land_provinces()
    for row in rows:
        province_id = row["province_id"]
        path = MOD / "history" / "provinces" / f"{province_id} - {safe_name(row['name'])}.txt"
        result[path] = (
            province_history(row, starting_buildings(row, tiers, capitals, coastal)),
            "cp1252",
        )
        display = row["name"].replace('"', r'\"')
        localization.extend([f' PROV{province_id}:0 "{display}"', f' PROV_ADJ{province_id}:0 "{display}"'])
    definition_names = province_definition_names()
    for province_id in sorted(water_province_ids()):
        name = definition_names.get(province_id, f"Sea {province_id}")
        path = MOD / "history" / "provinces" / f"{province_id} - {safe_name(name)}.txt"
        result[path] = (water_history(), "cp1252")
        display = name.replace('"', r'\"')
        localization.extend([f' PROV{province_id}:0 "{display}"', f' PROV_ADJ{province_id}:0 "{display}"'])
    result[MOD / "localisation" / "replace" / "eu4_2k_provinces_l_english.yml"] = (
        "\n".join(localization) + "\n", "utf-8-sig"
    )
    result[MOD / "common" / "tradenodes" / "00_tradenodes.txt"] = (
        aligned_vanilla_trade_nodes(game), "cp1252"
    )
    return result


def validate_rows(rows: Sequence[dict[str, str]], game: Path) -> None:
    errors: list[str] = []
    ids = [int(row["province_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate province IDs")
    non_land = countries.non_land_provinces()
    active = {row["tag"] for row in countries.load_manifest() if row["active_2000"] == "yes"}
    owned_tags: set[str] = set()
    vanilla = vanilla_religions(game)
    trade_goods = vanilla_trade_goods(game)
    national_totals: dict[str, int] = {}
    for row in rows:
        province_id = int(row["province_id"])
        if not 1 <= province_id <= 4941 or province_id in non_land:
            errors.append(f"invalid land province {province_id}")
        if row["owner"]:
            owned_tags.add(row["owner"])
            if row["owner"] not in active:
                errors.append(f"province {province_id}: inactive/unknown owner {row['owner']}")
            if row["controller"] != row["owner"] or row["core"] != row["owner"]:
                errors.append(f"province {province_id}: owner/controller/core mismatch")
            if not row["culture"] or row["religion"] not in vanilla:
                errors.append(f"province {province_id}: missing culture or non-vanilla religion")
        if row["trade_goods"] not in trade_goods:
            errors.append(f"province {province_id}: undefined trade good {row['trade_goods']}")
        try:
            center_level = int(row["center_of_trade"] or 0)
            if not 0 <= center_level <= 3:
                raise ValueError
        except ValueError:
            errors.append(f"province {province_id}: invalid center of trade")
        for field_name in ("base_tax", "base_production", "base_manpower"):
            try:
                if float(row[field_name]) < 0:
                    raise ValueError
            except ValueError:
                errors.append(f"province {province_id}: invalid {field_name}")
        try:
            total_development = sum(
                float(row[field])
                for field in ("base_tax", "base_production", "base_manpower")
            )
            if row["owner"]:
                if total_development < MINIMUM_OWNED_PROVINCE_DEVELOPMENT:
                    errors.append(
                        f"province {province_id}: owned development below "
                        f"{MINIMUM_OWNED_PROVINCE_DEVELOPMENT}"
                    )
                national_totals[row["owner"]] = (
                    national_totals.get(row["owner"], 0) + round(total_development)
                )
            if total_development > DEVELOPMENT_HARD_CAP:
                errors.append(
                    f"province {province_id}: development exceeds {DEVELOPMENT_HARD_CAP}"
                )
            required_floor = BALKAN_CAPITAL_FLOORS.get(province_id)
            if required_floor and total_development < required_floor:
                errors.append(
                    f"province {province_id}: below Balkan capital floor {required_floor}"
                )
        except ValueError:
            pass
    missing = active - owned_tags
    if missing:
        errors.append("active countries without territory: " + ", ".join(sorted(missing)))
    for tag, total in sorted(national_totals.items()):
        expected = national_development_target(tag, total)
        if tag in NATIONAL_DEVELOPMENT_TARGETS and total != expected:
            errors.append(f"{tag}: development must total {expected}, found {total}")
        if tag not in NATIONAL_DEVELOPMENT_TARGETS and not (
            MINIMUM_NATIONAL_DEVELOPMENT
            <= total
            <= MAXIMUM_NON_TARGET_NATIONAL_DEVELOPMENT
        ):
            errors.append(f"{tag}: development total {total} is outside tier bounds")
    country_rows = {row["tag"]: row for row in countries.load_manifest() if row["active_2000"] == "yes"}
    by_id = {row["province_id"]: row for row in rows}
    for tag, country in country_rows.items():
        capital = by_id.get(country["capital"])
        if not capital or capital["owner"] != tag:
            errors.append(f"{tag}: capital {country['capital']} is not owned at start")
    for province_id, required_level in MODERN_CENTER_OF_TRADE_OVERRIDES.items():
        row = by_id.get(str(province_id))
        if not row or row["center_of_trade"] != str(required_level):
            errors.append(
                f"province {province_id}: modern trade-center level must be {required_level}"
            )
    if errors:
        raise RuntimeError("Province data validation failed:\n- " + "\n- ".join(errors[:100]))


def write_outputs(rows: Sequence[dict[str, str]], game: Path) -> None:
    expected = outputs(rows, game)
    legacy_province_localisation = MOD / "localisation" / "eu4_2k_provinces_l_english.yml"
    if legacy_province_localisation.exists():
        legacy_province_localisation.unlink()
    history = MOD / "history" / "provinces"
    history.mkdir(parents=True, exist_ok=True)
    expected_history = {path for path in expected if path.parent == history}
    for path in history.glob("*.txt"):
        if path not in expected_history:
            path.unlink()
    for path, (content, encoding) in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = content.encode(encoding)
        if not path.exists() or path.read_bytes() != encoded:
            path.write_bytes(encoded)


def check_outputs(rows: Sequence[dict[str, str]], game: Path) -> None:
    errors: list[str] = []
    expected = outputs(rows, game)
    for path, (content, encoding) in expected.items():
        if not path.exists():
            errors.append(f"missing generated file: {path.relative_to(ROOT)}")
        elif path.read_bytes() != content.encode(encoding):
            errors.append(f"stale generated file: {path.relative_to(ROOT)}")
    history = MOD / "history" / "provinces"
    actual = set(history.glob("*.txt")) if history.exists() else set()
    expected_history = {path for path in expected if path.parent == history}
    for path in sorted(actual - expected_history):
        errors.append(f"unexpected province history: {path.name}")
    for path in expected_history:
        text = path.read_text(encoding="cp1252", errors="replace")
        if re.search(r"(?m)^\s*-?\d+\.\d+\.\d+\s*=", text):
            errors.append(f"dated history block found: {path.name}")
    import generate_starting_world as starting_world
    coastal = starting_world.coastal_land_provinces()
    for path in expected_history:
        match = re.match(r"^(\d+)", path.name)
        if not match:
            continue
        province_id = int(match.group(1))
        text = path.read_text(encoding="cp1252", errors="replace")
        if province_id not in coastal and re.search(
            r"(?m)^(dock|shipyard) = yes$", text
        ):
            errors.append(f"inland province {province_id} has a naval building")
    if errors:
        raise RuntimeError("Province output check failed:\n- " + "\n- ".join(errors[:100]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=("generate",), default="generate")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--game-root")
    parser.add_argument("--rebuild-data", action="store_true")
    parser.add_argument(
        "--rebalance-development",
        action="store_true",
        help="recalculate development from the ET 2000 baseline while preserving other CSV edits",
    )
    parser.add_argument(
        "--rebalance-trade-centers",
        action="store_true",
        help="apply the modern center-of-trade audit while preserving other CSV edits",
    )
    args = parser.parse_args()
    game = countries.find_game_root(args.game_root)
    if args.check and (args.rebalance_development or args.rebalance_trade_centers):
        raise SystemExit("--check cannot be combined with rebalance options")
    if args.rebuild_data or not DATA.exists():
        if args.check:
            raise SystemExit("Canonical province dataset is missing; run generate first")
        write_manifest(bootstrap_rows(game))
    elif args.rebalance_development:
        rows = load_manifest()
        baseline = {
            row["province_id"]: row for row in bootstrap_rows(game)
        }
        for row in rows:
            source = baseline[row["province_id"]]
            for field in (
                "base_tax", "base_production", "base_manpower", "verification_notes"
            ):
                row[field] = source[field]
        write_manifest(rows)
    elif args.rebalance_trade_centers:
        rows = load_manifest()
        for row in rows:
            apply_trade_center_balance(row)
        write_manifest(rows)
    rows = load_manifest()
    validate_rows(rows, game)
    if args.check:
        check_outputs(rows, game)
        print(f"Validated {len(rows)} land provinces; {sum(bool(row['owner']) for row in rows)} owned; {len(water_province_ids())} water zones discovered.")
    else:
        country_rows = countries.load_manifest()
        countries.validate_rows(country_rows, game)
        technology_setup = countries.load_technology_setup(country_rows)
        countries.write_outputs(country_rows, game, technology_setup)
        write_outputs(rows, game)
        check_outputs(rows, game)
        print(f"Generated {len(rows)} land provinces; {sum(bool(row['owner']) for row in rows)} owned; {len(water_province_ids())} water zones discovered.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
