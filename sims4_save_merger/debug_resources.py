#!/usr/bin/env python3
"""
Debug specific resources to understand the compression issue
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path
import struct

def debug():
    print("=" * 70)
    print("DEBUG: Resource details")
    print("=" * 70)

    working_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4")

    with open(working_path, 'rb') as f:
        orig_bytes = f.read()

    # Parse header
    index_offset = struct.unpack('<I', orig_bytes[64:68])[0]
    entry_count = struct.unpack('<I', orig_bytes[36:40])[0]

    # Parse first 20 index entries manually
    print(f"\nEerste 20 index entries:")
    print(f"{'Type':<12} {'Offset':>10} {'FileSize':>10} {'MemSize':>10} {'Comp':>6} {'ActualData':>12}")
    print("-" * 70)

    pos = index_offset + 4  # Skip flags

    total_file_size = 0
    total_mem_size = 0
    total_actual = 0

    for i in range(min(20, entry_count)):
        type_id = struct.unpack('<I', orig_bytes[pos:pos+4])[0]
        group_id = struct.unpack('<I', orig_bytes[pos+4:pos+8])[0]
        inst_high = struct.unpack('<I', orig_bytes[pos+8:pos+12])[0]
        inst_low = struct.unpack('<I', orig_bytes[pos+12:pos+16])[0]
        offset = struct.unpack('<I', orig_bytes[pos+16:pos+20])[0]
        file_size_raw = struct.unpack('<I', orig_bytes[pos+20:pos+24])[0]
        mem_size = struct.unpack('<I', orig_bytes[pos+24:pos+28])[0]

        compressed = bool(file_size_raw & 0x80000000)
        file_size = file_size_raw & 0x7FFFFFFF

        # Read actual data from file
        actual_data = orig_bytes[offset:offset+file_size]
        actual_len = len(actual_data)

        # Check first few bytes
        first_bytes = actual_data[:4].hex() if len(actual_data) >= 4 else actual_data.hex()

        print(f"0x{type_id:08X} {offset:>10} {file_size:>10} {mem_size:>10} {str(compressed):>6} {actual_len:>12}  {first_bytes}")

        total_file_size += file_size
        total_mem_size += mem_size
        total_actual += actual_len

        entry_size = 28
        if compressed:
            # Read compressed_size field
            comp_size = struct.unpack('<I', orig_bytes[pos+28:pos+32])[0]
            entry_size = 32

        pos += entry_size

    print(f"\nTotalen voor eerste 20:")
    print(f"  file_size sum: {total_file_size:,}")
    print(f"  mem_size sum:  {total_mem_size:,}")
    print(f"  actual sum:    {total_actual:,}")

    # Now check ALL entries
    print("\n" + "-" * 70)
    print("Alle entries analyseren...")

    pos = index_offset + 4
    total_file_size = 0
    total_mem_size = 0
    equal_count = 0
    larger_mem = 0
    larger_file = 0

    for i in range(entry_count):
        file_size_raw = struct.unpack('<I', orig_bytes[pos+20:pos+24])[0]
        mem_size = struct.unpack('<I', orig_bytes[pos+24:pos+28])[0]

        compressed = bool(file_size_raw & 0x80000000)
        file_size = file_size_raw & 0x7FFFFFFF

        total_file_size += file_size
        total_mem_size += mem_size

        if file_size == mem_size:
            equal_count += 1
        elif mem_size > file_size:
            larger_mem += 1
        else:
            larger_file += 1

        entry_size = 32 if compressed else 28
        pos += entry_size

    print(f"\nTotalen voor alle {entry_count} entries:")
    print(f"  Som file_size: {total_file_size:,}")
    print(f"  Som mem_size:  {total_mem_size:,}")
    print(f"\nVerdeling:")
    print(f"  file_size == mem_size: {equal_count}")
    print(f"  mem_size > file_size: {larger_mem}")
    print(f"  file_size > mem_size: {larger_file}")

    # Load with our parser and compare
    print("\n" + "-" * 70)
    print("Vergelijk met onze parser:")

    dbpf = DBPFFile(working_path)

    our_total = sum(len(r.data) for r in dbpf.resources.values())
    print(f"  Onze totale data: {our_total:,}")
    print(f"  Verwacht (mem_size): {total_mem_size:,}")
    print(f"  Verschil: {our_total - total_mem_size:+,}")

    # Check a few specific resources
    print("\n" + "-" * 70)
    print("Specifieke resources vergelijken:")

    pos = index_offset + 4
    for i in range(5):
        type_id = struct.unpack('<I', orig_bytes[pos:pos+4])[0]
        group_id = struct.unpack('<I', orig_bytes[pos+4:pos+8])[0]
        inst_high = struct.unpack('<I', orig_bytes[pos+8:pos+12])[0]
        inst_low = struct.unpack('<I', orig_bytes[pos+12:pos+16])[0]
        instance_id = (inst_high << 32) | inst_low
        offset = struct.unpack('<I', orig_bytes[pos+16:pos+20])[0]
        file_size_raw = struct.unpack('<I', orig_bytes[pos+20:pos+24])[0]
        mem_size = struct.unpack('<I', orig_bytes[pos+24:pos+28])[0]

        compressed = bool(file_size_raw & 0x80000000)
        file_size = file_size_raw & 0x7FFFFFFF

        key = (type_id, group_id, instance_id)
        if key in dbpf.resources:
            our_data = dbpf.resources[key].data
            print(f"\nResource {i+1}: Type 0x{type_id:08X}")
            print(f"  Index file_size: {file_size}")
            print(f"  Index mem_size: {mem_size}")
            print(f"  Our data len: {len(our_data)}")

        entry_size = 32 if compressed else 28
        pos += entry_size

if __name__ == '__main__':
    debug()
