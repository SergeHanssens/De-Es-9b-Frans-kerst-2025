#!/usr/bin/env python3
"""
Analyze all save files in AllSlots to find the best merge candidates
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path
import os

def get_file_info(filepath):
    """Get basic info about a save file"""
    try:
        dbpf = DBPFFile(filepath)
        size = filepath.stat().st_size

        # Count Type 0x00000006 resources (buildings/lots)
        building_resources = [k for k in dbpf.resources.keys() if k[0] == 0x00000006]
        building_data_size = sum(len(dbpf.resources[k].data) for k in building_resources)

        # Count other important types
        sim_types = {0xC0DB5AE7, 0x0C772E27, 0x3BD45407, 0x0000000D, 0x0000000F,
                     0xB61DE6B4, 0x00000014, 0x00000015}
        sim_resources = [k for k in dbpf.resources.keys() if k[0] in sim_types]

        return {
            'path': filepath,
            'size': size,
            'resources': len(dbpf.resources),
            'buildings': len(building_resources),
            'building_data': building_data_size,
            'sim_resources': len(sim_resources),
            'valid': True,
            'dbpf': dbpf
        }
    except Exception as e:
        return {
            'path': filepath,
            'size': filepath.stat().st_size if filepath.exists() else 0,
            'resources': 0,
            'buildings': 0,
            'building_data': 0,
            'sim_resources': 0,
            'valid': False,
            'error': str(e),
            'dbpf': None
        }

def analyze_all():
    print("=" * 80)
    print("ANALYSE VAN ALLE SAVE FILES IN AllSlots")
    print("=" * 80)

    allslots = Path("sims4_save_merger/AllSlots")
    files = sorted(allslots.glob("*.save*"))

    results = []
    for f in files:
        print(f"Analyseren: {f.name}...", end=" ")
        info = get_file_info(f)
        if info['valid']:
            print(f"OK - {info['resources']} resources, {info['buildings']} gebouwen")
        else:
            print(f"FOUT - {info.get('error', 'unknown')}")
        results.append(info)

    # Sort by size descending
    results.sort(key=lambda x: x['size'], reverse=True)

    print("\n" + "=" * 80)
    print("OVERZICHT (gesorteerd op grootte)")
    print("=" * 80)
    print(f"{'Bestand':<40} {'Grootte':>12} {'Resources':>10} {'Gebouwen':>10} {'Geb.Data':>12}")
    print("-" * 80)

    working_saves = []
    corrupted_saves = []

    for r in results:
        name = r['path'].name
        if len(name) > 38:
            name = name[:35] + "..."

        size_mb = r['size'] / 1024 / 1024
        building_mb = r['building_data'] / 1024 / 1024

        status = ""
        if r['valid']:
            if r['building_data'] > 5_000_000:  # More than 5MB of building data = likely working
                status = " [WERKEND]"
                working_saves.append(r)
            else:
                status = " [CORRUPT]"
                corrupted_saves.append(r)
            print(f"{name:<40} {size_mb:>10.2f}MB {r['resources']:>10} {r['buildings']:>10} {building_mb:>10.2f}MB{status}")
        else:
            print(f"{name:<40} {size_mb:>10.2f}MB {'ERROR':>10} {'-':>10} {'-':>12}")

    print("\n" + "=" * 80)
    print("SAMENVATTING")
    print("=" * 80)

    print(f"\nWerkende saves (met volledige gebouwdata): {len(working_saves)}")
    if working_saves:
        oldest_working = working_saves[-1]  # Smallest of the working ones
        newest_working = working_saves[0]   # Largest of the working ones
        print(f"  Nieuwste werkende: {newest_working['path'].name}")
        print(f"  Oudste werkende:   {oldest_working['path'].name}")

    print(f"\nCorrupte saves (gebouwdata ontbreekt): {len(corrupted_saves)}")
    if corrupted_saves:
        newest_corrupt = max(corrupted_saves, key=lambda x: x['sim_resources'])
        print(f"  Meeste sim resources: {newest_corrupt['path'].name} ({newest_corrupt['sim_resources']} sim resources)")

    # Determine best merge candidates
    print("\n" + "=" * 80)
    print("AANBEVOLEN MERGE")
    print("=" * 80)

    if working_saves and corrupted_saves:
        # Use the newest working save as base (most complete buildings)
        base = working_saves[0]
        # Use the newest corrupt save for sim updates
        newest = corrupted_saves[0] if corrupted_saves else None

        print(f"\nBASIS (werkende gebouwen): {base['path'].name}")
        print(f"  - {base['buildings']} gebouw resources")
        print(f"  - {base['building_data']/1024/1024:.2f} MB gebouwdata")

        if newest:
            print(f"\nSIM UPDATES VAN: {newest['path'].name}")
            print(f"  - {newest['sim_resources']} sim-gerelateerde resources")

        return base, newest

    return None, None

if __name__ == '__main__':
    base, newest = analyze_all()

    if base and newest:
        print("\n" + "=" * 80)
        print("NU MERGE AANMAKEN...")
        print("=" * 80)
