#!/usr/bin/env python3
"""
REVERSE APPROACH: Update WORKING save with newer sim data from CORRUPT save

Instead of trying to fix the corrupt save format (which doesn't work),
we take the working save (which the game accepts) and update ONLY the
sim-related data from the newer corrupt save.

This preserves:
- The exact file format the game expects
- All building/lot data from working save
- Updates sim ages/progress from newer save
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from pathlib import Path
import struct
import shutil

def update_working_save():
    print("=" * 70)
    print("REVERSE APPROACH: Update working save met nieuwe sim-data")
    print("=" * 70)

    working_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4")
    corrupt_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save")

    # Read both files completely
    print(f"\nLezen van werkende save: {working_path.name}")
    with open(working_path, 'rb') as f:
        working_bytes = bytearray(f.read())

    print(f"Lezen van corrupte save: {corrupt_path.name}")
    with open(corrupt_path, 'rb') as f:
        corrupt_bytes = bytearray(f.read())

    print(f"\nWerkende: {len(working_bytes):,} bytes")
    print(f"Corrupt:  {len(corrupt_bytes):,} bytes")

    # Parse index from working file to find resource locations
    # Header info
    index_offset_w = struct.unpack('<I', working_bytes[64:68])[0]
    index_size_w = struct.unpack('<I', working_bytes[44:48])[0]
    entry_count_w = struct.unpack('<I', working_bytes[36:40])[0]

    print(f"\nWerkende save index:")
    print(f"  Offset: {index_offset_w}")
    print(f"  Size: {index_size_w}")
    print(f"  Entries: {entry_count_w}")

    # Parse index from corrupt file
    index_offset_c = struct.unpack('<I', corrupt_bytes[64:68])[0]
    index_size_c = struct.unpack('<I', corrupt_bytes[44:48])[0]
    entry_count_c = struct.unpack('<I', corrupt_bytes[36:40])[0]

    print(f"\nCorrupte save index:")
    print(f"  Offset: {index_offset_c}")
    print(f"  Size: {index_size_c}")
    print(f"  Entries: {entry_count_c}")

    # Parse working file index entries
    def parse_index(data, index_offset, entry_count):
        entries = []
        pos = index_offset + 4  # Skip flags

        for i in range(entry_count):
            type_id = struct.unpack('<I', data[pos:pos+4])[0]
            group_id = struct.unpack('<I', data[pos+4:pos+8])[0]
            inst_high = struct.unpack('<I', data[pos+8:pos+12])[0]
            inst_low = struct.unpack('<I', data[pos+12:pos+16])[0]
            instance_id = (inst_high << 32) | inst_low
            offset = struct.unpack('<I', data[pos+16:pos+20])[0]
            file_size_raw = struct.unpack('<I', data[pos+20:pos+24])[0]
            compressed = bool(file_size_raw & 0x80000000)
            file_size = file_size_raw & 0x7FFFFFFF
            mem_size = struct.unpack('<I', data[pos+24:pos+28])[0]

            entry_size = 28
            if compressed:
                entry_size = 32  # Extra compressed_size field

            entries.append({
                'type_id': type_id,
                'group_id': group_id,
                'instance_id': instance_id,
                'offset': offset,
                'file_size': file_size,
                'mem_size': mem_size,
                'compressed': compressed,
                'index_pos': pos,
                'entry_size': entry_size
            })

            pos += entry_size

        return entries

    working_entries = parse_index(working_bytes, index_offset_w, entry_count_w)
    corrupt_entries = parse_index(corrupt_bytes, index_offset_c, entry_count_c)

    print(f"\nGeparsed: {len(working_entries)} werkende, {len(corrupt_entries)} corrupte entries")

    # Build lookup for corrupt entries
    corrupt_lookup = {}
    for entry in corrupt_entries:
        key = (entry['type_id'], entry['group_id'], entry['instance_id'])
        corrupt_lookup[key] = entry

    # Sim-related types to update
    sim_types = {0x0000000D, 0x0000000F, 0x00000014, 0x00000015}

    # Find resources we can update IN PLACE (same size or smaller in corrupt)
    updates = []
    for entry in working_entries:
        key = (entry['type_id'], entry['group_id'], entry['instance_id'])
        type_id = entry['type_id']

        if type_id in sim_types and key in corrupt_lookup:
            corrupt_entry = corrupt_lookup[key]

            working_size = entry['file_size']
            corrupt_size = corrupt_entry['file_size']

            # We can only do in-place update if corrupt data fits
            if corrupt_size <= working_size:
                updates.append({
                    'key': key,
                    'working_entry': entry,
                    'corrupt_entry': corrupt_entry,
                    'working_size': working_size,
                    'corrupt_size': corrupt_size
                })

    print(f"\nResources die we in-place kunnen updaten: {len(updates)}")

    if not updates:
        print("PROBLEEM: Geen resources kunnen in-place worden geupdate!")
        print("(De nieuwere data is groter dan de bestaande ruimte)")

        # Show size comparison
        for entry in working_entries:
            key = (entry['type_id'], entry['group_id'], entry['instance_id'])
            type_id = entry['type_id']

            if type_id in sim_types and key in corrupt_lookup:
                corrupt_entry = corrupt_lookup[key]
                print(f"  Type 0x{type_id:08X}: working={entry['file_size']}, corrupt={corrupt_entry['file_size']}")

        return None

    # Copy working file
    new_bytes = bytearray(working_bytes)

    # Apply updates
    updated_count = 0
    for update in updates:
        w_entry = update['working_entry']
        c_entry = update['corrupt_entry']

        # Get corrupt data
        c_offset = c_entry['offset']
        c_size = c_entry['file_size']
        corrupt_data = corrupt_bytes[c_offset:c_offset + c_size]

        # Write to working file location
        w_offset = w_entry['offset']
        w_size = w_entry['file_size']

        # Pad with zeros if corrupt data is smaller
        padded_data = corrupt_data + bytes(w_size - len(corrupt_data))

        new_bytes[w_offset:w_offset + w_size] = padded_data
        updated_count += 1

        print(f"  Updated Type 0x{w_entry['type_id']:08X}: {w_size} bytes @ offset {w_offset}")

    print(f"\nTotaal geupdate: {updated_count} resources")

    # Save output
    output = Path("sims4_save_merger/WORKING_UPDATED.save")
    with open(output, 'wb') as f:
        f.write(new_bytes)

    print(f"\nOutput: {output}")
    print(f"Size: {len(new_bytes):,} bytes (zelfde als werkende)")

    # Create slot folder
    slot_dir = Path("sims4_save_merger/WORKING_UPDATED_SLOT")
    slot_dir.mkdir(exist_ok=True)

    for i, filename in enumerate(["Slot_00000002.save",
                                   "Slot_00000002.save.ver0",
                                   "Slot_00000002.save.ver1",
                                   "Slot_00000002.save.ver2",
                                   "Slot_00000002.save.ver3"]):
        shutil.copy(output, slot_dir / filename)

    print(f"\nSlot folder: {slot_dir}")
    print("Kopieer naar saves folder en test!")

    return output

if __name__ == '__main__':
    update_working_save()
