#ifndef DEMO_INTERFACE_H
#define DEMO_INTERFACE_H

#include <stdint.h>

/**
 * Demo interface with intentional vulnerabilities.
 */

// Writes sequential bytes to a buffer.
// INTENTIONAL BUG: Implementation does not check if buffer is large enough for size.
int write_buffer(uint8_t* buffer, uint32_t size);

// Process config struct
// INTENTIONAL BUG: Implementation does not check null
struct Config {
    int mode;
};
int process_config(struct Config* cfg);

#endif // DEMO_INTERFACE_H
