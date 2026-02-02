#!/usr/bin/env python3
"""Validate end-to-end integration."""

import subprocess
import sys
import os

def main():
    print("Testing End-to-End Integration...")
    
    # Run integration test
    print("\n[1/3] Running integration test...")
    # Using python executable to run the test script
    result = subprocess.run([sys.executable, "tests/integration/test_end_to_end.py"])
    if result.returncode != 0:
        print("✗ Integration test failed")
        return False
    print("✓ Integration test passed")

    # Run demo
    print("\n[2/3] Running demo...")
    result = subprocess.run([sys.executable, "examples/demo/run_demo.py"])
    if result.returncode != 0:
        print("✗ Demo failed")
        return False
    print("✓ Demo passed")

    # Run regression tests
    print("\n[3/3] Running regression tests...")
    result = subprocess.run([sys.executable, "tests/regression/test_system_stability.py"])
    if result.returncode != 0:
        print("✗ Regression tests failed")
        return False
    print("✓ Regression tests passed")

    print("\n✓ ALL TESTS PASSED (3/3)")
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
