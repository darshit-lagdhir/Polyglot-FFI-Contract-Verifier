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
// File Integrity Identifier: 82256c7904981218
// ==============================================================================

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