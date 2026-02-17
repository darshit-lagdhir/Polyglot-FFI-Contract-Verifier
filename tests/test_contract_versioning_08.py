""" Tests for Contract Versioning - Prompt 8/20 Function Signature Diff Analysis & Parameter Change Detection

Testing Level: HARDEST (90 comprehensive tests) """

import pytest
import json

from modules.module_06_contract_schema.contract_versioning import (
    ChangeSeverity,
    DetailedChange,
    EntityDiff,
    FunctionSignatureAnalyzer,
    FunctionCatalogAnalyzer,
)


# ============================================================================
# TEST FUNCTION SIGNATURE ANALYZER - RETURN TYPE (15 TESTS)
# ============================================================================
class TestReturnTypeChanges:
    """Test return type change detection."""

    @pytest.fixture
    def analyzer(self):
        return FunctionSignatureAnalyzer()

    def test_return_type_changed_breaking(self, analyzer):
        """Test 1: Return type change is BREAKING."""
        baseline = {"return_type": "int32_t", "parameters": []}
        candidate = {"return_type": "int64_t", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "get_value")

        assert diff.has_breaking_changes()
        changes = [c for c in diff.changes if c.change_type == "return_type_changed"]
        assert len(changes) == 1
        assert changes[0].old_value == "int32_t"
        assert changes[0].new_value == "int64_t"

    def test_return_type_unchanged(self, analyzer):
        """Test 2: Unchanged return type no change."""
        baseline = {"return_type": "int32_t", "parameters": []}
        candidate = {"return_type": "int32_t", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        return_changes = [c for c in diff.changes if c.change_type == "return_type_changed"]
        assert len(return_changes) == 0

    def test_return_type_void_to_value(self, analyzer):
        """Test 3: void to value is BREAKING."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "int32_t", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_return_type_value_to_void(self, analyzer):
        """Test 4: value to void is BREAKING."""
        baseline = {"return_type": "int32_t", "parameters": []}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_return_type_pointer_to_value(self, analyzer):
        """Test 5: pointer to value is BREAKING."""
        baseline = {"return_type": "Point*", "parameters": []}
        candidate = {"return_type": "Point", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_return_type_int_to_float(self, analyzer):
        """Test 6: int to float is BREAKING."""
        baseline = {"return_type": "int32_t", "parameters": []}
        candidate = {"return_type": "float", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_return_type_description(self, analyzer):
        """Test 7: Return type change has description."""
        baseline = {"return_type": "int32_t", "parameters": []}
        candidate = {"return_type": "int64_t", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        changes = [c for c in diff.changes if c.change_type == "return_type_changed"]
        assert "int32_t" in changes[0].description
        assert "int64_t" in changes[0].description

    def test_return_type_location(self, analyzer):
        """Test 8: Return type change has location."""
        baseline = {"return_type": "int32_t", "parameters": []}
        candidate = {"return_type": "int64_t", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        changes = [c for c in diff.changes if c.change_type == "return_type_changed"]
        assert changes[0].location == "return type"

    def test_return_type_default_void(self, analyzer):
        """Test 9: Missing return_type defaults to void."""
        baseline = {"parameters": []}
        candidate = {"parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        return_changes = [c for c in diff.changes if c.change_type == "return_type_changed"]
        assert len(return_changes) == 0

    def test_return_type_entity_id(self, analyzer):
        """Test 10: Return type change includes entity_id."""
        baseline = {"return_type": "int32_t", "parameters": []}
        candidate = {"return_type": "int64_t", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "my_func")

        changes = [c for c in diff.changes if c.change_type == "return_type_changed"]
        assert changes[0].entity_id == "my_func"

    def test_return_type_severity_breaking(self, analyzer):
        """Test 11: Return type change is BREAKING severity."""
        baseline = {"return_type": "int32_t", "parameters": []}
        candidate = {"return_type": "int64_t", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        changes = [c for c in diff.changes if c.change_type == "return_type_changed"]
        assert changes[0].severity == ChangeSeverity.BREAKING

    def test_return_type_char_to_int(self, analyzer):
        """Test 12: char to int is BREAKING."""
        baseline = {"return_type": "char", "parameters": []}
        candidate = {"return_type": "int", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_return_type_unsigned_to_signed(self, analyzer):
        """Test 13: unsigned to signed is BREAKING."""
        baseline = {"return_type": "uint32_t", "parameters": []}
        candidate = {"return_type": "int32_t", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_return_type_struct_change(self, analyzer):
        """Test 14: struct type change is BREAKING."""
        baseline = {"return_type": "Point", "parameters": []}
        candidate = {"return_type": "Vector", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_return_type_const_qualifier(self, analyzer):
        """Test 15: const qualifier change."""
        baseline = {"return_type": "const char*", "parameters": []}
        candidate = {"return_type": "char*", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()


# ============================================================================
# TEST CALLING CONVENTION CHANGES (10 TESTS)
# ============================================================================
class TestCallingConventionChanges:
    """Test calling convention change detection."""

    @pytest.fixture
    def analyzer(self):
        return FunctionSignatureAnalyzer()

    def test_calling_convention_changed(self, analyzer):
        """Test 16: Calling convention change is BREAKING."""
        baseline = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "void", "calling_convention": "stdcall", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()
        changes = [c for c in diff.changes if c.change_type == "calling_convention_changed"]
        assert len(changes) == 1

    def test_calling_convention_unchanged(self, analyzer):
        """Test 17: Unchanged calling convention."""
        baseline = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        conv_changes = [c for c in diff.changes if c.change_type == "calling_convention_changed"]
        assert len(conv_changes) == 0

    def test_calling_convention_default_cdecl(self, analyzer):
        """Test 18: Missing calling_convention defaults to cdecl."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        conv_changes = [c for c in diff.changes if c.change_type == "calling_convention_changed"]
        assert len(conv_changes) == 0

    def test_calling_convention_cdecl_to_fastcall(self, analyzer):
        """Test 19: cdecl to fastcall is BREAKING."""
        baseline = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "void", "calling_convention": "fastcall", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_calling_convention_values(self, analyzer):
        """Test 20: Calling convention old/new values set."""
        baseline = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "void", "calling_convention": "stdcall", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        changes = [c for c in diff.changes if c.change_type == "calling_convention_changed"]
        assert changes[0].old_value == "cdecl"
        assert changes[0].new_value == "stdcall"

    def test_calling_convention_severity(self, analyzer):
        """Test 21: Calling convention change is BREAKING."""
        baseline = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "void", "calling_convention": "stdcall", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        changes = [c for c in diff.changes if c.change_type == "calling_convention_changed"]
        assert changes[0].severity == ChangeSeverity.BREAKING

    def test_calling_convention_description(self, analyzer):
        """Test 22: Calling convention change has description."""
        baseline = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "void", "calling_convention": "stdcall", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        changes = [c for c in diff.changes if c.change_type == "calling_convention_changed"]
        assert "cdecl" in changes[0].description
        assert "stdcall" in changes[0].description

    def test_calling_convention_thiscall(self, analyzer):
        """Test 23: thiscall convention."""
        baseline = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "void", "calling_convention": "thiscall", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_calling_convention_vectorcall(self, analyzer):
        """Test 24: vectorcall convention."""
        baseline = {"return_type": "void", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "void", "calling_convention": "vectorcall", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_calling_convention_combined_with_return_type(self, analyzer):
        """Test 25: Multiple changes detected."""
        baseline = {"return_type": "int32_t", "calling_convention": "cdecl", "parameters": []}
        candidate = {"return_type": "int64_t", "calling_convention": "stdcall", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert len(diff.changes) == 2
        assert diff.has_breaking_changes()


# ============================================================================
# TEST PARAMETER COUNT CHANGES (10 TESTS)
# ============================================================================
class TestParameterCountChanges:
    """Test parameter count change detection."""

    @pytest.fixture
    def analyzer(self):
        return FunctionSignatureAnalyzer()

    def test_parameter_count_increased(self, analyzer):
        """Test 26: Parameter count increase is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()
        count_changes = [c for c in diff.changes if c.change_type == "parameter_count_changed"]
        assert len(count_changes) == 1

    def test_parameter_count_decreased(self, analyzer):
        """Test 27: Parameter count decrease is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_parameter_count_unchanged(self, analyzer):
        """Test 28: Unchanged parameter count."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        count_changes = [c for c in diff.changes if c.change_type == "parameter_count_changed"]
        assert len(count_changes) == 0

    def test_parameter_count_zero_to_one(self, analyzer):
        """Test 29: Zero to one parameter is BREAKING."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_parameter_count_one_to_zero(self, analyzer):
        """Test 30: One to zero parameters is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_parameter_count_values(self, analyzer):
        """Test 31: Parameter count old/new values."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        count_changes = [c for c in diff.changes if c.change_type == "parameter_count_changed"]
        assert count_changes[0].old_value == 1
        assert count_changes[0].new_value == 2

    def test_parameter_count_large_increase(self, analyzer):
        """Test 32: Large parameter count increase."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": f"p{i}", "type": "int32_t"} for i in range(10)]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        count_changes = [c for c in diff.changes if c.change_type == "parameter_count_changed"]
        assert count_changes[0].old_value == 0
        assert count_changes[0].new_value == 10

    def test_parameter_count_description(self, analyzer):
        """Test 33: Parameter count change description."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        count_changes = [c for c in diff.changes if c.change_type == "parameter_count_changed"]
        assert "0" in count_changes[0].description
        assert "1" in count_changes[0].description

    def test_parameter_count_severity(self, analyzer):
        """Test 34: Parameter count change is BREAKING."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        count_changes = [c for c in diff.changes if c.change_type == "parameter_count_changed"]
        assert count_changes[0].severity == ChangeSeverity.BREAKING

    def test_parameter_count_default_empty(self, analyzer):
        """Test 35: Missing parameters defaults to empty list."""
        baseline = {"return_type": "void"}
        candidate = {"return_type": "void"}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        count_changes = [c for c in diff.changes if c.change_type == "parameter_count_changed"]
        assert len(count_changes) == 0


# ============================================================================
# TEST PARAMETER ADDITIONS (10 TESTS)
# ============================================================================
class TestParameterAdditions:
    """Test parameter addition detection."""

    @pytest.fixture
    def analyzer(self):
        return FunctionSignatureAnalyzer()

    def test_parameter_added_breaking(self, analyzer):
        """Test 36: Parameter added is BREAKING."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "new_param", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert len(added) == 1
        assert added[0].severity == ChangeSeverity.BREAKING

    def test_parameter_added_description(self, analyzer):
        """Test 37: Parameter added has description."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "flags", "type": "uint32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert "flags" in added[0].description
        assert "uint32_t" in added[0].description

    def test_parameter_added_location(self, analyzer):
        """Test 38: Parameter added has location."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "param", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert "parameter[0]" in added[0].location

    def test_parameter_added_at_end(self, analyzer):
        """Test 39: Parameter added at end."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert "index 1" in added[0].description

    def test_multiple_parameters_added(self, analyzer):
        """Test 40: Multiple parameters added."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert len(added) == 2

    def test_parameter_added_new_value(self, analyzer):
        """Test 41: Parameter added has new_value."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "param", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert added[0].new_value is not None
        assert added[0].new_value["name"] == "param"

    def test_parameter_added_pointer_type(self, analyzer):
        """Test 42: Pointer parameter added."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "buffer", "type": "void*"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert "void*" in added[0].description

    def test_parameter_added_struct_type(self, analyzer):
        """Test 43: Struct parameter added."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "point", "type": "Point"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert "Point" in added[0].description

    def test_parameter_added_entity_id(self, analyzer):
        """Test 44: Parameter added includes entity_id."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "param", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "my_function")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert added[0].entity_id == "my_function"

    def test_parameter_added_no_old_value(self, analyzer):
        """Test 45: Parameter added has no old_value."""
        baseline = {"return_type": "void", "parameters": []}
        candidate = {"return_type": "void", "parameters": [{"name": "param", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        added = [c for c in diff.changes if c.change_type == "parameter_added"]
        assert added[0].old_value is None


# ============================================================================
# TEST PARAMETER REMOVALS (10 TESTS)
# ============================================================================
class TestParameterRemovals:
    """Test parameter removal detection."""

    @pytest.fixture
    def analyzer(self):
        return FunctionSignatureAnalyzer()

    def test_parameter_removed_breaking(self, analyzer):
        """Test 46: Parameter removed is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "old_param", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert len(removed) == 1
        assert removed[0].severity == ChangeSeverity.BREAKING

    def test_parameter_removed_description(self, analyzer):
        """Test 47: Parameter removed has description."""
        baseline = {"return_type": "void", "parameters": [{"name": "deprecated", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert "deprecated" in removed[0].description
        assert "int32_t" in removed[0].description

    def test_parameter_removed_location(self, analyzer):
        """Test 48: Parameter removed has location."""
        baseline = {"return_type": "void", "parameters": [{"name": "param", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert "parameter[0]" in removed[0].location

    def test_parameter_removed_old_value(self, analyzer):
        """Test 49: Parameter removed has old_value."""
        baseline = {"return_type": "void", "parameters": [{"name": "param", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert removed[0].old_value is not None
        assert removed[0].old_value["name"] == "param"

    def test_parameter_removed_from_middle(self, analyzer):
        """Test 50: Parameter removed from middle."""
        baseline = {
            "return_type": "void",
            "parameters": [
                {"name": "a", "type": "int32_t"},
                {"name": "b", "type": "int32_t"},
                {"name": "c", "type": "int32_t"},
            ],
        }
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "c", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert len(removed) == 1
        assert "b" in removed[0].description

    def test_multiple_parameters_removed(self, analyzer):
        """Test 51: Multiple parameters removed."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert len(removed) == 2

    def test_parameter_removed_no_new_value(self, analyzer):
        """Test 52: Parameter removed has no new_value."""
        baseline = {"return_type": "void", "parameters": [{"name": "param", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert removed[0].new_value is None

    def test_parameter_removed_pointer(self, analyzer):
        """Test 53: Pointer parameter removed."""
        baseline = {"return_type": "void", "parameters": [{"name": "buffer", "type": "void*"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert "void*" in removed[0].description

    def test_parameter_removed_entity_id(self, analyzer):
        """Test 54: Parameter removed includes entity_id."""
        baseline = {"return_type": "void", "parameters": [{"name": "param", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": []}

        diff = analyzer.analyze_function(baseline, candidate, "process_data")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert removed[0].entity_id == "process_data"

    def test_parameter_removed_index_preserved(self, analyzer):
        """Test 55: Parameter removed preserves original index."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        removed = [c for c in diff.changes if c.change_type == "parameter_removed"]
        assert "index 1" in removed[0].description


# ============================================================================
# TEST PARAMETER TYPE CHANGES (10 TESTS)
# ============================================================================
class TestParameterTypeChanges:
    """Test parameter type change detection."""

    @pytest.fixture
    def analyzer(self):
        return FunctionSignatureAnalyzer()

    def test_parameter_type_changed_breaking(self, analyzer):
        """Test 56: Parameter type change is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "size", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "size", "type": "size_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        type_changes = [c for c in diff.changes if c.change_type == "parameter_type_changed"]
        assert len(type_changes) == 1
        assert type_changes[0].severity == ChangeSeverity.BREAKING

    def test_parameter_type_int_to_float(self, analyzer):
        """Test 57: int to float is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "value", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "value", "type": "float"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_parameter_type_value_to_pointer(self, analyzer):
        """Test 58: value to pointer is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "point", "type": "Point"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "point", "type": "Point*"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_parameter_type_unsigned_to_signed(self, analyzer):
        """Test 59: unsigned to signed is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "count", "type": "uint32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "count", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_parameter_type_description(self, analyzer):
        """Test 60: Parameter type change has description."""
        baseline = {"return_type": "void", "parameters": [{"name": "size", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "size", "type": "size_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        type_changes = [c for c in diff.changes if c.change_type == "parameter_type_changed"]
        assert "size" in type_changes[0].description
        assert "int32_t" in type_changes[0].description
        assert "size_t" in type_changes[0].description

    def test_parameter_type_values(self, analyzer):
        """Test 61: Parameter type change old/new values."""
        baseline = {"return_type": "void", "parameters": [{"name": "size", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "size", "type": "size_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        type_changes = [c for c in diff.changes if c.change_type == "parameter_type_changed"]
        assert type_changes[0].old_value == "int32_t"
        assert type_changes[0].new_value == "size_t"

    def test_parameter_type_location(self, analyzer):
        """Test 62: Parameter type change has location."""
        baseline = {"return_type": "void", "parameters": [{"name": "size", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "size", "type": "size_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        type_changes = [c for c in diff.changes if c.change_type == "parameter_type_changed"]
        assert "parameter[0]" in type_changes[0].location

    def test_parameter_type_struct_change(self, analyzer):
        """Test 63: struct type change is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "p", "type": "Point"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "p", "type": "Vector"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        assert diff.has_breaking_changes()

    def test_parameter_type_const_added(self, analyzer):
        """Test 64: const qualifier added."""
        baseline = {"return_type": "void", "parameters": [{"name": "str", "type": "char*"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "str", "type": "const char*"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        type_changes = [c for c in diff.changes if c.change_type == "parameter_type_changed"]
        assert len(type_changes) == 1

    def test_parameter_type_multiple_changed(self, analyzer):
        """Test 65: Multiple parameter types changed."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int64_t"}, {"name": "b", "type": "float"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        type_changes = [c for c in diff.changes if c.change_type == "parameter_type_changed"]
        assert len(type_changes) == 2


# ============================================================================
# TEST PARAMETER REORDERING (10 TESTS)
# ============================================================================
class TestParameterReordering:
    """Test parameter reordering detection."""

    @pytest.fixture
    def analyzer(self):
        return FunctionSignatureAnalyzer()

    def test_parameter_reordered_breaking(self, analyzer):
        """Test 66: Parameter reordering is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "b", "type": "int32_t"}, {"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        assert len(reordered) == 2
        assert all(c.severity == ChangeSeverity.BREAKING for c in reordered)

    def test_parameter_reordered_description(self, analyzer):
        """Test 67: Parameter reordered has description."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "b", "type": "int32_t"}, {"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        a_reorder = [c for c in reordered if "'a'" in c.description][0]
        assert "index 0" in a_reorder.description
        assert "index 1" in a_reorder.description

    def test_parameter_reordered_values(self, analyzer):
        """Test 68: Parameter reordered old/new values."""
        baseline = {"return_type": "void", "parameters": [{"name": "first", "type": "int32_t"}, {"name": "second", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "second", "type": "int32_t"}, {"name": "first", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        first_reorder = [c for c in reordered if "'first'" in c.description][0]
        assert first_reorder.old_value == 0
        assert first_reorder.new_value == 1

    def test_parameter_reordered_location(self, analyzer):
        """Test 69: Parameter reordered has location."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "b", "type": "int32_t"}, {"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        assert all(c.location is not None for c in reordered)

    def test_parameter_reordered_three_params(self, analyzer):
        """Test 70: Three parameters reordered."""
        baseline = {
            "return_type": "void",
            "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}, {"name": "c", "type": "int32_t"}],
        }
        candidate = {
            "return_type": "void",
            "parameters": [{"name": "c", "type": "int32_t"}, {"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}],
        }

        diff = analyzer.analyze_function(baseline, candidate, "func")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        assert len(reordered) == 3

    def test_parameter_reordered_entity_id(self, analyzer):
        """Test 71: Parameter reordered includes entity_id."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "b", "type": "int32_t"}, {"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "swap_params")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        assert all(c.entity_id == "swap_params" for c in reordered)

    def test_parameter_reordered_severity(self, analyzer):
        """Test 72: Parameter reordered is BREAKING."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "b", "type": "int32_t"}, {"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        assert all(c.severity == ChangeSeverity.BREAKING for c in reordered)

    def test_parameter_partial_reorder(self, analyzer):
        """Test 73: Partial reordering detected."""
        baseline = {
            "return_type": "void",
            "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}, {"name": "c", "type": "int32_t"}],
        }
        candidate = {
            "return_type": "void",
            "parameters": [{"name": "a", "type": "int32_t"}, {"name": "c", "type": "int32_t"}, {"name": "b", "type": "int32_t"}],
        }

        diff = analyzer.analyze_function(baseline, candidate, "func")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        assert len(reordered) == 2  # Only b and c moved

    def test_parameter_no_reorder_same_order(self, analyzer):
        """Test 74: No reordering when order unchanged."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        assert len(reordered) == 0

    def test_parameter_reordered_with_type_change(self, analyzer):
        """Test 75: Reordering combined with type change."""
        baseline = {"return_type": "void", "parameters": [{"name": "a", "type": "int32_t"}, {"name": "b", "type": "int32_t"}]}
        candidate = {"return_type": "void", "parameters": [{"name": "b", "type": "float"}, {"name": "a", "type": "int32_t"}]}

        diff = analyzer.analyze_function(baseline, candidate, "func")

        # Should detect both reordering and type change
        reordered = [c for c in diff.changes if c.change_type == "parameter_reordered"]
        type_changed = [c for c in diff.changes if c.change_type == "parameter_type_changed"]
        assert len(reordered) == 2
        assert len(type_changed) == 1


# ============================================================================
# TEST FUNCTION CATALOG ANALYZER (15 TESTS)
# ============================================================================
class TestFunctionCatalogAnalyzer:
    """Test FunctionCatalogAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        return FunctionCatalogAnalyzer()

    def test_function_added(self, analyzer):
        """Test 76: Function added is EXTENSION."""
        baseline = {}
        candidate = {"new_func": {"return_type": "void", "parameters": []}}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert len(diffs) == 1
        assert diffs[0].entity_id == "new_func"
        assert not diffs[0].has_breaking_changes()

    def test_function_removed(self, analyzer):
        """Test 77: Function removed is BREAKING."""
        baseline = {"old_func": {"return_type": "void", "parameters": []}}
        candidate = {}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert len(diffs) == 1
        assert diffs[0].entity_id == "old_func"
        assert diffs[0].has_breaking_changes()

    def test_function_modified(self, analyzer):
        """Test 78: Function modified detected."""
        baseline = {"func": {"return_type": "int32_t", "parameters": []}}
        candidate = {"func": {"return_type": "int64_t", "parameters": []}}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert len(diffs) == 1
        assert diffs[0].entity_id == "func"
        assert diffs[0].has_breaking_changes()

    def test_function_unchanged_not_reported(self, analyzer):
        """Test 79: Unchanged function not in diff."""
        baseline = {"func": {"return_type": "void", "parameters": []}}
        candidate = {"func": {"return_type": "void", "parameters": []}}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert len(diffs) == 0

    def test_multiple_functions_added(self, analyzer):
        """Test 80: Multiple functions added."""
        baseline = {}
        candidate = {"func1": {"return_type": "void", "parameters": []}, "func2": {"return_type": "int32_t", "parameters": []}}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert len(diffs) == 2
        added = [d for d in diffs if not d.has_breaking_changes()]
        assert len(added) == 2

    def test_multiple_functions_removed(self, analyzer):
        """Test 81: Multiple functions removed."""
        baseline = {"func1": {"return_type": "void", "parameters": []}, "func2": {"return_type": "int32_t", "parameters": []}}
        candidate = {}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert len(diffs) == 2
        removed = [d for d in diffs if d.has_breaking_changes()]
        assert len(removed) == 2

    def test_mixed_changes(self, analyzer):
        """Test 82: Mixed additions, removals, and modifications."""
        baseline = {
            "unchanged": {"return_type": "void", "parameters": []},
            "removed": {"return_type": "void", "parameters": []},
            "modified": {"return_type": "int32_t", "parameters": []},
        }
        candidate = {
            "unchanged": {"return_type": "void", "parameters": []},
            "modified": {"return_type": "int64_t", "parameters": []},
            "added": {"return_type": "float", "parameters": []},
        }

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert len(diffs) == 3  # removed, modified, added (unchanged not reported)

    def test_function_added_description(self, analyzer):
        """Test 83: Function added has description."""
        baseline = {}
        candidate = {"new_function": {"return_type": "void", "parameters": []}}

        diffs = analyzer.analyze_functions(baseline, candidate)

        added_change = diffs[0].changes[0]
        assert "new_function" in added_change.description
        assert added_change.change_type == "function_added"

    def test_function_removed_description(self, analyzer):
        """Test 84: Function removed has description."""
        baseline = {"old_function": {"return_type": "void", "parameters": []}}
        candidate = {}

        diffs = analyzer.analyze_functions(baseline, candidate)

        removed_change = diffs[0].changes[0]
        assert "old_function" in removed_change.description
        assert removed_change.change_type == "function_removed"

    def test_function_added_severity(self, analyzer):
        """Test 85: Function added is EXTENSION."""
        baseline = {}
        candidate = {"new_func": {"return_type": "void", "parameters": []}}

        diffs = analyzer.analyze_functions(baseline, candidate)

        added_change = diffs[0].changes[0]
        assert added_change.severity == ChangeSeverity.EXTENSION

    def test_function_removed_severity(self, analyzer):
        """Test 86: Function removed is BREAKING."""
        baseline = {"old_func": {"return_type": "void", "parameters": []}}
        candidate = {}

        diffs = analyzer.analyze_functions(baseline, candidate)

        removed_change = diffs[0].changes[0]
        assert removed_change.severity == ChangeSeverity.BREAKING

    def test_function_catalog_returns_entity_diffs(self, analyzer):
        """Test 87: Returns EntityDiff instances."""
        baseline = {}
        candidate = {"func": {"return_type": "void", "parameters": []}}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert all(isinstance(d, EntityDiff) for d in diffs)

    def test_function_catalog_entity_type(self, analyzer):
        """Test 88: EntityDiff has entity_type 'function'."""
        baseline = {}
        candidate = {"func": {"return_type": "void", "parameters": []}}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert all(d.entity_type == "function" for d in diffs)

    def test_empty_catalogs(self, analyzer):
        """Test 89: Empty catalogs produce no diffs."""
        baseline = {}
        candidate = {}

        diffs = analyzer.analyze_functions(baseline, candidate)

        assert len(diffs) == 0

    def test_large_catalog_change(self, analyzer):
        """Test 90: Large catalog with many changes."""
        baseline = {f"func{i}": {"return_type": "void", "parameters": []} for i in range(50)}
        candidate = {f"func{i}": {"return_type": "void", "parameters": []} for i in range(25, 75)}

        diffs = analyzer.analyze_functions(baseline, candidate)

        # 25 removed (0-24), 25 unchanged (25-49), 25 added (50-74)
        # Only changed functions reported
        removed = [d for d in diffs if d.has_breaking_changes()]
        added = [d for d in diffs if not d.has_breaking_changes()]
        assert len(removed) == 25
        assert len(added) == 25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
