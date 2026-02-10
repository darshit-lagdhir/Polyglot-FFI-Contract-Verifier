"""
Unit tests for Module 06: Package Initialization (Prompt 11/15)
Testing Level: MEDIUM (50 tests)
"""

import pytest
from pathlib import Path
import sys

# Ensure modules directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

class TestModuleImports:
    """Test module imports and public API."""
    
    def test_module_imports(self):
        """Test that module can be imported."""
        import module_06_contract_schema
        assert module_06_contract_schema is not None

    def test_version_available(self):
        """Test that version is accessible."""
        import module_06_contract_schema
        assert hasattr(module_06_contract_schema, '__version__')
        assert module_06_contract_schema.__version__ == "1.0.0"

    def test_version_info_available(self):
        """Test that version_info is accessible."""
        import module_06_contract_schema
        assert hasattr(module_06_contract_schema, '__version_info__')
        assert module_06_contract_schema.__version_info__ == (1, 0, 0)

class TestCoreEntityImports:
    """Test core entity imports."""
    
    def test_contract_document_import(self):
        from module_06_contract_schema import ContractDocument
        assert ContractDocument is not None

    def test_contract_header_import(self):
        from module_06_contract_schema import ContractHeader
        assert ContractHeader is not None

    def test_contract_clause_import(self):
        from module_06_contract_schema import ContractClause
        assert ContractClause is not None

    def test_subject_reference_import(self):
        from module_06_contract_schema import SubjectReference
        assert SubjectReference is not None

    def test_subject_kind_import(self):
        from module_06_contract_schema import SubjectKind
        assert SubjectKind is not None

    def test_severity_import(self):
        from module_06_contract_schema import Severity
        assert Severity is not None

    def test_clause_type_import(self):
        from module_06_contract_schema import ClauseType
        assert ClauseType is not None

class TestTypedClauseImports:
    """Test typed clause imports."""
    
    def test_layout_clause_import(self):
        from module_06_contract_schema import LayoutClause
        assert LayoutClause is not None

    def test_size_clause_import(self):
        from module_06_contract_schema import SizeClause
        assert SizeClause is not None

    def test_nullability_clause_import(self):
        from module_06_contract_schema import NullabilityClause
        assert NullabilityClause is not None

    def test_ownership_clause_import(self):
        from module_06_contract_schema import OwnershipClause
        assert OwnershipClause is not None

    def test_alignment_clause_import(self):
        from module_06_contract_schema import AlignmentClause
        assert AlignmentClause is not None

    def test_lifetime_clause_import(self):
        from module_06_contract_schema import LifetimeClause
        assert LifetimeClause is not None

    def test_relational_clause_import(self):
        from module_06_contract_schema import RelationalClause
        assert RelationalClause is not None

    def test_create_clause_factory_import(self):
        from module_06_contract_schema import create_clause_from_type
        assert create_clause_from_type is not None

class TestGenerationImports:
    """Test generation-related imports."""
    
    def test_contract_generator_import(self):
        from module_06_contract_schema import ContractGenerator
        assert ContractGenerator is not None

    def test_generation_config_import(self):
        from module_06_contract_schema import GenerationConfig
        assert GenerationConfig is not None

    def test_naming_pattern_matcher_import(self):
        from module_06_contract_schema import NamingPatternMatcher
        assert NamingPatternMatcher is not None

class TestValidationImports:
    """Test validation-related imports."""
    
    def test_contract_validator_import(self):
        from module_06_contract_schema import ContractValidator
        assert ContractValidator is not None

    def test_validation_context_import(self):
        from module_06_contract_schema import ValidationContext
        assert ValidationContext is not None

    def test_validation_result_import(self):
        from module_06_contract_schema import ValidationResult
        assert ValidationResult is not None

    def test_validation_layer_import(self):
        from module_06_contract_schema import ValidationLayer
        assert ValidationLayer is not None

    def test_validation_error_import(self):
        from module_06_contract_schema import ValidationError
        assert ValidationError is not None

    def test_complete_validation_result_import(self):
        from module_06_contract_schema import CompleteValidationResult
        assert CompleteValidationResult is not None

class TestVersioningImports:
    """Test versioning-related imports."""
    
    def test_semantic_version_import(self):
        from module_06_contract_schema import SemanticVersion
        assert SemanticVersion is not None

    def test_contract_differ_import(self):
        from module_06_contract_schema import ContractDiffer
        assert ContractDiffer is not None

class TestSerializationImports:
    """Test serialization-related imports."""
    
    def test_contract_serializer_import(self):
        from module_06_contract_schema import ContractSerializer
        assert ContractSerializer is not None

    def test_contract_deserializer_import(self):
        from module_06_contract_schema import ContractDeserializer
        assert ContractDeserializer is not None

    def test_contract_file_manager_import(self):
        from module_06_contract_schema import ContractFileManager
        assert ContractFileManager is not None

    def test_serialization_error_import(self):
        from module_06_contract_schema import SerializationError
        assert SerializationError is not None

    def test_integrity_error_import(self):
        from module_06_contract_schema import IntegrityError
        assert IntegrityError is not None

class TestDiffingImports:
    """Test diffing-related imports."""
    
    def test_advanced_contract_differ_import(self):
        from module_06_contract_schema import AdvancedContractDiffer
        assert AdvancedContractDiffer is not None

    def test_migration_guide_import(self):
        from module_06_contract_schema import MigrationGuide
        assert MigrationGuide is not None

    def test_change_impact_import(self):
        from module_06_contract_schema import ChangeImpact
        assert ChangeImpact is not None

    def test_change_category_import(self):
        from module_06_contract_schema import ChangeCategory
        assert ChangeCategory is not None

class TestEnforcementImports:
    """Test enforcement-related imports."""
    
    def test_enforcement_engine_import(self):
        from module_06_contract_schema import EnforcementEngine
        assert EnforcementEngine is not None

    def test_python_adapter_import(self):
        from module_06_contract_schema import PythonAdapter
        assert PythonAdapter is not None

    def test_enforcement_mode_import(self):
        from module_06_contract_schema import EnforcementMode
        assert EnforcementMode is not None

    def test_violation_type_import(self):
        from module_06_contract_schema import ViolationType
        assert ViolationType is not None

    def test_enforcement_violation_import(self):
        from module_06_contract_schema import EnforcementViolation
        assert EnforcementViolation is not None

class TestCLIImports:
    """Test CLI imports."""
    
    def test_cli_import(self):
        from module_06_contract_schema import cli
        assert cli is not None

    def test_main_import(self):
        from module_06_contract_schema import main
        assert main is not None

class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_load_contract_available(self):
        from module_06_contract_schema import load_contract
        assert load_contract is not None
        assert callable(load_contract)

    def test_save_contract_available(self):
        from module_06_contract_schema import save_contract
        assert save_contract is not None
        assert callable(save_contract)

    def test_quick_validate_available(self):
        from module_06_contract_schema import quick_validate
        assert quick_validate is not None
        assert callable(quick_validate)

class TestAllExports:
    """Test all completeness."""
    
    def test_all_defined(self):
        import module_06_contract_schema
        assert hasattr(module_06_contract_schema, '__all__')
        assert len(module_06_contract_schema.__all__) > 50

    def test_all_exports_importable(self):
        import module_06_contract_schema
        # Test that all __all__ exports are actually importable
        for name in module_06_contract_schema.__all__:
            assert hasattr(module_06_contract_schema, name), f"{name} in __all__ but not available"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
