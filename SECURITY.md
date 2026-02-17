# Security Policy

## Supported Versions

The following versions of **Polyglot FFI Contract Verifier (PFCV)** are currently supported with security updates:

| Version | Supported | Status |
| :--- | :--- | :--- |
| **1.0.x** | ✅ | Active Production Support |
| **0.9.x** | ❌ | End of Life |

---

## FFI Security Philosophy
PFCV is designed to be a "Zero-Trust" bridge between memory-safe languages (Python, Rust) and potentially unsafe native libraries. Our security focus is on:
- **Contract Enforcement**: Preventing invalid data from crossing the FFI boundary.
- **Buffer Safety**: Validating buffer sizes and bounds before native invocation.
- **Ownership Integrity**: Ensuring memory is neither leaked nor double-freed through strict ownership tracking.
- **Crash Isolation**: Isolating native segmentation faults and hardware exceptions to prevent parent process corruption.

---

## Reporting a Vulnerability

If you discover a security vulnerability in PFCV—especially one that could allow a native crash to bypass isolation or a malformed buffer to bypass contract validation—please:

1.  **Do NOT** open a public GitHub issue.
2.  Email a detailed report to **security@pfcv.dev**.
3.  Include a brief description, reproduction steps (ideally a minimal test case), and potential impact.

We will acknowledge your report within **24 hours** and provide a patch timeline. We practice coordinated disclosure.

---

## Security Best Practices for Users

1.  **Enable Manual Auditing**: While M07 (Synthesis) is highly accurate, always manually audit `relational` and `buffer-size` clauses for high-risk interfaces.
2.  **Use Enforcement Scopes**: Always wrap memory-intensive FFI calls in `enforcement_scope` to ensure automatic resource cleanup even during failures.
3.  **Strict Mode**: Run with `EnforcementMode.STRICT` in production to fail fast on any contract deviations.
4.  **Pin Contract Versions**: Use the built-in contract fingerprinting to ensure that production contracts haven't been tampered with.

---

## Security Features in PFCV

- **Memory Tracking**: The `MemoryManager` tracks all buffers passed to native code to prevent overflows.
- **Crash Isolation**: Module 05/08 provides signal handling and SEH translation to catch native crashes gracefully.
- **Ownership Registry**: Prevents "Use-After-Free" at the FFI boundary by tracking object lifecycles.
- **Immutable Schemas**: Contracts use a versioned, static schema to prevent "Rule-Injection" attacks.

---
© 2024-2026 PFCV Security Team.
