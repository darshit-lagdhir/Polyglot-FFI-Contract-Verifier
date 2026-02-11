
**Module ID:** 03 of 28  
**Version:** 1.0.0  
**Status:** COMPLETE  
**Purpose:** Foundational build system with correctness guarantees

---

## Table of Contents

1. [Build Philosophy & Core Architecture](#1-build-philosophy-core-architecture)
2. [Toolchain Detection & Validation](3. [Build Stage Pipeline Infrastructure](#3-build-stage-pipeline-infrastructure)
4. [Source Enumeration & Dependency Graph](#4-source-enumeration--dependency-graph)
5. [Dependency Resolution & Package Management](#5-dependency-resolution--package-management)
6. [Toolchain Validation & Capability Detection](7. [ABI Fidelity Enforcement & Compiler Config](#7-abi-fidelity-enforcement--compiler-configuration)
8. [Native Compilation & Object File Generation](#8-native-compilation--object-file-generation)
9. [Native Validation & Binary Self-Tests](#9-native-validation--binary-self-tests)
10. [Link-Time Control & Executable Generation](#10-link-time-control--executable-generation)
11. [Adapter Generation & Contract Integration](#11-adapter-generation--contract-integration)
12. [Orchestration Assembly & Python Integration](#12-orchestration-assembly--python-integration)
13. [Build Completion & Validation Gates](#13-build-completion--validation-gates)
14. [Incremental Build Infrastructure](#14-incremental-build-infrastructure)
15. [Cache Management & Eviction Policies](#15-cache-management--eviction-policies)
16. [Build Reproducibility & Determinism](#16-build-reproducibility--determinism)
17. [Build Performance Profiling & Optimization](#17-build-performance-profiling--optimization)
18. [Build Error Diagnostics & Recovery](#18-build-error-diagnostics--recovery)
19. [Cross-Platform Build Support](#19-cross-platform-build-support)
20. [Module Integration & Final Documentation](#20-module-integration--final-documentation)

---

## 1. Build Philosophy & Core Architecture

...

---


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
            
    def execute(context) -> updated_context:
        # Perform stage logic
        # Return updated context with outputs
    
    def validate_postconditions(context) -> None:
        # Validate stage produced required outputs
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


- Components: ABI observers, runtime controllers, crash handlers
- Requirements: Exact ABI knowledge, no target dependencies
- Isolation: Cannot link against verification targets

- Components: Python orchestration, generated wrappers, reporting
- Requirements: Stable interfaces, target-agnostic
- Isolation: No compile-time dependencies on targets

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



Toolchain validation verifies that detected toolchains can build verification
tooling correctly through:
- **Feature detection**: (language standards, sanitizers, optimizations)
- **ABI compatibility verification**: (structure layout, calling conventions)
- **Self-tests**: (compile and execute test programs)
- **Determinism validation**: (reproducible binary outputs)


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

capabilities = validator.validate()

# Query capabilities
if 'asan' in capabilities.sanitizers:
    print("AddressSanitizer available")

if caps.deterministic_output:
    print("Toolchain produces reproducible builds")
```

---

## 7. ABI Fidelity Enforcement & Compiler Config

### 7.1 ABI Fidelity as Foundation

ABI fidelity ensures that verification analyzes the actual ABI behavior of target
code, not an incorrect model. Mismatches between assumed and actual ABI invalidate
verification results.

### 7.2 ABI Config

Declarative ABI specifications in YAML:

```yaml
abi_specification:
  platform: "Windows-x86_64"
  structure_packing:
    default: 8
    compiler_flags:
      msvc: "/Zp8"
  calling_convention:
    default: "microsoft_x64"
  exception_handling:
    enabled: true
    model: "seh"
```

### 7.3 Compiler Flag Management

`CompilerFlagManager` handles:
- **Flag priority resolution**: (file > target > ABI > global)
- **Conflict detection**: (multiple packing flags)
- **Platform-specific flag generation**:
- **Validation of flag compatibility**

**Priority Hierarchy**:
1. File-specific flags (highest)
2. Target-specific flags
3. ABI configuration flags
4. Global flags (lowest)

### 7.4 Runtime ABI Verification

`ABIVerifier` performs runtime checks:
- Structure layout verification (sizes, offsets)
- Calling convention verification
- Name mangling verification
- Symbol presence verification

### 7.5 ABI Drift Detection

`ABIDriftDetector` compares builds:
- Records ABI baseline (structures, symbols, conventions)
- Detects changes between builds
- Categorizes drift (breaking, non-breaking, suspicious)

**Drift Categories**:
- **Breaking**: Structure size changed
- **Non-breaking**: New symbols added
- **Suspicious**: Mangling changed

### 7.6 Implementation Classes

- `ABIConfig`: Declarative ABI specification loaded from YAML.
- `CompilerFlagManager`: Manages flags with priority and conflict resolution.
- `ABIVerifier`: Runtime verification of library ABI.
- `ABIDriftDetector`: Detects ABI changes between builds.

### 7.7 Usage Example

```python
# Load ABI configuration
abi_config = ABIConfig.from_yaml(Path("abi_config.yaml"))

# Create flag manager
flag_manager = CompilerFlagManager(abi_config, toolchain)

# Add global optimization flags
flag_manager.add_global_flags(["-O2"])

# Get flags for specific file
flags = flag_manager.get_flags_for_file("src/module.c")

# Verify ABI at runtime
verifier = ABIVerifier(abi_config)
verifier.verify_structure_layout("MyStruct", 12, {"a": 0, "b": 4})
print(verifier.generate_report())

# Detect drift
drift_detector = ABIDriftDetector(Path("baseline.json"))
drift = drift_detector.detect_drift(current_snapshot)
if drift:
    print(f"ABI drift detected: {drift}")
```

---

## 8. Native Compilation & Object File Generation

### 8.1 Stage 4: Native Compilation

Native compilation transforms validated sources into object files with full 
provenance tracking and ABI enforcement.

**Inputs**:
- Validated sources (Stage 2)
- Toolchain descriptor ( & 6)
- ABI configuration
- Dependency graph

**Outputs**:
- Object files (`.o`, `.obj`)
- Debug symbols (`.pdb`, DWARF)
- Compilation metadata (provenance)

### 8.2 Compilation Unit

Complete specification for compiling a source:

```python
CompilationUnit:
    source_file: Path
    output_file: Path
    dependencies: List[Path]
    compiler_flags: List[str]
    include_paths: List[Path]
    defines: Dict[str, str]
    language: 'c' | 'cpp'
    build_mode: DEBUG | RELEASE
    abi_config: ABIConfig
    metadata: CompilationMetadata
```

### 8.3 Compilation Metadata

Provenance tracking for each compilation:

```python
CompilationMetadata:
    source_hash: SHA-256 of source
    output_hash: SHA-256 of object file
    compiler: "MSVC 19.29"
    compiler_hash: SHA-256 of compiler exe
    flags_used: ['/Zp8', '/O2', ...]
    dependencies: ['header1.h', ...]
    compilation_timestamp: ISO 8601
    compilation_duration: seconds
    success: bool
    warnings: [...]
    errors: [...]
```

### 8.4 Parallel Compilation

Compilation units compiled in parallel:
- Respects dependency order
- Limited to CPU count
- Handles failures gracefully
- Preserves determinism

### 8.5 Incremental Compilation

Recompile only when necessary:
- **Output missing** → recompile
- **Source changed (hash)** → recompile
- **Dependencies changed** → recompile
- **Compiler changed** → recompile
- **Flags changed** → recompile

### 8.6 Implementation Classes

- `CompilationMetadata`: Provenance tracking for compilations.
- `CompilationUnit`: Complete compilation specification.
- `CompilerInvocation`: Command-line construction and execution.
- `NativeCompiler`: Manages parallel compilation with caching.
- `NativeCompilationStage`: Stage 4 implementation.

### 8.7 Usage Example

```python
# Create stage
stage = NativeCompilationStage(
    output_dir=Path("build/obj"),
    build_mode=BuildMode.RELEASE
)

# Execute
context = stage.execute({
    'toolchain': toolchain_descriptor,
    'abi_config': abi_configuration,
    'sources_by_language': {
        'c': ['src/main.c', 'src/utils.c']
    }
})

# Check results
compilation = context['native_compilation']
print(f"Compiled {compilation['units_compiled']} units")
print(f"Time: {compilation['total_duration']:.2f}s")
```

---

## 9. Native Validation & Binary Self-Tests

### 9.1 Post-Compilation Validation

Stage 4.5 validates compiled object files beyond compiler error checking:
- **Object file format validation**
- **Symbol inspection and verification**
- **Debug symbol presence checking**
- **ABI conformance validation**
- **Binary self-tests** (runtime verification)

### 9.2 Object File Format Validation

Validates that compiled files are valid object code:

**Checks**:
- File exists and is non-empty
- Magic bytes match expected format (ELF, PE/COFF, Mach-O)
- File structure is parseable

**Detects**:
- Truncated files (corruption during write)
- Wrong file types (build script errors)
- Invalid object formats

### 9.3 Symbol Inspection

Extracts and validates symbols in object files:

**Platform-Specific Tools**:
- **Linux/macOS**: `nm` for symbol extraction
- **Windows**: `dumpbin` for symbol extraction

**Validation**:
- Verify expected symbols present
- Check symbol types (function vs data)
- Verify export visibility

**Detects**:
- Missing exports (visibility errors)
- Name mangling issues
- Linker stripping problems

### 9.4 Debug Symbol Validation

Verifies debug information is complete:

**Checks**:
- Debug sections present (DWARF on Unix, PDB on Windows)
- Debug info covers source lines
- Function debug entries present

**Detects**:
- Missing debug flags (compilation without -g)
- Stripped symbols (post-processing removed them)
- Incomplete debug coverage

### 9.5 Validation Result Model

```python
ValidationResult:
    object_file: Path
    format_valid: bool
    symbols_valid: bool
    debug_symbols_valid: bool
    abi_conformance_valid: bool
    self_test_passed: bool
    issues: List[str]
    warnings: List[str]
    overall_valid: bool
```

### 9.6 Implementation Classes

- `Symbol`: Represents a symbol in an object file (name, type, address).
- `ObjectFileValidator`: Performs all validation checks on object files.
- `ValidationResult`: Captures validation results with detailed issue tracking.
- `NativeValidationStage`: Stage 4.5 implementation (post-compilation validation).

### 9.7 Usage Example

```python
# Create validation stage
stage = NativeValidationStage()

# Execute (after Stage 4)
context = stage.execute({
    'native_compilation': {
        'object_files': ['build/obj/main.o'],
        'success': True
    },
    'toolchain': toolchain_descriptor
})

# Check results
validation = context['native_validation']
if validation['all_valid']:
    print("All object files validated successfully")
else:
    for result in validation['validation_results']:
        if not result['overall_valid']:
            print(f"Failed: {result['object_file']}")
            for issue in result['issues']:
                print(f"  - {issue}")
```

---

## 10. Link-Time Control & Executable Generation

### 10.1 Stage 5: Linking

Linking combines validated object files into complete executables and libraries.

**Inputs**:
- Validated object files (Stage 4.5)
- Toolchain descriptor
- Linker configuration

**Outputs**:
- Executables (`.exe`, ELF)
- Shared libraries (`.dll`, `.so`, `.dylib`)
- Linking metadata (provenance)

### 10.2 Link Target Specification

Complete specification for a link operation:

```python
LinkTarget:
    target_name: str
    target_type: 'executable' | 'shared_library'
    object_files: List[Path]
    output_path: Path
    linker_flags: List[str]
    libraries: List[str]
    enable_lto: bool
```

### 10.3 Linking Metadata

Provenance tracking for links:

```python
LinkingMetadata:
    target_name: str
    input_objects: List[Path]
    output_executable: Path
    output_hash: SHA-256
    linker_flags: List[str]
    libraries_linked: List[str]
    lto_enabled: bool
    link_duration: seconds
    build_id: str
```

### 10.4 Link-Time Optimization

LTO enabled conditionally:
- Requires toolchain support
- Enabled for RELEASE builds
- Disabled for DEBUG (complicates debugging)

**Flags**:
- Compilation: `-flto`
- Linking: `-flto` (MSVC: `/LTCG`)

### 10.5 Executable Validation

Post-link validation:
- Executable format (PE/ELF/Mach-O)
- Entry point present
- File permissions correct
- No undefined symbols (executables)

### 10.6 Implementation Classes

- `LinkingMetadata`: Provenance metadata for linking.
- `LinkTarget`: Complete link specification.
- `Linker`: Manages link command construction and execution.
- `ExecutableValidator`: Validates linked executables.
- `LinkingStage`: Stage 5 implementation.

### 10.7 Usage Example

```python
# Create linking stage
stage = LinkingStage(
    output_dir=Path("build/bin"),
    enable_lto=True
)

# Execute
context = stage.execute({
    'native_compilation': {
        'object_files': ['build/obj/main.o', 'build/obj/utils.o']
    },
    'native_validation': {
        'all_valid': True
    },
    'toolchain': toolchain_descriptor
})

# Check results
linking = context['linking']
if linking['all_successful']:
    print(f"Executables: {linking['executables']}")
```

---

## 11. Adapter Generation & Contract Integration

### 11.1 Stage 6: Adapter Generation

Generates runtime wrapper code from declarative contract specifications.

**Purpose**:
- Enforce contracts at FFI boundaries
- Validate preconditions/postconditions
- Log contract violations
- Translate error representations

### 11.2 Contract Specification

Declarative format (JSON):

```json
{
  "library_name": "libmath",
  "functions": [
    {
      "name": "add",
      "signature": "int add(int a, int b)",
      "preconditions": ["a >= INT_MIN", "b >= INT_MAX"],
      "postconditions": ["result == a + b"]
    }
  ]
}
```

### 11.3 Adapter Code Generation

Template-based synthesis:
1. Load contract specification
2. Select template based on target language
3. Expand template with contract data
4. Validate generated code syntax
5. Compile to object files

### 11.4 Adapter Metadata

Provenance tracking for adapters:

```python
AdapterMetadata:
    contract_name: str
    contract_hash: SHA-256 of contract
    adapter_source_hash: SHA-256 of generated code
    generator_version: str
    generation_timestamp: ISO 8601
    template_used: str
    validation_passed: bool
```

### 11.5 Incremental Regeneration

Regenerate only when necessary:
- Contract changed (hash mismatch)
- Generator version changed
- Template changed
- Adapter source missing

### 11.6 Multi-Language Support

Target languages:
- **C**: Direct FFI wrapping
- **C++**: Exception-based error handling
- **Rust**: Memory-safe FFI via `extern "C"`

### 11.7 Implementation Classes

- `AdapterMetadata`: Provenance tracking for adapters.
- `AdapterGenerator`: Template-based code synthesis.
- `AdapterGenerationStage`: Stage 6 implementation.

### 11.8 Usage Example

```python
# Create stage
stage = AdapterGenerationStage(
    adapter_dir=Path("build/adapters"),
    contract_dir=Path("contracts")
)

# Execute
context = stage.execute({
    'toolchain': toolchain_descriptor
})

# Check results
adapters = context['adapter_generation']
print(f"Generated {len(adapters['generated_adapters'])} adapters")
```

---

## 12. Orchestration Assembly & Python Integration

### 12.1 Stage 7: Final Integration

Assembles all components into deployable verification system.

**Components Integrated**:
- Native executables and libraries
- Generated adapters
- Python orchestration layer
- Config files
- Documentation

### 12.2 Python Package Structure

Generated structure:

```text
verification_tool/
├── __init__.py          # Package entry
├── __main__.py          # CLI entry (python -m)
├── cli.py               # Command-line interface
├── api.py               # Programmatic API
├── native/              # Native libraries
├── adapters/            # Generated adapters
└── config/              # Config files
```

### 12.3 Build Manifest

Complete build provenance:

```json
{
  "build_timestamp": "2026-02-04T12:00:00Z",
  "components": {
    "executables": [...],
    "adapters": [...],
    "python_modules": [...]
  },
  "provenance": {
    "toolchain": "GCC 11.2.0",
    "environment": "Linux-x86_64"
  }
}
```

### 12.4 Implementation Classes

- `BuildManifest`: Complete build artifact documentation.
- `PackageAssembler`: Creates Python package structure.
- `OrchestrationAssemblyStage`: Stage 7 implementation.

### 12.5 Usage Example

```python
# Create stage
stage = OrchestrationAssemblyStage(
    output_dir=Path("dist")
)

# Execute
context = stage.execute({
    'linking': {'executables': ['verify'], 'all_successful': True},
    'adapter_generation': {'generated_adapters': ['adapter.c']}
})

# Check results
package_dir = context['orchestration']['package_directory']
print(f"Package ready: {package_dir}")
```

---

## 13. Build Completion & Validation Gates

### 13.1 Build Completion Validation

Build completion is formal verification that all requirements are met.

**Validation Process**:
- Run all validation gates
- Collect results
- Generate completion report
- Mark build as complete (if all required gates pass)

### 13.2 Validation Gates

Multiple validation gates verify different aspects:

1.  **ArtifactExistenceGate**: 
    - Verifies all executables exist
    - Verifies package directory created
    - Required gate (build fails if not passed)

2.  **ArtifactIntegrityGate**:
    - Validates artifact hashes
    - Detects file corruption
    - Required gate

3.  **DocumentationCompletenessGate**:
    - Checks for required documentation
    - Warning-level gate (build succeeds with warnings)

### 13.3 Validation Result Model

```python
ValidationResult:
    gate_name: str
    passed: bool
    successes: List[str]
    errors: List[str]
    warnings: List[str]
```

### 13.4 Build Completion Report

Comprehensive report:

```text
BUILD COMPLETION REPORT
Timestamp: 2026-02-04T12:00:00Z
Overall Status: ✓ SUCCESS

Validation Gates:
  Total: 3
  Passed: 2
  Failed: 0
  Warnings: 1
```

### 13.5 Implementation Classes

- `ValidationResult`: Result of single gate validation.
- `ValidationGate` (ABC): Abstract base for validation gates.
- `ArtifactExistenceGate`: Validates artifact existence.
- `ArtifactIntegrityGate`: Validates artifact integrity.
- `DocumentationCompletenessGate`: Validates documentation.
- `BuildCompletionReport`: Complete validation report.
- `BuildCompletionValidator`: Runs all gates and generates report.

### 13.6 Usage Example

```python
# Create validator
validator = BuildCompletionValidator()

# Validate build
report = validator.validate_build(context)

# Check results
if report.build_successful:
    print("Build completed successfully!")
    report.save(Path("build_completion.txt"))
else:
    print(f"Build failed: {report.required_gates_failed} gates failed")
```

---

## 14. Incremental Build Infrastructure

### 14.1 Incremental Build Optimization

Incremental builds rebuild only changed components for faster iteration.

**Benefits**:
- Reduced build times (seconds vs minutes)
- Faster development iteration
- Lower CI/CD resource usage

**Correctness Guarantees**:
- Conservative invalidation (when uncertain, rebuild)
- Dependency propagation (changes propagate through graph)
- Toolchain change detection (compiler change triggers rebuild)

### 14.2 Build Cache

Cached artifacts with validation metadata:

```text
.build_cache/
├── objects/          # Cached object files
├── cache_index.json  # Cache metadata
└── validation/       # Validation results
```

**Cache Entry**:

```json
{
    "source_file": "src/main.c",
    "source_hash": "abc123...",
    "output_hash": "def456...",
    "dependencies": [...],
    "compiler_hash": "789abc...",
    "flags": ["-O2", "-g"]
}
```

### 14.3 Cache Validation

Cache entry valid if:
- Source hash matches
- All dependency hashes match
- Compiler hash matches
- Flags match
- Output file exists

Otherwise, rebuild required.

### 14.4 Change Propagation

Changes propagate through dependency graph:
1. Detect changed sources
2. Find all dependents (transitive closure)
3. Mark dependents for rebuild
4. Rebuild in dependency order

### 14.5 Implementation Classes

- `CacheEntry`: Metadata for cached artifact.
- `BuildCache`: Manages cache storage and retrieval.
- `IncrementalBuildManager`: Determines rebuild requirements.

### 14.6 Usage Example

```python
# Create cache
cache = BuildCache(Path(".build_cache"))

# Create incremental manager
manager = IncrementalBuildManager(cache, dependency_graph)

# Determine what to rebuild
to_rebuild, from_cache = manager.get_sources_to_rebuild(
    all_sources,
    toolchain
)

print(f"Rebuilding {len(to_rebuild)} sources")
print(f"Reusing {len(from_cache)} cached artifacts")
```

---

## 15. Cache Management & Eviction Policies

### 15.1 Cache Management

Manages cache size and health through eviction policies.

**Responsibilities**:
- Monitor cache size
- Apply eviction policies
- Remove stale entries
- Generate statistics

### 15.2 Cache Statistics

Tracks cache health:

```python
CacheStatistics:
    total_entries: int
    total_size_mb: float
    entries_by_age: {...}
    stale_entries: int
```

### 15.3 Eviction Policies

Multiple policies available:

1.  **LRU (Least Recently Used)**:
    - Evicts oldest accessed entries first
    - Optimizes for recency
    - Default policy

2.  **Age-Based (TTL)**:
    - Evicts entries older than threshold
    - Default: 30 days
    - Ensures freshness

### 15.4 Cache Manager

Orchestrates cache management:

```python
manager = CacheManager(
    cache=build_cache,
    eviction_policy=LRUEvictionPolicy(),
    max_size_mb=1024
)

# Apply eviction if needed
manager.apply_eviction()

# Clean stale entries
manager.clean_stale_entries()
```

### 15.5 Implementation Classes

- `CacheStatistics`: Cache health metrics.
- `EvictionPolicy` (ABC): Abstract eviction policy.
- `LRUEvictionPolicy`: Least recently used eviction.
- `AgeBasedEvictionPolicy`: Time-to-live eviction.
- `CacheManager`: Orchestrates cache management.

### 15.6 Usage Example

```python
# Create cache manager
manager = CacheManager(cache, max_size_mb=512)

# Get statistics
stats = manager.get_statistics()
print(stats.generate_report())

# Apply eviction
manager.apply_eviction()

# Clean stale
manager.clean_stale_entries()
```

---

## 16. Build Reproducibility & Determinism

### 16.1 Reproducible Builds

Reproducibility ensures building the same source multiple times produces bit-identical outputs.

**Benefits**:
- Verification (binaries match source)
- Security (detect supply chain attacks)
- Debugging (reproduce exact binaries)

### 16.2 Sources of Non-Determinism

**Timestamps**:
- Compiler macros: `__DATE__`, `__TIME__`
- File metadata in archives

**Paths**:
- Absolute paths in debug info

**Randomness**:
- Random seeds in compiler

**Solution**: Control via flags and environment.

### 16.3 SOURCE_DATE_EPOCH

Standard for reproducible timestamps:

```python
# Set based on latest source modification
epoch = set_source_date_epoch(source_files)

# Export for tools
os.environ['SOURCE_DATE_EPOCH'] = str(epoch)
```

### 16.4 Deterministic Flags

Compiler flags for determinism:

```python
flags = [
    '-Wno-builtin-macro-redefined',
    '-D__DATE__="reproducible"',
    '-D__TIME__="reproducible"',
    '-frandom-seed=0'
]
```

### 16.5 Implementation Classes

- `DeterministicBuildConfig`: Config for reproducible builds.
- `DeterministicFlagManager`: Manages determinism compiler flags.
- `ReproducibilityVerifier`: Verifies build reproducibility.

### 16.6 Usage Example

```python
# Set SOURCE_DATE_EPOCH
epoch = set_source_date_epoch(sources)

# Get determinism flags
flag_manager = DeterministicFlagManager(toolchain)
det_flags = flag_manager.get_determinism_flags()

# Build with flags
# ... build process ...

# Verify reproducibility
verifier = ReproducibilityVerifier()
artifacts = verifier.collect_artifacts(context)
verifier.verify_reproducibility(artifacts)
```

---

## 17. Build Performance Profiling & Optimization

### 17.1 Performance Profiling

Comprehensive profiling of build performance:

**Metrics Tracked**:
- Total build time
- Per-stage timing
- Per-file compilation timing
- Cache hit/miss rates
- Parallel speedup factor

### 17.2 Performance Profile

Complete performance snapshot:

```python
BuildPerformanceProfile:
    total_build_time: float
    stage_times: Dict[str, float]
    compilation_times: List[Tuple[Path, float]]
    cache_hit_rate: float
    slowest_stage: str
```

### 17.3 Profiling Integration

`ProfilingBuildStage`: Wraps any stage to add timing measurement.

**Usage**:

```python
original_stage = NativeCompilationStage(...)
profiled_stage = ProfilingBuildStage(original_stage)
```

### 17.4 Optimization Recommendations

`BuildOptimizationAdvisor`: Analyzes profiles and generates recommendations.

**Recommendations Include**:
- Parallel compilation tuning
- Cache configuration
- Precompiled headers
- I/O optimization

### 17.5 Implementation Classes

- `BuildPerformanceProfile`: Complete performance metrics.
- `ProfilingBuildStage`: Stage wrapper with timing.
- `BuildOptimizationAdvisor`: Generates optimization recommendations.

### 17.6 Usage Example

```python
# Wrap stages with profiling
stages = [
    ProfilingBuildStage(EnumerationStage(...)),
    ProfilingBuildStage(CompilationStage(...)),
    ProfilingBuildStage(LinkingStage(...))
]

# Execute build
for stage in stages:
    context = stage.execute(context)

# Generate profile
profile = BuildPerformanceProfile()
profile.stage_times = {
    name: data['wall_time']
    for name, data in context['profiling'].items()
}

# Print report
print(profile.generate_report())

# Get recommendations
advisor = BuildOptimizationAdvisor()
recommendations = advisor.generate_recommendations(profile)
for rec in recommendations:
    print(rec)
```

---

## 18. Build Error Diagnostics & Recovery

### 18.1 Error Diagnostics

Comprehensive error analysis and reporting:

**Error Categories**:
- Compilation errors (syntax, type, declaration)
- Linking errors (undefined reference, multiple definition)
- Config errors (missing toolchain, invalid flags)
- Environment errors (permissions, disk space)

### 18.2 Structured Errors

Errors represented as structured data:

```python
BuildErrorDetail:
    category: str
    source_file: Path
    line_number: int
    parsed_message: str
    suggestions: List[str]
```

### 18.3 Error Parsing

`CompilerErrorParser`: Parses compiler output (GCC, Clang, MSVC) into structured errors.

**Features**:
- Format detection
- Message classification
- Suggestion generation

### 18.4 Error Reporting

`BuildErrorReport`: Generates comprehensive error reports.

**Formats**:
- Console (colored, formatted)
- Text file (for logging)
- HTML (for web viewing)

### 18.5 Implementation Classes

- `BuildErrorDetail`: Structured error representation.
- `CompilerErrorParser`: Parses compiler output.
- `BuildErrorReport`: Generates error reports.

### 18.6 Usage Example

```python
# Parse compiler errors
parser = CompilerErrorParser("GCC")
errors = parser.parse_errors(compiler_stderr)

# Generate report
report = BuildErrorReport(errors)
print(report.generate_console_report())

# Save to file
report.save(Path("build_errors.txt"))
```

---

## 19. Cross-Platform Build Support

### 19.1 Platform Detection

Automatic platform detection and adaptation:

**Platforms Supported**:
- Windows (x86_64)
- Linux (x86_64, aarch64)
- macOS (x86_64, arm64)

### 19.2 Platform Information

Complete platform details:

```python
PlatformInfo:
    os_name: str
    architecture: str
    path_separator: str
    executable_extension: str
    shared_library_extension: str
    supports_symlinks: bool
```

### 19.3 Cross-Platform Paths

`CrossPlatformPath`: Handles path operations across platforms.

**Features**:
- Path normalization
- POSIX conversion
- Executable permissions
- Platform-appropriate separators


`PlatformToolchainAdapter`: Adds platform-specific compiler flags.

**Per-Platform Flags**:
- Windows: `/EHsc`, `/MD`
- macOS: `-mmacosx-version-min=10.13`
- Linux: `-fPIC`, `-pthread`

### 19.5 Implementation Classes

- `PlatformInfo`: Platform detection and metadata.
- `CrossPlatformPath`: Path utilities.
- `PlatformToolchainAdapter`: Compiler flag adaptation.
- `PlatformCompatibility`: Compatibility documentation.

### 19.6 Usage Example

```python
# Detect platform
platform_info = PlatformInfo.detect()
print(f"Platform: {platform_info.os_name}")

adapter = PlatformToolchainAdapter(platform_info)
flags = adapter.get_platform_specific_flags(['-O2'])

# Check compatibility
compatibility = PlatformCompatibility()
if compatibility.is_supported(platform_info):
    print("Platform is supported")
```

---

## 20. Module Integration & Final Documentation

### 20.1 Module Completion

Integration of all 19 previous prompts into a cohesive, production-ready build system.

### 20.2 Complete Build Pipeline

`CompleteBuildPipeline`: Orchestrates the full build process.

**Stages**:
1. Source Enumeration
2. Source Validation
3. Dependency Resolution
4. Native Compilation
5. Native Validation
6. Linking
7. Adapter Generation
8. Orchestration Assembly

### 20.3 Build Config

`BuildConfig`: Comprehensive configuration management.

**Features**:
- YAML file support
- Environment variable overrides
- Default values for all settings

### 20.4 Build Result

`BuildResult`: Detailed result object with performance profiles, error reports, and validation data.

### 20.5 Validation

`validate_module_integration()`: Verifies that all components are correctly integrated and functional.

### 20.6 Usage Example

```python
from modules.module_03_build_process.build_process import (
    CompleteBuildPipeline, BuildConfig
)

# Load configuration
config = BuildConfig.from_file("build.yaml")

# Execute build
pipeline = CompleteBuildPipeline(config)
result = pipeline.execute()

if result.success:
    print("Build successful!")
    print(f"Time: {result.performance_profile.total_build_time:.2f}s")
else:
    print("Build failed!")
    print(result.error_message)
```

---

**End of Module 03**  
**Status:** COMPLETE  
**Next Module:** Verification Execution
