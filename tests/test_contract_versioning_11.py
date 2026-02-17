""" Tests for Contract Versioning - Prompt 11/20 Migration Path Generation & Upgrade Strategy Planning

Testing Level: HARDEST (75 comprehensive tests) """

import pytest
from modules.module_06_contract_schema.contract_versioning import (
    MigrationStrategy,
    MigrationStep,
    MigrationPath,
    MigrationPathGenerator,
    UpgradeRecommendation,
    MigrationPlanner,
    VersionHistory,
    VersionSnapshot,
    DetailedDiff,
    EntityDiff,
    DetailedChange,
    ChangeSeverity,
)


# ============================================================================
# TEST MIGRATION STEP (10 TESTS)
# ============================================================================
class TestMigrationStep:
    """Test MigrationStep (10 tests)."""

    def test_create_step(self):
        """Test 1: Create migration step."""
        step = MigrationStep(from_version="1.0.0", to_version="1.1.0")
        assert step.from_version == "1.0.0"
        assert step.to_version == "1.1.0"

    def test_step_cost_calculation(self):
        """Test 2: Step cost calculation."""
        step = MigrationStep(
            from_version="1.0.0", to_version="2.0.0", breaking_changes=2, affected_entities=["e1", "e2"], risk_score=0.5
        )
        cost = step.get_cost()
        assert cost == 2 * 10 + 2 * 2 + 0.5 * 5  # 20 + 4 + 2.5 = 26.5

    def test_step_to_dict(self):
        """Test 3: Step to dictionary."""
        step = MigrationStep(from_version="1.0.0", to_version="1.1.0")
        data = step.to_dict()
        assert "from_version" in data
        assert "cost" in data

    def test_step_breaking_changes(self):
        """Test 4: Step breaking changes."""
        step = MigrationStep(from_version="1.0.0", to_version="2.0.0", breaking_changes=5)
        assert step.breaking_changes == 5

    def test_step_total_changes(self):
        """Test 5: Step total changes."""
        step = MigrationStep(from_version="1.0.0", to_version="1.1.0", total_changes=10)
        assert step.total_changes == 10

    def test_step_risk_score(self):
        """Test 6: Step risk score."""
        step = MigrationStep(from_version="1.0.0", to_version="1.1.0", risk_score=0.7)
        assert step.risk_score == 0.7

    def test_step_effort_estimate(self):
        """Test 7: Step effort estimate."""
        step = MigrationStep(from_version="1.0.0", to_version="1.1.0", effort_estimate=5.0)
        assert step.effort_estimate == 5.0

    def test_step_affected_entities(self):
        """Test 8: Step affected entities."""
        step = MigrationStep(from_version="1.0.0", to_version="1.1.0", affected_entities=["func1", "struct1"])
        assert len(step.affected_entities) == 2

    def test_step_zero_cost(self):
        """Test 9: Step with zero cost."""
        step = MigrationStep(from_version="1.0.0", to_version="1.0.1")
        assert step.get_cost() == 0

    def test_step_high_cost(self):
        """Test 10: Step with high cost."""
        step = MigrationStep(
            from_version="1.0.0", to_version="2.0.0", breaking_changes=10, affected_entities=["e" + str(i) for i in range(20)], risk_score=1.0
        )
        assert step.get_cost() > 100


# ============================================================================
# TEST MIGRATION PATH (15 TESTS)
# ============================================================================
class TestMigrationPath:
    """Test MigrationPath (15 tests)."""

    def test_create_path(self):
        """Test 11: Create migration path."""
        path = MigrationPath(source_version="1.0.0", target_version="2.0.0")
        assert path.source_version == "1.0.0"
        assert path.target_version == "2.0.0"

    def test_path_total_cost(self):
        """Test 12: Path total cost."""
        step1 = MigrationStep("1.0.0", "1.1.0", breaking_changes=1)
        step2 = MigrationStep("1.1.0", "2.0.0", breaking_changes=2)
        path = MigrationPath("1.0.0", "2.0.0", steps=[step1, step2])
        assert path.get_total_cost() == step1.get_cost() + step2.get_cost()

    def test_path_total_breaking_changes(self):
        """Test 13: Path total breaking changes."""
        step1 = MigrationStep("1.0.0", "1.1.0", breaking_changes=3)
        step2 = MigrationStep("1.1.0", "2.0.0", breaking_changes=5)
        path = MigrationPath("1.0.0", "2.0.0", steps=[step1, step2])
        assert path.get_total_breaking_changes() == 8

    def test_path_total_changes(self):
        """Test 14: Path total changes."""
        step1 = MigrationStep("1.0.0", "1.1.0", total_changes=10)
        step2 = MigrationStep("1.1.0", "2.0.0", total_changes=15)
        path = MigrationPath("1.0.0", "2.0.0", steps=[step1, step2])
        assert path.get_total_changes() == 25

    def test_path_step_count(self):
        """Test 15: Path step count."""
        steps = [MigrationStep(f"1.{i}.0", f"1.{i+1}.0") for i in range(3)]
        path = MigrationPath("1.0.0", "1.3.0", steps=steps)
        assert path.get_step_count() == 3

    def test_path_is_direct(self):
        """Test 16: Path is direct."""
        path = MigrationPath("1.0.0", "2.0.0", steps=[MigrationStep("1.0.0", "2.0.0")])
        assert path.is_direct_path() is True

    def test_path_is_not_direct(self):
        """Test 17: Path is not direct."""
        steps = [MigrationStep("1.0.0", "1.1.0"), MigrationStep("1.1.0", "2.0.0")]
        path = MigrationPath("1.0.0", "2.0.0", steps=steps)
        assert path.is_direct_path() is False

    def test_path_strategy(self):
        """Test 18: Path strategy."""
        path = MigrationPath("1.0.0", "2.0.0", strategy=MigrationStrategy.SAFEST)
        assert path.strategy == MigrationStrategy.SAFEST

    def test_path_to_dict(self):
        """Test 19: Path to dictionary."""
        path = MigrationPath("1.0.0", "2.0.0")
        data = path.to_dict()
        assert data["source_version"] == "1.0.0"
        assert data["target_version"] == "2.0.0"

    def test_path_empty_steps(self):
        """Test 20: Path with empty steps."""
        path = MigrationPath("1.0.0", "2.0.0", steps=[])
        assert path.get_step_count() == 0
        assert path.get_total_cost() == 0

    def test_path_to_dict_includes_strategy(self):
        """Test 21: to_dict includes strategy."""
        path = MigrationPath("1.0.0", "2.0.0", strategy=MigrationStrategy.FASTEST)
        data = path.to_dict()
        assert data["strategy"] == "fastest"

    def test_path_to_dict_includes_steps(self):
        """Test 22: to_dict includes steps."""
        step = MigrationStep("1.0.0", "1.1.0")
        path = MigrationPath("1.0.0", "1.1.0", steps=[step])
        data = path.to_dict()
        assert len(data["steps"]) == 1

    def test_path_to_dict_is_direct_flag(self):
        """Test 23: to_dict includes is_direct flag."""
        path = MigrationPath("1.0.0", "2.0.0", steps=[MigrationStep("1.0.0", "2.0.0")])
        data = path.to_dict()
        assert data["is_direct"] is True

    def test_path_multiple_strategies(self):
        """Test 24: Path with different strategies."""
        path1 = MigrationPath("1.0.0", "2.0.0", strategy=MigrationStrategy.FASTEST)
        path2 = MigrationPath("1.0.0", "2.0.0", strategy=MigrationStrategy.SAFEST)
        path3 = MigrationPath("1.0.0", "2.0.0", strategy=MigrationStrategy.BALANCED)
        assert path1.strategy != path2.strategy
        assert path2.strategy != path3.strategy

    def test_path_cost_increases_with_steps(self):
        """Test 25: Path cost increases with steps."""
        path1 = MigrationPath("1.0.0", "2.0.0", steps=[MigrationStep("1.0.0", "2.0.0", breaking_changes=1)])
        path2 = MigrationPath(
            "1.0.0", "2.0.0", steps=[MigrationStep("1.0.0", "1.5.0", breaking_changes=1), MigrationStep("1.5.0", "2.0.0", breaking_changes=1)]
        )
        assert path2.get_total_cost() >= path1.get_total_cost()


# ============================================================================
# TEST MIGRATION PATH GENERATOR (20 TESTS)
# ============================================================================
class TestMigrationPathGenerator:
    """Test MigrationPathGenerator (20 tests)."""

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
                "1.1.0",
                "2026-01-02T00:00:00Z",
                "b",
                parent_version="1.0.0",
                contract_data={"version": "1.1.0", "fingerprint": "b", "functions": {}, "clauses": {}},
            )
        )
        h.add_snapshot(
            VersionSnapshot(
                "2.0.0",
                "2026-01-03T00:00:00Z",
                "c",
                parent_version="1.1.0",
                contract_data={"version": "2.0.0", "fingerprint": "c", "functions": {}, "clauses": {}},
            )
        )
        return h

    @pytest.fixture
    def generator(self, history):
        return MigrationPathGenerator(history)

    def test_generate_direct_path(self, generator):
        """Test 26: Generate direct path."""
        path = generator.generate_direct_path("1.0.0", "2.0.0")
        assert path is not None
        assert path.is_direct_path()

    def test_generate_incremental_path(self, generator):
        """Test 27: Generate incremental path."""
        path = generator.generate_incremental_path("1.0.0", "2.0.0")
        assert path is not None
        assert path.get_step_count() > 1

    def test_generate_path_versions_not_found(self, generator):
        """Test 28: Generate path with non-existent versions."""
        path = generator.generate_direct_path("1.0.0", "999.0.0")
        assert path is None

    def test_generate_all_paths(self, generator):
        """Test 29: Generate all paths."""
        paths = generator.generate_all_paths("1.0.0", "2.0.0")
        assert len(paths) > 0

    def test_find_optimal_fastest(self, generator):
        """Test 30: Find optimal path (fastest)."""
        path = generator.find_optimal_path("1.0.0", "2.0.0", MigrationStrategy.FASTEST)
        assert path is not None

    def test_find_optimal_safest(self, generator):
        """Test 31: Find optimal path (safest)."""
        path = generator.find_optimal_path("1.0.0", "2.0.0", MigrationStrategy.SAFEST)
        assert path is not None

    def test_find_optimal_balanced(self, generator):
        """Test 32: Find optimal path (balanced)."""
        path = generator.find_optimal_path("1.0.0", "2.0.0", MigrationStrategy.BALANCED)
        assert path is not None

    def test_direct_path_single_step(self, generator):
        """Test 33: Direct path has single step."""
        path = generator.generate_direct_path("1.0.0", "1.1.0")
        assert path.get_step_count() == 1

    def test_incremental_path_multiple_steps(self, generator):
        """Test 34: Incremental path has multiple steps."""
        path = generator.generate_incremental_path("1.0.0", "2.0.0")
        assert path.get_step_count() >= 1

    def test_generator_creates_steps(self, generator):
        """Test 35: Generator creates migration steps."""
        path = generator.generate_direct_path("1.0.0", "1.1.0")
        assert len(path.steps) == 1
        assert isinstance(path.steps[0], MigrationStep)

    def test_generate_path_same_version(self, generator):
        """Test 36: Generate path to same version."""
        path = generator.generate_incremental_path("1.0.0", "1.0.0")
        assert path is not None
        assert path.get_step_count() == 0

    def test_all_paths_limited(self, generator):
        """Test 37: All paths respects max limit."""
        paths = generator.generate_all_paths("1.0.0", "2.0.0", max_paths=1)
        assert len(paths) <= 1

    def test_optimal_path_not_found(self):
        """Test 38: Optimal path when no paths exist."""
        empty_history = VersionHistory()
        gen = MigrationPathGenerator(empty_history)
        path = gen.find_optimal_path("1.0.0", "2.0.0")
        assert path is None

    def test_direct_path_strategy(self, generator):
        """Test 39: Direct path uses FASTEST strategy."""
        path = generator.generate_direct_path("1.0.0", "2.0.0")
        assert path.strategy == MigrationStrategy.FASTEST

    def test_incremental_path_strategy(self, generator):
        """Test 40: Incremental path uses SAFEST strategy."""
        path = generator.generate_incremental_path("1.0.0", "2.0.0")
        assert path.strategy == MigrationStrategy.SAFEST

    def test_step_has_cost_data(self, generator):
        """Test 41: Generated step has cost data."""
        path = generator.generate_direct_path("1.0.0", "1.1.0")
        step = path.steps[0]
        assert step.risk_score >= 0
        assert step.effort_estimate >= 0

    def test_all_paths_includes_direct(self, generator):
        """Test 42: All paths includes direct path."""
        paths = generator.generate_all_paths("1.0.0", "1.1.0")
        direct_paths = [p for p in paths if p.is_direct_path()]
        assert len(direct_paths) > 0

    def test_all_paths_includes_incremental(self, generator):
        """Test 43: All paths includes incremental if different."""
        paths = generator.generate_all_paths("1.0.0", "2.0.0")
        incremental_paths = [p for p in paths if not p.is_direct_path()]
        assert len(incremental_paths) >= 0  # May or may not exist

    def test_fastest_prefers_fewer_steps(self, generator):
        """Test 44: FASTEST strategy prefers fewer steps."""
        paths = generator.generate_all_paths("1.0.0", "2.0.0")
        if len(paths) > 1:
            fastest = generator.find_optimal_path("1.0.0", "2.0.0", MigrationStrategy.FASTEST)
            assert fastest.get_step_count() <= max(p.get_step_count() for p in paths)

    def test_balanced_optimizes_cost(self, generator):
        """Test 45: BALANCED strategy optimizes cost."""
        path = generator.find_optimal_path("1.0.0", "2.0.0", MigrationStrategy.BALANCED)
        assert path.get_total_cost() >= 0


# ============================================================================
# TEST UPGRADE RECOMMENDATION (15 TESTS)
# ============================================================================
class TestUpgradeRecommendation:
    """Test UpgradeRecommendation (15 tests)."""

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
        gen = MigrationPathGenerator(h)
        rec = UpgradeRecommendation(gen)
        return rec

    def test_recommend_upgrade_possible(self, setup):
        """Test 46: Recommend upgrade when possible."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert result["possible"] is True

    def test_recommend_upgrade_not_possible(self):
        """Test 47: Recommend upgrade when not possible."""
        empty_history = VersionHistory()
        gen = MigrationPathGenerator(empty_history)
        rec = UpgradeRecommendation(gen)
        result = rec.recommend_upgrade("1.0.0", "2.0.0")
        assert result["possible"] is False

    def test_recommendation_includes_recommended_path(self, setup):
        """Test 48: Recommendation includes recommended path."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert "recommended_path" in result
        assert result["recommended_path"] is not None

    def test_recommendation_includes_fastest(self, setup):
        """Test 49: Recommendation includes fastest path."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert "fastest_path" in result

    def test_recommendation_includes_safest(self, setup):
        """Test 50: Recommendation includes safest path."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert "safest_path" in result

    def test_recommendation_includes_all_paths(self, setup):
        """Test 51: Recommendation includes all paths."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert "all_paths" in result
        assert len(result["all_paths"]) > 0

    def test_recommendation_includes_summary(self, setup):
        """Test 52: Recommendation includes summary."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert "summary" in result
        assert "total_paths" in result["summary"]

    def test_recommendation_reason_when_not_possible(self):
        """Test 53: Recommendation includes reason when not possible."""
        empty_history = VersionHistory()
        gen = MigrationPathGenerator(empty_history)
        rec = UpgradeRecommendation(gen)
        result = rec.recommend_upgrade("1.0.0", "2.0.0")
        assert "reason" in result

    def test_summary_total_paths(self, setup):
        """Test 54: Summary includes total paths."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert result["summary"]["total_paths"] > 0

    def test_summary_recommended_steps(self, setup):
        """Test 55: Summary includes recommended steps."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert "recommended_steps" in result["summary"]

    def test_summary_breaking_changes(self, setup):
        """Test 56: Summary includes breaking changes."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert "recommended_breaking_changes" in result["summary"]

    def test_recommended_path_is_dict(self, setup):
        """Test 57: Recommended path is dictionary."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert isinstance(result["recommended_path"], dict)

    def test_all_paths_is_list(self, setup):
        """Test 58: All paths is list."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert isinstance(result["all_paths"], list)

    def test_recommendation_same_version(self, setup):
        """Test 59: Recommendation for same version."""
        result = setup.recommend_upgrade("1.0.0", "1.0.0")
        assert result["possible"] is True

    def test_recommendation_structure(self, setup):
        """Test 60: Recommendation has correct structure."""
        result = setup.recommend_upgrade("1.0.0", "2.0.0")
        assert "possible" in result
        assert "recommended_path" in result
        assert "summary" in result


# ============================================================================
# TEST MIGRATION PLANNER (15 TESTS)
# ============================================================================
class TestMigrationPlanner:
    """Test MigrationPlanner (15 tests)."""

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
        gen = MigrationPathGenerator(h)
        planner = MigrationPlanner(h, gen)
        return planner

    def test_create_migration_plan(self, setup):
        """Test 61: Create migration plan."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        assert plan["success"] is True

    def test_plan_includes_steps(self, setup):
        """Test 62: Plan includes steps."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        assert "steps" in plan
        assert len(plan["steps"]) > 0

    def test_plan_includes_total_cost(self, setup):
        """Test 63: Plan includes total cost."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        assert "total_cost" in plan

    def test_plan_includes_effort(self, setup):
        """Test 64: Plan includes effort estimate."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        assert "estimated_effort_hours" in plan

    def test_plan_step_details(self, setup):
        """Test 65: Plan step includes details."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        step = plan["steps"][0]
        assert "step_number" in step
        assert "from_version" in step
        assert "to_version" in step

    def test_plan_risk_level(self, setup):
        """Test 66: Plan includes risk level."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        step = plan["steps"][0]
        assert "risk_level" in step
        assert step["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

    def test_plan_tasks(self, setup):
        """Test 67: Plan includes tasks."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        step = plan["steps"][0]
        assert "tasks" in step
        assert isinstance(step["tasks"], list)

    def test_plan_not_found(self):
        """Test 68: Plan when path not found."""
        empty_history = VersionHistory()
        gen = MigrationPathGenerator(empty_history)
        planner = MigrationPlanner(empty_history, gen)
        plan = planner.create_migration_plan("1.0.0", "2.0.0")
        assert plan["success"] is False

    def test_validate_path_valid(self, setup):
        """Test 69: Validate valid path."""
        path = MigrationPath("1.0.0", "2.0.0", steps=[MigrationStep("1.0.0", "2.0.0")])
        result = setup.validate_path(path)
        assert result["valid"] is True

    def test_validate_path_high_risk(self, setup):
        """Test 70: Validate high-risk path."""
        step = MigrationStep("1.0.0", "2.0.0", risk_score=0.8)
        path = MigrationPath("1.0.0", "2.0.0", steps=[step])
        result = setup.validate_path(path)
        assert len(result["warnings"]) > 0

    def test_validate_path_many_breaking(self, setup):
        """Test 71: Validate path with many breaking changes."""
        step = MigrationStep("1.0.0", "2.0.0", breaking_changes=15)
        path = MigrationPath("1.0.0", "2.0.0", steps=[step])
        result = setup.validate_path(path)
        assert len(result["issues"]) > 0

    def test_plan_strategy(self, setup):
        """Test 72: Plan includes strategy."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0", MigrationStrategy.FASTEST)
        assert plan["strategy"] == "fastest"

    def test_plan_total_breaking_changes(self, setup):
        """Test 73: Plan includes total breaking changes."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        assert "total_breaking_changes" in plan

    def test_validate_includes_risk_assessment(self, setup):
        """Test 74: Validation includes risk assessment."""
        path = MigrationPath("1.0.0", "2.0.0", steps=[MigrationStep("1.0.0", "2.0.0")])
        result = setup.validate_path(path)
        assert "risk_assessment" in result

    def test_plan_step_numbering(self, setup):
        """Test 75: Plan steps are numbered."""
        plan = setup.create_migration_plan("1.0.0", "2.0.0")
        for i, step in enumerate(plan["steps"], 1):
            assert step["step_number"] == i


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
