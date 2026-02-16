# Contributing to Module 07: Contract Synthesis Engine

Thank you for your interest in contributing! This document provides guidelines 
for contributing to the project.

---

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you agree to 
uphold this code. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## How to Contribute

### Types of Contributions

We welcome:

- 🐛 **Bug Reports**: Found a bug? Report it!
- ✨ **Feature Requests**: Have an idea? Suggest it!
- 📖 **Documentation**: Improve or add documentation
- 🧪 **Tests**: Add test coverage
- 💻 **Code**: Fix bugs or implement features
- 🎨 **Examples**: Add usage examples

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/module-07-contract-synthesis.git
cd module-07-contract-synthesis
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### 3. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

---

## Development Workflow

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/tests.py -v

# With coverage
pytest tests/ --cov=module_07_contract_synthesis
```

### Code Formatting
```bash
# Format code
black modules/module_07_contract_synthesis/

# Check formatting
black --check modules/module_07_contract_synthesis/
```

### Type Checking
```bash
mypy modules/module_07_contract_synthesis/
```

### Linting
```bash
pylint modules/module_07_contract_synthesis/
```

---

## Pull Request Process

### 1. Before Submitting
- [ ] All tests pass
- [ ] Code is formatted (black)
- [ ] Type hints added
- [ ] Documentation updated
- [ ] Changelog updated (if applicable)

### 2. Commit Messages
Use clear, descriptive commit messages:

- `feat: Add custom clause generator support`
- `fix: Correct nullability inference for optional pointers`
- `docs: Update API reference with new examples`
- `test: Add stress tests for deep nesting`

Format: `type: description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement

### 3. Submit Pull Request
1. Create PR on GitHub
2. Fill out PR template
3. Link related issues
4. Request review

### 4. Review Process
- Maintainers will review within 3-5 days
- Address feedback
- Once approved, PR will be merged

---

## Coding Standards

### Python Style
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for public APIs

Example:
```python
def synthesize_from_ir(
    ir_path: Union[str, Path],
    config: Optional[SynthesisConfig] = None
) -> ContractDocument:
    """
    Synthesize contract from IR file.
    
    Args:
        ir_path: Path to IR JSON file
        config: Optional synthesis configuration
        
    Returns:
        Generated contract document
    """
    ...
```

### Testing Standards
- Write tests for new features
- Maintain test coverage > 80%
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

Example:
```python
def test_synthesize_with_custom_config():
    # Arrange
    config = SynthesisConfig(default_pointer_nonnull=False)
    ir_unit = create_test_ir()
    
    # Act
    result = engine.synthesize(ir_unit, 'test')
    
    # Assert
    assert result.success
    assert result.clauses_generated > 0
```

---

## Documentation Standards

### Docstrings
Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
```

### Updating Documentation
When adding features:
1. Update API reference
2. Add examples if applicable
3. Update relevant guides
4. Update `CHANGELOG.md`

---

## Issue Guidelines

### Bug Reports
Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (Python version, OS)
- Minimal reproducible example

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternatives considered
- Additional context

---

## Questions?
- Check existing issues
- Ask in discussions
- Read documentation

---

## Recognition
Contributors will be recognized in:
- `CHANGELOG.md`
- Release notes
- Project acknowledgments

Thank you for contributing! 🎉