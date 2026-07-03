#!/usr/bin/env python3
"""Apply canonical historical claims to an already-generated mod tree."""
from __future__ import annotations
import csv, re, shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; MOD = ROOT / "MillenniumDawnEU4"
CLAIMS = ROOT / "tools" / "data" / "historical_claims.csv"; GROUPS = ROOT / "tools" / "data" / "historical_claim_groups.csv"
claims_by_pid = defaultdict(list)
with CLAIMS.open(encoding="utf-8") as f:
    for row in csv.DictReader(f): claims_by_pid[row["province_id"]].append(row)
provinces=list(csv.DictReader((MOD/"source_data"/"provinces.csv").open(encoding="utf-8")))
provinces_by_owner=defaultdict(list)
for province in provinces: provinces_by_owner[province["tag"]].append(province)
with GROUPS.open(encoding="utf-8") as f:
    for group in csv.DictReader(f):
        for province in provinces_by_owner[group["target_tag"]]: claims_by_pid[province["id"]].append({**group,"province_id":province["id"]})
for pid, claims in claims_by_pid.items():
    matches = list((MOD / "history" / "provinces").glob(f"{pid} - *.txt"))
    if len(matches) != 1: raise SystemExit(f"Expected one history file for province {pid}, found {len(matches)}")
    path=matches[0]; text=path.read_text(encoding="utf-8")
    owner=re.search(r"(?m)^owner = ([A-Z0-9]{3})$",text).group(1)
    text=re.sub(r"(?m)^add_(?:claim|core) = (?!"+re.escape(owner)+r"$)[A-Z0-9]{3}\n","",text)
    owner_core=re.search(r"(?m)^add_core = [A-Z0-9]{3}\n",text)
    additions="".join(f"add_{row['strength']} = {row['claimant_tag']}\n" for row in sorted(claims,key=lambda r:(r['strength'],r['claimant_tag'])))
    path.write_text(text[:owner_core.end()]+additions+text[owner_core.end():],encoding="utf-8")
fields=["claimant_tag","province_id","strength","dispute","basis","source_url"]
with (MOD/"source_data"/"historical_claims.csv").open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    writer.writerows({field:row[field] for field in fields} for rows in claims_by_pid.values() for row in rows)
countries=list(csv.DictReader((MOD/"source_data"/"countries.csv").open(encoding="utf-8")))
claimants={row["claimant_tag"] for rows in claims_by_pid.values() for row in rows}
with (MOD/"source_data"/"country_claim_reviews.csv").open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=["tag","status","note"]);writer.writeheader()
    for country in sorted(countries,key=lambda row:row["tag"]):
        tag=country["tag"];writer.writerow({"tag":tag,"status":"claims_added" if tag in claimants else "reviewed_no_mappable_claim","note":"See historical_claims.csv" if tag in claimants else "No qualifying dispute mappable without materially overstating it on the vanilla province map"})
