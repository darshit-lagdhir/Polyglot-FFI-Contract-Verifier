""" Tests for Contract Versioning - Prompt 7/20 Detailed Diff Analysis Engine & Structural Change Detection

Testing Level: HARDEST (100 comprehensive tests) """

import pytest
import json

from modules.module_06_contract_schema.contract_versioning import (
    ChangeSeverity,
    DetailedChange,
    EntityDiff,
    DetailedDiff,
    DetailedDiffAnalyzer,
    StructLayoutAnalyzer,
    DiffFormatter,
)


# ============================================================================
# TEST CHANGE SEVERITY ENUM (10 TESTS)
# ============================================================================
class TestChangeSeverity:
    """Test ChangeSeverity enum."""

    def test_all_severities_defined(self):
        """Test 1: All severity levels exist."""
        assert ChangeSeverity.BREAKING
        assert ChangeSeverity.EXTENSION
        assert ChangeSeverity.STRENGTHENING
        assert ChangeSeverity.RELAXATION
        assert ChangeSeverity.NOTABLE
        assert ChangeSeverity.NEUTRAL

    def test_breaking_value(self):
        """Test 2: BREAKING severity value."""
        assert ChangeSeverity.BREAKING.value == "breaking"

    def test_extension_value(self):
        """Test 3: EXTENSION severity value."""
        assert ChangeSeverity.EXTENSION.value == "extension"

    def test_strengthening_value(self):
        """Test 4: STRENGTHENING severity value."""
        assert ChangeSeverity.STRENGTHENING.value == "strengthening"

    def test_relaxation_value(self):
        """Test 5: RELAXATION severity value."""
        assert ChangeSeverity.RELAXATION.value == "relaxation"

    def test_notable_value(self):
        """Test 6: NOTABLE severity value."""
        assert ChangeSeverity.NOTABLE.value == "notable"

    def test_neutral_value(self):
        """Test 7: NEUTRAL severity value."""
        assert ChangeSeverity.NEUTRAL.value == "neutral"

    def test_all_values_unique(self):
        """Test 8: All severity values are unique."""
        values = [s.value for s in ChangeSeverity]
        assert len(values) == len(set(values))

    def test_severity_count(self):
        """Test 9: Correct number of severity levels."""
        assert len(list(ChangeSeverity)) == 6

    def test_severity_enum_membership(self):
        """Test 10: Membership testing works."""
        assert ChangeSeverity.BREAKING in ChangeSeverity
        assert "invalid" not in [s.value for s in ChangeSeverity]


# ============================================================================
# TEST DETAILED CHANGE (15 TESTS)
# ============================================================================
class TestDetailedChange:
    """Test DetailedChange dataclass."""

    def test_create_basic_change(self):
        """Test 11: Create basic change."""
        change = DetailedChange("field_added", "struct_Point", ChangeSeverity.EXTENSION, "Field added")
        assert change.change_type == "field_added"
        assert change.entity_id == "struct_Point"
        assert change.severity == ChangeSeverity.EXTENSION

    def test_change_with_old_new_values(self):
        """Test 12: Change with old and new values."""
        change = DetailedChange("size_changed", "s", ChangeSeverity.BREAKING, "Size changed", old_value=8, new_value=12)
        assert change.old_value == 8
        assert change.new_value == 12

    def test_change_with_location(self):
        """Test 13: Change with location information."""
        change = DetailedChange("offset_changed", "s", ChangeSeverity.BREAKING, "Offset changed", location="field 'x'")
        assert change.location == "field 'x'"

    def test_change_with_details(self):
        """Test 14: Change with additional details."""
        change = DetailedChange("test", "e", ChangeSeverity.NEUTRAL, "Test", details={"key": "value", "impact": "high"})
        assert change.details["key"] == "value"
        assert change.details["impact"] == "high"

    def test_change_to_dict_basic(self):
        """Test 15: Basic to_dict conversion."""
        change = DetailedChange("test", "entity", ChangeSeverity.BREAKING, "Test change")
        data = change.to_dict()
        assert data["change_type"] == "test"
        assert data["entity_id"] == "entity"
        assert data["severity"] == "breaking"
        assert data["description"] == "Test change"

    def test_change_to_dict_with_values(self):
        """Test 16: to_dict with old/new values."""
        change = DetailedChange("test", "e", ChangeSeverity.NEUTRAL, "d", old_value=42, new_value=100)
        data = change.to_dict()
        assert data["old_value"] == "42"
        assert data["new_value"] == "100"

    def test_change_to_dict_none_values(self):
        """Test 17: to_dict with None values."""
        change = DetailedChange("test", "e", ChangeSeverity.NEUTRAL, "d", old_value=None, new_value=None)
        data = change.to_dict()
        assert data["old_value"] is None
        assert data["new_value"] is None

    def test_change_to_dict_includes_location(self):
        """Test 18: to_dict includes location."""
        change = DetailedChange("test", "e", ChangeSeverity.NEUTRAL, "d", location="param[0]")
        data = change.to_dict()
        assert data["location"] == "param[0]"

    def test_change_to_dict_includes_details(self):
        """Test 19: to_dict includes details."""
        change = DetailedChange("test", "e", ChangeSeverity.NEUTRAL, "d", details={"x": 1})
        data = change.to_dict()
        assert data["details"] == {"x": 1}

    def test_change_empty_details(self):
        """Test 20: Empty details dict by default."""
        change = DetailedChange("test", "e", ChangeSeverity.NEUTRAL, "d")
        assert change.details == {}

    def test_change_breaking_severity(self):
        """Test 21: BREAKING severity."""
        change = DetailedChange("t", "e", ChangeSeverity.BREAKING, "d")
        assert change.severity == ChangeSeverity.BREAKING

    def test_change_extension_severity(self):
        """Test 22: EXTENSION severity."""
        change = DetailedChange("t", "e", ChangeSeverity.EXTENSION, "d")
        assert change.severity == ChangeSeverity.EXTENSION

    def test_change_description(self):
        """Test 23: Description field."""
        desc = "This is a detailed description of the change"
        change = DetailedChange("t", "e", ChangeSeverity.NEUTRAL, desc)
        assert change.description == desc

    def test_change_entity_id(self):
        """Test 24: Entity ID field."""
        change = DetailedChange("t", "my_custom_entity_123", ChangeSeverity.NEUTRAL, "d")
        assert change.entity_id == "my_custom_entity_123"

    def test_change_type_field(self):
        """Test 25: Change type field."""
        change = DetailedChange("custom_change_type", "e", ChangeSeverity.NEUTRAL, "d")
        assert change.change_type == "custom_change_type"


# ============================================================================
# TEST ENTITY DIFF (15 TESTS)
# ============================================================================
class TestEntityDiff:
    """Test EntityDiff dataclass."""

    def test_create_entity_diff(self):
        """Test 26: Create entity diff."""
        e = EntityDiff("struct_Point", "struct")
        assert e.entity_id == "struct_Point"
        assert e.entity_type == "struct"
        assert len(e.changes) == 0

    def test_has_breaking_changes_true(self):
        """Test 27: has_breaking_changes returns True."""
        e = EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.BREAKING, "d")])
        assert e.has_breaking_changes() is True

    def test_has_breaking_changes_false(self):
        """Test 28: has_breaking_changes returns False."""
        e = EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.EXTENSION, "d")])
        assert e.has_breaking_changes() is False

    def test_has_breaking_changes_mixed(self):
        """Test 29: has_breaking_changes with mixed severities."""
        e = EntityDiff(
            "e",
            "t",
            [
                DetailedChange("c1", "e", ChangeSeverity.EXTENSION, "d"),
                DetailedChange("c2", "e", ChangeSeverity.BREAKING, "d"),
                DetailedChange("c3", "e", ChangeSeverity.NEUTRAL, "d"),
            ],
        )
        assert e.has_breaking_changes() is True

    def test_has_breaking_changes_empty(self):
        """Test 30: has_breaking_changes with no changes."""
        e = EntityDiff("e", "t", [])
        assert e.has_breaking_changes() is False

    def test_get_most_severe_breaking(self):
        """Test 31: get_most_severe returns BREAKING."""
        e = EntityDiff(
            "e",
            "t",
            [
                DetailedChange("c1", "e", ChangeSeverity.EXTENSION, "d"),
                DetailedChange("c2", "e", ChangeSeverity.BREAKING, "d"),
                DetailedChange("c3", "e", ChangeSeverity.NEUTRAL, "d"),
            ],
        )
        most_severe = e.get_most_severe_change()
        assert most_severe.severity == ChangeSeverity.BREAKING

    def test_get_most_severe_none(self):
        """Test 32: get_most_severe with empty changes."""
        e = EntityDiff("e", "t", [])
        assert e.get_most_severe_change() is None

    def test_severity_priority_breaking_over_relaxation(self):
        """Test 33: BREAKING takes priority over RELAXATION."""
        e = EntityDiff(
            "e",
            "t",
            [DetailedChange("c1", "e", ChangeSeverity.RELAXATION, "d"), DetailedChange("c2", "e", ChangeSeverity.BREAKING, "d")],
        )
        assert e.get_most_severe_change().severity == ChangeSeverity.BREAKING

    def test_severity_priority_relaxation_over_strengthening(self):
        """Test 34: RELAXATION takes priority over STRENGTHENING."""
        e = EntityDiff(
            "e",
            "t",
            [
                DetailedChange("c1", "e", ChangeSeverity.STRENGTHENING, "d"),
                DetailedChange("c2", "e", ChangeSeverity.RELAXATION, "d"),
            ],
        )
        assert e.get_most_severe_change().severity == ChangeSeverity.RELAXATION

    def test_severity_priority_strengthening_over_extension(self):
        """Test 35: STRENGTHENING takes priority over EXTENSION."""
        e = EntityDiff(
            "e",
            "t",
            [
                DetailedChange("c1", "e", ChangeSeverity.EXTENSION, "d"),
                DetailedChange("c2", "e", ChangeSeverity.STRENGTHENING, "d"),
            ],
        )
        assert e.get_most_severe_change().severity == ChangeSeverity.STRENGTHENING

    def test_severity_priority_extension_over_notable(self):
        """Test 36: EXTENSION takes priority over NOTABLE."""
        e = EntityDiff(
            "e",
            "t",
            [DetailedChange("c1", "e", ChangeSeverity.NOTABLE, "d"), DetailedChange("c2", "e", ChangeSeverity.EXTENSION, "d")],
        )
        assert e.get_most_severe_change().severity == ChangeSeverity.EXTENSION

    def test_severity_priority_notable_over_neutral(self):
        """Test 37: NOTABLE takes priority over NEUTRAL."""
        e = EntityDiff(
            "e",
            "t",
            [DetailedChange("c1", "e", ChangeSeverity.NEUTRAL, "d"), DetailedChange("c2", "e", ChangeSeverity.NOTABLE, "d")],
        )
        assert e.get_most_severe_change().severity == ChangeSeverity.NOTABLE

    def test_entity_diff_to_dict(self):
        """Test 38: to_dict conversion."""
        e = EntityDiff("test_entity", "struct", [DetailedChange("c", "e", ChangeSeverity.BREAKING, "d")])
        data = e.to_dict()
        assert data["entity_id"] == "test_entity"
        assert data["entity_type"] == "struct"
        assert len(data["changes"]) == 1
        assert data["has_breaking_changes"] is True

    def test_entity_diff_multiple_changes(self):
        """Test 39: Entity with multiple changes."""
        e = EntityDiff(
            "e",
            "t",
            [
                DetailedChange("c1", "e", ChangeSeverity.BREAKING, "d1"),
                DetailedChange("c2", "e", ChangeSeverity.EXTENSION, "d2"),
                DetailedChange("c3", "e", ChangeSeverity.NOTABLE, "d3"),
            ],
        )
        assert len(e.changes) == 3

    def test_entity_type_values(self):
        """Test 40: Different entity types."""
        struct_diff = EntityDiff("s", "struct", [])
        func_diff = EntityDiff("f", "function", [])
        clause_diff = EntityDiff("c", "clause", [])

        assert struct_diff.entity_type == "struct"
        assert func_diff.entity_type == "function"
        assert clause_diff.entity_type == "clause"


# ============================================================================
# TEST DETAILED DIFF (10 TESTS)
# ============================================================================
class TestDetailedDiff:
    """Test DetailedDiff dataclass."""

    def test_create_detailed_diff(self):
        """Test 41: Create detailed diff."""
        d = DetailedDiff("1.0.0", "1.1.0", "a" * 64, "b" * 64)
        assert d.baseline_version == "1.0.0"
        assert d.candidate_version == "1.1.0"
        assert len(d.entity_diffs) == 0

    def test_get_all_changes(self):
        """Test 42: get_all_changes aggregates changes."""
        d = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff(
                    "e1",
                    "t",
                    [
                        DetailedChange("c1", "e1", ChangeSeverity.BREAKING, "d1"),
                        DetailedChange("c2", "e1", ChangeSeverity.EXTENSION, "d2"),
                    ],
                ),
                EntityDiff("e2", "t", [DetailedChange("c3", "e2", ChangeSeverity.NEUTRAL, "d3")]),
            ],
        )
        all_changes = d.get_all_changes()
        assert len(all_changes) == 3

    def test_filter_by_severity(self):
        """Test 43: filter_by_severity filters correctly."""
        d = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff(
                    "e",
                    "t",
                    [
                        DetailedChange("c1", "e", ChangeSeverity.BREAKING, "d1"),
                        DetailedChange("c2", "e", ChangeSeverity.EXTENSION, "d2"),
                        DetailedChange("c3", "e", ChangeSeverity.BREAKING, "d3"),
                    ],
                )
            ],
        )
        breaking = d.filter_by_severity(ChangeSeverity.BREAKING)
        assert len(breaking) == 2
        assert all(c.severity == ChangeSeverity.BREAKING for c in breaking)

    def test_filter_by_entity_type(self):
        """Test 44: filter_by_entity_type filters correctly."""
        d = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("e1", "struct", []), EntityDiff("e2", "function", []), EntityDiff("e3", "struct", [])],
        )
        structs = d.filter_by_entity_type("struct")
        assert len(structs) == 2
        assert all(e.entity_type == "struct" for e in structs)

    def test_get_breaking_changes(self):
        """Test 45: get_breaking_changes returns only breaking."""
        d = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff(
                    "e",
                    "t",
                    [
                        DetailedChange("c1", "e", ChangeSeverity.BREAKING, "d1"),
                        DetailedChange("c2", "e", ChangeSeverity.EXTENSION, "d2"),
                    ],
                )
            ],
        )
        breaking = d.get_breaking_changes()
        assert len(breaking) == 1
        assert breaking[0].severity == ChangeSeverity.BREAKING

    def test_get_statistics(self):
        """Test 46: get_statistics computes correctly."""
        d = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff(
                    "e1",
                    "struct",
                    [
                        DetailedChange("c1", "e1", ChangeSeverity.BREAKING, "d1"),
                        DetailedChange("c2", "e1", ChangeSeverity.EXTENSION, "d2"),
                    ],
                ),
                EntityDiff("e2", "function", [DetailedChange("c3", "e2", ChangeSeverity.BREAKING, "d3")]),
            ],
        )
        stats = d.get_statistics()
        assert stats["total_changes"] == 3
        assert stats["total_entities_changed"] == 2
        assert stats["by_severity"]["breaking"] == 2
        assert stats["by_severity"]["extension"] == 1
        assert stats["by_entity_type"]["struct"] == 1
        assert stats["by_entity_type"]["function"] == 1

    def test_to_dict(self):
        """Test 47: to_dict conversion."""
        d = DetailedDiff("1.0.0", "1.1.0", "a" * 64, "b" * 64)
        data = d.to_dict()
        assert data["baseline_version"] == "1.0.0"
        assert data["candidate_version"] == "1.1.0"
        assert "statistics" in data
        assert "entity_diffs" in data

    def test_to_json(self):
        """Test 48: to_json produces valid JSON."""
        d = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("e", "struct", [DetailedChange("c", "e", ChangeSeverity.BREAKING, "d")])],
        )
        json_str = d.to_json()
        parsed = json.loads(json_str)
        assert parsed["baseline_version"] == "1.0.0"
        assert len(parsed["entity_diffs"]) == 1

    def test_empty_diff_statistics(self):
        """Test 49: Statistics with no changes."""
        d = DetailedDiff("1.0.0", "1.0.0", "a" * 64, "a" * 64)
        stats = d.get_statistics()
        assert stats["total_changes"] == 0
        assert stats["total_entities_changed"] == 0
        assert stats["by_severity"]["breaking"] == 0

    def test_fingerprint_fields(self):
        """Test 50: Fingerprint fields preserved."""
        baseline_fp = "baseline" + "0" * 56
        candidate_fp = "candidat" + "1" * 56
        d = DetailedDiff("1.0.0", "1.1.0", baseline_fp, candidate_fp)
        assert d.baseline_fingerprint == baseline_fp
        assert d.candidate_fingerprint == candidate_fp


# ============================================================================
# TEST STRUCT LAYOUT ANALYZER (30 TESTS)
# ============================================================================
class TestStructLayoutAnalyzer:
    """Test StructLayoutAnalyzer (30 tests)."""

    @pytest.fixture
    def analyzer(self):
        return StructLayoutAnalyzer()

    def test_size_change_detected(self, analyzer):
        """Test 51: Size change is detected as breaking."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 12, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "struct_Point")

        assert e.has_breaking_changes()
        size_changes = [c for c in e.changes if c.change_type == "size_changed"]
        assert len(size_changes) == 1
        assert size_changes[0].old_value == 8
        assert size_changes[0].new_value == 12

    def test_alignment_change_detected(self, analyzer):
        """Test 52: Alignment change is detected as breaking."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 8, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "struct_Point")

        align_changes = [c for c in e.changes if c.change_type == "alignment_changed"]
        assert len(align_changes) == 1
        assert align_changes[0].severity == ChangeSeverity.BREAKING

    def test_field_added_at_end_extension(self, analyzer):
        """Test 53: Field added at end is EXTENSION."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        candidate = {
            "size_bytes": 12,
            "alignment": 4,
            "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}, {"name": "z", "offset": 8}],
        }
        e = analyzer.analyze_struct(baseline, candidate, "struct_Point")

        field_added = [c for c in e.changes if c.change_type == "field_added"]
        assert len(field_added) == 1
        assert field_added[0].severity == ChangeSeverity.EXTENSION
        assert field_added[0].location == "field 'z'"

    def test_field_added_before_end_breaking(self, analyzer):
        """Test 54: Field added before end is BREAKING."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        candidate = {
            "size_bytes": 12,
            "alignment": 4,
            "fields": [{"name": "z", "offset": 0}, {"name": "x", "offset": 4}, {"name": "y", "offset": 8}],
        }
        e = analyzer.analyze_struct(baseline, candidate, "struct_Point")

        field_added = [c for c in e.changes if c.change_type == "field_added"]
        assert len(field_added) == 1
        assert field_added[0].severity == ChangeSeverity.BREAKING

    def test_field_removed_breaking(self, analyzer):
        """Test 55: Field removed is BREAKING."""
        baseline = {
            "size_bytes": 12,
            "alignment": 4,
            "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}, {"name": "z", "offset": 8}],
        }
        candidate = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        e = analyzer.analyze_struct(baseline, candidate, "struct_Point")

        field_removed = [c for c in e.changes if c.change_type == "field_removed"]
        assert len(field_removed) == 1
        assert field_removed[0].severity == ChangeSeverity.BREAKING
        assert "Field 'z' removed" in field_removed[0].description

    def test_field_offset_changed_breaking(self, analyzer):
        """Test 56: Field offset changed is BREAKING."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        candidate = {"size_bytes": 12, "alignment": 4, "fields": [{"name": "x", "offset": 4}, {"name": "y", "offset": 8}]}
        e = analyzer.analyze_struct(baseline, candidate, "struct_Point")

        offset_changes = [c for c in e.changes if c.change_type == "field_offset_changed"]
        assert len(offset_changes) == 2
        assert all(c.severity == ChangeSeverity.BREAKING for c in offset_changes)

    def test_no_changes_empty_diff(self, analyzer):
        """Test 57: No changes produces empty diff."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        e = analyzer.analyze_struct(baseline, candidate, "struct_Point")

        assert len(e.changes) == 0
        assert not e.has_breaking_changes()

    def test_returns_entity_diff(self, analyzer):
        """Test 58: Returns EntityDiff instance."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "test_struct")

        assert isinstance(e, EntityDiff)
        assert e.entity_id == "test_struct"
        assert e.entity_type == "struct"

    def test_struct_id_preserved(self, analyzer):
        """Test 59: Struct ID is preserved."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "my_custom_struct_id_123")

        assert e.entity_id == "my_custom_struct_id_123"

    def test_multiple_fields_added(self, analyzer):
        """Test 60: Multiple fields added."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}]}
        candidate = {
            "size_bytes": 16,
            "alignment": 4,
            "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}, {"name": "z", "offset": 8}],
        }
        e = analyzer.analyze_struct(baseline, candidate, "s")

        field_added = [c for c in e.changes if c.change_type == "field_added"]
        assert len(field_added) == 2

    def test_multiple_fields_removed(self, analyzer):
        """Test 61: Multiple fields removed."""
        baseline = {
            "size_bytes": 16,
            "alignment": 4,
            "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}, {"name": "z", "offset": 8}],
        }
        candidate = {"size_bytes": 4, "alignment": 4, "fields": [{"name": "x", "offset": 0}]}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        field_removed = [c for c in e.changes if c.change_type == "field_removed"]
        assert len(field_removed) == 2

    def test_field_offset_unchanged(self, analyzer):
        """Test 62: Unchanged field offset not reported."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        offset_changes = [c for c in e.changes if c.change_type == "field_offset_changed"]
        assert len(offset_changes) == 0

    def test_empty_struct(self, analyzer):
        """Test 63: Empty structs."""
        baseline = {"size_bytes": 0, "alignment": 1, "fields": []}
        candidate = {"size_bytes": 0, "alignment": 1, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "empty_struct")

        assert len(e.changes) == 0

    def test_size_increase(self, analyzer):
        """Test 64: Size increase."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 16, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        size_changes = [c for c in e.changes if c.change_type == "size_changed"]
        assert size_changes[0].old_value == 8
        assert size_changes[0].new_value == 16

    def test_size_decrease(self, analyzer):
        """Test 65: Size decrease."""
        baseline = {"size_bytes": 16, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        assert e.has_breaking_changes()

    def test_alignment_increase(self, analyzer):
        """Test 66: Alignment increase."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 8, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        align_changes = [c for c in e.changes if c.change_type == "alignment_changed"]
        assert align_changes[0].old_value == 4
        assert align_changes[0].new_value == 8

    def test_alignment_decrease(self, analyzer):
        """Test 67: Alignment decrease."""
        baseline = {"size_bytes": 8, "alignment": 8, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        assert e.has_breaking_changes()

    def test_change_descriptions_present(self, analyzer):
        """Test 68: All changes have descriptions."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}]}
        candidate = {"size_bytes": 12, "alignment": 8, "fields": [{"name": "y", "offset": 0}]}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        for change in e.changes:
            assert len(change.description) > 0

    def test_change_locations_set(self, analyzer):
        """Test 69: Field changes have locations set."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}]}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        field_removed = [c for c in e.changes if c.change_type == "field_removed"]
        assert field_removed[0].location == "field 'x'"

    def test_old_new_values_for_size(self, analyzer):
        """Test 70: Old/new values set for size changes."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 12, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        size_changes = [c for c in e.changes if c.change_type == "size_changed"]
        assert size_changes[0].old_value == 8
        assert size_changes[0].new_value == 12

    def test_old_new_values_for_alignment(self, analyzer):
        """Test 71: Old/new values set for alignment changes."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 8, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        align_changes = [c for c in e.changes if c.change_type == "alignment_changed"]
        assert align_changes[0].old_value == 4
        assert align_changes[0].new_value == 8

    def test_old_new_values_for_offset(self, analyzer):
        """Test 72: Old/new values set for offset changes."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}]}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 4}]}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        offset_changes = [c for c in e.changes if c.change_type == "field_offset_changed"]
        assert offset_changes[0].old_value == 0
        assert offset_changes[0].new_value == 4

    def test_field_added_at_exact_boundary(self, analyzer):
        """Test 73: Field added exactly at old size boundary."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        candidate = {
            "size_bytes": 12,
            "alignment": 4,
            "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}, {"name": "z", "offset": 8}],
        }
        e = analyzer.analyze_struct(baseline, candidate, "s")

        field_added = [c for c in e.changes if c.change_type == "field_added"]
        assert field_added[0].severity == ChangeSeverity.EXTENSION

    def test_combined_size_and_field_changes(self, analyzer):
        """Test 74: Size change combined with field changes."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}]}
        candidate = {"size_bytes": 12, "alignment": 4, "fields": [{"name": "x", "offset": 0}, {"name": "y", "offset": 4}]}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        assert len(e.changes) == 2
        assert any(c.change_type == "size_changed" for c in e.changes)
        assert any(c.change_type == "field_added" for c in e.changes)

    def test_entity_type_always_struct(self, analyzer):
        """Test 75: Entity type is always 'struct'."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "any_id")

        assert e.entity_type == "struct"

    def test_missing_size_defaults_to_zero(self, analyzer):
        """Test 76: Missing size_bytes defaults to 0."""
        baseline = {"alignment": 4, "fields": []}
        candidate = {"alignment": 4, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        # Should not raise, defaults to 0
        assert len(e.changes) == 0

    def test_missing_alignment_defaults_to_zero(self, analyzer):
        """Test 77: Missing alignment defaults to 0."""
        baseline = {"size_bytes": 8, "fields": []}
        candidate = {"size_bytes": 8, "fields": []}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        # Should not raise, defaults to 0
        assert len(e.changes) == 0

    def test_missing_fields_defaults_to_empty(self, analyzer):
        """Test 78: Missing fields defaults to empty list."""
        baseline = {"size_bytes": 8, "alignment": 4}
        candidate = {"size_bytes": 8, "alignment": 4}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        # Should not raise, defaults to []
        assert len(e.changes) == 0

    def test_field_offset_zero_valid(self, analyzer):
        """Test 79: Field at offset 0 is valid."""
        baseline = {"size_bytes": 8, "alignment": 4, "fields": []}
        candidate = {"size_bytes": 8, "alignment": 4, "fields": [{"name": "x", "offset": 0}]}
        e = analyzer.analyze_struct(baseline, candidate, "s")

        field_added = [c for c in e.changes if c.change_type == "field_added"]
        assert len(field_added) == 1

    def test_large_struct(self, analyzer):
        """Test 80: Large struct with many fields."""
        baseline = {"size_bytes": 100, "alignment": 8, "fields": [{"name": f"field_{i}", "offset": i * 4} for i in range(25)]}
        candidate = {"size_bytes": 100, "alignment": 8, "fields": [{"name": f"field_{i}", "offset": i * 4} for i in range(25)]}
        e = analyzer.analyze_struct(baseline, candidate, "large_struct")

        assert len(e.changes) == 0


# ============================================================================
# TEST DIFF FORMATTER (10 TESTS)
# ============================================================================
class TestDiffFormatter:
    """Test DiffFormatter (10 tests)."""

    @pytest.fixture
    def formatter(self):
        return DiffFormatter()

    @pytest.fixture
    def sample_diff(self):
        return DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff(
                    "struct_Point",
                    "struct",
                    [DetailedChange("size_changed", "struct_Point", ChangeSeverity.BREAKING, "Size changed from 8 to 12 bytes")],
                )
            ],
        )

    def test_format_text_basic(self, formatter, sample_diff):
        """Test 81: Basic text formatting."""
        text = formatter.format_text(sample_diff)
        assert "Contract Diff: 1.0.0 → 1.1.0" in text
        assert "struct_Point" in text
        assert "Size changed" in text

    def test_format_text_includes_summary(self, formatter, sample_diff):
        """Test 82: Text format includes summary."""
        text = formatter.format_text(sample_diff)
        assert "Summary:" in text
        assert "Total changes:" in text
        assert "Breaking:" in text

    def test_format_text_empty_diff(self, formatter):
        """Test 83: Text format for empty diff."""
        diff = DetailedDiff("1.0.0", "1.1.0", "a" * 64, "b" * 64)
        text = formatter.format_text(diff)
        assert "Total changes: 0" in text

    def test_format_markdown_basic(self, formatter, sample_diff):
        """Test 84: Basic markdown formatting."""
        md = formatter.format_markdown(sample_diff)
        assert "# Contract Diff: 1.0.0 → 1.1.0" in md
        assert "## 🚨 Breaking Changes" in md
        assert "struct_Point" in md

    def test_format_markdown_includes_summary(self, formatter, sample_diff):
        """Test 85: Markdown includes summary section."""
        md = formatter.format_markdown(sample_diff)
        assert "## Summary" in md
        assert "Total changes:" in md

    def test_format_markdown_no_breaking(self, formatter):
        """Test 86: Markdown without breaking changes."""
        diff = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.EXTENSION, "Extension change")])],
        )
        md = formatter.format_markdown(diff)
        assert "## Summary" in md
        # No breaking section if no breaking changes

    def test_get_severity_badge_all_types(self, formatter):
        """Test 87: Severity badges for all types."""
        assert formatter._get_severity_badge(DetailedChange("c", "e", ChangeSeverity.BREAKING, "d")) == "BREAKING"
        assert formatter._get_severity_badge(DetailedChange("c", "e", ChangeSeverity.EXTENSION, "d")) == "EXTENSION"
        assert (
            formatter._get_severity_badge(DetailedChange("c", "e", ChangeSeverity.STRENGTHENING, "d")) == "STRENGTHENING"
        )
        assert formatter._get_severity_badge(DetailedChange("c", "e", ChangeSeverity.RELAXATION, "d")) == "RELAXATION"
        assert formatter._get_severity_badge(DetailedChange("c", "e", ChangeSeverity.NOTABLE, "d")) == "NOTABLE"
        assert formatter._get_severity_badge(DetailedChange("c", "e", ChangeSeverity.NEUTRAL, "d")) == "NEUTRAL"

    def test_get_severity_badge_none(self, formatter):
        """Test 88: Severity badge for None."""
        assert formatter._get_severity_badge(None) == "UNKNOWN"

    def test_format_text_multiple_entities(self, formatter):
        """Test 89: Text format with multiple entities."""
        diff = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff("struct_Point", "struct", [DetailedChange("c1", "e1", ChangeSeverity.BREAKING, "Change 1")]),
                EntityDiff("function_process", "function", [DetailedChange("c2", "e2", ChangeSeverity.EXTENSION, "Change 2")]),
            ],
        )
        text = formatter.format_text(diff)
        assert "struct_Point" in text
        assert "function_process" in text

    def test_format_markdown_multiple_breaking(self, formatter):
        """Test 90: Markdown with multiple breaking changes."""
        diff = DetailedDiff(
            "1.0.0",
            "2.0.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff("e1", "t", [DetailedChange("c1", "e1", ChangeSeverity.BREAKING, "Breaking 1")]),
                EntityDiff("e2", "t", [DetailedChange("c2", "e2", ChangeSeverity.BREAKING, "Breaking 2")]),
            ],
        )
        md = formatter.format_markdown(diff)
        assert "Breaking 1" in md
        assert "Breaking 2" in md


# ============================================================================
# TEST DETAILED DIFF ANALYZER (10 TESTS)
# ============================================================================
class TestDetailedDiffAnalyzer:
    """Test DetailedDiffAnalyzer (10 tests)."""

    @pytest.fixture
    def analyzer(self):
        return DetailedDiffAnalyzer()

    @pytest.fixture
    def mock_contract_v1(self):
        class MockContract:
            contract_version = "1.0.0"
            contract_fingerprint = "a" * 64

        return MockContract()

    @pytest.fixture
    def mock_contract_v2(self):
        class MockContract:
            contract_version = "1.1.0"
            contract_fingerprint = "b" * 64

        return MockContract()

    def test_analyze_returns_detailed_diff(self, analyzer, mock_contract_v1, mock_contract_v2):
        """Test 91: analyze returns DetailedDiff."""
        diff = analyzer.analyze(mock_contract_v1, mock_contract_v2)
        assert isinstance(diff, DetailedDiff)

    def test_analyze_sets_versions(self, analyzer, mock_contract_v1, mock_contract_v2):
        """Test 92: analyze sets baseline and candidate versions."""
        diff = analyzer.analyze(mock_contract_v1, mock_contract_v2)
        assert diff.baseline_version == "1.0.0"
        assert diff.candidate_version == "1.1.0"

    def test_analyze_sets_fingerprints(self, analyzer, mock_contract_v1, mock_contract_v2):
        """Test 93: analyze sets fingerprints."""
        diff = analyzer.analyze(mock_contract_v1, mock_contract_v2)
        assert diff.baseline_fingerprint == "a" * 64
        assert diff.candidate_fingerprint == "b" * 64

    def test_analyze_handles_missing_version(self, analyzer):
        """Test 94: analyze handles missing version attribute."""

        class MockContract:
            contract_fingerprint = "a" * 64

        diff = analyzer.analyze(MockContract(), MockContract())
        assert diff.baseline_version == "unknown"
        assert diff.candidate_version == "unknown"

    def test_analyze_handles_missing_fingerprint(self, analyzer):
        """Test 95: analyze handles missing fingerprint attribute."""

        class MockContract:
            contract_version = "1.0.0"

        diff = analyzer.analyze(MockContract(), MockContract())
        assert diff.baseline_fingerprint == ""
        assert diff.candidate_fingerprint == ""

    def test_analyze_initializes_entity_diffs(self, analyzer, mock_contract_v1, mock_contract_v2):
        """Test 96: analyze initializes entity_diffs list."""
        diff = analyzer.analyze(mock_contract_v1, mock_contract_v2)
        assert isinstance(diff.entity_diffs, list)

    def test_analyze_placeholder_returns_empty(self, analyzer, mock_contract_v1, mock_contract_v2):
        """Test 97: Placeholder implementations return empty."""
        diff = analyzer.analyze(mock_contract_v1, mock_contract_v2)
        # Placeholder implementations return empty lists
        assert len(diff.entity_diffs) == 0

    def test_analyze_same_contract(self, analyzer, mock_contract_v1):
        """Test 98: analyze comparing same contract."""
        diff = analyzer.analyze(mock_contract_v1, mock_contract_v1)
        assert diff.baseline_fingerprint == diff.candidate_fingerprint

    def test_analyze_to_dict(self, analyzer, mock_contract_v1, mock_contract_v2):
        """Test 99: Analyzed diff can convert to dict."""
        diff = analyzer.analyze(mock_contract_v1, mock_contract_v2)
        data = diff.to_dict()
        assert "baseline_version" in data
        assert "candidate_version" in data
        assert "statistics" in data

    def test_analyze_to_json(self, analyzer, mock_contract_v1, mock_contract_v2):
        """Test 100: Analyzed diff can convert to JSON."""
        diff = analyzer.analyze(mock_contract_v1, mock_contract_v2)
        json_str = diff.to_json()
        parsed = json.loads(json_str)
        assert parsed["baseline_version"] == "1.0.0"
        assert parsed["candidate_version"] == "1.1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
