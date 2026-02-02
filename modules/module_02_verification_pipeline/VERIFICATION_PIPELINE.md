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
- ✅ : IR Normalization Stage (COMPLETE)
- ⏳ Prompts 6-20: Additional pipeline components (PENDING)

---

## Table of Contents

1. [Pipeline Philosophy & Formal Model](#1-pipeline-philosophy--formal-model)
2. [Stage State Machines & Artifact Validation](#2-stage-state-machines--artifact-validation)
3. [Artifact Schemas & Incremental Verification](#3-artifact-schemas--incremental-verification)
4. [Native Interface Ingestion Stage](#4-native-interface-ingestion-stage)
5. [IR Normalization Stage](#5-ir-normalization-stage)
6. [Implementation Architecture](#6-implementation-architecture)
7. [Usage Examples](#7-usage-examples)
8. [Next Steps](#8-next-steps)

---

## 1. Pipeline Philosophy & Formal Model

*(See previous versions for full text - preserved)*

### 1.1 Overview
The verification pipeline is a **formally constrained transformation system** that converts uncertainty into evidence.

### 1.2 Foundational Principles
1. **No Implicit Correctness Judgments**
2. **Temporal Separation**
3. **Monotonicity**
4. **Closed System**
5. **Determinism**
6. **Conservatism**

---

## 2. Stage State Machines & Artifact Validation

### 2.1 State Machine Enforcement
`PENDING` → `READY` → `EXECUTING` → `COMPLETED` / `FAILED`.

### 2.2 Advanced Artifact Validation
- Schema Compatibility
- Hash Verification

---

## 3. Artifact Schemas & Incremental Verification

### 3.1 Artifact Types
ExecutionContext, NativeInterface, IR, Contract, etc.

### 3.2 Provenance & Incremental
- Provenance tracking
- Staleness detection

---

## 4. Native Interface Ingestion Stage

### 4.1 Overview
Extracts ABI surface from C headers using `libclang` with lossless fidelity (padding, alignment, etc.).

### 4.2 Extracted Information
Functions, Structures (with padding), Enums, Typedefs.

---

## 5. IR Normalization Stage

### 5.1 Overview - Semantic-Preserving Transformation

The IR Normalization stage transforms the verbose, compiler-specific native interface artifact into a clean, canonical intermediate representation (IR).

**Principles:**
- **Canonical Form**: One unique representation per semantic concept.
- **Platform Abstraction**: Remove toolchain quirks.
- **Information Preservation**: No ABI details discarded.
- **Structural Identity**: Types are identified by structure, not name.

### 5.2 Transitive Typedef Resolution

Typedefs (e.g., `LPSTR` → `char*`) are resolved to their underlying canonical types. The pipeline handles:
- **Chained Typedefs**: `A` → `B` → `C` resolved to `C`.
- **Circular Detection**: `A` → `B` → `A` raises error.
- **Aliasing**: Typedefs preserved as aliases for diagnostics.

### 5.3 Type Registry & Stable IDs

All types are registered in a central `TypeRegistry`.
- **Type ID**: Deterministic, stable string (e.g., `pointer_to_primitive_int`).
- **Deduplication**: Identical structures share the same Type ID.
- **Bi-directional**: ID ↔ Type Info.

### 5.4 Normalization Rules

1.  **Structs**:
    - Inline types replaced with Type IDs.
    - Padding fields normalized (`__padding_N`, `is_implicit: true`).
    - Bitfields preserved with offset/width.

2.  **Functions**:
    - Parameter types resolved to IDs.
    - Calling conventions mapped to canonical set (`stdcall`, `cdecl`, `win64`, `sysv`).
    - Unnamed parameters given synthetic names (`param_0`).

3.  **Enums**:
    - Underlying type resolved.
    - All constants given explicit values.

4.  **Qualifiers**:
    - `const`, `volatile`, `restrict` normalized and preserved.

### 5.5 Artifact Schema: IR

```json
{
  "provenance": {...},
  "platform": {
    "pointer_size": 8,
    "endianness": "little",
    "alignment_rules": "msvc"
  },
  "type_registry": {
    "primitive_int": {"kind": "primitive", "name": "int", "size_bytes": 4},
    "pointer_to_primitive_int": {"kind": "pointer", "pointee_id": "primitive_int"}
  },
  "functions": [
    {
      "name": "process",
      "return_type_id": "primitive_int",
      "parameters": [{"name": "ptr", "type_id": "pointer_to_primitive_int"}]
    }
  ]
}
```

---

## 6. Implementation Architecture

### 6.1 Class Hierarchy

```
PipelineStage (ABC)
├── NativeInterfaceIngestionStage
├── IRNormalizationStage (NEW)
│   ├── Uses: TypeIDGenerator
│   ├── Uses: TypeRegistry
│   ├── Uses: TypedefResolver
│   └── Uses: TypeNormalizer
...
```

---

## 7. Usage Examples

### 7.1 Running IR Normalization

```bash
python modules/module_02_verification_pipeline/verification_pipeline.py run-incremental \
    --context artifacts/execution_context.json \
    --target ir
```

---

## 8. Next Steps

**** will implement:
- **Contract Synthesis Stage**: Generating formal logic constraints from the Normalized IR.
- Precondition extraction (non-null pointers).
- Buffer size inference.
