# Language Adapter User Guide

Complete guide to using the Language Adapter for FFI enforcement.

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
4. [Getting Started](#getting-started)
5. [Contracts](#contracts)
6. [Validation](#validation)
7. [Memory Management](#memory-management)
8. [Performance](#performance)
9. [Observability](#observability)
10. [Advanced Topics](#advanced-topics)

## Introduction
The Language Adapter provides runtime enforcement of FFI contracts, ensuring safe and correct interaction with native libraries.

**Why Use Language Adapter?**
- **Safety**: Catch FFI errors before they cause crashes
- **Debugging**: Rich diagnostics for FFI issues
- **Performance**: Minimal overhead with optimizations
- **Multi-language**: One contract works across languages

## Installation

### Python
```bash
pip install language-adapter
```

### Rust
```toml
[dependencies]
language-adapter = "1.0"
```

### C++
```bash
# Via CMake
find_package(LanguageAdapter REQUIRED)
target_link_libraries(myapp LanguageAdapter::LanguageAdapter)
```

## Core Concepts

### Contracts
Contracts define expected behavior of FFI functions:
```json
{
  "contract_id": "my_library",
  "functions": {
    "process": {
      "parameters": [
        {"name": "data", "type": "buffer"}
      ],
      "clauses": [
        {"type": "nullability", "allow_null": false}
      ]
    }
  }
}
```

### Enforcement
The adapter validates calls against contracts:
- **Pre-call validation**: Check inputs before calling
- **Execution**: Call native function safely
- **Post-call validation**: Check outputs after returning
- **Cleanup**: Release resources automatically

### Ownership
Track memory ownership across FFI boundaries:
- **Transfer**: Ownership moves to/from native code
- **Borrow**: Temporary access without transfer
- **Shared**: Reference-counted shared ownership

## Getting Started

### Hello World
```python
from language_adapter import create_adapter

# Create adapter
adapter = create_adapter()

# Load contract
adapter.load_contract('hello.json')

# Call function
result = adapter.call_with_enforcement('hello_world')
print(result)
```

### With Validation
```python
# Contract with validation rules
contract = {
    "functions": {
        "add": {
            "parameters": [
                {"name": "a", "type": "int"},
                {"name": "b", "type": "int"}
            ],
            "clauses": [
                {
                    "clause_type": "range",
                    "parameter": "a",
                    "min": 0,
                    "max": 100
                }
            ]
        }
    }
}

# Valid call
result = adapter.call_with_enforcement('add', 5, 10)  # OK

# Invalid call
# This will raise an exception because 'a' is 200 (>100)
result = adapter.call_with_enforcement('add', 200, 10)
```

## Performance

### Enable Caching
```python
adapter.enable_caching()
```

### Monitor Performance
```python
adapter.enable_profiling()
# ... make calls ...
metrics = adapter.get_performance_metrics()
print(f"Average duration: {metrics['average_time_ms']}ms")
```

## Observability

### Logging
```python
adapter.enable_diagnostic_mode()
# Calls are now logged
adapter.call_with_enforcement('function', args)
# View diagnostics
diagnostics = adapter.get_diagnostics()
```

### Metrics
```python
# Access metrics
if hasattr(adapter, 'observability'):
    summary = adapter.observability.get_summary()
    print(summary)
```

## Advanced Topics

### Custom Validation
```python
from language_adapter import ValidationGraph, ValidationNode, ClauseSeverity

graph = ValidationGraph('my_function')
node = ValidationNode(
    'custom_check',
    'custom',
    ClauseSeverity.MANDATORY,
    predicate=lambda inputs, params: inputs[0] > 0,
    parameters=[0]
)
graph.add_node(node)
adapter.validation_graphs['my_function'] = graph
```

### State Persistence
```python
from language_adapter import PersistenceManager

manager = PersistenceManager()
# Save state
manager.save_state(adapter, 'state.json')
# Load state
state = manager.load_state('state.json')
```

## Next Steps
- Read **API Reference** for complete API details.
- See **Examples** for working code.
- Check **Deployment Guide** for production best practices.
