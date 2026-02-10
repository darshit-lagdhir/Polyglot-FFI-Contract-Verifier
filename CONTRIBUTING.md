# Contributing to Module 06: Contract Schema

Thank you for considering contributing to Module 06! This document provides guidelines for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Basic understanding of FFI concepts

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/pfcv/pfcv.git
cd pfcv
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

5. Run tests to verify setup:
```bash
pytest tests/unit/test_contract_*.py -v
```

## Development Workflow

### Making Changes

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```
2. Make your changes, following code style guidelines
3. Write tests for new functionality
4. Run tests locally:
```bash
pytest tests/ -v
```
5. Run code quality checks:
```bash
black modules/module_06_contract_schema/
isort modules/module_06_contract_schema/
flake8 modules/module_06_contract_schema/
```
6. Commit your changes:
```bash
git commit -m "feat: Add new feature description"
```

### Commit Message Convention
Follow Conventional Commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

### Pull Request Process
1. Push your branch to GitHub:
```bash
git push origin feature/your-feature-name
```
2. Create a Pull Request on GitHub
3. Ensure CI checks pass
4. Request review from maintainers
5. Address review feedback
6. Once approved, maintainers will merge

## Code Style
- **Formatting**: Black with line length 100
- **Import sorting**: isort with black profile
- **Linting**: flake8 with max line length 100
- **Type hints**: Use type hints on all public functions
- **Docstrings**: Use Google-style docstrings

### Example Function
```python
def validate_contract(contract: ContractDocument) -> ValidationResult:
    """
    Validate contract through all layers.
    
    Args:
        contract: Contract to validate
        
    Returns:
        Validation result with errors and warnings
        
    Raises:
        ValidationError: If contract structure is invalid
        
    Example:
        >>> validator = ContractValidator()
        >>> result = validator.validate(contract)
        >>> print(result.passed)
        True
    """
    # Implementation
```

## Testing Requirements
- All new features must have tests
- Maintain code coverage > 85%
- Write both positive and negative tests
- Include edge case tests
- Add integration tests for workflows

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_contract_entities.py -v

# Run with coverage
pytest tests/ --cov=module_06_contract_schema --cov-report=term-missing

# Run benchmarks
pytest tests/benchmarks/ --benchmark-only
```

## Documentation
- Update documentation for new features
- Add examples for new functionality
- Keep README.md up to date
- Document breaking changes in CHANGELOG.md

## Questions?
- Open a GitHub Discussion
- Check existing Issues
- Email: team@pfcv.dev

Thank you for contributing! 🎉
