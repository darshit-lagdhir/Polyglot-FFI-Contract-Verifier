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
// File Integrity Identifier: c4db94da3fbb6989
// ==============================================================================

#ifndef CALCULATOR_H
#define CALCULATOR_H

#include <stddef.h>

/**
 * Add two integers.
 * 
 * @param a First operand
 * @param b Second operand
 * @return Sum of a and b
 */
int add(int a, int b);

/**
 * Subtract two integers.
 * 
 * @param a First operand
 * @param b Second operand
 * @return Difference (a - b)
 */
int subtract(int a, int b);

/**
 * Multiply two integers.
 * 
 * @param a First operand
 * @param b Second operand
 * @return Product of a and b
 */
int multiply(int a, int b);

/**
 * Divide two integers.
 * 
 * @param a Numerator
 * @param b Denominator
 * @return Quotient (a / b), or 0 if b is zero
 */
int divide(int a, int b);

/**
 * Sum all bytes in a buffer.
 * 
 * @param data Pointer to buffer (must not be null if length > 0)
 * @param length Number of bytes to sum
 * @return Sum of all bytes, or -1 if data is null
 */
int sum_buffer(const char* data, size_t length);

#endif /* CALCULATOR_H */