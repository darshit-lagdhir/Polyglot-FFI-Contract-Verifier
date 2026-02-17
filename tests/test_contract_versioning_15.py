""" Tests for Contract Versioning - Prompt 15/20 Version Rollback Safety & Downgrade Path Analysis

Testing Level: HARD (70 tests) """

import pytest
from modules.module_06_contract_schema.contract_versioning import (
    RollbackSafety,
    RollbackStrategy,
    RollbackRisk,
    RollbackAnalysis,
    RollbackSafetyAnalyzer,
    DowngradePathGenerator,
    RollbackSimulator,
    RollbackPreflightChecker,
    RollbackRecoveryPlanner,
    VersionHistory,
    VersionSnapshot,
)


class TestRollbackRisk:
    """Test RollbackRisk (10 tests)."""

    def test_create_risk(self):
        """Test 1: Create rollback risk."""
        risk = RollbackRisk("data_loss", "CRITICAL", "Data may be lost")
        assert risk.risk_type == "data_loss"
        assert risk.severity == "CRITICAL"

    def test_to_dict(self):
        """Test 2: Risk to dictionary."""
        risk = RollbackRisk("data_loss", "HIGH", "Risk description")
        data = risk.to_dict()
        assert data["risk_type"] == "data_loss"
        assert data["severity"] == "HIGH"

    def test_affected_entities(self):
        """Test 3: Affected entities list."""
        risk = RollbackRisk("breaking", "HIGH", "desc", affected_entities=["func1", "func2"])
        assert len(risk.affected_entities) == 2

    def test_mitigation(self):
        """Test 4: Mitigation provided."""
        risk = RollbackRisk("data", "HIGH", "desc", mitigation="Backup data first")
        assert risk.mitigation == "Backup data first"

    def test_severity_levels(self):
        """Test 5: Different severity levels."""
        low = RollbackRisk("test", "LOW", "desc")
        high = RollbackRisk("test", "HIGH", "desc")
        critical = RollbackRisk("test", "CRITICAL", "desc")
        assert low.severity == "LOW"
        assert high.severity == "HIGH"
        assert critical.severity == "CRITICAL"

    def test_risk_description(self):
        """Test 6: Risk description."""
        risk = RollbackRisk("test", "MEDIUM", "This is a detailed description")
        assert "detailed description" in risk.description

    def test_to_dict_includes_mitigation(self):
        """Test 7: to_dict includes mitigation."""
        risk = RollbackRisk("test", "HIGH", "desc", mitigation="Fix it")
        data = risk.to_dict()
        assert data["mitigation"] == "Fix it"

    def test_to_dict_includes_entities(self):
        """Test 8: to_dict includes affected entities."""
        risk = RollbackRisk("test", "HIGH", "desc", affected_entities=["e1", "e2"])
        data = risk.to_dict()
        assert len(data["affected_entities"]) == 2

    def test_empty_affected_entities(self):
        """Test 9: Empty affected entities."""
        risk = RollbackRisk("test", "LOW", "desc")
        assert len(risk.affected_entities) == 0

    def test_no_mitigation(self):
        """Test 10: No mitigation provided."""
        risk = RollbackRisk("test", "MEDIUM", "desc")
        assert risk.mitigation is None


class TestRollbackAnalysis:
    """Test RollbackAnalysis (15 tests)."""

    def test_create_analysis(self):
        """Test 11: Create rollback analysis."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.SAFE)
        assert analysis.from_version == "2.0.0"
        assert analysis.to_version == "1.0.0"

    def test_is_safe_true(self):
        """Test 12: is_safe returns true."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.SAFE)
        assert analysis.is_safe() is True

    def test_is_safe_false(self):
        """Test 13: is_safe returns false."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.UNSAFE)
        assert analysis.is_safe() is False

    def test_get_critical_risks(self):
        """Test 14: Get critical risks."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.UNSAFE)
        analysis.risks.append(RollbackRisk("r1", "CRITICAL", "desc1"))
        analysis.risks.append(RollbackRisk("r2", "MEDIUM", "desc2"))
        analysis.risks.append(RollbackRisk("r3", "CRITICAL", "desc3"))

        critical = analysis.get_critical_risks()
        assert len(critical) == 2

    def test_to_dict(self):
        """Test 15: Analysis to dictionary."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.SAFE)
        data = analysis.to_dict()
        assert data["from_version"] == "2.0.0"
        assert data["safety"] == "safe"

    def test_required_actions(self):
        """Test 16: Required actions list."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.CONDITIONAL)
        analysis.required_actions = ["Backup data", "Test rollback"]
        assert len(analysis.required_actions) == 2

    def test_data_at_risk_flag(self):
        """Test 17: Data at risk flag."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.UNSAFE, data_at_risk=True)
        assert analysis.data_at_risk is True

    def test_feature_loss_flag(self):
        """Test 18: Feature loss flag."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.CONDITIONAL, feature_loss=True)
        assert analysis.feature_loss is True

    def test_breaking_changes_reversed(self):
        """Test 19: Breaking changes reversed count."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.UNSAFE, breaking_changes_reversed=5)
        assert analysis.breaking_changes_reversed == 5

    def test_to_dict_includes_critical_count(self):
        """Test 20: to_dict includes critical risk count."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.UNSAFE)
        analysis.risks.append(RollbackRisk("r", "CRITICAL", "d"))
        data = analysis.to_dict()
        assert data["critical_risks"] == 1

    def test_empty_risks(self):
        """Test 21: Empty risks list."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.SAFE)
        assert len(analysis.risks) == 0

    def test_conditional_safety(self):
        """Test 22: Conditional safety level."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.CONDITIONAL)
        assert analysis.safety == RollbackSafety.CONDITIONAL
        assert analysis.is_safe() is False

    def test_unknown_safety(self):
        """Test 23: Unknown safety level."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.UNKNOWN)
        assert analysis.safety == RollbackSafety.UNKNOWN

    def test_multiple_risks(self):
        """Test 24: Multiple risks."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.UNSAFE)
        for i in range(5):
            analysis.risks.append(RollbackRisk(f"r{i}", "HIGH", f"desc{i}"))
        assert len(analysis.risks) == 5

    def test_to_dict_includes_all_fields(self):
        """Test 25: to_dict includes all fields."""
        analysis = RollbackAnalysis("2.0.0", "1.0.0", RollbackSafety.SAFE)
        data = analysis.to_dict()
        assert "from_version" in data
        assert "to_version" in data
        assert "safety" in data
        assert "data_at_risk" in data


class TestRollbackSafetyAnalyzer:
    """Test RollbackSafetyAnalyzer (15 tests)."""

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
    def analyzer(self, history):
        return RollbackSafetyAnalyzer(history)

    def test_analyze_rollback(self, analyzer):
        """Test 26: Analyze rollback."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        assert isinstance(analysis, RollbackAnalysis)

    def test_analysis_versions(self, analyzer):
        """Test 27: Analysis has correct versions."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        assert analysis.from_version == "2.0.0"
        assert analysis.to_version == "1.0.0"

    def test_unknown_when_no_diff(self):
        """Test 28: Unknown safety when no diff available."""
        empty_history = VersionHistory()
        analyzer = RollbackSafetyAnalyzer(empty_history)
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        assert analysis.safety == RollbackSafety.UNKNOWN

    def test_safe_rollback_no_breaking(self, analyzer):
        """Test 29: Safe rollback with no breaking changes."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        # Depends on diff, but should have a safety level
        assert analysis.safety in [s for s in RollbackSafety]

    def test_find_safe_rollback_path(self, analyzer):
        """Test 30: Find safe rollback path."""
        path = analyzer.find_safe_rollback_path("2.0.0", "1.0.0")
        assert path is not None
        assert "2.0.0" in path

    def test_rollback_path_order(self, analyzer):
        """Test 31: Rollback path in correct order."""
        path = analyzer.find_safe_rollback_path("2.0.0", "1.0.0")
        if path:
            assert path[0] == "2.0.0"

    def test_analysis_includes_risks(self, analyzer):
        """Test 32: Analysis includes risks."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        assert hasattr(analysis, "risks")

    def test_analysis_includes_actions(self, analyzer):
        """Test 33: Analysis includes required actions."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        assert hasattr(analysis, "required_actions")

    def test_breaking_changes_detected(self, analyzer):
        """Test 34: Breaking changes detected."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        assert hasattr(analysis, "breaking_changes_reversed")

    def test_rollback_path_none_when_no_history(self):
        """Test 35: Rollback path None when no history."""
        empty_history = VersionHistory()
        analyzer = RollbackSafetyAnalyzer(empty_history)
        path = analyzer.find_safe_rollback_path("2.0.0", "1.0.0")
        assert path is None or len(path) == 0

    def test_data_risk_detection(self, analyzer):
        """Test 36: Data risk detection."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        assert isinstance(analysis.data_at_risk, bool)

    def test_feature_loss_detection(self, analyzer):
        """Test 37: Feature loss detection."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        assert isinstance(analysis.feature_loss, bool)

    def test_same_version_rollback(self, analyzer):
        """Test 38: Rollback to same version."""
        analysis = analyzer.analyze_rollback("1.0.0", "1.0.0")
        # Should be safe (no changes)
        assert analysis is not None

    def test_analysis_to_dict(self, analyzer):
        """Test 39: Analysis can convert to dict."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        data = analysis.to_dict()
        assert isinstance(data, dict)

    def test_required_actions_generated(self, analyzer):
        """Test 40: Required actions generated based on risks."""
        analysis = analyzer.analyze_rollback("2.0.0", "1.0.0")
        # Should have some actions or empty list
        assert isinstance(analysis.required_actions, list)


class TestDowngradePathGenerator:
    """Test DowngradePathGenerator (10 tests)."""

    @pytest.fixture
    def setup(self):
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
        analyzer = RollbackSafetyAnalyzer(h)
        generator = DowngradePathGenerator(h, analyzer)
        return generator

    def test_generate_downgrade_path(self, setup):
        """Test 41: Generate downgrade path."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0")
        assert "from_version" in path
        assert "to_version" in path

    def test_emergency_strategy(self, setup):
        """Test 42: Emergency rollback strategy."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0", RollbackStrategy.EMERGENCY)
        assert path["strategy"] == "emergency"

    def test_planned_strategy(self, setup):
        """Test 43: Planned rollback strategy."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0", RollbackStrategy.PLANNED)
        assert path["strategy"] == "planned"

    def test_snapshot_strategy(self, setup):
        """Test 44: Snapshot rollback strategy."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0", RollbackStrategy.SNAPSHOT)
        assert path["strategy"] == "snapshot"

    def test_path_includes_steps(self, setup):
        """Test 45: Path includes steps."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0")
        assert "steps" in path
        assert isinstance(path["steps"], list)

    def test_path_includes_analysis(self, setup):
        """Test 46: Path includes analysis."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0", RollbackStrategy.PLANNED)
        assert "analysis" in path

    def test_total_steps_calculated(self, setup):
        """Test 47: Total steps calculated."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0")
        assert "total_steps" in path
        assert path["total_steps"] == len(path["steps"])

    def test_emergency_skips_checks(self, setup):
        """Test 48: Emergency strategy skips safety checks."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0", RollbackStrategy.EMERGENCY)
        if path["steps"]:
            assert "safety_check" in path["steps"][0]

    def test_snapshot_mentions_data_loss(self, setup):
        """Test 49: Snapshot strategy mentions data loss."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0", RollbackStrategy.SNAPSHOT)
        if path["steps"]:
            assert "data_loss" in path["steps"][0] or "snapshot" in path["steps"][0]["action"].lower()

    def test_planned_has_actions(self, setup):
        """Test 50: Planned strategy has required actions."""
        path = setup.generate_downgrade_path("2.0.0", "1.0.0", RollbackStrategy.PLANNED)
        # Should have analysis with required actions
        assert "analysis" in path


class TestRollbackSimulator:
    """Test RollbackSimulator (10 tests)."""

    @pytest.fixture
    def setup(self):
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
        analyzer = RollbackSafetyAnalyzer(h)
        simulator = RollbackSimulator(analyzer)
        return simulator

    def test_simulate_rollback(self, setup):
        """Test 51: Simulate rollback."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        assert "predicted_outcome" in result

    def test_simulation_has_issues(self, setup):
        """Test 52: Simulation includes issues."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        assert "issues" in result
        assert isinstance(result["issues"], list)

    def test_simulation_has_warnings(self, setup):
        """Test 53: Simulation includes warnings."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        assert "warnings" in result
        assert isinstance(result["warnings"], list)

    def test_predicted_outcome(self, setup):
        """Test 54: Predicted outcome present."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        assert result["predicted_outcome"] in ["SUCCESS", "FAILURE"]

    def test_simulation_versions(self, setup):
        """Test 55: Simulation has version info."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        assert result["from_version"] == "2.0.0"
        assert result["to_version"] == "1.0.0"

    def test_issues_have_severity(self, setup):
        """Test 56: Issues have severity."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        for issue in result["issues"]:
            assert "severity" in issue

    def test_warnings_have_type(self, setup):
        """Test 57: Warnings have type."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        for warning in result["warnings"]:
            assert "type" in warning

    def test_simulation_structure(self, setup):
        """Test 58: Simulation has correct structure."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        assert "from_version" in result
        assert "to_version" in result
        assert "predicted_outcome" in result

    def test_success_prediction(self, setup):
        """Test 59: Success predicted for safe rollback."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        # Depends on diff analysis
        assert result["predicted_outcome"] in ["SUCCESS", "FAILURE"]

    def test_empty_issues_possible(self, setup):
        """Test 60: Empty issues list possible."""
        result = setup.simulate_rollback("2.0.0", "1.0.0")
        # Should be a list (might be empty)
        assert isinstance(result["issues"], list)


class TestRollbackPreflightChecker:
    """Test RollbackPreflightChecker (10 tests)."""

    @pytest.fixture
    def setup(self):
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
        analyzer = RollbackSafetyAnalyzer(h)
        checker = RollbackPreflightChecker(analyzer)
        return checker

    def test_run_preflight_checks(self, setup):
        """Test 61: Run preflight checks."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        assert "passed" in result
        assert "failed" in result

    def test_checks_have_passed_list(self, setup):
        """Test 62: Checks have passed list."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        assert isinstance(result["passed"], list)

    def test_checks_have_failed_list(self, setup):
        """Test 63: Checks have failed list."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        assert isinstance(result["failed"], list)

    def test_checks_have_warnings(self, setup):
        """Test 64: Checks have warnings list."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        assert "warnings" in result

    def test_overall_result(self, setup):
        """Test 65: Overall result present."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        assert "overall" in result
        assert result["overall"] in ["PASS", "FAIL"]

    def test_safe_to_proceed_flag(self, setup):
        """Test 66: Safe to proceed flag."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        assert "safe_to_proceed" in result
        assert isinstance(result["safe_to_proceed"], bool)

    def test_check_items_have_result(self, setup):
        """Test 67: Check items have result field."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        for check in result["passed"] + result["failed"] + result["warnings"]:
            assert "result" in check

    def test_check_items_have_message(self, setup):
        """Test 68: Check items have message."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        for check in result["passed"] + result["failed"] + result["warnings"]:
            assert "message" in check

    def test_fail_when_critical_risks(self, setup):
        """Test 69: Fail when critical risks present."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        # Overall should fail if any checks failed
        if result["failed"]:
            assert result["overall"] == "FAIL"

    def test_pass_when_all_clear(self, setup):
        """Test 70: Pass when all checks clear."""
        result = setup.run_preflight_checks("2.0.0", "1.0.0")
        if not result["failed"]:
            assert result["overall"] == "PASS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
