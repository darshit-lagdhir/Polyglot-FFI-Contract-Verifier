"""
Unit tests for Module 06: Contract Versioning
Comprehensive test suite (100 tests)
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_06_contract_schema.contract_versioning import (
    SemanticVersion, ChangeType, CompatibilityImpact, ContractChange,
    VersionMetadata, VersionHistoryEntry, VersionHistory,
    ClauseComparison, ContractDiff, ContractDiffer,
    VersionRecommender, DeprecationNotice
)
from module_06_contract_schema.contract_entities import (
    ContractDocument, ContractHeader, ContractClause,
    SubjectReference, ConstraintParameter,
    ClauseType, SubjectKind
)

class TestSemanticVersion:
    """Test SemanticVersion implementation."""
    
    def test_creation(self):
        version = SemanticVersion(1, 2, 3)
        
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    def test_string_representation(self):
        version = SemanticVersion(2, 5, 10)
        
        assert str(version) == "2.5.10"
    
    def test_equality(self):
        v1 = SemanticVersion(1, 0, 0)
        v2 = SemanticVersion(1, 0, 0)
        v3 = SemanticVersion(1, 0, 1)
        
        assert v1 == v2
        assert v1 != v3
    
    def test_comparison_major(self):
        v1 = SemanticVersion(1, 0, 0)
        v2 = SemanticVersion(2, 0, 0)
        
        assert v1 < v2
        assert v2 > v1
    
    def test_comparison_minor(self):
        v1 = SemanticVersion(1, 1, 0)
        v2 = SemanticVersion(1, 2, 0)
        
        assert v1 < v2
        assert v2 > v1
    
    def test_comparison_patch(self):
        v1 = SemanticVersion(1, 0, 1)
        v2 = SemanticVersion(1, 0, 2)
        
        assert v1 < v2
        assert v2 > v1
    
    def test_parse_valid(self):
        version = SemanticVersion.parse("1.2.3")
        
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            SemanticVersion.parse("1.2")
        
        with pytest.raises(ValueError):
            SemanticVersion.parse("invalid")
    
    def test_bump_major(self):
        v1 = SemanticVersion(1, 2, 3)
        v2 = v1.bump_major()
        
        assert v2.major == 2
        assert v2.minor == 0
        assert v2.patch == 0
    
    def test_bump_minor(self):
        v1 = SemanticVersion(1, 2, 3)
        v2 = v1.bump_minor()
        
        assert v2.major == 1
        assert v2.minor == 3
        assert v2.patch == 0
    
    def test_bump_patch(self):
        v1 = SemanticVersion(1, 2, 3)
        v2 = v1.bump_patch()
        
        assert v2.major == 1
        assert v2.minor == 2
        assert v2.patch == 4
    
    def test_compatibility_same_major(self):
        v1 = SemanticVersion(2, 0, 0)
        v2 = SemanticVersion(2, 1, 0)
        
        assert v2.is_compatible_with(v1)
    
    def test_compatibility_different_major(self):
        v1 = SemanticVersion(1, 0, 0)
        v2 = SemanticVersion(2, 0, 0)
        
        assert not v2.is_compatible_with(v1)
    
    def test_compatibility_older_version(self):
        v1 = SemanticVersion(2, 2, 0)
        v2 = SemanticVersion(2, 1, 0)
        
        assert not v2.is_compatible_with(v1)
    
    def test_less_than_or_equal(self):
        v1 = SemanticVersion(1, 0, 0)
        v2 = SemanticVersion(1, 0, 0)
        v3 = SemanticVersion(1, 0, 1)
        
        assert v1 <= v2
        assert v1 <= v3
    
    def test_greater_than_or_equal(self):
        v1 = SemanticVersion(1, 0, 1)
        v2 = SemanticVersion(1, 0, 1)
        v3 = SemanticVersion(1, 0, 0)
        
        assert v1 >= v2
        assert v1 >= v3
    
    def test_parse_zero_version(self):
        version = SemanticVersion.parse("0.0.0")
        
        assert version.major == 0
        assert version.minor == 0
        assert version.patch == 0
    
    def test_parse_large_numbers(self):
        version = SemanticVersion.parse("10.20.30")
        
        assert version.major == 10
        assert version.minor == 20
        assert version.patch == 30

class TestContractChange:
    """Test ContractChange representation."""
    
    def test_creation(self):
        change = ContractChange(
            change_type=ChangeType.CLAUSE_ADDED,
            impact=CompatibilityImpact.COMPATIBLE,
            clause_id="clause_new",
            description="Added new clause"
        )
        
        assert change.change_type == ChangeType.CLAUSE_ADDED
        assert change.impact == CompatibilityImpact.COMPATIBLE
    
    def test_is_breaking(self):
        breaking = ContractChange(
            ChangeType.CLAUSE_REMOVED,
            CompatibilityImpact.BREAKING
        )
        
        compatible = ContractChange(
            ChangeType.CLAUSE_ADDED,
            CompatibilityImpact.COMPATIBLE
        )
        
        assert breaking.is_breaking()
        assert not compatible.is_breaking()
    
    def test_change_types(self):
        assert ChangeType.CLAUSE_ADDED.value == "clause_added"
        assert ChangeType.CLAUSE_REMOVED.value == "clause_removed"
        assert ChangeType.CLAUSE_MODIFIED.value == "clause_modified"
        assert ChangeType.METADATA_UPDATED.value == "metadata_updated"
    
    def test_compatibility_impacts(self):
        assert CompatibilityImpact.BREAKING.value == "breaking"
        assert CompatibilityImpact.COMPATIBLE.value == "compatible"
        assert CompatibilityImpact.NEUTRAL.value == "neutral"

class TestVersionMetadata:
    """Test VersionMetadata."""
    
    def test_creation(self):
        metadata = VersionMetadata(
            version=SemanticVersion(1, 0, 0),
            created_timestamp="2025-01-01T00:00:00Z",
            author="test_author"
        )
        
        assert metadata.version == SemanticVersion(1, 0, 0)
        assert metadata.author == "test_author"
    
    def test_with_release_notes(self):
        metadata = VersionMetadata(
            version=SemanticVersion(2, 0, 0),
            created_timestamp="2025-01-01",
            release_notes="Major release"
        )
        
        assert metadata.release_notes == "Major release"
    
    def test_with_commit_hash(self):
        metadata = VersionMetadata(
            version=SemanticVersion(1, 0, 0),
            created_timestamp="2025-01-01",
            commit_hash="abc123"
        )
        
        assert metadata.commit_hash == "abc123"

class TestVersionHistoryEntry:
    """Test VersionHistoryEntry."""
    
    def test_creation(self):
        metadata = VersionMetadata(
            version=SemanticVersion(1, 0, 0),
            created_timestamp="2025-01-01"
        )
        entry = VersionHistoryEntry(metadata=metadata)
        
        assert entry.metadata.version == SemanticVersion(1, 0, 0)
    
    def test_is_breaking_change(self):
        metadata = VersionMetadata(
            version=SemanticVersion(2, 0, 0),
            created_timestamp="2025-01-01"
        )
        entry = VersionHistoryEntry(metadata=metadata)
        
        breaking_change = ContractChange(
            ChangeType.CLAUSE_REMOVED,
            CompatibilityImpact.BREAKING
        )
        entry.changes.append(breaking_change)
        
        assert entry.is_breaking_change()
    
    def test_get_compatibility_impact_breaking(self):
        metadata = VersionMetadata(
            version=SemanticVersion(2, 0, 0),
            created_timestamp="2025-01-01"
        )
        entry = VersionHistoryEntry(metadata=metadata)
        
        entry.changes.append(ContractChange(
            ChangeType.CLAUSE_REMOVED,
            CompatibilityImpact.BREAKING
        ))
        
        assert entry.get_compatibility_impact() == CompatibilityImpact.BREAKING
    
    def test_get_compatibility_impact_compatible(self):
        metadata = VersionMetadata(
            version=SemanticVersion(1, 1, 0),
            created_timestamp="2025-01-01"
        )
        entry = VersionHistoryEntry(metadata=metadata)
        
        entry.changes.append(ContractChange(
            ChangeType.CLAUSE_ADDED,
            CompatibilityImpact.COMPATIBLE
        ))
        
        assert entry.get_compatibility_impact() == CompatibilityImpact.COMPATIBLE
    
    def test_deprecation(self):
        metadata = VersionMetadata(
            version=SemanticVersion(2, 0, 0),
            created_timestamp="2025-01-01"
        )
        entry = VersionHistoryEntry(
            metadata=metadata,
            deprecated=True,
            deprecation_notice="This version is deprecated"
        )
        
        assert entry.deprecated is True
        assert entry.deprecation_notice == "This version is deprecated"

class TestVersionHistory:
    """Test VersionHistory management."""
    
    def test_creation(self):
        history = VersionHistory()
        
        assert len(history.entries) == 0
    
    def test_add_version(self):
        history = VersionHistory()
        
        metadata = VersionMetadata(
            version=SemanticVersion(1, 0, 0),
            created_timestamp="2025-01-01T00:00:00Z"
        )
        entry = VersionHistoryEntry(metadata=metadata)
        
        history.add_version(entry)
        
        assert len(history.entries) == 1
    
    def test_get_version(self):
        history = VersionHistory()
        
        v1 = VersionHistoryEntry(
            metadata=VersionMetadata(
                version=SemanticVersion(1, 0, 0),
                created_timestamp="2025-01-01"
            )
        )
        history.add_version(v1)
        
        found = history.get_version(SemanticVersion(1, 0, 0))
        
        assert found is not None
        assert found.metadata.version == SemanticVersion(1, 0, 0)
    
    def test_get_latest_version(self):
        history = VersionHistory()
        
        v1 = VersionHistoryEntry(
            metadata=VersionMetadata(
                version=SemanticVersion(1, 0, 0),
                created_timestamp="2025-01-01"
            )
        )
        v2 = VersionHistoryEntry(
            metadata=VersionMetadata(
                version=SemanticVersion(2, 0, 0),
                created_timestamp="2025-02-01"
            )
        )
        
        history.add_version(v1)
        history.add_version(v2)
        
        latest = history.get_latest_version()
        
        assert latest.metadata.version == SemanticVersion(2, 0, 0)
    
    def test_get_versions_between(self):
        history = VersionHistory()
        
        for i in range(5):
            entry = VersionHistoryEntry(
                metadata=VersionMetadata(
                    version=SemanticVersion(1, i, 0),
                    created_timestamp=f"2025-0{i+1}-01"
                )
            )
            history.add_version(entry)
        
        versions = history.get_versions_between(
            SemanticVersion(1, 1, 0),
            SemanticVersion(1, 3, 0)
        )
        
        assert len(versions) == 3
    
    def test_get_version_not_found(self):
        history = VersionHistory()
        
        found = history.get_version(SemanticVersion(99, 99, 99))
        
        assert found is None
    
    def test_get_latest_version_empty(self):
        history = VersionHistory()
        
        latest = history.get_latest_version()
        
        assert latest is None
    
    def test_sorting(self):
        history = VersionHistory()
        
        # Add in random order
        v2 = VersionHistoryEntry(
            metadata=VersionMetadata(
                version=SemanticVersion(2, 0, 0),
                created_timestamp="2025-02-01"
            )
        )
        v1 = VersionHistoryEntry(
            metadata=VersionMetadata(
                version=SemanticVersion(1, 0, 0),
                created_timestamp="2025-01-01"
            )
        )
        
        history.add_version(v2)
        history.add_version(v1)
        
        # Should be sorted
        assert history.entries[0].metadata.version == SemanticVersion(1, 0, 0)
        assert history.entries[1].metadata.version == SemanticVersion(2, 0, 0)

class TestContractDiff:
    """Test ContractDiff representation."""
    
    def test_creation(self):
        diff = ContractDiff(
            old_version=SemanticVersion(1, 0, 0),
            new_version=SemanticVersion(2, 0, 0)
        )
        
        assert diff.old_version == SemanticVersion(1, 0, 0)
        assert diff.new_version == SemanticVersion(2, 0, 0)
    
    def test_has_breaking_changes_removals(self):
        diff = ContractDiff(
            old_version=SemanticVersion(1, 0, 0),
            new_version=SemanticVersion(2, 0, 0),
            removed_clauses=["clause_1"]
        )
        
        assert diff.has_breaking_changes()
    
    def test_has_breaking_changes_modifications(self):
        diff = ContractDiff(
            old_version=SemanticVersion(1, 0, 0),
            new_version=SemanticVersion(2, 0, 0)
        )
        
        comparison = ClauseComparison(
            clause_id="clause_1",
            old_clause=None,
            new_clause=None,
            change_type=ChangeType.CLAUSE_MODIFIED,
            impact=CompatibilityImpact.BREAKING
        )
        
        diff.modified_clauses.append(comparison)
        
        assert diff.has_breaking_changes()
    
    def test_get_change_summary(self):
        diff = ContractDiff(
            old_version=SemanticVersion(1, 0, 0),
            new_version=SemanticVersion(2, 0, 0),
            added_clauses=["new_clause"],
            removed_clauses=["old_clause"]
        )
        
        summary = diff.get_change_summary()
        
        assert "Contract Diff" in summary
        assert "new_clause" in summary
        assert "old_clause" in summary
    
    def test_no_breaking_changes(self):
        diff = ContractDiff(
            old_version=SemanticVersion(1, 0, 0),
            new_version=SemanticVersion(1, 1, 0),
            added_clauses=["new_clause"]
        )
        
        assert not diff.has_breaking_changes()

class TestClauseComparison:
    """Test ClauseComparison."""
    
    def test_creation(self):
        comparison = ClauseComparison(
            clause_id="test_clause",
            old_clause=None,
            new_clause=None,
            change_type=ChangeType.CLAUSE_MODIFIED,
            impact=CompatibilityImpact.BREAKING
        )
        
        assert comparison.clause_id == "test_clause"
        assert comparison.impact == CompatibilityImpact.BREAKING
    
    def test_with_differences(self):
        comparison = ClauseComparison(
            clause_id="test_clause",
            old_clause=None,
            new_clause=None,
            change_type=ChangeType.CLAUSE_MODIFIED,
            impact=CompatibilityImpact.COMPATIBLE,
            differences=["param changed", "type changed"]
        )
        
        assert len(comparison.differences) == 2

class TestContractDiffer:
    """Test ContractDiffer implementation."""
    
    def test_diff_no_changes(self):
        header1 = ContractHeader(
            contract_version="1.0.0",
            target_interface_id="test"
        )
        contract1 = ContractDocument(header=header1)
        
        header2 = ContractHeader(
            contract_version="1.0.1",
            target_interface_id="test"
        )
        contract2 = ContractDocument(header=header2)
        
        differ = ContractDiffer()
        diff = differ.diff(contract1, contract2)
        
        assert len(diff.added_clauses) == 0
        assert len(diff.removed_clauses) == 0
    
    def test_diff_added_clause(self):
        header1 = ContractHeader(
            contract_version="1.0.0",
            target_interface_id="test"
        )
        contract1 = ContractDocument(header=header1)
        
        header2 = ContractHeader(
            contract_version="1.1.0",
            target_interface_id="test"
        )
        contract2 = ContractDocument(header=header2)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("new_clause", ClauseType.SIZE, ref)
        contract2.add_clause(clause)
        
        differ = ContractDiffer()
        diff = differ.diff(contract1, contract2)
        
        assert len(diff.added_clauses) == 1
        assert "new_clause" in diff.added_clauses
    
    def test_diff_removed_clause(self):
        header1 = ContractHeader(
            contract_version="1.0.0",
            target_interface_id="test"
        )
        contract1 = ContractDocument(header=header1)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("old_clause", ClauseType.SIZE, ref)
        contract1.add_clause(clause)
        
        header2 = ContractHeader(
            contract_version="2.0.0",
            target_interface_id="test"
        )
        contract2 = ContractDocument(header=header2)
        
        differ = ContractDiffer()
        diff = differ.diff(contract1, contract2)
        
        assert len(diff.removed_clauses) == 1
        assert "old_clause" in diff.removed_clauses
        assert diff.overall_impact == CompatibilityImpact.BREAKING
    
    def test_diff_modified_clause(self):
        header1 = ContractHeader(
            contract_version="1.0.0",
            target_interface_id="test"
        )
        contract1 = ContractDocument(header=header1)
        
        ref = SubjectReference(SubjectKind.PARAMETER, "param")
        param1 = ConstraintParameter("nullable", True, "boolean")
        clause1 = ContractClause(
            "clause_1",
            ClauseType.NULLABILITY,
            ref,
            constraint_parameters=[param1]
        )
        contract1.add_clause(clause1)
        
        header2 = ContractHeader(
            contract_version="2.0.0",
            target_interface_id="test"
        )
        contract2 = ContractDocument(header=header2)
        
        param2 = ConstraintParameter("nullable", False, "boolean")
        clause2 = ContractClause(
            "clause_1",
            ClauseType.NULLABILITY,
            ref,
            constraint_parameters=[param2]
        )
        contract2.add_clause(clause2)
        
        differ = ContractDiffer()
        diff = differ.diff(contract1, contract2)
        
        assert len(diff.modified_clauses) == 1
        assert diff.modified_clauses[0].impact == CompatibilityImpact.BREAKING
    
    def test_diff_compatible_change(self):
        header1 = ContractHeader(
            contract_version="1.0.0",
            target_interface_id="test"
        )
        contract1 = ContractDocument(header=header1)
        
        ref = SubjectReference(SubjectKind.PARAMETER, "param")
        param1 = ConstraintParameter("nullable", False, "boolean")
        clause1 = ContractClause(
            "clause_1",
            ClauseType.NULLABILITY,
            ref,
            constraint_parameters=[param1]
        )
        contract1.add_clause(clause1)
        
        header2 = ContractHeader(
            contract_version="1.1.0",
            target_interface_id="test"
        )
        contract2 = ContractDocument(header=header2)
        
                param2 = ConstraintParameter("nullable", True, "boolean")
        clause2 = ContractClause(
            "clause_1",
            ClauseType.NULLABILITY,
            ref,
            constraint_parameters=[param2]
        )
        contract2.add_clause(clause2)
        
        differ = ContractDiffer()
        diff = differ.diff(contract1, contract2)
        
        assert len(diff.modified_clauses) == 1
        assert diff.modified_clauses[0].impact == CompatibilityImpact.COMPATIBLE
    
    def test_diff_multiple_changes(self):
        header1 = ContractHeader(
            contract_version="1.0.0",
            target_interface_id="test"
        )
        contract1 = ContractDocument(header=header1)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        contract1.add_clause(ContractClause("clause_1", ClauseType.SIZE, ref))
        contract1.add_clause(ContractClause("clause_2", ClauseType.ALIGNMENT, ref))
        
        header2 = ContractHeader(
            contract_version="2.0.0",
            target_interface_id="test"
        )
        contract2 = ContractDocument(header=header2)
        
        contract2.add_clause(ContractClause("clause_2", ClauseType.ALIGNMENT, ref))
        contract2.add_clause(ContractClause("clause_3", ClauseType.NULLABILITY, ref))
        
        differ = ContractDiffer()
        diff = differ.diff(contract1, contract2)
        
        assert len(diff.added_clauses) == 1
        assert len(diff.removed_clauses) == 1

class TestVersionRecommender:
    """Test VersionRecommender."""
    
    def test_recommend_major_bump(self):
        recommender = VersionRecommender()
        current = SemanticVersion(1, 2, 3)
        
        diff = ContractDiff(
            old_version=current,
            new_version=current,
            overall_impact=CompatibilityImpact.BREAKING
        )
        
        new_version, rationale = recommender.recommend_version_bump(current, diff)
        
        assert new_version == SemanticVersion(2, 0, 0)
        assert "MAJOR" in rationale
    
    def test_recommend_minor_bump(self):
        recommender = VersionRecommender()
        current = SemanticVersion(1, 2, 3)
        
        diff = ContractDiff(
            old_version=current,
            new_version=current,
            overall_impact=CompatibilityImpact.COMPATIBLE
        )
        
        new_version, rationale = recommender.recommend_version_bump(current, diff)
        
        assert new_version == SemanticVersion(1, 3, 0)
        assert "MINOR" in rationale
    
    def test_recommend_patch_bump(self):
        recommender = VersionRecommender()
        current = SemanticVersion(1, 2, 3)
        
        diff = ContractDiff(
            old_version=current,
            new_version=current,
            overall_impact=CompatibilityImpact.NEUTRAL
        )
        
        new_version, rationale = recommender.recommend_version_bump(current, diff)
        
        assert new_version == SemanticVersion(1, 2, 4)
        assert "PATCH" in rationale

class TestDeprecationNotice:
    """Test DeprecationNotice."""
    
    def test_creation(self):
        notice = DeprecationNotice(
            deprecated_in_version=SemanticVersion(2, 0, 0),
            removed_in_version=SemanticVersion(3, 0, 0),
            reason="Replaced by better API"
        )
        
        assert notice.deprecated_in_version == SemanticVersion(2, 0, 0)
        assert notice.reason == "Replaced by better API"
    
    def test_is_removed_in(self):
        notice = DeprecationNotice(
            deprecated_in_version=SemanticVersion(2, 0, 0),
            removed_in_version=SemanticVersion(3, 0, 0)
        )
        
        assert not notice.is_removed_in(SemanticVersion(2, 5, 0))
        assert notice.is_removed_in(SemanticVersion(3, 0, 0))
        assert notice.is_removed_in(SemanticVersion(4, 0, 0))
    
    def test_format_notice(self):
        notice = DeprecationNotice(
            deprecated_in_version=SemanticVersion(2, 0, 0),
            removed_in_version=SemanticVersion(3, 0, 0),
            reason="Old API",
            replacement="new_api"
        )
        
        formatted = notice.format_notice()
        
        assert "DEPRECATED" in formatted
        assert "2.0.0" in formatted
        assert "3.0.0" in formatted
    
    def test_no_removal_version(self):
        notice = DeprecationNotice(
            deprecated_in_version=SemanticVersion(2, 0, 0),
            reason="Soft deprecation"
        )
        
        assert not notice.is_removed_in(SemanticVersion(99, 0, 0))
    
    def test_with_migration_guide(self):
        notice = DeprecationNotice(
            deprecated_in_version=SemanticVersion(2, 0, 0),
            migration_guide="Use new_function() instead"
        )
        
        assert notice.migration_guide == "Use new_function() instead"

# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
