#!/usr/bin/env python3
"""
Compare working saves with corrupt save to find what's different
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def compare_all():
    print("=" * 70)
    print("VERGELIJKING: WERKENDE SAVES vs CORRUPTE SAVE")
    print("=" * 70)

    # Load all files
    files = {
        'corrupt': 'sims4_save_merger/Slot_00000002.save',
        'ver13 (Slot_12)': 'sims4_save_merger/Slot_00000012.save',
        'ver14': 'sims4_save_merger/Slot_00000002.save(14).ver4',
        'ver15': 'sims4_save_merger/Slot_00000002.save(15).ver4',
        'ver16': 'sims4_save_merger/Slot_00000002.save(16).ver4',
        'ver17 (oudste)': 'sims4_save_merger/Slot_00000002.save(17).ver4',
        'onze_merge': 'sims4_save_merger/test_prefer_larger.save',
    }

    loaded = {}
    for name, path in files.items():
        try:
            loaded[name] = DBPFFile(Path(path))
            size = Path(path).stat().st_size
            data_size = sum(len(r.data) for r in loaded[name].resources.values())
            print(f"\n📁 {name}:")
            print(f"   Bestand: {size / 1024 / 1024:.2f} MB")
            print(f"   Resources: {len(loaded[name].resources)}")
            print(f"   Data: {data_size / 1024 / 1024:.2f} MB")
        except Exception as e:
            print(f"\n❌ {name}: Kon niet laden - {e}")

    # Compare corrupt with most recent working (ver13/Slot_12)
    print("\n" + "=" * 70)
    print("CORRUPT vs WERKENDE (ver13/Slot_12)")
    print("=" * 70)

    corrupt = loaded.get('corrupt')
    working = loaded.get('ver13 (Slot_12)')

    if corrupt and working:
        corrupt_keys = set(corrupt.resources.keys())
        working_keys = set(working.resources.keys())

        only_corrupt = corrupt_keys - working_keys
        only_working = working_keys - corrupt_keys
        common = corrupt_keys & working_keys

        print(f"\n   Alleen in corrupt: {len(only_corrupt)}")
        print(f"   Alleen in werkende: {len(only_working)}")
        print(f"   In beide: {len(common)}")

        # Check size differences for common resources
        smaller_in_corrupt = []
        for key in common:
            c_size = len(corrupt.resources[key].data)
            w_size = len(working.resources[key].data)
            if c_size < w_size:
                smaller_in_corrupt.append({
                    'key': key,
                    'corrupt_size': c_size,
                    'working_size': w_size,
                    'diff': w_size - c_size
                })

        print(f"\n   Resources kleiner in corrupt: {len(smaller_in_corrupt)}")
        total_missing = sum(x['diff'] for x in smaller_in_corrupt)
        print(f"   Totaal ontbrekende data: {total_missing / 1024 / 1024:.2f} MB")

        # Show by type
        print(f"\n   Ontbrekende resources per type (alleen in werkende):")
        type_counts = {}
        for key in only_working:
            type_id = key[0]
            if type_id not in type_counts:
                type_counts[type_id] = {'count': 0, 'size': 0}
            type_counts[type_id]['count'] += 1
            type_counts[type_id]['size'] += len(working.resources[key].data)

        for type_id, stats in sorted(type_counts.items(), key=lambda x: -x[1]['size']):
            print(f"      Type 0x{type_id:08X}: {stats['count']} resources, {stats['size']/1024:.1f} KB")

    # Compare our merge with working
    print("\n" + "=" * 70)
    print("ONZE MERGE vs WERKENDE (ver13/Slot_12)")
    print("=" * 70)

    our_merge = loaded.get('onze_merge')
    if our_merge and working:
        merge_keys = set(our_merge.resources.keys())
        working_keys = set(working.resources.keys())

        only_merge = merge_keys - working_keys
        only_working = working_keys - merge_keys
        common = merge_keys & working_keys

        print(f"\n   Alleen in onze merge: {len(only_merge)}")
        print(f"   Alleen in werkende: {len(only_working)}")
        print(f"   In beide: {len(common)}")

        # Check if data matches for common resources
        matches = 0
        differs = 0
        for key in common:
            if our_merge.resources[key].data == working.resources[key].data:
                matches += 1
            else:
                differs += 1

        print(f"\n   Data identiek: {matches}")
        print(f"   Data verschilt: {differs}")

        # Show missing types
        if only_working:
            print(f"\n   Ontbrekende types in onze merge:")
            type_counts = {}
            for key in only_working:
                type_id = key[0]
                if type_id not in type_counts:
                    type_counts[type_id] = {'count': 0, 'size': 0}
                type_counts[type_id]['count'] += 1
                type_counts[type_id]['size'] += len(working.resources[key].data)

            for type_id, stats in sorted(type_counts.items(), key=lambda x: -x[1]['size']):
                print(f"      Type 0x{type_id:08X}: {stats['count']} resources, {stats['size']/1024:.1f} KB")

    # Compare header structures
    print("\n" + "=" * 70)
    print("HEADER VERGELIJKING")
    print("=" * 70)

    for name in ['corrupt', 'ver13 (Slot_12)', 'onze_merge']:
        if name in loaded:
            h = loaded[name].header
            print(f"\n   {name}:")
            print(f"      Version: {h.major_version}.{h.minor_version}")
            print(f"      Index type: {h.index_type}")
            print(f"      Index entries: {h.index_entry_count}")
            print(f"      Index offset: {h.index_offset}")
            print(f"      Index size: {h.index_size}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    compare_all()
