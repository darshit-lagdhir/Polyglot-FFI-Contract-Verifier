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
class VersionConstraint:
    """Single version constraint (e.g., >=1.2.0).
    Represents one component of a version range specification.
    """

    operator: str  # "==", "!=", "<", "<=", ">", ">="
    version: str

    def satisfied_by(self, version: str) -> bool:
        """
        Check if a version satisfies this constraint.
        Args:
            version: Version to check
        Returns:
            True if constraint satisfied
        """
        try:
            v = SemanticVersion(version)
            constraint_v = SemanticVersion(self.version)
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

    def _parse_range(self, spec: str) -> List[VersionConstraint]:
        """Parse range specification into constraints."""
        constraints = []
        spec = spec.strip()

        # Caret range: ^1.2.3 → >=1.2.3, <2.0.0
        if spec.startswith("^"):
            version = spec[1:]
            v = SemanticVersion(version)
            constraints.append(VersionConstraint(">=", version))
            constraints.append(VersionConstraint("<", f"{v.major + 1}.0.0"))

        # Tilde range: ~1.2.3 → >=1.2.3, <1.3.0
        elif spec.startswith("~"):
            version = spec[1:]
            v = SemanticVersion(version)
            constraints.append(VersionConstraint(">=", version))
            constraints.append(VersionConstraint("<", f"{v.major}.{v.minor + 1}.0"))

        # Wildcard: 1.2.* → >=1.2.0, <1.3.0
        elif "*" in spec:
            parts = spec.split(".")
            if parts[-1] == "*":
                if len(parts) == 3:
                    # 1.2.* → >=1.2.0, <1.3.0
                    major, minor = parts[0], parts[1]
                    constraints.append(VersionConstraint(">=", f"{major}.{minor}.0"))
                    constraints.append(VersionConstraint("<", f"{major}.{int(minor) + 1}.0"))
                elif len(parts) == 2:
                    # 1.* → >=1.0.0, <2.0.0
                    major = parts[0]
                    constraints.append(VersionConstraint(">=", f"{major}.0.0"))
                    constraints.append(VersionConstraint("<", f"{int(major) + 1}.0.0"))

        # Comma-separated constraints: >=1.0.0, <2.0.0
        elif "," in spec:
            for part in spec.split(","):
                part = part.strip()
                constraints.extend(self._parse_single_constraint(part))

        # Single constraint: >=1.0.0
        else:
            constraints.extend(self._parse_single_constraint(spec))

        return constraints

    def _parse_single_constraint(self, spec: str) -> List[VersionConstraint]:
        """Parse a single constraint like '>=1.0.0'."""
        # Match operator and version
        match = re.match(r"^\s*(==|!=|<=|>=|<|>)\s*(.+)$", spec)
        if match:
            operator, version = match.groups()
            return [VersionConstraint(operator, version.strip())]

        # No operator means exact match
        return [VersionConstraint("==", spec.strip())]

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
class CompatibilityMatrixEntry:
    """Single entry in compatibility matrix.
    Records compatibility relationship between two versions.
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


class CompatibilityMatrix:
    """Matrix of compatibility relationships between all version pairs.
    Provides O(1) lookup of compatibility between any two versions.
    """

    def __init__(self):
        self.matrix: Dict[Tuple[str, str], CompatibilityMatrixEntry] = {}
        self.versions: Set[str] = set()

    def add_entry(self, entry: CompatibilityMatrixEntry):
        """
        Add a compatibility entry to matrix.
        Args:
            entry: Compatibility entry
        """
        key = (entry.from_version, entry.to_version)
        self.matrix[key] = entry
        self.versions.add(entry.from_version)
        self.versions.add(entry.to_version)

    def get_compatibility(self, from_version: str, to_version: str) -> Optional[CompatibilityMatrixEntry]:
        """
        Get compatibility between two versions.
        Args:
            from_version: Source version
            to_version: Target version
        Returns:
            CompatibilityMatrixEntry if known, None otherwise
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
class CompatibilityMatrixBuilder:
    """Builds compatibility matrix for a set of versions.
    Computes pairwise compatibility and populates matrix.
    """

    def __init__(self, abi_detector: Optional[ABICompatibilityDetector] = None):
        self.abi_detector = abi_detector or ABICompatibilityDetector()
        self.cache: Dict[Tuple[str, str], CompatibilityMatrixEntry] = {}

    def build_matrix(self, versions: List[str], contracts: Dict[str, Any]) -> CompatibilityMatrix:
        """
        Build compatibility matrix for given versions.
        Args:
            versions: List of version strings
            contracts: Mapping of version → contract object
        Returns:
            Populated CompatibilityMatrix
        """
        matrix = CompatibilityMatrix()

        for v1 in versions:
            for v2 in versions:
                entry = self._compute_compatibility(v1, v2, contracts)
                matrix.add_entry(entry)

        return matrix

    def _compute_compatibility(
        self, from_version: str, to_version: str, contracts: Dict[str, Any]
    ) -> CompatibilityMatrixEntry:
        """Compute compatibility between two versions."""
        # Check cache
        cache_key = (from_version, to_version)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Identical versions
        if from_version == to_version:
            entry = CompatibilityMatrixEntry(
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
            entry = CompatibilityMatrixEntry(
                from_version=from_version,
                to_version=to_version,
                relationship=CompatibilityRelationship.BREAKING_INCOMPATIBLE,
                migration_required=True,
            )
            self.cache[cache_key] = entry
            return entry

        # Major version difference → breaking
        if v1.major != v2.major:
            entry = CompatibilityMatrixEntry(
                from_version=from_version,
                to_version=to_version,
                relationship=CompatibilityRelationship.BREAKING_INCOMPATIBLE,
                migration_required=True,
            )

        # Minor/patch version difference → backward compatible
        elif v2 > v1:
            entry = CompatibilityMatrixEntry(
                from_version=from_version,
                to_version=to_version,
                relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
                migration_required=False,
            )

        # Older version → forward compatible (rare)
        else:
            entry = CompatibilityMatrixEntry(
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

    def __init__(self, compatibility_matrix: CompatibilityMatrix):
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
class DependencyResolver:
    """Resolves version dependencies across multiple requirements.
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
        return max(candidates, key=lambda v: SemanticVersion(v))


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
    "VersionConstraint",
    "VersionRange",
    "CompatibilityMatrixEntry",
    "CompatibilityMatrix",
    "CompatibilityMatrixBuilder",
    "UpgradePath",
    "UpgradePathFinder",
    "DependencyResolver",
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
]
