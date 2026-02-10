#!/usr/bin/env python3
"""
Project Quality Check Script

Runs comprehensive quality checks on the modules and tests.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def main():
    """Run all quality checks."""
    # Move to project root if executed from scripts/
    project_root = Path(__file__).parent.parent.absolute()
    modules_path = project_root / "modules"
    
    if not modules_path.exists():
        print(f"Error: {modules_path} not found")
        sys.exit(1)
    
    # We use python -m variant for reliability
    checks = [
        (
            [sys.executable, "-m", "black", "--check", str(modules_path)],
            "Code formatting (Black)"
        ),
        (
            [sys.executable, "-m", "isort", "--check-only", str(modules_path)],
            "Import sorting (isort)"
        ),
        (
            [sys.executable, "-m", "flake8", str(modules_path), "--max-line-length=100"],
            "Linting (flake8)"
        ),
        (
            [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short", "-m", "not slow"],
            "Unit tests (Fast selection)"
        ),
    ]
    
    results = []
    
    # Add project root to PYTHONPATH for the checks
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "modules") + os.pathsep + env.get("PYTHONPATH", "")
    
    for cmd, description in checks:
        # Note: run_command above doesn't allow passing env, let's fix that or use a simple variant
        print(f"\n{'='*80}")
        print(f"Running: {description}")
        print(f"{'='*80}")
        
        try:
            res = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if res.returncode == 0:
                print(res.stdout)
                print(f"✓ {description} passed")
                results.append((description, True))
            else:
                print(res.stdout)
                print(res.stderr)
                print(f"✗ {description} failed")
                results.append((description, False))
        except Exception as e:
            print(f"✗ {description} failed with error: {e}")
            results.append((description, False))
    
    # Summary
    print(f"\n{'='*80}")
    print("Quality Check Summary")
    print(f"{'='*80}")
    
    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {description}")
    
    # Exit code
    if all(success for _, success in results):
        print("\n✓ All quality checks passed!")
        sys.exit(0)
    else:
        print("\n✗ Some quality checks failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
