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
<!-- File Integrity Identifier: 1d9dfe579399c996 -->
<!-- ============================================================================== -->

# Example 01: Basic Contract Generation

## Overview

This example demonstrates the most basic contract generation workflow:
1. Configure generation parameters using `GenerationConfig`.
2. Create a `ContractGenerator`.
3. Generate a contract from an IR artifact.
4. Inspect the generated clauses.
5. Save the contract to a JSON file.

## Prerequisites

- Module 06 installed.
- Python 3.9+.

## Running the Example

```bash
python generate.py
```

## Expected Output

```text
Generating contract from IR artifact...
✓ Generated 15 clauses

Clause Breakdown:
  layout: 5
  nullability: 5
  ownership: 3
  size: 2

✓ Contract saved to example_library.contract.json
✓ Contract version: 1.0.0
```

## What's Happening

1.  **Configuration**: We define a `GenerationConfig` that sets the confidence threshold and enables specific analysis passes.
2.  **Generation**: The `ContractGenerator` analyzes the provided IR artifact (mocked in this example) and synthesizes clauses based on structural data and naming heuristics.
3.  **Statistics**: We use a `Counter` to show the distribution of different clause types.
4.  **Persistence**: The `save_contract` convenience function handles serialization and integrity hashing before writing to the filesystem.

## Next Steps

- **Validate** the generated contract (see Example 02).
- **Inspect** clauses in detail (use CLI: `pfcv-contract inspect`).
- **Customize** generation config for specific interface requirements.