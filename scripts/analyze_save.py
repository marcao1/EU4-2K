#!/usr/bin/env python3
"""Summarize the wars in an EU4 2K save for observer-run comparisons.

Read-only. Reports the scripted 2000.1.1 wars from data/wars_2000.csv and every
other war started on or after the bookmark, grouped by casus belli. Plain-text
and zip-compressed saves are supported; ironman (binary) saves are not.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WAR_DATA = ROOT / "data" / "wars_2000.csv"
SAVE_CANDIDATES = tuple(
    base / "Paradox Interactive" / "Europa Universalis IV" / "save games" / "autosave.eu4"
    for base in (
        Path.home() / "Documents",
        Path.home() / "OneDrive" / "Dokumente",
        Path.home() / "OneDrive" / "Documents",
    )
)
# Inferred from test saves: scripted white peaces record 1, attacker victories 2.
OUTCOMES = {"1": "white peace", "2": "attacker won", "3": "defender won"}

WAR_BLOCK = re.compile(r'\n(active_war|previous_war)=\{\n\tname="([^"]+)"(.*?)\n\}', re.S)
DATED_ENTRY = re.compile(r'\n\t\t(\d+\.\d+\.\d+)=\{')


def read_save(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"PK"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            data = archive.read("gamestate")
    if data.startswith(b"EU4bin"):
        raise SystemExit("Binary (ironman) saves are not supported")
    return data.decode("latin-1")


def date_key(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def wars(text: str) -> list[dict[str, str]]:
    result = []
    for match in WAR_BLOCK.finditer(text):
        body = match.group(3)
        dates = DATED_ENTRY.findall(body)
        goal = re.findall(r'type="(\w+)"[^}]*?casus_belli="(\w+)"', body)
        removals = re.findall(r'\n\t\t(\d+\.\d+\.\d+)=\{\s*rem_(?:attacker|defender)=', body)
        outcome = re.search(r'\n\toutcome=(\d+)', body)
        attacker = re.search(r'original_attacker="(\w+)"', body)
        defender = re.search(r'original_defender="(\w+)"', body)
        result.append({
            "state": "active" if match.group(1) == "active_war" else "ended",
            "name": match.group(2),
            "start": dates[0] if dates else "",
            "end": max(removals, key=date_key) if removals and match.group(1) == "previous_war" else "",
            "casus_belli": goal[-1][1] if goal else "unknown",
            "attacker": attacker.group(1) if attacker else "?",
            "defender": defender.group(1) if defender else "?",
            "outcome": OUTCOMES.get(outcome.group(1), outcome.group(1)) if outcome else "",
        })
    return result


def scripted_war_names() -> set[str]:
    with WAR_DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["name"] for row in csv.DictReader(handle)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("save", nargs="?", help="save file (defaults to the autosave)")
    parser.add_argument("--since", type=int, default=2000, help="first year counted as a new war")
    args = parser.parse_args()
    if args.save:
        path = Path(args.save)
    else:
        path = next((candidate for candidate in SAVE_CANDIDATES if candidate.exists()), None)
        if path is None:
            raise SystemExit("No autosave found; pass the save path")
    text = read_save(path)
    date = re.search(r'^date=(\S+)', text, re.M)
    player = re.search(r'^player="(\w+)"', text, re.M)
    print(f"Save: {path}")
    print(f"Date: {date.group(1) if date else '?'}  Player: {player.group(1) if player else 'observer'}")

    all_wars = wars(text)
    scripted = scripted_war_names()
    print("\nScripted 2000.1.1 wars:")
    for war in all_wars:
        if war["name"] in scripted:
            ended = f"ended {war['end']}, {war['outcome']}" if war["state"] == "ended" else "still active"
            print(f"  {war['name']}: {ended}")
    missing = scripted - {war["name"] for war in all_wars}
    for name in sorted(missing):
        print(f"  {name}: not found in save")

    new_wars = [
        war for war in all_wars
        if war["name"] not in scripted and war["start"] and date_key(war["start"])[0] >= args.since
    ]
    by_cb = Counter(war["casus_belli"] for war in new_wars)
    print(f"\nWars started since {args.since}: {len(new_wars)}")
    for casus_belli, count in by_cb.most_common():
        print(f"  {casus_belli}: {count}")
    for war in sorted(new_wars, key=lambda item: date_key(item["start"])):
        status = war["outcome"] if war["state"] == "ended" else "active"
        print(f"  {war['start']:>10}  {war['attacker']} vs {war['defender']:<4} {war['casus_belli']:<22} {status:<13} {war['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
