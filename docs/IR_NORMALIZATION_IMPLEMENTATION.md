# Intermediate Representation Normalization Implementation

The Intermediate Representation (IR) Normalization layer transforms raw, compiler-specific Native Interface Artifacts into a canonical, compiler-agnostic representation. This document details the design and implementation of this subsystem.

## Overview

IR Normalization is the third phase of the Polyglot FFI Contract Verifier pipeline. Its primary goal is to decouple downstream verification stages from the idiosyncrasies of compiler frontends (like `libclang`) and platform-specific type naming conventions.

**Position in Pipeline:**
`ExecutionContext ()` -> `Native Interface Ingestion ()` -> **`IR Normalization ()`** -> `Contract Synthesis ()`

## Type Registry Design

The IR uses a centralized **Type Registry** to represent all types encountered in the interface. This design provides several benefits:
- **Deduplication**: Identical types are defined once and referenced by a unique ID.
- **Trivial Comparison**: Type equality checks become simple string comparisons of Type IDs.
- **Flat Structure**: Circular or recursive types (like linked list structs) are handled easily by ID references without deep nesting issues in JSON.

### Type ID Generation Algorithm
Type IDs are deterministic strings computed from the canonical representation of the type:
- **Primitives**: `primitive:<canonical_name>` (e.g., `primitive:int32`)
- **Pointers**: `pointer:<pointee_id>` (e.g., `pointer:primitive:void`)
- **Structs**: `struct:<name>` (e.g., `struct:Config`)
- **Enums**: `enum:<name>` (e.g., `enum:Status`)
- **Arrays**: `array:<element_id>:<count>` (e.g., `array:primitive:int8:10`)

## Typedef Resolution

The `TypeResolver` resolves all `typedef` chains transitively. If the native interface contains:
```c
typedef int MyInt;
typedef MyInt YourInt;
```
Any reference to `YourInt` is resolved to `primitive:int32` in the IR. This ensures that verification logic only deals with the actual memory-level type, not its various aliases.

## Canonical Type Mapping

The system maps compiler-specific type names to fixed-width canonical names based on the target platform (Windows x64).

| C Type | Canonical Name (Windows x64) | Size (Bytes) |
| :--- | :--- | :--- |
| `int` | `int32` | 4 |
| `long` | `int32` | 4 |
| `long long` | `int64` | 8 |
| `unsigned int` | `uint32` | 4 |
| `size_t` | `uint64` | 8 |
| `void*` | `pointer:void` | 8 |

## Qualifier Normalization

Type qualifiers (`const`, `volatile`, `restrict`) are extracted from compiler-specific lists and converted into a structured boolean map:
```json
"qualifiers": {
  "is_const": true,
  "is_volatile": false,
  "is_restrict": false
}
```

## Struct and Enum Normalization

### Structs
Struct layouts extracted in  are preserved exactly (including explicit padding fields). The normalization process replaces the deep, inline type definitions for fields with flat `type_id` references to the Type Registry.

### Enums
Enums are normalized by mapping their underlying storage type (usually `int`) to a canonical primitive ID and preserving the named constant values.

## Error Handling

- **Precondition Errors**: If `native_interface.json` is missing, the normalizer reports that  must be run first.
- **Validation Errors**: If the input artifact is malformed or contains circular typedefs, the system raises a detailed `ToolingError`.
- **Transparency**: All errors include context about the execution ID and producing phase to aid in debugging.

## Usage

### Orchestration
Normalization is triggered as part of the `synthesize` command (which runs phases 3 and 4):
```bash
python polyglot_ffi_verifier.py synthesize
```

### Standalone Validation
You can verify the IR normalization logic independently:
```bash
python validate_ir_normalization.py
```
