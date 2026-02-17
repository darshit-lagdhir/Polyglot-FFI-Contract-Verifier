""" Module 06: Contract Versioning System (Prompt 1/20)

Version identity model and cryptographic fingerprinting foundation.

This module implements the three-version identity system:
- schema_version: Structural format version
- synthesis_version: Rule set version
- contract_version: Interface evolution version

Plus cryptographic fingerprinting for deterministic identity. """

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
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
                f"{field_name} must be semantic version (MAJOR.MINOR.PATCH), " f"got: {version}"
            )

    def _validate_fingerprint_format(self, fingerprint: str, field_name: str):
        """Validate fingerprint is valid SHA-256 hex digest."""
        pattern = r"^[a-f0-9]{64}$"
        if not re.match(pattern, fingerprint.lower()):
            raise ValueError(
                f"{field_name} must be 64-character hex SHA-256 digest, " f"got: {fingerprint}"
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
        pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        match = re.match(pattern, version_string)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_string}")

        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
        self.version_string = version_string

    def __str__(self) -> str:
        return self.version_string

    def __repr__(self) -> str:
        return f"SemanticVersion('{self.version_string}')"

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
        """Check if this version is a major bump from other or minor bump."""
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

        Steps:
        1. Convert clauses to dictionaries
        2. Sort clauses by clause_id
        3. Sort parameters within each clause
        4. Sort metadata keys
        5. Remove any non-deterministic fields (timestamps, etc.)
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
    """Manages version identity for contract artifacts.

    Provides high-level operations:
    - Creating version metadata
    - Computing fingerprints
    - Validating version consistency
    """

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

        Args:
            schema_version: Schema version (e.g., "1.0.0")
            synthesis_version: Synthesis version (e.g., "1.0.0")
            contract_version: Contract version (e.g., "1.0.0")
            ir_fingerprint: IR fingerprint from Module 05
            clauses: List of contract clauses
            generator_tool_version: Optional tool version override

        Returns:
            ContractVersionMetadata with computed fingerprint
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

        Args:
            metadata: Contract version metadata
            clauses: List of contract clauses

        Returns:
            True if fingerprint matches, False otherwise
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

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
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
# EXPORTS
# ============================================================================
__all__ = [
    "ContractVersionMetadata",
    "SemanticVersion",
    "ContractFingerprintComputer",
    "VersionIdentityManager",
]
