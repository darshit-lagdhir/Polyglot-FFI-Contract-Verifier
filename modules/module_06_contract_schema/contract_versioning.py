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
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


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
@dataclass
class SemanticVersion:
    """Semantic version representation."""

    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: Optional[str] = None
    build_metadata: Optional[str] = None

    def __init__(
        self,
        major: Any = 0,
        minor: int = 0,
        patch: int = 0,
        prerelease: Optional[str] = None,
        build_metadata: Optional[str] = None,
    ):
        if isinstance(major, str):
            # Backward compatibility: parse from string
            parsed = self.parse(major)
            self.major = parsed.major
            self.minor = parsed.minor
            self.patch = parsed.patch
            self.prerelease = parsed.prerelease
            self.build_metadata = parsed.build_metadata
        else:
            self.major = major
            self.minor = minor
            self.patch = patch
            self.prerelease = prerelease
            self.build_metadata = build_metadata

    @staticmethod
    def parse(version_str: str) -> "SemanticVersion":
        """Parse semantic version string."""
        # Pattern: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z\-\.]+))?(?:\+([0-9A-Za-z\-\.]+))?$"
        match = re.match(pattern, version_str)

        if not match:
            raise ValueError(f"Invalid semantic version: {version_str}")

        major, minor, patch, prerelease, build = match.groups()

        return SemanticVersion(major=int(major), minor=int(minor), patch=int(patch), prerelease=prerelease, build_metadata=build)

    def __str__(self) -> str:
        """Convert to string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build_metadata:
            version += f"+{self.build_metadata}"
        return version

    def __repr__(self) -> str:
        """Convert to representation."""
        return f"SemanticVersion('{str(self)}')"

    def __lt__(self, other: "SemanticVersion") -> bool:
        """Compare versions (less than)."""
        # Compare MAJOR.MINOR.PATCH
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

        # Pre-release version < release version
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False

        # Compare pre-release versions
        if self.prerelease and other.prerelease:
            return self._compare_prerelease(self.prerelease, other.prerelease) < 0

        # Equal versions
        return False

    def __eq__(self, other: object) -> bool:
        """Compare versions (equality)."""
        if not isinstance(other, SemanticVersion):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __le__(self, other: "SemanticVersion") -> bool:
        """Compare versions (less than or equal)."""
        return self < other or self == other

    def __gt__(self, other: "SemanticVersion") -> bool:
        """Compare versions (greater than)."""
        return not self <= other

    def __ge__(self, other: "SemanticVersion") -> bool:
        """Compare versions (greater than or equal)."""
        return not self < other

    def _compare_prerelease(self, pre1: str, pre2: str) -> int:
        """Compare pre-release versions."""
        parts1 = pre1.split(".")
        parts2 = pre2.split(".")

        for p1, p2 in zip(parts1, parts2):
            # Try numeric comparison
            try:
                n1, n2 = int(p1), int(p2)
                if n1 != n2:
                    return -1 if n1 < n2 else 1
            except ValueError:
                # Lexical comparison
                if p1 != p2:
                    return -1 if p1 < p2 else 1

        # Shorter is less
        return len(parts1) - len(parts2)

    def is_prerelease(self) -> bool:
        """Check if this is a pre-release version."""
        return self.prerelease is not None

    def bump_major(self) -> "SemanticVersion":
        """Bump major version."""
        return SemanticVersion(self.major + 1, 0, 0)

    def bump_minor(self) -> "SemanticVersion":
        """Bump minor version."""
        return SemanticVersion(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "SemanticVersion":
        """Bump patch version."""
        return SemanticVersion(self.major, self.minor, self.patch + 1)


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
# SYNTHESIS VERSION ENUMS
# ============================================================================
class SynthesisCompatibility(Enum):
    """Synthesis version compatibility classifications.
    Defines semantic relationship between synthesis versions.
    """

    IDENTICAL = "identical"
    EQUIVALENT = "equivalent"
    STRENGTHENING = "strengthening"
    RELAXATION = "relaxation"
    INCOMPATIBLE = "incompatible"
    UNKNOWN_VERSION = "unknown_version"


class RuleCategory(Enum):
    """Categories of synthesis rules."""

    LAYOUT = "layout"
    NULLABILITY = "nullability"
    OWNERSHIP = "ownership"
    RELATIONAL = "relational"
    CALLING_CONVENTION = "calling_convention"
    ABI_COMPATIBILITY = "abi_compatibility"
    ADVISORY = "advisory"


class SynthesisVersionStatus(Enum):
    """Synthesis version lifecycle status."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


# ============================================================================
# SYNTHESIS RULE METADATA
# ============================================================================
@dataclass
class SynthesisRuleInfo:
    """Metadata about a specific synthesis rule.
    Each rule has immutable identity and versioning.
    """

    rule_id: str
    rule_version: str
    synthesis_version_introduced: str
    rule_category: RuleCategory
    applies_to: List[str] = field(default_factory=list)
    confidence_range: Tuple[float, float] = (0.0, 1.0)
    description: str = ""
    synthesis_version_deprecated: Optional[str] = None

    def is_deprecated_in(self, synthesis_version: str) -> bool:
        """Check if rule is deprecated in given synthesis version."""
        if not self.synthesis_version_deprecated:
            return False

        try:
            current = SemanticVersion(synthesis_version)
            deprecated_at = SemanticVersion(self.synthesis_version_deprecated)
            return current >= deprecated_at
        except ValueError:
            return False

    def is_active_in(self, synthesis_version: str) -> bool:
        """Check if rule is active in given synthesis version."""
        try:
            current = SemanticVersion(synthesis_version)
            introduced = SemanticVersion(self.synthesis_version_introduced)

            # Active if version >= introduced and not deprecated
            if current < introduced:
                return False

            return not self.is_deprecated_in(synthesis_version)
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "synthesis_version_introduced": self.synthesis_version_introduced,
            "rule_category": self.rule_category.value,
            "applies_to": self.applies_to,
            "confidence_range": self.confidence_range,
            "description": self.description,
            "synthesis_version_deprecated": self.synthesis_version_deprecated,
        }


@dataclass
class SynthesisVersionInfo:
    """Metadata about a specific synthesis version.
    Tracks which rules are active, changes from previous version, etc.
    """

    version: str
    release_date: str
    status: SynthesisVersionStatus
    active_rules: List[str] = field(default_factory=list)
    new_rules: List[str] = field(default_factory=list)
    deprecated_rules: List[str] = field(default_factory=list)
    changed_rules: List[str] = field(default_factory=list)
    description: str = ""
    deprecation_date: Optional[str] = None
    retirement_date: Optional[str] = None

    def is_active(self) -> bool:
        """Check if version is active."""
        return self.status == SynthesisVersionStatus.ACTIVE

    def is_deprecated(self) -> bool:
        """Check if version is deprecated."""
        return self.status == SynthesisVersionStatus.DEPRECATED

    def is_retired(self) -> bool:
        """Check if version is retired."""
        return self.status == SynthesisVersionStatus.RETIRED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "release_date": self.release_date,
            "status": self.status.value,
            "active_rules": self.active_rules,
            "new_rules": self.new_rules,
            "deprecated_rules": self.deprecated_rules,
            "changed_rules": self.changed_rules,
            "description": self.description,
            "deprecation_date": self.deprecation_date,
            "retirement_date": self.retirement_date,
        }


# ============================================================================
# SYNTHESIS RULE REGISTRY
# ============================================================================
class SynthesisRuleRegistry:
    """Registry of all synthesis rules across all versions.
    Provides rule lookup, version comparison, and evolution tracking.
    """

    def __init__(self):
        self.rules: Dict[str, SynthesisRuleInfo] = {}
        self.versions: Dict[str, SynthesisVersionInfo] = {}
        self._initialize_builtin_rules()

    def _initialize_builtin_rules(self):
        """Initialize built-in synthesis rules and versions."""
        # Version 1.0.0: Initial synthesis rules
        self.register_version(
            SynthesisVersionInfo(
                version="1.0.0",
                release_date="2025-01-20",
                status=SynthesisVersionStatus.ACTIVE,
                active_rules=[
                    "layout_struct_v1",
                    "nullability_pointer_default_v1",
                    "ownership_return_caller_v1",
                ],
                description="Initial synthesis rule set",
            )
        )

        # Register individual rules
        self.register_rule(
            SynthesisRuleInfo(
                rule_id="layout_struct_v1",
                rule_version="1.0.0",
                synthesis_version_introduced="1.0.0",
                rule_category=RuleCategory.LAYOUT,
                applies_to=["structures", "unions"],
                description="Generate layout clauses for structures",
            )
        )

        self.register_rule(
            SynthesisRuleInfo(
                rule_id="nullability_pointer_default_v1",
                rule_version="1.0.0",
                synthesis_version_introduced="1.0.0",
                rule_category=RuleCategory.NULLABILITY,
                applies_to=["pointer_parameters", "return_values"],
                confidence_range=(0.7, 0.9),
                description="Default nullability inference for pointers",
            )
        )

        self.register_rule(
            SynthesisRuleInfo(
                rule_id="ownership_return_caller_v1",
                rule_version="1.0.0",
                synthesis_version_introduced="1.0.0",
                rule_category=RuleCategory.OWNERSHIP,
                applies_to=["return_values"],
                confidence_range=(0.6, 0.8),
                description="Return value ownership defaults to caller",
            )
        )

    def register_rule(self, rule_info: SynthesisRuleInfo):
        """
        Register a synthesis rule.
        Args:
            rule_info: Rule metadata
        """
        self.rules[rule_info.rule_id] = rule_info

    def register_version(self, version_info: SynthesisVersionInfo):
        """
        Register a synthesis version.
        Args:
            version_info: Version metadata
        """
        self.versions[version_info.version] = version_info

    def get_rule(self, rule_id: str) -> Optional[SynthesisRuleInfo]:
        """Get rule metadata by ID."""
        return self.rules.get(rule_id)

    def get_version_info(self, version: str) -> Optional[SynthesisVersionInfo]:
        """Get version metadata."""
        return self.versions.get(version)

    def get_active_rules_for_version(self, version: str) -> List[SynthesisRuleInfo]:
        """
        Get all active rules for a synthesis version.
        Args:
            version: Synthesis version string
        Returns:
            List of active rules in that version
        """
        rules = []
        for rule_info in self.rules.values():
            if rule_info.is_active_in(version):
                rules.append(rule_info)
        return rules

    def get_rules_by_category(self, version: str, category: RuleCategory) -> List[SynthesisRuleInfo]:
        """Get all rules in a category for a version."""
        active_rules = self.get_active_rules_for_version(version)
        return [r for r in active_rules if r.rule_category == category]

    def is_known_version(self, version: str) -> bool:
        """Check if synthesis version is registered."""
        return version in self.versions


# ============================================================================
# SYNTHESIS COMPATIBILITY DETECTOR
# ============================================================================
class SynthesisCompatibilityDetector:
    """Detects compatibility between synthesis versions.
    Analyzes rule set changes to classify semantic drift.
    """

    def __init__(self, registry: Optional[SynthesisRuleRegistry] = None):
        """
        Initialize detector.
        Args:
            registry: Optional synthesis rule registry
        """
        self.registry = registry or SynthesisRuleRegistry()

    def detect_compatibility(self, version1: str, version2: str) -> SynthesisCompatibility:
        """
        Detect compatibility between synthesis versions.
        Args:
            version1: First synthesis version
            version2: Second synthesis version
        Returns:
            SynthesisCompatibility classification
        """
        # Step 1: Check if versions are known
        if not self.registry.is_known_version(version1):
            return SynthesisCompatibility.UNKNOWN_VERSION
        if not self.registry.is_known_version(version2):
            return SynthesisCompatibility.UNKNOWN_VERSION

        # Step 2: Parse versions
        try:
            v1 = SemanticVersion(version1)
            v2 = SemanticVersion(version2)
        except ValueError:
            return SynthesisCompatibility.UNKNOWN_VERSION

        # Step 3: Check if identical
        if v1 == v2:
            return SynthesisCompatibility.IDENTICAL

        # Step 4: Check MAJOR version difference
        if v1.major != v2.major:
            return SynthesisCompatibility.INCOMPATIBLE

        # Step 5: Load rule sets
        rules_v1 = set(r.rule_id for r in self.registry.get_active_rules_for_version(version1))
        rules_v2 = set(r.rule_id for r in self.registry.get_active_rules_for_version(version2))

        # Step 6: Compare rule sets
        added_rules = rules_v2 - rules_v1
        removed_rules = rules_v1 - rules_v2

        # Step 7: Classify change direction
        if added_rules and not removed_rules:
            # Only additions → strengthening
            return SynthesisCompatibility.STRENGTHENING

        if removed_rules:
            # Any removals → relaxation (requires review)
            return SynthesisCompatibility.RELAXATION

        if not added_rules and not removed_rules:
            # Same rule set → equivalent
            return SynthesisCompatibility.EQUIVALENT

        # Default
        return SynthesisCompatibility.EQUIVALENT

    def is_safe_upgrade(self, from_version: str, to_version: str) -> bool:
        """
        Check if upgrade is safe without review.
        Args:
            from_version: Current version
            to_version: Target version
        Returns:
            True if safe upgrade
        """
        compatibility = self.detect_compatibility(from_version, to_version)

        return compatibility in [
            SynthesisCompatibility.IDENTICAL,
            SynthesisCompatibility.EQUIVALENT,
            SynthesisCompatibility.STRENGTHENING,
        ]

    def requires_review(self, from_version: str, to_version: str) -> bool:
        """
        Check if version change requires manual review.
        Args:
            from_version: Current version
            to_version: Target version
        Returns:
            True if manual review required
        """
        compatibility = self.detect_compatibility(from_version, to_version)

        return compatibility in [SynthesisCompatibility.RELAXATION, SynthesisCompatibility.INCOMPATIBLE]


# ============================================================================
# SYNTHESIS EVOLUTION TRACKER
# ============================================================================
@dataclass
class SynthesisEvolutionEvent:
    """Records a synthesis evolution event.
    Tracks changes to synthesis rules over time.
    """

    event_id: str
    event_type: str  # "rule_added", "rule_deprecated", "confidence_adjusted", etc.
    synthesis_version: str
    timestamp: str
    affected_rules: List[str] = field(default_factory=list)
    description: str = ""
    impact_assessment: str = ""  # "strengthening", "relaxation", etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "synthesis_version": self.synthesis_version,
            "timestamp": self.timestamp,
            "affected_rules": self.affected_rules,
            "description": self.description,
            "impact_assessment": self.impact_assessment,
        }


class SynthesisEvolutionTracker:
    """Tracks evolution of synthesis rules over time.
    Maintains log of all changes to synthesis versions.
    """

    def __init__(self):
        self.events: List[SynthesisEvolutionEvent] = []

    def record_event(self, event: SynthesisEvolutionEvent):
        """
        Record a synthesis evolution event.
        Args:
            event: Evolution event to record
        """
        self.events.append(event)

    def get_events_for_version(self, version: str) -> List[SynthesisEvolutionEvent]:
        """Get all events for a specific version."""
        return [e for e in self.events if e.synthesis_version == version]

    def get_events_by_type(self, event_type: str) -> List[SynthesisEvolutionEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def get_timeline(self) -> List[SynthesisEvolutionEvent]:
        """Get chronological timeline of all events."""
        return sorted(self.events, key=lambda e: e.timestamp)


# ============================================================================
# DETERMINISM VERIFIER
# ============================================================================
class SynthesisDeterminismVerifier:
    """Verifies deterministic synthesis reproduction.
    Ensures identical inputs produce identical outputs.
    """

    def verify_determinism(
        self,
        ir_fingerprint: str,
        synthesis_version: str,
        schema_version: str,
        contract_fingerprint1: str,
        contract_fingerprint2: str,
    ) -> bool:
        """
        Verify two synthesis runs produced identical results.
        Args:
            ir_fingerprint: IR artifact fingerprint
            synthesis_version: Synthesis version used
            schema_version: Schema version used
            contract_fingerprint1: First contract fingerprint
            contract_fingerprint2: Second contract fingerprint
        Returns:
            True if deterministic (fingerprints match)
        """
        return contract_fingerprint1 == contract_fingerprint2

    def compute_expected_fingerprint(
        self, ir_fingerprint: str, synthesis_version: str, schema_version: str
    ) -> str:
        """
        Compute expected contract fingerprint deterministically.
        This is a placeholder - actual implementation would use
        synthesis engine to regenerate contract.
        Args:
            ir_fingerprint: IR fingerprint
            synthesis_version: Synthesis version
            schema_version: Schema version
        Returns:
            Expected contract fingerprint
        """
        # In real implementation, this would:
        # 1. Load IR from fingerprint
        # 2. Load synthesis rules for version
        # 3. Run synthesis
        # 4. Return contract fingerprint

        # For now, return placeholder
        import hashlib

        data = f"{ir_fingerprint}:{synthesis_version}:{schema_version}"
        return hashlib.sha256(data.encode()).hexdigest()


# ============================================================================
# ABI COMPATIBILITY ENUMS
# ============================================================================
class ABICompatibility(Enum):
    """ABI compatibility classifications for contract changes.
    Defines the impact of contract changes on binary compatibility.
    """

    ABI_IDENTICAL = "abi_identical"
    ABI_COMPATIBLE_EXTENSION = "abi_compatible_extension"
    ABI_COMPATIBLE_RELAXATION = "abi_compatible_relaxation"
    ABI_COMPATIBLE_STRENGTHENING = "abi_compatible_strengthening"
    ABI_BREAKING_LAYOUT = "abi_breaking_layout"
    ABI_BREAKING_SIGNATURE = "abi_breaking_signature"
    ABI_BREAKING_REMOVAL = "abi_breaking_removal"


class ChangeType(Enum):
    """Types of contract changes."""

    FUNCTION_ADDED = "function_added"
    FUNCTION_REMOVED = "function_removed"
    FUNCTION_MODIFIED = "function_modified"
    TYPE_ADDED = "type_added"
    TYPE_REMOVED = "type_removed"
    TYPE_MODIFIED = "type_modified"
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_MODIFIED = "field_modified"
    CLAUSE_ADDED = "clause_added"
    CLAUSE_REMOVED = "clause_removed"
    CLAUSE_MODIFIED = "clause_modified"


# ============================================================================
# CHANGE DETECTION ENTITIES
# ============================================================================
@dataclass
class ContractChange:
    """Represents a single change between contract versions.
    Records what changed, where, and why it matters.
    """

    change_type: ChangeType
    entity_id: str
    description: str
    abi_impact: ABICompatibility
    details: Dict[str, Any] = field(default_factory=dict)

    def is_breaking(self) -> bool:
        """Check if this change is ABI-breaking."""
        return self.abi_impact in [
            ABICompatibility.ABI_BREAKING_LAYOUT,
            ABICompatibility.ABI_BREAKING_SIGNATURE,
            ABICompatibility.ABI_BREAKING_REMOVAL,
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type.value,
            "entity_id": self.entity_id,
            "description": self.description,
            "abi_impact": self.abi_impact.value,
            "details": self.details,
        }


@dataclass
class ContractDiff:
    """Complete diff between two contract versions.
    Contains all detected changes and overall compatibility classification.
    """

    baseline_version: str
    candidate_version: str
    baseline_fingerprint: str
    candidate_fingerprint: str
    changes: List[ContractChange] = field(default_factory=list)
    overall_compatibility: Optional[ABICompatibility] = None

    def has_breaking_changes(self) -> bool:
        """Check if any changes are ABI-breaking."""
        return any(change.is_breaking() for change in self.changes)

    def get_breaking_changes(self) -> List[ContractChange]:
        """Get all breaking changes."""
        return [c for c in self.changes if c.is_breaking()]

    def get_compatible_changes(self) -> List[ContractChange]:
        """Get all compatible changes."""
        return [c for c in self.changes if not c.is_breaking()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline_version": self.baseline_version,
            "candidate_version": self.candidate_version,
            "baseline_fingerprint": self.baseline_fingerprint,
            "candidate_fingerprint": self.candidate_fingerprint,
            "changes": [c.to_dict() for c in self.changes],
            "overall_compatibility": self.overall_compatibility.value
            if self.overall_compatibility
            else None,
            "has_breaking_changes": self.has_breaking_changes(),
        }


# ============================================================================
# CONTRACT VERSION TRACKER
# ============================================================================
@dataclass
class ContractVersionSnapshot:
    """Snapshot of a contract at a specific version.
    Records contract state and metadata at a point in time.
    """

    version: str
    release_date: str
    contract_fingerprint: str
    schema_version: str
    synthesis_version: str
    ir_fingerprint: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "release_date": self.release_date,
            "contract_fingerprint": self.contract_fingerprint,
            "schema_version": self.schema_version,
            "synthesis_version": self.synthesis_version,
            "ir_fingerprint": self.ir_fingerprint,
            "description": self.description,
        }


class ContractEvolutionTimeline:
    """Timeline of contract version evolution.
    Tracks all versions of a contract interface over time.
    """

    def __init__(self, interface_id: str):
        self.interface_id = interface_id
        self.snapshots: Dict[str, ContractVersionSnapshot] = {}

    def add_snapshot(self, snapshot: ContractVersionSnapshot):
        """
        Add a version snapshot to timeline.
        Args:
            snapshot: Contract version snapshot
        """
        self.snapshots[snapshot.version] = snapshot

    def get_snapshot(self, version: str) -> Optional[ContractVersionSnapshot]:
        """Get snapshot for a specific version."""
        return self.snapshots.get(version)

    def get_all_versions(self) -> List[str]:
        """Get all tracked versions in chronological order."""
        versions = list(self.snapshots.keys())
        # Sort by semantic version
        try:
            return sorted(versions, key=lambda v: SemanticVersion(v))
        except ValueError:
            return sorted(versions)  # Fallback to string sort

    def get_latest_version(self) -> Optional[ContractVersionSnapshot]:
        """Get the latest version snapshot."""
        versions = self.get_all_versions()
        if not versions:
            return None
        return self.snapshots[versions[-1]]


# ============================================================================
# ABI COMPATIBILITY DETECTOR
# ============================================================================
class ABICompatibilityDetector:
    """Detects ABI compatibility between contract versions.
    Analyzes structural changes and classifies their impact.
    """

    def detect_compatibility(self, baseline_contract: Any, candidate_contract: Any) -> ContractDiff:
        """
        Detect compatibility between two contracts.
        Args:
            baseline_contract: Old contract version
            candidate_contract: New contract version
        Returns:
            ContractDiff with all detected changes
        """
        diff = ContractDiff(
            baseline_version=getattr(baseline_contract, "contract_version", "unknown"),
            candidate_version=getattr(candidate_contract, "contract_version", "unknown"),
            baseline_fingerprint=getattr(baseline_contract, "contract_fingerprint", ""),
            candidate_fingerprint=getattr(candidate_contract, "contract_fingerprint", ""),
        )

        # Step 1: Check if identical
        if diff.baseline_fingerprint == diff.candidate_fingerprint:
            diff.overall_compatibility = ABICompatibility.ABI_IDENTICAL
            return diff

        # Step 2: Detect changes (simplified - real implementation would compare entities)
        # In a full implementation, we would extract functions and structs
        # and compare them one by one.

        # Placeholder for structural analysis logic
        changes = []

        # Example: Mock function analysis if attributes exist
        if hasattr(baseline_contract, "functions") and hasattr(candidate_contract, "functions"):
            changes.extend(
                self._detect_function_changes(
                    baseline_contract.functions, candidate_contract.functions
                )
            )

        if hasattr(baseline_contract, "structs") and hasattr(candidate_contract, "structs"):
            changes.extend(
                self._detect_struct_changes(baseline_contract.structs, candidate_contract.structs)
            )

        diff.changes = changes

        # Determine overall compatibility based on most severe change
        if diff.has_breaking_changes():
            # Find most severe breaking impact
            impacts = [c.abi_impact for c in diff.get_breaking_changes()]
            if ABICompatibility.ABI_BREAKING_REMOVAL in impacts:
                diff.overall_compatibility = ABICompatibility.ABI_BREAKING_REMOVAL
            elif ABICompatibility.ABI_BREAKING_SIGNATURE in impacts:
                diff.overall_compatibility = ABICompatibility.ABI_BREAKING_SIGNATURE
            else:
                diff.overall_compatibility = ABICompatibility.ABI_BREAKING_LAYOUT
        elif changes:
            # All compatible
            diff.overall_compatibility = ABICompatibility.ABI_COMPATIBLE_EXTENSION
        else:
            # No structural changes detected but fingerprints differ
            # This indicates metadata or other non-structural changes
            diff.overall_compatibility = ABICompatibility.ABI_COMPATIBLE_EXTENSION

        return diff

    def _detect_function_changes(
        self, baseline_functions: List[Any], candidate_functions: List[Any]
    ) -> List[ContractChange]:
        """Detect changes to function signatures."""
        changes = []

        # Convert to dictionaries or lists of entities for comparison
        # This implementation assumes entities are dicts with 'id' or objects with 'function_id'
        def get_id(f):
            if isinstance(f, dict):
                return f.get("function_id") or f.get("id")
            return getattr(f, "function_id", None) or getattr(f, "id", None)

        baseline_map = {get_id(f): f for f in baseline_functions if get_id(f)}
        candidate_map = {get_id(f): f for f in candidate_functions if get_id(f)}

        # Detect additions
        added = set(candidate_map.keys()) - set(baseline_map.keys())
        for func_id in added:
            changes.append(
                ContractChange(
                    change_type=ChangeType.FUNCTION_ADDED,
                    entity_id=func_id,
                    description=f"Function '{func_id}' added",
                    abi_impact=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
                )
            )

        # Detect removals
        removed = set(baseline_map.keys()) - set(candidate_map.keys())
        for func_id in removed:
            changes.append(
                ContractChange(
                    change_type=ChangeType.FUNCTION_REMOVED,
                    entity_id=func_id,
                    description=f"Function '{func_id}' removed",
                    abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
                )
            )

        # Detect modifications (simplified)
        common = set(baseline_map.keys()) & set(candidate_map.keys())
        for func_id in common:
            # In real system, we'd compare signature properties
            # This is a placeholder for detection logic
            pass

        return changes

    def _detect_struct_changes(
        self, baseline_structs: List[Any], candidate_structs: List[Any]
    ) -> List[ContractChange]:
        """Detect changes to struct layouts."""
        changes = []

        def get_id(s):
            if isinstance(s, dict):
                return s.get("struct_id") or s.get("id")
            return getattr(s, "struct_id", None) or getattr(s, "id", None)

        baseline_map = {get_id(s): s for s in baseline_structs if get_id(s)}
        candidate_map = {get_id(s): s for s in candidate_structs if get_id(s)}

        # Detect additions/removals
        added = set(candidate_map.keys()) - set(baseline_map.keys())
        for struct_id in added:
            changes.append(
                ContractChange(
                    change_type=ChangeType.TYPE_ADDED,
                    entity_id=struct_id,
                    description=f"Struct '{struct_id}' added",
                    abi_impact=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
                )
            )

        removed = set(baseline_map.keys()) - set(candidate_map.keys())
        for struct_id in removed:
            changes.append(
                ContractChange(
                    change_type=ChangeType.TYPE_REMOVED,
                    entity_id=struct_id,
                    description=f"Struct '{struct_id}' removed",
                    abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
                )
            )

        return changes


# ============================================================================
# MIGRATION NECESSITY ANALYZER
# ============================================================================
@dataclass
class MigrationNecessity:
    """Analysis of whether migration is required.
    Provides detailed assessment of upgrade requirements.
    """

    required: bool
    reason: str
    affected_entities: List[str] = field(default_factory=list)
    migration_complexity: str = "unknown"  # "trivial", "moderate", "complex"
    estimated_effort: str = "unknown"  # "minutes", "hours", "days"
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "required": self.required,
            "reason": self.reason,
            "affected_entities": self.affected_entities,
            "migration_complexity": self.migration_complexity,
            "estimated_effort": self.estimated_effort,
            "recommendations": self.recommendations,
        }


class MigrationNecessityAnalyzer:
    """Analyzes whether migration is needed between contract versions.
    Provides detailed recommendations based on change analysis.
    """

    def analyze(self, diff: ContractDiff) -> MigrationNecessity:
        """
        Analyze migration necessity.
        Args:
            diff: Contract diff to analyze
        Returns:
            MigrationNecessity with analysis results
        """
        # Check for breaking changes
        if diff.has_breaking_changes():
            breaking = diff.get_breaking_changes()

            return MigrationNecessity(
                required=True,
                reason="ABI-breaking changes detected",
                affected_entities=[c.entity_id for c in breaking],
                migration_complexity=self._assess_complexity(breaking),
                estimated_effort=self._estimate_effort(breaking),
                recommendations=self._generate_recommendations(breaking),
            )

        # No breaking changes
        return MigrationNecessity(
            required=False,
            reason="All changes are ABI-compatible",
            migration_complexity="trivial",
            estimated_effort="none",
            recommendations=["Safe to upgrade without migration"],
        )

    def _assess_complexity(self, changes: List[ContractChange]) -> str:
        """Assess migration complexity based on changes."""
        if len(changes) <= 2:
            return "trivial"
        elif len(changes) <= 10:
            return "moderate"
        else:
            return "complex"

    def _estimate_effort(self, changes: List[ContractChange]) -> str:
        """Estimate migration effort."""
        if len(changes) <= 2:
            return "minutes"
        elif len(changes) <= 10:
            return "hours"
        else:
            return "days"

    def _generate_recommendations(self, changes: List[ContractChange]) -> List[str]:
        """Generate migration recommendations."""
        recommendations = []

        for change in changes:
            if change.change_type == ChangeType.FUNCTION_REMOVED:
                recommendations.append(f"Remove calls to deleted function '{change.entity_id}'")
            elif change.change_type == ChangeType.FUNCTION_MODIFIED:
                recommendations.append(f"Update calls to modified function '{change.entity_id}'")
            elif change.change_type == ChangeType.TYPE_REMOVED:
                recommendations.append(f"Replace usage of deleted type '{change.entity_id}'")

        return recommendations


# ============================================================================
# CONTRACT VERSION COMPARATOR
# ============================================================================
class ContractVersionComparator:
    """High-level contract version comparison.
    Combines ABI detection, migration analysis, and compatibility checking.
    """

    def __init__(self):
        self.abi_detector = ABICompatibilityDetector()
        self.migration_analyzer = MigrationNecessityAnalyzer()

    def compare(self, baseline_contract: Any, candidate_contract: Any) -> Dict[str, Any]:
        """
        Compare two contract versions.
        Args:
            baseline_contract: Old contract
            candidate_contract: New contract
        Returns:
            Dictionary with complete comparison results
        """
        # Detect ABI compatibility
        diff = self.abi_detector.detect_compatibility(baseline_contract, candidate_contract)

        # Analyze migration necessity
        migration = self.migration_analyzer.analyze(diff)

        return {
            "diff": diff.to_dict(),
            "migration": migration.to_dict(),
            "summary": {
                "safe_upgrade": not migration.required,
                "breaking_changes_count": len(diff.get_breaking_changes()),
                "compatible_changes_count": len(diff.get_compatible_changes()),
                "overall_compatibility": diff.overall_compatibility.value
                if diff.overall_compatibility
                else None,
            },
        }


# ============================================================================
# COMPATIBILITY RELATIONSHIPS
# ============================================================================
class CompatibilityRelationship(Enum):
    """Compatibility relationships between version pairs.
    Defines directional compatibility semantics.
    """

    IDENTICAL = "identical"
    BACKWARD_COMPATIBLE = "backward_compatible"
    FORWARD_COMPATIBLE = "forward_compatible"
    BI_DIRECTIONAL = "bi_directional"
    BREAKING_INCOMPATIBLE = "breaking_incompatible"
    UPGRADE_WITH_MIGRATION = "upgrade_with_migration"


# ============================================================================
# VERSION RANGE SPECIFICATION
# ============================================================================
@dataclass
class VersionConstraintComponent:
    """Single version constraint component (e.g., >=1.2.0).
    Represents one part of a multi-version range specification.
    """

    operator: str  # "==", "!=", "<", "<=", ">", ">="
    version: str

    def satisfied_by(self, version: str) -> bool:
        """
        Check if a version satisfies this constraint component.
        Args:
            version: Version to check
        Returns:
            True if constraint satisfied
        """
        try:
            v = SemanticVersion.parse(version)
            constraint_v = SemanticVersion.parse(self.version)
        except ValueError:
            return False

        if self.operator == "==":
            return v == constraint_v
        elif self.operator == "!=":
            return v != constraint_v
        elif self.operator == "<":
            return v < constraint_v
        elif self.operator == "<=":
            return v <= constraint_v
        elif self.operator == ">":
            return v > constraint_v
        elif self.operator == ">=":
            return v >= constraint_v
        else:
            return False


class VersionRange:
    """Version range specification parser and checker.
    Supports npm-style range syntax (^, ~, *, ranges).
    """

    def __init__(self, range_spec: str):
        """
        Initialize version range.
        Args:
            range_spec: Range specification string
                       (e.g., "^1.2.0", "~1.2.0", ">=1.0.0, <2.0.0")
        """
        self.range_spec = range_spec
        self.constraints = self._parse_range(range_spec)

    def _parse_range(self, spec: str) -> List[VersionConstraintComponent]:
        """Parse range specification into constraints."""
        constraints = []
        spec = spec.strip()

        # Caret range: ^1.2.3 → >=1.2.3, <2.0.0
        if spec.startswith("^"):
            version = spec[1:]
            v = SemanticVersion(version)
            constraints.append(VersionConstraintComponent(">=", version))
            constraints.append(VersionConstraintComponent("<", f"{v.major + 1}.0.0"))

        # Tilde range: ~1.2.3 → >=1.2.3, <1.3.0
        elif spec.startswith("~"):
            version = spec[1:]
            v = SemanticVersion(version)
            constraints.append(VersionConstraintComponent(">=", version))
            constraints.append(VersionConstraintComponent("<", f"{v.major}.{v.minor + 1}.0"))

        # Wildcard: 1.2.* → >=1.2.0, <1.3.0
        elif "*" in spec:
            parts = spec.split(".")
            if parts[-1] == "*":
                if len(parts) == 3:
                    # 1.2.* → >=1.2.0, <1.3.0
                    major, minor = parts[0], parts[1]
                    constraints.append(VersionConstraintComponent(">=", f"{major}.{minor}.0"))
                    constraints.append(VersionConstraintComponent("<", f"{major}.{int(minor) + 1}.0"))
                elif len(parts) == 2:
                    # 1.* → >=1.0.0, <2.0.0
                    major = parts[0]
                    constraints.append(VersionConstraintComponent(">=", f"{major}.0.0"))
                    constraints.append(VersionConstraintComponent("<", f"{int(major) + 1}.0.0"))

        # Comma-separated constraints: >=1.0.0, <2.0.0
        elif "," in spec:
            for part in spec.split(","):
                part = part.strip()
                constraints.extend(self._parse_single_constraint(part))

        # Single constraint: >=1.0.0
        else:
            constraints.extend(self._parse_single_constraint(spec))

        return constraints

    def _parse_single_constraint(self, spec: str) -> List[VersionConstraintComponent]:
        """Parse a single constraint like '>=1.0.0'."""
        # Match operator and version
        match = re.match(r"^\s*(==|!=|<=|>=|<|>)\s*(.+)$", spec)
        if match:
            operator, version = match.groups()
            return [VersionConstraintComponent(operator, version.strip())]

        # No operator means exact match
        return [VersionConstraintComponent("==", spec.strip())]

    def satisfied_by(self, version: str) -> bool:
        """
        Check if version satisfies this range.
        Args:
            version: Version to check
        Returns:
            True if all constraints satisfied
        """
        return all(c.satisfied_by(version) for c in self.constraints)

    def __str__(self) -> str:
        return self.range_spec


# ============================================================================
# COMPATIBILITY MATRIX
# ============================================================================
@dataclass
class VersionPairCompatibilityEntry:
    """Single entry in version pair compatibility matrix.
    Records compatibility relationship between two versions of the same contract.
    """

    from_version: str
    to_version: str
    relationship: CompatibilityRelationship
    abi_compatibility: Optional[ABICompatibility] = None
    migration_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "relationship": self.relationship.value,
            "abi_compatibility": self.abi_compatibility.value if self.abi_compatibility else None,
            "migration_required": self.migration_required,
        }


class VersionPairCompatibilityMatrix:
    """Matrix of compatibility relationships between all version pairs of a contract.
    Provides O(1) lookup of compatibility between any two versions.
    """

    def __init__(self):
        self.matrix: Dict[Tuple[str, str], VersionPairCompatibilityEntry] = {}
        self.versions: Set[str] = set()

    def add_entry(self, entry: VersionPairCompatibilityEntry):
        """
        Add a compatibility entry to matrix.
        Args:
            entry: Compatibility entry
        """
        key = (entry.from_version, entry.to_version)
        self.matrix[key] = entry
        self.versions.add(entry.from_version)
        self.versions.add(entry.to_version)

    def get_compatibility(self, from_version: str, to_version: str) -> Optional[VersionPairCompatibilityEntry]:
        """
        Get compatibility between two versions.
        Args:
            from_version: Source version
            to_version: Target version
        Returns:
            VersionPairCompatibilityEntry if known, None otherwise
        """
        key = (from_version, to_version)
        return self.matrix.get(key)

    def is_compatible(self, from_version: str, to_version: str) -> bool:
        """
        Check if versions are compatible.
        Args:
            from_version: Source version
            to_version: Target version
        Returns:
            True if compatible
        """
        entry = self.get_compatibility(from_version, to_version)
        if not entry:
            return False

        return entry.relationship in [
            CompatibilityRelationship.IDENTICAL,
            CompatibilityRelationship.BACKWARD_COMPATIBLE,
            CompatibilityRelationship.BI_DIRECTIONAL,
        ]

    def get_all_versions(self) -> List[str]:
        """Get all versions in matrix."""
        return sorted(list(self.versions), key=lambda v: SemanticVersion(v))

    def to_dict(self) -> Dict[str, Any]:
        """Convert matrix to dictionary."""
        return {
            "entries": [e.to_dict() for e in self.matrix.values()],
            "versions": self.get_all_versions(),
        }


# ============================================================================
# COMPATIBILITY MATRIX BUILDER
# ============================================================================
class VersionPairCompatibilityBuilder:
    """Builds pairwise compatibility matrix for a set of versions of the same contract.
    Computes pairwise compatibility and populates matrix.
    """

    def __init__(self, abi_detector: Optional[ABICompatibilityDetector] = None):
        self.abi_detector = abi_detector or ABICompatibilityDetector()
        self.cache: Dict[Tuple[str, str], VersionPairCompatibilityEntry] = {}

    def build_matrix(self, versions: List[str], contracts: Dict[str, Any]) -> VersionPairCompatibilityMatrix:
        """
        Build compatibility matrix for given versions.
        Args:
            versions: List of version strings
            contracts: Mapping of version → contract object
        Returns:
            Populated VersionPairCompatibilityMatrix
        """
        matrix = VersionPairCompatibilityMatrix()

        for v1 in versions:
            for v2 in versions:
                entry = self._compute_compatibility(v1, v2, contracts)
                matrix.add_entry(entry)

        return matrix

    def _compute_compatibility(
        self, from_version: str, to_version: str, contracts: Dict[str, Any]
    ) -> VersionPairCompatibilityEntry:
        """Compute compatibility between two versions."""
        # Check cache
        cache_key = (from_version, to_version)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Identical versions
        if from_version == to_version:
            entry = VersionPairCompatibilityEntry(
                from_version=from_version,
                to_version=to_version,
                relationship=CompatibilityRelationship.IDENTICAL,
                migration_required=False,
            )
            self.cache[cache_key] = entry
            return entry

        # Compare versions
        try:
            v1 = SemanticVersion(from_version)
            v2 = SemanticVersion(to_version)
        except ValueError:
            # Unknown versions
            entry = VersionPairCompatibilityEntry(
                from_version=from_version,
                to_version=to_version,
                relationship=CompatibilityRelationship.BREAKING_INCOMPATIBLE,
                migration_required=True,
            )
            self.cache[cache_key] = entry
            return entry

        # Major version difference → breaking
        if v1.major != v2.major:
            entry = VersionPairCompatibilityEntry(
                from_version=from_version,
                to_version=to_version,
                relationship=CompatibilityRelationship.BREAKING_INCOMPATIBLE,
                migration_required=True,
            )

        # Minor/patch version difference → backward compatible
        elif v2 > v1:
            entry = VersionPairCompatibilityEntry(
                from_version=from_version,
                to_version=to_version,
                relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
                migration_required=False,
            )

        # Older version → forward compatible (rare)
        else:
            entry = VersionPairCompatibilityEntry(
                from_version=from_version,
                to_version=to_version,
                relationship=CompatibilityRelationship.FORWARD_COMPATIBLE,
                migration_required=False,
            )

        self.cache[cache_key] = entry
        return entry


# ============================================================================
# UPGRADE PATH FINDER
# ============================================================================
@dataclass
class UpgradePath:
    """Path from one version to another.
    Represents a sequence of version transitions.
    """

    from_version: str
    to_version: str
    steps: List[str]
    total_cost: int
    migration_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "steps": self.steps,
            "total_cost": self.total_cost,
            "migration_required": self.migration_required,
        }


class UpgradePathFinder:
    """Finds optimal upgrade paths between versions.
    Uses graph search to find lowest-cost paths.
    """

    def __init__(self, compatibility_matrix: VersionPairCompatibilityMatrix):
        self.matrix = compatibility_matrix

    def find_path(self, from_version: str, to_version: str) -> Optional[UpgradePath]:
        """
        Find upgrade path from source to target version.
        Args:
            from_version: Source version
            to_version: Target version
        Returns:
            UpgradePath if path exists, None otherwise
        """
        # Simple implementation: direct path only
        # Production would use Dijkstra's algorithm for multi-step paths

        entry = self.matrix.get_compatibility(from_version, to_version)
        if not entry:
            return None

        # Direct path
        cost = self._compute_cost(entry.relationship)

        return UpgradePath(
            from_version=from_version,
            to_version=to_version,
            steps=[from_version, to_version],
            total_cost=cost,
            migration_required=entry.migration_required,
        )

    def _compute_cost(self, relationship: CompatibilityRelationship) -> int:
        """Compute cost of a compatibility relationship."""
        cost_map = {
            CompatibilityRelationship.IDENTICAL: 0,
            CompatibilityRelationship.BACKWARD_COMPATIBLE: 1,
            CompatibilityRelationship.BI_DIRECTIONAL: 1,
            CompatibilityRelationship.FORWARD_COMPATIBLE: 5,
            CompatibilityRelationship.UPGRADE_WITH_MIGRATION: 10,
            CompatibilityRelationship.BREAKING_INCOMPATIBLE: 100,
        }
        return cost_map.get(relationship, 1000)


# ============================================================================
# DEPENDENCY RESOLVER
# ============================================================================
class VersionResolver:
    """Simple version resolver across multiple requirements.
    Finds versions that satisfy all constraints.
    """

    def __init__(self, available_versions: List[str]):
        self.available_versions = available_versions

    def resolve(self, requirements: List[str]) -> Optional[str]:
        """
        Resolve dependencies to find compatible version.
        Args:
            requirements: List of version range specifications
        Returns:
            Latest version satisfying all requirements, or None
        """
        # Parse all requirements
        ranges = [VersionRange(req) for req in requirements]

        # Find candidates satisfying all
        candidates = []
        for version in self.available_versions:
            if all(r.satisfied_by(version) for r in ranges):
                candidates.append(version)

        if not candidates:
            return None

        # Return latest
        return max(candidates, key=lambda v: SemanticVersion.parse(v))


# ============================================================================
# POLICY FRAMEWORK
# ============================================================================
class PolicyLevel(Enum):
    """Policy enforcement levels."""

    STRICT = "strict"
    MODERATE = "moderate"
    PERMISSIVE = "permissive"


class AdvisorySeverity(Enum):
    """Advisory severity levels."""

    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"
    BLOCK = "block"


@dataclass
class CompatibilityPolicy:
    """Compatibility enforcement policy.
    Defines what changes are allowed and what requires approval.
    """

    level: PolicyLevel
    allow_breaking_changes: bool = False
    allow_relaxation: bool = False
    allow_strengthening: bool = True
    require_approval_for_breaking: bool = True
    require_approval_for_relaxation: bool = True
    block_on_unknown: bool = True

    @classmethod
    def strict(cls) -> "CompatibilityPolicy":
        """Create strict policy (production)."""
        return cls(
            level=PolicyLevel.STRICT,
            allow_breaking_changes=False,
            allow_relaxation=False,
            allow_strengthening=True,
            require_approval_for_breaking=True,
            require_approval_for_relaxation=True,
            block_on_unknown=True,
        )

    @classmethod
    def moderate(cls) -> "CompatibilityPolicy":
        """Create moderate policy (development)."""
        return cls(
            level=PolicyLevel.MODERATE,
            allow_breaking_changes=True,
            allow_relaxation=True,
            allow_strengthening=True,
            require_approval_for_breaking=True,
            require_approval_for_relaxation=True,
            block_on_unknown=True,
        )

    @classmethod
    def permissive(cls) -> "CompatibilityPolicy":
        """Create permissive policy (feature branches)."""
        return cls(
            level=PolicyLevel.PERMISSIVE,
            allow_breaking_changes=True,
            allow_relaxation=True,
            allow_strengthening=True,
            require_approval_for_breaking=False,
            require_approval_for_relaxation=False,
            block_on_unknown=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "allow_breaking_changes": self.allow_breaking_changes,
            "allow_relaxation": self.allow_relaxation,
            "allow_strengthening": self.allow_strengthening,
            "require_approval_for_breaking": self.require_approval_for_breaking,
            "require_approval_for_relaxation": self.require_approval_for_relaxation,
            "block_on_unknown": self.block_on_unknown,
        }


# ============================================================================
# COMPATIBILITY ADVISORY
# ============================================================================
@dataclass
class CompatibilityAdvisory:
    """Compatibility advisory with recommendations.
    Provides actionable guidance based on compatibility analysis.
    """

    severity: AdvisorySeverity
    title: str
    summary: str
    details: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    affected_entities: List[str] = field(default_factory=list)
    approval_required: bool = False
    upgrade_path: Optional[UpgradePath] = None

    def is_blocking(self) -> bool:
        """Check if advisory should block CI."""
        return self.severity in [AdvisorySeverity.ERROR, AdvisorySeverity.BLOCK]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "title": self.title,
            "summary": self.summary,
            "details": self.details,
            "recommendations": self.recommendations,
            "affected_entities": self.affected_entities,
            "approval_required": self.approval_required,
            "upgrade_path": self.upgrade_path.to_dict() if self.upgrade_path else None,
        }

    def to_markdown(self) -> str:
        """Format as Markdown for GitHub comments."""
        severity_icons = {
            AdvisorySeverity.PASS: "✓",
            AdvisorySeverity.WARNING: "⚠",
            AdvisorySeverity.ERROR: "✗",
            AdvisorySeverity.BLOCK: "⛔",
        }

        icon = severity_icons.get(self.severity, "•")

        md = f"## {icon} {self.title}\n\n"
        md += f"{self.summary}\n\n"

        if self.details:
            md += "### Changes\n"
            for detail in self.details:
                md += f"- {detail}\n"
            md += "\n"

        if self.recommendations:
            md += "### Recommendations\n"
            for rec in self.recommendations:
                md += f"- {rec}\n"
            md += "\n"

        if self.approval_required:
            md += "**⚠ Approval Required**: YES\n"

        return md


# ============================================================================
# ADVISORY GENERATOR
# ============================================================================
class AdvisoryGenerator:
    """Generates compatibility advisories from diff analysis.
    Produces human-readable recommendations.
    """

    def generate(self, diff: ContractDiff, policy: CompatibilityPolicy) -> CompatibilityAdvisory:
        """
        Generate advisory from diff and policy.
        Args:
            diff: Contract diff
            policy: Compatibility policy
        Returns:
            CompatibilityAdvisory
        """
        # Check for breaking changes
        if diff.has_breaking_changes():
            return self._generate_breaking_advisory(diff, policy)

        # Check for relaxation
        if self._has_relaxation(diff):
            return self._generate_relaxation_advisory(diff, policy)

        # Check for strengthening
        if self._has_strengthening(diff):
            return self._generate_strengthening_advisory(diff, policy)

        # No significant changes
        return self._generate_pass_advisory(diff)

    def _generate_breaking_advisory(self, diff: ContractDiff, policy: CompatibilityPolicy) -> CompatibilityAdvisory:
        """Generate advisory for breaking changes."""
        breaking = diff.get_breaking_changes()

        severity = AdvisorySeverity.ERROR
        if not policy.allow_breaking_changes:
            severity = AdvisorySeverity.BLOCK

        details = [f"BREAKING: {change.description}" for change in breaking]

        recommendations = ["Migration required", "Update all bindings", "Bump major version"]

        if policy.require_approval_for_breaking:
            recommendations.append("Obtain approval before merging")

        return CompatibilityAdvisory(
            severity=severity,
            title="Breaking Changes Detected",
            summary=f"{len(breaking)} ABI-breaking change(s) detected",
            details=details,
            recommendations=recommendations,
            affected_entities=[c.entity_id for c in breaking],
            approval_required=policy.require_approval_for_breaking,
        )

    def _generate_relaxation_advisory(self, diff: ContractDiff, policy: CompatibilityPolicy) -> CompatibilityAdvisory:
        """Generate advisory for constraint relaxation."""
        relaxed = [c for c in diff.changes if c.abi_impact == ABICompatibility.ABI_COMPATIBLE_RELAXATION]

        severity = AdvisorySeverity.WARNING

        details = [f"RELAXED: {c.description}" for c in relaxed]

        recommendations = ["Review runtime impact", "Ensure backward compatibility", "Consider security implications"]

        return CompatibilityAdvisory(
            severity=severity,
            title="Constraints Relaxed",
            summary=f"{len(relaxed)} constraint(s) relaxed",
            details=details,
            recommendations=recommendations,
            approval_required=policy.require_approval_for_relaxation,
        )

    def _generate_strengthening_advisory(self, diff: ContractDiff, policy: CompatibilityPolicy) -> CompatibilityAdvisory:
        """Generate advisory for strengthened constraints."""
        strengthened = [c for c in diff.changes if c.abi_impact == ABICompatibility.ABI_COMPATIBLE_STRENGTHENING]

        details = [f"STRENGTHENED: {c.description}" for c in strengthened]

        recommendations = ["Review runtime validation impact", "Ensure clients provide valid data", "Safe to merge"]

        return CompatibilityAdvisory(
            severity=AdvisorySeverity.WARNING,
            title="Constraints Strengthened",
            summary=f"{len(strengthened)} constraint(s) strengthened",
            details=details,
            recommendations=recommendations,
            approval_required=False,
        )

    def _generate_pass_advisory(self, diff: ContractDiff) -> CompatibilityAdvisory:
        """Generate pass advisory (no issues)."""
        compatible = diff.get_compatible_changes()

        details = [c.description for c in compatible]

        return CompatibilityAdvisory(
            severity=AdvisorySeverity.PASS,
            title="Fully Compatible",
            summary="All changes are backward compatible",
            details=details,
            recommendations=["Safe to merge", "No migration required"],
            approval_required=False,
        )

    def _has_relaxation(self, diff: ContractDiff) -> bool:
        """Check if diff contains relaxation."""
        return any(c.abi_impact == ABICompatibility.ABI_COMPATIBLE_RELAXATION for c in diff.changes)

    def _has_strengthening(self, diff: ContractDiff) -> bool:
        """Check if diff contains strengthening."""
        return any(c.abi_impact == ABICompatibility.ABI_COMPATIBLE_STRENGTHENING for c in diff.changes)


# ============================================================================
# BASELINE MANAGER
# ============================================================================
class BaselineSource(Enum):
    """Sources for baseline contracts."""

    BRANCH = "branch"
    TAG = "tag"
    FILE = "file"
    EXPLICIT = "explicit"


@dataclass
class BaselineConfig:
    """Configuration for baseline selection."""

    source: BaselineSource
    value: str  # Branch name, tag, file path, or explicit contract

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"source": self.source.value, "value": self.value}


class BaselineManager:
    """Manages baseline contract selection.
    Handles different baseline strategies.
    """

    def get_baseline(self, config: BaselineConfig) -> Optional[Any]:
        """
        Get baseline contract from configuration.
        Args:
            config: Baseline configuration
        Returns:
            Baseline contract object or None
        """
        if config.source == BaselineSource.BRANCH:
            return self._get_from_branch(config.value)
        elif config.source == BaselineSource.TAG:
            return self._get_from_tag(config.value)
        elif config.source == BaselineSource.FILE:
            return self._get_from_file(config.value)
        elif config.source == BaselineSource.EXPLICIT:
            return self._get_explicit(config.value)
        else:
            return None

    def _get_from_branch(self, branch: str) -> Optional[Any]:
        """Get baseline from git branch."""
        # Placeholder - real implementation would:
        # 1. Checkout branch
        # 2. Load contract from branch
        # 3. Return to current branch
        return None

    def _get_from_tag(self, tag: str) -> Optional[Any]:
        """Get baseline from git tag."""
        # Placeholder - real implementation would:
        # 1. Checkout tag
        # 2. Load contract from tag
        # 3. Return to current state
        return None

    def _get_from_file(self, path: str) -> Optional[Any]:
        """Get baseline from file path."""
        # Placeholder - real implementation would load from file
        return None

    def _get_explicit(self, contract_json: str) -> Optional[Any]:
        """Get baseline from explicit JSON string."""
        # Placeholder - real implementation would parse JSON
        return None


# ============================================================================
# CI/CD COMPATIBILITY CHECKER
# ============================================================================
@dataclass
class CompatibilityCheckResult:
    """Result of CI/CD compatibility check."""

    passed: bool
    advisory: CompatibilityAdvisory
    diff: ContractDiff
    policy: CompatibilityPolicy

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "advisory": self.advisory.to_dict(),
            "diff": self.diff.to_dict(),
            "policy": self.policy.to_dict(),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class CICDCompatibilityChecker:
    """CI/CD integration for compatibility checking.
    Orchestrates baseline loading, comparison, policy application, and
    advisory generation.
    """

    def __init__(self):
        self.abi_detector = ABICompatibilityDetector()
        self.advisory_generator = AdvisoryGenerator()
        self.baseline_manager = BaselineManager()

    def check(
        self, baseline_config: BaselineConfig, candidate_contract: Any, policy: CompatibilityPolicy
    ) -> CompatibilityCheckResult:
        """
        Perform CI/CD compatibility check.
        Args:
            baseline_config: How to get baseline
            candidate_contract: New contract to check
            policy: Enforcement policy
        Returns:
            CompatibilityCheckResult
        """
        # Get baseline
        baseline = self.baseline_manager.get_baseline(baseline_config)

        if baseline is None:
            # No baseline available
            advisory = CompatibilityAdvisory(
                severity=AdvisorySeverity.BLOCK,
                title="Baseline Not Found",
                summary="Unable to load baseline contract",
                recommendations=["Verify baseline configuration", "Ensure baseline source exists"],
            )

            # Create empty diff
            diff = ContractDiff(
                baseline_version="unknown",
                candidate_version=getattr(candidate_contract, "contract_version", "unknown"),
                baseline_fingerprint="",
                candidate_fingerprint=getattr(candidate_contract, "contract_fingerprint", ""),
            )

            return CompatibilityCheckResult(passed=False, advisory=advisory, diff=diff, policy=policy)

        # Compute diff
        diff = self.abi_detector.detect_compatibility(baseline, candidate_contract)

        # Generate advisory
        advisory = self.advisory_generator.generate(diff, policy)

        # Determine pass/fail
        passed = not advisory.is_blocking()

        return CompatibilityCheckResult(passed=passed, advisory=advisory, diff=diff, policy=policy)


# ============================================================================
# CHANGE SEVERITY
# ============================================================================
class ChangeSeverity(Enum):
    """Severity of individual changes."""

    BREAKING = "breaking"
    EXTENSION = "extension"
    STRENGTHENING = "strengthening"
    RELAXATION = "relaxation"
    NOTABLE = "notable"
    NEUTRAL = "neutral"


# ============================================================================
# DETAILED CHANGE ENTITIES
# ============================================================================
@dataclass
class DetailedChange:
    """Detailed description of a single change.
    Captures what changed, where, and why it matters.
    """

    change_type: str
    entity_id: str
    severity: ChangeSeverity
    description: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    location: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type,
            "entity_id": self.entity_id,
            "severity": self.severity.value,
            "description": self.description,
            "old_value": str(self.old_value) if self.old_value is not None else None,
            "new_value": str(self.new_value) if self.new_value is not None else None,
            "location": self.location,
            "details": self.details,
        }


@dataclass
class EntityDiff:
    """Diff for a single entity (function, struct, etc.).
    Groups all changes for one entity.
    """

    entity_id: str
    entity_type: str
    changes: List[DetailedChange] = field(default_factory=list)

    def has_breaking_changes(self) -> bool:
        """Check if entity has breaking changes."""
        return any(c.severity == ChangeSeverity.BREAKING for c in self.changes)

    def get_most_severe_change(self) -> Optional[DetailedChange]:
        """Get most severe change for this entity."""
        if not self.changes:
            return None

        priority = {
            ChangeSeverity.BREAKING: 0,
            ChangeSeverity.RELAXATION: 1,
            ChangeSeverity.STRENGTHENING: 2,
            ChangeSeverity.EXTENSION: 3,
            ChangeSeverity.NOTABLE: 4,
            ChangeSeverity.NEUTRAL: 5,
        }

        return min(self.changes, key=lambda c: priority.get(c.severity, 99))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "changes": [c.to_dict() for c in self.changes],
            "has_breaking_changes": self.has_breaking_changes(),
        }


# ============================================================================
# DETAILED DIFF RESULT
# ============================================================================
@dataclass
class DetailedDiff:
    """Complete detailed diff between two contracts.
    Contains granular change analysis at all levels.
    """

    baseline_version: str
    candidate_version: str
    baseline_fingerprint: str
    candidate_fingerprint: str
    entity_diffs: List[EntityDiff] = field(default_factory=list)

    def get_all_changes(self) -> List[DetailedChange]:
        """Get all changes across all entities."""
        all_changes = []
        for entity_diff in self.entity_diffs:
            all_changes.extend(entity_diff.changes)
        return all_changes

    def filter_by_severity(self, severity: ChangeSeverity) -> List[DetailedChange]:
        """Get all changes with specific severity."""
        return [c for c in self.get_all_changes() if c.severity == severity]

    def filter_by_entity_type(self, entity_type: str) -> List[EntityDiff]:
        """Get all entity diffs of specific type."""
        return [e for e in self.entity_diffs if e.entity_type == entity_type]

    def get_breaking_changes(self) -> List[DetailedChange]:
        """Get all breaking changes."""
        return self.filter_by_severity(ChangeSeverity.BREAKING)

    def get_statistics(self) -> Dict[str, Any]:
        """Get diff statistics."""
        all_changes = self.get_all_changes()

        by_severity = {}
        for severity in ChangeSeverity:
            count = len([c for c in all_changes if c.severity == severity])
            by_severity[severity.value] = count

        by_entity_type = {}
        for entity_diff in self.entity_diffs:
            entity_type = entity_diff.entity_type
            by_entity_type[entity_type] = by_entity_type.get(entity_type, 0) + 1

        return {
            "total_changes": len(all_changes),
            "total_entities_changed": len(self.entity_diffs),
            "by_severity": by_severity,
            "by_entity_type": by_entity_type,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline_version": self.baseline_version,
            "candidate_version": self.candidate_version,
            "baseline_fingerprint": self.baseline_fingerprint,
            "candidate_fingerprint": self.candidate_fingerprint,
            "entity_diffs": [e.to_dict() for e in self.entity_diffs],
            "statistics": self.get_statistics(),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# DIFF ANALYZER
# ============================================================================
class DetailedDiffAnalyzer:
    """Computes detailed diffs between contracts.
    Performs granular comparison at all levels.
    """

    def analyze(self, baseline_contract: Any, candidate_contract: Any) -> DetailedDiff:
        """
        Compute detailed diff.
        Args:
            baseline_contract: Old contract
            candidate_contract: New contract
        Returns:
            DetailedDiff with granular changes
        """
        diff = DetailedDiff(
            baseline_version=getattr(baseline_contract, "contract_version", "unknown"),
            candidate_version=getattr(candidate_contract, "contract_version", "unknown"),
            baseline_fingerprint=getattr(baseline_contract, "contract_fingerprint", ""),
            candidate_fingerprint=getattr(candidate_contract, "contract_fingerprint", ""),
        )

        # Analyze functions (placeholder)
        function_diffs = self._analyze_functions(baseline_contract, candidate_contract)
        diff.entity_diffs.extend(function_diffs)

        # Analyze types (placeholder)
        type_diffs = self._analyze_types(baseline_contract, candidate_contract)
        diff.entity_diffs.extend(type_diffs)

        # Analyze clauses (placeholder)
        clause_diffs = self._analyze_clauses(baseline_contract, candidate_contract)
        diff.entity_diffs.extend(clause_diffs)

        return diff

    def _analyze_functions(self, baseline: Any, candidate: Any) -> List[EntityDiff]:
        """Analyze function changes."""
        return []

    def _analyze_types(self, baseline: Any, candidate: Any) -> List[EntityDiff]:
        """Analyze type changes."""
        return []

    def _analyze_clauses(self, baseline: Any, candidate: Any) -> List[EntityDiff]:
        """Analyze clause changes."""
        return []


# ============================================================================
# STRUCT LAYOUT ANALYZER
# ============================================================================
class StructLayoutAnalyzer:
    """Analyzes struct layout changes in detail.
    Detects size, alignment, and field offset changes.
    """

    def analyze_struct(self, baseline_struct: Dict[str, Any], candidate_struct: Dict[str, Any], struct_id: str) -> EntityDiff:
        """
        Analyze struct changes.
        Args:
            baseline_struct: Old struct definition
            candidate_struct: New struct definition
            struct_id: Struct identifier
        Returns:
            EntityDiff for struct
        """
        entity_diff = EntityDiff(entity_id=struct_id, entity_type="struct")

        # Check size change
        baseline_size = baseline_struct.get("size_bytes", 0)
        candidate_size = candidate_struct.get("size_bytes", 0)

        if baseline_size != candidate_size:
            entity_diff.changes.append(
                DetailedChange(
                    change_type="size_changed",
                    entity_id=struct_id,
                    severity=ChangeSeverity.BREAKING,
                    description=f"Struct size changed from {baseline_size} to {candidate_size} bytes",
                    old_value=baseline_size,
                    new_value=candidate_size,
                )
            )

        # Check alignment change
        baseline_align = baseline_struct.get("alignment", 0)
        candidate_align = candidate_struct.get("alignment", 0)

        if baseline_align != candidate_align:
            entity_diff.changes.append(
                DetailedChange(
                    change_type="alignment_changed",
                    entity_id=struct_id,
                    severity=ChangeSeverity.BREAKING,
                    description=f"Struct alignment changed from {baseline_align} to {candidate_align}",
                    old_value=baseline_align,
                    new_value=candidate_align,
                )
            )

        # Analyze field changes
        baseline_fields = {f["name"]: f for f in baseline_struct.get("fields", [])}
        candidate_fields = {f["name"]: f for f in candidate_struct.get("fields", [])}

        # Added fields
        for name in candidate_fields.keys() - baseline_fields.keys():
            field_info = candidate_fields[name]
            offset = field_info.get("offset", 0)

            severity = ChangeSeverity.EXTENSION if offset >= baseline_size else ChangeSeverity.BREAKING

            entity_diff.changes.append(
                DetailedChange(
                    change_type="field_added",
                    entity_id=struct_id,
                    severity=severity,
                    description=f"Field '{name}' added at offset {offset}",
                    location=f"field '{name}'",
                    new_value=field_info,
                )
            )

        # Removed fields
        for name in baseline_fields.keys() - candidate_fields.keys():
            entity_diff.changes.append(
                DetailedChange(
                    change_type="field_removed",
                    entity_id=struct_id,
                    severity=ChangeSeverity.BREAKING,
                    description=f"Field '{name}' removed",
                    location=f"field '{name}'",
                )
            )

        # Modified fields
        for name in baseline_fields.keys() & candidate_fields.keys():
            baseline_field = baseline_fields[name]
            candidate_field = candidate_fields[name]

            baseline_offset = baseline_field.get("offset", 0)
            candidate_offset = candidate_field.get("offset", 0)

            if baseline_offset != candidate_offset:
                entity_diff.changes.append(
                    DetailedChange(
                        change_type="field_offset_changed",
                        entity_id=struct_id,
                        severity=ChangeSeverity.BREAKING,
                        description=f"Field '{name}' offset changed from {baseline_offset} to {candidate_offset}",
                        location=f"field '{name}'",
                        old_value=baseline_offset,
                        new_value=candidate_offset,
                    )
                )

        return entity_diff


# ============================================================================
# DIFF FORMATTER
# ============================================================================
class DiffFormatter:
    """Formats detailed diffs for various output formats.
    Supports text, JSON, and Markdown.
    """

    def format_text(self, diff: DetailedDiff) -> str:
        """Format diff as plain text."""
        lines = []

        lines.append(f"Contract Diff: {diff.baseline_version} → {diff.candidate_version}")
        lines.append("=" * 60)
        lines.append("")

        for entity_diff in diff.entity_diffs:
            if not entity_diff.changes:
                continue

            severity_badge = self._get_severity_badge(entity_diff.get_most_severe_change())
            lines.append(f"[{severity_badge}] {entity_diff.entity_id}")

            for change in entity_diff.changes:
                lines.append(f"  - {change.description}")

            lines.append("")

        stats = diff.get_statistics()
        lines.append("Summary:")
        lines.append(f"  Total changes: {stats['total_changes']}")
        lines.append(f"  Breaking: {stats['by_severity'].get('breaking', 0)}")
        lines.append(f"  Extensions: {stats['by_severity'].get('extension', 0)}")

        return "\n".join(lines)

    def format_markdown(self, diff: DetailedDiff) -> str:
        """Format diff as Markdown."""
        lines = []

        lines.append(f"# Contract Diff: {diff.baseline_version} → {diff.candidate_version}")
        lines.append("")

        breaking = diff.get_breaking_changes()
        if breaking:
            lines.append("## 🚨 Breaking Changes")
            lines.append("")
            for change in breaking:
                lines.append(f"- **{change.entity_id}**: {change.description}")
            lines.append("")

        stats = diff.get_statistics()
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Total changes: {stats['total_changes']}")
        lines.append(f"- Breaking: {stats['by_severity'].get('breaking', 0)}")
        lines.append(f"- Extensions: {stats['by_severity'].get('extension', 0)}")

        return "\n".join(lines)

    def _get_severity_badge(self, change: Optional[DetailedChange]) -> str:
        """Get severity badge text."""
        if not change:
            return "UNKNOWN"

        badges = {
            ChangeSeverity.BREAKING: "BREAKING",
            ChangeSeverity.EXTENSION: "EXTENSION",
            ChangeSeverity.STRENGTHENING: "STRENGTHENING",
            ChangeSeverity.RELAXATION: "RELAXATION",
            ChangeSeverity.NOTABLE: "NOTABLE",
            ChangeSeverity.NEUTRAL: "NEUTRAL",
        }

        return badges.get(change.severity, "UNKNOWN")


# ============================================================================
# FUNCTION SIGNATURE ANALYZER
# ============================================================================
class FunctionSignatureAnalyzer:
    """Analyzes function signature changes in detail.
    Detects parameter, return type, and calling convention changes.
    """

    def analyze_function(self, baseline_func: Dict[str, Any], candidate_func: Dict[str, Any], function_id: str) -> EntityDiff:
        """
        Analyze function signature changes.
        Args:
            baseline_func: Old function signature
            candidate_func: New function signature
            function_id: Function identifier
        Returns:
            EntityDiff for function
        """
        entity_diff = EntityDiff(entity_id=function_id, entity_type="function")

        # Check return type change
        baseline_return = baseline_func.get("return_type", "void")
        candidate_return = candidate_func.get("return_type", "void")

        if baseline_return != candidate_return:
            entity_diff.changes.append(
                DetailedChange(
                    change_type="return_type_changed",
                    entity_id=function_id,
                    severity=ChangeSeverity.BREAKING,
                    description=f"Return type changed from '{baseline_return}' to '{candidate_return}'",
                    location="return type",
                    old_value=baseline_return,
                    new_value=candidate_return,
                )
            )

        # Check calling convention change
        baseline_convention = baseline_func.get("calling_convention", "cdecl")
        candidate_convention = candidate_func.get("calling_convention", "cdecl")

        if baseline_convention != candidate_convention:
            entity_diff.changes.append(
                DetailedChange(
                    change_type="calling_convention_changed",
                    entity_id=function_id,
                    severity=ChangeSeverity.BREAKING,
                    description=f"Calling convention changed from '{baseline_convention}' to '{candidate_convention}'",
                    old_value=baseline_convention,
                    new_value=candidate_convention,
                )
            )

        # Analyze parameters
        baseline_params = baseline_func.get("parameters", [])
        candidate_params = candidate_func.get("parameters", [])

        param_changes = self._analyze_parameters(baseline_params, candidate_params, function_id)
        entity_diff.changes.extend(param_changes)

        return entity_diff

    def _analyze_parameters(
        self, baseline_params: List[Dict[str, Any]], candidate_params: List[Dict[str, Any]], function_id: str
    ) -> List[DetailedChange]:
        """Analyze parameter changes."""
        changes = []

        # Check parameter count change
        if len(baseline_params) != len(candidate_params):
            changes.append(
                DetailedChange(
                    change_type="parameter_count_changed",
                    entity_id=function_id,
                    severity=ChangeSeverity.BREAKING,
                    description=f"Parameter count changed from {len(baseline_params)} to {len(candidate_params)}",
                    old_value=len(baseline_params),
                    new_value=len(candidate_params),
                )
            )

        # Index baseline and candidate params by name
        baseline_by_name = {p.get("name", f"param_{i}"): (i, p) for i, p in enumerate(baseline_params)}
        candidate_by_name = {p.get("name", f"param_{i}"): (i, p) for i, p in enumerate(candidate_params)}

        # Detect added parameters
        added_names = set(candidate_by_name.keys()) - set(baseline_by_name.keys())
        for name in added_names:
            idx, param = candidate_by_name[name]
            param_type = param.get("type", "unknown")
            changes.append(
                DetailedChange(
                    change_type="parameter_added",
                    entity_id=function_id,
                    severity=ChangeSeverity.BREAKING,
                    description=f"Parameter '{name}' added at index {idx} (type: {param_type})",
                    location=f"parameter[{idx}]",
                    new_value=param,
                )
            )

        # Detect removed parameters
        removed_names = set(baseline_by_name.keys()) - set(candidate_by_name.keys())
        for name in removed_names:
            idx, param = baseline_by_name[name]
            param_type = param.get("type", "unknown")
            changes.append(
                DetailedChange(
                    change_type="parameter_removed",
                    entity_id=function_id,
                    severity=ChangeSeverity.BREAKING,
                    description=f"Parameter '{name}' removed from index {idx} (type: {param_type})",
                    location=f"parameter[{idx}]",
                    old_value=param,
                )
            )

        # Detect modified parameters (in both baseline and candidate)
        common_names = set(baseline_by_name.keys()) & set(candidate_by_name.keys())
        for name in common_names:
            baseline_idx, baseline_param = baseline_by_name[name]
            candidate_idx, candidate_param = candidate_by_name[name]

            # Check type change
            baseline_type = baseline_param.get("type", "unknown")
            candidate_type = candidate_param.get("type", "unknown")

            if baseline_type != candidate_type:
                changes.append(
                    DetailedChange(
                        change_type="parameter_type_changed",
                        entity_id=function_id,
                        severity=ChangeSeverity.BREAKING,
                        description=f"Parameter '{name}' type changed from '{baseline_type}' to '{candidate_type}'",
                        location=f"parameter[{candidate_idx}]",
                        old_value=baseline_type,
                        new_value=candidate_type,
                    )
                )

            # Check index change (reordering)
            if baseline_idx != candidate_idx:
                changes.append(
                    DetailedChange(
                        change_type="parameter_reordered",
                        entity_id=function_id,
                        severity=ChangeSeverity.BREAKING,
                        description=f"Parameter '{name}' moved from index {baseline_idx} to index {candidate_idx}",
                        location=f"parameter[{name}]",
                        old_value=baseline_idx,
                        new_value=candidate_idx,
                    )
                )

        return changes


# ============================================================================
# FUNCTION CATALOG ANALYZER
# ============================================================================
class FunctionCatalogAnalyzer:
    """Analyzes function catalog changes (additions/removals).
    Compares entire function sets between contract versions.
    """

    def __init__(self):
        self.signature_analyzer = FunctionSignatureAnalyzer()

    def analyze_functions(
        self, baseline_functions: Dict[str, Dict[str, Any]], candidate_functions: Dict[str, Dict[str, Any]]
    ) -> List[EntityDiff]:
        """
        Analyze function catalog changes.
        Args:
            baseline_functions: Dict of function_id -> function_signature
            candidate_functions: Dict of function_id -> function_signature
        Returns:
            List of EntityDiff for all changed functions
        """
        entity_diffs = []

        baseline_ids = set(baseline_functions.keys())
        candidate_ids = set(candidate_functions.keys())

        # Added functions
        for func_id in candidate_ids - baseline_ids:
            func = candidate_functions[func_id]
            entity_diff = EntityDiff(
                entity_id=func_id,
                entity_type="function",
                changes=[
                    DetailedChange(
                        change_type="function_added",
                        entity_id=func_id,
                        severity=ChangeSeverity.EXTENSION,
                        description=f"Function '{func_id}' added",
                        new_value=func,
                    )
                ],
            )
            entity_diffs.append(entity_diff)

        # Removed functions
        for func_id in baseline_ids - candidate_ids:
            func = baseline_functions[func_id]
            entity_diff = EntityDiff(
                entity_id=func_id,
                entity_type="function",
                changes=[
                    DetailedChange(
                        change_type="function_removed",
                        entity_id=func_id,
                        severity=ChangeSeverity.BREAKING,
                        description=f"Function '{func_id}' removed",
                        old_value=func,
                    )
                ],
            )
            entity_diffs.append(entity_diff)

        # Modified functions
        for func_id in baseline_ids & candidate_ids:
            baseline_func = baseline_functions[func_id]
            candidate_func = candidate_functions[func_id]

            entity_diff = self.signature_analyzer.analyze_function(baseline_func, candidate_func, func_id)

            # Only add if there are changes
            if entity_diff.changes:
                entity_diffs.append(entity_diff)

        return entity_diffs


# ============================================================================
# DIFF ANALYZER (UPDATE)
# ============================================================================
def _analyze_functions_implementation(self, baseline_contract: Any, candidate_contract: Any) -> List[EntityDiff]:
    """Analyze function changes (implementation of placeholder)."""
    # Extract function signatures from contracts
    baseline_funcs = getattr(baseline_contract, "functions", {})
    candidate_funcs = getattr(candidate_contract, "functions", {})

    # Use function catalog analyzer
    catalog_analyzer = FunctionCatalogAnalyzer()
    return catalog_analyzer.analyze_functions(baseline_funcs, candidate_funcs)


# Patch DetailedDiffAnalyzer
DetailedDiffAnalyzer._analyze_functions = _analyze_functions_implementation


# ============================================================================
# CLAUSE ANALYZER
# ============================================================================
class ClauseAnalyzer:
    """Analyzes clause changes in detail.
    Detects semantic shifts in nullability, ownership, and numeric bounds.
    """

    def analyze_clause(
        self, baseline_clause: Dict[str, Any], candidate_clause: Dict[str, Any], clause_id: str
    ) -> EntityDiff:
        """
        Analyze changes in a single clause.
        Args:
            baseline_clause: Old clause definition
            candidate_clause: New clause definition
            clause_id: Unique ID of the clause
        Returns:
            EntityDiff containing detected changes
        """
        entity_diff = EntityDiff(entity_id=clause_id, entity_type="clause")

        # Check severity change
        baseline_sev = baseline_clause.get("severity", "advisory")
        candidate_sev = candidate_clause.get("severity", "advisory")

        if baseline_sev != candidate_sev:
            severity_order = {"advisory": 0, "warning": 1, "error": 2, "fatal": 3}
            # Handle unknown severities gracefully
            b_val = severity_order.get(baseline_sev, 0)
            c_val = severity_order.get(candidate_sev, 0)

            change_severity = ChangeSeverity.STRENGTHENING if c_val > b_val else ChangeSeverity.RELAXATION

            entity_diff.changes.append(
                DetailedChange(
                    change_type="severity_changed",
                    entity_id=clause_id,
                    severity=change_severity,
                    description=f"Severity changed from '{baseline_sev}' to '{candidate_sev}'",
                    old_value=baseline_sev,
                    new_value=candidate_sev,
                )
            )

        # Analyze constraint parameters
        baseline_params = baseline_clause.get("constraint_parameters", {})
        candidate_params = candidate_clause.get("constraint_parameters", {})

        param_changes = self._analyze_constraint_parameters(baseline_params, candidate_params, clause_id)
        entity_diff.changes.extend(param_changes)

        return entity_diff

    def _analyze_constraint_parameters(
        self, baseline_params: Dict[str, Any], candidate_params: Dict[str, Any], clause_id: str
    ) -> List[DetailedChange]:
        """Analyze changes in clause constraint parameters."""
        changes = []

        all_keys = set(baseline_params.keys()) | set(candidate_params.keys())

        for key in all_keys:
            baseline_val = baseline_params.get(key)
            candidate_val = candidate_params.get(key)

            if baseline_val != candidate_val:
                change_sev = self._classify_constraint_change(key, baseline_val, candidate_val)

                changes.append(
                    DetailedChange(
                        change_type="constraint_parameter_changed",
                        entity_id=clause_id,
                        severity=change_sev,
                        description=f"Constraint '{key}' changed from {baseline_val} to {candidate_val}",
                        location=f"constraint '{key}'",
                        old_value=baseline_val,
                        new_value=candidate_val,
                    )
                )

        return changes

    def _classify_constraint_change(self, key: str, old_val: Any, new_val: Any) -> ChangeSeverity:
        """
        Classify the severity of a constraint parameter change.
        Follows strengthening/relaxation logic for semantic contracts.
        """
        # Nullability changes
        if key == "nullable":
            if old_val is True and new_val is False:
                return ChangeSeverity.STRENGTHENING  # Becomes non-null (stricter)
            elif old_val is False and new_val is True:
                return ChangeSeverity.RELAXATION  # Becomes null (looser)

        # Numeric constraints (min/max bounds)
        if key.startswith("min_") and old_val is not None and new_val is not None:
            return ChangeSeverity.STRENGTHENING if new_val > old_val else ChangeSeverity.RELAXATION

        if key.startswith("max_") and old_val is not None and new_val is not None:
            return ChangeSeverity.STRENGTHENING if new_val < old_val else ChangeSeverity.RELAXATION

        # Ownership changes are fundamentally breaking (ABI/Memory management)
        if key == "ownership":
            return ChangeSeverity.BREAKING

        # Default classification for other parameters (e.g., confidence, notes)
        return ChangeSeverity.NOTABLE


# ============================================================================
# CLAUSE CATALOG ANALYZER
# ============================================================================
class ClauseCatalogAnalyzer:
    """Analyzes clause catalog changes (additions/removals).
    Compares entire sets of semantic constraints.
    """

    def __init__(self):
        self.clause_analyzer = ClauseAnalyzer()

    def analyze_clauses(
        self, baseline_clauses: Dict[str, Dict[str, Any]], candidate_clauses: Dict[str, Dict[str, Any]]
    ) -> List[EntityDiff]:
        """
        Analyze clause catalog changes.
        Args:
            baseline_clauses: Dict of clause_id -> clause_definition
            candidate_clauses: Dict of clause_id -> clause_definition
        Returns:
            List of EntityDiff for all changed clauses
        """
        entity_diffs = []

        baseline_ids = set(baseline_clauses.keys())
        candidate_ids = set(candidate_clauses.keys())

        # Added clauses: Usually STRENGTHENING as they introduce new constraints
        for clause_id in candidate_ids - baseline_ids:
            clause = candidate_clauses[clause_id]
            entity_diff = EntityDiff(
                entity_id=clause_id,
                entity_type="clause",
                changes=[
                    DetailedChange(
                        change_type="clause_added",
                        entity_id=clause_id,
                        severity=ChangeSeverity.STRENGTHENING,
                        description=f"Clause '{clause_id}' added",
                        new_value=clause,
                    )
                ],
            )
            entity_diffs.append(entity_diff)

        # Removed clauses: Usually RELAXATION as constraints are lifted
        for clause_id in baseline_ids - candidate_ids:
            clause = baseline_clauses[clause_id]
            entity_diff = EntityDiff(
                entity_id=clause_id,
                entity_type="clause",
                changes=[
                    DetailedChange(
                        change_type="clause_removed",
                        entity_id=clause_id,
                        severity=ChangeSeverity.RELAXATION,
                        description=f"Clause '{clause_id}' removed",
                        old_value=clause,
                    )
                ],
            )
            entity_diffs.append(entity_diff)

        # Modified clauses: Compare internal parameters
        for clause_id in baseline_ids & candidate_ids:
            entity_diff = self.clause_analyzer.analyze_clause(
                baseline_clauses[clause_id], candidate_clauses[clause_id], clause_id
            )
            if entity_diff.changes:
                entity_diffs.append(entity_diff)

        return entity_diffs


# ============================================================================
# DIFF ANALYZER (UPDATE)
# ============================================================================
def _analyze_clauses_implementation(self, baseline_contract: Any, candidate_contract: Any) -> List[EntityDiff]:
    """Analyze clause changes (implementation of placeholder)."""
    # Extract clauses from contracts
    baseline_clauses = getattr(baseline_contract, "clauses", {})
    candidate_clauses = getattr(candidate_contract, "clauses", {})

    # Use clause catalog analyzer
    catalog_analyzer = ClauseCatalogAnalyzer()
    return catalog_analyzer.analyze_clauses(baseline_clauses, candidate_clauses)


# Patch DetailedDiffAnalyzer
DetailedDiffAnalyzer._analyze_clauses = _analyze_clauses_implementation


# ============================================================================
# VERSION HISTORY TRACKING
# ============================================================================
@dataclass
class VersionSnapshot:
    """Snapshot of a contract version at a specific point in time.
    Captures state, ancestry, and metadata.
    """

    version: str
    timestamp: str
    fingerprint: str
    parent_version: Optional[str] = None
    contract_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "fingerprint": self.fingerprint,
            "parent_version": self.parent_version,
            "metadata": self.metadata,
        }


class VersionHistory:
    """Manages version history and temporal diff queries.
    Allows traversing the evolution of a contract and computing diffs
    between any two points in the version graph.
    """

    def __init__(self):
        self.snapshots: Dict[str, VersionSnapshot] = {}
        self.diff_analyzer = DetailedDiffAnalyzer()

    def add_snapshot(self, snapshot: VersionSnapshot) -> None:
        """Add version snapshot to history."""
        self.snapshots[snapshot.version] = snapshot

    def get_snapshot(self, version: str) -> Optional[VersionSnapshot]:
        """Get snapshot by version."""
        return self.snapshots.get(version)

    def get_all_versions(self) -> List[str]:
        """Get all version identifiers."""
        return list(self.snapshots.keys())

    def get_parent_version(self, version: str) -> Optional[str]:
        """Get parent version of a specific version."""
        snapshot = self.snapshots.get(version)
        return snapshot.parent_version if snapshot else None

    def get_ancestry_chain(self, version: str) -> List[str]:
        """Get ancestry chain from root to the specified version."""
        chain = []
        current = version

        while current and current in self.snapshots:
            chain.insert(0, current)
            current = self.get_parent_version(current)

        return chain

    def diff_between(self, baseline_version: str, candidate_version: str) -> Optional[DetailedDiff]:
        """Compute the detailed diff between any two versions in history."""
        baseline_snap = self.snapshots.get(baseline_version)
        candidate_snap = self.snapshots.get(candidate_version)

        if not baseline_snap or not candidate_snap:
            return None

        if baseline_snap.contract_data is None or candidate_snap.contract_data is None:
            return None

        # internal helper for analysis compatibility
        class MockContract:
            def __init__(self, data):
                self.contract_version = data.get("version", "unknown")
                self.contract_fingerprint = data.get("fingerprint", "")
                self.functions = data.get("functions", {})
                self.clauses = data.get("clauses", {})

        baseline_contract = MockContract(baseline_snap.contract_data)
        candidate_contract = MockContract(candidate_snap.contract_data)

        return self.diff_analyzer.analyze(baseline_contract, candidate_contract)

    def timeline_between(self, start_version: str, end_version: str) -> List[Tuple[str, str]]:
        """Get timeline of version transitions between two versions."""
        if start_version == end_version:
            return []

        start_chain = self.get_ancestry_chain(start_version)
        end_chain = self.get_ancestry_chain(end_version)

        if not start_chain or not end_chain:
            return []

        # Find common ancestor
        common_idx = -1
        for i, (v1, v2) in enumerate(zip(start_chain, end_chain)):
            if v1 == v2:
                common_idx = i
            else:
                break

        if common_idx == -1:
            return []

        # Build timeline: skip versions before start_version and build path to end_version
        try:
            start_pos = end_chain.index(start_version)
            timeline_versions = end_chain[start_pos:]
        except ValueError:
            # If start_version is not an ancestor of end_version, use common ancestor to end
            timeline_versions = end_chain[common_idx:]

        timeline = []
        for i in range(len(timeline_versions) - 1):
            timeline.append((timeline_versions[i], timeline_versions[i + 1]))

        return timeline

    def find_breaking_changes_between(self, start_version: str, end_version: str) -> List[str]:
        """Find versions in the timeline that introduce breaking changes."""
        timeline = self.timeline_between(start_version, end_version)
        breaking_versions = []

        for baseline, candidate in timeline:
            diff = self.diff_between(baseline, candidate)
            if diff and len(diff.get_breaking_changes()) > 0:
                breaking_versions.append(candidate)

        return breaking_versions

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Check if one version is an ancestor of another."""
        chain = self.get_ancestry_chain(descendant)
        return ancestor in chain

    def common_ancestor(self, version1: str, version2: str) -> Optional[str]:
        """Find the most recent common ancestor of two versions."""
        chain1 = self.get_ancestry_chain(version1)
        chain2 = self.get_ancestry_chain(version2)

        common = None
        for v1, v2 in zip(chain1, chain2):
            if v1 == v2:
                common = v1
            else:
                break

        return common


class VersionHistoryBuilder:
    """Builds version history from contract snapshots."""

    def __init__(self):
        self.history = VersionHistory()

    def add_version(
        self,
        version: str,
        fingerprint: str,
        contract_data: Dict[str, Any],
        parent_version: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> VersionSnapshot:
        """Add a version to the history graph."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"

        snapshot = VersionSnapshot(
            version=version,
            timestamp=timestamp,
            fingerprint=fingerprint,
            parent_version=parent_version,
            contract_data=contract_data,
        )

        self.history.add_snapshot(snapshot)
        return snapshot

    def build(self) -> VersionHistory:
        """Finalize and return the version history."""
        return self.history


class ChangeAggregator:
    """Aggregates changes across multiple version transitions."""

    def aggregate_changes(self, diffs: List[DetailedDiff]) -> Dict[str, Any]:
        """Aggregate changes from multiple diff objects."""
        aggregated = {
            "total_changes": 0,
            "breaking_changes": 0,
            "extensions": 0,
            "strengthening": 0,
            "relaxation": 0,
            "notable": 0,
            "neutral": 0,
            "affected_entities": set(),
        }

        for diff in diffs:
            stats = diff.get_statistics()
            aggregated["total_changes"] += stats["total_changes"]
            aggregated["breaking_changes"] += stats["by_severity"].get("breaking", 0)
            aggregated["extensions"] += stats["by_severity"].get("extension", 0)
            aggregated["strengthening"] += stats["by_severity"].get("strengthening", 0)
            aggregated["relaxation"] += stats["by_severity"].get("relaxation", 0)
            aggregated["notable"] += stats["by_severity"].get("notable", 0)
            aggregated["neutral"] += stats["by_severity"].get("neutral", 0)

            for entity_diff in diff.entity_diffs:
                aggregated["affected_entities"].add(entity_diff.entity_id)

        # Convert set to sorted list for deterministic JSON output
        aggregated["affected_entities"] = sorted(list(aggregated["affected_entities"]))
        return aggregated


# ============================================================================
# MIGRATION PATH GENERATION & UPGRADE STRATEGY PLANNING
# ============================================================================
class MigrationStrategy(Enum):
    """Migration path selection strategy."""

    SAFEST = "safest"
    FASTEST = "fastest"
    BALANCED = "balanced"


@dataclass
class MigrationStep:
    """Single migration step in a path.
    Encapsulates cost, risk, and impact for a transition between two versions.
    """

    from_version: str
    to_version: str
    breaking_changes: int = 0
    total_changes: int = 0
    affected_entities: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    effort_estimate: float = 0.0

    def get_cost(self) -> float:
        """Calculate migration step cost based on industry heuristics."""
        return self.breaking_changes * 10 + len(self.affected_entities) * 2 + self.risk_score * 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "breaking_changes": self.breaking_changes,
            "total_changes": self.total_changes,
            "affected_entities": self.affected_entities,
            "risk_score": self.risk_score,
            "effort_estimate": self.effort_estimate,
            "cost": self.get_cost(),
        }


@dataclass
class MigrationPath:
    """Complete migration path from source to target version.
    Contains sequence of steps and aggregated metrics.
    """

    source_version: str
    target_version: str
    steps: List[MigrationStep] = field(default_factory=list)
    strategy: MigrationStrategy = MigrationStrategy.BALANCED

    def get_total_cost(self) -> float:
        """Calculate total path cost."""
        return sum(step.get_cost() for step in self.steps)

    def get_total_breaking_changes(self) -> int:
        """Get total breaking changes across path."""
        return sum(step.breaking_changes for step in self.steps)

    def get_total_changes(self) -> int:
        """Get total changes across path."""
        return sum(step.total_changes for step in self.steps)

    def get_step_count(self) -> int:
        """Get number of steps in path."""
        return len(self.steps)

    def is_direct_path(self) -> bool:
        """Check if this is a direct migration (single step)."""
        return len(self.steps) == 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert path to dictionary summary."""
        return {
            "source_version": self.source_version,
            "target_version": self.target_version,
            "strategy": self.strategy.value,
            "steps": [step.to_dict() for step in self.steps],
            "total_cost": self.get_total_cost(),
            "total_breaking_changes": self.get_total_breaking_changes(),
            "total_changes": self.get_total_changes(),
            "step_count": self.get_step_count(),
            "is_direct": self.is_direct_path(),
        }


class MigrationPathGenerator:
    """Generates and evaluates migration paths between versions."""

    def __init__(self, version_history: VersionHistory):
        self.history = version_history

    def generate_direct_path(self, source: str, target: str) -> Optional[MigrationPath]:
        """Generate direct migration path (single jump)."""
        if not self._versions_exist(source, target):
            return None

        step = self._create_migration_step(source, target)
        if step is None:
            return None

        return MigrationPath(
            source_version=source, target_version=target, steps=[step], strategy=MigrationStrategy.FASTEST
        )

    def generate_incremental_path(self, source: str, target: str) -> Optional[MigrationPath]:
        """Generate incremental migration path through the ancestry chain."""
        if not self._versions_exist(source, target):
            return None

        if source == target:
            return MigrationPath(source_version=source, target_version=target, steps=[], strategy=MigrationStrategy.SAFEST)

        timeline = self.history.timeline_between(source, target)
        if not timeline:
            return None

        steps = []
        for from_v, to_v in timeline:
            step = self._create_migration_step(from_v, to_v)
            if step:
                steps.append(step)

        if not steps and source != target:
            return None

        return MigrationPath(
            source_version=source, target_version=target, steps=steps, strategy=MigrationStrategy.SAFEST
        )

    def generate_all_paths(self, source: str, target: str, max_paths: int = 10) -> List[MigrationPath]:
        """Generate all possible migration paths."""
        paths = []

        # Direct path
        direct = self.generate_direct_path(source, target)
        if direct:
            paths.append(direct)

        # Incremental path
        incremental = self.generate_incremental_path(source, target)
        if incremental and incremental.get_step_count() > 1:
            paths.append(incremental)

        return paths[:max_paths]

    def find_optimal_path(
        self, source: str, target: str, strategy: MigrationStrategy = MigrationStrategy.BALANCED
    ) -> Optional[MigrationPath]:
        """Find the optimal migration path based on strategy."""
        paths = self.generate_all_paths(source, target)
        if not paths:
            if source == target:
                return MigrationPath(source_version=source, target_version=target, steps=[], strategy=strategy)
            return None

        if strategy == MigrationStrategy.FASTEST:
            return min(paths, key=lambda p: p.get_step_count())
        elif strategy == MigrationStrategy.SAFEST:
            return min(paths, key=lambda p: p.get_total_breaking_changes())
        else:  # BALANCED
            return min(paths, key=lambda p: p.get_total_cost())

    def _versions_exist(self, source: str, target: str) -> bool:
        """Check if both versions exist in history."""
        return self.history.get_snapshot(source) is not None and self.history.get_snapshot(target) is not None

    def _create_migration_step(self, from_version: str, to_version: str) -> Optional[MigrationStep]:
        """Create migration step with cost and risk analysis."""
        diff = self.history.diff_between(from_version, to_version)

        if diff is None:
            # Fallback for same version or missing data
            return MigrationStep(
                from_version=from_version,
                to_version=to_version,
                breaking_changes=0,
                total_changes=0,
                affected_entities=[],
                risk_score=0.0 if from_version == to_version else 1.0,
                effort_estimate=0.0 if from_version == to_version else 1.0,
            )

        stats = diff.get_statistics()
        breaking_count = stats["by_severity"].get("breaking", 0)
        total_count = stats["total_changes"]

        # Calculate heuristics
        risk_score = min(1.0, breaking_count / 10.0) if breaking_count > 0 else 0.1
        effort_estimate = breaking_count * 2.0 + total_count * 0.5

        affected_entities = [entity_diff.entity_id for entity_diff in diff.entity_diffs]

        return MigrationStep(
            from_version=from_version,
            to_version=to_version,
            breaking_changes=breaking_count,
            total_changes=total_count,
            affected_entities=affected_entities,
            risk_score=risk_score,
            effort_estimate=effort_estimate,
        )


class UpgradeRecommendation:
    """Generates tailored upgrade recommendations based on history and risk."""

    def __init__(self, path_generator: MigrationPathGenerator):
        self.generator = path_generator

    def recommend_upgrade(self, current_version: str, target_version: str) -> Dict[str, Any]:
        """Generate a complete upgrade recommendation suite."""
        paths = self.generator.generate_all_paths(current_version, target_version)

        if not paths and current_version != target_version:
            return {"possible": False, "reason": "No migration path found", "recommendation": None}

        recommended = self.generator.find_optimal_path(current_version, target_version, MigrationStrategy.BALANCED)
        fastest = self.generator.find_optimal_path(current_version, target_version, MigrationStrategy.FASTEST)
        safest = self.generator.find_optimal_path(current_version, target_version, MigrationStrategy.SAFEST)

        return {
            "possible": True,
            "recommended_path": recommended.to_dict() if recommended else None,
            "fastest_path": fastest.to_dict() if fastest else None,
            "safest_path": safest.to_dict() if safest else None,
            "all_paths": [p.to_dict() for p in paths],
            "summary": {
                "total_paths": len(paths),
                "recommended_steps": recommended.get_step_count() if recommended else 0,
                "recommended_breaking_changes": recommended.get_total_breaking_changes() if recommended else 0,
            },
        }


class MigrationPlanner:
    """Plans and validates detailed migration steps."""

    def __init__(self, version_history: VersionHistory, path_generator: MigrationPathGenerator):
        self.history = version_history
        self.generator = path_generator

    def create_migration_plan(
        self, source: str, target: str, strategy: MigrationStrategy = MigrationStrategy.BALANCED
    ) -> Dict[str, Any]:
        """Create a detailed migration plan with tasks."""
        path = self.generator.find_optimal_path(source, target, strategy)

        if not path:
            return {"success": False, "error": "No migration path found"}

        plan = {
            "success": True,
            "source_version": source,
            "target_version": target,
            "strategy": strategy.value,
            "total_steps": path.get_step_count(),
            "total_cost": path.get_total_cost(),
            "total_breaking_changes": path.get_total_breaking_changes(),
            "estimated_effort_hours": sum(s.effort_estimate for s in path.steps),
            "steps": [],
        }

        for i, step in enumerate(path.steps, 1):
            step_detail = {
                "step_number": i,
                "from_version": step.from_version,
                "to_version": step.to_version,
                "breaking_changes": step.breaking_changes,
                "affected_entities": step.affected_entities,
                "risk_level": self._get_risk_level(step.risk_score),
                "estimated_effort_hours": step.effort_estimate,
                "tasks": self._generate_tasks(step),
            }
            plan["steps"].append(step_detail)

        return plan

    def _get_risk_level(self, risk_score: float) -> str:
        """Categorize risk score into human-readable levels."""
        if risk_score < 0.3:
            return "LOW"
        elif risk_score < 0.6:
            return "MEDIUM"
        else:
            return "HIGH"

    def _generate_tasks(self, step: MigrationStep) -> List[str]:
        """Generate a task list for a specific migration step."""
        tasks = []

        if step.breaking_changes > 0:
            tasks.append(f"Review {step.breaking_changes} breaking changes")
            tasks.append("Update binding code for breaking changes")

        if step.affected_entities:
            tasks.append(f"Update {len(step.affected_entities)} affected entities")

        tasks.append("Regenerate bindings")
        tasks.append("Run integration tests")
        tasks.append("Update documentation")

        return tasks

    def validate_path(self, path: MigrationPath) -> Dict[str, Any]:
        """Validate the viability and risk of a migration path."""
        issues = []
        warnings = []

        for step in path.steps:
            if step.risk_score > 0.7:
                warnings.append(f"High risk step: {step.from_version} -> {step.to_version}")

            if step.breaking_changes > 10:
                issues.append(
                    f"Very high breaking changes ({step.breaking_changes}) in step {step.from_version} -> {step.to_version}"
                )

        total_cost = path.get_total_cost()
        if total_cost > 1000:
            warnings.append(f"High total migration cost: {total_cost}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "risk_assessment": "HIGH" if issues else ("MEDIUM" if warnings else "LOW"),
        }


# ============================================================================
# DEPENDENCY RESOLUTION & MULTI-CONTRACT VERSION COORDINATION
# ============================================================================
class ConstraintOperator(Enum):
    """Version constraint operators."""

    EQUAL = "=="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    GREATER = ">"
    LESS = "<"
    COMPATIBLE = "^"  # Caret (semver compatible)


@dataclass
class VersionConstraint:
    """Version constraint specification for a named contract."""

    contract_name: str
    operator: ConstraintOperator
    version: str

    def satisfies(self, candidate_version: str) -> bool:
        """Check if candidate version satisfies constraint."""
        try:
            baseline = self._parse_version(self.version)
            candidate = self._parse_version(candidate_version)
        except (ValueError, IndexError):
            return False

        if self.operator == ConstraintOperator.EQUAL:
            return candidate == baseline
        elif self.operator == ConstraintOperator.GREATER_EQUAL:
            return candidate >= baseline
        elif self.operator == ConstraintOperator.LESS_EQUAL:
            return candidate <= baseline
        elif self.operator == ConstraintOperator.GREATER:
            return candidate > baseline
        elif self.operator == ConstraintOperator.LESS:
            return candidate < baseline
        elif self.operator == ConstraintOperator.COMPATIBLE:
            # ^1.5.0 means >=1.5.0, <2.0.0
            major = baseline[0]
            return candidate >= baseline and candidate[0] == major

        return False

    def _parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """Parse semver version to tuple."""
        parts = version_str.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"contract_name": self.contract_name, "operator": self.operator.value, "version": self.version}


@dataclass
class ContractDependency:
    """Contract dependency specification."""

    contract_name: str
    current_version: str
    dependencies: List[VersionConstraint] = field(default_factory=list)

    def add_dependency(self, constraint: VersionConstraint) -> None:
        """Add dependency constraint."""
        self.dependencies.append(constraint)

    def get_dependency(self, contract_name: str) -> Optional[VersionConstraint]:
        """Get dependency constraint by contract name."""
        for dep in self.dependencies:
            if dep.contract_name == contract_name:
                return dep
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contract_name": self.contract_name,
            "current_version": self.current_version,
            "dependencies": [d.to_dict() for d in self.dependencies],
        }


class DependencyGraph:
    """Dependency graph for contracts and their relationships."""

    def __init__(self):
        self.nodes: Dict[str, ContractDependency] = {}
        self.edges: Dict[str, List[str]] = {}  # contract_name -> [dependencies]

    def add_contract(self, contract: ContractDependency) -> None:
        """Add contract to graph."""
        self.nodes[contract.contract_name] = contract
        self.edges[contract.contract_name] = [dep.contract_name for dep in contract.dependencies]

    def get_contract(self, name: str) -> Optional[ContractDependency]:
        """Get contract by name."""
        return self.nodes.get(name)

    def get_dependencies(self, contract_name: str) -> List[str]:
        """Get direct dependencies of contract."""
        return self.edges.get(contract_name, [])

    def get_transitive_dependencies(self, contract_name: str) -> Set[str]:
        """Get all transitive dependencies."""
        visited = set()
        to_visit = [contract_name]

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue

            visited.add(current)
            deps = self.get_dependencies(current)
            to_visit.extend(deps)

        visited.discard(contract_name)
        return visited

    def topological_sort(self) -> List[str]:
        """Topological sort (bottom-up dependency order)."""
        in_degree = {name: 0 for name in self.nodes}

        for deps in self.edges.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for dep in self.get_dependencies(node):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        # Reverse to get bottom-up order
        return list(reversed(result))

    def has_cycle(self) -> bool:
        """Check for circular dependencies."""
        sorted_list = self.topological_sort()
        return len(sorted_list) != len(self.nodes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation."""
        return {"contracts": [c.to_dict() for c in self.nodes.values()], "edges": self.edges}


class DependencyResolver:
    """Resolves dependencies and detects conflicts across multiple contracts."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph

    def resolve(self, contract_name: str) -> Dict[str, Any]:
        """Resolve dependencies for a specific contract."""
        contract = self.graph.get_contract(contract_name)
        if not contract:
            return {"success": False, "error": "Contract not found"}

        conflicts = self.detect_conflicts(contract_name)

        if conflicts:
            return {"success": False, "conflicts": conflicts, "error": "Dependency conflicts detected"}

        resolved_versions = self._resolve_versions(contract_name)

        return {"success": True, "contract": contract_name, "resolved_dependencies": resolved_versions}

    def detect_conflicts(self, contract_name: str) -> List[Dict[str, Any]]:
        """Detect dependency conflicts in the tree."""
        conflicts = []
        dependencies = self.graph.get_transitive_dependencies(contract_name)

        # Group constraints by target contract
        constraint_map: Dict[str, List[Tuple[str, VersionConstraint]]] = {}

        for dep_name in dependencies:
            dep_contract = self.graph.get_contract(dep_name)
            if dep_contract:
                for constraint in dep_contract.dependencies:
                    target = constraint.contract_name
                    if target not in constraint_map:
                        constraint_map[target] = []
                    constraint_map[target].append((dep_name, constraint))

        # Check for conflicting constraints
        for target, constraints in constraint_map.items():
            if len(constraints) > 1:
                # Check if any version satisfies all constraints
                if not self._has_satisfying_version(constraints):
                    conflicts.append(
                        {
                            "target_contract": target,
                            "conflicting_constraints": [{"from": source, "constraint": c.to_dict()} for source, c in constraints],
                        }
                    )

        return conflicts

    def _resolve_versions(self, contract_name: str) -> Dict[str, str]:
        """Resolve versions for all dependencies."""
        resolved = {}
        dependencies = self.graph.get_transitive_dependencies(contract_name)

        for dep_name in dependencies:
            dep_contract = self.graph.get_contract(dep_name)
            if dep_contract:
                resolved[dep_name] = dep_contract.current_version

        return resolved

    def _has_satisfying_version(self, constraints: List[Tuple[str, VersionConstraint]]) -> bool:
        """Check if any version satisfies all constraints (heuristic)."""
        if len(constraints) <= 1:
            return True

        # Check for simple contradictions like >= X and < X
        ge_versions = {c.version for _, c in constraints if c.operator == ConstraintOperator.GREATER_EQUAL}
        lt_versions = {c.version for _, c in constraints if c.operator == ConstraintOperator.LESS}

        if ge_versions & lt_versions:
            return False

        # General heuristic: too many constraints likely conflict
        return len(constraints) <= 3


class CoordinatedUpgradePlanner:
    """Plans coordinated upgrades across a complex dependency graph."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.resolver = DependencyResolver(graph)

    def plan_coordinated_upgrade(self, upgrades: Dict[str, str]) -> Dict[str, Any]:
        """Plan coordinated upgrade for multiple contracts."""
        # contract_name -> target_version
        
        # Get upgrade order (topological sort)
        upgrade_order = self._get_upgrade_order(list(upgrades.keys()))

        if not upgrade_order and upgrades:
            return {"success": False, "error": "Circular dependency detected"}

        # Build upgrade plan
        plan = {"success": True, "upgrade_order": upgrade_order, "steps": []}

        for contract_name in upgrade_order:
            if contract_name in upgrades:
                contract = self.graph.get_contract(contract_name)
                target_version = upgrades[contract_name]

                step = {
                    "contract": contract_name,
                    "from_version": contract.current_version if contract else "unknown",
                    "to_version": target_version,
                    "dependencies": self.graph.get_dependencies(contract_name),
                }
                plan["steps"].append(step)

        return plan

    def _get_upgrade_order(self, contract_names: List[str]) -> List[str]:
        """Get upgrade order for subsets of contracts."""
        # Create subgraph with only relevant contracts
        all_contracts = set(contract_names)

        # Add transitive dependencies
        for name in list(all_contracts):
            all_contracts.update(self.graph.get_transitive_dependencies(name))

        # Filter topological sort to include only relevant contracts
        full_order = self.graph.topological_sort()
        return [c for c in full_order if c in all_contracts]

    def validate_upgrade_plan(self, upgrades: Dict[str, str]) -> Dict[str, Any]:
        """Validate coordinated upgrade plan."""
        issues = []
        warnings = []

        # Check for circular dependencies
        if self.graph.has_cycle():
            issues.append("Circular dependency detected in dependency graph")

        # Check each upgrade
        for contract_name, target_version in upgrades.items():
            contract = self.graph.get_contract(contract_name)
            if not contract:
                issues.append(f"Contract '{contract_name}' not found in graph")
                continue

            # Check if upgrade breaks dependencies
            dependents = self._get_dependents(contract_name)
            for dependent in dependents:
                dep_contract = self.graph.get_contract(dependent)
                if dep_contract:
                    constraint = dep_contract.get_dependency(contract_name)
                    if constraint and not constraint.satisfies(target_version):
                        warnings.append(
                            f"Upgrade of {contract_name} to {target_version} may break dependent {dependent}"
                        )

        return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}

    def _get_dependents(self, contract_name: str) -> List[str]:
        """Get contracts that depend on this contract."""
        dependents = []
        for name, deps in self.graph.edges.items():
            if contract_name in deps:
                dependents.append(name)
        return dependents


# ============================================================================
# VERSION COMPATIBILITY MATRIX & CROSS-VERSION TESTING
# ============================================================================
class CompatibilityStatus(Enum):
    """Compatibility status between versions."""

    COMPATIBLE = "compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"
    UNTESTED = "untested"
    UNKNOWN = "unknown"


@dataclass
class CompatibilityTestResult:
    """Result of compatibility testing between two contract versions."""

    baseline_version: str
    candidate_version: str
    status: CompatibilityStatus
    binding_generation: str = "UNTESTED"  # PASS, FAIL, UNTESTED
    runtime_integration: str = "UNTESTED"
    feature_coverage: str = "UNTESTED"
    breaking_changes: int = 0
    warnings: List[str] = field(default_factory=list)
    notes: str = ""

    def is_compatible(self) -> bool:
        """Check if versions are compatible."""
        return self.status == CompatibilityStatus.COMPATIBLE

    def is_partially_compatible(self) -> bool:
        """Check if versions are partially compatible."""
        return self.status == CompatibilityStatus.PARTIALLY_COMPATIBLE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline_version": self.baseline_version,
            "candidate_version": self.candidate_version,
            "status": self.status.value,
            "binding_generation": self.binding_generation,
            "runtime_integration": self.runtime_integration,
            "feature_coverage": self.feature_coverage,
            "breaking_changes": self.breaking_changes,
            "warnings": self.warnings,
            "notes": self.notes,
        }


@dataclass
class CompatibilityMatrixEntry:
    """Single entry in compatibility matrix involving two different contracts/versions."""

    contract_a: str
    version_a: str
    contract_b: str
    version_b: str
    test_result: CompatibilityTestResult

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contract_a": self.contract_a,
            "version_a": self.version_a,
            "contract_b": self.contract_b,
            "version_b": self.version_b,
            "test_result": self.test_result.to_dict(),
        }


class CompatibilityMatrix:
    """Compatibility matrix for cross-contract versions."""

    def __init__(self):
        self.entries: Dict[Tuple[str, str, str, str], CompatibilityMatrixEntry] = {}

    def add_entry(self, entry: CompatibilityMatrixEntry) -> None:
        """Add entry to matrix."""
        key = (entry.contract_a, entry.version_a, entry.contract_b, entry.version_b)
        self.entries[key] = entry

    def get_compatibility(
        self, contract_a: str, version_a: str, contract_b: str, version_b: str
    ) -> Optional[CompatibilityTestResult]:
        """Get compatibility test result from matrix."""
        key = (contract_a, version_a, contract_b, version_b)
        entry = self.entries.get(key)
        return entry.test_result if entry else None

    def get_compatible_versions(self, contract_a: str, version_a: str, contract_b: str) -> List[str]:
        """Get all compatible versions of contract_b for a specific contract_a version."""
        compatible = []

        for (ca, va, cb, vb), entry in self.entries.items():
            if ca == contract_a and va == version_a and cb == contract_b:
                if entry.test_result.is_compatible():
                    compatible.append(vb)

        return compatible

    def get_all_entries_for_contract(self, contract: str) -> List[CompatibilityMatrixEntry]:
        """Get all matrix entries involving a specific contract."""
        entries = []

        for entry in self.entries.values():
            if entry.contract_a == contract or entry.contract_b == contract:
                entries.append(entry)

        return entries

    def to_dict(self) -> Dict[str, Any]:
        """Convert matrix to dictionary."""
        return {"entries": [e.to_dict() for e in self.entries.values()]}


class CompatibilityTester:
    """Tests compatibility between contract versions using version history."""

    def __init__(self, version_history: VersionHistory):
        self.history = version_history

    def test_compatibility(self, baseline_version: str, candidate_version: str) -> CompatibilityTestResult:
        """Test compatibility between two versions based on diff analysis."""
        # Get diff between versions
        diff = self.history.diff_between(baseline_version, candidate_version)

        if diff is None:
            return CompatibilityTestResult(
                baseline_version=baseline_version,
                candidate_version=candidate_version,
                status=CompatibilityStatus.UNKNOWN,
                notes="Unable to compute diff",
            )

        # Analyze diff for compatibility
        breaking_count = len(diff.get_breaking_changes())

        if breaking_count == 0:
            status = CompatibilityStatus.COMPATIBLE
            binding_gen = "PASS"
            runtime = "PASS"
            features = "PASS"
        elif breaking_count <= 3:
            status = CompatibilityStatus.PARTIALLY_COMPATIBLE
            binding_gen = "PASS"
            runtime = "PASS"
            features = "PARTIAL"
        else:
            status = CompatibilityStatus.INCOMPATIBLE
            binding_gen = "FAIL"
            runtime = "FAIL"
            features = "FAIL"

        warnings = []
        if breaking_count > 0:
            warnings.append(f"{breaking_count} breaking changes detected")

        return CompatibilityTestResult(
            baseline_version=baseline_version,
            candidate_version=candidate_version,
            status=status,
            binding_generation=binding_gen,
            runtime_integration=runtime,
            feature_coverage=features,
            breaking_changes=breaking_count,
            warnings=warnings,
        )

    def batch_test(self, baseline_versions: List[str], candidate_versions: List[str]) -> List[CompatibilityTestResult]:
        """Test compatibility for multiple version pairs in batch."""
        results = []

        for baseline in baseline_versions:
            for candidate in candidate_versions:
                result = self.test_compatibility(baseline, candidate)
                results.append(result)

        return results


class CompatibilityRecommendationEngine:
    """Generates compatibility recommendations based on the matrix."""

    def __init__(self, matrix: CompatibilityMatrix):
        self.matrix = matrix

    def recommend_version(self, contract_a: str, version_a: str, contract_b: str) -> Dict[str, Any]:
        """Recommend compatible version of contract_b for given contract_a."""
        compatible_versions = self.matrix.get_compatible_versions(contract_a, version_a, contract_b)

        if not compatible_versions:
            return {"found": False, "reason": "No compatible versions found", "recommended_version": None}

        # Return latest compatible version
        recommended = max(compatible_versions, key=self._parse_version)

        return {
            "found": True,
            "recommended_version": recommended,
            "all_compatible_versions": compatible_versions,
            "reason": f"Latest compatible version of {contract_b}",
        }

    def get_upgrade_recommendation(
        self, contract_a: str, current_version_a: str, target_version_a: str, contract_b: str, current_version_b: str
    ) -> Dict[str, Any]:
        """Recommend upgrade path for contract_b when upgrading contract_a."""
        # Check current compatibility
        current_compat = self.matrix.get_compatibility(contract_a, current_version_a, contract_b, current_version_b)

        # Check target compatibility
        target_compat = self.matrix.get_compatibility(contract_a, target_version_a, contract_b, current_version_b)

        if target_compat and target_compat.is_compatible():
            return {
                "upgrade_needed": False,
                "reason": f"{contract_b} {current_version_b} is compatible with {contract_a} {target_version_a}",
                "recommended_version": current_version_b,
            }

        # Find compatible version
        compatible_versions = self.matrix.get_compatible_versions(contract_a, target_version_a, contract_b)

        if not compatible_versions:
            return {
                "upgrade_needed": True,
                "upgrade_available": False,
                "reason": f"No compatible version of {contract_b} found for {contract_a} {target_version_a}",
            }

        recommended = max(compatible_versions, key=self._parse_version)

        return {
            "upgrade_needed": True,
            "upgrade_available": True,
            "recommended_version": recommended,
            "reason": f"{contract_b} must be upgraded to {recommended} for compatibility with {contract_a} {target_version_a}",
        }

    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string to tuple for comparison."""
        parts = version.split(".")
        return (
            int(parts[0]) if len(parts) > 0 else 0,
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0,
        )


class VersionRangeSpec:
    """Specifies version range compatibility using patterns."""

    def __init__(
        self,
        contract_a: str,
        version_pattern_a: str,
        contract_b: str,
        version_pattern_b: str,
        status: CompatibilityStatus,
    ):
        self.contract_a = contract_a
        self.version_pattern_a = version_pattern_a
        self.contract_b = contract_b
        self.version_pattern_b = version_pattern_b
        self.status = status

    def matches(self, contract_a: str, version_a: str, contract_b: str, version_b: str) -> bool:
        """Check if version pair matches this range spec."""
        if contract_a != self.contract_a or contract_b != self.contract_b:
            return False

        return self._matches_pattern(version_a, self.version_pattern_a) and self._matches_pattern(
            version_b, self.version_pattern_b
        )

    def _matches_pattern(self, version: str, pattern: str) -> bool:
        """Check if version matches pattern (e.g., 2.*.* matches 2.5.0)."""
        v_parts = version.split(".")
        p_parts = pattern.split(".")

        for i in range(min(len(v_parts), len(p_parts))):
            if p_parts[i] != "*" and p_parts[i] != v_parts[i]:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contract_a": self.contract_a,
            "version_pattern_a": self.version_pattern_a,
            "contract_b": self.contract_b,
            "version_pattern_b": self.version_pattern_b,
            "status": self.status.value,
        }


class CompatibilityMatrixBuilder:
    """Builds compatibility matrix from test results and range specs."""

    def __init__(self):
        self.matrix = CompatibilityMatrix()
        self.range_specs: List[VersionRangeSpec] = []

    def add_test_result(
        self, contract_a: str, version_a: str, contract_b: str, version_b: str, test_result: CompatibilityTestResult
    ) -> None:
        """Add test result to matrix."""
        entry = CompatibilityMatrixEntry(
            contract_a=contract_a,
            version_a=version_a,
            contract_b=contract_b,
            version_b=version_b,
            test_result=test_result,
        )
        self.matrix.add_entry(entry)

    def add_range_spec(self, spec: VersionRangeSpec) -> None:
        """Add version range specification."""
        self.range_specs.append(spec)

    def get_compatibility_from_ranges(
        self, contract_a: str, version_a: str, contract_b: str, version_b: str
    ) -> Optional[CompatibilityStatus]:
        """Get compatibility status from range specs."""
        for spec in self.range_specs:
            if spec.matches(contract_a, version_a, contract_b, version_b):
                return spec.status

        return None

    def build(self) -> CompatibilityMatrix:
        """Build and return compatibility matrix."""
        return self.matrix


class LifecycleStage(Enum):
    """Version lifecycle stage."""

    DEVELOPMENT = "development"
    PREVIEW = "preview"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    END_OF_LIFE = "end_of_life"


class SupportTier(Enum):
    """Support tier for version."""

    FULL = "full"
    MAINTENANCE = "maintenance"
    EXTENDED = "extended"
    NONE = "none"


@dataclass
class DeprecationNotice:
    """Deprecation notice for a version."""

    version: str
    deprecated_at: str  # ISO 8601 date
    end_of_life_at: str  # ISO 8601 date
    reason: str
    replacement_version: Optional[str] = None
    migration_guide_url: Optional[str] = None
    breaking_changes: List[str] = field(default_factory=list)

    def is_deprecated(self) -> bool:
        """Check if currently deprecated."""
        now = datetime.now(timezone.utc)
        deprecated_date = datetime.fromisoformat(self.deprecated_at.replace("Z", "+00:00"))
        return now >= deprecated_date

    def is_end_of_life(self) -> bool:
        """Check if end-of-life reached."""
        now = datetime.now(timezone.utc)
        eol_date = datetime.fromisoformat(self.end_of_life_at.replace("Z", "+00:00"))
        return now >= eol_date

    def days_until_eol(self) -> int:
        """Days until end-of-life."""
        now = datetime.now(timezone.utc)
        eol_date = datetime.fromisoformat(self.end_of_life_at.replace("Z", "+00:00"))
        delta = eol_date - now
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "deprecated_at": self.deprecated_at,
            "end_of_life_at": self.end_of_life_at,
            "reason": self.reason,
            "replacement_version": self.replacement_version,
            "migration_guide_url": self.migration_guide_url,
            "breaking_changes": self.breaking_changes,
            "days_until_eol": self.days_until_eol(),
        }


@dataclass
class VersionLifecycle:
    """Lifecycle information for a version."""

    version: str
    stage: LifecycleStage
    support_tier: SupportTier
    released_at: Optional[str] = None
    stable_at: Optional[str] = None
    deprecation_notice: Optional[DeprecationNotice] = None
    stability_guarantees: List[str] = field(default_factory=list)

    def is_production_ready(self) -> bool:
        """Check if version is production-ready."""
        return self.stage in [LifecycleStage.STABLE, LifecycleStage.DEPRECATED]

    def is_supported(self) -> bool:
        """Check if version is currently supported."""
        if self.deprecation_notice and self.deprecation_notice.is_end_of_life():
            return False
        return self.stage != LifecycleStage.END_OF_LIFE

    def get_support_description(self) -> str:
        """Get human-readable support description."""
        if self.stage == LifecycleStage.END_OF_LIFE:
            return "No longer supported"

        if self.deprecation_notice and self.deprecation_notice.is_deprecated():
            days = self.deprecation_notice.days_until_eol()
            return f"Deprecated, {days} days until end-of-life"

        tier_desc = {
            SupportTier.FULL: "Fully supported",
            SupportTier.MAINTENANCE: "Maintenance mode (security fixes only)",
            SupportTier.EXTENDED: "Extended support",
            SupportTier.NONE: "No support",
        }

        return tier_desc.get(self.support_tier, "Unknown")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "stage": self.stage.value,
            "support_tier": self.support_tier.value,
            "released_at": self.released_at,
            "stable_at": self.stable_at,
            "deprecation_notice": self.deprecation_notice.to_dict() if self.deprecation_notice else None,
            "stability_guarantees": self.stability_guarantees,
            "is_production_ready": self.is_production_ready(),
            "is_supported": self.is_supported(),
            "support_description": self.get_support_description(),
        }


class LifecycleManager:
    """Manages version lifecycles."""

    def __init__(self):
        self.lifecycles: Dict[str, VersionLifecycle] = {}

    def add_version(self, lifecycle: VersionLifecycle) -> None:
        """Add version lifecycle."""
        self.lifecycles[lifecycle.version] = lifecycle

    def get_lifecycle(self, version: str) -> Optional[VersionLifecycle]:
        """Get lifecycle for version."""
        return self.lifecycles.get(version)

    def get_supported_versions(self) -> List[str]:
        """Get all currently supported versions."""
        return [v for v, lc in self.lifecycles.items() if lc.is_supported()]

    def get_deprecated_versions(self) -> List[str]:
        """Get all deprecated versions."""
        deprecated = []
        for v, lc in self.lifecycles.items():
            if lc.stage == LifecycleStage.DEPRECATED:
                deprecated.append(v)
        return deprecated

    def get_production_ready_versions(self) -> List[str]:
        """Get all production-ready versions."""
        return [v for v, lc in self.lifecycles.items() if lc.is_production_ready()]

    def deprecate_version(
        self, version: str, reason: str, eol_days: int = 365, replacement_version: Optional[str] = None
    ) -> bool:
        """Deprecate a version."""
        lifecycle = self.lifecycles.get(version)
        if not lifecycle:
            return False

        now = datetime.now(timezone.utc)
        deprecated_at = now.isoformat().replace("+00:00", "Z")
        eol_at = (now + timedelta(days=eol_days)).isoformat().replace("+00:00", "Z")

        notice = DeprecationNotice(
            version=version,
            deprecated_at=deprecated_at,
            end_of_life_at=eol_at,
            reason=reason,
            replacement_version=replacement_version,
        )

        lifecycle.stage = LifecycleStage.DEPRECATED
        lifecycle.support_tier = SupportTier.MAINTENANCE
        lifecycle.deprecation_notice = notice

        return True

    def retire_version(self, version: str) -> bool:
        """Retire version to end-of-life."""
        lifecycle = self.lifecycles.get(version)
        if not lifecycle:
            return False

        lifecycle.stage = LifecycleStage.END_OF_LIFE
        lifecycle.support_tier = SupportTier.NONE

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "lifecycles": {v: lc.to_dict() for v, lc in self.lifecycles.items()},
            "supported_versions": self.get_supported_versions(),
            "deprecated_versions": self.get_deprecated_versions(),
        }


class DeprecationPolicy:
    """Defines deprecation policies."""

    def __init__(
        self, name: str, deprecation_period_days: int = 180, eol_period_days: int = 365, minimum_notice_days: int = 90
    ):
        self.name = name
        self.deprecation_period_days = deprecation_period_days
        self.eol_period_days = eol_period_days
        self.minimum_notice_days = minimum_notice_days

    def calculate_eol_date(self, deprecation_date: str) -> str:
        """Calculate EOL date from deprecation date."""
        dep_date = datetime.fromisoformat(deprecation_date.replace("Z", "+00:00"))
        eol_date = dep_date + timedelta(days=self.eol_period_days)
        return eol_date.isoformat() + "Z"

    def validate_deprecation_notice(self, notice: DeprecationNotice) -> Dict[str, Any]:
        """Validate deprecation notice against policy."""
        issues = []
        warnings = []

        # Check minimum notice period
        dep_date = datetime.fromisoformat(notice.deprecated_at.replace("Z", "+00:00"))
        eol_date = datetime.fromisoformat(notice.end_of_life_at.replace("Z", "+00:00"))
        notice_days = (eol_date - dep_date).days

        if notice_days < self.minimum_notice_days:
            issues.append(f"Notice period ({notice_days} days) is less than minimum ({self.minimum_notice_days} days)")

        # Check replacement version specified
        if not notice.replacement_version:
            warnings.append("No replacement version specified")

        # Check migration guide
        if not notice.migration_guide_url:
            warnings.append("No migration guide URL provided")

        return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "deprecation_period_days": self.deprecation_period_days,
            "eol_period_days": self.eol_period_days,
            "minimum_notice_days": self.minimum_notice_days,
        }


class VersionValidator:
    """Validates semantic versions."""

    def validate_format(self, version_str: str) -> Dict[str, Any]:
        """Validate version string format."""
        try:
            SemanticVersion.parse(version_str)
            return {"valid": True}
        except ValueError as e:
            return {"valid": False, "error": str(e), "issues": ["Invalid semantic version format"]}

    def validate_transition(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Validate version transition."""
        try:
            v_from = SemanticVersion.parse(from_version)
            v_to = SemanticVersion.parse(to_version)
        except ValueError as e:
            return {"valid": False, "error": f"Invalid version format: {e}"}

        issues = []

        # Check if version is moving forward
        if v_to <= v_from:
            issues.append(f"Version must increase: {from_version} → {to_version}")

        # Check for invalid transitions
        if v_to.major < v_from.major:
            issues.append("Major version cannot decrease")

        if v_to.major == v_from.major and v_to.minor < v_from.minor:
            issues.append("Minor version cannot decrease within same major version")

        return {"valid": len(issues) == 0, "issues": issues}

    def is_valid_next_version(self, current: str, proposed: str) -> bool:
        """Check if proposed is valid next version."""
        result = self.validate_transition(current, proposed)
        return result["valid"]


class VersionPolicy:
    """Version policy rules."""

    def __init__(self, name: str):
        self.name = name
        self.rules: List[str] = []

    def add_rule(self, rule: str) -> None:
        """Add policy rule."""
        self.rules.append(rule)

    def check_compliance(self, current_version: str, proposed_version: str, diff: Any) -> Dict[str, Any]:
        """Check if version change complies with policy."""
        try:
            v_current = SemanticVersion.parse(current_version)
            v_proposed = SemanticVersion.parse(proposed_version)
        except ValueError as e:
            return {"compliant": False, "violations": [f"Invalid version format: {e}"]}

        violations = []
        warnings = []

        # Rule: Breaking changes require major version bump
        breaking_changes = len(diff.get_breaking_changes())

        if breaking_changes > 0:
            if v_proposed.major == v_current.major:
                violations.append(
                    f"{breaking_changes} breaking changes require major version bump "
                    f"(expected v{v_current.major + 1}.0.0, got v{proposed_version})"
                )

        # Rule: No breaking changes in minor/patch bumps
        if v_proposed.major == v_current.major and v_proposed.minor > v_current.minor:
            if breaking_changes > 0:
                violations.append(
                    f"Minor version bump cannot include breaking changes " f"({breaking_changes} breaking changes found)"
                )

        # Rule: Patch bumps should be minimal changes
        if v_proposed.major == v_current.major and v_proposed.minor == v_current.minor and v_proposed.patch > v_current.patch:
            stats = diff.get_statistics()
            total_changes = stats["total_changes"]

            if total_changes > 5:
                warnings.append(f"Patch version bump with {total_changes} changes " f"(consider minor bump instead)")

        # Pre-release versions are exempt from strict rules
        if v_proposed.is_prerelease():
            violations.clear()
            warnings.append("Pre-release version: strict rules not enforced")

        return {"compliant": len(violations) == 0, "violations": violations, "warnings": warnings}


class VersionRecommendationEngine:
    """Recommends next version based on changes."""

    def recommend_version(self, current_version: str, diff: Any) -> Dict[str, Any]:
        """Recommend next version based on diff."""
        try:
            v_current = SemanticVersion.parse(current_version)
        except ValueError as e:
            return {"success": False, "error": f"Invalid current version: {e}"}

        stats = diff.get_statistics()
        breaking = stats["by_severity"].get("breaking", 0)
        extensions = stats["by_severity"].get("extension", 0)

        # Determine recommendation
        if breaking > 0:
            recommended = v_current.bump_major()
            reason = f"{breaking} breaking changes require major version bump"
        elif extensions > 0:
            recommended = v_current.bump_minor()
            reason = f"{extensions} new features suggest minor version bump"
        else:
            recommended = v_current.bump_patch()
            reason = "Only bug fixes or internal changes, patch version bump"

        # Alternative recommendations
        alternatives = []

        if breaking == 0:
            if extensions > 0:
                alternatives.append({"version": str(v_current.bump_patch()), "reason": "If features are considered bug fixes"})

            alternatives.append({"version": str(v_current.bump_major()), "reason": "If planning breaking changes in near future"})

        return {
            "success": True,
            "current_version": current_version,
            "recommended_version": str(recommended),
            "reason": reason,
            "alternatives": alternatives,
            "change_summary": {"breaking_changes": breaking, "extensions": extensions, "total_changes": stats["total_changes"]},
        }


class VersionPolicyEnforcer:
    """Enforces version policies."""

    def __init__(self, policy: VersionPolicy):
        self.policy = policy
        self.validator = VersionValidator()

    def enforce(self, current_version: str, proposed_version: str, diff: Any) -> Dict[str, Any]:
        """Enforce version policy."""
        # Validate format
        format_check = self.validator.validate_format(proposed_version)
        if not format_check["valid"]:
            return {"approved": False, "reason": "Invalid version format", "issues": format_check.get("issues", [])}

        # Validate transition
        transition_check = self.validator.validate_transition(current_version, proposed_version)
        if not transition_check["valid"]:
            return {"approved": False, "reason": "Invalid version transition", "issues": transition_check["issues"]}

        # Check policy compliance
        compliance = self.policy.check_compliance(current_version, proposed_version, diff)

        if not compliance["compliant"]:
            return {
                "approved": False,
                "reason": "Version policy violations",
                "violations": compliance["violations"],
                "warnings": compliance.get("warnings", []),
            }

        return {"approved": True, "version": proposed_version, "warnings": compliance.get("warnings", [])}


class VersionRangeParser:
    """Parses and evaluates version ranges."""

    def parse_range(self, range_spec: str) -> Dict[str, Any]:
        """Parse version range specification."""
        # Simple range patterns
        if range_spec.startswith(">="):
            return {"type": "greater_equal", "version": range_spec[2:].strip()}
        elif range_spec.startswith(">"):
            return {"type": "greater", "version": range_spec[1:].strip()}
        elif range_spec.startswith("<="):
            return {"type": "less_equal", "version": range_spec[2:].strip()}
        elif range_spec.startswith("<"):
            return {"type": "less", "version": range_spec[1:].strip()}
        elif range_spec.startswith("=="):
            return {"type": "equal", "version": range_spec[2:].strip()}
        elif range_spec.startswith("^"):
            return {"type": "caret", "version": range_spec[1:].strip()}
        else:
            return {"type": "exact", "version": range_spec}

    def satisfies_range(self, version: str, range_spec: str) -> bool:
        """Check if version satisfies range."""
        range_info = self.parse_range(range_spec)

        try:
            v = SemanticVersion.parse(version)
            v_range = SemanticVersion.parse(range_info["version"])
        except ValueError:
            return False

        range_type = range_info["type"]

        if range_type == "greater_equal":
            return v >= v_range
        elif range_type == "greater":
            return v > v_range
        elif range_type == "less_equal":
            return v <= v_range
        elif range_type == "less":
            return v < v_range
        elif range_type == "equal" or range_type == "exact":
            return v == v_range
        elif range_type == "caret":
            # ^1.5.0 means >=1.5.0, <2.0.0
            return v >= v_range and v.major == v_range.major

        return False


class VersionRetirementPlanner:
    """Plans version retirements."""

    def __init__(self, lifecycle_manager: LifecycleManager):
        self.manager = lifecycle_manager

    def plan_retirement(self, version: str, retirement_strategy: str = "graceful") -> Dict[str, Any]:
        """Plan version retirement."""
        lifecycle = self.manager.get_lifecycle(version)
        if not lifecycle:
            return {"success": False, "error": "Version not found"}

        if lifecycle.stage == LifecycleStage.END_OF_LIFE:
            return {"success": False, "error": "Version already retired"}

        plan = {"success": True, "version": version, "strategy": retirement_strategy, "phases": []}

        if retirement_strategy == "graceful":
            plan["phases"] = [
                {
                    "phase": 1,
                    "name": "Deprecation Notice",
                    "duration_days": 180,
                    "actions": ["Announce deprecation", "Update documentation", "Publish migration guide"],
                },
                {
                    "phase": 2,
                    "name": "Maintenance Mode",
                    "duration_days": 180,
                    "actions": ["Security fixes only", "No new features", "Encourage migration"],
                },
                {
                    "phase": 3,
                    "name": "End-of-Life",
                    "duration_days": 0,
                    "actions": ["Stop all updates", "Remove from supported versions list"],
                },
            ]
        elif retirement_strategy == "forced":
            plan["phases"] = [
                {
                    "phase": 1,
                    "name": "Final Notice",
                    "duration_days": 90,
                    "actions": ["Final warning", "Mandatory upgrade notice"],
                },
                {
                    "phase": 2,
                    "name": "Immediate Retirement",
                    "duration_days": 0,
                    "actions": ["Remove support", "Bindings may fail to compile"],
                },
            ]

        return plan

    def get_retirement_timeline(self, version: str) -> Dict[str, Any]:
        """Get retirement timeline for version."""
        lifecycle = self.manager.get_lifecycle(version)
        if not lifecycle or not lifecycle.deprecation_notice:
            return {"has_timeline": False}

        notice = lifecycle.deprecation_notice

        return {
            "has_timeline": True,
            "version": version,
            "deprecated_at": notice.deprecated_at,
            "end_of_life_at": notice.end_of_life_at,
            "days_remaining": notice.days_until_eol(),
            "replacement_version": notice.replacement_version,
            "migration_guide": notice.migration_guide_url,
        }


class StabilityGuaranteeChecker:
    """Checks if version changes violate stability guarantees."""

    def __init__(self, lifecycle_manager: LifecycleManager):
        self.manager = lifecycle_manager

    def check_compatibility_with_guarantees(
        self, baseline_version: str, candidate_version: str, diff: Any  # DetailedDiff
    ) -> Dict[str, Any]:
        """Check if diff violates stability guarantees."""
        baseline_lc = self.manager.get_lifecycle(baseline_version)

        if not baseline_lc:
            return {"checked": False, "reason": "Baseline version lifecycle not found"}

        violations = []
        warnings = []

        # Check if baseline is stable
        if baseline_lc.stage == LifecycleStage.STABLE:
            # Stable versions should not have breaking changes in minor/patch updates
            baseline_parts = baseline_version.split(".")
            candidate_parts = candidate_version.split(".")

            if len(baseline_parts) >= 1 and len(candidate_parts) >= 1:
                if baseline_parts[0] == candidate_parts[0]:
                    # Same major version
                    breaking_count = len(diff.get_breaking_changes())
                    if breaking_count > 0:
                        violations.append(
                            f"Breaking changes detected in same major version "
                            f"({baseline_version} → {candidate_version})"
                        )

        return {"checked": True, "compliant": len(violations) == 0, "violations": violations, "warnings": warnings}


class RollbackSafety(Enum):
    """Rollback safety level."""

    SAFE = "safe"
    CONDITIONAL = "conditional"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"


class RollbackStrategy(Enum):
    """Rollback execution strategy."""

    EMERGENCY = "emergency"
    PLANNED = "planned"
    CANARY = "canary"
    SNAPSHOT = "snapshot"


@dataclass
class RollbackRisk:
    """Individual rollback risk."""

    risk_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    affected_entities: List[str] = field(default_factory=list)
    mitigation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "risk_type": self.risk_type,
            "severity": self.severity,
            "description": self.description,
            "affected_entities": self.affected_entities,
            "mitigation": self.mitigation,
        }


@dataclass
class RollbackAnalysis:
    """Analysis of rollback safety."""

    from_version: str
    to_version: str
    safety: RollbackSafety
    risks: List[RollbackRisk] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    data_at_risk: bool = False
    feature_loss: bool = False
    breaking_changes_reversed: int = 0

    def is_safe(self) -> bool:
        """Check if rollback is safe."""
        return self.safety == RollbackSafety.SAFE

    def get_critical_risks(self) -> List[RollbackRisk]:
        """Get critical risks."""
        return [r for r in self.risks if r.severity == "CRITICAL"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "safety": self.safety.value,
            "risks": [r.to_dict() for r in self.risks],
            "required_actions": self.required_actions,
            "data_at_risk": self.data_at_risk,
            "feature_loss": self.feature_loss,
            "breaking_changes_reversed": self.breaking_changes_reversed,
            "critical_risks": len(self.get_critical_risks()),
        }


class RollbackSafetyAnalyzer:
    """Analyzes rollback safety."""

    def __init__(self, version_history: VersionHistory):
        self.history = version_history

    def analyze_rollback(self, from_version: str, to_version: str) -> RollbackAnalysis:
        """Analyze rollback safety from one version to another."""
        # Get diff between versions (reversed direction)
        diff = self.history.diff_between(to_version, from_version)

        if diff is None:
            return RollbackAnalysis(
                from_version=from_version,
                to_version=to_version,
                safety=RollbackSafety.UNKNOWN,
                risks=[RollbackRisk("unknown", "CRITICAL", "Unable to analyze rollback safety (no diff data)")],
            )

        analysis = RollbackAnalysis(from_version=from_version, to_version=to_version, safety=RollbackSafety.SAFE)

        # Analyze breaking changes
        breaking_changes = diff.get_breaking_changes()
        analysis.breaking_changes_reversed = len(breaking_changes)

        if breaking_changes:
            analysis.safety = RollbackSafety.UNSAFE
            analysis.risks.append(
                RollbackRisk(
                    "breaking_changes",
                    "CRITICAL",
                    f"Rolling back {len(breaking_changes)} breaking changes may cause incompatibilities",
                    affected_entities=[c.entity_id for c in breaking_changes],
                )
            )

        # Check for additions (become removals on rollback)
        stats = diff.get_statistics()
        extensions = stats["by_severity"].get("extension", 0)

        if extensions > 0:
            analysis.feature_loss = True
            analysis.risks.append(
                RollbackRisk("feature_loss", "MEDIUM", f"{extensions} features added in newer version will be lost on rollback")
            )

            if analysis.safety == RollbackSafety.SAFE:
                analysis.safety = RollbackSafety.CONDITIONAL

        # Check strengthening (becomes relaxation on rollback)
        strengthening = stats["by_severity"].get("strengthening", 0)

        if strengthening > 0:
            analysis.data_at_risk = True
            analysis.risks.append(
                RollbackRisk(
                    "constraint_relaxation",
                    "HIGH",
                    f"{strengthening} constraints will be relaxed on rollback",
                    mitigation="Validate data before rollback",
                )
            )

            if analysis.safety == RollbackSafety.SAFE:
                analysis.safety = RollbackSafety.CONDITIONAL

        # Generate required actions
        if analysis.data_at_risk:
            analysis.required_actions.append("Backup all data before rollback")
            analysis.required_actions.append("Validate data compatibility")

        if analysis.feature_loss:
            analysis.required_actions.append("Ensure no dependencies on removed features")

        if analysis.breaking_changes_reversed > 0:
            analysis.required_actions.append("Regenerate bindings for target version")
            analysis.required_actions.append("Test all affected code paths")

        return analysis

    def find_safe_rollback_path(self, from_version: str, target_version: str) -> Optional[List[str]]:
        """Find safe rollback path through intermediate versions."""
        # Get version timeline
        timeline = self.history.timeline_between(target_version, from_version)

        if not timeline:
            return None

        # Reverse timeline for rollback
        rollback_path = [from_version]

        for baseline, candidate in reversed(timeline):
            rollback_path.append(baseline)

        return rollback_path


class DowngradePathGenerator:
    """Generates downgrade paths."""

    def __init__(self, version_history: VersionHistory, safety_analyzer: RollbackSafetyAnalyzer):
        self.history = version_history
        self.analyzer = safety_analyzer

    def generate_downgrade_path(
        self, from_version: str, to_version: str, strategy: RollbackStrategy = RollbackStrategy.PLANNED
    ) -> Dict[str, Any]:
        """Generate downgrade path."""
        # Direct downgrade analysis
        direct_analysis = self.analyzer.analyze_rollback(from_version, to_version)

        path = {"from_version": from_version, "to_version": to_version, "strategy": strategy.value, "steps": []}

        if strategy == RollbackStrategy.EMERGENCY:
            # Emergency: direct rollback, skip safety checks
            path["steps"].append(
                {
                    "step": 1,
                    "action": f"Emergency rollback to {to_version}",
                    "safety_check": "SKIPPED",
                    "warnings": ["Safety checks bypassed", "Data loss possible"],
                }
            )

        elif strategy == RollbackStrategy.PLANNED:
            # Planned: include safety analysis
            if direct_analysis.is_safe():
                path["steps"].append(
                    {
                        "step": 1,
                        "action": f"Direct rollback to {to_version}",
                        "safety": "SAFE",
                        "required_actions": direct_analysis.required_actions,
                    }
                )
            else:
                # Find incremental path
                rollback_versions = self.analyzer.find_safe_rollback_path(from_version, to_version)

                if rollback_versions:
                    for i in range(len(rollback_versions) - 1):
                        path["steps"].append(
                            {
                                "step": i + 1,
                                "from": rollback_versions[i],
                                "to": rollback_versions[i + 1],
                                "action": f"Rollback to {rollback_versions[i + 1]}",
                            }
                        )

        elif strategy == RollbackStrategy.SNAPSHOT:
            # Snapshot: restore from backup
            path["steps"].append(
                {
                    "step": 1,
                    "action": "Restore from snapshot",
                    "snapshot_version": to_version,
                    "data_loss": "Changes after snapshot will be lost",
                }
            )

        path["total_steps"] = len(path["steps"])
        path["analysis"] = direct_analysis.to_dict()

        return path


class RollbackSimulator:
    """Simulates rollback scenarios."""

    def __init__(self, safety_analyzer: RollbackSafetyAnalyzer):
        self.analyzer = safety_analyzer

    def simulate_rollback(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Simulate rollback and predict issues."""
        analysis = self.analyzer.analyze_rollback(from_version, to_version)

        simulation = {
            "from_version": from_version,
            "to_version": to_version,
            "predicted_outcome": "SUCCESS" if analysis.is_safe() else "FAILURE",
            "issues": [],
            "warnings": [],
        }

        # Predict issues based on risks
        for risk in analysis.risks:
            issue = {"type": risk.risk_type, "severity": risk.severity, "description": risk.description}

            if risk.severity in ["CRITICAL", "HIGH"]:
                simulation["issues"].append(issue)
            else:
                simulation["warnings"].append(issue)

        # Predict data compatibility
        if analysis.data_at_risk:
            simulation["issues"].append(
                {
                    "type": "data_compatibility",
                    "severity": "HIGH",
                    "description": "Data written by newer version may not be readable by older version",
                }
            )

        # Predict feature availability
        if analysis.feature_loss:
            simulation["warnings"].append(
                {
                    "type": "feature_availability",
                    "severity": "MEDIUM",
                    "description": "Some features will no longer be available after rollback",
                }
            )

        return simulation


class RollbackPreflightChecker:
    """Performs preflight checks before rollback."""

    def __init__(self, safety_analyzer: RollbackSafetyAnalyzer):
        self.analyzer = safety_analyzer

    def run_preflight_checks(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Run preflight checks for rollback."""
        analysis = self.analyzer.analyze_rollback(from_version, to_version)

        checks = {"passed": [], "failed": [], "warnings": []}

        # Check 1: Safety level
        if analysis.is_safe():
            checks["passed"].append({"check": "safety_level", "result": "PASS", "message": "Rollback is safe"})
        elif analysis.safety == RollbackSafety.CONDITIONAL:
            checks["warnings"].append(
                {"check": "safety_level", "result": "WARNING", "message": "Rollback requires preparation"}
            )
        else:
            checks["failed"].append({"check": "safety_level", "result": "FAIL", "message": "Rollback is unsafe"})

        # Check 2: Critical risks
        critical_risks = analysis.get_critical_risks()
        if not critical_risks:
            checks["passed"].append({"check": "critical_risks", "result": "PASS", "message": "No critical risks detected"})
        else:
            checks["failed"].append(
                {"check": "critical_risks", "result": "FAIL", "message": f"{len(critical_risks)} critical risks detected"}
            )

        # Check 3: Data compatibility
        if not analysis.data_at_risk:
            checks["passed"].append({"check": "data_compatibility", "result": "PASS", "message": "Data is compatible"})
        else:
            checks["warnings"].append(
                {
                    "check": "data_compatibility",
                    "result": "WARNING",
                    "message": "Data compatibility requires verification",
                }
            )

        # Overall result
        checks["overall"] = "PASS" if not checks["failed"] else "FAIL"
        checks["safe_to_proceed"] = len(checks["failed"]) == 0

        return checks


class RollbackRecoveryPlanner:
    """Plans recovery from failed rollbacks."""

    def create_recovery_plan(
        self, failed_rollback_from: str, failed_rollback_to: str, failure_reason: str
    ) -> Dict[str, Any]:
        """Create plan to recover from failed rollback."""
        plan = {
            "failed_rollback": {
                "from_version": failed_rollback_from,
                "to_version": failed_rollback_to,
                "reason": failure_reason,
            },
            "recovery_options": [],
        }

        # Option 1: Roll forward to original version
        plan["recovery_options"].append(
            {
                "option": 1,
                "strategy": "roll_forward",
                "action": f"Upgrade back to {failed_rollback_from}",
                "description": "Return to version before rollback",
                "risk": "LOW",
                "time_estimate": "Quick",
            }
        )

        # Option 2: Restore from backup
        plan["recovery_options"].append(
            {
                "option": 2,
                "strategy": "restore_backup",
                "action": "Restore from backup snapshot",
                "description": "Restore complete state from backup",
                "risk": "MEDIUM",
                "time_estimate": "Medium",
                "data_loss": "Changes after backup will be lost",
            }
        )

        # Option 3: Manual intervention
        plan["recovery_options"].append(
            {
                "option": 3,
                "strategy": "manual_fix",
                "action": "Manual data repair",
                "description": "Manually fix data inconsistencies",
                "risk": "HIGH",
                "time_estimate": "Long",
            }
        )

        return plan


class ChangelogFormat(Enum):
    """Changelog output format."""

    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    TEXT = "text"


@dataclass
class ChangelogEntry:
    """Single changelog entry."""

    category: str
    description: str
    entity_id: Optional[str] = None
    severity: Optional[str] = None
    migration_hint: Optional[str] = None
    details: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        parts = []

        # Main description
        if self.entity_id:
            parts.append(f"- **{self.entity_id}**: {self.description}")
        else:
            parts.append(f"- {self.description}")

        # Add severity badge if present
        if self.severity and self.severity != "NEUTRAL":
            parts[0] += f" `[{self.severity}]`"

        # Add migration hint if present
        if self.migration_hint:
            parts.append(f"  - *Migration:* {self.migration_hint}")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "description": self.description,
            "entity_id": self.entity_id,
            "severity": self.severity,
            "migration_hint": self.migration_hint,
            "details": self.details,
        }


@dataclass
class Changelog:
    """Version changelog."""

    from_version: str
    to_version: str
    release_date: Optional[str] = None
    entries: List[ChangelogEntry] = field(default_factory=list)
    summary: Optional[str] = None

    def add_entry(self, entry: ChangelogEntry) -> None:
        """Add changelog entry."""
        self.entries.append(entry)

    def get_entries_by_category(self, category: str) -> List[ChangelogEntry]:
        """Get entries by category."""
        return [e for e in self.entries if e.category == category]

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        lines = []

        # Header
        lines.append(f"# Changelog: {self.from_version} → {self.to_version}")
        if self.release_date:
            lines.append(f"**Release Date:** {self.release_date}")
        lines.append("")

        # Summary
        if self.summary:
            lines.append(self.summary)
            lines.append("")

        # Categories in priority order
        categories = [
            ("Breaking Changes", "breaking"),
            ("Deprecations", "deprecation"),
            ("New Features", "feature"),
            ("Enhancements", "enhancement"),
            ("Bug Fixes", "bugfix"),
            ("Internal Changes", "internal"),
        ]

        for title, category in categories:
            entries = self.get_entries_by_category(category)
            if entries:
                lines.append(f"## {title}")
                lines.append("")
                for entry in entries:
                    lines.append(entry.to_markdown())
                lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "release_date": self.release_date,
            "summary": self.summary,
            "entries": [e.to_dict() for e in self.entries],
        }


class ChangelogGenerator:
    """Generates changelogs from diffs."""

    def generate(self, diff: Any, from_version: str, to_version: str) -> Changelog:
        """Generate changelog from diff."""
        changelog = Changelog(from_version, to_version)

        # Generate summary
        stats = diff.get_statistics()
        breaking_count = stats["by_severity"].get("breaking", 0)
        extension_count = stats["by_severity"].get("extension", 0)

        summary_parts = []
        if breaking_count > 0:
            summary_parts.append(f"{breaking_count} breaking change(s)")
        if extension_count > 0:
            summary_parts.append(f"{extension_count} new feature(s)")

        if summary_parts:
            changelog.summary = "This release includes: " + ", ".join(summary_parts) + "."

        # Process entity diffs
        for entity_diff in diff.entity_diffs:
            for change in entity_diff.changes:
                entry = self._change_to_entry(change, entity_diff)
                if entry:
                    changelog.add_entry(entry)

        return changelog

    def _change_to_entry(self, change: Any, entity_diff: Any) -> Optional[ChangelogEntry]:
        """Convert change to changelog entry."""
        category = self._determine_category(change)
        description = self._format_description(change, entity_diff)
        migration_hint = self._generate_migration_hint(change)

        return ChangelogEntry(
            category=category,
            description=description,
            entity_id=entity_diff.entity_id,
            severity=change.severity.value if hasattr(change.severity, "value") else str(change.severity),
            migration_hint=migration_hint,
        )

    def _determine_category(self, change: Any) -> str:
        """Determine changelog category."""
        change_type = change.change_type
        severity = str(change.severity).upper()

        if "BREAKING" in severity:
            return "breaking"
        elif "EXTENSION" in severity or "added" in change_type:
            return "feature"
        elif "removed" in change_type:
            return "breaking"
        elif "deprecated" in change_type:
            return "deprecation"
        elif "fix" in change_type.lower():
            return "bugfix"
        elif "STRENGTHENING" in severity or "RELAXATION" in severity:
            return "enhancement"
        else:
            return "internal"

    def _format_description(self, change: Any, entity_diff: Any) -> str:
        """Format change description."""
        if change.description:
            return change.description

        # Generate description from change type
        change_type = change.change_type
        entity_type = entity_diff.entity_type

        if change_type == "function_added":
            return f"Added new {entity_type}"
        elif change_type == "function_removed":
            return f"Removed {entity_type}"
        elif "type_changed" in change_type:
            return f"Changed {entity_type} type"
        else:
            return f"{change_type.replace('_', ' ').title()}"

    def _generate_migration_hint(self, change: Any) -> Optional[str]:
        """Generate migration hint."""
        if hasattr(change, "severity") and "BREAKING" in str(change.severity).upper():
            if "removed" in change.change_type:
                return "Remove references to this entity"
            elif "type_changed" in change.change_type:
                return "Update type declarations"
            elif "parameter" in change.change_type:
                return "Update function calls"

        return None


class ReleaseNotesGenerator:
    """Generates user-facing release notes."""

    def generate(self, changelog: Changelog, template: Optional[str] = None) -> str:
        """Generate release notes."""
        if template:
            return self._apply_template(changelog, template)

        # Default template
        lines = []

        # Header
        lines.append(f"# Release Notes: Version {changelog.to_version}")
        if changelog.release_date:
            lines.append(f"*Released: {changelog.release_date}*")
        lines.append("")

        # Highlights
        breaking = changelog.get_entries_by_category("breaking")
        features = changelog.get_entries_by_category("feature")

        if breaking or features:
            lines.append("## Highlights")
            lines.append("")

            if features:
                lines.append("### New Features")
                for entry in features[:3]:  # Top 3
                    lines.append(f"- {entry.description}")
                lines.append("")

            if breaking:
                lines.append("### Important Changes")
                lines.append(f"⚠️ This release includes {len(breaking)} breaking change(s).")
                lines.append("Please review the migration guide below.")
                lines.append("")

        # Migration guide for breaking changes
        if breaking:
            lines.append("## Migration Guide")
            lines.append("")
            for entry in breaking:
                lines.append(f"### {entry.entity_id or 'Change'}")
                lines.append(f"{entry.description}")
                if entry.migration_hint:
                    lines.append(f"**Action Required:** {entry.migration_hint}")
                lines.append("")

        # Full changelog reference
        lines.append("---")
        lines.append(f"For a complete list of changes, see the [full changelog](#changelog).")

        return "\n".join(lines)

    def _apply_template(self, changelog: Changelog, template: str) -> str:
        """Apply template to changelog."""
        replacements = {
            "{version}": changelog.to_version,
            "{from_version}": changelog.from_version,
            "{date}": changelog.release_date or "TBD",
            "{breaking_count}": str(len(changelog.get_entries_by_category("breaking"))),
            "{feature_count}": str(len(changelog.get_entries_by_category("feature"))),
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)

        return result


class MigrationGuideGenerator:
    """Generates migration guides."""

    def generate(self, changelog: Changelog) -> str:
        """Generate migration guide."""
        breaking_changes = changelog.get_entries_by_category("breaking")

        if not breaking_changes:
            return "# Migration Guide\n\nNo breaking changes in this release."

        lines = []
        lines.append(f"# Migration Guide: {changelog.from_version} → {changelog.to_version}")
        lines.append("")
        lines.append(f"This guide helps you migrate from version {changelog.from_version} to {changelog.to_version}.")
        lines.append("")

        # Overview
        lines.append("## Overview")
        lines.append(f"This release includes {len(breaking_changes)} breaking change(s).")
        lines.append("")

        # Individual changes
        lines.append("## Breaking Changes")
        lines.append("")

        for i, entry in enumerate(breaking_changes, 1):
            lines.append(f"### {i}. {entry.entity_id or 'Change'}")
            lines.append("")
            lines.append(f"**Description:** {entry.description}")
            lines.append("")

            if entry.migration_hint:
                lines.append(f"**Migration Steps:**")
                lines.append(f"1. {entry.migration_hint}")
                lines.append("")

            if entry.details:
                lines.append(f"**Details:**")
                lines.append(entry.details)
                lines.append("")

        return "\n".join(lines)


class ChangelogFormatter:
    """Formats changelogs in different formats."""

    def format(self, changelog: Changelog, format_type: ChangelogFormat) -> str:
        """Format changelog."""
        if format_type == ChangelogFormat.MARKDOWN:
            return changelog.to_markdown()
        elif format_type == ChangelogFormat.JSON:
            import json

            return json.dumps(changelog.to_dict(), indent=2)
        elif format_type == ChangelogFormat.TEXT:
            return self._to_plain_text(changelog)
        elif format_type == ChangelogFormat.HTML:
            return self._to_html(changelog)
        else:
            return changelog.to_markdown()

    def _to_plain_text(self, changelog: Changelog) -> str:
        """Convert to plain text."""
        lines = []
        lines.append(f"CHANGELOG: {changelog.from_version} -> {changelog.to_version}")
        lines.append("=" * 60)

        if changelog.release_date:
            lines.append(f"Release Date: {changelog.release_date}")

        lines.append("")

        categories = ["breaking", "feature", "bugfix", "internal"]
        category_names = {
            "breaking": "BREAKING CHANGES",
            "feature": "NEW FEATURES",
            "bugfix": "BUG FIXES",
            "internal": "INTERNAL CHANGES",
        }

        for cat in categories:
            entries = changelog.get_entries_by_category(cat)
            if entries:
                lines.append(category_names[cat])
                lines.append("-" * 40)
                for entry in entries:
                    lines.append(f"* {entry.description}")
                lines.append("")

        return "\n".join(lines)

    def _to_html(self, changelog: Changelog) -> str:
        """Convert to HTML."""
        html = []
        html.append("<div class='changelog'>")
        html.append(f"<h1>Changelog: {changelog.from_version} → {changelog.to_version}</h1>")

        if changelog.release_date:
            html.append(f"<p class='date'>{changelog.release_date}</p>")

        if changelog.summary:
            html.append(f"<p class='summary'>{changelog.summary}</p>")

        categories = [("Breaking Changes", "breaking"), ("New Features", "feature"), ("Bug Fixes", "bugfix")]

        for title, cat in categories:
            entries = changelog.get_entries_by_category(cat)
            if entries:
                html.append(f"<h2>{title}</h2>")
                html.append("<ul>")
                for entry in entries:
                    html.append(f"<li>{entry.description}</li>")
                html.append("</ul>")

        html.append("</div>")
        return "\n".join(html)


class ChangelogComparer:
    """Compares changelogs across versions."""

    def compare(self, changelog1: Changelog, changelog2: Changelog) -> Dict[str, Any]:
        """Compare two changelogs."""
        return {
            "changelog1": {
                "version": changelog1.to_version,
                "entry_count": len(changelog1.entries),
                "breaking_count": len(changelog1.get_entries_by_category("breaking")),
            },
            "changelog2": {
                "version": changelog2.to_version,
                "entry_count": len(changelog2.entries),
                "breaking_count": len(changelog2.get_entries_by_category("breaking")),
            },
            "differences": {
                "entry_count_diff": len(changelog2.entries) - len(changelog1.entries),
                "breaking_count_diff": (
                    len(changelog2.get_entries_by_category("breaking")) - len(changelog1.get_entries_by_category("breaking"))
                ),
            },
        }


@dataclass
class Author:
    """Version author information."""

    name: str
    email: str
    timestamp: Optional[str] = None
    role: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"name": self.name, "email": self.email, "timestamp": self.timestamp, "role": self.role}


@dataclass
class BuildInfo:
    """Build information."""

    build_number: Optional[int] = None
    build_timestamp: Optional[str] = None
    builder: Optional[str] = None
    build_host: Optional[str] = None
    compiler_version: Optional[str] = None
    tool_version: Optional[str] = None
    source_commit: Optional[str] = None
    source_branch: Optional[str] = None
    source_repo: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "build_number": self.build_number,
            "build_timestamp": self.build_timestamp,
            "builder": self.builder,
            "build_host": self.build_host,
            "compiler_version": self.compiler_version,
            "tool_version": self.tool_version,
            "source_commit": self.source_commit,
            "source_branch": self.source_branch,
            "source_repo": self.source_repo,
        }


@dataclass
class Certification:
    """Compliance certification."""

    standard: str
    level: Optional[str] = None
    issued_date: Optional[str] = None
    expires_date: Optional[str] = None
    issuer: Optional[str] = None
    attestation: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if certification is expired."""
        if not self.expires_date:
            return False

        try:
            # Handle isoformat with space instead of T, and handle Z
            date_str = self.expires_date.replace("Z", "+00:00")
            expires = datetime.fromisoformat(date_str)
            # Ensure compare same timezone awareness
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) > expires
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "standard": self.standard,
            "level": self.level,
            "issued_date": self.issued_date,
            "expires_date": self.expires_date,
            "issuer": self.issuer,
            "attestation": self.attestation,
        }


@dataclass
class VersionMetadata:
    """Comprehensive version metadata."""

    version: str
    created_at: str
    author: Optional[Author] = None
    build_info: Optional[BuildInfo] = None
    certifications: List[Certification] = field(default_factory=list)
    license: Optional[str] = None
    dependencies: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def add_certification(self, cert: Certification) -> None:
        """Add certification."""
        self.certifications.append(cert)

    def add_dependency(self, name: str, version: str) -> None:
        """Add dependency."""
        self.dependencies[name] = version

    def add_tag(self, tag: str) -> None:
        """Add tag."""
        if tag not in self.tags:
            self.tags.append(tag)

    def get_active_certifications(self) -> List[Certification]:
        """Get non-expired certifications."""
        return [c for c in self.certifications if not c.is_expired()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "author": self.author.to_dict() if self.author else None,
            "build_info": self.build_info.to_dict() if self.build_info else None,
            "certifications": [c.to_dict() for c in self.certifications],
            "license": self.license,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "custom_metadata": self.custom_metadata,
        }


@dataclass
class Signature:
    """Digital signature."""

    algorithm: str
    signature_data: str
    signer_name: str
    signer_email: str
    public_key_id: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "algorithm": self.algorithm,
            "signature": self.signature_data,
            "signer": {
                "name": self.signer_name,
                "email": self.signer_email,
                "public_key_id": self.public_key_id,
                "timestamp": self.timestamp,
            },
        }


@dataclass
class VersionProvenance:
    """Version provenance information."""

    version: str
    fingerprint: str
    parent_version: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Optional[VersionMetadata] = None
    signature: Optional[Signature] = None
    approval_chain: List[str] = field(default_factory=list)

    def add_approval(self, approver: str) -> None:
        """Add approver to chain."""
        if approver not in self.approval_chain:
            self.approval_chain.append(approver)

    def is_signed(self) -> bool:
        """Check if version is signed."""
        return self.signature is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "fingerprint": self.fingerprint,
            "parent_version": self.parent_version,
            "created_at": self.created_at,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "signature": self.signature.to_dict() if self.signature else None,
            "approval_chain": self.approval_chain,
        }


class MetadataManager:
    """Manages version metadata."""

    def __init__(self):
        self.metadata_store: Dict[str, VersionMetadata] = {}

    def add_metadata(self, metadata: VersionMetadata) -> None:
        """Add version metadata."""
        self.metadata_store[metadata.version] = metadata

    def get_metadata(self, version: str) -> Optional[VersionMetadata]:
        """Get metadata for version."""
        return self.metadata_store.get(version)

    def update_metadata(self, version: str, updates: Dict[str, Any]) -> bool:
        """Update version metadata."""
        metadata = self.metadata_store.get(version)
        if not metadata:
            return False

        for key, value in updates.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)

        return True

    def get_versions_by_tag(self, tag: str) -> List[str]:
        """Get versions with specific tag."""
        return [version for version, meta in self.metadata_store.items() if tag in meta.tags]

    def get_versions_by_author(self, author_email: str) -> List[str]:
        """Get versions by author."""
        return [version for version, meta in self.metadata_store.items() if meta.author and meta.author.email == author_email]


class ProvenanceTracker:
    """Tracks version provenance."""

    def __init__(self):
        self.provenance_store: Dict[str, VersionProvenance] = {}

    def add_provenance(self, provenance: VersionProvenance) -> None:
        """Add version provenance."""
        self.provenance_store[provenance.version] = provenance

    def get_provenance(self, version: str) -> Optional[VersionProvenance]:
        """Get provenance for version."""
        return self.provenance_store.get(version)

    def get_provenance_chain(self, version: str) -> List[VersionProvenance]:
        """Get full provenance chain."""
        chain = []
        current = version

        while current:
            prov = self.provenance_store.get(current)
            if not prov:
                break

            chain.append(prov)
            current = prov.parent_version

        return chain

    def verify_chain(self, version: str) -> Dict[str, Any]:
        """Verify provenance chain integrity."""
        chain = self.get_provenance_chain(version)

        if not chain:
            return {"valid": False, "reason": "No provenance data found"}

        issues = []

        # Check for gaps in chain
        for i in range(len(chain) - 1):
            current = chain[i]
            parent = chain[i + 1]

            if current.parent_version != parent.version:
                issues.append(f"Chain gap: {current.version} parent mismatch")

        return {"valid": len(issues) == 0, "chain_length": len(chain), "issues": issues}


class SignatureManager:
    """Manages digital signatures."""

    def create_signature(
        self, version: str, fingerprint: str, signer_name: str, signer_email: str, algorithm: str = "SHA256"
    ) -> Signature:
        """Create signature (simplified - no actual crypto)."""
        # In production, would use actual cryptographic signing
        now = datetime.now(timezone.utc)
        data_to_sign = f"{version}:{fingerprint}:{now.isoformat()}"
        signature_data = hashlib.sha256(data_to_sign.encode()).hexdigest()

        return Signature(
            algorithm=algorithm,
            signature_data=signature_data,
            signer_name=signer_name,
            signer_email=signer_email,
            timestamp=now.isoformat().replace("+00:00", "Z"),
        )

    def verify_signature(self, signature: Signature, version: str, fingerprint: str) -> Dict[str, Any]:
        """Verify signature (simplified)."""
        # In production, would use actual cryptographic verification

        if not signature.signature_data:
            return {"valid": False, "reason": "No signature data"}

        if not signature.timestamp:
            return {"valid": False, "reason": "No timestamp"}

        # Check timestamp is not too old (e.g., > 1 year)
        try:
            sig_time = datetime.fromisoformat(signature.timestamp.replace("Z", "+00:00"))
            # Force sig_time to be aware if it's not
            if sig_time.tzinfo is None:
                sig_time = sig_time.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - sig_time).days

            if age_days > 365:
                return {"valid": False, "reason": f"Signature too old ({age_days} days)"}
        except ValueError:
            return {"valid": False, "reason": "Invalid timestamp format"}

        return {"valid": True, "signer": signature.signer_name, "timestamp": signature.timestamp}


class ComplianceChecker:
    """Checks compliance status."""

    def check_compliance(self, metadata: VersionMetadata, required_standards: List[str]) -> Dict[str, Any]:
        """Check if version meets compliance requirements."""
        active_certs = metadata.get_active_certifications()
        active_standards = {cert.standard for cert in active_certs}

        missing = [std for std in required_standards if std not in active_standards]

        return {
            "compliant": len(missing) == 0,
            "active_certifications": list(active_standards),
            "missing_certifications": missing,
            "expired_certifications": [cert.standard for cert in metadata.certifications if cert.is_expired()],
        }


class MetadataValidator:
    """Validates metadata completeness."""

    def validate(self, metadata: VersionMetadata) -> Dict[str, Any]:
        """Validate metadata."""
        issues = []
        warnings = []

        # Check required fields
        if not metadata.version:
            issues.append("Version is required")

        if not metadata.created_at:
            issues.append("Created timestamp is required")

        # Check author info
        if metadata.author:
            if not metadata.author.name:
                warnings.append("Author name not specified")
            if not metadata.author.email:
                warnings.append("Author email not specified")
        else:
            warnings.append("No author information provided")

        # Check build info
        if metadata.build_info:
            if not metadata.build_info.source_commit:
                warnings.append("No source commit specified")
        else:
            warnings.append("No build information provided")

        # Check license
        if not metadata.license:
            warnings.append("No license specified")

        return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}


class ProvenanceExporter:
    """Exports provenance data."""

    def export(self, provenance: VersionProvenance, format: str = "json") -> str:
        """Export provenance data."""
        data = provenance.to_dict()

        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "yaml":
            # Simplified YAML representation
            lines = []
            lines.append(f"version: {data['version']}")
            lines.append(f"fingerprint: {data['fingerprint']}")
            if data["parent_version"]:
                lines.append(f"parent_version: {data['parent_version']}")
            if data["created_at"]:
                lines.append(f"created_at: {data['created_at']}")

            return "\n".join(lines)
        else:
            return str(data)

    def import_provenance(self, data_str: str, format: str = "json") -> Optional[VersionProvenance]:
        """Import provenance data."""
        try:
            if format == "json":
                data = json.loads(data_str)
            else:
                return None

            # Reconstruct provenance
            metadata = None
            if data.get("metadata"):
                meta_data = data["metadata"]
                author = None
                if meta_data.get("author"):
                    author = Author(**meta_data["author"])

                metadata = VersionMetadata(
                    version=meta_data["version"],
                    created_at=meta_data["created_at"],
                    author=author,
                    license=meta_data.get("license"),
                    dependencies=meta_data.get("dependencies", {}),
                    tags=meta_data.get("tags", []),
                )

            signature = None
            if data.get("signature"):
                sig_data = data["signature"]
                signer = sig_data.get("signer", {})
                signature = Signature(
                    algorithm=sig_data["algorithm"],
                    signature_data=sig_data["signature"],
                    signer_name=signer.get("name", ""),
                    signer_email=signer.get("email", ""),
                    public_key_id=signer.get("public_key_id"),
                    timestamp=signer.get("timestamp"),
                )

            return VersionProvenance(
                version=data["version"],
                fingerprint=data["fingerprint"],
                parent_version=data.get("parent_version"),
                created_at=data.get("created_at"),
                metadata=metadata,
                signature=signature,
                approval_chain=data.get("approval_chain", []),
            )

        except (json.JSONDecodeError, KeyError):
            return None


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
    # From Prompt 15
    "RollbackSafety",
    "RollbackStrategy",
    "RollbackRisk",
    "RollbackAnalysis",
    "RollbackSafetyAnalyzer",
    "DowngradePathGenerator",
    "RollbackSimulator",
    "RollbackPreflightChecker",
    "RollbackRecoveryPlanner",
    # From Prompt 3
    "SynthesisCompatibility",
    "RuleCategory",
    "SynthesisVersionStatus",
    "SynthesisRuleInfo",
    "SynthesisVersionInfo",
    "SynthesisRuleRegistry",
    "SynthesisCompatibilityDetector",
    "SynthesisEvolutionEvent",
    "SynthesisEvolutionTracker",
    "SynthesisDeterminismVerifier",
    # From Prompt 4
    "ABICompatibility",
    "ChangeType",
    "ContractChange",
    "ContractDiff",
    "ContractVersionSnapshot",
    "ContractEvolutionTimeline",
    "ABICompatibilityDetector",
    "MigrationNecessity",
    "MigrationNecessityAnalyzer",
    "ContractVersionComparator",
    # From Prompt 5
    "CompatibilityRelationship",
    "VersionRange",
    "UpgradePath",
    "UpgradePathFinder",
    # Renamed Internal Pairwise Matrix Components
    "VersionPairCompatibilityEntry",
    "VersionPairCompatibilityMatrix",
    "VersionPairCompatibilityBuilder",
    # From Prompt 6
    "PolicyLevel",
    "AdvisorySeverity",
    "CompatibilityPolicy",
    "CompatibilityAdvisory",
    "AdvisoryGenerator",
    "BaselineSource",
    "BaselineConfig",
    "BaselineManager",
    "CompatibilityCheckResult",
    "CICDCompatibilityChecker",
    # From Prompt 7
    "ChangeSeverity",
    "DetailedChange",
    "EntityDiff",
    "DetailedDiff",
    "DetailedDiffAnalyzer",
    "StructLayoutAnalyzer",
    "DiffFormatter",
    # From Prompt 8
    "FunctionSignatureAnalyzer",
    "FunctionCatalogAnalyzer",
    # From Prompt 9
    "ClauseAnalyzer",
    "ClauseCatalogAnalyzer",
    # From Prompt 10
    "VersionSnapshot",
    "VersionHistory",
    "VersionHistoryBuilder",
    "ChangeAggregator",
    # From Prompt 11
    "MigrationStrategy",
    "MigrationStep",
    "MigrationPath",
    "MigrationPathGenerator",
    "UpgradeRecommendation",
    "MigrationPlanner",
    # From Prompt 12
    "ConstraintOperator",
    "VersionConstraint",
    "ContractDependency",
    "DependencyGraph",
    "DependencyResolver",
    "CoordinatedUpgradePlanner",
    # Renamed internal components
    "VersionConstraintComponent",
    "VersionResolver",
    # From Prompt 13
    "CompatibilityStatus",
    "CompatibilityTestResult",
    "CompatibilityMatrixEntry",
    "CompatibilityMatrix",
    "CompatibilityTester",
    "CompatibilityRecommendationEngine",
    "VersionRangeSpec",
    "CompatibilityMatrixBuilder",
    # From Prompt 14
    "LifecycleStage",
    "SupportTier",
    "DeprecationNotice",
    "VersionLifecycle",
    "LifecycleManager",
    "DeprecationPolicy",
    "VersionRetirementPlanner",
    "StabilityGuaranteeChecker",
    # From Prompt 16
    "VersionValidator",
    "VersionPolicy",
    "VersionRecommendationEngine",
    "VersionPolicyEnforcer",
    "VersionRangeParser",
    # From Prompt 17
    "ChangelogFormat",
    "ChangelogEntry",
    "Changelog",
    "ChangelogGenerator",
    "ReleaseNotesGenerator",
    "MigrationGuideGenerator",
    "ChangelogFormatter",
    "ChangelogComparer",
    # From Prompt 18
    "Author",
    "BuildInfo",
    "Certification",
    "VersionMetadata",
    "Signature",
    "VersionProvenance",
    "MetadataManager",
    "ProvenanceTracker",
    "SignatureManager",
    "ComplianceChecker",
    "MetadataValidator",
    "ProvenanceExporter",
]
