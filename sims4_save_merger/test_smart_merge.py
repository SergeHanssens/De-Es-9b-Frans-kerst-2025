#!/usr/bin/env python3
"""
Test smart merge with real save files
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.merger import Sims4SaveMerger, MergeStrategy
from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def test_smart_merge():
    print("=" * 70)
    print("TEST: SMART MERGE MET ECHTE SAVE BESTANDEN")
    print("=" * 70)

    merger = Sims4SaveMerger()

    print("\n📂 Laden van saves...")
    newer_stats, older_stats = merger.load_files(
        Path("sims4_save_merger/Slot_00000002.save"),
        Path("sims4_save_merger/Slot_00000012.save")
    )

    print(f"   Nieuwere: {newer_stats['resource_count']} resources, {newer_stats['total_size']/1024/1024:.2f} MB")
    print(f"   Oudere: {older_stats['resource_count']} resources, {older_stats['total_size']/1024/1024:.2f} MB")

    # Get smart merge candidates
    candidates = merger.get_smart_merge_candidates()
    print(f"\n🔍 Smart merge detectie:")
    print(f"   Gevonden: {len(candidates)} lege/corrupte resources in nieuwere save")

    if candidates:
        total_restored = sum(old.size - new.size for new, old in candidates)
        print(f"   Data die hersteld wordt: {total_restored/1024/1024:.2f} MB")

        print(f"\n   Top 5 grootste:")
        for i, (new, old) in enumerate(candidates[:5]):
            diff = old.size - new.size
            print(f"      {i+1}. Type 0x{new.key[0]:08X}: {new.size} → {old.size} bytes (+{diff/1024:.1f} KB)")

    # Perform smart merge
    print(f"\n🔀 Uitvoeren smart merge...")
    output_path = Path("sims4_save_merger/Slot_00000002_smart_merged.save")
    result = merger.merge(output_path, strategy=MergeStrategy.SMART_MERGE)

    print(f"\n📊 Resultaat:")
    print(f"   Succes: {result.success}")
    print(f"   Resources van nieuwere: {result.resources_from_newer}")
    print(f"   Resources van oudere: {result.resources_from_older}")
    print(f"   Totaal: {result.resources_total}")

    if result.warnings:
        print(f"\n   Waarschuwingen:")
        for w in result.warnings:
            print(f"      • {w}")

    # Load merged file and check size
    print(f"\n📁 Verificatie merged bestand:")
    merged = DBPFFile(output_path)
    merged_total_size = sum(len(r.data) for r in merged.resources.values())
    print(f"   Resources: {len(merged.resources)}")
    print(f"   Data grootte: {merged_total_size/1024/1024:.2f} MB")

    # Compare with expected
    print(f"\n📊 Vergelijking:")

    # Calculate expected size
    older_only_keys = set(merger.older_file.resources.keys()) - set(merger.newer_file.resources.keys())
    expected_from_older = sum(len(merger.older_file.resources[k].data) for k in older_only_keys)

    # Plus smart merge restored data
    smart_restored = sum(old.size - new.size for new, old in candidates)

    expected_total = newer_stats['total_size'] + expected_from_older + smart_restored
    print(f"   Verwachte totale data: {expected_total/1024/1024:.2f} MB")
    print(f"   Werkelijke data: {merged_total_size/1024/1024:.2f} MB")

    # File size check
    file_size = output_path.stat().st_size
    print(f"\n   Bestandsgrootte: {file_size/1024/1024:.2f} MB")

    print("\n" + "=" * 70)
    print("TEST VOLTOOID")
    print("=" * 70)

if __name__ == '__main__':
    test_smart_merge()
