""" Tests for Contract Versioning - Prompt 10/20 Version History Tracking & Temporal Diff Analysis

Testing Level: HARDEST (80 comprehensive tests) """

import pytest
from datetime import datetime
from modules.module_06_contract_schema.contract_versioning import (
    VersionSnapshot,
    VersionHistory,
    VersionHistoryBuilder,
    ChangeAggregator,
    DetailedDiff,
    EntityDiff,
    DetailedChange,
    ChangeSeverity,
)


# ============================================================================
# TEST VERSION SNAPSHOT (10 TESTS)
# ============================================================================
class TestVersionSnapshot:
    """Test VersionSnapshot (10 tests)."""

    def test_create_snapshot(self):
        """Test 1: Create version snapshot."""
        snap = VersionSnapshot(version="1.0.0", timestamp="2026-01-01T00:00:00Z", fingerprint="abc123")
        assert snap.version == "1.0.0"
        assert snap.fingerprint == "abc123"

    def test_snapshot_with_parent(self):
        """Test 2: Snapshot with parent version."""
        snap = VersionSnapshot(
            version="1.1.0", timestamp="2026-01-02T00:00:00Z", fingerprint="def456", parent_version="1.0.0"
        )
        assert snap.parent_version == "1.0.0"

    def test_snapshot_no_parent(self):
        """Test 3: Snapshot without parent (root)."""
        snap = VersionSnapshot(version="1.0.0", timestamp="2026-01-01T00:00:00Z", fingerprint="abc123")
        assert snap.parent_version is None

    def test_snapshot_to_dict(self):
        """Test 4: Snapshot to dictionary."""
        snap = VersionSnapshot(version="1.0.0", timestamp="2026-01-01T00:00:00Z", fingerprint="abc123")
        data = snap.to_dict()
        assert data["version"] == "1.0.0"
        assert data["fingerprint"] == "abc123"

    def test_snapshot_with_metadata(self):
        """Test 5: Snapshot with metadata."""
        snap = VersionSnapshot(
            version="1.0.0",
            timestamp="2026-01-01T00:00:00Z",
            fingerprint="abc123",
            metadata={"author": "dev", "tag": "stable"},
        )
        assert snap.metadata["author"] == "dev"

    def test_snapshot_with_contract_data(self):
        """Test 6: Snapshot with contract data."""
        snap = VersionSnapshot(
            version="1.0.0", timestamp="2026-01-01T00:00:00Z", fingerprint="abc123", contract_data={"functions": {}, "clauses": {}}
        )
        assert snap.contract_data is not None

    def test_snapshot_timestamp_format(self):
        """Test 7: Timestamp format."""
        snap = VersionSnapshot(version="1.0.0", timestamp="2026-01-01T00:00:00Z", fingerprint="abc123")
        assert "T" in snap.timestamp
        assert "Z" in snap.timestamp

    def test_snapshot_version_field(self):
        """Test 8: Version field preserved."""
        snap = VersionSnapshot(version="2.5.13", timestamp="2026-01-01T00:00:00Z", fingerprint="abc123")
        assert snap.version == "2.5.13"

    def test_snapshot_fingerprint_field(self):
        """Test 9: Fingerprint field preserved."""
        fp = "a" * 64
        snap = VersionSnapshot(version="1.0.0", timestamp="2026-01-01T00:00:00Z", fingerprint=fp)
        assert snap.fingerprint == fp

    def test_snapshot_to_dict_includes_all_fields(self):
        """Test 10: to_dict includes all fields."""
        snap = VersionSnapshot(
            version="1.0.0",
            timestamp="2026-01-01T00:00:00Z",
            fingerprint="abc123",
            parent_version="0.9.0",
            metadata={"key": "value"},
        )
        data = snap.to_dict()
        assert "version" in data
        assert "timestamp" in data
        assert "fingerprint" in data
        assert "parent_version" in data
        assert "metadata" in data


# ============================================================================
# TEST VERSION HISTORY (25 TESTS)
# ============================================================================
class TestVersionHistory:
    """Test VersionHistory (25 tests)."""

    @pytest.fixture
    def history(self):
        return VersionHistory()

    def test_add_snapshot(self, history):
        """Test 11: Add snapshot to history."""
        snap = VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "abc123")
        history.add_snapshot(snap)
        assert history.get_snapshot("1.0.0") is not None

    def test_get_snapshot(self, history):
        """Test 12: Get snapshot by version."""
        snap = VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "abc123")
        history.add_snapshot(snap)
        retrieved = history.get_snapshot("1.0.0")
        assert retrieved.version == "1.0.0"

    def test_get_snapshot_not_found(self, history):
        """Test 13: Get non-existent snapshot."""
        result = history.get_snapshot("999.0.0")
        assert result is None

    def test_get_all_versions(self, history):
        """Test 14: Get all version identifiers."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("1.1.0", "2026-01-02T00:00:00Z", "b"))
        versions = history.get_all_versions()
        assert len(versions) == 2
        assert "1.0.0" in versions
        assert "1.1.0" in versions

    def test_get_parent_version(self, history):
        """Test 15: Get parent version."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("1.1.0", "2026-01-02T00:00:00Z", "b", parent_version="1.0.0"))
        parent = history.get_parent_version("1.1.0")
        assert parent == "1.0.0"

    def test_get_parent_version_root(self, history):
        """Test 16: Get parent of root version."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        parent = history.get_parent_version("1.0.0")
        assert parent is None

    def test_get_ancestry_chain_single(self, history):
        """Test 17: Ancestry chain for single version."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        chain = history.get_ancestry_chain("1.0.0")
        assert chain == ["1.0.0"]

    def test_get_ancestry_chain_linear(self, history):
        """Test 18: Ancestry chain for linear history."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("1.1.0", "2026-01-02T00:00:00Z", "b", parent_version="1.0.0"))
        history.add_snapshot(VersionSnapshot("1.2.0", "2026-01-03T00:00:00Z", "c", parent_version="1.1.0"))
        chain = history.get_ancestry_chain("1.2.0")
        assert chain == ["1.0.0", "1.1.0", "1.2.0"]

    def test_timeline_between_linear(self, history):
        """Test 19: Timeline between linear versions."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("1.1.0", "2026-01-02T00:00:00Z", "b", parent_version="1.0.0"))
        history.add_snapshot(VersionSnapshot("1.2.0", "2026-01-03T00:00:00Z", "c", parent_version="1.1.0"))
        timeline = history.timeline_between("1.0.0", "1.2.0")
        assert len(timeline) == 2
        assert timeline[0] == ("1.0.0", "1.1.0")
        assert timeline[1] == ("1.1.0", "1.2.0")

    def test_timeline_between_same_version(self, history):
        """Test 20: Timeline between same version."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        timeline = history.timeline_between("1.0.0", "1.0.0")
        assert len(timeline) == 0

    def test_is_ancestor_true(self, history):
        """Test 21: is_ancestor returns true."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("1.1.0", "2026-01-02T00:00:00Z", "b", parent_version="1.0.0"))
        history.add_snapshot(VersionSnapshot("1.2.0", "2026-01-03T00:00:00Z", "c", parent_version="1.1.0"))
        assert history.is_ancestor("1.0.0", "1.2.0") is True

    def test_is_ancestor_false(self, history):
        """Test 22: is_ancestor returns false."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("2.0.0", "2026-01-02T00:00:00Z", "b"))
        assert history.is_ancestor("2.0.0", "1.0.0") is False

    def test_is_ancestor_self(self, history):
        """Test 23: is_ancestor with self."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        assert history.is_ancestor("1.0.0", "1.0.0") is True

    def test_common_ancestor_linear(self, history):
        """Test 24: Common ancestor in linear history."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("1.1.0", "2026-01-02T00:00:00Z", "b", parent_version="1.0.0"))
        history.add_snapshot(VersionSnapshot("1.2.0", "2026-01-03T00:00:00Z", "c", parent_version="1.1.0"))
        ancestor = history.common_ancestor("1.1.0", "1.2.0")
        assert ancestor == "1.1.0"

    def test_common_ancestor_branched(self, history):
        """Test 25: Common ancestor in branched history."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("1.1.0", "2026-01-02T00:00:00Z", "b", parent_version="1.0.0"))
        history.add_snapshot(VersionSnapshot("2.0.0", "2026-01-03T00:00:00Z", "c", parent_version="1.0.0"))
        ancestor = history.common_ancestor("1.1.0", "2.0.0")
        assert ancestor == "1.0.0"

    def test_common_ancestor_same_version(self, history):
        """Test 26: Common ancestor of same version."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        ancestor = history.common_ancestor("1.0.0", "1.0.0")
        assert ancestor == "1.0.0"

    def test_diff_between_not_found(self, history):
        """Test 27: diff_between with non-existent versions."""
        diff = history.diff_between("1.0.0", "2.0.0")
        assert diff is None

    def test_diff_between_no_contract_data(self, history):
        """Test 28: diff_between with no contract data."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("1.1.0", "2026-01-02T00:00:00Z", "b", parent_version="1.0.0"))
        diff = history.diff_between("1.0.0", "1.1.0")
        assert diff is None

    def test_diff_between_with_contract_data(self, history):
        """Test 29: diff_between with contract data."""
        history.add_snapshot(
            VersionSnapshot(
                "1.0.0",
                "2026-01-01T00:00:00Z",
                "a",
                contract_data={"version": "1.0.0", "fingerprint": "a", "functions": {}, "clauses": {}},
            )
        )
        history.add_snapshot(
            VersionSnapshot(
                "1.1.0",
                "2026-01-02T00:00:00Z",
                "b",
                parent_version="1.0.0",
                contract_data={"version": "1.1.0", "fingerprint": "b", "functions": {}, "clauses": {}},
            )
        )
        diff = history.diff_between("1.0.0", "1.1.0")
        assert diff is not None

    def test_find_breaking_changes_between(self, history):
        """Test 30: Find breaking changes between versions."""
        history.add_snapshot(
            VersionSnapshot(
                "1.0.0",
                "2026-01-01T00:00:00Z",
                "a",
                contract_data={"version": "1.0.0", "fingerprint": "a", "functions": {}, "clauses": {}},
            )
        )
        history.add_snapshot(
            VersionSnapshot(
                "1.1.0",
                "2026-01-02T00:00:00Z",
                "b",
                parent_version="1.0.0",
                contract_data={"version": "1.1.0", "fingerprint": "b", "functions": {}, "clauses": {}},
            )
        )
        breaking = history.find_breaking_changes_between("1.0.0", "1.1.0")
        assert isinstance(breaking, list)

    def test_empty_history_get_all_versions(self, history):
        """Test 31: Get all versions from empty history."""
        versions = history.get_all_versions()
        assert len(versions) == 0

    def test_multiple_snapshots(self, history):
        """Test 32: Add multiple snapshots."""
        for i in range(5):
            history.add_snapshot(VersionSnapshot(f"1.{i}.0", "2026-01-01T00:00:00Z", f"hash{i}"))
        assert len(history.get_all_versions()) == 5

    def test_get_parent_version_not_found(self, history):
        """Test 33: Get parent of non-existent version."""
        parent = history.get_parent_version("999.0.0")
        assert parent is None

    def test_ancestry_chain_not_found(self, history):
        """Test 34: Ancestry chain for non-existent version."""
        chain = history.get_ancestry_chain("999.0.0")
        assert chain == []

    def test_common_ancestor_no_common(self, history):
        """Test 35: Common ancestor with no common root."""
        history.add_snapshot(VersionSnapshot("1.0.0", "2026-01-01T00:00:00Z", "a"))
        history.add_snapshot(VersionSnapshot("2.0.0", "2026-01-02T00:00:00Z", "b"))
        ancestor = history.common_ancestor("1.0.0", "2.0.0")
        assert ancestor is None


# ============================================================================
# TEST VERSION HISTORY BUILDER (15 TESTS)
# ============================================================================
class TestVersionHistoryBuilder:
    """Test VersionHistoryBuilder (15 tests)."""

    def test_create_builder(self):
        """Test 36: Create history builder."""
        builder = VersionHistoryBuilder()
        assert builder.history is not None

    def test_add_version(self):
        """Test 37: Add version to builder."""
        builder = VersionHistoryBuilder()
        builder.add_version("1.0.0", "abc123", {})
        history = builder.build()
        assert history.get_snapshot("1.0.0") is not None

    def test_add_version_with_parent(self):
        """Test 38: Add version with parent."""
        builder = VersionHistoryBuilder()
        builder.add_version("1.0.0", "abc123", {})
        builder.add_version("1.1.0", "def456", {}, parent_version="1.0.0")
        history = builder.build()
        assert history.get_parent_version("1.1.0") == "1.0.0"

    def test_add_version_generates_timestamp(self):
        """Test 39: Add version generates timestamp."""
        builder = VersionHistoryBuilder()
        snap = builder.add_version("1.0.0", "abc123", {})
        assert snap.timestamp is not None
        assert "T" in snap.timestamp

    def test_add_version_custom_timestamp(self):
        """Test 40: Add version with custom timestamp."""
        builder = VersionHistoryBuilder()
        custom_time = "2026-01-01T12:00:00Z"
        snap = builder.add_version("1.0.0", "abc123", {}, timestamp=custom_time)
        assert snap.timestamp == custom_time

    def test_add_version_with_contract_data(self):
        """Test 41: Add version with contract data."""
        builder = VersionHistoryBuilder()
        contract_data = {"functions": {}, "clauses": {}}
        snap = builder.add_version("1.0.0", "abc123", contract_data)
        assert snap.contract_data == contract_data

    def test_build_returns_history(self):
        """Test 42: Build returns VersionHistory."""
        builder = VersionHistoryBuilder()
        builder.add_version("1.0.0", "abc123", {})
        history = builder.build()
        assert isinstance(history, VersionHistory)

    def test_builder_chain(self):
        """Test 43: Builder chain multiple versions."""
        builder = VersionHistoryBuilder()
        builder.add_version("1.0.0", "a", {})
        builder.add_version("1.1.0", "b", {}, parent_version="1.0.0")
        builder.add_version("1.2.0", "c", {}, parent_version="1.1.0")
        history = builder.build()
        chain = history.get_ancestry_chain("1.2.0")
        assert len(chain) == 3

    def test_add_version_returns_snapshot(self):
        """Test 44: add_version returns snapshot."""
        builder = VersionHistoryBuilder()
        snap = builder.add_version("1.0.0", "abc123", {})
        assert isinstance(snap, VersionSnapshot)

    def test_builder_multiple_roots(self):
        """Test 45: Builder with multiple root versions."""
        builder = VersionHistoryBuilder()
        builder.add_version("1.0.0", "a", {})
        builder.add_version("2.0.0", "b", {})
        history = builder.build()
        assert len(history.get_all_versions()) == 2

    def test_builder_preserves_fingerprint(self):
        """Test 46: Builder preserves fingerprint."""
        builder = VersionHistoryBuilder()
        fp = "a" * 64
        builder.add_version("1.0.0", fp, {})
        history = builder.build()
        snap = history.get_snapshot("1.0.0")
        assert snap.fingerprint == fp

    def test_builder_preserves_version(self):
        """Test 47: Builder preserves version."""
        builder = VersionHistoryBuilder()
        builder.add_version("1.2.3", "abc123", {})
        history = builder.build()
        snap = history.get_snapshot("1.2.3")
        assert snap.version == "1.2.3"

    def test_builder_empty_contract_data(self):
        """Test 48: Builder with empty contract data."""
        builder = VersionHistoryBuilder()
        builder.add_version("1.0.0", "abc123", {})
        history = builder.build()
        snap = history.get_snapshot("1.0.0")
        assert snap.contract_data == {}

    def test_builder_complex_contract_data(self):
        """Test 49: Builder with complex contract data."""
        builder = VersionHistoryBuilder()
        contract_data = {"functions": {"f1": {}, "f2": {}}, "clauses": {"c1": {}, "c2": {}}}
        builder.add_version("1.0.0", "abc123", contract_data)
        history = builder.build()
        snap = history.get_snapshot("1.0.0")
        assert len(snap.contract_data["functions"]) == 2

    def test_builder_reuse(self):
        """Test 50: Builder can be reused."""
        builder = VersionHistoryBuilder()
        builder.add_version("1.0.0", "a", {})
        history1 = builder.build()
        builder.add_version("1.1.0", "b", {}, parent_version="1.0.0")
        history2 = builder.build()
        assert len(history2.get_all_versions()) == 2


# ============================================================================
# TEST CHANGE AGGREGATOR (30 TESTS)
# ============================================================================
class TestChangeAggregator:
    """Test ChangeAggregator (30 tests)."""

    @pytest.fixture
    def aggregator(self):
        return ChangeAggregator()

    @pytest.fixture
    def mock_diff(self):
        return DetailedDiff(
            baseline_version="1.0.0",
            candidate_version="1.1.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
            entity_diffs=[
                EntityDiff(
                    "entity1",
                    "function",
                    [
                        DetailedChange("c1", "e1", ChangeSeverity.BREAKING, "d1"),
                        DetailedChange("c2", "e1", ChangeSeverity.EXTENSION, "d2"),
                    ],
                )
            ],
        )

    def test_aggregate_empty(self, aggregator):
        """Test 51: Aggregate empty list."""
        result = aggregator.aggregate_changes([])
        assert result["total_changes"] == 0

    def test_aggregate_single_diff(self, aggregator, mock_diff):
        """Test 52: Aggregate single diff."""
        result = aggregator.aggregate_changes([mock_diff])
        assert result["total_changes"] == 2

    def test_aggregate_breaking_count(self, aggregator, mock_diff):
        """Test 53: Aggregate breaking changes count."""
        result = aggregator.aggregate_changes([mock_diff])
        assert result["breaking_changes"] == 1

    def test_aggregate_extension_count(self, aggregator, mock_diff):
        """Test 54: Aggregate extension count."""
        result = aggregator.aggregate_changes([mock_diff])
        assert result["extensions"] == 1

    def test_aggregate_affected_entities(self, aggregator, mock_diff):
        """Test 55: Aggregate affected entities."""
        result = aggregator.aggregate_changes([mock_diff])
        assert "entity1" in result["affected_entities"]

    def test_aggregate_multiple_diffs(self, aggregator, mock_diff):
        """Test 56: Aggregate multiple diffs."""
        result = aggregator.aggregate_changes([mock_diff, mock_diff])
        assert result["total_changes"] == 4

    def test_aggregate_strengthening_count(self, aggregator):
        """Test 57: Aggregate strengthening count."""
        diff = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("e", "clause", [DetailedChange("c", "e", ChangeSeverity.STRENGTHENING, "d")])],
        )
        result = aggregator.aggregate_changes([diff])
        assert result["strengthening"] == 1

    def test_aggregate_relaxation_count(self, aggregator):
        """Test 58: Aggregate relaxation count."""
        diff = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("e", "clause", [DetailedChange("c", "e", ChangeSeverity.RELAXATION, "d")])],
        )
        result = aggregator.aggregate_changes([diff])
        assert result["relaxation"] == 1

    def test_aggregate_notable_count(self, aggregator):
        """Test 59: Aggregate notable count."""
        diff = DetailedDiff(
            "1.0.0", "1.1.0", "a" * 64, "b" * 64, [EntityDiff("e", "function", [DetailedChange("c", "e", ChangeSeverity.NOTABLE, "d")])]
        )
        result = aggregator.aggregate_changes([diff])
        assert result["notable"] == 1

    def test_aggregate_neutral_count(self, aggregator):
        """Test 60: Aggregate neutral count."""
        diff = DetailedDiff(
            "1.0.0", "1.1.0", "a" * 64, "b" * 64, [EntityDiff("e", "function", [DetailedChange("c", "e", ChangeSeverity.NEUTRAL, "d")])]
        )
        result = aggregator.aggregate_changes([diff])
        assert result["neutral"] == 1

    def test_aggregate_deduplicates_entities(self, aggregator, mock_diff):
        """Test 61: Aggregate deduplicates entities."""
        result = aggregator.aggregate_changes([mock_diff, mock_diff])
        assert len(result["affected_entities"]) == 1

    def test_aggregate_returns_dict(self, aggregator, mock_diff):
        """Test 62: Aggregate returns dictionary."""
        result = aggregator.aggregate_changes([mock_diff])
        assert isinstance(result, dict)

    def test_aggregate_has_all_keys(self, aggregator, mock_diff):
        """Test 63: Aggregate has all expected keys."""
        result = aggregator.aggregate_changes([mock_diff])
        assert "total_changes" in result
        assert "breaking_changes" in result
        assert "extensions" in result
        assert "strengthening" in result
        assert "relaxation" in result
        assert "notable" in result
        assert "neutral" in result
        assert "affected_entities" in result

    def test_aggregate_multiple_entities(self, aggregator):
        """Test 64: Aggregate multiple entities."""
        diff = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff("e1", "function", [DetailedChange("c", "e1", ChangeSeverity.BREAKING, "d")]),
                EntityDiff("e2", "struct", [DetailedChange("c", "e2", ChangeSeverity.EXTENSION, "d")]),
            ],
        )
        result = aggregator.aggregate_changes([diff])
        assert len(result["affected_entities"]) == 2

    def test_aggregate_zero_counts_default(self, aggregator):
        """Test 65: Aggregate zero counts by default."""
        result = aggregator.aggregate_changes([])
        assert result["breaking_changes"] == 0
        assert result["extensions"] == 0

    def test_aggregate_affected_entities_list(self, aggregator, mock_diff):
        """Test 66: Affected entities is list."""
        result = aggregator.aggregate_changes([mock_diff])
        assert isinstance(result["affected_entities"], list)

    def test_aggregate_sum_across_diffs(self, aggregator, mock_diff):
        """Test 67: Aggregate sums across diffs."""
        result = aggregator.aggregate_changes([mock_diff, mock_diff])
        assert result["breaking_changes"] == 2

    def test_aggregate_empty_affected_entities(self, aggregator):
        """Test 68: Empty diffs have empty affected entities."""
        result = aggregator.aggregate_changes([])
        assert result["affected_entities"] == []

    def test_aggregate_large_diff_count(self, aggregator, mock_diff):
        """Test 69: Aggregate large number of diffs."""
        result = aggregator.aggregate_changes([mock_diff] * 100)
        assert result["total_changes"] == 200

    def test_aggregate_mixed_severity_counts(self, aggregator):
        """Test 70: Aggregate mixed severity counts."""
        diff = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff(
                    "e",
                    "t",
                    [
                        DetailedChange("c1", "e", ChangeSeverity.BREAKING, "d"),
                        DetailedChange("c2", "e", ChangeSeverity.EXTENSION, "d"),
                        DetailedChange("c3", "e", ChangeSeverity.STRENGTHENING, "d"),
                        DetailedChange("c4", "e", ChangeSeverity.RELAXATION, "d"),
                        DetailedChange("c5", "e", ChangeSeverity.NOTABLE, "d"),
                        DetailedChange("c6", "e", ChangeSeverity.NEUTRAL, "d"),
                    ],
                )
            ],
        )
        result = aggregator.aggregate_changes([diff])
        assert result["total_changes"] == 6
        assert result["breaking_changes"] == 1
        assert result["extensions"] == 1
        assert result["strengthening"] == 1
        assert result["relaxation"] == 1
        assert result["notable"] == 1
        assert result["neutral"] == 1

    def test_aggregate_statistics_consistency(self, aggregator, mock_diff):
        """Test 71: Statistics are consistent."""
        result = aggregator.aggregate_changes([mock_diff])
        total_by_severity = (
            result["breaking_changes"]
            + result["extensions"]
            + result["strengthening"]
            + result["relaxation"]
            + result["notable"]
            + result["neutral"]
        )
        assert total_by_severity == result["total_changes"]

    def test_aggregate_entity_uniqueness(self, aggregator):
        """Test 72: Entities are unique."""
        diff1 = DetailedDiff(
            "1.0.0", "1.1.0", "a" * 64, "b" * 64, [EntityDiff("e1", "t", [DetailedChange("c", "e1", ChangeSeverity.BREAKING, "d")])]
        )
        diff2 = DetailedDiff(
            "1.1.0", "1.2.0", "b" * 64, "c" * 64, [EntityDiff("e1", "t", [DetailedChange("c", "e1", ChangeSeverity.EXTENSION, "d")])]
        )
        result = aggregator.aggregate_changes([diff1, diff2])
        assert len(result["affected_entities"]) == 1

    def test_aggregate_no_diffs(self, aggregator):
        """Test 73: Aggregate with no diffs."""
        result = aggregator.aggregate_changes([])
        assert result["total_changes"] == 0
        assert result["affected_entities"] == []

    def test_aggregate_preserves_entity_names(self, aggregator):
        """Test 74: Aggregate preserves entity names."""
        diff = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("my_function", "function", [DetailedChange("c", "my_function", ChangeSeverity.BREAKING, "d")])],
        )
        result = aggregator.aggregate_changes([diff])
        assert "my_function" in result["affected_entities"]

    def test_aggregate_multiple_changes_same_entity(self, aggregator):
        """Test 75: Multiple changes to same entity."""
        diff = DetailedDiff(
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
                        DetailedChange("c2", "e1", ChangeSeverity.BREAKING, "d2"),
                        DetailedChange("c3", "e1", ChangeSeverity.EXTENSION, "d3"),
                    ],
                )
            ],
        )
        result = aggregator.aggregate_changes([diff])
        assert result["total_changes"] == 3
        assert result["breaking_changes"] == 2
        assert len(result["affected_entities"]) == 1

    def test_aggregate_dict_keys_types(self, aggregator, mock_diff):
        """Test 76: Aggregate dict keys are correct types."""
        result = aggregator.aggregate_changes([mock_diff])
        assert isinstance(result["total_changes"], int)
        assert isinstance(result["breaking_changes"], int)
        assert isinstance(result["affected_entities"], list)

    def test_aggregate_no_negative_counts(self, aggregator, mock_diff):
        """Test 77: No negative counts in aggregate."""
        result = aggregator.aggregate_changes([mock_diff])
        assert result["total_changes"] >= 0
        assert result["breaking_changes"] >= 0
        assert result["extensions"] >= 0

    def test_aggregate_idempotent(self, aggregator, mock_diff):
        """Test 78: Aggregate is idempotent."""
        result1 = aggregator.aggregate_changes([mock_diff])
        result2 = aggregator.aggregate_changes([mock_diff])
        assert result1 == result2

    def test_aggregate_order_independent(self, aggregator, mock_diff):
        """Test 79: Aggregate is order-independent."""
        diff2 = DetailedDiff(
            "1.0.0", "1.1.0", "a" * 64, "b" * 64, [EntityDiff("e2", "t", [DetailedChange("c", "e2", ChangeSeverity.EXTENSION, "d")])]
        )
        result1 = aggregator.aggregate_changes([mock_diff, diff2])
        result2 = aggregator.aggregate_changes([diff2, mock_diff])
        assert set(result1["affected_entities"]) == set(result2["affected_entities"])

    def test_aggregate_entity_count_matches(self, aggregator):
        """Test 80: Entity count matches."""
        diff = DetailedDiff(
            "1.0.0",
            "1.1.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff("e1", "t", [DetailedChange("c", "e1", ChangeSeverity.BREAKING, "d")]),
                EntityDiff("e2", "t", [DetailedChange("c", "e2", ChangeSeverity.EXTENSION, "d")]),
                EntityDiff("e3", "t", [DetailedChange("c", "e3", ChangeSeverity.NOTABLE, "d")]),
            ],
        )
        result = aggregator.aggregate_changes([diff])
        assert len(result["affected_entities"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
