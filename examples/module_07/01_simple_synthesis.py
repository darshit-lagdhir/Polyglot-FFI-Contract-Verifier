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
# File Integrity Identifier: 7626f13a559e996b
# ==============================================================================

"""
Example 01: Simple Contract Synthesis

This example demonstrates the most basic synthesis workflow:
1. Load IR from file
2. Synthesize contract
3. Examine results

Expected runtime: < 1 second
Difficulty: Beginner
"""

import os
import sys
from pathlib import Path

# Add project root and modules to path so we can import modules
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "modules"))

from module_07_contract_synthesis import synthesize_from_ir


def main():
    """Run simple synthesis example."""
    print("=" * 70)
    print("Example 01: Simple Contract Synthesis")
    print("=" * 70)
    
    # Path to sample IR file
    ir_file = Path(__file__).parent / "data" / "simple_interface.json"
    
    if not ir_file.exists():
        print(f"Error: Sample file not found: {ir_file}")
        print("Please ensure example data is available")
        return 1
    
    print(f"\nStep 1: Loading IR from {ir_file.name}")
    print("-" * 70)
    
    # Synthesize contract
    print("\nStep 2: Synthesizing contract...")
    try:
        contract = synthesize_from_ir(str(ir_file))
        print("[OK] Synthesis complete!")
    except Exception as e:
        print(f"[FAIL] Synthesis failed: {e}")
        return 1
    
    # Examine results
    print(f"\nStep 3: Examining results")
    print("-" * 70)
    
    print(f"Interface ID: {contract.header.target_interface_id}")
    print(f"Contract version: {contract.header.contract_version}")
    print(f"Total clauses generated: {len(contract.clauses)}")
    
    # Breakdown by clause type
    clause_types = {}
    for clause in contract.clauses:
        clause_type = clause.clause_type.value
        clause_types[clause_type] = clause_types.get(clause_type, 0) + 1
    
    print("\nClause breakdown:")
    for clause_type, count in sorted(clause_types.items()):
        print(f"  {clause_type:25s}: {count:3d}")
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("\nNext steps:")
    print("  - Run 02_configuration.py to learn about customization")
    
    return 0


if __name__ == '__main__':
    exit(main())