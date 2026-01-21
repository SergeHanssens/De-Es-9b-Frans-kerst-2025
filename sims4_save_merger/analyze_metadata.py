#!/usr/bin/env python3
"""
Find the resources responsible for save metadata/thumbnail/household preview
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def analyze_metadata():
    print("=" * 80)
    print("ANALYSE: SAVE METADATA / THUMBNAIL / HOUSEHOLD INFO")
    print("=" * 80)

    corrupt = DBPFFile(Path("sims4_save_merger/AllSlots/Slot_00000002.save"))
    working = DBPFFile(Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4"))
    merged = DBPFFile(Path("sims4_save_merger/FINAL_ALLSLOTS_MERGED.save"))

    print("\n1. RESOURCE TYPES IN CORRUPT SAVE (met household preview)")
    print("-" * 60)

    # Group by type
    corrupt_types = {}
    for key, resource in corrupt.resources.items():
        type_id = key[0]
        if type_id not in corrupt_types:
            corrupt_types[type_id] = []
        corrupt_types[type_id].append({
            'key': key,
            'size': len(resource.data),
            'data_preview': resource.data[:20] if len(resource.data) >= 20 else resource.data
        })

    working_types = {}
    for key, resource in working.resources.items():
        type_id = key[0]
        if type_id not in working_types:
            working_types[type_id] = []
        working_types[type_id].append({
            'key': key,
            'size': len(resource.data)
        })

    merged_types = {}
    for key, resource in merged.resources.items():
        type_id = key[0]
        if type_id not in merged_types:
            merged_types[type_id] = []
        merged_types[type_id].append({
            'key': key,
            'size': len(resource.data)
        })

    # Show all types in corrupt
    print(f"\n{'Type ID':<14} {'Count':>6} {'Total Size':>12}  In Working?  In Merged?")
    print("-" * 70)

    for type_id in sorted(corrupt_types.keys()):
        resources = corrupt_types[type_id]
        count = len(resources)
        total_size = sum(r['size'] for r in resources)

        in_working = "YES" if type_id in working_types else "NO"
        in_merged = "YES" if type_id in merged_types else "NO"

        print(f"0x{type_id:08X}  {count:>6}  {total_size:>10} bytes  {in_working:<11}  {in_merged}")

    # Find types that are ONLY in corrupt (not in working)
    print("\n2. TYPES ALLEEN IN CORRUPT (niet in werkende)")
    print("-" * 60)

    only_corrupt = set(corrupt_types.keys()) - set(working_types.keys())
    if only_corrupt:
        for type_id in sorted(only_corrupt):
            resources = corrupt_types[type_id]
            print(f"\nType 0x{type_id:08X}: {len(resources)} resources")
            for r in resources[:5]:
                print(f"  Key: {r['key']}, Size: {r['size']} bytes")
                print(f"  Data preview: {r['data_preview'].hex()}")
    else:
        print("Geen - alle types in corrupt zijn ook in werkende")

    # Find types that are in corrupt but NOT in our merge
    print("\n3. TYPES IN CORRUPT MAAR NIET IN ONZE MERGE")
    print("-" * 60)

    only_in_corrupt = set(corrupt_types.keys()) - set(merged_types.keys())
    if only_in_corrupt:
        for type_id in sorted(only_in_corrupt):
            resources = corrupt_types[type_id]
            print(f"\nType 0x{type_id:08X}: {len(resources)} resources ONTBREEKT IN MERGE!")
            for r in resources[:3]:
                print(f"  Key: {r['key']}, Size: {r['size']} bytes")
    else:
        print("Geen - alle types in corrupt zijn ook in merge")

    # Check specific known metadata types
    print("\n4. BEKENDE METADATA TYPES")
    print("-" * 60)

    known_metadata = {
        0x545AC67A: "Thumbnail",
        0xB61DE6B4: "Household",
        0xC0DB5AE7: "SimInfo",
        0x0C772E27: "RelationshipData",
        0x00000001: "SaveGameHeader",
        0x00000002: "SaveGameData",
        0x00000003: "ZoneData",
    }

    for type_id, name in known_metadata.items():
        in_corrupt = type_id in corrupt_types
        in_working = type_id in working_types
        in_merged = type_id in merged_types

        if in_corrupt or in_working or in_merged:
            c_count = len(corrupt_types.get(type_id, []))
            w_count = len(working_types.get(type_id, []))
            m_count = len(merged_types.get(type_id, []))

            c_size = sum(r['size'] for r in corrupt_types.get(type_id, []))
            w_size = sum(r['size'] for r in working_types.get(type_id, []))
            m_size = sum(r['size'] for r in merged_types.get(type_id, []))

            print(f"\n{name} (0x{type_id:08X}):")
            print(f"  Corrupt:  {c_count:>3} resources, {c_size:>10} bytes")
            print(f"  Working:  {w_count:>3} resources, {w_size:>10} bytes")
            print(f"  Merged:   {m_count:>3} resources, {m_size:>10} bytes")

    # Check resources only in corrupt
    print("\n5. RESOURCES ALLEEN IN CORRUPT (niet in werkende)")
    print("-" * 60)

    corrupt_keys = set(corrupt.resources.keys())
    working_keys = set(working.resources.keys())
    merged_keys = set(merged.resources.keys())

    only_corrupt_keys = corrupt_keys - working_keys
    print(f"Aantal: {len(only_corrupt_keys)}")

    # Group by type
    by_type = {}
    for key in only_corrupt_keys:
        type_id = key[0]
        if type_id not in by_type:
            by_type[type_id] = []
        by_type[type_id].append(key)

    for type_id, keys in sorted(by_type.items()):
        total_size = sum(len(corrupt.resources[k].data) for k in keys)
        in_merge = sum(1 for k in keys if k in merged_keys)
        print(f"  Type 0x{type_id:08X}: {len(keys)} resources ({total_size} bytes) - {in_merge} in merge")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    analyze_metadata()
