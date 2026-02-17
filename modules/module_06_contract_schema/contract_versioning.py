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
]
