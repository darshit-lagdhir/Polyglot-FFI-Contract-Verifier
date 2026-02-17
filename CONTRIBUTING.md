# Contributing to Polyglot FFI Contract Verifier

Thank you for your interest in contributing to the **Polyglot FFI Contract Verifier (PFCV)**! We are building a high-assurance bridge for the multi-language ecosystem, and we welcome your expertise.

---

## 🧭 Project Navigation
PFCV is organized as a monorepo with 8 core modules:
- `modules/module_01_ffi_verifier`: System Architecture
- `modules/module_02_verification_pipeline`: Orchestration
- `modules/module_03_build_process`: Build Systems
- `modules/module_04_native_interface_ingestion`: Ingestion
- `modules/module_05_ir_normalization`: IR / Types
- `modules/module_06_contract_schema`: Schema / Enforcement
- `modules/module_07_contract_synthesis`: Synthesis Engine
- `modules/module_08_language_adapter`: Multi-Language Adapters

---

## 🛠️ Development Setup

### 1. Prerequisites
- **Python 3.8+** (3.11+ recommended)
- **pip** and **venv**
- **libclang** (required for Module 04 development)
- **Rust Toolchain** (required for Rust adapter development)
- **C++17 Compiler** (required for C++ adapter development)

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier.git
cd Polyglot-FFI-Contract-Verifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

---

## 🧪 Testing Standards
We maintain a massive test suite (**2,220+ tests**) to ensure FFI safety.
- **Run all tests**: `pytest tests/`
- **Coverage**: All new code must maintain the **>95% coverage** baseline.
- **Performance**: New validation predicates must be benchmarked to ensure they don't break the <5% overhead target.

---

## 🚔 Code Style & Linting
- **Python**: PEP 8 compliance, Black formatting, and strict Mypy type hints.
- **Rust**: Follow `rustfmt` and `clippy` standards for Rust adapter code.
- **C++**: Follow `clang-format` (LLVM style) for C++ adapter components.

---

## 📬 Pull Request Process
1.  **Issue First**: Please open an issue to discuss significant changes before starting work.
2.  **Branching**: Use `feat/`, `fix/`, or `docs/` prefixes for your branches.
3.  **Tests**: Your code must pass all 2,220+ existing tests and include comprehensive new tests.
4.  **Documentation**: Update the relevant `.md` files in `docs/` and root.
5.  **Review**: At least one maintainer must approve your PR before merging.

---

## 📜 Commit Message Format
We follow the conventional commits format: `type(module): description`
- `feat(module_08): add rust ownership tracking`
- `fix(module_04): correct struct alignment on windows`
- `docs(root): update readme for v1.0.0`

---

## 🆕 Adding a New Language Adapter
To add a new language adapter (e.g., Go, Java):
1. Create a sub-package in `modules/module_08_language_adapter/`.
2. Implement the `LanguageAdapter` base class.
3. Add the language to the `UniversalType` system in `cross_language.py`.
4. Provide a full suite of implementation tests (refer to `tests/test_rust_adapter.py` for a template).

---

## ⚖️ Code of Conduct
By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

Thank you for contributing to the future of safe FFI! 🚀