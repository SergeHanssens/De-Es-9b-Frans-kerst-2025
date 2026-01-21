#!/usr/bin/env python3
"""
Analyze the DIFFERENT resources between saves
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def analyze_different():
    print("=" * 70)
    print("ANALYSE VAN VERSCHILLENDE RESOURCES")
    print("=" * 70)

    # Load files
    newer = DBPFFile(Path("sims4_save_merger/Slot_00000002.save"))
    older = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))

    newer_keys = set(newer.resources.keys())
    older_keys = set(older.resources.keys())

    # Find different resources (in both but different data)
    common = newer_keys & older_keys
    different = []

    for key in common:
        newer_data = newer.resources[key].data
        older_data = older.resources[key].data
        if newer_data != older_data:
            different.append({
                'key': key,
                'newer_size': len(newer_data),
                'older_size': len(older_data),
                'size_diff': len(older_data) - len(newer_data)
            })

    print(f"\nAantal resources in beide maar VERSCHILLEND: {len(different)}")

    # Sort by size difference (older - newer)
    different.sort(key=lambda x: x['size_diff'], reverse=True)

    # Total size difference
    total_newer_size = sum(d['newer_size'] for d in different)
    total_older_size = sum(d['older_size'] for d in different)

    print(f"\nTotale grootte van verschillende resources:")
    print(f"   In nieuwere save: {total_newer_size:,} bytes ({total_newer_size/1024/1024:.2f} MB)")
    print(f"   In oudere save:   {total_older_size:,} bytes ({total_older_size/1024/1024:.2f} MB)")
    print(f"   Verschil:         {total_older_size - total_newer_size:,} bytes ({(total_older_size - total_newer_size)/1024/1024:.2f} MB)")

    print(f"\n🔝 TOP 20 resources waar oudere MEER data heeft:")
    print("-" * 70)
    for i, d in enumerate(different[:20]):
        type_id = d['key'][0]
        print(f"   {i+1:2}. Type 0x{type_id:08X} | Nieuwer: {d['newer_size']:>8,} | Ouder: {d['older_size']:>8,} | +{d['size_diff']:>8,} bytes")

    # Group by type
    print(f"\n📊 GROOTTE VERSCHIL PER TYPE:")
    print("-" * 70)

    type_diffs = {}
    for d in different:
        type_id = d['key'][0]
        type_name = f"Type_0x{type_id:08X}"
        if type_id not in type_diffs:
            type_diffs[type_id] = {'count': 0, 'newer_total': 0, 'older_total': 0}
        type_diffs[type_id]['count'] += 1
        type_diffs[type_id]['newer_total'] += d['newer_size']
        type_diffs[type_id]['older_total'] += d['older_size']

    # Sort by total difference
    sorted_types = sorted(type_diffs.items(), key=lambda x: x[1]['older_total'] - x[1]['newer_total'], reverse=True)

    for type_id, stats in sorted_types[:15]:
        diff = stats['older_total'] - stats['newer_total']
        print(f"   Type 0x{type_id:08X}: {stats['count']:3} resources | Verschil: +{diff:>10,} bytes ({diff/1024:.1f} KB)")

    # Resources where older is SMALLER
    smaller_in_older = [d for d in different if d['size_diff'] < 0]
    print(f"\n📉 Resources waar NIEUWERE meer data heeft: {len(smaller_in_older)}")
    if smaller_in_older:
        smaller_in_older.sort(key=lambda x: x['size_diff'])
        for d in smaller_in_older[:5]:
            type_id = d['key'][0]
            print(f"   Type 0x{type_id:08X} | Nieuwer: {d['newer_size']:>8,} | Ouder: {d['older_size']:>8,} | {d['size_diff']:>8,} bytes")

if __name__ == '__main__':
    analyze_different()
