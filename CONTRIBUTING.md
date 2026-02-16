# Contributing to Polyglot FFI Contract Verifier

Thank you for your interest in contributing to the **Polyglot FFI Contract Verifier (PFCV)**! We are building a high-assurance bridge for the multi-language ecosystem, and we welcome your expertise.

---

## 🧭 Project Navigation
PFCV is organized as a monorepo with 7 core modules:
- `modules/module_01_ffi_verifier`: System Architecture
- `modules/module_02_verification_pipeline`: Orchestration
- `modules/module_03_build_process`: Build Systems
- `modules/module_04_native_interface_ingestion`: Ingestion
- `modules/module_05_ir_normalization`: IR / Types
- `modules/module_06_contract_schema`: Schema / Enforcement
- `modules/module_07_contract_synthesis`: Synthesis Engine

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.8+ (3.11+ recommended)
- `pip` and `venv`
- (Optional) `libclang` for Module 04 development

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier.git
cd Polyglot-FFI-Contract-Verifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

---

## 🧪 Testing Standards
We maintain a massive test suite (>2,200 tests) to ensure FFI safety.
- **Run all tests**: `pytest tests/`
- **Coverage Requirement**: New features must aim for **> 85% coverage**.
- **Style**: We use **Black** for formatting and **Mypy** for type checking.

---

## 📬 Pull Request Process
1.  **Issue First**: Please open an issue to discuss significant changes before starting work.
2.  **Branching**: Use `feat/` or `fix/` prefixes for your branches.
3.  **Tests**: Your code must pass all existing tests and add new ones for the fix/feature.
4.  **Documentation**: Update the relevant `.md` files in `docs/` or the module directory.
5.  **Review**: At least one maintainer must approve your PR before merging.

---

## 📜 Commit Message Format
We follow the conventional commits format: `type(module): description`
- `feat(module_07): add buffer-size pattern detection`
- `fix(module_05): correct alignment for nested unions`
- `docs(root): improve installation instructions`

---

## ⚖️ Code of Conduct
By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---
Thank you for contributing to the future of safe FFI! 🚀