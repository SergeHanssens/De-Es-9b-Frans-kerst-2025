#!/usr/bin/env python3
"""
Verify that WORKING_BASE_MERGED.save is correct
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def verify():
    print("=" * 70)
    print("VERIFICATIE: WORKING_BASE_MERGED.save")
    print("=" * 70)

    working = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))
    new_merge = DBPFFile(Path("sims4_save_merger/WORKING_BASE_MERGED.save"))
    old_merge = DBPFFile(Path("sims4_save_merger/FINAL_MERGED.save"))
    corrupt = DBPFFile(Path("sims4_save_merger/Slot_00000002.save"))

    print("\n1. BESTANDSGROOTTE VERGELIJKING")
    print("-" * 40)
    print(f"   Werkende save:         {Path('sims4_save_merger/Slot_00000012.save').stat().st_size:>12,} bytes")
    print(f"   WORKING_BASE merge:    {Path('sims4_save_merger/WORKING_BASE_MERGED.save').stat().st_size:>12,} bytes")
    print(f"   Oude FINAL merge:      {Path('sims4_save_merger/FINAL_MERGED.save').stat().st_size:>12,} bytes")
    print(f"   Corrupte save:         {Path('sims4_save_merger/Slot_00000002.save').stat().st_size:>12,} bytes")

    print("\n2. RESOURCE AANTALLEN")
    print("-" * 40)
    print(f"   Werkende:    {len(working.resources)}")
    print(f"   New merge:   {len(new_merge.resources)}")
    print(f"   Old merge:   {len(old_merge.resources)}")

    print("\n3. GEBOUW DATA (Type 0x00000006) - KRITISCH")
    print("-" * 40)

    working_buildings = {k: v for k, v in working.resources.items() if k[0] == 0x00000006}
    new_merge_buildings = {k: v for k, v in new_merge.resources.items() if k[0] == 0x00000006}
    old_merge_buildings = {k: v for k, v in old_merge.resources.items() if k[0] == 0x00000006}

    # Check new merge
    new_matches = sum(1 for k in working_buildings if k in new_merge_buildings and
                      new_merge_buildings[k].data == working_buildings[k].data)
    new_differs = len(working_buildings) - new_matches

    # Check old merge
    old_matches = sum(1 for k in working_buildings if k in old_merge_buildings and
                      old_merge_buildings[k].data == working_buildings[k].data)
    old_differs = len(working_buildings) - old_matches

    print(f"   Werkende save heeft: {len(working_buildings)} gebouw resources")
    print(f"\n   WORKING_BASE merge:")
    print(f"      Identiek aan werkende: {new_matches}")
    print(f"      Verschilt:             {new_differs}")

    print(f"\n   Oude FINAL merge:")
    print(f"      Identiek aan werkende: {old_matches}")
    print(f"      Verschilt:             {old_differs}")

    if new_differs == 0:
        print(f"\n   WORKING_BASE merge heeft ALLE gebouwen correct!")
    else:
        print(f"\n   WAARSCHUWING: {new_differs} gebouwen verschillen nog!")

    # Check sim data from corrupt
    print("\n4. SIM DATA UPDATES")
    print("-" * 40)

    sim_types = {0xC0DB5AE7, 0x0C772E27, 0x3BD45407, 0x0000000D, 0x0000000F,
                 0xB61DE6B4, 0x00000014, 0x00000015}

    new_merge_sim = {k: v for k, v in new_merge.resources.items() if k[0] in sim_types}
    corrupt_sim = {k: v for k, v in corrupt.resources.items() if k[0] in sim_types}

    from_corrupt = sum(1 for k in new_merge_sim if k in corrupt_sim and
                       new_merge_sim[k].data == corrupt_sim[k].data)

    print(f"   Sim-gerelateerde resources in merge: {len(new_merge_sim)}")
    print(f"   Daarvan met nieuwere sim-data:       {from_corrupt}")

    print("\n5. CONCLUSIE")
    print("-" * 40)

    if new_differs == 0 and from_corrupt > 0:
        print("   De WORKING_BASE merge zou correct moeten zijn!")
        print("   - Alle gebouwen van werkende save behouden")
        print(f"   - {from_corrupt} sim resources geupdate van nieuwere save")
        print("\n   Probeer: sims4_save_merger/WORKING_BASE_MERGED.save")
    elif new_differs > 0:
        print(f"   PROBLEEM: {new_differs} gebouwen zijn nog anders")
    else:
        print("   Onverwacht resultaat - controleer handmatig")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    verify()
