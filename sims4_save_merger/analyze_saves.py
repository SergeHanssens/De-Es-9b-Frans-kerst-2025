#!/usr/bin/env python3
"""
Analyze save files to understand the merge issue
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def analyze_saves():
    print("=" * 70)
    print("GEDETAILLEERDE SAVE ANALYSE")
    print("=" * 70)

    # Load all three files
    newer = DBPFFile(Path("sims4_save_merger/Slot_00000002.save"))
    older = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))
    merged = DBPFFile(Path("sims4_save_merger/Slot_00000002_merged.save"))

    print(f"\n📁 NIEUWERE SAVE:")
    print(f"   Resources: {len(newer.resources)}")
    total_newer = sum(len(r.data) for r in newer.resources.values())
    print(f"   Totale data grootte: {total_newer:,} bytes ({total_newer/1024/1024:.2f} MB)")

    print(f"\n📁 OUDERE SAVE:")
    print(f"   Resources: {len(older.resources)}")
    total_older = sum(len(r.data) for r in older.resources.values())
    print(f"   Totale data grootte: {total_older:,} bytes ({total_older/1024/1024:.2f} MB)")

    print(f"\n📁 MERGED SAVE:")
    print(f"   Resources: {len(merged.resources)}")
    total_merged = sum(len(r.data) for r in merged.resources.values())
    print(f"   Totale data grootte: {total_merged:,} bytes ({total_merged/1024/1024:.2f} MB)")

    # Check what should have been added
    newer_keys = set(newer.resources.keys())
    older_keys = set(older.resources.keys())
    merged_keys = set(merged.resources.keys())

    only_older = older_keys - newer_keys
    print(f"\n📊 VERGELIJKING:")
    print(f"   Resources alleen in oudere save: {len(only_older)}")

    # Calculate expected size from older-only resources
    older_only_size = sum(len(older.resources[k].data) for k in only_older)
    print(f"   Grootte van resources alleen in oudere: {older_only_size:,} bytes ({older_only_size/1024/1024:.2f} MB)")

    expected_total = total_newer + older_only_size
    print(f"\n   Verwachte totale grootte: {expected_total:,} bytes ({expected_total/1024/1024:.2f} MB)")
    print(f"   Werkelijke grootte merged: {total_merged:,} bytes ({total_merged/1024/1024:.2f} MB)")
    print(f"   Verschil: {expected_total - total_merged:,} bytes ({(expected_total - total_merged)/1024/1024:.2f} MB)")

    # Check if all older-only resources are in merged
    print(f"\n🔍 RESOURCES CHECK:")
    missing_from_merged = only_older - merged_keys
    print(f"   Resources die ontbreken in merged: {len(missing_from_merged)}")

    # Check data integrity
    print(f"\n🔍 DATA INTEGRITEIT CHECK:")

    # Sample some resources from newer that should be in merged
    newer_in_merged = 0
    newer_data_matches = 0
    for key in list(newer_keys)[:50]:  # Check first 50
        if key in merged_keys:
            newer_in_merged += 1
            if newer.resources[key].data == merged.resources[key].data:
                newer_data_matches += 1

    print(f"   Nieuwere resources in merged: {newer_in_merged}/50")
    print(f"   Data matches: {newer_data_matches}/50")

    # Sample some resources from older-only that should be in merged
    older_in_merged = 0
    older_data_matches = 0
    for key in list(only_older)[:50]:  # Check first 50
        if key in merged_keys:
            older_in_merged += 1
            if older.resources[key].data == merged.resources[key].data:
                older_data_matches += 1

    print(f"   Oudere-only resources in merged: {older_in_merged}/{min(50, len(only_older))}")
    print(f"   Data matches: {older_data_matches}/{min(50, len(only_older))}")

    # Show size distribution
    print(f"\n📊 RESOURCE GROOTTE VERDELING:")

    newer_sizes = sorted([len(r.data) for r in newer.resources.values()], reverse=True)
    older_sizes = sorted([len(r.data) for r in older.resources.values()], reverse=True)
    merged_sizes = sorted([len(r.data) for r in merged.resources.values()], reverse=True)

    print(f"\n   NIEUWERE - Top 10 grootste resources:")
    for i, size in enumerate(newer_sizes[:10]):
        print(f"      {i+1}. {size:,} bytes ({size/1024:.1f} KB)")

    print(f"\n   OUDERE - Top 10 grootste resources:")
    for i, size in enumerate(older_sizes[:10]):
        print(f"      {i+1}. {size:,} bytes ({size/1024:.1f} KB)")

    print(f"\n   MERGED - Top 10 grootste resources:")
    for i, size in enumerate(merged_sizes[:10]):
        print(f"      {i+1}. {size:,} bytes ({size/1024:.1f} KB)")

    # Check compression status
    print(f"\n📊 COMPRESSIE STATUS:")
    newer_compressed = sum(1 for r in newer.resources.values() if r.entry.compressed)
    older_compressed = sum(1 for r in older.resources.values() if r.entry.compressed)
    merged_compressed = sum(1 for r in merged.resources.values() if r.entry.compressed)

    print(f"   Nieuwere: {newer_compressed}/{len(newer.resources)} gecomprimeerd")
    print(f"   Oudere: {older_compressed}/{len(older.resources)} gecomprimeerd")
    print(f"   Merged: {merged_compressed}/{len(merged.resources)} gecomprimeerd")

if __name__ == '__main__':
    analyze_saves()
