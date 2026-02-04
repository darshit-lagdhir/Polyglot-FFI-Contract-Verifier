# Module 03: Build Process & Toolchain Integration

**Module ID:** 03 of 28  
**Version:** 1.0.0  
**Status:** IN PROGRESS  
**Purpose:** Foundational build system with correctness guarantees

---

## Table of Contents

1. [Build Philosophy & Core Architecture](#1-build-philosophy-core-architecture)
2. [Toolchain Detection & Validation](#2-toolchain-detection--validation)
3. [Build Stage Pipeline Infrastructure](#3-build-stage-pipeline-infrastructure)
4. [Source Enumeration & Dependency Graph](#4-source-enumeration--dependency-graph)
5. [Dependency Resolution & Package Management](#5-dependency-resolution--package-management)
6. [Toolchain Validation & Capability Detection](#6-toolchain-validation--capability-detection)
... (sections 7-20 to be added in subsequent prompts)

---

## 1. Build Philosophy & Core Architecture

...

---

## 2. Toolchain Detection & Validation

...

---

## 3. Build Stage Pipeline Infrastructure

...

---

## 4. Source Enumeration & Dependency Graph

### 4.1 Enhanced Source Discovery

Source enumeration is a semantic discovery process that:
- Identifies all source artifacts
- Extracts rich metadata for each source
- Discovers dependencies between sources
- Constructs queryable dependency graph
- Classifies sources by role and language

### 4.2 Source Metadata

Each source file has comprehensive metadata:

**File Properties**:
- Path (absolute and relative)
- Size (bytes)
- Line count
- Encoding
- Hash (SHA-256)
- Last modified timestamp

**Language Classification**:
- Language (C, C++, Python, Rust, etc.)
- Role (production, test, generated, build, example)
- Build domain (native, orchestration, targets)

**Dependencies**:
- List of dependencies (files this source depends on)
- Dependency type (include, import, link)

**Semantic Annotations**:
- Correctness sensitive (influences verification guarantees)
- ABI relevant (influences ABI behavior)
- Generated (not hand-written)

### 4.3 Language-Specific Handlers

Different languages have dedicated handlers:

**CSourceHandler**:
- Handles .c, .cpp, .h, .hpp files
- Extracts #include dependencies
- Distinguishes system vs. local includes
- Marks headers as ABI-relevant

**PythonSourceHandler**:
- Handles .py files
- Extracts import dependencies using AST parsing
- Distinguishes standard library vs. local imports
- Classifies by role (production, test, generated)

### 4.4 Dependency Graph

The dependency graph is a directed acyclic graph (DAG):
- **Nodes**: Source files with metadata
- **Edges**: Dependencies (A depends on B)

**Graph operations**:
- `get_dependencies(source)`: Direct dependencies of source
- `get_dependents(source)`: Sources that depend on this source
- `topological_sort()`: Build order (dependencies first)
- `detect_cycles()`: Find circular dependencies

### 4.5 Source Classification

Sources are classified multiple ways:

**By Role**:
- **Production**: Core implementation
- **Test**: Unit/integration tests
- **Generated**: Auto-generated code
- **Build**: Build scripts
- **Example**: Demonstrations

**By Language**:
- **C/C++**: Native sources
- **Python**: Orchestration sources
- **Rust**: Native components
- **Build**: CMake, Makefiles, etc.

**By Domain**:
- Native Verification Tooling
- Orchestration & Adapter Tooling
- Verification Targets

### 4.6 Usage

```python
stage = EnhancedSourceEnumerationStage(Path("src"))
context = stage.execute({'environment': env})

# Query metadata
metadata = context['source_metadata']['src/main.c']
print(f"Language: {metadata['language']}")
print(f"Dependencies: {metadata['dependencies']}")

# Query by role
production_sources = context['sources_by_role']['production']
test_sources = context['sources_by_role']['test']

# Query dependency graph
graph_data = context['dependency_graph']
print(f"Nodes: {len(graph_data['nodes'])}")
print(f"Edges: {len(graph_data['edges'])}")
```

---

**End of  Content**  
**Next Prompt:** Dependency Resolution & Package Management

...

---

## 2. Toolchain Detection & Validation

...

---

## 3. Build Stage Pipeline Infrastructure

### 3.1 Seven-Stage Architecture

The build process is structured as seven sequential stages, each with explicit
preconditions and postconditions:

**Stage 1: Source Enumeration**
- Preconditions: Environment descriptor, source root exists
- Action: Exhaustively enumerate all source files
- Postconditions: All sources enumerated, hashes computed

**Stage 2: Source Validation**
- Preconditions: Source files enumerated, toolchain descriptor exists
- Action: Validate syntax and toolchain compatibility
- Postconditions: All sources validated as parseable

**Stage 3: Dependency Resolution**
- Preconditions: Dependency manifest (optional)
- Action: Resolve external dependencies with fixed versions
- Postconditions: All dependencies resolved

**Stage 4: Native Compilation** (to be implemented)
- Preconditions: Validated sources, toolchain, dependencies
- Action: Compile native components with explicit ABI configuration
- Postconditions: All binaries produced, debug symbols preserved

**Stage 5: Adapter Generation** (to be implemented)
- Preconditions: Compiled binaries, contract specifications
- Action: Generate runtime adapters from contracts
- Postconditions: Adapters validated against contracts

**Stage 6: Orchestration Assembly** (to be implemented)
- Preconditions: Native tooling, adapters, orchestration sources
- Action: Assemble cross-component workflows
- Postconditions: All components integrated

**Stage 7: Packaging & Validation** (to be implemented)
- Preconditions: All artifacts produced
- Action: Package with manifests, perform final validation
- Postconditions: Complete, validated build artifacts

### 3.2 Precondition/Postcondition Contract

Each stage implements a strict contract:

```python
class BuildStageInterface:
    def check_preconditions(context) -> None:
        # Validate required inputs exist and are valid
        # Raise BuildPreconditionError if violated
    
    def execute(context) -> updated_context:
        # Perform stage logic
        # Return updated context with outputs
    
    def validate_postconditions(context) -> None:
        # Validate stage produced required outputs
        # Raise BuildPostconditionError if violated
```

Violations halt the build immediately with diagnostic information.

### 3.3 Build Context

The build context is a dictionary that accumulates state across stages:

```python
{
    'environment': EnvironmentDescriptor,
    'toolchain': ToolchainDescriptor,
    'source_files': {...},
    'source_hashes': {...},
    'validation_results': {...},
    'dependencies': {...},
    # ... more outputs as stages execute
}
```

Each stage:
1. Receives context from previous stages
2. Validates preconditions against context
3. Executes and updates context
4. Validates postconditions
5. Returns updated context

### 3.4 Checkpoint Management

The pipeline supports resumable builds through checkpointing:

**Checkpoint Creation**: After each successful stage, context is serialized to: `checkpoint_stage_N.pkl`

**Checkpoint Resumption**: Build can resume from any saved checkpoint:

```python
orchestrator.execute_build_with_checkpoints(resume_from=BuildStage.DEPENDENCY_RESOLUTION)
```

**Checkpoint Safety**:
- Checkpoints only saved after postconditions pass
- Resumption validates checkpoint compatibility
- Stale checkpoints detected via timestamps

### 3.5 Failure Diagnostics

When stages fail, the system generates comprehensive diagnostics:

**Diagnostic Contents**:
- Stage name and number where failure occurred
- Exception type and message
- Precondition or postcondition that failed
- Full build context snapshot
- Environment and toolchain details
- Suggested remediation steps

**Diagnostic Artifacts**:
- Console output with structured failure report
- `failure_diagnostic.txt` saved to checkpoint directory
- Build context preserved for post-mortem analysis

### 3.6 Implementation Classes

- **BuildStageInterface**: Abstract base class defining stage contract.
- **SourceEnumerationStage**: Implements Stage 1: Finds and hashes all source files.
- **SourceValidationStage**: Implements Stage 2: Validates syntax and toolchain compatibility.
- **DependencyResolutionStage**: Implements Stage 3: Resolves external dependencies.
- **PipelineCheckpoint**: Manages checkpoint save/load operations.
- **EnhancedBuildProcessOrchestrator**: Extended orchestrator with checkpoint and diagnostic support.

### 3.7 Usage Example

```python
# Configure environment
env = EnvironmentDescriptor(...)

# Create orchestrator with checkpoints
orchestrator = EnhancedBuildProcessOrchestrator(
    environment_descriptor=env,
    checkpoint_dir=Path("build_checkpoints")
)

# Register stages
orchestrator.register_stage(SourceEnumerationStage(Path("src")))
orchestrator.register_stage(SourceValidationStage())
orchestrator.register_stage(DependencyResolutionStage())

# Execute build
try:
    context = orchestrator.execute_build_with_checkpoints()
    print(f"Build succeeded: {context['status']}")
except BuildError as e:
    print(f"Build failed: {e}")
    # Checkpoints preserved - can resume later
```

---

**End of  Content**  
**Next Prompt:** Source Enumeration & Dependency Graph Parsing

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

## 5. Dependency Resolution & Package Management

### 5.1 Dependency Resolution as Correctness

Dependency resolution ensures builds operate on known, validated, reproducible
external dependencies with verified integrity.

**Risks Addressed**:
- Supply chain attacks (compromised packages)
- Dependency drift (different versions across builds)
- License incompatibility (legal risks)
- Transitive conflicts (incompatible version requirements)

### 5.2 Dependency Specification

Each dependency has comprehensive specification:

```python
DependencySpecification:
    name: str              # Package name
    version: str           # Exact version (not range)
    source: str            # PyPI, crates.io, system, git, local
    hash: str              # SHA-256 hash for verification
    license: str           # SPDX license identifier
    scope: str             # runtime, build, test, dev
    platform: str          # Platform-specific or all
    transitive: bool       # Direct or transitive dependency
```

### 5.3 Lock Files

Lock files capture exact resolved dependency tree:

**Format**:
```json
{
    "lock_version": "1.0.0",
    "generated": "2026-02-04T12:00:00Z",
    "platform": "Windows-x86_64",
    "dependencies": {
        "package_name": {
            "version": "1.2.3",
            "hash": "sha256:abc123...",
            "source": "PyPI",
            "transitive_deps": ["other_package"]
        }
    }
}
```

**Usage**:
- Generated during initial resolution
- Committed to version control
- Used for reproducible builds
- Updated explicitly (not automatically)

### 5.4 Hash Verification

Every dependency verified via cryptographic hash:

**Process**:
1. Download dependency from source
2. Compute SHA-256 hash
3. Compare against declared hash
4. Refuse installation if mismatch
5. Log verification for provenance

**Cache**:
- Dependencies cached locally (content-addressed)
- Cache verified on use (re-hash)
- Supports offline builds

### 5.5 Conflict Detection

Version conflicts detected and reported:

**Example Conflict**:
- Package A requires X >= 1.0, < 2.0
- Package B requires X >= 2.0, < 3.0
- → No version of X satisfies both

**Resolution Strategies**:
- **Strict mode**: Fail on any conflict
- **Permissive mode**: Try to find compatible version
- **Override mode**: Manual pinning (documented)

### 5.6 Implementation Classes

- **DependencySpecification**: Complete dependency metadata with hash verification.
- **DependencyLockFile**: Serializable lock file with save/load operations.
- **DependencyResolver**: Resolves transitive dependencies, detects conflicts, verifies hashes.
- **EnhancedDependencyResolutionStage**: Stage 3 implementation with lock file support.

### 5.7 Usage Example

```python
# Create resolver with cache
resolver = DependencyResolver(cache_dir=Path(".cache"))

# Define dependencies
deps = [
    DependencySpecification(
        name="libclang",
        version="16.0.6",
        source="pypi",
        hash="sha256:abc123..."
    )
]

# Resolve
lock_file = resolver.resolve(deps)

# Save lock file
lock_file.save(Path("dependencies.lock"))

# Later: Install from lock file
resolver.install_from_lock(lock_file)
```

---

## 6. Toolchain Validation & Capability Detection

### 6.1 Comprehensive Toolchain Validation

Toolchain validation verifies that detected toolchains can build verification
tooling correctly through:
- **Feature detection**: (language standards, sanitizers, optimizations)
- **ABI compatibility verification**: (structure layout, calling conventions)
- **Self-tests**: (compile and execute test programs)
- **Determinism validation**: (reproducible binary outputs)

### 6.2 Toolchain Capabilities

Complete capability model:

```python
ToolchainCapabilities:
    language_standards: {'c': [...], 'cpp': [...]}
    sanitizers: ['asan', 'ubsan', 'tsan']
    optimization_levels: ['O0', 'O1', 'O2', 'O3']
    supports_lto: bool
    debug_formats: ['dwarf4', 'dwarf5']
    calling_conventions: ['cdecl', 'stdcall']
    abi_compatible: bool
    deterministic_output: bool
```

### 6.3 Validation Process

**: Language Standard Detection**
Test compilation with various `-std=` flags to detect supported standards.

**: Sanitizer Detection**
Test compilation with `-fsanitize=` flags to detect available sanitizers.

**: Optimization Detection**
Test compilation with `-O` flags and `-flto` for LTO support.

**: ABI Validation**
Compile structure layout test and verify expected padding/offsets.

**: Determinism Validation**
Compile same program twice and compare binary hashes.

**: Smoke Test**
Compile and execute simple program to verify basic functionality.

### 6.4 Validation Caching

Validation results cached to avoid repeated expensive tests:
- **Cache Key**: `{compiler}-{version}-{architecture}`
- **Cache Invalidation**:
  - Compiler executable changed (hash mismatch)
  - Cache older than 30 days
  - Explicit cache clear requested

**Cache Structure**:
```json
{
    "timestamp": "2026-02-04T12:00:00Z",
    "compiler_hash": "abc123...",
    "capabilities": {...}
}
```

### 6.5 Implementation Classes

- `ToolchainCapabilities`: Complete capability model with serialization.
- `ToolchainValidator`: Performs all validation tests and generates capability matrix.

### 6.6 Usage Example

```python
# Create validator
validator = ToolchainValidator(toolchain_descriptor)

# Validate (uses cache if available)
capabilities = validator.validate()

# Query capabilities
if 'asan' in capabilities.sanitizers:
    print("AddressSanitizer available")

if caps.deterministic_output:
    print("Toolchain produces reproducible builds")
```

---

**End of  Content**  
**Next Prompt:** ABI Fidelity Enforcement & Compiler Config
