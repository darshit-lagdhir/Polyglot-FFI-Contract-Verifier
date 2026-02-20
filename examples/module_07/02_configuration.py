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
# File Integrity Identifier: b950f29c838e9495
# ==============================================================================

"""
Example 02: Synthesis Configuration

This example demonstrates customizing synthesis behavior:
- Adjusting default assumptions
- Enabling/disabling generators
- Using different synthesis versions

Expected runtime: < 1 second
Difficulty: Intermediate
"""

import sys
from pathlib import Path

# Add project root and modules to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "modules"))

from module_07_contract_synthesis import (
    SynthesisEngine,
    SynthesisConfig
)
from module_05_ir_normalization.ir_serialization import IRSerializer


def example_basic_config():
    """Example: Basic configuration."""
    print("\n1. Basic Configuration")
    print("-" * 70)
    
    # Create custom configuration
    config = SynthesisConfig(
        synthesis_version='1.0.0',
        default_pointer_nonnull=True,  # Strict null checking
        strict_mode=True
    )
    
    print(f"Synthesis version: {config.synthesis_version}")
    print(f"Pointer nullability default: non-null")
    print(f"Strict mode: enabled")
    
    # Use with engine
    engine = SynthesisEngine(config)
    print("[OK] Engine configured")


def example_permissive_config():
    """Example: Permissive configuration."""
    print("\n2. Permissive Configuration")
    print("-" * 70)
    
    # More permissive settings
    config = SynthesisConfig(
        default_pointer_nonnull=False,  # Allow null by default
        default_ownership_severity='WARNING',  # Reduce severity
        strict_mode=False
    )
    
    print(f"Pointer nullability default: nullable")
    print(f"Ownership severity: WARNING (advisory)")
    print(f"Strict mode: disabled")
    
    engine = SynthesisEngine(config)
    print("[OK] Engine configured with permissive settings")


def example_selective_generators():
    """Example: Enabling/disabling generators."""
    print("\n3. Selective Generator Configuration")
    print("-" * 70)
    
    # Disable specific generators
    config = SynthesisConfig(
        enable_layout_generation=True,
        enable_nullability_generation=True,
        enable_ownership_generation=False  # Disabled
    )
    
    print("Enabled generators:")
    print("  [OK] Layout clauses")
    print("  [OK] Nullability clauses")
    print("  [FAIL] Ownership clauses (disabled)")
    
    engine = SynthesisEngine(config)
    print("[OK] Engine configured with selective generators")


def example_version_pinning():
    """Example: Version pinning for stability."""
    print("\n4. Version Pinning")
    print("-" * 70)
    
    # Pin to specific synthesis version
    STABLE_VERSION = '1.0.0'
    
    config = SynthesisConfig(synthesis_version=STABLE_VERSION)
    
    print(f"Synthesis version pinned to: {STABLE_VERSION}")
    print("Benefits:")
    print("  - Reproducible results")
    print("  - Stable across updates")
    print("  - CI/CD friendly")
    
    engine = SynthesisEngine(config)
    print("[OK] Version pinned for stability")


def main():
    """Run configuration examples."""
    print("=" * 70)
    print("Example 02: Synthesis Configuration")
    print("=" * 70)
    
    example_basic_config()
    example_permissive_config()
    example_selective_generators()
    example_version_pinning()
    
    print("\n" + "=" * 70)
    print("Configuration examples complete!")
    
    return 0


if __name__ == '__main__':
    exit(main())