from pathlib import Path
import re

ROOT = Path(__file__).parent / "MillenniumDawnEU4"
FIRST_LEVEL = 96
LAST_LEVEL = 252
FIRST_YEAR = 2150
YEAR_STEP = 50

BRANCHES = {
    "adm": {
        "name": "Future Administration",
        "description": "Long-term advances in administration expand the state's capacity to coordinate an increasingly complex society.",
    },
    "dip": {
        "name": "Future Diplomacy",
        "description": "Long-term advances in communication, transport and exchange strengthen relations across an expanding civilization.",
    },
    "mil": {
        "name": "Future Military",
        "description": "Long-term advances in organization and logistics sustain effective armed forces across increasingly complex theatres.",
    },
}


def read(path: Path) -> str:
    return path.read_text(encoding="latin-1")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="latin-1", newline="")


def keep_through_level_95(text: str) -> str:
    starts = [m.start() for m in re.finditer(r"(?m)^technology\s*=\s*\{", text)]
    if len(starts) < 96:
        raise RuntimeError(f"Expected at least 96 technology blocks, found {len(starts)}")
    return text[:starts[95]].rstrip() + "\n\n"


def effects(branch: str, level: int) -> list[str]:
    cycle = level - FIRST_LEVEL + 1
    if branch == "adm":
        result = ["governing_capacity = 25"]
        if cycle % 4 == 0:
            result.append("production_efficiency = 0.01")
        return result
    if branch == "dip":
        result = ["trade_efficiency = 0.005"]
        if cycle % 4 == 0:
            result.append("trade_range = 10")
        return result
    result = ["supply_limit = 0.01"]
    if cycle % 4 == 0:
        result.extend(("military_tactics = 0.025", "land_morale = 0.02"))
    return result


for branch in BRANCHES:
    path = ROOT / f"common/technologies/{branch}.txt"
    output = [keep_through_level_95(read(path))]
    for level in range(FIRST_LEVEL, LAST_LEVEL + 1):
        year = FIRST_YEAR + (level - FIRST_LEVEL) * YEAR_STEP
        output.append("technology = {\n")
        output.append(f"\t# Tech {level}\n")
        output.append(f"\tyear = {year}\n\n")
        output.append(f"\t# {BRANCHES[branch]['name']} {level - 95}\n")
        for effect in effects(branch, level):
            output.append(f"\t{effect}\n")
        output.append("}\n\n")
    write(path, "".join(output))


def replace_future_localization(path: Path) -> None:
    raw = read(path)
    # Remove any old or previously generated future technology entries.
    key_pattern = re.compile(
        r"(?m)^\s*(?:adm|dip|mil)_tech_cs_(?:9[6-9]|[1-9][0-9]{2,})_(?:name|desc):.*\r?\n"
    )
    raw = key_pattern.sub("", raw).rstrip() + "\n"
    entries = []
    for branch, metadata in BRANCHES.items():
        for level in range(FIRST_LEVEL, LAST_LEVEL + 1):
            sequence = level - 95
            entries.append(f' {branch}_tech_cs_{level}_name:0 "{metadata["name"]} {sequence}"\n')
            entries.append(f' {branch}_tech_cs_{level}_desc:0 "{metadata["description"]}"\n')
    write(path, raw + "".join(entries))


for path in (ROOT / "localisation").glob("et_technology_l_*.yml"):
    replace_future_localization(path)

print(f"Generated technology levels {FIRST_LEVEL}–{LAST_LEVEL} through the year 9950.")
