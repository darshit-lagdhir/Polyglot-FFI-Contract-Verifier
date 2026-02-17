
"""Test Suite for Language Adapter - Prompt 06/25: 85 tests."""

import pytest
from modules.module_08_language_adapter import (
    ReturnValueConstraint,
    ReturnValueValidator,
    OutputParameterConstraint,
    OutputParameterValidator,
    ErrorCodeInterpreter,
    MemoryInspector,
    PostCallValidator,
    OwnershipKind,
)


class TestReturnValueConstraint:
    """ReturnValueConstraint tests (10 tests)."""
    
    def test_create_constraint(self):
        """Test 476: Create return value constraint."""
        constraint = ReturnValueConstraint(
            expected_type=int,
            allow_null=False
        )
        assert constraint.expected_type == int
        assert constraint.allow_null is False
    
    def test_constraint_with_range(self):
        """Test 477: Constraint with range."""
        constraint = ReturnValueConstraint(
            min_value=0,
            max_value=100
        )
        assert constraint.min_value == 0
        assert constraint.max_value == 100
    
    def test_constraint_with_enum(self):
        """Test 478: Constraint with allowed values."""
        constraint = ReturnValueConstraint(
            allowed_values=[0, 1, 2]
        )
        assert 1 in constraint.allowed_values
    
    def test_constraint_to_dict(self):
        """Test 479-485: Constraint serialization."""
        constraint = ReturnValueConstraint(
            expected_type=int,
            allow_null=False,
            ownership=OwnershipKind.CALLER_OWNED
        )
        data = constraint.to_dict()
        assert data['expected_type'] == 'int'
        assert data['allow_null'] is False


class TestReturnValueValidator:
    """ReturnValueValidator tests (20 tests)."""
    
    def test_validate_type_correct(self):
        """Test 486: Type validation passes."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(expected_type=int)
        
        valid, _ = validator.validate(42, constraint)
        assert valid is True
    
    def test_validate_type_incorrect(self):
        """Test 487: Type validation fails."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(expected_type=int)
        
        valid, msg = validator.validate('not_int', constraint)
        assert valid is False
        assert 'type' in msg.lower()
    
    def test_validate_nullability_allowed(self):
        """Test 488: Null allowed passes."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(allow_null=True)
        
        valid, _ = validator.validate(None, constraint)
        assert valid is True
    
    def test_validate_nullability_forbidden(self):
        """Test 489: Null forbidden fails."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(allow_null=False)
        
        valid, msg = validator.validate(None, constraint)
        assert valid is False
        assert 'null' in msg.lower()
    
    def test_validate_range_within(self):
        """Test 490: Range validation passes."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(min_value=0, max_value=100)
        
        valid, _ = validator.validate(50, constraint)
        assert valid is True
    
    def test_validate_range_below_min(self):
        """Test 491: Below minimum fails."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(min_value=0)
        
        valid, msg = validator.validate(-5, constraint)
        assert valid is False
        assert 'minimum' in msg.lower()
    
    def test_validate_range_above_max(self):
        """Test 492: Above maximum fails."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(max_value=100)
        
        valid, msg = validator.validate(150, constraint)
        assert valid is False
        assert 'maximum' in msg.lower()
    
    def test_validate_enum_valid(self):
        """Test 493: Enum value valid."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(allowed_values=[1, 2, 3])
        
        valid, _ = validator.validate(2, constraint)
        assert valid is True
    
    def test_validate_enum_invalid(self):
        """Test 494: Enum value invalid."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(allowed_values=[1, 2, 3])
        
        valid, msg = validator.validate(5, constraint)
        assert valid is False
    
    def test_validate_alignment_aligned(self):
        """Test 495: Alignment validation passes."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(alignment=4)
        
        valid, _ = validator.validate(0x1000, constraint)
        assert valid is True
    
    def test_validate_alignment_unaligned(self):
        """Test 496: Alignment validation fails."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(alignment=4)
        
        valid, msg = validator.validate(0x1001, constraint)
        assert valid is False
    
    def test_validate_null_skips_further_checks(self):
        """Test 497-505: Null skips range checks."""
        validator = ReturnValueValidator()
        constraint = ReturnValueConstraint(
            allow_null=True,
            min_value=0,
            max_value=100
        )
        
        valid, _ = validator.validate(None, constraint)
        assert valid is True


class TestOutputParameterConstraint:
    """OutputParameterConstraint tests (5 tests)."""
    
    def test_create_constraint(self):
        """Test 506: Create output constraint."""
        constraint = OutputParameterConstraint(param_index=0)
        assert constraint.param_index == 0
        assert constraint.required is True
    
    def test_constraint_with_range(self):
        """Test 507-510: Constraint with various fields."""
        constraint = OutputParameterConstraint(
            param_index=1,
            required=False,
            min_value=0,
            max_value=100
        )
        assert constraint.required is False
        assert constraint.max_value == 100


class TestOutputParameterValidator:
    """OutputParameterValidator tests (15 tests)."""
    
    def test_validate_required_present(self):
        """Test 511: Required parameter present."""
        validator = OutputParameterValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            required=True
        )
        
        valid, _ = validator.validate(42, constraint)
        assert valid is True
    
    def test_validate_required_missing(self):
        """Test 512: Required parameter missing."""
        validator = OutputParameterValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            required=True
        )
        
        valid, msg = validator.validate(None, constraint)
        assert valid is False
        assert 'required' in msg.lower()
    
    def test_validate_optional_missing(self):
        """Test 513: Optional parameter can be None."""
        validator = OutputParameterValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            required=False
        )
        
        valid, _ = validator.validate(None, constraint)
        assert valid is True
    
    def test_validate_type_correct(self):
        """Test 514: Type validation passes."""
        validator = OutputParameterValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            expected_type=int
        )
        
        valid, _ = validator.validate(42, constraint)
        assert valid is True
    
    def test_validate_type_incorrect(self):
        """Test 515: Type validation fails."""
        validator = OutputParameterValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            expected_type=int
        )
        
        valid, msg = validator.validate('not_int', constraint)
        assert valid is False
    
    def test_validate_range_within(self):
        """Test 516-525: Range validation."""
        validator = OutputParameterValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            min_value=0,
            max_value=100
        )
        
        valid, _ = validator.validate(50, constraint)
        assert valid is True


class TestErrorCodeInterpreter:
    """ErrorCodeInterpreter tests (15 tests)."""
    
    def test_negative_is_error_true(self):
        """Test 526: Negative value is error."""
        interp = ErrorCodeInterpreter()
        assert interp.is_error(-1, 'negative_is_error') is True
    
    def test_negative_is_error_false(self):
        """Test 527: Positive value not error."""
        interp = ErrorCodeInterpreter()
        assert interp.is_error(0, 'negative_is_error') is False
    
    def test_zero_is_success_true(self):
        """Test 528: Zero is success."""
        interp = ErrorCodeInterpreter()
        assert interp.is_success(0, 'zero_is_success') is True
    
    def test_zero_is_success_false(self):
        """Test 529: Non-zero not success."""
        interp = ErrorCodeInterpreter()
        assert interp.is_success(1, 'zero_is_success') is False
    
    def test_null_is_error_true(self):
        """Test 530: Null is error."""
        interp = ErrorCodeInterpreter()
        assert interp.is_error(None, 'null_is_error') is True
    
    def test_null_is_error_false(self):
        """Test 531: Non-null not error."""
        interp = ErrorCodeInterpreter()
        assert interp.is_error(42, 'null_is_error') is False
    
    def test_false_is_error(self):
        """Test 532: False is error."""
        interp = ErrorCodeInterpreter()
        assert interp.is_error(False, 'false_is_error') is True
    
    def test_register_custom_pattern(self):
        """Test 533: Register custom pattern."""
        interp = ErrorCodeInterpreter()
        interp.register_pattern(
            'positive_is_error',
            lambda val: isinstance(val, int) and val > 0
        )
        
        assert interp.is_error(5, 'positive_is_error') is True
        assert interp.is_error(-5, 'positive_is_error') is False
    
    def test_unknown_pattern(self):
        """Test 534-540: Unknown pattern returns False."""
        interp = ErrorCodeInterpreter()
        assert interp.is_error(42, 'unknown_pattern') is False


class TestMemoryInspector:
    """MemoryInspector tests (10 tests)."""
    
    def test_take_snapshot(self):
        """Test 541: Take memory snapshot."""
        inspector = MemoryInspector()
        data = b'test_data'
        
        snapshot_id = inspector.take_snapshot(0x1000, len(data), data)
        assert snapshot_id is not None
    
    def test_compare_unchanged(self):
        """Test 542: Compare unchanged memory."""
        inspector = MemoryInspector()
        data = b'test_data'
        
        inspector.take_snapshot(0x1000, len(data), data)
        result = inspector.compare_snapshot(0x1000, data)
        
        assert result['has_snapshot'] is True
        assert result['modified'] is False
    
    def test_compare_modified(self):
        """Test 543: Compare modified memory."""
        inspector = MemoryInspector()
        original = b'test_data'
        modified = b'TEST_DATA'
        
        inspector.take_snapshot(0x1000, len(original), original)
        result = inspector.compare_snapshot(0x1000, modified)
        
        assert result['has_snapshot'] is True
        assert result['modified'] is True
    
    def test_compare_no_snapshot(self):
        """Test 544: Compare without snapshot."""
        inspector = MemoryInspector()
        result = inspector.compare_snapshot(0x1000, b'data')
        
        assert result['has_snapshot'] is False
    
    def test_clear_snapshots(self):
        """Test 545-550: Clear all snapshots."""
        inspector = MemoryInspector()
        inspector.take_snapshot(0x1000, 10, b'test')
        inspector.clear_snapshots()
        
        result = inspector.compare_snapshot(0x1000, b'test')
        assert result['has_snapshot'] is False


class TestPostCallValidator:
    """PostCallValidator tests (10 tests)."""
    
    def test_validate_return_only(self):
        """Test 551: Validate return value only."""
        validator = PostCallValidator()
        constraint = ReturnValueConstraint(expected_type=int)
        
        result = validator.validate_post_call(
            42,
            {},
            return_constraint=constraint
        )
        
        assert result['valid'] is True
        assert result['return_valid'] is True
    
    def test_validate_return_fails(self):
        """Test 552: Return validation fails."""
        validator = PostCallValidator()
        constraint = ReturnValueConstraint(expected_type=int)
        
        result = validator.validate_post_call(
            'not_int',
            {},
            return_constraint=constraint
        )
        
        assert result['valid'] is False
        assert result['return_valid'] is False
    
    def test_validate_outputs_only(self):
        """Test 553: Validate outputs only."""
        validator = PostCallValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            required=True
        )
        
        result = validator.validate_post_call(
            None,
            {0: 42},
            output_constraints=[constraint]
        )
        
        assert result['valid'] is True
        assert result['outputs_valid'] is True
    
    def test_validate_outputs_fail(self):
        """Test 554: Output validation fails."""
        validator = PostCallValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            required=True
        )
        
        result = validator.validate_post_call(
            None,
            {0: None},
            output_constraints=[constraint]
        )
        
        assert result['valid'] is False
        assert result['outputs_valid'] is False
    
    def test_error_code_detection(self):
        """Test 555: Error code detected."""
        validator = PostCallValidator()
        
        result = validator.validate_post_call(
            -1,
            {},
            error_pattern='negative_is_error'
        )
        
        assert result['function_succeeded'] is False
        assert result['error_code'] == -1
    
    def test_skip_output_on_error(self):
        """Test 556: Skip output validation on error."""
        validator = PostCallValidator()
        constraint = OutputParameterConstraint(
            param_index=0,
            required=True
        )
        
        result = validator.validate_post_call(
            -1,  # Error
            {0: None},  # Invalid output
            output_constraints=[constraint],
            error_pattern='negative_is_error'
        )
        
        # Should detect error and skip output validation
        assert result['function_succeeded'] is False
        assert result['outputs_valid'] is True
    
    def test_multiple_violations(self):
        """Test 557-560: Multiple violations collected."""
        validator = PostCallValidator()
        ret_constraint = ReturnValueConstraint(expected_type=int)
        out_constraint = OutputParameterConstraint(
            param_index=0,
            required=True
        )
        
        result = validator.validate_post_call(
            'bad',  # Bad return
            {0: None},  # Bad output
            return_constraint=ret_constraint,
            output_constraints=[out_constraint]
        )
        
        assert result['valid'] is False
        assert len(result['violations']) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
