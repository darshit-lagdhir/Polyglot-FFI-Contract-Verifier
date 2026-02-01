# Contract Synthesis Implementation

This document details the implementation of **Phase 4: Contract Synthesis Engine** for the Polyglot FFI Contract Verifier.

## Overview

The Contract Synthesis Engine transforms normalized Intermediate Representation (IR) into a formal **FFI Contract**. While the IR describes *structure*, the Contract describes *intent* and *constraints*. 

The synthesis process makes the implicit assumptions of C developers explicit and machine-readable, enabling automated verification.

## Core Components

1.  **`ContractSynthesizer`**: The main orchestrator that sequences the analysis of functions, structs, and globals.
2.  **`ConstraintDeriver`**: Implements the semantic rules used to infer constraints from types and metadata.
3.  **`NamingConventionAnalyzer`**: Employs heuristics and naming patterns (e.g., `create_`, `optional_`) to detect developer intent.
4.  **`ConservativeDefaultPolicy`**: Provides safe fallback behaviors when evidence is missing, favoring safety over permissiveness.
5.  **`ConstraintIDGenerator`**: Produces deterministic, human-readable IDs for every constraint for traceability.

## Constraint Derivation Rules

The engine implements 10 core derivation rules:

| Rule | Category | Description |
|------|----------|-------------|
| 1 | Nullability | Infers if a pointer can be NULL based on naming (e.g., `optional_`) or defaults to non-null. |
| 2 | Ownership | Detects if memory ownership changes (e.g., `create_` transfers to caller, `destroy_` to callee). |
| 3 | Lifetime | Sets the validity period of pointers (usually `call_duration` for borrowed pointers). |
| 4 | Buffers | Detects adjacent buffer/size pairs (e.g., `void* buf, size_t len`) and establishes a dependency. |
| 5 | Struct Fields| Enforces that non-padding fields must be initialized and analyzes pointer fields. |
| 6 | Return Values | Detects error code patterns (int returns) and ownership of returned pointers. |
| 7 | Call Convention| Enforces the exact calling convention (e.g., `cdecl`) from the IR. |
| 8 | Struct Layout | Requires an exact binary match between the target language and native layout. |
| 9 | Multi-mutability| Uses the `const` qualifier to enforce immutability on parameters. |
| 10| Variadic | Issues warnings for variadic functions (e.g., `printf`) which require manual verification. |

## Conservative Default Policies

When semantic hints are absent, the engine applies the following policies:

1.  **Nullability**: Pointers are assumed **non-null**.
2.  **Ownership**: Pointers are assumed **borrowed** (no transfer).
3.  **Lifetime**: Pointers are assumed valid only for the **duration of the call**.
4.  **Mutability**: Pointers are assumed **mutable** unless marked `const`.
5.  **Buffers**: Pointers that look like buffers but lack a size parameter trigger an **error/warning**.
6.  **Integers**: Integer return values are treated as **error codes** (0 = success).

## Traceability and Justification

Every constraint in the produced `contract.json` includes:
-   `constraint_id`: A unique, deterministic string.
-   `justification`: A human-readable explanation of why the rule was applied (e.g., "Naming convention suggests optional parameter").
-   `severity`: Either `error`, `warning`, or `info`.

## Metadata and Warnings

The synthesizer tracks its own confidence. If it makes a high-risk assumption (like assuming a `void*` is just a borrowed pointer when it can't be sure), it logs a warning in the `synthesis_metadata` section of the contract.

## Example Contract Structure

```json
{
  "function_name": "process",
  "pre_conditions": [
    {
      "constraint_id": "func_process_p_cfg_non_null",
      "constraint_type": "non_null",
      "description": "Parameter 'cfg' must not be NULL",
      "target": "parameter:cfg",
      "justification": "Pointer parameter without indication of nullability",
      "severity": "error"
    }
  ],
  "parameter_contracts": [
    {
      "parameter_name": "cfg",
      "nullability": "non_null",
      "ownership": "borrowed",
      "lifetime": "call_duration",
      "mutability": "immutable"
    }
  ]
}
```
