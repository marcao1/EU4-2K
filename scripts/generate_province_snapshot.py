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
DEVELOPMENT_HARD_CAP = 60
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
        rows.append(row)
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


def province_history(row: dict[str, str]) -> str:
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
    for row in rows:
        province_id = row["province_id"]
        path = MOD / "history" / "provinces" / f"{province_id} - {safe_name(row['name'])}.txt"
        result[path] = (province_history(row), "cp1252")
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
    country_rows = {row["tag"]: row for row in countries.load_manifest() if row["active_2000"] == "yes"}
    by_id = {row["province_id"]: row for row in rows}
    for tag, country in country_rows.items():
        capital = by_id.get(country["capital"])
        if not capital or capital["owner"] != tag:
            errors.append(f"{tag}: capital {country['capital']} is not owned at start")
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
    args = parser.parse_args()
    game = countries.find_game_root(args.game_root)
    if args.check and args.rebalance_development:
        raise SystemExit("--check cannot be combined with --rebalance-development")
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
