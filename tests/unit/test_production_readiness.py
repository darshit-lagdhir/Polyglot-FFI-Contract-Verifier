"""
Unit tests for Module 06: Production Readiness (Prompt 15/15)
Testing Level: FINAL (20 tests)
"""

import pytest
from pathlib import Path
import sys
import importlib
import inspect

# Add modules to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "modules"))


class TestPackageStructure:
    """Test package structure for distribution."""

    def test_pyproject_toml_exists(self):
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"

    def test_manifest_exists(self):
        # Check in the module directory as specified in prompt
        manifest_path = PROJECT_ROOT / "modules" / "module_06_contract_schema" / "MANIFEST.in"
        assert manifest_path.exists(), "MANIFEST.in not found"

    def test_changelog_exists(self):
        changelog_path = PROJECT_ROOT / "CHANGELOG.md"
        assert changelog_path.exists(), "CHANGELOG.md not found"

    def test_contributing_exists(self):
        contributing_path = PROJECT_ROOT / "CONTRIBUTING.md"
        assert contributing_path.exists(), "CONTRIBUTING.md not found"


class TestVersionConsistency:
    """Test version consistency across files."""

    def test_version_in_module(self):
        import module_06_contract_schema

        assert hasattr(module_06_contract_schema, "__version__")
        # Assuming v1.0.0 based on changelog
        assert module_06_contract_schema.__version__ == "1.0.0"

    def test_version_info_tuple(self):
        import module_06_contract_schema

        assert hasattr(module_06_contract_schema, "__version_info__")
        assert module_06_contract_schema.__version_info__ == (1, 0, 0)


class TestImportability:
    """Test that package can be imported."""

    def test_main_module_imports(self):
        import module_06_contract_schema

        assert module_06_contract_schema is not None

    def test_all_exports_importable(self):
        from module_06_contract_schema import (
            ContractGenerator,
            ContractValidator,
            ContractSerializer,
            EnforcementEngine,
        )

        assert ContractGenerator is not None
        assert ContractValidator is not None
        assert ContractSerializer is not None
        assert EnforcementEngine is not None


class TestCLIEntryPoint:
    """Test CLI entry point."""

    def test_cli_main_function_exists(self):
        from module_06_contract_schema.contract_cli import main

        assert callable(main)

    def test_cli_command_group_exists(self):
        from module_06_contract_schema.contract_cli import cli

        assert cli is not None


class TestDocumentation:
    """Test documentation completeness."""

    def test_readme_exists(self):
        readme_path = PROJECT_ROOT / "modules" / "module_06_contract_schema" / "README.md"
        assert readme_path.exists()

    def test_examples_directory_exists(self):
        examples_dir = PROJECT_ROOT / "examples" / "module_06"
        assert examples_dir.exists()

    def test_changelog_has_version(self):
        changelog_path = PROJECT_ROOT / "CHANGELOG.md"
        content = changelog_path.read_text(encoding="utf-8")
        assert "1.0.0" in content


class TestNoDebugCode:
    """Test that no debug code remains."""

    def test_no_print_statements_in_core(self):
        from module_06_contract_schema import contract_entities

        source = Path(contract_entities.__file__).read_text(encoding="utf-8")

        # Should not have debug prints (excluding comments)
        lines = [line for line in source.split("\n") if "print(" in line]
        lines = [line for line in lines if not line.strip().startswith("#")]

        # In core entities, we expect 0 prints.
        assert len(lines) == 0, f"Found accidental prints: {lines}"


class TestTypeHints:
    """Test type hint coverage."""

    def test_contract_generator_has_type_hints(self):
        from module_06_contract_schema import ContractGenerator

        sig = inspect.signature(ContractGenerator.generate)

        # Check that method has annotations
        assert sig.return_annotation is not inspect.Signature.empty


class TestErrorHandling:
    """Test error handling is present."""

    def test_file_not_found_handled(self):
        from module_06_contract_schema.contract_serialization import ContractDeserializer

        deserializer = ContractDeserializer()

        # Try to load non-existent file path string if any method supports it,
        # but deserialize takes string. Let's check a file loading method.
        from module_06_contract_schema import load_contract

        with pytest.raises(Exception):
            load_contract(Path("nonexistent.json"))


class TestSecurityBasics:
    """Test basic security measures."""

    def test_no_eval_in_core_modules(self):
        from module_06_contract_schema import contract_entities

        source = Path(contract_entities.__file__).read_text(encoding="utf-8")
        assert "eval(" not in source, "eval() found in code"

    def test_no_exec_in_core_modules(self):
        from module_06_contract_schema import contract_entities

        source = Path(contract_entities.__file__).read_text(encoding="utf-8")
        assert "exec(" not in source, "exec() found in code"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
