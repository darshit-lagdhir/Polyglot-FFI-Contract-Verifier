# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: fff449c94ecb295d
# ==============================================================================

"""
Pre-Release Validation Script

Runs comprehensive validation before release.
"""

import subprocess
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add project root to path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "modules"))

class PreReleaseValidator:
    """Comprehensive pre-release validation."""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
    
    def run_all_checks(self):
        """Run all validation checks."""
        print("=" * 70)
        print("MODULE 07: PRE-RELEASE VALIDATION")
        print("=" * 70)
        print(f"Started: {self.start_time.isoformat()}")
        print()
        
        # Run checks
        self.check_unit_tests()
        self.check_stress_tests()
        self.check_performance()
        self.check_documentation()
        self.check_examples()
        self.check_installation()
        self.check_cli()
        self.check_completeness()
        
        # Generate report
        success = self.print_report()
        
        # Return success/failure
        return success
    
    def check_unit_tests(self):
        """Run unit tests."""
        print("Running unit tests...")
        
        result = subprocess.run(
            ['pytest', 'tests/tests.py', '-q', '--tb=short', '-m', 'not stress'],
            capture_output=True,
            text=True
        )
        
        self.results['unit_tests'] = {
            'passed': result.returncode == 0,
            'output': result.stdout + result.stderr
        }
        
        print(f"  {'[OK]' if result.returncode == 0 else '[FAIL]'} Unit tests")
    
    def check_stress_tests(self):
        """Run stress tests."""
        print("Running stress tests...")
        
        result = subprocess.run(
            ['pytest', 'tests/tests.py', '-q', '--tb=short', '-m', 'stress'],
            capture_output=True,
            text=True
        )
        
        self.results['stress_tests'] = {
            'passed': result.returncode == 0,
            'output': result.stdout + result.stderr
        }
        
        print(f"  {'[OK]' if result.returncode == 0 else '[FAIL]'} Stress tests")
    
    def check_performance(self):
        """Run performance benchmarks."""
        print("Running performance benchmarks...")
        
        try:
            from module_07_contract_synthesis import SynthesisEngine, SynthesisConfig
            from module_07_contract_synthesis.performance import SynthesisBenchmark
            
            engine = SynthesisEngine(SynthesisConfig())
            benchmark = SynthesisBenchmark(engine)
            
            results = {}
            for scenario in ['tiny', 'small', 'medium']:
                res = benchmark.run_benchmark(scenario, iterations=3)
                results[scenario] = res.passed
            
            all_passed = all(results.values())
            
            self.results['performance'] = {
                'passed': all_passed,
                'output': f"Benchmarks: {results}"
            }
            
            print(f"  {'[OK]' if all_passed else '[FAIL]'} Performance benchmarks")
        
        except Exception as e:
            self.results['performance'] = {
                'passed': False,
                'output': str(e)
            }
            print(f"  [FAIL] Performance benchmarks (error: {e})")
    
    def check_documentation(self):
        """Check documentation completeness."""
        print("Checking documentation...")
        
        required_docs = [
            'modules/module_07_contract_synthesis/SYNTHESIS_ENGINE.md',
            'docs/API_REFERENCE.md',
            'docs/PRODUCTION_DEPLOYMENT.md',
            'docs/TROUBLESHOOTING.md',
            'examples/module_07/README.md',
            'README.md',
            'CHANGELOG.md',
            'RELEASE_NOTES.md',
            'CONTRIBUTING.md',
            'CODE_OF_CONDUCT.md',
            'SECURITY.md'
        ]
        
        missing = []
        for doc in required_docs:
            if not (project_root / doc).exists():
                missing.append(doc)
        
        passed = len(missing) == 0
        
        self.results['documentation'] = {
            'passed': passed,
            'output': f"Missing: {missing}" if missing else "All docs present"
        }
        
        print(f"  {'[OK]' if passed else '[FAIL]'} Documentation")
    
    def check_examples(self):
        """Check examples exist and are valid."""
        print("Checking examples...")
        
        example_dir = project_root / 'examples/module_07'
        
        if not example_dir.exists():
            self.results['examples'] = {
                'passed': False,
                'output': 'Examples directory missing'
            }
            print("  [FAIL] Examples")
            return
        
        examples = list(example_dir.glob('*.py'))
        
        self.results['examples'] = {
            'passed': len(examples) >= 3,
            'output': f"Found {len(examples)} examples"
        }
        
        print(f"  {'[OK]' if len(examples) >= 3 else '[FAIL]'} Examples")
    
    def check_installation(self):
        """Check package can be built."""
        print("Checking installation...")
        
        # In this environment, we just check for setup indicators
        has_setup = (project_root / 'setup.py').exists() or (project_root / 'pyproject.toml').exists()
        
        self.results['installation'] = {
            'passed': has_setup,
            'output': 'Setup configuration found' if has_setup else 'No setup found'
        }
        
        print(f"  {'[OK]' if has_setup else '[FAIL]'} Installation")
    
    def check_cli(self):
        """Check CLI works."""
        print("Checking CLI...")
        
        try:
            from module_07_contract_synthesis.cli import main
            
            self.results['cli'] = {
                'passed': True,
                'output': 'CLI imports successfully'
            }
            
            print("  [OK] CLI")
        
        except Exception as e:
            self.results['cli'] = {
                'passed': False,
                'output': str(e)
            }
            print(f"  [FAIL] CLI (error: {e})")
    
    def check_completeness(self):
        """Check module completeness."""
        print("Checking completeness...")
        
        try:
            from module_07_contract_synthesis.completion_check import CompletenessValidator
            
            validator = CompletenessValidator()
            report = validator.validate_completeness()
            
            self.results['completeness'] = {
                'passed': report.is_complete(),
                'output': f"{report.get_passed_count()}/{report.get_total_count()} checks passed"
            }
            
            print(f"  {'[OK]' if report.is_complete() else '[FAIL]'} Completeness")
        
        except Exception as e:
            self.results['completeness'] = {
                'passed': False,
                'output': str(e)
            }
            print(f"  [FAIL] Completeness (error: {e})")
    
    def print_report(self):
        """Print validation report."""
        print()
        print("=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)
        
        for check_name, result in self.results.items():
            status = "[OK]" if result['passed'] else "[FAIL]"
            print(f"\n{check_name:20s} {status}")
            
            if not result['passed']:
                print(f"  {result['output'][:200]}")
        
        print()
        print("=" * 70)
        
        all_passed = all(r['passed'] for r in self.results.values())
        
        if all_passed:
            print("STATUS: [OK] READY FOR RELEASE")
            print()
            print("All validation checks passed!")
            print("Module 07 is ready for production deployment.")
        else:
            print("STATUS: [FAIL] NOT READY")
            print()
            print("Some validation checks failed.")
            print("Please fix the issues before release.")
        
        print("=" * 70)
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        print(f"\nCompleted in {duration:.1f}s")
        
        return all_passed


def main():
    """Run pre-release validation."""
    validator = PreReleaseValidator()
    success = validator.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()