# FFI Verification Demo

This demo shows the Polyglot FFI Contract Verifier detecting a buffer overflow
vulnerability in a C library.

## The Bug

The `write_buffer` function in `library.c` does not validate that the buffer
size matches the provided `size` parameter:

```c
int write_buffer(uint8_t* buffer, uint32_t size) {
    // BUG: No validation that buffer has 'size' bytes
    for (uint32_t i = 0; i < size; i++) {
        buffer[i] = (uint8_t)i;  // Writes beyond buffer if size > actual length
    }
    return 0;
}
```

## Running the Demo

```bash
python run_demo.py
```

## What Happens

1. **Ingestion**: Extracts interface from `interface.h`
2. **Contract Synthesis**: Derives constraint that buffer must have ≥ `size` bytes
3. **Test Generation**: Creates test with 5-byte buffer but `size=100`
4. **Execution**: Test triggers access violation (crash)
5. **Diagnostics**: Maps crash to buffer overflow violation
6. **Report**: Explains bug and provides fix

## Expected Output

The verifier will:

*   ❌ Detect **CRITICAL** violation: Buffer overflow in `write_buffer()`
*   📍 Identify root cause: Missing buffer size validation
*   🔧 Recommend fix: Add pre-call check in adapter
*   📊 Generate detailed HTML report

## The Fix

Add validation in the generated adapter:

```python
def write_buffer(buffer, size):
    # Add this check:
    if size > len(buffer):
        raise BufferSizeViolation(
            "func_write_buffer_buffer_size",
            f"Buffer size {len(buffer)} < required {size}"
        )
    
    # Then call native function
    return _lib.write_buffer(buffer, size)
```

## Verification After Fix

After adding the check, re-run verification:

*   ✅ All tests pass
*   ✅ Buffer overflow prevented
*   ✅ Safe to use
