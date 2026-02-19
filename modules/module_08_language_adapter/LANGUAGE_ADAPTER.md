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

---

## Part 2 — Prototype Authority Layer

The Prototype Authority Layer (PAL) acts as the ABI enforcer, overriding developer-defined FFI bindings with authoritative metadata from the contract.

### Why ctypes bindings cannot be trusted
In standard `ctypes` usage, the `argtypes` and `restype` attributes are manually assigned. Errors in these assignments lead to:
- **Silent Truncation**: `I64` being treated as `I32`.
- **Stack Corruption**: Incorrect calling conventions (e.g., `cdecl` vs `stdcall`).
- **Memory Violiations**: Incorrect pointer coercion.

### ABI Override Philosophy
The PAL treats the contract as the absolute authority. Upon initialization, it iterates through all functions defined in the contract and forcibly sets their `argtypes` and `restype` based on a fixed, internal type mapping table.

### Deterministic Binding Order
Functions are bound in alphabetical order based on their symbol names. This ensures that initialization failures are predictable and non-nondeterministic.

### Type Mapping Table
| Contract Type | ctypes Equivalent |
| :--- | :--- |
| `int32` | `ctypes.c_int32` |
| `uint32` | `ctypes.c_uint32` |
| `int64` | `ctypes.c_int64` |
| `uint64` | `ctypes.c_uint64` |
| `float` | `ctypes.c_float` |
| `double` | `ctypes.c_double` |
| `char_ptr` | `ctypes.c_char_p` |
| `void_ptr` | `ctypes.c_void_p` |
| `void` | `None` |

### cffi Validation Rules
While `cffi` handles its own ABI enforcement through C-style declarations, PAL validates that symbols referenced in the contract actually exist in the `cffi` namespace. PAL does not perform type coercion on `cffi` objects but ensures they are present for the later validation stages.

### Failure Semantics
- **PrototypeMismatchError**: Raised if a symbol is missing from the library handle or if the binding type (e.g., not a `ctypes._CFuncPtr`) is unsupported.
- **ContractInitializationError**: Raised if the contract contains a type string that has no authoritative mapping in `_CTYPES_TYPE_MAP`.

---

## Part 3 — Deterministic Initialization Orchestration

The final phase of the adapter bootstrapping ensures that initialization is a transactional, all-or-nothing process with strict integrity verification.

### Transactional Initialization Model
The adapter uses an `AdapterInitializationState` machine to track the progress of the bootstrapping process. If any step in the binding loop fails (symbol not found, type mismatch, etc.), the entire initialization is marked as failed, and the partial state is invalidated.

### Binding Integrity Verification
After the primary binding loop completes, a secondary verification pass compares the set of functions requested by the contract against the set of functions successfully bound by the `PrototypeAuthorityLayer`. Any discrepancy triggers a `PrototypeMismatchError`.

### Fail-Fast Semantics
- **No Incomplete State**: It is impossible to have an adapter where some functions are bound and others are not.
- **Immediate Abortion**: The binding loop aborts on the first encountered error to prevent cascading failures or corrupted library handles.

### Idempotent Initialization Rules
The `initialize_python_adapter` entrypoint is designed to be safe for re-initialization. However, internal state tracking ensures that only a fully successful, verified binding allows the adapter to be used for FFI enforcement.

### State Tracking Model
- `initialized`: Boolean flag indicating the binding loop and integrity check finished successfully.
- `bound_functions`: A sorted list of function names that were processed.
- `failed`: Boolean flag set if any exception occurred during the bootstrap.

### No Partial Success Guarantee
If `initialize_python_adapter` returns successfully, the caller is guaranteed that 100% of the contract's functions are bound with authoritative types and calling conventions.

### Deterministic Ordering Contract
The PAL enforces alphabetical processing of function symbols. This guarantees that side-effects or logging during initialization occur in a fixed, reproducible sequence regardless of the input contract's JSON structure.

### Integration Hardening Strategy
By isolating the initialization state and enforcing strict post-binding verification, the adapter provides a hardened boundary that resists inconsistent environment states and developer errors.

---

## Prompt 02 Part 1 — Invocation Proxy Generator

The Invocation Proxy Generator establishes a deterministic enforcement boundary between the Python runtime and native code. By interposing a controlled callable wrapper for every bound function, the system ensures that every cross-language invocation can be validated, audited, and isolated.

### Why raw invocation is unsafe
Directly calling raw `ctypes` or `cffi` functions bypasses all contract enforcement logic. Without an interposition layer, there is no mechanism to verify spatial memory constraints, relational invariants, or ownership transitions before the native boundary is crossed.

### Enforcement Boundary Concept
The proxy acts as a shell that surrounds the raw native call. This shell provides hooks for multiple stages of enforcement:
1. **Pre-call Validation**: Arity, types, and mathematical invariants.
2. **Ownership Management**: Pointer state transitions.
3. **Execution**: The actual native invocation.
4. **Post-call Validation**: Return value checks and pointer side-effects.
5. **Exception Translation**: Mapping native signals to Python exceptions.

### Proxy Replacement Model
During initialization, the `PrototypeAuthorityLayer` generates a unique proxy wrapper for every function defined in the contract. It then **forcibly replaces** the original attribute on the library handle with the proxy. Once the adapter is active, the developer can only access the native code through these proxies.

### Raw Function Retention in Registry
To prevent loss of access to the underlying native entry points, the original raw function pointers are stored in an internal `InvocationProxyRegistry`. This registry is private to the adapter and is the only authorized way to perform the final dispatch.

### Deterministic Wrapper Generation
Proxies are built in a fixed alphabetical sequence, ensuring that the initialization state and internal registry ordering are consistent across different runs and environments.

### Future Insertion Points for Validation Stages
While Part 1 focuses on the structural wrap, the proxy is designed to allow high-speed insertion of relational constraint evaluation and ownership tracking in subsequent phases without requiring changes to the core dispatch logic.

### No-trust direct invocation philosophy
The system operates on the principle that no raw library attribute can be trusted. Every callable exposed on a verified library handle MUST traverse the proxy boundary, or the system is considered compromised.

---

## Prompt 02 Part 2 — Validation Execution Core (Parameter-Level)

The Validation Execution Core transforms the passive proxy wrapper into an active enforcement boundary. In this stage, every parameter and return value is explicitly validated against the contract descriptor before and after the native FFI boundary is crossed.

### Argument count enforcement
The system explicitly verifies that the number of arguments provided in Python matches the `arg_types` definition in the contract. This prevents common C-level stack corruption bugs caused by mismatched arity.

### Range enforcement philosophy
Python integers have arbitrary precision, while C integers have fixed widths. The adapter enforces strict bounds for `int32`, `uint32`, `int64`, and `uint64`. This ensures that negative values are not passed to unsigned parameters and that overflow/truncation errors are caught in Python before they reach native memory.

### No implicit truncation rule
In raw `ctypes`, assigning a 65-bit integer to a `ctypes.c_int32` will result in silent truncation. The Language Adapter rejects any integer that does not fit exactly within the target type's range, ensuring mathematical integrity across the boundary.

### Nullability enforcement
The system enforces strict nullability rules. `None` is only permitted for types explicitly marked as pointers (`*_ptr` or `void_ptr`). Passing `None` to a scalar type (e.g., `int32`) triggers an immediate `ContractViolationError`.

### Return type validation
Post-invocation validation ensures that the native code produced a result compatible with the contract's expectations. This includes range checks for integer returns and `None` verification for `void` return types.

### Deterministic error format
When a violation occurs, the system raises a `ContractViolationError` containing:
- The function name.
- The 0-indexed parameter index (or -1 for global/return errors).
- A specific, human-readable violation message.
- The contract fingerprint.

### Boundary enforcement examples
- **Violation**: Passing `-1` to a `uint32` parameter.
- **Violation**: Passing `123` to a function expecting `0` arguments.
- **Violation**: A `void` function returning a non-zero integer.
- **Violation**: Passing `None` to a `double` parameter.

---

## Prompt 02 Part 3 — Relational Constraint Evaluator

While parameter-level validation ensures that individual values are safe, FFI correctness often depends on the relationship between multiple parameters. The Relational Constraint Evaluator enforces cross-parameter invariants.

### Cross-parameter invariants
Many C APIs require that a length parameter matches the size of a buffer, or that coordinates (width, height) do not exceed the capacity of a passed array. These are relational constraints that cannot be verified by looking at a single parameter in isolation.

### Supported Operators
The evaluator supports the following relational operators:
- `==`: Exact equality (e.g., `count == buffer_size`).
- `>=`: Greater than or equal (e.g., `stride >= width`).
- `<=`: Less than or equal (e.g., `offset <= total_size`).

### Conditional Rule Model (if_nonzero)
To support optional buffers or variable-length API patterns, the evaluator supports the `if_nonzero` condition. If a rule is marked with this condition, the validation logic is only executed if the `left_index` value is non-zero. This prevents false positives when a pointer is null and its associated size is zero.

### Deterministic Rule Ordering
To ensure that error messages are consistent and reproducible, relational rules are sorted by their unique `id` during contract loading. Rules are always evaluated in this fixed alphabetical order.

### Failure Semantics
Mismatched relational constraints raise a `ContractViolationError`. The error points to the `left_index` (the primary subject of the rule) and includes the rule ID and the observed values that caused the mismatch.

### Post-call Reconciliation Hook
This phase introduces a structural hook for post-call reconciliation. While currently acting as a pass-through, this hook is the architectural insertion point for future ownership state transitions and pointer validity checks that must occur after the native code has completed execution.

### Relational Violation Example
- **Mismatched Length**: `Relational rule LENGTH_MATCH failed: 1024 != 512` (where `length` was expected to match `buffer_capacity`).
- **Constraint Violation**: `Relational rule MIN_STRIDE failed: 640 < 1280` (where `stride` must be at least the image `width`).

---

## Prompt 03 Part 1 — Ownership Registry Engine

Memory management is the most critical failure point in FFI systems. The Ownership Registry Engine provides foundational tracking of native pointer lifecycles to prevent catastrophic memory errors.

### Pointer Lifecycle Tracking
The engine monitors the state of pointers from the moment they are returned by a native allocator until they are passed to a deallocator. This explicit tracking bridges the gap between Python's garbage collector and native memory management.

### Foundational Governance
This phase implements the base governance for pointer safety:
- **Canonical Identity**: Every pointer is reduced to its absolute memory address for tracking, regardless of its `ctypes` wrapper type.
- **State Records**: Each tracked pointer is associated with a `PointerOwnershipRecord` containing its origin function, current state (`active` or `freed`), and ownership type.
- **Double-Free Prevention**: The registry detects when a pointer is passed to a deallocation function multiple times, raising an immediate `OwnershipViolationError`.
- **Use-After-Free Detection**: Any attempt to pass a pointer that has been marked as `freed` into a native function triggers a violation before the native call is made.

### Free Function Enforcement
The adapter identifies deallocation functions through contract metadata. When a function marked as a `free_function` is invoked, the registry automatically transitions the subject pointer to the `freed` state.

### Explicit Return Ownership
Pointers returned by native functions can be marked as `caller_owned`. When such a pointer is returned, the adapter automatically registers it in the active tracking pool, ensuring its future lifecycle is governed by the enforcement engine.

### Deterministic Failure Reporting
Ownership violations follow a strict, reproducible reporting format including the function name, the pointer address in hexadecimal, and a specific message detailing the nature of the violation.

---

## Prompt 03 Part 2 — Ownership State Machine and Epoch Model

To handle real-world native memory behavior, the Ownership Registry has been upgraded to a formal State Machine utilizing a Pointer Epoch Model to address address-reuse collisions.

### The Address Reuse Problem
Native allocators frequently recycle memory addresses. A simple registry based solely on address will fail if a pointer is freed and then a new allocation is made at the same address. The simple registry would see the new pointer as already freed (a false positive use-after-free).

### Epoch-Based Canonical Identity
The system now uses a three-part canonical key for pointer identity: `(contract_fingerprint, pointer_address, epoch)`. 
- **Epoch**: A per-address counter that increments every time a pointer is freed. This effectively separates the identities of two different allocations that happen to share the same memory address over time.

### State Machine Lifecycle
Pointers transition through a strict set of lifecycle states:
- `ACTIVE_CALLER_OWNED`: Memory that the Python caller is responsible for deallocating.
- `BORROWED_INPUT`: Pointers passed into a function for temporary use. They cannot be freed by the callee.
- `FREED`: The terminal state for an allocation in its current epoch.
- `UNOBSERVED`: Pointers that are not currently tracked by the adapter.

### Transition Enforcement
Every state change is validated against an allowed transition matrix. For example:
- `ACTIVE_CALLER_OWNED` can transition to `FREED`.
- `BORROWED_INPUT` **cannot** transition to `FREED` through a deallocator call. Any attempt to do so triggers an `OwnershipViolationError` for an invalid state transition.

### Deterministic History Tracking
Each `PointerOwnershipRecord` maintains a chronological history of all transitions, including the function that triggered the change. This provides a deterministic "black box" recording for debugging memory safety violations.

---

## Prompt 03 Part 3 — Pointer Wrapper and Alias Enforcement

To prevent users from bypassing ownership rules using raw memory manipulation, the adapter now enforces usage through a controlled object boundary using Pointer Wrapper Objects.

### Wrapper Object Philosophy
When a native function returns a `caller_owned` pointer, the user no longer receives a raw integer or `ctypes` object. Instead, they receive a `ContractPointerWrapper`. This object acts as a proxy for the native memory, ensuring every access is governed by the registry.

### Proper Deallocation Enforcement
One of the most common FFI errors is calling a deallocator on a raw pointer address that has already been freed. With wrapper enforcement:
- **Free via Wrapper**: Users must call `wrapper.free(function_name)` or pass the wrapper object to a designated `free_function`.
- **Raw Bypass Prevention**: If a user attempts to call a `free_function` using a raw integer address that is currently governed by a wrapper, the system raises an `OwnershipViolationError`. This prevents "silent" double-frees occurring outside the managed lifecycle.

### Alias Detection Strategy
The system prevents "aliasing" where multiple independent Python objects attempt to manage the same native pointer. 
- **Unique Mapping**: The `OwnershipRegistry` maintains a `_wrapper_map` that links a specific `(fingerprint, address, epoch)` key to exactly one `ContractPointerWrapper`.
- **Collision Rejection**: Any attempt to attach a second wrapper to the same pointer identity (alias) is rejected, ensuring a strict one-to-one relationship between the Python management object and the native allocation.

### Pre-Invocation Ownership Guard
Before any native function is executed, the adapter performs a "pre-invoke guard" sweep:
1. **Unwrap Arguments**: Any `ContractPointerWrapper` arguments are identified and unwrapped to their raw native addresses.
2. **Liveness Check**: The unwrapped pointer's canonical identity is checked against the registry.
3. **Guard Abort**: If the pointer is not in an `ACTIVE` state for its recorded epoch (e.g., it was previously freed via its wrapper), the invocation is blocked before it reaches native code.

This architecture ensures that even if a user keeps a reference to an old wrapper, they cannot use it to trigger a Use-After-Free in native memory.
