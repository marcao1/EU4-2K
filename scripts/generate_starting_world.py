#!/usr/bin/env python3
"""Bootstrap, validate, and integrate canonical Step 3 starting-world data.

This stage owns the canonical CSVs and clean bilateral diplomacy history.
International-organization memberships and individual forces remain data-only.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from PIL import Image

import generate_country_snapshot as countries


ROOT = countries.ROOT
MOD = countries.MOD
ET = countries.ET
COUNTRY_DATA = ROOT / "data" / "country_setup_2000.csv"
DIPLOMACY_DATA = ROOT / "data" / "diplomacy_2000.csv"
FORCES_DATA = ROOT / "data" / "forces_2000.csv"
DIPLOMACY_OUTPUT = MOD / "history" / "diplomacy" / "00_eu4_2k_diplomacy.txt"

COUNTRY_FIELDS = [
    "tag", "adm_tech", "dip_tech", "mil_tech", "technology_tier",
    "embraced_institutions", "treasury", "inflation", "stability", "prestige",
    "corruption", "legitimacy_or_tradition", "manpower", "sailors",
    "army_quality_tier", "navy_quality_tier", "economic_tier",
    "infrastructure_tier", "source", "verification_notes",
]

# Starting cash is deliberately inverse to country size. Large states already
# have much higher monthly income, while small states need a larger reserve to
# survive the opening years without being forced into immediate loans.
LARGE_COUNTRY_DEVELOPMENT = 500
MEDIUM_COUNTRY_DEVELOPMENT = 150


def starting_treasury(total_development: int) -> int:
    if total_development >= LARGE_COUNTRY_DEVELOPMENT:
        return 50
    if total_development >= MEDIUM_COUNTRY_DEVELOPMENT:
        return 200
    return 600
DIPLOMACY_FIELDS = [
    "country_a", "country_b", "relationship_type", "start_date", "end_date",
    "initial_opinion", "organization", "source", "verification_notes",
]
FORCES_FIELDS = [
    "country", "branch", "formation_name", "location", "unit_category",
    "quantity", "quality_tier", "source", "verification_notes",
]

INSTITUTIONS = [
    "feudalism", "renaissance", "new_world_i", "printing_press",
    "global_trade", "manufactories", "enlightenment", "industrialization",
]

LEADING_TECH = {
    "USA", "CAN", "JAP", "SKO", "GER", "FR2", "GBR", "SWE", "FIN",
    "NED", "BEL", "SWI", "HAB", "DAN", "NOR", "AUS", "NZL", "SGA",
}
ADVANCED_TECH = {
    "ITA", "SPA", "POR", "IRE", "ICE", "LUX", "ISR", "FRM", "CHN",
    "CZE", "SLO", "HUN", "POL", "SVN", "CRO", "GRE", "CYP", "MLT",
}
FRAGILE_STATES = {
    "AFG", "SOM", "DRC", "SLE", "LBR", "BUU", "RWA", "GNB", "GZI",
    "YUG", "TJK", "IRQ", "SDN", "ERI",
}
LOW_TECH_STATES = {"AFG", "SOM", "DRC", "SLE", "LBR", "BUU"}
TECH_TIER_OVERRIDES = {"RUS": 4, "YUG": 3}

NATO_2000 = {
    "USA", "CAN", "GBR", "FR2", "BEL", "NED", "LUX", "POR", "ITA",
    "DAN", "NOR", "ICE", "GER", "SPA", "GRE", "TKY", "CZE", "HUN", "POL",
}
EU_2000 = {
    "HAB", "BEL", "DAN", "FIN", "FR2", "GER", "GRE", "IRE", "ITA",
    "LUX", "NED", "POR", "SPA", "SWE", "GBR",
}
CIS_2000 = {
    "ARM", "AZE", "BLR", "GEO", "KZK", "KYR", "MDV", "RUS", "TJK",
    "TRK", "UKR", "UZB",
}
UN_EXCLUSIONS_2000 = {"SWI", "FRM", "YUG", "TVL", "PLS"}

RELATIONSHIP_TYPES = {"alliance", "guarantee", "vassal", "union", "dependency", "royal_marriage"}
SYMMETRIC_RELATIONSHIPS = {"alliance", "royal_marriage"}
OPINION_BY_RELATIONSHIP = {
    "alliance": "100", "guarantee": "75", "vassal": "150",
    "union": "150", "dependency": "125", "royal_marriage": "100",
}

# Curated bilateral defence relationships effective on 2000.1.1. Membership
# in NATO, the EU, CIS, UN, OAS, or any other organization is excluded here.
CURATED_BILATERAL_RELATIONSHIPS = (
    ("GBR", "POR", "alliance", "1386.5.9", "uk-portugal-treaty-of-windsor"),
    ("USA", "AUS", "alliance", "1952.4.29", "us-state-collective-defense"),
    ("AUS", "NZL", "alliance", "1952.4.29", "us-state-collective-defense"),
    ("USA", "PHI", "alliance", "1952.8.27", "us-state-collective-defense"),
    ("USA", "SKO", "alliance", "1954.11.17", "us-state-collective-defense"),
    ("USA", "SIA", "alliance", "1954.9.8", "us-state-collective-defense"),
    ("USA", "JAP", "alliance", "1960.6.23", "us-state-collective-defense"),
    ("CHN", "NOK", "alliance", "1961.9.10", "china-dprk-mutual-assistance"),
    ("RUS", "ARM", "alliance", "1997.8.29", "russia-armenia-mutual-assistance"),
    ("RUS", "BLR", "alliance", "1999.12.8", "russia-belarus-union-state"),
    # The Taiwan Relations Act is represented as a unilateral gameplay
    # guarantee rather than a mutual alliance.
    ("USA", "FRM", "guarantee", "1979.4.10", "taiwan-relations-act"),
)


def bilateral_diplomacy(
    rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    """Return gameplay relationships, explicitly excluding organizations."""
    return [row for row in rows if row["relationship_type"] in RELATIONSHIP_TYPES]


def diplomacy_history(rows: Sequence[dict[str, str]]) -> str:
    lines = [
        "# Generated bilateral diplomacy effective on 2000.1.1.",
        "# International organizations are intentionally not integrated here.",
        "",
    ]
    for row in bilateral_diplomacy(rows):
        lines.extend([
            f"{row['relationship_type']} = {{",
            f"\tfirst = {row['country_a']}",
            f"\tsecond = {row['country_b']}",
            f"\t# Historical treaty start: {row['start_date']}",
            "\tstart_date = 2000.1.1",
            f"\tend_date = {row['end_date']}",
            "}",
            "",
        ])
    return "\n".join(lines)


def write_diplomacy(rows: Sequence[dict[str, str]]) -> None:
    DIPLOMACY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    for path in DIPLOMACY_OUTPUT.parent.glob("*.txt"):
        if path != DIPLOMACY_OUTPUT:
            path.unlink()
    content = diplomacy_history(rows).encode("cp1252")
    if not DIPLOMACY_OUTPUT.exists() or DIPLOMACY_OUTPUT.read_bytes() != content:
        DIPLOMACY_OUTPUT.write_bytes(content)


def validate_diplomacy_output(rows: Sequence[dict[str, str]]) -> None:
    expected = diplomacy_history(rows).encode("cp1252")
    if not DIPLOMACY_OUTPUT.exists():
        raise RuntimeError("Missing generated bilateral diplomacy history")
    if DIPLOMACY_OUTPUT.read_bytes() != expected:
        raise RuntimeError("Generated bilateral diplomacy history is stale")
    text = expected.decode("cp1252")
    if "organization_member" in text or any(
        f"organization = {name}" in text for name in ("NATO", "EU", "CIS", "UN")
    ):
        raise RuntimeError("International organization leaked into diplomacy output")
    blocks = re.findall(r"(?m)^(alliance|guarantee|vassal|union|dependency|royal_marriage)\s*=\s*\{", text)
    if len(blocks) != len(bilateral_diplomacy(rows)):
        raise RuntimeError("Generated bilateral diplomacy count is incorrect")


def read_csv(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(fields):
            raise RuntimeError(f"{path.name}: columns do not match the canonical schema")
        return list(reader)


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def active_country_rows() -> list[dict[str, str]]:
    return sorted(
        (row for row in countries.load_manifest() if row["active_2000"] == "yes"),
        key=lambda row: row["tag"],
    )


def province_rows() -> list[dict[str, str]]:
    with countries.PROVINCE_DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def technology_tier(row: dict[str, str]) -> int:
    tag = row["tag"]
    if tag in TECH_TIER_OVERRIDES:
        return TECH_TIER_OVERRIDES[tag]
    if tag in LOW_TECH_STATES:
        return 1
    if tag in LEADING_TECH:
        return 5
    if tag in ADVANCED_TECH:
        return 4
    return {
        "modern_western": 4,
        "modern_post_soviet": 3,
        "modern_east_asian": 3,
        "modern_south_asian": 3,
        "modern_southeast_asian": 3,
        "modern_middle_eastern_north_african": 3,
        "modern_sub_saharan_african": 2,
        "modern_latin_american": 3,
        "modern_oceanian": 3,
    }[row["technology_group"]]


def aggregate_provinces(rows: Sequence[dict[str, str]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for row in rows:
        tag = row["owner"]
        if not tag:
            continue
        values = result.setdefault(tag, {"tax": 0, "production": 0, "manpower": 0, "count": 0})
        values["tax"] += float(row["base_tax"])
        values["production"] += float(row["base_production"])
        values["manpower"] += float(row["base_manpower"])
        values["count"] += 1
    return result


def map_ids(key: str) -> set[int]:
    text = (MOD / "map" / "default.map").read_text(encoding="cp1252")
    match = re.search(rf"(?s)\b{re.escape(key)}\s*=\s*\{{(.*?)\}}", text)
    if not match:
        raise RuntimeError(f"Map block is missing: {key}")
    return set(map(int, re.findall(r"\b\d+\b", match.group(1))))


def coastal_land_provinces() -> set[int]:
    definitions: list[tuple[int, int]] = []
    with (MOD / "map" / "definition.csv").open("r", encoding="cp1252", newline="") as handle:
        for fields in csv.reader(handle, delimiter=";"):
            if fields and fields[0].isdigit() and int(fields[0]) > 0:
                province_id = int(fields[0])
                color_code = int(fields[1]) | (int(fields[2]) << 8) | (int(fields[3]) << 16)
                definitions.append((color_code, province_id))
    lookup = np.full(1 << 24, -1, dtype=np.int32)
    for color_code, province_id in definitions:
        lookup[color_code] = province_id
    rgb = np.asarray(Image.open(MOD / "map" / "provinces.bmp").convert("RGB"), dtype=np.uint32)
    codes = rgb[:, :, 0] | (rgb[:, :, 1] << 8) | (rgb[:, :, 2] << 16)
    province_map = lookup[codes]
    sea_ids = map_ids("sea_starts")
    sea_lookup = np.zeros(4942, dtype=bool)
    sea_lookup[list(sea_ids)] = True
    coastal: set[int] = set()
    for left, right in ((province_map[:, :-1], province_map[:, 1:]), (province_map[:-1, :], province_map[1:, :])):
        left_sea = sea_lookup[np.maximum(left, 0)]
        right_sea = sea_lookup[np.maximum(right, 0)]
        coastal.update(map(int, np.unique(left[(~left_sea) & right_sea & (left > 0)])))
        coastal.update(map(int, np.unique(right[left_sea & (~right_sea) & (right > 0)])))
    return coastal


def bootstrap_country_setup(country_rows: Sequence[dict[str, str]], provinces: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    aggregates = aggregate_provinces(provinces)
    coastal = coastal_land_provinces()
    owned_coastal: dict[str, int] = {}
    for province in provinces:
        if province["owner"] and int(province["province_id"]) in coastal:
            owned_coastal[province["owner"]] = owned_coastal.get(province["owner"], 0) + 1
    rows: list[dict[str, str]] = []
    tech_level_by_tier = {1: 5, 2: 6, 3: 7, 4: 8, 5: 9}
    for country in country_rows:
        tag = country["tag"]
        tier = technology_tier(country)
        values = aggregates[tag]
        total_development = values["tax"] + values["production"] + values["manpower"]
        treasury = starting_treasury(total_development)
        manpower = max(1000, round(values["manpower"] * 750))
        sailors = round(owned_coastal.get(tag, 0) * (150 + tier * 50))
        level = tech_level_by_tier[tier]
        rows.append({
            "tag": tag,
            "adm_tech": str(level),
            "dip_tech": str(level),
            "mil_tech": str(level),
            "technology_tier": str(tier),
            # All eight institutions now emerge after the 2000.1.1 bookmark.
            "embraced_institutions": "",
            "treasury": str(treasury),
            "inflation": "0",
            "stability": "-1" if tag in FRAGILE_STATES else "0",
            "prestige": "0",
            "corruption": "5" if tag in FRAGILE_STATES else "0",
            "legitimacy_or_tradition": "50" if tag in FRAGILE_STATES else "60",
            "manpower": str(manpower),
            "sailors": str(sailors),
            "army_quality_tier": str(tier),
            "navy_quality_tier": str(tier if sailors else 0),
            "economic_tier": str(tier),
            "infrastructure_tier": str(tier),
            "source": "generated:country-and-province-2000-foundation",
            "verification_notes": "Mechanically valid first-pass tier; manual historical verification pending.",
        })
    return rows


def effective_diplomacy(country_rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    active = {row["tag"] for row in country_rows}
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for first, second, relationship_type, start, source in CURATED_BILATERAL_RELATIONSHIPS:
        if first not in active or second not in active:
            raise RuntimeError(f"Curated diplomacy uses inactive tag: {first}/{second}")
        a, b = (
            sorted((first, second))
            if relationship_type in SYMMETRIC_RELATIONSHIPS
            else (first, second)
        )
        key = (relationship_type, a, b, "")
        if key in seen:
            raise RuntimeError(f"Duplicate curated diplomacy: {key}")
        seen.add(key)
        result.append({
            "country_a": a,
            "country_b": b,
            "relationship_type": relationship_type,
            "start_date": start,
            "end_date": "9999.12.31",
            "initial_opinion": OPINION_BY_RELATIONSHIP[relationship_type],
            "organization": "",
            "source": f"manual:{source}",
            "verification_notes": (
                "Curated bilateral relationship effective on 2000.1.1; "
                "international organizations excluded."
            ),
        })

    memberships = (("NATO", NATO_2000), ("EU", EU_2000), ("CIS", CIS_2000), ("UN", active - UN_EXCLUSIONS_2000))
    for organization, members in memberships:
        for tag in sorted(active & members):
            key = ("organization_member", tag, "", organization)
            if key in seen:
                continue
            seen.add(key)
            result.append({
                "country_a": tag,
                "country_b": "",
                "relationship_type": "organization_member",
                "start_date": "2000.1.1",
                "end_date": "9999.12.31",
                "initial_opinion": "0",
                "organization": organization,
                "source": "manual:membership-baseline-2000.1.1",
                "verification_notes": "Organization metadata only; does not create an EU4 alliance.",
            })
    return sorted(result, key=lambda row: (row["relationship_type"], row["organization"], row["country_a"], row["country_b"]))


def bootstrap_forces(
    country_rows: Sequence[dict[str, str]],
    provinces: Sequence[dict[str, str]],
    setup_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    setup = {row["tag"]: row for row in setup_rows}
    country_by_tag = {row["tag"]: row for row in country_rows}
    aggregates = aggregate_provinces(provinces)
    coastal = coastal_land_provinces()
    owned: dict[str, list[dict[str, str]]] = {}
    for province in provinces:
        if province["owner"]:
            owned.setdefault(province["owner"], []).append(province)
    rows: list[dict[str, str]] = []
    for tag in sorted(country_by_tag):
        country = country_by_tag[tag]
        tier = int(setup[tag]["army_quality_tier"])
        total_development = sum(aggregates[tag][key] for key in ("tax", "production", "manpower"))
        army_quantity = max(1, min(60, round(math.sqrt(total_development) * 0.7)))
        rows.append({
            "country": tag,
            "branch": "army",
            "formation_name": f"{country['name']} Armed Forces",
            "location": country["capital"],
            "unit_category": "regular_army",
            "quantity": str(army_quantity),
            "quality_tier": str(tier),
            "source": "generated:development-and-technology-tier",
            "verification_notes": "Simplified first-pass formation; real order of battle pending.",
        })
        coastal_owned = [province for province in owned[tag] if int(province["province_id"]) in coastal]
        if coastal_owned:
            port = max(
                coastal_owned,
                key=lambda province: sum(float(province[field]) for field in ("base_tax", "base_production", "base_manpower")),
            )
            navy_quantity = max(1, min(40, round(math.sqrt(len(coastal_owned) * max(tier, 1)) * 1.5)))
            rows.append({
                "country": tag,
                "branch": "navy",
                "formation_name": f"{country['name']} Fleet",
                "location": port["province_id"],
                "unit_category": "surface_fleet",
                "quantity": str(navy_quantity),
                "quality_tier": setup[tag]["navy_quality_tier"],
                "source": "generated:coastal-provinces-and-technology-tier",
                "verification_notes": "Simplified first-pass fleet; real naval inventory pending.",
            })
    return rows


def validate(
    country_rows: Sequence[dict[str, str]],
    provinces: Sequence[dict[str, str]],
    setup_rows: Sequence[dict[str, str]],
    diplomacy_rows: Sequence[dict[str, str]],
    force_rows: Sequence[dict[str, str]],
) -> None:
    errors: list[str] = []
    active = {row["tag"] for row in country_rows}
    if len(active) != 188:
        errors.append(f"expected 188 active tags, found {len(active)}")
    setup_tags = [row["tag"] for row in setup_rows]
    if len(setup_tags) != len(set(setup_tags)) or set(setup_tags) != active:
        errors.append("country setup must contain exactly one row for every active tag")
    aggregates = aggregate_provinces(provinces)
    owned_by_id = {row["province_id"]: row["owner"] for row in provinces}
    for row in setup_rows:
        tag = row["tag"]
        for field in ("adm_tech", "dip_tech", "mil_tech", "technology_tier", "army_quality_tier", "economic_tier", "infrastructure_tier"):
            try:
                value = int(row[field])
                if value < 0:
                    raise ValueError
            except ValueError:
                errors.append(f"{tag}: invalid {field}")
        institutions = row["embraced_institutions"].split("|") if row["embraced_institutions"] else []
        if any(institution not in INSTITUTIONS for institution in institutions):
            errors.append(f"{tag}: undefined institution metadata")
        if institutions:
            errors.append(f"{tag}: institutions must not be embraced before 2000.4.1")
        total_development = round(sum(
            aggregates[tag][field] for field in ("tax", "production", "manpower")
        ))
        expected_treasury = starting_treasury(total_development)
        if row["treasury"] != str(expected_treasury):
            errors.append(
                f"{tag}: treasury must be {expected_treasury} for "
                f"{total_development} development"
            )
    diplomacy_keys: set[tuple[str, str, str, str]] = set()
    for row in diplomacy_rows:
        a, b = row["country_a"], row["country_b"]
        if a not in active or (b and b not in active) or a == b:
            errors.append(f"invalid diplomacy endpoints: {a}/{b}")
        relationship_type = row["relationship_type"]
        if relationship_type != "organization_member" and relationship_type not in RELATIONSHIP_TYPES:
            errors.append(f"invalid relationship type: {relationship_type}")
        if relationship_type == "organization_member" and (b or not row["organization"]):
            errors.append(f"invalid organization membership: {a}")
        key = (relationship_type, a, b, row["organization"])
        if key in diplomacy_keys:
            errors.append(f"duplicate diplomacy row: {key}")
        diplomacy_keys.add(key)
        start, end = countries.date_number(row["start_date"]), countries.date_number(row["end_date"])
        if start is None or end is None or not start <= countries.START_NUMBER < end:
            errors.append(f"inactive diplomacy row at start: {key}")
    army_tags: set[str] = set()
    for row in force_rows:
        tag = row["country"]
        if tag not in active:
            errors.append(f"unknown force owner: {tag}")
            continue
        if row["branch"] not in {"army", "navy"}:
            errors.append(f"{tag}: invalid force branch")
        if owned_by_id.get(row["location"]) != tag:
            errors.append(f"{tag}: formation location {row['location']} is not owned")
        try:
            if int(row["quantity"]) <= 0 or not 0 <= int(row["quality_tier"]) <= 5:
                raise ValueError
        except ValueError:
            errors.append(f"{tag}: invalid force quantity or quality")
        if row["branch"] == "army":
            army_tags.add(tag)
    if army_tags != active:
        errors.append("every active country must have one starting army record")
    if errors:
        raise RuntimeError("Starting-world data validation failed:\n- " + "\n- ".join(errors[:100]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=("generate",), default="generate")
    parser.add_argument("--check", action="store_true", help="validate canonical CSVs without writing")
    parser.add_argument("--rebuild-data", action="store_true", help="replace all three canonical CSVs")
    parser.add_argument(
        "--rebuild-diplomacy",
        action="store_true",
        help="replace only bilateral diplomacy and organization metadata",
    )
    parser.add_argument(
        "--rebalance-economy",
        action="store_true",
        help="recalculate size-based treasury and development-derived reserves without replacing other setup data",
    )
    args = parser.parse_args()

    country_rows = active_country_rows()
    provinces = province_rows()
    missing = [path for path in (COUNTRY_DATA, DIPLOMACY_DATA, FORCES_DATA) if not path.exists()]
    if args.check and missing:
        raise SystemExit("Canonical starting-world data is missing; run generate first")
    if args.check and (args.rebalance_economy or args.rebuild_diplomacy):
        raise SystemExit(
            "--check cannot be combined with --rebalance-economy or --rebuild-diplomacy"
        )
    if args.rebuild_data or missing:
        setup_rows = bootstrap_country_setup(country_rows, provinces)
        diplomacy_rows = effective_diplomacy(country_rows)
        force_rows = bootstrap_forces(country_rows, provinces, setup_rows)
        write_csv(COUNTRY_DATA, COUNTRY_FIELDS, setup_rows)
        write_csv(DIPLOMACY_DATA, DIPLOMACY_FIELDS, diplomacy_rows)
        write_csv(FORCES_DATA, FORCES_FIELDS, force_rows)
    elif args.rebalance_economy:
        setup_rows = read_csv(COUNTRY_DATA, COUNTRY_FIELDS)
        recalculated = {
            row["tag"]: row for row in bootstrap_country_setup(country_rows, provinces)
        }
        for row in setup_rows:
            source = recalculated[row["tag"]]
            for field in ("treasury", "manpower", "sailors", "navy_quality_tier"):
                row[field] = source[field]
            row["verification_notes"] = (
                "Size-tier treasury and development-derived reserves rebalanced for the EU4 2K province model; "
                "manual historical verification pending."
            )
        write_csv(COUNTRY_DATA, COUNTRY_FIELDS, setup_rows)
    elif args.rebuild_diplomacy:
        write_csv(DIPLOMACY_DATA, DIPLOMACY_FIELDS, effective_diplomacy(country_rows))
    setup_rows = read_csv(COUNTRY_DATA, COUNTRY_FIELDS)
    diplomacy_rows = read_csv(DIPLOMACY_DATA, DIPLOMACY_FIELDS)
    force_rows = read_csv(FORCES_DATA, FORCES_FIELDS)
    validate(country_rows, provinces, setup_rows, diplomacy_rows, force_rows)
    if args.check:
        validate_diplomacy_output(diplomacy_rows)
    else:
        write_diplomacy(diplomacy_rows)
        validate_diplomacy_output(diplomacy_rows)
    action = "Validated" if args.check else "Generated"
    print(
        f"{action} starting-world data: {len(setup_rows)} countries, "
        f"{len(bilateral_diplomacy(diplomacy_rows))} bilateral relationships, "
        f"{sum(row['relationship_type'] == 'organization_member' for row in diplomacy_rows)} "
        f"organization records left data-only, {len(force_rows)} formations."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
