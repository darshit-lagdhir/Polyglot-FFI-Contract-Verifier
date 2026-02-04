# Module 03: Build Process & Toolchain Integration

**Module ID:** 03 of 28  
**Version:** 1.0.0  
**Status:** IN PROGRESS  
**Purpose:** Foundational build system with correctness guarantees

---

## Table of Contents

1. [Build Philosophy & Core Architecture](#1-build-philosophy-core-architecture)
2. [Toolchain Detection & Validation](#2-toolchain-detection--validation)
3. [Environment Descriptors](4. [Build Stage Pipeline](... (sections 5-20 to be added in subsequent prompts)

---

## 1. Build Philosophy & Core Architecture

...

---

## 2. Toolchain Detection & Validation

### 2.1 Introduction

Toolchain detection transforms implicit environmental state (installed compilers)
into explicit, validated build configuration. The compiler and linker are not
incidental details but semantic inputs that determine ABI behavior.

### 2.2 Detection Process

#### : Executable Discovery
The system searches for known compilers (MSVC, Clang, GCC) in system PATH and
standard installation locations.

#### : Version Extraction
For each discovered compiler, the system extracts:
- Short version (e.g., "19.29" for MSVC, "14" for Clang)
- Full version string (e.g., "19.29.30133")
- Executable hash for provenance

#### : Linker Detection
Associated linker is detected:
- MSVC: link.exe in same directory
- Clang/GCC: ld or lld in PATH

#### : Target Triple Detection
The system determines the target platform:
- MSVC: Windows-x86_64-msvc or Windows-x86-msvc
- Clang/GCC: Query with -dumpmachine (e.g., x86_64-pc-linux-gnu)

#### : ABI Property Inference
Based on compiler and target, infer:
- Default calling convention (microsoft_x64, sysv_amd64, cdecl)
- Default structure packing (8 for MSVC, 1 for GCC/Clang)
- Name mangling scheme (msvc or itanium)
- Determinism capability

### 2.3 Toolchain Descriptor

Generated descriptor includes:
- Compiler identity (name, version, executable path, hash)
- Linker identity (executable path, hash, version)
- Target triple (OS-architecture-ABI)
- ABI properties (calling convention, packing, mangling)
- Capabilities (debug symbols, optimization, determinism)

Descriptor is serialized to JSON and preserved as build artifact.

### 2.4 Validation Rules

**Rule 1: Executable Existence**
All toolchain executables must exist and be executable.

**Rule 2: Version Extractability**
System must extract version information. Compilers that don't support --version
or equivalent are rejected.

**Rule 3: Target Compatibility**
Toolchain target must match build target. Cannot use Linux toolchain for Windows builds.

**Rule 4: Minimum Version**
If specified, toolchain must meet minimum version requirements.

**Rule 5: ABI Compatibility**
Toolchain's default ABI must be compatible with verification requirements.

### 2.5 Implementation Classes

**ToolchainDescriptor**
- Comprehensive toolchain metadata
- Serializable to JSON
- Includes provenance (hashes, timestamps)

**ToolchainDetector**
- Discovers available toolchains
- Extracts version and ABI information
- Generates validated descriptors

**ToolchainValidator**
- Validates toolchains against requirements
- Enforces minimum versions
- Checks ABI compatibility

### 2.6 Integration Points

Toolchain descriptors are used by:
- Native compilation stages
- ABI fidelity validation
- Build provenance tracking
- Incremental build change detection

---

**End of  Content**  
**Next Prompt:** Build Stage Pipeline Infrastructure

### 1.1 Introduction

The Build Process module treats build correctness as inseparable from verification
correctness. Unlike conventional build systems that prioritize convenience, this
module prioritizes explicitness, determinism, and auditability.

### 1.2 Core Principles

**Principle 1: Build-as-Correctness**
The build process is a first-class correctness component. Verification guarantees
depend on build correctness.

**Principle 2: Explicitness Over Convenience**
All ABI-relevant configuration must be declared explicitly. No implicit defaults.

**Principle 3: Determinism**
Identical inputs produce identical outputs. Nondeterminism is documented explicitly.

**Principle 4: Domain Isolation**
Three build domains (native tooling, orchestration, verification targets) remain
strictly isolated.

**Principle 5: Complete Provenance**
Every artifact includes metadata documenting how it was produced.

### 1.3 Build Domain Separation

#### Domain 1: Native Verification Tooling
- Components: ABI observers, runtime controllers, crash handlers
- Requirements: Exact ABI knowledge, no target dependencies
- Isolation: Cannot link against verification targets

#### Domain 2: Orchestration & Adapter Tooling
- Components: Python orchestration, generated wrappers, reporting
- Requirements: Stable interfaces, target-agnostic
- Isolation: No compile-time dependencies on targets

#### Domain 3: Verification Targets
- Components: Native libraries being analyzed
- Requirements: Described and validated, not built by verifier
- Isolation: Never influence verifier build

### 1.4 Seven-Stage Build Pipeline

1. **Source Enumeration**: Exhaustively identify all source artifacts
2. **Source Validation**: Validate syntax, structure, toolchain compatibility
3. **Dependency Resolution**: Resolve fixed-version dependencies with integrity checks
4. **Native Compilation**: Compile with explicit ABI configuration
5. **Adapter Generation**: Generate and validate adapters from contracts
6. **Orchestration Assembly**: Assemble cross-component workflows
7. **Packaging & Validation**: Package with manifests and perform final checks

Each stage enforces preconditions and postconditions.

### 1.5 Implementation Architecture

#### Core Classes

**BuildPhilosophy**
- Encodes and enforces philosophical principles
- Validates configurations against principles
- Rejects implicit defaults and silent fallbacks

**EnvironmentDescriptor**
- Comprehensive build environment description
- Captures toolchain, platform, ABI configuration
- Serializable for provenance and reproducibility

**BuildStageInterface**
- Abstract base for all pipeline stages
- Enforces precondition/postcondition contract
- Standardizes stage execution pattern

**BuildProcessOrchestrator**
- Top-level pipeline controller
- Manages stage execution order
- Generates provenance artifacts

### 1.6 Integration with Module 02

Module 03 does not replace Module 02's verification pipeline. Instead:
- Module 03: HOW the verification system is built
- Module 02: WHAT the verification system does

Module 03 provides build validation artifacts that Module 02 references to
ensure runtime assumptions match build-time guarantees.

---

**End of  Content**  
**Next Prompt:** Environment Descriptor Implementation & Toolchain Detection
