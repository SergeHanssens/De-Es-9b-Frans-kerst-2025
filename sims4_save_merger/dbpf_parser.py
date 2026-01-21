"""
DBPF Parser for The Sims 4 Save Files

The Sims 4 uses the DBPF (Database Packed File) format for save files.
This module provides classes to read, parse, and write DBPF files.

DBPF Structure:
- Header (96 bytes for DBPF 2.0)
- Index entries (each entry points to a resource)
- Resource data

Each resource is identified by:
- Type ID (4 bytes)
- Group ID (4 bytes)
- Instance ID (8 bytes)
"""

import struct
import zlib
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, BinaryIO
from pathlib import Path


@dataclass
class DBPFHeader:
    """DBPF file header structure"""
    magic: bytes  # 'DBPF'
    major_version: int
    minor_version: int
    index_entry_count: int
    index_offset: int
    index_size: int
    index_type: int = 7

    @classmethod
    def from_bytes(cls, data: bytes) -> 'DBPFHeader':
        """Parse header from bytes"""
        if len(data) < 96:
            raise ValueError(f"Header te kort: {len(data)} bytes (minimaal 96 nodig)")

        magic = data[0:4]
        if magic != b'DBPF':
            raise ValueError(f"Ongeldig DBPF bestand: magic bytes zijn {magic!r}, verwacht b'DBPF'")

        major_version = struct.unpack('<I', data[4:8])[0]
        minor_version = struct.unpack('<I', data[8:12])[0]

        # Index type at offset 32
        index_type = struct.unpack('<I', data[32:36])[0]

        # Index entry count at offset 36
        index_entry_count = struct.unpack('<I', data[36:40])[0]

        # Index information varies by version
        if major_version == 2:
            # DBPF 2.0 (Sims 4) - index offset at 64-68
            index_offset = struct.unpack('<I', data[64:68])[0]

            # Index size can be at 68-72 OR 44-48 depending on the file
            index_size = struct.unpack('<I', data[68:72])[0]

            # If size is 0 at 68-72, use alternative location at 44-48
            if index_size == 0:
                index_size = struct.unpack('<I', data[44:48])[0]

            # If offset is 0, try alternative location at 40-44
            if index_offset == 0:
                index_offset = struct.unpack('<I', data[40:44])[0]
        else:
            # DBPF 1.x format
            index_offset = struct.unpack('<I', data[40:44])[0]
            index_size = struct.unpack('<I', data[44:48])[0]

        return cls(
            magic=magic,
            major_version=major_version,
            minor_version=minor_version,
            index_entry_count=index_entry_count,
            index_offset=index_offset,
            index_size=index_size,
            index_type=index_type
        )

    def to_bytes(self) -> bytes:
        """Convert header back to bytes for DBPF 2.0"""
        header = bytearray(96)

        # Magic
        header[0:4] = self.magic

        # Version
        struct.pack_into('<I', header, 4, self.major_version)
        struct.pack_into('<I', header, 8, self.minor_version)

        # Index info
        struct.pack_into('<I', header, 36, self.index_entry_count)
        struct.pack_into('<I', header, 64, self.index_offset)
        struct.pack_into('<I', header, 68, self.index_size)

        return bytes(header)


@dataclass
class IndexEntry:
    """DBPF index entry - identifies a resource"""
    type_id: int
    group_id: int
    instance_id: int
    offset: int
    file_size: int  # Size in file (possibly compressed)
    mem_size: int   # Size in memory (uncompressed)
    compressed: bool

    @property
    def key(self) -> Tuple[int, int, int]:
        """Return the unique resource key (Type, Group, Instance)"""
        return (self.type_id, self.group_id, self.instance_id)

    @property
    def key_hex(self) -> str:
        """Return the key as hex string for display"""
        return f"{self.type_id:08X}:{self.group_id:08X}:{self.instance_id:016X}"


@dataclass
class Resource:
    """A complete resource with index entry and data"""
    entry: IndexEntry
    data: bytes

    @property
    def key(self) -> Tuple[int, int, int]:
        return self.entry.key

    @property
    def key_hex(self) -> str:
        return self.entry.key_hex


class DBPFFile:
    """
    Represents a DBPF file (The Sims 4 save file)

    Can read existing files and write new ones.
    """

    # Known resource types in Sims 4 saves
    RESOURCE_TYPES = {
        0x0: "Unknown",
        0x220557DA: "SimData",
        0x545AC67A: "Thumbnail",
        0x62ECC59A: "ObjectData",
        0xB61DE6B4: "Household",
        0xE882D22F: "Lot",
        0xDC95CF1A: "Zone",
        0x0C772E27: "RelationshipData",
        0x3BD45407: "Situation",
        0xBC4587A3: "String Table",
        0xC0DB5AE7: "SimInfo",
    }

    def __init__(self, filepath: Optional[Path] = None):
        self.filepath = filepath
        self.header: Optional[DBPFHeader] = None
        self.resources: Dict[Tuple[int, int, int], Resource] = {}
        self._raw_header: bytes = b''

        if filepath:
            self.load(filepath)

    def load(self, filepath: Path) -> None:
        """Load a DBPF file"""
        self.filepath = Path(filepath)

        with open(filepath, 'rb') as f:
            # Read entire file first
            file_data = f.read()

        # Check if file is compressed (zlib header)
        if file_data[0:2] in [b'\x78\x9C', b'\x78\xDA', b'\x78\x01', b'\x78\x5E']:
            try:
                file_data = zlib.decompress(file_data)
            except zlib.error as e:
                raise ValueError(f"Kon gecomprimeerd bestand niet uitpakken: {e}")

        # Now parse as DBPF
        if len(file_data) < 96:
            raise ValueError(f"Bestand te klein: {len(file_data)} bytes")

        self._raw_header = file_data[0:96]
        self.header = DBPFHeader.from_bytes(self._raw_header)

        # Validate index offset
        if self.header.index_offset > len(file_data):
            raise ValueError(
                f"Ongeldige index offset: {self.header.index_offset} > bestandsgrootte {len(file_data)}"
            )

        # Read index
        index_end = self.header.index_offset + self.header.index_size
        if index_end > len(file_data):
            # Adjust index size if it goes beyond file
            actual_size = len(file_data) - self.header.index_offset
            index_data = file_data[self.header.index_offset:self.header.index_offset + actual_size]
        else:
            index_data = file_data[self.header.index_offset:index_end]

        # Parse index entries
        entries = self._parse_index(index_data, self.header.index_entry_count)

        # Read all resources
        for entry in entries:
            # Validate offset
            if entry.offset >= len(file_data):
                print(f"Waarschuwing: Resource offset {entry.offset} buiten bestand, overslaan")
                continue

            end_offset = min(entry.offset + entry.file_size, len(file_data))
            raw_data = file_data[entry.offset:end_offset]

            if len(raw_data) == 0:
                continue

            # Decompress if needed
            if entry.compressed and entry.file_size != entry.mem_size:
                try:
                    data = self._decompress(raw_data, entry.mem_size)
                except Exception:
                    # Keep raw data if decompression fails
                    data = raw_data
            else:
                data = raw_data

            resource = Resource(entry=entry, data=data)
            self.resources[resource.key] = resource

    def _safe_unpack(self, data: bytes, offset: int, size: int = 4) -> Tuple[int, int]:
        """Safely unpack an integer from data with bounds checking"""
        if offset + size > len(data):
            raise ValueError(f"Buffer te kort: nodig {offset + size} bytes, hebben {len(data)}")
        value = struct.unpack('<I', data[offset:offset+size])[0]
        return value, offset + size

    def _parse_index(self, data: bytes, count: int) -> List[IndexEntry]:
        """Parse index entries from raw data"""
        entries = []

        if count == 0 or len(data) < 4:
            return entries

        # Try standard DBPF 2.0 index format first
        try:
            entries = self._parse_index_dbpf2(data, count)
            if entries:
                return entries
        except Exception:
            pass

        # Fallback: try fixed-size entry format (32 bytes per entry, no flags)
        try:
            entries = self._parse_index_fixed(data, count)
            if entries:
                return entries
        except Exception:
            pass

        return entries

    def _parse_index_dbpf2(self, data: bytes, count: int) -> List[IndexEntry]:
        """Parse DBPF 2.0 index format with flags"""
        entries = []

        # Read index flags (first 4 bytes)
        flags, offset = self._safe_unpack(data, 0)

        # Check which fields are constant across all entries
        const_type = bool(flags & 0x01)
        const_group = bool(flags & 0x02)
        const_instance_high = bool(flags & 0x04)

        # Read constant values if flagged
        type_id_const = 0
        group_id_const = 0
        instance_high_const = 0

        if const_type:
            type_id_const, offset = self._safe_unpack(data, offset)
        if const_group:
            group_id_const, offset = self._safe_unpack(data, offset)
        if const_instance_high:
            instance_high_const, offset = self._safe_unpack(data, offset)

        # Parse each entry
        for i in range(count):
            try:
                if const_type:
                    type_id = type_id_const
                else:
                    type_id, offset = self._safe_unpack(data, offset)

                if const_group:
                    group_id = group_id_const
                else:
                    group_id, offset = self._safe_unpack(data, offset)

                if const_instance_high:
                    instance_high = instance_high_const
                else:
                    instance_high, offset = self._safe_unpack(data, offset)

                instance_low, offset = self._safe_unpack(data, offset)
                instance_id = (instance_high << 32) | instance_low

                entry_offset, offset = self._safe_unpack(data, offset)
                file_size_raw, offset = self._safe_unpack(data, offset)

                # Check compression flag (high bit of file_size)
                compressed = bool(file_size_raw & 0x80000000)
                file_size = file_size_raw & 0x7FFFFFFF

                mem_size, offset = self._safe_unpack(data, offset)

                # Skip compressed size field if present
                if compressed:
                    _, offset = self._safe_unpack(data, offset)

                entries.append(IndexEntry(
                    type_id=type_id,
                    group_id=group_id,
                    instance_id=instance_id,
                    offset=entry_offset,
                    file_size=file_size,
                    mem_size=mem_size,
                    compressed=compressed
                ))
            except ValueError as e:
                # Stop parsing if we run out of data
                print(f"Waarschuwing: Kon entry {i+1}/{count} niet parsen: {e}")
                break

        return entries

    def _parse_index_fixed(self, data: bytes, count: int) -> List[IndexEntry]:
        """Parse fixed-size index entries (32 bytes each, no flags header)"""
        entries = []
        entry_size = 32  # Type(4) + Group(4) + Instance(8) + Offset(4) + FileSize(4) + MemSize(4) + Compressed(4)

        # Check if we have flags header or direct entries
        # If data starts with reasonable entry values, assume no header
        offset = 0

        # Check if first 4 bytes look like flags (small number) or type ID (large hex)
        first_val = struct.unpack('<I', data[0:4])[0]
        if first_val < 8:  # Likely flags
            offset = 4
            flags = first_val
            if flags & 0x01:
                offset += 4
            if flags & 0x02:
                offset += 4
            if flags & 0x04:
                offset += 4

        remaining = len(data) - offset
        actual_count = min(count, remaining // entry_size)

        for i in range(actual_count):
            try:
                base = offset + (i * entry_size)

                type_id = struct.unpack('<I', data[base:base+4])[0]
                group_id = struct.unpack('<I', data[base+4:base+8])[0]
                instance_id = struct.unpack('<Q', data[base+8:base+16])[0]
                entry_offset = struct.unpack('<I', data[base+16:base+20])[0]

                file_size_raw = struct.unpack('<I', data[base+20:base+24])[0]
                compressed = bool(file_size_raw & 0x80000000)
                file_size = file_size_raw & 0x7FFFFFFF

                mem_size = struct.unpack('<I', data[base+24:base+28])[0]

                entries.append(IndexEntry(
                    type_id=type_id,
                    group_id=group_id,
                    instance_id=instance_id,
                    offset=entry_offset,
                    file_size=file_size,
                    mem_size=mem_size,
                    compressed=compressed
                ))
            except Exception as e:
                print(f"Waarschuwing: Fout bij fixed entry {i}: {e}")
                break

        return entries

    def _decompress(self, data: bytes, target_size: int) -> bytes:
        """Decompress resource data"""
        if len(data) < 2:
            return data

        # Check for zlib compression (common in Sims 4)
        if data[0:2] == b'\x78\x9C' or data[0:2] == b'\x78\xDA':
            return zlib.decompress(data)

        # Check for RefPack/QFS compression (EA proprietary)
        # 0x10FB = basic, 0x50FB = with size header (common in Sims 4), 0x90FB = 24-bit size
        if len(data) >= 5 and data[0:2] in [b'\x10\xFB', b'\x50\xFB', b'\x90\xFB']:
            return self._decompress_refpack(data, target_size)

        return data

    def _decompress_refpack(self, data: bytes, target_size: int) -> bytes:
        """Decompress RefPack/QFS compressed data"""
        # RefPack decompression (simplified version)
        result = bytearray()

        # Skip header based on first byte
        # 0x10FB: 2-byte header (no size)
        # 0x50FB: 5-byte header (3-byte size after signature)
        # 0x90FB: 5-byte header (3-byte size after signature)
        first_byte = data[0]
        if first_byte & 0x80:  # 0x90
            pos = 5
        elif first_byte & 0x40:  # 0x50
            pos = 5
        else:  # 0x10
            pos = 2

        while pos < len(data) and len(result) < target_size:
            ctrl = data[pos]
            pos += 1

            if ctrl < 0x80:
                # Literal bytes
                num_literal = ctrl & 0x03
                copy_offset = ((ctrl & 0x60) << 3)
                if pos < len(data):
                    copy_offset |= data[pos]
                    pos += 1
                copy_length = ((ctrl >> 2) & 0x07) + 3

                for _ in range(num_literal):
                    if pos < len(data):
                        result.append(data[pos])
                        pos += 1

                if copy_offset > 0:
                    start = len(result) - copy_offset - 1
                    for i in range(copy_length):
                        if start + i >= 0 and start + i < len(result):
                            result.append(result[start + i])

            elif ctrl < 0xC0:
                # More complex pattern
                num_literal = (data[pos] >> 6) if pos < len(data) else 0
                copy_length = (ctrl & 0x3F) + 4
                copy_offset = ((data[pos] & 0x3F) << 8) if pos < len(data) else 0
                pos += 1
                if pos < len(data):
                    copy_offset |= data[pos]
                    pos += 1

                for _ in range(num_literal):
                    if pos < len(data):
                        result.append(data[pos])
                        pos += 1

                start = len(result) - copy_offset - 1
                for i in range(copy_length):
                    if start + i >= 0 and start + i < len(result):
                        result.append(result[start + i])

            elif ctrl < 0xE0:
                # Large copy
                num_literal = ctrl & 0x03
                copy_length = ((ctrl >> 2) & 0x03) * 256
                if pos < len(data):
                    copy_length += data[pos] + 5
                    pos += 1
                copy_offset = 0
                if pos + 1 < len(data):
                    copy_offset = (data[pos] << 8) | data[pos + 1]
                    pos += 2

                for _ in range(num_literal):
                    if pos < len(data):
                        result.append(data[pos])
                        pos += 1

                start = len(result) - copy_offset - 1
                for i in range(copy_length):
                    if start + i >= 0 and start + i < len(result):
                        result.append(result[start + i])

            elif ctrl < 0xFC:
                # Literal run
                num_literal = ((ctrl & 0x1F) + 1) * 4
                for _ in range(num_literal):
                    if pos < len(data):
                        result.append(data[pos])
                        pos += 1

            else:
                # Short literal
                num_literal = ctrl & 0x03
                for _ in range(num_literal):
                    if pos < len(data):
                        result.append(data[pos])
                        pos += 1

        return bytes(result)

    def _compress(self, data: bytes) -> Tuple[bytes, bool]:
        """Compress resource data using zlib"""
        if len(data) < 64:  # Don't compress small data
            return data, False

        compressed = zlib.compress(data, 6)
        if len(compressed) < len(data) * 0.9:  # Only use if 10%+ savings
            return compressed, True
        return data, False

    def save(self, filepath: Path, compress_file: bool = False) -> None:
        """
        Save the DBPF file

        Args:
            filepath: Output path
            compress_file: If True, compress the entire file with zlib
        """
        filepath = Path(filepath)

        # Prepare all resources and build index
        resource_data = bytearray()
        entries = []

        data_offset = 96  # Start after header

        for key, resource in self.resources.items():
            # Store data uncompressed for maximum compatibility
            # Sims 4 can read uncompressed resources without issues
            data_to_write = resource.data

            entry = IndexEntry(
                type_id=key[0],
                group_id=key[1],
                instance_id=key[2],
                offset=data_offset,
                file_size=len(data_to_write),
                mem_size=len(data_to_write),
                compressed=False
            )
            entries.append(entry)

            resource_data.extend(data_to_write)
            data_offset += len(data_to_write)

        # Build index
        index_data = self._build_index(entries)
        index_offset = data_offset

        # Build complete DBPF 2.0 header (96 bytes)
        header = bytearray(96)

        # Magic and version
        header[0:4] = b'DBPF'
        struct.pack_into('<I', header, 4, 2)   # Major version
        struct.pack_into('<I', header, 8, 1)   # Minor version

        # User version (can be 0)
        struct.pack_into('<I', header, 12, 0)  # User major
        struct.pack_into('<I', header, 16, 0)  # User minor

        # Unused/flags
        struct.pack_into('<I', header, 20, 0)  # Flags

        # Created/modified timestamps (0 = not set)
        struct.pack_into('<I', header, 24, 0)  # Created
        struct.pack_into('<I', header, 28, 0)  # Modified

        # Index type (0 for Sims 4 saves, 7 for packages)
        struct.pack_into('<I', header, 32, 0)

        # Index entry count
        struct.pack_into('<I', header, 36, len(entries))

        # Index location (offset 40-44 is usually 0 for DBPF 2.0)
        struct.pack_into('<I', header, 40, 0)

        # Index size at offset 44 (alternative location)
        struct.pack_into('<I', header, 44, len(index_data))

        # Hole count/offset/size (usually 0)
        struct.pack_into('<I', header, 48, 0)  # Hole count
        struct.pack_into('<I', header, 52, 0)  # Hole offset
        struct.pack_into('<I', header, 56, 0)  # Hole size

        # Index minor version
        struct.pack_into('<I', header, 60, 3)

        # Index offset (primary location for DBPF 2.0)
        struct.pack_into('<I', header, 64, index_offset)

        # Bytes 68-72 should be 0 for Sims 4 saves (index size is at 44-48)
        struct.pack_into('<I', header, 68, 0)

        # Bytes 80-81 should be 0xFFFF in Sims 4 saves
        struct.pack_into('<H', header, 80, 0xFFFF)

        # Combine all data
        output_data = bytes(header) + bytes(resource_data) + bytes(index_data)

        # Optionally compress entire file
        if compress_file:
            output_data = zlib.compress(output_data, 6)

        # Write file
        with open(filepath, 'wb') as f:
            f.write(output_data)

    def _build_index(self, entries: List[IndexEntry]) -> bytes:
        """Build index data from entries"""
        if not entries:
            return struct.pack('<I', 0)  # Just flags

        index = bytearray()

        # Flags - no constant fields for simplicity
        index.extend(struct.pack('<I', 0))

        for entry in entries:
            index.extend(struct.pack('<I', entry.type_id))
            index.extend(struct.pack('<I', entry.group_id))
            index.extend(struct.pack('<I', entry.instance_id >> 32))  # High
            index.extend(struct.pack('<I', entry.instance_id & 0xFFFFFFFF))  # Low
            index.extend(struct.pack('<I', entry.offset))

            file_size = entry.file_size
            if entry.compressed:
                file_size |= 0x80000000
            index.extend(struct.pack('<I', file_size))

            index.extend(struct.pack('<I', entry.mem_size))

            if entry.compressed:
                index.extend(struct.pack('<I', entry.file_size))

        return bytes(index)

    def get_resource_type_name(self, type_id: int) -> str:
        """Get human-readable name for resource type"""
        return self.RESOURCE_TYPES.get(type_id, f"Type_{type_id:08X}")

    def get_statistics(self) -> Dict:
        """Get file statistics"""
        type_counts = {}
        total_size = 0

        for key, resource in self.resources.items():
            type_name = self.get_resource_type_name(key[0])
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            total_size += len(resource.data)

        return {
            'filepath': str(self.filepath) if self.filepath else None,
            'version': f"{self.header.major_version}.{self.header.minor_version}" if self.header else None,
            'resource_count': len(self.resources),
            'total_size': total_size,
            'type_counts': type_counts
        }


def compare_files(file1: DBPFFile, file2: DBPFFile) -> Dict:
    """
    Compare two DBPF files and return differences

    Returns:
        Dict with:
        - only_in_file1: keys only in first file
        - only_in_file2: keys only in second file
        - in_both: keys in both files
        - different: keys in both but with different data
    """
    keys1 = set(file1.resources.keys())
    keys2 = set(file2.resources.keys())

    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1
    in_both = keys1 & keys2

    different = set()
    same = set()

    for key in in_both:
        if file1.resources[key].data != file2.resources[key].data:
            different.add(key)
        else:
            same.add(key)

    return {
        'only_in_file1': only_in_1,
        'only_in_file2': only_in_2,
        'in_both': in_both,
        'same': same,
        'different': different
    }
