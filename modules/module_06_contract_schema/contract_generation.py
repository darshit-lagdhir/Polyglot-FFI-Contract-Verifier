"""
Module 06: Contract Schema - Automated Contract Synthesis

This module provides the core logic for automatically generating FFI contracts from
Intermediate Representation (IR) artifacts. It employs a multi-stage pipeline to
infer structural, semantic, and relational constraints using conservative defaults
and heuristic pattern matching.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
import re

from .contract_entities import (
    ContractDocument,
    ContractHeader,
    GenerationMetadata,
    SubjectReference,
    SubjectKind,
    ContractSeverity,
)
Severity = ContractSeverity
from .clause_types import (
    LayoutClause,
    SizeClause,
    AlignmentClause,
    NullabilityClause,
    OwnershipClause,
    LifetimeClause,
    RelationalClause,
    CallingConventionClause,
)


@dataclass
class GenerationConfig:
    """Configuration for the contract generation engine."""

    # Confidence thresholds
    confidence_threshold: float = 0.5
    include_low_confidence: bool = True

    # Clause generation toggles
    generate_layout: bool = True
    generate_size: bool = True
    generate_alignment: bool = True
    generate_nullability: bool = True
    generate_ownership: bool = True
    generate_lifetime: bool = False
    generate_relational: bool = True
    generate_calling_convention: bool = True

    # Naming conventions for heuristic analysis
    nullable_prefixes: List[str] = field(
        default_factory=lambda: ["optional_", "maybe_", "nullable_", "opt_"]
    )
    alloc_prefixes: List[str] = field(
        default_factory=lambda: ["create_", "alloc_", "new_", "make_", "build_"]
    )
    borrow_prefixes: List[str] = field(
        default_factory=lambda: ["get_", "peek_", "view_", "find_", "lookup_"]
    )
    buffer_names: List[str] = field(
        default_factory=lambda: ["buffer", "buf", "data", "ptr", "array", "items"]
    )
    length_names: List[str] = field(
        default_factory=lambda: ["length", "len", "size", "count", "num", "n"]
    )


@dataclass
class GeneratedClause:
    """A single clause generated from IR with associated provenance."""

    clause: any
    confidence: float
    rationale: str
    ir_source: Optional[str] = None


@dataclass
class MockIRType:
    """Mock representation of an IR type for internal logic checks."""

    entity_id: str
    type_name: str
    size_bytes: int
    alignment_bytes: int


@dataclass
class MockIRFunction:
    """Mock representation of an IR function for internal logic checks."""

    entity_id: str
    function_name: str
    parameters: List[Dict[str, any]] = field(default_factory=list)
    return_type: Optional[str] = None
    calling_convention: str = "cdecl"


class NamingPatternMatcher:
    """Analyzes identifier naming patterns to infer semantic intent."""

    def __init__(self, config: GenerationConfig):
        self.config = config

    def is_nullable_name(self, name: str) -> bool:
        """Determines if a name suggests the entity might be null."""
        lower_name = name.lower()
        return any(lower_name.startswith(p) for p in self.config.nullable_prefixes)

    def is_allocation_function(self, name: str) -> bool:
        """Determines if a function name suggests it returns a new allocation."""
        lower_name = name.lower()
        return any(lower_name.startswith(p) for p in self.config.alloc_prefixes)

    def is_borrow_function(self, name: str) -> bool:
        """Determines if a function name suggests it returns a borrowed reference."""
        lower_name = name.lower()
        return any(lower_name.startswith(p) for p in self.config.borrow_prefixes)

    def find_buffer_length_pair(
        self, parameters: List[Dict[str, any]]
    ) -> Optional[Tuple[str, str]]:
        for i, param in enumerate(parameters):
            name = param.get("name", "").lower()
            is_buf = any(b in name for b in self.config.buffer_names)
            is_ptr = param.get("is_pointer", False)

            if is_buf and is_ptr:
                for j, other in enumerate(parameters):
                    if i == j:
                        continue
                    o_name = other.get("name", "").lower()
                    is_len = any(l in o_name for l in self.config.length_names)
                    is_int = other.get("is_integer", False)
                    if is_len and is_int:
                        return (param["name"], other["name"])
        return None


class LayoutClauseGenerator:
    """Derives layout requirements from structural IR definitions."""

    def generate(self, ir_type: MockIRType) -> Optional[GeneratedClause]:
        ref = SubjectReference(SubjectKind.STRUCTURE, ir_type.entity_id)
        clause = LayoutClause(
            clause_id=f"layout_{ir_type.type_name}",
            subject_reference=ref,
            expected_size=ir_type.size_bytes,
            expected_alignment=ir_type.alignment_bytes,
            field_layout={},
            severity=ContractSeverity.ERROR,
            explanation=f"Memory layout for {ir_type.type_name} must match specifications.",
        )
        return GeneratedClause(clause, 1.0, "Derived from structural IR truth", ir_type.entity_id)


class NullabilityClauseGenerator:
    """Infers pointer nullability requirements."""

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.matcher = NamingPatternMatcher(config)

    def generate_for_parameter(
        self, func_name: str, p_name: str, p_id: str
    ) -> Optional[GeneratedClause]:
        nullable = self.matcher.is_nullable_name(p_name)
        ref = SubjectReference(SubjectKind.PARAMETER, p_id)
        clause = NullabilityClause(
            clause_id=f"null_{func_name}_{p_name}",
            subject_reference=ref,
            nullable=nullable,
            severity=ContractSeverity.ERROR if not nullable else ContractSeverity.WARNING,
            explanation=f"Parameter '{p_name}' {'is optional' if nullable else 'must not be null'}.",
        )
        conf = 0.8 if nullable else 0.6
        reason = "Inferred from naming hint" if nullable else "Conservative non-null default"
        return GeneratedClause(clause, conf, reason, p_id)


class OwnershipClauseGenerator:
    """Infers memory ownership and lifecycle responsibilities."""

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.matcher = NamingPatternMatcher(config)

    def generate_for_return(self, function: MockIRFunction) -> Optional[GeneratedClause]:
        if not function.return_type:
            return None
        is_alloc = self.matcher.is_allocation_function(function.function_name)
        is_borrow = self.matcher.is_borrow_function(function.function_name)

        mode = "transferred" if is_alloc else ("callee_owned" if is_borrow else "transferred")
        a_resp = "callee"
        d_resp = "caller" if mode == "transferred" else "callee"

        ref = SubjectReference(SubjectKind.RETURN_VALUE, function.entity_id)
        clause = OwnershipClause(
            clause_id=f"own_{function.function_name}_return",
            subject_reference=ref,
            ownership_mode=mode,
            allocation_responsibility=a_resp,
            deallocation_responsibility=d_resp,
            severity=ContractSeverity.ERROR,
            explanation=f"Return value ownership is {mode}.",
        )
        conf = 0.8 if is_alloc else (0.7 if is_borrow else 0.5)
        return GeneratedClause(clause, conf, "Inferred from naming pattern", function.entity_id)


class RelationalClauseGenerator:
    """Infers relationships between parameters, such as buffer sizes."""

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.matcher = NamingPatternMatcher(config)

    def generate_for_function(self, function: MockIRFunction) -> Optional[GeneratedClause]:
        pair = self.matcher.find_buffer_length_pair(function.parameters)
        if not pair:
            return None
        ref = SubjectReference(SubjectKind.FUNCTION, function.entity_id)
        clause = RelationalClause(
            clause_id=f"rel_{function.function_name}_{pair[0]}_{pair[1]}",
            subject_reference=ref,
            relation_kind="buffer_length",
            primary_reference=pair[0],
            secondary_reference=pair[1],
            severity=ContractSeverity.ERROR,
            explanation=f"Buffer '{pair[0]}' capacity is controlled by '{pair[1]}'.",
        )
        return GeneratedClause(
            clause, 0.75, "Detected buffer-length naming pattern", function.entity_id
        )


class ContractGenerator:
    """
    Generate contracts from IR artifacts.

    The ContractGenerator analyzes IR artifacts and produces contracts with
    conservative default constraints. Clauses are generated based on structural
    information and naming heuristics.

    Attributes:
        config (GenerationConfig): Active configuration
        layout_gen (LayoutClauseGenerator): Layout clause generator
        nullability_gen (NullabilityClauseGenerator): Nullability generator

    Example:
        >>> generator = ContractGenerator()
        >>> contract = generator.generate(ir_artifact, "my_interface")
        >>> print(f"Generated {len(contract.clauses)} clauses")
    """

    def __init__(self, config: Optional[GenerationConfig] = None):
        self.config = config or GenerationConfig()
        self.layout_gen = LayoutClauseGenerator()
        self.nullability_gen = NullabilityClauseGenerator(self.config)
        self.ownership_gen = OwnershipClauseGenerator(self.config)
        self.relational_gen = RelationalClauseGenerator(self.config)

    def generate(self, ir_artifact: any, target_interface_id: str) -> ContractDocument:
        header = ContractHeader(
            contract_version="1.0.0",
            target_interface_id=target_interface_id,
            generation_metadata=GenerationMetadata(generation_mode="auto"),
        )
        contract = ContractDocument(header=header)

        # Prototype: Example generation for a mock type
        mock_t = MockIRType("struct_Point", "Point", 8, 4)
        if self.config.generate_layout:
            res = self.layout_gen.generate(mock_t)
            if res and res.confidence >= self.config.confidence_threshold:
                contract.add_clause(res.clause.to_generic_clause())

        return contract

    def generate_summary(self, generated_clauses: List[GeneratedClause]) -> str:
        """Produces a metrics-focused summary of the synthesis process."""
        total = len(generated_clauses)
        high = sum(1 for c in generated_clauses if c.confidence >= 0.8)
        med = sum(1 for c in generated_clauses if 0.5 <= c.confidence < 0.8)
        low = sum(1 for c in generated_clauses if c.confidence < 0.5)

        lines = [
            "Contract Synthesis Summary",
            "=" * 30,
            f"Total Clauses: {total}",
            f"  High Confidence:   {high}",
            f"  Medium Confidence: {med}",
            f"  Low Confidence:    {low}",
            "",
        ]
        return "\n".join(lines)


__all__ = [
    "GenerationConfig",
    "GeneratedClause",
    "NamingPatternMatcher",
    "LayoutClauseGenerator",
    "NullabilityClauseGenerator",
    "OwnershipClauseGenerator",
    "RelationalClauseGenerator",
    "ContractGenerator",
    "MockIRType",
    "MockIRFunction",
]
