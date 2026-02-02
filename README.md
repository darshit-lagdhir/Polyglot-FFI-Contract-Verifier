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

## Consolidated Distribution

For maximum portability, ease of presentation, and single-file distribution, complete consolidated versions are available in the `modules/` directory:

### 📄 Module 01: FFI Contract Verifier

**Location:** `modules/module_01_ffi_verifier/`

**Files:**
- `system_architecture.py` - Single-file Python distribution containing all 12 phases (~5,700 lines)
- `SYSTEM_ARCHITECTURE.md` - Complete technical specification (~3,500 lines, 100% complete)

**Usage:**
```bash
# Run from project root
python modules/module_01_ffi_verifier/system_architecture.py verify interface.h library.dll
python modules/module_01_ffi_verifier/system_architecture.py context

# Or use the installed package
python -m polyglot_ffi_verifier verify interface.h library.dll
```

**Advantages:**
- ✅ **Self-contained** - No import issues, works standalone
- ✅ **Portable** - Just copy the module folder and run
- ✅ **Demo-ready** - Perfect for hackathon presentations
- ✅ **Complete** - All 60+ classes, 200+ functions included
- ✅ **Tested** - All tests pass identically to modular version
- ✅ **100% Documented** - Complete technical specification

### 📦 Project Modules Structure

This project contains **28 modules** total:

```
modules/
├── module_01_ffi_verifier/     ✅ COMPLETE (100%)
│   ├── system_architecture.py
│   └── SYSTEM_ARCHITECTURE.md
├── module_02_<name>/           📋 PLANNED
├── module_03_<name>/           📋 PLANNED
...
└── module_28_<name>/           📋 PLANNED
```

**Progress:**
- ✅ **Completed:** 1/28 modules (Module 01)
- 📋 **Remaining:** 27 modules
- 📊 **Total Scope:** ~56,000 words documentation + implementations

See [`modules/README.md`](modules/README.md) for complete module overview.

### When to Use What

**Use consolidated module files (`modules/module_01_ffi_verifier/`) when:**
- 🎯 Demonstrating the system to judges/reviewers
- 📤 Sharing with someone quickly
- 🚀 Deploying without pip install
- 📦 Vendoring into another project
- 📖 Reading documentation linearly

**Use modular structure (`polyglot_ffi_verifier/`, `docs/`) when:**
- 🔧 Developing or extending the system
- 📦 Installing via pip
- 🗂️ Need modular structure for maintenance
- 🔍 Navigating code with IDE

**Both versions are functionally identical and kept in sync.**

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
