#!/usr/bin/env python3
"""Static validation for the generated Millennium Dawn EU4 foundation."""
from __future__ import annotations
import argparse,csv,re,sys
from collections import Counter
from pathlib import Path

def balanced(path:Path)->bool:
    text=path.read_text(encoding="utf-8-sig",errors="ignore")
    return text.count('{')==text.count('}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mod',type=Path,required=True);a=ap.parse_args();m=a.mod
    errors=[]
    required=[m/'descriptor.mod',m/'common/defines/md_defines.lua',m/'source_data/countries.csv',m/'source_data/provinces.csv']
    for p in required:
        if not p.exists():errors.append(f"missing {p}")
    for p in m.rglob('*'):
        if p.suffix in {'.txt','.yml','.mod','.lua'} and not balanced(p):errors.append(f"unbalanced braces: {p}")
    if errors:
        print('\n'.join(errors));return 1
    countries=list(csv.DictReader((m/'source_data/countries.csv').open(encoding='utf-8')))
    provinces=list(csv.DictReader((m/'source_data/provinces.csv').open(encoding='utf-8')))
    tags=[c['tag'] for c in countries];dupes=[t for t,n in Counter(tags).items() if n>1]
    if dupes:errors.append('duplicate tags: '+','.join(dupes))
    pids=[p['id'] for p in provinces];dupes=[p for p,n in Counter(pids).items() if n>1]
    if dupes:errors.append('duplicate provinces: '+','.join(dupes[:20]))
    owners=set(p['tag'] for p in provinces)
    for c in countries:
        tag=c['tag'];cap=c['capital_province']
        if tag not in owners:errors.append(f'{tag} owns no province')
        if not any(p['id']==cap and p['tag']==tag for p in provinces):errors.append(f'{tag} does not own capital {cap}')
        for p in [m/f'common/countries/{tag}.txt',m/f'gfx/flags/{tag}.tga']:
            if not p.exists():errors.append(f'missing {p}')
    end=(m/'common/defines/md_defines.lua').read_text()
    if '9999.12.31' not in end:errors.append('open end date missing')
    expected_owners={'80':'DEU','93':'BEL','139':'BIH','4126':'YUG','4173':'YUG','4757':'YUG','4768':'DEU'}
    province_by_id={p['id']:p for p in provinces}
    for pid,owner in expected_owners.items():
        if province_by_id.get(pid,{}).get('tag') != owner:
            errors.append(f'province {pid} must be owned by {owner}')
    eu_members={'AUT','BEL','DEU','DNK','ESP','FIN','FRA','GRC','IRL','ITA','LUX','NLD','PRT','SWE','UKG'}
    actual_electors=set()
    for tag in eu_members:
        matches=list((m/'history/countries').glob(f'{tag} - *.txt'))
        if matches and re.search(r'(?m)^elector\s*=\s*yes\s*$',matches[0].read_text(encoding='utf-8-sig')):
            actual_electors.add(tag)
    if actual_electors != eu_members:errors.append('EU Council membership mismatch: '+','.join(sorted(eu_members-actual_electors)))
    eu_provinces=0
    for p in (m/'history/provinces').glob('*.txt'):
        text=p.read_text(encoding='utf-8-sig')
        owner=re.search(r'(?m)^owner\s*=\s*([A-Z0-9]{3})\s*$',text)
        if owner and owner.group(1) in eu_members:
            eu_provinces += 1
            if not re.search(r'(?m)^hre\s*=\s*yes\s*$',text):errors.append(f'EU province missing hre=yes: {p.name}')
    if eu_provinces == 0:errors.append('EU has no member provinces')
    if not (m/'history/diplomacy/hre.txt').exists():errors.append('EU presidency history missing')
    yug=next((c for c in countries if c['tag']=='YUG'),None)
    if not yug or yug.get('religion') != 'orthodox':errors.append('YUG must be orthodox')
    print(f"Validated {len(countries)} countries, {len(provinces)} provinces, {sum(1 for _ in m.rglob('*.txt'))} script files")
    if errors:print('\n'.join(errors));return 1
    print('Static validation passed');return 0
if __name__=='__main__':sys.exit(main())

