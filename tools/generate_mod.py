#!/usr/bin/env python3
"""Generate a standalone EU4 year-2000 foundation from independent datasets."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import shutil
import time
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

import shapefile
from PIL import Image
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "MillenniumDawnEU4"
CACHE = ROOT / ".cache"
CLAIMS_PATH = ROOT / "tools" / "data" / "historical_claims.csv"
CLAIM_GROUPS_PATH = ROOT / "tools" / "data" / "historical_claim_groups.csv"
NE_URL = "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip"
FLAG_URL = "https://flagcdn.com/w320/{iso2}.png"
CAPITALS_URL = "https://gist.githubusercontent.com/aratsimbaharison/d2b02b968bcfa03749c7c4ee9577dc68/raw/355eb56e164ddc3cd1a9467c524422cb674e71a9/country-capital-lat-long-population.csv"
MAP_W, MAP_H = 5632, 2048

# ISO-like tags that already identify unrelated vanilla EU4 countries.
TAG_REMAP = {
    "BRA":"BZ1", "BRB":"BBD", "BTN":"BT1", "CHE":"CH1", "COM":"CMO",
    "CRI":"COS", "ERI":"ERT", "GBR":"UKG", "GUY":"GYN", "IND":"IN1",
    "ISL":"IS1", "JAM":"JMC", "KAZ":"KZK", "KHM":"CBD", "KOR":"SKR",
    "LVA":"LAT", "MAR":"MRC", "MDA":"MLD", "MLI":"ML1", "MNG":"MGL",
    "MYS":"MLY", "NGA":"NGR", "NZL":"NZE", "PAN":"PNM", "PER":"P01",
    "PRK":"NKR", "PRY":"PGY", "SEN":"SNG", "SLE":"SLR", "TON":"TO1",
    "TUN":"TNS", "TUR":"TU1", "UKR":"UKN", "VEN":"VE1", "ZAF":"SAF",
}

def modern_tag(tag: str) -> str:
    return TAG_REMAP.get(tag, tag)

# Natural Earth entities mapped to their 1 January 2000 sovereign owner.
HISTORICAL_OWNER = {
    "Republic of Serbia": "YUG", "Montenegro": "YUG", "Kosovo": "YUG",
    "South Sudan": "SDN", "East Timor": "IDN", "Somaliland": "SOM",
    "Western Sahara": "MAR", "Northern Cyprus": "TUR",
    "Hong Kong S.A.R.": "CHN", "Macao S.A.R": "CHN",
}

SPECIAL_TAGS = {
    "France": "FRA", "Norway": "NOR", "United States of America": "USA",
    "United Kingdom": "GBR", "Palestine": "PSE", "Taiwan": "TWN",
    "Vatican": "VAT", "Republic of Serbia": "YUG",
}

COUNTRY_NAME_OVERRIDES = {
    "YUG": "Federal Republic of Yugoslavia", "USA": "United States",
    "TZA": "Tanzania", "COD": "Democratic Republic of the Congo",
    "COG": "Republic of the Congo", "CIV": "Cote d'Ivoire",
    "SWZ": "Swaziland", "MKD": "Republic of Macedonia",
    "MMR": "Myanmar", "CZE": "Czech Republic", "CPV": "Cape Verde",
}

RULERS = {
    "USA": ("Bill Clinton", 4, 5, 3), "RUS": ("Vladimir Putin", 4, 3, 4),
    "CHN": ("Jiang Zemin", 4, 4, 3), "UKR": ("Leonid Kuchma", 3, 3, 2),
    "IRQ": ("Saddam Hussein", 2, 2, 4), "AFG": ("Mohammed Omar", 2, 1, 4),
    "YUG": ("Slobodan Milosevic", 2, 2, 3), "GBR": ("Elizabeth II", 4, 5, 2),
    "FRA": ("Jacques Chirac", 4, 4, 3), "DEU": ("Johannes Rau", 3, 4, 2),
    "TWN": ("Lee Teng-hui", 4, 4, 3), "PSE": ("Yasser Arafat", 3, 4, 3),
    "VAT": ("John Paul II", 5, 6, 2),
}

UNIQUE_IDEA_TAGS = {"USA", "RUS", "CHN", "UKR", "IRQ", "AFG", "YUG", "GBR", "FRA", "DEU", "TWN"}

# European Union membership on the scenario start date (1 January 2000).
# The HRE engine is repurposed as the EU.
EU_2000_MEMBERS = {
    "AUT", "BEL", "DNK", "FIN", "FRA", "DEU", "GRC", "IRL", "ITA",
    "LUX", "NLD", "PRT", "ESP", "SWE", "UKG",
}
EU_2000_PRESIDENCY = "PRT"

# Vanilla provinces deliberately used to represent states too small for centroid
# assignment, plus historically sensitive borders on 1 January 2000.
PROVINCE_OWNER_OVERRIDES = {
    80: "DEU", 93: "BEL", 94: "LUX", 118: "VAT", 395: "QAT", 396: "BHR", 636: "BRN",
    836: "CRI", 839: "SLV", 843: "BLZ", 1180: "LSO", 1766: "YUG",
    139: "BIH", 1827: "YUG", 2850: "URY", 4126: "YUG", 4173: "YUG",
    4239: "YUG", 4757: "YUG", 4768: "DEU", 4783: "SWZ",
}

CAPITAL_COUNTRY_ALIASES = {
    "BOL": "Bolivia (Plurinational State of)", "BRN": "Brunei Darussalam",
    "COD": "Democratic Republic of the Congo", "COG": "Congo",
    "CIV": "CÃ´te d'Ivoire", "IRN": "Iran (Islamic Republic of)",
    "KOR": "Republic of Korea", "LAO": "Lao People's Democratic Republic",
    "MDA": "Republic of Moldova", "MKD": "North Macedonia",
    "PRK": "Dem. People's Republic of Korea", "PSE": "State of Palestine",
    "RUS": "Russian Federation", "SWZ": "Eswatini", "SYR": "Syrian Arab Republic",
    "TZA": "United Republic of Tanzania", "USA": "United States of America",
    "VAT": "Holy See", "VEN": "Venezuela (Bolivarian Republic of)",
    "VNM": "Viet Nam",
}

CAPITAL_COORD_OVERRIDES = {
    "YUG": (44.8176, 20.4633), "TWN": (25.0470, 121.5457),
    "PSE": (31.9038, 35.2034), "VAT": (41.9024, 12.4533),
}

CAPITAL_PROVINCE_OVERRIDES = {
    "AFG": 451, "CHN": 1816, "CUB": 484, "DEU": 50, "FRA": 183,
    "GBR": 236, "IRQ": 410, "NLD": 97, "RUS": 295, "UKR": 280,
    "YUG": 4239,
}

REGION_STYLE = {
    "Europe": ("western", "republic", "catholic", "western"),
    "North America": ("western", "republic", "catholic", "western"),
    "South America": ("western", "republic", "catholic", "western"),
    "Asia": ("eastern", "republic", "sunni", "eastern"),
    "Africa": ("sub_saharan", "republic", "sunni", "african"),
    "Oceania": ("western", "republic", "protestant", "western"),
    "Seven seas (open ocean)": ("western", "republic", "catholic", "western"),
}

MONARCHIES = {"GBR", "ESP", "BEL", "NLD", "NOR", "SWE", "DNK", "LUX", "MCO", "LIE", "AND", "JPN", "THA", "KHM", "MYS", "BRN", "JOR", "MAR", "SAU", "OMN", "QAT", "KWT", "BHR", "BTN", "NPL", "SWZ", "LSO", "TON"}
ISLAMIC = {"AFG", "ALB", "DZA", "AZE", "BHR", "BGD", "BRN", "BFA", "TCD", "COM", "DJI", "EGY", "GMB", "GIN", "IDN", "IRN", "IRQ", "JOR", "KAZ", "KWT", "KGZ", "LBN", "LBY", "MYS", "MDV", "MLI", "MRT", "MAR", "NER", "NGA", "OMN", "PAK", "PSE", "QAT", "SAU", "SEN", "SLE", "SOM", "SDN", "SYR", "TJK", "TUN", "TUR", "TKM", "ARE", "UZB", "YEM", "YUG"}
ORTHODOX = {"ARM", "BLR", "BGR", "CYP", "ETH", "GEO", "GRC", "MDA", "MKD", "ROU", "RUS", "UKR", "YUG"}
PROTESTANT = {"GBR", "USA", "CAN", "AUS", "NZL", "DNK", "FIN", "ISL", "NOR", "SWE", "ZAF", "NAM", "BWA", "LSO", "SWZ"}
EASTERN_RELIGION = {"CHN": "confucianism", "TWN": "confucianism", "JPN": "shinto", "KOR": "confucianism", "PRK": "confucianism", "IND": "hinduism", "NPL": "hinduism", "THA": "buddhism", "MMR": "buddhism", "KHM": "buddhism", "LAO": "buddhism", "LKA": "buddhism", "BTN": "vajrayana", "MNG": "vajrayana", "VNM": "mahayana"}

HISTORICAL_OWNER = {name: modern_tag(tag) for name, tag in HISTORICAL_OWNER.items()}
SPECIAL_TAGS = {name: modern_tag(tag) for name, tag in SPECIAL_TAGS.items()}
COUNTRY_NAME_OVERRIDES = {modern_tag(tag): name for tag, name in COUNTRY_NAME_OVERRIDES.items()}
RULERS = {modern_tag(tag): value for tag, value in RULERS.items()}
UNIQUE_IDEA_TAGS = {modern_tag(tag) for tag in UNIQUE_IDEA_TAGS}
PROVINCE_OWNER_OVERRIDES = {pid: modern_tag(tag) for pid, tag in PROVINCE_OWNER_OVERRIDES.items()}
CAPITAL_COUNTRY_ALIASES = {modern_tag(tag): value for tag, value in CAPITAL_COUNTRY_ALIASES.items()}
CAPITAL_COORD_OVERRIDES = {modern_tag(tag): value for tag, value in CAPITAL_COORD_OVERRIDES.items()}
CAPITAL_PROVINCE_OVERRIDES = {modern_tag(tag): value for tag, value in CAPITAL_PROVINCE_OVERRIDES.items()}
MONARCHIES = {modern_tag(tag) for tag in MONARCHIES}
ISLAMIC = {modern_tag(tag) for tag in ISLAMIC}
ISLAMIC.discard("YUG")
ORTHODOX = {modern_tag(tag) for tag in ORTHODOX}
PROTESTANT = {modern_tag(tag) for tag in PROTESTANT}
EASTERN_RELIGION = {modern_tag(tag): value for tag, value in EASTERN_RELIGION.items()}

# Preferred vanilla color sources for modern states whose EU4 tag or historical
# name differs. Exact-name matches are detected automatically as well.
COLOR_SOURCE_TAG = {
    "AUT":"HAB", "BGR":"BUL", "CHN":"MNG", "DEU":"GER", "DNK":"DAN",
    "ESP":"SPA", "GRC":"GRE", "HRV":"CRO", "IN1":"HIN", "IRL":"IRE",
    "IRN":"PER", "JPN":"JAP", "KZK":"KAZ", "LBN":"LEB", "LTU":"LIT",
    "MLD":"MOL", "NLD":"NED", "OMN":"OMA", "PRT":"POR", "ROU":"RMN",
    "RUS":"RUS", "SAF":"ZAF", "SKR":"KOR", "TNS":"TUN", "TU1":"TUR",
    "UKG":"GBR", "UKN":"UKR", "YUG":"SER",
}


def download(url: str, path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "MillenniumDawnEU4/0.1"})
    with urllib.request.urlopen(req, timeout=90) as response, path.open("wb") as f:
        shutil.copyfileobj(response, f)


def natural_earth_path() -> Path:
    zip_path = CACHE / "natural-earth" / "countries.zip"
    shp = CACHE / "natural-earth" / "countries" / "ne_10m_admin_0_countries.shp"
    download(NE_URL, zip_path)
    if not shp.exists():
        shp.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(shp.parent)
    return shp


def clean_output() -> None:
    if OUT.exists():
        # OneDrive can briefly hold generated files after a large write burst.
        for attempt in range(8):
            try:
                shutil.rmtree(OUT)
                break
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(0.5 * (attempt + 1))
    for folder in [
        "common/bookmarks", "common/countries", "common/country_tags", "common/defines",
        "common/ideas", "common/imperial_reforms", "common/institutions", "common/triggered_modifiers", "gfx/flags", "history/countries", "history/provinces",
        "history/diplomacy", "history/wars",
        "localisation", "source_data",
    ]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    # An explicit manifest prevents EU4's checksum walker from flattening paths
    # beneath replace_path directories in debug mode.
    (OUT / "checksum_manifest.txt").write_text("", encoding="utf-8")


def parse_fields(text: str) -> dict[str, str]:
    result = {}
    for key in ("owner", "controller", "culture", "religion", "trade_goods"):
        matches = re.findall(rf"(?m)^\s*{key}\s*=\s*([\w-]+)", text)
        if matches:
            result[key] = matches[0]
    return result


def province_records(game: Path) -> list[dict]:
    definitions = {}
    with (game / "map" / "definition.csv").open(encoding="cp1252") as f:
        for row in csv.reader(f, delimiter=";"):
            if row and row[0].isdigit():
                definitions[int(row[0])] = tuple(map(int, row[1:4]))
    image = Image.open(game / "map" / "provinces.bmp").convert("RGB")
    pixels = image.load()
    color_to_id = {rgb: pid for pid, rgb in definitions.items()}
    sums = defaultdict(lambda: [0, 0, 0])
    # Sampling every fourth pixel is accurate enough for province-country assignment.
    for y in range(0, image.height, 4):
        for x in range(0, image.width, 4):
            pid = color_to_id.get(pixels[x, y])
            if pid:
                sums[pid][0] += x; sums[pid][1] += y; sums[pid][2] += 1
    records = []
    for file in sorted((game / "history" / "provinces").glob("*.txt")):
        match = re.match(r"\s*(\d+)", file.name)
        if not match:
            continue
        pid = int(match.group(1))
        if pid not in sums or not sums[pid][2]:
            continue
        sx, sy, count = sums[pid]
        x, y = sx / count, sy / count
        fields = parse_fields(file.read_text(encoding="cp1252", errors="ignore"))
        # Vanilla ships placeholder history files for sea and wasteland IDs too.
        if not any(k in fields for k in ("owner", "culture", "religion", "trade_goods")):
            continue
        records.append({"id": pid, "name": file.stem, "x": x, "y": y, **fields})
    return records


def country_data(shp_path: Path):
    reader = shapefile.Reader(str(shp_path), encoding="utf-8")
    fields = [f[0] for f in reader.fields[1:]]
    records = []
    for sr in reader.iterShapeRecords():
        records.append((dict(zip(fields, sr.record)), sr))
    sovereign_tags = {}
    for d, _ in records:
        admin = d["ADMIN"]
        if d["SOVEREIGNT"] != admin:
            continue
        tag = SPECIAL_TAGS.get(admin) or modern_tag(d["ISO_A3"] if d["ISO_A3"] != "-99" else d["ADM0_A3"])
        if len(tag) == 3:
            sovereign_tags[admin] = tag
    polygons, metadata = [], []
    countries = {}
    for d, sr in records:
        admin = d["ADMIN"]
        tag = HISTORICAL_OWNER.get(admin)
        if not tag:
            if (d["SOVEREIGNT"] == admin and d["TYPE"] != "Indeterminate") or admin in {"Taiwan", "Palestine", "Vatican", "Israel"}:
                tag = SPECIAL_TAGS.get(admin) or modern_tag(d["ISO_A3"] if d["ISO_A3"] != "-99" else d["ADM0_A3"])
            else:
                tag = sovereign_tags.get(d["SOVEREIGNT"])
        if not tag or len(tag) != 3 or tag in {"ATA", "REB", "PIR", "NAT"}:
            continue
        if tag == "SRB": tag = "YUG"
        tag = modern_tag(tag)
        geom = shape(sr.shape.__geo_interface__)
        polygons.append(geom); metadata.append((tag, admin))
        is_primary = ((d["SOVEREIGNT"] == admin and d["TYPE"] != "Indeterminate" and admin not in HISTORICAL_OWNER)
                      or admin in {"Taiwan", "Palestine", "Vatican", "Israel"})
        if tag not in countries and is_primary:
            name = COUNTRY_NAME_OVERRIDES.get(tag, d["NAME_LONG"] or admin)
            countries[tag] = {
                "tag": tag, "name": name, "continent": d["CONTINENT"],
                "subregion": d["SUBREGION"], "population": max(int(d["POP_EST"] or 1), 1),
                "gdp": max(float(d["GDP_MD"] or 1), 1), "iso2": d["ISO_A2"] if d["ISO_A2"] != "-99" else "",
                "label_x": float(d["LABEL_X"]), "label_y": float(d["LABEL_Y"]),
                "mapcolor": int(d["MAPCOLOR7"] or 1),
            }
    # Historical entities missing from the modern sovereign metadata.
    countries["YUG"] = {"tag":"YUG", "name":COUNTRY_NAME_OVERRIDES["YUG"], "continent":"Europe", "subregion":"Southern Europe", "population":10600000, "gdp":26000, "iso2":"YU", "label_x":20.8, "label_y":44.0, "mapcolor":4}
    return countries, polygons, metadata


def pixel_to_lonlat(x: float, y: float) -> tuple[float, float]:
    # Longitude is plate-carree. Latitude follows the vanilla bitmap's custom
    # north-heavy projection, calibrated against widely separated city provinces.
    latitude = -0.00000702788425 * y * y - 0.0414938041 * y + 73.5182926
    longitude = x / MAP_W * 360.0 - 180.0
    # Paradox shifts the Americas north on the game map to use screen space.
    if longitude < -30.0:
        latitude -= 13.5
    return longitude, latitude


def assign_provinces(provinces, polygons, metadata):
    tree = STRtree(polygons)
    assigned = []
    for p in provinces:
        lon, lat = pixel_to_lonlat(p["x"], p["y"])
        point = Point(lon, lat)
        candidates = tree.query(point)
        tag = None
        for idx in candidates:
            if polygons[int(idx)].covers(point):
                tag = metadata[int(idx)][0]; break
        if tag is None:
            # Small islands and map-edge distortions: use the nearest boundary.
            idx = int(tree.nearest(point)); tag = metadata[idx][0]
        tag = PROVINCE_OWNER_OVERRIDES.get(p["id"], tag)
        assigned.append({**p, "lon": lon, "lat": lat, "tag": tag})
    return assigned


def capital_coordinates(countries: dict) -> dict[str, tuple[float, float, str]]:
    path = CACHE / "capital_cities.csv"
    download(CAPITALS_URL, path)
    with path.open(encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.DictReader(f))
    by_name = {r["Country"].strip().casefold(): r for r in rows}
    result = {}
    for tag, c in countries.items():
        if tag in CAPITAL_COORD_OVERRIDES:
            lat, lon = CAPITAL_COORD_OVERRIDES[tag]
            result[tag] = (lon, lat, "historical override")
            continue
        wanted = CAPITAL_COUNTRY_ALIASES.get(tag, c["name"])
        row = by_name.get(wanted.casefold())
        if row:
            result[tag] = (float(row["Longitude"]), float(row["Latitude"]), row["Capital City"])
        else:
            result[tag] = (c["label_x"], c["label_y"], "country label fallback")
    return result


def religion_for(tag: str, continent: str) -> str:
    if tag in EASTERN_RELIGION: return EASTERN_RELIGION[tag]
    if tag in ISLAMIC: return "shiite" if tag in {"IRN", "AZE", "IRQ"} else "sunni"
    if tag in ORTHODOX: return "orthodox"
    if tag in PROTESTANT: return "protestant"
    return "catholic" if continent in {"Europe", "North America", "South America", "Oceania"} else "animism"


def safe_color(tag: str, slot: int) -> tuple[int, int, int]:
    seed = sum((i + 3) * ord(c) for i, c in enumerate(tag)) + slot * 71
    return (55 + seed * 37 % 170, 55 + seed * 67 % 170, 55 + seed * 97 % 170)


def vanilla_color_map(game: Path, countries: dict) -> dict[str, tuple[tuple[int,int,int], str]]:
    tag_files = {}
    for source in sorted((game / "common" / "country_tags").glob("*.txt")):
        for line in source.read_text(encoding="cp1252", errors="ignore").splitlines():
            match = re.match(r'^\s*([A-Z0-9]{3})\s*=\s*"([^"]+)"', line)
            if match:
                tag_files[match.group(1)] = match.group(2)
    colors = {}
    for tag, relative in tag_files.items():
        path = game / "common" / relative
        if not path.exists():
            continue
        match = re.search(r'(?m)^\s*color\s*=\s*\{\s*(\d+)\s+(\d+)\s+(\d+)\s*\}', path.read_text(encoding="cp1252", errors="ignore"))
        if match:
            colors[tag] = tuple(map(int, match.groups()))
    names = {}
    for source in (game / "localisation").rglob("*_l_english.yml"):
        for line in source.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            match = re.match(r'^\s*([A-Z0-9]{3}):\d*\s+"([^"]+)"', line)
            if match and match.group(1) in colors:
                names.setdefault(match.group(2).casefold(), match.group(1))
    result = {}
    for tag, country in countries.items():
        source_tag = COLOR_SOURCE_TAG.get(tag) or names.get(country["name"].casefold())
        if source_tag in colors:
            result[tag] = (colors[source_tag], source_tag)
    return result


def write_descriptor() -> None:
    descriptor = '''version="0.1.0"\ntags={ "Alternative History" "Historical" "Map" "New Nations" }\nname="Millennium Dawn EU4"\nsupported_version="1.37.*"\nreplace_path="common/country_tags"\nreplace_path="common/institutions"\nreplace_path="history/countries"\nreplace_path="history/provinces"\nreplace_path="history/diplomacy"\nreplace_path="history/wars"\n'''
    (OUT / "descriptor.mod").write_text(descriptor, encoding="utf-8")
    (ROOT / "MillenniumDawnEU4.mod").write_text(descriptor + 'path="mod/MillenniumDawnEU4"\n', encoding="utf-8")


def write_eu_system() -> None:
    """Install the native-HRE European Union definitions and localisation."""
    template_root = ROOT / "tools" / "templates" / "eu"
    for source in template_root.rglob("*"):
        if source.is_file():
            target = OUT / source.relative_to(template_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def write_institutions() -> None:
    """Install the modern institution sequence and its localisation."""
    template_root = ROOT / "tools" / "templates" / "institutions"
    for source in template_root.rglob("*"):
        if source.is_file():
            target = OUT / source.relative_to(template_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def write_defines_bookmark() -> None:
    (OUT / "common/defines/md_defines.lua").write_text(
        'NDefines.NGame.START_DATE = "2000.1.1"\nNDefines.NGame.END_DATE = "9999.12.31"\n', encoding="utf-8")
    (OUT / "common/bookmarks/00_md_2000.txt").write_text('''bookmark = {\n name = "MD_BOOKMARK_2000"\n desc = "MD_BOOKMARK_2000_DESC"\n date = 2000.1.1\n center = 953\n default = yes\n country = USA\n country = RUS\n country = CHN\n country = YUG\n country = UKN\n country = IRQ\n country = AFG\n}\n''', encoding="utf-8")


def write_countries(countries, provinces, game: Path):
    by_tag = defaultdict(list)
    for p in provinces: by_tag[p["tag"]].append(p)
    # Drop polygon-only microstates that have no representable vanilla province.
    countries = {t:c for t,c in countries.items() if by_tag.get(t)}
    lines = ['REB = "countries/Rebels.txt"', 'PIR = "countries/Pirates.txt"', 'NAT = "countries/Natives.txt"', '']
    loc = ["l_english:", ' MD_BOOKMARK_2000:0 "The Millennium"', ' MD_BOOKMARK_2000_DESC:0 "The world at the dawn of the twenty-first century."']
    rows = []
    capitals = capital_coordinates(countries)
    original_colors = vanilla_color_map(game, countries)
    modern_tags = set(countries)
    # Base-game scripts parse historical tags even when those countries do not
    # exist in 2000. Retain them as dormant definitions to avoid parser errors.
    vanilla_tags = {}
    for source in sorted((game / "common" / "country_tags").glob("*.txt")):
        for line in source.read_text(encoding="cp1252", errors="ignore").splitlines():
            match = re.match(r'^\s*([A-Z0-9]{3})\s*=\s*"([^"]+)"', line)
            if match and match.group(1) not in modern_tags and match.group(1) not in {"REB", "PIR", "NAT"}:
                vanilla_tags[match.group(1)] = match.group(2)
    lines.extend(f'{tag} = "{path}"' for tag, path in sorted(vanilla_tags.items()))
    lines.append("")
    vanilla_loc_keys = set()
    for source in (game / "localisation").rglob("*_l_english.yml"):
        for line in source.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            match = re.match(r'^\s*([A-Z0-9]{3}(?:_ADJ)?):\d*\s+', line)
            if match:
                vanilla_loc_keys.add(match.group(1))
    for slot, tag in enumerate(sorted(countries)):
        c = countries[tag]
        lines.append(f'{tag} = "countries/{tag}.txt"')
        if tag not in vanilla_loc_keys:
            loc.append(f' {tag}:0 "{c["name"]}"')
        if f'{tag}_ADJ' not in vanilla_loc_keys:
            loc.append(f' {tag}_ADJ:0 "{c["name"]}"')
        color, color_source = original_colors.get(tag, (safe_color(tag, c["mapcolor"]), "generated"))
        gfx, government, _, unit = REGION_STYLE.get(c["continent"], REGION_STYLE["Europe"])
        if tag in MONARCHIES: government = "monarchy"
        if tag == "VAT": government = "theocracy"
        reform = {"monarchy":"autocracy_reform", "theocracy":"leading_clergy_reform"}.get(government, "oligarchy_reform")
        definition = f'''graphical_culture = {gfx}gfx\ncolor = {{ {color[0]} {color[1]} {color[2]} }}\nhistorical_score = 0\nhistorical_idea_groups = {{ economic_ideas defensive_ideas trade_ideas administrative_ideas }}\nmonarch_names = {{ "Leader #0" = 100 "Alexander #0" = 80 "Michael #0" = 80 "David #0" = 80 "John #0" = 80 "Maria #0" = 80 "Anna #0" = 80 "Peter #0" = 80 "George #0" = 80 "Thomas #0" = 80 }}\nleader_names = {{ "Smith" "Brown" "Martin" "Miller" "Wilson" "Moore" "Taylor" "Anderson" "Thomas" "Jackson" }}\nship_names = {{ "Unity" "Liberty" "Republic" "Defender" "Guardian" "Victory" "Enterprise" "Endeavour" "Independence" "Constitution" }}\n'''
        (OUT / f"common/countries/{tag}.txt").write_text(definition, encoding="utf-8")
        capital_lon, capital_lat, capital_source = capitals[tag]
        cap = CAPITAL_PROVINCE_OVERRIDES.get(tag)
        if cap is None or not any(p["id"] == cap for p in by_tag[tag]):
            cap = min(by_tag[tag], key=lambda p:(p["lon"]-capital_lon)**2 + (p["lat"]-capital_lat)**2)["id"]
        religion = religion_for(tag, c["continent"])
        ruler = RULERS.get(tag, (f'{c["name"]} Leadership', 3, 3, 3))
        primary_culture = by_tag[tag][0].get("culture", "english")
        eu_status = "elector = yes\n" if tag in EU_2000_MEMBERS else ""
        hist = f'''government = {government}\nadd_government_reform = {reform}\ntechnology_group = western\nprimary_culture = {primary_culture}\nreligion = {religion}\ncapital = {cap}\n{eu_status}2000.1.1 = {{\n monarch = {{ name = "{ruler[0]}" adm = {ruler[1]} dip = {ruler[2]} mil = {ruler[3]} }}\n}}\n'''
        (OUT / f"history/countries/{tag} - {c['name']}.txt").write_text(hist, encoding="utf-8")
        rows.append({**c, "capital_province": cap, "capital_source":capital_source, "color_source":color_source, "government": government, "religion": religion})
    (OUT / "common/country_tags/00_modern_countries.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
    (OUT / "localisation/md_countries_l_english.yml").write_text("\n".join(loc)+"\n", encoding="utf-8-sig")
    for tag in ["REB", "PIR", "NAT", *vanilla_tags]:
        (OUT / f"history/countries/{tag} - Dormant.txt").write_text(
            "# Dormant historical tag retained for base-script compatibility.\ntechnology_group = western\n",
            encoding="utf-8")
    with (OUT / "source_data/countries.csv").open("w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    return countries, by_tag


def write_provinces(provinces, countries):
    claims_by_province = defaultdict(list)
    with CLAIMS_PATH.open(encoding="utf-8") as f:
        for claim in csv.DictReader(f):
            claims_by_province[int(claim["province_id"])].append(claim)
    provinces_by_owner = defaultdict(list)
    for province in provinces:
        provinces_by_owner[province["tag"]].append(province)
    with CLAIM_GROUPS_PATH.open(encoding="utf-8") as f:
        for group in csv.DictReader(f):
            for province in provinces_by_owner[group["target_tag"]]:
                claims_by_province[province["id"]].append({**group, "province_id": str(province["id"])})
    country_pop = {t:max(c["population"],1) for t,c in countries.items()}
    country_gdp = {t:max(c["gdp"],1) for t,c in countries.items()}
    counts = defaultdict(int)
    for p in provinces:
        if p["tag"] in countries: counts[p["tag"]] += 1
    rows=[]
    for p in provinces:
        tag=p["tag"]
        if tag not in countries: continue
        # Country totals are logarithmically compressed, then spread over provinces.
        total = max(3*counts[tag], round(7*math.log10(country_pop[tag]) + 5*math.log10(country_gdp[tag])))
        dev = max(3, round(total/counts[tag]))
        tax=max(1,dev//3); prod=max(1,(dev-tax)//2); manpower=max(1,dev-tax-prod)
        culture=p.get("culture","english"); religion=p.get("religion",religion_for(tag,countries[tag]["continent"])); goods=p.get("trade_goods","grain")
        eu_status = "hre = yes\n" if tag in EU_2000_MEMBERS else ""
        historical = "".join(
            f'add_{claim["strength"]} = {claim["claimant_tag"]}\n'
            for claim in sorted(claims_by_province[p["id"]], key=lambda row: (row["strength"], row["claimant_tag"]))
        )
        text=f'''owner = {tag}\ncontroller = {tag}\nadd_core = {tag}\n{historical}{eu_status}culture = {culture}\nreligion = {religion}\ntrade_goods = {goods}\nbase_tax = {tax}\nbase_production = {prod}\nbase_manpower = {manpower}\ncapital = "{p["name"].split("-",1)[-1].strip()}"\nis_city = yes\n'''
        (OUT / f'history/provinces/{p["id"]} - MD.txt').write_text(text,encoding="utf-8")
        rows.append({k:p.get(k,"") for k in ["id","name","tag","lon","lat","culture","religion","trade_goods"]}|{"development":dev})
    with (OUT/"source_data/provinces.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    expanded_claims = [claim for values in claims_by_province.values() for claim in values]
    with (OUT / "source_data/historical_claims.csv").open("w", newline="", encoding="utf-8") as f:
        fields=["claimant_tag","province_id","strength","dispute","basis","source_url"]
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows({field:claim[field] for field in fields} for claim in sorted(expanded_claims,key=lambda row:(int(row["province_id"]),row["claimant_tag"])))
    claimants = {claim["claimant_tag"] for claim in expanded_claims}
    with (OUT / "source_data/country_claim_reviews.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tag", "status", "note"]); writer.writeheader()
        for country_tag in sorted(countries):
            writer.writerow({"tag": country_tag, "status": "claims_added" if country_tag in claimants else "reviewed_no_mappable_claim", "note": "See historical_claims.csv" if country_tag in claimants else "No qualifying dispute mappable without materially overstating it on the vanilla province map"})


def write_ideas(countries):
    groups=defaultdict(list)
    for tag,c in countries.items():
        region = re.sub(r'[^a-z0-9]+', '_', c["continent"].lower()).strip('_')
        groups[region].append(tag)
    out=[]
    loc=["l_english:"]
    for region,tags in sorted(groups.items()):
        generic=[t for t in tags if t not in UNIQUE_IDEA_TAGS]
        if generic:
            title=region.replace('_',' ').title()
            loc.extend([f' md_{region}_ideas:0 "{title} Ideas"', f' md_{region}_ideas_start:0 "{title} Traditions"', f' md_{region}_ideas_bonus:0 "{title} Ambition"'])
            for i in range(1,8):
                loc.extend([f' md_{region}_{i}:0 "{title} Priority {i}"', f' md_{region}_{i}_desc:0 "A shared modern strategic priority for states in this region."'])
            out.append(f'''md_{region}_ideas = {{\n start = {{ global_tax_modifier = 0.1 }}\n bonus = {{ discipline = 0.05 }}\n trigger = {{ OR = {{ {' '.join(f'tag = {t}' for t in generic)} }} }}\n free = yes\n md_{region}_1 = {{ production_efficiency = 0.1 }}\n md_{region}_2 = {{ manpower_recovery_speed = 0.1 }}\n md_{region}_3 = {{ global_trade_power = 0.1 }}\n md_{region}_4 = {{ diplomatic_reputation = 1 }}\n md_{region}_5 = {{ land_morale = 0.1 }}\n md_{region}_6 = {{ technology_cost = -0.05 }}\n md_{region}_7 = {{ global_unrest = -1 }}\n}}''')
    for tag in sorted(UNIQUE_IDEA_TAGS & countries.keys()):
        name=countries[tag]["name"]
        loc.extend([f' md_{tag.lower()}_ideas:0 "{name} Ideas"', f' md_{tag.lower()}_ideas_start:0 "{name} Traditions"', f' md_{tag.lower()}_ideas_bonus:0 "{name} Ambition"'])
        for i in range(1,8):
            loc.extend([f' md_{tag.lower()}_{i}:0 "{name} Priority {i}"', f' md_{tag.lower()}_{i}_desc:0 "A defining strategic capability of {name} at the dawn of the millennium."'])
        out.append(f'''md_{tag.lower()}_ideas = {{\n start = {{ administrative_efficiency = 0.05 }}\n bonus = {{ discipline = 0.05 }}\n trigger = {{ tag = {tag} }}\n free = yes\n md_{tag.lower()}_1 = {{ global_tax_modifier = 0.15 }}\n md_{tag.lower()}_2 = {{ manpower_recovery_speed = 0.15 }}\n md_{tag.lower()}_3 = {{ diplomatic_reputation = 1 }}\n md_{tag.lower()}_4 = {{ production_efficiency = 0.15 }}\n md_{tag.lower()}_5 = {{ land_morale = 0.1 }}\n md_{tag.lower()}_6 = {{ technology_cost = -0.05 }}\n md_{tag.lower()}_7 = {{ global_unrest = -1 }}\n}}''')
    (OUT/"common/ideas/00_md_national_ideas.txt").write_text("\n\n".join(out)+"\n",encoding="utf-8")
    (OUT/"localisation/md_ideas_l_english.yml").write_text("\n".join(loc)+"\n",encoding="utf-8-sig")


def write_flags(countries):
    for tag,c in countries.items():
        iso2=c.get("iso2","").lower()
        flag_url=FLAG_URL.format(iso2=iso2) if len(iso2)==2 else None
        target=OUT/f"gfx/flags/{tag}.tga"
        try:
            if flag_url:
                png=CACHE/"flags"/f"{tag}.png"; download(flag_url,png)
                image=Image.open(png).convert("RGB")
                # EU4 flags are square textures; preserve the flag's aspect ratio with padding.
                image.thumbnail((128,128),Image.Resampling.LANCZOS)
                canvas=Image.new("RGB",(128,128),(240,240,240))
                canvas.paste(image,((128-image.width)//2,(128-image.height)//2))
                canvas.save(target)
                continue
        except Exception:
            pass
        color=safe_color(tag,c["mapcolor"])
        img=Image.new("RGB",(128,128),color)
        img.save(target)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--game",type=Path,required=True)
    args=parser.parse_args()
    if not (args.game/"eu4.exe").exists(): raise SystemExit(f"Invalid EU4 path: {args.game}")
    clean_output(); write_descriptor(); write_defines_bookmark(); write_eu_system(); write_institutions()
    countries,polygons,metadata=country_data(natural_earth_path())
    provinces=assign_provinces(province_records(args.game),polygons,metadata)
    countries,_=write_countries(countries,provinces,args.game)
    write_provinces(provinces,countries); write_ideas(countries); write_flags(countries)
    (OUT/"source_data/dataset_sources.txt").write_text(
        "Natural Earth Admin 0 Countries 5.1.1 (public domain)\n"+NE_URL+"\nFlagCDN national flag images\nhttps://flagcdn.com/\nCapital coordinate dataset\n"+CAPITALS_URL+"\n",encoding="utf-8")
    print(f"Generated {len(countries)} countries and {sum(1 for p in provinces if p['tag'] in countries)} provinces in {OUT}")

if __name__ == "__main__": main()

