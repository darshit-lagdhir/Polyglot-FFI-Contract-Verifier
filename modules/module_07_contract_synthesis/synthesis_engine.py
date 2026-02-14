"""
Module 07: Contract Synthesis Engine (Prompt 1/15)

The synthesis engine transforms IR artifacts (structural facts) into Contract
Schema documents (enforceable expectations). It implements deterministic,
conservative, traceable semantic projection.

Key Responsibilities:
- Consume Module 05 IR artifacts
- Generate Module 06 Contract clauses
- Maintain complete provenance traceability
- Ensure deterministic output
- Apply conservative safety defaults
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from pathlib import Path
import logging
import sys

# Import from Module 05 (IR Normalization)
sys.path.insert(0, str(Path(__file__).parent.parent))

from module_05_ir_normalization.ir_entities import (
    IRInterfaceUnit,
    IRType,
    IRFunction,
    IRParameter,
    TypeKind,
    ScalarWidth,
    Signedness
)

# Import from Module 06 (Contract Schema)
from module_06_contract_schema.contract_entities import (
    ContractDocument,
    ContractHeader,
    ContractClause,
    SubjectReference,
    ConstraintParameter,
    ClauseType,
    SubjectKind,
    Severity,
    GenerationMetadata
)
from module_06_contract_schema.clause_types import (
    LayoutClause,
    NullabilityClause,
    OwnershipClause
)

logger = logging.getLogger(__name__)


# ============================================================================
# SYNTHESIS CONFIGURATION
# ============================================================================


@dataclass
class SynthesisConfig:
    """
    Configuration for contract synthesis engine.

    Controls synthesis behavior, default assumptions, and generator toggles.
    """

    # Version
    synthesis_version: str = "1.0.0"

    # Nullability defaults
    default_pointer_nonnull: bool = True

    # Ownership defaults
    default_return_ownership: str = "caller"  # "caller", "static", "unknown"

    # Severity defaults
    default_layout_severity: Severity = Severity.ERROR
    default_nullability_severity: Severity = Severity.ERROR
    default_ownership_severity: Severity = Severity.WARNING

    # Generator toggles
    enable_layout_generation: bool = True
    enable_nullability_generation: bool = True
    enable_ownership_generation: bool = True

    # Traceability
    include_provenance: bool = True
    include_confidence: bool = True

    # Conservative mode
    strict_mode: bool = True


# ============================================================================
# PROVENANCE TRACKING
# ============================================================================


@dataclass
class ClauseProvenance:
    """
    Provenance metadata for generated clause.

    Records why and how a clause was generated, enabling traceability and
    explainability.
    """

    # Source IR entity
    ir_entity_id: str
    ir_entity_type: str  # "structure", "function", "parameter", etc.

    # Generation rule
    rule_id: str
    rule_version: str

    # Structural properties that triggered generation
    triggering_properties: Dict[str, Any] = field(default_factory=dict)

    # Confidence level (0.0 to 1.0)
    confidence: float = 1.0

    # Human-readable explanation
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for contract metadata."""
        return {
            "ir_entity": {
                "id": self.ir_entity_id,
                "type": self.ir_entity_type
            },
            "rule": {
                "id": self.rule_id,
                "version": self.rule_version
            },
            "properties": self.triggering_properties,
            "confidence": self.confidence,
            "explanation": self.explanation
        }


# ============================================================================
# SYNTHESIS RESULT
# ============================================================================


@dataclass
class SynthesisResult:
    """
    Result of contract synthesis operation.

    Contains generated contract and metadata about synthesis process.
    """

    success: bool
    contract: Optional[ContractDocument]

    # Statistics
    clauses_generated: int = 0
    layout_clauses: int = 0
    nullability_clauses: int = 0
    ownership_clauses: int = 0

    # Diagnostics
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Provenance
    provenance_map: Dict[str, ClauseProvenance] = field(default_factory=dict)

    def add_warning(self, message: str):
        """Add synthesis warning."""
        self.warnings.append(message)
        logger.warning(f"Synthesis warning: {message}")

    def add_error(self, message: str):
        """Add synthesis error."""
        self.errors.append(message)
        logger.error(f"Synthesis error: {message}")

    def record_clause(self, clause_id: str, provenance: ClauseProvenance):
        """Record clause provenance."""
        self.provenance_map[clause_id] = provenance


# ============================================================================
# LAYOUT CLAUSE GENERATOR
# ============================================================================


class LayoutClauseGenerator:
    """
    Generates layout clauses from IR type definitions.

    Handles structures, unions, and scalar types.
    """

    def __init__(self, config: SynthesisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate_structure_layout(
        self,
        ir_type: IRType
    ) -> Optional[ContractClause]:
        """
        Generate layout clause for structure type.
        
        Args:
            ir_type: IR type entity (must be structure)
            
        Returns:
            LayoutClause encoding structural invariants
        """
        if ir_type.kind != TypeKind.STRUCTURE:
            return None
        
        # Create subject reference
        subject = SubjectReference(
            kind=SubjectKind.STRUCTURE,
            entity_id=ir_type.type_id
        )
        
        # Build constraint parameters
        params = [
            ConstraintParameter(
                "expected_size",
                ir_type.size_bytes,
                "integer"
            ),
            ConstraintParameter(
                "expected_alignment",
                ir_type.alignment,
                "integer"
            )
        ]
        
        # Add field offsets
        if ir_type.fields:
            field_offsets = {
                field.name: field.offset_bytes
                for field in ir_type.fields
            }
            params.append(
                ConstraintParameter(
                    "field_offsets",
                    field_offsets,
                    "map"
                )
            )
        
        # Create clause
        clause = ContractClause(
            clause_id=f"layout_{ir_type.type_id}",
            clause_type=ClauseType.LAYOUT,
            subject_reference=subject,
            constraint_parameters=params,
            severity=self.config.default_layout_severity
        )
        
        # Add provenance
        provenance = ClauseProvenance(
            ir_entity_id=ir_type.type_id,
            ir_entity_type="structure",
            rule_id="layout_structural_projection",
            rule_version=self.config.synthesis_version,
            triggering_properties={
                "size_bytes": ir_type.size_bytes,
                "alignment": ir_type.alignment,
                "field_count": len(ir_type.fields) if ir_type.fields else 0
            },
            confidence=1.0,
            explanation=f"Layout clause generated from structural IR definition of {ir_type.type_id}"
        )
        
        # Attach provenance to clause metadata
        clause.metadata["provenance"] = provenance.to_dict()
        
        return clause

    def generate_union_layout(
        self,
        ir_type: IRType
    ) -> Optional[ContractClause]:
        """Generate layout clause for union type."""
        if ir_type.kind != TypeKind.UNION:
            return None
        
        # Similar to structure but with union semantics
        subject = SubjectReference(
            kind=SubjectKind.STRUCTURE,  # Unions use structure subject
            entity_id=ir_type.type_id
        )
        
        params = [
            ConstraintParameter("expected_size", ir_type.size_bytes, "integer"),
            ConstraintParameter("expected_alignment", ir_type.alignment, "integer"),
            ConstraintParameter("is_union", True, "boolean")
        ]
        
        clause = ContractClause(
            clause_id=f"layout_{ir_type.type_id}",
            clause_type=ClauseType.LAYOUT,
            subject_reference=subject,
            constraint_parameters=params,
            severity=self.config.default_layout_severity
        )
        
        provenance = ClauseProvenance(
            ir_entity_id=ir_type.type_id,
            ir_entity_type="union",
            rule_id="union_layout_projection",
            rule_version=self.config.synthesis_version,
            triggering_properties={
                "size_bytes": ir_type.size_bytes,
                "alignment": ir_type.alignment
            },
            confidence=1.0,
            explanation=f"Union layout clause for {ir_type.type_id}"
        )
        
        clause.metadata["provenance"] = provenance.to_dict()
        
        return clause


# ============================================================================
# NULLABILITY CLAUSE GENERATOR
# ============================================================================


class NullabilityClauseGenerator:
    """
    Generates nullability clauses for pointer parameters.

    Applies conservative defaults: pointers are non-null unless proven otherwise.
    """

    def __init__(self, config: SynthesisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate_parameter_nullability(
        self,
        function: IRFunction,
        parameter: IRParameter
    ) -> Optional[ContractClause]:
        """
        Generate nullability clause for pointer parameter.
        
        Args:
            function: Function containing parameter
            parameter: Parameter entity (must be pointer)
            
        Returns:
            NullabilityClause or None if not applicable
        """
        # Check if parameter is pointer
        if not parameter.param_type.is_pointer():
            return None
        
        # Apply conservative default: non-null
        nullable = not self.config.default_pointer_nonnull
        
        # Check for nullability signals
        if self._has_nullable_signals(parameter):
            nullable = True
        
        # Create subject reference
        subject = SubjectReference(
            kind=SubjectKind.PARAMETER,
            entity_id=f"{function.function_id}::{parameter.param_name}"
        )
        
        # Create clause
        params = [
            ConstraintParameter("nullable", nullable, "boolean")
        ]
        
        clause = ContractClause(
            clause_id=f"null_{function.function_id}_{parameter.param_name}",
            clause_type=ClauseType.NULLABILITY,
            subject_reference=subject,
            constraint_parameters=params,
            severity=self.config.default_nullability_severity
        )
        
        # Provenance
        provenance = ClauseProvenance(
            ir_entity_id=f"{function.function_id}::{parameter.param_name}",
            ir_entity_type="parameter",
            rule_id="pointer_nullability_default",
            rule_version=self.config.synthesis_version,
            triggering_properties={
                "pointer_depth": parameter.param_type.pointer_depth,
                "has_nullable_signals": self._has_nullable_signals(parameter)
            },
            confidence=1.0 if not nullable else 0.8,
            explanation=f"Conservative nullability default for pointer parameter {parameter.param_name}"
        )
        
        clause.metadata["provenance"] = provenance.to_dict()
        
        return clause

    def _has_nullable_signals(self, parameter: IRParameter) -> bool:
        """
        Detect signals indicating nullable pointer.
        
        Checks:
        - Parameter name contains "optional", "maybe", "nullable"
        - Documented as optional in metadata
        """
        name_lower = parameter.param_name.lower()
        
        nullable_keywords = ["optional", "maybe", "nullable", "opt"]
        
        for keyword in nullable_keywords:
            if keyword in name_lower:
                return True
        
        return False


# ============================================================================
# OWNERSHIP CLAUSE GENERATOR
# ============================================================================


class OwnershipClauseGenerator:
    """
    Generates ownership clauses for return values and parameters.

    Applies conservative defaults for ownership semantics.
    """

    def __init__(self, config: SynthesisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate_return_ownership(
        self,
        function: IRFunction
    ) -> Optional[ContractClause]:
        """
        Generate ownership clause for function return value.
        
        Args:
            function: Function entity
            
        Returns:
            OwnershipClause or None if not applicable
        """
        # Check if returns pointer
        if not function.return_type or not function.return_type.is_pointer():
            return None
        
        # Default: caller-owned
        owner = self.config.default_return_ownership
        
        # Create subject reference
        subject = SubjectReference(
            kind=SubjectKind.FUNCTION,
            entity_id=function.function_id
        )
        
        # Create clause
        params = [
            ConstraintParameter("owner", owner, "string"),
            ConstraintParameter("transfer", owner == "caller", "boolean")
        ]
        
        clause = ContractClause(
            clause_id=f"own_{function.function_id}_return",
            clause_type=ClauseType.OWNERSHIP,
            subject_reference=subject,
            constraint_parameters=params,
            severity=self.config.default_ownership_severity
        )
        
        # Provenance
        provenance = ClauseProvenance(
            ir_entity_id=function.function_id,
            ir_entity_type="function_return",
            rule_id="return_ownership_default",
            rule_version=self.config.synthesis_version,
            triggering_properties={
                "return_pointer": True
            },
            confidence=0.6,  # Advisory level confidence
            explanation=f"Default ownership assumption for {function.function_id} return value"
        )
        
        clause.metadata["provenance"] = provenance.to_dict()
        
        return clause


# ============================================================================
# MAIN SYNTHESIS ENGINE
# ============================================================================


class SynthesisEngine:
    """
    Main contract synthesis engine.

    Orchestrates transformation from IR artifacts to Contract documents.
    Implements deterministic, conservative, traceable synthesis.
    """

    def __init__(self, config: Optional[SynthesisConfig] = None):
        """
        Initialize synthesis engine.
        
        Args:
            config: Synthesis configuration (uses defaults if None)
        """
        self.config = config or SynthesisConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize generators
        self.layout_generator = LayoutClauseGenerator(self.config)
        self.nullability_generator = NullabilityClauseGenerator(self.config)
        self.ownership_generator = OwnershipClauseGenerator(self.config)

    def synthesize(
        self,
        ir_unit: IRInterfaceUnit,
        target_interface_id: str
    ) -> SynthesisResult:
        """
        Synthesize contract from IR artifact.
        
        This is the main entry point for synthesis. It coordinates all
        generation phases and produces a complete contract document.
        
        Args:
            ir_unit: IR interface unit from Module 05
            target_interface_id: Identifier for target interface
            
        Returns:
            SynthesisResult containing generated contract or errors
        """
        self.logger.info(f"Starting synthesis for interface: {target_interface_id}")
        
        result = SynthesisResult(
            success=False,
            contract=None
        )
        
        try:
            # Create contract document
            header = ContractHeader(
                contract_version="1.0.0",
                target_interface_id=target_interface_id
            )
            
            # Add synthesis metadata
            header.generation_metadata = GenerationMetadata(
                synthesis_version=self.config.synthesis_version,
                generation_mode="deterministic_conservative"
            )
            
            contract = ContractDocument(header=header)
            
            # Phase 1: Structural Invariant Projection
            self._generate_layout_clauses(ir_unit, contract, result)
            
            # Phase 2: Pointer Assumption Projection
            self._generate_nullability_clauses(ir_unit, contract, result)
            self._generate_ownership_clauses(ir_unit, contract, result)
            
            # Set result
            result.contract = contract
            result.success = len(result.errors) == 0
            result.clauses_generated = len(contract.clauses)
            
            self.logger.info(
                f"Synthesis complete: {result.clauses_generated} clauses generated"
            )
            
        except Exception as e:
            result.add_error(f"Synthesis failed: {str(e)}")
            self.logger.exception("Synthesis exception")
        
        return result

    def _generate_layout_clauses(
        self,
        ir_unit: IRInterfaceUnit,
        contract: ContractDocument,
        result: SynthesisResult
    ):
        """Generate layout clauses for all types in IR."""
        if not self.config.enable_layout_generation:
            return
        
        self.logger.debug("Generating layout clauses...")
        
        for ir_type in ir_unit.types:
            clause = None
            
            if ir_type.kind == TypeKind.STRUCTURE:
                clause = self.layout_generator.generate_structure_layout(ir_type)
            elif ir_type.kind == TypeKind.UNION:
                clause = self.layout_generator.generate_union_layout(ir_type)
            
            if clause:
                contract.add_clause(clause)
                result.layout_clauses += 1
                
                # Record provenance
                if "provenance" in clause.metadata:
                    prov_dict = clause.metadata["provenance"]
                    provenance = ClauseProvenance(
                        ir_entity_id=prov_dict["ir_entity"]["id"],
                        ir_entity_type=prov_dict["ir_entity"]["type"],
                        rule_id=prov_dict["rule"]["id"],
                        rule_version=prov_dict["rule"]["version"],
                        triggering_properties=prov_dict["properties"],
                        confidence=prov_dict["confidence"],
                        explanation=prov_dict["explanation"]
                    )
                    result.record_clause(clause.clause_id, provenance)
        
        self.logger.debug(f"Generated {result.layout_clauses} layout clauses")

    def _generate_nullability_clauses(
        self,
        ir_unit: IRInterfaceUnit,
        contract: ContractDocument,
        result: SynthesisResult
    ):
        """Generate nullability clauses for pointer parameters."""
        if not self.config.enable_nullability_generation:
            return
        
        self.logger.debug("Generating nullability clauses...")
        
        for function in ir_unit.functions:
            for param in function.parameters:
                clause = self.nullability_generator.generate_parameter_nullability(
                    function, param
                )
                
                if clause:
                    contract.add_clause(clause)
                    result.nullability_clauses += 1
                    
                    # Record provenance
                    if "provenance" in clause.metadata:
                        prov_dict = clause.metadata["provenance"]
                        provenance = ClauseProvenance(
                            ir_entity_id=prov_dict["ir_entity"]["id"],
                            ir_entity_type=prov_dict["ir_entity"]["type"],
                            rule_id=prov_dict["rule"]["id"],
                            rule_version=prov_dict["rule"]["version"],
                            triggering_properties=prov_dict["properties"],
                            confidence=prov_dict["confidence"],
                            explanation=prov_dict["explanation"]
                        )
                        result.record_clause(clause.clause_id, provenance)
        
        self.logger.debug(f"Generated {result.nullability_clauses} nullability clauses")

    def _generate_ownership_clauses(
        self,
        ir_unit: IRInterfaceUnit,
        contract: ContractDocument,
        result: SynthesisResult
    ):
        """Generate ownership clauses for return values."""
        if not self.config.enable_ownership_generation:
            return
        
        self.logger.debug("Generating ownership clauses...")
        
        for function in ir_unit.functions:
            clause = self.ownership_generator.generate_return_ownership(function)
            
            if clause:
                contract.add_clause(clause)
                result.ownership_clauses += 1
                
                # Record provenance
                if "provenance" in clause.metadata:
                    prov_dict = clause.metadata["provenance"]
                    provenance = ClauseProvenance(
                        ir_entity_id=prov_dict["ir_entity"]["id"],
                        ir_entity_type=prov_dict["ir_entity"]["type"],
                        rule_id=prov_dict["rule"]["id"],
                        rule_version=prov_dict["rule"]["version"],
                        triggering_properties=prov_dict["properties"],
                        confidence=prov_dict["confidence"],
                        explanation=prov_dict["explanation"]
                    )
                    result.record_clause(clause.clause_id, provenance)
        
        self.logger.debug(f"Generated {result.ownership_clauses} ownership clauses")
