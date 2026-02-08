# IR Normalization Diagnostics Guide

This guide helps resolve common issues with IR normalization.

## Table of Contents

- [E1001: Type Conversion Error](#e1001)
- [E2101: Structure Size Mismatch](#e2101)
- [E2102: Overlapping Structure Fields](#e2102)
- [W1001: Type Deduplication Warning](#w1001)

## Error Reference

### E1001: Type Conversion Error

**Category:** conversion  
**Severity:** error

Failed to convert Module 04 type to IR entity

**Common Causes:**

- Unsupported type construct in source code
- Incomplete type information from Module 04
- Corrupted artifact data

**Solutions:**

1. Verify Module 04 artifact is valid
2. Check artifact version compatibility
3. Re-run Module 04 ingestion
4. Report issue if type should be supported

---

### E2101: Structure Size Mismatch

**Category:** validation  
**Severity:** error

Computed structure size does not match compiler-reported size

**Common Causes:**

- Missing padding in field layout
- Flexible array member not handled
- Packing attribute not captured
- Bitfield layout error

**Solutions:**

1. Compare with: clang -cc1 -fdump-record-layouts
2. Check for __attribute__((packed))
3. Inspect structure: pfcv-ir inspect --show-type <name>
4. Verify Module 04 captured all fields

---

### E2102: Overlapping Structure Fields

**Category:** validation  
**Severity:** error

Structure fields overlap in memory

**Common Causes:**

- Incorrect field offsets from Module 04
- Bitfield layout error
- Union mistakenly represented as structure

**Solutions:**

1. Verify source structure definition
2. Check if should be union instead of struct
3. Re-run Module 04 ingestion

---

### W1001: Type Deduplication Warning

**Category:** normalization  
**Severity:** warning

Multiple structurally identical types found

**Common Causes:**

- Typedef chains to same type
- Forward declarations and definitions

**Solutions:**

1. This is usually benign
2. Review typedef usage if unexpected

---
