""" Module 06: Contract Versioning System (Prompt 2/20)

Version identity model, cryptographic fingerprinting, and schema evolution tracking.

This module implements the following:
- Three-version identity system (schema, synthesis, contract)
- Cryptographic fingerprinting for deterministic identity
- Schema compatibility detection & evolution registry
- Schema migration path tracking & upgrade checking
"""

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# VERSION METADATA
# ============================================================================
@dataclass
class ContractVersionMetadata:
    """Version metadata for contract artifacts.

    Contains three independent version identifiers plus fingerprint.
    """

    schema_version: str
    synthesis_version: str
    contract_version: str
    contract_fingerprint: str
    ir_fingerprint: str
    generation_timestamp: str
    generator_tool_version: str = "contract-schema-1.0.0"

    def __post_init__(self):
        """Validate version formats after initialization."""
        self._validate_version_format(self.schema_version, "schema_version")
        self._validate_version_format(self.synthesis_version, "synthesis_version")
        self._validate_version_format(self.contract_version, "contract_version")
        self._validate_fingerprint_format(self.contract_fingerprint, "contract_fingerprint")
        self._validate_fingerprint_format(self.ir_fingerprint, "ir_fingerprint")

    def _validate_version_format(self, version: str, field_name: str):
        """Validate semantic version format (MAJOR.MINOR.PATCH)."""
        pattern = r"^\d+\.\d+\.\d+$"
        if not re.match(pattern, version):
            raise ValueError(
                f"{field_name} must be semantic version (MAJOR.MINOR.PATCH), got: {version}"
            )

    def _validate_fingerprint_format(self, fingerprint: str, field_name: str):
        """Validate fingerprint is valid SHA-256 hex digest."""
        pattern = r"^[a-f0-9]{64}$"
        if not re.match(pattern, fingerprint.lower()):
            raise ValueError(
                f"{field_name} must be 64-character hex SHA-256 digest, got: {fingerprint}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContractVersionMetadata":
        """Create from dictionary."""
        return cls(**data)


# ============================================================================
# SEMANTIC VERSION COMPARISON
# ============================================================================
class SemanticVersion:
    """Semantic version parser and comparator.

    Supports MAJOR.MINOR.PATCH format with comparison operations.
    """

    def __init__(self, version_string: str):
        """
        Initialize semantic version.

        Args:
            version_string: Version in "MAJOR.MINOR.PATCH" format
        """
        parsed = self.parse(version_string)
        self.major = parsed.major
        self.minor = parsed.minor
        self.patch = parsed.patch
        self.version_string = version_string

    @staticmethod
    def parse(version_str: str) -> "SemanticVersion":
        """Parse version string into SemanticVersion object."""
        pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        match = re.match(pattern, version_str)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_str}")

        # This is a bit recursive in the actual implementation to support both static and instance use
        # but for internal use, we just return a temporary object for the __init__ to copy
        class Temp:
            pass

        t = Temp()
        t.major = int(match.group(1))
        t.minor = int(match.group(2))
        t.patch = int(match.group(3))
        return t

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"SemanticVersion('{str(self)}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __lt__(self, other: "SemanticVersion") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: "SemanticVersion") -> bool:
        return self == other or self < other

    def __gt__(self, other: "SemanticVersion") -> bool:
        return not self <= other

    def __ge__(self, other: "SemanticVersion") -> bool:
        return not self < other

    def is_major_bump(self, other: "SemanticVersion") -> bool:
        """Check if this version is a major bump from other."""
        return self.major > other.major

    def is_minor_bump(self, other: "SemanticVersion") -> bool:
        """Check if this version is a minor bump from other."""
        return self.major == other.major and self.minor > other.minor

    def is_patch_bump(self, other: "SemanticVersion") -> bool:
        """Check if this version is a patch bump from other."""
        return self.major == other.major and self.minor == other.minor and self.patch > other.patch


# ============================================================================
# CRYPTOGRAPHIC FINGERPRINTING
# ============================================================================
class ContractFingerprintComputer:
    """Computes cryptographic fingerprints for contract identity.

    Fingerprint is SHA-256 hash over:
    - IR fingerprint
    - schema_version
    - synthesis_version
    - Canonicalized clause content
    """

    def compute_fingerprint(
        self, ir_fingerprint: str, schema_version: str, synthesis_version: str, clauses: List[Any]
    ) -> str:
        """
        Compute deterministic contract fingerprint.

        Args:
            ir_fingerprint: IR fingerprint from Module 05
            schema_version: Schema version string
            synthesis_version: Synthesis version string
            clauses: List of contract clauses

        Returns:
            64-character hex SHA-256 digest
        """
        # Step 1: Validate inputs
        self._validate_fingerprint(ir_fingerprint)
        self._validate_version(schema_version)
        self._validate_version(synthesis_version)

        # Step 2: Canonicalize clause content
        canonical_clauses = self._canonicalize_clauses(clauses)

        # Step 3: Construct fingerprint input
        fingerprint_data = {
            "ir_fingerprint": ir_fingerprint,
            "schema_version": schema_version,
            "synthesis_version": synthesis_version,
            "clauses": canonical_clauses,
        }

        # Step 4: Serialize to canonical JSON
        canonical_json = json.dumps(
            fingerprint_data, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )

        # Step 5: Compute SHA-256
        fingerprint_bytes = canonical_json.encode("utf-8")
        sha256_hash = hashlib.sha256(fingerprint_bytes)

        return sha256_hash.hexdigest()

    def _validate_fingerprint(self, fingerprint: str):
        """Validate fingerprint format."""
        pattern = r"^[a-f0-9]{64}$"
        if not re.match(pattern, fingerprint.lower()):
            raise ValueError(f"Invalid fingerprint format: {fingerprint}")

    def _validate_version(self, version: str):
        """Validate semantic version format."""
        pattern = r"^\d+\.\d+\.\d+$"
        if not re.match(pattern, version):
            raise ValueError(f"Invalid version format: {version}")

    def _canonicalize_clauses(self, clauses: List[Any]) -> List[Dict]:
        """
        Canonicalize clause content for deterministic hashing.
        """
        canonical_clauses = []

        for clause in clauses:
            # Convert to dict if needed
            if hasattr(clause, "to_dict"):
                clause_dict = clause.to_dict()
            elif hasattr(clause, "__dict__"):
                clause_dict = clause.__dict__.copy()
            else:
                clause_dict = dict(clause)

            # Remove non-deterministic fields
            clause_dict.pop("creation_timestamp", None)
            clause_dict.pop("last_modified", None)

            # Sort nested structures
            if "constraint_parameters" in clause_dict:
                params = clause_dict["constraint_parameters"]
                if isinstance(params, list):
                    clause_dict["constraint_parameters"] = sorted(
                        params, key=lambda p: p.get("name", "") if isinstance(p, dict) else str(p)
                    )

            if "metadata" in clause_dict and isinstance(clause_dict["metadata"], dict):
                clause_dict["metadata"] = dict(sorted(clause_dict["metadata"].items()))

            canonical_clauses.append(clause_dict)

        # Sort clauses by clause_id
        canonical_clauses.sort(key=lambda c: c.get("clause_id", ""))

        return canonical_clauses


# ============================================================================
# VERSION IDENTITY MANAGER
# ============================================================================
class VersionIdentityManager:
    """Manages version identity for contract artifacts."""

    def __init__(self):
        self.fingerprint_computer = ContractFingerprintComputer()

    def create_version_metadata(
        self,
        schema_version: str,
        synthesis_version: str,
        contract_version: str,
        ir_fingerprint: str,
        clauses: List[Any],
        generator_tool_version: Optional[str] = None,
    ) -> ContractVersionMetadata:
        """
        Create complete version metadata for a contract.
        """
        # Compute contract fingerprint
        contract_fingerprint = self.fingerprint_computer.compute_fingerprint(
            ir_fingerprint=ir_fingerprint,
            schema_version=schema_version,
            synthesis_version=synthesis_version,
            clauses=clauses,
        )

        # Generate timestamp
        generation_timestamp = datetime.utcnow().isoformat() + "Z"

        # Create metadata
        return ContractVersionMetadata(
            schema_version=schema_version,
            synthesis_version=synthesis_version,
            contract_version=contract_version,
            contract_fingerprint=contract_fingerprint,
            ir_fingerprint=ir_fingerprint,
            generation_timestamp=generation_timestamp,
            generator_tool_version=generator_tool_version or "contract-schema-1.0.0",
        )

    def verify_fingerprint(self, metadata: ContractVersionMetadata, clauses: List[Any]) -> bool:
        """
        Verify contract fingerprint matches content.
        """
        computed_fingerprint = self.fingerprint_computer.compute_fingerprint(
            ir_fingerprint=metadata.ir_fingerprint,
            schema_version=metadata.schema_version,
            synthesis_version=metadata.synthesis_version,
            clauses=clauses,
        )

        return computed_fingerprint == metadata.contract_fingerprint

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two semantic versions.
        """
        v1 = SemanticVersion(version1)
        v2 = SemanticVersion(version2)

        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0


# ============================================================================
# SCHEMA COMPATIBILITY STATES
# ============================================================================
class SchemaCompatibility(Enum):
    """Schema version compatibility classifications."""

    IDENTICAL = "identical"
    BACKWARD_COMPATIBLE = "backward_compatible"
    FORWARD_COMPATIBLE = "forward_compatible"
    PATCH_DIFFERENCE = "patch_difference"
    BREAKING_INCOMPATIBLE = "breaking_incompatible"
    UNKNOWN_FUTURE = "unknown_future"
    DEPRECATED_VERSION = "deprecated_version"


class SchemaVersionStatus(Enum):
    """Schema version lifecycle status."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


# ============================================================================
# SCHEMA VERSION METADATA
# ============================================================================
@dataclass
class SchemaVersionInfo:
    """Metadata about a specific schema version."""

    version: str
    release_date: str
    status: SchemaVersionStatus
    breaking_changes: List[str] = field(default_factory=list)
    new_features: List[str] = field(default_factory=list)
    bug_fixes: List[str] = field(default_factory=list)
    migration_available: bool = False
    backward_compatible_with: List[str] = field(default_factory=list)
    deprecation_date: Optional[str] = None
    retirement_date: Optional[str] = None

    def is_deprecated(self) -> bool:
        """Check if this version is deprecated."""
        return self.status == SchemaVersionStatus.DEPRECATED

    def is_retired(self) -> bool:
        """Check if this version is retired."""
        return self.status == SchemaVersionStatus.RETIRED

    def is_active(self) -> bool:
        """Check if this version is active."""
        return self.status == SchemaVersionStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "release_date": self.release_date,
            "status": self.status.value,
            "breaking_changes": self.breaking_changes,
            "new_features": self.new_features,
            "bug_fixes": self.bug_fixes,
            "migration_available": self.migration_available,
            "backward_compatible_with": self.backward_compatible_with,
            "deprecation_date": self.deprecation_date,
            "retirement_date": self.retirement_date,
        }


# ============================================================================
# SCHEMA EVOLUTION REGISTRY
# ============================================================================
class SchemaEvolutionRegistry:
    """Registry of all known schema versions and their metadata."""

    def __init__(self):
        self.versions: Dict[str, SchemaVersionInfo] = {}
        self._initialize_builtin_versions()

    def _initialize_builtin_versions(self):
        """Initialize built-in schema versions."""
        # Version 1.0.0: Initial release
        self.register_version(
            SchemaVersionInfo(
                version="1.0.0",
                release_date="2025-01-20",
                status=SchemaVersionStatus.ACTIVE,
                breaking_changes=[],
                new_features=["Initial contract schema definition"],
                backward_compatible_with=[],
            )
        )

    def register_version(self, version_info: SchemaVersionInfo):
        """Register a schema version in the registry."""
        self.versions[version_info.version] = version_info

    def get_version_info(self, version: str) -> Optional[SchemaVersionInfo]:
        """Get metadata for a specific schema version."""
        return self.versions.get(version)

    def is_known_version(self, version: str) -> bool:
        """Check if version is registered."""
        return version in self.versions

    def get_active_versions(self) -> List[SchemaVersionInfo]:
        """Get all active schema versions."""
        return [info for info in self.versions.values() if info.is_active()]

    def get_deprecated_versions(self) -> List[SchemaVersionInfo]:
        """Get all deprecated schema versions."""
        return [info for info in self.versions.values() if info.is_deprecated()]

    def get_latest_version(self) -> Optional[SchemaVersionInfo]:
        """Get the latest active schema version."""
        active_versions = self.get_active_versions()
        if not active_versions:
            return None

        # Sort by semantic version
        sorted_versions = sorted(
            active_versions, key=lambda v: SemanticVersion(v.version), reverse=True
        )

        return sorted_versions[0]


# ============================================================================
# SCHEMA COMPATIBILITY DETECTOR
# ============================================================================
class SchemaCompatibilityDetector:
    """Detects compatibility between schema versions."""

    def __init__(self, registry: Optional[SchemaEvolutionRegistry] = None):
        """Initialize detector."""
        self.registry = registry or SchemaEvolutionRegistry()

    def detect_compatibility(self, version1: str, version2: str) -> SchemaCompatibility:
        """Detect compatibility between two schema versions."""
        # Step 1: Parse versions
        try:
            v1 = SemanticVersion(version1)
            v2 = SemanticVersion(version2)
        except ValueError:
            return SchemaCompatibility.UNKNOWN_FUTURE

        # Step 2: Check if identical
        if v1 == v2:
            return SchemaCompatibility.IDENTICAL

        # Step 3: Check registry for deprecation
        v1_info = self.registry.get_version_info(version1)
        v2_info = self.registry.get_version_info(version2)

        if v1_info and v1_info.is_deprecated():
            return SchemaCompatibility.DEPRECATED_VERSION

        # Step 4: Compare MAJOR versions
        if v1.major != v2.major:
            return SchemaCompatibility.BREAKING_INCOMPATIBLE

        # Step 5: Compare MINOR versions (MAJOR is same)
        if v1.minor < v2.minor:
            # v2 is newer minor version
            return SchemaCompatibility.BACKWARD_COMPATIBLE

        if v1.minor > v2.minor:
            # v1 is newer minor version
            return SchemaCompatibility.FORWARD_COMPATIBLE

        # Step 6: Compare PATCH versions (MAJOR and MINOR are same)
        if v1.patch != v2.patch:
            return SchemaCompatibility.PATCH_DIFFERENCE

        # Should not reach here if versions are equal
        return SchemaCompatibility.IDENTICAL

    def is_compatible(self, version1: str, version2: str) -> bool:
        """Check if two versions are compatible (not breaking)."""
        compatibility = self.detect_compatibility(version1, version2)

        return compatibility not in [
            SchemaCompatibility.BREAKING_INCOMPATIBLE,
            SchemaCompatibility.UNKNOWN_FUTURE,
        ]

    def requires_migration(self, from_version: str, to_version: str) -> bool:
        """Check if migration is required between versions."""
        compatibility = self.detect_compatibility(from_version, to_version)

        return compatibility == SchemaCompatibility.BREAKING_INCOMPATIBLE

    def can_downgrade(self, from_version: str, to_version: str) -> bool:
        """Check if downgrade from newer to older version is safe."""
        compatibility = self.detect_compatibility(to_version, from_version)

        # Downgrade safe if older version can read newer contracts
        return compatibility == SchemaCompatibility.BACKWARD_COMPATIBLE


# ============================================================================
# SCHEMA MIGRATION FRAMEWORK
# ============================================================================
@dataclass
class SchemaMigrationPath:
    """Defines a migration path between schema versions."""

    from_version: str
    to_version: str
    migration_steps: List[str] = field(default_factory=list)
    reversible: bool = False
    semantic_preserving: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "migration_steps": self.migration_steps,
            "reversible": self.reversible,
            "semantic_preserving": self.semantic_preserving,
            "description": self.description,
        }


class SchemaMigrationRegistry:
    """Registry of available schema migration paths."""

    def __init__(self):
        self.migrations: Dict[tuple, SchemaMigrationPath] = {}

    def register_migration(self, migration: SchemaMigrationPath):
        """Register a migration path."""
        key = (migration.from_version, migration.to_version)
        self.migrations[key] = migration

    def get_migration(self, from_version: str, to_version: str) -> Optional[SchemaMigrationPath]:
        """Get migration path between versions."""
        key = (from_version, to_version)
        return self.migrations.get(key)

    def has_migration(self, from_version: str, to_version: str) -> bool:
        """Check if migration path exists."""
        return (from_version, to_version) in self.migrations

    def find_migration_chain(
        self, from_version: str, to_version: str
    ) -> Optional[List[SchemaMigrationPath]]:
        """Find chain of migrations from source to target version."""
        # Direct migration available?
        direct = self.get_migration(from_version, to_version)
        if direct:
            return [direct]

        return None


# ============================================================================
# VERSION UPGRADE CHECKER
# ============================================================================
class SchemaUpgradeChecker:
    """Checks if schema upgrade is safe and provides upgrade recommendations."""

    def __init__(
        self,
        compatibility_detector: Optional[SchemaCompatibilityDetector] = None,
        migration_registry: Optional[SchemaMigrationRegistry] = None,
    ):
        self.detector = compatibility_detector or SchemaCompatibilityDetector()
        self.migration_registry = migration_registry or SchemaMigrationRegistry()

    def check_upgrade(self, current_version: str, target_version: str) -> Dict[str, Any]:
        """Check if upgrade from current to target version is safe."""
        compatibility = self.detector.detect_compatibility(current_version, target_version)

        result = {
            "current_version": current_version,
            "target_version": target_version,
            "compatibility": compatibility.value,
            "safe_upgrade": False,
            "migration_required": False,
            "migration_available": False,
            "warnings": [],
            "recommendations": [],
        }

        # Analyze compatibility
        if compatibility == SchemaCompatibility.IDENTICAL:
            result["safe_upgrade"] = True
            result["recommendations"].append("Already at target version")

        elif compatibility == SchemaCompatibility.BACKWARD_COMPATIBLE:
            result["safe_upgrade"] = True
            result["recommendations"].append("Direct upgrade safe - backward compatible")

        elif compatibility == SchemaCompatibility.PATCH_DIFFERENCE:
            result["safe_upgrade"] = True
            result["recommendations"].append("Patch version difference - safe to upgrade")

        elif compatibility == SchemaCompatibility.BREAKING_INCOMPATIBLE:
            result["migration_required"] = True
            result["migration_available"] = self.migration_registry.has_migration(
                current_version, target_version
            )

            if result["migration_available"]:
                result["recommendations"].append("Migration tool available - use migration")
            else:
                result["warnings"].append("No migration tool available for this upgrade")

        elif compatibility == SchemaCompatibility.DEPRECATED_VERSION:
            result["warnings"].append(f"Current version {current_version} is deprecated")
            result["recommendations"].append("Upgrade to active version recommended")

        elif compatibility == SchemaCompatibility.UNKNOWN_FUTURE:
            result["warnings"].append(f"Target version {target_version} is unknown")
            result["recommendations"].append("Update tooling before upgrading")

        return result


# ============================================================================
# EXPORTS
# ============================================================================
__all__ = [
    # From Prompt 1
    "ContractVersionMetadata",
    "SemanticVersion",
    "ContractFingerprintComputer",
    "VersionIdentityManager",
    # From Prompt 2
    "SchemaCompatibility",
    "SchemaVersionStatus",
    "SchemaVersionInfo",
    "SchemaEvolutionRegistry",
    "SchemaCompatibilityDetector",
    "SchemaMigrationPath",
    "SchemaMigrationRegistry",
    "SchemaUpgradeChecker",
]
