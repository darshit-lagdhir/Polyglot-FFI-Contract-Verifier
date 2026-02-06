# Module 04: Native Interface Ingestion

**Ground-Truth Interface Extraction via Compiler Interrogation**

## Overview

Native interface ingestion is the foundational stage of the Polyglot FFI Contract Verifier that establishes the absolute ground truth of what a compiler believes an external interface to be. Every subsequent stage depends entirely on the fidelity and completeness of ingestion.

## Core Philosophy

### Compiler Reality as Single Source of Truth

Source code is not the interface. Headers are not the interface. Comments and documentation are not the interface. **The interface is the compiler's view of externally visible symbols, types, and calling conventions after all compilation context has been applied.**

### Architectural Principles

1. **Compiler Reality**: Operate at compiler-grade precision, not textual parsing
2. **Environment Fidelity**: Respect compilation context (flags, macros, target triple)
3. **Lossless Extraction**: Preserve all ABI-relevant information
4. **Non-Interpretation**: Record facts, never infer semantics
5. **Determinism**: Identical inputs → identical artifacts

## Implementation Progress


**Status:** Complete

**Implemented:**
- Core data structures (CompilationContext, RawInterfaceArtifact)
- Compiler frontend abstraction layer (CompilerFrontend base class)
- Error taxonomy (IngestionError hierarchy)
- Artifact serialization and persistence
- Module metadata and versioning

**Key Classes:**
- `CompilationContext`: Explicit compilation environment specification
- `RawInterfaceArtifact`: Primary ingestion output artifact
- `CompilerFrontend`: Abstract base for compiler integrations
- `ExternalSymbol`: Symbol representation (stub)
- `TypeInfo`: Type information (stub)

**Design Principles Enforced:**
- Compiler reality as single source of truth
- Environment fidelity through explicit contexts
- Lossless information preservation
- Zero semantic interpretation
- Deterministic and reproducible outputs

**Files Modified:**
- `native_interface_ingestion.py`: ~350 lines (foundation)
- `NATIVE_INTERFACE_INGESTION.md`: Implementation progress section added

**Tests:** 21 unit tests (all passing)

**Next Prompt:** Clang frontend integration via libclang

---

## Module Structure

```
module_04_native_interface_ingestion/
├── native_interface_ingestion.py    # Core implementation
└── NATIVE_INTERFACE_INGESTION.md    # This file
```

## Integration Points

- **Input**: Source headers, compilation context
- **Output**: Raw interface artifact (for IR normalization stage)
- **Dependencies**: None (foundational stage)

## Key Invariants

1. **No Partial Ingestion**: Complete or fail, never partial
2. **No Semantic Inference**: Facts only, no assumptions
3. **No Normalization**: Preserve compiler representation exactly
4. **Deterministic Output**: Stable traversal order, serialization
5. **Validation is Mandatory**: Extraction without validation = false certainty

---

**Module Status:** 🏗️ IN PROGRESS (1/20 components complete)  
**Next Milestone:** Clang/libclang integration for C/C++ header parsing
