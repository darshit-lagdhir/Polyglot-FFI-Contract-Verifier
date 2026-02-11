"""
Unit tests for Module 06: Clause Types
Test suite (90 tests)
"""

from module_06_contract_schema.contract_entities import (
    SubjectReference,
    SubjectKind,
    ClauseType,
    Severity,
)
from module_06_contract_schema.clause_types import (
    LayoutClause,
    SizeClause,
    AlignmentClause,
    NullabilityClause,
    OwnershipClause,
    LifetimeClause,
    RelationalClause,
    CallingConventionClause,
    ABICompatibilityClause,
    create_clause_from_type,
)
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules"))


class TestLayoutClause:
    """Test LayoutClause implementation."""

    def test_creation(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Point")

        clause = LayoutClause(
            clause_id="layout_001", subject_reference=ref, expected_size=8, expected_alignment=4
        )

        assert clause.clause_type == ClauseType.LAYOUT
        assert clause.expected_size == 8
        assert clause.expected_alignment == 4

    def test_with_field_layout(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Point")

        clause = LayoutClause(
            clause_id="layout_002",
            subject_reference=ref,
            expected_size=8,
            expected_alignment=4,
            field_layout={"x": 0, "y": 4},
        )

        assert len(clause.field_layout) == 2
        assert clause.field_layout["x"] == 0
        assert clause.field_layout["y"] == 4

    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Point")

        clause = LayoutClause(
            clause_id="layout_003",
            subject_reference=ref,
            expected_size=16,
            expected_alignment=8,
            field_layout={"a": 0, "b": 8},
        )

        errors = clause.validate_parameters()

        assert len(errors) == 0

    def test_validation_invalid_size(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Bad")

        clause = LayoutClause(
            clause_id="layout_bad", subject_reference=ref, expected_size=-1, expected_alignment=4
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0
        assert any("size" in e.lower() for e in errors)

    def test_validation_alignment_not_power_of_2(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Bad")

        clause = LayoutClause(
            clause_id="layout_bad2", subject_reference=ref, expected_size=10, expected_alignment=3
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0
        assert any("power of 2" in e for e in errors)

    def test_validation_negative_offset(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Bad")

        clause = LayoutClause(
            clause_id="layout_bad3",
            subject_reference=ref,
            expected_size=8,
            expected_alignment=4,
            field_layout={"x": -1},
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_to_generic_clause(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Point")

        clause = LayoutClause(
            clause_id="layout_gen", subject_reference=ref, expected_size=8, expected_alignment=4
        )

        generic = clause.to_generic_clause()

        assert generic.clause_type == ClauseType.LAYOUT
        assert len(generic.constraint_parameters) == 4

    def test_enforce_padding_flag(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Point")

        clause = LayoutClause(
            clause_id="layout_004",
            subject_reference=ref,
            expected_size=8,
            expected_alignment=4,
            enforce_padding=False,
        )

        assert clause.enforce_padding is False


class TestSizeClause:
    """Test SizeClause implementation."""

    def test_exact_size(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(
            clause_id="size_001", subject_reference=ref, size_kind="exact", size_value=256
        )

        assert clause.size_kind == "exact"
        assert clause.size_value == 256

    def test_minimum_size(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(
            clause_id="size_002", subject_reference=ref, size_kind="minimum", size_value=128
        )

        assert clause.size_kind == "minimum"
        assert clause.size_value == 128

    def test_maximum_size(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(
            clause_id="size_003", subject_reference=ref, size_kind="maximum", size_value=1024
        )

        assert clause.size_kind == "maximum"
        assert clause.size_value == 1024

    def test_relational_size(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(
            clause_id="size_004",
            subject_reference=ref,
            size_kind="relational",
            size_reference="length_param",
            multiplier=4,
        )

        assert clause.size_kind == "relational"
        assert clause.size_reference == "length_param"
        assert clause.multiplier == 4

    def test_validation_invalid_kind(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(clause_id="size_bad", subject_reference=ref, size_kind="invalid")

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_missing_value_for_exact(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(
            clause_id="size_bad2", subject_reference=ref, size_kind="exact", size_value=None
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_missing_reference_for_relational(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(
            clause_id="size_bad3",
            subject_reference=ref,
            size_kind="relational",
            size_reference=None,
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_negative_size(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(
            clause_id="size_bad4", subject_reference=ref, size_kind="exact", size_value=-10
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_to_generic_clause(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = SizeClause(
            clause_id="size_gen", subject_reference=ref, size_kind="exact", size_value=100
        )

        generic = clause.to_generic_clause()

        assert generic.clause_type == ClauseType.SIZE


class TestAlignmentClause:
    """Test AlignmentClause implementation."""

    def test_creation(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = AlignmentClause(clause_id="align_001", subject_reference=ref, required_alignment=8)

        assert clause.required_alignment == 8
        assert clause.context == "parameter"

    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = AlignmentClause(
            clause_id="align_002", subject_reference=ref, required_alignment=16
        )

        errors = clause.validate_parameters()

        assert len(errors) == 0

    def test_validation_not_power_of_2(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = AlignmentClause(clause_id="align_bad", subject_reference=ref, required_alignment=7)

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_too_large(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = AlignmentClause(
            clause_id="align_bad2", subject_reference=ref, required_alignment=256
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_different_contexts(self):
        ref = SubjectReference(SubjectKind.RETURN_VALUE, "result")

        clause = AlignmentClause(
            clause_id="align_003", subject_reference=ref, required_alignment=8, context="return"
        )

        assert clause.context == "return"

    def test_validation_invalid_context(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = AlignmentClause(
            clause_id="align_bad3", subject_reference=ref, required_alignment=8, context="invalid"
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0


class TestNullabilityClause:
    """Test NullabilityClause implementation."""

    def test_non_nullable(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = NullabilityClause(clause_id="null_001", subject_reference=ref, nullable=False)

        assert clause.nullable is False

    def test_nullable(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "optional_ptr")

        clause = NullabilityClause(clause_id="null_002", subject_reference=ref, nullable=True)

        assert clause.nullable is True

    def test_conditional_nullability(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = NullabilityClause(
            clause_id="null_003", subject_reference=ref, nullable=True, conditional="if flag is set"
        )

        assert clause.conditional == "if flag is set"

    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = NullabilityClause(clause_id="null_004", subject_reference=ref, nullable=False)

        errors = clause.validate_parameters()

        assert len(errors) == 0

    def test_validation_empty_conditional(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = NullabilityClause(
            clause_id="null_bad", subject_reference=ref, nullable=True, conditional=""
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_to_generic_clause(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = NullabilityClause(clause_id="null_gen", subject_reference=ref, nullable=False)

        generic = clause.to_generic_clause()

        assert generic.clause_type == ClauseType.NULLABILITY


class TestOwnershipClause:
    """Test OwnershipClause implementation."""

    def test_caller_owned(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = OwnershipClause(
            clause_id="own_001",
            subject_reference=ref,
            ownership_mode="caller_owned",
            allocation_responsibility="caller",
            deallocation_responsibility="caller",
        )

        assert clause.ownership_mode == "caller_owned"

    def test_transferred_ownership(self):
        ref = SubjectReference(SubjectKind.RETURN_VALUE, "new_object")

        clause = OwnershipClause(
            clause_id="own_002",
            subject_reference=ref,
            ownership_mode="transferred",
            allocation_responsibility="callee",
            deallocation_responsibility="caller",
        )

        assert clause.ownership_mode == "transferred"

    def test_callee_owned(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "internal_buffer")

        clause = OwnershipClause(
            clause_id="own_003",
            subject_reference=ref,
            ownership_mode="callee_owned",
            allocation_responsibility="callee",
            deallocation_responsibility="callee",
        )

        assert clause.ownership_mode == "callee_owned"

    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = OwnershipClause(
            clause_id="own_004",
            subject_reference=ref,
            ownership_mode="caller_owned",
            allocation_responsibility="caller",
            deallocation_responsibility="caller",
        )

        errors = clause.validate_parameters()

        assert len(errors) == 0

    def test_validation_invalid_mode(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = OwnershipClause(
            clause_id="own_bad", subject_reference=ref, ownership_mode="invalid_mode"
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_transferred_without_allocation(self):
        ref = SubjectReference(SubjectKind.RETURN_VALUE, "obj")

        clause = OwnershipClause(
            clause_id="own_bad2",
            subject_reference=ref,
            ownership_mode="transferred",
            allocation_responsibility="none",
            deallocation_responsibility="caller",
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0


class TestLifetimeClause:
    """Test LifetimeClause implementation."""

    def test_call_scoped(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "temp_ptr")

        clause = LifetimeClause(clause_id="life_001", subject_reference=ref, lifetime_scope="call")

        assert clause.lifetime_scope == "call"

    def test_global_lifetime(self):
        ref = SubjectReference(SubjectKind.RETURN_VALUE, "static_ptr")

        clause = LifetimeClause(
            clause_id="life_002", subject_reference=ref, lifetime_scope="global"
        )

        assert clause.lifetime_scope == "global"

    def test_context_lifetime(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ctx_ptr")

        clause = LifetimeClause(
            clause_id="life_003", subject_reference=ref, lifetime_scope="context"
        )

        assert clause.lifetime_scope == "context"

    def test_with_invalidation_event(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = LifetimeClause(
            clause_id="life_004",
            subject_reference=ref,
            lifetime_scope="context",
            invalidation_event="next_call",
        )

        assert clause.invalidation_event == "next_call"

    def test_validation_invalid_scope(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = LifetimeClause(
            clause_id="life_bad", subject_reference=ref, lifetime_scope="invalid"
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = LifetimeClause(clause_id="life_005", subject_reference=ref, lifetime_scope="call")

        errors = clause.validate_parameters()

        assert len(errors) == 0


class TestRelationalClause:
    """Test RelationalClause implementation."""

    def test_buffer_length_relation(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "process")

        clause = RelationalClause(
            clause_id="rel_001",
            subject_reference=ref,
            relation_kind="buffer_length",
            primary_reference="buffer_param",
            secondary_reference="length_param",
        )

        assert clause.relation_kind == "buffer_length"
        assert clause.primary_reference == "buffer_param"
        assert clause.secondary_reference == "length_param"

    def test_paired_params(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = RelationalClause(
            clause_id="rel_002",
            subject_reference=ref,
            relation_kind="paired_params",
            primary_reference="param1",
            secondary_reference="param2",
        )

        assert clause.relation_kind == "paired_params"

    def test_dependent_null(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = RelationalClause(
            clause_id="rel_003",
            subject_reference=ref,
            relation_kind="dependent_null",
            primary_reference="ptr1",
            secondary_reference="ptr2",
        )

        assert clause.relation_kind == "dependent_null"

    def test_with_expression(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = RelationalClause(
            clause_id="rel_004",
            subject_reference=ref,
            relation_kind="buffer_length",
            primary_reference="buf",
            secondary_reference="len",
            relation_expression="buf_size == len * sizeof(int)",
        )

        assert clause.relation_expression is not None

    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = RelationalClause(
            clause_id="rel_005",
            subject_reference=ref,
            relation_kind="buffer_length",
            primary_reference="buf",
            secondary_reference="len",
        )

        errors = clause.validate_parameters()

        assert len(errors) == 0

    def test_validation_missing_references(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = RelationalClause(
            clause_id="rel_bad", subject_reference=ref, relation_kind="buffer_length"
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_same_references(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = RelationalClause(
            clause_id="rel_bad2",
            subject_reference=ref,
            relation_kind="buffer_length",
            primary_reference="same",
            secondary_reference="same",
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_invalid_kind(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = RelationalClause(
            clause_id="rel_bad3",
            subject_reference=ref,
            relation_kind="invalid",
            primary_reference="a",
            secondary_reference="b",
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0


class TestCallingConventionClause:
    """Test CallingConventionClause implementation."""

    def test_cdecl(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = CallingConventionClause(
            clause_id="cc_001", subject_reference=ref, required_convention="cdecl"
        )

        assert clause.required_convention == "cdecl"
        assert clause.strict is True

    def test_stdcall(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "callback")

        clause = CallingConventionClause(
            clause_id="cc_002", subject_reference=ref, required_convention="stdcall", strict=True
        )

        assert clause.required_convention == "stdcall"

    def test_fastcall(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "fast_func")

        clause = CallingConventionClause(
            clause_id="cc_003", subject_reference=ref, required_convention="fastcall", strict=False
        )

        assert clause.required_convention == "fastcall"
        assert clause.strict is False

    def test_validation_invalid_convention(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = CallingConventionClause(
            clause_id="cc_bad", subject_reference=ref, required_convention="invalid"
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = CallingConventionClause(
            clause_id="cc_004", subject_reference=ref, required_convention="sysv"
        )

        errors = clause.validate_parameters()

        assert len(errors) == 0


class TestABICompatibilityClause:
    """Test ABICompatibilityClause implementation."""

    def test_strict_compatibility(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = ABICompatibilityClause(
            clause_id="abi_001",
            subject_reference=ref,
            compatible_versions=["1.0.0"],
            compatibility_mode="strict",
        )

        assert len(clause.compatible_versions) == 1
        assert clause.compatibility_mode == "strict"

    def test_backward_compatibility(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = ABICompatibilityClause(
            clause_id="abi_002",
            subject_reference=ref,
            compatible_versions=["2.0.0", "2.1.0"],
            compatibility_mode="backward",
        )

        assert len(clause.compatible_versions) == 2
        assert clause.compatibility_mode == "backward"

    def test_forward_compatibility(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = ABICompatibilityClause(
            clause_id="abi_003",
            subject_reference=ref,
            compatible_versions=["3.0.0"],
            compatibility_mode="forward",
        )

        assert clause.compatibility_mode == "forward"

    def test_validation_empty_versions(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = ABICompatibilityClause(
            clause_id="abi_bad",
            subject_reference=ref,
            compatible_versions=[],
            compatibility_mode="strict",
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_invalid_mode(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = ABICompatibilityClause(
            clause_id="abi_bad2",
            subject_reference=ref,
            compatible_versions=["1.0.0"],
            compatibility_mode="invalid",
        )

        errors = clause.validate_parameters()

        assert len(errors) > 0

    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        clause = ABICompatibilityClause(
            clause_id="abi_004",
            subject_reference=ref,
            compatible_versions=["1.0.0", "1.1.0"],
            compatibility_mode="backward",
        )

        errors = clause.validate_parameters()

        assert len(errors) == 0


class TestClauseFactory:
    """Test clause factory function."""

    def test_create_layout_clause(self):
        ref = SubjectReference(SubjectKind.STRUCTURE, "Point")

        clause = create_clause_from_type(
            ClauseType.LAYOUT, "factory_001", ref, expected_size=8, expected_alignment=4
        )

        assert isinstance(clause, LayoutClause)
        assert clause.expected_size == 8

    def test_create_size_clause(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "buffer")

        clause = create_clause_from_type(
            ClauseType.SIZE, "factory_002", ref, size_kind="exact", size_value=256
        )

        assert isinstance(clause, SizeClause)
        assert clause.size_value == 256

    def test_create_nullability_clause(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = create_clause_from_type(ClauseType.NULLABILITY, "factory_003", ref, nullable=False)

        assert isinstance(clause, NullabilityClause)
        assert clause.nullable is False

    def test_create_ownership_clause(self):
        ref = SubjectReference(SubjectKind.RETURN_VALUE, "obj")

        clause = create_clause_from_type(
            ClauseType.OWNERSHIP, "factory_004", ref, ownership_mode="transferred"
        )

        assert isinstance(clause, OwnershipClause)

    def test_create_alignment_clause(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "ptr")

        clause = create_clause_from_type(
            ClauseType.ALIGNMENT, "factory_005", ref, required_alignment=16
        )

        assert isinstance(clause, AlignmentClause)

    def test_unsupported_clause_type(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")

        # Use a clause type that's not in the map
        with pytest.raises(ValueError):
            create_clause_from_type(
                ClauseType.INITIALIZATION,
                "factory_bad",
                ref,  # Not implemented yet
            )


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
