# Language Adapter - Runtime FFI Enforcement

## Overview
Module 08 transforms static contract artifacts into runtime-enforced FFI boundaries. The Language Adapter is the operationalization layer that transforms static contract artifacts into runtime-enforced guarantees.

## Architecture

The adapter architecture consists of seven distinct layers:

1. **Contract Projection Layer**: Consumes contract artifacts and builds an internal enforcement graph.
2. **Validation Engine Core**: Executes validation graphs in dependency order.
3. **Ownership State Machine**: Tracks pointer ownership across FFI boundaries.
4. **Language Specialization Interface**: Defines abstract interfaces for language-specific adapters.
5. **Invocation Orchestrator**: Coordinates the complete enforcement lifecycle.
6. **Crash Isolation Boundary**: Captures native crashes and translates them into exceptions.
7. **Reporting & Diagnostics**: Produces structured violation reports.

## Core Components

### Data Structures
- **ValidationNode**: Represents a single validation check (clause predicate).
- **ValidationGraph**: DAG of nodes ensuring correct execution order.
- **OwnershipState**: State tracking for specific memory addresses.

### Management
- **ContractProjector**: Loads and projects contract artifacts.
- **OwnershipRegistry**: Global mapping for ownership states.
- **EnforcementContext**: Per-invocation audit trail.

### Public API
- **LanguageAdapter**: Main entry point for system coordination.

## Implementation Status

| Feature | Status |
| :--- | :--- |
| Core Data Structures | ✅ Complete |
| Contract Projection | ✅ Complete |
| Ownership Tracking | ✅ Complete |
| Validation Engine | ⏳ Pending |
| Python Specialization | ⏳ Pending |

## Test Coverage
- **Unit Tests**: 120 passing
- **Date**: 2026-02-17


## Usage

```python
from modules.module_08_language_adapter import LanguageAdapter

# 1. Initialize adapter
adapter = LanguageAdapter()

# 2. Load contract
adapter.load_contract('path/to/contract.json')

# 3. Create enforcement context
ctx = adapter.create_enforcement_context('my_native_func')

# ... execution phases ...
```

---

## Part 1 — Contract Runtime Loader

The Contract Runtime Loader serves as the foundational authority layer of the runtime adapter. It is responsible for ingesting, validating, and transforming static contract artifacts into immutable runtime metadata structures.

### Loader Responsibility
- **Artifact Validation**: Ensures the contract JSON follows the required schema for Module 08.
- **ABI Enforcement**: Validates that the contract's target ABI matches the host machine's architecture (32-bit vs 64-bit).
- **Metadata IMMUTABILITY**: Translates raw data into frozen dataclasses to prevent runtime tampering.
- **Fail-Fast Semantics**: The system refuses to initialize if any validation criteria are breached.

### Initialization Flow
1. **Ingest**: Receive raw dictionary representation of the contract.
2. **Schema Check**: Verify `schema_version`, `fingerprint`, and root keys.
3. **Architecture Match**: Compare `sys.maxsize` against the contract's `abi` field.
4. **Descriptor Construction**: Iterate through the `functions` map and build an alphabetical lookup table.

### Example Contract Structure
```json
{
  "schema_version": "1.0",
  "synthesis_version": "1.0.0",
  "fingerprint": "a1b2c3d4e5f6g7h8i9j0",
  "abi": 64,
  "functions": {
    "calculate_hash": {
      "calling_convention": "cdecl",
      "arg_types": ["U8*", "U64"],
      "return_type": "U32"
    }
  }
}
```

### Failure Semantics
- **ContractInitializationError**: Raised for missing keys, invalid types, or schema mismatches.
- **ABICompatibilityError**: Raised exclusively for architecture mismatches (e.g., loading a 64-bit contract on a 32-bit system).
