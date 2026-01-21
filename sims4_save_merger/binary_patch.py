#!/usr/bin/env python3
"""
BINARY PATCHING approach:
Instead of parsing and rebuilding the entire save file,
we patch ONLY the empty building data while keeping the
exact binary structure intact.

This preserves the game's expectations for file format.
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path
import struct

def binary_patch():
    print("=" * 70)
    print("BINARY PATCHING: Behoud exacte bestandsstructuur")
    print("=" * 70)

    corrupt_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save")
    working_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4")

    # Read the corrupt file as raw bytes
    print(f"\nLezen van corrupt bestand: {corrupt_path}")
    with open(corrupt_path, 'rb') as f:
        corrupt_data = bytearray(f.read())

    print(f"Originele grootte: {len(corrupt_data):,} bytes")

    # Parse both files to understand the structure
    corrupt = DBPFFile(corrupt_path)
    working = DBPFFile(working_path)

    print(f"\nCorrupt save: {len(corrupt.resources)} resources")
    print(f"Working save: {len(working.resources)} resources")

    # Find Type 0x00000006 resources that are empty in corrupt
    print("\n" + "-" * 50)
    print("Zoeken naar lege gebouw resources...")

    patches_needed = []
    for key, resource in corrupt.resources.items():
        if key[0] == 0x00000006:  # Building data
            corrupt_size = len(resource.data)
            if key in working.resources:
                working_size = len(working.resources[key].data)
                if corrupt_size < 100 and working_size > 1000:
                    patches_needed.append({
                        'key': key,
                        'corrupt_entry': resource.entry,
                        'working_data': working.resources[key].data,
                        'corrupt_size': corrupt_size,
                        'working_size': working_size
                    })

    print(f"Gevonden: {len(patches_needed)} resources om te patchen")

    if not patches_needed:
        print("Geen patches nodig!")
        return

    # Calculate total new size
    extra_bytes = sum(p['working_size'] - p['corrupt_size'] for p in patches_needed)
    print(f"Extra bytes nodig: {extra_bytes:,}")

    # For binary patching, we can't easily expand resources in place
    # because the file format has fixed offsets.
    #
    # Instead, let's try a different approach:
    # Keep the corrupt save's INDEX structure but append new data at the end
    # and update the index entries to point to the new data.

    print("\n" + "-" * 50)
    print("Strategie: Append nieuwe data aan einde van bestand")

    # Read the original header info
    header_size = 96
    index_offset = corrupt.header.index_offset
    index_size = corrupt.header.index_size

    print(f"Header size: {header_size}")
    print(f"Index offset: {index_offset}")
    print(f"Index size: {index_size}")

    # The data section is from header_size to index_offset
    data_section_end = index_offset

    # We'll append new building data after the current data section
    # and update the index entries

    # First, let's understand the index structure
    index_start = index_offset
    index_end = index_offset + index_size

    # Copy the file
    new_data = bytearray(corrupt_data)

    # Append new building data at the end of the data section (before index)
    # We need to:
    # 1. Move the index to a new location
    # 2. Insert new data where the index was
    # 3. Update header to point to new index location

    # Actually, simpler approach:
    # Since we're replacing small data with larger data, we can't do in-place.
    # Let's rebuild the file but keep the EXACT same structure.

    print("\nHerbouwen met behoud van structuur...")

    # Rebuild approach:
    # 1. Keep exact same header
    # 2. Keep exact same data order
    # 3. Only replace the actual resource bytes
    # 4. Rebuild index with new offsets

    new_file = bytearray()

    # Copy header exactly
    new_file.extend(corrupt_data[:header_size])

    # Track where we are in the new file
    current_offset = header_size

    # Build new index entries
    new_index_entries = []

    # Go through each resource in original order
    # We need to parse the original index to get the order
    index_data = corrupt_data[index_offset:index_offset + index_size]

    # Parse index (get original order)
    original_entries = list(corrupt.resources.values())
    original_entries.sort(key=lambda r: r.entry.offset)

    patches_dict = {p['key']: p for p in patches_needed}

    for resource in original_entries:
        key = resource.key

        if key in patches_dict:
            # Use working data
            data_to_write = patches_dict[key]['working_data']
        else:
            # Use original data
            data_to_write = resource.data

        # Write data
        new_file.extend(data_to_write)

        # Record new entry
        new_index_entries.append({
            'type_id': key[0],
            'group_id': key[1],
            'instance_id': key[2],
            'offset': current_offset,
            'file_size': len(data_to_write),
            'mem_size': len(data_to_write),
            'compressed': False
        })

        current_offset += len(data_to_write)

    # Now build the index
    new_index_offset = current_offset

    # Build index with same format as original
    new_index = bytearray()

    # Index flags (0 = no constant fields)
    new_index.extend(struct.pack('<I', 0))

    for entry in new_index_entries:
        new_index.extend(struct.pack('<I', entry['type_id']))
        new_index.extend(struct.pack('<I', entry['group_id']))
        new_index.extend(struct.pack('<I', entry['instance_id'] >> 32))
        new_index.extend(struct.pack('<I', entry['instance_id'] & 0xFFFFFFFF))
        new_index.extend(struct.pack('<I', entry['offset']))
        new_index.extend(struct.pack('<I', entry['file_size']))  # No compression flag
        new_index.extend(struct.pack('<I', entry['mem_size']))

    new_file.extend(new_index)

    # Update header with new index location
    struct.pack_into('<I', new_file, 36, len(new_index_entries))  # Entry count
    struct.pack_into('<I', new_file, 44, len(new_index))  # Index size (alt location)
    struct.pack_into('<I', new_file, 64, new_index_offset)  # Index offset
    struct.pack_into('<I', new_file, 68, len(new_index))  # Index size

    # Write output
    output = Path("sims4_save_merger/BINARY_PATCHED.save")
    with open(output, 'wb') as f:
        f.write(new_file)

    print(f"\nResultaat:")
    print(f"  Output: {output}")
    print(f"  Originele grootte: {len(corrupt_data):,} bytes")
    print(f"  Nieuwe grootte: {len(new_file):,} bytes")
    print(f"  Verschil: {len(new_file) - len(corrupt_data):+,} bytes")

    # Verify the file
    print("\nVerificatie...")
    try:
        verify = DBPFFile(output)
        print(f"  Resources gelezen: {len(verify.resources)}")

        # Check building data
        building_data = sum(len(v.data) for k, v in verify.resources.items() if k[0] == 0x00000006)
        print(f"  Totale gebouwdata: {building_data:,} bytes ({building_data/1024/1024:.2f} MB)")

        # Check if Orozco is present
        for key, res in verify.resources.items():
            if key[0] == 0x0000000D:
                if b'Orozco' in res.data:
                    print(f"  Bevat 'Orozco': JA")
                break

    except Exception as e:
        print(f"  FOUT bij verificatie: {e}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    binary_patch()
