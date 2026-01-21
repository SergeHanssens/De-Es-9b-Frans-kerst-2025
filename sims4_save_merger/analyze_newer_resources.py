#!/usr/bin/env python3
"""
Analyze the 140 resources that come from the newer save
Maybe these should also come from older?
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def analyze():
    print("=" * 70)
    print("ANALYSE: RESOURCES DIE VAN NIEUWERE SAVE KOMEN")
    print("=" * 70)

    newer = DBPFFile(Path("sims4_save_merger/Slot_00000002.save"))
    older = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))
    merged = DBPFFile(Path("sims4_save_merger/Slot_00000002_smart_merged.save"))

    # Find resources in merged that match newer (not older)
    from_newer = []

    for key in merged.resources:
        merged_data = merged.resources[key].data
        has_newer = key in newer.resources
        has_older = key in older.resources

        if has_newer and newer.resources[key].data == merged_data:
            # This came from newer
            newer_size = len(newer.resources[key].data)
            older_size = len(older.resources[key].data) if has_older else 0

            from_newer.append({
                'key': key,
                'type_id': key[0],
                'newer_size': newer_size,
                'older_size': older_size,
                'in_older': has_older,
                'diff': older_size - newer_size if has_older else 0
            })

    print(f"\n📊 Resources die van NIEUWERE save komen: {len(from_newer)}")

    # Group by whether older has larger version
    older_larger = [x for x in from_newer if x['diff'] > 0]
    older_smaller = [x for x in from_newer if x['diff'] < 0]
    same_size = [x for x in from_newer if x['diff'] == 0]
    not_in_older = [x for x in from_newer if not x['in_older']]

    print(f"\n   Oudere heeft GROTERE versie: {len(older_larger)}")
    print(f"   Oudere heeft KLEINERE versie: {len(older_smaller)}")
    print(f"   Zelfde grootte: {len(same_size)}")
    print(f"   Niet in oudere save: {len(not_in_older)}")

    if older_larger:
        print(f"\n⚠️  Resources waar oudere GROTER is (maar we nieuwere gebruiken):")
        older_larger.sort(key=lambda x: -x['diff'])
        total_potential = sum(x['diff'] for x in older_larger)
        print(f"   Totaal potentieel te herstellen: {total_potential / 1024:.1f} KB")

        for i, item in enumerate(older_larger[:20]):
            print(f"      {i+1}. Type 0x{item['type_id']:08X}: nieuwer={item['newer_size']:>8} vs ouder={item['older_size']:>8} (+{item['diff']/1024:.1f} KB)")

    # Analyze the "not in older" resources - these are only in newer
    if not_in_older:
        print(f"\n📌 Resources ALLEEN in nieuwere save (niet in oudere):")
        type_counts = {}
        for item in not_in_older:
            type_id = item['type_id']
            if type_id not in type_counts:
                type_counts[type_id] = {'count': 0, 'size': 0}
            type_counts[type_id]['count'] += 1
            type_counts[type_id]['size'] += item['newer_size']

        for type_id, stats in sorted(type_counts.items(), key=lambda x: -x[1]['size']):
            print(f"      Type 0x{type_id:08X}: {stats['count']} resources, {stats['size']/1024:.1f} KB")

    # Look at Type 0x00000006 specifically
    type6_from_newer = [x for x in from_newer if x['type_id'] == 0x00000006]
    print(f"\n🏠 Type 0x00000006 resources van nieuwere save: {len(type6_from_newer)}")

    if type6_from_newer:
        for item in type6_from_newer:
            status = "GROTER in ouder!" if item['diff'] > 0 else "OK"
            print(f"      nieuwer={item['newer_size']:>8}, ouder={item['older_size']:>8} - {status}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    analyze()
