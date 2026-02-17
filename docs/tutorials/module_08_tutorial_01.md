# Language Adapter Tutorial: Python FFI with Enforcement

## Overview

This tutorial demonstrates using the Python Language Adapter for safe FFI calls
with automatic contract enforcement, memory management, and exception handling.

## Basic Usage

```python
from modules.module_08_language_adapter import PythonAdapterComplete

# Create adapter
adapter = PythonAdapterComplete()

# Load contract
adapter.load_contract('path/to/contract.json')

# Simple invocation
result = adapter.call_with_enforcement(
    'my_function', arg1, arg2,
    native_callable=lib.my_function
)
```

## With Context Manager

The `EnforcementScope` ensures automatic resource cleanup:

```python
with adapter.enforcement_scope('process_buffer') as scope:
    buffer = bytearray(1024)
    wrapper = scope.add_buffer(buffer)
    result = scope.invoke(buffer, 1024)
# Automatic cleanup on exit - buffers unpinned, references released
```

## Diagnostic Mode

Enable diagnostics to collect execution traces and timing:

```python
adapter.enable_diagnostic_mode()

result = adapter.call_with_enforcement(
    'function', arg1,
    native_callable=lib.function
)

# Get metrics
metrics = adapter.get_performance_metrics()
print(f"Total time: {metrics['total_time_ms']}ms")
print(f"Timing breakdown: {metrics['timing_breakdown']}")

# Get full diagnostic report
report = adapter.get_diagnostics()
for trace in report['traces']:
    print(f"[{trace['phase']}] {trace['message']}")
```

## Validation Pipeline

Add validation graphs to enforce contracts:

```python
from modules.module_08_language_adapter import (
    ValidationGraph, ValidationNode, ClauseSeverity
)

# Create validation graph
graph = ValidationGraph('safe_divide')
graph.add_node(ValidationNode(
    'divisor_nonzero', 'range', ClauseSeverity.MANDATORY,
    predicate=lambda inputs, params: inputs[1] != 0,
    parameters=[1],
    failure_message='Divisor must not be zero'
))

adapter.validation_graphs['safe_divide'] = graph

# This will raise ContractViolationError if divisor is 0
result = adapter.call_with_enforcement(
    'safe_divide', 10, 0,
    native_callable=lib.divide
)
```

## Exception Handling

The adapter translates native errors into Python exceptions:

```python
from modules.module_08_language_adapter import (
    ContractViolationError, NativeCrashError
)

try:
    result = adapter.call_with_enforcement(
        'risky_function', args,
        native_callable=lib.risky
    )
except ContractViolationError as e:
    print(f"Contract violated: {e}")
    print(f"Hints: {e.remediation_hints}")
except NativeCrashError as e:
    print(f"Native crash: {e.crash_type} at {e.crash_address}")
```

## FFI Modes

The adapter supports both ctypes and cffi:

```python
# ctypes mode (default)
adapter_ct = PythonAdapterComplete(ffi_mode='ctypes')

# cffi mode
adapter_cf = PythonAdapterComplete(ffi_mode='cffi')
```
