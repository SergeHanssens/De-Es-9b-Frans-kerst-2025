#!/usr/bin/env python3
"""
Debug: Compare our file format with files the game DOES recognize
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from pathlib import Path
import struct

def hexdump(data, length=None):
    if length:
        data = data[:length]
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'{i:04X}: {hex_part:<48} {ascii_part}')
    return '\n'.join(lines)

def analyze_header(filepath):
    """Analyze the header of a save file"""
    with open(filepath, 'rb') as f:
        data = f.read(96)

    print(f"\n{'='*60}")
    print(f"FILE: {filepath.name}")
    print(f"{'='*60}")
    print(f"Size: {filepath.stat().st_size:,} bytes")

    print(f"\nHeader (96 bytes):")
    print(hexdump(data))

    # Parse key fields
    print(f"\nParsed header fields:")
    print(f"  Magic: {data[0:4]}")
    print(f"  Major version: {struct.unpack('<I', data[4:8])[0]}")
    print(f"  Minor version: {struct.unpack('<I', data[8:12])[0]}")
    print(f"  Bytes 12-16: {struct.unpack('<I', data[12:16])[0]}")
    print(f"  Bytes 16-20: {struct.unpack('<I', data[16:20])[0]}")
    print(f"  Bytes 20-24: {struct.unpack('<I', data[20:24])[0]}")
    print(f"  Bytes 24-28: {struct.unpack('<I', data[24:28])[0]}")
    print(f"  Bytes 28-32: {struct.unpack('<I', data[28:32])[0]}")
    print(f"  Index type (32-36): {struct.unpack('<I', data[32:36])[0]}")
    print(f"  Entry count (36-40): {struct.unpack('<I', data[36:40])[0]}")
    print(f"  Bytes 40-44: {struct.unpack('<I', data[40:44])[0]}")
    print(f"  Index size alt (44-48): {struct.unpack('<I', data[44:48])[0]}")
    print(f"  Bytes 48-52: {struct.unpack('<I', data[48:52])[0]}")
    print(f"  Bytes 52-56: {struct.unpack('<I', data[52:56])[0]}")
    print(f"  Bytes 56-60: {struct.unpack('<I', data[56:60])[0]}")
    print(f"  Index minor ver (60-64): {struct.unpack('<I', data[60:64])[0]}")
    print(f"  Index offset (64-68): {struct.unpack('<I', data[64:68])[0]}")
    print(f"  Index size (68-72): {struct.unpack('<I', data[68:72])[0]}")

    # Check index location
    index_offset = struct.unpack('<I', data[64:68])[0]
    index_size = struct.unpack('<I', data[68:72])[0]
    if index_size == 0:
        index_size = struct.unpack('<I', data[44:48])[0]

    print(f"\n  Calculated index range: {index_offset} - {index_offset + index_size}")

    return data

def compare():
    files = [
        Path("sims4_save_merger/AllSlots/Slot_00000002.save"),  # Corrupt but recognized
        Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4"),  # Working
        Path("sims4_save_merger/COMPLETE_REPAIR.save"),  # Our file
    ]

    headers = []
    for f in files:
        if f.exists():
            h = analyze_header(f)
            headers.append((f.name, h))

    # Compare headers byte by byte
    print(f"\n{'='*60}")
    print("HEADER COMPARISON")
    print(f"{'='*60}")

    if len(headers) >= 2:
        corrupt_h = headers[0][1]
        working_h = headers[1][1]
        our_h = headers[2][1] if len(headers) > 2 else None

        print(f"\nByte differences (Corrupt vs Working):")
        for i in range(96):
            if corrupt_h[i] != working_h[i]:
                print(f"  Byte {i:2d}: Corrupt=0x{corrupt_h[i]:02X}, Working=0x{working_h[i]:02X}")

        if our_h:
            print(f"\nByte differences (Corrupt vs Our file):")
            for i in range(96):
                if corrupt_h[i] != our_h[i]:
                    print(f"  Byte {i:2d}: Corrupt=0x{corrupt_h[i]:02X}, Ours=0x{our_h[i]:02X}")

    # Check index structure
    print(f"\n{'='*60}")
    print("INDEX STRUCTURE CHECK")
    print(f"{'='*60}")

    for filepath, _ in headers:
        filepath = Path("sims4_save_merger/AllSlots/" + filepath) if "AllSlots" not in filepath else Path("sims4_save_merger/" + filepath)
        if "AllSlots" in str(filepath):
            filepath = Path("sims4_save_merger/AllSlots") / Path(filepath).name
        else:
            filepath = Path("sims4_save_merger") / Path(filepath).name

        if not filepath.exists():
            for f in files:
                if f.name == Path(filepath).name:
                    filepath = f
                    break

        with open(filepath, 'rb') as f:
            data = f.read()

        # Get index location
        index_offset = struct.unpack('<I', data[64:68])[0]
        index_size = struct.unpack('<I', data[68:72])[0]
        if index_size == 0:
            index_size = struct.unpack('<I', data[44:48])[0]

        print(f"\n{filepath.name}:")
        print(f"  File size: {len(data):,}")
        print(f"  Index at: {index_offset}")
        print(f"  Index size: {index_size}")
        print(f"  Index end: {index_offset + index_size}")
        print(f"  File end: {len(data)}")
        print(f"  Bytes after index: {len(data) - (index_offset + index_size)}")

        # Check first few bytes of index
        if index_offset < len(data):
            index_start = data[index_offset:index_offset+32]
            print(f"  Index first 32 bytes: {index_start.hex()}")

if __name__ == '__main__':
    compare()
