# Polyglot FFI Contract Verifier (PFCV)

**High-assurance automated verification for cross-language foreign function interfaces.**

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/actions)
[![Test Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](tests/)

---

## What is PFCV?

Foreign Function Interface (FFI) safety is notoriously difficult. Modern software systems often combine high-level languages (Python, Java, Go) with performance-critical native code (C, Rust, C++). Discrepancies in memory layout, calling conventions, or pointer nullability between these layers lead to catastrophic crashes, memory corruption, and security vulnerabilities.

**Polyglot FFI Contract Verifier (PFCV)** is a comprehensive system designed to eliminate FFI mismatches through automated contract synthesis and validation. It provides a formal, verifiable bridge between high-level language expectations and low-level native implementations.

### How it Works
PFCV implements a rigorous 7-module pipeline that extracts semantics from native code, normalizes them into a language-agnostic Intermediate Representation (IR), synthesizes enforceable contracts, and validates them against target implementations.

```text
[Native Header/Library] 
          ↓
[Module 04: Ingestion] ➔ [Module 05: Normalization]
          ↓
[Intermediate Representation (IR)]
          ↓
[Module 07: Synthesis] ➔ [Module 06: Contract Schema]
          ↓
[FFI Contracts (.json/.yaml)]
          ↓
[Module 02: Pipeline] ➔ [Module 01: Architecture]
          ↓
[FFI Verification Report]
```

---

## Complete Module Overview

| Component | Status | Purpose |
| :--- | :--- | :--- |
| **Module 01: System Architecture** | ✅ Complete | Formal system design and architectural constraints mapping. |
| **Module 02: Verification Pipeline** | ✅ Complete | Orchestration of the end-to-end verification workflow. |
| **Module 03: Build Process** | ✅ Complete | Integration with native build systems (Make, CMake, Cargo). |
| **Module 04: Native Interface Ingestion** | ✅ Complete | Extraction of symbols and types from C/C++/Rust. |
| **Module 05: IR Normalization** | ✅ Complete | Normalization into a unified, language-agnostic type system. |
| **Module 06: Contract Schema** | ✅ Complete | Formal schema for FFI safety contracts and enforcement. |
| **Module 07: Contract Synthesis** | ✅ Complete | Deterministic generation of contracts from IR analysis. |

---

## Features

- 🌐 **Multi-Language Support**: Extract interfaces from C headers, C++ binaries, and Rust crates.
- 🎯 **Deterministic Synthesis**: 100% reproducible contract generation using versioned rules.
- 🔍 **Contextual Intelligence**: Interface-wide pattern detection for nullability, ownership, and array-length relationships.
- 🚀 **High Performance**: Synthesize contracts for 1000+ functions in under 60 seconds.
- ✅ **Rigorous Validation**: Schema-based validation ensures contracts are well-formed and consistent.
- 🛠️ **Developer Friendly**: 16 CLI commands for granular control over the entire verification pipeline.
- 🏗️ **Production Ready**: Full support for CI/CD integration, regression detection, and monitoring.

---

## Quick Start (5 Minutes)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier.git
cd Polyglot-FFI-Contract-Verifier

# Install core dependencies
pip install -e .
```

### 2. Complete Workflow Example

```bash
# 1. Extract IR from a C library header
pfcv-ir extract include/mylibrary.h -o ir/

# 2. Synthesize an FFI contract from the IR
pfcv-synth synthesize ir/mylibrary.json -o contract.json

# 3. Validate the generated contract
pfcv-synth validate contract.json

# 4. Run the full verification pipeline
python -m verification_pipeline --contract contract.json --lib lib/mylibrary.so
```

---

## Documentation Map

- 📘 **User Guide**: [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - Deep dive into project usage.
- 📖 **API Reference**: Detailed references for [Module 05](docs/module_05/api-reference.md), [Module 06](docs/API_REFERENCE.md), and [Module 07](modules/module_07_contract_synthesis/SYNTHESIS_ENGINE.md).
- 🚀 **Deployment Guide**: [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) - How to run at scale.
- 🔧 **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and fixes.
- 🏛️ **Architecture**: [docs/ARCHITECTURE_DEEP_DIVE.md](docs/ARCHITECTURE_DEEP_DIVE.md) - The math and logic behind PFCV.

---

## Project Status

- **Current Version**: 1.0.0 (Production Stable)
- **Total Tests**: 2,220+ passing
- **Test Coverage**: > 95%
- **Status**: Ready for production deployment in security-critical FFI environments.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on development setup, testing standards, and pull request processes.

---

## License & Acknowledgments

- **License**: Released under the [MIT License](LICENSE).
- **Credits**: Developed by the PFCV Team. Special thanks to the open-source community for the robust foundations in `libclang`, `click`, and `rich`.

---
© 2026 PFCV Team. All rights reserved.
