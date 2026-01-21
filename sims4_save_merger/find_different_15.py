#!/usr/bin/env python3
"""
Find the 15 resources that differ between our merge and the working save
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def find_different():
    print("=" * 70)
    print("RESOURCES DIE VERSCHILLEN TUSSEN MERGE EN WERKENDE SAVE")
    print("=" * 70)

    working = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))
    our_merge = DBPFFile(Path("sims4_save_merger/test_prefer_larger.save"))
    corrupt = DBPFFile(Path("sims4_save_merger/Slot_00000002.save"))

    different = []
    for key in set(our_merge.resources.keys()) & set(working.resources.keys()):
        merge_data = our_merge.resources[key].data
        work_data = working.resources[key].data

        if merge_data != work_data:
            # Check where our merge data came from
            in_corrupt = key in corrupt.resources
            matches_corrupt = in_corrupt and corrupt.resources[key].data == merge_data

            different.append({
                'key': key,
                'type_id': key[0],
                'merge_size': len(merge_data),
                'working_size': len(work_data),
                'from_corrupt': matches_corrupt,
                'diff': len(merge_data) - len(work_data)
            })

    print(f"\nAantal verschillende resources: {len(different)}")
    print(f"\n{'Type':<12} {'Merge':<10} {'Working':<10} {'Diff':<10} {'Bron'}")
    print("-" * 60)

    for d in sorted(different, key=lambda x: -abs(x['diff'])):
        source = "CORRUPT" if d['from_corrupt'] else "OUDER?"
        print(f"0x{d['type_id']:08X}  {d['merge_size']:<10} {d['working_size']:<10} {d['diff']:<+10} {source}")

    # Summary
    from_corrupt = sum(1 for d in different if d['from_corrupt'])
    print(f"\n📊 Samenvatting:")
    print(f"   Van corrupte save: {from_corrupt}")
    print(f"   Van andere bron: {len(different) - from_corrupt}")

    total_extra = sum(d['diff'] for d in different if d['diff'] > 0)
    total_missing = sum(-d['diff'] for d in different if d['diff'] < 0)
    print(f"   Totaal extra data in merge: {total_extra / 1024:.1f} KB")
    print(f"   Totaal ontbrekende data: {total_missing / 1024:.1f} KB")

if __name__ == '__main__':
    find_different()
