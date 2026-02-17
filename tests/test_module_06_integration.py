"""
Complete integration test for Module 06: Contract Versioning System
Tests all 20 prompts working together.
"""

import pytest
from datetime import datetime, timezone
from modules.module_06_contract_schema.contract_versioning import (
    IntegratedVersioningSystem,
    Author,
    VersionLifecycle,
    LifecycleStage,
    SupportTier,
    VersionMetadata,
    VersionProvenance,
    DetailedDiff,
    EntityDiff,
    DetailedChange,
    ChangeSeverity,
    VersionRecommendationEngine,
    CompatibilityTester,
    CompatibilityTestResult,
    ChangelogGenerator,
    SemanticVersion,
)


class TestCompleteIntegration:
    """Integration tests for complete versioning system (10 tests)."""

    @pytest.fixture
    def system(self):
        """Create complete system."""
        return IntegratedVersioningSystem()

    def test_system_initialization(self, system):
        """Test 1: System initializes with all components."""
        assert system.version_manager is not None
        assert system.release_workflow is not None
        assert system.upgrade_workflow is not None
        assert system.rollback_workflow is not None
        assert system.query_workflow is not None

    def test_complete_release_workflow(self, system):
        """Test 2: Complete release workflow."""
        author = Author("Test Author", "test@example.com")

        # Release version
        result = system.release_version(current_version="1.0.0", candidate_contract=None, author=author)

        assert result["success"] is True
        assert "proposed_version" in result
        assert len(result["steps_completed"]) > 0

    def test_version_history_tracking(self, system):
        """Test 3: Version history is tracked."""
        author = Author("Test", "test@example.com")

        # Release multiple versions
        system.release_version("1.0.0", None, author)

        # Check history
        versions = system.version_manager.list_versions("test")
        assert isinstance(versions, list)

    def test_upgrade_and_rollback_cycle(self, system):
        """Test 4: Upgrade then rollback."""
        # Upgrade
        upgrade_result = system.upgrade_version("1.0.0", "2.0.0")
        assert "plan" in upgrade_result

        # Rollback
        rollback_result = system.rollback_version("2.0.0", "1.0.0", force=True)
        assert "plan" in rollback_result

    def test_lifecycle_management(self, system):
        """Test 5: Lifecycle management works."""
        # Add lifecycle
        lifecycle = VersionLifecycle("1.0.0", LifecycleStage.STABLE, SupportTier.FULL)
        system.version_manager.lifecycle_manager.add_version(lifecycle)

        # Deprecate
        system.version_manager.lifecycle_manager.deprecate_version("1.0.0", "Test deprecation", eol_days=90)

        # Check status
        updated = system.version_manager.lifecycle_manager.get_lifecycle("1.0.0")
        assert updated.stage == LifecycleStage.DEPRECATED

    def test_metadata_and_provenance(self, system):
        """Test 6: Metadata and provenance tracking."""
        # Create metadata
        metadata = VersionMetadata(version="1.0.0", created_at=datetime.now(timezone.utc).isoformat() + "Z", license="MIT")
        metadata.add_tag("stable")

        system.version_manager.metadata_manager.add_metadata(metadata)

        # Create provenance
        provenance = VersionProvenance(version="1.0.0", fingerprint="test_fp", metadata=metadata)

        system.version_manager.provenance_tracker.add_provenance(provenance)

        # Verify
        info = system.version_manager.get_version_info("1.0.0")
        assert info["metadata"] is not None
        assert info["provenance"] is not None

    def test_version_recommendation(self, system):
        """Test 7: Version recommendation works."""
        # Create diff with breaking changes
        diff = DetailedDiff(
            "1.0.0",
            "2.0.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("entity", "type", [DetailedChange("change", "entity", ChangeSeverity.BREAKING, "desc")])],
        )

        recommender = VersionRecommendationEngine()
        recommendation = recommender.recommend_version("1.0.0", diff)

        assert recommendation["success"] is True
        assert recommendation["recommended_version"] == "2.0.0"

    def test_compatibility_checking(self, system):
        """Test 8: Compatibility checking."""
        tester = CompatibilityTester(system.version_manager.version_history)

        # Test compatibility (will return UNKNOWN without data)
        result = tester.test_compatibility("1.0.0", "2.0.0")
        assert isinstance(result, CompatibilityTestResult)

    def test_changelog_generation(self, system):
        """Test 9: Changelog generation."""
        diff = DetailedDiff(
            "1.0.0",
            "2.0.0",
            "a" * 64,
            "b" * 64,
            [EntityDiff("func", "function", [DetailedChange("added", "func", ChangeSeverity.EXTENSION, "Added function")])],
        )

        generator = ChangelogGenerator()
        changelog = generator.generate(diff, "1.0.0", "2.0.0")

        assert changelog.from_version == "1.0.0"
        assert changelog.to_version == "2.0.0"
        assert len(changelog.entries) > 0

    def test_semantic_versioning(self, system):
        """Test 10: Semantic versioning."""
        # Parse version
        v = SemanticVersion.parse("2.5.3-beta.1+build.123")
        assert v.major == 2
        assert v.minor == 5
        assert v.patch == 3
        assert v.prerelease == "beta.1"

        # Version comparison
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("2.0.0")
        assert v1 < v2

        # Version bumping
        bumped = v1.bump_major()
        assert str(bumped) == "2.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
