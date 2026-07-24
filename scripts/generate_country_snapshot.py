#!/usr/bin/env python3
"""Generate the clean EU4 2K country foundation for 2000.1.1.

The canonical CSV is bootstrapped from Extended Timeline once. Subsequent
generation treats that CSV as the source of truth. Starting technology,
economy, and reserve values are read from the Step 3 country setup CSV. The
script intentionally does not import dated country history, diplomacy, wars,
missions, or events.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "MillenniumDawnEU4"
DATA = ROOT / "data" / "countries_2000.csv"
PROVINCE_DATA = ROOT / "data" / "provinces_2000.csv"
COUNTRY_SETUP_DATA = ROOT / "data" / "country_setup_2000.csv"
ET = ROOT / "ExtendedTimeline 1.18.2" / "ExtendedTimeline"
DEFAULT_GAME_CANDIDATES = (
    Path(r"F:\Steam\steamapps\common\Europa Universalis IV"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Europa Universalis IV"),
    Path(r"C:\Program Files\Steam\steamapps\common\Europa Universalis IV"),
)
START = (2000, 1, 1)
START_NUMBER = 20000101
SUCCESSORS = {"ETI", "KOS", "MON", "SER", "SSU"}
REMOVED_RELIGIONS = {"secularism", "irreligious"}

TECH_GROUPS = {
    "modern_western": "western",
    "modern_post_soviet": "eastern",
    "modern_east_asian": "chinese",
    "modern_south_asian": "indian",
    "modern_southeast_asian": "chinese",
    "modern_middle_eastern_north_african": "muslim",
    "modern_sub_saharan_african": "sub_saharan",
    "modern_latin_american": "south_american",
    "modern_oceanian": "polynesian_tech",
}

# EU4 generates initial armies only when a valid infantry type is unlocked.
# Five is the lowest level in the canonical 2000 setup, so it is the shared
# group baseline; country history adds the remaining levels up to each tag's
# individual ADM/DIP/MIL targets.
MODERN_START_LEVEL = 5
MODERN_TECH_LEVELS = tuple(range(5, 10))

# The internal identifiers remain vanilla so the existing technology tables,
# interface art, and hard-coded institution slots continue to work. Everything
# players see and every gameplay definition is replaced with the modern model.
MODERN_INSTITUTIONS = (
    ("feudalism", "Globalized Economy", "2000.4.1", ("merchants", "1")),
    ("renaissance", "Advanced Automation", "2050.4.1", (("development_cost", "-0.05"), ("build_cost", "-0.05"))),
    ("new_world_i", "Drone Technology", "2100.4.1", ("free_leader_pool", "1")),
    ("printing_press", "Social Media", "2150.4.1", ("stability_cost_modifier", "-0.05")),
    ("global_trade", "Renewable Energy", "2200.4.1", ("global_trade_goods_size_modifier", "0.10")),
    ("manufactories", "Artificial Intelligence", "2250.4.1", ("global_prov_trade_power_modifier", "0.10")),
    ("enlightenment", "Mars Economy", "2300.4.1", ("global_tax_modifier", "0.15")),
    ("industrialization", "Space Marines", "2350.4.1", ("global_manpower_modifier", "0.25")),
)

INSTITUTION_DESCRIPTIONS = {
    "feudalism": "National economies become tightly connected through global finance, supply chains, trade, and communications.",
    "renaissance": "Advanced robotics and autonomous production transform construction, industry, and the efficient use of land.",
    "new_world_i": "Uncrewed aerial, naval, ground, and orbital systems reshape warfare and command structures.",
    "printing_press": "Networked social platforms become a central arena for public opinion, political organization, and state legitimacy.",
    "global_trade": "Large-scale renewable generation, storage, and distribution provide abundant energy for a productive economy.",
    "manufactories": "Artificial intelligence becomes embedded in government, commerce, logistics, research, and strategic planning.",
    "enlightenment": "Permanent settlement and industry on Mars create a new interplanetary tax base and commercial system.",
    "industrialization": "Specialized forces trained and equipped for warfare beyond Earth greatly expand national military manpower.",
}

INSTITUTION_HISTORICAL_ORIGINS = {
    "feudalism": 965,          # New York
    "renaissance": 1028,      # Tokyo
    "new_world_i": 953,       # Washington
    "printing_press": 4637,   # San Francisco
    "global_trade": 12,       # Copenhagen
    "manufactories": 1816,    # Beijing
    "enlightenment": 888,     # Houston
    "industrialization": 295, # Moscow
}


def tiered_technology_group(group: str, level: int) -> str:
    return f"{group}_tier_{level}"


def all_modern_technology_groups() -> dict[str, tuple[str, int]]:
    groups: dict[str, tuple[str, int]] = {}
    for group, unit_type in TECH_GROUPS.items():
        groups[group] = (unit_type, MODERN_START_LEVEL)
        for level in MODERN_TECH_LEVELS:
            groups[tiered_technology_group(group, level)] = (unit_type, level)
    return groups

EXECUTIVE_MODELS = {
    "parliamentary_republic": ("republic", "eu4_2k_parliamentary_republic"),
    "presidential_republic": ("republic", "eu4_2k_presidential_republic"),
    "semi_presidential_republic": ("republic", "eu4_2k_semi_presidential_republic"),
    "parliamentary_monarchy": ("republic", "eu4_2k_parliamentary_monarchy"),
    "absolute_monarchy": ("monarchy", "eu4_2k_absolute_monarchy"),
    "one_party_state": ("republic", "eu4_2k_one_party_state"),
    "military_government": ("republic", "eu4_2k_military_government"),
    "theocratic_state": ("theocracy", "eu4_2k_theocratic_state"),
    "transitional_government": ("republic", "eu4_2k_transitional_government"),
}
STATE_REFORMS = {
    "unitary": "eu4_2k_unitary_state",
    "federal": "eu4_2k_federal_state",
    "confederal": "eu4_2k_confederal_state",
}
COMPETITION_REFORMS = {
    "multiparty": "eu4_2k_multiparty_system",
    "dominant_party": "eu4_2k_dominant_party_system",
    "single_party": "eu4_2k_single_party_system",
    "nonpartisan": "eu4_2k_nonpartisan_system",
    "closed_authoritarian": "eu4_2k_closed_authoritarian_system",
}

# Historical executives manually audited for the initial priority region and
# featured powers. Other countries retain ET's effective 2000 leader as a
# first-pass record and are explicitly marked for later manual verification.
EXECUTIVE_OVERRIDES = {
    "USA": ("Bill Clinton", "1946.8.19", "Democratic Party", 5, 5, 3),
    "RUS": ("Vladimir Putin", "1952.10.7", "Independent", 5, 4, 4),
    "CHN": ("Jiang Zemin", "1926.8.17", "Chinese Communist Party", 5, 4, 3),
    "YUG": ("Slobodan Milosevic", "1941.8.20", "Socialist Party of Serbia", 4, 3, 4),
    "GER": ("Gerhard Schroder", "1944.4.7", "Social Democratic Party", 5, 4, 3),
    "FR2": ("Jacques Chirac", "1932.11.29", "Rally for the Republic", 4, 5, 3),
    "GBR": ("Tony Blair", "1953.5.6", "Labour Party", 5, 5, 3),
    "ALB": ("Ilir Meta", "1969.3.24", "Socialist Party", 4, 3, 2),
    "HAB": ("Viktor Klima", "1947.6.4", "Social Democratic Party", 4, 4, 2),
    "BEL": ("Guy Verhofstadt", "1953.4.11", "Open VLD Coalition", 4, 4, 2),
    "BLR": ("Alexander Lukashenko", "1954.8.30", "Independent", 4, 2, 3),
    "BUL": ("Ivan Kostov", "1949.12.23", "Union of Democratic Forces", 4, 4, 2),
    "CRO": ("Zlatko Matesa", "1949.6.17", "Croatian Democratic Union", 3, 3, 2),
    "CZE": ("Milos Zeman", "1944.9.28", "Social Democratic Party", 4, 4, 2),
    "DAN": ("Poul Nyrup Rasmussen", "1943.6.15", "Social Democrats", 4, 4, 2),
    "EST": ("Mart Laar", "1960.4.22", "Pro Patria Union", 4, 4, 2),
    "FIN": ("Paavo Lipponen", "1941.4.23", "Social Democratic Party", 4, 4, 2),
    "GRE": ("Costas Simitis", "1936.6.23", "PASOK", 4, 4, 2),
    "HUN": ("Viktor Orban", "1963.5.31", "Fidesz", 4, 3, 2),
    "ICE": ("David Oddsson", "1948.1.17", "Independence Party", 4, 4, 2),
    "IRE": ("Bertie Ahern", "1951.9.12", "Fianna Fail", 4, 4, 2),
    "ITA": ("Massimo D'Alema", "1949.4.20", "Democrats of the Left", 4, 4, 2),
    "LTV": ("Andris Skele", "1958.1.16", "People's Party", 4, 3, 2),
    "LIT": ("Andrius Kubilius", "1956.12.8", "Homeland Union", 4, 4, 2),
    "LUX": ("Jean-Claude Juncker", "1954.12.9", "Christian Social People's Party", 5, 5, 2),
    "MAC": ("Ljubco Georgievski", "1966.1.17", "VMRO-DPMNE", 3, 3, 2),
    "MDV": ("Dumitru Braghis", "1957.12.28", "Independent", 3, 3, 2),
    "NED": ("Wim Kok", "1938.9.29", "Labour Party", 5, 4, 2),
    "NOR": ("Kjell Magne Bondevik", "1947.9.3", "Christian Democratic Party", 4, 4, 2),
    "POL": ("Jerzy Buzek", "1940.7.3", "Solidarity Electoral Action", 4, 4, 2),
    "POR": ("Antonio Guterres", "1949.4.30", "Socialist Party", 5, 4, 2),
    "RMN": ("Mugur Isarescu", "1949.8.1", "Independent", 5, 3, 2),
    "SVK": ("Mikulas Dzurinda", "1955.2.4", "Slovak Democratic Coalition", 4, 4, 2),
    "SVN": ("Janez Drnovsek", "1950.5.17", "Liberal Democracy of Slovenia", 4, 4, 2),
    "SPA": ("Jose Maria Aznar", "1953.2.25", "People's Party", 4, 4, 2),
    "SWE": ("Goran Persson", "1949.1.20", "Social Democratic Party", 4, 4, 2),
    "SWI": ("Adolf Ogi", "1942.7.18", "Swiss People's Party", 4, 4, 2),
    "UKR": ("Leonid Kuchma", "1938.8.9", "Independent", 4, 3, 3),
    "TKY": ("Bulent Ecevit", "1925.5.28", "Democratic Left Party", 4, 4, 3),
    "CYP": ("Glafcos Clerides", "1919.4.24", "Democratic Rally", 4, 4, 2),
    "GEO": ("Eduard Shevardnadze", "1928.1.25", "Union of Citizens of Georgia", 3, 5, 2),
    "ARM": ("Robert Kocharyan", "1954.8.31", "Independent", 4, 3, 3),
    "AZE": ("Heydar Aliyev", "1923.5.10", "New Azerbaijan Party", 4, 3, 3),
    "BGD": ("Sheikh Hasina", "1947.9.28", "Awami League", 4, 3, 2),
    "BHE": ("Haris Silajdzic", "1945.10.1", "Party for Bosnia and Herzegovina", 3, 4, 2),
    "INI": ("Atal Bihari Vajpayee", "1924.12.25", "Bharatiya Janata Party", 4, 4, 3),
    "ISR": ("Ehud Barak", "1942.2.12", "One Israel", 4, 4, 4),
    "JAP": ("Keizo Obuchi", "1937.6.25", "Liberal Democratic Party", 4, 4, 2),
    "KHM": ("Hun Sen", "1952.8.5", "Cambodian People's Party", 4, 3, 3),
    "LES": ("Pakalitha Mosisili", "1945.3.14", "Lesotho Congress for Democracy", 3, 3, 2),
    "MLA": ("Mahathir Mohamad", "1925.7.10", "Barisan Nasional", 5, 4, 3),
    "NPL": ("Krishna Prasad Bhattarai", "1924.12.13", "Nepali Congress", 3, 3, 2),
    "SIA": ("Chuan Leekpai", "1938.7.28", "Democrat Party", 4, 4, 2),
    "SOM": ("Interim National Administration", "1950.1.1", "Transitional authorities", 1, 1, 2),
}

BIRTH_OVERRIDES = {
    "ANB": "1938.2.21", "BBD": "1949.10.17", "BHR": "1950.1.28",
    "BHU": "1955.11.11", "BLZ": "1944.3.19", "CAN": "1934.1.11",
    "CMR": "1933.2.13", "CNG": "1943.11.23", "DJI": "1947.11.27",
    "EGY": "1928.5.4", "EQG": "1942.6.5", "ERT": "1946.2.2",
    "GRN": "1946.11.12", "IRA": "1939.4.19", "IVO": "1941.3.16",
    "JOR": "1962.1.30", "KUW": "1926.6.29", "MOR": "1963.8.21",
    "MZM": "1939.10.22", "NCR": "1946.1.23", "NOK": "1942.2.16",
    "PLS": "1929.8.24", "PNG": "1946.6.12", "QTR": "1952.1.1",
    "RWA": "1950.4.1", "SAU": "1921.3.16", "SUD": "1944.1.1",
    "SVG": "1931.5.15", "SWZ": "1968.4.19", "TGO": "1935.12.26",
    "TJK": "1952.10.5", "TOG": "1918.7.4", "UAE": "1918.5.6",
    "UGA": "1944.9.15", "UZB": "1938.1.30", "VNZ": "1954.7.28",
}

PARLIAMENTARY_MONARCHIES = {
    "GBR", "DAN", "NOR", "SWE", "NED", "BEL", "SPA", "JAP", "MLA",
    "KHM", "SIA", "LES", "JOR", "KUW", "MOR",
}
ABSOLUTE_MONARCHIES = {"SAU", "OMA", "QTR", "UAE", "BRU", "BHR", "BHU", "SWZ"}
ONE_PARTY_STATES = {"CHN", "NOK", "VTN", "LAO", "CUB", "ERT"}
MILITARY_GOVERNMENTS = {"MNM", "PAK", "SUD", "GMB"}
THEOCRATIC_STATES = {"PAP"}
TRANSITIONAL_GOVERNMENTS = {"SOM"}
SEMI_PRESIDENTIAL = {
    "FR2", "RUS", "UKR", "RMN", "POR", "FIN", "LIT", "POL", "CRO",
    "ARM", "GEO", "AZE", "KZK", "KYR", "MDV", "MNG", "SGL",
}
PARLIAMENTARY_REPUBLICS = {
    "ALB", "HAB", "BEL", "BHE", "BUL", "CZE", "GER", "GRE", "HUN",
    "ICE", "IRE", "ITA", "LTV", "LUX", "MAC", "NED", "NOR", "SVK",
    "SVN", "SWE", "SWI", "CAN", "INI", "ISR", "RSA", "NZL", "AUS",
    "BGD", "NPL", "SIA", "JAP", "GBR", "DAN", "SPA", "MLA",
}
AUTHORITARIAN_STATES = {
    "BLR", "LBY", "SYR", "IRQ", "EGY", "TRK", "UZB", "TJK", "KZK",
    "YUG", "ZIM", "TUN", "ALG", "CMR", "GAB", "EQG", "RWA", "UGA",
    "BFA", "TGO", "GUI", "CNG", "DRC", "ETH", "SOM", "AFG",
}
FEDERAL_STATES = {
    "USA", "CAN", "MEX", "BRZ", "LAP", "GER", "HAB", "SWI", "BEL",
    "RUS", "INI", "PAK", "MLA", "AUS", "NGR", "ETH", "UAE", "VNZ",
    "BHE", "YUG", "MIC", "SKN", "COM",
}
CONFEDERAL_STATES = {"BHE"}
POST_SOVIET = {
    "RUS", "UKR", "BLR", "MDV", "EST", "LTV", "LIT", "GEO", "ARM",
    "AZE", "KZK", "UZB", "TRK", "KYR", "TJK",
}
EAST_ASIAN = {"CHN", "JAP", "SKO", "NOK", "FRM", "MNG"}
SOUTH_ASIAN = {"INI", "PAK", "BGD", "NPL", "BHU", "SRL", "MDV", "AFG"}
SOUTHEAST_ASIAN = {"MNM", "SIA", "LAO", "KHM", "VTN", "MLA", "IDN", "PHI", "BRU", "SGA", "ETI"}
MENA = {
    "MOR", "ALG", "TUN", "LBY", "EGY", "SUD", "ISR", "PLS", "LEB",
    "SYR", "IRQ", "JOR", "SAU", "YEM", "OMA", "UAE", "QTR", "BHR",
    "KUW", "IRA", "TKY", "DJI", "MRT",
}
LATIN_AMERICAN = {
    "MEX", "GTM", "BLZ", "ELS", "HON", "NCR", "COS", "PNM", "CUB",
    "BHM", "JMC", "HAT", "DOM", "SKN", "ANB", "DMN", "SLU", "SVG",
    "BBD", "GRN", "COL", "VNZ", "GYA", "SRN", "ECU", "PEU", "BOL",
    "BRZ", "LAP", "CHL", "URU",
}
OCEANIAN = {"PNG", "FIJ", "SLM", "VNU", "SAM", "TOG", "TVL", "NAU", "KIR", "MRS", "PLU", "MIC"}

RELIGION_FALLBACKS = {
    "chalcedonism": "orthodox",
    "slavic": "orthodox",
    "bogomilism": "orthodox",
    "nestorian": "coptic",
    "manichean": "zoroastrian",
    "jainism": "hinduism",
    "confucianism": "confucianism",
}

NAME_ADJ_OVERRIDES = {
    "ALG": ("Algeria", "Algerian"),
    "BHM": ("Bahamas", "Bahamian"),
    "CAF": ("Central African Republic", "Central African"),
    "CMO": ("Comoros", "Comorian"),
    "CNG": ("Republic of the Congo", "Congolese"),
    "CZE": ("Czech Republic", "Czech"),
    "DRC": ("Democratic Republic of the Congo", "Congolese"),
    "FR2": ("France", "French"),
    "FRM": ("Taiwan", "Taiwanese"),
    "GBR": ("United Kingdom", "British"),
    "GMB": ("The Gambia", "Gambian"),
    "GZI": ("Zimbabwe", "Zimbabwean"),
    "INI": ("India", "Indian"),
    "ISR": ("Israel", "Israeli"),
    "JOR": ("Jordan", "Jordanian"),
    "KHA": ("Mongolia", "Mongolian"),
    "KHM": ("Cambodia", "Cambodian"),
    "LAP": ("Argentina", "Argentine"),
    "LUX": ("Luxembourg", "Luxembourgish"),
    "NZL": ("New Zealand", "New Zealander"),
    "PNM": ("Panama", "Panamanian"),
    "SIA": ("Thailand", "Thai"),
    "STP": ("Sao Tome and Principe", "Sao Tomean"),
    "TRK": ("Turkmenistan", "Turkmen"),
    "UAE": ("United Arab Emirates", "Emirati"),
    "UKR": ("Ukraine", "Ukrainian"),
    "VIT": ("Fiji", "Fijian"),
}
SUCCESSOR_DEFAULTS = {
    "ETI": {"name": "East Timor", "capital": "2692", "culture": "moluccan", "religion": "catholic"},
    "KOS": {"name": "Kosovo", "capital": "1766", "culture": "albanian", "religion": "sunni"},
    "MON": {"name": "Montenegro", "capital": "1853", "culture": "serbian", "religion": "orthodox"},
    "SER": {"name": "Serbia", "capital": "4239", "culture": "serbian", "religion": "orthodox"},
    "SSU": {"name": "South Sudan", "capital": "1227", "culture": "nubian", "religion": "coptic"},
}

CSV_FIELDS = [
    "tag", "active_2000", "name", "adjective", "capital", "primary_culture",
    "accepted_cultures", "religion", "government_model", "state_structure",
    "political_competition", "government_rank", "ruling_group", "executive",
    "executive_birth", "head_of_state", "adm", "dip", "mil", "technology_group",
    "unit_type", "graphical_culture", "color_r", "color_g", "color_b",
    "country_definition_source", "flag_source", "verification_notes",
]


Entry = tuple[str | None, str | list["Entry"]]


def find_game_root(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).resolve()
        if (path / "eu4.exe").exists():
            return path
        raise SystemExit(f"EU4 game root does not contain eu4.exe: {path}")
    for candidate in DEFAULT_GAME_CANDIDATES:
        if (candidate / "eu4.exe").exists():
            return candidate
    raise SystemExit("EU4 game root not found; pass --game-root")


def strip_comments(text: str) -> str:
    output: list[str] = []
    quoted = False
    escaped = False
    comment = False
    for char in text:
        if comment:
            if char in "\r\n":
                output.append(char)
                comment = False
            continue
        if escaped:
            output.append(char)
            escaped = False
        elif char == "\\" and quoted:
            output.append(char)
            escaped = True
        elif char == '"':
            output.append(char)
            quoted = not quoted
        elif char == "#" and not quoted:
            comment = True
        else:
            output.append(char)
    return "".join(output)


TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=#"]+')


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(strip_comments(text))


def parse_scope(tokens: Sequence[str], index: int = 0, stop_on_brace: bool = False) -> tuple[list[Entry], int]:
    entries: list[Entry] = []
    while index < len(tokens):
        token = tokens[index]
        if token == "}" and stop_on_brace:
            return entries, index + 1
        if token in {"{", "=", "}"}:
            index += 1
            continue
        if index + 1 < len(tokens) and tokens[index + 1] == "=":
            key = unquote(token)
            index += 2
            if index < len(tokens) and tokens[index] == "{":
                value, index = parse_scope(tokens, index + 1, True)
            elif index < len(tokens):
                value = unquote(tokens[index])
                index += 1
            else:
                value = ""
            entries.append((key, value))
        else:
            entries.append((None, unquote(token)))
            index += 1
    return entries, index


def parse_file(path: Path) -> list[Entry]:
    source = path.read_bytes()
    try:
        raw = source.decode("utf-8-sig")
    except UnicodeDecodeError:
        raw = source.decode("cp1252", errors="replace")
    return parse_scope(tokenize(raw))[0]


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1].replace(r'\"', '"').replace(r"\\", "\\")
    return value


def quote(value: str) -> str:
    return '"' + value.replace("\\", r"\\").replace('"', r'\"') + '"'


def date_number(value: str) -> int | None:
    match = re.fullmatch(r"(-?\d+)\.(\d+)\.(\d+)", value)
    if not match:
        return None
    return int(match[1]) * 10000 + int(match[2]) * 100 + int(match[3])


def scalar(entries: Sequence[Entry], key: str, default: str = "") -> str:
    result = default
    for candidate, value in entries:
        if candidate == key and isinstance(value, str):
            result = value
    return result


def scopes(entries: Sequence[Entry], key: str) -> Iterator[list[Entry]]:
    for candidate, value in entries:
        if candidate == key and isinstance(value, list):
            yield value


@dataclass
class CountryState:
    government: str = "republic"
    rank: str = "2"
    culture: str = ""
    accepted: list[str] = field(default_factory=list)
    religion: str = ""
    last_conventional_religion: str = ""
    technology_group: str = "western"
    unit_type: str = "western"
    capital: str = ""
    monarch: dict[str, str] = field(default_factory=dict)

    def apply(self, entries: Sequence[Entry]) -> None:
        scalar_fields = {
            "government": "government", "government_rank": "rank",
            "primary_culture": "culture", "technology_group": "technology_group",
            "unit_type": "unit_type", "capital": "capital",
        }
        for key, value in entries:
            if key in scalar_fields and isinstance(value, str):
                setattr(self, scalar_fields[key], value)
            elif key == "religion" and isinstance(value, str):
                self.religion = value
                if value not in REMOVED_RELIGIONS:
                    self.last_conventional_religion = value
            elif key == "add_accepted_culture" and isinstance(value, str):
                if value not in self.accepted:
                    self.accepted.append(value)
            elif key == "remove_accepted_culture" and isinstance(value, str):
                if value in self.accepted:
                    self.accepted.remove(value)
            elif key == "monarch" and isinstance(value, list):
                parsed = {k: v for k, v in value if k and isinstance(v, str)}
                if parsed.get("name"):
                    self.monarch = parsed


def effective_country_state(path: Path) -> CountryState:
    root = parse_file(path)
    state = CountryState()
    dated: list[tuple[int, list[Entry]]] = []
    for key, value in root:
        number = date_number(key or "")
        if number is not None and isinstance(value, list):
            if number <= START_NUMBER:
                dated.append((number, value))
        elif key is not None:
            state.apply([(key, value)])
    for _, entries in sorted(dated, key=lambda item: item[0]):
        state.apply(entries)
    return state


def effective_owner(path: Path) -> str:
    root = parse_file(path)
    owner = ""
    dated: list[tuple[int, list[Entry]]] = []
    for key, value in root:
        number = date_number(key or "")
        if number is not None and isinstance(value, list):
            if number <= START_NUMBER:
                dated.append((number, value))
        elif key == "owner" and isinstance(value, str):
            owner = value
    for _, entries in sorted(dated, key=lambda item: item[0]):
        candidate = scalar(entries, "owner")
        if candidate:
            owner = candidate
    return owner


def load_tag_map(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    pattern = re.compile(r'^\s*([A-Z0-9]{3})\s*=\s*"([^"]+)"')
    for line in path.read_bytes().decode("cp1252", errors="replace").splitlines():
        match = pattern.match(line.split("#", 1)[0])
        if match:
            result[match[1]] = match[2]
    return result


def load_localisation(paths: Iterable[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    pattern = re.compile(r'^\s*([^\s:#]+):\d*\s+"(.*)"\s*$')
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            match = pattern.match(line)
            if match:
                result[match[1]] = match[2].replace(r'\"', '"')
    return result


def history_files_by_tag() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted((ET / "history" / "countries").glob("*.txt")):
        match = re.match(r"^([A-Z0-9]{3}) - ", path.name)
        if match:
            result[match[1]] = path
    return result


def province_continents() -> dict[int, str]:
    result: dict[int, str] = {}
    for group, value in parse_file(MOD / "map" / "continent.txt"):
        if group and isinstance(value, list):
            for key, item in value:
                if key is None and isinstance(item, str) and item.isdigit():
                    result[int(item)] = group
    return result


def non_land_provinces() -> set[int]:
    text = (MOD / "map" / "default.map").read_text(encoding="cp1252")
    result: set[int] = set()
    for key in ("sea_starts", "lakes"):
        match = re.search(rf"(?s)\b{key}\s*=\s*\{{(.*?)\}}", text)
        if not match:
            raise RuntimeError(f"Missing {key} block in default.map")
        result.update(map(int, re.findall(r"\b\d+\b", match.group(1))))
    return result


def definition_identity(path: Path) -> tuple[str, tuple[int, int, int]]:
    text = path.read_bytes().decode("cp1252", errors="replace")
    gfx = re.search(r"(?m)^\s*graphical_culture\s*=\s*([A-Za-z0-9_]+)", text)
    color = re.search(r"(?ms)^\s*color\s*=\s*\{\s*(\d+)\s+(\d+)\s+(\d+)", text)
    return (
        gfx.group(1) if gfx else "westerngfx",
        tuple(map(int, color.groups())) if color else (128, 128, 128),
    )


def clean_name(tag: str, history: Path, loc: dict[str, str]) -> str:
    if tag in NAME_ADJ_OVERRIDES:
        return NAME_ADJ_OVERRIDES[tag][0]
    match = re.match(r"^[A-Z0-9]{3} - (.+)\.txt$", history.name)
    if match:
        return match[1].replace("Modern ", "")
    localized = loc.get(tag, "").strip()
    return localized if localized and localized != tag else tag


def slug(value: str) -> str:
    value = value.lower().replace("'", "")
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value or "independent"


def choose_government(tag: str, state: CountryState) -> tuple[str, str, str]:
    if tag in THEOCRATIC_STATES or state.government == "theocracy":
        model = "theocratic_state"
    elif tag in ABSOLUTE_MONARCHIES:
        model = "absolute_monarchy"
    elif tag in PARLIAMENTARY_MONARCHIES:
        model = "parliamentary_monarchy"
    elif tag in ONE_PARTY_STATES:
        model = "one_party_state"
    elif tag in MILITARY_GOVERNMENTS:
        model = "military_government"
    elif tag in TRANSITIONAL_GOVERNMENTS:
        model = "transitional_government"
    elif tag in SEMI_PRESIDENTIAL:
        model = "semi_presidential_republic"
    elif tag in PARLIAMENTARY_REPUBLICS:
        model = "parliamentary_republic"
    else:
        model = "presidential_republic"
    structure = "confederal" if tag in CONFEDERAL_STATES else "federal" if tag in FEDERAL_STATES else "unitary"
    if model == "one_party_state":
        competition = "single_party"
    elif model in {"absolute_monarchy", "theocratic_state"}:
        competition = "nonpartisan"
    elif model == "military_government" or tag in AUTHORITARIAN_STATES:
        competition = "closed_authoritarian"
    elif tag in {"SGA", "MLA", "MEX", "JAP"}:
        competition = "dominant_party"
    else:
        competition = "multiparty"
    return model, structure, competition


def choose_tech_group(tag: str, continent: str) -> str:
    if tag in POST_SOVIET:
        return "modern_post_soviet"
    if tag in EAST_ASIAN:
        return "modern_east_asian"
    if tag in SOUTH_ASIAN:
        return "modern_south_asian"
    if tag in SOUTHEAST_ASIAN:
        return "modern_southeast_asian"
    if tag in MENA:
        return "modern_middle_eastern_north_african"
    if tag in LATIN_AMERICAN:
        return "modern_latin_american"
    if tag in OCEANIAN or continent == "oceania" and tag not in {"AUS", "NZL"}:
        return "modern_oceanian"
    if continent == "africa":
        return "modern_sub_saharan_african"
    return "modern_western"


def normalized_religion(state: CountryState, vanilla: set[str]) -> str:
    candidate = state.last_conventional_religion or state.religion
    candidate = RELIGION_FALLBACKS.get(candidate, candidate)
    if candidate in vanilla:
        return candidate
    return "catholic"


def collect_religions(path: Path) -> set[str]:
    result: set[str] = set()
    metadata = {"flags_with_emblem_percentage", "flag_emblem_index_range", "center_of_religion"}
    for _, group in parse_file(path):
        if not isinstance(group, list):
            continue
        for key, value in group:
            if key and key not in metadata and isinstance(value, list) and any(k == "color" for k, _ in value):
                result.add(key)
    return result


def collect_cultures(path: Path) -> set[str]:
    result: set[str] = set()
    metadata = {"graphical_culture", "male_names", "female_names", "dynasty_names"}
    for _, group in parse_file(path):
        if not isinstance(group, list):
            continue
        for key, value in group:
            if key and key not in metadata and isinstance(value, list):
                result.add(key)
    return result


def bootstrap_rows(game: Path) -> list[dict[str, str]]:
    base_tags = load_tag_map(game / "common" / "country_tags" / "00_countries.txt")
    et_tags = load_tag_map(ET / "common" / "country_tags" / "et_countries.txt")
    histories = history_files_by_tag()
    active = {effective_owner(path) for path in sorted((ET / "history" / "provinces").glob("*.txt"))}
    active.discard("")
    if len(active) != 188:
        raise RuntimeError(f"Expected 188 active owner tags at 2000.1.1, found {len(active)}")
    tags = sorted(active | SUCCESSORS)
    loc = load_localisation(
        list((game / "localisation").glob("*_l_english.yml"))
        + list((ET / "localisation").glob("*_l_english.yml"))
    )
    vanilla_religions = collect_religions(game / "common" / "religions" / "00_religion.txt")
    continents = province_continents()
    rows: list[dict[str, str]] = []
    for tag in tags:
        history = histories.get(tag)
        if history is None:
            raise RuntimeError(f"No ET country history for {tag}")
        state = effective_country_state(history)
        defaults = SUCCESSOR_DEFAULTS.get(tag, {})
        name = defaults.get("name") or clean_name(tag, history, loc)
        adjective = NAME_ADJ_OVERRIDES.get(tag, ("", ""))[1] or loc.get(f"{tag}_ADJ", "").strip() or name
        capital = defaults.get("capital") or state.capital
        culture = defaults.get("culture") or state.culture
        culture = {"slovenian": "slovene"}.get(culture, culture)
        religion = defaults.get("religion") or normalized_religion(state, vanilla_religions)
        model, structure, competition = choose_government(tag, state)
        source_rel = et_tags.get(tag) or base_tags.get(tag)
        if not source_rel:
            raise RuntimeError(f"No country definition mapping for {tag}")
        source_root = ET if tag in et_tags else game
        source_definition = source_root / "common" / source_rel
        if not source_definition.exists():
            raise RuntimeError(f"Missing country definition for {tag}: {source_definition}")
        graphical, color = definition_identity(source_definition)
        et_flag = ET / "gfx" / "flags" / f"{tag}.tga"
        base_flag = game / "gfx" / "flags" / f"{tag}.tga"
        flag_path = et_flag if et_flag.exists() else base_flag
        if not flag_path.exists():
            raise RuntimeError(f"Missing flag for {tag}")
        monarch = state.monarch
        head_of_state = monarch.get("name", "")
        executive = head_of_state
        birth = monarch.get("birth_date", "1950.1.1")
        if birth == "1950.1.1" and tag in BIRTH_OVERRIDES:
            birth = BIRTH_OVERRIDES[tag]
        party = "Independent or nonpartisan"
        adm = monarch.get("adm", "3")
        dip = monarch.get("dip", "3")
        mil = monarch.get("mil", "3")
        notes = "ET 2000 snapshot; manual verification pending"
        if tag in EXECUTIVE_OVERRIDES:
            executive, birth, party, adm_i, dip_i, mil_i = EXECUTIVE_OVERRIDES[tag]
            adm, dip, mil = str(adm_i), str(dip_i), str(mil_i)
            notes = "Priority-region executive manually audited for 2000.1.1"
        if tag in SUCCESSORS:
            executive = ""
            birth = ""
            party = "Dormant successor"
            head_of_state = ""
            notes = "Dormant historical successor; leadership assigned by formation event"
        try:
            capital_id = int(capital)
        except ValueError as exc:
            raise RuntimeError(f"Invalid capital for {tag}: {capital}") from exc
        continent = continents.get(capital_id, "")
        tech = choose_tech_group(tag, continent)
        unit_type = TECH_GROUPS[tech]
        rows.append({
            "tag": tag,
            "active_2000": "yes" if tag in active else "no",
            "name": name,
            "adjective": adjective,
            "capital": str(capital_id),
            "primary_culture": culture,
            "accepted_cultures": "|".join({"slovenian": "slovene"}.get(value, value) for value in state.accepted),
            "religion": religion,
            "government_model": model,
            "state_structure": structure,
            "political_competition": competition,
            "government_rank": state.rank if state.rank in {"1", "2", "3"} else "2",
            "ruling_group": party,
            "executive": executive,
            "executive_birth": birth,
            "head_of_state": head_of_state,
            "adm": str(max(1, min(6, int(adm or 3)))),
            "dip": str(max(1, min(6, int(dip or 3)))),
            "mil": str(max(1, min(6, int(mil or 3)))),
            "technology_group": tech,
            "unit_type": unit_type,
            "graphical_culture": graphical,
            "color_r": str(color[0]), "color_g": str(color[1]), "color_b": str(color[2]),
            "country_definition_source": ("et:" if source_root == ET else "base:") + source_rel,
            "flag_source": ("et:" if flag_path == et_flag else "base:") + f"gfx/flags/{tag}.tga",
            "verification_notes": notes,
        })
    return rows


def write_manifest(rows: Sequence[dict[str, str]]) -> None:
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_manifest() -> list[dict[str, str]]:
    with DATA.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_technology_setup(rows: Sequence[dict[str, str]]) -> dict[str, dict[str, int]]:
    """Load canonical technology, economy, and reserve values for active tags."""
    if not COUNTRY_SETUP_DATA.exists():
        raise RuntimeError(
            "Missing data/country_setup_2000.csv; run generate_starting_world.py first"
        )
    with COUNTRY_SETUP_DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        numeric_fields = {
            "adm_tech", "dip_tech", "mil_tech", "technology_tier",
            "treasury", "inflation", "stability", "prestige", "corruption",
            "legitimacy_or_tradition", "manpower", "sailors",
            "economic_tier", "infrastructure_tier",
        }
        required = {"tag", *numeric_fields}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError("country_setup_2000.csv is missing setup columns")
        setup: dict[str, dict[str, int]] = {}
        for source in reader:
            tag = source["tag"]
            if tag in setup:
                raise RuntimeError(f"Duplicate country setup for {tag}")
            try:
                levels = {key: int(source[key]) for key in numeric_fields}
            except ValueError as exc:
                raise RuntimeError(f"Invalid numeric country setup for {tag}") from exc
            technology_levels = [
                levels[key] for key in ("adm_tech", "dip_tech", "mil_tech")
            ]
            if any(
                level < MODERN_START_LEVEL or level > 32
                for level in technology_levels
            ):
                raise RuntimeError(
                    f"{tag}: technology must be between {MODERN_START_LEVEL} and 32"
                )
            if len(set(technology_levels)) != 1:
                raise RuntimeError(
                    f"{tag}: tiered startup requires equal ADM/DIP/MIL levels"
                )
            if levels["treasury"] < 0 or levels["inflation"] < 0:
                raise RuntimeError(f"{tag}: treasury and inflation cannot be negative")
            if not -3 <= levels["stability"] <= 3:
                raise RuntimeError(f"{tag}: stability must be between -3 and 3")
            if not -100 <= levels["prestige"] <= 100:
                raise RuntimeError(f"{tag}: prestige must be between -100 and 100")
            if not 0 <= levels["corruption"] <= 100:
                raise RuntimeError(f"{tag}: corruption must be between 0 and 100")
            if not 0 <= levels["legitimacy_or_tradition"] <= 100:
                raise RuntimeError(f"{tag}: legitimacy/tradition must be between 0 and 100")
            if levels["manpower"] < 0 or levels["sailors"] < 0:
                raise RuntimeError(f"{tag}: manpower and sailors cannot be negative")
            if not 1 <= levels["economic_tier"] <= 5:
                raise RuntimeError(f"{tag}: economic tier must be between 1 and 5")
            if not 1 <= levels["infrastructure_tier"] <= 5:
                raise RuntimeError(f"{tag}: infrastructure tier must be between 1 and 5")
            setup[tag] = levels
    active = {row["tag"] for row in rows if row["active_2000"] == "yes"}
    if set(setup) != active:
        missing = sorted(active - set(setup))
        extra = sorted(set(setup) - active)
        raise RuntimeError(
            "Country setup tags do not match active countries; "
            f"missing={missing}, extra={extra}"
        )
    return setup


def validate_rows(rows: Sequence[dict[str, str]], game: Path) -> None:
    active = [row for row in rows if row["active_2000"] == "yes"]
    dormant = [row for row in rows if row["active_2000"] == "no"]
    errors: list[str] = []
    if len(rows) != 193:
        errors.append(f"expected 193 rows, found {len(rows)}")
    if len(active) != 188:
        errors.append(f"expected 188 active rows, found {len(active)}")
    if {row["tag"] for row in dormant} != SUCCESSORS:
        errors.append("dormant successor set does not match ETI/KOS/MON/SER/SSU")
    tags = [row["tag"] for row in rows]
    if len(tags) != len(set(tags)):
        errors.append("duplicate country tags")
    vanilla_religions = collect_religions(game / "common" / "religions" / "00_religion.txt")
    non_land = non_land_provinces()
    base_cultures = collect_cultures(game / "common" / "cultures" / "00_cultures.txt")
    et_cultures = collect_cultures(ET / "common" / "cultures" / "00_cultures.txt")
    for row in rows:
        tag = row["tag"]
        try:
            capital = int(row["capital"])
        except ValueError:
            errors.append(f"{tag}: invalid capital {row['capital']}")
            continue
        if not 1 <= capital <= 4941:
            errors.append(f"{tag}: capital outside map bounds: {capital}")
        elif capital in non_land:
            errors.append(f"{tag}: capital is a sea or lake province: {capital}")
        if row["religion"] not in vanilla_religions:
            errors.append(f"{tag}: non-vanilla religion {row['religion']}")
        if row["religion"] in REMOVED_RELIGIONS:
            errors.append(f"{tag}: forbidden religion {row['religion']}")
        cultures = [row["primary_culture"], *filter(None, row["accepted_cultures"].split("|"))]
        for culture in cultures:
            if culture not in base_cultures and culture not in et_cultures:
                errors.append(f"{tag}: undefined culture {culture}")
        if row["government_model"] not in EXECUTIVE_MODELS:
            errors.append(f"{tag}: invalid government model {row['government_model']}")
        if row["state_structure"] not in STATE_REFORMS:
            errors.append(f"{tag}: invalid state structure {row['state_structure']}")
        if row["political_competition"] not in COMPETITION_REFORMS:
            errors.append(f"{tag}: invalid political competition {row['political_competition']}")
        if row["technology_group"] not in TECH_GROUPS:
            errors.append(f"{tag}: invalid technology group {row['technology_group']}")
        if row["active_2000"] == "yes":
            if not row["executive"]:
                errors.append(f"{tag}: active country has no executive")
            number = date_number(row["executive_birth"])
            if number is None or number >= START_NUMBER:
                errors.append(f"{tag}: invalid executive birth date {row['executive_birth']}")
    if errors:
        raise RuntimeError("Manifest validation failed:\n- " + "\n- ".join(errors))


def government_reforms_text() -> str:
    icons = {
        "parliamentary_republic": "judge", "presidential_republic": "man_on_podium",
        "semi_presidential_republic": "states_general", "parliamentary_monarchy": "parliament_hall",
        "absolute_monarchy": "crown", "one_party_state": "political_dynasties",
        "military_government": "military_governance", "theocratic_state": "religious_state",
        "transitional_government": "republicanism",
    }
    lines = ["# Generated by scripts/generate_country_snapshot.py", ""]
    for model, (_, reform) in EXECUTIVE_MODELS.items():
        lines.extend([
            f"{reform} = {{", f'\ticon = "{icons[model]}"', "\tallow_normal_conversion = no",
            "\tvalid_for_nation_designer = no", "\tlock_level_when_selected = yes",
            f"\tpotential = {{ has_reform = {reform} }}", "\tmodifiers = { }",
            "\tai = { factor = 0 }", "}", "",
        ])
    for reform in [*STATE_REFORMS.values(), *COMPETITION_REFORMS.values()]:
        lines.extend([
            f"{reform} = {{", '\ticon = "administrative_divisions"',
            "\tallow_normal_conversion = no", "\tvalid_for_nation_designer = no",
            "\tlock_level_when_selected = yes", f"\tpotential = {{ has_reform = {reform} }}",
            "\tmodifiers = { }", "\tai = { factor = 0 }", "}", "",
        ])
    return "\n".join(lines)


def technology_text(game: Path) -> str:
    source = (game / "common" / "technology.txt").read_text(encoding="cp1252")
    marker = "\n}\n\ntables = {"
    index = source.rfind(marker)
    if index < 0:
        raise RuntimeError("Could not locate technology groups closing marker")
    blocks = ["\n\t# EU4 2K equal-cost regional modern technology groups"]
    for group, (unit_type, start_level) in all_modern_technology_groups().items():
        blocks.extend([
            f"\t{group} = {{", f"\t\tstart_level = {start_level}", "\t\tstart_cost_modifier = 0",
            f"\t\tnation_designer_unit_type = {unit_type}", "\t}",
        ])
    return source[:index] + "\n".join(blocks) + source[index:]


def institutions_text() -> str:
    """Render the eight modern institutions over vanilla-compatible IDs."""
    blocks = [
        "# Generated EU4 2K modern institution sequence.",
        "# Vanilla identifiers are retained for engine and technology compatibility.",
        "",
    ]
    previous: str | None = None
    for event_id, (institution_id, name, date, raw_bonus) in enumerate(
        MODERN_INSTITUTIONS, start=1
    ):
        year = date.split(".", 1)[0]
        if isinstance(raw_bonus[0], str):
            bonuses = (raw_bonus,)
        else:
            bonuses = raw_bonus
        blocks.extend([institution_id + " = {", "\tbonus = {"])
        for modifier, value in bonuses:
            blocks.append(f"\t\t{modifier} = {value}")
        blocks.extend([
            "\t}",
            f"\thistorical_start_date = {date}",
            f"\thistorical_start_province = {INSTITUTION_HISTORICAL_ORIGINS[institution_id]}",
            "\thistory = { always = no }",
            "",
            "\tcan_start = {",
            f"\t\tis_year = {year}",
            "\t\tis_month = 3 # April or later",
            "\t\tis_city = yes",
            "\t\tis_state = yes",
            "\t\tis_capital = yes",
            "\t\tdevelopment = 20",
        ])
        if previous:
            blocks.extend([
                f"\t\tis_institution_enabled = {previous}",
                f"\t\t{previous} = 100",
            ])
        blocks.extend([
            "\t}",
            "\tstart_chance = 100",
            f"\ton_start = eu4_2k_institution_events.{event_id}",
            "",
            "\tcan_embrace = {",
        ])
        if previous:
            blocks.append(f"\t\towner = {{ has_institution = {previous} }}")
        else:
            blocks.append("\t\talways = yes")
        blocks.extend([
            "\t}",
            "",
            "\tembracement_speed = {",
            "\t\tmodifier = {",
            "\t\t\tfactor = 0.6",
            "\t\t\tscale = yes",
            f"\t\t\tany_friendly_coast_border_province = {{ {institution_id} = 100 }}",
            "\t\t}",
            "\t\tmodifier = {",
            "\t\t\tfactor = 0.25",
            "\t\t\tscale = yes",
            f"\t\t\tany_neighbor_province = {{ {institution_id} = 100 }}",
            "\t\t}",
            "\t\tmodifier = {",
            "\t\t\tfactor = 0.10",
            "\t\t\tscale = yes",
            "\t\t\tis_capital = yes",
            "\t\t\tdevelopment = 20",
            "\t\t}",
            "\t\tmodifier = {",
            "\t\t\tfactor = 1",
            "\t\t\tscale = yes",
            f"\t\t\towner = {{ has_institution = {institution_id} }}",
            "\t\t}",
            "\t}",
            "",
            "\tai_will_do = {",
            "\t\tfactor = 24",
            "\t\tmodifier = { factor = 0.25 is_at_war = yes }",
            "\t}",
            "}",
            "",
        ])
        previous = institution_id
    return "\n".join(blocks)


def institution_events_text() -> str:
    lines = [
        "# Generated origin events for the EU4 2K institution sequence.",
        "namespace = eu4_2k_institution_events",
        "",
    ]
    for event_id, (institution_id, _, _, _) in enumerate(MODERN_INSTITUTIONS, start=1):
        lines.extend([
            "country_event = {",
            f"\tid = eu4_2k_institution_events.{event_id}",
            f"\ttitle = eu4_2k_institution_events.{event_id}.t",
            f"\tdesc = eu4_2k_institution_events.{event_id}.d",
            "\tpicture = BIG_BOOK_eventPicture",
            "\tis_triggered_only = yes",
            "\tgoto = institution_origin",
            "\ttrigger = { always = yes }",
            "\timmediate = {",
            "\t\thidden_effect = {",
            "\t\t\tFROM = {",
            "\t\t\t\tsave_event_target_as = institution_origin",
            f"\t\t\t\tsave_global_event_target_as = eu4_2k_origin_{institution_id}",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "\toption = {",
            "\t\tname = eu4_2k_institution_events.origin_option",
            "\t\tFROM = {",
            "\t\t\tadd_permanent_province_modifier = {",
            f"\t\t\t\tname = eu4_2k_birthplace_{institution_id}",
            "\t\t\t\tduration = -1",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "}",
            "",
        ])
    return "\n".join(lines)


def institution_modifiers_text() -> str:
    lines = ["# Permanent markers for modern institution origin provinces.", ""]
    for institution_id, _, _, _ in MODERN_INSTITUTIONS:
        lines.extend([
            f"eu4_2k_birthplace_{institution_id} = {{",
            "\tlocal_institution_spread = 0.25",
            "}",
            "",
        ])
    return "\n".join(lines)


def institution_localisation() -> str:
    lines = ["l_english:"]
    for event_id, (institution_id, name, date, _) in enumerate(
        MODERN_INSTITUTIONS, start=1
    ):
        description = INSTITUTION_DESCRIPTIONS[institution_id].replace('"', r'\"')
        lines.append(f' {institution_id}:0 "{name}"')
        lines.append(f' desc_{institution_id}:0 "{description}\\n\\nExpected emergence: §Y{date}§!."')
        lines.append(f' eu4_2k_institution_events.{event_id}.t:0 "The Birth of {name}"')
        lines.append(
            f' eu4_2k_institution_events.{event_id}.d:0 "{name} first emerged in §Y[From.GetName]§!. This province will remain recorded as its birthplace."'
        )
        lines.append(f' eu4_2k_birthplace_{institution_id}:0 "Birthplace of {name}"')
        lines.append(
            f' desc_eu4_2k_birthplace_{institution_id}:0 "This province is where {name} first emerged. It receives faster institution spread and remains the permanent historical origin."'
        )
        lines.append(
            f' eu4_2k_birthplace_{institution_id}_desc:0 "This province is where {name} first emerged. It receives faster institution spread and remains the permanent historical origin."'
        )
    lines.append(' eu4_2k_institution_events.origin_option:0 "A new era begins."')
    return "\n".join(lines) + "\n"


def extract_named_block(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*\{{", text)
    if not match:
        return None
    opening = text.find("{", match.start())
    depth = 0
    quoted = escaped = comment = False
    for index in range(opening, len(text)):
        char = text[index]
        if comment:
            if char in "\r\n":
                comment = False
            continue
        if escaped:
            escaped = False
            continue
        if char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == "#" and not quoted:
            comment = True
        elif not quoted and char == "{":
            depth += 1
        elif not quoted and char == "}":
            depth -= 1
            if depth == 0:
                return text[match.start():index + 1].strip()
    return None


def source_country_definition(row: dict[str, str], game: Path) -> Path:
    prefix, relative = row["country_definition_source"].split(":", 1)
    root = ET / "common" if prefix == "et" else game / "common"
    return root / relative


def country_definition(row: dict[str, str], game: Path) -> str:
    source = source_country_definition(row, game).read_bytes().decode("cp1252", errors="replace")
    required_name_blocks: list[str] = []
    fallbacks = {
        "monarch_names": 'monarch_names = { "Modern Leader #0" = 100 }',
        "leader_names": "leader_names = { Adams Brown Clark Davis Evans Garcia Harris Jones Martin Wilson }",
        "ship_names": "ship_names = { Freedom Unity Republic Horizon Discovery Endeavour Enterprise Liberty Peace Hope }",
    }
    for key, fallback in fallbacks.items():
        block = extract_named_block(source, key)
        if block and key == "ship_names":
            block = block.rstrip()[:-1] + "\n\tFreedom Unity Republic Horizon Discovery Endeavour Enterprise Liberty Peace Hope\n}"
        required_name_blocks.append(block or fallback)
    return "\n".join([
        "# Generated by scripts/generate_country_snapshot.py",
        f"graphical_culture = {row['graphical_culture']}", "",
        f"color = {{ {row['color_r']} {row['color_g']} {row['color_b']} }}", "",
        *required_name_blocks, "",
    ])


def modern_cultures(rows: Sequence[dict[str, str]], game: Path) -> tuple[str, list[str]]:
    base_cultures: set[str] = set()
    for path in (game / "common" / "cultures").glob("*.txt"):
        base_cultures.update(collect_cultures(path))
    assignments: dict[str, tuple[str, str]] = {}
    for row in sorted(rows, key=lambda item: item["tag"]):
        used = [row["primary_culture"], *filter(None, row["accepted_cultures"].split("|"))]
        for culture in used:
            if culture not in base_cultures:
                assignments.setdefault(culture, (row["technology_group"], row["graphical_culture"]))
    countries = {row["tag"]: row for row in rows}
    if PROVINCE_DATA.exists():
        with PROVINCE_DATA.open("r", encoding="utf-8-sig", newline="") as handle:
            for province in csv.DictReader(handle):
                culture = province.get("culture", "")
                if not culture or culture in base_cultures:
                    continue
                owner = countries.get(province.get("owner", ""))
                technology_group = owner["technology_group"] if owner else "modern_western"
                graphical_culture = owner["graphical_culture"] if owner else "westerngfx"
                assignments.setdefault(culture, (technology_group, graphical_culture))

    et_source = (ET / "common" / "cultures" / "00_cultures.txt").read_bytes().decode("cp1252", errors="replace")
    groups: dict[str, list[tuple[str, str, str]]] = {}
    fallback = (
        "{culture} = {\n"
        "\tmale_names = { Alexander Benjamin Daniel Edward James Michael Nicholas Robert Samuel William }\n"
        "\tfemale_names = { Anna Catherine Elizabeth Emma Julia Maria Olivia Sarah Sophia Victoria }\n"
        "\tdynasty_names = { Adams Brown Clark Davis Evans Garcia Harris Jones Martin Wilson }\n"
        "}"
    )
    for culture, (technology_group, graphical_culture) in sorted(assignments.items()):
        block = extract_named_block(et_source, culture) or fallback.format(culture=culture)
        groups.setdefault(technology_group, []).append((culture, graphical_culture, block))

    lines = ["# Generated subset of modern cultures required by the 2000 snapshot."]
    for technology_group, cultures in sorted(groups.items()):
        lines.extend([f"eu4_2k_{technology_group}_cultures = {{", f"\tgraphical_culture = {cultures[0][1]}", ""])
        for _, _, block in cultures:
            lines.extend("\t" + line if line else "" for line in block.splitlines())
            lines.append("")
        lines.append("}")
    return "\n".join(lines) + "\n", sorted(assignments)


def starting_economy_history(
    row: dict[str, str], setup: dict[str, int]
) -> list[str]:
    """Render exact 2000 economy and reserve values as history effects.

    EU4 derives cash and reserve pools from development before country history
    effects are applied. Resetting each bounded value first prevents those
    engine defaults from being added to the canonical scenario values.
    """
    manpower_thousands = setup["manpower"] / 1000
    manpower_value = f"{manpower_thousands:.3f}".rstrip("0").rstrip(".")
    government, _ = EXECUTIVE_MODELS[row["government_model"]]
    authority_effect = {
        "monarchy": "add_legitimacy",
        "republic": "add_republican_tradition",
        "theocracy": "add_devotion",
    }[government]
    return [
        "# Canonical 2000 economy and reserves from data/country_setup_2000.csv",
        f"set_country_flag = eu4_2k_economic_tier_{setup['economic_tier']}",
        f"set_country_flag = eu4_2k_infrastructure_tier_{setup['infrastructure_tier']}",
        "add_treasury = -1000000",
        f"add_treasury = {setup['treasury']}",
        "add_inflation = -100",
        f"add_inflation = {setup['inflation']}",
        "add_stability = -3",
        f"add_stability = {setup['stability'] + 3}",
        "add_prestige = -1000",
        f"add_prestige = {setup['prestige'] + 100}",
        "add_corruption = -100",
        f"add_corruption = {setup['corruption']}",
        f"{authority_effect} = -100",
        f"{authority_effect} = {setup['legitimacy_or_tradition']}",
        "add_manpower = -1000000",
        f"add_manpower = {manpower_value}",
        "add_sailors = -1000000",
        f"add_sailors = {setup['sailors']}",
    ]


def country_history(
    row: dict[str, str], technology_setup: dict[str, dict[str, int]]
) -> str:
    government, executive_reform = EXECUTIVE_MODELS[row["government_model"]]
    lines = [
        "# Generated 2000.1.1 snapshot; later historical changes belong in events.",
        f"government = {government}", f"government_rank = {row['government_rank']}",
        f"add_government_reform = {executive_reform}",
        f"add_government_reform = {STATE_REFORMS[row['state_structure']]}",
        f"add_government_reform = {COMPETITION_REFORMS[row['political_competition']]}",
        f"primary_culture = {row['primary_culture']}",
    ]
    for culture in filter(None, row["accepted_cultures"].split("|")):
        if culture != row["primary_culture"]:
            lines.append(f"add_accepted_culture = {culture}")
    technology_group = row["technology_group"]
    if row["active_2000"] == "yes":
        levels = technology_setup[row["tag"]]
        technology_group = tiered_technology_group(technology_group, levels["adm_tech"])
    lines.extend([
        f"religion = {row['religion']}", f"technology_group = {technology_group}",
        f"unit_type = {row['unit_type']}", f"capital = {row['capital']}",
        f"set_country_flag = eu4_2k_ruling_group_{row['tag'].lower()}_{slug(row['ruling_group'])}",
    ])
    if row["active_2000"] == "yes":
        lines.extend(starting_economy_history(row, technology_setup[row["tag"]]))
        lines.append(
            "# Canonical starting ADM/DIP/MIL technology from "
            "data/country_setup_2000.csv"
        )
        lines.extend([
            f"# Historical executive birth date: {row['executive_birth']}",
            "monarch = {", f"\tname = {quote(row['executive'])}",
            f"\tadm = {row['adm']}",
            f"\tdip = {row['dip']}", f"\tmil = {row['mil']}", "}",
        ])
    else:
        lines.append("set_country_flag = eu4_2k_dormant_successor")
    return "\n".join(lines) + "\n"


def generated_country_tag_text(rows: Sequence[dict[str, str]], game: Path) -> str:
    base = (game / "common" / "country_tags" / "00_countries.txt").read_text(encoding="cp1252")
    active_tags = {row["tag"] for row in rows}
    pattern = re.compile(r'(?m)^(\s*)([A-Z0-9]{3})(\s*=\s*)"[^"]+"')
    seen: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        tag = match[2]
        if tag in active_tags:
            seen.add(tag)
            return f'{match[1]}{tag}{match[3]}"countries/EU4_2K_{tag}.txt"'
        return match[0]

    rendered = pattern.sub(replace, base).rstrip() + "\n\n# EU4 2K modern and successor tags\n"
    for row in rows:
        if row["tag"] not in seen:
            rendered += f'{row["tag"]} = "countries/EU4_2K_{row["tag"]}.txt"\n'
    return rendered


def registered_tags(rows: Sequence[dict[str, str]], game: Path) -> list[str]:
    """Return every tag exposed by the generated registry in stable file order."""
    registry = generated_country_tag_text(rows, game)
    return re.findall(r'(?m)^\s*([A-Z0-9]{3})\s*=\s*"countries/[^\"]+"', registry)


def framework_localisation(rows: Sequence[dict[str, str]]) -> str:
    labels = {
        "eu4_2k_parliamentary_republic": "Parliamentary Republic",
        "eu4_2k_presidential_republic": "Presidential Republic",
        "eu4_2k_semi_presidential_republic": "Semi-Presidential Republic",
        "eu4_2k_parliamentary_monarchy": "Parliamentary Monarchy",
        "eu4_2k_absolute_monarchy": "Absolute Monarchy",
        "eu4_2k_one_party_state": "One-Party State",
        "eu4_2k_military_government": "Military Government",
        "eu4_2k_theocratic_state": "Theocratic State",
        "eu4_2k_transitional_government": "Transitional Government",
        "eu4_2k_unitary_state": "Unitary State",
        "eu4_2k_federal_state": "Federal State",
        "eu4_2k_confederal_state": "Confederal State",
        "eu4_2k_multiparty_system": "Multiparty System",
        "eu4_2k_dominant_party_system": "Dominant-Party System",
        "eu4_2k_single_party_system": "Single-Party System",
        "eu4_2k_nonpartisan_system": "Nonpartisan System",
        "eu4_2k_closed_authoritarian_system": "Closed Authoritarian System",
        "modern_western": "Western Modern",
        "modern_post_soviet": "Post-Soviet Modern",
        "modern_east_asian": "East Asian Modern",
        "modern_south_asian": "South Asian Modern",
        "modern_southeast_asian": "Southeast Asian Modern",
        "modern_middle_eastern_north_african": "Middle Eastern and North African Modern",
        "modern_sub_saharan_african": "Sub-Saharan African Modern",
        "modern_latin_american": "Latin American Modern",
        "modern_oceanian": "Oceanian Modern",
    }
    lines = ["l_english:"]
    for key, value in sorted(labels.items()):
        lines.append(f' {key}:0 "{value}"')
        lines.append(f' {key}_desc:0 "A modern political or technological classification used by EU4 2K."')
    for group, label in sorted(
        (key, value) for key, value in labels.items() if key in TECH_GROUPS
    ):
        for level in MODERN_TECH_LEVELS:
            key = tiered_technology_group(group, level)
            lines.append(f' {key}:0 "{label}"')
            lines.append(
                f' {key}_desc:0 "{label} technology tier {level} at the 2000 start."'
            )
    lines.extend([
        ' EU4_2K_2000_NAME:0 "The New Millennium"',
        ' EU4_2K_2000_DESC:0 "On 1 January 2000, globalization, regional integration, technological change, and unresolved conflicts shape a new century."',
    ])
    return "\n".join(lines) + "\n"


def culture_localisation(rows: Sequence[dict[str, str]], game: Path) -> str:
    _, cultures = modern_cultures(rows, game)
    lines = ["l_english:"]
    for culture in cultures:
        label = culture.replace("_", " ").title()
        lines.append(f' {culture}:0 "{label}"')
    return "\n".join(lines) + "\n"


def country_localisation(rows: Sequence[dict[str, str]]) -> str:
    lines = ["l_english:"]
    for row in rows:
        name = row["name"].replace('"', r'\"')
        adjective = row["adjective"].replace('"', r'\"')
        lines.extend([f' {row["tag"]}:0 "{name}"', f' {row["tag"]}_ADJ:0 "{adjective}"'])
    return "\n".join(lines) + "\n"


def text_outputs(
    rows: Sequence[dict[str, str]],
    game: Path,
    technology_setup: dict[str, dict[str, int]],
) -> dict[Path, tuple[str, str]]:
    outputs: dict[Path, tuple[str, str]] = {
        MOD / "common" / "country_tags" / "00_countries.txt": (generated_country_tag_text(rows, game), "cp1252"),
        MOD / "common" / "government_reforms" / "00_eu4_2k_government_reforms.txt": (government_reforms_text(), "cp1252"),
        MOD / "common" / "cultures" / "00_eu4_2k_cultures.txt": (modern_cultures(rows, game)[0], "cp1252"),
        MOD / "common" / "technology.txt": (technology_text(game), "cp1252"),
        MOD / "common" / "institutions" / "00_Core.txt": (institutions_text(), "cp1252"),
        MOD / "common" / "event_modifiers" / "zz_eu4_2k_institution_origins.txt": (institution_modifiers_text(), "cp1252"),
        MOD / "events" / "eu4_2k_institution_events.txt": (institution_events_text(), "cp1252"),
        MOD / "common" / "defines" / "zz_eu4_2k_dates.lua": ('NDefines.NGame.START_DATE = "2000.1.1"\nNDefines.NGame.END_DATE = "9999.12.31"\n', "ascii"),
        MOD / "common" / "bookmarks" / "00_eu4_2k_2000.txt": ("bookmark = {\n\tname = \"EU4_2K_2000_NAME\"\n\tdesc = \"EU4_2K_2000_DESC\"\n\tdate = 2000.1.1\n\tcountry = USA\n\tcountry = RUS\n\tcountry = CHN\n\tcountry = GER\n\tcountry = FR2\n\tcountry = GBR\n\tcountry = YUG\n}\n", "cp1252"),
        MOD / "localisation" / "replace" / "zz_eu4_2k_countries_l_english.yml": (country_localisation(rows), "utf-8-sig"),
        MOD / "localisation" / "eu4_2k_framework_l_english.yml": (framework_localisation(rows), "utf-8-sig"),
        MOD / "localisation" / "eu4_2k_cultures_l_english.yml": (culture_localisation(rows, game), "utf-8-sig"),
        MOD / "localisation" / "replace" / "zz_eu4_2k_institutions_l_english.yml": (institution_localisation(), "utf-8-sig"),
    }
    if not PROVINCE_DATA.exists():
        outputs[MOD / "history" / "provinces" / "00_placeholder.txt"] = (
            "# Empty clean province-history layer used while generating the 2000 snapshot.\n",
            "cp1252",
        )
    for row in rows:
        outputs[MOD / "common" / "countries" / f"EU4_2K_{row['tag']}.txt"] = (country_definition(row, game), "cp1252")
        safe_name = re.sub(r'[<>:"/\\|?*]', "", row["name"])
        outputs[MOD / "history" / "countries" / f"{row['tag']} - {safe_name}.txt"] = (
            country_history(row, technology_setup),
            "cp1252",
        )
    snapshot_tags = {row["tag"] for row in rows}
    for tag in registered_tags(rows, game):
        if tag not in snapshot_tags:
            outputs[MOD / "history" / "countries" / f"{tag} - Inactive compatibility.txt"] = (
                "# Inactive compatibility tag retained for vanilla script references.\n"
                "government = monarchy\n",
                "cp1252",
            )
    return outputs


def flag_source(row: dict[str, str], game: Path) -> Path:
    prefix, relative = row["flag_source"].split(":", 1)
    return (ET if prefix == "et" else game) / relative


def write_outputs(
    rows: Sequence[dict[str, str]],
    game: Path,
    technology_setup: dict[str, dict[str, int]],
) -> None:
    outputs = text_outputs(rows, game, technology_setup)
    legacy_country_localisation = MOD / "localisation" / "eu4_2k_countries_l_english.yml"
    if legacy_country_localisation.exists():
        legacy_country_localisation.unlink()
    old_replace_localisation = MOD / "localisation" / "replace" / "eu4_2k_countries_l_english.yml"
    if old_replace_localisation.exists():
        old_replace_localisation.unlink()
    history_dir = MOD / "history" / "countries"
    expected_history = {path for path in outputs if path.parent == history_dir}
    if history_dir.exists():
        for path in history_dir.glob("*.txt"):
            if path not in expected_history:
                path.unlink()
    countries_dir = MOD / "common" / "countries"
    expected_countries = {path for path in outputs if path.parent == countries_dir}
    if countries_dir.exists():
        for path in countries_dir.glob("EU4_2K_*.txt"):
            if path not in expected_countries:
                path.unlink()
    for path, (content, encoding) in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = content.encode(encoding)
        if not path.exists() or path.read_bytes() != encoded:
            path.write_bytes(encoded)
    flags = MOD / "gfx" / "flags"
    flags.mkdir(parents=True, exist_ok=True)
    expected_flags = {flags / f"{row['tag']}.tga" for row in rows}
    for path in flags.glob("*.tga"):
        if path not in expected_flags:
            path.unlink()
    for row in rows:
        source = flag_source(row, game)
        target = flags / f"{row['tag']}.tga"
        if not target.exists() or target.read_bytes() != source.read_bytes():
            shutil.copyfile(source, target)


def check_outputs(
    rows: Sequence[dict[str, str]],
    game: Path,
    technology_setup: dict[str, dict[str, int]],
) -> None:
    errors: list[str] = []
    expected = text_outputs(rows, game, technology_setup)
    for path, (content, encoding) in expected.items():
        if not path.exists():
            errors.append(f"missing generated file: {path.relative_to(ROOT)}")
        elif path.read_bytes() != content.encode(encoding):
            errors.append(f"generated file is stale: {path.relative_to(ROOT)}")
    for row in rows:
        target = MOD / "gfx" / "flags" / f"{row['tag']}.tga"
        source = flag_source(row, game)
        if not target.exists() or target.read_bytes() != source.read_bytes():
            errors.append(f"missing or stale flag: {row['tag']}")
    history_dir = MOD / "history" / "countries"
    expected_history = {path for path in expected if path.parent == history_dir}
    actual_history = set(history_dir.glob("*.txt")) if history_dir.exists() else set()
    for path in sorted(actual_history - expected_history):
        errors.append(f"unexpected generated history file: {path.name}")
    for path in history_dir.glob("*.txt") if history_dir.exists() else []:
        text = path.read_bytes().decode("cp1252", errors="replace")
        if re.search(r"(?m)^\s*-?\d+\.\d+\.\d+\s*=", text):
            errors.append(f"dated history block found: {path.name}")
        if "secularism" in text or "irreligious" in text:
            errors.append(f"forbidden religion found: {path.name}")
    tech = expected[MOD / "common" / "technology.txt"][0]
    costs = re.findall(r"(?s)(modern_[a-z0-9_]+)\s*=\s*\{.*?start_cost_modifier\s*=\s*([0-9.]+)", tech)
    if len(costs) != len(all_modern_technology_groups()) or {cost for _, cost in costs} != {"0"}:
        errors.append("regional modern technology groups do not all have equal zero base cost")
    if errors:
        raise RuntimeError("Generated output check failed:\n- " + "\n- ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=("generate",), default="generate")
    parser.add_argument("--check", action="store_true", help="validate without writing files")
    parser.add_argument("--game-root")
    parser.add_argument("--rebuild-data", action="store_true")
    args = parser.parse_args()
    game = find_game_root(args.game_root)
    if args.rebuild_data or not DATA.exists():
        if args.check:
            raise SystemExit("Canonical dataset is missing; run generate first")
        rows = bootstrap_rows(game)
        write_manifest(rows)
    rows = load_manifest()
    validate_rows(rows, game)
    technology_setup = load_technology_setup(rows)
    if args.check:
        check_outputs(rows, game, technology_setup)
        print(f"Validated {len(rows)} countries ({sum(r['active_2000'] == 'yes' for r in rows)} active, {len(SUCCESSORS)} dormant).")
    else:
        write_outputs(rows, game, technology_setup)
        check_outputs(rows, game, technology_setup)
        print(f"Generated {len(rows)} countries ({sum(r['active_2000'] == 'yes' for r in rows)} active, {len(SUCCESSORS)} dormant).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
