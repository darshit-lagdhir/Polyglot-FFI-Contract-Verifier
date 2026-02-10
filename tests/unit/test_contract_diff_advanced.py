"""
Unit tests for the Advanced Contract Diffing system.
Validates semantic change detection, impact classification, and migration guidance.
"""

import pytest
from pathlib import Path
import sys

# Ensure the modules directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_06_contract_schema.contract_diff_advanced import (
    ChangeCategory, ChangeImpact, MigrationDifficulty,
    ParameterChange, DetailedClauseChange, MigrationStep,
    MigrationGuide, AdvancedDiffResult, NullabilityChangeAnalyzer,
    SizeChangeAnalyzer, OwnershipChangeAnalyzer, AdvancedContractDiffer
)
from module_06_contract_schema.contract_entities import (
    ContractDocument, ContractHeader, ContractClause,
    SubjectReference, ConstraintParameter, ClauseType, SubjectKind
)
from module_06_contract_schema.contract_versioning import SemanticVersion

class TestSemanticClassification:
    """Validation for impact classification logic."""
    
    def test_nullability_tightening_is_breaking(self):
        analyzer = NullabilityChangeAnalyzer()
        ref = SubjectReference(SubjectKind.PARAMETER, "p1")
        old_c = ContractClause("c1", ClauseType.NULLABILITY, ref, [ConstraintParameter("nullable", True, "boolean")])
        new_c = ContractClause("c1", ClauseType.NULLABILITY, ref, [ConstraintParameter("nullable", False, "boolean")])
        assert analyzer.analyze_impact(old_c, new_c) == ChangeImpact.BREAKING

    def test_nullability_relaxation_is_compatible(self):
        analyzer = NullabilityChangeAnalyzer()
        ref = SubjectReference(SubjectKind.PARAMETER, "p1")
        old_c = ContractClause("c1", ClauseType.NULLABILITY, ref, [ConstraintParameter("nullable", False, "boolean")])
        new_c = ContractClause("c1", ClauseType.NULLABILITY, ref, [ConstraintParameter("nullable", True, "boolean")])
        assert analyzer.analyze_impact(old_c, new_c) == ChangeImpact.COMPATIBLE

    def test_size_increase_is_breaking(self):
        analyzer = SizeChangeAnalyzer()
        ref = SubjectReference(SubjectKind.PARAMETER, "buf")
        old_c = ContractClause("c1", ClauseType.SIZE, ref, [ConstraintParameter("size_value", 10, "integer")])
        new_c = ContractClause("c1", ClauseType.SIZE, ref, [ConstraintParameter("size_value", 20, "integer")])
        assert analyzer.analyze_impact(old_c, new_c) == ChangeImpact.BREAKING

    def test_size_decrease_is_compatible(self):
        analyzer = SizeChangeAnalyzer()
        ref = SubjectReference(SubjectKind.PARAMETER, "buf")
        old_c = ContractClause("c1", ClauseType.SIZE, ref, [ConstraintParameter("size_value", 20, "integer")])
        new_c = ContractClause("c1", ClauseType.SIZE, ref, [ConstraintParameter("size_value", 10, "integer")])
        assert analyzer.analyze_impact(old_c, new_c) == ChangeImpact.COMPATIBLE

class TestMigrationGuidance:
    """Validation for migration step synthesis."""
    
    def test_nullability_migration_generation(self):
        analyzer = NullabilityChangeAnalyzer()
        ref = SubjectReference(SubjectKind.PARAMETER, "p1")
        old_c = ContractClause("c1", ClauseType.NULLABILITY, ref, [ConstraintParameter("nullable", True, "boolean")])
        new_c = ContractClause("c1", ClauseType.NULLABILITY, ref, [ConstraintParameter("nullable", False, "boolean")])
        step = analyzer.generate_migration_step(old_c, new_c)
        assert step is not None
        assert "non-null" in step.change_description
        assert step.difficulty == MigrationDifficulty.EASY

class TestAdvancedDiffer:
    """Validation for high-level difference orchestration."""
    
    @pytest.fixture
    def differ(self):
        return AdvancedContractDiffer()

    def test_full_diff_orchestration(self, differ):
        h1 = ContractHeader(contract_version="1.0.0", target_interface_id="libtest")
        doc1 = ContractDocument(header=h1)
        ref = SubjectReference(SubjectKind.PARAMETER, "p1")
        doc1.add_clause(ContractClause("c1", ClauseType.NULLABILITY, ref, [ConstraintParameter("nullable", True, "boolean")]))
        
        h2 = ContractHeader(contract_version="2.0.0", target_interface_id="libtest")
        doc2 = ContractDocument(header=h2)
        doc2.add_clause(ContractClause("c1", ClauseType.NULLABILITY, ref, [ConstraintParameter("nullable", False, "boolean")]))
        
        result = differ.compute_diff(doc1, doc2)
        assert result.overall_impact == ChangeImpact.BREAKING
        assert len(result.detailed_changes) == 1
        assert result.migration_guide is not None
        assert len(result.migration_guide.steps) == 1

    def test_compatible_addition_detection(self, differ):
        h1 = ContractHeader(contract_version="1.0.0", target_interface_id="libtest")
        doc1 = ContractDocument(header=h1)
        
        h2 = ContractHeader(contract_version="1.1.0", target_interface_id="libtest")
        doc2 = ContractDocument(header=h2)
        ref = SubjectReference(SubjectKind.PARAMETER, "p1")
        doc2.add_clause(ContractClause("cnew", ClauseType.SIZE, ref, [ConstraintParameter("size_value", 10, "integer")]))
        
        result = differ.compute_diff(doc1, doc2)
        assert result.overall_impact == ChangeImpact.COMPATIBLE
        assert result.detailed_changes[0].category == ChangeCategory.CLAUSE_ADDED

class TestResultFormatting:
    """Validation for reporting and visualization."""
    
    def test_summary_formatting(self):
        res = AdvancedDiffResult(SemanticVersion(1,0,0), SemanticVersion(2,0,0))
        res.detailed_changes.append(DetailedClauseChange("c1", ChangeCategory.CLAUSE_REMOVED, ChangeImpact.BREAKING, description="Test Removal"))
        res.overall_impact = ChangeImpact.BREAKING
        summary = res.format_summary()
        assert "BREAKING CHANGES" in summary
        assert "Test Removal" in summary

if __name__ == '__main__':
    pytest.main([__file__])
