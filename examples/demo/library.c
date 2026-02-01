#include "interface.h"
#include <stdio.h>

int write_buffer(uint8_t* buffer, uint32_t size) {
    // VULNERABILITY: No check for valid pointer or buffer size vs size param
    for (uint32_t i = 0; i < size; i++) {
        buffer[i] = (uint8_t)(i % 255);
    }
    return 0;
}

int process_config(struct Config* cfg) {
    // VULNERABILITY: No check for NULL
    return cfg->mode; # Crash if cfg is NULL
}
