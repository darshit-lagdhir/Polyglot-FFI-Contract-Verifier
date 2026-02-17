# Rust Adapter Guide

The Rust Language Adapter bridges Rust's compile-time ownership guarantees with runtime FFI enforcement, providing defense-in-depth safety.

## Overview

Rust provides strong safety guarantees through its borrow checker at compile time. However, when crossing the FFI boundary into C or other native languages, these guarantees are suspended within `unsafe` blocks. The Rust Adapter extends Polyglot FFI's runtime enforcement to Rust, ensuring that even `unsafe` code adheres to predefined contracts.

## Key Concepts

### Ownership Tracking
Rust's ownership model is integrated into the adapter's runtime registry. The adapter tracks whether a value is owned, borrowed immutably, or borrowed mutably when passed to native code.

```rust
// Runtime ownership validation example
let data = vec![1, 2, 3];

// Record borrow in adapter before passing to unsafe C function
adapter.borrow_for_call(&data, data.as_ptr() as usize, false)?;

unsafe {
    ffi_process_data(data.as_ptr(), data.len());
}
```

### Type Mapping
Rust types are mapped to C-compatible types with specific ownership semantics:

| Rust Type | C Type | Ownership |
|-----------|--------|-----------|
| `i32` | `int32_t` | Owned (Copy) |
| `&[u8]` | `const uint8_t*` | Borrowed |
| `&mut [u8]` | `uint8_t*` | Mutable |
| `*const T` | `const T*` | Raw Const |
| `*mut T` | `T*` | Raw Mut |
| `Option<*const T>` | `const T*` | Nullable Pointer |

### Safety Guarantees
1.  **Contract Validation**: Pre-call and post-call validation ensures inputs and outputs meet contract specifications.
2.  **Ownership Verification**: Ensures that pointers passed to FFI haven't been prematurely dropped or multi-borrowed mutably in a way that violates Rust's rules.
3.  **Panic Isolation**: Handles Rust panics gracefully, preventing them from crashing the entire host process if possible, and converting them into managed error states.

## Usage Example

```rust
use polyglot_ffi::{RustAdapter, contract_enforce};

#[contract_enforce("image_processing.json")]
fn process_image(path: &str, filter: i32) -> Result<(), FfiError> {
    let adapter = RustAdapter::default();
    
    // The macro handles the wrapper logic:
    // 1. Validates 'path' and 'filter' against contract
    // 2. Records borrows in the ownership bridge
    // 3. Executes the underlying native call
    // 4. Validates return codes
    // 5. Cleans up recorded borrows
    
    adapter.call("apply_filter", (path, filter))?;
    Ok(())
}
```

## Best Practices
- **Prefer References**: Use `&T` or `&mut T` over raw pointers whenever possible to leverage Rust's compile-time safety alongside runtime enforcement.
- **Use Options for Null**: Always use `Option<*const T>` or `Option<Box<T>>` when a pointer in a contract is marked as nullable.
- **Annotate Lifetimes**: When using high-level bindings, ensure lifetimes are correctly annotated so the adapter can track valid scopes.
- **Panic Strategy**: Use `std::panic::catch_unwind` if you are calling into Rust from a different language to prevent panics from crossing FFI boundaries improperly.
