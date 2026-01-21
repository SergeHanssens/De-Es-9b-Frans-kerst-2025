"""
Sims 4 Save Merger

A tool to merge two The Sims 4 save files, combining resources from
a newer save (with up-to-date Sim progress) and an older save
(with buildings and objects that may be missing).

Usage:
    # GUI
    python -m sims4_save_merger

    # CLI
    python -m sims4_save_merger.cli newer.save older.save output.save

    # Python API
    from sims4_save_merger import merge_saves
    result = merge_saves('newer.save', 'older.save', 'output.save')
"""

__version__ = '1.0.0'
__author__ = 'Sims 4 Save Merger Team'

from .dbpf_parser import DBPFFile, DBPFHeader, IndexEntry, Resource
from .merger import (
    Sims4SaveMerger,
    MergeStrategy,
    MergeResult,
    merge_saves
)

__all__ = [
    'DBPFFile',
    'DBPFHeader',
    'IndexEntry',
    'Resource',
    'Sims4SaveMerger',
    'MergeStrategy',
    'MergeResult',
    'merge_saves',
]
