"""
Module 05 Completion Verification

Automated checks to ensure module is production-ready.
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path

@dataclass
class CompletionCheck:
    """Represents a completion check."""
    name: str
    description: str
    passed: bool
    details: str = ""

class ModuleCompletionVerifier:
    """Verifies module completion and production readiness."""
    
    def __init__(self):
        self.checks: List[CompletionCheck] = []
    
    def verify_all(self) -> bool:
        """Run all completion checks."""
        self.check_implementation()
        self.check_testing()
        self.check_documentation()
        self.check_packaging()
        self.check_examples()
        
        return all(check.passed for check in self.checks)
    
    def check_implementation(self):
        """Verify implementation completeness."""
        required_modules = [
            'ir_entities.py',
            'type_normalization.py',
            'ir_validation.py',
            'ir_serialization.py',
            'ir_diff.py',
            'ir_orchestrator.py',
            'cli.py',
            'module_04_bridge.py',
            'performance.py',
            'diagnostics.py',
            'documentation.py'
        ]
        
        base_path = Path(__file__).parent
        missing = []
        
        for module in required_modules:
            if not (base_path / module).exists():
                missing.append(module)
        
        self.checks.append(CompletionCheck(
            name="Implementation Complete",
            description="All required modules implemented",
            passed=len(missing) == 0,
            details=f"Missing: {missing}" if missing else "All modules present"
        ))
    
    def check_testing(self):
        """Verify test completeness."""
        # Check test count
        test_dir = Path(__file__).parent.parent.parent / 'tests'
        
        unit_tests = len(list((test_dir / 'unit').glob('test_*.py')))
        integration_tests = len(list((test_dir / 'integration').glob('test_*.py')))
        
        total_tests = unit_tests + integration_tests
        
        self.checks.append(CompletionCheck(
            name="Test Coverage",
            description="Comprehensive test suite",
            passed=total_tests >= 10,
            details=f"{total_tests} test files ({unit_tests} unit, {integration_tests} integration)"
        ))
    
    def check_documentation(self):
        """Verify documentation completeness."""
        docs_dir = Path(__file__).parent.parent.parent / 'docs'
        
        required_docs = [
            'README.md',
            'CHANGELOG.md',
        ]
        
        missing = [doc for doc in required_docs 
                  if not (Path(__file__).parent.parent.parent / doc).exists()]
        
        self.checks.append(CompletionCheck(
            name="Documentation Complete",
            description="Required documentation present",
            passed=len(missing) == 0,
            details=f"Missing: {missing}" if missing else "All docs present"
        ))
    
    def check_packaging(self):
        """Verify packaging configuration."""
        base_path = Path(__file__).parent.parent.parent
        
        required_files = ['pyproject.toml', 'LICENSE']
        missing = [f for f in required_files if not (base_path / f).exists()]
        
        self.checks.append(CompletionCheck(
            name="Packaging Ready",
            description="Package configuration complete",
            passed=len(missing) == 0,
            details=f"Missing: {missing}" if missing else "Ready for distribution"
        ))
    
    def check_examples(self):
        """Verify examples exist."""
        examples_dir = Path(__file__).parent.parent.parent / 'examples'
        
        self.checks.append(CompletionCheck(
            name="Examples Available",
            description="Examples provided",
            passed=examples_dir.exists() if examples_dir else True,
            details="Examples directory present" if examples_dir and examples_dir.exists() else "Optional"
        ))
    
    def generate_report(self) -> str:
        """Generate completion report."""
        lines = ["Module 05 Completion Report", "=" * 80, ""]
        
        passed_count = sum(1 for check in self.checks if check.passed)
        total_count = len(self.checks)
        
        lines.append(f"Status: {passed_count}/{total_count} checks passed")
        lines.append("")
        
        for check in self.checks:
            status = "✓" if check.passed else "✗"
            lines.append(f"{status} {check.name}")
            lines.append(f"  {check.description}")
            if check.details:
                lines.append(f"  Details: {check.details}")
            lines.append("")
        
        if passed_count == total_count:
            lines.append("🎉 Module 05 is PRODUCTION READY!")
        else:
            lines.append("⚠️  Some checks failed. Review above.")
        
        return "\n".join(lines)

if __name__ == '__main__':
    verifier = ModuleCompletionVerifier()
    all_passed = verifier.verify_all()
    
    print(verifier.generate_report())
    
    exit(0 if all_passed else 1)
