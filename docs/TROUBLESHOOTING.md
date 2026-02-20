<!-- ============================================================================== -->
<!-- Polyglot FFI Contract Verifier -->
<!-- Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved. -->
<!--  -->
<!-- This file is part of the Polyglot FFI Contract Verifier ecosystem. -->
<!-- It is licensed under the Antigravity Source-Available and Technical  -->
<!-- Protection License (ASTPL). -->
<!--  -->
<!-- PROHIBITED USES: Commercial Use, Network Access Provision, and Machine  -->
<!-- Training Use are strictly prohibited absent explicit written authorization. -->
<!--  -->
<!-- Removal or alteration of this header may constitute a violation of the  -->
<!-- repository's governing agreements. -->
<!--  -->
<!-- File Integrity Identifier: 7575cde3e6661651 -->
<!-- ============================================================================== -->

# Troubleshooting Guide

Common issues, their causes, and recommended solutions for the Language Adapter.

## Common Issues
Below are some frequently encountered issues and their solutions.

## IR Validation Failures
Errors encountered during IR normalization or cross-language validation are documented in our [Detailed Diagnostics Guide](module_05/troubleshooting.md).

## Contract Violations

### Issue: `ContractViolationError` raised
**Cause**: The inputs provided to the FFI function or the values returned by it do not adhere to the clauses defined in the loaded contract.

**Solution**:
Inspect the error details to identify the failing clause.
```python
try:
    adapter.call_with_enforcement('process_data', data)
except ContractViolationError as e:
    print(f"Violation ID: {e.clause_id}")
    print(f"Expected: {e.expected}")
    print(f"Observed: {e.observed}")
    # Adjust input or check native logic
```

## Performance Issues

### Issue: Noticeable latency in FFI calls
**Cause**: Heavy validation logic, high logging volume, or disabled caching.

**Solutions**:
1. Enable the validation cache: `adapter.enable_caching()`.
2. Set logging level to `ERROR` in `AdapterConfiguration`.
3. Check for expensive custom validation predicates.
4. Enable basic profiling to find bottlenecks: `adapter.enable_profiling()`.

## Memory Management

### Issue: Process memory usage increases unexpectedly
**Cause**: Native memory leaks or the adapter tracking too many buffers without cleanup.

**Solutions**:
1. Ensure all memory-intensive operations are wrapped in `enforcement_scope`.
2. Check memory statistics: `adapter.memory_manager.get_statistics()`.
3. Verify ownership transfer clauses in the contract; ensure `TRANSFER_TO_NATIVE` is used when the library takes control.

## Interoperability Errors

### Issue: Type mismatch during cross-language sharing
**Cause**: Incorrect type projection between Universal types and language-specific types.

**Solution**:
Verify the mapping using the `TypeProjector`:
```python
from language_adapter.cross_language import TypeProjector, UniversalType, UniversalTypeDescriptor

projector = TypeProjector('rust')
u_type = UniversalTypeDescriptor(base_type=UniversalType.BUFFER)
print(f"Rust projection: {projector.project_type(u_type)}")
```

## Getting Help
- **Project Site**: Check the root `docs/` directory for full tutorials.
- **Bug Reports**: Open an issue on GitHub with a minimal reproduction case.
- **Community**: Join the discussions on our community forum for integration advice.