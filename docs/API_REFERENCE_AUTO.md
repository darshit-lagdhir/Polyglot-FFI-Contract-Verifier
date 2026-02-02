# API Reference: modules.module_02_verification_pipeline.verification_pipeline

Polyglot FFI Contract Verifier - Module 02: Verification Pipeline
Complete implementation of the formal verification pipeline.

This module implements a deterministic, artifact-driven verification pipeline
that transforms implicit FFI assumptions into explicit, testable correctness claims.

Usage:
    python verification_pipeline.py run <execution_context.json>
    python verification_pipeline.py validate-stage <stage_name>
    
API:
    from verification_pipeline import VerificationPipeline, PipelineStage
    pipeline = VerificationPipeline(context)
    result = pipeline.execute_full()

## Functions

### `abstractmethod(funcobj)`

A decorator indicating abstract methods.

Requires that the metaclass is ABCMeta or derived from it.  A
class that has a metaclass derived from ABCMeta cannot be
instantiated unless all of its abstract methods are overridden.
The abstract methods can be called using any of the normal
'super' call mechanisms.  abstractmethod() may be used to declare
abstract methods for properties and descriptors.

Usage:

    class C(metaclass=ABCMeta):
        @abstractmethod
        def my_abstract_method(self, arg1, arg2, argN):
            ...

### `as_completed(fs, timeout=None)`

An iterator over the given futures that yields each as it completes.

Args:
    fs: The sequence of Futures (possibly created by different Executors) to
        iterate over.
    timeout: The maximum number of seconds to wait. If None, then there
        is no limit on the wait time.

Returns:
    An iterator that yields the given Futures as they complete (finished or
    cancelled). If any given Futures are duplicated, they will be returned
    once.

Raises:
    TimeoutError: If the entire result iterator could not be generated
        before the given timeout.

### `cli_main()`

Command-line interface for verification pipeline.

### `dataclass(cls=None, /, *, init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False, match_args=True, kw_only=False, slots=False, weakref_slot=False)`

Add dunder methods based on the fields defined in the class.

Examines PEP 526 __annotations__ to determine fields.

If init is true, an __init__() method is added to the class. If repr
is true, a __repr__() method is added. If order is true, rich
comparison dunder methods are added. If unsafe_hash is true, a
__hash__() method is added. If frozen is true, fields may not be
assigned to after instance creation. If match_args is true, the
__match_args__ tuple is added. If kw_only is true, then by default
all fields are keyword-only. If slots is true, a new class with a
__slots__ attribute is returned.

### `field(*, default=<dataclasses._MISSING_TYPE object at 0x0000022946F734D0>, default_factory=<dataclasses._MISSING_TYPE object at 0x0000022946F734D0>, init=True, repr=True, hash=None, compare=True, metadata=None, kw_only=<dataclasses._MISSING_TYPE object at 0x0000022946F734D0>)`

Return an object to identify dataclass fields.

default is the default value of the field.  default_factory is a
0-argument function called to initialize a field's value.  If init
is true, the field will be a parameter to the class's __init__()
function.  If repr is true, the field will be included in the
object's repr().  If hash is true, the field will be included in the
object's hash().  If compare is true, the field will be used in
comparison functions.  metadata, if specified, must be a mapping
which is stored but not otherwise examined by dataclass.  If kw_only
is true, the field will become a keyword-only parameter to
__init__().

It is an error to specify both default and default_factory.

### `initialize_libclang() -> bool`

Initialize libclang library.

Attempts to locate libclang.dll/so and configure clang.cindex.

Returns:
    True if initialization successful, False otherwise

### `verify(header_path: str, library_path: str, output_dir: str = 'artifacts', verbose: bool = True) -> modules.module_02_verification_pipeline.verification_pipeline.VerificationResult`

Complete FFI verification pipeline.

This is the main entry point for verification. It executes all stages
from native interface ingestion through diagnostics and reporting.

Args:
    header_path: Path to C header file
    library_path: Path to native library (.dll, .so, .dylib)
    output_dir: Directory for artifacts and reports
    verbose: Show progress messages
    
Returns:
    VerificationResult with summary and artifact paths
    
Example:
    >>> result = verify("interface.h", "library.dll")
    >>> if result.success:
    ...     print(f"Verification passed: {result.pass_rate}%")
    ... else:
    ...     print(f"Verification failed: {len(result.critical_issues)} critical issues")

### `verify_extensible(header_path: str, library_path: str, output_dir: str = 'artifacts', plugins: Optional[List[modules.module_02_verification_pipeline.verification_pipeline.PipelinePlugin]] = None, hooks: Optional[Dict[str, Callable]] = None, custom_rules: Optional[Dict] = None, **kwargs) -> modules.module_02_verification_pipeline.verification_pipeline.VerificationResult`

Extensible FFI verification with plugins and hooks.

Args:
    header_path: Path to C header
    library_path: Path to native library
    output_dir: Output directory
    plugins: List of plugins to register
    hooks: Dictionary of hook_point → function
    custom_rules: Dictionary of custom rules to register
    **kwargs: Additional options
    
Returns:
    VerificationResult
    
Example:
    >>> plugin = MyCustomPlugin()
    >>> result = verify_extensible(
    ...     "interface.h", "library.dll",
    ...     plugins=[plugin],
    ...     hooks={"post_contract_synthesis": my_hook}
    ... )

### `verify_optimized(header_path: str, library_path: str, output_dir: str = 'artifacts', verbose: bool = True, cache: bool = True, parallel: bool = False, max_workers: int = 4, profile: bool = False) -> modules.module_02_verification_pipeline.verification_pipeline.VerificationResult`

Optimized FFI verification with caching and parallel execution.

Args:
    header_path: Path to C header
    library_path: Path to native library
    output_dir: Output directory
    verbose: Show progress
    cache: Enable artifact caching
    parallel: Enable parallel stage execution
    max_workers: Maximum parallel workers
    profile: Enable performance profiling
    
Returns:
    VerificationResult
    
Example:
    >>> result = verify_optimized(
    ...     "interface.h", "library.dll",
    ...     cache=True, parallel=True, max_workers=8
    ... )

## Classes

## class `AdapterGenerationStage`

Stage 4: Adapter Generation

Generates runtime enforcement adapters from contracts.
Produces Python ctypes wrappers with pre/post checks.

#### `AdapterGenerationStage.create_provenance()`

Create provenance metadata for an output artifact.

Args:
    input_artifacts: List of input artifact paths
    
Returns:
    ArtifactProvenance object to embed in output artifact

#### `AdapterGenerationStage.execute()`

Execute stage transformation.

This is the main entry point for stage execution. It:
1. Validates preconditions
2. Transitions to EXECUTING state
3. Calls _execute_impl (implemented by subclass)
4. Validates postconditions
5. Transitions to COMPLETED or FAILED state

Raises:
    PreconditionError: If preconditions aren't satisfied
    StageError: If execution fails
    PostconditionError: If postconditions aren't satisfied

#### `AdapterGenerationStage.get_execution_summary()`

Get summary of stage execution for logging.

Returns:
    Dictionary with stage name, state, timestamps, error (if any)

#### `AdapterGenerationStage.validate_postconditions()`

Validate that all required output artifacts were produced and are valid.

This enforces the architectural law: "No stage produces artifacts
without ensuring they satisfy their schema."

Raises:
    PostconditionError: If required outputs are missing or invalid

#### `AdapterGenerationStage.validate_preconditions()`

Validate that all required input artifacts exist and are valid.

This method enforces the architectural law: "No stage executes until
all preconditions are satisfied."

Raises:
    PreconditionError: If required artifacts are missing or invalid

## class `AdapterGenerator`

Generates complete adapter module from contract.

#### `AdapterGenerator.generate_adapter_module()`

Generate complete adapter module code.

## class `ArtifactProvenance`

Provenance metadata embedded in every artifact.

This metadata enables complete traceability from outputs back to inputs
and execution context.

#### `ArtifactProvenance.to_dict()`

Serialize to dictionary for embedding in artifacts.

## class `ArtifactSchema`

Complete schema definition for an artifact type.

Defines structure, validation rules, and versioning for artifacts.

#### `ArtifactSchema.validate()`

Validate artifact data against schema.

Args:
    artifact_data: Parsed artifact to validate
    
Returns:
    List of validation error messages (empty if valid)

## class `ArtifactType`

Enumeration of all artifact types in the pipeline.

## class `ArtifactValidator`

Validates artifacts against their schemas and checks provenance metadata.

All artifacts must pass validation before being used as inputs to stages.
This enforces the architectural law: "No stage may read artifacts without
validating them first."

#### `ArtifactValidator.compute_artifact_hash()`

Compute SHA-256 hash of artifact file.

Used for provenance tracking and change detection.

#### `ArtifactValidator.validate_artifact()`

Validate artifact exists, is readable, has valid JSON, and contains
required provenance metadata.

Args:
    artifact_path: Path to artifact file
    expected_schema_version: Optional schema version to enforce
    
Returns:
    Parsed artifact as dictionary
    
Raises:
    ConfigError: If artifact doesn't exist or isn't readable
    PostconditionError: If artifact is invalid

## class `CacheManager`

Manages artifact caching for performance optimization.

Caches expensive stage outputs and reuses them when inputs unchanged.

#### `CacheManager.clear_all()`

Clear entire cache.

#### `CacheManager.compute_cache_key()`

Compute deterministic cache key from inputs.

Args:
    inputs: Dictionary of input artifacts
    
Returns:
    SHA-256 hash as hex string

#### `CacheManager.get_stats()`

Get cache statistics.

#### `CacheManager.invalidate_stage()`

Invalidate all cache entries for a stage.

#### `CacheManager.lookup()`

Look up cached outputs for stage and inputs.

Args:
    stage_name: Stage name
    stage_version: Stage version
    inputs: Input artifacts
    
Returns:
    Dictionary of output artifacts if cache hit, None if miss

#### `CacheManager.store()`

Store stage outputs in cache.

Args:
    stage_name: Stage name
    stage_version: Stage version
    inputs: Input artifacts
    outputs: Output artifacts

## class `CheckGenerator`

Generates runtime check code from constraints.

#### `CheckGenerator.generate_check_function()`

Generate check function for a constraint.

Returns Python code as string.

## class `CodeGenerator`

Utility for generating Python code with proper indentation.

#### `CodeGenerator.add_block()`

Add a block with header and indented content.

#### `CodeGenerator.add_line()`

Add a line with current indentation.

#### `CodeGenerator.dedent()`

Decrease indentation level.

#### `CodeGenerator.get_code()`

Get generated code as string.

#### `CodeGenerator.indent()`

Increase indentation level.

## class `CompletePipeline`

Complete integrated verification pipeline.

Orchestrates all 7 stages from header/library to final report.

#### `CompletePipeline.execute()`

Execute complete verification pipeline.

Args:
    verbose: Show progress messages
    
Returns:
    VerificationResult with summary and paths

## class `ConfigError`

Invalid user configuration or inputs.
Examples: missing files, unsupported platform, invalid arguments.

## class `Constraint`

A single constraint on an FFI interface element.

Represents an assumption that must hold for correct behavior.

#### `Constraint.to_dict()`

Serialize to dictionary.

## class `ConstraintSynthesizer`

Synthesizes constraints from IR using derivation rules.

Applies heuristics and naming analysis to infer semantic properties.

#### `ConstraintSynthesizer.synthesize_function_constraints()`

Synthesize constraints for a single function.

Args:
    function: Normalized function from IR
    
Returns:
    List of constraints

## class `ConstraintType`

Types of constraints that can be synthesized.

## class `ContractSynthesisStage`

Stage 3: Contract Synthesis

Transforms structural IR into semantic correctness constraints.
Infers nullability, buffer sizes, ownership, and other properties.

#### `ContractSynthesisStage.create_provenance()`

Create provenance metadata for an output artifact.

Args:
    input_artifacts: List of input artifact paths
    
Returns:
    ArtifactProvenance object to embed in output artifact

#### `ContractSynthesisStage.execute()`

Execute stage transformation.

This is the main entry point for stage execution. It:
1. Validates preconditions
2. Transitions to EXECUTING state
3. Calls _execute_impl (implemented by subclass)
4. Validates postconditions
5. Transitions to COMPLETED or FAILED state

Raises:
    PreconditionError: If preconditions aren't satisfied
    StageError: If execution fails
    PostconditionError: If postconditions aren't satisfied

#### `ContractSynthesisStage.get_execution_summary()`

Get summary of stage execution for logging.

Returns:
    Dictionary with stage name, state, timestamps, error (if any)

#### `ContractSynthesisStage.validate_postconditions()`

Validate that all required output artifacts were produced and are valid.

This enforces the architectural law: "No stage produces artifacts
without ensuring they satisfy their schema."

Raises:
    PostconditionError: If required outputs are missing or invalid

#### `ContractSynthesisStage.validate_preconditions()`

Validate that all required input artifacts exist and are valid.

This method enforces the architectural law: "No stage executes until
all preconditions are satisfied."

Raises:
    PreconditionError: If required artifacts are missing or invalid

## class `CoverageAnalyzer`

Analyzes test plan for constraint coverage.

Ensures all constraints are exercised by at least one test.

#### `CoverageAnalyzer.analyze_coverage()`

Analyze constraint coverage.

Returns coverage report.

## class `CustomConstraint`

Base class for custom user-defined constraints.

Users extend this to create domain-specific constraint types.

#### `CustomConstraint.generate_check_code()`

Generate Python code for runtime check.

Returns:
    Python code as string

#### `CustomConstraint.to_dict()`

Serialize to dictionary.

#### `CustomConstraint.validate()`

Validate value against constraint.

Args:
    value: Value to validate
    
Returns:
    True if valid, False otherwise

## class `DependencyGraph`

Simple dependency graph for stage ordering.

## class `DiagnosticsReportingStage`

Stage 7: Diagnostics & Reporting

Analyzes execution results, classifies failures, generates root cause
analysis, and produces human-readable reports.

#### `DiagnosticsReportingStage.create_provenance()`

Create provenance metadata for an output artifact.

Args:
    input_artifacts: List of input artifact paths
    
Returns:
    ArtifactProvenance object to embed in output artifact

#### `DiagnosticsReportingStage.execute()`

Execute stage transformation.

This is the main entry point for stage execution. It:
1. Validates preconditions
2. Transitions to EXECUTING state
3. Calls _execute_impl (implemented by subclass)
4. Validates postconditions
5. Transitions to COMPLETED or FAILED state

Raises:
    PreconditionError: If preconditions aren't satisfied
    StageError: If execution fails
    PostconditionError: If postconditions aren't satisfied

#### `DiagnosticsReportingStage.get_execution_summary()`

Get summary of stage execution for logging.

Returns:
    Dictionary with stage name, state, timestamps, error (if any)

#### `DiagnosticsReportingStage.validate_postconditions()`

Validate that all required output artifacts were produced and are valid.

This enforces the architectural law: "No stage produces artifacts
without ensuring they satisfy their schema."

Raises:
    PostconditionError: If required outputs are missing or invalid

#### `DiagnosticsReportingStage.validate_preconditions()`

Validate that all required input artifacts exist and are valid.

This method enforces the architectural law: "No stage executes until
all preconditions are satisfied."

Raises:
    PreconditionError: If required artifacts are missing or invalid

## class `EnhancedArtifactValidator`

Advanced artifact validation with schema checking, hash verification,
and provenance validation.

#### `EnhancedArtifactValidator.validate_artifact()`

Comprehensive artifact validation.

Args:
    artifact_path: Path to artifact
    expected_schema_version: Expected schema version (if any)
    verify_hashes: Whether to verify input artifact hashes
    
Returns:
    Parsed and validated artifact
    
Raises:
    ConfigError: If artifact doesn't exist
    PostconditionError: If artifact is invalid

## class `EnhancedVerificationPipeline`

Enhanced pipeline orchestrator with advanced state management,
dependency resolution, and error recovery.

#### `EnhancedVerificationPipeline.execute_full_pipeline()`

Execute all registered stages in order.

Returns:
    True if all stages completed successfully, False otherwise

#### `EnhancedVerificationPipeline.execute_full_pipeline_with_dependency_resolution()`

Execute pipeline with automatic dependency resolution.

Stages are executed in topological order based on their dependencies.

Returns:
    True if all stages completed successfully

#### `EnhancedVerificationPipeline.execute_stage()`

Execute a single stage by name.

Args:
    stage_name: Name of stage to execute
    
Returns:
    True if stage completed successfully, False otherwise

#### `EnhancedVerificationPipeline.list_stages()`

Print list of registered stages.

#### `EnhancedVerificationPipeline.register_stage()`

Register a stage for execution.

Args:
    stage_class: Subclass of PipelineStage

## class `ExecutionSummarizer`

Generates summary statistics from test results.

#### `ExecutionSummarizer.summarize()`

Generate summary statistics.

Args:
    test_results: List of test result dictionaries
    
Returns:
    Summary dictionary

## class `ExtensiblePipeline`

Pipeline with plugin and hook support.

#### `ExtensiblePipeline.execute()`

Execute with hooks.

#### `ExtensiblePipeline.register_custom_rule()`

Register custom rule.

#### `ExtensiblePipeline.register_hook()`

Register hook function.

#### `ExtensiblePipeline.register_plugin()`

Register plugin.

## class `FailureCategory`

Categories of verification failures.

## class `FailureClassifier`

Classifies test failures into categories and assigns severity.

#### `FailureClassifier.classify()`

Classify a failed test.

Args:
    test_result: Test execution result
    test_case: Original test case specification
    
Returns:
    Classification dict with category, severity, root_cause

## class `FieldSchema`

Schema definition for a single field in an artifact.

## class `HTMLReportGenerator`

Generates rich HTML report from execution results.

#### `HTMLReportGenerator.generate()`

Generate HTML report.

## class `HookContext`

Context passed to hook functions.

## class `HookManager`

Manages hook registration and execution.

#### `HookManager.execute()`

Execute all hooks for a hook point.

Args:
    hook_point: Hook point identifier
    context: Hook execution context
    **kwargs: Hook-specific arguments

#### `HookManager.list_hooks()`

List registered hooks.

Args:
    hook_point: Specific hook point or None for all
    
Returns:
    Dictionary of hook_point → count

#### `HookManager.register()`

Register hook function.

Args:
    hook_point: Hook point identifier (from HookPoints)
    func: Hook function

## class `HookPoints`

Enumeration of available hook points.

## class `IRNormalizationStage`

Stage 2: IR Normalization

Transforms raw native interface into canonical intermediate representation
with typedef resolution, type registry, and normalized structures.

#### `IRNormalizationStage.create_provenance()`

Create provenance metadata for an output artifact.

Args:
    input_artifacts: List of input artifact paths
    
Returns:
    ArtifactProvenance object to embed in output artifact

#### `IRNormalizationStage.execute()`

Execute stage transformation.

This is the main entry point for stage execution. It:
1. Validates preconditions
2. Transitions to EXECUTING state
3. Calls _execute_impl (implemented by subclass)
4. Validates postconditions
5. Transitions to COMPLETED or FAILED state

Raises:
    PreconditionError: If preconditions aren't satisfied
    StageError: If execution fails
    PostconditionError: If postconditions aren't satisfied

#### `IRNormalizationStage.get_execution_summary()`

Get summary of stage execution for logging.

Returns:
    Dictionary with stage name, state, timestamps, error (if any)

#### `IRNormalizationStage.validate_postconditions()`

Validate that all required output artifacts were produced and are valid.

This enforces the architectural law: "No stage produces artifacts
without ensuring they satisfy their schema."

Raises:
    PostconditionError: If required outputs are missing or invalid

#### `IRNormalizationStage.validate_preconditions()`

Validate that all required input artifacts exist and are valid.

This method enforces the architectural law: "No stage executes until
all preconditions are satisfied."

Raises:
    PreconditionError: If required artifacts are missing or invalid

## class `IncrementalPipelineExecutor`

Executes pipeline incrementally, reusing fresh artifacts.

Only re-runs stages whose outputs are stale or missing.

#### `IncrementalPipelineExecutor.execute_incremental()`

Execute pipeline incrementally.

Args:
    target_artifact: Target artifact to produce (None = all artifacts)
    
Returns:
    True if execution successful

## class `InputInstantiator`

Converts abstract input specifications to concrete Python values.

Handles type conversions, null values, and special cases.

#### `InputInstantiator.instantiate()`

Convert input specification to actual value.

Args:
    input_spec: Input specification from test plan
    
Returns:
    Concrete Python value

#### `InputInstantiator.instantiate_all()`

Instantiate all inputs for a test case.

Args:
    inputs: Dictionary of parameter_name -> input_spec
    
Returns:
    Dictionary of parameter_name -> actual_value

## class `InputValueGenerator`

Generates deterministic input values for test cases.

Provides valid, invalid, and boundary values for various types.

#### `InputValueGenerator.generate_boundary_int()`

Generate boundary integer values.

#### `InputValueGenerator.generate_invalid_buffer()`

Generate invalid buffer values.

#### `InputValueGenerator.generate_invalid_int()`

Generate out-of-range integer values.

#### `InputValueGenerator.generate_non_null_terminated_string()`

Generate strings missing null terminator.

#### `InputValueGenerator.generate_null_terminated_string()`

Generate null-terminated strings.

#### `InputValueGenerator.generate_valid_buffer()`

Generate valid buffer test values.

#### `InputValueGenerator.generate_valid_int()`

Generate valid integer test values.

## class `InvalidStateTransitionError`

Raised when an invalid stage state transition is attempted.

State transitions must follow strict rules defined by the state machine.

## class `MarkdownReportGenerator`

Generates Markdown report for version control.

#### `MarkdownReportGenerator.generate()`

Generate Markdown report.

## class `NamingPatternAnalyzer`

Analyzes naming patterns to infer semantic properties.

Uses heuristics based on common C naming conventions.

#### `NamingPatternAnalyzer.suggests_buffer_parameter()`

Check if name suggests parameter is a buffer.

#### `NamingPatternAnalyzer.suggests_nullable()`

Check if name suggests pointer may be null.

#### `NamingPatternAnalyzer.suggests_ownership_transfer_in()`

Check if name suggests function destroys/frees resource.

#### `NamingPatternAnalyzer.suggests_ownership_transfer_out()`

Check if name suggests function creates/allocates resource.

#### `NamingPatternAnalyzer.suggests_size_parameter()`

Check if name suggests parameter is a size/length.

## class `NativeInterfaceIngestionStage`

Stage 1: Native Interface Ingestion

Extracts compiler-grade ABI information from C headers using libclang.
This is a lossless extraction - all ABI-relevant details are preserved.

#### `NativeInterfaceIngestionStage.create_provenance()`

Create provenance metadata for an output artifact.

Args:
    input_artifacts: List of input artifact paths
    
Returns:
    ArtifactProvenance object to embed in output artifact

#### `NativeInterfaceIngestionStage.execute()`

Execute stage transformation.

This is the main entry point for stage execution. It:
1. Validates preconditions
2. Transitions to EXECUTING state
3. Calls _execute_impl (implemented by subclass)
4. Validates postconditions
5. Transitions to COMPLETED or FAILED state

Raises:
    PreconditionError: If preconditions aren't satisfied
    StageError: If execution fails
    PostconditionError: If postconditions aren't satisfied

#### `NativeInterfaceIngestionStage.get_execution_summary()`

Get summary of stage execution for logging.

Returns:
    Dictionary with stage name, state, timestamps, error (if any)

#### `NativeInterfaceIngestionStage.validate_postconditions()`

Validate that all required output artifacts were produced and are valid.

This enforces the architectural law: "No stage produces artifacts
without ensuring they satisfy their schema."

Raises:
    PostconditionError: If required outputs are missing or invalid

#### `NativeInterfaceIngestionStage.validate_preconditions()`

Validate that all required input artifacts exist and are valid.

This method enforces the architectural law: "No stage executes until
all preconditions are satisfied."

Raises:
    PreconditionError: If required artifacts are missing or invalid

## class `OptimizedCompletePipeline`

Enhanced pipeline with caching, parallel execution, and profiling.

#### `OptimizedCompletePipeline.execute()`

Execute with optimizations.

## class `OutcomeValidator`

Validates actual outcomes against expected outcomes.

Determines if test passes or fails.

#### `OutcomeValidator.validate()`

Compare expected and actual outcomes.

Args:
    expected: Expected outcome from test plan
    actual: Actual outcome from execution
    
Returns:
    Tuple of (validation_result, failure_reason)
    validation_result is "PASS" or "FAIL"
    failure_reason is None if PASS, string if FAIL

## class `ParallelPipelineExecutor`

Executes independent pipeline stages in parallel.

Uses level-based parallelism based on dependency graph.

#### `ParallelPipelineExecutor.execute_parallel()`

Execute pipeline with parallel stage execution.

Returns:
    True if all stages completed successfully

## class `PerformanceProfiler`

Profiles pipeline execution for performance analysis.

#### `PerformanceProfiler.generate_report()`

Generate performance report.

#### `PerformanceProfiler.profile_stage()`

Profile stage execution.

Args:
    stage_name: Stage name
    execution_func: Function to execute
    
Returns:
    Execution result

## class `PipelineError`

Base class for all pipeline errors.

## class `PipelineExecutionLog`

Records all pipeline execution events.

The execution log is append-only and immutable. It captures:
- Which stages executed
- State transitions
- Errors and warnings
- Produced artifacts
- Timing information

#### `PipelineExecutionLog.log_pipeline_complete()`

Log that pipeline execution completed.

#### `PipelineExecutionLog.log_pipeline_start()`

Log that pipeline execution started.

#### `PipelineExecutionLog.log_stage_complete()`

Log that a stage completed successfully.

#### `PipelineExecutionLog.log_stage_failed()`

Log that a stage failed.

#### `PipelineExecutionLog.log_stage_start()`

Log that a stage started executing.

#### `PipelineExecutionLog.save()`

Save execution log to file.

## class `PipelinePlugin`

Base class for pipeline plugins.

Plugins extend pipeline with custom stages, rules, and hooks.

#### `PipelinePlugin.get_hooks()`

Get hook functions.

Returns:
    Dictionary of hook_point → function

#### `PipelinePlugin.initialize()`

Initialize plugin with pipeline.

Args:
    pipeline: Pipeline instance

#### `PipelinePlugin.register_rules()`

Register custom constraint rules.

Args:
    registry: Rule registry

#### `PipelinePlugin.register_stages()`

Register custom stages.

Args:
    registry: Stage registry

## class `PipelineStage`

Abstract base class for all pipeline stages.

Each stage is a correctness boundary with explicit preconditions,
postconditions, and invariants. Stages must implement:
- Precondition checking (required inputs exist and are valid)
- Execution logic (transformation from inputs to outputs)
- Postcondition checking (outputs satisfy requirements)

The stage lifecycle is:
1. __init__: Stage created in PENDING state
2. validate_preconditions: Check inputs → READY or raise PreconditionError
3. execute: Perform transformation → COMPLETED or raise StageError
4. validate_postconditions: Check outputs → success or raise PostconditionError

#### `PipelineStage.create_provenance()`

Create provenance metadata for an output artifact.

Args:
    input_artifacts: List of input artifact paths
    
Returns:
    ArtifactProvenance object to embed in output artifact

#### `PipelineStage.execute()`

Execute stage transformation.

This is the main entry point for stage execution. It:
1. Validates preconditions
2. Transitions to EXECUTING state
3. Calls _execute_impl (implemented by subclass)
4. Validates postconditions
5. Transitions to COMPLETED or FAILED state

Raises:
    PreconditionError: If preconditions aren't satisfied
    StageError: If execution fails
    PostconditionError: If postconditions aren't satisfied

#### `PipelineStage.get_execution_summary()`

Get summary of stage execution for logging.

Returns:
    Dictionary with stage name, state, timestamps, error (if any)

#### `PipelineStage.validate_postconditions()`

Validate that all required output artifacts were produced and are valid.

This enforces the architectural law: "No stage produces artifacts
without ensuring they satisfy their schema."

Raises:
    PostconditionError: If required outputs are missing or invalid

#### `PipelineStage.validate_preconditions()`

Validate that all required input artifacts exist and are valid.

This method enforces the architectural law: "No stage executes until
all preconditions are satisfied."

Raises:
    PreconditionError: If required artifacts are missing or invalid

## class `PluginManager`

Manages plugin registration and lifecycle.

#### `PluginManager.list_plugins()`

List registered plugins.

#### `PluginManager.register_plugin()`

Register plugin.

Args:
    plugin: Plugin instance

## class `PostconditionError`

Stage completed but produced invalid artifacts.
This indicates a bug in the stage implementation.

## class `PreconditionError`

Required input artifacts missing or invalid.
Examples: stage requires IR artifact but it doesn't exist.

## class `ProvenanceChainValidator`

Validates provenance chains across multiple artifacts.

Ensures artifacts form valid lineage with consistent execution context
and unbroken hash chains.

#### `ProvenanceChainValidator.validate_chain()`

Validate provenance chain across multiple artifacts.

Args:
    artifact_paths: List of artifact paths to validate
    
Returns:
    List of validation error messages (empty if valid)

## class `RemediationGenerator`

Generates actionable remediation recommendations for failures.

#### `RemediationGenerator.generate()`

Generate remediation steps.

Args:
    classification: Failure classification
    test_result: Test execution result
    test_case: Original test case
    
Returns:
    List of recommended actions

## class `RuleRegistry`

Registry of custom constraint rules.

Manages user-defined rules and their synthesis heuristics.

#### `RuleRegistry.get_applicable_rules()`

Get rules applicable to given context.

Args:
    context: Context (parameter, function, etc.)
    
Returns:
    List of applicable rule infos, sorted by priority

#### `RuleRegistry.list_rules()`

List all registered rule IDs.

#### `RuleRegistry.register()`

Register custom rule.

Args:
    rule_id: Unique rule identifier
    constraint_class: CustomConstraint subclass
    synthesis_heuristic: Function to determine if rule applies
    priority: Rule priority (higher = applied first)

## class `RuleTemplates`

Collection of reusable constraint templates.

Provides common constraint patterns that users can apply.

#### `RuleTemplates.buffer_with_length()`

Template: Buffer with explicit length parameter.

#### `RuleTemplates.output_parameter()`

Template: Output parameter (pointer-to-pointer).

#### `RuleTemplates.pointer_not_null()`

Template: Pointer must not be null.

## class `SchemaRegistry`

Registry of all artifact schemas.

Provides schema lookup, validation, and versioning support.

#### `SchemaRegistry.get_latest_schema()`

Get latest schema version for artifact type.

#### `SchemaRegistry.get_schema()`

Get schema for specific artifact type and version.

#### `SchemaRegistry.register_schema()`

Register an artifact schema.

## class `SchemaVersionValidator`

Validates artifact schema versions for compatibility.

#### `SchemaVersionValidator.validate_compatibility()`

Validate that artifact schema version is compatible with required version.

Args:
    artifact_path: Path to artifact (for error messages)
    artifact_version: Actual schema version in artifact
    required_version: Required schema version
    
Raises:
    PostconditionError: If versions are incompatible

## class `SemanticVersion`

Semantic version (MAJOR.MINOR.PATCH).

#### `SemanticVersion.is_compatible_with()`

Check if this version is compatible with a required version.

Compatibility rules (semantic versioning):
- Major version must match (breaking changes)
- Minor version must be >= required (backward compatible additions)
- Patch version irrelevant (bug fixes always compatible)

Args:
    required: Required version
    
Returns:
    True if compatible, False otherwise

## class `Severity`

Failure severity levels.

## class `StageError`

Error during stage execution.
Examples: parse failures, validation errors, runtime exceptions.

## class `StageRegistry`

Registry of available pipeline stages.

The registry maintains a mapping from stage names to stage classes
and validates stage definitions.

#### `StageRegistry.get_stage_class()`

Get stage class by name.

Args:
    stage_name: Name of stage
    
Returns:
    Stage class
    
Raises:
    KeyError: If stage not registered

#### `StageRegistry.get_stage_info()`

Get information about a registered stage.

Args:
    stage_name: Name of stage
    
Returns:
    Dictionary with stage metadata

#### `StageRegistry.list_stages()`

Get list of registered stage names.

#### `StageRegistry.register_stage()`

Register a stage class.

Args:
    stage_class: Subclass of PipelineStage
    
Raises:
    ValueError: If stage class is invalid

## class `StageState`

Enumeration of valid pipeline stage states.

State transitions are strictly controlled:
PENDING → READY → EXECUTING → COMPLETED
                             → FAILED
                 → SKIPPED

## class `StalenessDetector`

Detects stale artifacts for incremental verification.

An artifact is stale if its inputs have changed or the stage that
produced it has been updated.

#### `StalenessDetector.check_staleness()`

Check if artifact is stale.

Args:
    artifact_path: Path to artifact
    stage_class: Stage class that produces this artifact
    
Returns:
    Staleness status

#### `StalenessDetector.set_current_execution_context()`

Set current execution context for staleness checking.

## class `StalenessStatus`

Artifact freshness status.

## class `StateMachineValidator`

Validates stage state transitions according to formal state machine rules.

This enforces the architectural invariant that state transitions are
explicit, validated, and follow a deterministic pattern.

## class `StructLayoutExtractor`

Extracts struct layouts with explicit padding detection.

Computes implicit padding fields by comparing field offsets.

#### `StructLayoutExtractor.extract_layout()`

Extract complete struct layout including padding.

Args:
    cursor: clang.cindex.IDE for struct
    
Returns:
    Dictionary with struct layout information

## class `TestCaseGenerator`

Generates test cases from contract constraints.

Creates positive, negative, boundary, and combinatorial tests.

#### `TestCaseGenerator.generate_test_cases_for_function()`

Generate all test cases for a function.

Returns list of test case specifications.

## class `TestExecutor`

Executes individual test cases using generated adapters.

Handles input instantiation, adapter invocation, outcome capture,
and validation.

#### `TestExecutor.execute_test()`

Execute a single test case.

Args:
    test_case: Test case specification from test plan
    
Returns:
    Test result dictionary

## class `TestPlanGenerationStage`

Stage 5: Test Plan Generation

Generates systematic test cases from contracts to achieve
100% constraint coverage with deterministic inputs.

#### `TestPlanGenerationStage.create_provenance()`

Create provenance metadata for an output artifact.

Args:
    input_artifacts: List of input artifact paths
    
Returns:
    ArtifactProvenance object to embed in output artifact

#### `TestPlanGenerationStage.execute()`

Execute stage transformation.

This is the main entry point for stage execution. It:
1. Validates preconditions
2. Transitions to EXECUTING state
3. Calls _execute_impl (implemented by subclass)
4. Validates postconditions
5. Transitions to COMPLETED or FAILED state

Raises:
    PreconditionError: If preconditions aren't satisfied
    StageError: If execution fails
    PostconditionError: If postconditions aren't satisfied

#### `TestPlanGenerationStage.get_execution_summary()`

Get summary of stage execution for logging.

Returns:
    Dictionary with stage name, state, timestamps, error (if any)

#### `TestPlanGenerationStage.validate_postconditions()`

Validate that all required output artifacts were produced and are valid.

This enforces the architectural law: "No stage produces artifacts
without ensuring they satisfy their schema."

Raises:
    PostconditionError: If required outputs are missing or invalid

#### `TestPlanGenerationStage.validate_preconditions()`

Validate that all required input artifacts exist and are valid.

This method enforces the architectural law: "No stage executes until
all preconditions are satisfied."

Raises:
    PreconditionError: If required artifacts are missing or invalid

## class `TypeExtractor`

Extracts complete type information from libclang type objects.

Handles recursive type structures (pointers to arrays to structs, etc.)

#### `TypeExtractor.extract_type()`

Extract complete type information from clang type.

Args:
    clang_type: clang.cindex.Type object
    
Returns:
    Dictionary with type information

## class `TypeIDGenerator`

Generates stable, unique type IDs from type structures.

Type IDs are deterministic and human-readable for debugging.

#### `TypeIDGenerator.generate()`

Generate type ID from type structure.

Args:
    type_info: Type information dictionary
    
Returns:
    Unique type ID string

## class `TypeMapper`

Maps IR types to ctypes types.

#### `TypeMapper.map_type()`

Map IR type to ctypes type string.

Args:
    type_id: Type ID from IR
    type_registry: Type registry from IR
    
Returns:
    Python code string for ctypes type

## class `TypeNormalizer`

Normalizes types from native interface to canonical IR form.

Handles:
- Typedef resolution
- Type registration
- Qualifier normalization
- Recursive type processing

#### `TypeNormalizer.normalize_type()`

Normalize type and return its type ID.

Args:
    native_type: Type from native interface
    resolve_typedefs: Whether to resolve typedefs to underlying types
    
Returns:
    Type ID in registry

## class `TypeRegistry`

Registry of all types with bidirectional lookup.

Maintains:
- type_id → type_info (forward lookup)
- type_structure → type_id (reverse lookup for deduplication)

#### `TypeRegistry.get_all_types()`

Get all registered types.

#### `TypeRegistry.get_type()`

Get type information by ID.

#### `TypeRegistry.has_type()`

Check if type ID is registered.

#### `TypeRegistry.register_type()`

Register a type and return its ID.

If type already registered, returns existing ID.

Args:
    type_info: Type information dictionary
    
Returns:
    Type ID

## class `TypedefResolver`

Resolves typedef chains to underlying canonical types.

Handles:
- Transitive typedef resolution
- Circular typedef detection
- Preservation of typedef info for diagnostics

#### `TypedefResolver.register_typedef()`

Register a typedef for later resolution.

#### `TypedefResolver.resolve()`

Resolve typedef to underlying canonical type.

Args:
    type_info: Type that may be a typedef
    
Returns:
    Resolved canonical type (not a typedef)
    
Raises:
    StageError: If circular typedef detected

## class `VerificationExecutionStage`

Stage 6: Verification Execution

Executes test plan using generated adapters, validates outcomes,
and produces comprehensive execution log.

#### `VerificationExecutionStage.create_provenance()`

Create provenance metadata for an output artifact.

Args:
    input_artifacts: List of input artifact paths
    
Returns:
    ArtifactProvenance object to embed in output artifact

#### `VerificationExecutionStage.execute()`

Execute stage transformation.

This is the main entry point for stage execution. It:
1. Validates preconditions
2. Transitions to EXECUTING state
3. Calls _execute_impl (implemented by subclass)
4. Validates postconditions
5. Transitions to COMPLETED or FAILED state

Raises:
    PreconditionError: If preconditions aren't satisfied
    StageError: If execution fails
    PostconditionError: If postconditions aren't satisfied

#### `VerificationExecutionStage.get_execution_summary()`

Get summary of stage execution for logging.

Returns:
    Dictionary with stage name, state, timestamps, error (if any)

#### `VerificationExecutionStage.validate_postconditions()`

Validate that all required output artifacts were produced and are valid.

This enforces the architectural law: "No stage produces artifacts
without ensuring they satisfy their schema."

Raises:
    PostconditionError: If required outputs are missing or invalid

#### `VerificationExecutionStage.validate_preconditions()`

Validate that all required input artifacts exist and are valid.

This method enforces the architectural law: "No stage executes until
all preconditions are satisfied."

Raises:
    PreconditionError: If required artifacts are missing or invalid

## class `VerificationPipeline`

Main pipeline orchestrator.

Responsibilities:
- Load and validate execution context
- Register and instantiate stages
- Execute stages in correct order
- Enforce preconditions and postconditions
- Handle errors according to classification
- Produce pipeline execution log

The pipeline enforces all architectural laws:
- No stage executes until preconditions are satisfied
- No stage reads unvalidated artifacts
- No validation steps are skipped
- All failures are classified and reported

#### `VerificationPipeline.execute_full_pipeline()`

Execute all registered stages in order.

Returns:
    True if all stages completed successfully, False otherwise

#### `VerificationPipeline.execute_stage()`

Execute a single stage by name.

Args:
    stage_name: Name of stage to execute
    
Returns:
    True if stage completed successfully, False otherwise

#### `VerificationPipeline.list_stages()`

Print list of registered stages.

#### `VerificationPipeline.register_stage()`

Register a stage for execution.

Args:
    stage_class: Subclass of PipelineStage

## class `VerificationResult`

Result of complete verification pipeline execution.

Contains summary statistics, paths to artifacts, and any errors.

