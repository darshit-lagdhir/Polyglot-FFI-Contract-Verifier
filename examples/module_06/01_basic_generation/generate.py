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
# File Integrity Identifier: d6e5e674e05a214f
# ==============================================================================

"""
Example 01: Basic Contract Generation

This example demonstrates how to generate a contract from an IR artifact.
"""

from module_06_contract_schema import ContractGenerator, GenerationConfig, save_contract
import sys
from pathlib import Path
from collections import Counter

# Add modules to path if running from example directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "modules"))


def main():
    """Generate a basic contract from IR."""

    # Step 1: Configure generation
    config = GenerationConfig(
        confidence_threshold=0.6,
        include_low_confidence=True,
        generate_ownership=True,
        generate_layout=True,
    )

    # Step 2: Create generator
    generator = ContractGenerator(config)

    print("Generating contract from IR artifact...")

    # Step 3: Generate contract
    # In real usage, ir_artifact would be loaded from Module 05 output
    # Here we use None to trigger the mock-based generation for demonstration
    contract = generator.generate(ir_artifact=None, target_interface_id="example_library")

    print(f"✓ Generated {len(contract.clauses)} clauses")

    # Step 4: Show statistics
    clause_types = Counter(c.clause_type.value for c in contract.clauses)

    print("\nClause Breakdown:")
    for clause_type, count in clause_types.most_common():
        print(f"  {clause_type}: {count}")

    # Step 5: Save contract
    output_path = Path("example_library.contract.json")
    save_contract(contract, output_path)

    print(f"\n✓ Contract saved to {output_path}")
    print(f"✓ Contract version: {contract.header.contract_version}")


if __name__ == "__main__":
    main()