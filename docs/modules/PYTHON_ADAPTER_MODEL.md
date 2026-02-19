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

**STATUS**: PHASE 2 COMPLETE: PROTOTYPE AUTHORITY AND BINDING ENGINE ACTIVE.

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
