<!-- ============================================================================== -->
<!-- Polyglot FFI Contract Verifier -->
<!-- Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved. -->
<!--  -->
<!-- This file is part of the Polyglot FFI Contract Verifier ecosystem. -->
<!-- It is licensed under the Antigravity Source-Available and Technical  -->
<!-- Protection License (ASTPL). -->
<!--  -->
<!-- PROHIBITED USES: Commercial Use, Network Access Provision, and Machine  -->
<!-- Training Use are strictly prohibited absent explicit written authorization. -->
<!--  -->
<!-- Removal or alteration of this header may constitute a violation of the  -->
<!-- repository's governing agreements. -->
<!--  -->
<!-- File Integrity Identifier: 65159911a6c6ae82 -->
<!-- ============================================================================== -->

# Example 02: Contract Validation

## Overview

This example demonstrates how to validate a contract through multiple layers:
1. **Schema Layer**: Verifies that the JSON structure matches the expected schema.
2. **Referential Layer**: Verifies that all entity IDs mentioned in the contract exist in the target interface.
3. **Constraint Layer**: Verifies that constraints are logically consistent (e.g., no conflicting size requirements).

## Prerequisites

- Module 06 installed.
- **Example 01 output**: This example expects `example_library.contract.json` to exist in the `01_basic_generation` folder.

## Running the Example

```bash
python validate.py
```

## Expected Output

```text
Loading contract from example_library.contract.json...
✓ Loaded contract with 15 clauses

Performing validation (Schema Layer)...

✓ Contract validation PASSED
  - Schema Layer: PASS
```

## What's Happening

1.  **Loading**: We use the `load_contract` utility which automatically handles JSON parsing and basic integrity checks.
2.  **Context**: A `ValidationContext` is created to control validator behavior (strict mode, warning handling).
3.  **Validation**: In this example, we perform a partial validation (Schema Layer) because performing Referential or Constraint validation requires an IR artifact from Module 05.
4.  **Reporting**: We inspect the `ValidationResult` object to report specific failures or warnings.

## Next Steps

- **Compare versions** using the diffing engine (Example 03).
- **Enforce constraints** at runtime (Example 04).
- **Run validation via CLI**: `pfcv-contract validate contract.json`.