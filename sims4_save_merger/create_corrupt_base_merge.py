#!/usr/bin/env python3
"""
NEW STRATEGY: Use CORRUPT save as base, only fix empty building data

The problem with our previous approach:
- Working save (old) has different household structure
- Corrupt save (new) has current household/game state
- Mixing them causes the game to not recognize the active household

New approach:
1. Start with CORRUPT save (preserves current game state, active household, thumbnails)
2. ONLY replace Type 0x00000006 resources that are empty/tiny (< 1KB)
   with the larger versions from working save
3. This preserves the game's understanding of current state while restoring building data
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile, Resource, IndexEntry
from pathlib import Path
import struct

def create_merge():
    print("=" * 80)
    print("NIEUWE STRATEGIE: CORRUPT BASE + GEBOUW FIXES")
    print("=" * 80)

    corrupt_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save")
    working_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4")

    print(f"\nBASIS: {corrupt_path.name} (behoudt game state, active household)")
    print(f"FIXES VAN: {working_path.name} (alleen lege gebouw resources)")

    # Load both files
    print("\nLaden van bestanden...")
    corrupt = DBPFFile(corrupt_path)
    working = DBPFFile(working_path)

    print(f"\nCorrupt save: {len(corrupt.resources)} resources")
    print(f"Working save: {len(working.resources)} resources")

    # Create new DBPF starting from corrupt
    merged = DBPFFile()
    merged.header = corrupt.header

    # Copy ALL resources from corrupt first
    for key, resource in corrupt.resources.items():
        merged.resources[key] = resource

    # Now find and fix empty Type 0x00000006 resources
    print("\n" + "-" * 60)
    print("Zoeken naar lege gebouw resources...")

    fixed_count = 0
    fixed_bytes = 0

    type_6_corrupt = {k: v for k, v in corrupt.resources.items() if k[0] == 0x00000006}
    type_6_working = {k: v for k, v in working.resources.items() if k[0] == 0x00000006}

    print(f"\nType 0x00000006 in corrupt: {len(type_6_corrupt)}")
    print(f"Type 0x00000006 in working: {len(type_6_working)}")

    for key in type_6_corrupt:
        corrupt_data = type_6_corrupt[key].data
        corrupt_size = len(corrupt_data)

        if key in type_6_working:
            working_data = type_6_working[key].data
            working_size = len(working_data)

            # If corrupt version is tiny but working version is much larger
            # then the corrupt version is likely empty/damaged
            if corrupt_size < 100 and working_size > 1000:
                # Replace with working version
                merged.resources[key] = type_6_working[key]
                fixed_count += 1
                fixed_bytes += (working_size - corrupt_size)
                print(f"  FIX: Key ...{key[2]:08X}: {corrupt_size} → {working_size} bytes (+{working_size - corrupt_size})")

            elif corrupt_size < 1000 and working_size > corrupt_size * 10:
                # Also fix if corrupt is small and working is 10x larger
                merged.resources[key] = type_6_working[key]
                fixed_count += 1
                fixed_bytes += (working_size - corrupt_size)
                print(f"  FIX: Key ...{key[2]:08X}: {corrupt_size} → {working_size} bytes (+{working_size - corrupt_size})")

    print(f"\n{'-'*60}")
    print(f"Gefixte resources: {fixed_count}")
    print(f"Herstelde data: {fixed_bytes:,} bytes ({fixed_bytes/1024/1024:.2f} MB)")

    # Save
    output = Path("sims4_save_merger/CORRUPT_BASE_FIXED.save")
    print(f"\nOpslaan naar: {output}")
    merged.save(output)

    # Verify
    print("\n" + "=" * 80)
    print("VERIFICATIE")
    print("=" * 80)

    result = DBPFFile(output)

    print(f"\nResultaat:")
    print(f"  Resources: {len(result.resources)}")
    print(f"  Bestandsgrootte: {output.stat().st_size:,} bytes")

    # Check thumbnails are from corrupt
    thumb_type = 0xF8E1457A
    thumb_corrupt = {k: v for k, v in corrupt.resources.items() if k[0] == thumb_type}
    thumb_result = {k: v for k, v in result.resources.items() if k[0] == thumb_type}

    matches = sum(1 for k in thumb_result if k in thumb_corrupt and
                  thumb_result[k].data == thumb_corrupt[k].data)
    print(f"\n  Thumbnail resources: {len(thumb_result)}")
    print(f"  Van corrupt (correct): {matches}")

    # Check main save data
    main_type = 0x0000000D
    main_corrupt = {k: v for k, v in corrupt.resources.items() if k[0] == main_type}
    main_result = {k: v for k, v in result.resources.items() if k[0] == main_type}

    for key in main_result:
        if key in main_corrupt and main_result[key].data == main_corrupt[key].data:
            print(f"\n  Main save data (0x0000000D): Van corrupt (correct)")
            # Check for Orozco
            if b'Orozco' in main_result[key].data:
                print(f"  Bevat 'Orozco': JA")
        else:
            print(f"\n  Main save data (0x0000000D): ANDERS (probleem!)")

    # Check building data
    type_6_result = {k: v for k, v in result.resources.items() if k[0] == 0x00000006}
    total_building_data = sum(len(v.data) for v in type_6_result.values())
    print(f"\n  Gebouw resources: {len(type_6_result)}")
    print(f"  Totale gebouwdata: {total_building_data:,} bytes ({total_building_data/1024/1024:.2f} MB)")

    print("\n" + "=" * 80)
    print(f"OUTPUT: {output}")
    print("=" * 80)
    print("\nDit bestand zou moeten:")
    print("- De household preview tonen (The Orozco Household)")
    print("- Resume Game optie hebben")
    print("- Gebouwen correct weergeven")

if __name__ == '__main__':
    create_merge()
