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


**Status:** Complete

**Implemented:**
- `GlobalVariableInfo` data structure for complete variable metadata
- `GlobalVariableExtractor` class for variable analysis
- Mutability qualifier extraction (`const`, `volatile`, `restrict`)
- Thread-local storage detection
- Visibility query (`default`, `hidden`, `protected`)
- Size and alignment extraction
- Definition vs declaration detection
- Integration with `ExternalSymbol`

**Tests:** 102 tests total (92 from Prompts 1-7 + 10 new)

**Next Prompt:** Typedef and type alias resolution with complete chain tracking


**Status:** Complete

**Implemented:**
- Typedef resolution chain tracking in `TypeInfo`
- `_extract_typedef_info` logic in `TypeExtractor`
- Mapping type aliases to canonical forms
- Circular typedef detection and protection
- Support for `TYPEDEF_DECL` and C++ `TYPE_ALIAS_DECL`
- Preservation of complete alias chains for diagnostics

**Tests:** 113 tests total (102 from Prompts 1-8 + 11 new)

**Next Prompt:** Macro Definition Extraction


**Status:** Complete

**Implemented:**
- `MacroInfo` data structure for macro metadata
- `MacroExtractor` class for macro analysis
- Object-like macro extraction
- Function-like macro detection
- Platform-specific macro identification
- Builtin/predefined macro detection
- Macro classification (constant, builtin, etc.)
- Integration with `ExternalSymbol` and `ClangFrontend`

**Macro Properties Captured:**
- Macro name and body
- Macro value (for constants)
- Function-like flag and parameters
- Macro type classification
- Source location (file, line)
- Predefined/builtin flags
- Platform-specific markers
- Conditional compilation context

**Tests:** 124 tests total (113 from Prompts 1-9 + 11 new)

**Next Prompt:** Attribute and annotation extraction (packed, aligned, visibility, etc.)


**Status:** Complete

**Implemented:**
- `AttributeInfo` data structure for attribute metadata
- `AttributeExtractor` class for attribute analysis
- Alignment attribute detection
- Deprecated attribute detection
- Attribute impact classification (ABI, visibility, semantics)
- Integration with `ExternalSymbol`
- Quick-access deprecated flags

**Attribute Properties Captured:**
- Attribute kind and syntax
- Attribute arguments
- ABI impact flag
- Visibility impact flag
- Semantic impact flag
- Platform-specific marker
- Deprecation messages

**Tests:** 134 tests total (124 from Prompts 1-10 + 10 new)

**Next Prompt:** Source location tracking and provenance metadata


**Status:** Complete

**Implemented:**
- `SourceLocation` data structure for file/line/column
- `SourceRange` for multi-line declarations
- `ProvenanceInfo` for complete metadata
- `LocationExtractor` for location queries
- Spelling and expansion location support
- System header detection
- Range extraction for multi-line spans
- Integration with `ExternalSymbol`

**Location Properties Captured:**
- File path, line number, column number
- Byte offset in file
- System header flag
- Source ranges (start/end)
- Include chain (basic)
- Header classification
- Expansion locations

**Tests:** 145 tests total (134 from Prompts 1-11 + 11 new)

**Next Prompt:** Diagnostic reporting and error message generation


**Status:** Complete

**Implemented:**
- `Diagnostic` data structure with severity levels
- `IngestionReport` for aggregated diagnostics
- `DiagnosticCollector` for accumulating messages
- Clang diagnostic integration
- Console and JSON output formatting
- Summary statistics and reporting

**Diagnostic Features:**
- Severity levels (fatal, error, warning, info, note)
- Source location tracking
- Explanation, impact, and suggestion fields
- Console and JSON output formats
- Clang diagnostic collection
- Aggregated reporting with statistics

**Tests:** 159 tests total (145 from Prompts 1-12 + 14 new)

**Next Prompt:** Incremental ingestion and caching for performance

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

Status: Complete

Implemented:

- `HeaderMetadata` for change detection
- `IngestionCache` for artifact storage and retrieval
- Change detection (timestamp + hash hybrid)
- Compilation context change detection
- Cache storage and loading
- `IngestionPerformance` metrics
- `IncrementalIngestionOrchestrator`

**Cache Features:**
- Timestamp and hash-based change detection
- Artifact storage with metadata
- Compilation context tracking
- Cache invalidation on context change
- Performance metrics (hit rate, timing)

**Next Prompt:** Validation and consistency checking

---

## Module Structure
