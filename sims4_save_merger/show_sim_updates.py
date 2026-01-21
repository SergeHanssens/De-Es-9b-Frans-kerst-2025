#!/usr/bin/env python3
"""
Show which sim resources were updated from the newest save
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path

def show_updates():
    print("=" * 70)
    print("SIM UPDATES IN FINAL_ALLSLOTS_MERGED.save")
    print("=" * 70)

    merged = DBPFFile(Path("sims4_save_merger/FINAL_ALLSLOTS_MERGED.save"))
    newest = DBPFFile(Path("sims4_save_merger/AllSlots/Slot_00000002.save"))
    base = DBPFFile(Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4"))

    sim_types = {
        0xC0DB5AE7: "SimInfo",
        0x0C772E27: "RelationshipData",
        0x3BD45407: "Situation",
        0x0000000D: "SimGameData",
        0x0000000F: "GameState",
        0xB61DE6B4: "Household",
        0x00000014: "Achievement",
        0x00000015: "Skills"
    }

    print(f"\nResources die zijn GEUPDATE van nieuwste save:")
    print("-" * 70)

    updates_by_type = {}
    for key, resource in merged.resources.items():
        type_id = key[0]
        if type_id in sim_types:
            # Check if this came from newest (not from base)
            if key in newest.resources:
                if resource.data == newest.resources[key].data:
                    type_name = sim_types[type_id]
                    if type_name not in updates_by_type:
                        updates_by_type[type_name] = []
                    updates_by_type[type_name].append({
                        'key': key,
                        'size': len(resource.data)
                    })

    for type_name, updates in sorted(updates_by_type.items()):
        print(f"\n{type_name}: {len(updates)} resources")
        total_size = sum(u['size'] for u in updates)
        print(f"  Totale grootte: {total_size:,} bytes ({total_size/1024:.1f} KB)")

    print("\n" + "=" * 70)
    print("SAMENVATTING")
    print("=" * 70)

    total_updates = sum(len(u) for u in updates_by_type.values())
    print(f"\nTotaal {total_updates} sim-gerelateerde resources geupdate")
    print(f"Dit bevat je nieuwste sim voortgang (leeftijd, skills, relaties, etc.)")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    show_updates()
