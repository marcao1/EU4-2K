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
    required=[m/'descriptor.mod',m/'common/defines/md_defines.lua',m/'common/institutions/00_md_institutions.txt',m/'localisation/md_institutions_l_english.yml',m/'source_data/countries.csv',m/'source_data/provinces.csv',m/'source_data/historical_claims.csv',m/'source_data/country_claim_reviews.csv']
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
    claims=list(csv.DictReader((m/'source_data/historical_claims.csv').open(encoding='utf-8')))
    reviews=list(csv.DictReader((m/'source_data/country_claim_reviews.csv').open(encoding='utf-8')))
    review_tags=[r['tag'] for r in reviews]
    if set(review_tags) != set(tags) or len(review_tags) != len(set(review_tags)):errors.append('claim reviews must cover every playable country exactly')
    province_ids=set(pids);claim_keys=[]
    province_by_id={p['id']:p for p in provinces}
    for claim in claims:
        key=(claim['claimant_tag'],claim['province_id'],claim['strength']);claim_keys.append(key)
        if claim['claimant_tag'] not in tags:errors.append(f'unknown claim tag {claim["claimant_tag"]}')
        if claim['province_id'] not in province_ids:errors.append(f'unknown claimed province {claim["province_id"]}')
        if claim['strength'] not in {'claim','core'}:errors.append(f'invalid claim strength {claim["strength"]}')
        if not claim.get('source_url'):errors.append(f'unsourced claim {key}')
        pf=next(m.glob(f'history/provinces/{claim["province_id"]} - *.txt'),None)
        if province_by_id.get(claim['province_id'],{}).get('tag') == claim['claimant_tag']:errors.append(f'self-claim is redundant: {key}')
        if not pf:errors.append(f'claimed province history missing: {key}')
        elif pf.read_text(encoding='utf-8').count(f'add_{claim["strength"]} = {claim["claimant_tag"]}') != 1:errors.append(f'claim not emitted exactly once: {key}')
    if len(claim_keys) != len(set(claim_keys)):errors.append('duplicate historical claims')
    for c in countries:
        tag=c['tag'];cap=c['capital_province']
        if tag not in owners:errors.append(f'{tag} owns no province')
        if not any(p['id']==cap and p['tag']==tag for p in provinces):errors.append(f'{tag} does not own capital {cap}')
        for p in [m/f'common/countries/{tag}.txt',m/f'gfx/flags/{tag}.tga']:
            if not p.exists():errors.append(f'missing {p}')
    end=(m/'common/defines/md_defines.lua').read_text()
    if '9999.12.31' not in end:errors.append('open end date missing')
    descriptor=(m/'descriptor.mod').read_text(encoding='utf-8-sig')
    if 'replace_path="common/institutions"' not in descriptor:errors.append('institution replacement path missing')
    institutions=(m/'common/institutions/00_md_institutions.txt').read_text(encoding='utf-8-sig')
    institution_keys=['feudalism','renaissance','colonialism','printing_press','global_trade','manufactories','enlightenment','industrialization']
    for key in institution_keys:
        if len(re.findall(rf'(?m)^{key}\s*=\s*\{{',institutions)) != 1:errors.append(f'institution {key} must be defined exactly once')
    expected_owners={'80':'DEU','93':'BEL','139':'BIH','4126':'YUG','4173':'YUG','4757':'YUG','4768':'DEU'}
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

