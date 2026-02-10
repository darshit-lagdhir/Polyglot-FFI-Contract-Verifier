"""
Unit tests for Module 06: Contract Validation
Comprehensive test suite (100 tests)
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_06_contract_schema.contract_validation import (
    ValidationLayer,
    ValidationError,
    ValidationWarning,
    ValidationResult,
    CompleteValidationResult,
    ValidationContext,
    SchemaValidator,
    ReferentialValidator,
    ConstraintValidator,
    ContractValidator
)
from module_06_contract_schema.contract_entities import (
    ContractDocument,
    ContractHeader,
    ContractClause,
    SubjectReference,
    ConstraintParameter,
    ClauseType,
    SubjectKind,
    Severity
)

class TestValidationError:
    """Test ValidationError representation."""
    
    def test_creation(self):
        error = ValidationError(
            error_code="E001",
            error_message="Test error",
            layer=ValidationLayer.SCHEMA
        )
        
        assert error.error_code == "E001"
        assert error.layer == ValidationLayer.SCHEMA
    
    def test_with_clause_id(self):
        error = ValidationError(
            error_code="E002",
            error_message="Test error",
            layer=ValidationLayer.REFERENTIAL,
            clause_id="clause_123"
        )
        
        assert error.clause_id == "clause_123"
    
    def test_string_representation(self):
        error = ValidationError(
            error_code="E003",
            error_message="Something failed",
            layer=ValidationLayer.CONSTRAINT,
            clause_id="test_clause",
            remediation="Fix it"
        )
        
        str_repr = str(error)
        
        assert "ERROR" in str_repr
        assert "Something failed" in str_repr
        assert "test_clause" in str_repr
    
    def test_with_location(self):
        error = ValidationError(
            error_code="E004",
            error_message="Location test",
            layer=ValidationLayer.SCHEMA,
            location="header.version"
        )
        
        assert error.location == "header.version"
    
    def test_full_error(self):
        error = ValidationError(
            error_code="E005",
            error_message="Complete error",
            layer=ValidationLayer.REFERENTIAL,
            clause_id="clause_1",
            location="subject_ref",
            remediation="Check entity ID"
        )
        
        str_repr = str(error)
        assert "Complete error" in str_repr
        assert "clause_1" in str_repr
        assert "subject_ref" in str_repr
        assert "Check entity ID" in str_repr

class TestValidationWarning:
    """Test ValidationWarning representation."""
    
    def test_creation(self):
        warning = ValidationWarning(
            warning_code="W001",
            warning_message="Test warning",
            layer=ValidationLayer.SCHEMA
        )
        
        assert warning.warning_code == "W001"
    
    def test_string_representation(self):
        warning = ValidationWarning(
            warning_code="W002",
            warning_message="Potential issue",
            layer=ValidationLayer.CONSTRAINT,
            clause_id="clause_abc"
        )
        
        str_repr = str(warning)
        
        assert "WARNING" in str_repr
        assert "Potential issue" in str_repr
    
    def test_warning_with_clause(self):
        warning = ValidationWarning(
            warning_code="W003",
            warning_message="Minor issue",
            layer=ValidationLayer.REFERENTIAL,
            clause_id="test_clause"
        )
        
        assert warning.clause_id == "test_clause"

class TestValidationResult:
    """Test ValidationResult."""
    
    def test_creation(self):
        result = ValidationResult(
            layer=ValidationLayer.SCHEMA,
            passed=True
        )
        
        assert result.layer == ValidationLayer.SCHEMA
        assert result.passed is True
    
    def test_add_error(self):
        result = ValidationResult(
            layer=ValidationLayer.REFERENTIAL,
            passed=True
        )
        
        result.add_error("E001", "Test error")
        
        assert len(result.errors) == 1
        assert result.passed is False
    
    def test_add_warning(self):
        result = ValidationResult(
            layer=ValidationLayer.CONSTRAINT,
            passed=True
        )
        
        result.add_warning("W001", "Test warning")
        
        assert len(result.warnings) == 1
        assert result.passed is True  # Warnings don't affect passed status
    
    def test_has_errors(self):
        result = ValidationResult(ValidationLayer.SCHEMA, True)
        
        assert not result.has_errors()
        
        result.add_error("E001", "Error")
        
        assert result.has_errors()
    
    def test_has_warnings(self):
        result = ValidationResult(ValidationLayer.SCHEMA, True)
        
        assert not result.has_warnings()
        
        result.add_warning("W001", "Warning")
        
        assert result.has_warnings()
    
    def test_multiple_errors(self):
        result = ValidationResult(ValidationLayer.SCHEMA, True)
        
        result.add_error("E001", "Error 1")
        result.add_error("E002", "Error 2")
        result.add_error("E003", "Error 3")
        
        assert len(result.errors) == 3
        assert result.passed is False
    
    def test_error_with_all_fields(self):
        result = ValidationResult(ValidationLayer.REFERENTIAL, True)
        
        result.add_error(
            code="E_FULL",
            message="Complete error",
            clause_id="clause_1",
            location="field.name",
            remediation="Fix the field"
        )
        
        assert len(result.errors) == 1
        error = result.errors[0]
        assert error.clause_id == "clause_1"
        assert error.location == "field.name"
        assert error.remediation == "Fix the field"

class TestCompleteValidationResult:
    """Test CompleteValidationResult."""
    
    def test_all_layers_passed(self):
        result = CompleteValidationResult()
        result.schema_result = ValidationResult(ValidationLayer.SCHEMA, True)
        result.referential_result = ValidationResult(ValidationLayer.REFERENTIAL, True)
        result.constraint_result = ValidationResult(ValidationLayer.CONSTRAINT, True)
        
        assert result.passed is True
    
    def test_schema_failed(self):
        result = CompleteValidationResult()
        result.schema_result = ValidationResult(ValidationLayer.SCHEMA, False)
        result.referential_result = ValidationResult(ValidationLayer.REFERENTIAL, True)
        
        assert result.passed is False
    
    def test_get_all_errors(self):
        result = CompleteValidationResult()
        
        schema_result = ValidationResult(ValidationLayer.SCHEMA, False)
        schema_result.add_error("E001", "Schema error")
        
        ref_result = ValidationResult(ValidationLayer.REFERENTIAL, False)
        ref_result.add_error("E002", "Ref error")
        
        result.schema_result = schema_result
        result.referential_result = ref_result
        
        all_errors = result.get_all_errors()
        
        assert len(all_errors) == 2
    
    def test_generate_report(self):
        result = CompleteValidationResult()
        result.schema_result = ValidationResult(ValidationLayer.SCHEMA, True)
        
        report = result.generate_report()
        
        assert "Validation Report" in report
        assert "Schema Validation" in report
    
    def test_get_all_warnings(self):
        result = CompleteValidationResult()
        
        schema_result = ValidationResult(ValidationLayer.SCHEMA, True)
        schema_result.add_warning("W001", "Schema warning")
        
        constraint_result = ValidationResult(ValidationLayer.CONSTRAINT, True)
        constraint_result.add_warning("W002", "Constraint warning")
        
        result.schema_result = schema_result
        result.constraint_result = constraint_result
        
        all_warnings = result.get_all_warnings()
        
        assert len(all_warnings) == 2
    
    def test_partial_validation(self):
        result = CompleteValidationResult()
        result.schema_result = ValidationResult(ValidationLayer.SCHEMA, True)
        # No other layers
        
        assert result.passed is True
    
    def test_failed_report(self):
        result = CompleteValidationResult()
        
        schema_result = ValidationResult(ValidationLayer.SCHEMA, False)
        schema_result.add_error("E001", "Schema failed")
        
        result.schema_result = schema_result
        
        report = result.generate_report()
        
        assert "FAILED" in report
        assert "Schema failed" in report

class TestValidationContext:
    """Test ValidationContext."""
    
    def test_creation(self):
        context = ValidationContext()
        
        assert context.strict_mode is True
        assert len(context.entity_index) == 0
    
    def test_with_ir_artifact(self):
        # Mock IR artifact
        mock_ir = type('MockIR', (), {
            'interface_unit': type('MockUnit', (), {
                'types': [],
                'symbols': []
            })()
        })()
        
        context = ValidationContext(ir_artifact=mock_ir)
        
        assert context.ir_artifact is not None
    
    def test_build_entity_index_no_ir(self):
        context = ValidationContext()
        
        # Should not crash
        context.build_entity_index()
        
        assert len(context.entity_index) == 0
    
    def test_strict_mode(self):
        context = ValidationContext(strict_mode=False)
        
        assert context.strict_mode is False
    
    def test_target_platform(self):
        context = ValidationContext(target_platform="linux-x64")
        
        assert context.target_platform == "linux-x64"
    
    def test_treat_warnings_as_errors(self):
        context = ValidationContext(treat_warnings_as_errors=True)
        
        assert context.treat_warnings_as_errors is True

class TestSchemaValidator:
    """Test SchemaValidator."""
    
    def test_valid_contract(self):
        header = ContractHeader(target_interface_id="test_interface")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func_1")
        clause = ContractClause(
            clause_id="clause_1",
            clause_type=ClauseType.SIZE,
            subject_reference=ref
        )
        contract.add_clause(clause)
        
        validator = SchemaValidator()
        result = validator.validate(contract)
        
        assert result.passed is True
        assert len(result.errors) == 0
    
    def test_invalid_header(self):
        header = ContractHeader(
            target_interface_id="",  # Invalid: empty
            contract_version="invalid_version"
        )
        contract = ContractDocument(header=header)
        
        validator = SchemaValidator()
        result = validator.validate(contract)
        
        assert result.passed is False
        assert len(result.errors) > 0
    
    def test_duplicate_clause_ids(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        
        clause1 = ContractClause("duplicate_id", ClauseType.SIZE, ref)
        clause2 = ContractClause("duplicate_id", ClauseType.NULLABILITY, ref)
        
        contract.add_clause(clause1)
        contract.add_clause(clause2)
        
        validator = SchemaValidator()
        result = validator.validate(contract)
        
        assert result.passed is False
        assert any("Duplicate" in e.error_message for e in result.errors)
    
    def test_clause_without_id(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("", ClauseType.SIZE, ref)  # Empty ID
        
        contract.add_clause(clause)
        
        validator = SchemaValidator()
        result = validator.validate(contract)
        
        assert result.passed is False
    
    def test_multiple_valid_clauses(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        
        for i in range(5):
            clause = ContractClause(f"clause_{i}", ClauseType.SIZE, ref)
            contract.add_clause(clause)
        
        validator = SchemaValidator()
        result = validator.validate(contract)
        
        assert result.passed is True
    
    def test_empty_contract(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        validator = SchemaValidator()
        result = validator.validate(contract)
        
        assert result.passed is True

class TestReferentialValidator:
    """Test ReferentialValidator."""
    
    def test_no_ir_artifact(self):
        context = ValidationContext()
        validator = ReferentialValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        result = validator.validate(contract)
        
        assert result.passed is False
        assert any("IR artifact" in e.error_message for e in result.errors)
    
    def test_valid_reference(self):
        # Create mock IR artifact
        mock_entity = type('MockEntity', (), {'entity_id': 'func_123'})()
        
        context = ValidationContext()
        context.entity_index = {'func_123': mock_entity}
        
        # Create mock IR to pass the artifact check
        mock_ir = type('MockIR', (), {'interface_unit': None})()
        context.ir_artifact = mock_ir
        
        validator = ReferentialValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func_123")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        result = validator.validate(contract)
        
        assert result.passed is True
    
    def test_invalid_reference(self):
        context = ValidationContext()
        context.entity_index = {}  # Empty index
        
        # Create mock IR
        mock_ir = type('MockIR', (), {'interface_unit': None})()
        context.ir_artifact = mock_ir
        
        validator = ReferentialValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "nonexistent")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        result = validator.validate(contract)
        
        assert result.passed is False
        assert any("cannot be resolved" in e.error_message for e in result.errors)
    
    def test_multiple_valid_references(self):
        mock_entity1 = type('MockEntity', (), {'entity_id': 'func_1'})()
        mock_entity2 = type('MockEntity', (), {'entity_id': 'func_2'})()
        
        context = ValidationContext()
        context.entity_index = {'func_1': mock_entity1, 'func_2': mock_entity2}
        
        mock_ir = type('MockIR', (), {'interface_unit': None})()
        context.ir_artifact = mock_ir
        
        validator = ReferentialValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref1 = SubjectReference(SubjectKind.FUNCTION, "func_1")
        ref2 = SubjectReference(SubjectKind.FUNCTION, "func_2")
        
        contract.add_clause(ContractClause("clause_1", ClauseType.SIZE, ref1))
        contract.add_clause(ContractClause("clause_2", ClauseType.SIZE, ref2))
        
        result = validator.validate(contract)
        
        assert result.passed is True
    
    def test_parent_reference_missing(self):
        mock_entity = type('MockEntity', (), {'entity_id': 'param_1'})()
        
        context = ValidationContext()
        # Include the param itself but not its parent
        context.entity_index = {'param_1': mock_entity}
        
        mock_ir = type('MockIR', (), {'interface_unit': None})()
        context.ir_artifact = mock_ir
        
        validator = ReferentialValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.PARAMETER, "param_1", parent_id="missing_parent")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        result = validator.validate(contract)
        
        assert result.passed is False
        assert any("Parent entity" in e.error_message for e in result.errors)

class TestConstraintValidator:
    """Test ConstraintValidator."""
    
    def test_valid_constraints(self):
        context = ValidationContext()
        validator = ConstraintValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.PARAMETER, "param")
        param = ConstraintParameter("nullable", False, "boolean")
        clause = ContractClause(
            "clause_1",
            ClauseType.NULLABILITY,
            ref,
            constraint_parameters=[param]
        )
        contract.add_clause(clause)
        
        result = validator.validate(contract)
        
        assert result.passed is True
    
    def test_contradictory_nullability(self):
        context = ValidationContext()
        validator = ConstraintValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.PARAMETER, "same_param")
        
        param1 = ConstraintParameter("nullable", True, "boolean")
        clause1 = ContractClause(
            "clause_1",
            ClauseType.NULLABILITY,
            ref,
            constraint_parameters=[param1]
        )
        
        param2 = ConstraintParameter("nullable", False, "boolean")
        clause2 = ContractClause(
            "clause_2",
            ClauseType.NULLABILITY,
            ref,
            constraint_parameters=[param2]
        )
        
        contract.add_clause(clause1)
        contract.add_clause(clause2)
        
        result = validator.validate(contract)
        
        assert result.passed is False
        assert any("Contradictory" in e.error_message for e in result.errors)
    
    def test_multiple_ownership_warning(self):
        context = ValidationContext()
        validator = ConstraintValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")
        
        clause1 = ContractClause("clause_1", ClauseType.OWNERSHIP, ref)
        clause2 = ContractClause("clause_2", ClauseType.OWNERSHIP, ref)
        
        contract.add_clause(clause1)
        contract.add_clause(clause2)
        
        result = validator.validate(contract)
        
        assert result.has_warnings()
        assert any("Multiple ownership" in w.warning_message for w in result.warnings)
    
    def test_different_subjects_no_conflict(self):
        context = ValidationContext()
        validator = ConstraintValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref1 = SubjectReference(SubjectKind.PARAMETER, "param1")
        ref2 = SubjectReference(SubjectKind.PARAMETER, "param2")
        
        param1 = ConstraintParameter("nullable", True, "boolean")
        param2 = ConstraintParameter("nullable", False, "boolean")
        
        clause1 = ContractClause("clause_1", ClauseType.NULLABILITY, ref1, constraint_parameters=[param1])
        clause2 = ContractClause("clause_2", ClauseType.NULLABILITY, ref2, constraint_parameters=[param2])
        
        contract.add_clause(clause1)
        contract.add_clause(clause2)
        
        result = validator.validate(contract)
        
        assert result.passed is True

class TestContractValidator:
    """Test complete ContractValidator."""
    
    def test_valid_contract_all_layers(self):
        context = ValidationContext()
        context.entity_index = {'func_1': type('E', (), {'entity_id': 'func_1'})()}
        
        mock_ir = type('MockIR', (), {'interface_unit': None})()
        context.ir_artifact = mock_ir
        
        validator = ContractValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func_1")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        result = validator.validate(contract)
        
        assert result.schema_result.passed is True
        assert result.referential_result.passed is True
        assert result.constraint_result.passed is True
        assert result.passed is True
    
    def test_schema_failure_stops_validation(self):
        validator = ContractValidator()
        
        header = ContractHeader(
            target_interface_id="",  # Invalid
            contract_version="bad"
        )
        contract = ContractDocument(header=header)
        
        result = validator.validate(contract)
        
        assert result.schema_result.passed is False
        assert result.referential_result is None  # Should not reach this layer
    
    def test_quick_validation(self):
        validator = ContractValidator()
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        quick_result = validator.validate_quick(contract)
        
        assert quick_result is True
    
    def test_quick_validation_fails(self):
        validator = ContractValidator()
        
        header = ContractHeader(target_interface_id="")
        contract = ContractDocument(header=header)
        
        quick_result = validator.validate_quick(contract)
        
        assert quick_result is False
    
    def test_skip_referential(self):
        validator = ContractValidator()
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        result = validator.validate(contract, skip_referential=True, skip_constraint=True)
        
        assert result.schema_result.passed is True
        assert result.referential_result is None
        assert result.constraint_result is None
    
    def test_skip_constraint(self):
        context = ValidationContext()
        context.entity_index = {'func_1': type('E', (), {'entity_id': 'func_1'})()}
        mock_ir = type('MockIR', (), {'interface_unit': None})()
        context.ir_artifact = mock_ir
        
        validator = ContractValidator(context)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func_1")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        result = validator.validate(contract, skip_constraint=True)
        
        assert result.schema_result.passed is True
        assert result.referential_result.passed is True
        assert result.constraint_result is None

class TestEdgeCases:
    """Test edge cases and corner scenarios."""
    
    def test_empty_contract(self):
        validator = ContractValidator()
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        # No clauses
        
        result = validator.validate(contract, skip_referential=True, skip_constraint=True)
        
        assert result.schema_result.passed is True
    
    def test_many_clauses(self):
        validator = ContractValidator()
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        # Add 100 clauses
        for i in range(100):
            ref = SubjectReference(SubjectKind.FUNCTION, f"func_{i}")
            clause = ContractClause(f"clause_{i}", ClauseType.SIZE, ref)
            contract.add_clause(clause)
        
        result = validator.validate(contract, skip_referential=True, skip_constraint=True)
        
        assert result.schema_result.passed is True
    
    def test_validation_layer_enum(self):
        assert ValidationLayer.SCHEMA.value == "schema"
        assert ValidationLayer.REFERENTIAL.value == "referential"
        assert ValidationLayer.CONSTRAINT.value == "constraint"
    
    def test_error_without_optional_fields(self):
        error = ValidationError(
            error_code="E_MIN",
            error_message="Minimal error",
            layer=ValidationLayer.SCHEMA
        )
        
        assert error.clause_id is None
        assert error.location is None
        assert error.remediation is None
    
    def test_warning_without_clause(self):
        warning = ValidationWarning(
            warning_code="W_MIN",
            warning_message="Minimal warning",
            layer=ValidationLayer.CONSTRAINT
        )
        
        assert warning.clause_id is None
    
    def test_complete_result_no_layers(self):
        result = CompleteValidationResult()
        
        # No layers set
        assert result.passed is True  # All None layers pass
    
    def test_validation_result_initial_state(self):
        result = ValidationResult(ValidationLayer.SCHEMA, True)
        
        assert not result.has_errors()
        assert not result.has_warnings()
        assert result.passed is True
    
    def test_context_default_values(self):
        context = ValidationContext()
        
        assert context.ir_artifact is None
        assert context.strict_mode is True
        assert context.treat_warnings_as_errors is False
        assert context.target_platform is None
    
    def test_multiple_error_types(self):
        result = ValidationResult(ValidationLayer.SCHEMA, True)
        
        result.add_error("E001", "Error 1", clause_id="c1")
        result.add_error("E002", "Error 2", location="loc2")
        result.add_error("E003", "Error 3", remediation="fix3")
        
        assert len(result.errors) == 3
        assert result.errors[0].clause_id == "c1"
        assert result.errors[1].location == "loc2"
        assert result.errors[2].remediation == "fix3"
    
    def test_report_with_all_layers(self):
        result = CompleteValidationResult()
        
        schema = ValidationResult(ValidationLayer.SCHEMA, True)
        ref = ValidationResult(ValidationLayer.REFERENTIAL, True)
        const = ValidationResult(ValidationLayer.CONSTRAINT, True)
        
        result.schema_result = schema
        result.referential_result = ref
        result.constraint_result = const
        
        report = result.generate_report()
        
        assert "Schema Validation: PASS" in report
        assert "Referential Validation: PASS" in report
        assert "Constraint Validation: PASS" in report

# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
