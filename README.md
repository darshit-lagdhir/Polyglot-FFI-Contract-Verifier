# Polyglot FFI Contract Verifier

**From "it compiles" to "it is actually correct" across language boundaries.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-lightgrey.svg)](https://www.microsoft.com/windows)

## Overview

The Polyglot FFI Contract Verifier is a developer-focused verification system designed to make foreign function interface (FFI) boundaries explicit, testable, and explainable. It addresses a critical gap in modern polyglot software development: verifying that assumptions made by one language runtime about another are actually valid at runtime.

## The Problem

Modern software systems are deliberately polyglot, combining multiple programming languages to exploit their individual strengths. However, FFI boundaries remain one of the least rigorously verified layers in software engineering:

- **Code can compile successfully** while silently violating assumptions about memory layout, alignment, ownership, or calling conventions
- **Bugs surface late** under specific workloads, compiler versions, or timing conditions
- **Failures are severe** - undefined behavior, crashes, data corruption, security vulnerabilities
- **Debugging is expensive** - requires deep knowledge of multiple languages, ABIs, and runtime internals

## The Solution

The Polyglot FFI Contract Verifier reframes FFI correctness as a **contract verification problem**:

1. **Extract** the native interface as understood by the compiler
2. **Synthesize** an explicit FFI contract encoding all assumptions
3. **Generate** runtime verification adapters and targeted tests
4. **Execute** verification and detect violations
5. **Report** failures in terms of violated assumptions, not low-level crashes

### Key Features

- ✅ **Explicit Contracts** - Makes implicit FFI assumptions explicit and machine-readable
- ✅ **Deterministic Verification** - Reproducible results across machines and time
- ✅ **Semantic Reporting** - Explains violations in plain language, not ABI jargon
- ✅ **Artifact-Driven** - All intermediate outputs are inspectable and versioned
- ✅ **Incremental Adoption** - Verify individual functions or entire interfaces
- ✅ **CI Integration Ready** - Machine-readable outputs for automated workflows

## What You Get

**Input:**
```c
// interface.h
struct Config {
    int mode;
    void* data;
};

int process(struct Config* cfg);
```

**Outcome:**
- ✅ **Detected** that `struct Config` has 4 bytes of padding between `mode` and `data` on x64.
- ✅ **Verified** that specific language bindings allocate the struct with correct size (16 bytes, not 12).
- ✅ **Confirmed** calling convention is `cdecl` (standard for C).
- ✅ **Generated** report explaining why incorrect struct size would cause a heap corruption crash.

## Current Status

**Phase 1 Complete** ✅ - Execution Context and Orchestration Layer  
**Phase 2 Complete** ✅ - Native Interface Ingestion  
**Phase 3 Complete** ✅ - Intermediate Representation Normalization  
**Phase 4 Complete** ✅ - Contract Synthesis Engine  
**Phase 5 Complete** ✅ - Contract Schema Versioning

The core verification engine and contract management layer are fully implemented and validated.

### Phase 1: Execution Context and Orchestration
- Immutable execution context capturing all environmental details
- Deterministic 8-step context construction process
- Complete CLI with 9 commands for pipeline control
- Error classification and handling framework
- Artifact management and provenance tracking

See [`docs/ORCHESTRATION_IMPLEMENTATION.md`](docs/ORCHESTRATION_IMPLEMENTATION.md) for detailed documentation.

### Phase 2: Native Interface Ingestion
- Compiler-grade ABI extraction using libclang
- Struct layouts with explicit padding detection
- Calling convention detection (cdecl, stdcall, fastcall, win64)
- Complete type information with recursive representation
- Source location tracking for all symbols
- Full provenance metadata linking to ExecutionContext

**Key Features**:
- ✅ libclang integration with Windows/MSVC support
- ✅ Explicit padding fields in struct layouts
- ✅ Platform-aware compilation (Windows x64)
- ✅ Comprehensive error reporting

**Artifacts Produced**:
- `artifacts/native_interface.json` - Complete ABI description

### Phase 3: IR Normalization
- Transformation of native artifacts into canonical, platform-agnostic IR
- Transitive typedef resolution to underlying primitive types
- Deterministic type registry with stable, unique type IDs
- Normalization of struct layouts and function signatures
- Standardized representation of type qualifiers (const, volatile)

See [`docs/IR_NORMALIZATION_IMPLEMENTATION.md`](docs/IR_NORMALIZATION_IMPLEMENTATION.md) for detailed documentation.

### Phase 4: Contract Synthesis Engine
- Transformation of structural IR into semantic correctness constraints
- Rule-based constraint derivation (nullability, ownership, lifetime)
- Heuristic naming convention analysis (create_, optional_, etc.)
- Conservative default policies for safety-first verification
- Deterministic constraint ID generation for traceability
- Support for buffer-length relationship detection

**Artifacts Produced**:
- `artifacts/contract.json` - Formal FFI contract

See [`docs/CONTRACT_SYNTHESIS_IMPLEMENTATION.md`](docs/CONTRACT_SYNTHESIS_IMPLEMENTATION.md) for detailed documentation.

### Phase 5: Contract Schema Versioning
- Semantic versioning (MAJOR.MINOR.PATCH) for contract artifacts
- Precise contract comparison and diffing (baseline vs. current)
- Automated compatibility assessment (Breaking, Semantic, Compatible)
- Human-readable compatibility reports with action recommendations
- Traceability of ABI changes across native library versions

**Artifacts Produced**:
- `artifacts/contract_diff.json` - ABI change diff
- `artifacts/compatibility_report.txt` - Human-readable assessment

See [`docs/CONTRACT_VERSIONING_IMPLEMENTATION.md`](docs/CONTRACT_VERSIONING_IMPLEMENTATION.md) for detailed documentation.

## Quick Start

### Prerequisites

- **Windows x64** (v1.0 requirement)
- **Python 3.11+**
- **MSVC compiler** (Visual Studio)
- **libclang** (for native interface ingestion)

### Installation

```bash
# Clone repository
git clone https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier.git
cd Polyglot-FFI-Contract-Verifier

# Install dependencies
pip install libclang

# Note: You may need to set LIBCLANG_PATH environment variable if libclang is not in your PATH
# Example: set LIBCLANG_PATH=C:\Program Files\LLVM\bin\libclang.dll
```

### Basic Usage

```bash
# Full verification pipeline (when implemented)
python polyglot_ffi_verifier.py verify interface.h library.dll

# Individual stage execution
python polyglot_ffi_verifier.py ingest interface.h library.dll
python polyglot_ffi_verifier.py synthesize
python polyglot_ffi_verifier.py generate-tests

# Display execution context
python polyglot_ffi_verifier.py context

# Validate implementations
python validate_orchestration.py       # Phase 1
python validate_ingestion.py           # Phase 2
python validate_ir_normalization.py    # Phase 3
python validate_contract_synthesis.py  # Phase 4
python validate_contract_versioning.py # Phase 5
```

## Architecture

The system is organized as a deterministic, artifact-driven pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Execution Context                            │
│  (Immutable environmental state for all stages)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Native Interface Ingestion                            │
│  Input:  C header, library                                      │
│  Output: Native Interface Artifact (native_interface.json)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: IR Normalization                                      │
│  Input:  Native Interface Artifact                              │
│  Output: Intermediate Representation (IR)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Contract Synthesis                                    │
│  Input:  Intermediate Representation                            │
│  Output: FFI Contract                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: Contract Schema Versioning                           │
│  Input:  FFI Contract, (Baseline Contract)                      │
│  Output: Diff Artifact, Compatibility Report                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 5: Language Adapter Generation                           │
│  Input:  FFI Contract                                           │
│  Output: Runtime Verification Adapters                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 6: Test Plan Generation                                  │
│  Input:  FFI Contract                                           │
│  Output: Test Plan                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 7: Verification Execution                                │
│  Input:  Adapters, Test Plan                                   │
│  Output: Execution Log                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 8: Diagnostics Mapping                                   │
│  Input:  Execution Log, Contract                                │
│  Output: Diagnostics Artifact                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 9: Report Generation                                     │
│  Input:  Diagnostics                                            │
│  Output: Human-Readable Report                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
Polyglot-FFI-Contract-Verifier/
├── src/
│   ├── core/                       # Phase 1: Orchestration & context
│   ├── ingestion/                  # Phase 2: Native interface ingestion
│   ├── representation/             # Phase 3: IR normalization
│   ├── synthesis/                  # Phase 4: Contract synthesis
│   ├── contract/                   # Phase 5: Contract schema versioning
│   └── ...                         # Additional phases
├── docs/
│   ├── ORCHESTRATION_IMPLEMENTATION.md
│   ├── INGESTION_IMPLEMENTATION.md
│   ├── IR_NORMALIZATION_IMPLEMENTATION.md
│   ├── CONTRACT_SYNTHESIS_IMPLEMENTATION.md
│   └── CONTRACT_VERSIONING_IMPLEMENTATION.md
├── polyglot_ffi_verifier.py        # Main entry point
├── validate_orchestration.py       # Phase 1 validation
├── validate_ingestion.py           # Phase 2 validation
├── validate_ir_normalization.py    # Phase 3 validation
├── validate_contract_synthesis.py  # Phase 4 validation
├── validate_contract_versioning.py # Phase 5 validation
├── quick_test.py                   # Quick smoke test
└── README.md                       # This file
```

## Development Roadmap

### ✅ Completed
- **Phase 1**: Execution Context and Orchestration Layer
- **Phase 2**: Native Interface Ingestion
- **Phase 3**: Intermediate Representation Normalization
- **Phase 4**: Contract Synthesis Engine
- **Phase 5**: Contract Schema Versioning

### 🔄 In Progress
- **Phase 6**: Language Adapter Generation (Python)

### 📋 Planned
- **Phase 7**: Test Plan Generation
- **Phase 8**: Verification Engine Execution
- **Phase 9**: Runtime Monitoring & Crash Handling
- **Phase 10**: Diagnostics Mapping
- **Phase 11**: Reporting (Human-Readable)
- **Phase 12**: Machine-Readable Output & CI Integration
- **Phase 13**: Cross-Cutting Concerns
- **Phase 14**: End-to-End Integration
- **Phase 15**: Final Polish & Documentation

## Architectural Principles

1. **Immutability** - Once created, artifacts are never modified
2. **Explicitness** - No implicit assumptions or hidden behavior
3. **Determinism** - Identical inputs produce identical outputs
4. **Artifact-Driven** - All communication through explicit artifacts
5. **Failure Isolation** - Errors classified and handled appropriately
6. **Partial Execution** - Individual stages can be invoked independently
7. **Provenance Tracking** - Full traceability from inputs to outputs

## Documentation

- **[Orchestration Implementation](docs/ORCHESTRATION_IMPLEMENTATION.md)** - Phase 1 detailed documentation
- **[Ingestion Implementation](docs/INGESTION_IMPLEMENTATION.md)** - Phase 2 detailed documentation

## Contributing

This project is being developed as part of the AMD Slingshot Hackathon following a structured 15-phase implementation plan. Each phase builds on previous work while maintaining clear boundaries and testability.

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - See [LICENSE](LICENSE) file for details

## Acknowledgments

- Developed for the **AMD Slingshot Hackathon 2026**
- Inspired by the need for rigorous FFI verification in polyglot systems

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Status**: Phase 5 Complete ✅ | **Next**: Phase 6 - Language Adapter Generation
