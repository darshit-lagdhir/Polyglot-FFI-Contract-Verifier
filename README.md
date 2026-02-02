# Polyglot FFI Contract Verifier

**From "it compiles" to "it is actually correct" across language boundaries.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-lightgrey.svg)](https://www.microsoft.com/windows)

---

## 🎯 Overview

The Polyglot FFI Contract Verifier makes foreign function interface (FFI) boundaries **explicit, testable, and explainable**. It verifies that assumptions made by one language runtime about another are actually valid at runtime.

---

## 🔥 The Problem

Modern polyglot software combines multiple programming languages, but FFI boundaries remain dangerously unverified:

- ❌ **Code compiles** but silently violates memory layout, alignment, or calling conventions
- ❌ **Bugs surface late** under specific workloads or compiler versions
- ❌ **Failures are severe** - crashes, data corruption, security vulnerabilities
- ❌ **Debugging is expensive** - requires deep ABI knowledge across languages

---

## ✅ The Solution

Reframe FFI correctness as a **contract verification problem**:

1. **Extract** native interface via compiler frontends
2. **Synthesize** explicit FFI contracts encoding all assumptions
3. **Generate** runtime verification adapters and targeted tests
4. **Execute** deterministic verification and detect violations
5. **Report** failures in terms of violated assumptions, not crashes

---

## 🌟 Key Features

- ✅ **Explicit Contracts** - Makes implicit FFI assumptions machine-readable
- ✅ **Deterministic Verification** - Reproducible results across machines and time
- ✅ **Semantic Reporting** - Explains violations in plain language, not ABI jargon
- ✅ **Artifact-Driven** - All intermediate outputs are inspectable and versioned
- ✅ **Incremental Adoption** - Verify individual functions or entire interfaces
- ✅ **CI Integration Ready** - Machine-readable outputs for automated workflows

---

## 📦 Module Architecture

This project is organized into **28 technical modules**, each addressing a specific aspect of FFI verification:

### **Module Status**

| Module | Name | Status | Progress |
|--------|------|--------|----------|
| 01 | FFI Contract Verifier | ✅ COMPLETE | 100% |
| 02 | Verification Pipeline | 🔄 IN PROGRESS | 75% (15/20 prompts) |
| 03-28 | Various Technical Modules | 📋 PLANNED | 0% |

**Overall Progress:** 2/28 modules started (7%)

See [`modules/README.md`](modules/README.md) for complete module list and details.

---

## 🚀 Quick Start

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

# Install package
pip install -e .

# Verify installation
polyglot-ffi-verifier --version
```

### Basic Usage

#### Option 1: Use Module 01 (Consolidated)

```bash
# Run complete verification
python modules/module_01_ffi_verifier/system_architecture.py verify interface.h library.dll

# Show execution context
python modules/module_01_ffi_verifier/system_architecture.py context
```

#### Option 2: Use Installed Package (Modular)

```bash
# Full verification pipeline
python -m polyglot_ffi_verifier verify interface.h library.dll

# Individual stages
python -m polyglot_ffi_verifier ingest interface.h library.dll
python -m polyglot_ffi_verifier synthesize
python -m polyglot_ffi_verifier generate-tests
```

---

## 📂 Project Structure

```
Polyglot-FFI-Contract-Verifier/
├── modules/                      # 28 Technical Modules (self-contained)
│   ├── module_01_ffi_verifier/   # ✅ Complete
│   ├── module_02_verification_pipeline/  # 🔄 In Progress
│   ├── module_03_.../            # 📋 Planned
│   └── ...
│
├── polyglot_ffi_verifier/        # Modular packacge (for pip install)
│   ├── __init__.py
│   ├── context.py
│   ├── pipeline.py
│   ├── ingestion.py
│   └── ...
│
├── tests/                        # Test suite
├── examples/                     # Demo usage
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── configs/                      # Config
├── .github/                      # CI/CD
├── README.md                     # This file
├── setup.py                      # Install
└── requirements.txt              # Dependencies
```

---

## 🏗️ Architecture Principles

- **Immutability** - Artifacts never modified after creation
- **Explicitness** - No implicit assumptions or hidden behavior
- **Determinism** - Identical inputs → identical outputs
- **Artifact-Driven** - All communication through explicit artifacts
- **Failure Isolation** - Errors classified and handled appropriately
- **Provenance Tracking** - Full traceability from inputs to outputs

---

## 📚 Documentation

### Module Documentation
- [**Module 01: FFI Contract Verifier**](modules/module_01_ffi_verifier/SYSTEM_ARCHITECTURE.md) - Complete system implementation
- [**Module 02: Verification Pipeline**](modules/module_02_verification_pipeline/VERIFICATION_PIPELINE.md) - Formal pipeline architecture
- [**Modules Overview**](modules/README.md) - All 28 modules

### Implementation Guides
- **: Orchestration** - Execution context
- **: Ingestion** - Native interface extraction
- **Additional Docs** - Detailed implementation guides

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_ingestion.py -v
pytest tests/test_synthesis.py -v

# Run integration tests
pytest tests/integration/ -v

# Quick smoke test
python tests/test_quick_smoke.py
```

---

## 🎯 Current Status

### Module 01: ✅ Complete (100%)
- Execution context & orchestration
- Native interface ingestion
- IR normalization
- Contract synthesis
- Adapter generation
- Test generation
- Verification execution
- Diagnostics & reporting
- CI/CD integration

### Module 02: 🔄 In Progress (75%)
- Pipeline philosophy & formal model ✅
- Stage state machines & artifact validation ✅
- Artifact schemas & incremental verification ✅
- Native Interface Ingestion Stage ✅
- IR Normalization Stage ✅
- Contract Synthesis Stage ✅
- Adapter Generation Stage ✅
- Test Plan Generation Stage ✅
- Verification Execution Stage ✅
- Diagnostics & Reporting Stage ✅
- Pipeline Completion & Integration ✅
- Advanced Features - Caching & Performance ✅
- Advanced Features - Extensibility & Customization ✅
- Documentation & Examples ✅
- Testing & Quality Assurance ✅
- Remaining 5 prompts in progress

### Modules 03-28: 📋 Planned

---

## 🤝 Contributing

This project is developed as part of the **AMD Slingshot Hackathon 2026**. Each of the 28 modules is implemented through detailed prompts following a structured approach.

Contributions are welcome! Please:
1. Review `CONTRIBUTING.md`
2. Check module status in `modules/README.md`
3. Submit issues or pull requests

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Developed for **AMD Slingshot Hackathon 2026**
- Inspired by the need for rigorous FFI verification in polyglot systems

---

## 📞 Contact

For questions or feedback:
- **GitHub Issues:** [https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/issues](https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/issues)
- **Discussions:** [https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/discussions](https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/discussions)

**Project Status:** 🔄 Active Development | **Modules Complete:** 1/28 (3.6%)
