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

**Tests:** 18 tests (all passing)

**Next Prompt:** Clang frontend integration via libclang


**Status:** Complete

**Implemented:**
- libclang C API bindings (minimal subset for AST traversal)
- `ClangFrontend` class implementing `CompilerFrontend` interface
- AST traversal via `clang_visitChildren`
- External symbol extraction based on linkage
- Compilation context to Clang arguments translation
- Resource management (index and translation unit disposal)

**Key Classes:**
- `ClangFrontend`: Clang integration via libclang
- `ClangCompilationUnit`: Clang-specific compilation unit wrapper
- `SourceLocation`: Source code location tracking
- Enhanced `ExternalSymbol`: Added source location, linkage, type metadata

**libclang Integration:**
- Index creation and disposal
- Translation unit parsing with context
- AST cursor traversal
- Symbol name and linkage extraction
- Command-line argument construction

**Tests:** 28 tests total (18 from  + 10 new)

**Next Prompt:** Type information extraction and canonicalization


**Status:** Complete

**Implemented:**
- Complete `TypeInfo` data structure with ABI properties
- `TypeExtractor` class for comprehensive type queries
- Type classification system (primitive, pointer, array, record, function, enum)
- Type canonicalization (typedef resolution)
- Size and alignment extraction
- Pointer depth and pointee type queries
- Array element type and size queries
- Function return/parameter type extraction
- Calling convention detection
- Type qualifier extraction (const, volatile, restrict)

**Type Categories Supported:**
- **Primitives**: int, float, char, bool, etc.
- **Pointers**: T*, T**, etc. with depth tracking
- **Arrays**: T[N], T[] with element type
- **Functions**: return_type(params...) with calling convention
- **Records**: struct/union (basic identification)
- **Enums**: with underlying type
- **Typedefs**: with canonical resolution

**Tests:** 38 tests total (27 from Prompts 1-2 + 11 new)

**Next Prompt:** Structure and union field extraction with offset calculation


**Status:** Complete

**Implemented:**
- `FieldInfo` data structure for field metadata
- `PaddingInfo` data structure for padding regions
- `RecordLayout` data structure for complete struct/union layout
- `RecordLayoutExtractor` class for field enumeration and offset calculation
- Padding detection (inter-field and trailing)
- Nested structure handling
- Anonymous struct/union detection
- Integration with `TypeInfo`

**Key Features:**
- **Exact byte offset calculation** via Clang
- **Field type resolution** with complete `TypeInfo`
- **Automatic padding detection** and classification
- **Support for both structures and unions**
- **Bitfield detection** (basic, full handling in )

**Layout Properties Captured:**
- Field names, types, offsets, sizes, alignments
- Structure/union total size and alignment
- Inter-field padding regions
- Trailing padding
- Packed structure detection (basic)
- Anonymous record handling
- Nested structure support

**Tests:** 51 tests total (38 from Prompts 1-3 + 13 new)

**Next Prompt:** Bitfield extraction with bit-precise offset and width calculation


**Status:** Complete

**Implemented:**
- Bit-precise offset calculation for bitfields
- Bit-width detection
- Packing analysis
- Integration with `FieldInfo`

**Tests:** 65 tests total (51 from Prompts 1-4 + 14 new)

**Next Prompt:** Enum extraction with enumerator values and underlying type detection


**Status:** Complete

**Implemented:**
- `EnumeratorInfo` data structure for enum constants
- `EnumExtractor` class for comprehensive enum analysis
- Enumerator value extraction (signed and unsigned)
- Underlying type detection and signedness analysis
- Value range computation (min, max)
- Bitmask pattern detection
- Sequential pattern detection
- Integration with `TypeInfo`

**Tests:** 79 tests total (65 from Prompts 1-5 + 14 new)

**Next Prompt:** Function signature extraction with parameter names, calling conventions, and variadic detection


**Status:** Complete

**Implemented:**
- `ParameterInfo` data structure for function parameters
- `FunctionSignature` data structure for complete signatures
- `FunctionSignatureExtractor` class for signature analysis
- Parameter extraction with names and types
- Calling convention detection (cdecl, stdcall, win64, etc.)
- Variadic function detection
- Return type analysis
- Language linkage detection (C vs C++)
- Integration with `ExternalSymbol`

**Tests:** 92 tests total (79 from Prompts 1-6 + 13 new)

**Next Prompt:** Global variable extraction with size, alignment, and mutability analysis

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

**Module Status:** 🏗️ IN PROGRESS (7/20 components complete)  
**Next Milestone:** Global variable extraction with size, alignment, and mutability analysis
