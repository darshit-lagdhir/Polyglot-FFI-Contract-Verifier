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
<!-- File Integrity Identifier: 4ab1c255a514e76e -->
<!-- ============================================================================== -->

# C++ Adapter Guide

The C++ Language Adapter integrates C++'s object model, RAII, smart pointers, and exception handling with runtime FFI enforcement.

## Overview

C++ presents a complex set of challenges for FFI boundaries, including manual memory management, RAII semantics, and complex exception propagation. The C++ Adapter provides a safety layer that bridges these C++ features with the Polyglot FFI runtime enforcement system.

## Key Features

### Smart Pointer Integration
The adapter provides built-in tracking for standard C++ smart pointers, ensuring that ownership transfers are correctly recorded and validated.

```cpp
// unique_ptr - Exclusive ownership transfer
std::unique_ptr<Widget> widget = std::make_unique<Widget>();
adapter.call_with_unique_ptr("process_widget", std::move(widget));

// shared_ptr - Reference count tracking
std::shared_ptr<Data> data = std::make_shared<Data>();
adapter.call_with_shared_ptr("process_data", data);
```

### RAII Support
The adapter leverages C++ RAII (Resource Acquisition Is Initialization) to ensure that resources are automatically cleaned up, even in the presence of errors or exceptions.

```cpp
adapter.call_with_raii(
    "process_file",
    []() { return open_file("data.txt"); },  // Acquire
    [](File* f) { close_file(f); },          // Release
    additional_args...
);
```

### Exception Handling
C++ exceptions are caught at the FFI boundary and translated into Polyglot FFI errors, preventing unhandled exceptions from crashing the host process.

| C++ Exception | Adapter Error |
|---------------|---------------|
| `std::bad_alloc` | `NativeCrashError` (Memory) |
| `std::exception` | `NativeCrashError` (Generic) |
| Unknown `catch(...)` | `NativeCrashError` (Unknown) |

### Template Validation
The adapter supports validating template instantiations by creating type-specific validation graphs for concrete template instances.

## Best Practices

1.  **Prefer Smart Pointers**: Use `std::unique_ptr` and `std::shared_ptr` to automate ownership management and integration with the adapter.
2.  **Use RAII Guards**: Wrap FFI-related resources in `RAIIGuard` to guarantee cleanup during scope exit.
3.  **Specify Exception Safety**: Clearly define the exception safety guarantees (No-throw, Basic, Strong) in your contract metadata.
4.  **Isolate Exceptions**: Always wrap native C++ calls in exception-handling blocks when calling from languages that do not support C++ exceptions.
5.  **Type-Safe Templates**: Register specific contracts for common template instantiations to ensure robust validation.