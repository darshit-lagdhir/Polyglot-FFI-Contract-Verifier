# Language Adapter - Runtime FFI Enforcement System

**Version 1.0.0** | [Documentation](USER_GUIDE.md) | [API Reference](API_REFERENCE.md) | [Examples](../examples/)

## Overview

The Language Adapter is a production-ready runtime FFI (Foreign Function Interface) 
enforcement system that validates foreign function calls against contracts, manages 
memory safety, tracks ownership, and provides comprehensive observability.

**Supported Languages**: Python, Rust, C++

## Quick Start

### Installation

```bash
pip install language-adapter
```

### Basic Usage

```python
from language_adapter import create_adapter

# Create adapter with contract
adapter = create_adapter('contract.json')

# Call FFI function with enforcement
result = adapter.call_with_enforcement('my_function', arg1, arg2)
```

### With Resource Management

```python
with adapter.enforcement_scope('process_buffer') as scope:
    buffer = bytearray(1024)
    scope.add_buffer(buffer)
    result = scope.invoke(buffer, len(buffer))
# Automatic cleanup
```

## Key Features

✅ **Contract-Based Validation** - Enforce contracts at runtime  
✅ **Memory Safety** - Automatic buffer tracking and ownership  
✅ **Multi-Language Support** - Python, Rust, C++ adapters  
✅ **Performance Optimization** - Caching and fast paths  
✅ **Comprehensive Observability** - Logging, metrics, tracing  
✅ **State Persistence** - Save and restore adapter state  
✅ **CLI Tools** - Command-line utilities  
✅ **Production Ready** - Tested, documented, deployed  

## Documentation

- [User Guide](USER_GUIDE.md) - Complete guide to using the adapter
- [API Reference](API_REFERENCE.md) - Full API documentation
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment
- [Performance Guide](PERFORMANCE_GUIDE.md) - Optimization tips
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

## Examples

### Python: Image Processing
```python
from language_adapter import create_adapter

adapter = create_adapter('image_processing.json')
adapter.enable_caching()

# Safe FFI call with validation
result = adapter.call_with_enforcement(
    'process_image',
    image_data,
    width,
    height
)
```

## Architecture

```text
┌─────────────────────────────────────────────────┐
│         User Application Code                  │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         Language Adapter                        │
│  ┌──────────────────────────────────────────┐  │
│  │  Validation Engine                       │  │
│  │  Memory Management                       │  │
│  │  Ownership Tracking                      │  │
│  │  Observability                           │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         Native Libraries (C/C++/Rust)           │
└─────────────────────────────────────────────────┘
```

## Statistics
- **Lines of Code**: 20,000+
- **Test Coverage**: 2,220+ tests (>95% coverage)
- **Documentation Pages**: 30+
- **Language Adapters**: 3 (Python, Rust, C++)
- **Performance Overhead**: <5%

## License
MIT License - See LICENSE file

## Support
- **Documentation**: `docs/`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
