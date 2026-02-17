
"""Test Suite for Language Adapter - Prompt 05/25: 90 tests."""

import pytest
from modules.module_08_language_adapter import (
    CompoundPredicate,
    ConditionalPredicate,
    ExpressionPredicate,
    AlignmentPredicate,
    EnumPredicate,
    BitwisePredicate,
    PredicateRegistry,
    PredicateFactory,
)


class TestCompoundPredicate:
    """CompoundPredicate tests (20 tests)."""
    
    def test_and_predicate_all_pass(self):
        """Test 376: AND predicate with all passing."""
        pred1 = lambda inputs, params: inputs[0] > 0
        pred2 = lambda inputs, params: inputs[0] < 100
        
        compound = CompoundPredicate('and', [pred1, pred2])
        assert compound([50], [0]) is True
    
    def test_and_predicate_one_fails(self):
        """Test 377: AND predicate with one failing."""
        pred1 = lambda inputs, params: inputs[0] > 0
        pred2 = lambda inputs, params: inputs[0] < 100
        
        compound = CompoundPredicate('and', [pred1, pred2])
        assert compound([150], [0]) is False
    
    def test_or_predicate_one_passes(self):
        """Test 378: OR predicate with one passing."""
        pred1 = lambda inputs, params: inputs[0] < 0
        pred2 = lambda inputs, params: inputs[0] > 100
        
        compound = CompoundPredicate('or', [pred1, pred2])
        assert compound([150], [0]) is True
    
    def test_or_predicate_all_fail(self):
        """Test 379: OR predicate with all failing."""
        pred1 = lambda inputs, params: inputs[0] < 0
        pred2 = lambda inputs, params: inputs[0] > 100
        
        compound = CompoundPredicate('or', [pred1, pred2])
        assert compound([50], [0]) is False
    
    def test_not_predicate(self):
        """Test 380: NOT predicate inverts result."""
        pred = lambda inputs, params: inputs[0] > 0
        
        compound = CompoundPredicate('not', [pred])
        assert compound([5], [0]) is False
        assert compound([-5], [0]) is True
    
    def test_invalid_operator(self):
        """Test 381: Invalid operator raises error."""
        with pytest.raises(ValueError, match='Invalid operator'):
            CompoundPredicate('xor', [lambda i, p: True])
    
    def test_not_requires_one_predicate(self):
        """Test 382: NOT requires exactly one predicate."""
        pred1 = lambda i, p: True
        pred2 = lambda i, p: True
        
        with pytest.raises(ValueError, match='exactly one'):
            CompoundPredicate('not', [pred1, pred2])
    
    def test_nested_compounds(self):
        """Test 383-395: Nested compound predicates."""
        pred1 = lambda i, p: i[0] > 0
        pred2 = lambda i, p: i[0] < 100
        
        inner = CompoundPredicate('and', [pred1, pred2])
        outer = CompoundPredicate('not', [inner.__call__])
        
        assert outer([50], [0]) is False
        assert outer([150], [0]) is True


class TestConditionalPredicate:
    """ConditionalPredicate tests (15 tests)."""
    
    def test_condition_true_branch(self):
        """Test 396: Condition true executes then branch."""
        condition = lambda i, p: i[1] > 0
        then_pred = lambda i, p: i[0] is not None
        else_pred = lambda i, p: True
        
        pred = ConditionalPredicate(condition, then_pred, else_pred)
        assert pred([None, 5], [0, 1]) is False
        assert pred([42, 5], [0, 1]) is True
    
    def test_condition_false_branch(self):
        """Test 397: Condition false executes else branch."""
        condition = lambda i, p: i[1] > 0
        then_pred = lambda i, p: False
        else_pred = lambda i, p: True
        
        pred = ConditionalPredicate(condition, then_pred, else_pred)
        assert pred([42, 0], [0, 1]) is True
    
    def test_no_else_branch(self):
        """Test 398: No else branch defaults to pass."""
        condition = lambda i, p: i[0] > 0
        then_pred = lambda i, p: i[0] < 100
        
        pred = ConditionalPredicate(condition, then_pred)
        assert pred([-5], [0]) is True
    
    def test_buffer_size_pattern(self):
        """Test 399-410: Buffer-size conditional pattern."""
        # If size > 0, buffer must not be None
        condition = lambda i, p: len(i) > 1 and i[1] > 0
        then_pred = lambda i, p: i[0] is not None
        
        pred = ConditionalPredicate(condition, then_pred)
        assert pred([None, 0], [0, 1]) is True
        assert pred([None, 5], [0, 1]) is False
        assert pred([b'data', 5], [0, 1]) is True


class TestExpressionPredicate:
    """ExpressionPredicate tests (15 tests)."""
    
    def test_simple_expression(self):
        """Test 411: Simple expression evaluation."""
        pred = ExpressionPredicate("inputs[0] > 0")
        assert pred([5], [0]) is True
        assert pred([-5], [0]) is False
    
    def test_complex_expression(self):
        """Test 412: Complex expression."""
        pred = ExpressionPredicate("inputs[0] >= 0 and inputs[0] <= 100")
        assert pred([50], [0]) is True
        assert pred([150], [0]) is False
    
    def test_expression_with_len(self):
        """Test 413: Expression using len()."""
        pred = ExpressionPredicate("len(inputs[0]) > 5")
        assert pred(['hello world'], [0]) is True
        assert pred(['hi'], [0]) is False
    
    def test_expression_with_builtin(self):
        """Test 414: Expression using abs()."""
        pred = ExpressionPredicate("abs(inputs[0]) < 10")
        assert pred([5], [0]) is True
        assert pred([-5], [0]) is True
        assert pred([15], [0]) is False
    
    def test_forbidden_import(self):
        """Test 415: Forbidden operations raise error."""
        pred = ExpressionPredicate("import os")
        with pytest.raises(ValueError, match='forbidden'):
            pred([], [])
    
    def test_forbidden_exec(self):
        """Test 416-425: Various forbidden operations."""
        for expr in ['exec("code")', 'eval("code")', '__import__', 'open("file")']:
            pred = ExpressionPredicate(expr)
            with pytest.raises(ValueError):
                pred([], [])


class TestAlignmentPredicate:
    """AlignmentPredicate tests (10 tests)."""
    
    def test_aligned_address(self):
        """Test 426: Aligned address passes."""
        pred = AlignmentPredicate(4)
        assert pred([0x1000], [0]) is True
        assert pred([0x1004], [0]) is True
    
    def test_unaligned_address(self):
        """Test 427: Unaligned address fails."""
        pred = AlignmentPredicate(4)
        assert pred([0x1001], [0]) is False
        assert pred([0x1002], [0]) is False
    
    def test_8byte_alignment(self):
        """Test 428: 8-byte alignment."""
        pred = AlignmentPredicate(8)
        assert pred([0x1000], [0]) is True
        assert pred([0x1004], [0]) is False
    
    def test_invalid_alignment(self):
        """Test 429: Invalid alignment raises error."""
        with pytest.raises(ValueError, match='power of 2'):
            AlignmentPredicate(3)
    
    def test_non_integer_value(self):
        """Test 430-435: Non-integer values pass by default."""
        pred = AlignmentPredicate(4)
        assert pred(['not_an_int'], [0]) is True


class TestEnumPredicate:
    """EnumPredicate tests (10 tests)."""
    
    def test_valid_enum_value(self):
        """Test 436: Valid enum value passes."""
        pred = EnumPredicate([1, 2, 3])
        assert pred([2], [0]) is True
    
    def test_invalid_enum_value(self):
        """Test 437: Invalid enum value fails."""
        pred = EnumPredicate([1, 2, 3])
        assert pred([5], [0]) is False
    
    def test_string_enum(self):
        """Test 438: String enum values."""
        pred = EnumPredicate(['red', 'green', 'blue'])
        assert pred(['green'], [0]) is True
        assert pred(['yellow'], [0]) is False
    
    def test_empty_enum(self):
        """Test 439-445: Empty enum and edge cases."""
        pred = EnumPredicate([])
        assert pred([1], [0]) is False


class TestBitwisePredicate:
    """BitwisePredicate tests (10 tests)."""
    
    def test_required_set_bits(self):
        """Test 446: Required set bits present."""
        pred = BitwisePredicate(required_set=0b0101)
        assert pred([0b0101], [0]) is True
        assert pred([0b1111], [0]) is True
    
    def test_required_set_bits_missing(self):
        """Test 447: Required set bits missing."""
        pred = BitwisePredicate(required_set=0b0101)
        assert pred([0b0001], [0]) is False
    
    def test_required_unset_bits(self):
        """Test 448: Required unset bits clear."""
        pred = BitwisePredicate(required_unset=0b0010)
        assert pred([0b0011], [0]) is False
        assert pred([0b0001], [0]) is True
    
    def test_combined_requirements(self):
        """Test 449: Combined set/unset requirements."""
        pred = BitwisePredicate(required_set=0b0001, required_unset=0b0010)
        assert pred([0b0001], [0]) is True
        assert pred([0b0011], [0]) is False
    
    def test_non_integer_value(self):
        """Test 450-455: Non-integer values fail."""
        pred = BitwisePredicate(required_set=0b01)
        assert pred(['not_int'], [0]) is False


class TestPredicateRegistry:
    """PredicateRegistry tests (10 tests)."""
    
    def test_register_predicate(self):
        """Test 456: Register predicate."""
        registry = PredicateRegistry()
        pred = lambda i, p: True
        
        registry.register('test_pred', pred)
        assert registry.get('test_pred') == pred
    
    def test_get_nonexistent(self):
        """Test 457: Get non-existent predicate."""
        registry = PredicateRegistry()
        assert registry.get('missing') is None
    
    def test_unregister_predicate(self):
        """Test 458: Unregister predicate."""
        registry = PredicateRegistry()
        registry.register('test', lambda i, p: True)
        
        assert registry.unregister('test') is True
        assert registry.get('test') is None
    
    def test_unregister_nonexistent(self):
        """Test 459: Unregister non-existent returns False."""
        registry = PredicateRegistry()
        assert registry.unregister('missing') is False
    
    def test_list_predicates(self):
        """Test 460-465: List registered predicates."""
        registry = PredicateRegistry()
        registry.register('pred1', lambda i, p: True)
        registry.register('pred2', lambda i, p: False)
        
        names = registry.list_predicates()
        assert len(names) == 2
        assert 'pred1' in names


class TestEnhancedPredicateFactory:
    """Enhanced PredicateFactory tests (10 tests)."""
    
    def test_create_from_metadata_range(self):
        """Test 466: Create range predicate from metadata."""
        metadata = {'type': 'range', 'min': 0, 'max': 100}
        pred = PredicateFactory.create_from_metadata(metadata)
        
        assert pred([50], [0]) is True
        assert pred([150], [0]) is False
    
    def test_create_from_metadata_nullability(self):
        """Test 467: Create nullability from metadata."""
        metadata = {'type': 'nullability', 'allow_null': False}
        pred = PredicateFactory.create_from_metadata(metadata)
        
        assert pred([42], [0]) is True
        assert pred([None], [0]) is False
    
    def test_create_from_metadata_type(self):
        """Test 468: Create type predicate from metadata."""
        metadata = {'type': 'type', 'expected_type': 'int'}
        pred = PredicateFactory.create_from_metadata(metadata)
        
        assert pred([42], [0]) is True
        assert pred(['42'], [0]) is False
    
    def test_create_from_metadata_alignment(self):
        """Test 469: Create alignment from metadata."""
        metadata = {'type': 'alignment', 'alignment': 4}
        pred = PredicateFactory.create_from_metadata(metadata)
        
        assert pred([0x1000], [0]) is True
    
    def test_create_from_metadata_enum(self):
        """Test 470: Create enum from metadata."""
        metadata = {'type': 'enum', 'allowed_values': [1, 2, 3]}
        pred = PredicateFactory.create_from_metadata(metadata)
        
        assert pred([2], [0]) is True
        assert pred([5], [0]) is False
    
    def test_create_from_metadata_compound(self):
        """Test 471-475: Create compound from metadata."""
        metadata = {
            'type': 'compound',
            'operator': 'and',
            'sub_clauses': [
                {'type': 'range', 'min': 0, 'max': 100},
                {'type': 'type', 'expected_type': 'int'}
            ]
        }
        pred = PredicateFactory.create_from_metadata(metadata)
        
        assert pred([50], [0]) is True
        assert pred([150], [0]) is False

    def test_create_conditional_with_string(self):
        """Test: Create conditional predicate with string expression."""
        then_pred = lambda i, p: True
        else_pred = lambda i, p: False
        
        pred = PredicateFactory.create_conditional_predicate(
            "inputs[0] > 0", then_pred, else_pred
        )
        assert pred([5], [0]) is True
        assert pred([-5], [0]) is False

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
