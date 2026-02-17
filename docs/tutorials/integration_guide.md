# Integration Guide

## Quick Start

### 1. Basic Setup
```python
from modules.module_08_language_adapter import PythonAdapterComplete

# Create adapter
adapter = PythonAdapterComplete()

# Load contract
adapter.load_contract('contract.json')

# Call function
result = adapter.call_with_enforcement('my_function', arg1, arg2)
```

### 2. With Resource Management
```python
with adapter.enforcement_scope('process_buffer') as scope:
    buffer = bytearray(1024)
    # Register buffer for safety
    scope.add_buffer(buffer)
    # Native call within scope ensures proper pinning and later cleanup
    result = adapter.call_with_enforcement('my_function', buffer)
```

### 3. Error Handling
```python
from modules.module_08_language_adapter import ContractViolationError, NativeCrashError

try:
    result = adapter.call_with_enforcement('func', 42)
except ContractViolationError as e:
    print(f"Contract violation: {e.clause_id} in {e.function_name}")
    # Handle validation failure (e.g., return default value)
except NativeCrashError as e:
    print(f"Critical Native error: {e}")
    # Handle crash (e.g., restart subsystem)
```

## Best Practices

### Use Enforcement Scopes for Buffer Management
Always use `enforcement_scope` when dealing with raw buffers (`bytearray`, `bytes`). It handles pinning and ensures that memory doesn't move during native calls.

### Enable Caching in Production
For high-performance applications, enable validation caching to avoid repeated overhead for the same input patterns.
```python
adapter.enable_caching()
```

### Use Pre-defined Deployment Configurations
Instead of manual configuration, use the templates provided in `DeploymentConfigurations`.
```python
from examples.deployment_configs import DeploymentConfigurations
config = DeploymentConfigurations.production_config()
adapter = PythonAdapterComplete(config=config)
```

### Distinguish Between Violation and Crash
Treat `ContractViolationError` as a functional catchable error (e.g., "invalid user input passed to FFI"). Treat `NativeCrashError` as a system instability that might require more drastic recovery.

### Enable Diagnostics During Development
Use diagnostic mode to track down performance bottlenecks and see exactly why a contract might be failing.
```python
adapter.enable_diagnostic_mode()
# ... make calls ...
report = adapter.get_performance_metrics()
print(report)
```
