"""
Main entry point for running the Sims 4 Save Merger

Usage:
    python -m sims4_save_merger         # Start GUI
    python -m sims4_save_merger --cli   # Start CLI with no args (shows help)
"""

import sys


def main():
    """Main entry point - start GUI by default, CLI if args provided"""
    # If command line arguments are provided (other than the script name),
    # use the CLI
    if len(sys.argv) > 1:
        from .cli import main as cli_main
        sys.exit(cli_main())
    else:
        # Default to GUI
        try:
            from .gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"Kon GUI niet starten: {e}")
            print("Probeer de CLI met: python -m sims4_save_merger.cli --help")
            sys.exit(1)
        except Exception as e:
            print(f"Fout bij starten GUI: {e}")
            print("Probeer de CLI met: python -m sims4_save_merger.cli --help")
            sys.exit(1)


if __name__ == '__main__':
    main()
