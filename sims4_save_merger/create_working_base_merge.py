#!/usr/bin/env python3
"""
Create a merge using WORKING_BASE strategy:
- Use the WORKING save (Slot_12) as the complete base
- Only update sim-related data from the newer (corrupt) save

This should preserve ALL buildings and lots while updating sim ages/progress.
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.merger import Sims4SaveMerger, MergeStrategy
from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def create_merge():
    print("=" * 70)
    print("WORKING_BASE MERGE: Werkende save + sim updates")
    print("=" * 70)

    print("\nStrategie:")
    print("  1. Gebruik ALLE data van werkende save (Slot_12) als basis")
    print("  2. Update ALLEEN sim-gerelateerde resources van nieuwere save")
    print("  3. Behoud ALLE gebouwen en lots van werkende save")

    merger = Sims4SaveMerger()

    # Load files - newer is the corrupt one, older is the working one
    print("\nLaden van bestanden...")
    newer_stats, older_stats = merger.load_files(
        Path("sims4_save_merger/Slot_00000002.save"),  # corrupt/newer (sim updates)
        Path("sims4_save_merger/Slot_00000012.save")   # working/older (base)
    )

    print(f"\nNieuwere save (corrupt): {newer_stats['resource_count']} resources")
    print(f"Oudere save (werkend):   {older_stats['resource_count']} resources")

    # Show what sim-related types will be updated
    print("\nSim-gerelateerde types die worden geupdate:")
    for type_id in merger.SIM_RELATED_TYPES:
        print(f"  0x{type_id:08X}")

    # Create merge
    output = Path("sims4_save_merger/WORKING_BASE_MERGED.save")
    print(f"\nAanmaken van merge: {output}")

    result = merger.merge(output, strategy=MergeStrategy.WORKING_BASE)

    print(f"\nResultaat:")
    print(f"  Succes: {result.success}")
    print(f"  Resources van werkende save: {result.resources_from_older}")
    print(f"  Resources van nieuwere save: {result.resources_from_newer}")
    print(f"  Totaal resources: {result.resources_total}")

    if result.warnings:
        print(f"\nWaarschuwingen:")
        for w in result.warnings:
            print(f"  - {w}")

    if result.errors:
        print(f"\nFouten:")
        for e in result.errors:
            print(f"  - {e}")

    # Verify the merge
    print("\n" + "=" * 70)
    print("VERIFICATIE")
    print("=" * 70)

    merged = DBPFFile(output)
    working = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))

    # Check file sizes
    merged_size = output.stat().st_size
    working_size = Path("sims4_save_merger/Slot_00000012.save").stat().st_size

    print(f"\nBestandsgrootte:")
    print(f"  Werkende save:  {working_size:,} bytes")
    print(f"  Nieuwe merge:   {merged_size:,} bytes")

    # Check if all working resources are present
    working_keys = set(working.resources.keys())
    merged_keys = set(merged.resources.keys())

    missing = working_keys - merged_keys
    print(f"\nResources uit werkende save die ontbreken in merge: {len(missing)}")

    # Check Type 0x00000006 (lot/building data)
    print(f"\nType 0x00000006 (gebouw/lot data) check:")
    type6_working = [k for k in working.resources.keys() if k[0] == 0x00000006]
    type6_merged = [k for k in merged.resources.keys() if k[0] == 0x00000006]

    print(f"  In werkende save: {len(type6_working)}")
    print(f"  In merge:         {len(type6_merged)}")

    # Check if Type 0x00000006 data matches working save
    matches = 0
    differs = 0
    for key in type6_working:
        if key in merged.resources:
            if merged.resources[key].data == working.resources[key].data:
                matches += 1
            else:
                differs += 1

    print(f"  Identiek aan werkende: {matches}")
    print(f"  Verschilt van werkende: {differs}")

    if differs > 0:
        print(f"\n  WAARSCHUWING: {differs} gebouw resources zijn anders dan werkende save!")

    print("\n" + "=" * 70)
    print(f"OUTPUT: {output}")
    print("=" * 70)

if __name__ == '__main__':
    create_merge()
