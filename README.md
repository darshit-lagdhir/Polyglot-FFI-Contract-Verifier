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

## Current Status

**Phase 1 Complete** ✅ - Execution Context and Orchestration Layer

The foundational orchestration and execution context subsystem is fully implemented and validated. This provides:

- Immutable execution context capturing all environmental details
- Deterministic 8-step context construction process
- Complete CLI with 9 commands for pipeline control
- Error classification and handling framework
- Artifact management and provenance tracking

See [`docs/ORCHESTRATION_IMPLEMENTATION.md`](docs/ORCHESTRATION_IMPLEMENTATION.md) for detailed documentation.

## Quick Start

### Prerequisites

- **Windows x64** (v1.0 requirement)
- **Python 3.11+**
- **MSVC compiler** (Visual Studio)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/Polyglot-FFI-Contract-Verifier.git
cd Polyglot-FFI-Contract-Verifier

# No additional dependencies required for Phase 1
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

# Validate implementation
python validate_orchestration.py
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
│  Output: Intermediate Representation (IR)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Contract Synthesis                                    │
│  Input:  Intermediate Representation                            │
│  Output: FFI Contract                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Language Adapter Generation                           │
│  Input:  FFI Contract                                           │
│  Output: Runtime Verification Adapters                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: Test Generation                                       │
│  Input:  FFI Contract                                           │
│  Output: Test Plan                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 5: Verification Execution                                │
│  Input:  Adapters, Test Plan                                   │
│  Output: Execution Log                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 6: Diagnostics Mapping                                   │
│  Input:  Execution Log, Contract                                │
│  Output: Diagnostics Report                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 7: Report Generation                                     │
│  Input:  Diagnostics                                            │
│  Output: Human-Readable Report                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
Polyglot-FFI-Contract-Verifier/
├── src/
│   ├── core/
│   │   ├── execution_context.py    # ExecutionContext and Builder
│   │   └── orchestration.py        # Pipeline orchestration and CLI
│   └── stages/                     # Pipeline stage implementations (future)
├── docs/
│   └── ORCHESTRATION_IMPLEMENTATION.md   # Detailed implementation docs
├── polyglot_ffi_verifier.py              # Main entry point
├── validate_orchestration.py             # Validation suite
├── quick_test.py                         # Quick smoke test
└── README.md                             # This file
```

## Development Roadmap

### ✅ Completed
- **Phase 1**: Execution Context and Orchestration Layer

### 🔄 In Progress
- **Phase 2**: Native Interface Ingestion

### 📋 Planned
- **Phase 3**: Intermediate Representation
- **Phase 4**: Contract Synthesis
- **Phase 5**: Language Adapter Generation
- **Phase 6**: Test Generation
- **Phase 7**: Verification Execution
- **Phase 8**: Diagnostics Mapping
- **Phase 9**: Report Generation
- **Phases 10-15**: Advanced features and extensions

## Architectural Principles

1. **Immutability** - Once created, artifacts are never modified
2. **Explicitness** - No implicit assumptions or hidden behavior
3. **Determinism** - Identical inputs produce identical outputs
4. **Artifact-Driven** - All communication through explicit artifacts
5. **Failure Isolation** - Errors classified and handled appropriately
6. **Partial Execution** - Individual stages can be invoked independently
7. **Provenance Tracking** - Full traceability from inputs to outputs

## Documentation

- **[Orchestration Implementation](docs/ORCHESTRATION_IMPLEMENTATION.md)** - Detailed Phase 1 documentation

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

**Status**: Phase 1 Complete ✅ | **Next**: Phase 2 - Native Interface Ingestion