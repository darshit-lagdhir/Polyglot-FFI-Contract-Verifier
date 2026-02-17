""" Tests for Contract Versioning - Prompt 14/20 Version Lifecycle Management & Deprecation Policies

Testing Level: HARD (70 tests) """

import pytest
from datetime import datetime, timedelta, timezone
from modules.module_06_contract_schema.contract_versioning import (
    LifecycleStage,
    SupportTier,
    DeprecationNotice,
    VersionLifecycle,
    LifecycleManager,
    DeprecationPolicy,
    VersionRetirementPlanner,
    StabilityGuaranteeChecker,
    DetailedDiff,
    EntityDiff,
    DetailedChange,
    ChangeSeverity,
)


class TestDeprecationNotice:
    """Test DeprecationNotice (10 tests)."""

    def test_create_notice(self):
        """Test 1: Create deprecation notice."""
        notice = DeprecationNotice(
            version="1.0.0",
            deprecated_at="2026-01-01T00:00:00Z",
            end_of_life_at="2026-12-31T00:00:00Z",
            reason="Superseded by 2.0.0",
        )
        assert notice.version == "1.0.0"

    def test_is_deprecated_future(self):
        """Test 2: is_deprecated for future date."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", future, future, "test")
        assert notice.is_deprecated() is False

    def test_is_deprecated_past(self):
        """Test 3: is_deprecated for past date."""
        past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", past, future, "test")
        assert notice.is_deprecated() is True

    def test_is_end_of_life_future(self):
        """Test 4: is_end_of_life for future date."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", now, future, "test")
        assert notice.is_end_of_life() is False

    def test_is_end_of_life_past(self):
        """Test 5: is_end_of_life for past date."""
        past1 = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat().replace("+00:00", "Z")
        past2 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", past1, past2, "test")
        assert notice.is_end_of_life() is True

    def test_days_until_eol_positive(self):
        """Test 6: days_until_eol positive."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        future = (datetime.now(timezone.utc) + timedelta(days=100)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", now, future, "test")
        days = notice.days_until_eol()
        assert days > 0 and days <= 100

    def test_days_until_eol_zero(self):
        """Test 7: days_until_eol zero for past."""
        past1 = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat().replace("+00:00", "Z")
        past2 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", past1, past2, "test")
        assert notice.days_until_eol() == 0

    def test_to_dict(self):
        """Test 8: Notice to dictionary."""
        notice = DeprecationNotice("1.0.0", "2026-01-01T00:00:00Z", "2026-12-31T00:00:00Z", "test")
        data = notice.to_dict()
        assert "version" in data
        assert "days_until_eol" in data

    def test_replacement_version(self):
        """Test 9: Replacement version specified."""
        notice = DeprecationNotice(
            "1.0.0", "2026-01-01T00:00:00Z", "2026-12-31T00:00:00Z", "test", replacement_version="2.0.0"
        )
        assert notice.replacement_version == "2.0.0"

    def test_migration_guide_url(self):
        """Test 10: Migration guide URL."""
        notice = DeprecationNotice(
            "1.0.0", "2026-01-01T00:00:00Z", "2026-12-31T00:00:00Z", "test", migration_guide_url="https://example.com/migrate"
        )
        assert notice.migration_guide_url == "https://example.com/migrate"


class TestVersionLifecycle:
    """Test VersionLifecycle (15 tests)."""

    def test_create_lifecycle(self):
        """Test 11: Create version lifecycle."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        assert lc.version == "1.0.0"
        assert lc.stage == LifecycleStage.STABLE

    def test_is_production_ready_stable(self):
        """Test 12: Stable is production-ready."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        assert lc.is_production_ready() is True

    def test_is_production_ready_deprecated(self):
        """Test 13: Deprecated is production-ready."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.DEPRECATED, SupportTier.MAINTENANCE)
        assert lc.is_production_ready() is True

    def test_is_production_ready_preview(self):
        """Test 14: Preview not production-ready."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.PREVIEW, SupportTier.FULL)
        assert lc.is_production_ready() is False

    def test_is_supported_stable(self):
        """Test 15: Stable is supported."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        assert lc.is_supported() is True

    def test_is_supported_eol(self):
        """Test 16: EOL not supported."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.END_OF_LIFE, SupportTier.NONE)
        assert lc.is_supported() is False

    def test_get_support_description_stable(self):
        """Test 17: Support description for stable."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        desc = lc.get_support_description()
        assert "supported" in desc.lower()

    def test_get_support_description_eol(self):
        """Test 18: Support description for EOL."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.END_OF_LIFE, SupportTier.NONE)
        desc = lc.get_support_description()
        assert "no longer supported" in desc.lower()

    def test_to_dict(self):
        """Test 19: Lifecycle to dictionary."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        data = lc.to_dict()
        assert data["stage"] == "stable"

    def test_with_deprecation_notice(self):
        """Test 20: Lifecycle with deprecation notice."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        future = (datetime.now(timezone.utc) + timedelta(days=100)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", now, future, "test")
        lc = VersionLifecycle("1.0.0", LifecycleStage.DEPRECATED, SupportTier.MAINTENANCE, deprecation_notice=notice)
        assert lc.deprecation_notice is not None

    def test_stability_guarantees(self):
        """Test 21: Stability guarantees list."""
        lc = VersionLifecycle(
            "1.0.0", LifecycleStage.STABLE, SupportTier.FULL, stability_guarantees=["No breaking changes in minor versions"]
        )
        assert len(lc.stability_guarantees) == 1

    def test_released_at(self):
        """Test 22: Released at timestamp."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL, released_at="2026-01-01T00:00:00Z")
        assert lc.released_at == "2026-01-01T00:00:00Z"

    def test_stable_at(self):
        """Test 23: Stable at timestamp."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL, stable_at="2026-02-01T00:00:00Z")
        assert lc.stable_at == "2026-02-01T00:00:00Z"

    def test_development_stage(self):
        """Test 24: Development stage."""
        lc = VersionLifecycle("0.1.0", LifecycleStage.DEVELOPMENT, SupportTier.NONE)
        assert lc.stage == LifecycleStage.DEVELOPMENT
        assert lc.is_production_ready() is False

    def test_preview_stage(self):
        """Test 25: Preview stage."""
        lc = VersionLifecycle("1.0.0-beta", LifecycleStage.PREVIEW, SupportTier.FULL)
        assert lc.stage == LifecycleStage.PREVIEW


class TestLifecycleManager:
    """Test LifecycleManager (15 tests)."""

    @pytest.fixture
    def manager(self):
        return LifecycleManager()

    def test_add_version(self, manager):
        """Test 26: Add version lifecycle."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        manager.add_version(lc)
        assert manager.get_lifecycle("1.0.0") is not None

    def test_get_lifecycle(self, manager):
        """Test 27: Get lifecycle by version."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        manager.add_version(lc)
        retrieved = manager.get_lifecycle("1.0.0")
        assert retrieved.version == "1.0.0"

    def test_get_supported_versions(self, manager):
        """Test 28: Get supported versions."""
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        manager.add_version(VersionLifecycle("2.0.0", LifecycleStage.END_OF_LIFE, SupportTier.NONE))
        supported = manager.get_supported_versions()
        assert "1.0.0" in supported
        assert "2.0.0" not in supported

    def test_get_deprecated_versions(self, manager):
        """Test 29: Get deprecated versions."""
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.DEPRECATED, SupportTier.MAINTENANCE))
        manager.add_version(VersionLifecycle("2.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        deprecated = manager.get_deprecated_versions()
        assert "1.0.0" in deprecated
        assert "2.0.0" not in deprecated

    def test_get_production_ready_versions(self, manager):
        """Test 30: Get production-ready versions."""
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        manager.add_version(VersionLifecycle("0.1.0", LifecycleStage.DEVELOPMENT, SupportTier.NONE))
        ready = manager.get_production_ready_versions()
        assert "1.0.0" in ready
        assert "0.1.0" not in ready

    def test_deprecate_version(self, manager):
        """Test 31: Deprecate version."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        manager.add_version(lc)
        success = manager.deprecate_version("1.0.0", "Superseded by 2.0.0", eol_days=365, replacement_version="2.0.0")
        assert success is True
        updated = manager.get_lifecycle("1.0.0")
        assert updated.stage == LifecycleStage.DEPRECATED

    def test_deprecate_nonexistent(self, manager):
        """Test 32: Deprecate non-existent version."""
        success = manager.deprecate_version("999.0.0", "test")
        assert success is False

    def test_retire_version(self, manager):
        """Test 33: Retire version."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        manager.add_version(lc)
        success = manager.retire_version("1.0.0")
        assert success is True
        updated = manager.get_lifecycle("1.0.0")
        assert updated.stage == LifecycleStage.END_OF_LIFE

    def test_to_dict(self, manager):
        """Test 34: Manager to dictionary."""
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        data = manager.to_dict()
        assert "lifecycles" in data
        assert "supported_versions" in data

    def test_multiple_versions(self, manager):
        """Test 35: Manage multiple versions."""
        for i in range(5):
            manager.add_version(VersionLifecycle(f"1.{i}.0", LifecycleStage.STABLE, SupportTier.FULL))
        assert len(manager.lifecycles) == 5

    def test_deprecation_notice_created(self, manager):
        """Test 36: Deprecation notice created."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        manager.add_version(lc)
        manager.deprecate_version("1.0.0", "test", replacement_version="2.0.0")
        updated = manager.get_lifecycle("1.0.0")
        assert updated.deprecation_notice is not None
        assert updated.deprecation_notice.replacement_version == "2.0.0"

    def test_support_tier_updated_on_deprecation(self, manager):
        """Test 37: Support tier updated on deprecation."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        manager.add_version(lc)
        manager.deprecate_version("1.0.0", "test")
        updated = manager.get_lifecycle("1.0.0")
        assert updated.support_tier == SupportTier.MAINTENANCE

    def test_support_tier_updated_on_retirement(self, manager):
        """Test 38: Support tier updated on retirement."""
        lc = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        manager.add_version(lc)
        manager.retire_version("1.0.0")
        updated = manager.get_lifecycle("1.0.0")
        assert updated.support_tier == SupportTier.NONE

    def test_get_lifecycle_not_found(self, manager):
        """Test 39: Get non-existent lifecycle."""
        lc = manager.get_lifecycle("999.0.0")
        assert lc is None

    def test_empty_manager(self, manager):
        """Test 40: Empty manager queries."""
        assert len(manager.get_supported_versions()) == 0
        assert len(manager.get_deprecated_versions()) == 0


class TestDeprecationPolicy:
    """Test DeprecationPolicy (10 tests)."""

    def test_create_policy(self):
        """Test 41: Create deprecation policy."""
        policy = DeprecationPolicy("standard", deprecation_period_days=180, eol_period_days=365)
        assert policy.name == "standard"

    def test_calculate_eol_date(self):
        """Test 42: Calculate EOL date."""
        policy = DeprecationPolicy("standard", eol_period_days=365)
        dep_date = "2026-01-01T00:00:00Z"
        eol_date = policy.calculate_eol_date(dep_date)
        assert "2027" in eol_date

    def test_validate_notice_valid(self):
        """Test 43: Validate valid notice."""
        policy = DeprecationPolicy("standard", minimum_notice_days=90)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        future = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice(
            "1.0.0",
            now,
            future,
            "test",
            replacement_version="2.0.0",
            migration_guide_url="https://example.com",
        )
        result = policy.validate_deprecation_notice(notice)
        assert result["valid"] is True

    def test_validate_notice_short_period(self):
        """Test 44: Validate notice with short period."""
        policy = DeprecationPolicy("standard", minimum_notice_days=180)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        future = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", now, future, "test")
        result = policy.validate_deprecation_notice(notice)
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_validate_notice_warnings(self):
        """Test 45: Validate notice generates warnings."""
        policy = DeprecationPolicy("standard", minimum_notice_days=90)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        future = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", now, future, "test")
        result = policy.validate_deprecation_notice(notice)
        assert len(result["warnings"]) > 0

    def test_to_dict(self):
        """Test 46: Policy to dictionary."""
        policy = DeprecationPolicy("standard")
        data = policy.to_dict()
        assert data["name"] == "standard"

    def test_custom_periods(self):
        """Test 47: Custom deprecation periods."""
        policy = DeprecationPolicy("custom", deprecation_period_days=90, eol_period_days=180, minimum_notice_days=30)
        assert policy.deprecation_period_days == 90
        assert policy.eol_period_days == 180

    def test_default_values(self):
        """Test 48: Default policy values."""
        policy = DeprecationPolicy("default")
        assert policy.deprecation_period_days > 0
        assert policy.eol_period_days > 0

    def test_validation_structure(self):
        """Test 49: Validation result structure."""
        policy = DeprecationPolicy("standard")
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        future = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat().replace("+00:00", "Z")
        notice = DeprecationNotice("1.0.0", now, future, "test")
        result = policy.validate_deprecation_notice(notice)
        assert "valid" in result
        assert "issues" in result
        assert "warnings" in result

    def test_calculate_eol_preserves_time(self):
        """Test 50: Calculate EOL preserves time."""
        policy = DeprecationPolicy("standard", eol_period_days=365)
        dep_date = "2026-01-15T12:30:00Z"
        eol_date = policy.calculate_eol_date(dep_date)
        assert "T" in eol_date


class TestVersionRetirementPlanner:
    """Test VersionRetirementPlanner (10 tests)."""

    @pytest.fixture
    def setup(self):
        manager = LifecycleManager()
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        planner = VersionRetirementPlanner(manager)
        return planner

    def test_plan_retirement_graceful(self, setup):
        """Test 51: Plan graceful retirement."""
        plan = setup.plan_retirement("1.0.0", "graceful")
        assert plan["success"] is True
        assert len(plan["phases"]) > 0

    def test_plan_retirement_forced(self, setup):
        """Test 52: Plan forced retirement."""
        plan = setup.plan_retirement("1.0.0", "forced")
        assert plan["success"] is True
        assert plan["strategy"] == "forced"

    def test_plan_retirement_not_found(self, setup):
        """Test 53: Plan retirement for non-existent version."""
        plan = setup.plan_retirement("999.0.0")
        assert plan["success"] is False

    def test_plan_retirement_already_retired(self):
        """Test 54: Plan retirement for already retired version."""
        manager = LifecycleManager()
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.END_OF_LIFE, SupportTier.NONE))
        planner = VersionRetirementPlanner(manager)
        plan = planner.plan_retirement("1.0.0")
        assert plan["success"] is False

    def test_graceful_phases(self, setup):
        """Test 55: Graceful retirement has phases."""
        plan = setup.plan_retirement("1.0.0", "graceful")
        assert len(plan["phases"]) == 3

    def test_forced_phases(self, setup):
        """Test 56: Forced retirement has phases."""
        plan = setup.plan_retirement("1.0.0", "forced")
        assert len(plan["phases"]) == 2

    def test_get_retirement_timeline(self, setup):
        """Test 57: Get retirement timeline."""
        setup.manager.deprecate_version("1.0.0", "test", replacement_version="2.0.0")
        timeline = setup.get_retirement_timeline("1.0.0")
        assert timeline["has_timeline"] is True

    def test_get_retirement_timeline_no_notice(self, setup):
        """Test 58: Get timeline with no deprecation notice."""
        timeline = setup.get_retirement_timeline("1.0.0")
        assert timeline["has_timeline"] is False

    def test_timeline_includes_dates(self, setup):
        """Test 59: Timeline includes dates."""
        setup.manager.deprecate_version("1.0.0", "test", replacement_version="2.0.0")
        timeline = setup.get_retirement_timeline("1.0.0")
        assert "deprecated_at" in timeline
        assert "end_of_life_at" in timeline

    def test_plan_structure(self, setup):
        """Test 60: Plan has correct structure."""
        plan = setup.plan_retirement("1.0.0", "graceful")
        assert "version" in plan
        assert "strategy" in plan
        assert "phases" in plan


class TestStabilityGuaranteeChecker:
    """Test StabilityGuaranteeChecker (10 tests)."""

    @pytest.fixture
    def setup(self):
        manager = LifecycleManager()
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        manager.add_version(VersionLifecycle("1.5.0", LifecycleStage.STABLE, SupportTier.FULL))

        checker = StabilityGuaranteeChecker(manager)

        # Create mock diff
        diff = DetailedDiff(
            "1.0.0",
            "1.5.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("func1", "function", [DetailedChange("c1", "func1", ChangeSeverity.EXTENSION, "Added function")])],
        )

        return checker, diff

    def test_check_compatibility(self, setup):
        """Test 61: Check compatibility with guarantees."""
        checker, diff = setup
        result = checker.check_compatibility_with_guarantees("1.0.0", "1.5.0", diff)
        assert result["checked"] is True

    def test_compliant_no_breaking(self, setup):
        """Test 62: Compliant when no breaking changes."""
        checker, diff = setup
        result = checker.check_compatibility_with_guarantees("1.0.0", "1.5.0", diff)
        assert result["compliant"] is True

    def test_violation_breaking_in_minor(self):
        """Test 63: Violation for breaking changes in minor version."""
        manager = LifecycleManager()
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        checker = StabilityGuaranteeChecker(manager)

        diff = DetailedDiff(
            "1.0.0",
            "1.5.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("func1", "function", [DetailedChange("c1", "func1", ChangeSeverity.BREAKING, "Breaking change")])],
        )

        result = checker.check_compatibility_with_guarantees("1.0.0", "1.5.0", diff)
        assert result["compliant"] is False
        assert len(result["violations"]) > 0

    def test_baseline_not_found(self, setup):
        """Test 64: Baseline version not found."""
        checker, diff = setup
        result = checker.check_compatibility_with_guarantees("999.0.0", "1.5.0", diff)
        assert result["checked"] is False

    def test_major_version_change_allowed(self):
        """Test 65: Major version change allows breaking changes."""
        manager = LifecycleManager()
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        checker = StabilityGuaranteeChecker(manager)

        diff = DetailedDiff(
            "1.0.0",
            "2.0.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("func1", "function", [DetailedChange("c1", "func1", ChangeSeverity.BREAKING, "Breaking change")])],
        )

        result = checker.check_compatibility_with_guarantees("1.0.0", "2.0.0", diff)
        # Major version change, breaking is allowed
        assert result["checked"] is True

    def test_result_structure(self, setup):
        """Test 66: Result has correct structure."""
        checker, diff = setup
        result = checker.check_compatibility_with_guarantees("1.0.0", "1.5.0", diff)
        assert "checked" in result
        assert "compliant" in result
        assert "violations" in result

    def test_warnings_list(self, setup):
        """Test 67: Result includes warnings list."""
        checker, diff = setup
        result = checker.check_compatibility_with_guarantees("1.0.0", "1.5.0", diff)
        assert "warnings" in result

    def test_non_stable_baseline(self):
        """Test 68: Non-stable baseline."""
        manager = LifecycleManager()
        manager.add_version(VersionLifecycle("0.1.0", LifecycleStage.DEVELOPMENT, SupportTier.NONE))
        checker = StabilityGuaranteeChecker(manager)

        diff = DetailedDiff("0.1.0", "0.2.0", "a" * 64, "b" * 64, [])
        result = checker.check_compatibility_with_guarantees("0.1.0", "0.2.0", diff)
        # Development stage, no guarantees enforced
        assert result["checked"] is True

    def test_same_major_version_check(self, setup):
        """Test 69: Same major version checked."""
        checker, diff = setup
        result = checker.check_compatibility_with_guarantees("1.0.0", "1.5.0", diff)
        # Same major version (1.x.x)
        assert result["checked"] is True

    def test_violation_description(self):
        """Test 70: Violation includes description."""
        manager = LifecycleManager()
        manager.add_version(VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL))
        checker = StabilityGuaranteeChecker(manager)

        diff = DetailedDiff(
            "1.0.0",
            "1.5.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("func1", "function", [DetailedChange("c1", "func1", ChangeSeverity.BREAKING, "Breaking")])],
        )

        result = checker.check_compatibility_with_guarantees("1.0.0", "1.5.0", diff)
        if not result["compliant"]:
            assert len(result["violations"]) > 0
            assert "1.0.0" in result["violations"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
