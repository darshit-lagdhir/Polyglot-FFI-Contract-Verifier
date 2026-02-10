"""
Unit tests for Module 06: Documentation (Prompt 12/15)
Testing Level: MEDIUM (30 tests)
"""

import pytest
from pathlib import Path
import sys

# Ensure modules directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))


class TestREADMEExists:
    """Test README.md exists and has content."""
    
    def test_readme_exists(self):
        readme_path = Path(__file__).parent.parent.parent / 'modules' / 'module_06_contract_schema' / 'README.md'
        assert readme_path.exists(), "README.md not found"
    
    def test_readme_not_empty(self):
        readme_path = Path(__file__).parent.parent.parent / 'modules' / 'module_06_contract_schema' / 'README.md'
        content = readme_path.read_text(encoding='utf-8')
        assert len(content) > 1000, "README.md is too short or empty"


class TestREADMEContent:
    """Test README.md contains required sections."""
    
    @pytest.fixture
    def readme_content(self):
        readme_path = Path(__file__).parent.parent.parent / 'modules' / 'module_06_contract_schema' / 'README.md'
        return readme_path.read_text(encoding='utf-8')
    
    def test_has_title(self, readme_content):
        assert "# Module 06: Contract Schema & Synthesis" in readme_content
    
    def test_has_overview(self, readme_content):
        assert "## 🎯 Overview" in readme_content
    
    def test_has_quick_start(self, readme_content):
        assert "## 🚀 Quick Start" in readme_content
    
    def test_has_installation(self, readme_content):
        assert "### Installation" in readme_content
    
    def test_has_architecture(self, readme_content):
        assert "## 🏗️ Architecture" in readme_content
    
    def test_has_license(self, readme_content):
        assert "## 📄 License" in readme_content


    def test_has_performance(self, readme_content):
        assert "## 📊 Performance" in readme_content

    def test_has_testing(self, readme_content):
        assert "## 🧪 Testing" in readme_content

class TestExamplesExist:
    """Test that examples directory exists."""
    
    def test_examples_directory_exists(self):
        examples_dir = Path(__file__).parent.parent.parent / 'examples' / 'module_06'
        assert examples_dir.exists(), "examples/module_06 directory not found"
    
    def test_basic_generation_example_exists(self):
        example_dir = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '01_basic_generation'
        assert example_dir.exists(), "Basic generation example not found"
    
    def test_validation_example_exists(self):
        example_dir = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '02_validation'
        assert example_dir.exists(), "Validation example not found"

    def test_examples_readme_exists(self):
        readme_path = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / 'README.md'
        assert readme_path.exists(), "Examples README.md not found"


class TestExampleContent:
    """Test that examples have proper structure."""
    
    def test_basic_generation_has_readme(self):
        readme_path = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '01_basic_generation' / 'README.md'
        assert readme_path.exists(), "Example 01 README.md not found"
    
    def test_basic_generation_has_code(self):
        code_path = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '01_basic_generation' / 'generate.py'
        assert code_path.exists(), "Example 01 generate.py not found"
    
    def test_validation_has_code(self):
        code_path = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '02_validation' / 'validate.py'
        assert code_path.exists(), "Example 02 validate.py not found"


class TestDocstrings:
    """Test that public API has docstrings."""
    
    def test_contract_generator_has_docstring(self):
        from module_06_contract_schema import ContractGenerator
        assert ContractGenerator.__doc__ is not None
        assert len(ContractGenerator.__doc__) > 100
    
    def test_contract_validator_has_docstring(self):
        from module_06_contract_schema import ContractValidator
        assert ContractValidator.__doc__ is not None
        assert len(ContractValidator.__doc__) > 100
    
    def test_enforcement_engine_has_docstring(self):
        from module_06_contract_schema import EnforcementEngine
        assert EnforcementEngine.__doc__ is not None
        assert len(EnforcementEngine.__doc__) > 100

    def test_contract_document_has_docstring(self):
        from module_06_contract_schema import ContractDocument
        assert ContractDocument.__doc__ is not None
        assert len(ContractDocument.__doc__) > 50


    def test_semantic_version_has_docstring(self):
        from module_06_contract_schema import SemanticVersion
        assert SemanticVersion.__doc__ is not None
        assert len(SemanticVersion.__doc__) > 50

    def test_contract_differ_has_docstring(self):
        from module_06_contract_schema import ContractDiffer
        assert ContractDiffer.__doc__ is not None
        assert len(ContractDiffer.__doc__) > 50

    def test_python_adapter_has_docstring(self):
        from module_06_contract_schema import PythonAdapter
        assert PythonAdapter.__doc__ is not None
        assert len(PythonAdapter.__doc__) > 50

    def test_advanced_contract_differ_has_docstring(self):
        from module_06_contract_schema import AdvancedContractDiffer
        assert AdvancedContractDiffer.__doc__ is not None
        assert len(AdvancedContractDiffer.__doc__) > 50

class TestModuleDocstring:
    """Test module-level docstring."""
    
    def test_module_has_docstring(self):
        import module_06_contract_schema
        assert module_06_contract_schema.__doc__ is not None
        assert len(module_06_contract_schema.__doc__) > 500


class TestExampleExecution:
    """Test that examples can be imported (for syntax check)."""
    
    def test_import_example_01(self):
        example_path = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '01_basic_generation'
        sys.path.insert(0, str(example_path))
        import generate
        assert generate.main is not None
        sys.path.pop(0)

    def test_import_example_02(self):
        example_path = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '02_validation'
        sys.path.insert(0, str(example_path))
        import validate
        assert validate.main is not None
        sys.path.pop(0)


class TestExampleReadmeContent:
    """Test examples README content."""

    def test_example_01_readme_has_prerequisites(self):
        readme_path = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '01_basic_generation' / 'README.md'
        content = readme_path.read_text(encoding='utf-8')
        assert "Prerequisites" in content

    def test_example_01_readme_has_output(self):
        readme_path = Path(__file__).parent.parent.parent / 'examples' / 'module_06' / '01_basic_generation' / 'README.md'
        content = readme_path.read_text(encoding='utf-8')
        assert "Expected Output" in content

# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
