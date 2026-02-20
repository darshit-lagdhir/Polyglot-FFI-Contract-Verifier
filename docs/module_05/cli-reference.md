<!-- ============================================================================== -->
<!-- Polyglot FFI Contract Verifier -->
<!-- Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved. -->
<!--  -->
<!-- This file is part of the Polyglot FFI Contract Verifier ecosystem. -->
<!-- It is licensed under the Antigravity Source-Available and Technical  -->
<!-- Protection License (ASTPL). -->
<!--  -->
<!-- PROHIBITED USES: Commercial Use, Network Access Provision, and Machine  -->
<!-- Training Use are strictly prohibited absent explicit written authorization. -->
<!--  -->
<!-- Removal or alteration of this header may constitute a violation of the  -->
<!-- repository's governing agreements. -->
<!--  -->
<!-- File Integrity Identifier: 2873f2fae1c198fa -->
<!-- ============================================================================== -->

# CLI Reference

Complete reference for the `pfcv-ir` command-line tool.

## Global Options

### `--version`
Show version information and exit.
```bash
pfcv-ir --version
```

### `--verbose`
Enable verbose output showing detailed progress.
```bash
pfcv-ir --verbose normalize input.json
```

### `--quiet`
Suppress all output except errors.
```bash
pfcv-ir --quiet normalize input.json
```

### `--config FILE`
Load configuration from specified file.
```bash
pfcv-ir --config .pfcv-ir.yaml normalize
```

## Commands

### `normalize`
Normalize raw interface artifact from Module 04.

**Usage:**
```bash
pfcv-ir normalize [OPTIONS] <input-artifact>
```

**Options:**
- `-o, --output DIR`: Output directory (default: `.pfcv/ir_cache`)
- `--compress / --no-compress`: Enable/disable compression (default: enabled)
- `--validate / --no-validate`: Enable/disable validation (default: enabled)
- `--cache-dir DIR`: Cache directory location
- `--no-cache`: Disable caching entirely
- `--diff-baseline FILE`: Compare with baseline artifact
- `--report FILE`: Output report to file
- `--profile`: Enable performance profiling

**Examples:**
```bash
pfcv-ir normalize raw_interface.json
pfcv-ir normalize raw_interface.json -o ./ir_output
pfcv-ir normalize new.json --diff-baseline old_ir.json
```

### `validate`
Validate existing IR artifact.

**Usage:**
```bash
pfcv-ir validate [OPTIONS] <ir-artifact>
```

**Options:**
- `--report FILE`: Output validation report

**Examples:**
```bash
pfcv-ir validate ir_artifact.json
```

### `diff`
Compare two IR artifacts.

**Usage:**
```bash
pfcv-ir diff [OPTIONS] <old-artifact> <new-artifact>
```

**Options:**
- `--format FORMAT`: Output format: text, json, markdown (default: text)
- `--output FILE`: Write diff to file
- `--filter TYPE`: Show only: breaking, compatible, all (default: all)
- `--recommend`: Show version bump recommendation

**Examples:**
```bash
pfcv-ir diff v1_ir.json v2_ir.json --recommend
```

### `inspect`
Inspect and query IR artifact contents.

**Usage:**
```bash
pfcv-ir inspect [OPTIONS] <ir-artifact>
```

**Options:**
- `--list-types`: List all types
- `--list-functions`: List all functions
- `--show-type NAME`: Show detailed type information

### `cache`
Manage artifact cache.

**Usage:**
```bash
pfcv-ir cache <subcommand>
```

**Subcommands:**
- `stats`: Show cache statistics
- `clear`: Clear entire cache

## Exit Codes
- 0: Success
- 1: Validation failed
- 2: Normalization error
- 3: Config error
- 4: File not found

## Environment Variables
- `PFCV_CACHE_DIR`: Override default cache directory
- `PFCV_CONFIG`: Default configuration file location

## Config Files
Config can be provided via YAML or JSON files.