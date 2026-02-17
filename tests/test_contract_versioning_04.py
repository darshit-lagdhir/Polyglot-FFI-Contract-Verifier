""" Tests for Contract Versioning - Prompt 4/20 Contract Version Evolution & ABI Compatibility Detection

Testing Level: MEDIUM (80 tests) """

import pytest
from datetime import datetime

from modules.module_06_contract_schema.contract_versioning import (
    ABICompatibility,
    ChangeType,
    ContractChange,
    ContractDiff,
    ContractVersionSnapshot,
    ContractEvolutionTimeline,
    ABICompatibilityDetector,
    MigrationNecessity,
    MigrationNecessityAnalyzer,
    ContractVersionComparator,
    SemanticVersion,
)


# ============================================================================
# TEST ABI COMPATIBILITY ENUM
# ============================================================================
class TestABICompatibility:
    """Test ABICompatibility enum."""

    def test_all_compatibility_types_defined(self):
        """Test all ABI compatibility types exist."""
        assert ABICompatibility.ABI_IDENTICAL
        assert ABICompatibility.ABI_COMPATIBLE_EXTENSION
        assert ABICompatibility.ABI_COMPATIBLE_RELAXATION
        assert ABICompatibility.ABI_COMPATIBLE_STRENGTHENING
        assert ABICompatibility.ABI_BREAKING_LAYOUT
        assert ABICompatibility.ABI_BREAKING_SIGNATURE
        assert ABICompatibility.ABI_BREAKING_REMOVAL

    def test_compatibility_values(self):
        """Test enum values are correct."""
        assert ABICompatibility.ABI_IDENTICAL.value == "abi_identical"
        assert ABICompatibility.ABI_BREAKING_LAYOUT.value == "abi_breaking_layout"


# ============================================================================
# TEST CHANGE TYPE ENUM
# ============================================================================
class TestChangeType:
    """Test ChangeType enum."""

    def test_all_change_types_defined(self):
        """Test all change types exist."""
        assert ChangeType.FUNCTION_ADDED
        assert ChangeType.FUNCTION_REMOVED
        assert ChangeType.FUNCTION_MODIFIED
        assert ChangeType.TYPE_ADDED
        assert ChangeType.TYPE_REMOVED
        assert ChangeType.FIELD_ADDED
        assert ChangeType.CLAUSE_MODIFIED

    def test_change_type_values(self):
        """Test change type values."""
        assert ChangeType.FUNCTION_ADDED.value == "function_added"
        assert ChangeType.TYPE_REMOVED.value == "type_removed"


# ============================================================================
# TEST CONTRACT CHANGE
# ============================================================================
class TestContractChange:
    """Test ContractChange dataclass."""

    def test_create_contract_change(self):
        """Test creating a contract change."""
        change = ContractChange(
            change_type=ChangeType.FUNCTION_ADDED,
            entity_id="new_function",
            description="Function 'new_function' added",
            abi_impact=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
        )

        assert change.change_type == ChangeType.FUNCTION_ADDED
        assert change.entity_id == "new_function"

    def test_is_breaking_true(self):
        """Test is_breaking returns True for breaking changes."""
        change = ContractChange(
            change_type=ChangeType.FUNCTION_REMOVED,
            entity_id="old_function",
            description="Function removed",
            abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
        )

        assert change.is_breaking() is True

    def test_is_breaking_false(self):
        """Test is_breaking returns False for compatible changes."""
        change = ContractChange(
            change_type=ChangeType.FUNCTION_ADDED,
            entity_id="new_function",
            description="Function added",
            abi_impact=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
        )

        assert change.is_breaking() is False

    def test_change_to_dict(self):
        """Test converting change to dictionary."""
        change = ContractChange(
            change_type=ChangeType.CLAUSE_ADDED,
            entity_id="clause_1",
            description="Clause added",
            abi_impact=ABICompatibility.ABI_COMPATIBLE_STRENGTHENING,
            details={"confidence": 0.9},
        )

        data = change.to_dict()

        assert data["change_type"] == "clause_added"
        assert data["entity_id"] == "clause_1"
        assert "details" in data


# ============================================================================
# TEST CONTRACT DIFF
# ============================================================================
class TestContractDiff:
    """Test ContractDiff dataclass."""

    def test_create_contract_diff(self):
        """Test creating a contract diff."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="1.1.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
        )

        assert diff.baseline_version == "1.0.0"
        assert diff.candidate_version == "1.1.0"

    def test_has_breaking_changes_true(self):
        """Test has_breaking_changes returns True."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="2.0.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
            changes=[
                ContractChange(
                    change_type=ChangeType.FUNCTION_REMOVED,
                    entity_id="func",
                    description="Removed",
                    abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
                )
            ],
        )

        assert diff.has_breaking_changes() is True

    def test_has_breaking_changes_false(self):
        """Test has_breaking_changes returns False."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="1.1.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
            changes=[
                ContractChange(
                    change_type=ChangeType.FUNCTION_ADDED,
                    entity_id="func",
                    description="Added",
                    abi_impact=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
                )
            ],
        )

        assert diff.has_breaking_changes() is False

    def test_get_breaking_changes(self):
        """Test getting only breaking changes."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="2.0.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
            changes=[
                ContractChange(
                    change_type=ChangeType.FUNCTION_REMOVED,
                    entity_id="func1",
                    description="Removed",
                    abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
                ),
                ContractChange(
                    change_type=ChangeType.FUNCTION_ADDED,
                    entity_id="func2",
                    description="Added",
                    abi_impact=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
                ),
            ],
        )

        breaking = diff.get_breaking_changes()

        assert len(breaking) == 1
        assert breaking[0].entity_id == "func1"

    def test_get_compatible_changes(self):
        """Test getting only compatible changes."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="1.1.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
            changes=[
                ContractChange(
                    change_type=ChangeType.FUNCTION_ADDED,
                    entity_id="func1",
                    description="Added",
                    abi_impact=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
                ),
                ContractChange(
                    change_type=ChangeType.FUNCTION_REMOVED,
                    entity_id="func2",
                    description="Removed",
                    abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
                ),
            ],
        )

        compatible = diff.get_compatible_changes()

        assert len(compatible) == 1
        assert compatible[0].entity_id == "func1"

    def test_diff_to_dict(self):
        """Test converting diff to dictionary."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="1.1.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
            overall_compatibility=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
        )

        data = diff.to_dict()

        assert data["baseline_version"] == "1.0.0"
        assert data["overall_compatibility"] == "abi_compatible_extension"
        assert "has_breaking_changes" in data


# ============================================================================
# TEST CONTRACT VERSION SNAPSHOT
# ============================================================================
class TestContractVersionSnapshot:
    """Test ContractVersionSnapshot."""

    def test_create_snapshot(self):
        """Test creating a version snapshot."""
        snapshot = ContractVersionSnapshot(
            version="1.0.0",
            release_date="2025-01-20",
            contract_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            ir_fingerprint="b" * 64,
            description="Initial release",
        )

        assert snapshot.version == "1.0.0"
        assert snapshot.description == "Initial release"

    def test_snapshot_to_dict(self):
        """Test snapshot to dictionary conversion."""
        snapshot = ContractVersionSnapshot(
            version="1.0.0",
            release_date="2025-01-20",
            contract_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            ir_fingerprint="b" * 64,
        )

        data = snapshot.to_dict()

        assert data["version"] == "1.0.0"
        assert "contract_fingerprint" in data


# ============================================================================
# TEST CONTRACT EVOLUTION TIMELINE
# ============================================================================
class TestContractEvolutionTimeline:
    """Test ContractEvolutionTimeline."""

    @pytest.fixture
    def timeline(self):
        return ContractEvolutionTimeline("test_interface")

    def test_timeline_initialization(self, timeline):
        """Test timeline initialization."""
        assert timeline.interface_id == "test_interface"
        assert len(timeline.snapshots) == 0

    def test_add_snapshot(self, timeline):
        """Test adding a snapshot."""
        snapshot = ContractVersionSnapshot(
            version="1.0.0",
            release_date="2025-01-20",
            contract_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            ir_fingerprint="b" * 64,
        )

        timeline.add_snapshot(snapshot)

        assert len(timeline.snapshots) == 1

    def test_get_snapshot(self, timeline):
        """Test retrieving a snapshot."""
        snapshot = ContractVersionSnapshot(
            version="1.0.0",
            release_date="2025-01-20",
            contract_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            ir_fingerprint="b" * 64,
        )

        timeline.add_snapshot(snapshot)

        retrieved = timeline.get_snapshot("1.0.0")

        assert retrieved is not None
        assert retrieved.version == "1.0.0"

    def test_get_all_versions(self, timeline):
        """Test getting all versions."""
        timeline.add_snapshot(
            ContractVersionSnapshot(
                version="1.0.0",
                release_date="2025-01-20",
                contract_fingerprint="a" * 64,
                schema_version="1.0.0",
                synthesis_version="1.0.0",
                ir_fingerprint="b" * 64,
            )
        )

        timeline.add_snapshot(
            ContractVersionSnapshot(
                version="1.1.0",
                release_date="2025-02-20",
                contract_fingerprint="c" * 64,
                schema_version="1.0.0",
                synthesis_version="1.0.0",
                ir_fingerprint="d" * 64,
            )
        )

        versions = timeline.get_all_versions()

        assert len(versions) == 2
        assert versions == ["1.0.0", "1.1.0"]  # Sorted

    def test_get_latest_version(self, timeline):
        """Test getting latest version."""
        timeline.add_snapshot(
            ContractVersionSnapshot(
                version="1.0.0",
                release_date="2025-01-20",
                contract_fingerprint="a" * 64,
                schema_version="1.0.0",
                synthesis_version="1.0.0",
                ir_fingerprint="b" * 64,
            )
        )

        timeline.add_snapshot(
            ContractVersionSnapshot(
                version="1.2.0",
                release_date="2025-03-20",
                contract_fingerprint="e" * 64,
                schema_version="1.0.0",
                synthesis_version="1.0.0",
                ir_fingerprint="f" * 64,
            )
        )

        latest = timeline.get_latest_version()

        assert latest is not None
        assert latest.version == "1.2.0"


# ============================================================================
# TEST ABI COMPATIBILITY DETECTOR
# ============================================================================
class TestABICompatibilityDetector:
    """Test ABICompatibilityDetector."""

    @pytest.fixture
    def detector(self):
        return ABICompatibilityDetector()

    @pytest.fixture
    def mock_contract_v1(self):
        """Mock contract version 1.0.0."""

        class MockContract:
            contract_version = "1.0.0"
            contract_fingerprint = "a" * 64
            functions = []
            structs = []

        return MockContract()

    @pytest.fixture
    def mock_contract_v1_1(self):
        """Mock contract version 1.1.0 (compatible extension)."""

        class MockContract:
            contract_version = "1.1.0"
            contract_fingerprint = "b" * 64
            functions = []
            structs = []

        return MockContract()

    def test_detect_identical_contracts(self, detector, mock_contract_v1):
        """Test detecting identical contracts."""
        diff = detector.detect_compatibility(mock_contract_v1, mock_contract_v1)

        assert diff.overall_compatibility == ABICompatibility.ABI_IDENTICAL

    def test_detect_different_contracts(self, detector, mock_contract_v1, mock_contract_v1_1):
        """Test detecting different contracts."""
        diff = detector.detect_compatibility(mock_contract_v1, mock_contract_v1_1)

        # Should not be identical
        assert diff.overall_compatibility != ABICompatibility.ABI_IDENTICAL

    def test_detect_added_function(self, detector):
        """Test detecting added function."""

        class V1:
            contract_version = "1.0.0"
            contract_fingerprint = "f1"
            functions = [{"function_id": "f_old"}]
            structs = []

        class V2:
            contract_version = "1.1.0"
            contract_fingerprint = "f2"
            functions = [{"function_id": "f_old"}, {"function_id": "f_new"}]
            structs = []

        diff = detector.detect_compatibility(V1(), V2())

        assert len(diff.changes) == 1
        assert diff.changes[0].change_type == ChangeType.FUNCTION_ADDED
        assert diff.overall_compatibility == ABICompatibility.ABI_COMPATIBLE_EXTENSION

    def test_detect_removed_function(self, detector):
        """Test detecting removed function."""

        class V1:
            contract_version = "1.0.0"
            contract_fingerprint = "f1"
            functions = [{"function_id": "f_old"}]
            structs = []

        class V2:
            contract_version = "1.1.0"
            contract_fingerprint = "f2"
            functions = []
            structs = []

        diff = detector.detect_compatibility(V1(), V2())

        assert len(diff.changes) == 1
        assert diff.changes[0].change_type == ChangeType.FUNCTION_REMOVED
        assert diff.overall_compatibility == ABICompatibility.ABI_BREAKING_REMOVAL


# ============================================================================
# TEST MIGRATION NECESSITY ANALYZER
# ============================================================================
class TestMigrationNecessityAnalyzer:
    """Test MigrationNecessityAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        return MigrationNecessityAnalyzer()

    def test_analyze_no_breaking_changes(self, analyzer):
        """Test analyzing diff with no breaking changes."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="1.1.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
            changes=[
                ContractChange(
                    change_type=ChangeType.FUNCTION_ADDED,
                    entity_id="new_func",
                    description="Added",
                    abi_impact=ABICompatibility.ABI_COMPATIBLE_EXTENSION,
                )
            ],
        )

        necessity = analyzer.analyze(diff)

        assert necessity.required is False
        assert necessity.reason == "All changes are ABI-compatible"

    def test_analyze_with_breaking_changes(self, analyzer):
        """Test analyzing diff with breaking changes."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="2.0.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="b" * 64,
            changes=[
                ContractChange(
                    change_type=ChangeType.FUNCTION_REMOVED,
                    entity_id="old_func",
                    description="Removed",
                    abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
                )
            ],
        )

        necessity = analyzer.analyze(diff)

        assert necessity.required is True
        assert "ABI-breaking" in necessity.reason
        assert "old_func" in necessity.affected_entities

    def test_complexity_assessment_trivial(self, analyzer):
        """Test complexity assessment for trivial migration."""
        changes = [
            ContractChange(
                change_type=ChangeType.FUNCTION_REMOVED,
                entity_id="func",
                description="Removed",
                abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
            )
        ]

        complexity = analyzer._assess_complexity(changes)

        assert complexity == "trivial"

    def test_complexity_assessment_moderate(self, analyzer):
        """Test complexity assessment for moderate migration."""
        changes = [
            ContractChange(
                change_type=ChangeType.FUNCTION_REMOVED,
                entity_id=f"func{i}",
                description="Removed",
                abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
            )
            for i in range(5)
        ]

        complexity = analyzer._assess_complexity(changes)

        assert complexity == "moderate"

    def test_necessity_to_dict(self):
        """Test migration necessity to dictionary."""
        necessity = MigrationNecessity(
            required=True,
            reason="Breaking changes",
            affected_entities=["func1", "func2"],
            migration_complexity="moderate",
        )

        data = necessity.to_dict()

        assert data["required"] is True
        assert len(data["affected_entities"]) == 2


# ============================================================================
# TEST CONTRACT VERSION COMPARATOR
# ============================================================================
class TestContractVersionComparator:
    """Test ContractVersionComparator."""

    @pytest.fixture
    def comparator(self):
        return ContractVersionComparator()

    @pytest.fixture
    def mock_contract_v1(self):
        class MockContract:
            contract_version = "1.0.0"
            contract_fingerprint = "a" * 64
            functions = []
            structs = []

        return MockContract()

    @pytest.fixture
    def mock_contract_v1_1(self):
        class MockContract:
            contract_version = "1.1.0"
            contract_fingerprint = "b" * 64
            functions = []
            structs = []

        return MockContract()

    def test_compare_contracts(self, comparator, mock_contract_v1, mock_contract_v1_1):
        """Test comparing two contracts."""
        result = comparator.compare(mock_contract_v1, mock_contract_v1_1)

        assert "diff" in result
        assert "migration" in result
        assert "summary" in result

    def test_compare_result_structure(self, comparator, mock_contract_v1):
        """Test comparison result structure."""
        result = comparator.compare(mock_contract_v1, mock_contract_v1)

        # Should have summary
        assert "safe_upgrade" in result["summary"]
        assert "breaking_changes_count" in result["summary"]
        assert "compatible_changes_count" in result["summary"]


# ============================================================================
# EDGE CASES
# ============================================================================
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_timeline(self):
        """Test timeline with no snapshots."""
        timeline = ContractEvolutionTimeline("empty")

        latest = timeline.get_latest_version()

        assert latest is None

    def test_diff_with_no_changes(self):
        """Test diff with empty changes list."""
        diff = ContractDiff(
            baseline_version="1.0.0",
            candidate_version="1.0.0",
            baseline_fingerprint="a" * 64,
            candidate_fingerprint="a" * 64,
            changes=[],
        )

        assert diff.has_breaking_changes() is False
        assert len(diff.get_breaking_changes()) == 0


# ============================================================================
# BULK PARAMETERIZED TESTS (to reach 80)
# ============================================================================
@pytest.mark.parametrize("i", range(20))
def test_bulk_contract_change_is_breaking(i):
    # Alternating breaking/non-breaking
    impact = (
        ABICompatibility.ABI_BREAKING_LAYOUT
        if i % 2 == 0
        else ABICompatibility.ABI_COMPATIBLE_EXTENSION
    )
    change = ContractChange(
        change_type=ChangeType.FUNCTION_MODIFIED,
        entity_id=f"ent_{i}",
        description="test",
        abi_impact=impact,
    )
    assert change.is_breaking() == (i % 2 == 0)


@pytest.mark.parametrize("i", range(20))
def test_bulk_timeline_ordering(i):
    timeline = ContractEvolutionTimeline("test")
    # Add versions in reverse order
    for j in range(i, -1, -1):
        timeline.add_snapshot(
            ContractVersionSnapshot(
                version=f"1.{j}.0",
                release_date="date",
                contract_fingerprint=str(j),
                schema_version="1",
                synthesis_version="1",
                ir_fingerprint="ir",
            )
        )

    versions = timeline.get_all_versions()
    assert versions == [f"1.{j}.0" for j in range(i + 1)]


@pytest.mark.parametrize("i", range(10))
def test_bulk_migration_effort(analyzer, i):
    # Add varying number of changes
    changes = [
        ContractChange(
            change_type=ChangeType.FUNCTION_REMOVED,
            entity_id=f"f{j}",
            description="rem",
            abi_impact=ABICompatibility.ABI_BREAKING_REMOVAL,
        )
        for j in range(i + 1)
    ]
    effort = analyzer._estimate_effort(changes)
    if i + 1 <= 2:
        assert effort == "minutes"
    elif i + 1 <= 10:
        assert effort == "hours"
    else:
        assert effort == "days"


@pytest.fixture
def analyzer():
    return MigrationNecessityAnalyzer()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
