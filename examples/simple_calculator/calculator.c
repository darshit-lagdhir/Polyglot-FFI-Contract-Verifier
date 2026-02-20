// ==============================================================================
// Polyglot FFI Contract Verifier
// Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
//
// This file is part of the Polyglot FFI Contract Verifier ecosystem.
// It is licensed under the Antigravity Source-Available and Technical
// Protection License (ASTPL).
//
// PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
// Training Use are strictly prohibited absent explicit written authorization.
//
// Removal or alteration of this header may constitute a violation of the
// repository's governing agreements.
//
// File Integrity Identifier: 31a58980eb351913
// ==============================================================================

#include "calculator.h"

int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int multiply(int a, int b) {
    return a * b;
}

int divide(int a, int b) {
    // Handle division by zero
    if (b == 0) {
        return 0;
    }
    return a / b;
}

int sum_buffer(const char* data, size_t length) {
    // Handle null pointer
    if (data == NULL) {
        return -1;
    }
    
    int sum = 0;
    for (size_t i = 0; i < length; i++) {
        sum += (unsigned char)data[i];
    }
    return sum;
}