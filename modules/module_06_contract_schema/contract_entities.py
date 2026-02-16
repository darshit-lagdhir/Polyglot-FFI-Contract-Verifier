"""
Module 06: Contract Schema - Entity Model

Foundational entity model for FFI contract representation.
Establishes the semantic layer above IR that encodes explicit assumptions
about FFI usage, ownership, nullability, and correctness.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from enum import Enum
from datetime import datetime
import hashlib
import json

# ============================================================================
# ENUMERATIONS
# ============================================================================


class SchemaVersion(Enum):
    """Contract schema version."""

    V1_0_0 = "1.0.0"


class GenerationMode(Enum):
    """Contract generation mode."""

    AUTO = "auto"  # Fully automated generation
    MANUAL = "manual"  # Human-authored
    HYBRID = "hybrid"  # Auto-generated with manual refinement


class ContractSeverity(Enum):
    """Clause violation severity."""

    FATAL = "fatal"
    ERROR = "error"  # Incorrect usage, block in strict mode
    WARNING = "warning"  # Potential issue, continue
    ADVISORY = "advisory"  # Informational only
    INFO = "info"
    DEBUG = "debug"


class ClauseType(Enum):
    """Semantic category of contract clause."""

    LAYOUT = "layout"  # Structure layout matching
    SIZE = "size"
    ALIGNMENT = "alignment"  # Alignment requirements
    NULLABILITY = "nullability"
    OWNERSHIP = "ownership"  # Memory ownership
    LIFETIME = "lifetime"  # Value lifetime
    RELATIONAL = "relational"  # Multi-entity relationships
    CALLING_CONVENTION = "calling_convention"  # Call mechanism
    ABI_COMPATIBILITY = "abi_compatibility"  # Version compatibility
    INITIALIZATION = "initialization"  # Memory initialization
    MUTABILITY = "mutability"
    THREAD_SAFETY = "thread_safety"  # Concurrency assumptions
    ADVISORY = "advisory"  # Non-fatal documentation


class SubjectKind(Enum):
    """Kind of IR entity referenced by clause."""

    FUNCTION = "function"
    PARAMETER = "parameter"
    RETURN_VALUE = "return_value"
    TYPE = "type"
    STRUCTURE = "structure"
    FIELD = "field"
    UNION = "union"
    ENUM = "enum"


# ============================================================================
# GENERATION METADATA
# ============================================================================


@dataclass
class GenerationMetadata:
    """
    Metadata about contract generation.

    Records how, when, and why contract was created.
    Supports auditability and trust but doesn't affect enforcement.
    """

    tool_name: str = "pfcv-contract-gen"
    tool_version: str = "1.0.0"
    generation_timestamp: str = ""
    generation_mode: GenerationMode = GenerationMode.AUTO
    ir_artifact_hash: str = ""
    generator_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if not self.generation_timestamp:
            self.generation_timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        mode_val = (
            self.generation_mode.value
            if hasattr(self.generation_mode, "value")
            else self.generation_mode
        )

        return {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "generation_timestamp": self.generation_timestamp,
            "generation_mode": mode_val,
            "ir_artifact_hash": self.ir_artifact_hash,
            "generator_config": self.generator_config,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "GenerationMetadata":
        """Deserialize from dictionary."""
        return GenerationMetadata(
            tool_name=data.get("tool_name", "pfcv-contract-gen"),
            tool_version=data.get("tool_version", "1.0.0"),
            generation_timestamp=data.get("generation_timestamp", ""),
            generation_mode=GenerationMode(data.get("generation_mode", "auto")),
            ir_artifact_hash=data.get("ir_artifact_hash", ""),
            generator_config=data.get("generator_config", {}),
        )


# ============================================================================
# CONTRACT HEADER
# ============================================================================


@dataclass
class ContractHeader:
    """
    Contract document header.

    Establishes contract identity, version, and binding to IR interface.
    Immutable once published.
    """

    schema_version: str = SchemaVersion.V1_0_0.value
    contract_version: str = "1.0.0"
    target_interface_id: str = ""
    generation_metadata: GenerationMetadata = field(default_factory=GenerationMetadata)

    # Optional fields
    contract_id: Optional[str] = None
    contract_name: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Generate contract ID if not provided."""
        if not self.contract_id:
            self.contract_id = self._generate_contract_id()

    def _generate_contract_id(self) -> str:
        """Generate stable contract identifier."""
        data = f"{self.target_interface_id}:{self.contract_version}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def validate(self) -> List[str]:
        """
        Validate header correctness.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Schema version must be valid
        try:
            SchemaVersion(self.schema_version)
        except ValueError:
            errors.append(f"Invalid schema_version: {self.schema_version}")

        # Contract version must follow semver
        if not self._is_valid_semver(self.contract_version):
            errors.append(f"Invalid contract_version: {self.contract_version}")

        # Target interface must be specified
        if not self.target_interface_id:
            errors.append("target_interface_id is required")

        return errors

    def _is_valid_semver(self, version: str) -> bool:
        """Check if version string is valid semantic version."""
        parts = version.split(".")
        if len(parts) != 3:
            return False

        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "contract_id": self.contract_id,
            "contract_name": self.contract_name,
            "target_interface_id": self.target_interface_id,
            "description": self.description,
            "generation_metadata": self.generation_metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ContractHeader":
        """Deserialize from dictionary."""
        return ContractHeader(
            schema_version=data.get("schema_version", SchemaVersion.V1_0_0.value),
            contract_version=data.get("contract_version", "1.0.0"),
            contract_id=data.get("contract_id"),
            contract_name=data.get("contract_name"),
            target_interface_id=data.get("target_interface_id", ""),
            description=data.get("description"),
            generation_metadata=GenerationMetadata.from_dict(data.get("generation_metadata", {})),
        )


# ============================================================================
# SUBJECT REFERENCE
# ============================================================================


@dataclass
class SubjectReference:
    """
    Reference to IR entity that clause applies to.

    Strongly typed reference validated against IR.
    """

    subject_kind: SubjectKind
    entity_id: str

    # Optional qualifiers for nested references
    parent_id: Optional[str] = None
    index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        kind_val = (
            self.subject_kind.value if hasattr(self.subject_kind, "value") else self.subject_kind
        )

        result = {"subject_kind": kind_val, "entity_id": self.entity_id}

        if self.parent_id:
            result["parent_id"] = self.parent_id
        if self.index is not None:
            result["index"] = self.index

        return result

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SubjectReference":
        """Deserialize from dictionary."""
        return SubjectReference(
            subject_kind=SubjectKind(data["subject_kind"]),
            entity_id=data["entity_id"],
            parent_id=data.get("parent_id"),
            index=data.get("index"),
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        ref = f"{self.subject_kind.value}:{self.entity_id}"
        if self.parent_id:
            ref += f"@{self.parent_id}"
        if self.index is not None:
            ref += f"[{self.index}]"
        return ref


# ============================================================================
# ============================================================================


@dataclass
class ConstraintParameter:
    """
    Single parameter in clause constraint.

    Typed, validated parameter value or reference.
    """

    name: str
    value: Any
    value_type: str  # "integer", "boolean", "string", "reference", "expression"

    def validate(self) -> List[str]:
        """Validate parameter correctness."""
        errors = []

        # Validate value type
        if self.value_type not in ["integer", "boolean", "string", "reference", "expression"]:
            errors.append(f"Invalid value_type: {self.value_type}")

        # Type-specific validation
        if self.value_type == "integer":
            if not isinstance(self.value, int):
                errors.append(f"Parameter {self.name} must be integer")

        elif self.value_type == "boolean":
            if not isinstance(self.value, bool):
                errors.append(f"Parameter {self.name} must be boolean")

        elif self.value_type == "string":
            if not isinstance(self.value, str):
                errors.append(f"Parameter {self.name} must be string")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {"name": self.name, "value": self.value, "value_type": self.value_type}

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ConstraintParameter":
        """Deserialize from dictionary."""
        return ConstraintParameter(
            name=data["name"], value=data["value"], value_type=data["value_type"]
        )


# ============================================================================
# CONTRACT CLAUSE
# ============================================================================


@dataclass
class ContractClause:
    """
    Single contract clause encoding one assumption.

    Independently verifiable unit of contract semantics.
    """

    clause_id: str
    clause_type: ClauseType
    subject_reference: SubjectReference
    constraint_parameters: List[ConstraintParameter] = field(default_factory=list)
    severity: ContractSeverity = ContractSeverity.ERROR

    # Optional fields
    explanation: Optional[str] = None
    rationale: Optional[str] = None
    remediation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate_structure(self) -> List[str]:
        """
        Validate clause structure (not semantics).

        Returns:
            List of structural validation errors
        """
        errors = []

        # Clause ID must be non-empty
        if not self.clause_id:
            errors.append("clause_id is required")

        # Subject reference must be valid
        if not self.subject_reference:
            errors.append("subject_reference is required")

        # Validate parameters
        for param in self.constraint_parameters:
            param_errors = param.validate()
            errors.extend(param_errors)

        return errors

    def get_parameter(self, name: str) -> Optional[ConstraintParameter]:
        """Get parameter by name."""
        for param in self.constraint_parameters:
            if param.name == name:
                return param
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        clause_type_val = (
            self.clause_type.value if hasattr(self.clause_type, "value") else self.clause_type
        )
        severity_val = self.severity.value if hasattr(self.severity, "value") else self.severity

        result = {
            "clause_id": self.clause_id,
            "clause_type": clause_type_val,
            "subject_reference": self.subject_reference.to_dict(),
            "constraint_parameters": [p.to_dict() for p in self.constraint_parameters],
            "severity": severity_val,
        }

        if self.explanation:
            result["explanation"] = self.explanation
        if self.rationale:
            result["rationale"] = self.rationale
        if self.remediation:
            result["remediation"] = self.remediation
        if self.metadata:
            result["metadata"] = self.metadata

        return result

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ContractClause":
        """Deserialize from dictionary."""
        return ContractClause(
            clause_id=data["clause_id"],
            clause_type=ClauseType(data["clause_type"]),
            subject_reference=SubjectReference.from_dict(data["subject_reference"]),
            constraint_parameters=[
                ConstraintParameter.from_dict(p) for p in data.get("constraint_parameters", [])
            ],
            severity=ContractSeverity(data.get("severity", "error")),
            explanation=data.get("explanation"),
            rationale=data.get("rationale"),
            remediation=data.get("remediation"),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# CONTRACT DOCUMENT
# ============================================================================


@dataclass
class ContractDocument:
    """
    Complete contract document.

    Top-level container for contract header and clauses.
    """

    header: ContractHeader
    clauses: List[ContractClause] = field(default_factory=list)

    def add_clause(self, clause: ContractClause):
        """Add clause to contract."""
        self.clauses.append(clause)

    def get_clause(self, clause_id: str) -> Optional[ContractClause]:
        """Get clause by ID."""
        for clause in self.clauses:
            if clause.clause_id == clause_id:
                return clause
        return None

    def get_clauses_by_type(self, clause_type: ClauseType) -> List[ContractClause]:
        """Get all clauses of specific type."""
        return [c for c in self.clauses if c.clause_type == clause_type]

    def validate_structure(self) -> List[str]:
        """
        Validate contract structure.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate header
        header_errors = self.header.validate()
        errors.extend(header_errors)

        # Validate clauses
        for clause in self.clauses:
            clause_errors = clause.validate_structure()
            errors.extend([f"Clause {clause.clause_id}: {e}" for e in clause_errors])

        # Check for duplicate clause IDs
        clause_ids = [c.clause_id for c in self.clauses]
        if len(clause_ids) != len(set(clause_ids)):
            errors.append("Duplicate clause IDs found")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {"header": self.header.to_dict(), "clauses": [c.to_dict() for c in self.clauses]}

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ContractDocument":
        """Deserialize from dictionary."""
        return ContractDocument(
            header=ContractHeader.from_dict(data["header"]),
            clauses=[ContractClause.from_dict(c) for c in data.get("clauses", [])],
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @staticmethod
    def from_json(json_str: str) -> "ContractDocument":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return ContractDocument.from_dict(data)


__all__ = [
    # Enums
    "SchemaVersion",
    "GenerationMode",
    "ContractSeverity",
    "ClauseType",
    "SubjectKind",
    # Entities
    "GenerationMetadata",
    "ContractHeader",
    "SubjectReference",
    "ConstraintParameter",
    "ContractClause",
    "ContractDocument",
]


# Compatibility Alias
Severity = ContractSeverity
