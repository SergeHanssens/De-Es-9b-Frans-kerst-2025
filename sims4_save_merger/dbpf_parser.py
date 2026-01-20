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

    @classmethod
    def from_bytes(cls, data: bytes) -> 'DBPFHeader':
        """Parse header from bytes"""
        if len(data) < 96:
            raise ValueError(f"Header too short: {len(data)} bytes")

        magic = data[0:4]
        if magic != b'DBPF':
            raise ValueError(f"Invalid DBPF magic: {magic}")

        major_version = struct.unpack('<I', data[4:8])[0]
        minor_version = struct.unpack('<I', data[8:12])[0]

        # Index information varies by version
        if major_version == 2:
            index_entry_count = struct.unpack('<I', data[36:40])[0]
            index_offset = struct.unpack('<I', data[64:68])[0]
            index_size = struct.unpack('<I', data[68:72])[0]
        else:
            # DBPF 1.x format
            index_entry_count = struct.unpack('<I', data[36:40])[0]
            index_offset = struct.unpack('<I', data[40:44])[0]
            index_size = struct.unpack('<I', data[44:48])[0]

        return cls(
            magic=magic,
            major_version=major_version,
            minor_version=minor_version,
            index_entry_count=index_entry_count,
            index_offset=index_offset,
            index_size=index_size
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
            # Read and parse header
            self._raw_header = f.read(96)
            self.header = DBPFHeader.from_bytes(self._raw_header)

            # Read index
            f.seek(self.header.index_offset)
            index_data = f.read(self.header.index_size)

            # Parse index entries
            entries = self._parse_index(index_data, self.header.index_entry_count)

            # Read all resources
            for entry in entries:
                f.seek(entry.offset)
                raw_data = f.read(entry.file_size)

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

    def _parse_index(self, data: bytes, count: int) -> List[IndexEntry]:
        """Parse index entries from raw data"""
        entries = []

        if count == 0:
            return entries

        # Read index flags (first 4 bytes)
        flags = struct.unpack('<I', data[0:4])[0]
        offset = 4

        # Check which fields are constant across all entries
        const_type = flags & 0x01
        const_group = flags & 0x02
        const_instance_high = flags & 0x04

        # Read constant values if flagged
        type_id_const = 0
        group_id_const = 0
        instance_high_const = 0

        if const_type:
            type_id_const = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
        if const_group:
            group_id_const = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
        if const_instance_high:
            instance_high_const = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4

        # Parse each entry
        for _ in range(count):
            if const_type:
                type_id = type_id_const
            else:
                type_id = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4

            if const_group:
                group_id = group_id_const
            else:
                group_id = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4

            if const_instance_high:
                instance_high = instance_high_const
            else:
                instance_high = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4

            instance_low = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4

            instance_id = (instance_high << 32) | instance_low

            entry_offset = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4

            file_size = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4

            # Check compression flag (high bit of file_size)
            compressed = bool(file_size & 0x80000000)
            file_size = file_size & 0x7FFFFFFF

            mem_size = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4

            # Skip compressed size field if present
            if compressed:
                offset += 4

            entries.append(IndexEntry(
                type_id=type_id,
                group_id=group_id,
                instance_id=instance_id,
                offset=entry_offset,
                file_size=file_size,
                mem_size=mem_size,
                compressed=compressed
            ))

        return entries

    def _decompress(self, data: bytes, target_size: int) -> bytes:
        """Decompress resource data"""
        if len(data) < 2:
            return data

        # Check for zlib compression (common in Sims 4)
        if data[0:2] == b'\x78\x9C' or data[0:2] == b'\x78\xDA':
            return zlib.decompress(data)

        # Check for RefPack/QFS compression (EA proprietary)
        if len(data) >= 5 and data[0:2] in [b'\x10\xFB', b'\x90\xFB']:
            return self._decompress_refpack(data, target_size)

        return data

    def _decompress_refpack(self, data: bytes, target_size: int) -> bytes:
        """Decompress RefPack/QFS compressed data"""
        # RefPack decompression (simplified version)
        result = bytearray()

        # Skip header
        pos = 2
        if data[0] & 0x80:
            pos = 5

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

    def save(self, filepath: Path) -> None:
        """Save the DBPF file"""
        filepath = Path(filepath)

        # Prepare all resources and build index
        resource_data = bytearray()
        entries = []

        data_offset = 96  # Start after header

        for key, resource in self.resources.items():
            # Optionally compress data
            compressed_data, is_compressed = self._compress(resource.data)

            entry = IndexEntry(
                type_id=key[0],
                group_id=key[1],
                instance_id=key[2],
                offset=data_offset,
                file_size=len(compressed_data),
                mem_size=len(resource.data),
                compressed=is_compressed
            )
            entries.append(entry)

            resource_data.extend(compressed_data)
            data_offset += len(compressed_data)

        # Build index
        index_data = self._build_index(entries)
        index_offset = data_offset

        # Update header
        header = bytearray(96)
        header[0:4] = b'DBPF'
        struct.pack_into('<I', header, 4, 2)  # Major version
        struct.pack_into('<I', header, 8, 1)  # Minor version
        struct.pack_into('<I', header, 36, len(entries))
        struct.pack_into('<I', header, 64, index_offset)
        struct.pack_into('<I', header, 68, len(index_data))

        # Write file
        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(resource_data)
            f.write(index_data)

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
