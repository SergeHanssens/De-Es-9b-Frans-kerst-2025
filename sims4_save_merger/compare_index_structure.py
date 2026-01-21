#!/usr/bin/env python3
"""
Compare binary structure of working save vs our merge
"""

import sys
import struct
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from pathlib import Path

def hexdump(data, length=128):
    result = []
    for i in range(0, min(len(data), length), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f'{i:08X}  {hex_part:<48}  {ascii_part}')
    return '\n'.join(result)

def analyze_index(filepath, name):
    print(f"\n{'='*70}")
    print(f"INDEX ANALYSE: {name}")
    print(f"{'='*70}")

    with open(filepath, 'rb') as f:
        data = f.read()

    # Read header
    index_offset = struct.unpack('<I', data[64:68])[0]
    index_size = struct.unpack('<I', data[44:48])[0]
    if index_size == 0:
        index_size = struct.unpack('<I', data[68:72])[0]

    entry_count = struct.unpack('<I', data[36:40])[0]

    print(f"\nHeader info:")
    print(f"  Index offset: {index_offset}")
    print(f"  Index size: {index_size}")
    print(f"  Entry count: {entry_count}")

    # Read index data
    index_data = data[index_offset:index_offset + min(index_size, 512)]

    print(f"\nEerste 256 bytes van index:")
    print(hexdump(index_data, 256))

    # Parse index flags
    if len(index_data) >= 4:
        flags = struct.unpack('<I', index_data[0:4])[0]
        print(f"\nIndex flags: 0x{flags:08X}")
        print(f"  Const type: {bool(flags & 1)}")
        print(f"  Const group: {bool(flags & 2)}")
        print(f"  Const instance_hi: {bool(flags & 4)}")

    # Try to parse first entry
    print(f"\nProbeer eerste entry te parsen...")
    offset = 4
    try:
        # Assume no constant fields
        type_id = struct.unpack('<I', index_data[offset:offset+4])[0]
        group_id = struct.unpack('<I', index_data[offset+4:offset+8])[0]
        inst_hi = struct.unpack('<I', index_data[offset+8:offset+12])[0]
        inst_lo = struct.unpack('<I', index_data[offset+12:offset+16])[0]
        res_offset = struct.unpack('<I', index_data[offset+16:offset+20])[0]
        file_size = struct.unpack('<I', index_data[offset+20:offset+24])[0]
        mem_size = struct.unpack('<I', index_data[offset+24:offset+28])[0]

        compressed = bool(file_size & 0x80000000)
        file_size_clean = file_size & 0x7FFFFFFF

        print(f"  Type: 0x{type_id:08X}")
        print(f"  Group: 0x{group_id:08X}")
        print(f"  Instance: 0x{inst_hi:08X}{inst_lo:08X}")
        print(f"  Offset: {res_offset}")
        print(f"  File size: {file_size_clean} (compressed: {compressed})")
        print(f"  Mem size: {mem_size}")

        # Check if there's an extra field for compressed
        if compressed:
            comp_size = struct.unpack('<I', index_data[offset+28:offset+32])[0]
            print(f"  Compressed size field: {comp_size}")

    except Exception as e:
        print(f"  Fout: {e}")

    return index_data

def main():
    working_idx = analyze_index("sims4_save_merger/Slot_00000012.save", "WERKENDE SAVE")
    merged_idx = analyze_index("sims4_save_merger/FINAL_MERGED.save", "ONZE MERGE")

    # Compare first 64 bytes of index
    print(f"\n{'='*70}")
    print("VERGELIJKING EERSTE 64 BYTES INDEX")
    print(f"{'='*70}")

    print("\nWERKEND:")
    print(hexdump(working_idx[:64], 64))

    print("\nMERGE:")
    print(hexdump(merged_idx[:64], 64))

    # Byte-by-byte comparison
    print("\nVerschillen in eerste 64 bytes:")
    for i in range(min(64, len(working_idx), len(merged_idx))):
        if working_idx[i] != merged_idx[i]:
            print(f"  Offset {i}: werkend=0x{working_idx[i]:02X}, merge=0x{merged_idx[i]:02X}")

if __name__ == '__main__':
    main()
