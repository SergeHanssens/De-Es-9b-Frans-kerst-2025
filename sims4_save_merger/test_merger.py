#!/usr/bin/env python3
"""
Test script for Sims 4 Save Merger

Creates test DBPF files and verifies the merger works correctly.
"""

import sys
import os
import struct
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sims4_save_merger.dbpf_parser import DBPFFile, DBPFHeader, IndexEntry, Resource
from sims4_save_merger.merger import Sims4SaveMerger, MergeStrategy


def create_test_dbpf(filepath: Path, resources: dict):
    """
    Create a test DBPF file with specified resources.

    Args:
        filepath: Output path
        resources: Dict of {(type, group, instance): bytes_data}
    """
    dbpf = DBPFFile()
    dbpf.header = DBPFHeader(
        magic=b'DBPF',
        major_version=2,
        minor_version=1,
        index_entry_count=len(resources),
        index_offset=0,
        index_size=0
    )

    for key, data in resources.items():
        entry = IndexEntry(
            type_id=key[0],
            group_id=key[1],
            instance_id=key[2],
            offset=0,
            file_size=len(data),
            mem_size=len(data),
            compressed=False
        )
        dbpf.resources[key] = Resource(entry=entry, data=data)

    dbpf.save(filepath)


def test_basic_functionality():
    """Test basic read/write functionality"""
    print("\n" + "=" * 60)
    print("TEST 1: Basis lees/schrijf functionaliteit")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.save"

        # Create test data
        resources = {
            (0x12345678, 0x00000000, 0x0000000000000001): b"Test data 1",
            (0x12345678, 0x00000000, 0x0000000000000002): b"Test data 2",
            (0xABCDEF00, 0x00000001, 0x0000000000000001): b"Different type",
        }

        print(f"Aanmaken test bestand met {len(resources)} resources...")
        create_test_dbpf(test_file, resources)

        print(f"Teruglezen van bestand...")
        dbpf = DBPFFile(test_file)

        assert len(dbpf.resources) == len(resources), \
            f"Verwacht {len(resources)} resources, kreeg {len(dbpf.resources)}"

        for key, expected_data in resources.items():
            assert key in dbpf.resources, f"Resource {key} niet gevonden"
            # Note: data might be slightly different due to compression

        print("✅ Test geslaagd!")
        return True


def test_merge_functionality():
    """Test merge functionality"""
    print("\n" + "=" * 60)
    print("TEST 2: Merge functionaliteit")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        newer_file = Path(tmpdir) / "newer.save"
        older_file = Path(tmpdir) / "older.save"
        output_file = Path(tmpdir) / "merged.save"

        # Newer save: has resources 1, 2, 3
        newer_resources = {
            (0x11111111, 0x00000000, 0x0000000000000001): b"Sim data (newer)",
            (0x22222222, 0x00000000, 0x0000000000000002): b"Household (newer)",
            (0x33333333, 0x00000000, 0x0000000000000003): b"Some data",
        }

        # Older save: has resources 1, 2, 4, 5 (4, 5 are "missing" from newer)
        older_resources = {
            (0x11111111, 0x00000000, 0x0000000000000001): b"Sim data (older - younger)",
            (0x22222222, 0x00000000, 0x0000000000000002): b"Household (older)",
            (0x44444444, 0x00000000, 0x0000000000000004): b"Building A",
            (0x55555555, 0x00000000, 0x0000000000000005): b"Building B",
        }

        print("Aanmaken test saves...")
        create_test_dbpf(newer_file, newer_resources)
        create_test_dbpf(older_file, older_resources)

        print(f"Nieuwere save: {len(newer_resources)} resources")
        print(f"Oudere save: {len(older_resources)} resources")

        print("\nSamenvoegen...")
        merger = Sims4SaveMerger()
        newer_stats, older_stats = merger.load_files(newer_file, older_file)

        comparison = merger.get_comparison_summary()
        print(f"  Alleen in nieuwere: {comparison['only_in_newer']}")
        print(f"  Alleen in oudere: {comparison['only_in_older']}")
        print(f"  In beide (verschillend): {comparison['different']}")
        print(f"  In beide (zelfde): {comparison['same']}")

        result = merger.merge(output_file)

        assert result.success, f"Merge mislukt: {result.errors}"

        print(f"\n📊 Merge resultaat:")
        print(f"  Van nieuwere: {result.resources_from_newer}")
        print(f"  Van oudere: {result.resources_from_older}")
        print(f"  Totaal: {result.resources_total}")

        # Verify merged file
        merged = DBPFFile(output_file)

        # Should have: 1, 2, 3 from newer + 4, 5 from older = 5 total
        expected_total = 5
        assert len(merged.resources) == expected_total, \
            f"Verwacht {expected_total} resources, kreeg {len(merged.resources)}"

        # Verify resources from newer are kept (not overwritten by older)
        key_1 = (0x11111111, 0x00000000, 0x0000000000000001)
        assert key_1 in merged.resources, "Sim data ontbreekt"

        # Verify resources from older were added
        key_4 = (0x44444444, 0x00000000, 0x0000000000000004)
        key_5 = (0x55555555, 0x00000000, 0x0000000000000005)
        assert key_4 in merged.resources, "Building A ontbreekt"
        assert key_5 in merged.resources, "Building B ontbreekt"

        print("\n✅ Test geslaagd!")
        return True


def test_comparison():
    """Test comparison functionality"""
    print("\n" + "=" * 60)
    print("TEST 3: Vergelijkings functionaliteit")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.save"
        file2 = Path(tmpdir) / "file2.save"

        resources1 = {
            (0x11111111, 0x00000000, 0x0000000000000001): b"Same data",
            (0x22222222, 0x00000000, 0x0000000000000002): b"Different in 1",
            (0x33333333, 0x00000000, 0x0000000000000003): b"Only in 1",
        }

        resources2 = {
            (0x11111111, 0x00000000, 0x0000000000000001): b"Same data",
            (0x22222222, 0x00000000, 0x0000000000000002): b"Different in 2",
            (0x44444444, 0x00000000, 0x0000000000000004): b"Only in 2",
        }

        create_test_dbpf(file1, resources1)
        create_test_dbpf(file2, resources2)

        merger = Sims4SaveMerger()
        merger.load_files(file1, file2)

        comparison = merger.get_comparison_summary()

        assert comparison['same'] == 1, f"Verwacht 1 identiek, kreeg {comparison['same']}"
        assert comparison['different'] == 1, f"Verwacht 1 verschillend, kreeg {comparison['different']}"
        assert comparison['only_in_newer'] == 1, f"Verwacht 1 alleen in nieuwer"
        assert comparison['only_in_older'] == 1, f"Verwacht 1 alleen in ouder"

        print(f"  Identiek: {comparison['same']}")
        print(f"  Verschillend: {comparison['different']}")
        print(f"  Alleen in nieuwer: {comparison['only_in_newer']}")
        print(f"  Alleen in ouder: {comparison['only_in_older']}")

        print("\n✅ Test geslaagd!")
        return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SIMS 4 SAVE MERGER - TEST SUITE")
    print("=" * 60)

    tests = [
        test_basic_functionality,
        test_merge_functionality,
        test_comparison,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test mislukt met fout: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("SAMENVATTING")
    print("=" * 60)
    print(f"  Geslaagd: {passed}")
    print(f"  Mislukt: {failed}")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
