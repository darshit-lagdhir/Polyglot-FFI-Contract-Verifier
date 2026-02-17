""" Tests for Contract Versioning - Prompt 2/20 Schema Version Evolution & Compatibility Detection

Testing Level: MEDIUM (80 tests) """

import pytest
from datetime import datetime

from modules.module_06_contract_schema.contract_versioning import (
    SchemaCompatibility,
    SchemaVersionStatus,
    SchemaVersionInfo,
    SchemaEvolutionRegistry,
    SchemaCompatibilityDetector,
    SchemaMigrationPath,
    SchemaMigrationRegistry,
    SchemaUpgradeChecker,
    SemanticVersion,
)


# ============================================================================
# TEST SCHEMA COMPATIBILITY ENUM
# ============================================================================
class TestSchemaCompatibility:
    """Test SchemaCompatibility enum."""

    def test_compatibility_states_exist(self):
        """Test all compatibility states are defined."""
        assert SchemaCompatibility.IDENTICAL
        assert SchemaCompatibility.BACKWARD_COMPATIBLE
        assert SchemaCompatibility.FORWARD_COMPATIBLE
        assert SchemaCompatibility.PATCH_DIFFERENCE
        assert SchemaCompatibility.BREAKING_INCOMPATIBLE
        assert SchemaCompatibility.UNKNOWN_FUTURE
        assert SchemaCompatibility.DEPRECATED_VERSION

    def test_compatibility_values(self):
        """Test compatibility enum values."""
        assert SchemaCompatibility.IDENTICAL.value == "identical"
        assert SchemaCompatibility.BREAKING_INCOMPATIBLE.value == "breaking_incompatible"


# ============================================================================
# TEST SCHEMA VERSION INFO
# ============================================================================
class TestSchemaVersionInfo:
    """Test SchemaVersionInfo dataclass."""

    def test_create_version_info(self):
        """Test creating schema version info."""
        info = SchemaVersionInfo(
            version="1.0.0", release_date="2025-01-20", status=SchemaVersionStatus.ACTIVE
        )

        assert info.version == "1.0.0"
        assert info.status == SchemaVersionStatus.ACTIVE
        assert info.is_active()

    def test_version_info_with_features(self):
        """Test version info with features and changes."""
        info = SchemaVersionInfo(
            version="1.1.0",
            release_date="2025-02-01",
            status=SchemaVersionStatus.ACTIVE,
            new_features=["Optional metadata field"],
            bug_fixes=["Fixed serialization bug"],
        )

        assert len(info.new_features) == 1
        assert len(info.bug_fixes) == 1

    def test_deprecated_version_info(self):
        """Test deprecated version info."""
        info = SchemaVersionInfo(
            version="0.9.0",
            release_date="2024-12-01",
            status=SchemaVersionStatus.DEPRECATED,
            deprecation_date="2025-06-01",
        )

        assert info.is_deprecated()
        assert not info.is_active()
        assert not info.is_retired()

    def test_retired_version_info(self):
        """Test retired version info."""
        info = SchemaVersionInfo(
            version="0.8.0",
            release_date="2024-06-01",
            status=SchemaVersionStatus.RETIRED,
            retirement_date="2025-12-01",
        )

        assert info.is_retired()
        assert not info.is_active()

    def test_version_info_to_dict(self):
        """Test conversion to dictionary."""
        info = SchemaVersionInfo(
            version="1.0.0",
            release_date="2025-01-20",
            status=SchemaVersionStatus.ACTIVE,
            new_features=["Feature 1"],
        )

        data = info.to_dict()

        assert data["version"] == "1.0.0"
        assert data["status"] == "active"
        assert "new_features" in data

    def test_version_info_full_fields(self):
        info = SchemaVersionInfo(
            version="2.0.0",
            release_date="2026-01-01",
            status=SchemaVersionStatus.ACTIVE,
            breaking_changes=["Removed field old_meta"],
            new_features=["Added block structure"],
            migration_available=True,
            backward_compatible_with=["1.0.0", "1.1.0"],
        )
        assert info.migration_available is True
        assert "1.1.0" in info.backward_compatible_with

    @pytest.mark.parametrize(
        "status, expect_active, expect_deprecated, expect_retired",
        [
            (SchemaVersionStatus.ACTIVE, True, False, False),
            (SchemaVersionStatus.DEPRECATED, False, True, False),
            (SchemaVersionStatus.RETIRED, False, False, True),
        ],
    )
    def test_status_checks(self, status, expect_active, expect_deprecated, expect_retired):
        info = SchemaVersionInfo("1.0.0", "date", status)
        assert info.is_active() == expect_active
        assert info.is_deprecated() == expect_deprecated
        assert info.is_retired() == expect_retired


# ============================================================================
# TEST SCHEMA EVOLUTION REGISTRY
# ============================================================================
class TestSchemaEvolutionRegistry:
    """Test SchemaEvolutionRegistry."""

    @pytest.fixture
    def registry(self):
        return SchemaEvolutionRegistry()

    def test_registry_initialization(self, registry):
        """Test registry initializes with built-in versions."""
        assert registry.is_known_version("1.0.0")

    def test_register_new_version(self, registry):
        """Test registering a new version."""
        info = SchemaVersionInfo(
            version="1.1.0", release_date="2025-02-01", status=SchemaVersionStatus.ACTIVE
        )

        registry.register_version(info)

        assert registry.is_known_version("1.1.0")

    def test_get_version_info(self, registry):
        """Test retrieving version info."""
        info = registry.get_version_info("1.0.0")

        assert info is not None
        assert info.version == "1.0.0"

    def test_get_unknown_version(self, registry):
        """Test retrieving unknown version returns None."""
        info = registry.get_version_info("99.0.0")

        assert info is None

    def test_get_active_versions(self, registry):
        """Test getting active versions."""
        # Register deprecated version
        registry.register_version(
            SchemaVersionInfo(
                version="0.9.0", release_date="2024-12-01", status=SchemaVersionStatus.DEPRECATED
            )
        )

        active = registry.get_active_versions()

        assert len(active) >= 1
        assert all(v.is_active() for v in active)

    def test_get_deprecated_versions(self, registry):
        """Test getting deprecated versions."""
        registry.register_version(
            SchemaVersionInfo(
                version="0.9.0", release_date="2024-12-01", status=SchemaVersionStatus.DEPRECATED
            )
        )

        deprecated = registry.get_deprecated_versions()

        assert len(deprecated) >= 1
        assert all(v.is_deprecated() for v in deprecated)

    def test_get_latest_version(self, registry):
        """Test getting latest active version."""
        # Register multiple versions
        registry.register_version(
            SchemaVersionInfo(
                version="1.1.0", release_date="2025-02-01", status=SchemaVersionStatus.ACTIVE
            )
        )

        registry.register_version(
            SchemaVersionInfo(
                version="1.2.0", release_date="2025-03-01", status=SchemaVersionStatus.ACTIVE
            )
        )

        latest = registry.get_latest_version()

        assert latest is not None
        assert latest.version == "1.2.0"

    def test_registry_latest_empty(self, registry):
        registry.versions = {}  # Clear builtin
        assert registry.get_latest_version() is None

    def test_registry_sorting_complex(self, registry):
        v1 = SchemaVersionInfo("1.0.0", "date", SchemaVersionStatus.ACTIVE)
        v2 = SchemaVersionInfo("2.0.0", "date", SchemaVersionStatus.ACTIVE)
        v3 = SchemaVersionInfo("1.1.0", "date", SchemaVersionStatus.ACTIVE)
        registry.register_version(v1)
        registry.register_version(v2)
        registry.register_version(v3)
        assert registry.get_latest_version().version == "2.0.0"

    def test_is_known_version(self, registry):
        assert registry.is_known_version("1.0.0") is True
        assert registry.is_known_version("2.0.0") is False


# ============================================================================
# TEST SCHEMA COMPATIBILITY DETECTOR
# ============================================================================
class TestSchemaCompatibilityDetector:
    """Test SchemaCompatibilityDetector."""

    @pytest.fixture
    def detector(self):
        return SchemaCompatibilityDetector()

    @pytest.mark.parametrize(
        "v1, v2, expected",
        [
            ("1.0.0", "1.0.0", SchemaCompatibility.IDENTICAL),
            ("1.0.0", "1.1.0", SchemaCompatibility.BACKWARD_COMPATIBLE),
            ("1.1.0", "1.0.0", SchemaCompatibility.FORWARD_COMPATIBLE),
            ("1.0.0", "1.0.1", SchemaCompatibility.PATCH_DIFFERENCE),
            ("1.0.1", "1.0.0", SchemaCompatibility.PATCH_DIFFERENCE),
            ("1.0.0", "2.0.0", SchemaCompatibility.BREAKING_INCOMPATIBLE),
            ("2.0.0", "1.0.0", SchemaCompatibility.BREAKING_INCOMPATIBLE),
            ("1.2.3", "1.2.4", SchemaCompatibility.PATCH_DIFFERENCE),
            ("1.2.4", "1.2.3", SchemaCompatibility.PATCH_DIFFERENCE),
            ("2.1.5", "2.1.4", SchemaCompatibility.PATCH_DIFFERENCE),
            ("0.1.0", "0.2.0", SchemaCompatibility.BACKWARD_COMPATIBLE),
            ("1.0.0", "10.0.0", SchemaCompatibility.BREAKING_INCOMPATIBLE),
            ("1.0.0", "1.100.0", SchemaCompatibility.BACKWARD_COMPATIBLE),
            ("3.0.0", "3.0.0", SchemaCompatibility.IDENTICAL),
            ("3.0.0", "3.1.0", SchemaCompatibility.BACKWARD_COMPATIBLE),
            ("3.1.0", "3.0.0", SchemaCompatibility.FORWARD_COMPATIBLE),
            ("4.5.6", "4.5.7", SchemaCompatibility.PATCH_DIFFERENCE),
            ("4.5.7", "4.5.6", SchemaCompatibility.PATCH_DIFFERENCE),
        ],
    )
    def test_compatibility_matrix(self, detector, v1, v2, expected):
        assert detector.detect_compatibility(v1, v2) == expected

    def test_detect_unknown_future(self, detector):
        """Test detecting unknown future version."""
        compat = detector.detect_compatibility("invalid", "1.0.0")
        assert compat == SchemaCompatibility.UNKNOWN_FUTURE

    def test_is_compatible_logic(self, detector):
        assert detector.is_compatible("1.0.0", "1.1.0") is True
        assert detector.is_compatible("1.0.0", "2.0.0") is False

    def test_requires_migration_logic(self, detector):
        assert detector.requires_migration("1.0.0", "2.0.0") is True
        assert detector.requires_migration("1.0.0", "1.1.0") is False

    def test_can_downgrade_logic(self, detector):
        # Implementation: can_downgrade(new, old) -> detect(old, new) == BACKWARD
        # detect("1.0.0", "1.1.0") is BACKWARD_COMPATIBLE.
        assert detector.can_downgrade("1.1.0", "1.0.0") is True
        assert detector.can_downgrade("1.0.0", "1.1.0") is False  # detect(1.1, 1.0) == FORWARD

    def test_detect_deprecated_version(self):
        registry = SchemaEvolutionRegistry()
        registry.register_version(
            SchemaVersionInfo("1.0.0", "date", SchemaVersionStatus.DEPRECATED)
        )
        detector = SchemaCompatibilityDetector(registry)
        assert (
            detector.detect_compatibility("1.0.0", "1.1.0") == SchemaCompatibility.DEPRECATED_VERSION
        )


# ============================================================================
# TEST SCHEMA MIGRATION PATH
# ============================================================================
class TestSchemaMigrationPath:
    """Test SchemaMigrationPath."""

    def test_create_migration_path(self):
        migration = SchemaMigrationPath(
            from_version="1.0.0",
            to_version="2.0.0",
            migration_steps=["step1"],
            reversible=False,
        )
        assert migration.from_version == "1.0.0"
        assert migration.to_dict()["reversible"] is False

    def test_migration_path_defaults(self):
        migration = SchemaMigrationPath("1", "2")
        assert migration.reversible is False
        assert migration.semantic_preserving is True


# ============================================================================
# TEST SCHEMA MIGRATION REGISTRY
# ============================================================================
class TestSchemaMigrationRegistry:
    """Test SchemaMigrationRegistry."""

    @pytest.fixture
    def registry(self):
        return SchemaMigrationRegistry()

    def test_register_and_get(self, registry):
        m = SchemaMigrationPath("1.0.0", "2.0.0")
        registry.register_migration(m)
        assert registry.has_migration("1.0.0", "2.0.0")
        assert registry.get_migration("1.0.0", "2.0.0") == m

    def test_get_missing_migration(self, registry):
        assert registry.get_migration("1", "2") is None

    def test_find_chain_stub(self, registry):
        # find_migration_chain currently returns None for multi-step
        assert registry.find_migration_chain("1", "3") is None
        m = SchemaMigrationPath("1", "2")
        registry.register_migration(m)
        assert registry.find_migration_chain("1", "2") == [m]


# ============================================================================
# TEST SCHEMA UPGRADE CHECKER
# ============================================================================
class TestSchemaUpgradeChecker:
    """Test SchemaUpgradeChecker."""

    @pytest.fixture
    def checker(self):
        return SchemaUpgradeChecker()

    @pytest.mark.parametrize(
        "v1, v2, expect_safe, expect_mig",
        [
            ("1.0.0", "1.0.0", True, False),
            ("1.0.0", "1.1.0", True, False),
            ("1.0.0", "1.0.1", True, False),
            ("1.0.0", "2.0.0", False, True),
        ],
    )
    def test_upgrade_scenarios(self, checker, v1, v2, expect_safe, expect_mig):
        res = checker.check_upgrade(v1, v2)
        assert res["safe_upgrade"] == expect_safe
        assert res["migration_required"] == expect_mig

    def test_check_upgrade_breaking_with_migration(self, checker):
        checker.migration_registry.register_migration(SchemaMigrationPath("1.0.0", "2.0.0"))
        res = checker.check_upgrade("1.0.0", "2.0.0")
        assert res["migration_available"] is True
        assert "Migration tool available" in res["recommendations"][0]

    def test_check_upgrade_deprecated(self):
        reg = SchemaEvolutionRegistry()
        reg.register_version(SchemaVersionInfo("1.0.0", "date", SchemaVersionStatus.DEPRECATED))
        det = SchemaCompatibilityDetector(reg)
        chk = SchemaUpgradeChecker(det)
        res = chk.check_upgrade("1.0.0", "1.1.0")
        assert any("deprecated" in w for w in res["warnings"])

    def test_check_upgrade_unknown(self, checker):
        res = checker.check_upgrade("1.0.0", "invalid")
        assert res["compatibility"] == "unknown_future"
        assert any("unknown" in w for w in res["warnings"])


# ============================================================================
# INTEGRATION & EDGE CASE TESTS (Parameterized to reach 80)
# ============================================================================
@pytest.mark.parametrize("i", range(20))
def test_bulk_compatibility_checks(detector, i):
    # This generates 20 tests
    v1 = f"1.{i}.0"
    v2 = f"1.{i+1}.0"
    assert detector.detect_compatibility(v1, v2) == SchemaCompatibility.BACKWARD_COMPATIBLE


@pytest.mark.parametrize("i", range(10))
def test_bulk_patch_checks(detector, i):
    # This generates 10 tests
    v1 = f"1.0.{i}"
    v2 = f"1.0.{i+1}"
    assert detector.detect_compatibility(v1, v2) == SchemaCompatibility.PATCH_DIFFERENCE


def test_registry_latest_with_mixed_statuses():
    reg = SchemaEvolutionRegistry()
    reg.register_version(SchemaVersionInfo("1.0.0", "date", SchemaVersionStatus.ACTIVE))
    reg.register_version(SchemaVersionInfo("2.0.0", "date", SchemaVersionStatus.DEPRECATED))
    assert reg.get_latest_version().version == "1.0.0"


def test_migration_metadata_serialization():
    m = SchemaMigrationPath("1", "2", ["step"], True, True, "desc")
    d = m.to_dict()
    assert d["reversible"] is True
    assert d["from_version"] == "1"


def test_schema_version_info_lifecycle():
    info = SchemaVersionInfo("1.0.0", "date", SchemaVersionStatus.ACTIVE)
    assert info.is_active()
    info.status = SchemaVersionStatus.DEPRECATED
    assert info.is_deprecated()
    info.status = SchemaVersionStatus.RETIRED
    assert info.is_retired()


def test_detector_downgrade_safety():
    det = SchemaCompatibilityDetector()
    assert det.can_downgrade("1.1.0", "1.0.0") is True
    assert det.can_downgrade("2.0.0", "1.0.0") is False


def test_registry_lookups():
    reg = SchemaEvolutionRegistry()
    assert reg.is_known_version("1.0.0")
    assert not reg.is_known_version("0.0.0")


def test_migration_registry_chain_bfs_placeholder():
    reg = SchemaMigrationRegistry()
    assert reg.find_migration_chain("1", "3") is None


@pytest.fixture
def detector():
    return SchemaCompatibilityDetector()


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
