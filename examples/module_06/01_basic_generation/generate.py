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
