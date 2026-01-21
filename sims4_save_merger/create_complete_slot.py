#!/usr/bin/env python3
"""
Create a complete Sims 4 save slot with all required files:
- Slot_XXXXXXXX.save (main)
- Slot_XXXXXXXX.save.ver0 through .ver4 (backups)

The game might need these files to properly display thumbnails and allow Resume Game.
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from pathlib import Path
import shutil

def create_complete_slot():
    print("=" * 70)
    print("CREATE COMPLETE SAVE SLOT")
    print("=" * 70)

    # Our fixed save
    fixed_save = Path("sims4_save_merger/CORRUPT_BASE_FIXED.save")

    # Output folder
    output_dir = Path("sims4_save_merger/COMPLETE_SLOT")
    output_dir.mkdir(exist_ok=True)

    print(f"\nBron: {fixed_save}")
    print(f"Output folder: {output_dir}")

    # Create all the files needed
    files_to_create = [
        "Slot_00000002.save",
        "Slot_00000002.save.ver0",
        "Slot_00000002.save.ver1",
        "Slot_00000002.save.ver2",
        "Slot_00000002.save.ver3",
        "Slot_00000002.save.ver4",
    ]

    print(f"\nAanmaken van bestanden:")
    for filename in files_to_create:
        output_path = output_dir / filename
        shutil.copy(fixed_save, output_path)
        print(f"  {filename}: {output_path.stat().st_size:,} bytes")

    print(f"\n" + "=" * 70)
    print("INSTRUCTIES")
    print("=" * 70)
    print(f"""
1. Kopieer ALLE bestanden uit de folder:
   {output_dir}

2. Naar je Sims 4 saves folder:
   Documents/Electronic Arts/The Sims 4/saves/

3. VERVANG de bestaande Slot_00000002 bestanden
   (maak eerst een backup!)

4. Start Sims 4 opnieuw
""")

    # Also try: use the WORKING save (13) as the complete base
    # and only fix the building data
    print("=" * 70)
    print("ALTERNATIEF: Gebruik werkende save structuur")
    print("=" * 70)

    # Copy the working save files structure
    allslots = Path("sims4_save_merger/AllSlots")

    alt_dir = Path("sims4_save_merger/COMPLETE_SLOT_ALT")
    alt_dir.mkdir(exist_ok=True)

    # Use (13) as base for structure
    working_files = [
        ("Slot_00000002.save(13).ver4", "Slot_00000002.save"),
        ("Slot_00000002.save(14).ver4", "Slot_00000002.save.ver0"),
        ("Slot_00000002.save(15).ver4", "Slot_00000002.save.ver1"),
        ("Slot_00000002.save(16).ver4", "Slot_00000002.save.ver2"),
        ("Slot_00000002.save(17).ver4", "Slot_00000002.save.ver3"),
        ("Slot_00000002.save(18).ver4", "Slot_00000002.save.ver4"),
    ]

    print(f"\nKopieren van werkende save structuur naar: {alt_dir}")
    for src_name, dst_name in working_files:
        src = allslots / src_name
        dst = alt_dir / dst_name
        if src.exists():
            shutil.copy(src, dst)
            print(f"  {src_name} -> {dst_name}: {dst.stat().st_size:,} bytes")
        else:
            print(f"  {src_name} NIET GEVONDEN")

    print(f"""
Dit is de WERKENDE save structuur die je al testte.
Als dit werkt, weten we dat de file structuur correct is.

De volgende stap zou zijn: de gebouwdata in de main save fixen
terwijl we de exacte bestandsstructuur behouden.
""")

if __name__ == '__main__':
    create_complete_slot()
