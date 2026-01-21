#!/usr/bin/env python3
"""
Test PREFER_LARGER merge strategy
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.merger import Sims4SaveMerger, MergeStrategy
from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def test():
    print("=" * 70)
    print("TEST: PREFER_LARGER STRATEGIE")
    print("=" * 70)

    merger = Sims4SaveMerger()

    print("\n📂 Laden van saves...")
    newer_stats, older_stats = merger.load_files(
        Path("sims4_save_merger/Slot_00000002.save"),
        Path("sims4_save_merger/Slot_00000012.save")
    )

    # Get larger resources
    larger = merger._get_larger_resources()
    print(f"\n🔍 Resources waar oudere GROTER is: {len(larger)}")

    # Test both strategies
    print("\n" + "=" * 70)
    print("SMART MERGE vs PREFER_LARGER")
    print("=" * 70)

    # Smart merge
    output_smart = Path("sims4_save_merger/test_smart.save")
    result_smart = merger.merge(output_smart, strategy=MergeStrategy.SMART_MERGE)

    # Reload for prefer larger
    merger2 = Sims4SaveMerger()
    merger2.load_files(
        Path("sims4_save_merger/Slot_00000002.save"),
        Path("sims4_save_merger/Slot_00000012.save")
    )

    output_larger = Path("sims4_save_merger/test_prefer_larger.save")
    result_larger = merger2.merge(output_larger, strategy=MergeStrategy.PREFER_LARGER)

    print(f"\n📊 SMART MERGE:")
    print(f"   Resources van nieuwere: {result_smart.resources_from_newer}")
    print(f"   Resources van oudere:   {result_smart.resources_from_older}")
    print(f"   Bestandsgrootte: {output_smart.stat().st_size / 1024 / 1024:.2f} MB")

    print(f"\n📊 PREFER LARGER:")
    print(f"   Resources van nieuwere: {result_larger.resources_from_newer}")
    print(f"   Resources van oudere:   {result_larger.resources_from_older}")
    print(f"   Bestandsgrootte: {output_larger.stat().st_size / 1024 / 1024:.2f} MB")

    # Compare data sizes
    smart_file = DBPFFile(output_smart)
    larger_file = DBPFFile(output_larger)

    smart_data = sum(len(r.data) for r in smart_file.resources.values())
    larger_data = sum(len(r.data) for r in larger_file.resources.values())

    print(f"\n📊 DATA VERGELIJKING:")
    print(f"   Smart merge data:    {smart_data / 1024 / 1024:.2f} MB")
    print(f"   Prefer larger data:  {larger_data / 1024 / 1024:.2f} MB")
    print(f"   Verschil:            {(larger_data - smart_data) / 1024:.1f} KB")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    test()
