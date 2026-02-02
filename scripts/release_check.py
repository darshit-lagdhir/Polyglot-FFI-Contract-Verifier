#!/usr/bin/env python3
"""
Release checklist validation script.

Verifies all requirements for release are met.
"""

import sys
import os
from pathlib import Path
import subprocess

class ReleaseChecker:
    """Validates release readiness."""
    
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
    
    def check(self, name: str, func):
        """Run a check."""
        print(f"Checking: {name}...", end=" ")
        try:
            func()
            print("✓")
            self.passed += 1
            return True
        except AssertionError as e:
            print(f"✗ {e}")
            self.failed += 1
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            self.failed += 1
            return False
    
    def check_documentation_exists(self):
        """Check: Documentation files exist."""
        required_docs = [
            "docs/getting_started.md",
            "docs/api_reference.md",
            "docs/troubleshooting.md",
            "docs/best_practices.md",
            "docs/tutorials/01_basic_verification.md"
        ]
        
        missing = []
        for doc in required_docs:
            if not Path(doc).exists():
                missing.append(doc)
        
        assert len(missing) == 0, f"Missing docs: {', '.join(missing)}"
    
    def check_examples_exist(self):
        """Check: Examples are present."""
        example_dir = Path("examples/simple_calculator")
        assert example_dir.exists(), "Missing examples directory"
        
        required_files = [
            "calculator.h",
            "calculator.c",
            "verify.py",
            "build.bat",
            "build.sh",
            "README.md"
        ]
        
        missing = []
        for file in required_files:
            if not (example_dir / file).exists():
                missing.append(file)
        
        assert len(missing) == 0, f"Missing example files: {', '.join(missing)}"
    
    def check_tests_exist(self):
        """Check: Test files exist."""
        test_dirs = [
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "tests/system",
            "tests/benchmarks",
            "tests/stress",
            "tests/compatibility"
        ]
        
        missing = []
        for test_dir in test_dirs:
            if not Path(test_dir).exists():
                missing.append(test_dir)
        
        assert len(missing) == 0, f"Missing test directories: {', '.join(missing)}"
    
    def check_module_files_exist(self):
        """Check: Module files exist."""
        module_dir = Path("modules/module_02_verification_pipeline")
        assert module_dir.exists(), "Missing module directory"
        
        required_files = [
            "verification_pipeline.py",
            "VERIFICATION_PIPELINE.md",
            "README.md"
        ]
        
        missing = []
        for file in required_files:
            if not (module_dir / file).exists():
                missing.append(file)
        
        assert len(missing) == 0, f"Missing module files: {', '.join(missing)}"
    
    def check_ci_config_exists(self):
        """Check: CI/CD configuration exists."""
        ci_file = Path(".github/workflows/test.yml")
        assert ci_file.exists(), "Missing CI/CD configuration"
    
    def check_readme_updated(self):
        """Check: README files are updated."""
        readme_files = [
            "README.md",
            "modules/README.md",
            "modules/module_02_verification_pipeline/README.md"
        ]
        
        for readme in readme_files:
            path = Path(readme)
            if path.exists():
                content = path.read_text()
                assert len(content) > 100, f"{readme} seems incomplete"
    
    def run_all_checks(self):
        """Run all release checks."""
        print("=" * 60)
        print("RELEASE READINESS CHECK")
        print("=" * 60)
        print()
        
        self.check("Documentation exists", self.check_documentation_exists)
        self.check("Examples exist", self.check_examples_exist)
        self.check("Tests exist", self.check_tests_exist)
        self.check("Module files exist", self.check_module_files_exist)
        self.check("CI/CD config exists", self.check_ci_config_exists)
        self.check("README files updated", self.check_readme_updated)
        
        print()
        print("=" * 60)
        print(f"RESULTS: {self.passed} passed, {self.failed} failed")
        print("=" * 60)
        
        if self.failed == 0:
            print("✓ READY FOR RELEASE")
            return 0
        else:
            print("✗ NOT READY FOR RELEASE")
            return 1

if __name__ == "__main__":
    checker = ReleaseChecker()
    sys.exit(checker.run_all_checks())
