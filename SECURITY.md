# Security Policy

## Supported Versions

The following versions of **Polyglot FFI Contract Verifier (PFCV)** are currently supported with security updates:

| Module | Branch | Supported Versions | Status |
| :--- | :--- | :--- | :--- |
| **All Modules** | `main` | 1.0.x | ✅ Active |
| **BETA Versions** | `legacy` | 0.9.x | ❌ End of Life |

---

## Reporting a Vulnerability

We take the security of FFI boundaries and contract synthesis extremely seriously. If you discover a vulnerability in PFCV—especially one that could lead to a contract bypass or unsafe code generation—please:

1.  **Do NOT** open a public GitHub issue.
2.  Email a detailed report to **security@pfcv.dev**.
3.  Include a brief description, reproduction steps, and potential impact.

We will acknowledge your report within **48 hours** and provide a timeline for a patch. We follow coordinated disclosure and will credit you for the discovery in our release notes.

---

## Security Best Practices for PFCV Users

To maintain maximum safety when using synthesized contracts:

1.  **Enable Strict Mode**: Always run synthesis with `strict_mode=True` (default) to ensure no malformed IR generates unsafe clauses.
2.  **Verify Fingerprints**: Use the cryptographic fingerprints in the contract metadata to detect tampering in your CI/CD pipeline.
3.  **Audit Relational Clauses**: While our engine is 99% accurate, always manually audit generated `buffer-size` relational clauses for mission-critical security boundaries.
4.  **Sandbox Synthesis**: If you are synthesizing contracts from untrusted third-party IR, run the synthesis engine in an isolated container.

---

## Secure Infrastructure

PFCV is designed with security in mind:
- **Deterministic Synthesis**: Prevents hidden "backdoors" in contract generation.
- **No Remote Calls**: The synthesis engine operates entirely locally; no code or IR is ever transmitted to external servers.
- **Immutable Rules**: Our rule registry is version-pinned and immutable to prevent runtime logic hijacking.

---
© 2026 PFCV Security Team.
