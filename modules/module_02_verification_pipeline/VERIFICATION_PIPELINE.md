# VERIFICATION PIPELINE - MODULE 02

**Version:** 1.0.0  
**Module:** 02 of 28  
**Status:** In Progress ( Complete)  
**Author:** Darshit Lagdhir  
**Date:** 2026-02-02  

---

## Document Overview

This document provides the complete technical specification for the Verification Pipeline module of the Polyglot FFI Contract Verifier.

**Progress:**
- ✅ : Pipeline Philosophy & Formal Model (COMPLETE)
- ✅ : Stage State Machines & Artifact Validation (COMPLETE)
- ✅ : Artifact Schemas & Incremental Verification (COMPLETE)
- ✅ : Native Interface Ingestion Stage (COMPLETE)
- ⏳ Prompts 5-20: Additional pipeline components (PENDING)

---

## Table of Contents

1. [Pipeline Philosophy & Formal Model](#1-pipeline-philosophy--formal-model)
2. [Stage State Machines & Artifact Validation](#2-stage-state-machines--artifact-validation)
3. [Artifact Schemas & Incremental Verification](#3-artifact-schemas--incremental-verification)
4. [Native Interface Ingestion Stage](#4-native-interface-ingestion-stage)
5. [Implementation Architecture](#5-implementation-architecture)
6. [Usage Examples](#6-usage-examples)
7. [Next Steps](#7-next-steps)

---

## 1. Pipeline Philosophy & Formal Model

*(See previous versions for full text - preserved)*

### 1.1 Overview
The verification pipeline is a **formally constrained transformation system** that converts uncertainty into evidence.

### 1.2 Foundational Principles
1. **No Implicit Correctness Judgments**: Every claim backed by artifacts.
2. **Temporal Separation**: Derivation → Synthesis → Enforcement → Interpretation.
3. **Monotonicity**: Information is never lost, only refined.
4. **Closed System**: All inputs declared upfront.
5. **Determinism**: Identical inputs → Identical outputs.
6. **Conservatism**: Assume worst case (e.g. non-null pointers).

---

## 2. Stage State Machines & Artifact Validation

### 2.1 State Machine Enforcement
`PENDING` → `READY` → `EXECUTING` → `COMPLETED` / `FAILED`.

### 2.2 Advanced Artifact Validation
- **Schema Compatibility**: Semantic versioning.
- **Hash Verification**: Integrity checks.

---

## 3. Artifact Schemas & Incremental Verification

### 3.1 Artifact Types
ExecutionContext, NativeInterface, Contract, TestPlan, ExecutionLog, etc.

### 3.2 Provenance & Incremental
- **Provenance**: Chain of custody for data.
- **Deep Hash Validation**: Ensuring inputs haven't changed.
- **Staleness Detection**: Reusing fresh artifacts.

---

## 4. Native Interface Ingestion Stage

### 4.1 Overview

The Native Interface Ingestion stage is the entry point of the verification pipeline. It is responsible for extracting the ABI (Application Binary Interface) surface from C header files exactly as the compiler sees it. This stage must be **lossless** - no ABI-relevant details can be discarded or simplified.

**Critical Principle: Compiler Reality, Not Developer Intention**
We use `libclang` to parse headers with the exact compilation flags used for the library. This ensures we capture:
- True struct sizes (including padding).
- Actual calling conventions.
- Explicit and implicit alignment rules.

### 4.2 Extracted Information

**1. Functions:**
- Complete signature (return type, parameters with positions).
- Calling convention (`cdecl`, `stdcall`, `fastcall`).
- Linkage and visibility.
- Source location.

**2. Structures:**
- Total size and alignment.
- Fields with precise offsets.
- **Implicit Padding**: Computed gaps between fields.
- **Trailing Padding**: Padding at end of struct for array alignment.

**3. Types:**
- Recursive type definitions (pointers to arrays of structs...).
- Qualifiers (`const`, `volatile`).
- Exact size and alignment for every type.

### 4.3 Struct Layout Computation Algorithm

1. **Extract Declared Fields**: Get offset/size from libclang.
2. **Sort by Offset**: Ensure processing order.
3. **Detect Implicit Padding**:
   If `offset[i+1] > offset[i] + size[i]`, insert `__padding_N` field.
4. **Detect Trailing Padding**:
   If `struct_size > last_field_end`, insert `__padding_N` at end.
5. **Handle Unions**: All fields at offset 0, size is max(fields).

### 4.4 Calling Convention Detection

Crucial for Windows FFI. We map libclang conventions:
- `CallingConv.C` → `cdecl`
- `CallingConv.X86_STDCALL` → `stdcall`
- `CallingConv.X86_FASTCALL` → `fastcall`
- `CallingConv.WIN64` → `win64`

### 4.5 Error Handling

- **Compilation Errors**: Fail stage with compiler diagnostics.
- **Missing libclang**: Fail with ConfigError.
- **Platform Mismatch**: Fail if header target differs from host.

### 4.6 Artifact Schema: NativeInterface

```json
{
  "provenance": { ... },
  "header_path": "/abs/path.h",
  "compilation_flags": ["-I...", "-DWIN32"],
  "functions": [
    {
      "name": "func",
      "calling_convention": "cdecl",
      "parameters": [...]
    }
  ],
  "structures": [
    {
      "name": "MyStruct",
      "size_bytes": 16,
      "fields": [
        {"name": "a", "offset_bytes": 0, "size_bytes": 4},
        {"name": "__padding_1", "offset_bytes": 4, "size_bytes": 4, "is_implicit": true},
        {"name": "b", "offset_bytes": 8, "size_bytes": 8}
      ]
    }
  ]
}
```

---

## 5. Implementation Architecture

### 5.1 Class Hierarchy

```
PipelineStage (ABC)
├── NativeInterfaceIngestionStage (NEW)
│   ├── Uses: libclang
│   ├── Uses: TypeExtractor
│   └── Uses: StructLayoutExtractor
...

VerificationPipeline
├── EnhancedVerificationPipeline
    ├── SchemaRegistry
    └── IncrementalPipelineExecutor
```

### 5.2 External Dependencies
- **libclang**: LLVM's C interface for parsing C/C++.
- **clang.cindex**: Python bindings for libclang.

---

## 6. Usage Examples

### 6.1 Running Ingestion (via Incremental)

```bash
python modules/module_02_verification_pipeline/verification_pipeline.py run-incremental \
    --context artifacts/execution_context.json \
    --target native_interface
```

### 6.2 Checking Staleness

```bash
python modules/module_02_verification_pipeline/verification_pipeline.py check-staleness \
    artifacts/native_interface.json --context artifacts/execution_context.json
```

---

## 7. Next Steps

**** will implement:
- **IR Normalization Stage**: Converting raw NativeInterface into a platform-agnostic Intermediate Representation (IR).
- Canonicalization of types.
- Resolution of typedefs.
