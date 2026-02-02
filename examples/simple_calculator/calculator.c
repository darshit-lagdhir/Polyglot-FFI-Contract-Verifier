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
