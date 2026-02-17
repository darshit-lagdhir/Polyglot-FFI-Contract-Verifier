""" Tests for Contract Versioning - Prompt 9/20 Clause-Level Diff Analysis & Constraint Change Detection

Testing Level: HARDEST (70 comprehensive tests) """

import pytest
from modules.module_06_contract_schema.contract_versioning import (
    ChangeSeverity,
    DetailedChange,
    EntityDiff,
    ClauseAnalyzer,
    ClauseCatalogAnalyzer,
)


# ============================================================================
# TEST CLAUSE ANALYZER - SEVERITY CHANGES (10 TESTS)
# ============================================================================
class TestSeverityChanges:
    """Test clause severity changes (10 tests)."""

    @pytest.fixture
    def analyzer(self):
        return ClauseAnalyzer()

    def test_severity_increased_strengthening(self, analyzer):
        """Test 1: Severity increase is STRENGTHENING."""
        baseline = {"severity": "advisory", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        assert diff.has_breaking_changes() is False
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_severity_decreased_relaxation(self, analyzer):
        """Test 2: Severity decrease is RELAXATION."""
        baseline = {"severity": "fatal", "constraint_parameters": {}}
        candidate = {"severity": "warning", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert changes[0].severity == ChangeSeverity.RELAXATION

    def test_severity_unchanged(self, analyzer):
        """Test 3: Unchanged severity."""
        baseline = {"severity": "error", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert len(changes) == 0

    def test_severity_advisory_to_fatal(self, analyzer):
        """Test 4: Advisory to fatal."""
        baseline = {"severity": "advisory", "constraint_parameters": {}}
        candidate = {"severity": "fatal", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_severity_default_advisory(self, analyzer):
        """Test 5: Missing severity defaults to advisory."""
        baseline = {"constraint_parameters": {}}
        candidate = {"constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert len(changes) == 0

    def test_severity_description(self, analyzer):
        """Test 6: Severity change has description."""
        baseline = {"severity": "warning", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert "warning" in changes[0].description
        assert "error" in changes[0].description

    def test_severity_values(self, analyzer):
        """Test 7: Severity old/new values."""
        baseline = {"severity": "advisory", "constraint_parameters": {}}
        candidate = {"severity": "warning", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert changes[0].old_value == "advisory"
        assert changes[0].new_value == "warning"

    def test_severity_entity_id(self, analyzer):
        """Test 8: Severity change includes entity_id."""
        baseline = {"severity": "advisory", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "my_clause")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert changes[0].entity_id == "my_clause"

    def test_severity_warning_to_error(self, analyzer):
        """Test 9: Warning to error is strengthening."""
        baseline = {"severity": "warning", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_severity_error_to_fatal(self, analyzer):
        """Test 10: Error to fatal is strengthening."""
        baseline = {"severity": "error", "constraint_parameters": {}}
        candidate = {"severity": "fatal", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "severity_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING


# ============================================================================
# TEST NULLABILITY CONSTRAINTS (15 TESTS)
# ============================================================================
class TestNullabilityConstraints:
    """Test nullability constraint changes (15 tests)."""

    @pytest.fixture
    def analyzer(self):
        return ClauseAnalyzer()

    def test_nullable_true_to_false_strengthening(self, analyzer):
        """Test 11: nullable true→false is STRENGTHENING."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_nullable_false_to_true_relaxation(self, analyzer):
        """Test 12: nullable false→true is RELAXATION."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": False}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": True}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.RELAXATION

    def test_nullable_unchanged(self, analyzer):
        """Test 13: Unchanged nullable."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": True}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 0

    def test_nullable_description(self, analyzer):
        """Test 14: Nullable change has description."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert "nullable" in changes[0].description

    def test_nullable_location(self, analyzer):
        """Test 15: Nullable change has location."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert "constraint 'nullable'" in changes[0].location

    def test_nullable_values(self, analyzer):
        """Test 16: Nullable old/new values."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].old_value is True
        assert changes[0].new_value is False

    def test_nullable_added(self, analyzer):
        """Test 17: Nullable constraint added."""
        baseline = {"severity": "error", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 1

    def test_nullable_removed(self, analyzer):
        """Test 18: Nullable constraint removed."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": False}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 1

    def test_nullable_with_confidence(self, analyzer):
        """Test 19: Nullable change with other params."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True, "confidence": 0.7}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False, "confidence": 0.9}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        assert len(diff.changes) == 2

    def test_confidence_change_notable(self, analyzer):
        """Test 20: Confidence change is NOTABLE."""
        baseline = {"severity": "error", "constraint_parameters": {"confidence": 0.7}}
        candidate = {"severity": "error", "constraint_parameters": {"confidence": 0.9}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.NOTABLE

    def test_multiple_constraints_changed(self, analyzer):
        """Test 21: Multiple constraints changed."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True, "min_size": 0}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False, "min_size": 10}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 2

    def test_empty_constraint_parameters(self, analyzer):
        """Test 22: Empty constraint parameters."""
        baseline = {"severity": "error", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 0

    def test_default_empty_parameters(self, analyzer):
        """Test 23: Missing constraint_parameters."""
        baseline = {"severity": "error"}
        candidate = {"severity": "error"}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 0

    def test_constraint_entity_id(self, analyzer):
        """Test 24: Constraint change includes entity_id."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False}}
        diff = analyzer.analyze_clause(baseline, candidate, "my_clause_id")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].entity_id == "my_clause_id"

    def test_constraint_change_type(self, analyzer):
        """Test 25: Constraint change type is correct."""
        baseline = {"severity": "error", "constraint_parameters": {"nullable": True}}
        candidate = {"severity": "error", "constraint_parameters": {"nullable": False}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].change_type == "constraint_parameter_changed"


# ============================================================================
# TEST NUMERIC CONSTRAINTS (15 TESTS)
# ============================================================================
class TestNumericConstraints:
    """Test numeric constraint changes (15 tests)."""

    @pytest.fixture
    def analyzer(self):
        return ClauseAnalyzer()

    def test_min_size_increased_strengthening(self, analyzer):
        """Test 26: min_size increase is STRENGTHENING."""
        baseline = {"severity": "error", "constraint_parameters": {"min_size": 0}}
        candidate = {"severity": "error", "constraint_parameters": {"min_size": 10}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_min_size_decreased_relaxation(self, analyzer):
        """Test 27: min_size decrease is RELAXATION."""
        baseline = {"severity": "error", "constraint_parameters": {"min_size": 10}}
        candidate = {"severity": "error", "constraint_parameters": {"min_size": 0}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.RELAXATION

    def test_max_size_decreased_strengthening(self, analyzer):
        """Test 28: max_size decrease is STRENGTHENING."""
        baseline = {"severity": "error", "constraint_parameters": {"max_size": 100}}
        candidate = {"severity": "error", "constraint_parameters": {"max_size": 50}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_max_size_increased_relaxation(self, analyzer):
        """Test 29: max_size increase is RELAXATION."""
        baseline = {"severity": "error", "constraint_parameters": {"max_size": 50}}
        candidate = {"severity": "error", "constraint_parameters": {"max_size": 100}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.RELAXATION

    def test_min_value_increased(self, analyzer):
        """Test 30: min_value increase."""
        baseline = {"severity": "error", "constraint_parameters": {"min_value": 0}}
        candidate = {"severity": "error", "constraint_parameters": {"min_value": 1}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_max_value_decreased(self, analyzer):
        """Test 31: max_value decrease."""
        baseline = {"severity": "error", "constraint_parameters": {"max_value": 255}}
        candidate = {"severity": "error", "constraint_parameters": {"max_value": 127}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_numeric_constraint_values(self, analyzer):
        """Test 32: Numeric constraint old/new values."""
        baseline = {"severity": "error", "constraint_parameters": {"min_size": 0}}
        candidate = {"severity": "error", "constraint_parameters": {"min_size": 10}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].old_value == 0
        assert changes[0].new_value == 10

    def test_min_length_constraint(self, analyzer):
        """Test 33: min_length constraint."""
        baseline = {"severity": "error", "constraint_parameters": {"min_length": 1}}
        candidate = {"severity": "error", "constraint_parameters": {"min_length": 5}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_max_length_constraint(self, analyzer):
        """Test 34: max_length constraint."""
        baseline = {"severity": "error", "constraint_parameters": {"max_length": 100}}
        candidate = {"severity": "error", "constraint_parameters": {"max_length": 50}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_min_count_constraint(self, analyzer):
        """Test 35: min_count constraint."""
        baseline = {"severity": "error", "constraint_parameters": {"min_count": 0}}
        candidate = {"severity": "error", "constraint_parameters": {"min_count": 3}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_numeric_none_to_value(self, analyzer):
        """Test 36: Numeric constraint added."""
        baseline = {"severity": "error", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {"min_size": 10}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 1

    def test_numeric_value_to_none(self, analyzer):
        """Test 37: Numeric constraint removed."""
        baseline = {"severity": "error", "constraint_parameters": {"min_size": 10}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 1

    def test_combined_min_max(self, analyzer):
        """Test 38: Combined min/max changes."""
        baseline = {"severity": "error", "constraint_parameters": {"min_size": 0, "max_size": 100}}
        candidate = {"severity": "error", "constraint_parameters": {"min_size": 10, "max_size": 50}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 2
        assert all(c.severity == ChangeSeverity.STRENGTHENING for c in changes)

    def test_numeric_description(self, analyzer):
        """Test 39: Numeric constraint description."""
        baseline = {"severity": "error", "constraint_parameters": {"min_size": 0}}
        candidate = {"severity": "error", "constraint_parameters": {"min_size": 10}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert "min_size" in changes[0].description
        assert "0" in changes[0].description
        assert "10" in changes[0].description

    def test_numeric_location(self, analyzer):
        """Test 40: Numeric constraint location."""
        baseline = {"severity": "error", "constraint_parameters": {"min_size": 0}}
        candidate = {"severity": "error", "constraint_parameters": {"min_size": 10}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert "constraint 'min_size'" in changes[0].location


# ============================================================================
# TEST OWNERSHIP CONSTRAINTS (10 TESTS)
# ============================================================================
class TestOwnershipConstraints:
    """Test ownership constraint changes (10 tests)."""

    @pytest.fixture
    def analyzer(self):
        return ClauseAnalyzer()

    def test_ownership_change_breaking(self, analyzer):
        """Test 41: Ownership change is BREAKING."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "callee"}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.BREAKING

    def test_ownership_caller_to_callee(self, analyzer):
        """Test 42: caller→callee ownership."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "callee"}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        assert diff.has_breaking_changes()

    def test_ownership_callee_to_caller(self, analyzer):
        """Test 43: callee→caller ownership."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "callee"}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        assert diff.has_breaking_changes()

    def test_ownership_unchanged(self, analyzer):
        """Test 44: Unchanged ownership."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert len(changes) == 0

    def test_ownership_values(self, analyzer):
        """Test 45: Ownership old/new values."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "callee"}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].old_value == "caller"
        assert changes[0].new_value == "callee"

    def test_ownership_description(self, analyzer):
        """Test 46: Ownership change description."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "callee"}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert "ownership" in changes[0].description

    def test_ownership_shared(self, analyzer):
        """Test 47: Shared ownership."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "shared"}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        assert diff.has_breaking_changes()

    def test_ownership_added(self, analyzer):
        """Test 48: Ownership constraint added."""
        baseline = {"severity": "error", "constraint_parameters": {}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "callee"}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.BREAKING

    def test_ownership_removed(self, analyzer):
        """Test 49: Ownership constraint removed."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "caller"}}
        candidate = {"severity": "error", "constraint_parameters": {}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        changes = [c for c in diff.changes if c.change_type == "constraint_parameter_changed"]
        assert changes[0].severity == ChangeSeverity.BREAKING

    def test_ownership_with_other_constraints(self, analyzer):
        """Test 50: Ownership change with others."""
        baseline = {"severity": "error", "constraint_parameters": {"ownership": "caller", "nullable": False}}
        candidate = {"severity": "error", "constraint_parameters": {"ownership": "callee", "nullable": False}}
        diff = analyzer.analyze_clause(baseline, candidate, "clause_1")
        assert diff.has_breaking_changes()


# ============================================================================
# TEST CLAUSE CATALOG CHANGES (20 TESTS)
# ============================================================================
class TestClauseCatalog:
    """Test clause catalog changes (20 tests)."""

    @pytest.fixture
    def analyzer(self):
        return ClauseCatalogAnalyzer()

    def test_clause_added_strengthening(self, analyzer):
        """Test 51: Clause added is STRENGTHENING."""
        baseline = {}
        candidate = {"clause_1": {"severity": "error", "constraint_parameters": {"nullable": False}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert len(diffs) == 1
        assert diffs[0].changes[0].severity == ChangeSeverity.STRENGTHENING

    def test_clause_removed_relaxation(self, analyzer):
        """Test 52: Clause removed is RELAXATION."""
        baseline = {"clause_1": {"severity": "error", "constraint_parameters": {"nullable": False}}}
        candidate = {}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert len(diffs) == 1
        assert diffs[0].changes[0].severity == ChangeSeverity.RELAXATION

    def test_clause_modified(self, analyzer):
        """Test 53: Clause modified."""
        baseline = {"clause_1": {"severity": "warning", "constraint_parameters": {}}}
        candidate = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert len(diffs) == 1

    def test_clause_unchanged_not_reported(self, analyzer):
        """Test 54: Unchanged clause not reported."""
        baseline = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        candidate = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert len(diffs) == 0

    def test_multiple_clauses_added(self, analyzer):
        """Test 55: Multiple clauses added."""
        baseline = {}
        candidate = {
            "clause_1": {"severity": "error", "constraint_parameters": {}},
            "clause_2": {"severity": "warning", "constraint_parameters": {}},
        }
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert len(diffs) == 2

    def test_multiple_clauses_removed(self, analyzer):
        """Test 56: Multiple clauses removed."""
        baseline = {
            "clause_1": {"severity": "error", "constraint_parameters": {}},
            "clause_2": {"severity": "warning", "constraint_parameters": {}},
        }
        candidate = {}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert len(diffs) == 2

    def test_mixed_clause_changes(self, analyzer):
        """Test 57: Mixed clause changes."""
        baseline = {
            "unchanged": {"severity": "error", "constraint_parameters": {}},
            "removed": {"severity": "error", "constraint_parameters": {}},
            "modified": {"severity": "warning", "constraint_parameters": {}},
        }
        candidate = {
            "unchanged": {"severity": "error", "constraint_parameters": {}},
            "modified": {"severity": "error", "constraint_parameters": {}},
            "added": {"severity": "error", "constraint_parameters": {}},
        }
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert len(diffs) == 3

    def test_clause_added_description(self, analyzer):
        """Test 58: Clause added description."""
        baseline = {}
        candidate = {"new_clause": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert "new_clause" in diffs[0].changes[0].description

    def test_clause_removed_description(self, analyzer):
        """Test 59: Clause removed description."""
        baseline = {"old_clause": {"severity": "error", "constraint_parameters": {}}}
        candidate = {}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert "old_clause" in diffs[0].changes[0].description

    def test_clause_entity_type(self, analyzer):
        """Test 60: Clause entity type."""
        baseline = {}
        candidate = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert diffs[0].entity_type == "clause"

    def test_empty_catalogs(self, analyzer):
        """Test 61: Empty catalogs."""
        baseline = {}
        candidate = {}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert len(diffs) == 0

    def test_clause_added_change_type(self, analyzer):
        """Test 62: Clause added change type."""
        baseline = {}
        candidate = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert diffs[0].changes[0].change_type == "clause_added"

    def test_clause_removed_change_type(self, analyzer):
        """Test 63: Clause removed change type."""
        baseline = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        candidate = {}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert diffs[0].changes[0].change_type == "clause_removed"

    def test_clause_added_new_value(self, analyzer):
        """Test 64: Clause added has new_value."""
        baseline = {}
        candidate = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert diffs[0].changes[0].new_value is not None

    def test_clause_removed_old_value(self, analyzer):
        """Test 65: Clause removed has old_value."""
        baseline = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        candidate = {}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert diffs[0].changes[0].old_value is not None

    def test_clause_catalog_returns_entity_diffs(self, analyzer):
        """Test 66: Returns EntityDiff instances."""
        baseline = {}
        candidate = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert all(isinstance(d, EntityDiff) for d in diffs)

    def test_large_catalog_change(self, analyzer):
        """Test 67: Large catalog change."""
        baseline = {f"clause_{i}": {"severity": "error", "constraint_parameters": {}} for i in range(50)}
        candidate = {f"clause_{i}": {"severity": "error", "constraint_parameters": {}} for i in range(25, 75)}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        added = [d for d in diffs if d.changes[0].change_type == "clause_added"]
        removed = [d for d in diffs if d.changes[0].change_type == "clause_removed"]
        assert len(added) == 25
        assert len(removed) == 25

    def test_clause_id_preserved(self, analyzer):
        """Test 68: Clause ID preserved."""
        baseline = {}
        candidate = {"my_custom_clause_id": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert diffs[0].entity_id == "my_custom_clause_id"

    def test_clause_added_no_old_value(self, analyzer):
        """Test 69: Clause added has no old_value."""
        baseline = {}
        candidate = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert diffs[0].changes[0].old_value is None

    def test_clause_removed_no_new_value(self, analyzer):
        """Test 70: Clause removed has no new_value."""
        baseline = {"clause_1": {"severity": "error", "constraint_parameters": {}}}
        candidate = {}
        diffs = analyzer.analyze_clauses(baseline, candidate)
        assert diffs[0].changes[0].new_value is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
