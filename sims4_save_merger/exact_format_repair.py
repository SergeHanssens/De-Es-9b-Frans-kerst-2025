#!/usr/bin/env python3
"""
Create a repair file with EXACT same format as original Sims 4 saves:
- Index size only at bytes 44-48 (bytes 68-72 = 0)
- Compression flag 0x80000000 on file_size
- Resources in original order
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path
import struct
import shutil

def exact_repair():
    print("=" * 70)
    print("EXACT FORMAT REPAIR")
    print("=" * 70)

    corrupt_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save")
    working_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4")

    # Read original corrupt file completely
    with open(corrupt_path, 'rb') as f:
        corrupt_bytes = f.read()

    # Parse to understand structure
    corrupt = DBPFFile(corrupt_path)
    working = DBPFFile(working_path)

    print(f"Corrupt: {len(corrupt.resources)} resources, {len(corrupt_bytes):,} bytes")
    print(f"Working: {len(working.resources)} resources")

    # Get original resource order from corrupt file
    # Sort by offset to get original order
    corrupt_entries = list(corrupt.resources.values())
    corrupt_entries.sort(key=lambda r: r.entry.offset)

    print(f"\nOriginele resource volgorde behouden...")

    # Build patches for empty Type 0x00000006 resources
    patches = {}
    for resource in corrupt_entries:
        key = resource.key
        if key[0] == 0x00000006 and len(resource.data) < 100:
            if key in working.resources and len(working.resources[key].data) > 1000:
                patches[key] = working.resources[key].data

    print(f"Te patchen: {len(patches)} resources")

    # Now build new file
    new_file = bytearray()

    # Copy header from corrupt (first 96 bytes)
    new_file.extend(corrupt_bytes[:96])

    # Track new offsets
    current_offset = 96
    new_index_data = []

    # Write resources in SAME ORDER as corrupt
    for resource in corrupt_entries:
        key = resource.key
        entry = resource.entry

        # Get data (patched or original)
        if key in patches:
            data = patches[key]
        else:
            data = resource.data

        # Write data
        new_file.extend(data)

        # Build index entry with SAME format as original
        # Original format uses compression flag 0x80000000
        new_index_data.append({
            'type_id': entry.type_id,
            'group_id': entry.group_id,
            'instance_id': entry.instance_id,
            'offset': current_offset,
            'file_size': len(data) | 0x80000000,  # Set compression flag like original
            'mem_size': len(data)
        })

        current_offset += len(data)

    # Build index in SAME format as original
    new_index_offset = current_offset

    index_bytes = bytearray()

    # Index flags (0 = no constant fields, same as original)
    index_bytes.extend(struct.pack('<I', 0))

    for entry in new_index_data:
        index_bytes.extend(struct.pack('<I', entry['type_id']))
        index_bytes.extend(struct.pack('<I', entry['group_id']))
        index_bytes.extend(struct.pack('<I', entry['instance_id'] >> 32))
        index_bytes.extend(struct.pack('<I', entry['instance_id'] & 0xFFFFFFFF))
        index_bytes.extend(struct.pack('<I', entry['offset']))
        index_bytes.extend(struct.pack('<I', entry['file_size']))  # With compression flag
        index_bytes.extend(struct.pack('<I', entry['mem_size']))
        # Add compressed size field (same as mem_size since not actually compressed)
        index_bytes.extend(struct.pack('<I', entry['mem_size']))

    new_file.extend(index_bytes)

    # Update header with EXACT same format as original
    # Entry count at 36-40
    struct.pack_into('<I', new_file, 36, len(new_index_data))

    # Index size at 44-48 (primary location for Sims 4)
    struct.pack_into('<I', new_file, 44, len(index_bytes))

    # Index offset at 64-68
    struct.pack_into('<I', new_file, 64, new_index_offset)

    # Index size at 68-72 should be 0 (like original!)
    struct.pack_into('<I', new_file, 68, 0)

    # Write output
    output = Path("sims4_save_merger/EXACT_FORMAT.save")
    with open(output, 'wb') as f:
        f.write(new_file)

    print(f"\nOutput: {output}")
    print(f"Size: {len(new_file):,} bytes")

    # Verify header matches original format
    print("\n" + "-" * 50)
    print("Header vergelijking:")

    print(f"\nByte 68-72 (moet 0 zijn):")
    print(f"  Origineel: {struct.unpack('<I', corrupt_bytes[68:72])[0]}")
    print(f"  Ons:       {struct.unpack('<I', new_file[68:72])[0]}")

    print(f"\nByte 44-48 (index size):")
    print(f"  Origineel: {struct.unpack('<I', corrupt_bytes[44:48])[0]}")
    print(f"  Ons:       {struct.unpack('<I', new_file[44:48])[0]}")

    # Verify
    print("\n" + "-" * 50)
    print("Verificatie...")
    try:
        verify = DBPFFile(output)
        print(f"  Resources: {len(verify.resources)}")

        building_data = sum(len(v.data) for k, v in verify.resources.items() if k[0] == 0x00000006)
        print(f"  Gebouwdata: {building_data:,} bytes ({building_data/1024/1024:.2f} MB)")

    except Exception as e:
        print(f"  FOUT: {e}")
        import traceback
        traceback.print_exc()

    # Create slot folder
    print("\n" + "-" * 50)
    slot_dir = Path("sims4_save_merger/EXACT_FORMAT_SLOT")
    slot_dir.mkdir(exist_ok=True)

    for filename in ["Slot_00000002.save",
                     "Slot_00000002.save.ver0",
                     "Slot_00000002.save.ver1",
                     "Slot_00000002.save.ver2",
                     "Slot_00000002.save.ver3",
                     "Slot_00000002.save.ver4"]:
        shutil.copy(output, slot_dir / filename)
        print(f"Created: {filename}")

    print(f"\nKopieer {slot_dir} naar saves folder!")

if __name__ == '__main__':
    exact_repair()
