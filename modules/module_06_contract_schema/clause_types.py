"""
Module 06: Contract Schema - Clause Types

Typed clause hierarchy implementing 12 constraint categories.
Each clause type provides type-safe parameters, validation, and semantics.
"""

from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod

from .contract_entities import (
    ContractClause,
    SubjectReference,
    ConstraintParameter,
    ClauseType,
    ContractSeverity as Severity,
    SubjectKind,
)

# ============================================================================
# BASE TYPED CLAUSE
# ============================================================================


class TypedClause(ABC):
    """
    Base class for all typed constraint clauses.

    Provides common interface and conversion to/from generic ContractClause.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
    ):
        self.clause_id = clause_id
        self.subject_reference = subject_reference
        self.severity = severity
        self.explanation = explanation

    @property
    @abstractmethod
    def clause_type(self) -> ClauseType:
        """Get clause type."""
        pass

    @abstractmethod
    def validate_parameters(self) -> List[str]:
        """
        Validate constraint-specific parameters.

        Returns:
            List of validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def to_generic_clause(self) -> ContractClause:
        """Convert to generic ContractClause for serialization."""
        pass


# ============================================================================
# LAYOUT CLAUSE
# ============================================================================


class LayoutClause(TypedClause):
    """
    Asserts structure layout matching.

    Ensures consumer-side representation matches IR layout exactly.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        expected_size: int = 0,
        expected_alignment: int = 1,
        field_layout: Optional[Dict[str, int]] = None,
        enforce_padding: bool = True,
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.expected_size = expected_size
        self.expected_alignment = expected_alignment
        self.field_layout = field_layout if field_layout is not None else {}
        self.enforce_padding = enforce_padding

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.LAYOUT

    def validate_parameters(self) -> List[str]:
        """Validate layout clause parameters."""
        errors = []

        # Size must be positive
        if self.expected_size <= 0:
            errors.append(f"expected_size must be positive, got {self.expected_size}")

        # Alignment must be power of 2
        if self.expected_alignment <= 0:
            errors.append("expected_alignment must be positive")
        elif (self.expected_alignment & (self.expected_alignment - 1)) != 0:
            errors.append(f"expected_alignment must be power of 2, got {self.expected_alignment}")

        # Field offsets must be non-negative
        for field_name, offset in self.field_layout.items():
            if offset < 0:
                errors.append(f"Field {field_name} offset must be non-negative, got {offset}")

        # Check for overlapping fields (simplified check)
        offsets = list(self.field_layout.values())
        if len(offsets) != len(set(offsets)):
            errors.append("Duplicate field offsets detected")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [
            ConstraintParameter("expected_size", self.expected_size, "integer"),
            ConstraintParameter("expected_alignment", self.expected_alignment, "integer"),
            ConstraintParameter("field_layout", self.field_layout, "reference"),
            ConstraintParameter("enforce_padding", self.enforce_padding, "boolean"),
        ]

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# SIZE CLAUSE
# ============================================================================


class SizeClause(TypedClause):
    """
    Asserts size expectations for values or memory regions.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        size_kind: str = "exact",
        size_value: Optional[int] = None,
        size_reference: Optional[str] = None,
        multiplier: int = 1,
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.size_kind = size_kind
        self.size_value = size_value
        self.size_reference = size_reference
        self.multiplier = multiplier

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.SIZE

    def validate_parameters(self) -> List[str]:
        """Validate size clause parameters."""
        errors = []

        # size_kind must be valid
        valid_kinds = ["exact", "minimum", "maximum", "relational"]
        if self.size_kind not in valid_kinds:
            errors.append(f"size_kind must be one of {valid_kinds}")

        # For non-relational, size_value is required
        if self.size_kind != "relational":
            if self.size_value is None:
                errors.append(f"size_value required for {self.size_kind} size")
            elif self.size_value < 0:
                errors.append("size_value must be non-negative")

        # For relational, size_reference is required
        if self.size_kind == "relational":
            if not self.size_reference:
                errors.append("size_reference required for relational size")

        # Multiplier must be positive
        if self.multiplier <= 0:
            errors.append("multiplier must be positive")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [
            ConstraintParameter("size_kind", self.size_kind, "string"),
            ConstraintParameter("multiplier", self.multiplier, "integer"),
        ]

        if self.size_value is not None:
            params.append(ConstraintParameter("size_value", self.size_value, "integer"))

        if self.size_reference:
            params.append(ConstraintParameter("size_reference", self.size_reference, "reference"))

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# ALIGNMENT CLAUSE
# ============================================================================


class AlignmentClause(TypedClause):
    """
    Asserts alignment requirements for pointers or values.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        required_alignment: int = 1,
        context: str = "parameter",
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.required_alignment = required_alignment
        self.context = context

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.ALIGNMENT

    def validate_parameters(self) -> List[str]:
        """Validate alignment clause parameters."""
        errors = []

        # Alignment must be power of 2
        if self.required_alignment <= 0:
            errors.append("required_alignment must be positive")
        elif (self.required_alignment & (self.required_alignment - 1)) != 0:
            errors.append("required_alignment must be power of 2")

        # Alignment should be reasonable
        if self.required_alignment > 128:
            errors.append(f"required_alignment {self.required_alignment} exceeds typical maximum")

        # Context must be valid
        valid_contexts = ["parameter", "return", "field"]
        if self.context not in valid_contexts:
            errors.append(f"context must be one of {valid_contexts}")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [
            ConstraintParameter("required_alignment", self.required_alignment, "integer"),
            ConstraintParameter("context", self.context, "string"),
        ]

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# NULLABILITY CLAUSE
# ============================================================================


class NullabilityClause(TypedClause):
    """
    Asserts whether pointer may be null.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        nullable: bool = False,
        conditional: Optional[str] = None,
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.nullable = nullable
        self.conditional = conditional

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.NULLABILITY

    def validate_parameters(self) -> List[str]:
        """Validate nullability clause parameters."""
        errors = []

        # Subject should be pointer (checked at higher level)
        # Conditional must be non-empty if specified
        if self.conditional is not None and not self.conditional:
            errors.append("conditional must be non-empty if specified")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [ConstraintParameter("nullable", self.nullable, "boolean")]

        if self.conditional:
            params.append(ConstraintParameter("conditional", self.conditional, "string"))

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# OWNERSHIP CLAUSE
# ============================================================================


class OwnershipClause(TypedClause):
    """
    Asserts memory management responsibility.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        ownership_mode: str = "caller_owned",
        allocation_responsibility: str = "caller",
        deallocation_responsibility: str = "caller",
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.ownership_mode = ownership_mode
        self.allocation_responsibility = allocation_responsibility
        self.deallocation_responsibility = deallocation_responsibility

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.OWNERSHIP

    def validate_parameters(self) -> List[str]:
        """Validate ownership clause parameters."""
        errors = []

        # Ownership mode must be valid
        valid_modes = ["caller_owned", "callee_owned", "transferred"]
        if self.ownership_mode not in valid_modes:
            errors.append(f"ownership_mode must be one of {valid_modes}")

        # Responsibilities must be valid
        valid_resp = ["caller", "callee", "external", "none"]
        if self.allocation_responsibility not in valid_resp:
            errors.append(f"allocation_responsibility must be one of {valid_resp}")
        if self.deallocation_responsibility not in valid_resp:
            errors.append(f"deallocation_responsibility must be one of {valid_resp}")

        # Check consistency
        if self.ownership_mode == "transferred":
            if self.allocation_responsibility == "none":
                errors.append("transferred ownership requires allocation")
            if self.deallocation_responsibility == "none":
                errors.append("transferred ownership requires deallocation")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [
            ConstraintParameter("ownership_mode", self.ownership_mode, "string"),
            ConstraintParameter(
                "allocation_responsibility", self.allocation_responsibility, "string"
            ),
            ConstraintParameter(
                "deallocation_responsibility", self.deallocation_responsibility, "string"
            ),
        ]

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# LIFETIME CLAUSE
# ============================================================================


class LifetimeClause(TypedClause):
    """
    Asserts how long value remains valid.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        lifetime_scope: str = "call",
        invalidation_event: Optional[str] = None,
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.lifetime_scope = lifetime_scope
        self.invalidation_event = invalidation_event

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.LIFETIME

    def validate_parameters(self) -> List[str]:
        """Validate lifetime clause parameters."""
        errors = []

        # Lifetime scope must be valid
        valid_scopes = ["call", "context", "global"]
        if self.lifetime_scope not in valid_scopes:
            errors.append(f"lifetime_scope must be one of {valid_scopes}")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [ConstraintParameter("lifetime_scope", self.lifetime_scope, "string")]

        if self.invalidation_event:
            params.append(
                ConstraintParameter("invalidation_event", self.invalidation_event, "string")
            )

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# RELATIONAL CLAUSE
# ============================================================================


class RelationalClause(TypedClause):
    """
    Asserts relationships between multiple entities.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        relation_kind: str = "buffer_length",
        primary_reference: str = "",
        secondary_reference: str = "",
        relation_expression: Optional[str] = None,
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.relation_kind = relation_kind
        self.primary_reference = primary_reference
        self.secondary_reference = secondary_reference
        self.relation_expression = relation_expression

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.RELATIONAL

    def validate_parameters(self) -> List[str]:
        """Validate relational clause parameters."""
        errors = []

        # Relation kind must be valid
        valid_kinds = ["buffer_length", "paired_params", "dependent_null"]
        if self.relation_kind not in valid_kinds:
            errors.append(f"relation_kind must be one of {valid_kinds}")

        # Both references required
        if not self.primary_reference:
            errors.append("primary_reference is required")
        if not self.secondary_reference:
            errors.append("secondary_reference is required")

        # References must be different
        if self.primary_reference == self.secondary_reference:
            errors.append("primary and secondary references must be different")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [
            ConstraintParameter("relation_kind", self.relation_kind, "string"),
            ConstraintParameter("primary_reference", self.primary_reference, "reference"),
            ConstraintParameter("secondary_reference", self.secondary_reference, "reference"),
        ]

        if self.relation_expression:
            params.append(
                ConstraintParameter("relation_expression", self.relation_expression, "expression")
            )

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# CALLING CONVENTION CLAUSE
# ============================================================================


class CallingConventionClause(TypedClause):
    """
    Asserts calling convention requirements.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        required_convention: str = "cdecl",
        strict: bool = True,
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.required_convention = required_convention
        self.strict = strict

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.CALLING_CONVENTION

    def validate_parameters(self) -> List[str]:
        """Validate calling convention clause parameters."""
        errors = []

        # Convention must be valid
        valid_conventions = [
            "cdecl",
            "stdcall",
            "fastcall",
            "thiscall",
            "vectorcall",
            "sysv",
            "win64",
        ]
        if self.required_convention not in valid_conventions:
            errors.append(f"required_convention must be one of {valid_conventions}")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [
            ConstraintParameter("required_convention", self.required_convention, "string"),
            ConstraintParameter("strict", self.strict, "boolean"),
        ]

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# ABI COMPATIBILITY CLAUSE
# ============================================================================


class ABICompatibilityClause(TypedClause):
    """
    Asserts ABI version compatibility requirements.
    """

    def __init__(
        self,
        clause_id: str,
        subject_reference: SubjectReference,
        severity: Severity = Severity.ERROR,
        explanation: Optional[str] = None,
        compatible_versions: Optional[List[str]] = None,
        compatibility_mode: str = "strict",
    ):
        super().__init__(clause_id, subject_reference, severity, explanation)
        self.compatible_versions = compatible_versions if compatible_versions is not None else []
        self.compatibility_mode = compatibility_mode

    @property
    def clause_type(self) -> ClauseType:
        return ClauseType.ABI_COMPATIBILITY

    def validate_parameters(self) -> List[str]:
        """Validate ABI compatibility clause parameters."""
        errors = []

        # Must have at least one compatible version
        if not self.compatible_versions:
            errors.append("compatible_versions must be non-empty")

        # Compatibility mode must be valid
        valid_modes = ["strict", "backward", "forward"]
        if self.compatibility_mode not in valid_modes:
            errors.append(f"compatibility_mode must be one of {valid_modes}")

        return errors

    def to_generic_clause(self) -> ContractClause:
        """Convert to generic clause."""
        params = [
            ConstraintParameter("compatible_versions", self.compatible_versions, "reference"),
            ConstraintParameter("compatibility_mode", self.compatibility_mode, "string"),
        ]

        return ContractClause(
            clause_id=self.clause_id,
            clause_type=self.clause_type,
            subject_reference=self.subject_reference,
            constraint_parameters=params,
            severity=self.severity,
            explanation=self.explanation,
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_clause_from_type(
    clause_type: ClauseType, clause_id: str, subject_reference: SubjectReference, **kwargs
) -> TypedClause:
    """
    Factory function to create typed clause from clause type.

    Args:
        clause_type: Type of clause to create
        clause_id: Clause identifier
        subject_reference: Subject reference
        **kwargs: Clause-specific parameters

    Returns:
        Typed clause instance
    """
    clause_map = {
        ClauseType.LAYOUT: LayoutClause,
        ClauseType.SIZE: SizeClause,
        ClauseType.ALIGNMENT: AlignmentClause,
        ClauseType.NULLABILITY: NullabilityClause,
        ClauseType.OWNERSHIP: OwnershipClause,
        ClauseType.LIFETIME: LifetimeClause,
        ClauseType.RELATIONAL: RelationalClause,
        ClauseType.CALLING_CONVENTION: CallingConventionClause,
        ClauseType.ABI_COMPATIBILITY: ABICompatibilityClause,
    }

    clause_class = clause_map.get(clause_type)
    if not clause_class:
        raise ValueError(f"Unsupported clause type: {clause_type}")

    return clause_class(clause_id, subject_reference, **kwargs)


__all__ = [
    "TypedClause",
    "LayoutClause",
    "SizeClause",
    "AlignmentClause",
    "NullabilityClause",
    "OwnershipClause",
    "LifetimeClause",
    "RelationalClause",
    "CallingConventionClause",
    "ABICompatibilityClause",
    "create_clause_from_type",
]
