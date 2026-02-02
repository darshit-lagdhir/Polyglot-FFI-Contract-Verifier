# Contributing to Polyglot FFI Contract Verifier

Thank you for your interest in contributing!

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier.git
   cd Polyglot-FFI-Contract-Verifier
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

3. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

## Project Structure

```
polyglot_ffi_verifier/     # Main package
├── __init__.py            # Package API
├── context.py             # Execution context
├── pipeline.py            # Pipeline orchestration
├── ingestion.py           # Native interface extraction
├── normalization.py       # IR normalization
├── synthesis.py           # Contract synthesis
├── versioning.py          # Contract versioning
├── adapters.py            # Adapter generation
├── test_planning.py       # Test plan generation
├── execution.py           # Verification execution
├── subprocess_runner.py   # Crash detection
├── diagnosis.py           # Diagnostics mapping
└── reporting.py           # Report generation
```

## Coding Standards
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all public functions
- Add tests for new functionality

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
python tests/test_ingestion.py

# Run with coverage
pytest tests/ --cov=polyglot_ffi_verifier
```

## Submitting Changes

1. Create a new branch: `git checkout -b feature-name`
2. Make your changes
3. Run tests: `pytest tests/`
4. Commit: `git commit -m "Description of changes"`
5. Push: `git push origin feature-name`
6. Open a Pull Request

## Support
Open an issue on GitHub!
