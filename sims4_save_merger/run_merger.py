#!/usr/bin/env python3
"""
Sims 4 Save Merger - Launcher Script

Dit script start de grafische interface van de Sims 4 Save Merger.
Dubbelklik op dit bestand om de applicatie te starten.

Alternatief:
    python run_merger.py          # Start GUI
    python run_merger.py --help   # Toon CLI help
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # CLI mode
        from sims4_save_merger.cli import main
        sys.exit(main())
    else:
        # GUI mode
        from sims4_save_merger.gui import main
        main()
