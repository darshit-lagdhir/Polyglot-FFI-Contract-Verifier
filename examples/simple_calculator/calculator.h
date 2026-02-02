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
