"""
Module 05: IR Diffing and Change Detection

Detects and classifies changes between IR artifacts for ABI evolution tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .ir_entities import (
    FunctionSymbol,
    IREntity,
    StructureType,
    TypeEntity,
    UnionType,
    VariableSymbol,
)
from .ir_serialization import IRArtifact

# ============================================================================
# CHANGE CLASSIFICATION
# ============================================================================

class ABIImpact(Enum):
    """ABI impact classification."""
    BREAKING = "breaking"      # Requires recompilation / Breaks binary compatibility
    COMPATIBLE = "compatible"  # Backward compatible addition
    NEUTRAL = "neutral"        # No impact on binary interface

class ChangeKind(Enum):
    """Type of change detected."""
    # Entity-level
    ENTITY_ADDED = "entity_added"
    ENTITY_REMOVED = "entity_removed"

    # Structure/Type changes
    SIZE_CHANGED = "size_changed"
    ALIGNMENT_CHANGED = "alignment_changed"
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_OFFSET_CHANGED = "field_offset_changed"
    FIELD_TYPE_CHANGED = "field_type_changed"
    FIELD_SIZE_CHANGED = "field_size_changed"
    FIELD_REORDERED = "field_reordered"

    # Function changes
    CALLING_CONVENTION_CHANGED = "calling_convention_changed"
    RETURN_TYPE_CHANGED = "return_type_changed"
    PARAMETER_COUNT_CHANGED = "parameter_count_changed"
    PARAMETER_TYPE_CHANGED = "parameter_type_changed"
    PARAMETER_NAME_CHANGED = "parameter_name_changed"
    VARIADIC_CHANGED = "variadic_changed"

    # Variable changes
    VARIABLE_TYPE_CHANGED = "variable_type_changed"
    CONSTNESS_CHANGED = "constness_changed"

class VersionBump(Enum):
    """Recommended semantic version bump."""
    MAJOR = "major"  # X.0.0
    MINOR = "minor"  # 0.X.0
    PATCH = "patch"  # 0.0.X
    NONE = "none"

# ============================================================================
# CHANGE REPRESENTATION
# ============================================================================

@dataclass
class Change:
    """Represents a single semantic change between entities."""
    kind: ChangeKind
    description: str
    abi_impact: ABIImpact
    entity_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize change to dictionary."""
        return {
            'kind': self.kind.value,
            'description': self.description,
            'abi_impact': self.abi_impact.value,
            'entity_id': self.entity_id
        }

# ============================================================================
# IR DIFF
# ============================================================================

@dataclass
class IRDiff:
    """Complete semantic diff between two IR artifacts."""

    old_version: str = "0.0.0"
    new_version: str = "0.0.0"

    added_entities: List[IREntity] = field(default_factory=list)
    removed_entities: List[IREntity] = field(default_factory=list)
    modified_entities: List[Dict[str, Any]] = field(default_factory=list)

    breaking_changes: List[Change] = field(default_factory=list)
    compatible_changes: List[Change] = field(default_factory=list)
    neutral_changes: List[Change] = field(default_factory=list)

    overall_impact: ABIImpact = ABIImpact.NEUTRAL

    def has_breaking_changes(self) -> bool:
        return len(self.breaking_changes) > 0

    def has_compatible_changes(self) -> bool:
        return len(self.compatible_changes) > 0

    def has_neutral_changes(self) -> bool:
        return len(self.neutral_changes) > 0

    def total_changes(self) -> int:
        return (len(self.breaking_changes) +
                len(self.compatible_changes) +
                len(self.neutral_changes))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize diff for persistence."""
        return {
            'old_version': self.old_version,
            'new_version': self.new_version,
            'added_count': len(self.added_entities),
            'removed_count': len(self.removed_entities),
            'modified_count': len(self.modified_entities),
            'breaking_changes': [c.to_dict() for c in self.breaking_changes],
            'compatible_changes': [c.to_dict() for c in self.compatible_changes],
            'neutral_changes': [c.to_dict() for c in self.neutral_changes],
            'overall_impact': self.overall_impact.value,
            'total_changes': self.total_changes()
        }

# ============================================================================
# DIFF COMPUTER
# ============================================================================

class IRDiffComputer:
    """Computes semantic differences and ABI impact between IR artifacts."""

    def compute_diff(
        self,
        old_artifact: IRArtifact,
        new_artifact: IRArtifact
    ) -> IRDiff:
        """Compute complete diff between two artifacts."""
        diff = IRDiff()
        diff.old_version = old_artifact.normalization_version
        diff.new_version = new_artifact.normalization_version

        # Build entity maps by ID for matching
        old_map = self._build_entity_map(old_artifact)
        new_map = self._build_entity_map(new_artifact)

        old_ids = set(old_map.keys())
        new_ids = set(new_map.keys())

        # Added entities
        for eid in sorted(new_ids - old_ids):
            entity = new_map[eid]
            diff.added_entities.append(entity)
            change = Change(
                kind=ChangeKind.ENTITY_ADDED,
                description=f"Added {entity.kind.value}: {eid}",
                abi_impact=ABIImpact.COMPATIBLE, # Additions are usually compatible
                entity_id=eid
            )
            diff.compatible_changes.append(change)

        # Removed entities
        for eid in sorted(old_ids - new_ids):
            entity = old_map[eid]
            diff.removed_entities.append(entity)
            change = Change(
                kind=ChangeKind.ENTITY_REMOVED,
                description=f"Removed {entity.kind.value}: {eid}",
                abi_impact=ABIImpact.BREAKING, # Removals are breaking
                entity_id=eid
            )
            diff.breaking_changes.append(change)

        # Modified entities
        for eid in sorted(old_ids & new_ids):
            old_e = old_map[eid]
            new_e = new_map[eid]

            changes = self._detect_entity_changes(old_e, new_e)
            if changes:
                diff.modified_entities.append({
                    'entity_id': eid,
                    'changes': [c.to_dict() for c in changes]
                })

                for c in changes:
                    if c.abi_impact == ABIImpact.BREAKING:
                        diff.breaking_changes.append(c)
                    elif c.abi_impact == ABIImpact.COMPATIBLE:
                        diff.compatible_changes.append(c)
                    else:
                        diff.neutral_changes.append(c)

        # Determine overall impact
        if diff.has_breaking_changes():
            diff.overall_impact = ABIImpact.BREAKING
        elif diff.has_compatible_changes():
            diff.overall_impact = ABIImpact.COMPATIBLE
        else:
            diff.overall_impact = ABIImpact.NEUTRAL

        return diff

    def _build_entity_map(self, artifact: IRArtifact) -> Dict[str, IREntity]:
        entity_map = {}
        if not artifact.interface_unit:
            return entity_map

        for symbol in artifact.interface_unit.symbols:
            entity_map[symbol.entity_id] = symbol
        for type_e in artifact.interface_unit.types:
            entity_map[type_e.entity_id] = type_e

        return entity_map

    def _detect_entity_changes(self, old: IREntity, new: IREntity) -> List[Change]:
        """Dispatch change detection based on entity class."""
        if type(old) != type(new):
            # This should theoretically not happen if IDs are stable and based on kind
            return [Change(
                kind=ChangeKind.ENTITY_REMOVED, # Effectively a swap
                description=f"Entity kind changed from {old.kind.value} to {new.kind.value}",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            )]

        if isinstance(old, StructureType):
            return self._diff_structures(old, new)
        elif isinstance(old, UnionType):
            return self._diff_unions(old, new)
        elif isinstance(old, FunctionSymbol):
            return self._diff_functions(old, new)
        elif isinstance(old, VariableSymbol):
            return self._diff_variables(old, new)
        elif isinstance(old, TypeEntity):
            return self._diff_base_types(old, new)

        return []

    def _diff_base_types(self, old: TypeEntity, new: TypeEntity) -> List[Change]:
        changes = []
        if old.size_bytes != new.size_bytes:
            changes.append(Change(
                kind=ChangeKind.SIZE_CHANGED,
                description=f"Size changed from {old.size_bytes} to {new.size_bytes}",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))
        if old.alignment_bytes != new.alignment_bytes:
            changes.append(Change(
                kind=ChangeKind.ALIGNMENT_CHANGED,
                description=f"Alignment changed from {old.alignment_bytes} to {new.alignment_bytes}",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))
        return changes

    def _diff_structures(self, old: StructureType, new: StructureType) -> List[Change]:
        changes = self._diff_base_types(old, new)

        # Diff fields by name (semantic matching)
        old_fields = {f.field_name: f for f in old.fields if f.field_name}
        new_fields = {f.field_name: f for f in new.fields if f.field_name}

        # Added/Removed named fields
        for name in sorted(new_fields.keys() - old_fields.keys()):
            changes.append(Change(
                kind=ChangeKind.FIELD_ADDED,
                description=f"Field '{name}' added",
                abi_impact=ABIImpact.BREAKING, # Struct field addition usually breaks layout
                entity_id=old.entity_id
            ))
        for name in sorted(old_fields.keys() - new_fields.keys()):
            changes.append(Change(
                kind=ChangeKind.FIELD_REMOVED,
                description=f"Field '{name}' removed",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))

        # Field properties
        for name in sorted(old_fields.keys() & new_fields.keys()):
            of = old_fields[name]
            nf = new_fields[name]

            if of.byte_offset != nf.byte_offset:
                changes.append(Change(
                    kind=ChangeKind.FIELD_OFFSET_CHANGED,
                    description=f"Field '{name}' offset changed from {of.byte_offset} to {nf.byte_offset}",
                    abi_impact=ABIImpact.BREAKING,
                    entity_id=old.entity_id
                ))
            if of.type_reference != nf.type_reference:
                changes.append(Change(
                    kind=ChangeKind.FIELD_TYPE_CHANGED,
                    description=f"Field '{name}' type reference changed",
                    abi_impact=ABIImpact.BREAKING,
                    entity_id=old.entity_id
                ))

        # Check reordering of named fields
        old_order = [f.field_name for f in old.fields if f.field_name]
        new_order = [f.field_name for f in new.fields if f.field_name]
        common = [n for n in old_order if n in new_fields]
        reordered = [n for n in new_order if n in old_fields]
        if common != reordered:
             changes.append(Change(
                kind=ChangeKind.FIELD_REORDERED,
                description="Structure fields were reordered",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))

        return changes

    def _diff_unions(self, old: UnionType, new: UnionType) -> List[Change]:
        changes = self._diff_base_types(old, new)
        # Similar to structs but offsets are always 0
        old_members = {m.field_name: m for m in old.members if m.field_name}
        new_members = {m.field_name: m for m in new.members if m.field_name}

        for name in sorted(new_members.keys() - old_members.keys()):
            changes.append(Change(
                kind=ChangeKind.FIELD_ADDED,
                description=f"Union member '{name}' added",
                abi_impact=ABIImpact.COMPATIBLE, # Adding union member is often compatible if size doesn't change
                entity_id=old.entity_id
            ))
        for name in sorted(old_members.keys() - new_members.keys()):
            changes.append(Change(
                kind=ChangeKind.FIELD_REMOVED,
                description=f"Union member '{name}' removed",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))
        return changes

    def _diff_functions(self, old: FunctionSymbol, new: FunctionSymbol) -> List[Change]:
        changes = []
        if old.calling_convention != new.calling_convention:
            changes.append(Change(
                kind=ChangeKind.CALLING_CONVENTION_CHANGED,
                description=f"Calling convention changed from {old.calling_convention.value} to {new.calling_convention.value}",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))

        if old.return_entity and new.return_entity:
            new_entity = new.return_entity
            if old.return_entity.type_reference != new_entity.type_reference:
                changes.append(Change(
                    kind=ChangeKind.RETURN_TYPE_CHANGED,
                    description="Return type changed",
                    abi_impact=ABIImpact.BREAKING,
                    entity_id=old.entity_id
                ))

        if len(old.parameters) != len(new.parameters):
            changes.append(Change(
                kind=ChangeKind.PARAMETER_COUNT_CHANGED,
                description=f"Parameter count changed from {len(old.parameters)} to {len(new.parameters)}",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))
        else:
            for i, (op, np) in enumerate(zip(old.parameters, new.parameters)):
                if op.type_reference != np.type_reference:
                    changes.append(Change(
                        kind=ChangeKind.PARAMETER_TYPE_CHANGED,
                        description=f"Parameter {i} type changed",
                        abi_impact=ABIImpact.BREAKING,
                        entity_id=old.entity_id
                    ))
                if op.parameter_name != np.parameter_name:
                    changes.append(Change(
                        kind=ChangeKind.PARAMETER_NAME_CHANGED,
                        description=f"Parameter {i} name changed from '{op.parameter_name}' to '{np.parameter_name}'",
                        abi_impact=ABIImpact.NEUTRAL,
                        entity_id=old.entity_id
                    ))

        if old.is_variadic != new.is_variadic:
            changes.append(Change(
                kind=ChangeKind.VARIADIC_CHANGED,
                description="Variadic status changed",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))

        return changes

    def _diff_variables(self, old: VariableSymbol, new: VariableSymbol) -> List[Change]:
        changes = []
        if old.type_reference != new.type_reference:
            changes.append(Change(
                kind=ChangeKind.VARIABLE_TYPE_CHANGED,
                description="Variable type reference changed",
                abi_impact=ABIImpact.BREAKING,
                entity_id=old.entity_id
            ))
        if old.is_const != new.is_const:
            changes.append(Change(
                kind=ChangeKind.CONSTNESS_CHANGED,
                description=f"Constness changed to {new.is_const}",
                abi_impact=ABIImpact.BREAKING, # Sometimes breaking depending on platform/language
                entity_id=old.entity_id
            ))
        return changes

# ============================================================================
# CHANGE SUMMARY
# ============================================================================

class Change
    """Generates human-readable summaries of IR differences."""

    def __init__(self, diff: IRDiff):
        self.diff = diff

    def generate_summary(self) -> str:
        """Produce a formatted text report of all changes and their impact."""
        lines = []
        lines.append("=" * 80)
        lines.append("IR CHANGE DETECTION REPORT")
        lines.append(f"Versions: {self.diff.old_version} -> {self.diff.new_version}")
        lines.append(f"Overall Impact: {self.diff.overall_impact.value.upper()}")
        lines.append("=" * 80)

        lines.append("\nSUMMARY STATISTICS:")
        lines.append(f"  Added entities:    {len(self.diff.added_entities)}")
        lines.append(f"  Removed entities:  {len(self.diff.removed_entities)}")
        lines.append(f"  Modified entities: {len(self.diff.modified_entities)}")
        lines.append(f"  Total changes:     {self.diff.total_changes()}")

        if self.diff.breaking_changes:
            lines.append("\nBREAKING CHANGES:")
            for c in self.diff.breaking_changes:
                lines.append(f"  [!] {c.description} (Entity: {c.entity_id})")

        if self.diff.compatible_changes:
            lines.append("\nCOMPATIBLE CHANGES:")
            for c in self.diff.compatible_changes:
                if c.kind != ChangeKind.ENTITY_ADDED: # Filter noisy additions if desired
                    lines.append(f"  [+] {c.description} (Entity: {c.entity_id})")
                else:
                    lines.append(f"  [+] {c.description}")

        if self.diff.neutral_changes:
            lines.append("\nNEUTRAL CHANGES:")
            for c in self.diff.neutral_changes:
                lines.append(f"  [*] {c.description}")

        return "\n".join(lines)

# ============================================================================
# VERSION RECOMMENDATION
# ============================================================================

def recommend_version_bump(diff: IRDiff) -> VersionBump:
    """Determine the required semantic version bump based on observed changes."""
    if diff.has_breaking_changes():
        return VersionBump.MAJOR

    if diff.has_compatible_changes():
        return VersionBump.MINOR

    if diff.has_neutral_changes():
        return VersionBump.PATCH

    return VersionBump.NONE

__all__ = [
    'ABIImpact',
    'ChangeKind',
    'VersionBump',
    'Change',
    'IRDiff',
    'IRDiffComputer',
    'ChangeSummary',
    'recommend_version_bump'
]
