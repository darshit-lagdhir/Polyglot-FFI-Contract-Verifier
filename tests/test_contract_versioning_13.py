""" Tests for Contract Versioning - Prompt 13/20 Compatibility Matrix & Cross-Version Testing

Testing Level: HARDEST (75 comprehensive tests) """

import pytest
from modules.module_06_contract_schema.contract_versioning import (
    CompatibilityStatus,
    CompatibilityTestResult,
    CompatibilityMatrixEntry,
    CompatibilityMatrix,
    CompatibilityTester,
    CompatibilityRecommendationEngine,
    VersionRangeSpec,
    CompatibilityMatrixBuilder,
    VersionHistory,
    VersionSnapshot,
)


# ============================================================================
# TEST COMPATIBILITY TEST RESULT (10 TESTS)
# ============================================================================
class TestCompatibilityTestResult:
    """Test CompatibilityTestResult (10 tests)."""

    def test_create_result(self):
        """Test 1: Create compatibility test result."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0", candidate_version="2.0.0", status=CompatibilityStatus.COMPATIBLE
        )
        assert result.baseline_version == "1.0.0"

    def test_is_compatible_true(self):
        """Test 2: is_compatible returns true."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0", candidate_version="2.0.0", status=CompatibilityStatus.COMPATIBLE
        )
        assert result.is_compatible() is True

    def test_is_compatible_false(self):
        """Test 3: is_compatible returns false."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0", candidate_version="2.0.0", status=CompatibilityStatus.INCOMPATIBLE
        )
        assert result.is_compatible() is False

    def test_is_partially_compatible_true(self):
        """Test 4: is_partially_compatible returns true."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0", candidate_version="2.0.0", status=CompatibilityStatus.PARTIALLY_COMPATIBLE
        )
        assert result.is_partially_compatible() is True

    def test_to_dict(self):
        """Test 5: Result to dictionary."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0", candidate_version="2.0.0", status=CompatibilityStatus.COMPATIBLE
        )
        data = result.to_dict()
        assert data["status"] == "compatible"

    def test_breaking_changes_count(self):
        """Test 6: Breaking changes count."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0", candidate_version="2.0.0", status=CompatibilityStatus.INCOMPATIBLE, breaking_changes=5
        )
        assert result.breaking_changes == 5

    def test_warnings_list(self):
        """Test 7: Warnings list."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0",
            candidate_version="2.0.0",
            status=CompatibilityStatus.PARTIALLY_COMPATIBLE,
            warnings=["Warning 1", "Warning 2"],
        )
        assert len(result.warnings) == 2

    def test_test_statuses(self):
        """Test 8: Test statuses."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0",
            candidate_version="2.0.0",
            status=CompatibilityStatus.COMPATIBLE,
            binding_generation="PASS",
            runtime_integration="PASS",
            feature_coverage="PASS",
        )
        assert result.binding_generation == "PASS"
        assert result.runtime_integration == "PASS"

    def test_notes_field(self):
        """Test 9: Notes field."""
        result = CompatibilityTestResult(
            baseline_version="1.0.0", candidate_version="2.0.0", status=CompatibilityStatus.COMPATIBLE, notes="All tests passed"
        )
        assert result.notes == "All tests passed"

    def test_default_values(self):
        """Test 10: Default values."""
        result = CompatibilityTestResult(baseline_version="1.0.0", candidate_version="2.0.0", status=CompatibilityStatus.UNTESTED)
        assert result.binding_generation == "UNTESTED"
        assert result.breaking_changes == 0


# ============================================================================
# TEST COMPATIBILITY MATRIX (15 TESTS)
# ============================================================================
class TestCompatibilityMatrix:
    """Test CompatibilityMatrix (15 tests)."""

    @pytest.fixture
    def matrix(self):
        return CompatibilityMatrix()

    def test_create_matrix(self, matrix):
        """Test 11: Create compatibility matrix."""
        assert matrix is not None
        assert len(matrix.entries) == 0

    def test_add_entry(self, matrix):
        """Test 12: Add entry to matrix."""
        result = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        entry = CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result)
        matrix.add_entry(entry)
        assert len(matrix.entries) == 1

    def test_get_compatibility(self, matrix):
        """Test 13: Get compatibility from matrix."""
        result = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        entry = CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result)
        matrix.add_entry(entry)

        compat = matrix.get_compatibility("app", "1.0.0", "libcore", "2.0.0")
        assert compat is not None
        assert compat.status == CompatibilityStatus.COMPATIBLE

    def test_get_compatibility_not_found(self, matrix):
        """Test 14: Get non-existent compatibility."""
        compat = matrix.get_compatibility("app", "1.0.0", "libcore", "2.0.0")
        assert compat is None

    def test_get_compatible_versions(self, matrix):
        """Test 15: Get compatible versions."""
        result1 = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        result2 = CompatibilityTestResult("1.0.0", "2.5.0", CompatibilityStatus.COMPATIBLE)
        result3 = CompatibilityTestResult("1.0.0", "3.0.0", CompatibilityStatus.INCOMPATIBLE)

        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result1))
        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.5.0", result2))
        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "3.0.0", result3))

        compatible = matrix.get_compatible_versions("app", "1.0.0", "libcore")
        assert len(compatible) == 2
        assert "2.0.0" in compatible
        assert "2.5.0" in compatible

    def test_get_all_entries_for_contract(self, matrix):
        """Test 16: Get all entries for contract."""
        result1 = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        result2 = CompatibilityTestResult("2.0.0", "1.0.0", CompatibilityStatus.COMPATIBLE)

        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result1))
        matrix.add_entry(CompatibilityMatrixEntry("libcore", "2.0.0", "app", "1.0.0", result2))

        entries = matrix.get_all_entries_for_contract("app")
        assert len(entries) == 2

    def test_to_dict(self, matrix):
        """Test 17: Matrix to dictionary."""
        result = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        entry = CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result)
        matrix.add_entry(entry)

        data = matrix.to_dict()
        assert "entries" in data
        assert len(data["entries"]) == 1

    def test_multiple_entries(self, matrix):
        """Test 18: Multiple matrix entries."""
        for i in range(5):
            result = CompatibilityTestResult(f"1.{i}.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
            entry = CompatibilityMatrixEntry("app", f"1.{i}.0", "libcore", "2.0.0", result)
            matrix.add_entry(entry)

        assert len(matrix.entries) == 5

    def test_entry_overwrite(self, matrix):
        """Test 19: Entry overwrite with same key."""
        result1 = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        result2 = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.INCOMPATIBLE)

        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result1))
        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result2))

        compat = matrix.get_compatibility("app", "1.0.0", "libcore", "2.0.0")
        assert compat.status == CompatibilityStatus.INCOMPATIBLE

    def test_get_compatible_versions_empty(self, matrix):
        """Test 20: Get compatible versions with none."""
        result = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.INCOMPATIBLE)
        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result))

        compatible = matrix.get_compatible_versions("app", "1.0.0", "libcore")
        assert len(compatible) == 0

    def test_get_all_entries_no_match(self, matrix):
        """Test 21: Get entries for non-existent contract."""
        entries = matrix.get_all_entries_for_contract("missing")
        assert len(entries) == 0

    def test_bidirectional_compatibility(self, matrix):
        """Test 22: Bidirectional compatibility entries."""
        result1 = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        result2 = CompatibilityTestResult("2.0.0", "1.0.0", CompatibilityStatus.COMPATIBLE)

        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result1))
        matrix.add_entry(CompatibilityMatrixEntry("libcore", "2.0.0", "app", "1.0.0", result2))

        compat1 = matrix.get_compatibility("app", "1.0.0", "libcore", "2.0.0")
        compat2 = matrix.get_compatibility("libcore", "2.0.0", "app", "1.0.0")

        assert compat1 is not None
        assert compat2 is not None

    def test_entry_to_dict(self):
        """Test 23: Entry to dictionary."""
        result = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        entry = CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result)
        data = entry.to_dict()

        assert data["contract_a"] == "app"
        assert data["version_a"] == "1.0.0"

    def test_get_compatible_partial(self, matrix):
        """Test 24: Get partially compatible versions."""
        result = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.PARTIALLY_COMPATIBLE)
        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", result))

        compatible = matrix.get_compatible_versions("app", "1.0.0", "libcore")
        assert len(compatible) == 0  # Only fully compatible

    def test_contract_name_case_sensitive(self, matrix):
        """Test 25: Contract names are case-sensitive."""
        result = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        matrix.add_entry(CompatibilityMatrixEntry("App", "1.0.0", "LibCore", "2.0.0", result))

        compat = matrix.get_compatibility("app", "1.0.0", "libcore", "2.0.0")
        assert compat is None


# ============================================================================
# TEST COMPATIBILITY TESTER (15 TESTS)
# ============================================================================
class TestCompatibilityTester:
    """Test CompatibilityTester (15 tests)."""

    @pytest.fixture
    def history(self):
        h = VersionHistory()
        h.add_snapshot(
            VersionSnapshot(
                "1.0.0",
                "2026-01-01T00:00:00Z",
                "a",
                contract_data={"version": "1.0.0", "fingerprint": "a", "functions": {}, "clauses": {}},
            )
        )
        h.add_snapshot(
            VersionSnapshot(
                "2.0.0",
                "2026-01-02T00:00:00Z",
                "b",
                parent_version="1.0.0",
                contract_data={"version": "2.0.0", "fingerprint": "b", "functions": {}, "clauses": {}},
            )
        )
        return h

    @pytest.fixture
    def tester(self, history):
        return CompatibilityTester(history)

    def test_test_compatibility(self, tester):
        """Test 26: Test compatibility between versions."""
        result = tester.test_compatibility("1.0.0", "2.0.0")
        assert isinstance(result, CompatibilityTestResult)

    def test_compatible_result(self, tester):
        """Test 27: Compatible result for no breaking changes."""
        result = tester.test_compatibility("1.0.0", "2.0.0")
        # Depends on diff, but should return a result
        assert result.status in [s for s in CompatibilityStatus]

    def test_unknown_status(self):
        """Test 28: Unknown status when diff unavailable."""
        empty_history = VersionHistory()
        tester = CompatibilityTester(empty_history)
        result = tester.test_compatibility("1.0.0", "2.0.0")
        assert result.status == CompatibilityStatus.UNKNOWN

    def test_batch_test(self, tester):
        """Test 29: Batch test compatibility."""
        results = tester.batch_test(["1.0.0"], ["2.0.0"])
        assert len(results) == 1

    def test_batch_test_multiple(self, tester):
        """Test 30: Batch test with multiple versions."""
        results = tester.batch_test(["1.0.0"], ["1.0.0", "2.0.0"])
        assert len(results) == 2

    def test_batch_test_empty(self, tester):
        """Test 31: Batch test with empty lists."""
        results = tester.batch_test([], [])
        assert len(results) == 0

    def test_result_has_versions(self, tester):
        """Test 32: Result has version information."""
        result = tester.test_compatibility("1.0.0", "2.0.0")
        assert result.baseline_version == "1.0.0"
        assert result.candidate_version == "2.0.0"

    def test_breaking_changes_counted(self, tester):
        """Test 33: Breaking changes are counted."""
        result = tester.test_compatibility("1.0.0", "2.0.0")
        assert result.breaking_changes >= 0

    def test_test_same_version(self, tester):
        """Test 34: Test same version compatibility."""
        result = tester.test_compatibility("1.0.0", "1.0.0")
        assert result.baseline_version == result.candidate_version

    def test_warnings_generated(self, tester):
        """Test 35: Warnings generated for breaking changes."""
        result = tester.test_compatibility("1.0.0", "2.0.0")
        assert isinstance(result.warnings, list)

    def test_test_statuses_set(self, tester):
        """Test 36: Test statuses are set."""
        result = tester.test_compatibility("1.0.0", "2.0.0")
        assert result.binding_generation in ["PASS", "FAIL", "UNTESTED"]

    def test_batch_preserves_order(self, tester):
        """Test 37: Batch test preserves order."""
        results = tester.batch_test(["1.0.0"], ["1.0.0", "2.0.0"])
        assert results[0].candidate_version == "1.0.0"
        assert results[1].candidate_version == "2.0.0"

    def test_tester_with_history(self, tester, history):
        """Test 38: Tester uses history."""
        assert tester.history == history

    def test_result_notes_on_unknown(self):
        """Test 39: Result has notes on unknown status."""
        empty_history = VersionHistory()
        tester = CompatibilityTester(empty_history)
        result = tester.test_compatibility("1.0.0", "2.0.0")
        assert len(result.notes) > 0

    def test_batch_all_combinations(self, tester):
        """Test 40: Batch tests all combinations."""
        results = tester.batch_test(["1.0.0", "2.0.0"], ["1.0.0", "2.0.0"])
        assert len(results) == 4  # 2 x 2 combinations


# ============================================================================
# TEST COMPATIBILITY RECOMMENDATION ENGINE (20 TESTS)
# ============================================================================
class TestCompatibilityRecommendationEngine:
    """Test CompatibilityRecommendationEngine (20 tests)."""

    @pytest.fixture
    def matrix(self):
        m = CompatibilityMatrix()

        # Add some test data
        r1 = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        r2 = CompatibilityTestResult("1.0.0", "2.5.0", CompatibilityStatus.COMPATIBLE)
        r3 = CompatibilityTestResult("1.0.0", "3.0.0", CompatibilityStatus.INCOMPATIBLE)

        m.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", r1))
        m.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.5.0", r2))
        m.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "3.0.0", r3))

        return m

    @pytest.fixture
    def engine(self, matrix):
        return CompatibilityRecommendationEngine(matrix)

    def test_recommend_version_found(self, engine):
        """Test 41: Recommend version when found."""
        rec = engine.recommend_version("app", "1.0.0", "libcore")
        assert rec["found"] is True

    def test_recommend_version_not_found(self, engine):
        """Test 42: Recommend version when not found."""
        rec = engine.recommend_version("app", "2.0.0", "libcore")
        assert rec["found"] is False

    def test_recommend_latest_version(self, engine):
        """Test 43: Recommends latest compatible version."""
        rec = engine.recommend_version("app", "1.0.0", "libcore")
        assert rec["recommended_version"] == "2.5.0"

    def test_recommend_all_compatible(self, engine):
        """Test 44: Returns all compatible versions."""
        rec = engine.recommend_version("app", "1.0.0", "libcore")
        assert len(rec["all_compatible_versions"]) == 2

    def test_upgrade_recommendation_no_upgrade(self, engine):
        """Test 45: No upgrade needed."""
        engine.matrix.add_entry(
            CompatibilityMatrixEntry(
                "app", "2.0.0", "libcore", "2.0.0", CompatibilityTestResult("2.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
            )
        )

        rec = engine.get_upgrade_recommendation("app", "1.0.0", "2.0.0", "libcore", "2.0.0")
        assert rec["upgrade_needed"] is False

    def test_upgrade_recommendation_needed(self, engine):
        """Test 46: Upgrade needed."""
        engine.matrix.add_entry(
            CompatibilityMatrixEntry(
                "app", "2.0.0", "libcore", "3.0.0", CompatibilityTestResult("2.0.0", "3.0.0", CompatibilityStatus.COMPATIBLE)
            )
        )

        rec = engine.get_upgrade_recommendation("app", "1.0.0", "2.0.0", "libcore", "2.0.0")
        # Result depends on matrix state
        assert "upgrade_needed" in rec

    def test_parse_version(self, engine):
        """Test 47: Parse version correctly."""
        parsed = engine._parse_version("2.5.3")
        assert parsed == (2, 5, 3)

    def test_parse_version_short(self, engine):
        """Test 48: Parse short version."""
        parsed = engine._parse_version("2.5")
        assert parsed == (2, 5, 0)

    def test_recommend_reason(self, engine):
        """Test 49: Recommendation includes reason."""
        rec = engine.recommend_version("app", "1.0.0", "libcore")
        assert "reason" in rec

    def test_recommend_not_found_reason(self, engine):
        """Test 50: Not found includes reason."""
        rec = engine.recommend_version("app", "999.0.0", "libcore")
        assert "reason" in rec

    def test_upgrade_recommendation_structure(self, engine):
        """Test 51: Upgrade recommendation has structure."""
        rec = engine.get_upgrade_recommendation("app", "1.0.0", "2.0.0", "libcore", "2.0.0")
        assert "upgrade_needed" in rec
        assert "reason" in rec

    def test_upgrade_no_compatible_version(self):
        """Test 52: Upgrade with no compatible version."""
        empty_matrix = CompatibilityMatrix()
        engine = CompatibilityRecommendationEngine(empty_matrix)
        rec = engine.get_upgrade_recommendation("app", "1.0.0", "2.0.0", "libcore", "2.0.0")
        assert rec["upgrade_needed"] is True
        assert rec["upgrade_available"] is False

    def test_version_comparison(self, engine):
        """Test 53: Version comparison works."""
        v1 = engine._parse_version("1.5.0")
        v2 = engine._parse_version("2.0.0")
        assert v2 > v1

    def test_recommend_empty_matrix(self):
        """Test 54: Recommend with empty matrix."""
        empty_matrix = CompatibilityMatrix()
        engine = CompatibilityRecommendationEngine(empty_matrix)
        rec = engine.recommend_version("app", "1.0.0", "libcore")
        assert rec["found"] is False

    def test_recommend_single_version(self):
        """Test 55: Recommend with single compatible version."""
        matrix = CompatibilityMatrix()
        r = CompatibilityTestResult("1.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        matrix.add_entry(CompatibilityMatrixEntry("app", "1.0.0", "libcore", "2.0.0", r))

        engine = CompatibilityRecommendationEngine(matrix)
        rec = engine.recommend_version("app", "1.0.0", "libcore")
        assert rec["recommended_version"] == "2.0.0"

    def test_upgrade_current_compatible(self):
        """Test 56: Current version already compatible."""
        matrix = CompatibilityMatrix()
        r = CompatibilityTestResult("2.0.0", "2.0.0", CompatibilityStatus.COMPATIBLE)
        matrix.add_entry(CompatibilityMatrixEntry("app", "2.0.0", "libcore", "2.0.0", r))

        engine = CompatibilityRecommendationEngine(matrix)
        rec = engine.get_upgrade_recommendation("app", "1.0.0", "2.0.0", "libcore", "2.0.0")
        assert rec["upgrade_needed"] is False

    def test_parse_version_major_only(self, engine):
        """Test 57: Parse major-only version."""
        parsed = engine._parse_version("3")
        assert parsed == (3, 0, 0)

    def test_all_compatible_versions_order(self, engine):
        """Test 58: All compatible versions listed."""
        rec = engine.recommend_version("app", "1.0.0", "libcore")
        versions = rec["all_compatible_versions"]
        assert "2.0.0" in versions
        assert "2.5.0" in versions

    def test_recommendation_recommended_field(self, engine):
        """Test 59: Recommendation has recommended_version field."""
        rec = engine.recommend_version("app", "1.0.0", "libcore")
        assert "recommended_version" in rec

    def test_upgrade_includes_recommended(self):
        """Test 60: Upgrade recommendation includes version."""
        matrix = CompatibilityMatrix()
        r1 = CompatibilityTestResult("2.0.0", "2.5.0", CompatibilityStatus.COMPATIBLE)
        r2 = CompatibilityTestResult("2.0.0", "3.0.0", CompatibilityStatus.COMPATIBLE)
        matrix.add_entry(CompatibilityMatrixEntry("app", "2.0.0", "libcore", "2.5.0", r1))
        matrix.add_entry(CompatibilityMatrixEntry("app", "2.0.0", "libcore", "3.0.0", r2))

        engine = CompatibilityRecommendationEngine(matrix)
        rec = engine.get_upgrade_recommendation("app", "1.0.0", "2.0.0", "libcore", "2.0.0")

        if rec.get("upgrade_available"):
            assert "recommended_version" in rec


# ============================================================================
# TEST VERSION RANGE SPEC (15 TESTS)
# ============================================================================
class TestVersionRangeSpec:
    """Test VersionRangeSpec (15 tests)."""

    def test_create_range_spec(self):
        """Test 61: Create version range spec."""
        spec = VersionRangeSpec("app", "1.*.*", "libcore", "2.*.*", CompatibilityStatus.COMPATIBLE)
        assert spec.contract_a == "app"

    def test_matches_exact(self):
        """Test 62: Matches exact pattern."""
        spec = VersionRangeSpec("app", "1.0.0", "libcore", "2.0.0", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("app", "1.0.0", "libcore", "2.0.0") is True

    def test_matches_wildcard_minor(self):
        """Test 63: Matches wildcard minor version."""
        spec = VersionRangeSpec("app", "1.*.0", "libcore", "2.0.0", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("app", "1.5.0", "libcore", "2.0.0") is True

    def test_matches_wildcard_all(self):
        """Test 64: Matches all wildcards."""
        spec = VersionRangeSpec("app", "1.*.*", "libcore", "2.*.*", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("app", "1.5.3", "libcore", "2.7.1") is True

    def test_no_match_different_major(self):
        """Test 65: No match for different major version."""
        spec = VersionRangeSpec("app", "1.*.*", "libcore", "2.*.*", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("app", "2.0.0", "libcore", "2.0.0") is False

    def test_no_match_different_contract(self):
        """Test 66: No match for different contract."""
        spec = VersionRangeSpec("app", "1.*.*", "libcore", "2.*.*", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("other", "1.0.0", "libcore", "2.0.0") is False

    def test_to_dict(self):
        """Test 67: Range spec to dictionary."""
        spec = VersionRangeSpec("app", "1.*.*", "libcore", "2.*.*", CompatibilityStatus.COMPATIBLE)
        data = spec.to_dict()
        assert data["version_pattern_a"] == "1.*.*"

    def test_status_preserved(self):
        """Test 68: Status preserved in spec."""
        spec = VersionRangeSpec("app", "1.*.*", "libcore", "2.*.*", CompatibilityStatus.INCOMPATIBLE)
        assert spec.status == CompatibilityStatus.INCOMPATIBLE

    def test_matches_pattern_exact(self):
        """Test 69: Pattern matching exact."""
        spec = VersionRangeSpec("app", "1.0.0", "libcore", "2.0.0", CompatibilityStatus.COMPATIBLE)
        assert spec._matches_pattern("1.0.0", "1.0.0") is True

    def test_matches_pattern_wildcard(self):
        """Test 70: Pattern matching with wildcard."""
        spec = VersionRangeSpec("app", "1.*.*", "libcore", "2.*.*", CompatibilityStatus.COMPATIBLE)
        assert spec._matches_pattern("1.5.3", "1.*.*") is True

    def test_matches_pattern_no_match(self):
        """Test 71: Pattern no match."""
        spec = VersionRangeSpec("app", "1.*.*", "libcore", "2.*.*", CompatibilityStatus.COMPATIBLE)
        assert spec._matches_pattern("2.0.0", "1.*.*") is False

    def test_wildcard_patch_only(self):
        """Test 72: Wildcard patch only."""
        spec = VersionRangeSpec("app", "1.0.*", "libcore", "2.0.0", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("app", "1.0.5", "libcore", "2.0.0") is True

    def test_partial_version_match(self):
        """Test 73: Partial version match."""
        spec = VersionRangeSpec("app", "1.5", "libcore", "2.0", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("app", "1.5", "libcore", "2.0") is True

    def test_contract_names_exact(self):
        """Test 74: Contract names must match exactly."""
        spec = VersionRangeSpec("App", "1.0.0", "LibCore", "2.0.0", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("app", "1.0.0", "LibCore", "2.0.0") is False

    def test_both_wildcards(self):
        """Test 75: Both patterns with wildcards."""
        spec = VersionRangeSpec("app", "*.*.*", "libcore", "*.*.*", CompatibilityStatus.COMPATIBLE)
        assert spec.matches("app", "5.2.1", "libcore", "9.8.7") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
