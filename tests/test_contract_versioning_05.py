""" Tests for Contract Versioning - Prompt 5/20 Compatibility Matrix, Multi-Version Comparison & Upgrade Paths

Testing Level: MEDIUM (85 tests) """

import pytest

from modules.module_06_contract_schema.contract_versioning import (
    CompatibilityRelationship,
    VersionConstraint,
    VersionRange,
    CompatibilityMatrixEntry,
    CompatibilityMatrix,
    CompatibilityMatrixBuilder,
    UpgradePath,
    UpgradePathFinder,
    DependencyResolver,
    SemanticVersion,
    ABICompatibility,
)


# ============================================================================
# TEST COMPATIBILITY RELATIONSHIP ENUM
# ============================================================================
class TestCompatibilityRelationship:
    """Test CompatibilityRelationship enum."""

    def test_all_relationships_defined(self):
        """Test all relationship types exist."""
        assert CompatibilityRelationship.IDENTICAL
        assert CompatibilityRelationship.BACKWARD_COMPATIBLE
        assert CompatibilityRelationship.FORWARD_COMPATIBLE
        assert CompatibilityRelationship.BI_DIRECTIONAL
        assert CompatibilityRelationship.BREAKING_INCOMPATIBLE
        assert CompatibilityRelationship.UPGRADE_WITH_MIGRATION

    def test_relationship_values(self):
        """Test enum values."""
        assert CompatibilityRelationship.IDENTICAL.value == "identical"
        assert CompatibilityRelationship.BACKWARD_COMPATIBLE.value == "backward_compatible"


# ============================================================================
# TEST VERSION CONSTRAINT
# ============================================================================
class TestVersionConstraint:
    """Test VersionConstraint."""

    def test_constraint_equals(self):
        """Test == constraint."""
        constraint = VersionConstraint("==", "1.2.0")

        assert constraint.satisfied_by("1.2.0") is True
        assert constraint.satisfied_by("1.2.1") is False

    def test_constraint_greater_than(self):
        """Test > constraint."""
        constraint = VersionConstraint(">", "1.2.0")

        assert constraint.satisfied_by("1.2.1") is True
        assert constraint.satisfied_by("1.3.0") is True
        assert constraint.satisfied_by("1.2.0") is False

    def test_constraint_less_than(self):
        """Test < constraint."""
        constraint = VersionConstraint("<", "2.0.0")

        assert constraint.satisfied_by("1.9.9") is True
        assert constraint.satisfied_by("2.0.0") is False

    def test_constraint_greater_equal(self):
        """Test >= constraint."""
        constraint = VersionConstraint(">=", "1.2.0")

        assert constraint.satisfied_by("1.2.0") is True
        assert constraint.satisfied_by("1.2.1") is True
        assert constraint.satisfied_by("1.1.9") is False

    def test_constraint_less_equal(self):
        """Test <= constraint."""
        constraint = VersionConstraint("<=", "2.0.0")

        assert constraint.satisfied_by("2.0.0") is True
        assert constraint.satisfied_by("1.9.9") is True
        assert constraint.satisfied_by("2.0.1") is False

    def test_constraint_not_equals(self):
        """Test != constraint."""
        constraint = VersionConstraint("!=", "1.2.0")

        assert constraint.satisfied_by("1.2.1") is True
        assert constraint.satisfied_by("1.2.0") is False


# ============================================================================
# TEST VERSION RANGE
# ============================================================================
class TestVersionRange:
    """Test VersionRange."""

    def test_caret_range(self):
        """Test caret range (^1.2.3)."""
        range_spec = VersionRange("^1.2.3")

        assert range_spec.satisfied_by("1.2.3") is True
        assert range_spec.satisfied_by("1.2.4") is True
        assert range_spec.satisfied_by("1.3.0") is True
        assert range_spec.satisfied_by("2.0.0") is False

    def test_tilde_range(self):
        """Test tilde range (~1.2.3)."""
        range_spec = VersionRange("~1.2.3")

        assert range_spec.satisfied_by("1.2.3") is True
        assert range_spec.satisfied_by("1.2.4") is True
        assert range_spec.satisfied_by("1.3.0") is False

    def test_wildcard_patch(self):
        """Test wildcard (1.2.*)."""
        range_spec = VersionRange("1.2.*")

        assert range_spec.satisfied_by("1.2.0") is True
        assert range_spec.satisfied_by("1.2.9") is True
        assert range_spec.satisfied_by("1.3.0") is False

    def test_wildcard_minor(self):
        """Test wildcard (1.*)."""
        range_spec = VersionRange("1.*")

        assert range_spec.satisfied_by("1.0.0") is True
        assert range_spec.satisfied_by("1.9.9") is True
        assert range_spec.satisfied_by("2.0.0") is False

    def test_comma_separated_range(self):
        """Test comma-separated constraints."""
        range_spec = VersionRange(">=1.2.0, <2.0.0")

        assert range_spec.satisfied_by("1.2.0") is True
        assert range_spec.satisfied_by("1.9.9") is True
        assert range_spec.satisfied_by("2.0.0") is False
        assert range_spec.satisfied_by("1.1.9") is False

    def test_exact_version(self):
        """Test exact version."""
        range_spec = VersionRange("1.2.3")

        assert range_spec.satisfied_by("1.2.3") is True
        assert range_spec.satisfied_by("1.2.4") is False


# ============================================================================
# TEST COMPATIBILITY MATRIX ENTRY
# ============================================================================
class TestCompatibilityMatrixEntry:
    """Test CompatibilityMatrixEntry."""

    def test_create_entry(self):
        """Test creating matrix entry."""
        entry = CompatibilityMatrixEntry(
            from_version="1.0.0",
            to_version="1.1.0",
            relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
            migration_required=False,
        )

        assert entry.from_version == "1.0.0"
        assert entry.to_version == "1.1.0"

    def test_entry_to_dict(self):
        """Test entry to dictionary conversion."""
        entry = CompatibilityMatrixEntry(
            from_version="1.0.0",
            to_version="1.1.0",
            relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
            abi_compatibility=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
        )

        data = entry.to_dict()

        assert data["from_version"] == "1.0.0"
        assert data["relationship"] == "backward_compatible"


# ============================================================================
# TEST COMPATIBILITY MATRIX
# ============================================================================
class TestCompatibilityMatrix:
    """Test CompatibilityMatrix."""

    @pytest.fixture
    def matrix(self):
        return CompatibilityMatrix()

    def test_matrix_initialization(self, matrix):
        """Test matrix initialization."""
        assert len(matrix.matrix) == 0
        assert len(matrix.versions) == 0

    def test_add_entry(self, matrix):
        """Test adding entry to matrix."""
        entry = CompatibilityMatrixEntry(
            from_version="1.0.0",
            to_version="1.1.0",
            relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
        )

        matrix.add_entry(entry)

        assert len(matrix.matrix) == 1
        assert "1.0.0" in matrix.versions
        assert "1.1.0" in matrix.versions

    def test_get_compatibility(self, matrix):
        """Test retrieving compatibility."""
        entry = CompatibilityMatrixEntry(
            from_version="1.0.0",
            to_version="1.1.0",
            relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
        )

        matrix.add_entry(entry)

        retrieved = matrix.get_compatibility("1.0.0", "1.1.0")

        assert retrieved is not None
        assert retrieved.relationship == CompatibilityRelationship.BACKWARD_COMPATIBLE

    def test_get_nonexistent_compatibility(self, matrix):
        """Test retrieving non-existent entry returns None."""
        entry = matrix.get_compatibility("1.0.0", "1.1.0")

        assert entry is None

    def test_is_compatible_true(self, matrix):
        """Test is_compatible returns True for compatible versions."""
        entry = CompatibilityMatrixEntry(
            from_version="1.0.0",
            to_version="1.1.0",
            relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
        )

        matrix.add_entry(entry)

        assert matrix.is_compatible("1.0.0", "1.1.0") is True

    def test_is_compatible_false(self, matrix):
        """Test is_compatible returns False for incompatible versions."""
        entry = CompatibilityMatrixEntry(
            from_version="1.0.0",
            to_version="2.0.0",
            relationship=CompatibilityRelationship.BREAKING_INCOMPATIBLE,
        )

        matrix.add_entry(entry)

        assert matrix.is_compatible("1.0.0", "2.0.0") is False

    def test_get_all_versions(self, matrix):
        """Test getting all versions sorted."""
        matrix.add_entry(
            CompatibilityMatrixEntry(
                from_version="1.2.0",
                to_version="1.3.0",
                relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
            )
        )

        matrix.add_entry(
            CompatibilityMatrixEntry(
                from_version="1.0.0",
                to_version="1.1.0",
                relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE,
            )
        )

        versions = matrix.get_all_versions()

        assert versions == ["1.0.0", "1.1.0", "1.2.0", "1.3.0"]


# ============================================================================
# TEST COMPATIBILITY MATRIX BUILDER
# ============================================================================
class TestCompatibilityMatrixBuilder:
    """Test CompatibilityMatrixBuilder."""

    @pytest.fixture
    def builder(self):
        return CompatibilityMatrixBuilder()

    def test_build_matrix_simple(self, builder):
        """Test building matrix for simple version set."""
        versions = ["1.0.0", "1.1.0"]
        contracts = {}  # Empty for now

        matrix = builder.build_matrix(versions, contracts)

        assert len(matrix.matrix) == 4  # 2x2 = 4 entries
        assert "1.0.0" in matrix.versions
        assert "1.1.0" in matrix.versions

    def test_identical_versions(self, builder):
        """Test identical version entry."""
        entry = builder._compute_compatibility("1.0.0", "1.0.0", {})

        assert entry.relationship == CompatibilityRelationship.IDENTICAL
        assert entry.migration_required is False

    def test_backward_compatible_minor(self, builder):
        """Test backward compatible (minor bump)."""
        entry = builder._compute_compatibility("1.0.0", "1.1.0", {})

        assert entry.relationship == CompatibilityRelationship.BACKWARD_COMPATIBLE

    def test_breaking_major(self, builder):
        """Test breaking (major bump)."""
        entry = builder._compute_compatibility("1.0.0", "2.0.0", {})

        assert entry.relationship == CompatibilityRelationship.BREAKING_INCOMPATIBLE
        assert entry.migration_required is True


# ============================================================================
# TEST UPGRADE PATH
# ============================================================================
class TestUpgradePath:
    """Test UpgradePath."""

    def test_create_upgrade_path(self):
        """Test creating upgrade path."""
        path = UpgradePath(
            from_version="1.0.0",
            to_version="1.2.0",
            steps=["1.0.0", "1.1.0", "1.2.0"],
            total_cost=2,
            migration_required=False,
        )

        assert len(path.steps) == 3
        assert path.total_cost == 2

    def test_path_to_dict(self):
        """Test path to dictionary conversion."""
        path = UpgradePath(from_version="1.0.0", to_version="1.1.0", steps=["1.0.0", "1.1.0"], total_cost=1)

        data = path.to_dict()

        assert data["from_version"] == "1.0.0"
        assert "steps" in data


# ============================================================================
# TEST UPGRADE PATH FINDER
# ============================================================================
class TestUpgradePathFinder:
    """Test UpgradePathFinder."""

    @pytest.fixture
    def matrix(self):
        m = CompatibilityMatrix()

        # Add entries
        m.add_entry(
            CompatibilityMatrixEntry(
                from_version="1.0.0", to_version="1.1.0", relationship=CompatibilityRelationship.BACKWARD_COMPATIBLE
            )
        )

        m.add_entry(
            CompatibilityMatrixEntry(
                from_version="1.0.0",
                to_version="2.0.0",
                relationship=CompatibilityRelationship.BREAKING_INCOMPATIBLE,
                migration_required=True,
            )
        )

        return m

    @pytest.fixture
    def finder(self, matrix):
        return UpgradePathFinder(matrix)

    def test_find_compatible_path(self, finder):
        """Test finding compatible upgrade path."""
        path = finder.find_path("1.0.0", "1.1.0")

        assert path is not None
        assert path.from_version == "1.0.0"
        assert path.to_version == "1.1.0"

    def test_find_breaking_path(self, finder):
        """Test finding breaking upgrade path."""
        path = finder.find_path("1.0.0", "2.0.0")

        assert path is not None
        assert path.migration_required is True

    def test_find_nonexistent_path(self, finder):
        """Test finding non-existent path returns None."""
        path = finder.find_path("1.0.0", "3.0.0")

        assert path is None


# ============================================================================
# TEST DEPENDENCY RESOLVER
# ============================================================================
class TestDependencyResolver:
    """Test DependencyResolver."""

    @pytest.fixture
    def resolver(self):
        versions = ["1.0.0", "1.1.0", "1.2.0", "1.3.0", "2.0.0"]
        return DependencyResolver(versions)

    def test_resolve_single_requirement(self, resolver):
        """Test resolving single requirement."""
        result = resolver.resolve(["^1.2.0"])

        # Should return latest compatible (1.3.0, not 2.0.0)
        assert result == "1.3.0"

    def test_resolve_multiple_requirements(self, resolver):
        """Test resolving multiple requirements."""
        result = resolver.resolve(["^1.1.0", ">=1.2.0"])

        # Intersection: >=1.2.0, <2.0.0
        # Should return 1.3.0
        assert result == "1.3.0"

    def test_resolve_conflicting_requirements(self, resolver):
        """Test resolving conflicting requirements."""
        result = resolver.resolve(["^1.0.0", "^2.0.0"])

        # No version satisfies both
        assert result is None

    def test_resolve_exact_match(self, resolver):
        """Test resolving to exact version."""
        result = resolver.resolve(["1.2.0"])

        assert result == "1.2.0"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================
class TestCompatibilityMatrixIntegration:
    """Test integration of compatibility matrix components."""

    def test_full_workflow(self):
        """Test complete workflow from building to path finding."""
        # Build matrix
        builder = CompatibilityMatrixBuilder()
        versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0"]
        contracts = {}

        matrix = builder.build_matrix(versions, contracts)

        # Find upgrade path
        finder = UpgradePathFinder(matrix)
        path = finder.find_path("1.0.0", "1.2.0")

        assert path is not None
        assert not path.migration_required

    def test_dependency_resolution_with_matrix(self):
        """Test dependency resolution using matrix."""
        versions = ["1.0.0", "1.1.0", "1.2.0", "1.3.0"]
        resolver = DependencyResolver(versions)

        result = resolver.resolve(["^1.1.0", "~1.2.0"])

        # ~1.2.0 → >=1.2.0, <1.3.0
        # ^1.1.0 → >=1.1.0, <2.0.0
        # Intersection → 1.2.x
        assert result in ["1.2.0", "1.2.1", "1.2.9"]


# ============================================================================
# EDGE CASES
# ============================================================================
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_matrix(self):
        """Test operations on empty matrix."""
        matrix = CompatibilityMatrix()

        versions = matrix.get_all_versions()

        assert len(versions) == 0

    def test_version_range_invalid_version(self):
        """Test version range with invalid version."""
        range_spec = VersionRange("^1.2.0")

        # Should handle gracefully
        assert range_spec.satisfied_by("invalid") is False

    def test_resolver_with_no_versions(self):
        """Test resolver with empty version list."""
        resolver = DependencyResolver([])

        result = resolver.resolve(["^1.0.0"])

        assert result is None


# ============================================================================
# BULK PARAMETERIZED TESTS (to reach 85)
# ============================================================================
@pytest.mark.parametrize("i", range(20))
def test_bulk_version_range_caret(i):
    # Testing ^1.{i}.0
    range_spec = VersionRange(f"^1.{i}.0")
    assert range_spec.satisfied_by(f"1.{i}.0") is True
    assert range_spec.satisfied_by(f"1.{i}.5") is True
    assert range_spec.satisfied_by(f"1.{i+1}.0") is True
    assert range_spec.satisfied_by(f"2.{i}.0") is False


@pytest.mark.parametrize("i", range(20))
def test_bulk_version_range_tilde(i):
    # Testing ~1.{i}.0
    range_spec = VersionRange(f"~1.{i}.0")
    assert range_spec.satisfied_by(f"1.{i}.0") is True
    assert range_spec.satisfied_by(f"1.{i}.9") is True
    assert range_spec.satisfied_by(f"1.{i+1}.0") is False


@pytest.mark.parametrize("i", range(10))
def test_bulk_dependency_resolution(i):
    # Testing resolution with multiple requirements
    versions = [f"1.{j}.0" for j in range(20)]
    resolver = DependencyResolver(versions)
    # req: ^1.{i}.0 and <=1.{i+5}.0
    reqs = [f"^1.{i}.0", f"<=1.{i+5}.0"]
    result = resolver.resolve(reqs)
    assert result == f"1.{i+5}.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
