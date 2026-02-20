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
<!-- File Integrity Identifier: c7063db4df7a1b21 -->
<!-- ============================================================================== -->

# Python Adapter Model

## Overview
The Python Adapter Model defines the concrete, operational realization of the Language Adapter Specification within the Python runtime ecosystem.

## 1. CONTRACT RUNTIME LOADER
The Contract Runtime Loader is the secure entry-point for transforming serialized contract artifacts into executable enforcement logic.

### 1.1 Integrity Verification
- **Cryptographic Anchoring**: Every contract is verified against a SHA-256 fingerprint embedded in the metadata.
- **Constant-Time Comparison**: Uses `hmac.compare_digest` for the fingerprint check to prevent timing attacks.
- **Binary-Safe Ingestion**: Contracts are read in binary mode (`rb`) to prevent silent byte mutation from newline normalization.

### 1.2 ABI Truth Mapping
- **Hardware Interrogation**: Dynamically verifies host pointer width using `struct.calcsize("P")` to prevent 32/64-bit truncation or extension errors.
- **Endianness Guard**: Confirms `sys.byteorder` matches contract endianness to prevent data corruption.
- **Platform Validation**: Rejects contracts synthesized for different OS families (e.g., Linux vs. Windows).

### 1.3 Enforcement Descriptor Table (EDT)
- **O(1) Performance**: Function descriptors are stored in a high-speed lookup table for constant-time retrieval.
- **Memory Optimization**: Uses `__slots__` in `EnforcementDescriptor` classes to minimize memory footprint in large-scale deployments (10,000+ functions).
- **Collision Protection**: Enforces single-registration logic to prevent silent constraint shadowing.

**STATUS**: PHASE 4 COMPLETE: RELATIONAL CONSTRAINT EVALUATOR AND AST COMPILER ACTIVE.

## 2. PROTOTYPE AUTHORITY LAYER
The Prototype Authority Layer (PAL) intercepts the standard `ctypes` binding process, ensuring that the verified Contract serves as the absolute and only authorized source of truth for FFI signatures.

### 2.1 ABI Type Factory
- **Bit-Width Fidelity**: Maps abstract Contract IR types (e.g., `I32`, `U64`) to concrete, fixed-width `ctypes` objects (e.g., `c_int32`, `c_uint64`).
- **Platform Independence**: Prevents data model mismatch errors (LLP64 vs LP64) by avoiding loosely defined C aliases like `c_long`.
- **O(1) Performance**: Utilizes pre-computed mapping matrices for constant-time type translation.

### 2.2 Calling Convention Orchestration
- **Stack Protection**: Dynamically routes symbols through either `ctypes.CFUNCTYPE` or `ctypes.WINFUNCTYPE` based on the contract's calling convention (`cdecl` vs `stdcall`).
- **Convention Selection**: Automatically unified for x64 architecture while maintaining strict 32-bit routing for legacy Windows support.

### 2.3 Symbol Interposition
- **Truth Overriding**: Reconstructs the function prototype from the contract metadata and applies it to the raw native symbol.
- **FFI Locking**: Explicitly sets `argtypes` and `restype` on all bound functions to prevent runtime attribute manipulation.

## 3. INVOCATION PROXY GENERATOR
The Invocation Proxy wraps every bound native function in a deterministic Python callable to enforce safety invariants *before* the native crossing.

### 3.1 Zero-Mistake Marshalling
- **Boundary Enforcement**: Explicitly validates that Python arbitrary-precision integers fall within the mathematical bounds of the target C type (e.g., checking `0 <= val <= 255` for a `U8` parameter).
- **Silent Truncation Prevention**: Instantly raises a `MarshallingViolationError` if bounds are exceeded, preventing `ctypes` from silently truncating high-order bits.
- **Hot-Path Optimization**: Generated proxies utilize `__slots__` and pre-computed parameter lists for near-native performance overhead.

## 4. MEMORY PINNING CONTROLLER
The Memory Pinning Controller captures and anchors Python objects to prevent premature reclamation by the Garbage Collector during native execution.

### 4.1 Scope Retention
- **Strong Reference Anchoring**: Captures ephemeral objects (like inline `c_char_p` instantiations) in an internal list, forcefully incrementing their reference count.
- **Context Manager Lifecycle**: Uses `__enter__` and `__exit__` to guarantee that pinned objects are released exactly once the native call yields control.

## 5. LAYOUT VERIFICATION ENGINE
The Layout Verification Engine performs recursive metrology on complex structures to ensure perfect ABI alignment.

### 5.1 Recursive Metrology
- **Padding Trap Detection**: Calculates byte-offsets and sizes for every field, including nested structs and arrays, to ensure they match the native compiler's layout.
- **DFS Traversal**: Executes a Depth-First Search over the `ctypes.Structure` metadata to prove alignment at all levels.
- **O(1) Metrology Cache**: Caches the verification status of struct types using their memory `id()`, eliminating verification overhead on subsequent calls.

## 6. RELATIONAL CONSTRAINT EVALUATOR (RCE)
The Relational Constraint Evaluator prevents spatial memory violations by proving mathematical invariants between multiple parameters before invocation.

### 6.1 Algebraic Syntax Tree (AST) Architecture
- **Sandboxed Execution**: Compiles Contract-defined JSON constraints into executable Python memory graphs using optimized `ASTNode` hierarchies.
- **Parametric Binding**: Uses direct O(1) tuple-indexing for argument substitution, avoiding expensive lookups or copies.
- **Zero-Allocation Evaluation**: Designed for high-speed hot-path execution with minimal memory pressure.

### 6.2 Deterministic Constraint Compiler
- **Depth-Limited Parsing**: Enforces a strict recursion depth limit (50) to prevent load-time Stack Overflow DoS attacks.
- **Hermetically Sealed Operators**: Strictly maps mathematical operators to safe, built-in Python C-functions, preventing `eval()` based code injection.
- **Overflow Guarding**: Actively monitors internal calculations to prevent bypasses via 64-bit coordinate wrapping.