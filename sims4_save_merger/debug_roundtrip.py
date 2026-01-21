#!/usr/bin/env python3
"""
Debug why roundtrip loses data
"""

import sys
sys.path.insert(0, '/home/user/De-Es-9b-Frans-kerst-2025')

from sims4_save_merger.dbpf_parser import DBPFFile
from pathlib import Path
import struct

def debug():
    print("=" * 70)
    print("DEBUG: Waarom verliezen we data?")
    print("=" * 70)

    working_path = Path("sims4_save_merger/AllSlots/Slot_00000002.save(13).ver4")

    # Read original file
    with open(working_path, 'rb') as f:
        orig_bytes = f.read()

    print(f"\nOrigineel bestand: {len(orig_bytes):,} bytes")

    # Parse header
    index_offset = struct.unpack('<I', orig_bytes[64:68])[0]
    index_size = struct.unpack('<I', orig_bytes[44:48])[0]
    entry_count = struct.unpack('<I', orig_bytes[36:40])[0]

    print(f"\nHeader info:")
    print(f"  Entry count: {entry_count}")
    print(f"  Index offset: {index_offset}")
    print(f"  Index size: {index_size}")
    print(f"  Data section: 96 - {index_offset} = {index_offset - 96:,} bytes")

    # Load with our parser
    print("\n" + "-" * 50)
    print("Laden met onze parser...")
    dbpf = DBPFFile(working_path)

    print(f"Resources geladen: {len(dbpf.resources)}")

    # Calculate total data size we read
    total_data = sum(len(r.data) for r in dbpf.resources.values())
    print(f"Totale data in memory: {total_data:,} bytes")

    # Check original data section size
    original_data_size = index_offset - 96
    print(f"\nOriginele data sectie: {original_data_size:,} bytes")
    print(f"Onze data in memory:   {total_data:,} bytes")
    print(f"Verschil:              {total_data - original_data_size:+,} bytes")

    # Expected output size
    expected_output = 96 + total_data + index_size
    print(f"\nVerwachte output: 96 + {total_data:,} + ~{index_size} = ~{expected_output:,} bytes")

    # Check for compressed resources
    print("\n" + "-" * 50)
    print("Gecomprimeerde resources:")

    compressed_count = 0
    compressed_savings = 0

    for key, resource in dbpf.resources.items():
        entry = resource.entry
        if entry.compressed:
            compressed_count += 1
            # file_size is compressed, mem_size is uncompressed
            savings = entry.mem_size - entry.file_size
            compressed_savings += savings

    print(f"Aantal gecomprimeerd: {compressed_count}")
    print(f"Compressie besparing: {compressed_savings:,} bytes")

    # What happens when we write
    print("\n" + "-" * 50)
    print("Wat we schrijven:")

    # We write uncompressed data, so file_size = mem_size = len(data)
    written_data = sum(len(r.data) for r in dbpf.resources.values())
    print(f"Data bytes: {written_data:,}")

    # Our index is different - no compression flags, no compressed_size field
    # Each entry: type(4) + group(4) + inst_high(4) + inst_low(4) + offset(4) + file_size(4) + mem_size(4) = 28 bytes
    # Plus flags at start (4 bytes)
    our_index_size = 4 + len(dbpf.resources) * 28
    print(f"Onze index: {our_index_size:,} bytes")

    our_total = 96 + written_data + our_index_size
    print(f"Verwacht totaal: {our_total:,} bytes")

    # Compare with actual
    output = Path("sims4_save_merger/ROUNDTRIP_TEST.save")
    if output.exists():
        actual = output.stat().st_size
        print(f"Werkelijk: {actual:,} bytes")
        print(f"Verschil: {actual - our_total:+,} bytes")

    # Check if we're losing resources during parsing
    print("\n" + "-" * 50)
    print("Resource telling:")

    # Parse index manually to count resources
    pos = index_offset + 4  # Skip flags
    manual_count = 0

    while pos < index_offset + index_size and manual_count < entry_count:
        type_id = struct.unpack('<I', orig_bytes[pos:pos+4])[0]
        file_size_raw = struct.unpack('<I', orig_bytes[pos+20:pos+24])[0]
        compressed = bool(file_size_raw & 0x80000000)

        entry_size = 28
        if compressed:
            entry_size = 32

        pos += entry_size
        manual_count += 1

    print(f"Header zegt: {entry_count} entries")
    print(f"Onze parser las: {len(dbpf.resources)} resources")
    print(f"Handmatig geteld: {manual_count} entries in index")

if __name__ == '__main__':
    debug()
