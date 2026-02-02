# Polyglot FFI Contract Verifier
## Complete System Architecture and Technical Specification

**Version:** 1.0.0  
**Author:** Darshit Lagdhir  
**Date:** 2026-02-02  
**License:** MIT

---

## Document Overview

This document provides a complete technical specification for the Polyglot FFI
Contract Verifier, consolidating all implementation documentation, operational
guides, and architectural decisions into a single comprehensive reference.

**Document Statistics:**
- Total Sections: 50+
- Source Documents: 19
- Consolidated: 2026-02-02

**Reading Guide:**
- For quick overview: Read  (System Overview)
- For implementation details: Read  (Phase Implementations)
- For operational use: Read  (Operational Guides)
- For integration: Read  (Integration)

---

## Table of Contents

1. [SYSTEM OVERVIEW](#1-system-overview)
2. [PIPELINE ARCHITECTURE](#2-pipeline-architecture)
3. [PHASE IMPLEMENTATIONS](#3-phase-implementations)
   - 3.1 [: Execution Context & Orchestration](#31-phase-1-execution-context--orchestration)
   - 3.2 [: Native Interface Ingestion](#32-phase-2-native-interface-ingestion)
   - 3.3 [: IR Normalization](#33-phase-3-ir-normalization)
   - 3.4 [: Contract Synthesis](#34-phase-4-contract-synthesis)
   - 3.5 [: Contract Versioning](#35-phase-5-contract-versioning)
   - 3.6 [: Adapter Generation](#36-phase-6-adapter-generation)
   - 3.7 [: Test Plan Generation](#37-phase-7-test-plan-generation)
   - 3.8 [: Verification Execution](#38-phase-8-verification-execution)
   - 3.9 [: Runtime Monitoring](#39-phase-9-runtime-monitoring)
   - 3.10 [0: Diagnostics Mapping](#310-phase-10-diagnostics-mapping)
   - 3.11 [1: Report Generation](#311-phase-11-report-generation)
   - 3.12 [2: CI/CD Integration](#312-phase-12-cicd-integration)
4. [OPERATIONAL GUIDES](#4-operational-guides)
   - 4.1 [Performance Considerations](#41-performance-considerations)
   - 4.2 [Security Considerations](#42-security-considerations)
   - 4.3 [Limitations and Non-Goals](#43-limitations-and-non-goals)
   - 4.4 [Error Handling Patterns](#44-error-handling-patterns)
   - 4.5 [Logging Strategy](#45-logging-strategy)
   - 4.6 [Best Practices](#46-best-practices)
5. [INTEGRATION](#5-integration)
   - 5.1 [CI/CD Integration](#51-cicd-integration)
   - 5.2 [End-to-End Validation](#52-end-to-end-validation)
6. [APPENDICES](#6-appendices)

---

---

## 2 PIPELINE ARCHITECTURE

The Polyglot FFI Contract Verifier is organized as a deterministic, artifact-driven pipeline:

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
                          [Continue through all 12 phases...]
```

### Key Architectural Principles

1. **Immutability** - Once created, artifacts are never modified
2. **Explicitness** - No implicit assumptions or hidden behavior
3. **Determinism** - Identical inputs produce identical outputs
4. **Artifact-Driven** - All communication through explicit artifacts
5. **Failure Isolation** - Errors classified and handled appropriately
6. **Partial Execution** - Individual stages can be invoked independently
7. **Provenance Tracking** - Full traceability from inputs to outputs

---

## 3 PHASE IMPLEMENTATIONS

### 1. SYSTEM OVERVIEW

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

**** ✅ - Execution Context and Orchestration Layer  
**** ✅ - Native Interface Ingestion  
**** ✅ - Intermediate Representation Normalization  
**** ✅ - Contract Synthesis Engine  
**** ✅ - Contract Schema Versioning  
**** ✅ - Language Adapter Generation (Python)  
**** ✅ - Test Plan Generation  
**** ✅ - Verification Execution

The core verification engine, contract management, and active execution layers are fully implemented and validated.

### : Execution Context and Orchestration
- Immutable execution context capturing all environmental details
- Deterministic 8-step context construction process
- Complete CLI with 9 commands for pipeline control
- Error classification and handling framework
- Artifact management and provenance tracking

See [`docs/ORCHESTRATION_IMPLEMENTATION.md`](docs/ORCHESTRATION_IMPLEMENTATION.md) for detailed documentation.

### : Native Interface Ingestion
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

### : IR Normalization
- Transformation of native artifacts into canonical, platform-agnostic IR
- Transitive typedef resolution to underlying primitive types
- Deterministic type registry with stable, unique type IDs
- Normalization of struct layouts and function signatures
- Standardized representation of type qualifiers (const, volatile)

See [`docs/IR_NORMALIZATION_IMPLEMENTATION.md`](docs/IR_NORMALIZATION_IMPLEMENTATION.md) for detailed documentation.

### : Contract Synthesis Engine
- Transformation of structural IR into semantic correctness constraints
- Rule-based constraint derivation (nullability, ownership, lifetime)
- Heuristic naming convention analysis (create_, optional_, etc.)
- Conservative default policies for safety-first verification
- Deterministic constraint ID generation for traceability
- Support for buffer-length relationship detection

**Artifacts Produced**:
- `artifacts/contract.json` - Formal FFI contract

See [`docs/CONTRACT_SYNTHESIS_IMPLEMENTATION.md`](docs/CONTRACT_SYNTHESIS_IMPLEMENTATION.md) for detailed documentation.

### : Contract Schema Versioning
- Semantic versioning (MAJOR.MINOR.PATCH) for contract artifacts
- Precise contract comparison and diffing (baseline vs. current)
- Automated compatibility assessment (Breaking, Semantic, Compatible)
- Human-readable compatibility reports with action recommendations
- Traceability of ABI changes across native library versions

**Artifacts Produced**:
- `artifacts/contract_diff.json` - ABI change diff
- `artifacts/compatibility_report.txt` - Human-readable assessment

See [`docs/CONTRACT_VERSIONING_IMPLEMENTATION.md`](docs/CONTRACT_VERSIONING_IMPLEMENTATION.md) for detailed documentation.

### : Language Adapter Generation (Python)
- Automatic generation of contract-enforcing `ctypes` wrappers
- Runtime enforcement of nullability, buffer sizes, and alignment
- Struct definitions with explicit padding and memory layout validation
- Ownership tracking (borrowed vs. transferred) to detect memory leaks and use-after-free
- Precise, contract-referencing exception hierarchy

**Artifacts Produced**:
- `adapters/<lib>_adapter.py` - Function wrappers
- `adapters/<lib>_structs.py` - Validated struct definitions
- `adapters/adapter_metadata.json` - Generation metadata

See [`docs/ADAPTER_GENERATION_IMPLEMENTATION.md`](docs/ADAPTER_GENERATION_IMPLEMENTATION.md) for detailed documentation.

### : Test Plan Generation
- Systematic derivation of positive, negative, and boundary test cases
- 100% constraint coverage tracking and mapping
- Deterministic input value generation for all FFI types
- Fault injection strategy (violating exactly one constraint per test)
- Structured, declarative test specification (`test_plan.json`)

**Artifacts Produced**:
- `artifacts/test_plan.json` - Complete test specification
- `artifacts/test_coverage.json` - Coverage analysis report

See [`docs/TEST_PLAN_GENERATION_IMPLEMENTATION.md`](docs/TEST_PLAN_GENERATION_IMPLEMENTATION.md) for detailed documentation.

### : Verification Execution
- Active execution of structured test plans using generated adapters
- Robust input instantiation (primitives, pointers, structs, buffers)
- Precise outcome validation (success vs. expected contract violations)
- Immutable, append-only execution logging with detailed audit trails
- Automated generation of human-readable execution summaries

**Artifacts Produced**:
- `artifacts/execution_log.json` - Complete test results
- `artifacts/execution_summary.txt` - Human-readable report

See [`docs/VERIFICATION_EXECUTION_IMPLEMENTATION.md`](docs/VERIFICATION_EXECUTION_IMPLEMENTATION.md) for detailed documentation.

### : Runtime Monitoring and Crash Detection
- Subprocess-based isolation (crashes don't terminate the verifier)
- Platform-specific failure detection (Windows SEH, Linux Signals)
- Heuristic classification of memory safety violations (Null deref, Buffer overflow)
- Detailed crash context capture (address, registers, timing)
- Automated crash report generation and execution log augmentation

**Artifacts Produced**:
- `artifacts/crashes/` - Directory of detailed crash reports
- `artifacts/execution_log.json` - Augmented with crash diagnostics

See [`docs/RUNTIME_MONITORING_IMPLEMENTATION.md`](docs/RUNTIME_MONITORING_IMPLEMENTATION.md) for detailed documentation.

### 0: Diagnostics Mapping and Failure Classification
- Automatic categorization of failures (buffer overflow, null pointer, etc.)
- Severity assessment and exploitability analysis
- Traceability from raw crashes to specific contract constraints
- Aggregation of related violations to reduce reporting noise
- Actionable remediation recommendations with code snippets

**Artifacts Produced**:
- `artifacts/diagnostics.json` - Machine-readable diagnostics
- `artifacts/violation_summary.txt` - Human-readable summary

See [`docs/DIAGNOSTICS_MAPPING_IMPLEMENTATION.md`](docs/DIAGNOSTICS_MAPPING_IMPLEMENTATION.md) for detailed documentation.

### 1: Comprehensive Report Generation
- Professional, stakeholder-ready reports in HTML, Markdown, and CI Summary (JSON)
- Visual hierarchy with color-coded severity badges and card-based layout
- Prioritized violations with detailed RCA and remediation steps
- Machine-readable CI integration with exit codes and status badge metadata
- Self-contained HTML reports with inline CSS

**Artifacts Produced**:
- `reports/verification_report.html` - Primary visual report
- `reports/verification_report.md` - Version-control friendly report
- `reports/ci_summary.json` - CI/CD pipeline data

See [`docs/REPORT_GENERATION_IMPLEMENTATION.md`](docs/REPORT_GENERATION_IMPLEMENTATION.md) for detailed documentation.

### 2: CI/CD Integration
- Turnkey workflow templates for GitHub Actions, GitLab CI, and Jenkins
- Automated failure gating based on contract violation severity
- Dynamic status badge generation (shields.io compatible)
- Machine-readable configuration via YAML and environment variables
- Automated artifact collection (reports, logs, diagnostics)

**Key Integration Scripts**:
- `scripts/check_ci_status.py` - Intelligent failure gating for pipelines
- `scripts/generate_badge.py` - Visual status metadata generation

See [`docs/CI_INTEGRATION.md`](docs/CI_INTEGRATION.md) for complete setup guides.

## Quick Start

### Requirements

- **Windows x64** (v1.0 requirement)
- **Python 3.11+**
- **MSVC compiler** (IDE)
- **libclang** (for native interface ingestion)

### Install

```bash
# Clone repository
git clone https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier.git
cd Polyglot-FFI-Contract-Verifier

# Install the package
pip install -e .

# Verify installation
polyglot-ffi-verifier --version

# Important: You may need to set LIBCLANG_PATH environment variable:
# Windows
set LIBCLANG_PATH=C:\Program Files\LLVM\bin\libclang.dll

# Linux/Mac
export LIBCLANG_PATH=/usr/lib/llvm-16/lib/libclang.so
```

### Basic Usage

```bash
# Full verification pipeline
polyglot-ffi-verifier verify interface.h library.dll

# Or using Python module
python -m polyglot_ffi_verifier verify interface.h library.dll

# Individual stage execution
polyglot-ffi-verifier ingest interface.h library.dll
polyglot-ffi-verifier synthesize
polyglot-ffi-verifier generate-tests

# Display execution context
polyglot-ffi-verifier context

# Run tests
pytest tests/ -v

# Or run individual tests
python tests/test_ingestion.py
python tests/test_synthesis.py
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
│  Stage 5: Language Adapter Generation ()                 │
│  Input:  FFI Contract                                           │
│  Output: Runtime Verification Adapters                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 6: Test Plan Generation ()                        │
│  Input:  FFI Contract                                           │
│  Output: Test Plan & Coverage Map                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 7: Verification Execution ()                      │
│  Input:  Test Plan & Adapters                                   │
│  Output: Execution Log & Summary                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 8: Runtime Monitoring ()                          │
│  Input:  Active Execution                                       │
│  Output: Crash Reports & Logs                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 9: Diagnostics & Reporting (Phases 10-11)                │
│  Input:  Execution Log                                          │
│  Output: Final Verification Report                              │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
Polyglot-FFI-Contract-Verifier/
├── polyglot_ffi_verifier/     # Main package
│   ├── __init__.py            # Package API
│   ├── __main__.py            # CLI entry point
│   ├── context.py             # Execution context
│   ├── pipeline.py            # Pipeline orchestration
│   ├── ingestion.py           # : Native interface ingestion
│   ├── normalization.py       # : IR normalization
│   ├── synthesis.py           # : Contract synthesis
│   ├── versioning.py          # : Contract versioning
│   ├── adapters.py            # : Adapter generation
│   ├── test_planning.py       # : Test plan generation
│   ├── execution.py           # : Verification execution
│   ├── subprocess_runner.py   # : Crash detection
│   ├── diagnosis.py           # 0: Diagnostics mapping
│   └── reporting.py           # 1: Report generation
├── tests/                     # Test suite
│   ├── test_orchestration.py
│   ├── test_ingestion.py
│   ├── test_normalization.py
│   ├── test_synthesis.py
│   ├── test_versioning.py
│   ├── test_adapters.py
│   ├── test_test_planning.py
│   ├── test_execution.py
│   ├── test_monitoring.py
│   ├── test_diagnosis.py
│   ├── test_reporting.py
│   ├── test_ci.py
│   ├── test_cross_cutting.py
│   ├── test_end_to_end_integration.py
│   ├── test_quick_smoke.py
│   ├── integration/
│   │   └── test_end_to_end.py
│   └── regression/
│       └── test_system_stability.py
├── docs/                      # Documentation
│   ├── architecture/          # System design
│   ├── implementation/        # Implementation details
│   ├── api/                   # API reference
│   └── operations/            # Operational guides
├── examples/                  # Usage
│   └── demo/
│       ├── run_demo.py
│       ├── interface.h
│       └── library.c
├── scripts/                   # Utility scripts
├── configs/                   # Config files
├── .github/                   # GitHub Actions
├── setup.py                   # Install script
├── pyproject.toml             # Project configuration
├── requirements.txt           # Dependencies
├── requirements-dev.txt       # Dev dependencies
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guide
├── README.md                  # This file
├── LICENSE                    # MIT License
├── BENCHMARKS.md              # Performance data
└── .gitignore                 # Git ignore rules
```

## Development Roadmap

### ✅ Completed
- [x] **: Orchestration & Infrastructure** - Functional
- [x] **: Native Interface Ingestion** - Functional
- [x] **: IR Normalization** - Functional
- [x] **: Contract Synthesis** - Functional
- [x] **: Contract Schema Versioning** - Functional
- [x] **: Language Adapter Generation** - Functional
- [x] **: Test Plan Generation** - Functional
- [x] **: Verification Execution** - Functional
- [x] **: Runtime Monitoring & Crash Detection** - Functional
- [x] **0: Diagnostics Mapping** - Functional
- [x] **1: Report Generation** - Functional
- [x] **2: CI/CD Integration** - Functional
- [x] **3: Cross-Cutting Concerns** - Documented
- [ ] **4: End-to-End Integration** - Planned

### 🔄 In Progress

### 📋 Planned
- **5**: Final Polish & Documentation

## System Characteristics

### Performance
- Suitable for development-time and CI verification
- Typical verification time: 10 seconds to 5 minutes depending on interface size
- See `docs/PERFORMANCE_CONSIDERATIONS.md` for details

### Security
- Designed for trusted development environments
- Native code runs with full privileges (no sandboxing)
- See `docs/SECURITY_CONSIDERATIONS.md` for threat model

### Limitations
- Windows x64 only (v1.0)
- C interfaces only (C++ via extern "C")
- Python adapters only (v1.0)
- See `docs/LIMITATIONS_AND_NON_GOALS.md` for complete list
- **5**: Final Polish & Documentation

## Architectural Principles

1. **Immutability** - Once created, artifacts are never modified
2. **Explicitness** - No implicit assumptions or hidden behavior
3. **Determinism** - Identical inputs produce identical outputs
4. **Artifact-Driven** - All communication through explicit artifacts
5. **Failure Isolation** - Errors classified and handled appropriately
6. **Partial Execution** - Individual stages can be invoked independently
7. **Provenance Tracking** - Full traceability from inputs to outputs

## Documentation

- **[Orchestration Implementation](docs/ORCHESTRATION_IMPLEMENTATION.md)** -  detailed documentation
- **[Ingestion Implementation](docs/INGESTION_IMPLEMENTATION.md)** -  detailed documentation

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

**Status**: 4 Complete ✅ | **Next**: 5 - Final Documentation

### 3.1 : Execution Context & Orchestration

## Overview

This document describes the implementation of ****: Execution Context and Orchestration Layer for the Polyglot FFI Contract Verifier.

## Implementation Status

✅ **COMPLETE** - All requirements from  have been implemented and validated.

## Components Implemented

### 1. ExecutionContext Data Structure (`src/core/execution_context.py`)

The `ExecutionContext` is an immutable, frozen dataclass that captures all environment-specific details relevant to FFI correctness verification.

#### Structure (7 Required Field Categories)

1. **PlatformIdentification**
   - `os_name`: Operating system name (e.g., "Windows")
   - `os_version`: OS version string
   - `architecture`: CPU architecture (e.g., "AMD64", "x86_64")
   - `pointer_width`: Pointer width in bits (32 or 64)
   - `endianness`: Byte order ("little" or "big")

2. **CompilerInformation**
   - `compiler_name`: Compiler name (e.g., "MSVC")
   - `compiler_version`: Compiler version string
   - `compiler_flags`: List of compiler flags
   - `include_paths`: Ordered list of include search paths
   - `preprocessor_macros`: Dictionary of preprocessor macro definitions
   - `standard_library_version`: Optional standard library version

3. **NativeLibraryInformation**
   - `library_path`: Absolute path to native library (DLL/SO/DYLIB)
   - `library_hash`: SHA-256 hash of library binary
   - `library_load_paths`: DLL search paths (Windows-specific)
   - `additional_dependencies`: List of additional required libraries

4. **TargetLanguageRuntime**
   - `language_name`: Target language (e.g., "Python")
   - `language_version`: Language version string
   - `ffi_mechanism`: FFI mechanism used ("ctypes" or "cffi")
   - `runtime_path`: Absolute path to interpreter
   - `runtime_config`: Runtime-specific configuration dictionary

5. **VerificationConfig**
   - `random_seed`: Deterministic random seed for test generation
   - `per_test_timeout_seconds`: Timeout per individual test
   - `total_timeout_seconds`: Total verification timeout
   - `crash_handling_mode`: Crash handling mode ("monitor" or "fail-fast")
   - `verbosity_level`: Output verbosity ("quiet", "normal", "verbose")

6. **ProvenanceMetadata**
   - `schema_version`: Execution context schema version (currently "1.0.0")
   - `creation_timestamp`: ISO 8601 timestamp in UTC
   - `execution_id`: UUID v4 for unique execution identification
   - `tool_version`: Verifier tool version (currently "1.0.0")

7. **ArtifactPaths**
   - `working_directory`: Absolute path to working directory
   - `intermediate_representation_path`: Path to IR artifact
   - `contract_path`: Path to contract artifact
   - `test_plan_path`: Path to test plan artifact
   - `execution_log_path`: Path to execution log
   - `diagnostics_path`: Path to diagnostics output
   - `report_path`: Path to final report
   - `execution_context_path`: Path to serialized context

### 2. ExecutionContextBuilder

The builder implements the deterministic 8-step construction process:

#### : Platform Detection
- Queries OS name, version, and architecture using `platform` module
- Determines pointer width from `sys.maxsize`
- Determines endianness from `sys.byteorder`
- **Validates platform support** (v1.0 requires Windows x64)

#### : Compiler and Tooling Resolution
- Auto-detects MSVC compiler on Windows if not specified
- Queries compiler version by invoking with version flags
- Resolves include paths to absolute paths
- Collects preprocessor macros from user input and platform defaults

#### : Native Library Validation
- Resolves library path to absolute path
- Computes SHA-256 hash of library file for identity verification
- Determines library load paths following Windows DLL search order
- Validates library file exists and is readable

#### : Target Language Runtime Resolution
- Auto-detects Python interpreter from `sys.executable` if not specified
- Queries Python version by invoking interpreter with `--version`
- Validates FFI mechanism ("ctypes" or "cffi")
- Verifies FFI module is available in Python runtime

#### : Verification Config
- Generates deterministic seed if not provided (hash of library path + rounded timestamp)
- Sets timeout limits with sensible defaults
- Validates crash handling mode and verbosity level

#### : Provenance Metadata Generation
- Generates UUID v4 for execution identifier
- Captures current timestamp in UTC, ISO 8601 format
- Records schema version and tool version

#### : Artifact Path Resolution
- Resolves working directory to absolute path
- Creates `artifacts/` subdirectory
- Validates write permissions
- Resolves all artifact paths to absolute paths

#### : Immutable Context Object Construction
- Assembles all components into frozen dataclass
- Serializes context to `execution_context.json`
- Returns immutable ExecutionContext object

### 3. Orchestration Layer (`src/core/orchestration.py`)

#### Error Classification

Four distinct error types with appropriate handling:

1. **ConfigError**
   - Missing required arguments
   - Invalid file paths
   - Unsupported platform
   - Write permission denied

2. **ToolingError**
   - Compiler not found
   - Library not loadable
   - Python interpreter incompatible

3. **PreconditionError**
   - Required input artifact missing
   - Provides command to generate missing artifact

4. **StageError**
   - Errors during stage execution
   - Preserves partial artifacts for debugging

#### PipelineOrchestrator

Coordinates execution of verification pipeline stages:

- **Stage Registration**: Allows registration of stage handlers
- **Precondition Checking**: Validates required artifacts exist before execution
- **Stage Invocation**: Executes stage with execution context
- **Output Validation**: Verifies expected artifacts were produced
- **Failure Handling**: Halts pipeline on first failure, preserves artifacts

#### CLIOrchestrator

Provides command-line interface with 9 commands:

1. **`verify`** - Full pipeline execution from ingestion to reporting
2. **`ingest`** - Native interface ingestion only
3. **`synthesize`** - Contract synthesis (requires IR artifact)
4. **`generate-adapters`** - Adapter generation (requires contract)
5. **`generate-tests`** - Test plan generation (requires contract)
6. **`execute`** - Verification execution (requires adapters and test plan)
7. **`diagnose`** - Diagnostics mapping (requires execution log)
8. **`report`** - Report generation (requires diagnostics)
9. **`context`** - Display or validate execution context

Each command supports:
- Required arguments (header file, library file for native commands)
- Optional flags (compiler path, include paths, defines, etc.)
- Common flags (verbose, quiet, working directory)

## Architectural Principles Enforced

### 1. Immutability
- ExecutionContext uses `@dataclass(frozen=True)` to prevent modification
- All nested structures are also frozen
- Attempting to modify raises `FrozenInstanceError`

### 2. Explicitness
- All environmental details captured explicitly in execution context
- No implicit queries during stage execution
- All assumptions documented in data structures

### 3. Determinism
- Identical inputs produce byte-identical contexts (except timestamps)
- Deterministic seed generation from library path + rounded timestamp
- Fixed execution order for all stages

### 4. Artifact-Driven
- All communication between stages through explicit artifacts
- No shared mutable state
- Artifacts are inspectable, diffable, and versioned

### 5. Failure Isolation
- Errors classified by type and handled appropriately
- Failures in one stage don't corrupt downstream artifacts
- Clear error messages with actionable suggestions

### 6. Partial Execution Support
- Individual stages can be invoked independently
- Preconditions enforced before each stage
- Intermediate artifacts can be reused

### 7. Provenance Tracking
- Every artifact includes provenance metadata
- Full traceability from inputs to outputs
- Execution ID links all artifacts from same run

## File Structure

```
Polyglot Ffi Contract Verifier/
├── src/
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── execution_context.py    # ExecutionContext and Builder
│       └── orchestration.py        # Orchestration and CLI
├── polyglot_ffi_verifier.py        # Main entry point
└── validate_orchestration.py             # Validation suite
```

## Usage Examples

### Creating an Execution Context

```python
from src.core.execution_context import ExecutionContextBuilder

builder = ExecutionContextBuilder()
context = builder.build(
    header_file="path/to/interface.h",
    library_file="path/to/library.dll",
    compiler_path="C:/path/to/cl.exe",  # Optional, auto-detected
    include_paths=["C:/includes"],
    preprocessor_macros={"DEBUG": "1"},
    python_interpreter="C:/Python311/python.exe",  # Optional
    ffi_mechanism="ctypes",
    random_seed=42,  # Optional, generated if not provided
    working_directory="C:/workspace"
)

# Context is automatically saved to artifacts/execution_context.json
print(f"Execution ID: {context.provenance.execution_id}")
```

### Using the CLI

```bash
# Full verification pipeline
python polyglot_ffi_verifier.py verify interface.h library.dll --verbose

# Individual stage execution
python polyglot_ffi_verifier.py ingest interface.h library.dll
python polyglot_ffi_verifier.py synthesize
python polyglot_ffi_verifier.py generate-tests

# Display execution context
python polyglot_ffi_verifier.py context

# Validate existing context
python polyglot_ffi_verifier.py context --validate
```

### Loading Existing Context

```python
from src.core.execution_context import ExecutionContext

context = ExecutionContext.load("artifacts/execution_context.json")
print(context.to_json(indent=2))
```

## Validation

Run the comprehensive validation suite:

```bash
python validate_orchestration.py
```

This validates:
- ✅ ExecutionContext has all 7 required field categories
- ✅ Context construction performs all 8 steps deterministically
- ✅ CLI supports all 9 commands
- ✅ Determinism (identical inputs → identical contexts)
- ✅ Immutability (context cannot be modified after construction)
- ✅ JSON serialization and deserialization
- ✅ Error classification (4 error types)
- ✅ Provenance metadata completeness
- ✅ Absolute path resolution

## Execution Context JSON Schema

Example serialized execution context:

```json
{
  "platform": {
    "os_name": "Windows",
    "os_version": "10.0.22631",
    "architecture": "AMD64",
    "pointer_width": 64,
    "endianness": "little"
  },
  "compiler": {
    "compiler_name": "MSVC",
    "compiler_version": "19.35.32215",
    "compiler_flags": [],
    "include_paths": [],
    "preprocessor_macros": {},
    "standard_library_version": null
  },
  "native_library": {
    "library_path": "C:\\path\\to\\library.dll",
    "library_hash": "abc123...",
    "library_load_paths": ["C:\\path\\to", "..."],
    "additional_dependencies": []
  },
  "target_runtime": {
    "language_name": "Python",
    "language_version": "3.11.5",
    "ffi_mechanism": "ctypes",
    "runtime_path": "C:\\Python311\\python.exe",
    "runtime_config": {}
  },
  "verification_config": {
    "random_seed": 123456789,
    "per_test_timeout_seconds": 5,
    "total_timeout_seconds": 300,
    "crash_handling_mode": "monitor",
    "verbosity_level": "normal"
  },
  "provenance": {
    "schema_version": "1.0.0",
    "creation_timestamp": "2026-02-01T13:17:00+00:00",
    "execution_id": "550e8400-e29b-41d4-a716-446655440000",
    "tool_version": "1.0.0"
  },
  "artifacts": {
    "working_directory": "C:\\workspace",
    "intermediate_representation_path": "C:\\workspace\\artifacts\\intermediate_representation.json",
    "contract_path": "C:\\workspace\\artifacts\\contract.json",
    "test_plan_path": "C:\\workspace\\artifacts\\test_plan.json",
    "execution_log_path": "C:\\workspace\\artifacts\\execution_log.json",
    "diagnostics_path": "C:\\workspace\\artifacts\\diagnostics.json",
    "report_path": "C:\\workspace\\artifacts\\report.txt",
    "execution_context_path": "C:\\workspace\\artifacts\\execution_context.json"
  }
}
```

## Next Steps

This implementation provides the foundational orchestration and execution context subsystem. All subsequent pipeline stages (Phases 2-15) will:

1. Receive the immutable ExecutionContext as input
2. Read required input artifacts specified in the context
3. Perform stage-specific processing
4. Write output artifacts to paths specified in the context
5. Include provenance metadata referencing the execution ID

**** will implement Native Interface Ingestion, which consumes the ExecutionContext and produces the Intermediate Representation artifact.

## Checklist Completion

- [x] ExecutionContext has all 7 required field categories
- [x] Context construction performs all 8 steps deterministically
- [x] CLI supports all 9 commands
- [x] Orchestration engine validates preconditions before each stage
- [x] Error types are classified into 4 categories and handled appropriately
- [x] Execution context is serialized to JSON
- [x] Provenance metadata includes UUID, timestamp, tool version, stage name
- [x] Deterministic seed generation works correctly
- [x] Full pipeline execution halts on first failure
- [x] Partial execution (single stage invocation) works correctly
- [x] File paths are resolved to absolute paths
- [x] ExecutionContext is immutable after construction
- [x] Error messages are clear and actionable
- [x] All artifacts include provenance metadata
- [x] Implementation follows all 7 architectural principles

### 3.2 : Native Interface Ingestion

## Overview

This document describes the implementation of the **Native Interface Ingestion** component for the Polyglot FFI Contract Verifier. This component extracts compiler-grade ABI (Application Binary Interface) information from C header files using libclang.

### Position in Pipeline

```
ExecutionContext (Orchestration Layer)
  ↓
Native Interface Ingestion ← YOU ARE HERE
  ↓
IR Normalization ()
  ↓
Contract Synthesis ()
  ↓
... remaining phases
```

### Input Artifacts
- **ExecutionContext** - Immutable context from orchestration layer
- **C Header File(s)** - User-specified interface definitions
- **Native Library** - Binary for validation

### Output Artifacts
- **native_interface.json** - Complete ABI description with:
  - Functions with full signatures
  - Structs with explicit padding
  - Enums with values
  - Typedefs with underlying types
  - Complete provenance metadata

---

## Components Implemented

### 1. NativeInterfaceAnalyzer
**Location**: `src/ingestion/native_interface_analyzer.py`

Main orchestrator for the ingestion process.

**Responsibilities**:
- Coordinate parsing and extraction
- Walk AST to extract symbols
- Generate Native Interface Artifact
- Ensure provenance tracking

**Key Methods**:
```python
analyze(header_path, library_path, context) -> Dict
extract_functions(cursor) -> List[Dict]
extract_structs(cursor) -> List[Dict]
extract_enums(cursor) -> List[Dict]
extract_typedefs(cursor) -> List[Dict]
save_artifact(artifact, output_path)
```

### 2. CompilerFrontend
**Location**: `src/ingestion/compiler_frontend.py`

Interfaces with libclang for header parsing.

**Responsibilities**:
- Configure libclang with correct flags
- Parse headers into AST
- Validate compilation
- Report errors clearly

**Key Methods**:
```python
parse_header(header_path, context) -> TranslationUnit
get_compiler_command(context) -> List[str]
validate_compilation(tu) -> bool
```

**Windows/MSVC Integration**:
- Auto-detects libclang.dll from common LLVM paths
- Adds MSVC compatibility flags (`-fms-compatibility`)
- Uses include paths and macros from ExecutionContext
- Handles Windows SDK headers correctly

### 3. ABIExtractor
**Location**: `src/ingestion/abi_extractor.py`

Extracts ABI-specific details from AST nodes.

**Responsibilities**:
- Compute struct layouts with padding
- Extract type information recursively
- Determine calling conventions
- Calculate padding fields

**Key Methods**:
```python
compute_struct_layout(cursor) -> Dict
extract_type_info(clang_type) -> Dict
determine_calling_convention(cursor) -> str
calculate_padding(fields, total_size, alignment, is_union) -> List[Dict]
```

### 4. SourceLocationTracker
**Location**: `src/ingestion/source_location_tracker.py`

Captures source locations from AST nodes.

**Responsibilities**:
- Extract source locations from cursors
- Resolve to absolute paths
- Format consistently for artifacts
- Handle missing locations gracefully

**Key Methods**:
```python
get_location(cursor) -> SourceLocation
format_location(location) -> Dict
get_location_dict(cursor) -> Dict
```

---

## libclang Integration

### Install
```bash
pip install libclang
```

### Config
The compiler frontend automatically configures libclang by searching common Windows paths:
- `C:\Program Files\LLVM\bin\libclang.dll`
- `C:\Program Files (x86)\LLVM\bin\libclang.dll`
- `C:\LLVM\bin\libclang.dll`

Alternatively, set the `LIBCLANG_PATH` environment variable.

### Usage Pattern
```python
import clang.cindex as clang

# Create index
index = clang.Index.create()

# Parse translation unit
tu = index.parse(
    header_path,
    args=['-I/include/path', '-DMACRO=value'],
    options=clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
)

# Walk AST
for cursor in tu.cursor.walk_preorder():
    if cursor.kind == clang.IDEKind.FUNCTION_DECL:
        # Extract function information
        pass
```

### IDE Kinds Extracted
- `FUNCTION_DECL` - Function declarations
- `STRUCT_DECL` - Struct definitions
- `UNION_DECL` - Union definitions
- `ENUM_DECL` - Enum definitions
- `TYPEDEF_DECL` - Typedef declarations
- `FIELD_DECL` - Struct fields
- `ENUM_CONSTANT_DECL` - Enum values

---

## Struct Layout Computation

Struct layout is the most complex aspect of ingestion. The algorithm:

### : Extract Field Declarations
Iterate through struct fields in declaration order and extract name and type for each.

### : Compute Field Offsets
Use `cursor.get_field_offsetof()` from libclang:
- Returns offset in **bits**
- Divide by 8 to get bytes
- Offsets account for alignment and padding

### : Detect Implicit Padding
Compare consecutive field offsets:
```python
if offset[i+1] != offset[i] + size[i]:
    # Padding exists
    padding_size = offset[i+1] - (offset[i] + size[i])
    # Insert synthetic padding field
```

### : Compute Total Size and Alignment
- Total size: `cursor.type.get_size()`
- Alignment: `cursor.type.get_align()`
- Check for trailing padding

### Example

```c
struct Example {
    int a;      // offset 0, size 4
    // implicit padding: offset 4, size 4
    void* b;    // offset 8, size 8
    char c;     // offset 16, size 1
    // implicit trailing padding: offset 17, size 7
};
// Total size: 24, alignment: 8
```

**Artifact Representation**:
```json
{
  "name": "Example",
  "size_bytes": 24,
  "alignment_bytes": 8,
  "fields": [
    {
      "name": "a",
      "offset_bytes": 0,
      "type": {"kind": "primitive", "name": "int", "size_bytes": 4},
      "is_implicit": false
    },
    {
      "name": "__padding_1",
      "offset_bytes": 4,
      "type": {"kind": "padding", "size_bytes": 4},
      "is_implicit": true
    },
    {
      "name": "b",
      "offset_bytes": 8,
      "type": {"kind": "pointer", "size_bytes": 8},
      "is_implicit": false
    },
    {
      "name": "c",
      "offset_bytes": 16,
      "type": {"kind": "primitive", "name": "char", "size_bytes": 1},
      "is_implicit": false
    },
    {
      "name": "__padding_2",
      "offset_bytes": 17,
      "type": {"kind": "padding", "size_bytes": 7},
      "is_implicit": true
    }
  ]
}
```

---

## Type Representation

Types are represented recursively in the artifact.

### Primitive Types
```json
{
  "kind": "primitive",
  "name": "int",
  "size_bytes": 4,
  "alignment_bytes": 4
}
```

### Pointer Types
```json
{
  "kind": "pointer",
  "pointee": {
    "kind": "primitive",
    "name": "char",
    "size_bytes": 1
  },
  "size_bytes": 8,
  "alignment_bytes": 8
}
```

### Array Types
```json
{
  "kind": "array",
  "element_type": {"kind": "primitive", "name": "int"},
  "size": 10,
  "size_bytes": 40
}
```

### Typedef Types
```json
{
  "kind": "typedef",
  "name": "size_t",
  "underlying_type": {
    "kind": "primitive",
    "name": "unsigned long long",
    "size_bytes": 8
  }
}
```

---

## Calling Convention Detection

On Windows with MSVC, functions may use different calling conventions.

### Supported Conventions
- **cdecl** - Standard C calling convention (default)
- **stdcall** - Windows API convention (callee cleans stack)
- **fastcall** - First two args in registers
- **win64** - x64 Windows calling convention

### Detection Method
```python
calling_conv = cursor.type.get_calling_conv()
if calling_conv == clang.CallingConv.C:
    return "cdecl"
elif calling_conv == clang.CallingConv.X86_STDCALL:
    return "stdcall"
elif calling_conv == clang.CallingConv.X86_FASTCALL:
    return "fastcall"
elif calling_conv == clang.CallingConv.WIN64:
    return "win64"
```

### Example
```c
int __cdecl normal_func(int x);
int __stdcall windows_func(int x);
```

Artifact:
```json
{
  "name": "normal_func",
  "calling_convention": "cdecl",
  ...
},
{
  "name": "windows_func",
  "calling_convention": "stdcall",
  ...
}
```

---

## Error Handling

### Compilation Errors
If a header cannot be parsed:
- Report which header file failed
- Show compiler diagnostics (errors/warnings)
- Suggest missing include paths or macros
- Exit with `ToolingError`
- **Do not produce partial artifacts**

Example error:
```
ToolingError: Header compilation failed:
Error: test.h:10:5: unknown type name 'HANDLE'
Important: Did you include windows.h
```

### Missing libclang
If libclang is not installed:
```
ImportError: libclang not found. Install with: pip install libclang
On Windows, ensure LLVM is installed and libclang.dll is available.
```

### Unknown Source Locations
If source location cannot be determined:
```json
{
  "file": "<unknown>",
  "line": 0,
  "column": 0
}
```

---

## Usage Examples

### Standalone Invocation
```bash
# Through orchestrator
python polyglot_ffi_verifier.py ingest interface.h library.dll

# Direct usage
python -c "
from src.core.execution_context import ExecutionContextBuilder
from src.ingestion import NativeInterfaceAnalyzer

builder = ExecutionContextBuilder()
context = builder.build('library.dll', '.')

analyzer = NativeInterfaceAnalyzer()
artifact = analyzer.analyze('interface.h', 'library.dll', context)
analyzer.save_artifact(artifact, 'artifacts/native_interface.json')
"
```

### Inspecting Output
```bash
# Pretty-print artifact
python -m json.tool artifacts/native_interface.json

# Extract function names
python -c "
import json
with open('artifacts/native_interface.json') as f:
    artifact = json.load(f)
    for func in artifact['functions']:
        print(func['name'])
"
```

---

## Known Limitations

### v1.0 Does NOT Support
- **C++ features** - Only C headers are supported
  - Workaround: Use `extern "C"` blocks
- **Complex macros** - Macros are not expanded
- **Variadic macros** - Not fully supported
- **Inline functions** - Only declarations extracted
- **Bitfields** - Not yet implemented
- **Flexible array members** - Not yet implemented

### Future Extensions
- C++ support via separate analyzer
- Macro expansion and evaluation
- Bitfield layout computation
- Flexible array member handling
- Cross-platform support (Linux, macOS)

---

## Validation

Run comprehensive validation:
```bash
python validate_ingestion.py
```

**Expected Output**:
```
======================================================================
  Native Interface Ingestion Validation
======================================================================

Testing ExecutionContext Integration...
  ✓ ExecutionContext integration working

Testing Simple Header Parsing...
  ✓ Simple header parsing successful

Testing Struct Layout with Padding...
  ✓ Struct layout with padding correct

Testing Enum Extraction...
  ✓ Enum extraction working

Testing Typedef Extraction...
  ✓ Typedef extraction working

Testing Calling Convention Detection...
  ✓ Calling convention detection working

Testing Source Location Tracking...
  ✓ Source location tracking working

Testing Provenance Metadata...
  ✓ Provenance metadata complete

======================================================================
  ✓ ALL TESTS PASSED (8/8)
======================================================================
```

---

## Artifact Schema

Complete schema for `native_interface.json`:

```json
{
  "provenance": {
    "producing_phase": "Native Interface Ingestion",
    "execution_id": "<UUID from ExecutionContext>",
    "timestamp": "<ISO 8601 UTC>",
    "tool_version": "1.0.0",
    "schema_version": "1.0.0",
    "input_artifacts": ["<header path>", "<library path>"],
    "compiler_invocation": "<full clang command>"
  },
  "platform": {
    "os_name": "Windows",
    "architecture": "AMD64",
    "pointer_width": 64,
    "endianness": "little"
  },
  "functions": [...],
  "structs": [...],
  "enums": [...],
  "typedefs": [...]
}
```

See specification for complete field details.

---

## Integration with Orchestration Layer

### ExecutionContext Usage
```python
# Read compiler configuration
compiler_path = context.compiler.compiler_path
include_paths = context.compiler.include_paths
macros = context.compiler.preprocessor_macros

# Read platform information
os_name = context.platform.os_name
architecture = context.platform.architecture

# Use execution ID for provenance
execution_id = context.provenance.execution_id
```

### Artifact Output
```python
# Write to artifacts directory
output_path = "artifacts/native_interface.json"
analyzer.save_artifact(artifact, output_path)
```

---

## Status

✅ **COMPLETE AND VALIDATED**

All requirements implemented:
- libclang integration working on Windows
- Struct layout with explicit padding
- Calling convention detection
- Complete provenance tracking
- All 8 validation tests passing

**Ready for : IR Normalization**

### 3.3 : IR Normalization

The Intermediate Representation (IR) Normalization layer transforms raw, compiler-specific Native Interface Artifacts into a canonical, compiler-agnostic representation. This document details the design and implementation of this subsystem.

## Overview

IR Normalization is the third phase of the Polyglot FFI Contract Verifier pipeline. Its primary goal is to decouple downstream verification stages from the idiosyncrasies of compiler frontends (like `libclang`) and platform-specific type naming conventions.

**Position in Pipeline:**
`ExecutionContext ()` -> `Native Interface Ingestion ()` -> **`IR Normalization ()`** -> `Contract Synthesis ()`

## Type Registry Design

The IR uses a centralized **Type Registry** to represent all types encountered in the interface. This design provides several benefits:
- **Deduplication**: Identical types are defined once and referenced by a unique ID.
- **Trivial Comparison**: Type equality checks become simple string comparisons of Type IDs.
- **Flat Structure**: Circular or recursive types (like linked list structs) are handled easily by ID references without deep nesting issues in JSON.

### Type ID Generation Algorithm
Type IDs are deterministic strings computed from the canonical representation of the type:
- **Primitives**: `primitive:<canonical_name>` (e.g., `primitive:int32`)
- **Pointers**: `pointer:<pointee_id>` (e.g., `pointer:primitive:void`)
- **Structs**: `struct:<name>` (e.g., `struct:Config`)
- **Enums**: `enum:<name>` (e.g., `enum:Status`)
- **Arrays**: `array:<element_id>:<count>` (e.g., `array:primitive:int8:10`)

## Typedef Resolution

The `TypeResolver` resolves all `typedef` chains transitively. If the native interface contains:
```c
typedef int MyInt;
typedef MyInt YourInt;
```
Any reference to `YourInt` is resolved to `primitive:int32` in the IR. This ensures that verification logic only deals with the actual memory-level type, not its various aliases.

## Canonical Type Mapping

The system maps compiler-specific type names to fixed-width canonical names based on the target platform (Windows x64).

| C Type | Canonical Name (Windows x64) | Size (Bytes) |
| :--- | :--- | :--- |
| `int` | `int32` | 4 |
| `long` | `int32` | 4 |
| `long long` | `int64` | 8 |
| `unsigned int` | `uint32` | 4 |
| `size_t` | `uint64` | 8 |
| `void*` | `pointer:void` | 8 |

## Qualifier Normalization

Type qualifiers (`const`, `volatile`, `restrict`) are extracted from compiler-specific lists and converted into a structured boolean map:
```json
"qualifiers": {
  "is_const": true,
  "is_volatile": false,
  "is_restrict": false
}
```

## Struct and Enum Normalization

### Structs
Struct layouts extracted in  are preserved exactly (including explicit padding fields). The normalization process replaces the deep, inline type definitions for fields with flat `type_id` references to the Type Registry.

### Enums
Enums are normalized by mapping their underlying storage type (usually `int`) to a canonical primitive ID and preserving the named constant values.

## Error Handling

- **Precondition Errors**: If `native_interface.json` is missing, the normalizer reports that  must be run first.
- **Validation Errors**: If the input artifact is malformed or contains circular typedefs, the system raises a detailed `ToolingError`.
- **Transparency**: All errors include context about the execution ID and producing phase to aid in debugging.

## Usage

### Orchestration
Normalization is triggered as part of the `synthesize` command (which runs phases 3 and 4):
```bash
python polyglot_ffi_verifier.py synthesize
```

### Standalone Validation
You can verify the IR normalization logic independently:
```bash
python validate_ir_normalization.py
```

### 3.4 : Contract Synthesis

This document details the implementation of **: Contract Synthesis Engine** for the Polyglot FFI Contract Verifier.

## Overview

The Contract Synthesis Engine transforms normalized Intermediate Representation (IR) into a formal **FFI Contract**. While the IR describes *structure*, the Contract describes *intent* and *constraints*. 

The synthesis process makes the implicit assumptions of C developers explicit and machine-readable, enabling automated verification.

## Core Components

1.  **`ContractSynthesizer`**: The main orchestrator that sequences the analysis of functions, structs, and globals.
2.  **`ConstraintDeriver`**: Implements the semantic rules used to infer constraints from types and metadata.
3.  **`NamingConventionAnalyzer`**: Employs heuristics and naming patterns (e.g., `create_`, `optional_`) to detect developer intent.
4.  **`ConservativeDefaultPolicy`**: Provides safe fallback behaviors when evidence is missing, favoring safety over permissiveness.
5.  **`ConstraintIDGenerator`**: Produces deterministic, human-readable IDs for every constraint for traceability.

## Constraint Derivation Rules

The engine implements 10 core derivation rules:

| Rule | Category | Description |
|------|----------|-------------|
| 1 | Nullability | Infers if a pointer can be NULL based on naming (e.g., `optional_`) or defaults to non-null. |
| 2 | Ownership | Detects if memory ownership changes (e.g., `create_` transfers to caller, `destroy_` to callee). |
| 3 | Lifetime | Sets the validity period of pointers (usually `call_duration` for borrowed pointers). |
| 4 | Buffers | Detects adjacent buffer/size pairs (e.g., `void* buf, size_t len`) and establishes a dependency. |
| 5 | Struct Fields| Enforces that non-padding fields must be initialized and analyzes pointer fields. |
| 6 | Return Values | Detects error code patterns (int returns) and ownership of returned pointers. |
| 7 | Call Convention| Enforces the exact calling convention (e.g., `cdecl`) from the IR. |
| 8 | Struct Layout | Requires an exact binary match between the target language and native layout. |
| 9 | Multi-mutability| Uses the `const` qualifier to enforce immutability on parameters. |
| 10| Variadic | Issues warnings for variadic functions (e.g., `printf`) which require manual verification. |

## Conservative Default Policies

When semantic hints are absent, the engine applies the following policies:

1.  **Nullability**: Pointers are assumed **non-null**.
2.  **Ownership**: Pointers are assumed **borrowed** (no transfer).
3.  **Lifetime**: Pointers are assumed valid only for the **duration of the call**.
4.  **Mutability**: Pointers are assumed **mutable** unless marked `const`.
5.  **Buffers**: Pointers that look like buffers but lack a size parameter trigger an **error/warning**.
6.  **Integers**: Integer return values are treated as **error codes** (0 = success).

## Traceability and Justification

Every constraint in the produced `contract.json` includes:
-   `constraint_id`: A unique, deterministic string.
-   `justification`: A human-readable explanation of why the rule was applied (e.g., "Naming convention suggests optional parameter").
-   `severity`: Either `error`, `warning`, or `info`.

## Metadata and Warnings

The synthesizer tracks its own confidence. If it makes a high-risk assumption (like assuming a `void*` is just a borrowed pointer when it can't be sure), it logs a warning in the `synthesis_metadata` section of the contract.

## Example Contract Structure

```json
{
  "function_name": "process",
  "pre_conditions": [
    {
      "constraint_id": "func_process_p_cfg_non_null",
      "constraint_type": "non_null",
      "description": "Parameter 'cfg' must not be NULL",
      "target": "parameter:cfg",
      "justification": "Pointer parameter without indication of nullability",
      "severity": "error"
    }
  ],
  "parameter_contracts": [
    {
      "parameter_name": "cfg",
      "nullability": "non_null",
      "ownership": "borrowed",
      "lifetime": "call_duration",
      "mutability": "immutable"
    }
  ]
}
```

### 3.5 : Contract Versioning

This document details the implementation of **: Contract Schema Versioning and Evolution** for the Polyglot FFI Contract Verifier.

## Overview

The Contract Schema Versioning system ensures that FFI contracts are stable and evolvable. It enables detecting ABI changes when a native library or its header is updated, mapping these changes to risk categories, and providing actionable recommendations for developers.

## Core Components

1.  **`SchemaVersionManager`**: Manages semantic versioning (MAJOR.MINOR.PATCH) for contracts. It determines if two contracts are structure-compatible based on their schema version.
2.  **`ContractSchemaValidator`**: Ensures that contract files conform to the expected structural requirements and version constraints.
3.  **`ContractComparator`**: Implements a systematic 8-step algorithm to compare two contracts and identify every addition, removal, and modification.
4.  **`ChangeClassifier`**: Assigns risk categories (Breaking, Compatible, Semantic, etc.) and impact descriptions to each detected change.
5.  **`CompatibilityReportGenerator`**: Produces professional, human-readable summary reports that help developers understand the risks of an ABI update.

## Change Detection Algorithm

The system follows a deterministic comparison process:
1.  **Load & Validate**: Load baseline and current contracts; verify JSON integrity and schema.
2.  **Schema Check**: Verify that the schema versions are compatible (matching Major version).
3.  **Indexing**: Create lookup maps for functions, structs, and types.
4.  **Function Diff**: Detect added/removed functions, and changes in signatures or calling conventions.
5.  **Struct Diff**: Detect layout changes, size/alignment shifts, and field modifications.
6.  **Type Registry Diff**: Track changes in primitive or derived type definitions.
7.  **Global Constraints Diff**: Track changes in environment-wide safety invariants.
8.  **Artifact Assembly**: Generate `contract_diff.json` with full metadata.

## Change Categories & Impact

| Category | Impact | Action Required |
|----------|--------|-----------------|
| **Breaking** | Bindings will crash or fail to link. | Update bindings/adapters immediately and recompile. |
| **Potentially Breaking** | May break if size/offsets are hardcoded. | Review struct layout and regenerate adapters. |
| **Semantic** | Safety rules changed (e.g. non-null). | Review application logic for contract compliance. |
| **Compatible** | New functionality added. | Regenerate adapters to expose new features (optional). |
| **Schema** | Tool incompatibility. | Upgrade verifier tools. |

## Compatibility Levels

The system assigns an overall compatibility level to every comparison:
-   **FULLY_COMPATIBLE**: Identical contracts or zero-risk additions.
-   **COMPATIBLE**: Function/struct additions that don't affect existing code.
-   **SEMANTICALLY_INCOMPATIBLE**: structural parity but safety constraints (like nullability) have tightened.
-   **POTENTIALLY_BREAKING**: Changes like adding fields to structs which change size.
-   **BREAKING**: Removals or signature changes that invalidate existing binary interfaces.

## Usage

### Validate Schema
```bash
python polyglot_ffi_verifier.py validate-schema
```

### Compare Contracts
```bash
python polyglot_ffi_verifier.py compare-contracts --baseline previous_contract.json
```
This produces:
-   `artifacts/contract_diff.json`: Machine-readable diff.
-   `artifacts/compatibility_report.txt`: Human-readable assessment.

### 3.6 : Adapter Generation

This document details the implementation of **: Language Adapter Generation** for the Polyglot FFI Contract Verifier.

## Overview

The Language Adapter Generation subsystem transforms abstract FFI contracts () into concrete, executable Python code. This code enforces all contract constraints at runtime, providing a verified safety layer between Python code and native libraries.

## Generated Architecture

The system produces a modular Python package in the `adapters/` directory:

1.  **`<lib>_adapter.py`**: The main entry point. It loads the native library using `ctypes` and provides wrapped versions of all functions.
2.  **`<lib>_structs.py`**: Contains `ctypes.Structure` definitions for all structs in the contract, including explicit padding and size/alignment validation.
3.  **`<lib>_exceptions.py`**: Defines a specific exception hierarchy for different types of contract violations (e.g., `NullPointerViolation`, `LayoutMismatchError`).
4.  **`<lib>_ownership.py`**: A runtime tracker that monitors memory ownership (borrowed vs. transferred) to detect use-after-transfer and double-free errors.
5.  **`adapter_metadata.json`**: Records generation details, including provenance, statistics, and enforced constraints.

## Constraint Enforcement Patterns

### Nullability
Generated wrappers perform `if ptr is None or not bool(ptr)` checks before passing pointers to native code, raising `NullPointerViolation` if the contract specifies `non_null`.

### Struct Layout
Structs are validated for both **Size** and **Alignment**. The system calculates expected offsets and sizes (including padding) and verifies them at runtime using `ctypes.sizeof()` and `ctypes.addressof() % alignment`.

### Buffer Sizes
Relationship between buffers and their size parameters are checked. If a buffer is non-NULL, the system ensures its associated size parameter is valid.

### Ownership & Lifetimes
- **Borrowed**: Tracked during the call to ensure no illegal transfers occur.
- **Transferred**: Marked as invalid for future use in the Python runtime. Any attempt to use a transferred pointer raises an `OwnershipViolation`.

### Calling Conventions
The generator distinguishes between `cdecl` (using `ctypes.CDLL`) and `stdcall` (using `ctypes.WinDLL`) to ensure stack integrity.

## Usage

Generated adapters can be used directly in Python applications:

```python
from adapters.example_lib import adapter, structs

# Create a validated struct
cfg = structs.Config(mode=1)

# Call a wrapped function (automatically validated)
try:
    result = adapter.process(cfg)
except exceptions.FFIContractViolation as e:
    print(f"Contract violation detected: {e}")
```

## Implementation Details

- **`AdapterGenerator`**: The main orchestrator that sequences module generation.
- **`FunctionWrapperGenerator`**: Generates the `ctypes` function signatures and the logic for pre/post-condition checks.
- **`StructDefinitionGenerator`**: Maps IR types to `ctypes` types and handles structure layout.
- **`ConstraintEnforcementCodegen`**: Translates declarative contract constraints into Python code snippets.

### 3.7 : Test Plan Generation

This document details the implementation of **: Test Plan Generation** for the Polyglot FFI Contract Verifier.

## Overview

The Test Plan Generation subsystem transforms abstract FFI contracts () into comprehensive, structured test specifications (`test_plan.json`). It provides systematic, deterministic coverage of both valid use cases (positive tests) and error conditions (negative tests).

## Test Case Categories

The generator produces four primary categories of tests:

1.  **Positive Tests**: Valid inputs designed to satisfy all contract constraints. These verify that the native library and its adapter function correctly under normal conditions.
2.  **Negative Tests**: Deliberate constraint violations. For every `pre_condition` in the contract, a test case is generated that violates only that specific constraint. This verifies the enforcement logic in the  adapters.
3.  **Boundary Value Tests**: Edge cases for numeric parameters (e.g., `0`, `MAX_INT`, `MIN_INT`).
4.  **Ownership Tests**: (Future) Focused on monitoring memory lifecycle, such as double-free or use-after-transfer detection.

## Test Derivation Algorithm

1.  **Enumerate Constraints**: Every unique `constraint_id` is extracted from the contract.
2.  **Positive Case Generation**: For each function, "minimal" and "typical" success cases are generated.
3.  **Fault Injection**: For each constraint, an input set is created where only that constraint is violated.
4.  **Deterministic Values**: Inputs are generated using a seed-less, rule-based approach to ensure byte-identical test plans on every run.
5.  **Coverage Mapping**: Each test is linked back to the constraints it exercises.

## Input Generation Strategies

- **Primitives**: Uses a fixed set of boundary and typical values (e.g., `42` for `int32`).
- **Pointers**: Generates `null` for negative tests and valid buffers/structs for positive tests.
- **Structs**: Recursively populates fields using the IR type definitions.
- **Strings**: Ensures null-termination unless deliberately testing for its absence.

## Coverage Analysis

The system generates a `test_coverage.json` report summarizing:
- Total number of constraints.
- Percentage of constraints covered by at least one negative test.
- List of any uncovered constraints (e.g., those currently too complex for automated fault injection).

## Artifacts

1.  **`test_plan.json`**: The declarative test suite specification.
2.  **`test_coverage.json`**: Coverage analytics and mapping.

### 3.8 : Verification Execution

This document details the implementation of **: Verification Execution** for the Polyglot FFI Contract Verifier.

## Overview

The Verification Execution Engine is the active component that runs contract tests. It consumes declarative test plans (), invokes contract-enforcing adapters (), and produces an immutable execution log.

## Execution Algorithm

The engine follows a 6-step loop for each test case:

1.  **Test Case Initialization**: Load metadata, category, and expected outcomes from the plan.
2.  **Input Instantiation**: Convert JSON-based values into `ctypes` primitives, structs, and pointers.
3.  **Adapter Invocation**: Dynamically load the generated Python adapter and call the specified function.
4.  **Exception Classification**: Catch all exceptions. Map known contract violations (from ) to specific results.
5.  **Outcome Validation**: Compare the actual result (success or exception) against the expected one.
6.  **Immutable Logging**: Record results, timing, and failure reasons in the append-only log.

## Input Instantiation

The `InputInstantiator` bridges the gap between the portable test plan and Python's memory model:
- **Primitives**: Direct mapping to `ctypes.c_*` types.
- **Pointers**: Handles `NULL` as `None` or casts memory to the appropriate pointer type.
- **Structs**: Recursively instantiates fields using the generated `_structs.py` module.
- **Buffers**: Allocates memory and populates it with test data.

## Outcome Assessment

Tests are classified into three logical results:
- **PASS**: Actual outcome matches expectations (e.g., a negative test correctly triggered a violation).
- **FAIL**: Mismatch (e.g., a function succeeded when it should have failed, or vice-versa).
- **ERROR/CRASH**: Unexpected infrastructure failure or native library crash.

## Isolation and Reproducibility

- **Test Isolation**: Each test is independent. A crash or failure in one test does not propagate state to the next.
- **Determinism**: By using fixed inputs from the test plan, the execution results are reproducible across identical library versions.

## Artifacts

1.  **`execution_log.json`**: The complete audit trail of the verification run.
2.  **`execution_summary.txt`**: A human-readable report summarizing pass rates and critical failures.

### 3.9 : Runtime Monitoring

This document details the implementation of **: Runtime Monitoring and Crash Detection** for the Polyglot FFI Contract Verifier.

## Overview

Runtime Monitoring ensures that native crashes (segfaults, access violations, etc.) are detected and recorded even when they bypass standard Python exception handling. This is achieved by executing each test case in an isolated subprocess.

## Architecture

The system uses a parent-child process model:
- **Parent Process**: Orchestrates the verification run, spawns children, and monitors their exit status.
- **Child Process**: Executes exactly one test case using the generated adapters.
- **IPC**: Results are serialized to JSON and communicated via stdout.

## Crash Detection Mechanism

### Subprocess Monitoring
The parent process uses the subprocess return code to detect abnormal termination:
- **Windows**: Detects NT status codes like `0xC0000005` (Access Violation).
- **Linux**: Detects signals like `SIGSEGV` (Segmentation Fault) or `SIGABRT` (Abort).

### Heuristic Analysis
`CrashAnalyzer` uses heuristics to classify crashes:
- Addresses near `0x0` are classified as **Null Pointer Dereferences**.
- Crashes during tests with `BufferSizeViolation` expectations are flagged as **Buffer Overflows**.

## Classification of Failures

1.  **SUCCESS**: Test returned exact expected value or raised expected exception.
2.  **FAILURE**: Test returned wrong value or wrong exception.
3.  **CRASH**: Native code terminated the process (e.g., Segfault).
4.  **TIMEOUT**: Test exceeded the allowed duration (default 60s).

## Artifacts

### Execution Log Augmentation
The `execution_log.json` is enhanced with a `crash_info` block for crashed tests:
```json
{
  "test_id": "test_001",
  "status": "failed",
  "crash_detected": true,
  "crash_info": {
    "crash_type": "access_violation",
    "exit_code": -1073741819
  }
}
```

### Crash Reports
For every crash, a detailed report is saved in `artifacts/crashes/crash_<test_id>_<timestamp>.json` containing context and analysis.

## Platform Support
- **Windows**: Supports SEH-based exit code detection.
- **Linux**: Supports signal-based termination detection.

### 3.10 0: Diagnostics Mapping

This document details the implementation of **0: Diagnostics Mapping** for the Polyglot FFI Contract Verifier.

## Overview

Diagnostics Mapping transforms raw execution results (test outcomes and native crashes) into human-understandable, semantic insights. It bridges the gap between technical symptoms (e.g., "Access Violation at 0x0") and contract violations (e.g., "Missing null check for parameter 'cfg'").

## Failure Classification

The `FailureClassifier` uses a decision tree to categorize failures:

1.  **Failure Mode Detection**:
    - `passed`: Not a failure.
    - `crashed`: Native process termination (Segfault, Access Violation).
    - `failed`: Python-level failure (wrong return value, missing exception).
    - `timeout`: Native code hung.

2.  **Severity Assignment**:
    - **CRITICAL**: Buffer overflows, use-after-free, and any native crash.
    - **HIGH**: Missing null pointer enforcement.
    - **MEDIUM**: Type layout mismatches or custom constraint violations.
    - **LOW**: Minor discrepancies or informational issues.

## Root Cause Analysis

The `RootCauseAnalyzer` identifies four primary failure patterns:

- **Adapter Missing Enforcement**: Native crash occurred because the adapter didn't reject invalid input.
- **Adapter Missing Pre-call Check**: Test expected an exception but native code was called without validation.
- **Unexpected Exception Type**: Adapter raised an exception, but not the specific one required by the contract.
- **Native Deadlock**: Native code timed out.

## Remediation Generation

The `RemediationGenerator` produces actionable instructions including:
- Concrete code snippets for pre-call checks.
- Specific adapter files and functions requiring modification.
- Contract revision suggestions if the specification is insufficient.

## Violation Aggregation

To avoid "alert fatigue," the `ViolationAggregator` groups related test failures by the underlying **Constraint ID**. Even if 100 tests fail due to a single missing null check, they are reported as one aggregated violation with a "Affected Tests" count.

## Artifacts

### `diagnostics.json`
Machine-readable report containing:
- Summary statistics (passed/total, severity counts).
- Aggregated violations with full context (impact, cause, fix).
- Provenance metadata for traceability.

### `violation_summary.txt`
Human-readable executive summary listing critical and high-severity issues first with clear remediation steps.

## Usage

Run the diagnostics stage independently:
```bash
python polyglot-ffi-verifier.py diagnose
```
Or as part of the full pipeline:
```bash
python polyglot-ffi-verifier.py verify <header> <library>
```

### 3.11 1: Report Generation

This document details the implementation of **1: Comprehensive Report Generation** for the Polyglot FFI Contract Verifier.

## Overview

Comprehensive Report Generation transforms the technical diagnostics and execution logs into polished, stakeholder-ready reports. This is the final core functionality phase, producing the primary user-facing deliverables of the verification process.

## Report Formats

The system generates reports in three distinct formats to serve different needs:

1.  **HTML Report (`verification_report.html`)**:
    - A single, self-contained file with inline CSS.
    - Features a rich visual hierarchy with color-coded severity badges.
    - Responsive design for desktop and mobile viewing.
    - Collapsible sections for technical details.
2.  **Markdown Report (`verification_report.md`)**:
    - Versions-control friendly plain text format.
    - Consistent content with the HTML report.
    - Ideal for embedding in documentation or PR comments.
3.  **CI Summary (`ci_summary.json`)**:
    - Machine-readable JSON for CI/CD integration.
    - Includes exit codes, blocking issues, and status badge metadata.

## Report Sections

### Executive Summary
Provides a high-level overview of the library's safety status. Includes "summary cards" showing the count of Critical, High, and Medium violations, along with the overall pass rate.

### Test Results
A statistical breakdown of the verification run, showing total tests executed, passed, failed, and the calculated pass rate.

### Detailed Violations
Prioritized by severity (Critical > High > Medium > Low). Each violation card includes:
- **Constraint Reference**: The specific contract ID.
- **Description**: Clear explanation of the observed failure.
- **Impact**: Assessment of security and stability risks.
- **Evidence**: Test case IDs and failure symptoms (crashes/exceptions).
- **Remediation**: Actionable, step-by-step instructions to fix the issue.

### Verified Constraints
A list of all contract constraints that were successfully verified with no observed violations, providing confidence in the "green" parts of the FFI surface.

### Recommendations
Actionable next steps categorized by priority (Immediate Action vs. Follow-up).

## Visual Design

- **Color Scheme**: 
  - Red: Critical violations (Blocked).
  - Orange: High severity.
  - Yellow: Medium severity.
  - Green: Passed/Verified.
- **Typography**: Uses modern, readable sans-serif fonts with monospaced blocks for code and logs.
- **Layout**: Card-based design for easy scanning of multiple issues.

## CI/CD Integration

The `ci_summary.json` is designed for automated pipeline gates:
- **Exit Code**: 0 if no critical violations exist, 1 otherwise.
- **Blocking Issues**: Explicit list of critical violations that should prevent deployment.
- **Status Badge**: Metadata for generating shields.io style badges (e.g., `FFI Verification: FAILED (3 critical)`).

## Usage

Generate reports for an existing execution:
```bash
python polyglot_ffi_verifier.py report
```
The reports will be saved in the `reports/` subdirectory of your working directory.

### 3.12 2: CI/CD Integration

This document details the implementation of **2: CI/CD Integration** for the Polyglot FFI Contract Verifier.

## Overview

The CI/CD Integration subsystem enables development teams to automate FFI verification as part of their standard build pipelines. It provides pre-built templates for popular CI platforms, status badge generation, and intelligent failure gating based on contract violation severity.

## Quick Start

1.  **Select a Template**: Choose the template for your CI platform from the `templates/` directory or generate one using the CLI.
2.  **Configure Paths**: Update the `header` and `library` paths in your CI configuration to point to your project's native interface and build output.
3.  **Run Verification**: Add the verification step to your pipeline. The verifier will automatically produce reports and machine-readable summaries.

## Supported Platforms

### GitHub Actions
Copy `templates/github_actions.yml` to `.github/workflows/ffi-verification.yml`.
This template runs on `windows-latest` by default and is optimized for C/C++ projects using MSVC.

### GitLab CI
Copy `templates/gitlab_ci.yml` (or use the content) to your `.gitlab-ci.yml`.
Uses GitLab's artifact storage to preserve verification reports.

### Jenkins
Use the provided `Jenkinsfile` template. Requires a Windows agent with Python 3.11+.

## Config

The CI behavior can be controlled via `configs/ffi_verifier.yml` or environment variables.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FFI_HEADER_PATH` | Path to the C header file | `native/interface.h` |
| `FFI_LIBRARY_PATH` | Path to the built library | `build/library.dll` |
| `FFI_VERIFIER_STRICT` | If `true`, fails on any violation (not just critical) | `false` |
| `FFI_VERIFIER_TIMEOUT` | Global execution timeout in seconds | `600` |

### Failure Policy

The `failure_policy` section in the config file determines when a build should fail:
- `block_on_critical`: Fail the build if any Critical (crash-prone) violations are found.
- `strict_mode`: Fail the build if *any* violation is found, including warnings.
- `max_violations`: Fail if the total number of violations exceeds this limit.

## Status Badges

The verifier can generate dynamic status badges for your README.

1.  Add a step to your CI to run `python scripts/generate_badge.py`.
2.  Use the generated `badges/ffi-status.json` with a shields.io endpoint.

Markdown Example:
```markdown
![FFI Verification](https://img.shields.io/endpointurl=https://raw.githubusercontent.com/user/repo/main/badges/ffi-status.json)
```

## Artifact Publishing

All verification runs produce:
- `reports/verification_report.html`: Visual report for humans.
- `reports/ci_summary.json`: Machine-readable summary for automation.
- `artifacts/diagnostics.json`: Technical diagnostic data.

These should be configured as "artifacts" in your CI platform to ensure they are saved after the build completes.

## Diagnostics

- **Missing Header**: Ensure the path to the C header is relative to the project root or provide an absolute path.
- **Library Not Found**: Verification often runs after the build stage. Ensure the library exists at the specified path before the verifier runs.
- **Python Dependencies**: Ensure `libclang` and `PyYAML` are installed in the CI runner.

### 4.1 Performance Considerations

## Overview
The Polyglot FFI Contract Verifier is designed for development-time and CI
verification, not runtime production use. Performance is adequate for typical
verification workloads but not optimized for high-throughput scenarios.

## Performance Characteristics

### : Orchestration
- **Time Complexity:** O(1)
- **Space Complexity:** O(1)
- **Typical Duration:** < 100ms
- **Bottlenecks:** None

### : Native Interface Ingestion
- **Time Complexity:** O(n) where n = number of declarations in header
- **Space Complexity:** O(n)
- **Typical Duration:** 500ms - 5s depending on header complexity
- **Bottlenecks:** 
  * libclang parsing (dependent on header size and complexity)
  * Macro expansion (can be expensive for heavily templated headers)
  * Include resolution (dependent on number of includes)

**Optimization Strategies:**
- Minimize include depth where possible
- Use precompiled headers if available
- Cache native_interface.json to avoid re-ingestion

### : IR Normalization
- **Time Complexity:** O(n) where n = number of types
- **Space Complexity:** O(n)
- **Typical Duration:** 100ms - 1s
- **Bottlenecks:**
  * Typedef resolution (recursive traversal)
  * Type registry construction

### : Contract Synthesis
- **Time Complexity:** O(f * c) where f = functions, c = constraints per function
- **Space Complexity:** O(f * c)
- **Typical Duration:** 200ms - 2s
- **Bottlenecks:**
  * Constraint derivation rules (10 rules per function)
  * Naming convention analysis (pattern matching)

### : Contract Versioning
- **Time Complexity:** O(c1 + c2) where c = constraints in each contract
- **Space Complexity:** O(c1 + c2)
- **Typical Duration:** 50ms - 500ms
- **Bottlenecks:** 
  * Deep comparison of contract structures

### : Adapter Generation
- **Time Complexity:** O(f + s) where f = functions, s = structs
- **Space Complexity:** O(f + s)
- **Typical Duration:** 100ms - 1s
- **Bottlenecks:**
  * Code generation (template rendering)
  * File I/O (writing multiple adapter modules)

### : Test Plan Generation
- **Time Complexity:** O(c * t) where c = constraints, t = tests per constraint
- **Space Complexity:** O(c * t)
- **Typical Duration:** 200ms - 2s
- **Bottlenecks:**
  * Input value generation (deterministic but computationally intensive)
  * Coverage analysis

### : Verification Execution
- **Time Complexity:** O(t * e) where t = tests, e = execution time per test
- **Space Complexity:** O(t)
- **Typical Duration:** 5s - 5min depending on test count
- **Bottlenecks:**
  * Test execution (calling native library repeatedly)
  * Serialization/deserialization overhead

**Critical Performance Factor:** This is the slowest phase by far.

### : Runtime Monitoring
- **Time Complexity:** O(t) where t = tests
- **Space Complexity:** O(t)
- **Typical Duration:** +20-50% overhead over 
- **Bottlenecks:**
  * Subprocess spawning (expensive on Windows)
  * IPC overhead (serialization between parent/child)

**Optimization Strategies:**
- Reuse subprocesses where possible (future improvement)
- Minimize serialization overhead
- Run tests in parallel (future improvement)

### 0: Diagnostics Mapping
- **Time Complexity:** O(v) where v = violations
- **Space Complexity:** O(v)
- **Typical Duration:** 100ms - 1s
- **Bottlenecks:**
  * Root cause analysis heuristics
  * Violation aggregation

### 1: Report Generation
- **Time Complexity:** O(v) where v = violations
- **Space Complexity:** O(v)
- **Typical Duration:** 200ms - 2s
- **Bottlenecks:**
  * HTML rendering (template expansion)
  * CSS embedding

### 2: CI Integration
- **Time Complexity:** O(1)
- **Space Complexity:** O(1)
- **Typical Duration:** < 100ms
- **Bottlenecks:** None

## Overall Pipeline Performance

**Typical Full Verification Run:**
- Small interface (5 functions, 20 constraints): 10-30 seconds
- Medium interface (20 functions, 80 constraints): 1-3 minutes
- Large interface (100 functions, 400 constraints): 5-15 minutes

**Breakdown by Phase (Medium Interface):**
- Ingestion: 5%
- Normalization: 2%
- Synthesis: 5%
- Versioning: 1%
- Adapter Generation: 3%
- Test Generation: 5%
- Execution: 70%  ← Dominant phase
- Monitoring Overhead: 5%
- Diagnostics: 2%
- Reporting: 2%

## Scalability Limits

### Theoretical Limits:
- **Maximum Functions:** ~10,000 (limited by Python memory, not design)
- **Maximum Constraints:** ~100,000 (limited by JSON serialization performance)
- **Maximum Test Cases:** ~100,000 (limited by execution time, not design)

### Practical Limits (for reasonable execution time):
- **Recommended Functions:** < 100
- **Recommended Constraints:** < 1,000
- **Recommended Test Cases:** < 1,000 (translates to < 5min execution)

## Memory Usage

**Typical Memory Footprint:**
- Orchestration: < 50 MB
- Ingestion: 100-500 MB (libclang)
- Normalization: 50-200 MB
- Synthesis: 50-200 MB
- Execution: 100-500 MB per subprocess
- Reporting: 50-200 MB

**Peak Memory:** ~1-2 GB for large interfaces

## Performance Optimization Recommendations

### For Users:
1. **Cache Artifacts:** Reuse contract.json across runs if interface hasn't changed
2. **Selective Verification:** Verify only changed functions (requires manual test plan filtering)
3. **Parallel Execution:** Run multiple verifier instances for different headers (manual orchestration)
4. **Reduce Test Count:** Use sampling for large interfaces (trade coverage for speed)

### For Future Development:
1. **Parallel Test Execution:** Run multiple subprocesses concurrently ( improvement)
2. **Incremental Verification:** Only re-verify changed functions
3. **Lazy Loading:** Load artifacts on-demand rather than upfront
4. **Caching:** Cache expensive computations (e.g., typedef resolution)

## Performance Monitoring

The system does not currently include built-in performance profiling.

**Manual Profiling:**
```python
python -m cProfile -o profile.stats polyglot_ffi_verifier.py verify ...
python -m pstats profile.stats
```

### Recommended Metrics:
- Time per phase (currently logged to stdout)
- Memory usage per phase (use external tools)
- Test execution rate (tests/second)

## When Performance Matters
Performance is acceptable for:
- Development-time verification (interactive use)
- CI pipelines (< 5 minute builds)
- Pre-commit hooks (with small interfaces)

Performance is insufficient for:
- Runtime enforcement (use generated adapters, not full verification)
- High-frequency testing (e.g., every function call)
- Real-time verification

### 4.2 Security Considerations

## Threat Model
The Polyglot FFI Contract Verifier operates in a trusted development environment. It is designed for use by developers verifying their own code, not for analyzing untrusted or adversarial code.

### Assumptions:
- The native library is not malicious (may be buggy, but not actively hostile)
- The execution environment is trusted (developer workstation or CI runner)
- Input headers are not crafted to exploit the verifier

### Out of Scope:
- Protection against malicious native libraries designed to exploit the verifier
- Sandboxing or isolation of native code execution
- Defense against timing attacks or side-channel attacks

## Attack Surface

### 1. Native Code Execution
**Risk:** The verifier executes native code from the library being verified. If the library is malicious or severely buggy, it could:
- Crash the verifier
- Corrupt memory
- Execute arbitrary code
- Access filesystem or network

**Mitigation:**
- Subprocess isolation () prevents crashes from killing the verifier
- Timeouts prevent infinite loops
- No sandboxing - native code runs with full privileges

**Residual Risk:** HIGH if library is malicious
**Recommendation:** Only verify libraries you trust

### 2. Header File Parsing
**Risk:** Maliciously crafted headers could exploit libclang vulnerabilities:
- Buffer overflows in parser
- Infinite loops in macro expansion
- Resource exhaustion (memory, CPU)

**Mitigation:**
- Use well-tested libclang version
- Timeout for ingestion phase
- Memory limits (if configured by OS)

**Residual Risk:** LOW (libclang is well-tested)

### 3. Artifact Deserialization
**Risk:** Malicious artifacts (JSON files) could:
- Exploit JSON parser vulnerabilities
- Cause resource exhaustion (deeply nested structures)
- Inject malicious data into execution

**Mitigation:**
- Use standard library json module (well-tested)
- Validate artifact schemas before processing
- Size limits on artifacts (implicit via memory)

**Residual Risk:** LOW

### 4. Code Generation
**Risk:** Generated adapters could:
- Contain code injection vulnerabilities
- Execute unintended code
- Expose sensitive information

**Mitigation:**
- Template-based generation (no eval/exec)
- Deterministic generation (no user input in templates)
- Generated code is Python (no shell commands)

**Residual Risk:** VERY LOW

### 5. File System Access
**Risk:** The verifier reads and writes files:
- Could read sensitive files if paths are user-controlled
- Could overwrite important files
- Could follow symlinks to unintended locations

**Mitigation:**
- All output paths are under user-specified output directory
- No automatic file deletion
- Explicit warnings before overwriting files

**Residual Risk:** LOW (requires misconfiguration)

### 6. Dependency Vulnerabilities
**Risk:** Third-party dependencies (libclang) could have vulnerabilities

**Mitigation:**
- Minimal dependencies (only libclang)
- Recommend using latest stable version
- No automatic updates (user controls versions)

**Residual Risk:** LOW

## Sensitive Information Handling

### Artifacts May Contain:
- Function names, parameter names (likely not sensitive)
- Struct layouts (likely not sensitive)
- File paths (potentially sensitive - could reveal directory structure)
- Platform details (likely not sensitive)

### Artifacts Do NOT Contain:
- Source code implementations
- Data values from memory
- Secrets, API keys, passwords

**Recommendation:** Review artifacts before sharing publicly if internal paths or proprietary interface names are sensitive.

## CI/CD Security

### Secrets Management:
- CI templates do not expose secrets in logs
- Use platform secret management (GitHub Secrets, GitLab Variables)
- Avoid hardcoding paths or credentials in config files

### Artifact Publishing:
- Reports may contain proprietary interface details
- Restrict access to CI artifacts if needed
- Be cautious publishing status badges with internal URLs

## Network Security
The verifier does NOT:
- Make network requests
- Download dependencies automatically
- Send telemetry or analytics

**Exception:** Badge URLs (shields.io) may be publicly accessible if hosted

## Recommendations for Secure Usage

### 1. Development Environment:
- ✅ Safe to use on developer workstations
- ✅ Safe to use in CI pipelines
- ⚠️ Review artifacts before sharing
- ❌ Do not run on untrusted libraries

### 2. CI Integration:
- ✅ Use platform secret management for paths
- ✅ Restrict artifact access if needed
- ⚠️ Be aware that native code runs with full privileges
- ❌ Do not verify untrusted third-party libraries automatically

### 3. Artifact Handling:
- ✅ Artifacts are safe to version control (if interface is not sensitive)
- ✅ Reports can be shared with team members
- ⚠️ Review for sensitive paths before public sharing
- ❌ Do not include API keys or secrets in headers

## Known Security Limitations
- **No Sandboxing:** Native code runs with full privileges
- **No Input Validation:** Headers are assumed to be well-formed
- **No Cryptographic Integrity:** Artifacts are not signed or verified
- **No Access Control:** File system permissions are the only protection

## Future Security Enhancements
Potential improvements (not planned for v1.0):
- Sandboxed execution (using containers or VMs)
- Artifact signing and verification
- Header validation before parsing
- Network isolation for verification runs

### 4.3 Limitations and Non-Goals

## Overview
This document explicitly states what the Polyglot FFI Contract Verifier does NOT do, known limitations, and deliberate non-goals. Understanding these boundaries is essential for setting appropriate expectations.

## Explicit Non-Goals

### 1. Functional Correctness of Native Code
**Not a Goal:** Verify that native functions implement correct business logic.

**Why:** The verifier checks FFI contract adherence (memory safety, calling conventions, ownership), not algorithmic correctness.

**Example:**
```c
// This function has correct FFI behavior but wrong logic
int add(int a, int b) {
    return a - b;  // Wrong! But FFI-safe.
}
```
The verifier will NOT detect this bug.

### 2. Static Analysis of Native Code
**Not a Goal:** Analyze native C/C++ implementation for bugs.

**Why:** The verifier tests runtime behavior via adapters, not source code analysis.

**Tools for static analysis:** Clang Static Analyzer, Coverity, PVS-Studio

### 3. Automatic Bug Fixing
**Not a Goal:** Automatically fix detected violations.

**Why:** Fixes require human judgment (fix adapter vs fix native code vs update contract).
The verifier provides recommendations, not automatic patches.

### 4. Runtime Production Enforcement
**Not a Goal:** Replace generated adapters in production with live verification.

**Why:** Full verification is too slow for production. Use generated adapters ( output) for runtime enforcement.

### 5. Cross-Language Semantic Verification
**Not a Goal:** Verify semantic equivalence between languages.
**Example:** Verify that Python binding semantics match C semantics.

**Why:** This requires formal verification, which is out of scope.

### 6. Performance Optimization of Native Code
**Not a Goal:** Suggest performance improvements for native code.

**Why:** Performance is orthogonal to correctness.

### 7. Memory Leak Detection (General)
**Not a Goal:** Detect all memory leaks in native code.

**Why:** Only ownership-transfer violations are detected. Internal leaks are not.
Use Valgrind or AddressSanitizer for comprehensive leak detection.

### 8. Concurrency Bug Detection
**Not a Goal:** Detect race conditions, deadlocks, or thread safety issues.

**Why:** Verification runs are single-threaded by design.

### 9. Binary Compatibility Verification
**Not a Goal:** Verify that compiled library matches header ABI.

**Why:** The verifier trusts that libclang reflects the compiled ABI. If compiler and header are mismatched, verification may pass incorrectly.

**Mitigation:** Use same compiler for both native library and ingestion.

## Known Limitations

### Platform Support
- **Supported:** Windows x64 (v1.0)
- **Not Supported:** Linux, macOS (future versions may add support)
- **Not Supported:** 32-bit architectures

### Language Support
- **Supported:** C interfaces
- **Partially Supported:** C++ (if interface is C-compatible with extern "C")
- **Not Supported:** C++ templates, classes, virtual functions

### Target Language Support
- **Supported:** Python adapters (v1.0)
- **Not Supported:** Rust, Go, JavaScript adapters (future versions may add support)

### Header Complexity
- **Supported:** Standard C headers
- **Limited Support:** Heavily templated headers (slow ingestion)
- **Not Supported:** Headers requiring C++ compiler (use extern "C" wrappers)

### Constraint Types
- **Supported:** Nullability, buffer sizes, struct layouts, ownership, calling conventions
- **Not Supported:** Alignment constraints beyond struct layout
- **Not Supported:** Endianness constraints
- **Not Supported:** Numeric range constraints (e.g., value must be 0-100)

### Test Coverage
- **Guaranteed:** 100% constraint coverage (every constraint tested)
- **Not Guaranteed:** 100% code path coverage in native library
- **Not Guaranteed:** All corner cases discovered

### Error Detection
- **Detects:** Contract violations, crashes, assertion failures
- **Does Not Detect:** Silent data corruption (unless it causes crash)
- **Does Not Detect:** Subtle undefined behavior (unless sanitizers enabled)

### Performance
- **Suitable For:** Development-time verification, CI pipelines
- **Not Suitable For:** Runtime production use, high-frequency testing

### Crash Detection
- **Detects:** Segfaults, access violations, illegal instructions, aborts
- **Does Not Detect:** Silent corruption, delayed crashes (after function returns)

### Ownership Tracking
- **Tracks:** Explicit ownership transfer (destroy functions, free functions)
- **Does Not Track:** Reference counting, shared ownership, custom allocators

## Edge Cases and Corner Cases

### 1. Platform-Specific Behavior
**Issue:** ABI details vary across platforms (calling conventions, struct padding).
**Limitation:** Verification on Windows does not guarantee correctness on Linux.
**Mitigation:** Run verification on target platform.

### 2. Compiler-Specific Behavior
**Issue:** Different compilers may have different padding, alignment, or calling conventions.
**Limitation:** Verification with MSVC does not guarantee correctness with GCC.
**Mitigation:** Use same compiler for verification and production.

### 3. Dynamic Linking Issues
**Issue:** Library may behave differently when statically vs dynamically linked.
**Limitation:** Verifier only tests dynamic linking (DLL/SO).

### 4. Callback Functions
**Issue:** Native code calling back into Python.
**Limitation:** Callbacks are not automatically verified (adapter does not wrap callbacks).
**Mitigation:** Manually test callback paths.

### 5. Variadic Functions
**Issue:** Functions with variable arguments (e.g., printf-style).
**Limitation:** Variadic functions are difficult to verify automatically.
**Status:** Limited support (tests only with fixed argument counts).

### 6. Function Pointers
**Issue:** Function pointers in structs or parameters.
**Limitation:** Function pointer validity cannot be verified automatically.
**Status:** Null checks only (no signature verification).

### 7. Opaque Pointers
**Issue:** Pointers to incomplete types (e.g., void* to internal struct).
**Limitation:** Cannot verify pointed-to data, only pointer nullability.

### 8. Const Correctness
**Issue:** Const qualifiers in C.
**Limitation:** Const is documented in contract but not enforced at runtime (Python/ctypes does not enforce const).

### 9. Global State
**Issue:** Native library may maintain global state.
**Limitation:** Tests are isolated but cannot detect state corruption across tests.

### 10. Timing-Dependent Bugs
**Issue:** Bugs that only manifest under specific timing (race conditions, timing attacks).
**Limitation:** Verification is deterministic and single-threaded.

## Workarounds and Alternatives

### For Functional Correctness:
- Use unit tests for native code
- Use property-based testing (e.g., Hypothesis)

### For Static Analysis:
- Use Clang Static Analyzer
- Use Coverity or PVS-Studio

### For Memory Safety:
- Compile native library with AddressSanitizer (ASan)
- Use Valgrind for leak detection

### For Concurrency:
- Use ThreadSanitizer (TSan)
- Use race detection tools

### For Performance:
- Use profiling tools (gprof, perf)
- Use benchmarking frameworks

## When NOT to Use This Tool

**❌ Do not use if:**
- You need functional correctness verification (use unit tests)
- You need static analysis (use Clang Static Analyzer)
- You need cross-platform verification (run on each platform)
- You need real-time enforcement (use generated adapters only)
- Your interface is C++ (use extern "C" wrappers first)

**✅ Use if:**
- You have C interfaces accessed from Python
- You want to detect FFI contract violations
- You want automated safety checks in CI
- You want actionable violation reports

### 4.4 Error Handling Patterns

## Overview
This document outlines the standardized error handling strategy used across the Polyglot FFI Contract Verifier. A consistent approach to error management ensures that failures are classified correctly, actionable feedback is provided to the user, and the system fails gracefully without undefined behavior.

## Error Taxonomy

The system explicitly distinguishes between three categories of errors:

### 1. User Errors (Input Validation)
Errors caused by invalid input, misconfiguration, or missing files. These are expected and should be reported with clear instructions for resolution.
- **Examples**: Missing header file, invalid JSON schema, unsupported compiler version.
- **Handling**: Catch specific exceptions, print friendly error message, exit with code `1`.
- **Traceback**: Suppressed by default (unless `--debug` is used).

### 2. System Errors (Infrastructure)
Errors caused by environmental issues, resource exhaustion, or external dependency failures.
- **Examples**: libclang crash, out of memory, file permission denied, native library load failure.
- **Handling**: Catch specific exceptions, suggest environmental fixes, exit with code `2`.
- **Traceback**: Logged to debug file.

### 3. Internal Errors (Bugs)
Unexpected states or logic errors within the verifier itself.
- **Examples**: Assertion failure, key error in internal dict, unhandled type.
- **Handling**: Catch generic `Exception` at top level, print "Internal Error" banner, exit with code `3`.
- **Traceback**: Always printed to facilitate bug reporting.

## Exception Hierarchy

All custom exceptions inherit from `PolyglotFFIError`.

```python
class PolyglotFFIError(Exception):
    """Base class for all verifier exceptions."""

class ConfigError(PolyglotFFIError):
    """Invalid user configuration."""

class IngestionError(PolyglotFFIError):
    """Failures during native interface parsing."""

class SynthesisError(PolyglotFFIError):
    """Failures during contract synthesis."""

class VerificationError(PolyglotFFIError):
    """Failures during test execution (not test failures)."""
```

## Exit Codes

The CLI uses standard exit codes to communicate status to automation tools:

| Code | Meaning |
|------|---------|
| `0`  | Success (Verification Passed) |
| `1`  | Verification Failed (Contract Violations Found) |
| `2`  | User/Config Error |
| `3`  | System/Environment Error |
| `4`  | Internal Error |

## Recovery Strategies

### 1. Verification Failures
If a verification test fails (e.g., native code crash):
- **Action**: The `MonitoredVerificationExecutor` catches the subprocess exit code.
- **Recovery**: Log the failure as a `Critical Violation` and continue to the next test.
- **Result**: The pipeline completes, but the final report status is "FAILED".

### 2. Partial Results
If the pipeline crashes mid-execution:
- **Action**: Artifacts from completed phases are persisted on disk.
- **Recovery**: User can inspect `execution_log.json` to see how far it got.
- **Restart**: Re-running the command overwrites previous artifacts safely.

## User Messaging Guidelines

Error messages should follow the **"What, Why, Fix"** pattern:

1.  **What happened**: "Could not load native library."
2.  **Why it happened**: "File 'build/lib.dll' not found."
3.  **How to fix it**: "Ensure the build path is correct and the library is compiled."

**Bad Example:**
`FileNotFoundError: [Errno 2] No such file or directory: 'lib.dll'`

**Good Example:**
`Error: Native library not found at 'lib.dll'. Please check the --library-path argument.`

## Implementation in Code

Global exception handler pattern in `polyglot_ffi_verifier.py`:

```python
def main():
    try:
        # Run pipeline
        orchestrator.run()
    except PolyglotFFIError as e:
        print(f"❌ Error: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"💥 Internal Error: {e}")
        traceback.print_exc()
        sys.exit(4)
```

### 4.5 Logging Strategy

## Overview
Standardized logging is crucial for diagnosing verification issues, understanding execution flow, and debugging integration problems. This document defines the logging strategy for the Polyglot FFI Contract Verifier.

## Logging Levels

The system uses standard Python logging levels with specific semantic meanings:

| Level | Usage | Target Audience | Example |
|-------|-------|-----------------|---------|
| `CRITICAL` | System cannot continue. Immediate exit. | User | "Disk full - cannot write report" |
| `ERROR` | Operation failed, but pipeline might proceed. | User | "Failed to parse header file" |
| `WARNING` | Something looks wrong, but using defaults. | User | "Function 'foo' has no constraints" |
| `INFO` | High-level progress steps. | User | ": Ingestion complete" |
| `DEBUG` | Detailed execution logic. | Developer | "Parsed AST node: FunctionDecl" |

## Log Output Channels

### 1. Console (Standard Output/Error)
- **Content**: `INFO` and higher.
- **Format**: Human-readable, minimal metadata.
- **Purpose**: Interactive feedback for the user.

**Format:**
```text
[INFO] Verifying contract...
[WARN] Constraint 'len' references non-existent param 'n'
```

### 2. Execution Log (`execution_log.json`)
- **Content**: Structured data about test execution.
- **Format**: JSON.
- **Purpose**: Machine-readable record of functional verification.
- **Persistence**: Persisted to `artifacts/execution_log.json`.

### 3. Debug Log (`debug_output.txt`)
- **Content**: `DEBUG` and higher.
- **Format**: Full timestamped log lines with module names.
- **Purpose**: Diagnostics internal logic and tracing flow.
- **Persistence**: Temporary file in working directory (optional).

## Contextual Logging

Logs are enriched with context where possible to aid debugging:

- **Execution ID**: Unique UUID for the run (traceable across system).
- **Phase Name**: All logs indicate the active pipeline phase.
- **Component**: The specific module generating the log.

## Best Practices for Developers

1.  **Do not log secrets**: Never log environment variables that might contain keys.
2.  **Use lazy formatting**: Use `logger.debug("Val: %s", val)` instead of f-strings for performance.
3.  **Log boundaries**: Log entry and exit of major phases.
4.  **Structured info**: When logging about a function or constraint, include its ID.

## Log Parsing for Automation

Do not rely on parsing console output for automation. Use the structured artifacts instead:
- **Status Checks**: Parse `ci_summary.json`.
- **Test Results**: Parse `execution_log.json`.
- **Diagnostics**: Parse `diagnostics.json`.

Console output format is subject to change for UX improvements.

### 4.6 Best Practices

## Overview
This guide provides practical recommendations for users and maintainers to get the most out of the Polyglot FFI Contract Verifier. Following these practices ensures reliable, efficient, and maintainable verification pipelines.

## For Users

### 1. Workflow Integration
- **Run Locally First**: Always run verification locally (`polyglot_ffi_verifier.py verify`) before pushing to CI.
- **Fail Fast**: Configure your CI to run FFI verification early in the pipeline, as native crashes can destabilize later steps.
- **Use Badges**: Add the status badge to your README to keep FFI safety visible to the team.

### 2. Header Management
- **Self-Contained Headers**: Ensure your interface header includes all necessary types. The ingestor is not a full compiler preprocessor.
- **Stable Interfaces**: Avoid changing function signatures frequently. If you do, regenerate the contract and adapters.
- **Documentation Comments**: Use Doxygen-style comments in your C header. While currently ignored, future versions may use them for constraint inference.

### 3. Contract Management
- **Version Control Contracts**: Check `contract.json` into git. It is the source of truth for your interface safety.
- **Review Changes**: When `contract.json` changes, review the diff manually to ensure valid constraints weren't lost.
- **Baseline Comparison**: Use `compare-contracts` command to detect accidental breaking changes.

### 4. Test Data Management
- **Deterministic Tests**: Ensure your native library behavior is deterministic for the same inputs.
- **Mock External Dependencies**: If your native library calls network/DB, mock these out for FFI verification. The verifier checks the *boundary*, not the backend.

### 5. Diagnostics
- **Enable Debugging**: Use `--debug` flag if ingestion is failing. It prints libclang details.
- **Isolate Crashes**: If verification hangs, check the `execution_log.json` to see which test ran last. The crash is likely in that function.

## For Maintainers

### 1. Extending the System
- **Follow Phase Isolation**: If adding a feature, place it in the appropriate phase. Do not mix ingestion logic with verification logic.
- **Update Artifacts**: If you change an artifact schema, update the version number in `ProvenanceMetadata`.
- **Add Validation**: Every new phase must have a corresponding `validate_*.py` script.

### 2. Code Style
- **Type Hints**: Use Python type hints everywhere.
- **Docstrings**: Document every class and public method.
- **No Global State**: Pass `ExecutionContext` explicitly. Do not rely on module-level variables.

### 3. Release Process
- **Run Full Validation**: Execute all `validate_*.py` scripts before tagging a release.
- **Update Documentation**: Ensure all `docs/*.md` files are current with code changes.
- **Semantic Versioning**: Bump major version if `contract.json` schema changes incompatibly.

### 4. Dependencies
- **Pin Versions**: Pin `libclang` and `PyYAML` versions in `requirements.txt` to avoid upstream breakage.
- **Vendor Critical Libs**: If a library is small and critical, consider vendoring it to reduce install friction.

### 5.2 End-to-End Validation

This document explains how to validate the Polyglot FFI Contract Verifier system.

## Integration Tests

The integration test suite (`tests/integration/test_end_to_end.py`) does the following:

1.  Creates a temporary C interface (`test_interface.h`).
2.  Runs the **FULL PIPELINE** from ingestion to reporting.
3.  Mocks the native library execution (for portability) but validates all pipeline logic.
4.  Asserts that critical bugs are found and reported correcty.

### Running Integration Tests

```bash
python tests/integration/test_end_to_end.py
```

**Expected Output:**
```text
END-TO-END INTEGRATION TEST
...
✓ END-TO-END INTEGRATION TEST PASSED
```

## Demo

The demo (`examples/demo/`) is a user-friendly showcase.

### Running the Demo

```bash
python examples/demo/run_demo.py
```

The script simulates the verification of a vulnerable library, showing exactly what users encounter when the tool finds bugs.

## Diagnostics

### "Libclang analysis failed"
- If you see this warning in integration tests, it means `libclang` is not installed or configured.
- The test will fall back to using a mock interface to verify the rest of the pipeline.
- To fix: `pip install libclang` and ensure LLVM is installed.

### "Context setup failed"
- Ensure you are running from the project root or PYTHONPATH includes `src`.

## Validation Script

Run the all-in-one validation script to verify everything:

```bash
python validate_end_to_end_integration.py
```

This runs:
1. Integration Test
2. Demo Simulation
3. Regression Tests

## Regression Tests

Located in `tests/regression/`, these guard against:
- **Determinism**: Ensuring synthesis and generation produce identical outputs for identical inputs.
- **Consistency**: Ensuring artifact structures remain valid properly.

Run specifically:
```bash
python tests/regression/test_system_stability.py
```

---

## 4 OPERATIONAL GUIDES

*See individual sections below for operational guidance.*

---

## 5 INTEGRATION

*See individual sections below for integration guidance.*

---

## 6 APPENDICES

### 6.1 Glossary

**ABI** - Application Binary Interface  
**FFI** - Foreign Function Interface  
**IR** - Intermediate Representation  
**libclang** - C language family frontend for LLVM  
**ctypes** - Python foreign function interface library  
**MSVC** - Microsoft Visual C++ Compiler  
**Provenance** - Traceability of data origin and transformations  
**Artifact** - Immutable output file from a pipeline stage  

### 6.2 References

- [libclang documentation](https://libclang.readthedocs.io/)
- [Python ctypes documentation](https://docs.python.org/3/library/ctypes.html)
- [LLVM Project](https://llvm.org/)
- [Microsoft ABI Documentation](https://docs.microsoft.com/en-us/cpp/build/reference/)

### 6.3 History

**1.0.0** (2026-02-02)
- Initial release
- Complete 12-phase implementation
- Full documentation consolidation
- All 19 source documents merged

---

**End of System Architecture Documentation**

*This document was automatically created by consolidating 19 source documentation files.*  
*For the modular documentation (for development), see: docs/ directory*  
*For the modular code (for development), see: polyglot_ffi_verifier/ directory*  
*For the consolidated code, see: system_architecture.py*

## 6. GLOSSARY

### Core Terms

**ABI (Application Binary Interface)**  
The low-level interface between program components, defining calling conventions, data layout, and system interactions at the binary level.

**Artifact**  
An immutable file produced by a pipeline stage (e.g., native_interface.json, contract.json) that serves as input for subsequent stages.

**Calling Convention**  
The protocol for how functions receive parameters and return values (e.g., cdecl, stdcall, fastcall, win64).

**Contract**  
A machine-readable specification of correctness constraints for FFI functions, including nullability, ownership, lifetime, and buffer size requirements.

**Constraint**  
A single verifiable requirement in an FFI contract (e.g., "parameter 0 must not be NULL").

**Determinism**  
The property that identical inputs always produce identical outputs, critical for reproducible verification.

**Execution Context**  
An immutable record of the environment in which verification runs, including platform details, timestamp, and execution ID.

**FFI (Foreign Function Interface)**  
The mechanism by which code written in one programming language can call functions written in another language.

**Immutability**  
The property that once created, an artifact or context cannot be modified, ensuring data integrity and provenance.

**IR (Intermediate Representation)**  
A normalized, platform-agnostic representation of native interfaces used as input for contract synthesis.

**libclang**  
The C language family frontend for LLVM, used to parse C headers and extract ABI information.

**Padding**  
Extra bytes inserted by compilers between struct fields to satisfy alignment requirements.

**Provenance**  
The complete history and metadata of an artifact, tracking which execution context and inputs produced it.

**Struct Layout**  
The specific arrangement of fields in a struct, including sizes, offsets, padding, and total size.

**Type Resolver**  
Component that transitively resolves typedefs to their underlying primitive types for canonical representation.

### Phase-Specific Terms

**Constraint Derivation**  
The process of analyzing function signatures and types to generate correctness constraints.

**Heuristic Analysis**  
Using naming patterns (e.g., `create_`, `free_`, `optional_`) to infer ownership and nullability semantics.

**Ownership Tracking**  
Monitoring whether pointers are borrowed (caller retains) or transferred (callee takes ownership).

**Crash Detection**  
Using subprocess isolation to detect and classify native crashes (segfaults, access violations).

**Root Cause Analysis**  
Mapping runtime failures back to specific contract violations and providing actionable diagnostics.

### Operational Terms

**Baseline Contract**  
A reference contract from a previous version, used for compatibility analysis.

**Breaking Change**  
A modification that violates existing contracts and requires consumer code updates.

**Semantic Change**  
A modification that alters behavior without breaking the ABI (e.g., adding constraints).

**Compatible Change**  
A modification that maintains backward compatibility (e.g., relaxing constraints).

**Verification Run**  
A complete execution of the pipeline from ingestion through report generation.

---

## 7. TROUBLESHOOTING

### 7.1 Common Issues

#### Issue: libclang not found

**Symptom:**
```
ImportError: libclang not found
```

**Solution:**
```bash
# Install libclang
pip install libclang

# Set LIBCLANG_PATH if needed
# Windows:
set LIBCLANG_PATH=C:\Program Files\LLVM\bin\libclang.dll

# Linux:
export LIBCLANG_PATH=/usr/lib/llvm-16/lib/libclang.so
```

#### Issue: Native interface ingestion fails

**Symptom:**
```
ERROR: Failed to parse header file
```

**Solutions:**
- Ensure MSVC compiler is installed (Windows)
- Check header file syntax (must be valid C)
- Verify include paths are correct
- Check for missing dependencies

**Debug command:**
```bash
clang -fsyntax-only -v interface.h
```

#### Issue: Tests fail with "Import Error"

**Symptom:**
```
ModuleNotFoundError: No module named 'polyglot_ffi_verifier'
```

**Solution:**
```bash
# Install package in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Issue: Verification runs slowly

**Symptom:** Verification takes more than 5 minutes for small interfaces

**Solutions:**
- Reduce test count in test plan
- Disable crash detection (use `--no-crash-detection`)
- Run on faster hardware
- Check for infinite loops in test code

#### Issue: False positive violations

**Symptom:** Diagnostics report violations that don't exist

**Solutions:**
- Review contract synthesis (may be overly conservative)
- Add manual contract overrides
- Adjust heuristic thresholds
- Check for platform-specific behavior

#### Issue: Crash detector doesn't capture crashes

**Symptom:** Tests crash but no crash reports generated

**Solutions:**
- Ensure subprocess isolation is enabled
- Check platform-specific crash handlers (Windows SEH, Linux signals)
- Verify crash report directory permissions
- Check for signal masking in test code

### 7.2 Debugging Commands

**Check execution context:**
```bash
python system_architecture.py context
```

**Verbose logging:**
```bash
python system_architecture.py verify interface.h library.dll --verbose
```

### 7.3 Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 1 | Precondition error | Fix input files |
| 2 | Tooling error | Check dependencies |
| 3 | Verification failure | Review violations |
| 4 | Internal error | Report bug |
| 5 | Timeout | Increase timeout or simplify |

### 7.4 Getting Help

**Check logs:**
```bash
cat artifacts/verification.log
```

**Report issues:**
- GitHub Issues: https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/issues
- Include: execution_id, platform info, error messages, logs

---

## 8. CONFIGURATION MANAGEMENT

### 8.1 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LIBCLANG_PATH` | Path to libclang library | Auto-detect |
| `FFI_VERIFIER_OUTPUT` | Output directory | `artifacts/` |
| `FFI_VERIFIER_TIMEOUT` | Global timeout (seconds) | 300 |
| `FFI_VERIFIER_VERBOSE` | Enable verbose logging | false |

**Usage:**
```bash
export LIBCLANG_PATH=/usr/lib/llvm-16/lib/libclang.so
export FFI_VERIFIER_VERBOSE=true
python system_architecture.py verify interface.h library.dll
```

### 8.2 Command-Line Overrides

Config can be overridden via CLI:

```bash
python system_architecture.py verify interface.h library.dll \
  --output-dir custom_artifacts/ \
  --timeout 600 \
  --verbose
```

**Priority order (highest to lowest):**
1. Command-line arguments
2. Environment variables
3. Built-in defaults

---

## 9. RESOURCE MANAGEMENT

### 9.1 Temporary File Handling

**Temporary files created during execution:**
- Subprocess test runners: `artifacts/temp/test_runner_<pid>.py`
- Crash dumps: `artifacts/crashes/crash_<timestamp>_<pid>.dmp`
- Compilation intermediates: `artifacts/temp/compile_<hash>.o`

**Automatic cleanup:**
- Temporary files are deleted on successful completion
- Crash dumps are preserved for diagnostics

**Manual cleanup:**
```bash
# Clean all temporary files
rm -rf artifacts/temp/

# Clean all artifacts
rm -rf artifacts/
```

### 9.2 Resource Limits

**Memory:**
- Maximum per test: 1 GB (configurable)
- Maximum total: System RAM - 2 GB

**Disk:**
- Artifacts directory: Unlimited (user responsibility)
- Temporary files: Auto-cleaned, max 1 GB

**Processes:**
- Concurrent tests: 1 (sequential execution in v1.0)
- Maximum subprocess lifetime: 10 seconds per test

**File handles:**
- Maximum open files: OS limit
- Artifacts use append-only logging (minimal handles)

### 9.3 Artifact Retention

**Default retention policy:**
- Artifacts: Preserved indefinitely
- Logs: Preserved indefinitely
- Crash dumps: Preserved indefinitely

**Manual retention management:**
```bash
# Delete artifacts older than 30 days
find artifacts/ -mtime +30 -delete

# Archive artifacts
tar -czf artifacts_backup_$(date +%Y%m%d).tar.gz artifacts/
```

---

## APPENDIX A: VERSION HISTORY

### Version 1.0.0 (2026-02-02)

**Initial Release**

**Features:**
- Complete 12-phase verification pipeline
- Native interface ingestion via libclang
- IR normalization with typedef resolution
- Contract synthesis with heuristic analysis
- Contract versioning and compatibility checking
- Python adapter generation with ctypes
- Comprehensive test plan generation
- Deterministic verification execution
- Runtime crash detection and monitoring
- Failure diagnostics and root cause analysis
- Multi-format report generation (HTML, Markdown, JSON)
- CI/CD integration (GitHub Actions, GitLab CI, Jenkins)

**Platform Support:**
- Windows x64 (primary)

**Dependencies:**
- Python 3.11+
- libclang 16.0+
- MSVC compiler (Windows)

**Known Limitations:**
- Windows x64 only for v1.0
- C interfaces only (C++ via extern "C")
- Python adapters only
- Single-threaded execution

**Documentation:**
- Complete system architecture specification
- All 12 phase implementation guides
- Performance, security, and operational guides
- CI/CD integration examples
- Comprehensive test suite

---

## APPENDIX B: FUTURE ROADMAP

### Version 1.1.0 (Planned: Q2 2026)

- Linux x64 support
- macOS support (ARM and x64)
- Parallel test execution
- Incremental verification
- Caching layer

### Version 2.0.0 (Planned: Q3 2026)

- C++ support (full, not just extern "C")
- Rust adapter generation
- Go adapter generation
- Multi-language test generation
- Performance optimizations (10x faster)

### Version 3.0.0 (Planned: Q4 2026)

- Distributed verification
- Cloud integration (AWS, Azure, GCP)
- Real-time monitoring dashboard
- Automated contract learning from tests
- Machine learning-based heuristics

---
