"""
Module 06: Contract Schema - Versioning & Evolution

Contract versioning system supporting:
    - Semantic versioning for contracts and schema
- Version history and changelog
- Compatibility assessment
- Contract diffing
- Deprecation support
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
from datetime import datetime
import re

from .contract_entities import ContractDocument, ContractClause, ClauseType

# ============================================================================
# VERSION TYPES
# ============================================================================


@dataclass
class SemanticVersion:
    """
    Semantic version (MAJOR.MINOR.PATCH).

    Supports comparison and compatibility checking.
    """

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return self.major == other.major and self.minor == other.minor and self.patch == other.patch

    def __lt__(self, other: "SemanticVersion") -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch

    def __le__(self, other: "SemanticVersion") -> bool:
        return self == other or self < other

    def __gt__(self, other: "SemanticVersion") -> bool:
        return not (self <= other)

    def __ge__(self, other: "SemanticVersion") -> bool:
        return not (self < other)

    def is_compatible_with(self, other: "SemanticVersion") -> bool:
        """
        Check if this version is backward compatible with other.

        Compatible if same MAJOR, and this >= other.
        """
        return self.major == other.major and self >= other

    @staticmethod
    def parse(version_str: str) -> "SemanticVersion":
        """Parse version string to SemanticVersion."""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_str}")

        return SemanticVersion(
            major=int(match.group(1)), minor=int(match.group(2)), patch=int(match.group(3))
        )

    def bump_major(self) -> "SemanticVersion":
        """Create new version with MAJOR bumped."""
        return SemanticVersion(self.major + 1, 0, 0)

    def bump_minor(self) -> "SemanticVersion":
        """Create new version with MINOR bumped."""
        return SemanticVersion(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "SemanticVersion":
        """Create new version with PATCH bumped."""
        return SemanticVersion(self.major, self.minor, self.patch + 1)


# ============================================================================
# CHANGE TYPES
# ============================================================================


class ChangeType(Enum):
    """Type of change in contract version."""

    CLAUSE_ADDED = "clause_added"
    CLAUSE_REMOVED = "clause_removed"
    CLAUSE_MODIFIED = "clause_modified"
    METADATA_UPDATED = "metadata_updated"


class CompatibilityImpact(Enum):
    """Impact of change on compatibility."""

    BREAKING = "breaking"  # Requires recompilation
    COMPATIBLE = "compatible"  # Backward compatible
    NEUTRAL = "neutral"  # No impact (metadata only)


@dataclass
class ContractChange:
    """Single change in contract version."""

    change_type: ChangeType
    impact: CompatibilityImpact
    clause_id: Optional[str] = None
    description: str = ""

    def is_breaking(self) -> bool:
        """Check if change is breaking."""
        return self.impact == CompatibilityImpact.BREAKING


# ============================================================================
# VERSION HISTORY
# ============================================================================


@dataclass
class VersionMetadata:
    """Metadata for contract version."""

    version: SemanticVersion
    created_timestamp: str
    author: Optional[str] = None
    commit_hash: Optional[str] = None
    release_notes: str = ""

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if not self.created_timestamp:
            self.created_timestamp = datetime.utcnow().isoformat()


@dataclass
class VersionHistoryEntry:
    """Entry in contract version history."""

    metadata: VersionMetadata
    changes: List[ContractChange] = field(default_factory=list)
    previous_version: Optional[SemanticVersion] = None
    compatibility_declaration: Optional[str] = None
    deprecated: bool = False
    deprecation_notice: Optional[str] = None

    def is_breaking_change(self) -> bool:
        """Check if any changes are breaking."""
        return any(c.is_breaking() for c in self.changes)

    def get_compatibility_impact(self) -> CompatibilityImpact:
        """Get overall compatibility impact."""
        if any(c.impact == CompatibilityImpact.BREAKING for c in self.changes):
            return CompatibilityImpact.BREAKING
        if any(c.impact == CompatibilityImpact.COMPATIBLE for c in self.changes):
            return CompatibilityImpact.COMPATIBLE
        return CompatibilityImpact.NEUTRAL


@dataclass
class VersionHistory:
    """Complete version history for contract."""

    entries: List[VersionHistoryEntry] = field(default_factory=list)

    def add_version(self, entry: VersionHistoryEntry):
        """Add version to history."""
        self.entries.append(entry)
        # Keep sorted by version
        self.entries.sort(key=lambda e: e.metadata.version)

    def get_version(self, version: SemanticVersion) -> Optional[VersionHistoryEntry]:
        """Get specific version entry."""
        for entry in self.entries:
            if entry.metadata.version == version:
                return entry
        return None

    def get_latest_version(self) -> Optional[VersionHistoryEntry]:
        """Get latest version."""
        if not self.entries:
            return None
        return self.entries[-1]

    def get_versions_between(
        self, start: SemanticVersion, end: SemanticVersion
    ) -> List[VersionHistoryEntry]:
        """Get all versions between start and end (inclusive)."""
        return [e for e in self.entries if start <= e.metadata.version <= end]


# ============================================================================
# CONTRACT DIFF
# ============================================================================


@dataclass
class ClauseComparison:
    """Comparison of single clause between versions."""

    clause_id: str
    old_clause: Optional[ContractClause]
    new_clause: Optional[ContractClause]
    change_type: ChangeType
    impact: CompatibilityImpact
    differences: List[str] = field(default_factory=list)


@dataclass
class ContractDiff:
    """Diff between two contract versions."""

    old_version: SemanticVersion
    new_version: SemanticVersion

    added_clauses: List[str] = field(default_factory=list)
    removed_clauses: List[str] = field(default_factory=list)
    modified_clauses: List[ClauseComparison] = field(default_factory=list)

    overall_impact: CompatibilityImpact = CompatibilityImpact.NEUTRAL

    def has_breaking_changes(self) -> bool:
        if self.removed_clauses:
            return True

        for comparison in self.modified_clauses:
            if comparison.impact == CompatibilityImpact.BREAKING:
                return True

        return False

    def get_change_summary(self) -> str:
        """Generate human-readable summary."""
        lines = [f"Contract Diff: {self.old_version} → {self.new_version}", "=" * 80, ""]

        lines.append(f"Overall Impact: {self.overall_impact.value}")
        lines.append("")

        if self.added_clauses:
            lines.append(f"Added Clauses ({len(self.added_clauses)}):")
            for clause_id in self.added_clauses:
                lines.append(f"  + {clause_id}")

        if self.removed_clauses:
            lines.append(f"Removed Clauses ({len(self.removed_clauses)}):")
            for clause_id in self.removed_clauses:
                lines.append(f"  - {clause_id}")

        if self.modified_clauses:
            lines.append(f"Modified Clauses ({len(self.modified_clauses)}):")
            for comparison in self.modified_clauses:
                lines.append(f"  ~ {comparison.clause_id} ({comparison.impact.value})")

        return "\n".join(lines)


# ============================================================================
# CONTRACT DIFFER
# ============================================================================


class ContractDiffer:
    """
    Computes structural differences between contract versions.

    The ContractDiffer compares two ContractDocument instances to identify
    added, removed, and modified clauses. It performs initial impact
    assessment for simple parameter changes (e.g., nullability relaxation).
    """

    def diff(self, old_contract: ContractDocument, new_contract: ContractDocument) -> ContractDiff:
        """
        Compute diff between two contracts.

        Args:
            old_contract: Older contract version
            new_contract: Newer contract version

        Returns:
            ContractDiff with changes
        """
        old_version = SemanticVersion.parse(old_contract.header.contract_version)
        new_version = SemanticVersion.parse(new_contract.header.contract_version)

        diff = ContractDiff(old_version=old_version, new_version=new_version)

        # Build clause maps
        old_clauses = {c.clause_id: c for c in old_contract.clauses}
        new_clauses = {c.clause_id: c for c in new_contract.clauses}

        # Detect additions
        for clause_id in new_clauses:
            if clause_id not in old_clauses:
                diff.added_clauses.append(clause_id)

        # Detect removals
        for clause_id in old_clauses:
            if clause_id not in new_clauses:
                diff.removed_clauses.append(clause_id)

        # Detect modifications
        for clause_id in old_clauses:
            if clause_id in new_clauses:
                old_clause = old_clauses[clause_id]
                new_clause = new_clauses[clause_id]

                comparison = self._compare_clauses(old_clause, new_clause)
                if comparison.differences:
                    diff.modified_clauses.append(comparison)

        # Assess overall impact
        diff.overall_impact = self._assess_impact(diff)

        return diff

    def _compare_clauses(
        self, old_clause: ContractClause, new_clause: ContractClause
    ) -> ClauseComparison:
        """Compare two clauses with same ID."""
        comparison = ClauseComparison(
            clause_id=old_clause.clause_id,
            old_clause=old_clause,
            new_clause=new_clause,
            change_type=ChangeType.CLAUSE_MODIFIED,
            impact=CompatibilityImpact.NEUTRAL,
        )

        # Compare clause types
        if old_clause.clause_type != new_clause.clause_type:
            comparison.differences.append("Clause type changed")
            comparison.impact = CompatibilityImpact.BREAKING

        # Compare parameters
        old_params = {p.name: p for p in old_clause.constraint_parameters}
        new_params = {p.name: p for p in new_clause.constraint_parameters}

        for param_name in old_params:
            if param_name not in new_params:
                comparison.differences.append(f"Parameter '{param_name}' removed")
                comparison.impact = CompatibilityImpact.BREAKING
            elif old_params[param_name].value != new_params[param_name].value:
                comparison.differences.append(f"Parameter '{param_name}' value changed")
                # Assess if breaking based on clause type and parameter
                comparison.impact = self._assess_parameter_change_impact(
                    old_clause.clause_type,
                    param_name,
                    old_params[param_name].value,
                    new_params[param_name].value,
                )

        return comparison

    def _assess_parameter_change_impact(
        self, clause_type: ClauseType, param_name: str, old_value: any, new_value: any
    ) -> CompatibilityImpact:
        """Assess impact of parameter change."""
        # Nullability: nullable → non-nullable is breaking
        if clause_type == ClauseType.NULLABILITY and param_name == "nullable":
            if old_value is True and new_value is False:
                return CompatibilityImpact.BREAKING
            # non-nullable → nullable is compatible (relaxed)
            return CompatibilityImpact.COMPATIBLE

        # Size: minimum increased is breaking
        if clause_type == ClauseType.SIZE and param_name == "size_value":
            if new_value > old_value:
                return CompatibilityImpact.BREAKING
            return CompatibilityImpact.COMPATIBLE

        # Default: assume breaking for safety
        return CompatibilityImpact.BREAKING

    def _assess_impact(self, diff: ContractDiff) -> CompatibilityImpact:
        """Assess overall compatibility impact."""
        # Removals are always breaking
        if diff.removed_clauses:
            return CompatibilityImpact.BREAKING

        # Check modifications
        for comparison in diff.modified_clauses:
            if comparison.impact == CompatibilityImpact.BREAKING:
                return CompatibilityImpact.BREAKING

        # Additions are compatible
        if diff.added_clauses:
            return CompatibilityImpact.COMPATIBLE

        return CompatibilityImpact.NEUTRAL


# ============================================================================
# VERSION RECOMMENDATION
# ============================================================================


class VersionRecommender:
    """Recommends version bump based on changes."""

    def recommend_version_bump(
        self, current_version: SemanticVersion, diff: ContractDiff
    ) -> Tuple[SemanticVersion, str]:
        """
        Recommend next version based on changes.

        Returns:
            (new_version, rationale)
        """
        if diff.overall_impact == CompatibilityImpact.BREAKING:
            return (current_version.bump_major(), "Breaking changes detected (MAJOR bump)")

        if diff.overall_impact == CompatibilityImpact.COMPATIBLE:
            return (current_version.bump_minor(), "Backward-compatible additions (MINOR bump)")

        return (current_version.bump_patch(), "Metadata or documentation changes only (PATCH bump)")


# ============================================================================
# DEPRECATION SUPPORT
# ============================================================================


@dataclass
class DeprecationNotice:
    """Deprecation notice for clause or contract."""

    deprecated_in_version: SemanticVersion
    removed_in_version: Optional[SemanticVersion] = None
    reason: str = ""
    replacement: Optional[str] = None
    migration_guide: str = ""

    def is_removed_in(self, version: SemanticVersion) -> bool:
        """Check if deprecated item is removed in given version."""
        if not self.removed_in_version:
            return False
        return version >= self.removed_in_version

    def format_notice(self) -> str:
        """Format deprecation notice for display."""
        lines = [f"DEPRECATED in version {self.deprecated_in_version}"]

        if self.removed_in_version:
            lines.append(f"Will be removed in version {self.removed_in_version}")

        if self.reason:
            lines.append(f"Reason: {self.reason}")

        if self.replacement:
            lines.append(f"Use instead: {self.replacement}")

        return "\n".join(lines)


__all__ = [
    "SemanticVersion",
    "ChangeType",
    "CompatibilityImpact",
    "ContractChange",
    "VersionMetadata",
    "VersionHistoryEntry",
    "VersionHistory",
    "ClauseComparison",
    "ContractDiff",
    "ContractDiffer",
    "VersionRecommender",
    "DeprecationNotice",
]
