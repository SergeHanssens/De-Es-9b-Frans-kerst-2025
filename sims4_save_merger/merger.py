"""
Sims 4 Save File Merger

This module provides functionality to merge two Sims 4 save files,
taking the newer save as the base and adding missing resources from
the older save.

The merge strategy:
1. Use the newer save as the base (Sim ages, relationships, etc.)
2. Add any resources from the older save that are missing in the newer save
   (buildings, lots, objects that weren't saved properly)
3. Optionally allow selection of specific resources to include
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import shutil
from datetime import datetime

from .dbpf_parser import DBPFFile, Resource, compare_files


class MergeStrategy(Enum):
    """Available merge strategies"""
    NEWER_BASE_ADD_MISSING = "newer_base_add_missing"  # Default: newer + missing from older
    OLDER_BASE_ADD_NEWER = "older_base_add_newer"      # Older + updates from newer
    SMART_MERGE = "smart_merge"                        # Smart: use larger version for lot data
    PREFER_LARGER = "prefer_larger"                    # Always use larger version for ALL conflicts
    WORKING_BASE = "working_base"                      # Use working/older as base, only update sim data from newer
    MANUAL_SELECT = "manual_select"                    # User selects each resource


@dataclass
class MergeResult:
    """Result of a merge operation"""
    success: bool
    output_file: Optional[Path]
    resources_from_newer: int
    resources_from_older: int
    resources_total: int
    errors: List[str]
    warnings: List[str]


@dataclass
class ResourceInfo:
    """Information about a resource for display"""
    key: Tuple[int, int, int]
    key_hex: str
    type_name: str
    size: int
    source: str  # 'newer', 'older', or 'both'


class Sims4SaveMerger:
    """
    Merges two Sims 4 save files

    The typical use case:
    - newer_save: A more recent save where Sims are older but some data is missing
    - older_save: An older save with all the buildings/lots intact

    The merger will create a new save with:
    - All data from the newer save (keeping Sim progress)
    - Missing data from the older save (restoring buildings/lots)
    """

    # Resource types that typically contain Sim-related data (use from newer)
    SIM_RELATED_TYPES = {
        0xC0DB5AE7,  # SimInfo
        0xB61DE6B4,  # Household
        0x0C772E27,  # RelationshipData
        0x3BD45407,  # Situation
        0x0000000D,  # Sim-related game data
        0x0000000F,  # Game state data
        0x00000014,  # Achievement/progress data
        0x00000015,  # Skills/relationships data
    }

    # Resource types that typically contain world/lot data (may need from older)
    WORLD_RELATED_TYPES = {
        0xE882D22F,  # Lot
        0xDC95CF1A,  # Zone
        0x62ECC59A,  # ObjectData
        0x00000006,  # Zone/Lot data (contains buildings!)
    }

    # Minimum size threshold - if newer is smaller than this, likely corrupted/empty
    MIN_LOT_SIZE = 100  # bytes

    def __init__(self, progress_callback: Optional[Callable[[str, int], None]] = None):
        """
        Initialize the merger

        Args:
            progress_callback: Optional function(message, percent) for progress updates
        """
        self.progress_callback = progress_callback
        self.newer_file: Optional[DBPFFile] = None
        self.older_file: Optional[DBPFFile] = None
        self._comparison: Optional[Dict] = None

    def _report_progress(self, message: str, percent: int = -1):
        """Report progress to callback if set"""
        if self.progress_callback:
            self.progress_callback(message, percent)

    def load_files(self, newer_path: Path, older_path: Path) -> Tuple[Dict, Dict]:
        """
        Load both save files and analyze them

        Args:
            newer_path: Path to the newer save file
            older_path: Path to the older save file

        Returns:
            Tuple of (newer_stats, older_stats)
        """
        self._report_progress("Laden van nieuwere save...", 0)
        self.newer_file = DBPFFile(newer_path)

        self._report_progress("Laden van oudere save...", 25)
        self.older_file = DBPFFile(older_path)

        self._report_progress("Vergelijken van bestanden...", 50)
        self._comparison = compare_files(self.newer_file, self.older_file)

        self._report_progress("Analyse voltooid", 100)

        return (
            self.newer_file.get_statistics(),
            self.older_file.get_statistics()
        )

    def get_comparison_summary(self) -> Dict:
        """
        Get a summary of differences between the files

        Returns:
            Dict with comparison information
        """
        if not self._comparison:
            raise ValueError("Files not loaded. Call load_files first.")

        # Count by type
        only_newer_types = {}
        only_older_types = {}
        different_types = {}

        for key in self._comparison['only_in_file1']:
            type_name = self.newer_file.get_resource_type_name(key[0])
            only_newer_types[type_name] = only_newer_types.get(type_name, 0) + 1

        for key in self._comparison['only_in_file2']:
            type_name = self.older_file.get_resource_type_name(key[0])
            only_older_types[type_name] = only_older_types.get(type_name, 0) + 1

        for key in self._comparison['different']:
            type_name = self.newer_file.get_resource_type_name(key[0])
            different_types[type_name] = different_types.get(type_name, 0) + 1

        return {
            'only_in_newer': len(self._comparison['only_in_file1']),
            'only_in_older': len(self._comparison['only_in_file2']),
            'same': len(self._comparison['same']),
            'different': len(self._comparison['different']),
            'only_newer_by_type': only_newer_types,
            'only_older_by_type': only_older_types,
            'different_by_type': different_types,
            'resources_to_add': len(self._comparison['only_in_file2']),
        }

    def get_mergeable_resources(self) -> List[ResourceInfo]:
        """
        Get list of resources that could be added from the older save

        Returns:
            List of ResourceInfo for resources only in older save
        """
        if not self._comparison:
            raise ValueError("Files not loaded. Call load_files first.")

        resources = []

        # Resources only in older save (can be added)
        for key in self._comparison['only_in_file2']:
            resource = self.older_file.resources[key]
            resources.append(ResourceInfo(
                key=key,
                key_hex=resource.key_hex,
                type_name=self.older_file.get_resource_type_name(key[0]),
                size=len(resource.data),
                source='older'
            ))

        return sorted(resources, key=lambda r: (r.type_name, r.key))

    def _detect_empty_resources(self) -> Set[Tuple[int, int, int]]:
        """
        Detect resources in newer save that appear empty/corrupted compared to older save.

        Returns:
            Set of keys for resources where older version should be used
        """
        empty_resources = set()

        if not self._comparison:
            return empty_resources

        for key in self._comparison['different']:
            newer_resource = self.newer_file.resources[key]
            older_resource = self.older_file.resources[key]

            newer_size = len(newer_resource.data)
            older_size = len(older_resource.data)

            # Check if this is a world/lot resource type
            type_id = key[0]

            # For lot data (type 0x00000006), if newer is tiny but older is large,
            # the newer version is likely corrupted/empty
            if type_id == 0x00000006:
                # More aggressive: if older is at least 10x larger, use older
                if older_size > newer_size * 10:
                    empty_resources.add(key)
                # Also if newer is very small (<2KB) and older is significantly larger
                elif newer_size < 2000 and older_size > newer_size * 5:
                    empty_resources.add(key)

            # For other world-related types, use similar logic
            elif type_id in self.WORLD_RELATED_TYPES:
                if newer_size < 100 and older_size > newer_size * 5:
                    empty_resources.add(key)

            # General rule: if newer is less than 5% of older size, it's likely empty
            elif older_size > 1000 and newer_size < older_size * 0.05:
                empty_resources.add(key)

        return empty_resources

    def _get_larger_resources(self) -> Set[Tuple[int, int, int]]:
        """
        Get all resources where the older version is larger.

        Returns:
            Set of keys where older version is larger
        """
        larger = set()

        if not self._comparison:
            return larger

        for key in self._comparison['different']:
            newer_size = len(self.newer_file.resources[key].data)
            older_size = len(self.older_file.resources[key].data)

            if older_size > newer_size:
                larger.add(key)

        return larger

    def get_smart_merge_candidates(self) -> List[Tuple[ResourceInfo, ResourceInfo]]:
        """
        Get list of resources that would be taken from older save in smart merge.

        Returns:
            List of (newer_info, older_info) tuples for resources that appear empty
        """
        candidates = []
        empty_keys = self._detect_empty_resources()

        for key in empty_keys:
            newer_resource = self.newer_file.resources[key]
            older_resource = self.older_file.resources[key]

            newer_info = ResourceInfo(
                key=key,
                key_hex=newer_resource.key_hex,
                type_name=self.newer_file.get_resource_type_name(key[0]),
                size=len(newer_resource.data),
                source='newer'
            )

            older_info = ResourceInfo(
                key=key,
                key_hex=older_resource.key_hex,
                type_name=self.older_file.get_resource_type_name(key[0]),
                size=len(older_resource.data),
                source='older'
            )

            candidates.append((newer_info, older_info))

        return sorted(candidates, key=lambda x: x[1].size - x[0].size, reverse=True)

    def get_conflicting_resources(self) -> List[Tuple[ResourceInfo, ResourceInfo]]:
        """
        Get list of resources that exist in both files but are different

        Returns:
            List of (newer_info, older_info) tuples
        """
        if not self._comparison:
            raise ValueError("Files not loaded. Call load_files first.")

        conflicts = []

        for key in self._comparison['different']:
            newer_resource = self.newer_file.resources[key]
            older_resource = self.older_file.resources[key]

            newer_info = ResourceInfo(
                key=key,
                key_hex=newer_resource.key_hex,
                type_name=self.newer_file.get_resource_type_name(key[0]),
                size=len(newer_resource.data),
                source='newer'
            )

            older_info = ResourceInfo(
                key=key,
                key_hex=older_resource.key_hex,
                type_name=self.older_file.get_resource_type_name(key[0]),
                size=len(older_resource.data),
                source='older'
            )

            conflicts.append((newer_info, older_info))

        return conflicts

    def merge(
        self,
        output_path: Path,
        strategy: MergeStrategy = MergeStrategy.NEWER_BASE_ADD_MISSING,
        resources_to_add: Optional[Set[Tuple[int, int, int]]] = None,
        resources_from_older: Optional[Set[Tuple[int, int, int]]] = None,
        create_backup: bool = True
    ) -> MergeResult:
        """
        Merge the two save files

        Args:
            output_path: Path for the merged save file
            strategy: Merge strategy to use
            resources_to_add: If set, only add these specific resources from older save
                            If None, add all missing resources
            resources_from_older: For conflicts, use older version for these keys
            create_backup: Create backup of output if it exists

        Returns:
            MergeResult with details about the merge
        """
        if not self.newer_file or not self.older_file or not self._comparison:
            raise ValueError("Files not loaded. Call load_files first.")

        errors = []
        warnings = []
        output_path = Path(output_path)

        # Create backup if needed
        if create_backup and output_path.exists():
            backup_path = output_path.with_suffix(
                f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.save'
            )
            shutil.copy2(output_path, backup_path)
            warnings.append(f"Backup gemaakt: {backup_path}")

        self._report_progress("Samenvoegen van bestanden...", 0)

        # Create new DBPF file
        merged = DBPFFile()
        merged.header = self.newer_file.header

        # Start with all resources from newer save
        resources_from_newer_count = 0
        resources_from_older_count = 0

        self._report_progress("Kopieren van nieuwere save resources...", 10)

        # Determine which resources should come from older save
        use_older_keys = set()

        if strategy == MergeStrategy.SMART_MERGE:
            # Smart merge: detect empty/corrupted resources
            use_older_keys = self._detect_empty_resources()
            if use_older_keys:
                warnings.append(f"Smart merge: {len(use_older_keys)} resources worden uit oudere save genomen (lege/corrupte detectie)")

        elif strategy == MergeStrategy.PREFER_LARGER:
            # Prefer larger: use older whenever it's bigger
            use_older_keys = self._get_larger_resources()
            if use_older_keys:
                warnings.append(f"Prefer larger: {len(use_older_keys)} resources worden uit oudere save genomen (grotere versie)")

        elif strategy == MergeStrategy.WORKING_BASE:
            # WORKING_BASE: Use older (working) save as the base
            # Only update sim-related resources from newer (corrupt) save
            warnings.append("Working base strategie: werkende save als basis, alleen sim-data van nieuwere")

            # Start with ALL resources from older (working) save
            for key, resource in self.older_file.resources.items():
                merged.resources[key] = resource
                resources_from_older_count += 1

            # Now ONLY update sim-related resources from newer save
            sim_updates = 0
            for key, resource in self.newer_file.resources.items():
                type_id = key[0]
                # Only use newer version for sim-related types
                if type_id in self.SIM_RELATED_TYPES:
                    merged.resources[key] = resource
                    resources_from_newer_count += 1
                    resources_from_older_count -= 1  # We're replacing
                    sim_updates += 1

            warnings.append(f"Updated {sim_updates} sim-gerelateerde resources van nieuwere save")

            # Add any new resources from newer that don't exist in older
            for key in self._comparison['only_in_file1']:
                if key not in merged.resources:
                    merged.resources[key] = self.newer_file.resources[key]
                    resources_from_newer_count += 1

            # Skip the normal resource loop for WORKING_BASE
            self._report_progress("Opslaan van samengevoegd bestand...", 80)

            try:
                merged.save(output_path)
            except Exception as e:
                errors.append(f"Fout bij opslaan: {str(e)}")
                return MergeResult(
                    success=False,
                    output_file=None,
                    resources_from_newer=resources_from_newer_count,
                    resources_from_older=resources_from_older_count,
                    resources_total=len(merged.resources),
                    errors=errors,
                    warnings=warnings
                )

            self._report_progress("Samenvoegen voltooid!", 100)

            return MergeResult(
                success=True,
                output_file=output_path,
                resources_from_newer=resources_from_newer_count,
                resources_from_older=resources_from_older_count,
                resources_total=len(merged.resources),
                errors=errors,
                warnings=warnings
            )

        for key, resource in self.newer_file.resources.items():
            # Check if we should use older version for conflicts
            use_older = False

            # Explicit override
            if resources_from_older and key in resources_from_older:
                use_older = True

            # Strategy-based selection
            if key in use_older_keys:
                use_older = True

            if use_older and key in self.older_file.resources:
                merged.resources[key] = self.older_file.resources[key]
                resources_from_older_count += 1
                continue

            merged.resources[key] = resource
            resources_from_newer_count += 1

        self._report_progress("Toevoegen van ontbrekende resources...", 50)

        # Determine which resources to add from older save
        if resources_to_add is not None:
            # Only add specified resources
            to_add = resources_to_add & self._comparison['only_in_file2']
        else:
            # Add all missing resources
            to_add = self._comparison['only_in_file2']

        # Add missing resources from older save
        for key in to_add:
            if key in self.older_file.resources:
                merged.resources[key] = self.older_file.resources[key]
                resources_from_older_count += 1

        self._report_progress("Opslaan van samengevoegd bestand...", 80)

        try:
            merged.save(output_path)
        except Exception as e:
            errors.append(f"Fout bij opslaan: {str(e)}")
            return MergeResult(
                success=False,
                output_file=None,
                resources_from_newer=resources_from_newer_count,
                resources_from_older=resources_from_older_count,
                resources_total=len(merged.resources),
                errors=errors,
                warnings=warnings
            )

        self._report_progress("Samenvoegen voltooid!", 100)

        return MergeResult(
            success=True,
            output_file=output_path,
            resources_from_newer=resources_from_newer_count,
            resources_from_older=resources_from_older_count,
            resources_total=len(merged.resources),
            errors=errors,
            warnings=warnings
        )

    def quick_merge(
        self,
        newer_path: Path,
        older_path: Path,
        output_path: Path,
        smart: bool = True
    ) -> MergeResult:
        """
        Perform a quick merge with default settings

        Takes newer save as base, adds all missing resources from older save.
        Uses SMART_MERGE by default to detect empty/corrupted resources.

        Args:
            newer_path: Path to newer save (base)
            older_path: Path to older save (source for missing data)
            output_path: Path for merged output
            smart: Use smart merge strategy (default True)

        Returns:
            MergeResult
        """
        self.load_files(newer_path, older_path)
        strategy = MergeStrategy.SMART_MERGE if smart else MergeStrategy.NEWER_BASE_ADD_MISSING
        return self.merge(output_path, strategy=strategy)


def merge_saves(
    newer_path: str,
    older_path: str,
    output_path: str,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> MergeResult:
    """
    Convenience function to merge two save files

    Args:
        newer_path: Path to newer save file
        older_path: Path to older save file
        output_path: Path for output file
        progress_callback: Optional progress callback

    Returns:
        MergeResult with merge details
    """
    merger = Sims4SaveMerger(progress_callback)
    return merger.quick_merge(
        Path(newer_path),
        Path(older_path),
        Path(output_path)
    )
