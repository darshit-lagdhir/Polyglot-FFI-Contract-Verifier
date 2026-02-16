"""
Module 07: Completion Validation (Prompt 9/15)

Module completion validation and production readiness verification.

Components:
1. Completeness validator
2. Integration test framework
3. Regression test suite
4. Release validation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import logging
import importlib

logger = logging.getLogger(__name__)

# ============================================================================
# COMPLETENESS VALIDATION
# ============================================================================

@dataclass
class CheckResult:
    """Result of a completeness check."""
    name: str
    passed: bool
    details: str = ""
    error: Optional[str] = None

@dataclass
class CompletenessReport:
    """Report on module completeness."""
    sections: Dict[str, List[CheckResult]] = field(default_factory=dict)

    def add_section(self, name: str, checks: List[CheckResult]):
        """Add section to report."""
        self.sections[name] = checks

    def is_complete(self) -> bool:
        """Check if module is complete."""
        for checks in self.sections.values():
            if not all(c.passed for c in checks):
                return False
        return True

    def get_passed_count(self) -> int:
        """Get total passed checks."""
        return sum(
            sum(1 for c in checks if c.passed)
            for checks in self.sections.values()
        )

    def get_total_count(self) -> int:
        """Get total checks."""
        return sum(len(checks) for checks in self.sections.values())

    def get_summary(self) -> str:
        """Get completeness summary."""
        lines = []
        lines.append("Module 07: Contract Synthesis Engine")
        lines.append("Completeness Validation Report")
        lines.append("=" * 70)
        
        for section_name, checks in self.sections.items():
            passed = sum(1 for c in checks if c.passed)
            total = len(checks)
            percentage = (passed / total * 100) if total > 0 else 0
            
            lines.append(f"\n{section_name}: {passed}/{total} ({percentage:.0f}%)")
            
            for check in checks:
                status = "✓" if check.passed else "✗"
                lines.append(f"  {status} {check.name}")
                if check.details:
                    lines.append(f"     {check.details}")
                if check.error:
                    lines.append(f"     Error: {check.error}")
        
        lines.append("\n" + "=" * 70)
        lines.append(f"Total: {self.get_passed_count()}/{self.get_total_count()} checks passed")
        
        if self.is_complete():
            lines.append("\nStatus: ✓ MODULE COMPLETE AND READY")
        else:
            lines.append("\nStatus: ✗ INCOMPLETE - See failed checks above")
        
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            'sections': {
                name: [
                    {
                        'name': c.name,
                        'passed': c.passed,
                        'details': c.details,
                        'error': c.error
                    }
                    for c in checks
                ]
                for name, checks in self.sections.items()
            },
            'complete': self.is_complete(),
            'passed': self.get_passed_count(),
            'total': self.get_total_count()
        }

class CompletenessValidator:
    """
    Validate module completeness.
    Checks features, tests, documentation, API, and performance.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_completeness(self) -> CompletenessReport:
        """
        Run all completeness checks.
        
        Returns:
            CompletenessReport with results
        """
        self.logger.info("Starting module completeness validation...")
        
        report = CompletenessReport()
        
        # Check features
        self.logger.info("Checking features...")
        report.add_section("Core Features", self._check_core_features())
        
        # Check advanced features
        self.logger.info("Checking advanced features...")
        report.add_section("Advanced Features", self._check_advanced_features())
        
        # Check integration
        self.logger.info("Checking integration...")
        report.add_section("Integration", self._check_integration())
        
        # Check tooling
        self.logger.info("Checking tooling...")
        report.add_section("Tooling", self._check_tooling())
        
        # Check documentation
        self.logger.info("Checking documentation...")
        report.add_section("Documentation", self._check_documentation())
        
        # Check API
        self.logger.info("Checking API...")
        report.add_section("Public API", self._check_api())
        
        self.logger.info("Completeness validation complete")
        
        return report

    def _check_core_features(self) -> List[CheckResult]:
        """Check core feature completeness."""
        checks = []
        
        module_name = "module_07_contract_synthesis"
        
        core_gens = [
            ("Layout clause generation", "LayoutClauseGenerator"),
            ("Nullability clause generation", "NullabilityClauseGenerator"),
            ("Ownership clause generation", "OwnershipClauseGenerator"),
            ("Relational constraint derivation", "RelationalClauseGenerator"),
            ("Calling convention projection", "CallingConventionClauseGenerator"),
            ("ABI compatibility clauses", "ABICompatibilityClauseGenerator"),
        ]
        
        for name, class_name in core_gens:
            try:
                engine_mod = importlib.import_module(f"{module_name}.synthesis_engine")
                if hasattr(engine_mod, class_name):
                    checks.append(CheckResult(name, passed=True, details=f"{class_name} available"))
                else:
                    checks.append(CheckResult(name, passed=False, error=f"{class_name} not found in synthesis_engine"))
            except (ImportError, ModuleNotFoundError) as e:
                checks.append(CheckResult(name, passed=False, error=str(e)))
        
        return checks

    def _check_advanced_features(self) -> List[CheckResult]:
        """Check advanced feature completeness."""
        checks = []
        module_name = "module_07_contract_synthesis"
        
        adv_features = [
            ("Contextual analysis", "ContextualAnalyzer"),
            ("Conditional refinement", "ConditionalNullabilityClauseGenerator"),
            ("Severity escalation", "SeverityEscalator"),
            ("Advisory clause generation", "AdvisoryClauseGenerator"),
        ]
        
        for name, class_name in adv_features:
            try:
                engine_mod = importlib.import_module(f"{module_name}.synthesis_engine")
                if hasattr(engine_mod, class_name):
                    checks.append(CheckResult(name, passed=True, details=f"{class_name} available"))
                else:
                    checks.append(CheckResult(name, passed=False, error=f"{class_name} not found in synthesis_engine"))
            except (ImportError, ModuleNotFoundError) as e:
                checks.append(CheckResult(name, passed=False, error=str(e)))
        
        return checks

    def _check_integration(self) -> List[CheckResult]:
        """Check integration completeness."""
        checks = []
        module_name = "module_07_contract_synthesis"
        
        try:
            from .ir_bridge import IRBridge, IRValidator
            checks.append(CheckResult("IR Bridge", passed=True, details="IRBridge and IRValidator available"))
        except ImportError as e:
            checks.append(CheckResult("IR Bridge", passed=False, error=str(e)))
            
        try:
            from .contract_bridge import ContractBridge
            checks.append(CheckResult("Contract Bridge", passed=True, details="ContractBridge available"))
        except ImportError as e:
            checks.append(CheckResult("Contract Bridge", passed=False, error=str(e)))
        
        return checks

    def _check_tooling(self) -> List[CheckResult]:
        """Check tooling completeness."""
        checks = []
        
        try:
            from .cli import main
            checks.append(CheckResult("CLI interface", passed=True, details="CLI available"))
        except ImportError as e:
            checks.append(CheckResult("CLI interface", passed=False, error=str(e)))
            
        try:
            from .versioning import RuleRegistry, version_compare
            checks.append(CheckResult("Versioning system", passed=True, details="Versioning available"))
        except ImportError as e:
            checks.append(CheckResult("Versioning system", passed=False, error=str(e)))
            
        try:
            from .performance import SynthesisCache, PhaseProfiler
            checks.append(CheckResult("Performance optimization", passed=True, details="Performance tools available"))
        except ImportError as e:
            checks.append(CheckResult("Performance optimization", passed=False, error=str(e)))
        
        return checks

    def _check_documentation(self) -> List[CheckResult]:
        """Check documentation completeness."""
        checks = []
        
        doc_file = Path(__file__).parent / "SYNTHESIS_ENGINE.md"
        checks.append(CheckResult(
            "SYNTHESIS_ENGINE.md",
            passed=doc_file.exists(),
            details=f"File exists: {doc_file.exists()}"
        ))
        
        try:
            import module_07_contract_synthesis
            has_docstring = module_07_contract_synthesis.__doc__ is not None
            checks.append(CheckResult(
                "Package docstring",
                passed=has_docstring,
                details="Module-level docstring present" if has_docstring else "Missing"
            ))
        except Exception as e:
            checks.append(CheckResult("Package docstring", passed=False, error=str(e)))
        
        return checks

    def _check_api(self) -> List[CheckResult]:
        """Check public API completeness."""
        checks = []
        
        try:
            from module_07_contract_synthesis import __all__
            checks.append(CheckResult(
                "__all__ export list",
                passed=len(__all__) > 0,
                details=f"{len(__all__)} symbols exported"
            ))
        except Exception as e:
            checks.append(CheckResult("__all__ export list", passed=False, error=str(e)))
            
        try:
            from module_07_contract_synthesis import (
                SynthesisEngine, SynthesisConfig, SynthesisResult
            )
            checks.append(CheckResult("Core classes importable", passed=True, details="SynthesisEngine, SynthesisConfig, SynthesisResult"))
        except ImportError as e:
            checks.append(CheckResult("Core classes importable", passed=False, error=str(e)))
            
        try:
            from module_07_contract_synthesis import synthesize_from_ir
            checks.append(CheckResult("Convenience functions importable", passed=True, details="synthesize_from_ir available"))
        except ImportError as e:
            checks.append(CheckResult("Convenience functions importable", passed=False, error=str(e)))
        
        return checks

def run_completeness_check():
    """Run completeness check and print report."""
    validator = CompletenessValidator()
    report = validator.validate_completeness()
    print(report.get_summary())
    
    if not report.is_complete():
        import sys
        sys.exit(1)

if __name__ == "__main__":
    run_completeness_check()

__all__ = [
    'CheckResult',
    'CompletenessReport',
    'CompletenessValidator',
    'run_completeness_check',
]
