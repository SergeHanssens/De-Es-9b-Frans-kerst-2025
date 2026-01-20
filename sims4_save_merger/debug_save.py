#!/usr/bin/env python3
"""
Debug tool to examine the structure of a Sims 4 save file.

Usage:
    python debug_save.py <save_file>
"""

import sys
import struct
import zlib
from pathlib import Path


def hexdump(data: bytes, length: int = 64) -> str:
    """Create a hex dump of data"""
    result = []
    for i in range(0, min(len(data), length), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f'{i:08X}  {hex_part:<48}  {ascii_part}')
    return '\n'.join(result)


def analyze_file(filepath: str):
    """Analyze a Sims 4 save file"""
    path = Path(filepath)

    if not path.exists():
        print(f"Bestand niet gevonden: {filepath}")
        return

    print(f"\n{'='*60}")
    print(f"ANALYSE: {path.name}")
    print(f"{'='*60}")

    with open(path, 'rb') as f:
        data = f.read()

    print(f"\nBestandsgrootte: {len(data):,} bytes ({len(data)/1024/1024:.2f} MB)")

    # Check first bytes
    print(f"\nEerste 4 bytes: {data[0:4]} (hex: {data[0:4].hex()})")

    # Check if file is zlib compressed
    is_compressed = False
    if data[0:2] in [b'\x78\x9C', b'\x78\xDA', b'\x78\x01', b'\x78\x5E']:
        print(f"\n*** Bestand is zlib gecomprimeerd ***")
        is_compressed = True
        try:
            decompressed = zlib.decompress(data)
            print(f"Gedecomprimeerde grootte: {len(decompressed):,} bytes")
            data = decompressed
        except zlib.error as e:
            print(f"Kon niet decomprimeren: {e}")
            return

    # Check for DBPF magic
    magic = data[0:4]
    print(f"\nMagic bytes: {magic} (verwacht: b'DBPF')")

    if magic != b'DBPF':
        print(f"\nGeen DBPF bestand!")
        print(f"\nEerste 256 bytes hex dump:")
        print(hexdump(data, 256))
        return

    print("\n*** Valide DBPF bestand gevonden ***")

    # Parse header
    major_version = struct.unpack('<I', data[4:8])[0]
    minor_version = struct.unpack('<I', data[8:12])[0]
    print(f"\nDBPF Versie: {major_version}.{minor_version}")

    # Different header parsing based on version
    print("\n--- Header Details ---")

    # Bytes 12-16: User version major
    user_major = struct.unpack('<I', data[12:16])[0]
    print(f"User Version Major: {user_major}")

    # Bytes 16-20: User version minor
    user_minor = struct.unpack('<I', data[16:20])[0]
    print(f"User Version Minor: {user_minor}")

    # Bytes 20-24: Flags
    flags = struct.unpack('<I', data[20:24])[0]
    print(f"Flags: {flags} (0x{flags:08X})")

    # Bytes 24-28: Created timestamp
    created = struct.unpack('<I', data[24:28])[0]
    print(f"Created: {created}")

    # Bytes 28-32: Modified timestamp
    modified = struct.unpack('<I', data[28:32])[0]
    print(f"Modified: {modified}")

    # Bytes 32-36: Index type
    index_type = struct.unpack('<I', data[32:36])[0]
    print(f"Index Type: {index_type}")

    # Bytes 36-40: Index entry count
    index_count = struct.unpack('<I', data[36:40])[0]
    print(f"Index Entry Count: {index_count}")

    # Bytes 40-44: Index location (offset)
    index_loc = struct.unpack('<I', data[40:44])[0]
    print(f"Index Location (40-44): {index_loc}")

    # Bytes 44-48: Index size
    index_size_44 = struct.unpack('<I', data[44:48])[0]
    print(f"Index Size (44-48): {index_size_44}")

    # Bytes 64-68: Index offset (primary for DBPF 2.0)
    index_offset = struct.unpack('<I', data[64:68])[0]
    print(f"Index Offset (64-68): {index_offset}")

    # Bytes 68-72: Index size (primary for DBPF 2.0)
    index_size = struct.unpack('<I', data[68:72])[0]
    print(f"Index Size (68-72): {index_size}")

    print(f"\n--- Index Analyse ---")
    print(f"Bestandsgrootte: {len(data)}")
    print(f"Index offset: {index_offset}")
    print(f"Index size: {index_size}")
    print(f"Index eind: {index_offset + index_size}")

    if index_offset > len(data):
        print(f"\n*** FOUT: Index offset ({index_offset}) is groter dan bestand ({len(data)}) ***")
        return

    if index_offset + index_size > len(data):
        print(f"\n*** WAARSCHUWING: Index gaat voorbij einde bestand ***")

    # Read index
    index_data = data[index_offset:index_offset + min(index_size, len(data) - index_offset)]
    print(f"\nIndex data grootte: {len(index_data)} bytes")

    if len(index_data) >= 4:
        index_flags = struct.unpack('<I', index_data[0:4])[0]
        print(f"Index flags: {index_flags} (0x{index_flags:08X})")
        print(f"  Const Type: {bool(index_flags & 0x01)}")
        print(f"  Const Group: {bool(index_flags & 0x02)}")
        print(f"  Const Instance High: {bool(index_flags & 0x04)}")

    # Calculate expected entry size
    const_type = bool(index_flags & 0x01) if len(index_data) >= 4 else False
    const_group = bool(index_flags & 0x02) if len(index_data) >= 4 else False
    const_inst_hi = bool(index_flags & 0x04) if len(index_data) >= 4 else False

    header_size = 4  # flags
    if const_type:
        header_size += 4
    if const_group:
        header_size += 4
    if const_inst_hi:
        header_size += 4

    entry_size = 0
    if not const_type:
        entry_size += 4  # type
    if not const_group:
        entry_size += 4  # group
    if not const_inst_hi:
        entry_size += 4  # instance high
    entry_size += 4  # instance low
    entry_size += 4  # offset
    entry_size += 4  # file size
    entry_size += 4  # mem size
    # Plus optionally 4 more for compressed size

    print(f"\nIndex header size: {header_size} bytes")
    print(f"Entry size (min): {entry_size} bytes per entry")
    print(f"Beschikbaar voor entries: {len(index_data) - header_size} bytes")

    if entry_size > 0:
        max_entries = (len(index_data) - header_size) // entry_size
        print(f"Max entries die passen: ~{max_entries}")
        print(f"Verwacht entries: {index_count}")

    # Show first few bytes of index
    print(f"\nEerste 128 bytes van index:")
    print(hexdump(index_data, 128))

    # Try to parse first entry
    print(f"\n--- Eerste Entry Parsen ---")
    try:
        offset = 4  # Skip flags

        if const_type:
            const_type_val = struct.unpack('<I', index_data[offset:offset+4])[0]
            print(f"Const Type: 0x{const_type_val:08X}")
            offset += 4

        if const_group:
            const_group_val = struct.unpack('<I', index_data[offset:offset+4])[0]
            print(f"Const Group: 0x{const_group_val:08X}")
            offset += 4

        if const_inst_hi:
            const_inst_hi_val = struct.unpack('<I', index_data[offset:offset+4])[0]
            print(f"Const Instance High: 0x{const_inst_hi_val:08X}")
            offset += 4

        # First entry
        if not const_type:
            type_id = struct.unpack('<I', index_data[offset:offset+4])[0]
            print(f"Type ID: 0x{type_id:08X}")
            offset += 4

        if not const_group:
            group_id = struct.unpack('<I', index_data[offset:offset+4])[0]
            print(f"Group ID: 0x{group_id:08X}")
            offset += 4

        if not const_inst_hi:
            inst_hi = struct.unpack('<I', index_data[offset:offset+4])[0]
            print(f"Instance High: 0x{inst_hi:08X}")
            offset += 4

        inst_lo = struct.unpack('<I', index_data[offset:offset+4])[0]
        print(f"Instance Low: 0x{inst_lo:08X}")
        offset += 4

        entry_offset = struct.unpack('<I', index_data[offset:offset+4])[0]
        print(f"Entry Offset: {entry_offset}")
        offset += 4

        file_size = struct.unpack('<I', index_data[offset:offset+4])[0]
        compressed = bool(file_size & 0x80000000)
        file_size_clean = file_size & 0x7FFFFFFF
        print(f"File Size: {file_size_clean} (compressed: {compressed})")
        offset += 4

        mem_size = struct.unpack('<I', index_data[offset:offset+4])[0]
        print(f"Mem Size: {mem_size}")

    except Exception as e:
        print(f"Fout bij parsen: {e}")

    print(f"\n{'='*60}")
    print("ANALYSE VOLTOOID")
    print(f"{'='*60}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Gebruik: python debug_save.py <save_bestand>")
        sys.exit(1)

    analyze_file(sys.argv[1])
