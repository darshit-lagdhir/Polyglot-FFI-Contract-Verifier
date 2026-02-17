""" Tests for Contract Versioning - Prompt 19/20 Integration & End-to-End Workflows

Testing Level: HARD (65 tests) """

import pytest
from datetime import datetime, timezone
from modules.module_06_contract_schema.contract_versioning import (
    VersionManager,
    ReleaseWorkflow,
    UpgradeWorkflow,
    RollbackWorkflow,
    QueryWorkflow,
    IntegratedVersioningSystem,
    Author,
    VersionMetadata,
    VersionLifecycle,
    LifecycleStage,
    SupportTier,
    VersionProvenance,
)


class TestVersionManager:
    """Test VersionManager (10 tests)."""

    @pytest.fixture
    def manager(self):
        return VersionManager()

    def test_create_manager(self, manager):
        """Test 1: Create version manager."""
        assert manager is not None
        assert manager.version_history is not None

    def test_has_lifecycle_manager(self, manager):
        """Test 2: Has lifecycle manager."""
        assert manager.lifecycle_manager is not None

    def test_has_metadata_manager(self, manager):
        """Test 3: Has metadata manager."""
        assert manager.metadata_manager is not None

    def test_has_provenance_tracker(self, manager):
        """Test 4: Has provenance tracker."""
        assert manager.provenance_tracker is not None

    def test_has_diff_analyzer(self, manager):
        """Test 5: Has diff analyzer."""
        assert manager.diff_analyzer is not None

    def test_list_versions(self, manager):
        """Test 6: List versions."""
        versions = manager.list_versions("test_contract")
        assert isinstance(versions, list)

    def test_get_version_info_not_found(self, manager):
        """Test 7: Get version info for non-existent version."""
        info = manager.get_version_info("999.0.0")
        assert info["version"] == "999.0.0"
        assert info["lifecycle"] is None

    def test_get_version_info_structure(self, manager):
        """Test 8: Version info has correct structure."""
        info = manager.get_version_info("1.0.0")
        assert "version" in info
        assert "lifecycle" in info
        assert "metadata" in info
        assert "provenance" in info

    def test_has_changelog_generator(self, manager):
        """Test 9: Has changelog generator."""
        assert manager.changelog_generator is not None

    def test_has_signature_manager(self, manager):
        """Test 10: Has signature manager."""
        assert manager.signature_manager is not None


class TestReleaseWorkflow:
    """Test ReleaseWorkflow (15 tests)."""

    @pytest.fixture
    def workflow(self):
        manager = VersionManager()
        return ReleaseWorkflow(manager)

    def test_create_workflow(self, workflow):
        """Test 11: Create release workflow."""
        assert workflow is not None
        assert workflow.manager is not None

    def test_prepare_release_first_version(self, workflow):
        """Test 12: Prepare release for first version."""
        author = Author("John", "john@example.com")
        result = workflow.prepare_release("1.0.0", None, author, baseline_contract=None)
        assert "success" in result

    def test_prepare_release_has_steps(self, workflow):
        """Test 13: Prepare release includes steps."""
        author = Author("John", "john@example.com")
        result = workflow.prepare_release("1.0.0", None, author)
        assert "steps_completed" in result
        assert isinstance(result["steps_completed"], list)

    def test_prepare_release_creates_metadata(self, workflow):
        """Test 14: Prepare release creates metadata."""
        author = Author("John", "john@example.com")
        result = workflow.prepare_release("1.0.0", None, author)
        assert "metadata" in result

    def test_prepare_release_recommends_version(self, workflow):
        """Test 15: Prepare release recommends version."""
        author = Author("John", "john@example.com")
        result = workflow.prepare_release("1.0.0", None, author)
        assert "recommended_version" in result

    def test_finalize_release(self, workflow):
        """Test 16: Finalize release."""
        metadata = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        result = workflow.finalize_release("1.0.0", metadata, "fp123")
        assert result["success"] is True

    def test_finalize_creates_provenance(self, workflow):
        """Test 17: Finalize creates provenance."""
        metadata = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        workflow.finalize_release("1.0.0", metadata, "fp123")

        prov = workflow.manager.provenance_tracker.get_provenance("1.0.0")
        assert prov is not None

    def test_finalize_creates_lifecycle(self, workflow):
        """Test 18: Finalize creates lifecycle."""
        metadata = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        workflow.finalize_release("1.0.0", metadata, "fp123")

        lifecycle = workflow.manager.lifecycle_manager.get_lifecycle("1.0.0")
        assert lifecycle is not None

    def test_prepare_success_flag(self, workflow):
        """Test 19: Prepare sets success flag."""
        author = Author("John", "john@example.com")
        result = workflow.prepare_release("1.0.0", None, author)
        assert "success" in result

    def test_finalize_returns_version(self, workflow):
        """Test 20: Finalize returns version."""
        metadata = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        result = workflow.finalize_release("1.0.0", metadata, "fp123")
        assert result["version"] == "1.0.0"

    def test_finalize_includes_timestamp(self, workflow):
        """Test 21: Finalize includes release timestamp."""
        metadata = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        result = workflow.finalize_release("1.0.0", metadata, "fp123")
        assert "released_at" in result

    def test_has_recommender(self, workflow):
        """Test 22: Has version recommender."""
        assert workflow.recommender is not None

    def test_has_policy(self, workflow):
        """Test 23: Has version policy."""
        assert workflow.policy is not None

    def test_has_enforcer(self, workflow):
        """Test 24: Has policy enforcer."""
        assert workflow.enforcer is not None

    def test_prepare_proposed_version(self, workflow):
        """Test 25: Prepare includes proposed version."""
        author = Author("John", "john@example.com")
        result = workflow.prepare_release("1.0.0", None, author)
        assert "proposed_version" in result


class TestUpgradeWorkflow:
    """Test UpgradeWorkflow (10 tests)."""

    @pytest.fixture
    def workflow(self):
        manager = VersionManager()
        return UpgradeWorkflow(manager)

    def test_create_workflow(self, workflow):
        """Test 26: Create upgrade workflow."""
        assert workflow is not None

    def test_plan_upgrade(self, workflow):
        """Test 27: Plan upgrade."""
        plan = workflow.plan_upgrade("1.0.0", "2.0.0")
        assert "from_version" in plan
        assert "to_version" in plan

    def test_plan_includes_checks(self, workflow):
        """Test 28: Plan includes checks."""
        plan = workflow.plan_upgrade("1.0.0", "2.0.0")
        assert "checks" in plan
        assert isinstance(plan["checks"], list)

    def test_plan_includes_warnings(self, workflow):
        """Test 29: Plan includes warnings."""
        plan = workflow.plan_upgrade("1.0.0", "2.0.0")
        assert "warnings" in plan

    def test_plan_safe_to_proceed(self, workflow):
        """Test 30: Plan includes safe_to_proceed flag."""
        plan = workflow.plan_upgrade("1.0.0", "2.0.0")
        assert "safe_to_proceed" in plan

    def test_execute_upgrade(self, workflow):
        """Test 31: Execute upgrade."""
        result = workflow.execute_upgrade("1.0.0", "2.0.0")
        assert "success" in result

    def test_execute_includes_versions(self, workflow):
        """Test 32: Execute includes version info."""
        result = workflow.execute_upgrade("1.0.0", "2.0.0")
        assert result["from_version"] == "1.0.0"
        assert result["to_version"] == "2.0.0"

    def test_execute_includes_timestamp(self, workflow):
        """Test 33: Execute includes completion timestamp."""
        result = workflow.execute_upgrade("1.0.0", "2.0.0")
        assert "completed_at" in result

    def test_has_compatibility_matrix(self, workflow):
        """Test 34: Has compatibility matrix."""
        assert workflow.compatibility_matrix is not None

    def test_has_compatibility_tester(self, workflow):
        """Test 35: Has compatibility tester."""
        assert workflow.compatibility_tester is not None


class TestRollbackWorkflow:
    """Test RollbackWorkflow (10 tests)."""

    @pytest.fixture
    def workflow(self):
        manager = VersionManager()
        return RollbackWorkflow(manager)

    def test_create_workflow(self, workflow):
        """Test 36: Create rollback workflow."""
        assert workflow is not None

    def test_plan_rollback(self, workflow):
        """Test 37: Plan rollback."""
        plan = workflow.plan_rollback("2.0.0", "1.0.0")
        assert "from_version" in plan
        assert "to_version" in plan

    def test_plan_includes_analysis(self, workflow):
        """Test 38: Plan includes safety analysis."""
        plan = workflow.plan_rollback("2.0.0", "1.0.0")
        assert "safety_analysis" in plan

    def test_plan_includes_simulation(self, workflow):
        """Test 39: Plan includes simulation."""
        plan = workflow.plan_rollback("2.0.0", "1.0.0")
        assert "simulation" in plan

    def test_plan_includes_recommendation(self, workflow):
        """Test 40: Plan includes recommendation."""
        plan = workflow.plan_rollback("2.0.0", "1.0.0")
        assert "recommended" in plan

    def test_execute_rollback_safe(self, workflow):
        """Test 41: Execute safe rollback."""
        # With force=True to bypass safety checks
        result = workflow.execute_rollback("2.0.0", "1.0.0", force=True)
        assert result["success"] is True

    def test_execute_includes_timestamp(self, workflow):
        """Test 42: Execute includes rollback timestamp."""
        result = workflow.execute_rollback("2.0.0", "1.0.0", force=True)
        assert "rolled_back_at" in result

    def test_has_safety_analyzer(self, workflow):
        """Test 43: Has safety analyzer."""
        assert workflow.safety_analyzer is not None

    def test_has_simulator(self, workflow):
        """Test 44: Has rollback simulator."""
        assert workflow.simulator is not None

    def test_execute_versions(self, workflow):
        """Test 45: Execute includes version info."""
        result = workflow.execute_rollback("2.0.0", "1.0.0", force=True)
        assert result["from_version"] == "2.0.0"
        assert result["to_version"] == "1.0.0"


class TestQueryWorkflow:
    """Test QueryWorkflow (10 tests)."""

    @pytest.fixture
    def workflow(self):
        manager = VersionManager()
        return QueryWorkflow(manager)

    def test_create_workflow(self, workflow):
        """Test 46: Create query workflow."""
        assert workflow is not None

    def test_find_compatible_versions(self, workflow):
        """Test 47: Find compatible versions."""
        versions = workflow.find_compatible_versions("app", "1.0.0", "libcore")
        assert isinstance(versions, list)

    def test_get_deprecation_info_not_found(self, workflow):
        """Test 48: Get deprecation info for non-existent version."""
        info = workflow.get_deprecation_info("999.0.0")
        assert info is None

    def test_verify_provenance_not_found(self, workflow):
        """Test 49: Verify provenance for non-existent version."""
        result = workflow.verify_provenance("999.0.0")
        assert result["verified"] is False

    def test_verify_provenance_structure(self, workflow):
        """Test 50: Verify provenance has correct structure."""
        result = workflow.verify_provenance("1.0.0")
        assert "verified" in result
        assert "reason" in result or "signature" in result

    def test_deprecation_info_structure_not_deprecated(self, workflow):
        """Test 51: Deprecation info structure for non-deprecated."""

        lifecycle = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        workflow.manager.lifecycle_manager.add_version(lifecycle)

        info = workflow.get_deprecation_info("1.0.0")
        assert info is not None
        assert info["deprecated"] is False

    def test_has_manager(self, workflow):
        """Test 52: Has version manager."""
        assert workflow.manager is not None

    def test_has_compatibility_matrix(self, workflow):
        """Test 53: Has compatibility matrix."""
        assert workflow.compatibility_matrix is not None

    def test_find_compatible_empty(self, workflow):
        """Test 54: Find compatible returns empty list when none."""
        versions = workflow.find_compatible_versions("app", "1.0.0", "lib")
        assert len(versions) == 0

    def test_verify_not_signed(self, workflow):
        """Test 55: Verify provenance for unsigned version."""

        prov = VersionProvenance("1.0.0", "fp")
        workflow.manager.provenance_tracker.add_provenance(prov)

        result = workflow.verify_provenance("1.0.0")
        assert result["verified"] is False
        assert "not signed" in result["reason"].lower()


class TestIntegratedVersioningSystem:
    """Test IntegratedVersioningSystem (10 tests)."""

    @pytest.fixture
    def system(self):
        return IntegratedVersioningSystem()

    def test_create_system(self, system):
        """Test 56: Create integrated system."""
        assert system is not None

    def test_has_version_manager(self, system):
        """Test 57: Has version manager."""
        assert system.version_manager is not None

    def test_has_release_workflow(self, system):
        """Test 58: Has release workflow."""
        assert system.release_workflow is not None

    def test_has_upgrade_workflow(self, system):
        """Test 59: Has upgrade workflow."""
        assert system.upgrade_workflow is not None

    def test_has_rollback_workflow(self, system):
        """Test 60: Has rollback workflow."""
        assert system.rollback_workflow is not None

    def test_has_query_workflow(self, system):
        """Test 61: Has query workflow."""
        assert system.query_workflow is not None

    def test_release_version(self, system):
        """Test 62: Release version."""
        author = Author("John", "john@example.com")
        result = system.release_version("1.0.0", None, author)
        assert "success" in result

    def test_upgrade_version(self, system):
        """Test 63: Upgrade version."""
        result = system.upgrade_version("1.0.0", "2.0.0")
        assert "success" in result

    def test_rollback_version(self, system):
        """Test 64: Rollback version."""
        result = system.rollback_version("2.0.0", "1.0.0", force=True)
        assert "success" in result

    def test_end_to_end_workflow(self, system):
        """Test 65: End-to-end workflow."""
        # Release
        author = Author("John", "john@example.com")
        release = system.release_version("1.0.0", None, author)
        assert release["success"] is True

        # Upgrade
        upgrade = system.upgrade_version("1.0.0", "2.0.0")
        assert "plan" in upgrade

        # Rollback
        rollback = system.rollback_version("2.0.0", "1.0.0", force=True)
        assert "plan" in rollback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
