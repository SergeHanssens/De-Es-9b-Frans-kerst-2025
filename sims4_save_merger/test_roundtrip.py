#!/usr/bin/env python3
"""
ROUNDTRIP TEST: Read a working save and write it back unchanged.
If this doesn't work, our read/write code has a bug.
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path
import shutil

def test_roundtrip():
    print("=" * 70)
    print("ROUNDTRIP TEST: Lees werkende save, schrijf ongewijzigd terug")
    print("=" * 70)

    working_path = Path("sims4_save_merger/TEST_WORKING_SLOT/Slot_00000002.save")

    print(f"\nOrigineel: {working_path}")
    print(f"Size: {working_path.stat().st_size:,} bytes")

    # Read with our parser
    print("\nLezen met onze parser...")
    dbpf = DBPFFile(working_path)
    print(f"Resources gelezen: {len(dbpf.resources)}")

    # Write back
    output = Path("sims4_save_merger/ROUNDTRIP_TEST.save")
    print(f"\nTerugschrijven naar: {output}")
    dbpf.save(output)
    print(f"Nieuwe size: {output.stat().st_size:,} bytes")

    # Compare files
    print("\n" + "-" * 50)
    print("VERGELIJKING:")

    with open(working_path, 'rb') as f:
        orig_bytes = f.read()
    with open(output, 'rb') as f:
        new_bytes = f.read()

    print(f"Origineel: {len(orig_bytes):,} bytes")
    print(f"Nieuw:     {len(new_bytes):,} bytes")
    print(f"Verschil:  {len(new_bytes) - len(orig_bytes):+,} bytes")

    if orig_bytes == new_bytes:
        print("\n✓ IDENTIEK - Roundtrip succesvol!")
    else:
        print("\n✗ VERSCHILLEND - Er is een bug!")

        # Find first difference
        for i in range(min(len(orig_bytes), len(new_bytes))):
            if orig_bytes[i] != new_bytes[i]:
                print(f"\nEerste verschil op byte {i}:")
                print(f"  Origineel: 0x{orig_bytes[i]:02X}")
                print(f"  Nieuw:     0x{new_bytes[i]:02X}")

                # Show context
                start = max(0, i - 8)
                end = min(len(orig_bytes), i + 8)
                print(f"\nContext (bytes {start}-{end}):")
                print(f"  Orig: {orig_bytes[start:end].hex()}")
                print(f"  New:  {new_bytes[start:end].hex()}")
                break

        # Compare headers specifically
        print("\n" + "-" * 50)
        print("HEADER VERGELIJKING (bytes 0-96):")
        for i in range(96):
            if i < len(orig_bytes) and i < len(new_bytes):
                if orig_bytes[i] != new_bytes[i]:
                    print(f"  Byte {i:2d}: orig=0x{orig_bytes[i]:02X}, new=0x{new_bytes[i]:02X}")

    # Create test slot
    print("\n" + "-" * 50)
    slot_dir = Path("sims4_save_merger/ROUNDTRIP_SLOT")
    slot_dir.mkdir(exist_ok=True)

    for filename in ["Slot_00000002.save",
                     "Slot_00000002.save.ver0",
                     "Slot_00000002.save.ver1",
                     "Slot_00000002.save.ver2",
                     "Slot_00000002.save.ver3"]:
        shutil.copy(output, slot_dir / filename)
        print(f"Created: {filename}")

    print(f"\nTest deze folder: {slot_dir}")
    print("Als deze NIET werkt, is er een bug in onze save functie!")

if __name__ == '__main__':
    test_roundtrip()
