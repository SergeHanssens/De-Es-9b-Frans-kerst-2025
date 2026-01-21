"""
Command Line Interface for Sims 4 Save Merger

Usage:
    python -m sims4_save_merger.cli <newer_save> <older_save> <output_save>

Or:
    python -m sims4_save_merger.cli --analyze <save_file>
"""

import argparse
import sys
from pathlib import Path

from .dbpf_parser import DBPFFile, compare_files
from .merger import Sims4SaveMerger, MergeStrategy


def print_progress(message: str, percent: int):
    """Print progress to console"""
    if percent >= 0:
        print(f"[{percent:3d}%] {message}")
    else:
        print(f"       {message}")


def analyze_single(filepath: str):
    """Analyze a single save file"""
    print(f"\nAnalyseren van: {filepath}")
    print("=" * 60)

    try:
        dbpf = DBPFFile(Path(filepath))
        stats = dbpf.get_statistics()

        print(f"\nBestand: {Path(filepath).name}")
        print(f"DBPF Versie: {stats['version']}")
        print(f"Aantal resources: {stats['resource_count']}")
        print(f"Totale grootte: {stats['total_size'] / 1024 / 1024:.2f} MB")

        print("\nResources per type:")
        for type_name, count in sorted(stats['type_counts'].items()):
            print(f"  • {type_name}: {count}")

    except Exception as e:
        print(f"Fout: {e}")
        return 1

    return 0


def analyze_compare(newer_path: str, older_path: str):
    """Compare two save files"""
    print("\nVergelijken van save bestanden...")
    print("=" * 60)

    try:
        merger = Sims4SaveMerger(print_progress)
        newer_stats, older_stats = merger.load_files(
            Path(newer_path),
            Path(older_path)
        )

        comparison = merger.get_comparison_summary()

        print(f"\n📁 Nieuwere save: {Path(newer_path).name}")
        print(f"   Resources: {newer_stats['resource_count']}")
        print(f"   Grootte: {newer_stats['total_size'] / 1024 / 1024:.2f} MB")

        print(f"\n📁 Oudere save: {Path(older_path).name}")
        print(f"   Resources: {older_stats['resource_count']}")
        print(f"   Grootte: {older_stats['total_size'] / 1024 / 1024:.2f} MB")

        print("\n" + "=" * 60)
        print("VERGELIJKING")
        print("=" * 60)

        print(f"\n✅ Identiek in beide:     {comparison['same']}")
        print(f"🔄 Verschillend:          {comparison['different']}")
        print(f"📌 Alleen in nieuwere:    {comparison['only_in_newer']}")
        print(f"📌 Alleen in oudere:      {comparison['only_in_older']}")

        if comparison['only_older_by_type']:
            print("\nResources die toegevoegd kunnen worden:")
            for type_name, count in sorted(comparison['only_older_by_type'].items()):
                print(f"   • {type_name}: {count}")

    except Exception as e:
        print(f"Fout: {e}")
        return 1

    return 0


def merge_files(newer_path: str, older_path: str, output_path: str, force: bool = False):
    """Merge two save files"""
    print("\n🎮 Sims 4 Save Merger")
    print("=" * 60)

    # Check if output exists
    output = Path(output_path)
    if output.exists() and not force:
        response = input(f"\n⚠️ Output bestand bestaat al: {output_path}\nOverschrijven? (j/n): ")
        if response.lower() not in ['j', 'ja', 'y', 'yes']:
            print("Geannuleerd.")
            return 0

    try:
        merger = Sims4SaveMerger(print_progress)

        print(f"\n📂 Nieuwere save laden: {newer_path}")
        print(f"📂 Oudere save laden: {older_path}")

        newer_stats, older_stats = merger.load_files(
            Path(newer_path),
            Path(older_path)
        )

        comparison = merger.get_comparison_summary()

        print(f"\n📊 Analyse:")
        print(f"   Resources in nieuwere: {newer_stats['resource_count']}")
        print(f"   Resources toe te voegen: {comparison['resources_to_add']}")

        print(f"\n🔀 Samenvoegen naar: {output_path}")

        result = merger.merge(
            Path(output_path),
            MergeStrategy.NEWER_BASE_ADD_MISSING
        )

        if result.success:
            print("\n" + "=" * 60)
            print("✅ SAMENVOEGEN SUCCESVOL")
            print("=" * 60)
            print(f"\n📊 Resultaat:")
            print(f"   Resources van nieuwere save: {result.resources_from_newer}")
            print(f"   Resources van oudere save:   {result.resources_from_older}")
            print(f"   Totaal resources:            {result.resources_total}")
            print(f"\n📁 Opgeslagen naar: {result.output_file}")

            if result.warnings:
                print("\n⚠️ Waarschuwingen:")
                for warning in result.warnings:
                    print(f"   • {warning}")

            return 0
        else:
            print("\n❌ SAMENVOEGEN MISLUKT")
            for error in result.errors:
                print(f"   Fout: {error}")
            return 1

    except Exception as e:
        print(f"\n❌ Fout: {e}")
        return 1


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Sims 4 Save File Merger - Combineer twee save bestanden',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  Analyseer een save bestand:
    python -m sims4_save_merger.cli --analyze mysave.save

  Vergelijk twee save bestanden:
    python -m sims4_save_merger.cli --compare nieuwer.save ouder.save

  Voeg twee saves samen:
    python -m sims4_save_merger.cli nieuwer.save ouder.save merged.save

  Met --force om zonder bevestiging te overschrijven:
    python -m sims4_save_merger.cli -f nieuwer.save ouder.save merged.save
"""
    )

    parser.add_argument(
        '--analyze', '-a',
        metavar='FILE',
        help='Analyseer een enkel save bestand'
    )

    parser.add_argument(
        '--compare', '-c',
        nargs=2,
        metavar=('NEWER', 'OLDER'),
        help='Vergelijk twee save bestanden'
    )

    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Overschrijf output zonder te vragen'
    )

    parser.add_argument(
        '--gui', '-g',
        action='store_true',
        help='Start de grafische interface'
    )

    parser.add_argument(
        'files',
        nargs='*',
        metavar='FILE',
        help='Save bestanden: <nieuwer> <ouder> <output>'
    )

    args = parser.parse_args()

    # Start GUI if requested
    if args.gui:
        from .gui import main as gui_main
        gui_main()
        return 0

    # Analyze single file
    if args.analyze:
        return analyze_single(args.analyze)

    # Compare two files
    if args.compare:
        return analyze_compare(args.compare[0], args.compare[1])

    # Merge files
    if len(args.files) == 3:
        return merge_files(
            args.files[0],
            args.files[1],
            args.files[2],
            args.force
        )

    # No valid action
    if len(args.files) > 0 and len(args.files) < 3:
        print("Fout: Voor samenvoegen heb je 3 bestanden nodig: <nieuwer> <ouder> <output>")
        return 1

    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
