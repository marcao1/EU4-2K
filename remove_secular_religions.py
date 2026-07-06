from pathlib import Path
import re

ROOT = Path(__file__).parent / "MillenniumDawnEU4"
REMOVED = {"secularism", "irreligious"}


def read(path: Path) -> str:
    # Latin-1 is intentionally used as a lossless one-byte transport. The
    # substitutions below only touch ASCII script identifiers.
    return path.read_text(encoding="latin-1", errors="strict")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="latin-1", newline="")


def remove_named_block(text: str, name: str, required: bool = True) -> str:
    match = re.search(rf"(?m)^(?P<indent>\s*){re.escape(name)}\s*=\s*\{{", text)
    if not match:
        if required:
            raise RuntimeError(f"Block not found: {name}")
        return text
    start = match.start()
    brace = text.find("{", match.start())
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                while end < len(text) and text[end] in " \t":
                    end += 1
                if end < len(text) and text[end] == "\r":
                    end += 1
                if end < len(text) and text[end] == "\n":
                    end += 1
                return text[:start] + text[end:]
    raise RuntimeError(f"Unclosed block: {name}")


def remove_outer_blocks_containing(text: str, block_name: str, needle: str) -> str:
    while True:
        found = None
        for match in re.finditer(rf"(?m)^\s*{re.escape(block_name)}\s*=\s*\{{", text):
            brace = text.find("{", match.start())
            depth = 0
            for index in range(brace, len(text)):
                if text[index] == "{":
                    depth += 1
                elif text[index] == "}":
                    depth -= 1
                    if depth == 0:
                        segment = text[match.start():index + 1]
                        if needle in segment:
                            end = index + 1
                            while end < len(text) and text[end] in " \t\r\n":
                                end += 1
                            found = (match.start(), end)
                        break
            if found:
                break
        if not found:
            return text
        text = text[:found[0]] + text[found[1]:]


def normalize_history(path: Path) -> int:
    text = read(path)
    pattern = re.compile(r"\breligion\s*=\s*([A-Za-z0-9_]+)")
    matches = list(pattern.finditer(text))
    conventional = [m for m in matches if m.group(1) not in REMOVED]
    changed = 0

    def replacement(match: re.Match[str]) -> str:
        nonlocal changed
        if match.group(1) not in REMOVED:
            return match.group(0)
        preceding = [m for m in conventional if m.start() < match.start()]
        following = [m for m in conventional if m.start() > match.start()]
        if preceding:
            religion = preceding[-1].group(1)
        elif following:
            religion = following[0].group(1)
        elif path.name.startswith("EUR -"):
            religion = "catholic"
        else:
            raise RuntimeError(f"No conventional religion available in {path}")
        changed += 1
        return match.group(0).replace(match.group(1), religion)

    updated = pattern.sub(replacement, text)
    if changed:
        write(path, updated)
    return changed


religions = ROOT / "common/religions/et_religion.txt"
write(religions, remove_named_block(read(religions), "secular", required=False))

decisions = ROOT / "decisions/et_conversion_decisions.txt"
decision_text = read(decisions)
for block in ("adopt_secularism", "abandon_secularism"):
    decision_text = remove_named_block(decision_text, block, required=False)
write(decisions, decision_text)

event_file = ROOT / "events/et_secular_events.txt"
event_file.unlink(missing_ok=True)

history_changes = 0
for folder in (ROOT / "history/countries", ROOT / "history/provinces"):
    for file in folder.glob("*.txt"):
        history_changes += normalize_history(file)

print(f"Normalized {history_changes} history religion assignments.")

# Remove remaining feature-specific runtime hooks and modifiers.
for relative, block, needle in (
    ("events/et_china_events.txt", "country_event", "id = et_china.6"),
    ("events/et_immigration_events.txt", "modifier", "religion = secularism"),
    ("decisions/et_political_decisions.txt", "modifier", "religion = secularism"),
    ("common/rebel_types/et_revolutionary_rebels.txt", "modifier", "religion = secularism"),
):
    path = ROOT / relative
    write(path, remove_outer_blocks_containing(read(path), block, needle))

for relative, block in (
    ("common/event_modifiers/et_harmonized_modifiers.txt", "harmonized_irreligious"),
    ("common/on_actions/00_on_actions.txt", "on_harmonized_secular"),
    ("common/scripted_triggers/et_scripted_triggers.txt", "has_owner_religion_or_secularism"),
):
    path = ROOT / relative
    write(path, remove_named_block(read(path), block, required=False))

# Conditions excluding a now-impossible religion are redundant. Positive
# alternatives for that religion are removed from OR blocks.
for path in ROOT.rglob("*.txt"):
    if "history" in path.parts or path.name == "et_secular_events.txt":
        continue
    text = read(path)
    text = re.sub(r"(?m)^\s*NOT\s*=\s*\{\s*religion\s*=\s*secularism\s*\}\s*\r?\n", "", text)
    text = re.sub(r"(?m)^\s*owner\s*=\s*\{\s*religion\s*=\s*secularism\s*\}\s*\r?\n", "", text)
    text = re.sub(r"(?m)^\s*religion\s*=\s*secularism\s*\r?\n", "", text)
    text = text.replace("has_owner_religion_or_secularism = yes", "has_owner_religion = yes")
    write(path, text)

# Remove localization entries dedicated to the removed religion mechanics.
dedicated_key = re.compile(
    r"^(?:secularism|irreligious|secularism_religion_desc|irreligious_religion_desc|"
    r"province_is_or_accepts_secularism_tt|"
    r"adopt_secularism_(?:title|desc)|abandon_secularism_(?:title|desc)|"
    r"harmonized_irreligious|desc_harmonized_irreligious|"
    r"et\.(?:EVTNAME|EVTDESC|EVTOPT[A-Z])(?:28|54|76|77|78)|"
    r"et_china\.6\.[tda]):"
)
for path in (ROOT / "localisation").rglob("*.yml"):
    raw = read(path)
    lines = raw.splitlines(keepends=True)
    updated = "".join(line for line in lines if not dedicated_key.match(line.lstrip()))
    if updated != raw:
        write(path, updated)

# Technology 79 remains mechanically unchanged but no longer advertises the
# removed religion system.
technology = ROOT / "common/technologies/adm.txt"
write(technology, read(technology).replace("#Secularism", "#Religious Pluralism"))
for path in (ROOT / "localisation").glob("et_technology_l_*.yml"):
    raw = read(path)
    raw = re.sub(
        r'(?m)^(\s*adm_tech_cs_79_name:0\s+).+$',
        r'\1"Religious Pluralism"',
        raw,
    )
    raw = re.sub(
        r'(?m)^(\s*adm_tech_cs_79_desc:0\s+).+$',
        r'\1"Modern states increasingly protect freedom of conscience and equal treatment under the law."',
        raw,
    )
    write(path, raw)

china_events = ROOT / "events/et_china_events.txt"
write(china_events, re.sub(r"(?m)^#Irreligious Harmonization\r?\n", "", read(china_events)))
