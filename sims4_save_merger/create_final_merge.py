#!/usr/bin/env python3
"""
Create final merge with corrected header
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.merger import Sims4SaveMerger, MergeStrategy
from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def create_merge():
    print("=" * 70)
    print("FINALE MERGE MET GECORRIGEERDE HEADER")
    print("=" * 70)

    merger = Sims4SaveMerger()

    print("\n📂 Laden van saves...")
    merger.load_files(
        Path("sims4_save_merger/Slot_00000002.save"),  # corrupt/nieuwer
        Path("sims4_save_merger/Slot_00000012.save")   # werkend/ouder
    )

    # Create merge with PREFER_LARGER strategy
    output = Path("sims4_save_merger/FINAL_MERGED.save")
    result = merger.merge(output, strategy=MergeStrategy.PREFER_LARGER)

    print(f"\n📊 Merge resultaat:")
    print(f"   Succes: {result.success}")
    print(f"   Resources van nieuwere: {result.resources_from_newer}")
    print(f"   Resources van oudere: {result.resources_from_older}")
    print(f"   Totaal: {result.resources_total}")

    # Verify header
    print(f"\n🔍 Verificatie...")
    merged = DBPFFile(output)
    working = DBPFFile(Path("sims4_save_merger/Slot_00000012.save"))

    print(f"\n   Header vergelijking:")
    print(f"   Werkende - Index type: {working.header.index_type}")
    print(f"   Merged   - Index type: {merged.header.index_type}")

    print(f"\n   Bestandsgrootte: {output.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   Data grootte: {sum(len(r.data) for r in merged.resources.values()) / 1024 / 1024:.2f} MB")

    # Check resource coverage
    working_keys = set(working.resources.keys())
    merged_keys = set(merged.resources.keys())

    missing = working_keys - merged_keys
    print(f"\n   Resources uit werkende save die ontbreken: {len(missing)}")

    if len(missing) == 0:
        print("\n✅ Alle resources uit werkende save zijn aanwezig!")

    print(f"\n📁 Output: {output}")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    create_merge()
