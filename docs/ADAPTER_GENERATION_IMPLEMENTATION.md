# Language Adapter Generation (Python) Implementation

This document details the implementation of **: Language Adapter Generation** for the Polyglot FFI Contract Verifier.

## Overview

The Language Adapter Generation subsystem transforms abstract FFI contracts () into concrete, executable Python code. This code enforces all contract constraints at runtime, providing a verified safety layer between Python code and native libraries.

## Generated Architecture

The system produces a modular Python package in the `adapters/` directory:

1.  **`<lib>_adapter.py`**: The main entry point. It loads the native library using `ctypes` and provides wrapped versions of all functions.
2.  **`<lib>_structs.py`**: Contains `ctypes.Structure` definitions for all structs in the contract, including explicit padding and size/alignment validation.
3.  **`<lib>_exceptions.py`**: Defines a specific exception hierarchy for different types of contract violations (e.g., `NullPointerViolation`, `LayoutMismatchError`).
4.  **`<lib>_ownership.py`**: A runtime tracker that monitors memory ownership (borrowed vs. transferred) to detect use-after-transfer and double-free errors.
5.  **`adapter_metadata.json`**: Records generation details, including provenance, statistics, and enforced constraints.

## Constraint Enforcement Patterns

### Nullability
Generated wrappers perform `if ptr is None or not bool(ptr)` checks before passing pointers to native code, raising `NullPointerViolation` if the contract specifies `non_null`.

### Struct Layout
Structs are validated for both **Size** and **Alignment**. The system calculates expected offsets and sizes (including padding) and verifies them at runtime using `ctypes.sizeof()` and `ctypes.addressof() % alignment`.

### Buffer Sizes
Relationship between buffers and their size parameters are checked. If a buffer is non-NULL, the system ensures its associated size parameter is valid.

### Ownership & Lifetimes
- **Borrowed**: Tracked during the call to ensure no illegal transfers occur.
- **Transferred**: Marked as invalid for future use in the Python runtime. Any attempt to use a transferred pointer raises an `OwnershipViolation`.

### Calling Conventions
The generator distinguishes between `cdecl` (using `ctypes.CDLL`) and `stdcall` (using `ctypes.WinDLL`) to ensure stack integrity.

## Usage

Generated adapters can be used directly in Python applications:

```python
from adapters.example_lib import adapter, structs

# Create a validated struct
cfg = structs.Config(mode=1)

# Call a wrapped function (automatically validated)
try:
    result = adapter.process(cfg)
except exceptions.FFIContractViolation as e:
    print(f"Contract violation detected: {e}")
```

## Implementation Details

- **`AdapterGenerator`**: The main orchestrator that sequences module generation.
- **`FunctionWrapperGenerator`**: Generates the `ctypes` function signatures and the logic for pre/post-condition checks.
- **`StructDefinitionGenerator`**: Maps IR types to `ctypes` types and handles structure layout.
- **`ConstraintEnforcementCodegen`**: Translates declarative contract constraints into Python code snippets.
