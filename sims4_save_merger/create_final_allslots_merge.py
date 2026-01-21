#!/usr/bin/env python3
"""
Create the FINAL merge using:
- BASE: Slot_00000002.save(13).ver4 - oldest fully working save (all buildings intact)
- SIM UPDATES: Slot_00000002.save - newest save (latest sim ages/progress)

This will create a save with:
- ALL buildings and lots from the working save
- Updated sim data from the newest save
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.merger import Sims4SaveMerger, MergeStrategy
from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def create_merge():
    print("=" * 80)
    print("FINALE MERGE: WERKENDE GEBOUWEN + NIEUWSTE SIM DATA")
    print("=" * 80)

    base_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4")
    newest_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save")

    print(f"\nBASIS (werkende save met alle gebouwen):")
    print(f"  {base_path.name}")
    print(f"  Grootte: {base_path.stat().st_size:,} bytes")

    print(f"\nSIM UPDATES VAN (nieuwste save):")
    print(f"  {newest_path.name}")
    print(f"  Grootte: {newest_path.stat().st_size:,} bytes")

    # Load and analyze
    print("\n" + "-" * 40)
    print("Laden van bestanden...")

    merger = Sims4SaveMerger()

    # Note: in WORKING_BASE mode, the "newer" file provides sim updates,
    # and the "older" file is the base with buildings
    # So we swap: newest_path is "newer" (sim source), base_path is "older" (building source)
    newer_stats, older_stats = merger.load_files(
        newest_path,  # "newer" = source for sim updates
        base_path     # "older" = base with all buildings
    )

    print(f"\nNieuwste save (sim bron):  {newer_stats['resource_count']} resources")
    print(f"Werkende save (basis):     {older_stats['resource_count']} resources")

    # Get comparison
    comparison = merger.get_comparison_summary()
    print(f"\nVergelijking:")
    print(f"  Identiek in beide:     {comparison['same']}")
    print(f"  Verschillend:          {comparison['different']}")
    print(f"  Alleen in nieuwste:    {comparison['only_in_newer']}")
    print(f"  Alleen in werkende:    {comparison['only_in_older']}")

    # Create output
    output = Path("sims4_save_merger/FINAL_ALLSLOTS_MERGED.save")

    print(f"\n" + "-" * 40)
    print(f"Aanmaken van merge: {output}")

    result = merger.merge(output, strategy=MergeStrategy.WORKING_BASE)

    print(f"\nResultaat:")
    print(f"  Succes: {result.success}")
    print(f"  Resources van werkende save: {result.resources_from_older}")
    print(f"  Sim resources van nieuwste:  {result.resources_from_newer}")
    print(f"  Totaal resources:            {result.resources_total}")

    if result.warnings:
        print(f"\nDetails:")
        for w in result.warnings:
            print(f"  - {w}")

    # Verify
    print("\n" + "=" * 80)
    print("VERIFICATIE")
    print("=" * 80)

    merged = DBPFFile(output)
    base = DBPFFile(base_path)
    newest = DBPFFile(newest_path)

    # Check building data
    base_buildings = {k: v for k, v in base.resources.items() if k[0] == 0x00000006}
    merged_buildings = {k: v for k, v in merged.resources.items() if k[0] == 0x00000006}

    buildings_match = sum(1 for k in base_buildings if k in merged_buildings and
                          merged_buildings[k].data == base_buildings[k].data)

    print(f"\nGebouw resources (Type 0x00000006):")
    print(f"  In werkende basis:  {len(base_buildings)}")
    print(f"  In merge:           {len(merged_buildings)}")
    print(f"  Identiek aan basis: {buildings_match}")

    if buildings_match == len(base_buildings):
        print(f"  ALLE GEBOUWEN CORRECT BEHOUDEN!")
    else:
        print(f"  WAARSCHUWING: {len(base_buildings) - buildings_match} gebouwen verschillen!")

    # Check sim data
    sim_types = {0xC0DB5AE7, 0x0C772E27, 0x3BD45407, 0x0000000D, 0x0000000F,
                 0xB61DE6B4, 0x00000014, 0x00000015}

    merged_sim = {k: v for k, v in merged.resources.items() if k[0] in sim_types}
    newest_sim = {k: v for k, v in newest.resources.items() if k[0] in sim_types}

    sim_from_newest = sum(1 for k in merged_sim if k in newest_sim and
                          merged_sim[k].data == newest_sim[k].data)

    print(f"\nSim-gerelateerde resources:")
    print(f"  In nieuwste save: {len(newest_sim)}")
    print(f"  In merge:         {len(merged_sim)}")
    print(f"  Van nieuwste:     {sim_from_newest}")

    # File sizes
    print(f"\nBestandsgroottes:")
    print(f"  Werkende basis:   {base_path.stat().st_size:>12,} bytes")
    print(f"  Merge resultaat:  {output.stat().st_size:>12,} bytes")
    print(f"  Nieuwste corrupt: {newest_path.stat().st_size:>12,} bytes")

    print("\n" + "=" * 80)
    print(f"OUTPUT BESTAND: {output}")
    print("=" * 80)
    print("\nGebruik dit bestand door:")
    print("1. Kopieer naar je Sims 4 saves folder")
    print("2. Hernoem naar Slot_00000002.save")
    print("3. Start Sims 4 en laad de save")

if __name__ == '__main__':
    create_merge()
