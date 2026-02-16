# Security Policy

## Supported Versions

| Module | Version | Supported |
| :--- | :--- | :--- |
| **Module 05** | 1.0.x | ✅ Yes |
| **Module 06** | 1.0.x | ✅ Yes |
| **Module 07** | 1.0.x | ✅ Yes |
| **All Modules** | < 1.0 | ❌ No |

---

## Reporting a Vulnerability

We take the security of FFI interfaces seriously. If you discover a vulnerability in PFCV itself or a way to bypass synthesis safety, please:

1.  **DO NOT** open a public issue.
2.  Email `security@pfcv.dev` with a detailed description.
3.  Include reproduction steps and potential impact.

We will respond within 48 hours and work with you on a patch before public disclosure.

---

## Security Best Practices

To ensure the highest level of FFI safety when using PFCV:
1.  **Validate Inputs**: Always validate native artifacts from untrusted sources using `pfcv-ir validate`.
2.  **Strict Mode**: Enable `strict_mode=True` in production synthesis to treat warnings as errors.
3.  **Review Contracts**: While synthesis is deterministic, always manually review critical security contracts before deployment.
4.  **Sandbox Synthesis**: Run contract synthesis in a sandboxed environment when processing untrusted IR artifacts.

---

## Security Features
- **Deterministic Synthesis**: Prevents tampered outputs through reproducible builds.
- **Cryptographic Fingerprinting**: Every contract includes an SHA-256 fingerprint for integrity verification.
- **Input Validation**: Multi-stage validation for IR and Schema artifacts at every module boundary.

---
© 2026 PFCV Team.
