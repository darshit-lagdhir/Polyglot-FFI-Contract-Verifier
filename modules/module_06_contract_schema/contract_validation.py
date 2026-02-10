"""
Module 06: Contract Schema - Validation Framework

Three-layer validation framework for contracts:
1. Schema validation (structural correctness)
2. Referential validation (IR entity resolution)
3. Constraint validation (semantic correctness)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum

from .contract_entities import (
    ContractDocument,
    ContractClause,
    SubjectReference,
    ConstraintParameter,
    ClauseType,
    SubjectKind
)

# ============================================================================
# VALIDATION RESULT TYPES
# ============================================================================

class ValidationLayer(Enum):
    """Validation layer identifier."""
    SCHEMA = "schema"
    REFERENTIAL = "referential"
    CONSTRAINT = "constraint"

@dataclass
class ValidationError:
    """Single validation error."""
    
    error_code: str
    error_message: str
    layer: ValidationLayer
    clause_id: Optional[str] = None
    location: Optional[str] = None
    remediation: Optional[str] = None
    
    def __str__(self) -> str:
        """Human-readable error format."""
        parts = [f"ERROR [{self.layer.value}]: {self.error_message}"]
        
        if self.clause_id:
            parts.append(f"  Clause: {self.clause_id}")
        if self.location:
            parts.append(f"  Location: {self.location}")
        if self.remediation:
            parts.append(f"  Fix: {self.remediation}")
        
        return "\n".join(parts)

@dataclass
class ValidationWarning:
    """Non-fatal validation issue."""
    
    warning_code: str
    warning_message: str
    layer: ValidationLayer
    clause_id: Optional[str] = None
    
    def __str__(self) -> str:
        """Human-readable warning format."""
        parts = [f"WARNING [{self.layer.value}]: {self.warning_message}"]
        if self.clause_id:
            parts.append(f"  Clause: {self.clause_id}")
        return "\n".join(parts)

@dataclass
class ValidationResult:
    """Result of validation layer."""
    
    layer: ValidationLayer
    passed: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    
    def has_errors(self) -> bool:
        """Check if errors present."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if warnings present."""
        return len(self.warnings) > 0
    
    def add_error(
        self,
        code: str,
        message: str,
        clause_id: Optional[str] = None,
        location: Optional[str] = None,
        remediation: Optional[str] = None
    ):
        """Add validation error."""
        error = ValidationError(
            error_code=code,
            error_message=message,
            layer=self.layer,
            clause_id=clause_id,
            location=location,
            remediation=remediation
        )
        self.errors.append(error)
        self.passed = False
    
    def add_warning(
        self,
        code: str,
        message: str,
        clause_id: Optional[str] = None
    ):
        """Add validation warning."""
        warning = ValidationWarning(
            warning_code=code,
            warning_message=message,
            layer=self.layer,
            clause_id=clause_id
        )
        self.warnings.append(warning)

@dataclass
class CompleteValidationResult:
    """Complete validation result across all layers."""
    
    schema_result: Optional[ValidationResult] = None
    referential_result: Optional[ValidationResult] = None
    constraint_result: Optional[ValidationResult] = None
    
    @property
    def passed(self) -> bool:
        """Check if all layers passed."""
        results = [
            self.schema_result,
            self.referential_result,
            self.constraint_result
        ]
        return all(r and r.passed for r in results if r is not None)
    
    def get_all_errors(self) -> List[ValidationError]:
        """Get all errors from all layers."""
        errors = []
        for result in [self.schema_result, self.referential_result, self.constraint_result]:
            if result:
                errors.extend(result.errors)
        return errors
    
    def get_all_warnings(self) -> List[ValidationWarning]:
        """Get all warnings from all layers."""
        warnings = []
        for result in [self.schema_result, self.referential_result, self.constraint_result]:
            if result:
                warnings.extend(result.warnings)
        return warnings
    
    def generate_report(self) -> str:
        """Generate human-readable validation report."""
        lines = ["Contract Validation Report", "=" * 80, ""]
        
        # Overall status
        if self.passed:
            lines.append("✓ All validation layers PASSED")
        else:
            lines.append("✗ Validation FAILED")
        
        lines.append("")
        
        # Schema layer
        if self.schema_result:
            lines.append(f"Schema Validation: {'PASS' if self.schema_result.passed else 'FAIL'}")
            for error in self.schema_result.errors:
                lines.append(f"  {error}")
        
        # Referential layer
        if self.referential_result:
            lines.append(f"Referential Validation: {'PASS' if self.referential_result.passed else 'FAIL'}")
            for error in self.referential_result.errors:
                lines.append(f"  {error}")
        
        # Constraint layer
        if self.constraint_result:
            lines.append(f"Constraint Validation: {'PASS' if self.constraint_result.passed else 'FAIL'}")
            for error in self.constraint_result.errors:
                lines.append(f"  {error}")
        
        # Warnings
        all_warnings = self.get_all_warnings()
        if all_warnings:
            lines.append(f"\nWarnings ({len(all_warnings)}):")
            for warning in all_warnings:
                lines.append(f"  {warning}")
        
        return "\n".join(lines)

# ============================================================================
# VALIDATION CONTEXT
# ============================================================================

@dataclass
class ValidationContext:
    """
    Context for contract validation.
    
    Provides IR artifact and configuration for validation.
    """
    
    # IR artifact for referential validation
    ir_artifact: Optional[Any] = None
    
    # Entity index for fast lookups
    entity_index: Dict[str, Any] = field(default_factory=dict)
    
    # Validation configuration
    strict_mode: bool = True
    treat_warnings_as_errors: bool = False
    
    # Platform information
    target_platform: Optional[str] = None
    
    def build_entity_index(self):
        """Build entity index from IR artifact for fast lookups."""
        if not self.ir_artifact or not hasattr(self.ir_artifact, 'interface_unit'):
            return
        
        interface_unit = self.ir_artifact.interface_unit
        if not interface_unit:
            return
        
        # Index types
        for type_entity in getattr(interface_unit, 'types', []):
            if hasattr(type_entity, 'entity_id'):
                self.entity_index[type_entity.entity_id] = type_entity
        
        # Index symbols
        for symbol in getattr(interface_unit, 'symbols', []):
            if hasattr(symbol, 'entity_id'):
                self.entity_index[symbol.entity_id] = symbol

# ============================================================================
# SCHEMA VALIDATOR
# ============================================================================

class SchemaValidator:
    """
    Layer 1: Schema Validation.
    
    Validates structural conformance to contract schema.
    """
    
    def validate(self, contract: ContractDocument) -> ValidationResult:
        """
        Validate contract schema.
        
        Args:
            contract: Contract document to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult(
            layer=ValidationLayer.SCHEMA,
            passed=True
        )
        
        # Validate header
        self._validate_header(contract.header, result)
        
        # Validate clause structure
        self._validate_clause_structure(contract.clauses, result)
        
        # Check for duplicate clause IDs
        self._check_duplicate_clause_ids(contract.clauses, result)
        
        return result
    
    def _validate_header(self, header, result: ValidationResult):
        """Validate contract header."""
        header_errors = header.validate()
        
        for error in header_errors:
            result.add_error(
                code="E_SCHEMA_001",
                message=f"Header validation failed: {error}",
                location="contract_header",
                remediation="Fix header field values"
            )
    
    def _validate_clause_structure(self, clauses: List[ContractClause], result: ValidationResult):
        """Validate clause structure."""
        for clause in clauses:
            # Validate clause structure
            clause_errors = clause.validate_structure()
            
            for error in clause_errors:
                result.add_error(
                    code="E_SCHEMA_002",
                    message=f"Clause structure invalid: {error}",
                    clause_id=clause.clause_id,
                    remediation="Check clause required fields"
                )
    
    def _check_duplicate_clause_ids(self, clauses: List[ContractClause], result: ValidationResult):
        """Check for duplicate clause IDs."""
        seen_ids: Set[str] = set()
        
        for clause in clauses:
            if clause.clause_id in seen_ids:
                result.add_error(
                    code="E_SCHEMA_003",
                    message=f"Duplicate clause ID: {clause.clause_id}",
                    clause_id=clause.clause_id,
                    remediation="Ensure all clause IDs are unique"
                )
            seen_ids.add(clause.clause_id)

# ============================================================================
# REFERENTIAL VALIDATOR
# ============================================================================

class ReferentialValidator:
    """
    Layer 2: Referential Validation.
    
    Validates all subject references resolve to IR entities.
    """
    
    def __init__(self, context: ValidationContext):
        self.context = context
    
    def validate(self, contract: ContractDocument) -> ValidationResult:
        """
        Validate contract references.
        
        Args:
            contract: Contract document to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult(
            layer=ValidationLayer.REFERENTIAL,
            passed=True
        )
        
        if not self.context.ir_artifact:
            result.add_error(
                code="E_REF_001",
                message="IR artifact not provided for referential validation",
                remediation="Load target IR artifact before validation"
            )
            return result
        
        # Build entity index if not already built
        if not self.context.entity_index:
            self.context.build_entity_index()
        
        # Validate each clause reference
        for clause in contract.clauses:
            self._validate_clause_reference(clause, result)
        
        return result
    
    def _validate_clause_reference(self, clause: ContractClause, result: ValidationResult):
        """Validate clause subject reference."""
        ref = clause.subject_reference
        
        # Check entity exists
        if ref.entity_id not in self.context.entity_index:
            result.add_error(
                code="E_REF_002",
                message=f"Subject reference cannot be resolved: {ref.entity_id}",
                clause_id=clause.clause_id,
                location=str(ref),
                remediation="Verify entity exists in IR artifact"
            )
            return
        
        entity = self.context.entity_index[ref.entity_id]
        
        # Validate entity kind matches (simplified check)
        # In real implementation, would check entity type matches subject_kind
        
        # For nested references (parameters, fields), validate parent
        if ref.parent_id:
            if ref.parent_id not in self.context.entity_index:
                result.add_error(
                    code="E_REF_003",
                    message=f"Parent entity not found: {ref.parent_id}",
                    clause_id=clause.clause_id,
                    remediation="Verify parent entity exists"
                )

# ============================================================================
# ============================================================================

class ConstraintValidator:
    """
    Layer 3: Constraint Validation.
    
    Validates constraint parameters are semantically meaningful.
    """
    
    def __init__(self, context: ValidationContext):
        self.context = context
    
    def validate(self, contract: ContractDocument) -> ValidationResult:
        """
        Validate contract constraints.
        
        Args:
            contract: Contract document to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult(
            layer=ValidationLayer.CONSTRAINT,
            passed=True
        )
        
        # Validate individual clause parameters
        for clause in contract.clauses:
            self._validate_clause_parameters(clause, result)
        
        # Check cross-clause consistency
        self._validate_cross_clause_consistency(contract.clauses, result)
        
        return result
    
    def _validate_clause_parameters(self, clause: ContractClause, result: ValidationResult):
        """Validate clause-specific parameters."""
        # Get parameter validation from clause type
                
        # For each parameter, validate type and range
        for param in clause.constraint_parameters:
            param_errors = param.validate()
            
            for error in param_errors:
                result.add_error(
                    code="E_CONST_001",
                    message=f"Parameter validation failed: {error}",
                    clause_id=clause.clause_id,
                    location=param.name
                )
    
    def _validate_cross_clause_consistency(self, clauses: List[ContractClause], result: ValidationResult):
        """Validate clauses don't contradict each other."""
        # Group clauses by subject
        clauses_by_subject: Dict[str, List[ContractClause]] = {}
        
        for clause in clauses:
            subject_key = clause.subject_reference.entity_id
            if subject_key not in clauses_by_subject:
                clauses_by_subject[subject_key] = []
            clauses_by_subject[subject_key].append(clause)
        
        # Check for contradictions within each subject
        for subject_id, subject_clauses in clauses_by_subject.items():
            self._check_nullability_contradictions(subject_clauses, result)
            self._check_ownership_contradictions(subject_clauses, result)
    
    def _check_nullability_contradictions(self, clauses: List[ContractClause], result: ValidationResult):
        """Check for contradictory nullability clauses."""
        nullable_clauses = [c for c in clauses if c.clause_type == ClauseType.NULLABILITY]
        
        if len(nullable_clauses) > 1:
            # Check if they agree
            nullable_values = []
            for clause in nullable_clauses:
                nullable_param = clause.get_parameter("nullable")
                if nullable_param:
                    nullable_values.append(nullable_param.value)
            
            if len(set(nullable_values)) > 1:
                result.add_error(
                    code="E_CONST_002",
                    message="Contradictory nullability clauses on same entity",
                    remediation="Remove conflicting clauses"
                )
    
    def _check_ownership_contradictions(self, clauses: List[ContractClause], result: ValidationResult):
        """Check for contradictory ownership clauses."""
        ownership_clauses = [c for c in clauses if c.clause_type == ClauseType.OWNERSHIP]
        
        if len(ownership_clauses) > 1:
            result.add_warning(
                code="W_CONST_001",
                message="Multiple ownership clauses on same entity"
            )

# ============================================================================
# COMPLETE VALIDATOR
# ============================================================================

class ContractValidator:
    """
    Complete multi-layer contract validator.
    
    The ContractValidator orchestrates the three validation layers:
    1. Schema Layer: Verifies structural integrity against JSON schema.
    2. Referential Layer: Ensures all symbol identifiers exist in the IR artifact.
    3. Constraint Layer: Checks for logical consistency between constraints.
    
    Attributes:
        context (ValidationContext): Validation settings and behavior
        schema_validator (SchemaValidator): Structural integrity checker
    """
    
    def __init__(self, context: Optional[ValidationContext] = None):
        self.context = context or ValidationContext()
        
        self.schema_validator = SchemaValidator()
        self.referential_validator = ReferentialValidator(self.context)
        self.constraint_validator = ConstraintValidator(self.context)
    
    def validate(
        self,
        contract: ContractDocument,
        skip_referential: bool = False,
        skip_constraint: bool = False
    ) -> CompleteValidationResult:
        """
        Validate contract through all layers.
        
        Args:
            contract: Contract to validate
            skip_referential: Skip referential validation (for testing)
            skip_constraint: Skip constraint validation (for testing)
            
        Returns:
            Complete validation result
        """
        result = CompleteValidationResult()
        
        # Layer 1: Schema validation
        result.schema_result = self.schema_validator.validate(contract)
        
        if not result.schema_result.passed:
            return result
        
        # Layer 2: Referential validation
        if not skip_referential:
            result.referential_result = self.referential_validator.validate(contract)
            
            if not result.referential_result.passed:
                return result
        
        if not skip_constraint:
            result.constraint_result = self.constraint_validator.validate(contract)
        
        return result
    
    def validate_quick(self, contract: ContractDocument) -> bool:
        """
        Quick validation check (schema only).
        
        Returns:
            True if schema valid
        """
        result = self.schema_validator.validate(contract)
        return result.passed

__all__ = [
    'ValidationLayer',
    'ValidationError',
    'ValidationWarning',
    'ValidationResult',
    'CompleteValidationResult',
    'ValidationContext',
    'SchemaValidator',
    'ReferentialValidator',
    'ConstraintValidator',
    'ContractValidator',
]
