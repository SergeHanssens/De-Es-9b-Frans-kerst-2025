#!/usr/bin/env python3
"""
Final analysis: vergelijk onze merge met de werkende save op alle vlakken
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path
import struct

def hexdump(data, length=64):
    result = []
    for i in range(0, min(len(data), length), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        result.append(f'{i:08X}  {hex_part:<48}')
    return '\n'.join(result)

def analyze():
    print("=" * 80)
    print("FINALE ANALYSE: WAAROM WERKT ONZE MERGE NIET?")
    print("=" * 80)

    # Load files
    working = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))
    our_merge = DBPFFile(Path("sims4_save_merger/FINAL_MERGED.save"))
    corrupt = DBPFFile(Path("sims4_save_merger/Slot_00000002.save"))

    print(f"\n1. BESTANDSGROOTTES")
    print("-" * 40)
    print(f"   Werkende save (Slot_12):  {Path('sims4_save_merger/Slot_00000012.save').stat().st_size:,} bytes")
    print(f"   Onze merge (FINAL):       {Path('sims4_save_merger/FINAL_MERGED.save').stat().st_size:,} bytes")
    print(f"   Corrupte save (Slot_02):  {Path('sims4_save_merger/Slot_00000002.save').stat().st_size:,} bytes")

    print(f"\n2. RESOURCE AANTALLEN")
    print("-" * 40)
    print(f"   Werkende:  {len(working.resources)} resources")
    print(f"   Merge:     {len(our_merge.resources)} resources")
    print(f"   Corrupt:   {len(corrupt.resources)} resources")

    # Check if all working resources are in merge
    working_keys = set(working.resources.keys())
    merge_keys = set(our_merge.resources.keys())
    corrupt_keys = set(corrupt.resources.keys())

    missing_from_merge = working_keys - merge_keys
    extra_in_merge = merge_keys - working_keys

    print(f"\n3. MISSING RESOURCES IN MERGE")
    print("-" * 40)
    print(f"   Ontbreken in merge (wel in werkende): {len(missing_from_merge)}")
    print(f"   Extra in merge (niet in werkende):   {len(extra_in_merge)}")

    if missing_from_merge:
        print(f"\n   ONTBREKENDE RESOURCES:")
        for key in sorted(missing_from_merge):
            size = len(working.resources[key].data)
            print(f"      Type 0x{key[0]:08X}, Group 0x{key[1]:08X}, Inst 0x{key[2]:016X} - {size} bytes")

    # Check data content differences
    print(f"\n4. DATA VERSCHILLEN")
    print("-" * 40)
    common_keys = working_keys & merge_keys
    identical = 0
    different = 0
    diff_list = []

    for key in common_keys:
        work_data = working.resources[key].data
        merge_data = our_merge.resources[key].data

        if work_data == merge_data:
            identical += 1
        else:
            different += 1
            diff_list.append({
                'key': key,
                'work_size': len(work_data),
                'merge_size': len(merge_data),
                'from_corrupt': key in corrupt_keys and corrupt.resources[key].data == merge_data
            })

    print(f"   Identieke resources: {identical}")
    print(f"   Verschillende resources: {different}")

    if diff_list:
        print(f"\n   DETAILS VAN VERSCHILLEN:")
        for d in sorted(diff_list, key=lambda x: -abs(x['work_size'] - x['merge_size'])):
            source = "van CORRUPT" if d['from_corrupt'] else "ANDERS"
            diff = d['merge_size'] - d['work_size']
            print(f"      Type 0x{d['key'][0]:08X}: werk={d['work_size']:>8}, merge={d['merge_size']:>8} ({diff:+}) {source}")

    # Check header differences
    print(f"\n5. HEADER VERGELIJKING")
    print("-" * 40)

    print(f"   WERKENDE SAVE:")
    print(f"      Version: {working.header.major_version}.{working.header.minor_version}")
    print(f"      Index type: {working.header.index_type}")
    print(f"      Index entries: {working.header.index_entry_count}")
    print(f"      Index offset: {working.header.index_offset}")
    print(f"      Index size: {working.header.index_size}")

    print(f"\n   ONZE MERGE:")
    print(f"      Version: {our_merge.header.major_version}.{our_merge.header.minor_version}")
    print(f"      Index type: {our_merge.header.index_type}")
    print(f"      Index entries: {our_merge.header.index_entry_count}")
    print(f"      Index offset: {our_merge.header.index_offset}")
    print(f"      Index size: {our_merge.header.index_size}")

    # Read raw headers
    print(f"\n6. RAW HEADER BYTES")
    print("-" * 40)

    with open("sims4_save_merger/Slot_00000012.save", 'rb') as f:
        work_header = f.read(96)
    with open("sims4_save_merger/FINAL_MERGED.save", 'rb') as f:
        merge_header = f.read(96)

    print(f"\n   WERKENDE HEADER (eerste 48 bytes):")
    print(hexdump(work_header, 48))

    print(f"\n   MERGE HEADER (eerste 48 bytes):")
    print(hexdump(merge_header, 48))

    # Check byte differences
    print(f"\n   HEADER VERSCHILLEN:")
    for i in range(96):
        if work_header[i] != merge_header[i]:
            print(f"      Byte {i}: werkend=0x{work_header[i]:02X}, merge=0x{merge_header[i]:02X}")

    # Compare total data sizes
    print(f"\n7. TOTALE DATA GROOTTE")
    print("-" * 40)
    work_data_size = sum(len(r.data) for r in working.resources.values())
    merge_data_size = sum(len(r.data) for r in our_merge.resources.values())

    print(f"   Werkende data: {work_data_size:,} bytes ({work_data_size/1024/1024:.2f} MB)")
    print(f"   Merge data:    {merge_data_size:,} bytes ({merge_data_size/1024/1024:.2f} MB)")
    print(f"   Verschil:      {merge_data_size - work_data_size:+,} bytes")

    # Analyze which resources from corrupt are SMALLER than from working
    # These might be the "empty" resources that lost data
    print(f"\n8. RESOURCES WAAR CORRUPT KLEINER IS DAN WERKEND")
    print("-" * 40)
    corrupt_smaller = []
    for key in corrupt_keys & working_keys:
        c_size = len(corrupt.resources[key].data)
        w_size = len(working.resources[key].data)
        if c_size < w_size:
            corrupt_smaller.append({
                'key': key,
                'corrupt_size': c_size,
                'working_size': w_size,
                'diff': w_size - c_size
            })

    corrupt_smaller.sort(key=lambda x: -x['diff'])
    total_missing = sum(x['diff'] for x in corrupt_smaller)
    print(f"   Aantal resources: {len(corrupt_smaller)}")
    print(f"   Totaal ontbrekende data: {total_missing:,} bytes ({total_missing/1024/1024:.2f} MB)")

    print(f"\n   TOP 20 GROOTSTE VERSCHILLEN:")
    for d in corrupt_smaller[:20]:
        print(f"      Type 0x{d['key'][0]:08X}: corrupt={d['corrupt_size']:>8}, werk={d['working_size']:>8} (-{d['diff']:,})")

    # Check if our merge uses the working data for these
    print(f"\n9. CHECK: GEBRUIKT ONZE MERGE DE WERKENDE DATA?")
    print("-" * 40)
    uses_working = 0
    uses_corrupt = 0
    uses_neither = 0

    for d in corrupt_smaller:
        key = d['key']
        if key not in our_merge.resources:
            print(f"   ONTBREEKT: Type 0x{key[0]:08X}")
            continue

        merge_data = our_merge.resources[key].data
        work_data = working.resources[key].data
        corrupt_data = corrupt.resources[key].data

        if merge_data == work_data:
            uses_working += 1
        elif merge_data == corrupt_data:
            uses_corrupt += 1
        else:
            uses_neither += 1

    print(f"   Gebruikt WERKENDE data: {uses_working}")
    print(f"   Gebruikt CORRUPTE data: {uses_corrupt}")
    print(f"   Gebruikt ANDERE data:   {uses_neither}")

    if uses_corrupt > 0:
        print(f"\n   WAARSCHUWING: {uses_corrupt} resources gebruiken nog steeds corrupte data!")
        print(f"   Dit kan de reden zijn waarom sims/gebouwen ontbreken!")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    analyze()
