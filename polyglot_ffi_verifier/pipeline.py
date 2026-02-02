"""
Orchestration Layer Module

This module implements the orchestration layer responsible for sequencing
pipeline stages, managing configuration, coordinating artifact flow, and
handling the overall verification workflow.

The orchestration layer does NOT perform analysis, synthesis, or verification
logic itself. Its sole responsibility is lifecycle management.
"""

import argparse
import os
import sys
import json
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import importlib

from .context import ExecutionContext, ExecutionContextBuilder
# Updated imports from consolidated modules
from .ingestion import NativeInterfaceAnalyzer
from .normalization import IRNormalizer
from .synthesis import ContractSynthesizer
from .versioning import ContractSchemaValidator, ContractComparator, CompatibilityReportGenerator
from .adapters import AdapterGenerator
from .test_planning import TestPlanGenerator
from .execution import VerificationExecutor
from .diagnosis import DiagnosticMapper
from .reporting import ReportGenerator


class ErrorType(Enum):
    """Classification of error types for proper handling."""
    CONFIGURATION_ERROR = "configuration"
    TOOLING_ERROR = "tooling"
    PRECONDITION_ERROR = "precondition"
    STAGE_ERROR = "stage"


class PipelineStage(Enum):
    """Pipeline stages in execution order."""
    INGEST = "ingest"
    SYNTHESIZE = "synthesize"
    GENERATE_ADAPTERS = "generate-adapters"
    GENERATE_TESTS = "generate-tests"
    EXECUTE = "execute"
    DIAGNOSE = "diagnose"
    REPORT = "report"
    VALIDATE_SCHEMA = "validate-schema"
    COMPARE_CONTRACTS = "compare-contracts"


class VerificationError(Exception):
    """Base exception for verification errors with type classification."""
    
    def __init__(self, message: str, error_type: ErrorType):
        super().__init__(message)
        self.error_type = error_type


class ConfigurationError(VerificationError):
    """Configuration-related errors."""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorType.CONFIGURATION_ERROR)


class ToolingError(VerificationError):
    """Tooling-related errors (compiler, library, runtime not found)."""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorType.TOOLING_ERROR)


class PreconditionError(VerificationError):
    """Precondition errors (missing required artifacts)."""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorType.PRECONDITION_ERROR)


class StageError(VerificationError):
    """Stage-specific execution errors."""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorType.STAGE_ERROR)


class Pipeline:
    """
    Orchestrates execution of verification pipeline stages.
    
    Responsibilities:
    - Sequence pipeline stages in correct order
    - Validate preconditions before each stage
    - Coordinate artifact flow between stages
    - Handle failures at appropriate abstraction level
    - Support partial execution of individual stages
    """
    
    def __init__(self, context: ExecutionContext):
        """
        Initialize orchestrator with execution context.
        
        Args:
            context: Immutable execution context
        """
        self.context = context
        self._stage_registry: Dict[PipelineStage, Callable] = {}
        self._register_default_stages()
    
    def _register_default_stages(self) -> None:
        """Register default stage handlers."""
        self.register_stage(PipelineStage.INGEST, self._handle_ingest_stage)
        self.register_stage(PipelineStage.SYNTHESIZE, self._handle_synthesize_stage)
        self.register_stage(PipelineStage.VALIDATE_SCHEMA, self._handle_validate_schema_stage)
        self.register_stage(PipelineStage.COMPARE_CONTRACTS, self._handle_compare_contracts_stage)
        self.register_stage(PipelineStage.GENERATE_ADAPTERS, self._handle_generate_adapters_stage)
        self.register_stage(PipelineStage.GENERATE_TESTS, self._handle_generate_tests_stage)
        self.register_stage(PipelineStage.EXECUTE, self._handle_execute_stage)
        self.register_stage(PipelineStage.DIAGNOSE, self._handle_diagnose_stage)
        self.register_stage(PipelineStage.REPORT, self._handle_report_stage)
    
    def _handle_ingest_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle native interface ingestion stage."""
        analyzer = NativeInterfaceAnalyzer()
        artifact = analyzer.analyze(
            header_path=context.native_library.interface_header_path,
            library_path=context.native_library.library_path,
            context=context
        )
        analyzer.save_artifact(artifact, context.artifacts.native_interface_path)
        return {"artifact_path": context.artifacts.native_interface_path}

    def _handle_synthesize_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle IR normalization and contract synthesis (Phase 3 & 4)."""
        # Phase 3: IR Normalization
        normalizer = IRNormalizer()
        ir_artifact = normalizer.normalize(context)
        
        # Ensure path is available in context
        ir_path = context.artifacts.intermediate_representation_path
        normalizer.save_artifact(ir_artifact, ir_path)
        
        # Phase 4: Contract Synthesis
        synthesizer = ContractSynthesizer()
        contract_artifact = synthesizer.synthesize(context)
        
        return {
            "ir_artifact_path": ir_path,
            "contract_artifact_path": context.artifacts.contract_path
        }

    def _handle_validate_schema_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Validate the contract schema."""
        validator = ContractSchemaValidator()
        result = validator.validate_contract(context.artifacts.contract_path)
        if not result["valid"]:
            raise StageError(f"Contract schema validation failed: {', '.join(result['errors'])}")
        return {"status": "valid", "schema_version": result["contract"]["provenance"]["schema_version"]}

    def _handle_compare_contracts_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Compare current contract with a baseline."""
        baseline_path = getattr(context, "baseline_contract_path", None)
        if not baseline_path:
             raise PreconditionError("Baseline contract path not provided for comparison.")
             
        comparator = ContractComparator()
        diff = comparator.compare_contracts(baseline_path, context.artifacts.contract_path, context.provenance.execution_id)
        
        # Save diff artifact
        diff_path = os.path.join(os.path.dirname(context.artifacts.contract_path), "contract_diff.json")
        with open(diff_path, "w") as f:
            json.dump(diff, f, indent=2)
            
        # Generate human-readable report
        report_gen = CompatibilityReportGenerator()
        report = report_gen.generate_report(diff)
        report_path = os.path.join(os.path.dirname(context.artifacts.contract_path), "compatibility_report.txt")
        with open(report_path, "w") as f:
            f.write(report)
            
        return {
            "diff_path": diff_path,
            "report_path": report_path,
            "summary": diff["summary"]
        }

    def _handle_generate_adapters_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle language adapter generation (Phase 6)."""
        generator = AdapterGenerator()
        metadata = generator.generate(context)
        return metadata

    def _handle_generate_tests_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle test plan generation (Phase 7)."""
        generator = TestPlanGenerator()
        plan = generator.generate(context)
        return plan["test_suite_metadata"]

    def _handle_execute_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle verification execution (Phase 8 & 9)."""
        # Monitoring/Crash Detection is now standard behavior in VerificationExecutor via subprocesses
        executor = VerificationExecutor()
        log = executor.execute(context)
        return log["execution_summary"]

    def _handle_diagnose_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle diagnostics mapping (Phase 10)."""
        mapper = DiagnosticMapper()
        diagnostics = mapper.map_diagnostics(context)
        return diagnostics["summary"]

    def _handle_report_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle comprehensive report generation (Phase 11)."""
        generator = ReportGenerator()
        metadata = generator.generate_reports(context)
        return metadata["metadata"]
    
    def register_stage(self, stage: PipelineStage, handler: Callable) -> None:
        """Register a pipeline stage handler."""
        self._stage_registry[stage] = handler
    
    def execute_stage(self, stage: PipelineStage) -> Dict[str, Any]:
        """Execute a single pipeline stage with precondition checking."""
        # Check preconditions
        self._check_preconditions(stage)
        
        # Get stage handler
        if stage not in self._stage_registry:
            raise StageError(f"Stage '{stage.value}' not implemented yet")
        
        handler = self._stage_registry[stage]
        
        # Execute stage
        try:
            result = handler(self.context)
            
            # Validate output artifacts
            self._validate_outputs(stage, result)
            
            return result
            
        except Exception as e:
            if isinstance(e, VerificationError):
                raise
            raise StageError(f"Stage '{stage.value}' failed: {e}")
    
    def execute_full_pipeline(self) -> Dict[str, Any]:
        """Execute full verification pipeline from ingestion to reporting."""
        stages = [
            PipelineStage.INGEST,
            PipelineStage.SYNTHESIZE,
            PipelineStage.GENERATE_ADAPTERS,
            PipelineStage.GENERATE_TESTS,
            PipelineStage.EXECUTE,
            PipelineStage.DIAGNOSE,
            PipelineStage.REPORT
        ]
        
        results = {}
        
        for stage in stages:
            try:
                if self.context.verification_config.verbosity_level != "quiet":
                    print(f"Executing stage: {stage.value}...")
                
                stage_result = self.execute_stage(stage)
                results[stage.value] = stage_result
                
                if self.context.verification_config.verbosity_level == "verbose":
                    print(f"  ✓ Stage '{stage.value}' completed successfully")
                    
            except VerificationError as e:
                if self.context.verification_config.verbosity_level != "quiet":
                    print(f"  ✗ Stage '{stage.value}' failed: {e}")
                
                results[stage.value] = {"error": str(e), "error_type": e.error_type.value}
                
                # Halt pipeline on first failure
                raise
        
        return results
    
    def _check_preconditions(self, stage: PipelineStage) -> None:
        """Check preconditions for a pipeline stage."""
        required_artifacts = {
            PipelineStage.INGEST: [],
            PipelineStage.SYNTHESIZE: [self.context.artifacts.native_interface_path],
            PipelineStage.GENERATE_ADAPTERS: [self.context.artifacts.contract_path],
            PipelineStage.GENERATE_TESTS: [self.context.artifacts.contract_path],
            PipelineStage.EXECUTE: [
                self.context.artifacts.contract_path,
                self.context.artifacts.test_plan_path
            ],
            PipelineStage.DIAGNOSE: [self.context.artifacts.execution_log_path],
            PipelineStage.REPORT: [self.context.artifacts.diagnostics_path]
        }
        
        for artifact_path in required_artifacts.get(stage, []):
            if not os.path.exists(artifact_path):
                producing_stage = self._get_producing_stage(artifact_path)
                raise PreconditionError(
                    f"Required artifact missing: {os.path.basename(artifact_path)}\n"
                    f"  Path: {artifact_path}\n"
                    f"  This artifact is produced by stage: {producing_stage}\n"
                    f"  Run: polyglot-ffi-verifier {producing_stage} [options]"
                )
    
    def _get_producing_stage(self, artifact_path: str) -> str:
        """Determine which stage produces a given artifact."""
        artifact_map = {
            self.context.artifacts.native_interface_path: "ingest",
            self.context.artifacts.intermediate_representation_path: "synthesize",
            self.context.artifacts.contract_path: "synthesize",
            self.context.artifacts.test_plan_path: "generate-tests",
            self.context.artifacts.execution_log_path: "execute",
            self.context.artifacts.diagnostics_path: "diagnose",
            self.context.artifacts.report_path: "report"
        }
        return artifact_map.get(artifact_path, "unknown")
    
    def _validate_outputs(self, stage: PipelineStage, result: Dict[str, Any]) -> None:
        """Validate that expected output artifacts were produced."""
        expected_artifacts = {
            PipelineStage.INGEST: [self.context.artifacts.native_interface_path],
            PipelineStage.SYNTHESIZE: [self.context.artifacts.intermediate_representation_path],
            PipelineStage.GENERATE_ADAPTERS: [],  # Adapters stored in result/disk but path not standard in context yet?
            PipelineStage.GENERATE_TESTS: [self.context.artifacts.test_plan_path],
            PipelineStage.EXECUTE: [self.context.artifacts.execution_log_path],
            PipelineStage.DIAGNOSE: [self.context.artifacts.diagnostics_path],
            PipelineStage.REPORT: [self.context.artifacts.report_path]
        }
        
        for artifact_path in expected_artifacts.get(stage, []):
            if not os.path.exists(artifact_path):
                raise StageError(
                    f"Stage '{stage.value}' did not produce expected artifact: "
                    f"{os.path.basename(artifact_path)}"
                )


class CLIOrchestrator:
    """
    Command-line interface orchestrator for the verification system.
    """
    
    def __init__(self):
        self.parser = self._build_parser()
    
    def _build_parser(self) -> argparse.ArgumentParser:
        """Build argument parser with all commands and options."""
        parser = argparse.ArgumentParser(
            prog="polyglot-ffi-verifier",
            description="Polyglot FFI Contract Verifier - Make FFI assumptions explicit and enforceable",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        
        # Common arguments for all commands
        common_args = argparse.ArgumentParser(add_help=False)
        common_args.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
        common_args.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output")
        common_args.add_argument("--working-dir", "-w", type=str, help="Working directory for artifacts (default: current directory)")
        
        # Arguments for stages that need native interface
        native_args = argparse.ArgumentParser(add_help=False)
        native_args.add_argument("header_file", type=str, help="Path to C header file defining native interface")
        native_args.add_argument("library_file", type=str, help="Path to native library (DLL/SO/DYLIB)")
        native_args.add_argument("--compiler", type=str, help="Path to compiler (auto-detected if not specified)")
        native_args.add_argument("--include", type=str, action="append", dest="include_paths", help="Additional include path")
        native_args.add_argument("--define", "-D", type=str, action="append", dest="defines", help="Preprocessor macro definition (NAME=VALUE)")
        native_args.add_argument("--flag", type=str, action="append", dest="compiler_flags", help="Additional compiler flag")
        native_args.add_argument("--python", type=str, help="Path to Python interpreter")
        native_args.add_argument("--ffi", type=str, choices=["ctypes", "cffi"], default="ctypes", help="FFI mechanism")
        native_args.add_argument("--seed", type=int, help="Random seed")
        native_args.add_argument("--per-test-timeout", type=int, default=5, help="Timeout per test in seconds")
        native_args.add_argument("--total-timeout", type=int, default=300, help="Total timeout in seconds")
        native_args.add_argument("--subprocess-timeout", type=int, default=60, help="Timeout for individual test subprocesses in seconds")
        native_args.add_argument("--enable-crash-detection", type=str, default="true", help="Enable crash detection (true/false)")
        
        # Commands
        subparsers.add_parser("verify", parents=[common_args, native_args], help="Execute full verification pipeline")
        subparsers.add_parser("ingest", parents=[common_args, native_args], help="Ingest native interface (extract ABI information)")
        subparsers.add_parser("synthesize", parents=[common_args], help="Synthesize FFI contract")
        subparsers.add_parser("generate-adapters", parents=[common_args], help="Generate language adapters")
        subparsers.add_parser("generate-tests", parents=[common_args], help="Generate test plan")
        subparsers.add_parser("execute", parents=[common_args], help="Execute verification tests")
        subparsers.add_parser("diagnose", parents=[common_args], help="Diagnose failures")
        subparsers.add_parser("report", parents=[common_args], help="Generate human-readable report")
        subparsers.add_parser("validate-schema", parents=[common_args], help="Validate contract schema")
        
        compare_parser = subparsers.add_parser("compare-contracts", parents=[common_args], help="Compare contracts")
        compare_parser.add_argument("--baseline", type=str, required=True, help="Path to baseline contract.json")
        
        context_parser = subparsers.add_parser("context", parents=[common_args], help="Display/validate execution context")
        context_parser.add_argument("--validate", action="store_true", help="Validate existing context")
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        parsed_args = self.parser.parse_args(args)
        if not parsed_args.command:
            self.parser.print_help()
            return 1
        
        try:
            verbosity = "verbose" if parsed_args.verbose else ("quiet" if parsed_args.quiet else "normal")
            
            if parsed_args.command == "context":
                return self._handle_context_command(parsed_args, verbosity)
            elif parsed_args.command in ["verify", "ingest"]:
                return self._handle_native_command(parsed_args, verbosity)
            else:
                return self._handle_stage_command(parsed_args, verbosity)
                
        except Exception as e:
            print(f"Error: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 99

    def _handle_context_command(self, args, verbosity: str) -> int:
        working_dir = args.working_dir or os.getcwd()
        context_path = os.path.join(working_dir, "artifacts", "execution_context.json")
        
        if args.validate:
            if not os.path.exists(context_path):
                print(f"Error: Execution context not found at {context_path}")
                return 1
            try:
                ExecutionContext.load(context_path)
                print("✓ Execution context is valid")
                return 0
            except Exception as e:
                print(f"✗ Execution context is invalid: {e}")
                return 1
        else:
            if os.path.exists(context_path):
                context = ExecutionContext.load(context_path)
                print(context.to_json())
                return 0
            else:
                print(f"No execution context found at {context_path}")
                return 1

    def _handle_native_command(self, args, verbosity: str) -> int:
        macros = {}
        if hasattr(args, 'defines') and args.defines:
            for define in args.defines:
                if '=' in define:
                    name, value = define.split('=', 1)
                    macros[name] = value
                else:
                    macros[define] = "1"
        
        builder = ExecutionContextBuilder()
        try:
            context = builder.build(
                header_file=args.header_file,
                library_file=args.library_file,
                compiler_path=getattr(args, 'compiler', None),
                include_paths=getattr(args, 'include_paths', None) or [],
                preprocessor_macros=macros,
                compiler_flags=getattr(args, 'compiler_flags', None) or [],
                python_interpreter=getattr(args, 'python', None),
                ffi_mechanism=getattr(args, 'ffi', 'ctypes'),
                random_seed=getattr(args, 'seed', None),
                per_test_timeout=getattr(args, 'subprocess_timeout', 5),
                total_timeout=getattr(args, 'total_timeout', 300),
                enable_crash_detection=str(getattr(args, 'enable_crash_detection', 'true')).lower() == 'true',
                verbosity=verbosity,
                working_directory=args.working_dir
            )
            
            if verbosity != "quiet":
                print(f"✓ Execution context created")
            
            orchestrator = Pipeline(context)
            if args.command == "verify":
                orchestrator.execute_full_pipeline()
                if verbosity != "quiet":
                    print(f"\n✓ Full verification pipeline completed successfully")
                    print(f"  Report: {context.artifacts.report_path}")
                return 0
            else:
                orchestrator.execute_stage(PipelineStage.Ingest) # wait, usage of PipelineStage.INGEST
                # Correcting for case consistency
                orchestrator.execute_stage(PipelineStage.INGEST)
                if verbosity != "quiet":
                    print(f"✓ Native interface ingestion completed")
                return 0
        except Exception as e:
            # Reraise for run() to catch
            raise e

    def _handle_stage_command(self, args, verbosity: str) -> int:
        working_dir = args.working_dir or os.getcwd()
        context_path = os.path.join(working_dir, "artifacts", "execution_context.json")
        
        if not os.path.exists(context_path):
            raise PreconditionError(f"Execution context not found at {context_path}")
        
        context = ExecutionContext.load(context_path)
        orchestrator = Pipeline(context)
        
        stage_map = {
            "synthesize": PipelineStage.SYNTHESIZE,
            "generate-adapters": PipelineStage.GENERATE_ADAPTERS,
            "generate-tests": PipelineStage.GENERATE_TESTS,
            "execute": PipelineStage.EXECUTE,
            "diagnose": PipelineStage.DIAGNOSE,
            "report": PipelineStage.REPORT,
            "validate-schema": PipelineStage.VALIDATE_SCHEMA,
            "compare-contracts": PipelineStage.COMPARE_CONTRACTS
        }
        
        if args.command == "compare-contracts":
            context.baseline_contract_path = args.baseline
        
        stage = stage_map[args.command]
        orchestrator.execute_stage(stage)
        
        if verbosity != "quiet":
            print(f"✓ Stage '{args.command}' completed successfully")
        
        return 0
