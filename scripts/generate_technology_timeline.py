#!/usr/bin/env python3
"""Retitle and redate vanilla EU4 technology without changing its gameplay."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "MillenniumDawnEU4"
DATA = ROOT / "data" / "technology_years_titles.csv"
TECH_OUTPUT = MOD / "common" / "technologies"
LOC_OUTPUT = MOD / "localisation" / "replace" / "eu4_2k_technology_l_english.yml"
LEGACY_LOC_OUTPUT = MOD / "localisation" / "eu4_2k_technology_l_english.yml"
TRACKS = ("adm", "dip", "mil")

GAME_CANDIDATES = (
    Path(r"F:\Steam\steamapps\common\Europa Universalis IV"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Europa Universalis IV"),
    Path(r"C:\Program Files\Steam\steamapps\common\Europa Universalis IV"),
)

TECH_START = re.compile(r"^(\s*technology\s*=\s*\{)(?:\s*#.*)?$")
YEAR_LINE = re.compile(r"^(\s*)year\s*=\s*-?\d+(\s*(?:#.*)?)$")


def locate_game(explicit: Path | None) -> Path:
    if explicit is not None:
        if not (explicit / "eu4.exe").exists():
            raise SystemExit(f"EU4 game root does not contain eu4.exe: {explicit}")
        return explicit
    for candidate in GAME_CANDIDATES:
        if (candidate / "eu4.exe").exists():
            return candidate
    raise SystemExit("Could not locate EU4; pass --game-root.")


def load_rows() -> list[dict[str, str]]:
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"level", "year", *(f"{track}_title" for track in TRACKS)}
    if not rows or set(rows[0]) != required:
        raise SystemExit(f"{DATA} must contain exactly: {', '.join(sorted(required))}")
    if len(rows) != 33:
        raise SystemExit(f"Expected 33 technology rows, found {len(rows)}")
    levels = [int(row["level"]) for row in rows]
    years = [int(row["year"]) for row in rows]
    if levels != list(range(33)):
        raise SystemExit("Technology levels must be exactly 0 through 32 in order.")
    if years != sorted(years) or len(set(years)) != len(years):
        raise SystemExit("Technology years must be unique and strictly increasing.")
    if years[9] != 2000 or years[10:17] != list(range(2005, 2040, 5)):
        raise SystemExit("Required timeline is level 9=2000 and levels 10-16=2005-2035.")
    for row in rows:
        for track in TRACKS:
            if not row[f"{track}_title"].strip():
                raise SystemExit(f"Missing {track} title at level {row['level']}")
    return rows


def code_part(line: str) -> str:
    quoted = False
    escaped = False
    result: list[str] = []
    for char in line:
        if escaped:
            result.append(char)
            escaped = False
        elif char == "\\" and quoted:
            result.append(char)
            escaped = True
        elif char == '"':
            quoted = not quoted
            result.append(char)
        elif char == "#" and not quoted:
            break
        else:
            result.append(char)
    return "".join(result)


def brace_delta(line: str) -> int:
    code = code_part(line)
    return code.count("{") - code.count("}")


def transform_technology(source: str, rows: list[dict[str, str]], track: str) -> str:
    output: list[str] = []
    level = -1
    depth = 0
    in_technology = False
    found_year = False

    for original_line in source.splitlines():
        line = original_line
        start = TECH_START.match(line) if depth == 0 else None
        if start:
            level += 1
            if level >= len(rows):
                raise ValueError(f"{track}.txt contains more than 33 technologies")
            line = f"{start.group(1)} #{rows[level][f'{track}_title']}"
            in_technology = True
            found_year = False

        if in_technology and depth == 1:
            year_match = YEAR_LINE.match(line)
            if year_match:
                if found_year:
                    raise ValueError(f"Duplicate year in {track} technology level {level}")
                line = f"{year_match.group(1)}year = {rows[level]['year']}{year_match.group(2)}"
                found_year = True

        output.append(line)
        depth += brace_delta(line)
        if in_technology and depth == 0:
            if not found_year:
                raise ValueError(f"Missing year in {track} technology level {level}")
            in_technology = False

    if depth != 0:
        raise ValueError(f"Unbalanced braces in {track}.txt")
    if level != 32:
        raise ValueError(f"{track}.txt contains {level + 1} technologies instead of 33")
    return "\n".join(output) + "\n"


def gameplay_signature(text: str) -> str:
    """Normalize only the two fields this generator is allowed to change."""
    normalized: list[str] = []
    for line in text.splitlines():
        start = TECH_START.match(line)
        if start:
            normalized.append(start.group(1))
            continue
        year = YEAR_LINE.match(line)
        if year:
            normalized.append(f"{year.group(1)}year = <TIMELINE_YEAR>{year.group(2)}")
            continue
        normalized.append(line)
    return "\n".join(normalized)


def localization_text(rows: list[dict[str, str]]) -> str:
    lines = ["l_english:"]
    for track in TRACKS:
        for row in rows:
            title = row[f"{track}_title"].replace('"', '\\"')
            lines.append(f' {track}_tech_cs_{row["level"]}_name:0 "{title}"')
    return "\n".join(lines) + "\n"


def expected_outputs(game: Path, rows: list[dict[str, str]]) -> tuple[dict[Path, str], str]:
    technology: dict[Path, str] = {}
    for track in TRACKS:
        source_path = game / "common" / "technologies" / f"{track}.txt"
        source = source_path.read_text(encoding="cp1252")
        generated = transform_technology(source, rows, track)
        if gameplay_signature(source) != gameplay_signature(generated):
            raise ValueError(f"Generated {track}.txt changes vanilla gameplay content")
        technology[TECH_OUTPUT / f"{track}.txt"] = generated
    return technology, localization_text(rows)


def generate(game: Path, rows: list[dict[str, str]]) -> None:
    technologies, localization = expected_outputs(game, rows)
    TECH_OUTPUT.mkdir(parents=True, exist_ok=True)
    for path, content in technologies.items():
        path.write_text(content, encoding="cp1252", newline="\n")
    LOC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LOC_OUTPUT.write_text(localization, encoding="utf-8-sig", newline="\n")
    if LEGACY_LOC_OUTPUT.exists():
        LEGACY_LOC_OUTPUT.unlink()


def check(game: Path, rows: list[dict[str, str]]) -> None:
    technologies, localization = expected_outputs(game, rows)
    errors: list[str] = []
    for path, expected in technologies.items():
        if not path.exists():
            errors.append(f"missing: {path.relative_to(ROOT)}")
        elif path.read_text(encoding="cp1252") != expected:
            errors.append(f"stale: {path.relative_to(ROOT)}")
    if not LOC_OUTPUT.exists():
        errors.append(f"missing: {LOC_OUTPUT.relative_to(ROOT)}")
    elif LOC_OUTPUT.read_text(encoding="utf-8-sig") != localization:
        errors.append(f"stale: {LOC_OUTPUT.relative_to(ROOT)}")
    if LEGACY_LOC_OUTPUT.exists():
        errors.append(f"obsolete generated path: {LEGACY_LOC_OUTPUT.relative_to(ROOT)}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("generate",), default="generate")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--game-root", type=Path)
    args = parser.parse_args()
    game = locate_game(args.game_root)
    rows = load_rows()
    if args.check:
        check(game, rows)
        print("Validated 33 unchanged-gameplay vanilla technologies in each track.")
    else:
        generate(game, rows)
        print("Generated 33 retitled and redated vanilla technologies in each track.")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
