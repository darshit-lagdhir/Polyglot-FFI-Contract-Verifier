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
# File Integrity Identifier: 8b1153b57352f26d
# ==============================================================================

"""
Simple calculator verification example.

This demonstrates basic FFI verification workflow.
"""

from verification_pipeline import verify
import sys
import os

# Add parent directories to path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "modules", "module_02_verification_pipeline"
    ),
)


def main():
    print("=" * 60)
    print("SIMPLE CALCULATOR VERIFICATION EXAMPLE")
    print("=" * 60)
    print()

    # Determine library name based on platform
    if sys.platform == "win32":
        library = "calculator.dll"
    elif sys.platform == "darwin":
        library = "libcalculator.dylib"
    else:
        library = "libcalculator.so"

    # Check if library exists
    if not os.path.exists(library):
        print(f"Error: Library '{library}' not found.")
        print("Please build the library first:")
        if sys.platform == "win32":
            print("  build.bat")
        else:
            print("  ./build.sh")
        return 1

    # Run verification
    print(f"Verifying: calculator.h + {library}")
    print()

    result = verify(
        header_path="calculator.h",
        library_path=library,
        output_dir="verification_results",
        verbose=True,
    )

    # Print results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(result)

    if result.success:
        print()
        print("✓ All tests passed!")
        print(f"  Report: {result.report_path}")
        return 0
    else:
        print()
        print("✗ Some tests failed")
        print(f"  Critical issues: {len(result.critical_issues)}")
        print(f"  Report: {result.report_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())