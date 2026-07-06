from pathlib import Path
import re

ROOT = Path(__file__).parent / "MillenniumDawnEU4"

NAMES = {
    "adm": {
        85: "Computerized Administration", 86: "Regulatory State",
        87: "Digital Administration", 88: "Electronic Government",
        89: "Data Governance", 90: "AI-assisted Administration",
        91: "Climate-resilient State", 92: "Fusion Economy",
        93: "Planetary Administration", 94: "Post-scarcity Governance",
        95: "Mature Space-age State",
    },
    "dip": {
        85: "Containerization and Mass Media", 86: "Satellite Communications",
        87: "Global Supply Chains", 88: "Internet Economy",
        89: "Automated Logistics", 90: "AI Logistics",
        91: "Orbital Commerce", 92: "Cislunar Logistics",
        93: "Space Trade Networks", 94: "Interplanetary Logistics",
        95: "Interplanetary Diplomacy",
    },
    "mil": {
        85: "Jet and Missile Warfare", 86: "Main Battle Tanks",
        87: "Precision-guided Weapons", 88: "Network-centric Warfare",
        89: "Drones and Modern Combined Arms", 90: "Autonomous Warfare",
        91: "Directed-energy Systems", 92: "Powered Combat Systems",
        93: "Military Robotics", 94: "Autonomous Armies",
        95: "Orbital Defence",
    },
}

DESCRIPTIONS = {
    "adm": {
        85: "Electronic computers allow governments to process taxation, statistics and public records at unprecedented scale.",
        86: "Specialized regulators manage increasingly complex markets, infrastructure and public services.",
        87: "Networked databases connect ministries and replace isolated paper bureaucracies.",
        88: "Public administration and citizen services increasingly operate through secure electronic systems.",
        89: "States treat reliable data, privacy and digital identity as core public infrastructure.",
        90: "Artificial intelligence assists routine administration, forecasting and allocation of public resources.",
        91: "Government institutions adapt infrastructure, budgets and planning to long-term environmental risks.",
        92: "Commercial fusion power transforms energy policy, industrial capacity and strategic planning.",
        93: "Mature global institutions coordinate densely connected planetary infrastructure and resources.",
        94: "Automation and material abundance shift government from scarcity management toward access and stewardship.",
        95: "Space-age government integrates planetary administration with permanent off-world settlements.",
    },
    "dip": {
        85: "Container shipping and mass broadcasting bind distant markets and societies into shared commercial networks.",
        86: "Communication satellites provide continuous global links for diplomacy, navigation and trade.",
        87: "Integrated global supply chains coordinate production across many countries and transport systems.",
        88: "The internet becomes essential infrastructure for international commerce, finance and communication.",
        89: "Autonomous ports, warehouses and vehicles coordinate high-volume trade with minimal delay.",
        90: "Artificial intelligence predicts demand and continuously optimizes global transportation networks.",
        91: "Permanent orbital infrastructure supports trade, communications and industrial activity beyond Earth.",
        92: "Reliable transport between Earth and the Moon creates a unified cislunar economy.",
        93: "Interconnected orbital and planetary hubs form durable trade networks throughout near space.",
        94: "Regular interplanetary transport turns distant settlements into practical economic partners.",
        95: "Permanent off-world societies require mature institutions for interplanetary negotiation and law.",
    },
    "mil": {
        85: "Jet aircraft, guided missiles and modern assault rifles redefine operational reach and firepower.",
        86: "Main battle tanks combine mobility, protection and firepower into a standardized armoured force.",
        87: "Precision guidance and modern artillery allow targets to be struck accurately at long range.",
        88: "Digital communications connect sensors, commanders and combat units into a shared battlefield network.",
        89: "Uncrewed systems and modern combined-arms formations expand surveillance and precision strike capacity.",
        90: "Autonomous systems increasingly conduct reconnaissance, logistics and combat with limited supervision.",
        91: "Directed-energy weapons provide rapid, precise defence against aircraft, missiles and electronic systems.",
        92: "Powered armour and advanced human-machine interfaces increase the capability of individual soldiers.",
        93: "Robotic formations perform sustained combat in environments too dangerous for conventional troops.",
        94: "Integrated autonomous armies coordinate machines, sensors and weapons at operational scale.",
        95: "Orbital surveillance and defence systems extend military competition permanently into space.",
    },
}

MOVES = {
    "adm": [(88, 85, "nuclear_plant = yes")],
    "dip": [
        (89, 85, "mass_transit_system = yes"),
        (90, 86, "enable = missile_cruiser"),
        (90, 86, "enable = missile_destroyer"),
    ],
    "mil": [
        (87, 84, "enable = katyusha_rocket"),
        (87, 84, "enable = land_mattress"),
        (87, 84, "enable = carro_armato_p2640"),
        (89, 85, "enable = ak47"),
        (89, 85, "enable = m16_rifle"),
        (90, 86, "enable = m1_abrams"),
        (90, 86, "enable = leopard_2"),
        (90, 86, "enable = t64"),
        (90, 86, "enable = type62"),
        (90, 86, "enable = type90"),
        (91, 87, "enable = pzh_2000"),
        (91, 87, "enable = a2s19_msta"),
        (91, 87, "enable = m270_mlrs"),
        (93, 88, "enable = land_warrior"),
        (92, 89, "enable = armata"),
        (92, 89, "enable = m1a3_abrams"),
        (96, 93, "enable = robot_soldier"),
        (96, 93, "enable = mecha_warrior"),
    ],
}


def read(path: Path) -> str:
    return path.read_text(encoding="latin-1")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="latin-1", newline="")


def blocks(text: str) -> tuple[str, list[str]]:
    starts = [m.start() for m in re.finditer(r"(?m)^technology\s*=\s*\{", text)]
    if len(starts) != 100:
        raise RuntimeError(f"Expected 100 technologies, found {len(starts)}")
    return text[:starts[0]], [text[starts[i]:starts[i + 1] if i + 1 < 100 else len(text)] for i in range(100)]


def remove_line(block: str, statement: str) -> str:
    updated, count = re.subn(rf"(?m)^\s*{re.escape(statement)}\s*\r?\n", "", block)
    if count != 1:
        raise RuntimeError(f"Expected one source statement '{statement}', found {count}")
    return updated


def add_line(block: str, statement: str) -> str:
    if re.search(rf"(?m)^\s*{re.escape(statement)}\s*$", block):
        raise RuntimeError(f"Duplicate destination statement '{statement}'")
    end = block.rfind("}")
    return block[:end] + f"\t{statement}\n" + block[end:]


for branch in ("adm", "dip", "mil"):
    path = ROOT / f"common/technologies/{branch}.txt"
    prefix, tech = blocks(read(path))
    for source, destination, statement in MOVES[branch]:
        tech[source - 1] = remove_line(tech[source - 1], statement)
        tech[destination - 1] = add_line(tech[destination - 1], statement)
    write(path, prefix + "".join(tech))

for path in (ROOT / "localisation").glob("et_technology_l_*.yml"):
    raw = read(path)
    for branch, levels in NAMES.items():
        for level, name in levels.items():
            key = f"{branch}_tech_cs_{level}_name"
            raw = re.sub(rf'(?m)^(\s*{key}:\d*\s+).+$', rf'\g<1>"{name}"', raw)
    if path.name.endswith("_english.yml"):
        for branch, levels in DESCRIPTIONS.items():
            for level, description in levels.items():
                key = f"{branch}_tech_cs_{level}_desc"
                raw, count = re.subn(rf'(?m)^(\s*{key}:\d*\s+).+$', rf'\g<1>"{description}"', raw)
                if count != 1:
                    raise RuntimeError(f"Missing English localization {key}")
    write(path, raw)

# The Information Age previously required ADM 89. Under the synchronized
# timeline that is a 2020 technology; ADM 86 is the intended 1975 threshold.
ages = ROOT / "common/ages/01_late_ages.txt"
age_text = read(ages)
age_text, count = re.subn(
    r"(information_age\s*=\s*\{.*?can_start\s*=\s*\{\s*any_country\s*=\s*\{\s*adm_tech\s*=\s*)89",
    r"\g<1>86",
    age_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("Information Age ADM 89 trigger not found")
write(ages, age_text)

print("Reworked technology levels 85–95 and updated the Information Age trigger.")
