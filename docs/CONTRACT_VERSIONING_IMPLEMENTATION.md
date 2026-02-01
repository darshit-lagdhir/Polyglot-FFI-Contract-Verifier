# Contract Schema Versioning Implementation

This document details the implementation of **Phase 5: Contract Schema Versioning and Evolution** for the Polyglot FFI Contract Verifier.

## Overview

The Contract Schema Versioning system ensures that FFI contracts are stable and evolvable. It enables detecting ABI changes when a native library or its header is updated, mapping these changes to risk categories, and providing actionable recommendations for developers.

## Core Components

1.  **`SchemaVersionManager`**: Manages semantic versioning (MAJOR.MINOR.PATCH) for contracts. It determines if two contracts are structure-compatible based on their schema version.
2.  **`ContractSchemaValidator`**: Ensures that contract files conform to the expected structural requirements and version constraints.
3.  **`ContractComparator`**: Implements a systematic 8-step algorithm to compare two contracts and identify every addition, removal, and modification.
4.  **`ChangeClassifier`**: Assigns risk categories (Breaking, Compatible, Semantic, etc.) and impact descriptions to each detected change.
5.  **`CompatibilityReportGenerator`**: Produces professional, human-readable summary reports that help developers understand the risks of an ABI update.

## Change Detection Algorithm

The system follows a deterministic comparison process:
1.  **Load & Validate**: Load baseline and current contracts; verify JSON integrity and schema.
2.  **Schema Check**: Verify that the schema versions are compatible (matching Major version).
3.  **Indexing**: Create lookup maps for functions, structs, and types.
4.  **Function Diff**: Detect added/removed functions, and changes in signatures or calling conventions.
5.  **Struct Diff**: Detect layout changes, size/alignment shifts, and field modifications.
6.  **Type Registry Diff**: Track changes in primitive or derived type definitions.
7.  **Global Constraints Diff**: Track changes in environment-wide safety invariants.
8.  **Artifact Assembly**: Generate `contract_diff.json` with full metadata.

## Change Categories & Impact

| Category | Impact | Action Required |
|----------|--------|-----------------|
| **Breaking** | Bindings will crash or fail to link. | Update bindings/adapters immediately and recompile. |
| **Potentially Breaking** | May break if size/offsets are hardcoded. | Review struct layout and regenerate adapters. |
| **Semantic** | Safety rules changed (e.g. non-null). | Review application logic for contract compliance. |
| **Compatible** | New functionality added. | Regenerate adapters to expose new features (optional). |
| **Schema** | Tool incompatibility. | Upgrade verifier tools. |

## Compatibility Levels

The system assigns an overall compatibility level to every comparison:
-   **FULLY_COMPATIBLE**: Identical contracts or zero-risk additions.
-   **COMPATIBLE**: Function/struct additions that don't affect existing code.
-   **SEMANTICALLY_INCOMPATIBLE**: structural parity but safety constraints (like nullability) have tightened.
-   **POTENTIALLY_BREAKING**: Changes like adding fields to structs which change size.
-   **BREAKING**: Removals or signature changes that invalidate existing binary interfaces.

## Usage

### Validate Schema
```bash
python polyglot_ffi_verifier.py validate-schema
```

### Compare Contracts
```bash
python polyglot_ffi_verifier.py compare-contracts --baseline previous_contract.json
```
This produces:
-   `artifacts/contract_diff.json`: Machine-readable diff.
-   `artifacts/compatibility_report.txt`: Human-readable assessment.
