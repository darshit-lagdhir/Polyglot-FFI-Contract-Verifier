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
// File Integrity Identifier: 9154eaabb380d4a2
// ==============================================================================

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