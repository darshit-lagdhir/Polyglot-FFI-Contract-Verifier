# Contributing to Polyglot FFI Contract Verifier

Thank you for your interest in contributing to PFCV! We are excited to build the future of FFI safety together.

This project is organized into 7 specialized modules. Whether you're interested in type normalization, compiler technology, or high-performance synthesis, there's a place for you.

---

## Code of Conduct
This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## Getting Started

### 1. Setting Up Your Development Environment

```bash
# Clone the repository
git clone https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier.git
cd Polyglot-FFI-Contract-Verifier

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install the project in editable mode with development dependencies
pip install -e ".[dev]"
```

### 2. Module Development
PFCV is a multi-module project. When working on a specific module, we recommend installing its specific dev dependencies:

- **Module 05 (IR)**: `pip install -e "modules/module_05_ir_normalization[dev]"`
- **Module 06 (Schema)**: `pip install -e "modules/module_06_contract_schema[dev]"`
- **Module 07 (Synthesis)**: `pip install -e "modules/module_07_contract_synthesis[dev]"`

---

## Development Workflow

### Running Tests
We use `pytest` for our massive test suite (2,220+ tests).

```bash
# Run all tests
pytest tests/ -v

# Run module-specific tests
pytest tests/tests.py -k "module_07" -v
```

### Coding Standards
- **Python Version**: 3.11+
- **Style**: [Black](https://github.com/psf/black) formatted.
- **Typing**: Performance-critical paths must include [Type Hints](https://docs.python.org/3/library/typing.html).
- **Documentation**: Google-style docstrings for all public APIs.
- **Coverage**: All new features must aim for > 85% test coverage.

### Pull Request Process
1.  **Branching**: Create a feature branch from `main` (e.g., `feat/custom-generator`).
2.  **Tests**: Ensure all existing tests pass and add new tests for your changes.
3.  **Linting**: Run `black .` and `ruff check .` before committing.
4.  **Changelog**: Add a brief entry to `CHANGELOG.md` under `[Unreleased]`.
5.  **Description**: Provide a clear PR description explaining *what* changed and *why*.

---

## Commit Message Format
We follow a structured commit format: `type(module): description`

- `feat(module_07): Add support for SIMD vector types`
- `fix(module_05): Correct alignment for nested unions`
- `docs(module_06): Improve contract schema examples`
- `test(module_07): Add stress tests for deep nesting`

---

## Questions & Help
- **Issues**: Report bugs or request features on our [GitHub Issues](https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/issues).
- **Discussions**: Ask questions and share ideas in [GitHub Discussions](https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/discussions).
- **Contact**: For sensitive matters, email `team@pfcv.dev`.

---
Thank you for making FFI safety a reality! 🚀