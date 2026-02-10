"""
Example 02: Contract Validation

This example demonstrates validating a contract through multiple layers.
"""

import sys
from pathlib import Path

# Add modules to path if running from example directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'modules'))

from module_06_contract_schema import (
    load_contract,
    ContractValidator,
    ValidationContext
)


def main():
    """Validate a contract."""
    
    # Step 1: Load contract (from example 01)
    # We look for the file in the sibling directory
    contract_path = Path(__file__).parent.parent / "01_basic_generation" / "example_library.contract.json"
    
    if not contract_path.exists():
        print(f"Error: {contract_path} not found")
        print("Please run example 01 ('generate.py') first to create the contract file.")
        return
    
    print(f"Loading contract from {contract_path.name}...")
    try:
        contract = load_contract(contract_path)
    except Exception as e:
        print(f"Failed to load contract: {e}")
        return
        
    print(f"✓ Loaded contract with {len(contract.clauses)} clauses")
    
    # Step 2: Create validation context
    context = ValidationContext(
        strict_mode=True,
        treat_warnings_as_errors=False
    )
    
    # Step 3: Create validator
    validator = ContractValidator(context)
    
    # Step 4: Validate
    # Since we don't have the original IR artifact here, we perform 
    # schema validation. In real usage, you'd provide the IR for 
    # referential and constraint validation.
    print("\nPerforming validation (Schema Layer)...")
    result = validator.validate(
        contract,
        skip_referential=True,
        skip_constraint=True
    )
    
    # Step 5: Report results
    if result.passed:
        print("\n✓ Contract validation PASSED")
        
        # Breakdown of layers
        if result.schema_result:
            print(f"  - Schema Layer: {'PASS' if result.schema_result.passed else 'FAIL'}")
    else:
        print("\n✗ Contract validation FAILED")
        
        errors = result.get_all_errors()
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - [{error.layer.name}] {error.error_message}")
    
    # Step 6: Check for warnings
    warnings = result.get_all_warnings()
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning.warning_message}")


if __name__ == '__main__':
    main()
