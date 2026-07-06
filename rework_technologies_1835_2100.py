from pathlib import Path
import re

ROOT = Path(__file__).parent / "MillenniumDawnEU4"

YEARS = {
    78: 1835, 79: 1850, 80: 1870, 81: 1890, 82: 1910, 83: 1930,
    84: 1945, 85: 1960, 86: 1975, 87: 1990, 88: 2005, 89: 2020,
    90: 2035, 91: 2050, 92: 2065, 93: 2080, 94: 2090, 95: 2100,
}

NAMES = {
    "adm": {
        78: "Industrial Administration",
        79: "Professional Civil Service",
        80: "Industrial Standardization",
        81: "Mass Politics",
        82: "Mass Production",
        83: "Managed Economy",
        84: "Post-war Administration",
    },
    "dip": {
        78: "Rail Transport",
        79: "Steam Navigation",
        80: "Telegraph Networks",
        81: "Wireless Communication",
        82: "Global Shipping",
        83: "Radio and Civil Aviation",
        84: "Radar and Modern Fleets",
    },
    "mil": {
        78: "Percussion Warfare",
        79: "Rifled Weapons",
        80: "Breech-loading Artillery",
        81: "Repeating Rifles",
        82: "Industrial Warfare",
        83: "Mechanized Warfare",
        84: "Combined Arms",
    },
}

DESCRIPTIONS = {
    "adm": {
        78: "Industrial growth requires permanent agencies capable of managing factories, infrastructure and rapidly expanding cities.",
        79: "Professional examinations and salaried officials replace patronage with a more capable civil service.",
        80: "Common technical, legal and commercial standards allow industrial economies to operate at national scale.",
        81: "Mass parties, newspapers and expanding electorates transform the relationship between government and society.",
        82: "Assembly lines and scientific management make large-scale standardized production possible.",
        83: "Modern states coordinate strategic industry, public finance and national economic planning.",
        84: "Post-war institutions combine reconstruction, social administration and professional economic management.",
    },
    "dip": {
        78: "Railways compress distance and link inland production to ports, markets and national administrations.",
        79: "Steam propulsion and iron hulls transform naval power and commercial shipping.",
        80: "Telegraph cables permit governments, merchants and commanders to communicate across continents.",
        81: "Wireless communication connects fleets and distant territories without dependence on physical cables.",
        82: "Standardized modern shipping and specialized fleets expand the scale of global commerce and naval operations.",
        83: "Radio broadcasting and civil aviation create new international networks for information and travel.",
        84: "Radar, mature capital ships and coordinated fleets define modern control of the seas.",
    },
    "mil": {
        78: "Percussion ignition and improved field artillery make firearms more reliable in all weather.",
        79: "Rifled barrels greatly improve the range and accuracy of infantry weapons.",
        80: "Breech-loading rifled artillery increases fire rate, accuracy and battlefield mobility.",
        81: "Repeating and bolt-action rifles provide disciplined infantry with sustained accurate fire.",
        82: "Machine guns, quick-firing artillery and industrial logistics reshape the battlefield.",
        83: "Armoured vehicles and motorized formations turn mobility into a decisive operational weapon.",
        84: "Tanks, infantry, artillery, aircraft and communications are integrated into combined-arms formations.",
    },
}

MOVES = {
    "adm": [(86, 83, "coal_plant = yes")],
    "dip": [
        (79, 78, "railroad = yes"),
        (80, 79, "enable = ironclad"),
        (84, 82, "enable = dreadnought"),
        (87, 84, "enable = battleship"),
    ],
    "mil": [
        (84, 82, "enable = machine_gun"),
        (84, 83, "enable = mark_heavy_tank"),
        (84, 83, "enable = renault_light_tank"),
        (84, 83, "enable = fiat3000"),
        (84, 83, "enable = 89chiro"),
        (86, 84, "enable = churchill"),
        (86, 84, "enable = tiger"),
        (86, 84, "enable = t38"),
        (86, 84, "enable = m4_sherman"),
        (86, 84, "enable = assault_rifle"),
    ],
}


def read(path: Path) -> str:
    return path.read_text(encoding="latin-1")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="latin-1", newline="")


def split_technologies(text: str) -> tuple[str, list[str]]:
    starts = [m.start() for m in re.finditer(r"(?m)^technology\s*=\s*\{", text)]
    if len(starts) != 100:
        raise RuntimeError(f"Expected 100 technology blocks, found {len(starts)}")
    prefix = text[:starts[0]]
    return prefix, [text[starts[i]: starts[i + 1] if i + 1 < len(starts) else len(text)] for i in range(len(starts))]


def remove_top_level_line(block: str, statement: str) -> str:
    pattern = re.compile(rf"(?m)^\s*{re.escape(statement)}\s*\r?\n")
    updated, count = pattern.subn("", block)
    if count != 1:
        raise RuntimeError(f"Expected one '{statement}', found {count}")
    return updated


def add_top_level_line(block: str, statement: str) -> str:
    if re.search(rf"(?m)^\s*{re.escape(statement)}\s*$", block):
        raise RuntimeError(f"Duplicate destination statement: {statement}")
    end = block.rfind("}")
    if end < 0:
        raise RuntimeError("Technology block has no closing brace")
    return block[:end] + f"\t{statement}\n" + block[end:]


for branch in ("adm", "dip", "mil"):
    path = ROOT / f"common/technologies/{branch}.txt"
    prefix, blocks = split_technologies(read(path))

    for level, year in YEARS.items():
        block = blocks[level - 1]
        block, count = re.subn(r"(?m)^(\s*year\s*=\s*)\d+", rf"\g<1>{year}", block, count=1)
        if count != 1:
            raise RuntimeError(f"Missing year in {branch} technology {level}")
        blocks[level - 1] = block

    for source, destination, statement in MOVES[branch]:
        blocks[source - 1] = remove_top_level_line(blocks[source - 1], statement)
        blocks[destination - 1] = add_top_level_line(blocks[destination - 1], statement)

    write(path, prefix + "".join(blocks))

for path in (ROOT / "localisation").glob("et_technology_l_*.yml"):
    raw = read(path)
    for branch, levels in NAMES.items():
        for level, name in levels.items():
            key = f"{branch}_tech_cs_{level}_name"
            raw, count = re.subn(rf'(?m)^(\s*{key}:\d*\s+).+$', rf'\g<1>"{name}"', raw)
            if count == 0 and path.name.endswith("_english.yml"):
                raise RuntimeError(f"Missing localization key {key} in {path.name}")
    if path.name.endswith("_english.yml"):
        for branch, levels in DESCRIPTIONS.items():
            for level, description in levels.items():
                key = f"{branch}_tech_cs_{level}_desc"
                raw, count = re.subn(rf'(?m)^(\s*{key}:\d*\s+).+$', rf'\g<1>"{description}"', raw)
                if count == 0:
                    raise RuntimeError(f"Missing localization key {key} in {path.name}")
    write(path, raw)

print("Reworked technology levels 78–84 and synchronized years through level 95.")
