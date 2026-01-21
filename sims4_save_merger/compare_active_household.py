#!/usr/bin/env python3
"""
Compare the specific resources that might control the active household display
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def compare():
    print("=" * 80)
    print("VERGELIJK: ACTIVE HOUSEHOLD / THUMBNAIL DATA")
    print("=" * 80)

    corrupt = DBPFFile(Path("sims4_save_merger/AllSlots/Slot_00000002.save"))
    working = DBPFFile(Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4"))
    merged = DBPFFile(Path("sims4_save_merger/FINAL_ALLSLOTS_MERGED.save"))

    # Types that might be involved in save display
    interesting_types = {
        0xE88DB35F: "Image/Screenshot data",
        0xF8E1457A: "Thumbnail/Portrait data",
        0x0000000D: "Save game main data",
        0x0000000F: "Game state/World data",
        0x00000010: "Zone/Lot state"
    }

    for type_id, description in interesting_types.items():
        print(f"\n{'='*70}")
        print(f"TYPE 0x{type_id:08X}: {description}")
        print(f"{'='*70}")

        corrupt_res = {k: v for k, v in corrupt.resources.items() if k[0] == type_id}
        working_res = {k: v for k, v in working.resources.items() if k[0] == type_id}
        merged_res = {k: v for k, v in merged.resources.items() if k[0] == type_id}

        print(f"\n  Corrupt: {len(corrupt_res)} resources")
        print(f"  Working: {len(working_res)} resources")
        print(f"  Merged:  {len(merged_res)} resources")

        # Check which version is in merged
        for key in merged_res:
            merged_data = merged_res[key].data
            source = "UNKNOWN"

            if key in corrupt_res and merged_data == corrupt_res[key].data:
                source = "CORRUPT (nieuwste)"
            elif key in working_res and merged_data == working_res[key].data:
                source = "WORKING (oudere)"
            elif key in corrupt_res and key in working_res:
                source = "ANDERS (modified)"
            elif key in corrupt_res:
                source = "CORRUPT-only"
            elif key in working_res:
                source = "WORKING-only"

            size = len(merged_data)
            print(f"\n    Key: ...{key[2]:08X} - {size:>8} bytes - Bron: {source}")

    # Check Type 0x0000000D specifically - this is often the main save data
    print(f"\n{'='*70}")
    print("DETAIL: Type 0x0000000D (Main Save Data)")
    print(f"{'='*70}")

    for save_name, save in [("Corrupt", corrupt), ("Working", working), ("Merged", merged)]:
        type_d = {k: v for k, v in save.resources.items() if k[0] == 0x0000000D}
        if type_d:
            for key, res in type_d.items():
                data = res.data
                # Look for strings in the data
                print(f"\n  {save_name}: {len(data)} bytes")
                # Try to find "Orozco" or other household names
                try:
                    data_str = data.decode('utf-8', errors='ignore')
                    if 'Orozco' in data_str:
                        print(f"    Contains 'Orozco': YES")
                    else:
                        print(f"    Contains 'Orozco': NO")

                    # Find any readable strings
                    import re
                    strings = re.findall(r'[A-Za-z]{4,20}', data_str)
                    unique = list(set(strings))[:20]
                    print(f"    Sample strings: {unique[:10]}")
                except:
                    pass

    print("\n" + "=" * 80)
    print("CONCLUSIE")
    print("=" * 80)

    # The issue: our merge uses WORKING data for non-sim types
    # But the household name/thumbnail comes from the corrupt save
    # We need to also include the thumbnail/screenshot data from corrupt

    print("""
De merge gebruikt werkende data voor de meeste resources.
Maar de household preview (naam, thumbnail) komt van de NIEUWSTE save.

Oplossing: We moeten ook de thumbnail/image resources van de
nieuwste save nemen, niet alleen de sim-data types.
""")

if __name__ == '__main__':
    compare()
