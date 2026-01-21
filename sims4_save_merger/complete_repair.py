#!/usr/bin/env python3
"""
COMPLETE REPAIR:
1. Start with corrupt save (keeps game state, active household)
2. Fix empty building resources
3. ADD missing resources from working save

This should create a complete save file.
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path
import struct

def complete_repair():
    print("=" * 70)
    print("COMPLETE REPAIR: Fix + Add Missing Resources")
    print("=" * 70)

    corrupt_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save")
    working_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4")

    corrupt = DBPFFile(corrupt_path)
    working = DBPFFile(working_path)

    print(f"\nCorrupt save: {len(corrupt.resources)} resources")
    print(f"Working save: {len(working.resources)} resources")

    # Find missing resources
    corrupt_keys = set(corrupt.resources.keys())
    working_keys = set(working.resources.keys())

    missing_keys = working_keys - corrupt_keys
    print(f"Ontbrekende resources: {len(missing_keys)}")

    # Group missing by type
    missing_by_type = {}
    for key in missing_keys:
        type_id = key[0]
        if type_id not in missing_by_type:
            missing_by_type[type_id] = []
        missing_by_type[type_id].append(key)

    print("\nOntbrekende resources per type:")
    for type_id, keys in sorted(missing_by_type.items()):
        total_size = sum(len(working.resources[k].data) for k in keys)
        print(f"  Type 0x{type_id:08X}: {len(keys)} resources ({total_size:,} bytes)")

    # Create new file starting from corrupt
    new_file = bytearray()
    header_size = 96

    # Read original corrupt file
    with open(corrupt_path, 'rb') as f:
        corrupt_data = f.read()

    # Copy header
    new_file.extend(corrupt_data[:header_size])

    current_offset = header_size
    new_entries = []

    # 1. First, process all resources from corrupt (with fixes)
    print("\n" + "-" * 50)
    print("Stap 1: Verwerken van corrupt resources (met fixes)...")

    corrupt_entries = list(corrupt.resources.values())
    corrupt_entries.sort(key=lambda r: r.entry.offset)

    fixed_count = 0
    for resource in corrupt_entries:
        key = resource.key
        data = resource.data

        # Check if this needs fixing (Type 0x00000006 that's too small)
        if key[0] == 0x00000006 and len(data) < 100:
            if key in working.resources:
                working_data = working.resources[key].data
                if len(working_data) > 1000:
                    data = working_data
                    fixed_count += 1

        new_file.extend(data)
        new_entries.append({
            'type_id': key[0],
            'group_id': key[1],
            'instance_id': key[2],
            'offset': current_offset,
            'file_size': len(data),
            'mem_size': len(data),
            'compressed': False
        })
        current_offset += len(data)

    print(f"  Verwerkt: {len(corrupt_entries)} resources")
    print(f"  Gefixed: {fixed_count} gebouw resources")

    # 2. Add missing resources from working
    print("\n" + "-" * 50)
    print("Stap 2: Toevoegen van ontbrekende resources...")

    added_count = 0
    added_bytes = 0
    for key in missing_keys:
        resource = working.resources[key]
        data = resource.data

        new_file.extend(data)
        new_entries.append({
            'type_id': key[0],
            'group_id': key[1],
            'instance_id': key[2],
            'offset': current_offset,
            'file_size': len(data),
            'mem_size': len(data),
            'compressed': False
        })
        current_offset += len(data)
        added_count += 1
        added_bytes += len(data)

    print(f"  Toegevoegd: {added_count} resources")
    print(f"  Extra data: {added_bytes:,} bytes ({added_bytes/1024/1024:.2f} MB)")

    # 3. Build index
    print("\n" + "-" * 50)
    print("Stap 3: Index opbouwen...")

    new_index_offset = current_offset
    new_index = bytearray()

    # Index flags
    new_index.extend(struct.pack('<I', 0))

    for entry in new_entries:
        new_index.extend(struct.pack('<I', entry['type_id']))
        new_index.extend(struct.pack('<I', entry['group_id']))
        new_index.extend(struct.pack('<I', entry['instance_id'] >> 32))
        new_index.extend(struct.pack('<I', entry['instance_id'] & 0xFFFFFFFF))
        new_index.extend(struct.pack('<I', entry['offset']))
        new_index.extend(struct.pack('<I', entry['file_size']))
        new_index.extend(struct.pack('<I', entry['mem_size']))

    new_file.extend(new_index)

    # Update header
    struct.pack_into('<I', new_file, 36, len(new_entries))
    struct.pack_into('<I', new_file, 44, len(new_index))
    struct.pack_into('<I', new_file, 64, new_index_offset)
    struct.pack_into('<I', new_file, 68, len(new_index))

    # Write output
    output = Path("sims4_save_merger/COMPLETE_REPAIR.save")
    with open(output, 'wb') as f:
        f.write(new_file)

    print(f"\n" + "=" * 70)
    print("RESULTAAT")
    print("=" * 70)

    print(f"\nOutput: {output}")
    print(f"Originele corrupt: {len(corrupt_data):,} bytes ({len(corrupt.resources)} resources)")
    print(f"Nieuwe grootte: {len(new_file):,} bytes ({len(new_entries)} resources)")

    # Verify
    print("\nVerificatie...")
    try:
        verify = DBPFFile(output)
        print(f"  Resources gelezen: {len(verify.resources)}")

        building_data = sum(len(v.data) for k, v in verify.resources.items() if k[0] == 0x00000006)
        print(f"  Gebouwdata: {building_data:,} bytes ({building_data/1024/1024:.2f} MB)")

        for key, res in verify.resources.items():
            if key[0] == 0x0000000D:
                if b'Orozco' in res.data:
                    print(f"  Bevat 'Orozco': JA")
                break

        # Compare with working
        working_buildings = sum(len(v.data) for k, v in working.resources.items() if k[0] == 0x00000006)
        print(f"\n  Vergelijking met werkende save:")
        print(f"    Werkende gebouwdata: {working_buildings:,} bytes")
        print(f"    Onze gebouwdata:     {building_data:,} bytes")
        print(f"    Verschil: {building_data - working_buildings:+,} bytes")

    except Exception as e:
        print(f"  FOUT bij verificatie: {e}")
        import traceback
        traceback.print_exc()

    # Create complete slot folder
    print("\n" + "=" * 70)
    print("COMPLETE SLOT FOLDER")
    print("=" * 70)

    import shutil
    slot_dir = Path("sims4_save_merger/COMPLETE_SLOT_REPAIR")
    slot_dir.mkdir(exist_ok=True)

    # Copy to all slot files
    for filename in ["Slot_00000002.save",
                     "Slot_00000002.save.ver0",
                     "Slot_00000002.save.ver1",
                     "Slot_00000002.save.ver2",
                     "Slot_00000002.save.ver3",
                     "Slot_00000002.save.ver4"]:
        shutil.copy(output, slot_dir / filename)
        print(f"  Created: {filename}")

    print(f"\nKopieer de inhoud van {slot_dir} naar je saves folder!")

if __name__ == '__main__':
    complete_repair()
