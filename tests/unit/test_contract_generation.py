"""
Unit tests for the Contract Generation system.
Ensures correct heuristic inference and clause synthesis from IR artifacts.
"""

from module_06_contract_schema.clause_types import (
    LayoutClause,
    NullabilityClause,
    OwnershipClause,
    RelationalClause,
)
from module_06_contract_schema.contract_generation import (
    GenerationConfig,
    GeneratedClause,
    NamingPatternMatcher,
    LayoutClauseGenerator,
    NullabilityClauseGenerator,
    OwnershipClauseGenerator,
    RelationalClauseGenerator,
    ContractGenerator,
    MockIRType,
    MockIRFunction,
)
import pytest
from pathlib import Path
import sys

# Ensure the modules directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules"))


class TestGenerationConfig:
    """Validation for generation configuration objects."""

    def test_default_config(self):
        config = GenerationConfig()
        assert config.confidence_threshold == 0.5
        assert config.generate_layout is True
        assert config.generate_nullability is True

    def test_custom_thresholds(self):
        config = GenerationConfig(confidence_threshold=0.7, include_low_confidence=False)
        assert config.confidence_threshold == 0.7
        assert config.include_low_confidence is False


class TestNamingPatternMatcher:
    """Validation for naming-based intent inference."""

    @pytest.fixture
    def matcher(self):
        return NamingPatternMatcher(GenerationConfig())

    def test_nullability_detection(self, matcher):
        assert matcher.is_nullable_name("optional_ptr")
        assert matcher.is_nullable_name("maybe_data")
        assert not matcher.is_nullable_name("strict_value")

    def test_allocation_detection(self, matcher):
        assert matcher.is_allocation_function("create_instance")
        assert matcher.is_allocation_function("alloc_memory")
        assert not matcher.is_allocation_function("view_data")

    def test_buffer_pair_matching(self, matcher):
        params = [
            {"name": "data_ptr", "is_pointer": True},
            {"name": "data_size", "is_integer": True},
        ]
        pair = matcher.find_buffer_length_pair(params)
        assert pair == ("data_ptr", "data_size")


class TestLayoutClauseGenerator:
    """Validation for layout requirement derivation."""

    @pytest.fixture
    def generator(self):
        return LayoutClauseGenerator()

    def test_structural_layout_generation(self, generator):
        ir_type = MockIRType("struct_1", "Point", 8, 4)
        result = generator.generate(ir_type)
        assert result.confidence == 1.0
        assert result.clause.expected_size == 8
        assert result.clause.clause_id == "layout_Point"


class TestNullabilityClauseGenerator:
    @pytest.fixture
    def generator(self):
        return NullabilityClauseGenerator(GenerationConfig())

    def test_parameter_nullability_inference(self, generator):
        # Default non-null
        res_std = generator.generate_for_parameter("do_work", "ptr", "p1")
        assert res_std.clause.nullable is False

        # Explicitly nullable naming
        res_opt = generator.generate_for_parameter("do_work", "opt_ptr", "p2")
        assert res_opt.clause.nullable is True


class TestOwnershipClauseGenerator:
    """Validation for memory ownership lifecycle inference."""

    @pytest.fixture
    def generator(self):
        return OwnershipClauseGenerator(GenerationConfig())

    def test_return_ownership_transfer(self, generator):
        func = MockIRFunction("f1", "create_buffer", return_type="char*")
        res = generator.generate_for_return(func)
        assert res.clause.ownership_mode == "transferred"
        assert res.clause.deallocation_responsibility == "caller"

    def test_borrow_ownership_inference(self, generator):
        func = MockIRFunction("f2", "peek_buffer", return_type="char*")
        res = generator.generate_for_return(func)
        assert res.clause.ownership_mode == "callee_owned"


class TestRelationalClauseGenerator:
    @pytest.fixture
    def generator(self):
        return RelationalClauseGenerator(GenerationConfig())

    def test_buffer_relation_detection(self, generator):
        func = MockIRFunction(
            "f3",
            "process",
            parameters=[{"name": "buf", "is_pointer": True}, {"name": "len", "is_integer": True}],
        )
        res = generator.generate_for_function(func)
        assert res.clause.relation_kind == "buffer_length"
        assert res.clause.primary_reference == "buf"


class TestContractGenerator:
    """High-level orchestration testing."""

    def test_contract_synthesis_flow(self):
        generator = ContractGenerator()
        contract = generator.generate(None, "v1_interface")
        assert contract.header.target_interface_id == "v1_interface"
        assert len(contract.clauses) > 0  # Initial Point structure gen


if __name__ == "__main__":
    pytest.main([__file__])
