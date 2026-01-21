#!/usr/bin/env python3
"""
Deep analysis of what's missing after the smart merge
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def deep_analysis():
    print("=" * 70)
    print("DIEPE ANALYSE: WAT ONTBREEKT ER NOG?")
    print("=" * 70)

    # Load all files
    newer = DBPFFile(Path("sims4_save_merger/Slot_00000002.save"))
    older = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))
    merged = DBPFFile(Path("sims4_save_merger/Slot_00000002_smart_merged.save"))

    print(f"\n📁 Bestandsgrootte:")
    print(f"   Nieuwere save: {Path('sims4_save_merger/Slot_00000002.save').stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   Oudere save:   {Path('sims4_save_merger/Slot_00000012.save').stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   Smart merged:  {Path('sims4_save_merger/Slot_00000002_smart_merged.save').stat().st_size / 1024 / 1024:.2f} MB")

    newer_keys = set(newer.resources.keys())
    older_keys = set(older.resources.keys())
    merged_keys = set(merged.resources.keys())

    print(f"\n📊 Resource telling:")
    print(f"   Nieuwere: {len(newer_keys)}")
    print(f"   Oudere:   {len(older_keys)}")
    print(f"   Merged:   {len(merged_keys)}")

    # What's in older but NOT in merged?
    missing_from_merged = older_keys - merged_keys
    print(f"\n❌ Resources in oudere save maar NIET in merged: {len(missing_from_merged)}")

    if missing_from_merged:
        print("\n   Per type:")
        type_counts = {}
        for key in missing_from_merged:
            type_id = key[0]
            type_counts[type_id] = type_counts.get(type_id, 0) + 1
        for type_id, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"      Type 0x{type_id:08X}: {count}")

    # Check data sizes in merged vs older for resources that ARE in merged
    print(f"\n🔍 Data vergelijking (merged vs oudere save):")

    # Resources that are in both merged and older
    common_with_older = merged_keys & older_keys

    smaller_in_merged = []
    for key in common_with_older:
        merged_size = len(merged.resources[key].data)
        older_size = len(older.resources[key].data)
        if merged_size < older_size:
            smaller_in_merged.append({
                'key': key,
                'merged_size': merged_size,
                'older_size': older_size,
                'diff': older_size - merged_size
            })

    print(f"   Resources waar merged KLEINER is dan oudere: {len(smaller_in_merged)}")

    if smaller_in_merged:
        smaller_in_merged.sort(key=lambda x: -x['diff'])
        total_missing = sum(x['diff'] for x in smaller_in_merged)
        print(f"   Totaal ontbrekende data: {total_missing / 1024 / 1024:.2f} MB")

        print(f"\n   Top 20 grootste verschillen:")
        for i, item in enumerate(smaller_in_merged[:20]):
            type_id = item['key'][0]
            print(f"      {i+1}. Type 0x{type_id:08X}: merged={item['merged_size']:>8} vs older={item['older_size']:>8} (mist {item['diff']/1024:.1f} KB)")

    # Check which version was used in merged (newer or older)
    print(f"\n🔍 Bron analyse (waar komt merged data vandaan?):")

    from_newer = 0
    from_older = 0
    from_neither = 0
    modified = 0

    for key in merged_keys:
        merged_data = merged.resources[key].data
        has_newer = key in newer_keys
        has_older = key in older_keys

        if has_newer and newer.resources[key].data == merged_data:
            from_newer += 1
        elif has_older and older.resources[key].data == merged_data:
            from_older += 1
        elif has_newer or has_older:
            modified += 1  # Data is different from both
        else:
            from_neither += 1

    print(f"   Van nieuwere save: {from_newer}")
    print(f"   Van oudere save:   {from_older}")
    print(f"   Gemodificeerd:     {modified}")
    print(f"   Van geen beide:    {from_neither}")

    # Analyze Type 0x00000006 specifically (lot data)
    print(f"\n🏠 Type 0x00000006 (Lot/Zone data) analyse:")

    type6_newer = {k: v for k, v in newer.resources.items() if k[0] == 0x00000006}
    type6_older = {k: v for k, v in older.resources.items() if k[0] == 0x00000006}
    type6_merged = {k: v for k, v in merged.resources.items() if k[0] == 0x00000006}

    print(f"   In nieuwere: {len(type6_newer)} resources, {sum(len(r.data) for r in type6_newer.values())/1024/1024:.2f} MB")
    print(f"   In oudere:   {len(type6_older)} resources, {sum(len(r.data) for r in type6_older.values())/1024/1024:.2f} MB")
    print(f"   In merged:   {len(type6_merged)} resources, {sum(len(r.data) for r in type6_merged.values())/1024/1024:.2f} MB")

    # Check if merged type6 matches older
    type6_matches_older = 0
    type6_matches_newer = 0
    type6_smaller = 0

    for key in type6_merged:
        merged_data = type6_merged[key].data
        if key in type6_older and type6_older[key].data == merged_data:
            type6_matches_older += 1
        elif key in type6_newer and type6_newer[key].data == merged_data:
            type6_matches_newer += 1

        if key in type6_older and len(merged_data) < len(type6_older[key].data):
            type6_smaller += 1

    print(f"\n   Type 0x00000006 bronnen:")
    print(f"      Komt van oudere: {type6_matches_older}")
    print(f"      Komt van nieuwere: {type6_matches_newer}")
    print(f"      Kleiner dan oudere: {type6_smaller}")

    # Show all unique resource types in older save
    print(f"\n📋 Alle resource types in oudere save:")
    type_summary = {}
    for key, resource in older.resources.items():
        type_id = key[0]
        if type_id not in type_summary:
            type_summary[type_id] = {'count': 0, 'size': 0}
        type_summary[type_id]['count'] += 1
        type_summary[type_id]['size'] += len(resource.data)

    for type_id, stats in sorted(type_summary.items(), key=lambda x: -x[1]['size']):
        in_merged = sum(1 for k in merged_keys if k[0] == type_id)
        print(f"   Type 0x{type_id:08X}: {stats['count']:4} resources, {stats['size']/1024/1024:>6.2f} MB | In merged: {in_merged}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    deep_analysis()
