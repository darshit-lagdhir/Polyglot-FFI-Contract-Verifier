# CI/CD Integration and Automation Guide

This document details the implementation of **2: CI/CD Integration** for the Polyglot FFI Contract Verifier.

## Overview

The CI/CD Integration subsystem enables development teams to automate FFI verification as part of their standard build pipelines. It provides pre-built templates for popular CI platforms, status badge generation, and intelligent failure gating based on contract violation severity.

## Quick Start

1.  **Select a Template**: Choose the template for your CI platform from the `templates/` directory or generate one using the CLI.
2.  **Configure Paths**: Update the `header` and `library` paths in your CI configuration to point to your project's native interface and build output.
3.  **Run Verification**: Add the verification step to your pipeline. The verifier will automatically produce reports and machine-readable summaries.

## Supported Platforms

### GitHub Actions
Copy `templates/github_actions.yml` to `.github/workflows/ffi-verification.yml`.
This template runs on `windows-latest` by default and is optimized for C/C++ projects using MSVC.

### GitLab CI
Copy `templates/gitlab_ci.yml` (or use the content) to your `.gitlab-ci.yml`.
Uses GitLab's artifact storage to preserve verification reports.

### Jenkins
Use the provided `Jenkinsfile` template. Requires a Windows agent with Python 3.11+.

## Config

The CI behavior can be controlled via `configs/ffi_verifier.yml` or environment variables.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FFI_HEADER_PATH` | Path to the C header file | `native/interface.h` |
| `FFI_LIBRARY_PATH` | Path to the built library | `build/library.dll` |
| `FFI_VERIFIER_STRICT` | If `true`, fails on any violation (not just critical) | `false` |
| `FFI_VERIFIER_TIMEOUT` | Global execution timeout in seconds | `600` |

### Failure Policy

The `failure_policy` section in the config file determines when a build should fail:
- `block_on_critical`: Fail the build if any Critical (crash-prone) violations are found.
- `strict_mode`: Fail the build if *any* violation is found, including warnings.
- `max_violations`: Fail if the total number of violations exceeds this limit.

## Status Badges

The verifier can generate dynamic status badges for your README.

1.  Add a step to your CI to run `python scripts/generate_badge.py`.
2.  Use the generated `badges/ffi-status.json` with a shields.io endpoint.

Markdown Example:
```markdown
![FFI Verification](https://img.shields.io/endpointurl=https://raw.githubusercontent.com/user/repo/main/badges/ffi-status.json)
```

## Artifact Publishing

All verification runs produce:
- `reports/verification_report.html`: Visual report for humans.
- `reports/ci_summary.json`: Machine-readable summary for automation.
- `artifacts/diagnostics.json`: Technical diagnostic data.

These should be configured as "artifacts" in your CI platform to ensure they are saved after the build completes.

## Diagnostics

- **Missing Header**: Ensure the path to the C header is relative to the project root or provide an absolute path.
- **Library Not Found**: Verification often runs after the build stage. Ensure the library exists at the specified path before the verifier runs.
- **Python Dependencies**: Ensure `libclang` and `PyYAML` are installed in the CI runner.
