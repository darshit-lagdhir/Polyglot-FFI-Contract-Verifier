# PFCV Modules

This directory contains the core implementation of the **Polyglot FFI Contract Verifier**. The project is structured into 7 primary modules, each responsible for a specific stage of the high-assurance verification pipeline.

## 🏗️ Module Architecture

| Module | Identifier | Status | Responsibility |
| :--- | :--- | :--- | :--- |
| **Module 01** | `ffi_verifier` | ✅ 1.0.0 | System-level architecture and formal safety constraints. |
| **Module 02** | `verification_pipeline` | ✅ 1.0.0 | End-to-end orchestration and reporting infrastructure. |
| **Module 03** | `build_process` | ✅ 1.0.0 | Native build system hooks (Make, CMake, Cargo). |
| **Module 04** | `native_ingestion` | ✅ 1.0.0 | Clang-based symbol and type extraction from native source. |
| **Module 05** | `ir_normalization` | ✅ 1.0.0 | Universal IR projection and language-agnostic type safety. |
| **Module 06** | `contract_schema` | ✅ 1.0.0 | Formal schema definition and runtime enforcement adapters. |
| **Module 07** | `contract_synthesis` | ✅ 1.0.0 | Intelligence layer for automated contract generation. |

---

## 🛠️ Module Development Guidelines

Each module in this directory follows a strict layout:
- `modules/module_XX_<name>/`: Root directory for the module.
- `modules/module_XX_<name>/__init__.py`: Public API exports.
- `modules/module_XX_<name>/<name>.py`: Core logic implementation.
- `modules/module_XX_<name>/<NAME>.md`: Technical specification and documentation.

### Standards
1.  **Isolation**: Modules should interact via clearly defined bridges (e.g., Module 05 -> Module 07 bridge).
2.  **Type Safety**: All public APIs must utilize Python type hints.
3.  **Documentation**: Every module must maintain a `CODE_SPEC.md` or equivalent technical reference.

---

## 🚀 Working with Modules

### Installation
You can install the entire suite from the project root:
```bash
pip install -e .
```

### Direct Usage (Internal)
If you are developing a specific module, you can add it to your path:
```python
import sys
from pathlib import Path
sys.path.append(str(Path("modules/module_05_ir_normalization")))
```

---
© 2026 PFCV Team.
