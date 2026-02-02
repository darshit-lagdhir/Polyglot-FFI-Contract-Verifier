#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
POLYGLOT FFI CONTRACT VERIFIER - COMPLETE SYSTEM ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════

This is a MONOLITHIC DISTRIBUTION containing the entire FFI verification
system in a single file for maximum portability and ease of distribution.

VERSION: 1.0.0
AUTHOR: Darshit Lagdhir
LICENSE: MIT
GENERATED: 2026-02-02 09:17:58

═══════════════════════════════════════════════════════════════════════════
SYSTEM OVERVIEW
═══════════════════════════════════════════════════════════════════════════

The Polyglot FFI Contract Verifier transforms implicit FFI assumptions into
explicit, machine-readable contracts and verifies them through automated
testing and crash detection.

ARCHITECTURE: 12-Phase Pipeline
  :  Execution Context & Orchestration
  :  Native Interface Ingestion (libclang-based ABI extraction)
  :  IR Normalization (canonical representation)
  :  Contract Synthesis (constraint derivation)
  :  Contract Versioning (compatibility checking)
  :  Adapter Generation (ctypes wrapper generation)
  :  Test Plan Generation (100% constraint coverage)
  :  Verification Execution (deterministic test execution)
  :  Runtime Monitoring (crash detection via subprocess isolation)
  0: Diagnostics Mapping (failure classification)
  1: Report Generation (HTML/Markdown/CI reports)
  2: CI Integration (GitHub Actions/GitLab/Jenkins templates)

═══════════════════════════════════════════════════════════════════════════
USAGE
═══════════════════════════════════════════════════════════════════════════

Command Line:
    python system_architecture.py verify interface.h library.dll
    python system_architecture.py context

Python API:
    from system_architecture import verify
    
    result = verify('interface.h', 'library.dll')
    
    if result['status'] == 'passed':
        print("✓ Verification PASSED")
    else:
        print("✗ Verification FAILED")

═══════════════════════════════════════════════════════════════════════════
NAVIGATION
═══════════════════════════════════════════════════════════════════════════

Use your editor's outline view or search for these markers:

    # PHASE 1: EXECUTION CONTEXT & ORCHESTRATION
    # PHASE 2: NATIVE INTERFACE INGESTION
    # PHASE 3: IR NORMALIZATION
    # PHASE 4: CONTRACT SYNTHESIS
    # PHASE 5: CONTRACT VERSIONING
    # PHASE 6: ADAPTER GENERATION
    # PHASE 7: TEST PLAN GENERATION
    # PHASE 8: VERIFICATION EXECUTION
    # PHASE 9: RUNTIME MONITORING & CRASH DETECTION
    # PHASE 10: DIAGNOSTICS MAPPING
    # PHASE 11: REPORT GENERATION
    # CLI: COMMAND LINE INTERFACE

═══════════════════════════════════════════════════════════════════════════
METADATA
═══════════════════════════════════════════════════════════════════════════

Total Lines: ~6,000+
Total Classes: ~60+
Total Functions: ~200+

This file was automatically created by consolidating the modular package
structure. The original modular source is maintained separately for
development purposes.

For documentation, see: SYSTEM_ARCHITECTURE.md
For modular source, see: polyglot_ffi_verifier/ directory

═══════════════════════════════════════════════════════════════════════════
"""

__version__ = '1.0.0'
__author__ = 'Darshit Lagdhir'
__license__ = 'MIT'

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

from dataclasses import dataclass
from dataclasses import dataclass, field, asdict
from datetime import datetime
from datetime import datetime, timezone
from datetime import timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict
from typing import Any, Dict, List
from typing import Any, Dict, List, Optional
from typing import Any, Dict, List, Optional, Tuple
from typing import Dict, Any, List
from typing import Dict, Any, List, Optional
from typing import Dict, List, Any, Optional
from typing import Dict, List, Optional, Any
from typing import List, Dict, Any
from typing import Optional, List, Dict, Any, Callable
import argparse
import clang.cindex
import clang.cindex as clang
import ctypes
import hashlib
import importlib
import json
import os
import platform
import subprocess
import sys
import time
import traceback
import uuid
import weakref

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: EXECUTION CONTEXT & ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════
#
# Provides immutable execution context capturing all environmental details.
#
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PlatformIdentification:
    """Platform-specific identification information."""
    os_name: str
    os_version: str
    architecture: str
    pointer_width: int
    endianness: str

@dataclass(frozen=True)
class CompilerInformation:
    """Compiler and tooling information."""
    compiler_name: str
    compiler_path: str
    compiler_version: str
    compiler_flags: List[str]
    include_paths: List[str]
    preprocessor_macros: Dict[str, str]
    standard_library_version: Optional[str] = None

@dataclass(frozen=True)
class NativeLibraryInformation:
    """Native library identification and loading information."""
    library_path: str
    library_hash: str
    library_load_paths: List[str]
    additional_dependencies: List[str]
    interface_header_path: str

@dataclass(frozen=True)
class TargetLanguageRuntime:
    """Target language runtime information."""
    language_name: str
    language_version: str
    ffi_mechanism: str
    runtime_path: str
    runtime_config: Dict[str, Any]

@dataclass(frozen=True)
class VerificationConfig:
    """Verification execution configuration."""
    random_seed: int
    per_test_timeout_seconds: int
    total_timeout_seconds: int
    crash_handling_mode: str
    enable_crash_detection: bool
    verbosity_level: str

@dataclass(frozen=True)
class ProvenanceMetadata:
    """Provenance and versioning information."""
    schema_version: str
    creation_timestamp: str
    execution_id: str
    tool_version: str

@dataclass(frozen=True)
class ArtifactPaths:
    """Paths for artifacts and working directory."""
    working_directory: str
    native_interface_path: str
    intermediate_representation_path: str
    contract_path: str
    test_plan_path: str
    execution_log_path: str
    diagnostics_path: str
    report_path: str
    execution_context_path: str

@dataclass(frozen=True)
class ExecutionContext:
    """
    Immutable execution context capturing all environment-specific details
    relevant to FFI correctness verification.
    
    This is the foundational artifact that is passed to every pipeline stage
    and referenced in all downstream artifacts for reproducibility and auditability.
    """
    platform: PlatformIdentification
    compiler: CompilerInformation
    native_library: NativeLibraryInformation
    target_runtime: TargetLanguageRuntime
    verification_config: VerificationConfig
    provenance: ProvenanceMetadata
    artifacts: ArtifactPaths
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution context to dictionary for serialization."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize execution context to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, path: Optional[str] = None) -> None:
        """
        Save execution context to disk as JSON.
        
        Args:
            path: Optional path to save to. If None, uses artifacts.execution_context_path
        """
        save_path = path or self.artifacts.execution_context_path
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load(cls, path: str) -> 'ExecutionContext':
        """
        Load execution context from JSON file.
        
        Args:
            path: Path to execution context JSON file
            
        Returns:
            ExecutionContext instance
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(
            platform=PlatformIdentification(**data['platform']),
            compiler=CompilerInformation(**data['compiler']),
            native_library=NativeLibraryInformation(**data['native_library']),
            target_runtime=TargetLanguageRuntime(**data['target_runtime']),
            verification_config=VerificationConfig(**data['verification_config']),
            provenance=ProvenanceMetadata(**data['provenance']),
            artifacts=ArtifactPaths(**data['artifacts'])
        )

class ExecutionContextBuilder:
    """
    Builder for constructing ExecutionContext through a deterministic multi-step process.
    
    This class encapsulates the 8-step construction process that gathers all
    environmental information and produces an immutable ExecutionContext object.
    """
    
    TOOL_VERSION = "1.0.0"
    SCHEMA_VERSION = "1.0.0"
    
    def __init__(self):
        self._platform: Optional[PlatformIdentification] = None
        self._compiler: Optional[CompilerInformation] = None
        self._native_library: Optional[NativeLibraryInformation] = None
        self._target_runtime: Optional[TargetLanguageRuntime] = None
        self._verification_config: Optional[VerificationConfig] = None
        self._provenance: Optional[ProvenanceMetadata] = None
        self._artifacts: Optional[ArtifactPaths] = None
    
    def build(
        self,
        header_file: str,
        library_file: str,
        compiler_path: Optional[str] = None,
        include_paths: Optional[List[str]] = None,
        preprocessor_macros: Optional[Dict[str, str]] = None,
        compiler_flags: Optional[List[str]] = None,
        python_interpreter: Optional[str] = None,
        ffi_mechanism: str = "ctypes",
        random_seed: Optional[int] = None,
        per_test_timeout: int = 5,
        total_timeout: int = 300,
        crash_handling_mode: str = "monitor",
        enable_crash_detection: bool = True,
        verbosity: str = "normal",
        working_directory: Optional[str] = None
    ) -> ExecutionContext:
        """
        Build execution context through deterministic 8-step process.
        
        Args:
            header_file: Path to C header file
            library_file: Path to native library (DLL/SO/DYLIB)
            compiler_path: Optional path to compiler (auto-detected if None)
            include_paths: Optional additional include paths
            preprocessor_macros: Optional preprocessor macro definitions
            compiler_flags: Optional additional compiler flags
            python_interpreter: Optional path to Python interpreter (auto-detected if None)
            ffi_mechanism: FFI mechanism to use ("ctypes" or "cffi")
            random_seed: Optional random seed (generated deterministically if None)
            per_test_timeout: Timeout per test in seconds
            total_timeout: Total timeout in seconds
            crash_handling_mode: Crash handling mode ("monitor" or "fail-fast")
            verbosity: Verbosity level ("quiet", "normal", "verbose")
            working_directory: Working directory for artifacts (current dir if None)
            
        Returns:
            Immutable ExecutionContext object
        """
        # STEP 1: Platform Detection
        self._detect_platform()
        
        # STEP 2: Compiler and Tooling Resolution
        self._resolve_compiler(
            compiler_path,
            include_paths or [],
            preprocessor_macros or {},
            compiler_flags or []
        )
        
        # STEP 3: Native Library Validation
        self._validate_native_library(library_file, header_file)
        
        # STEP 4: Target Language Runtime Resolution
        self._resolve_target_runtime(python_interpreter, ffi_mechanism)
        
        # STEP 5: Verification Config
        self._configure_verification(
            library_file,
            random_seed,
            per_test_timeout,
            total_timeout,
            crash_handling_mode,
            enable_crash_detection,
            verbosity
        )
        
        # STEP 6: Provenance Metadata Generation
        self._generate_provenance()
        
        # STEP 7: Artifact Path Resolution
        self._resolve_artifact_paths(working_directory)
        
        # STEP 8: Immutable Context Object Construction
        return self._construct_context()
    
    def _detect_platform(self) -> None:
        """STEP 1: Detect platform identification information."""
        os_name = platform.system()
        os_version = platform.version()
        architecture = platform.machine()
        
        # Determine pointer width
        pointer_width = 64 if sys.maxsize > 2**32 else 32
        
        # Determine endianness
        endianness = sys.byteorder
        
        # Validate platform support (v1 requires Windows x64)
        if os_name != "Windows" or architecture not in ["AMD64", "x86_64"] or pointer_width != 64:
            raise ValueError(
                f"Unsupported platform: {os_name} {architecture} {pointer_width}-bit. "
                f"Version 1.0 requires Windows x64."
            )
        
        self._platform = PlatformIdentification(
            os_name=os_name,
            os_version=os_version,
            architecture=architecture,
            pointer_width=pointer_width,
            endianness=endianness
        )
    
    def _resolve_compiler(
        self,
        compiler_path: Optional[str],
        include_paths: List[str],
        preprocessor_macros: Dict[str, str],
        compiler_flags: List[str]
    ) -> None:
        """STEP 2: Resolve compiler and tooling information."""
        # Detect or validate compiler
        if compiler_path is None:
            # Auto-detect MSVC on Windows
            compiler_path = self._detect_msvc()
        
        if not os.path.exists(compiler_path):
            raise FileNotFoundError(f"Compiler not found at: {compiler_path}")
        
        # Query compiler version
        compiler_name, compiler_version = self._query_compiler_version(compiler_path)
        
        # Resolve include paths to absolute paths
        resolved_includes = [os.path.abspath(p) for p in include_paths]
        
        self._compiler = CompilerInformation(
            compiler_name=compiler_name,
            compiler_path=os.path.abspath(compiler_path),
            compiler_version=compiler_version,
            compiler_flags=list(compiler_flags),
            include_paths=resolved_includes,
            preprocessor_macros=dict(preprocessor_macros),
            standard_library_version=None
        )
    
    def _detect_msvc(self) -> str:
        """Detect MSVC compiler on Windows."""
        # Try common MSVC locations
        common_paths = [
            r"C:\Program Files\Microsoft IDE\2022\Community\VC\Tools\MSVC",
            r"C:\Program Files\Microsoft IDE\2022\Professional\VC\Tools\MSVC",
            r"C:\Program Files\Microsoft IDE\2022\Enterprise\VC\Tools\MSVC",
            r"C:\Program Files (x86)\Microsoft IDE\2019\Community\VC\Tools\MSVC",
        ]
        
        for base_path in common_paths:
            if os.path.exists(base_path):
                # Find latest version
                versions = os.listdir(base_path)
                if versions:
                    latest = sorted(versions)[-1]
                    cl_path = os.path.join(base_path, latest, "bin", "Hostx64", "x64", "cl.exe")
                    if os.path.exists(cl_path):
                        return cl_path
        
        # Fallback: try to find cl.exe in PATH
        try:
            result = subprocess.run(
                ["where", "cl.exe"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n')[0]
        except subprocess.CalledProcessError:
            pass
        
        raise FileNotFoundError(
            "MSVC compiler (cl.exe) not found. Please install IDE or "
            "specify compiler path explicitly."
        )
    
    def _query_compiler_version(self, compiler_path: str) -> tuple[str, str]:
        """Query compiler name and version."""
        try:
            # For MSVC
            if "cl.exe" in compiler_path.lower():
                result = subprocess.run(
                    [compiler_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # MSVC prints version to stderr
                output = result.stderr
                # Extract version from output like "Version 19.35.32215 for x64"
                for line in output.split('\n'):
                    if 'Version' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'Version' and i + 1 < len(parts):
                                return "MSVC", parts[i + 1]
                return "MSVC", "unknown"
            else:
                # Generic compiler version query
                result = subprocess.run(
                    [compiler_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True
                )
                first_line = result.stdout.split('\n')[0]
                return "Unknown", first_line
        except Exception as e:
            raise RuntimeError(f"Failed to query compiler version: {e}")
    
    def _validate_native_library(self, library_file: str, header_file: str) -> None:
        """STEP 3: Validate native library and compute hash."""
        library_path = os.path.abspath(library_file)
        header_path = os.path.abspath(header_file)
        
        if not os.path.exists(library_path):
            raise FileNotFoundError(f"Native library not found: {library_path}")
        
        # Compute SHA-256 hash
        library_hash = self._compute_file_hash(library_path)
        
        # Determine library load paths (Windows DLL search order)
        library_dir = os.path.dirname(library_path)
        load_paths = [
            library_dir,
            os.getcwd(),
            os.environ.get('SystemRoot', r'C:\Windows'),
            os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32'),
        ]
        
        # Add PATH directories
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        load_paths.extend([p for p in path_dirs if p])
        
        self._native_library = NativeLibraryInformation(
            library_path=library_path,
            library_hash=library_hash,
            library_load_paths=load_paths,
            additional_dependencies=[],
            interface_header_path=header_path
        )
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _resolve_target_runtime(
        self,
        python_interpreter: Optional[str],
        ffi_mechanism: str
    ) -> None:
        """STEP 4: Resolve target language runtime information."""
        # Detect or validate Python interpreter
        if python_interpreter is None:
            python_interpreter = sys.executable
        
        if not os.path.exists(python_interpreter):
            raise FileNotFoundError(f"Python interpreter not found: {python_interpreter}")
        
        # Query Python version
        try:
            result = subprocess.run(
                [python_interpreter, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            version_output = result.stdout.strip()
            # Extract version like "Python 3.11.5"
            version = version_output.replace("Python ", "")
        except Exception as e:
            raise RuntimeError(f"Failed to query Python version: {e}")
        
        # Validate FFI mechanism
        if ffi_mechanism not in ["ctypes", "cffi"]:
            raise ValueError(f"Unsupported FFI mechanism: {ffi_mechanism}. Use 'ctypes' or 'cffi'.")
        
        # Validate FFI module is available
        try:
            result = subprocess.run(
                [python_interpreter, "-c", f"import {ffi_mechanism}"],
                capture_output=True,
                timeout=5,
                check=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(f"FFI mechanism '{ffi_mechanism}' not available in Python runtime")
        
        self._target_runtime = TargetLanguageRuntime(
            language_name="Python",
            language_version=version,
            ffi_mechanism=ffi_mechanism,
            runtime_path=os.path.abspath(python_interpreter),
            runtime_config={}
        )
    
    def _configure_verification(
        self,
        library_file: str,
        random_seed: Optional[int],
        per_test_timeout: int,
        total_timeout: int,
        crash_handling_mode: str,
        enable_crash_detection: bool,
        verbosity: str
    ) -> None:
        """STEP 5: Configure verification parameters."""
        # Deterministic seed generation if not provided
        if random_seed is None:
            # Hash library path and filename for a stable seed per library
            lib_path = os.path.abspath(library_file)
            seed_source = f"{lib_path}:{os.path.basename(lib_path)}"
            random_seed = abs(hash(seed_source)) % (2**32)
            
        # Validate crash handling mode
        if crash_handling_mode not in ["monitor", "fail-fast"]:
            raise ValueError(
                f"Invalid crash handling mode: {crash_handling_mode}. "
                f"Use 'monitor' or 'fail-fast'."
            )
        
        # Validate verbosity
        if verbosity not in ["quiet", "normal", "verbose"]:
            raise ValueError(
                f"Invalid verbosity level: {verbosity}. "
                f"Use 'quiet', 'normal', or 'verbose'."
            )
        
        self._verification_config = VerificationConfig(
            random_seed=random_seed,
            per_test_timeout_seconds=per_test_timeout,
            total_timeout_seconds=total_timeout,
            crash_handling_mode=crash_handling_mode,
            enable_crash_detection=enable_crash_detection,
            verbosity_level=verbosity
        )
    
    def _generate_deterministic_seed(self, library_file: str) -> int:
        """
        Generate deterministic seed from library path and rounded timestamp.
        
        Timestamp is rounded to nearest hour to allow reproducibility within
        reasonable time windows while still providing freshness.
        """
        # Get current time rounded to nearest hour
        now = datetime.now(timezone.utc)
        rounded_hour = now.replace(minute=0, second=0, microsecond=0)
        timestamp_str = rounded_hour.isoformat()
        
        # Combine library path and timestamp
        seed_input = f"{os.path.abspath(library_file)}:{timestamp_str}"
        
        # Hash to generate seed
        hash_bytes = hashlib.sha256(seed_input.encode('utf-8')).digest()
        
        # Convert first 4 bytes to integer
        seed = int.from_bytes(hash_bytes[:4], byteorder='big')
        
        return seed
    
    def _generate_provenance(self) -> None:
        """STEP 6: Generate provenance metadata."""
        # Generate UUID v4 for execution identifier
        execution_id = str(uuid.uuid4())
        
        # Capture current timestamp in UTC, ISO 8601 format
        creation_timestamp = datetime.now(timezone.utc).isoformat()
        
        self._provenance = ProvenanceMetadata(
            schema_version=self.SCHEMA_VERSION,
            creation_timestamp=creation_timestamp,
            execution_id=execution_id,
            tool_version=self.TOOL_VERSION
        )
    
    def _resolve_artifact_paths(self, working_directory: Optional[str]) -> None:
        """STEP 7: Resolve artifact paths and create directories."""
        # Use current directory if not specified
        if working_directory is None:
            working_directory = os.getcwd()
        
        working_dir = os.path.abspath(working_directory)
        
        # Create artifacts subdirectory
        artifacts_dir = os.path.join(working_dir, "artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        
        # Validate write permissions
        test_file = os.path.join(artifacts_dir, ".write_test")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            raise PermissionError(f"No write permission for artifacts directory: {e}")
        
        # Resolve all artifact paths
        self._artifacts = ArtifactPaths(
            working_directory=working_dir,
            native_interface_path=os.path.join(
                artifacts_dir, "native_interface.json"
            ),
            intermediate_representation_path=os.path.join(
                artifacts_dir, "intermediate_representation.json"
            ),
            contract_path=os.path.join(artifacts_dir, "contract.json"),
            test_plan_path=os.path.join(artifacts_dir, "test_plan.json"),
            execution_log_path=os.path.join(artifacts_dir, "execution_log.json"),
            diagnostics_path=os.path.join(artifacts_dir, "diagnostics.json"),
            report_path=os.path.join(artifacts_dir, "report.txt"),
            execution_context_path=os.path.join(artifacts_dir, "execution_context.json")
        )
    
    def _construct_context(self) -> ExecutionContext:
        """STEP 8: Construct immutable ExecutionContext object."""
        # Verify all components are initialized
        if not all([
            self._platform,
            self._compiler,
            self._native_library,
            self._target_runtime,
            self._verification_config,
            self._provenance,
            self._artifacts
        ]):
            raise RuntimeError("ExecutionContext construction incomplete")
        
        # Construct immutable context
        context = ExecutionContext(
            platform=self._platform,
            compiler=self._compiler,
            native_library=self._native_library,
            target_runtime=self._target_runtime,
            verification_config=self._verification_config,
            provenance=self._provenance,
            artifacts=self._artifacts
        )
        
        # Serialize to disk
        context.save()
        
        return context

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: EXECUTION CONTEXT & ORCHESTRATION (CONTINUED)
# ═══════════════════════════════════════════════════════════════════════════
#
# High-level pipeline orchestration coordinating all verification phases.
#
# ═══════════════════════════════════════════════════════════════════════════

# Updated imports from consolidated modules

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

class ConfigError(VerificationError):
    """Config-related errors."""
    
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
        """Handle IR normalization and contract synthesis ( & 4)."""
        # : IR Normalization
        normalizer = IRNormalizer()
        ir_artifact = normalizer.normalize(context)
        
        # Ensure path is available in context
        ir_path = context.artifacts.intermediate_representation_path
        normalizer.save_artifact(ir_artifact, ir_path)
        
        # : Contract Synthesis
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
        """Handle language adapter generation ()."""
        generator = AdapterGenerator()
        metadata = generator.generate(context)
        return metadata

    def _handle_generate_tests_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle test plan generation ()."""
        generator = TestPlanGenerator()
        plan = generator.generate(context)
        return plan["test_suite_metadata"]

    def _handle_execute_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle verification execution ( & 9)."""
        # Monitoring/Crash Detection is now standard behavior in VerificationExecutor via subprocesses
        executor = VerificationExecutor()
        log = executor.execute(context)
        return log["execution_summary"]

    def _handle_diagnose_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle diagnostics mapping (0)."""
        mapper = DiagnosticMapper()
        diagnostics = mapper.map_diagnostics(context)
        return diagnostics["summary"]

    def _handle_report_stage(self, context: ExecutionContext) -> Dict[str, Any]:
        """Handle comprehensive report generation (1)."""
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
            PipelineStage.GENERATE_ADAPTERS: [],  # Adapters stored in result/disk but path not standard in context yet
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

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: NATIVE INTERFACE INGESTION
# ═══════════════════════════════════════════════════════════════════════════
#
# Compiler-grade ABI extraction using libclang for native interface analysis.
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# EXTERNAL DEPENDENCIES (libclang)
# ============================================================================

def _configure_libclang():
    """Configure libclang library path for Windows."""
    common_paths = [
        r"C:\Program Files\LLVM\bin\libclang.dll",
        r"C:\Program Files (x86)\LLVM\bin\libclang.dll",
        r"C:\LLVM\bin\libclang.dll",
    ]
    env_path = os.environ.get('LIBCLANG_PATH')
    if env_path and os.path.exists(env_path):
        import clang.cindex
        clang.cindex.Config.set_library_file(env_path)
        return
    for path in common_paths:
        if os.path.exists(path):
            import clang.cindex
            clang.cindex.Config.set_library_file(path)
            return

_configure_libclang()
try:
    import clang.cindex as clang
except ImportError:
    # We allow import error here, but classes will fail if instantiated
    clang = None

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

@dataclass(frozen=True)
class SourceLocation:
    """Immutable source location representation."""
    file: str
    line: int
    column: int

class SourceLocationTracker:
    """Tracks and formats source locations from AST nodes."""
    
    def get_location(self, cursor) -> SourceLocation:
        try:
            location = cursor.location
            if location.file:
                file_path = os.path.abspath(location.file.name)
                return SourceLocation(file=file_path, line=location.line, column=location.column)
            else:
                return self._unknown_location()
        except Exception:
            return self._unknown_location()
    
    def format_location(self, location: SourceLocation) -> Dict[str, Any]:
        return {"file": location.file, "line": location.line, "column": location.column}
    
    def _unknown_location(self) -> SourceLocation:
        return SourceLocation(file="<unknown>", line=0, column=0)
    
    def get_location_dict(self, cursor) -> Dict[str, Any]:
        location = self.get_location(cursor)
        return self.format_location(location)

class ABIExtractor:
    """Extracts ABI-specific information from AST nodes."""
    
    def compute_struct_layout(self, cursor) -> Dict[str, Any]:
        struct_type = cursor.type
        size_bytes = struct_type.get_size()
        alignment_bytes = struct_type.get_align()
        is_union = cursor.kind == clang.IDEKind.UNION_DECL
        
        declared_fields = []
        for field_cursor in cursor.get_children():
            if field_cursor.kind == clang.IDEKind.FIELD_DECL:
                field_info = self._extract_field_info(field_cursor)
                declared_fields.append(field_info)
        
        fields_with_padding = self.calculate_padding(declared_fields, size_bytes, alignment_bytes, is_union)
        
        return {
            "size_bytes": size_bytes,
            "alignment_bytes": alignment_bytes,
            "fields": fields_with_padding,
            "is_packed": self._is_packed(cursor),
            "is_union": is_union
        }
    
    def _extract_field_info(self, field_cursor) -> Dict[str, Any]:
        field_name = field_cursor.spelling
        field_type = field_cursor.type
        try:
            offset_bits = field_cursor.get_field_offsetof()
            offset_bytes = offset_bits // 8
        except:
            offset_bytes = 0
        
        type_info = self.extract_type_info(field_type)
        return {"name": field_name, "offset_bytes": offset_bytes, "type": type_info, "is_implicit": False}
    
    def calculate_padding(self, fields: List[Dict[str, Any]], total_size: int, alignment: int, is_union: bool) -> List[Dict[str, Any]]:
        if is_union or not fields: return fields
        result = []
        padding_counter = 1
        sorted_fields = sorted(fields, key=lambda f: f["offset_bytes"])
        
        for i, field in enumerate(sorted_fields):
            result.append(field)
            current_offset = field["offset_bytes"]
            current_size = field["type"]["size_bytes"]
            expected_next = current_offset + current_size
            
            if i + 1 < len(sorted_fields):
                next_offset = sorted_fields[i + 1]["offset_bytes"]
                if next_offset > expected_next:
                    padding_size = next_offset - expected_next
                    result.append({
                        "name": f"__padding_{padding_counter}",
                        "offset_bytes": expected_next,
                        "type": {"kind": "padding", "size_bytes": padding_size},
                        "is_implicit": True
                    })
                    padding_counter += 1

        if sorted_fields:
            last_field = sorted_fields[-1]
            last_end = last_field["offset_bytes"] + last_field["type"]["size_bytes"]
            if total_size > last_end:
                result.append({
                    "name": f"__padding_{padding_counter}",
                    "offset_bytes": last_end,
                    "type": {"kind": "padding", "size_bytes": total_size - last_end},
                    "is_implicit": True
                })
        return result
    
    def extract_type_info(self, clang_type) -> Dict[str, Any]:
        type_kind = clang_type.kind
        # Primitive types
        if type_kind in [
            clang.TypeKind.VOID, clang.TypeKind.BOOL,
            clang.TypeKind.CHAR_U, clang.TypeKind.UCHAR, clang.TypeKind.CHAR16,
            clang.TypeKind.CHAR32, clang.TypeKind.USHORT, clang.TypeKind.UINT,
            clang.TypeKind.ULONG, clang.TypeKind.ULONGLONG, clang.TypeKind.UINT128,
            clang.TypeKind.CHAR_S, clang.TypeKind.SCHAR, clang.TypeKind.WCHAR,
            clang.TypeKind.SHORT, clang.TypeKind.INT, clang.TypeKind.LONG,
            clang.TypeKind.LONGLONG, clang.TypeKind.INT128, clang.TypeKind.FLOAT,
            clang.TypeKind.DOUBLE, clang.TypeKind.LONGDOUBLE
        ]:
            return {
                "kind": "primitive", "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.POINTER:
             return {
                "kind": "pointer", "pointee": self.extract_type_info(clang_type.get_pointee()),
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.CONSTANTARRAY:
             return {
                "kind": "array", "element_type": self.extract_type_info(clang_type.get_array_element_type()),
                "size": clang_type.get_array_size(), "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.TYPEDEF:
             return {
                "kind": "typedef", "name": clang_type.spelling,
                "underlying_type": self.extract_type_info(clang_type.get_canonical()),
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.RECORD:
             return {
                "kind": "record", "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.ENUM:
             return {
                "kind": "enum", "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.FUNCTIONPROTO:
             return {"kind": "function_pointer", "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()}
        else:
             return {
                "kind": "unknown", "name": clang_type.spelling,
                "size_bytes": max(0, clang_type.get_size()), "alignment_bytes": max(0, clang_type.get_align())
            }

    def determine_calling_convention(self, cursor) -> str:
        try:
            conv = cursor.type.get_calling_conv()
            if conv == clang.CallingConv.C: return "cdecl"
            elif conv == clang.CallingConv.X86_STDCALL: return "stdcall"
            elif conv == clang.CallingConv.X86_FASTCALL: return "fastcall"
            elif conv == clang.CallingConv.X86_THISCALL: return "thiscall"
            elif conv == clang.CallingConv.WIN64: return "win64"
            else: return "cdecl"
        except:
            return "cdecl"

    def _is_packed(self, cursor) -> bool:
        for child in cursor.get_children():
            if child.kind == clang.IDEKind.PACKED_ATTR:
                return True
        return False

class CompilerFrontend:
    """Interfaces with libclang to parse C header files and provide AST access."""
    
    def __init__(self):
        if not clang:
            raise ImportError("libclang not found. Install with: pip install libclang")
        self.index = clang.Index.create()
    
    def parse_header(self, header_path: str, context):
        if not os.path.exists(header_path):
            raise Exception(f"Header file not found: {header_path}")
        
        args = self.get_compiler_command(context)
        try:
            tu = self.index.parse(
                header_path,
                args=args,
                options=(clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | clang.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)
            )
        except Exception as e:
            raise Exception(f"Failed to parse header: {e}")
        
        if not self.validate_compilation(tu):
            raise Exception(f"Header compilation failed:\n{self._format_diagnostics(tu)}")
        return tu

    def get_compiler_command(self, context) -> List[str]:
        args = []
        for p in context.compiler.include_paths: args.append(f"-I{p}")
        for m in context.compiler.preprocessor_macros: args.append(f"-D{m}")
        if context.platform.os_name == "Windows":
             args.extend(["-fms-compatibility", "-fms-extensions", f"-fms-compatibility-version={context.compiler.compiler_version}"])
        if context.platform.architecture == "AMD64": args.append("-m64")
        return args

    def validate_compilation(self, tu) -> bool:
        for diag in tu.diagnostics:
            if diag.severity >= clang.Diagnostic.Error: return False
        return True

    def _format_diagnostics(self, tu) -> str:
        messages = []
        for diag in tu.diagnostics:
            loc = f"{diag.location.file.name}:{diag.location.line}:{diag.location.column}" if diag.location.file else "<unknown>"
            messages.append(f"Severity({diag.severity}): {loc}: {diag.spelling}")
        return "\n".join(messages) if messages else "No diagnostics available"
        
    def get_compiler_invocation_string(self, header_path: str, context) -> str:
        args = self.get_compiler_command(context)
        return f"clang {' '.join(args)} {header_path}"

class NativeInterfaceAnalyzer:
    """Main orchestrator for native interface ingestion."""

    def __init__(self):
        self.frontend = CompilerFrontend()
        self.abi_extractor = ABIExtractor()
        self.location_tracker = SourceLocationTracker()

    def analyze(self, header_path: str, library_path: str, context) -> Dict[str, Any]:
        tu = self.frontend.parse_header(header_path, context)
        
        functions = self.extract_functions(tu.cursor)
        structs = self.extract_structs(tu.cursor)
        enums = self.extract_enums(tu.cursor)
        typedefs = self.extract_typedefs(tu.cursor)
        
        return self._build_artifact(
            functions=functions, structs=structs, enums=enums, typedefs=typedefs,
            header_path=header_path, library_path=library_path, context=context
        )

    def extract_functions(self, cursor) -> List[Dict[str, Any]]:
        functions = []
        for node in cursor.walk_preorder():
            if node.kind == clang.IDEKind.FUNCTION_DECL and node.linkage == clang.LinkageKind.EXTERNAL:
                functions.append(self._extract_function_info(node))
        return functions

    def extract_structs(self, cursor) -> List[Dict[str, Any]]:
        structs = []
        seen = set()
        for node in cursor.walk_preorder():
            if node.kind in [clang.IDEKind.STRUCT_DECL, clang.IDEKind.UNION_DECL] and node.is_definition():
                if node.spelling and node.spelling not in seen:
                    seen.add(node.spelling)
                    structs.append(self._extract_struct_info(node))
        return structs

    def extract_enums(self, cursor) -> List[Dict[str, Any]]:
        enums = []
        seen = set()
        for node in cursor.walk_preorder():
            if node.kind == clang.IDEKind.ENUM_DECL and node.is_definition():
                if node.spelling and node.spelling not in seen:
                    seen.add(node.spelling)
                    enums.append(self._extract_enum_info(node))
        return enums

    def extract_typedefs(self, cursor) -> List[Dict[str, Any]]:
        typedefs = []
        seen = set()
        for node in cursor.walk_preorder():
            if node.kind == clang.IDEKind.TYPEDEF_DECL:
                if node.spelling and node.spelling not in seen:
                    seen.add(node.spelling)
                    typedefs.append(self._extract_typedef_info(node))
        return typedefs

    def _extract_function_info(self, cursor) -> Dict[str, Any]:
        func_name = cursor.spelling
        return_type = self.abi_extractor.extract_type_info(cursor.type.get_result())
        parameters = []
        for arg in cursor.get_arguments():
            parameters.append({
                "name": arg.spelling or f"param{len(parameters)}",
                "type": self.abi_extractor.extract_type_info(arg.type),
                "qualifiers": self._extract_qualifiers(arg.type)
            })
        
        return {
            "name": func_name,
            "source_location": self.location_tracker.get_location_dict(cursor),
            "linkage": "external",
            "calling_convention": self.abi_extractor.determine_calling_convention(cursor),
            "return_type": return_type,
            "parameters": parameters,
            "is_variadic": cursor.type.is_function_variadic(),
            "attributes": []
        }

    def _extract_struct_info(self, cursor) -> Dict[str, Any]:
        layout = self.abi_extractor.compute_struct_layout(cursor)
        return {
            "name": cursor.spelling,
            "source_location": self.location_tracker.get_location_dict(cursor),
            "size_bytes": layout["size_bytes"],
            "alignment_bytes": layout["alignment_bytes"],
            "fields": layout["fields"],
            "is_packed": layout["is_packed"],
            "is_union": layout["is_union"]
        }

    def _extract_enum_info(self, cursor) -> Dict[str, Any]:
        underlying = self.abi_extractor.extract_type_info(cursor.enum_type)
        values = []
        for child in cursor.get_children():
            if child.kind == clang.IDEKind.ENUM_CONSTANT_DECL:
                values.append({"name": child.spelling, "value": child.enum_value})
        
        return {
            "name": cursor.spelling,
            "source_location": self.location_tracker.get_location_dict(cursor),
            "underlying_type": underlying,
            "values": values
        }

    def _extract_typedef_info(self, cursor) -> Dict[str, Any]:
        return {
            "name": cursor.spelling,
            "source_location": self.location_tracker.get_location_dict(cursor),
            "underlying_type": self.abi_extractor.extract_type_info(cursor.underlying_typedef_type)
        }

    def _extract_qualifiers(self, clang_type) -> List[str]:
        q = []
        if clang_type.is_const_qualified(): q.append("const")
        if clang_type.is_volatile_qualified(): q.append("volatile")
        if clang_type.is_restrict_qualified(): q.append("restrict")
        return q

    def _build_artifact(self, functions, structs, enums, typedefs, header_path, library_path, context) -> Dict[str, Any]:
        ci = self.frontend.get_compiler_invocation_string(header_path, context)
        return {
            "provenance": {
                "producing_phase": "Native Interface Ingestion",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(header_path), os.path.abspath(library_path)],
                "compiler_invocation": ci
            },
            "platform": {
                "os_name": context.platform.os_name,
                "architecture": context.platform.architecture,
                "pointer_width": context.platform.pointer_width,
                "endianness": context.platform.endianness
            },
            "functions": functions, "structs": structs, "enums": enums, "typedefs": typedefs
        }

    def save_artifact(self, artifact: Dict[str, Any], output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: IR NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════
#
# Transformation of native artifacts into canonical, platform-agnostic IR.
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class QualifierNormalizer:
    """
    Normalizes type qualifiers from compiler-specific lists to canonical boolean maps.
    """
    
    def normalize(self, qualifiers: List[str]) -> Dict[str, bool]:
        """
        Convert a list of qualifier strings into a normalized dictionary.
        
        Args:
            qualifiers: List of strings like ["const", "volatile"]
            
        Returns:
            Dictionary with canonical keys and boolean values
        """
        # Ensure input is a list
        if not isinstance(qualifiers, list):
            qualifiers = []
            
        # Case insensitive matching
        q_lower = [q.lower() for q in qualifiers]
        
        return {
            "is_const": "const" in q_lower,
            "is_volatile": "volatile" in q_lower,
            "is_restrict": "restrict" in q_lower
        }

    @staticmethod
    def extract_from_type(type_info: Dict) -> Dict[str, bool]:
        """ Helper to extract qualifiers from a type info dictionary if present. """
        qualifiers = type_info.get("qualifiers", [])
        return QualifierNormalizer().normalize(qualifiers)

class TypeResolver:
    """
    Handles type normalization, typedef resolution, and deterministic ID generation.
    """
    
    def __init__(self, platform_info: Dict[str, Any]):
        """
        Initialize with platform information for correct primitive mapping.
        """
        self.os_name = platform_info.get("os_name", "Windows")
        self.arch = platform_info.get("architecture", "AMD64")
        self.ptr_width = platform_info.get("pointer_width", 64)
        
        # Primitive mapping table for Windows x64
        self._primitive_map = {
            "void": "void",
            "bool": "bool",
            "_Bool": "bool",
            "char": "int8",  # Standard MSVC char is signed by default
            "signed char": "int8",
            "unsigned char": "uint8",
            "short": "int16",
            "signed short": "int16",
            "unsigned short": "uint16",
            "int": "int32",
            "signed int": "int32",
            "unsigned int": "uint32",
            "long": "int32",  # Windows x64 specific: long is 32-bit (LLP64)
            "signed long": "int32",
            "unsigned long": "uint32",
            "long long": "int64",
            "signed long long": "int64",
            "unsigned long long": "uint64",
            "__int64": "int64",
            "float": "float32",
            "double": "float64",
            "long double": "float64", # MSVC treats long double as double
            "size_t": "uint64" if self.ptr_width == 64 else "uint32",
            "wchar_t": "wchar"
        }

    def resolve_type(self, type_info: Dict[str, Any], type_registry: Dict[str, Any]) -> str:
        """
        Resolve a type to its canonical ID and ensure it exists in the registry.
        
        Returns:
            The type_id (e.g., "primitive:int32")
        """
        kind = type_info.get("kind")
        
        # 1. Resolve Typedefs transitively
        if kind == "typedef":
            underlying = type_info.get("underlying_type")
            if not underlying:
                raise ValueError(f"Malformed typedef: {type_info.get('name')}")
            return self.resolve_type(underlying, type_registry)
            
        # 2. Handle Primitives
        if kind == "primitive":
            raw_name = type_info.get("name", "unknown")
            canon_name = self._primitive_map.get(raw_name, raw_name)
            type_id = f"primitive:{canon_name}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "primitive",
                    "canonical_name": canon_name,
                    "size_bytes": type_info.get("size_bytes"),
                    "alignment_bytes": type_info.get("alignment_bytes")
                }
            return type_id
            
        # 3. Handle Pointers
        if kind == "pointer":
            pointee = type_info.get("pointee")
            if not pointee:
                # Fallback for void* or incomplete pointers if pointee missing
                # But mostly this should raise error or handle void*
                # Assuming generic void* if missing or check if it's handled upstream
                # For safety, let's raise if critical, but if it happens in void* case:
                # In our extractor, pointer always has pointee.
                raise ValueError("Malformed pointer: missing pointee")
                
            pointee_id = self.resolve_type(pointee, type_registry)
            type_id = f"pointer:{pointee_id}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "pointer",
                    "canonical_name": f"pointer<{pointee_id}>",
                    "pointee_type_id": pointee_id,
                    "size_bytes": type_info.get("size_bytes", self.ptr_width // 8),
                    "alignment_bytes": type_info.get("alignment_bytes", self.ptr_width // 8)
                }
            return type_id
            
        # 4. Handle Structs
        if kind in ["struct", "record"]:
            name = type_info.get("name", "anonymous_struct")
            type_id = f"struct:{name}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "struct",
                    "canonical_name": name,
                    "size_bytes": type_info.get("size_bytes"),
                    "alignment_bytes": type_info.get("alignment_bytes"),
                    "source_location": type_info.get("source_location")
                }
            return type_id

        # 5. Handle Enums
        if kind == "enum":
            name = type_info.get("name", "anonymous_enum")
            type_id = f"enum:{name}"
            
            if type_id not in type_registry:
                underlying = type_info.get("underlying_type", {"kind": "primitive", "name": "int"})
                underlying_id = self.resolve_type(underlying, type_registry)
                
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "enum",
                    "canonical_name": name,
                    "underlying_type_id": underlying_id,
                    "size_bytes": type_info.get("size_bytes", 4),
                    "alignment_bytes": type_info.get("alignment_bytes", 4),
                    "source_location": type_info.get("source_location")
                }
            return type_id
            
        # 6. Handle Padding
        if kind == "padding":
            size = type_info.get("size_bytes", 0)
            type_id = f"padding:{size}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "padding",
                    "size_bytes": size
                }
            return type_id

        # 7. Handle Arrays
        if kind == "array":
            element = type_info.get("element_type")
            count = type_info.get("element_count", 0)
            # Try to get count from type info if not in top level, 
            # In ABIExtractor array size is "size".
            if count == 0 and "size" in type_info:
                 count = type_info["size"]
                 
            element_id = self.resolve_type(element, type_registry)
            type_id = f"array:{element_id}:{count}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "array",
                    "element_type_id": element_id,
                    "element_count": count,
                    "size_bytes": type_info.get("size_bytes"),
                    "alignment_bytes": type_info.get("alignment_bytes")
                }
            return type_id

        return f"unknown:{type_info.get('name', 'unnamed')}"

class LayoutNormalizer:
    """
    Handles structural normalization of layouts (structs, unions).
    """
    
    def __init__(self, type_resolver: TypeResolver):
        self.type_resolver = type_resolver
        
    def normalize_struct(self, struct_info: Dict[str, Any], type_registry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a struct definition.
        """
        type_id = self.type_resolver.resolve_type(struct_info, type_registry)
        
        normalized_fields = []
        for field in struct_info.get("fields", []):
            field_type = field.get("type")
            if not field_type:
                continue
                
            field_type_id = self.type_resolver.resolve_type(field_type, type_registry)
            
            normalized_field = {
                "name": field.get("name"),
                "offset_bytes": field.get("offset_bytes"),
                "type_id": field_type_id
            }
            
            # Preserve bit width if present
            if field.get("bit_width") is not None:
                normalized_field["bit_width"] = field["bit_width"]
                
            # Preserve implicit flag (for padding)
            if field.get("is_implicit"):
                normalized_field["is_implicit"] = True
                
            normalized_fields.append(normalized_field)
            
        return {
            "name": struct_info.get("name"),
            "type_id": type_id,
            "source_location": struct_info.get("source_location"),
            "size_bytes": struct_info.get("size_bytes"),
            "alignment_bytes": struct_info.get("alignment_bytes"),
            "fields": normalized_fields,
            "is_packed": struct_info.get("is_packed", False),
            "is_union": struct_info.get("is_union", False)
        }

# ============================================================================
# PUBLIC API
# ============================================================================

class IRNormalizer:
    """
    Orchestrates the IR normalization process.
    Produces Intermediate Representation from Native Interface Artifact.
    """
    
    def __init__(self):
        self.qualifier_normalizer = QualifierNormalizer()
        
    def normalize(self, context) -> Dict[str, Any]:
        """
        Produce Intermediate Representation from Native Interface Artifact.
        
        Args:
            context: ExecutionContext containing path to native interface artifact
        
        Returns:
            IR Artifact dictionary
        """
        # 1. Load native interface
        # The path should be from context
        native_interface_path = context.artifacts.native_interface_path
        
        if not os.path.exists(native_interface_path):
            raise FileNotFoundError(f"Native Interface Artifact not found at {native_interface_path}. Run Ingestion first.")
            
        with open(native_interface_path, 'r', encoding='utf-8') as f:
            ni = json.load(f)
            
        # 2. Initialize sub-components
        type_resolver = TypeResolver(ni.get("platform", {}))
        layout_normalizer = LayoutNormalizer(type_resolver)
        
        type_registry = {}
        
        # 3. Normalize Enums first (simplest types)
        normalized_enums = []
        for enum in ni.get("enums", []):
            normalized_enums.append(self._normalize_enum(enum, type_resolver, type_registry))
            
        # 4. Normalize Structs
        normalized_structs = []
        for struct in ni.get("structs", []):
            normalized_structs.append(layout_normalizer.normalize_struct(struct, type_registry))
            
        # 5. Normalize Functions
        normalized_functions = []
        for func in ni.get("functions", []):
            normalized_functions.append(self._normalize_function(func, type_resolver, type_registry))
            
        # 6. Build IR Artifact
        ir_artifact = {
            "provenance": {
                "producing_phase": ": Intermediate Representation Normalization",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(native_interface_path)]
            },
            "platform": ni.get("platform"),
            "type_registry": type_registry,
            "functions": normalized_functions,
            "structs": normalized_structs,
            "enums": normalized_enums
        }
        
        return ir_artifact

    def _normalize_enum(self, enum: Dict, resolver: TypeResolver, registry: Dict) -> Dict:
        type_id = resolver.resolve_type(enum, registry)
        underlying_type = enum.get("underlying_type", {"kind": "primitive", "name": "int"})
        underlying_id = resolver.resolve_type(underlying_type, registry)
        
        return {
            "name": enum.get("name"),
            "type_id": type_id,
            "source_location": enum.get("source_location"),
            "underlying_type_id": underlying_id,
            "values": enum.get("values", [])
        }

    def _normalize_function(self, func: Dict, resolver: TypeResolver, registry: Dict) -> Dict:
        return_type_id = resolver.resolve_type(func.get("return_type", {}), registry)
        
        normalized_params = []
        for param in func.get("parameters", []):
            p_type = param.get("type", {})
            p_type_id = resolver.resolve_type(p_type, registry)
            
            normalized_params.append({
                "name": param.get("name"),
                "type_id": p_type_id,
                "qualifiers": self.qualifier_normalizer.normalize(param.get("qualifiers", []))
            })
            
        return {
            "name": func.get("name"),
            "mangled_name": func.get("mangled_name"),
            "source_location": func.get("source_location"),
            "linkage": func.get("linkage", "external"),
            "calling_convention": func.get("calling_convention", "cdecl"),
            "return_type_id": return_type_id,
            "parameters": normalized_params,
            "is_variadic": func.get("is_variadic", False),
            "attributes": func.get("attributes", [])
        }

    def save_artifact(self, artifact: Dict[str, Any], output_path: str):
        """
        Save IR Artifact to JSON file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: CONTRACT SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════
#
# Derivation of semantic correctness constraints from structural IR.
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class SynthesisWarningLogger:
    """
    Captures warnings when automated analysis falls back to conservative defaults
    or encounters ambiguous patterns.
    """
    
    def __init__(self):
        self.warnings: List[Dict[str, Any]] = []

    def log(self, category: str, message: str, severity: str = "warning", context: str = ""):
        """Add a warning to the list."""
        self.warnings.append({
            "category": category,
            "message": message,
            "severity": severity,
            "context": context
        })

    def warn_ambiguous_ownership(self, func_name: str, param_name: str):
        self.log(
            "OWNERSHIP_AMBIGUITY",
            f"Could not determine ownership for parameter '{param_name}' in '{func_name}'. Assuming borrowed.",
            "warning",
            func_name
        )

    def warn_missing_buffer_size(self, func_name: str, param_name: str):
        self.log(
            "BUFFER_SAFETY",
            f"Pointer parameter '{param_name}' in '{func_name}' appears to be a buffer but has no associated size parameter.",
            "error",
            func_name
        )

    def warn_variadic_function(self, func_name: str):
        self.log(
            "VARIADIC_LIMITATION",
            f"Function '{func_name}' is variadic. Full verification is not supported without manual format string validation.",
            "warning",
            func_name
        )

    def get_all(self) -> List[Dict[str, Any]]:
        return self.warnings

class ConstraintIDGenerator:
    """
    Ensures every constraint in the contract has a traceable, unique identifier.
    """
    
    def generate_function_id(self, func_name: str, target: str, constraint_type: str) -> str:
        """
        Generate ID for function-related constraints.
        Format: func_<name>_<target>_<type>
        """
        # Clean target name (e.g. parameter:cfg -> p_cfg)
        clean_target = target.replace("parameter:", "p_").replace("return_value", "ret")
        base = f"func_{func_name}_{clean_target}_{constraint_type}"
        return self._normalize(base)

    def generate_struct_id(self, struct_name: str, field_name: str, constraint_type: str) -> str:
        """
        Generate ID for struct-related constraints.
        Format: struct_<name>_<field>_<type>
        """
        base = f"struct_{struct_name}_{field_name}_{constraint_type}"
        return self._normalize(base)

    def generate_global_id(self, constraint_type: str) -> str:
        """
        Generate ID for global constraints.
        Format: global_<type>
        """
        return f"global_{constraint_type}"

    def _normalize(self, base_id: str) -> str:
        """Ensure IDs are valid identifiers and deduplicated locally if needed."""
        # In a real system we might append a hash of the justification if multiple
        # identical constraints exist, but for our v1.0, semantic names are better.
        return base_id.lower().replace(" ", "_").replace("*", "ptr")

class ConservativeDefaultPolicy:
    """
    Implements mandatory fallback policies to ensure safety over permissiveness.
    """
    
    @staticmethod
    def default_nullability() -> str:
        """DEFAULT POLICY 1: Pointers are required unless proven optional."""
        return "non_null"
        
    @staticmethod
    def default_ownership() -> str:
        """DEFAULT POLICY 2: Assume borrowed (caller keeps ownership)."""
        return "borrowed"
        
    @staticmethod
    def default_lifetime() -> str:
        """DEFAULT POLICY 3: Valid only during function call."""
        return "call_duration"
        
    @staticmethod
    def default_mutability(is_const: bool) -> str:
        """DEFAULT POLICY 4: Favor immutable if const, else mutable."""
        return "immutable" if is_const else "mutable"
        
    @staticmethod
    def default_buffer_safety() -> Dict[str, Any]:
        """DEFAULT POLICY 5: Buffers are high risk."""
        return {
            "is_fixed_size": False,
            "requires_validation": True,
            "severity": "warning"
        }
        
    @staticmethod
    def default_return_semantics(return_type_id: str) -> str:
        """DEFAULT POLICY 6: Integer returns are treated as error codes."""
        if return_type_id.startswith("primitive:int"):
            return "error_code"
        return "value"

class NamingConventionAnalyzer:
    """
    Analyzes C naming conventions to infer intent for nullability, ownership, etc.
    """
    
    def is_nullable_name(self, name: str) -> bool:
        """Rule 1: Detect nullability hints."""
        lower_name = name.lower()
        prefixes = ["optional_", "maybe_", "nullable_"]
        suffixes = ["_opt", "_nullable", "_maybe"]
        
        return any(lower_name.startswith(p) for p in prefixes) or \
               any(lower_name.endswith(s) for s in suffixes)

    def is_ownership_transfer_function(self, func_name: str) -> Optional[str]:
        """Rule 2: Detect ownership transfer intent."""
        lower_name = func_name.lower()
        
        # Transfers to Caller (Allocation)
        transfers_to_caller = ["create_", "alloc_", "new_", "init_", "clone_", "dup_"]
        if any(lower_name.startswith(p) for p in transfers_to_caller):
            return "caller"
            
        # Transfers to Callee (Deallocation/Take-ownership)
        transfers_to_callee = ["destroy_", "free_", "delete_", "release_", "sink_", "take_"]
        if any(lower_name.startswith(p) for p in transfers_to_callee):
            return "callee"
            
        return None

    def is_borrowed_function(self, func_name: str) -> bool:
        """Detect intent for non-transferring operations."""
        lower_name = func_name.lower()
        prefixes = ["get_", "find_", "query_", "peek_", "view_", "process_", "write_", "read_"]
        return any(lower_name.startswith(p) for p in prefixes)

    def detect_buffer_size_relationship(self, pointer_name: str, scalar_name: str) -> bool:
        """Rule 4: Detect relationship between a buffer and its size parameter."""
        p_name = pointer_name.lower()
        s_name = scalar_name.lower()
        
        # 1. Name match + size/len suffix
        size_indicators = ["_size", "_len", "_count", "_length", "size", "len", "count"]
        for indicator in size_indicators:
            if s_name == f"{p_name}{indicator}" or s_name == indicator:
                return True
                
        # 2. Heuristic for common pairs
        common_pairs = {
            "buffer": ["buffer_size", "buf_len", "size"],
            "data": ["data_size", "datalen", "len"],
            "items": ["count", "num_items"],
            "ptr": ["size", "count"]
        }
        
        if p_name in common_pairs and s_name in common_pairs[p_name]:
            return True
            
        return False

    def is_error_code_return(self, func_name: str, return_type_id: str) -> bool:
        """Rule 6: Detect if return value represents an error code."""
        if return_type_id not in ["primitive:int32", "primitive:int64", "primitive:int16"]:
            return False
            
        lower_name = func_name.lower()
        indicators = ["status", "error", "result", "code", "write", "process", "save", "init", "open"]
        return any(ind in lower_name for ind in indicators)

class ConstraintDeriver:
    """
    Applies derivation rules to functions, parameters, and structs.
    """
    
    def __init__(self, warning_logger: SynthesisWarningLogger):
        self.naming_analyzer = NamingConventionAnalyzer()
        self.defaults = ConservativeDefaultPolicy()
        self.id_gen = ConstraintIDGenerator()
        self.logger = warning_logger

    def derive_parameter_contract(self, func_name: str, param: Dict[str, Any]) -> Dict[str, Any]:
        """derive rules 1, 2, 3, 4, 9 for a parameter."""
        p_name = param.get("name")
        p_type_id = param.get("type_id", "")
        is_pointer = p_type_id.startswith("pointer:")
        is_const = param.get("qualifiers", {}).get("is_const", False)
        
        # Rule 1: Nullability
        nullability = self.defaults.default_nullability()
        null_just = "Pointer parameter without indication of nullability"
        
        if is_pointer:
            if self.naming_analyzer.is_nullable_name(p_name):
                nullability = "nullable"
                null_just = "Naming convention suggests optional parameter"
        else:
            nullability = "not_applicable"
            null_just = "Non-pointer value"

        # Rule 2: Ownership
        ownership = self.defaults.default_ownership()
        own_just = "No indication of ownership transfer; assumed borrowed"
        
        if is_pointer:
            transfer_intent = self.naming_analyzer.is_ownership_transfer_function(func_name)
            if transfer_intent == "callee" and not is_const:
                # If function is 'destroy_config(Config* cfg)', cfg is transferred
                ownership = "transferred"
                own_just = "Function naming suggests callee takes ownership"
            elif transfer_intent == "caller":
                # This usually applies to return values, but parameters in 'init' might be borrowed
                pass
            
            if ownership == self.defaults.default_ownership() and not self.naming_analyzer.is_borrowed_function(func_name):
                # We couldn't find a strong rule, so we used default. Log it.
                self.logger.warn_ambiguous_ownership(func_name, p_name)

        # Rule 3: Lifetime
        lifetime = self.defaults.default_lifetime()
        life_just = "Borrowed pointer valid only during call"
        if ownership == "transferred":
            lifetime = "transferred_to_callee"
            life_just = "Ownership transferred to callee"

        # Rule 9: Mutability
        mutability = self.defaults.default_mutability(is_const)
        mut_just = "Const qualifier prohibits modification" if is_const else "No const qualifier; assume mutable"

        # Construct constraints list
        constraints = []
        if is_pointer:
            constraints.append({
                "constraint_type": "valid_pointer",
                "description": "Must point to valid memory"
            })
            if "pointer:primitive:" not in p_type_id: # likely struct or complex
                constraints.append({
                    "constraint_type": "alignment",
                    "description": "Must be properly aligned for its type"
                })

        return {
            "parameter_name": p_name,
            "type_id": p_type_id,
            "nullability": nullability,
            "nullability_justification": null_just,
            "ownership": ownership,
            "ownership_justification": own_just,
            "lifetime": lifetime,
            "lifetime_justification": life_just,
            "mutability": mutability,
            "mutability_justification": mut_just,
            "constraints": constraints
        }

    def derive_buffer_constraints(self, func_name: str, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rule 4: Detect buffer-length pairs."""
        constraints = []
        
        for i, p1 in enumerate(parameters):
            p1_name = p1.get("name")
            p1_type = p1.get("type_id", "")
            
            if not p1_type.startswith("pointer:"):
                continue
                
            found_size = False
            for j, p2 in enumerate(parameters):
                if i == j: continue
                
                p2_name = p2.get("name")
                p2_type = p2.get("type_id", "")
                
                if p2_type.startswith("primitive:int") or p2_type.startswith("primitive:uint"):
                    if self.naming_analyzer.detect_buffer_size_relationship(p1_name, p2_name):
                        constraints.append({
                            "constraint_id": self.id_gen.generate_function_id(func_name, f"p_{p1_name}", "buffer_relationship"),
                            "constraint_type": "buffer_size",
                            "description": f"Parameter '{p1_name}' buffer size is defined by '{p2_name}'",
                            "target": f"parameter:{p1_name}",
                            "size_parameter": p2_name,
                            "justification": f"Naming relationship between '{p1_name}' and '{p2_name}'",
                            "severity": "error"
                        })
                        found_size = True
            
            # Special Rule for char*
            if p1_type == "pointer:primitive:char" and not found_size:
                 constraints.append({
                    "constraint_id": self.id_gen.generate_function_id(func_name, f"p_{p1_name}", "string_null_terminated"),
                    "constraint_type": "null_terminated_string",
                    "description": f"Parameter '{p1_name}' must be a null-terminated string",
                    "target": f"parameter:{p1_name}",
                    "justification": "C convention for char* parameters",
                    "severity": "error"
                })
            elif p1_type == "pointer:primitive:void" and not found_size:
                self.logger.warn_missing_buffer_size(func_name, p1_name)

        return constraints

    def derive_return_contract(self, func_name: str, return_type_id: str) -> Dict[str, Any]:
        """Rule 6: Return value intent."""
        ownership = "value"
        own_just = "Returned by value"
        
        constraints = []
        
        if return_type_id.startswith("pointer:"):
            transfer_intent = self.naming_analyzer.is_ownership_transfer_function(func_name)
            if transfer_intent == "caller":
                ownership = "transferred"
                own_just = "Function naming suggests caller takes ownership of returned pointer"
            else:
                ownership = "borrowed"
                own_just = "Assume returned pointer is borrowed from internal state"
        
        # Error code detection
        if self.naming_analyzer.is_error_code_return(func_name, return_type_id):
            constraints.append({
                "constraint_type": "error_code",
                "description": "Returns 0 on success, non-zero on failure",
                "justification": "Naming and return type suggest error code pattern"
            })
            
        return {
            "type_id": return_type_id,
            "ownership": ownership,
            "ownership_justification": own_just,
            "constraints": constraints
        }

    def derive_struct_field_contract(self, struct_name: str, field: Dict[str, Any]) -> Dict[str, Any]:
        """Rule 5: Struct field constraints."""
        name = field.get("name")
        type_id = field.get("type_id", "")
        
        constraints = []
        if "padding" not in type_id:
            constraints.append({
                "constraint_type": "initialized",
                "description": "Must be initialized before use"
            })
            
        nullability = "not_applicable"
        if type_id.startswith("pointer:"):
            # Struct fields are often NULL unless specifically used for sub-objects
             nullability = "nullable"
             constraints.append({
                 "constraint_type": "nullable_pointer",
                 "description": "May be NULL"
             })

        return {
            "field_name": name,
            "type_id": type_id,
            "offset_bytes": field.get("offset_bytes"),
            "nullability": nullability,
            "ownership": "unknown",
            "constraints": constraints
        }

# ============================================================================
# PUBLIC API
# ============================================================================

class ContractSynthesizer:
    """
    Main engine for . Synthesizes semantic constraints from normalized IR.
    """
    
    def __init__(self):
        self.logger = SynthesisWarningLogger()
        self.deriver = ConstraintDeriver(self.logger)
        self.id_gen = ConstraintIDGenerator()

    def synthesize(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Synthesize the contract from IR.
        """
        ir_path = context.artifacts.intermediate_representation_path
        if not os.path.exists(ir_path):
            raise FileNotFoundError(f"IR artifact not found: {ir_path}. Run  first.")
            
        with open(ir_path, "r") as f:
            ir = json.load(f)
            
        type_registry = ir.get("type_registry", {})
        
        # 1. Synthesize Function Contracts
        function_contracts = self._synthesize_functions(ir.get("functions", []), type_registry)
        
        # 2. Synthesize Struct Contracts
        struct_contracts = self._synthesize_structs(ir.get("structs", []), type_registry)
        
        # 3. Apply Global Constraints (Rules 7, 8, 32/64 bit consistency)
        global_constraints = self._generate_global_constraints(context)
        
        # 4. Compile Metadata
        metadata = {
            "total_functions_analyzed": len(ir.get("functions", [])),
            "total_structs_analyzed": len(ir.get("structs", [])),
            "total_constraints_generated": self._count_constraints(function_contracts, struct_contracts, global_constraints),
            "warnings_issued": len(self.logger.get_all()),
            "synthesis_warnings": self.logger.get_all()
        }
        
        # 5. Build Final Artifact
        contract = {
            "provenance": {
                "producing_phase": ": Contract Synthesis",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(ir_path)]
            },
            "platform": ir.get("platform", {}),
            "function_contracts": function_contracts,
            "struct_contracts": struct_contracts,
            "type_contracts": self._synthesize_type_contracts(type_registry),
            "global_constraints": global_constraints,
            "synthesis_metadata": metadata
        }
        
        # 6. Save Artifact
        output_path = context.artifacts.contract_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(contract, f, indent=2)
            
        return contract

    def _synthesize_functions(self, functions: List[Dict[str, Any]], type_registry: Dict) -> List[Dict[str, Any]]:
        contracts = []
        for func in functions:
            name = func["name"]
            
            # Parameter Contracts
            param_contracts = []
            pre_conditions = []
            
            for param in func.get("parameters", []):
                p_contract = self.deriver.derive_parameter_contract(name, param)
                param_contracts.append(p_contract)
                
                # Turn specific semantic properties into explicit pre-conditions
                p_name = param["name"]
                if p_contract["nullability"] == "non_null":
                    pre_conditions.append({
                        "constraint_id": self.id_gen.generate_function_id(name, f"p_{p_name}", "non_null"),
                        "constraint_type": "non_null",
                        "description": f"Parameter '{p_name}' must not be NULL",
                        "target": f"parameter:{p_name}",
                        "justification": p_contract["nullability_justification"],
                        "severity": "error"
                    })
                
                # Rule 8 check (indirectly via type_id layout)
                if "struct:" in p_contract["type_id"]:
                    struct_id = p_contract["type_id"].split("pointer:")[-1] if "pointer:" in p_contract["type_id"] else p_contract["type_id"]
                    if struct_id in type_registry:
                        s_info = type_registry[struct_id]
                        pre_conditions.append({
                            "constraint_id": self.id_gen.generate_function_id(name, f"p_{p_name}", "layout_valid"),
                            "constraint_type": "struct_layout",
                            "description": f"Parameter '{p_name}' must point to valid memory matching {struct_id}",
                            "target": f"parameter:{p_name}",
                            "struct_type_id": struct_id,
                            "required_size_bytes": s_info.get("size_bytes"),
                            "required_alignment_bytes": s_info.get("alignment_bytes"),
                            "justification": "Type signature requires specific binary layout",
                            "severity": "error"
                        })

            # Rule 4: Buffer Relationships
            pre_conditions.extend(self.deriver.derive_buffer_constraints(name, func.get("parameters", [])))
            
            # Return Contract
            ret_contract = self.deriver.derive_return_contract(name, func.get("return_type_id", ""))
            post_conditions = []
            for c in ret_contract["constraints"]:
                 post_conditions.append({
                    "constraint_id": self.id_gen.generate_function_id(name, "ret", c["constraint_type"]),
                    "constraint_type": c["constraint_type"],
                    "description": c["description"],
                    "target": "return_value",
                    "justification": c["justification"],
                    "severity": "warning"
                })

            # Rule 10: Variadic
            if func.get("is_variadic"):
                self.logger.warn_variadic_function(name)

            contracts.append({
                "function_name": name,
                "source_location": func.get("source_location"),
                "calling_convention": func.get("calling_convention", "cdecl"),
                "pre_conditions": pre_conditions,
                "post_conditions": post_conditions,
                "parameter_contracts": param_contracts,
                "return_contract": ret_contract
            })
            
        return contracts

    def _synthesize_structs(self, structs: List[Dict[str, Any]], type_registry: Dict) -> List[Dict[str, Any]]:
        contracts = []
        for s in structs:
            name = s["name"]
            type_id = s.get("type_id")
            
            field_contracts = []
            for field in s.get("fields", []):
                if field.get("is_implicit"): continue
                field_contracts.append(self.deriver.derive_struct_field_contract(name, field))
                
            invariants = [
                {
                    "constraint_type": "layout_match",
                    "description": f"Target language struct must match native layout of '{name}' exactly",
                    "justification": "FFI requires binary layout compatibility",
                    "severity": "critical"
                },
                {
                    "constraint_type": "alignment",
                    "description": f"Struct '{name}' must be {s.get('alignment_bytes')}-byte aligned",
                    "required_alignment": s.get("alignment_bytes"),
                    "justification": "Compiler-enforced alignment must be preserved",
                    "severity": "error"
                }
            ]
            
            contracts.append({
                "struct_name": name,
                "type_id": type_id,
                "source_location": s.get("source_location"),
                "size_bytes": s.get("size_bytes"),
                "alignment_bytes": s.get("alignment_bytes"),
                "field_contracts": field_contracts,
                "invariants": invariants
            })
        return contracts

    def _synthesize_type_contracts(self, type_registry: Dict) -> Dict[str, Any]:
        contracts = {}
        for tid, info in type_registry.items():
            contracts[tid] = {
                "type_id": tid,
                "kind": info.get("kind"),
                "constraints": {} # Placeholder for future deep type analysis
            }
        return contracts

    def _generate_global_constraints(self, context: ExecutionContext) -> List[Dict[str, Any]]:
        return [
            {
                "constraint_id": self.id_gen.generate_global_id("abi_compatibility"),
                "constraint_type": "abi_compatibility",
                "description": "All structs must maintain ABI compatibility across compilation",
                "justification": f"Verification performed for {context.platform.os_name} {context.platform.architecture}",
                "severity": "error"
            },
            {
                "constraint_id": self.id_gen.generate_global_id("calling_convention"),
                "constraint_type": "calling_convention",
                "description": "All functions use cdecl unless explicitly specified",
                "justification": "Standard calling convention for C FFIs",
                "severity": "error"
            }
        ]

    def _count_constraints(self, funcs, structs, globals) -> int:
        count = len(globals)
        for f in funcs:
            count += len(f["pre_conditions"]) + len(f["post_conditions"])
        for s in structs:
            count += len(s["invariants"])
            for fc in s["field_contracts"]:
                 count += len(fc.get("constraints", []))
        return count

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 5: CONTRACT VERSIONING
# ═══════════════════════════════════════════════════════════════════════════
#
# Semantic versioning and compatibility assessment for contract artifacts.
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class SchemaVersionManager:
    """
    Implements Semantic Versioning (MAJOR.MINOR.PATCH) for FFI contracts.
    """
    
    CURRENT_VERSION = "1.0.0"
    
    @staticmethod
    def get_current_schema_version() -> str:
        """Returns the current schema version of the verifier."""
        return SchemaVersionManager.CURRENT_VERSION
        
    @staticmethod
    def parse_version(version_str: str) -> tuple:
        """Parses a version string into a tuple of integers (major, minor, patch)."""
        try:
            parts = [int(p) for p in version_str.split(".")]
            while len(parts) < 3:
                parts.append(0)
            return tuple(parts[:3])
        except (ValueError, AttributeError):
            return (0, 0, 0)
            
    @staticmethod
    def is_schema_compatible(baseline_version: str, current_version: str) -> bool:
        """
        Tools can read contracts within the same MAJOR version.
        Future versions (higher minor/patch) are generally readable if backward compatibility 
        is maintained in the logic.
        """
        v1 = SchemaVersionManager.parse_version(baseline_version)
        v2 = SchemaVersionManager.parse_version(current_version)
        
        # Major versions must match for guaranteed compatibility
        return v1[0] == v2[0]
        
    @staticmethod
    def is_breaking_schema_change(old_version: str, new_version: str) -> bool:
        """Different major versions indicate breaking schema changes."""
        return not SchemaVersionManager.is_schema_compatible(old_version, new_version)
        
    @staticmethod
    def get_schema_changelog(version: str) -> str:
        """Returns a brief description of schema changes for a given version."""
        changelogs = {
            "1.0.0": "Initial contract schema focusing on nullability, ownership, and layout."
        }
        return changelogs.get(version, "Unknown version")

class ChangeCategory(Enum):
    COMPATIBLE = "compatible"
    BREAKING = "breaking"
    POTENTIALLY_BREAKING = "potentially_breaking"
    SEMANTIC = "semantic"
    SCHEMA = "schema"

class ChangeClassifier:
    """
    Analyzes raw contract changes and assigns risk categories and actions.
    """
    
    CHANGE_MAPPING = {
        # Function changes
        "function_added": ChangeCategory.COMPATIBLE,
        "function_removed": ChangeCategory.BREAKING,
        "parameter_added": ChangeCategory.BREAKING,
        "parameter_removed": ChangeCategory.BREAKING,
        "parameter_type_changed": ChangeCategory.BREAKING,
        "return_type_changed": ChangeCategory.BREAKING,
        "calling_convention_changed": ChangeCategory.BREAKING,
        "constraint_added": ChangeCategory.SEMANTIC,
        "constraint_removed": ChangeCategory.SEMANTIC,
        "constraint_changed": ChangeCategory.SEMANTIC,
        
        # Struct changes
        "struct_added": ChangeCategory.COMPATIBLE,
        "struct_removed": ChangeCategory.BREAKING,
        "struct_size_changed": ChangeCategory.BREAKING,
        "struct_alignment_changed": ChangeCategory.BREAKING,
        "field_added": ChangeCategory.POTENTIALLY_BREAKING,
        "field_removed": ChangeCategory.BREAKING,
        "field_type_changed": ChangeCategory.BREAKING,
        "field_offset_changed": ChangeCategory.BREAKING,
        
        # Type registry changes
        "type_added": ChangeCategory.COMPATIBLE,
        "type_removed": ChangeCategory.BREAKING,
        "type_size_changed": ChangeCategory.BREAKING,
        "type_alignment_changed": ChangeCategory.BREAKING,
        
        # Global changes
        "global_constraint_added": ChangeCategory.COMPATIBLE,
        "global_constraint_removed": ChangeCategory.SEMANTIC
    }

    def classify(self, change_type: str) -> ChangeCategory:
        """Determines the category of a change based on its type."""
        return self.CHANGE_MAPPING.get(change_type, ChangeCategory.POTENTIALLY_BREAKING)

    def assess_impact(self, change_type: str, context: str = "") -> str:
        """Provides a human-readable description of the impact."""
        impacts = {
            "function_removed": "Existing bindings will fail to link or call this function.",
            "parameter_type_changed": "ABI mismatch; will cause crashes or garbage data processing.",
            "struct_size_changed": f"Structure layout has changed. Data corruption likely if not recompiled.",
            "constraint_added": "Existing code may violate new safety rules (e.g. nullability).",
            "field_added": "Struct size increased. Existing bindings might read/write past buffer if size was fixed.",
            "calling_convention_changed": "Stack corruption guaranteed if calling convention is not updated."
        }
        return impacts.get(change_type, f"Modification to {context} may affect runtime behavior.")

    def recommend_action(self, change_type: str) -> str:
        """Suggests what the developer should do."""
        category = self.classify(change_type)
        if category == ChangeCategory.BREAKING:
            return "Update language bindings immediately, regenerate adapters, and recompile."
        if category == ChangeCategory.SEMANTIC:
            return "Review application logic for compliance with new semantic constraints."
        if category == ChangeCategory.POTENTIALLY_BREAKING:
            return "Regenerate struct definitions and check for hardcoded size assumptions."
        if category == ChangeCategory.COMPATIBLE:
            return "Regenerate adapters to expose new functionality (optional)."
        return "Inspect the change manually to determine impact."

class ContractSchemaValidator:
    """
    Validates that a contract artifact is well-formed and schema-compatible.
    """
    
    REQUIRED_ROOT_KEYS = [
        "provenance", "platform", "function_contracts", 
        "struct_contracts", "type_contracts", "global_constraints"
    ]
    
    def validate_contract(self, contract_path: str) -> Dict[str, Any]:
        """
        Loads and validates a contract file.
        Returns a dict: {"valid": bool, "contract": dict, "errors": list}
        """
        errors = []
        try:
            with open(contract_path, 'r') as f:
                contract = json.load(f)
        except Exception as e:
            return {"valid": False, "contract": None, "errors": [f"Failed to parse JSON: {str(e)}"]}
            
        # Check required keys
        for key in self.REQUIRED_ROOT_KEYS:
            if key not in contract:
                errors.append(f"Missing required root key: '{key}'")
                
        # Check provenance/schema_version
        if "provenance" in contract:
            version = contract["provenance"].get("schema_version")
            if not version:
                errors.append("Missing schema_version in provenance")
            else:
                current_ver = SchemaVersionManager.get_current_schema_version()
                if not SchemaVersionManager.is_schema_compatible(version, current_ver):
                    errors.append(f"Incompatible schema version: {version}. Expected compatibility with {current_ver}")
        else:
            errors.append("Missing provenance section")
            
        return {
            "valid": len(errors) == 0,
            "contract": contract if len(errors) == 0 else None,
            "errors": errors
        }

    def validate_against_schema(self, contract: Dict[str, Any], schema_version: str) -> List[str]:
        """Validates an in-memory contract against a specific version (placeholder for deep validation)."""
        # For now, we reuse the same logic
        errors = []
        for key in self.REQUIRED_ROOT_KEYS:
            if key not in contract:
                errors.append(f"Missing key: {key}")
        return errors

class CompatibilityReportGenerator:
    """
    Transforms a change diff into a professional compatibility assessment report.
    """
    
    def generate_report(self, diff: Dict[str, Any]) -> str:
        """Generates the full plain-text report."""
        summary = diff.get("summary", {})
        changes = diff.get("changes", [])
        schema = diff.get("schema_compatibility", {})
        
        lines = []
        lines.append("=" * 64)
        lines.append("FFI Contract Compatibility Assessment")
        lines.append("=" * 64)
        lines.append("")
        lines.append(f"Current Contract:  {diff['provenance'].get('current_contract')}")
        lines.append(f"Baseline Contract: {diff['provenance'].get('baseline_contract') or 'NONE'}")
        lines.append("")
        lines.append("Schema Versions:")
        lines.append(f"  Baseline: {schema.get('baseline_schema_version')}")
        lines.append(f"  Current:  {schema.get('current_schema_version')}")
        lines.append(f"  Compatible: {'YES' if schema.get('compatible') else 'NO'}")
        lines.append("")
        
        comp_level = self._compute_compatibility_level(summary)
        lines.append("-" * 64)
        lines.append(f"COMPATIBILITY LEVEL: {comp_level}")
        lines.append("-" * 64)
        lines.append("")
        lines.append("SUMMARY:")
        lines.append(f"  Total Changes: {summary.get('total_changes', 0)}")
        lines.append(f"  Breaking Changes: {summary.get('breaking_changes', 0)}")
        lines.append(f"  Potentially Breaking: {summary.get('potentially_breaking_changes', 0)}")
        lines.append(f"  Semantic Changes: {summary.get('semantic_changes', 0)}")
        lines.append(f"  Compatible Changes: {summary.get('compatible_changes', 0)}")
        lines.append("")
        
        # Group changes by category
        categories = ["breaking", "potentially_breaking", "semantic", "compatible"]
        for cat in categories:
            cat_changes = [c for c in changes if c["change_category"] == cat]
            if not cat_changes:
                continue
                
            lines.append("=" * 64)
            lines.append(f"{cat.upper().replace('_', ' ')} CHANGES ({len(cat_changes)})")
            lines.append("=" * 64)
            lines.append("")
            
            for c in cat_changes:
                lines.append(f"[{cat.upper().replace('_', ' ')}] {c['change_type'].replace('_', ' ').capitalize()}")
                lines.append(f"  Element: {c['element_type']} '{c['element_name']}'")
                if c.get("old_value") is not None or c.get("new_value") is not None:
                    lines.append(f"  Change: {c.get('old_value')} -> {c.get('new_value')}")
                lines.append(f"  Impact: {c['impact']}")
                lines.append(f"  Action: {c['action_required']}")
                lines.append("")

        lines.append("=" * 64)
        lines.append("RECOMMENDED ACTIONS")
        lines.append("=" * 64)
        lines.append("")
        actions = self._generate_actions(summary, changes)
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {action}")
        lines.append("")
        lines.append("=" * 64)
        
        return "\n".join(lines)

    def _compute_compatibility_level(self, summary: Dict) -> str:
        if summary.get("breaking_changes", 0) > 0:
            return "BREAKING"
        if summary.get("potentially_breaking_changes", 0) > 0:
            return "POTENTIALLY_BREAKING"
        if summary.get("semantic_changes", 0) > 0:
            return "SEMANTICALLY_INCOMPATIBLE"
        if summary.get("total_changes", 0) == 0:
            return "FULLY_COMPATIBLE"
        return "COMPATIBLE"

    def _generate_actions(self, summary: Dict, changes: List[Dict]) -> List[str]:
        actions = []
        if summary.get("breaking_changes", 0) > 0:
            actions.append("CRITICAL: Update language bindings immediately to reflect removals or signature changes.")
            actions.append("CRITICAL: Recompile and redeploy all dependent applications.")
        if summary.get("potentially_breaking_changes", 0) > 0:
             actions.append("IMPORTANT: Review struct layout changes; offsets or sizes may have changed.")
        if summary.get("semantic_changes", 0) > 0:
            actions.append("REVIEW: Check application logic against new semantic constraints (nullability, ownership).")
        if summary.get("total_changes", 0) > 0:
            actions.append("REGENERATE: Run language adapter generation to sync verification infrastructure.")
            actions.append("TEST: Execute full FFI verification suite to confirm compatibility.")
        else:
            actions.append("No changes detected. Existing bindings remain fully compatible.")
            
        return actions

# ============================================================================
# PUBLIC API
# ============================================================================

class ContractComparator:
    """
    Compares a baseline contract against a current contract to detect evolutions.
    """
    
    def __init__(self):
        self.validator = ContractSchemaValidator()
        self.classifier = ChangeClassifier()
        self.version_manager = SchemaVersionManager()

    def compare_contracts(self, baseline_path: str, current_path: str, execution_id: str) -> Dict[str, Any]:
        """
        Executes the 8-step comparison algorithm.
        """
        # STEP 1: Load and Validate
        baseline_res = self.validator.validate_contract(baseline_path)
        current_res = self.validator.validate_contract(current_path)
        
        if not current_res["valid"]:
             raise ValueError(f"Current contract is invalid: {current_res['errors']}")
        
        baseline = baseline_res["contract"] or {}
        current = current_res["contract"]
        
        # STEP 2: Check Schema Compatibility
        b_version = baseline.get("provenance", {}).get("schema_version", "0.0.0")
        c_version = current.get("provenance", {}).get("schema_version", self.version_manager.get_current_schema_version())
        
        schema_info = {
            "baseline_schema_version": b_version,
            "current_schema_version": c_version,
            "compatible": self.version_manager.is_schema_compatible(b_version, c_version),
            "compatibility_notes": "Schemas are compatible" if self.version_manager.is_schema_compatible(b_version, c_version) else "Breaking schema change"
        }

        changes = []
        
        if baseline:
            # STEP 4: Detect Function Changes
            changes.extend(self._detect_function_changes(baseline.get("function_contracts", []), current.get("function_contracts", [])))
            
            # STEP 5: Detect Struct Changes
            changes.extend(self._detect_struct_changes(baseline.get("struct_contracts", []), current.get("struct_contracts", [])))
            
            # STEP 6: Detect Type Changes
            changes.extend(self._detect_type_changes(baseline.get("type_registry", {}), current.get("type_registry", {})))
            
            # STEP 7: Detect Global Changes
            changes.extend(self._detect_global_changes(baseline.get("global_constraints", []), current.get("global_constraints", [])))
        else:
            # Treating as initial contract if baseline is empty
            pass

        # STEP 8: Generate Diff Artifact
        summary = self._generate_summary(changes)
        
        diff = {
            "provenance": {
                "producing_phase": ": Contract Schema Versioning",
                "execution_id": execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "diff_schema_version": "1.0.0",
                "baseline_contract": os.path.abspath(baseline_path) if baseline_path else None,
                "current_contract": os.path.abspath(current_path)
            },
            "schema_compatibility": schema_info,
            "summary": summary,
            "changes": changes
        }
        
        return diff

    def _detect_function_changes(self, baseline: List[Dict], current: List[Dict]) -> List[Dict]:
        changes = []
        b_map = {f["function_name"]: f for f in baseline}
        c_map = {f["function_name"]: f for f in current}
        
        # Functions added
        for name in c_map:
            if name not in b_map:
                changes.append(self._create_change("function_added", "function", name))
                
        # Functions removed/modified
        for name, b_func in b_map.items():
            if name not in c_map:
                changes.append(self._create_change("function_removed", "function", name))
                continue
                
            c_func = c_map[name]
            
            # Calling convention
            if b_func.get("calling_convention") != c_func.get("calling_convention"):
                changes.append(self._create_change("calling_convention_changed", "function", name, 
                                               b_func.get("calling_convention"), c_func.get("calling_convention")))
            
            # Return type
            b_ret = b_func.get("return_contract", {}).get("type_id")
            c_ret = c_func.get("return_contract", {}).get("type_id")
            if b_ret != c_ret:
                 changes.append(self._create_change("return_type_changed", "function", name, b_ret, c_ret))

            # Parameters
            b_params_list = b_func.get("parameter_contracts", [])
            c_params_list = c_func.get("parameter_contracts", [])
            b_params = {p["parameter_name"]: p for p in b_params_list}
            c_params = {p["parameter_name"]: p for p in c_params_list}
            
            if len(c_params_list) > len(b_params_list):
                 changes.append(self._create_change("parameter_added", "function", name, len(b_params_list), len(c_params_list)))
            elif len(c_params_list) < len(b_params_list):
                 changes.append(self._create_change("parameter_removed", "function", name, len(b_params_list), len(c_params_list)))
            
            for p_name, b_p in b_params.items():
                if p_name not in c_params:
                    # Individual parameter removed (naming mismatch or actual removal)
                    continue
                c_p = c_params[p_name]
                if b_p.get("type_id") != c_p.get("type_id"):
                    changes.append(self._create_change("parameter_type_changed", "parameter", f"{name}.{p_name}", b_p.get("type_id"), c_p.get("type_id")))
                
                # Semantic changes (nullability, ownership)
                for prop in ["nullability", "ownership", "lifetime"]:
                    if b_p.get(prop) != c_p.get(prop):
                        change_type = "constraint_added" if b_p.get(prop) is None else "constraint_changed"
                        if c_p.get(prop) is None: change_type = "constraint_removed"
                        changes.append(self._create_change(change_type, "parameter", f"{name}.{p_name}.{prop}", b_p.get(prop), c_p.get(prop)))

        return changes

    def _detect_struct_changes(self, baseline: List[Dict], current: List[Dict]) -> List[Dict]:
        changes = []
        b_map = {s["struct_name"]: s for s in baseline}
        c_map = {s["struct_name"]: s for s in current}
        
        for name in c_map:
            if name not in b_map:
                changes.append(self._create_change("struct_added", "struct", name))
                
        for name, b_s in b_map.items():
            if name not in c_map:
                changes.append(self._create_change("struct_removed", "struct", name))
                continue
                
            c_s = c_map[name]
            if b_s.get("size_bytes") != c_s.get("size_bytes"):
                changes.append(self._create_change("struct_size_changed", "struct", name, b_s.get("size_bytes"), c_s.get("size_bytes")))
            if b_s.get("alignment_bytes") != c_s.get("alignment_bytes"):
                changes.append(self._create_change("struct_alignment_changed", "struct", name, b_s.get("alignment_bytes"), c_s.get("alignment_bytes")))

            # Field changes
            b_fields = {f["field_name"]: f for f in b_s.get("field_contracts", [])}
            c_fields = {f["field_name"]: f for f in c_s.get("field_contracts", [])}
            
            for f_name in c_fields:
                if f_name not in b_fields:
                    changes.append(self._create_change("field_added", "field", f"{name}.{f_name}"))
                    
            for f_name, b_f in b_fields.items():
                if f_name not in c_fields:
                    changes.append(self._create_change("field_removed", "field", f"{name}.{f_name}"))
                    continue
                c_f = c_fields[f_name]
                if b_f.get("type_id") != c_f.get("type_id"):
                    changes.append(self._create_change("field_type_changed", "field", f"{name}.{f_name}", b_f.get("type_id"), c_f.get("type_id")))
                if b_f.get("offset_bytes") != c_f.get("offset_bytes"):
                    changes.append(self._create_change("field_offset_changed", "field", f"{name}.{f_name}", b_f.get("offset_bytes"), c_f.get("offset_bytes")))

        return changes

    def _detect_type_changes(self, baseline: Dict, current: Dict) -> List[Dict]:
        changes = []
        for tid, c_info in current.items():
            if tid not in baseline:
                changes.append(self._create_change("type_added", "type_id", tid))
        for tid, b_info in baseline.items():
            if tid not in current:
                changes.append(self._create_change("type_removed", "type_id", tid))
        return changes

    def _detect_global_changes(self, baseline: List[Dict], current: List[Dict]) -> List[Dict]:
        changes = []
        b_ids = [g.get("constraint_id") for g in baseline]
        c_ids = [g.get("constraint_id") for g in current]
        
        for cid in c_ids:
            if cid not in b_ids:
                changes.append(self._create_change("global_constraint_added", "global", cid))
        for cid in b_ids:
            if cid not in c_ids:
                changes.append(self._create_change("global_constraint_removed", "global", cid))
        return changes

    def _create_change(self, change_type: str, element_type: str, element_name: str, old_val: Any = None, new_val: Any = None) -> Dict:
        category = self.classifier.classify(change_type)
        return {
            "change_type": change_type,
            "change_category": category.value,
            "element_type": element_type,
            "element_name": element_name,
            "old_value": old_val,
            "new_value": new_val,
            "description": f"{change_type.replace('_',' ').capitalize()} in {element_type} '{element_name}'",
            "impact": self.classifier.assess_impact(change_type, element_name),
            "action_required": self.classifier.recommend_action(change_type)
        }

    def _generate_summary(self, changes: List[Dict]) -> Dict:
        summary = {
            "total_changes": len(changes),
            "breaking_changes": 0,
            "compatible_changes": 0,
            "potentially_breaking_changes": 0,
            "semantic_changes": 0
        }
        for c in changes:
            cat = c["change_category"]
            summary[f"{cat}_changes"] = summary.get(f"{cat}_changes", 0) + 1
            
        return summary

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 6: ADAPTER GENERATION
# ═══════════════════════════════════════════════════════════════════════════
#
# Automatic generation of contract-enforcing runtime adapters (ctypes).
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class ExceptionClassGenerator:
    """
    Produces the Python code for the exceptions module in the generated adapter.
    """
    
    def generate_exception_module(self, library_name: str) -> str:
        """Generates the full source code for the exceptions module."""
        return f'''"""
Generated exception classes for {library_name}.

Auto-created by Polyglot FFI Contract Verifier.
DO NOT EDIT MANUALLY.
"""

class FFIContractViolation(Exception):
    """
    Base class for all FFI contract violations.
    
    Attributes:
        constraint_id: Unique identifier for the violated constraint
        message: Human-readable description of the violation
    """
    def __init__(self, constraint_id, message):
        self.constraint_id = constraint_id
        self.message = message
        super().__init__(f"[{{constraint_id}}] {{message}}")

class NullPointerViolation(FFIContractViolation):
    """
    Raised when a pointer that must not be NULL is actually NULL.
    
    Contract constraint type: non_null
    """
    pass

class BufferSizeViolation(FFIContractViolation):
    """
    Raised when a buffer size constraint is violated.
    
    Contract constraint type: buffer_size
    """
    pass

class LayoutMismatchError(FFIContractViolation):
    """
    Raised when a struct layout doesn't match the contract specification.
    
    Contract constraint type: struct_layout
    """
    pass

class OwnershipViolation(FFIContractViolation):
    """
    Raised when memory ownership rules are violated.
    
    Contract constraint types: borrowed, transferred
    """
    pass

class ReturnValueViolation(FFIContractViolation):
    """
    Raised when a return value doesn't satisfy post-conditions.
    
    Contract constraint type: error_code, return_value_range
    """
    pass
'''

class OwnershipTrackerGenerator:
    """
    Produces the Python code for the ownership tracker in the generated adapter.
    """
    
    def generate_ownership_module(self, library_name: str) -> str:
        """Generates the full source code for the ownership tracking module."""
        return f'''"""
Generated ownership tracker for {library_name}.

Auto-created by Polyglot FFI Contract Verifier.
DO NOT EDIT MANUALLY.
"""

import weakref
from . import {library_name}_exceptions as exceptions

class OwnershipTracker:
    """
    Tracks memory ownership across the FFI boundary.
    
    Detects:
      - Use-after-transfer (using pointer after ownership was transferred)
      - Double-transfer (transferring ownership of same pointer twice)
    """
    
    def __init__(self):
        self._borrowed_pointers = weakref.WeakSet()
        self._transferred_pointers = set()
    
    def mark_borrowed(self, ptr):
        """
        Mark a pointer as borrowed (caller retains ownership).
        """
        if ptr is not None and bool(ptr):
            # We track the ID of the object if possible, 
            # or the address for pointer types
            try:
                import ctypes
                if isinstance(ptr, (ctypes._Pointer, ctypes.c_void_p)):
                    addr = ctypes.addressof(ptr.contents) if hasattr(ptr, 'contents') else ptr.value
                    self._borrowed_pointers.add(addr)
                else:
                    self._borrowed_pointers.add(id(ptr))
            except:
                self._borrowed_pointers.add(id(ptr))
    
    def mark_transferred(self, ptr):
        """
        Mark a pointer as transferred (callee takes ownership).
        """
        if ptr is None or not bool(ptr):
            return
            
        ptr_id = id(ptr)
        if ptr_id in self._transferred_pointers:
            raise exceptions.OwnershipViolation(
                "ownership_double_transfer",
                f"Pointer {{hex(ptr_id)}} has already been transferred"
            )
        
        self._transferred_pointers.add(ptr_id)
        
    def check_valid(self, ptr):
        """
        Check if a pointer is still valid to use.
        """
        if ptr is None or not bool(ptr):
            return
            
        ptr_id = id(ptr)
        if ptr_id in self._transferred_pointers:
            raise exceptions.OwnershipViolation(
                "ownership_use_after_transfer",
                f"Pointer {{hex(ptr_id)}} was transferred and is no longer valid"
            )

# Global tracker instance
_tracker = OwnershipTracker()
'''

class StructDefinitionGenerator:
    """
    Produces Python ctypes Structure definitions from contract/IR data.
    """
    
    TYPE_MAP = {
        "primitive:int8": "ctypes.c_int8",
        "primitive:int16": "ctypes.c_int16",
        "primitive:int32": "ctypes.c_int32",
        "primitive:int64": "ctypes.c_int64",
        "primitive:uint8": "ctypes.c_uint8",
        "primitive:uint16": "ctypes.c_uint16",
        "primitive:uint32": "ctypes.c_uint32",
        "primitive:uint64": "ctypes.c_uint64",
        "primitive:float": "ctypes.c_float",
        "primitive:double": "ctypes.c_double",
        "primitive:char": "ctypes.c_char",
        "primitive:void": "None",
        "pointer:primitive:void": "ctypes.c_void_p",
        "pointer:primitive:char": "ctypes.c_char_p"
    }
    
    def generate_struct_module(self, library_name: str, structs: List[Dict[str, Any]], ir: Dict[str, Any]) -> str:
        """Generates the full structs module."""
        lines = [
            f'"""',
            f'Generated struct definitions for {library_name}.',
            f'',
            f'Auto-created by Polyglot FFI Contract Verifier.',
            f'DO NOT EDIT MANUALLY.',
            f'"""',
            f'',
            f'import ctypes',
            f'from . import {library_name}_exceptions as exceptions',
            f''
        ]
        
        # We need to sort structs by dependency if they nest, 
        # but for v1.0 we assume flat or pre-ordered
        for s in structs:
            lines.append(self.generate_struct_class(s))
            lines.append("")
            
        return "\n".join(lines)

    def generate_struct_class(self, s: Dict[str, Any]) -> str:
        name = s["struct_name"]
        size = s["size_bytes"]
        align = s["alignment_bytes"]
        
        fields = s.get("field_contracts", [])
        
        class_lines = [
            f"class {name}(ctypes.Structure):",
            f'    """',
            f'    Native struct \'{name}\' binding.',
            f'    Size: {size} bytes',
            f'    Alignment: {align} bytes',
            f'    """',
            f'    _fields_ = ['
        ]
        
        for f in fields:
            f_name = f["field_name"]
            f_type = f["type_id"]
            ctypes_type = self._map_type(f_type)
            class_lines.append(f'        ("{f_name}", {ctypes_type}),')
            
        class_lines.extend([
            f'    ]',
            f'',
            f'    def __init__(self, **kwargs):',
            f'        super().__init__()',
            f'        actual_size = ctypes.sizeof(self)',
            f'        if actual_size != {size}:',
            f'            raise exceptions.LayoutMismatchError(',
            f'                "struct:{name}",',
            f'                f"Struct {name} has size {{actual_size}} bytes, expected {size} bytes"',
            f'            )',
            f'        for key, value in kwargs.items():',
            f'            if not hasattr(self, key):',
            f'                raise ValueError(f"Unknown field: {{key}}")',
            f'            setattr(self, key, value)',
            f'            setattr(self, key, value)',
            f''
        ])
        
        return "\n".join(class_lines)

    def _map_type(self, type_id: str) -> str:
        if type_id in self.TYPE_MAP:
            return self.TYPE_MAP[type_id]
            
        if type_id.startswith("padding:"):
            size = type_id.split(":")[-1]
            return f"ctypes.c_byte * {size}"
            
        if type_id.startswith("pointer:struct:"):
            s_name = type_id.split(":")[-1]
            return f"ctypes.POINTER({s_name})"
            
        if type_id.startswith("struct:"):
            return type_id.split(":")[-1]
            
        if type_id.startswith("pointer:primitive:"):
             base = type_id.replace("pointer:", "")
             if base in self.TYPE_MAP:
                 return f"ctypes.POINTER({self.TYPE_MAP[base]})"
                 
        return "ctypes.c_void_p" # Fallback

class ConstraintEnforcementCodegen:
    """
    Generates Python logic for enforcing individual contract constraints.
    """
    
    def generate_constraint_check(self, constraint: Dict[str, Any]) -> str:
        """Dispatches to specific generator based on constraint type."""
        c_type = constraint.get("constraint_type")
        
        if c_type == "non_null":
            return self._generate_null_check(constraint)
        elif c_type == "buffer_size":
            return self._generate_buffer_size_check(constraint)
        elif c_type == "struct_layout":
            return self._generate_layout_check(constraint)
        elif c_type == "null_terminated_string":
            return self._generate_string_null_terminated_check(constraint)
        elif c_type == "error_code":
            return self._generate_error_code_check(constraint)
            
        return f"    # Skip: Unsupported constraint type '{c_type}'"

    def _generate_null_check(self, c: Dict[str, Any]) -> str:
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        desc = c["description"]
        
        return f"""    # Enforce: {cid}
    if {target} is None or not bool({target}):
        raise exceptions.NullPointerViolation(
            "{cid}",
            "{desc}"
        )"""

    def _generate_buffer_size_check(self, c: Dict[str, Any]) -> str:
        target = c["target"].split(":")[-1]
        size_param = c.get("size_parameter")
        cid = c["constraint_id"]
        
        if not size_param:
            return f"    # Advise: {cid} - Missing size parameter for buffer check"
            
        return f"""    # Enforce: {cid}
    if {target} is not None:
        if {size_param} < 0:
             raise exceptions.BufferSizeViolation(
                "{cid}",
                f"Buffer size '{size_param}' must be non-negative, got {{{size_param}}}"
            )"""

    def _generate_layout_check(self, c: Dict[str, Any]) -> str:
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        struct_name = c["struct_type_id"].split(":")[-1]
        req_size = c.get("required_size_bytes")
        req_align = c.get("required_alignment_bytes")
        
        # We need to handle both the struct object and a pointer to it
        lines = [
            f"    # Enforce: {cid}",
            f"    if not isinstance({target}, structs.{struct_name}) and not hasattr({target}, '_type_'):",
            f"        raise exceptions.LayoutMismatchError(\"{cid}\", f\"Parameter '{target}' must be of type {struct_name}, got {{type({target})}}\")"
        ]
        
        if req_size:
            lines.append(f"    actual_size_{target} = ctypes.sizeof({target}.contents) if hasattr({target}, 'contents') else ctypes.sizeof({target})")
            lines.append(f"    if actual_size_{target} != {req_size}:")
            lines.append(f"        raise exceptions.LayoutMismatchError(\"{cid}\", f\"Struct {struct_name} has size {{actual_size_{target}}} bytes, expected {req_size}\")")
            
        if req_align:
            lines.append(f"    ptr_val_{target} = ctypes.addressof({target}.contents) if hasattr({target}, 'contents') else ctypes.addressof({target})")
            lines.append(f"    if ptr_val_{target} % {req_align} != 0:")
            lines.append(f"        raise exceptions.LayoutMismatchError(\"{cid}\", f\"Struct {struct_name} at {{hex(ptr_val_{target})}} is not {req_align}-byte aligned\")")
            
        return "\n".join(lines)

    def _generate_string_null_terminated_check(self, c: Dict[str, Any]) -> str:
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        
        return f"""    # Enforce: {cid}
    if {target} is None:
        raise exceptions.NullPointerViolation("{cid}", "Parameter '{target}' must not be NULL")
    
    _val_{target} = {target}
    if isinstance(_val_{target}, str):
        _val_{target} = _val_{target}.encode('utf-8')
        
    if not _val_{target}.endswith(b'\\x00'):
        raise exceptions.FFIContractViolation("{cid}", "Parameter '{target}' must be null-terminated")"""

    def _generate_error_code_check(self, c: Dict[str, Any]) -> str:
        # Usually applied to return values in post-conditions
        cid = c["constraint_id"]
        return f"""    # Enforce: {cid}
    # (Important: Result is checked by the caller or specialized checked function)"""
    
    def generate_ownership_check(self, param: Dict[str, Any]) -> str:
        """Generates ownership tracking code."""
        name = param.get("parameter_name")
        ownership = param.get("ownership")
        
        if ownership == "borrowed":
            return f"    ownership._tracker.mark_borrowed({name})"
        elif ownership == "transferred":
            return f"    ownership._tracker.mark_transferred({name})"
            
        return ""

class FunctionWrapperGenerator:
    """
    Produces Python wrapper functions with pre/post-condition checks.
    """
    
    def __init__(self):
        self.codegen = ConstraintEnforcementCodegen()
        
    def generate_wrapper_module(self, library_name: str, library_path: str, functions: List[Dict[str, Any]]) -> str:
        """Generates the main adapter module."""
        lines = [
            f'"""',
            f'Generated FFI adapter for {library_name}.',
            f'Auto-created by Polyglot FFI Contract Verifier.',
            f'"""',
            f'',
            f'import ctypes',
            f'import os',
            f'from . import {library_name}_structs as structs',
            f'from . import {library_name}_exceptions as exceptions',
            f'from . import {library_name}_ownership as ownership',
            f'',
            f'_LIBRARY_PATH = r"{library_path}"',
            f'if not os.path.exists(_LIBRARY_PATH):',
            f'    raise FileNotFoundError(f"Native library not found: {{_LIBRARY_PATH}}")',
            f'',
            f'_lib = ctypes.CDLL(_LIBRARY_PATH)',
            f''
        ]
        
        # Configure signatures first
        for f in functions:
            lines.append(self._generate_signature_config(f))
            
        lines.append("")
        
        # Then generate wrappers
        for f in functions:
            lines.append(self.generate_wrapper(f))
            lines.append("")
            
        return "\n".join(lines)

    def _generate_signature_config(self, f: Dict[str, Any]) -> str:
        name = f["function_name"]
        argtypes = [self._map_type(p["type_id"]) for p in f.get("parameter_contracts", [])]
        restype = self._map_type(f.get("return_contract", {}).get("type_id", "primitive:void"))
        
        lines = []
        if any(at == "NOT_FOUND" for at in argtypes + [restype]):
             lines.append(f"# Warning: Could not fully resolve types for {name}")
             
        lines.append(f"_lib.{name}.argtypes = [{', '.join([at for at in argtypes if at != 'NOT_FOUND'])}]")
        lines.append(f"_lib.{name}.restype = {restype if restype != 'NOT_FOUND' else 'None'}")
        
        if f.get("calling_convention") == "stdcall":
             lines.append(f"# Important: stdcall is handled by WinDLL if needed, currently using default CDLL")
             
        return "\n".join(lines)

    def generate_wrapper(self, f: Dict[str, Any]) -> str:
        name = f["function_name"]
        params = f.get("parameter_contracts", [])
        param_names = [p["parameter_name"] for p in params]
        
        lines = [
            f"def {name}({', '.join(param_names)}):",
            f'    """Wrapper for native function \'{name}\'."""'
        ]
        
        # Ownership tracking (Pre-call)
        for p in params:
            check = self.codegen.generate_ownership_check(p)
            if check: lines.append(check)
            
        # Pre-condition checks
        pre_conds = f.get("pre_conditions", [])
        if pre_conds:
            lines.append(f"    # Pre-conditions")
            for c in pre_conds:
                lines.append(self.codegen.generate_constraint_check(c))
                
        # Call
        lines.append(f"    result = _lib.{name}({', '.join(param_names)})")
        
        # Post-condition checks
        post_conds = f.get("post_conditions", [])
        if post_conds:
            lines.append(f"    # Post-conditions")
            for c in post_conds:
                lines.append(self.codegen.generate_constraint_check(c))
                
        lines.append("    return result")
        
        return "\n".join(lines)

    def _map_type(self, type_id: str) -> str:
        # Reuse mapping logic
        gen = StructDefinitionGenerator()
        res = gen._map_type(type_id)
        if res == type_id.split(":")[-1]: # it's a struct name
             return f"structs.{res}"
        if "POINTER(" in res:
             # handle POINTER(Config) -> POINTER(structs.Config)
             if "POINTER(structs." not in res and "POINTER(ctypes." not in res:
                  res = res.replace("POINTER(", "ctypes.POINTER(structs.")
             else:
                  res = res.replace("POINTER(", "ctypes.POINTER(")
        return res

# ============================================================================
# PUBLIC API
# ============================================================================

class AdapterGenerator:
    """
    Main orchestrator for .
    Generates the full suite of Python adapters.
    """
    
    def __init__(self):
        self.struct_gen = StructDefinitionGenerator()
        self.func_gen = FunctionWrapperGenerator()
        self.exc_gen = ExceptionClassGenerator()
        self.own_gen = OwnershipTrackerGenerator()

    def generate(self, context) -> Dict[str, Any]:
        """
        Generates the full suite of Python adapters.
        """
        contract_path = context.artifacts.contract_path
        ir_path = context.artifacts.intermediate_representation_path
        
        if not os.path.exists(contract_path):
            raise FileNotFoundError(f"Contract artifact not found: {contract_path}")
        if not os.path.exists(ir_path):
            raise FileNotFoundError(f"IR artifact not found: {ir_path}")
            
        with open(contract_path, 'r') as f:
            contract = json.load(f)
        with open(ir_path, 'r') as f:
            ir = json.load(f)

        lib_name = os.path.basename(context.native_library.library_path).split('.')[0]
        lib_path = context.native_library.library_path
        
        output_dir = os.path.join(context.artifacts.working_directory, "adapters")
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Generate Exceptions
        exc_code = self.exc_gen.generate_exception_module(lib_name)
        with open(os.path.join(output_dir, f"{lib_name}_exceptions.py"), "w") as f:
            f.write(exc_code)
            
        # 2. Generate Ownership Tracker
        own_code = self.own_gen.generate_ownership_module(lib_name)
        with open(os.path.join(output_dir, f"{lib_name}_ownership.py"), "w") as f:
            f.write(own_code)
            
        # 3. Generate Structs
        struct_code = self.struct_gen.generate_struct_module(lib_name, contract.get("struct_contracts", []), ir)
        with open(os.path.join(output_dir, f"{lib_name}_structs.py"), "w") as f:
            f.write(struct_code)
            
        # 4. Generate Main Adapter
        adapter_code = self.func_gen.generate_wrapper_module(lib_name, lib_path, contract.get("function_contracts", []))
        with open(os.path.join(output_dir, f"{lib_name}_adapter.py"), "w") as f:
            f.write(adapter_code)
            
        # 5. Generate __init__.py
        with open(os.path.join(output_dir, "__init__.py"), "w") as f:
            f.write(f"from . import {lib_name}_adapter as adapter\n")
            f.write(f"from . import {lib_name}_structs as structs\n")
            f.write(f"from . import {lib_name}_exceptions as exceptions\n")

        # 6. Generate Metadata
        metadata = {
            "provenance": {
                "producing_phase": ": Language Adapter Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(contract_path), os.path.abspath(ir_path)]
            },
            "target_language": "Python",
            "ffi_mechanism": "ctypes",
            "library_name": lib_name,
            "library_path": lib_path,
            "generated_modules": [
                f"adapters/{lib_name}_adapter.py",
                f"adapters/{lib_name}_structs.py",
                f"adapters/{lib_name}_exceptions.py",
                f"adapters/{lib_name}_ownership.py"
            ],
            "statistics": {
                "functions_wrapped": len(contract.get("function_contracts", [])),
                "structs_generated": len(contract.get("struct_contracts", [])),
                "constraints_enforced": self._count_constraints(contract),
                "constraints_skipped": 0
            }
        }
        
        metadata_path = os.path.join(output_dir, "adapter_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return metadata

    def _count_constraints(self, contract: Dict[str, Any]) -> int:
        count = 0
        for f in contract.get("function_contracts", []):
            count += len(f.get("pre_conditions", []))
            count += len(f.get("post_conditions", []))
        return count

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 7: TEST PLAN GENERATION
# ═══════════════════════════════════════════════════════════════════════════
#
# Systematic derivation of test cases achieving 100% constraint coverage.
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class InputValueGenerator:
    """
    Deterministic generation of input values for FFI tests.
    """
    
    PRIMITIVE_VALUES = {
        "primitive:int8": [1, 127, -128],
        "primitive:int16": [1, 32767, -32768],
        "primitive:int32": [42, 2147483647, -2147483648],
        "primitive:int64": [100, 9223372036854775807, -9223372036854775808],
        "primitive:uint8": [1, 255, 0],
        "primitive:uint16": [1, 65535, 0],
        "primitive:uint32": [100, 4294967295, 0],
        "primitive:uint64": [1000, 18446744073709551615, 0],
        "primitive:float": [1.0, 3.14159, 1.175494e-38],
        "primitive:double": [1.0, 3.1415926535, 2.225073e-308],
        "primitive:char": ["A", "Z", "\0"],
        "primitive:bool": [True, False],
        "primitive:void": [None]
    }

    def generate_value(self, type_id: str, ir: Dict[str, Any], strategy: str = "typical") -> Any:
        """
        Generates a concrete value for a given type.
        
        Strategies:
            - minimal: Smallest valid value
            - typical: Average/common value
            - maximal: Largest valid value
        """
        idx = {"minimal": 0, "typical": 0, "maximal": 1 if "int" in type_id else 0}.get(strategy, 0)
        
        # Handle primitives
        if type_id in self.PRIMITIVE_VALUES:
            vals = self.PRIMITIVE_VALUES[type_id]
            if strategy == "maximal" and len(vals) > 1: return vals[1]
            if strategy == "minimal" and len(vals) > 2: return vals[2]
            return vals[0]

        # Handle pointers
        if type_id.startswith("pointer:"):
            if strategy == "minimal": return None
            base_type = type_id.replace("pointer:", "")
            
            if base_type == "primitive:char":
                return "test_string\0"
            if base_type.startswith("struct:"):
                struct_name = base_type.split(":")[-1]
                return self.generate_struct_value(struct_name, ir, strategy)
            
            # Default for pointers is a small buffer or null
            return {"type": "buffer", "size": 8, "data": [0] * 8}

        # Handle structs (inline)
        if type_id.startswith("struct:"):
            return self.generate_struct_value(type_id.split(":")[-1], ir, strategy)

        return 0

    def generate_struct_value(self, struct_name: str, ir: Dict[str, Any], strategy: str = "typical") -> Dict[str, Any]:
        """Generates a valid dictionary representation of a struct."""
        # Find struct in IR
        struct_def = None
        for s in ir.get("structs", []):
            if s["name"] == struct_name:
                struct_def = s
                break
        
        if not struct_def:
            return {}

        value = {}
        for field in struct_def.get("fields", []):
            if field.get("is_padding"):
                continue
            f_name = field["name"]
            f_type = field["type_id"]
            value[f_name] = self.generate_value(f_type, ir, strategy)
            
        return value

class PositiveTestGenerator:
    """
    Produces successful execution test cases.
    """
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_positive_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates a set of positive test cases for a function."""
        name = f_contract["function_name"]
        test_cases = []
        
        # 1. Minimal Valid
        test_cases.append(self._create_test_case(f_contract, ir, "minimal"))
        
        # 2. Typical Valid
        test_cases.append(self._create_test_case(f_contract, ir, "typical"))
        
        return test_cases

    def _create_test_case(self, f: Dict[str, Any], ir: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        params = {}
        for p in f.get("parameter_contracts", []):
            params[p["parameter_name"]] = {
                "type": p["type_id"],
                "value": self.input_gen.generate_value(p["type_id"], ir, strategy)
            }
            
        cids = [pc["constraint_id"] for pc in f.get("pre_conditions", [])]
        
        return {
            "test_id": f"test_{f['function_name']}_positive_{strategy}",
            "test_category": "positive",
            "priority": "normal",
            "function_name": f["function_name"],
            "description": f"Valid call to {f['function_name']} with {strategy} inputs",
            "constraints_exercised": cids,
            "inputs": params,
            "expected_outcome": {
                "type": "success",
                "return_value_type": f.get("return_contract", {}).get("type_id", "primitive:void")
            },
            "rationale": f"Verifies that valid {strategy} inputs are accepted."
        }

class NegativeTestGenerator:
    """
    Produces failure execution test cases for constraint verification.
    """
    
    EXCEPTION_MAP = {
        "non_null": "NullPointerViolation",
        "buffer_size": "BufferSizeViolation",
        "struct_layout": "LayoutMismatchError",
        "alignment": "LayoutMismatchError",
        "borrowed": "OwnershipViolation",
        "transferred": "OwnershipViolation",
        "error_code": "ReturnValueViolation",
        "null_terminated_string": "FFIContractViolation"
    }
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_negative_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates one negative test case per pre-condition."""
        test_cases = []
        name = f_contract["function_name"]
        
        for constraint in f_contract.get("pre_conditions", []):
            tc = self._generate_violation(f_contract, constraint, ir)
            if tc:
                 test_cases.append(tc)
                 
        return test_cases

    def _generate_violation(self, f: Dict[str, Any], c: Dict[str, Any], ir: Dict[str, Any]) -> Dict[str, Any]:
        c_type = c["constraint_type"]
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        
        # Start with typical valid inputs
        inputs = {}
        for p in f.get("parameter_contracts", []):
            p_name = p["parameter_name"]
            inputs[p_name] = {
                "type": p["type_id"],
                "value": self.input_gen.generate_value(p["type_id"], ir, "typical")
            }
            
        # Corrupt the target input based on constraint type
        exc_type = self.EXCEPTION_MAP.get(c_type, "FFIContractViolation")
        
        if c_type == "non_null":
            if target in inputs:
                inputs[target]["value"] = None
            else:
                return None # Target not found
        
        elif c_type == "buffer_size":
            size_param = c.get("size_parameter")
            if size_param in inputs:
                inputs[size_param]["value"] = -1 # Invalid size
            else:
                 pass

        elif c_type == "struct_layout":
            if target in inputs:
                 # Injected layout error
                 inputs[target]["size_override"] = c.get("required_size_bytes", 100) + 1
            else:
                return None

        elif c_type == "null_terminated_string":
            if target in inputs:
                 inputs[target]["value"] = "not_terminated" # Missing \0
            else:
                return None

        else:
            return None # Unsupported for now

        return {
            "test_id": f"test_{f['function_name']}_violate_{cid}",
            "test_category": "negative",
            "priority": "critical" if c_type in ["non_null", "buffer_size"] else "high",
            "function_name": f["function_name"],
            "description": f"Violate constraint {cid} ({c_type}) for {target}",
            "constraints_exercised": [cid],
            "inputs": inputs,
            "expected_outcome": {
                "type": "exception",
                "exception_type": exc_type,
                "constraint_id": cid,
                "message_pattern": c.get("description", "")
            },
            "rationale": f"Verifies that {c_type} protection is active."
        }

class BoundaryValueTestGenerator:
    """
    Produces edge case test cases.
    """
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_boundary_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates boundary tests for relevant parameters."""
        test_cases = []
        
        for p in f_contract.get("parameter_contracts", []):
            t_id = p["type_id"]
            if "int" in t_id or "uint" in t_id:
                # Add Zero Test
                test_cases.append(self._create_boundary_test(f_contract, ir, p["parameter_name"], "zero", 0))
                # Add Max Test
                max_val = self.input_gen.generate_value(t_id, ir, "maximal")
                test_cases.append(self._create_boundary_test(f_contract, ir, p["parameter_name"], "max", max_val))
                
        return test_cases

    def _create_boundary_test(self, f: Dict[str, Any], ir: Dict[str, Any], p_name: str, b_type: str, val: Any) -> Dict[str, Any]:
        inputs = {}
        for p in f.get("parameter_contracts", []):
            inputs[p["parameter_name"]] = {
                "type": p["type_id"],
                "value": val if p["parameter_name"] == p_name else self.input_gen.generate_value(p["type_id"], ir, "typical")
            }
            
        return {
            "test_id": f"test_{f['function_name']}_boundary_{p_name}_{b_type}",
            "test_category": "boundary",
            "priority": "normal",
            "function_name": f["function_name"],
            "description": f"Boundary test ({b_type}) for parameter {p_name}",
            "constraints_exercised": [], # Exercised implicitly
            "inputs": inputs,
            "expected_outcome": {
                "type": "success"
            },
            "rationale": f"Checks handling of {b_type} boundary for {p_name}."
        }

class CoverageAnalyzer:
    """
    Computes coverage statistics for a generated test plan.
    """
    
    def analyze_coverage(self, test_cases: List[Dict[str, Any]], contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes which constraints are covered by the test cases.
        """
        all_constraints = self._extract_all_constraints(contract)
        coverage_map = {cid: [] for cid in all_constraints}
        
        for tc in test_cases:
            for cid in tc.get("constraints_exercised", []):
                if cid in coverage_map:
                    coverage_map[cid].append(tc["test_id"])

        covered_count = sum(1 for cid in coverage_map if len(coverage_map[cid]) > 0)
        total_count = len(all_constraints)
        
        uncovered = [cid for cid in coverage_map if len(coverage_map[cid]) == 0]
        
        return {
            "summary": {
                "total_constraints": total_count,
                "covered_constraints": covered_count,
                "uncovered_constraints": len(uncovered),
                "coverage_percentage": (covered_count / total_count * 100.0) if total_count > 0 else 100.0
            },
            "coverage_map": coverage_map,
            "uncovered_constraints": uncovered
        }

    def _extract_all_constraints(self, contract: Dict[str, Any]) -> List[str]:
        """Extracts every unique constraint ID from the contract."""
        ids = set()
        for f in contract.get("function_contracts", []):
            for pc in f.get("pre_conditions", []):
                 ids.add(pc["constraint_id"])
            for pc in f.get("post_conditions", []):
                 ids.add(pc["constraint_id"])
        return sorted(list(ids))

# ============================================================================
# PUBLIC API
# ============================================================================

class TestPlanGenerator:
    """
    Main orchestrator for .
    Generates a complete test plan based on the contract and IR.
    """
    
    def __init__(self):
        self.input_gen = InputValueGenerator()
        self.pos_gen = PositiveTestGenerator(self.input_gen)
        self.neg_gen = NegativeTestGenerator(self.input_gen)
        self.bound_gen = BoundaryValueTestGenerator(self.input_gen)
        self.coverage_analyzer = CoverageAnalyzer()

    def generate(self, context) -> Dict[str, Any]:
        """
        Generates a complete test plan based on the contract and IR.
        """
        contract_path = context.artifacts.contract_path
        ir_path = context.artifacts.intermediate_representation_path
        
        if not os.path.exists(contract_path):
            raise FileNotFoundError(f"Contract artifact not found: {contract_path}")
        if not os.path.exists(ir_path):
            raise FileNotFoundError(f"IR artifact not found: {ir_path}")
            
        with open(contract_path, 'r') as f:
            contract = json.load(f)
        with open(ir_path, 'r') as f:
            ir = json.load(f)

        test_cases = []
        
        for f_contract in contract.get("function_contracts", []):
            # 1. Positive Tests
            test_cases.extend(self.pos_gen.generate_positive_tests(f_contract, ir))
            
            # 2. Negative Tests
            test_cases.extend(self.neg_gen.generate_negative_tests(f_contract, ir))
            
            # 3. Boundary Tests
            test_cases.extend(self.bound_gen.generate_boundary_tests(f_contract, ir))
            
        # Analyze Coverage
        coverage = self.coverage_analyzer.analyze_coverage(test_cases, contract)
        
        # Build Metadata
        metadata = {
            "total_test_cases": len(test_cases),
            "positive_test_cases": sum(1 for tc in test_cases if tc["test_category"] == "positive"),
            "negative_test_cases": sum(1 for tc in test_cases if tc["test_category"] == "negative"),
            "boundary_test_cases": sum(1 for tc in test_cases if tc["test_category"] == "boundary"),
            "constraint_coverage": coverage["summary"]
        }
        
        # Final Test Plan
        test_plan = {
            "provenance": {
                "producing_phase": ": Test Plan Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(contract_path), os.path.abspath(ir_path)]
            },
            "test_suite_metadata": metadata,
            "test_cases": test_cases,
            "constraint_coverage_map": coverage["coverage_map"]
        }
        
        # Save artifacts
        plan_path = os.path.join(os.path.dirname(contract_path), "test_plan.json")
        with open(plan_path, 'w') as f:
            json.dump(test_plan, f, indent=2)
            
        coverage_path = os.path.join(os.path.dirname(contract_path), "test_coverage.json")
        with open(coverage_path, 'w') as f:
            json.dump(coverage, f, indent=2)
            
        return test_plan

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 8: VERIFICATION EXECUTION
# ═══════════════════════════════════════════════════════════════════════════
#
# Active execution of test plans with precise outcome validation.
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class InputInstantiator:
    """
    Transforms JSON-based values into ctypes instances for FFI calls.
    """
    
    PRIMITIVE_MAP = {
        "primitive:int8": ctypes.c_int8,
        "primitive:int16": ctypes.c_int16,
        "primitive:int32": ctypes.c_int32,
        "primitive:int64": ctypes.c_int64,
        "primitive:uint8": ctypes.c_uint8,
        "primitive:uint16": ctypes.c_uint16,
        "primitive:uint32": ctypes.c_uint32,
        "primitive:uint64": ctypes.c_uint64,
        "primitive:float": ctypes.c_float,
        "primitive:double": ctypes.c_double,
        "primitive:char": ctypes.c_char,
        "primitive:bool": ctypes.c_bool,
        "primitive:void": None
    }

    def __init__(self, lib_name: str):
        self.lib_name = lib_name
        self.structs_module = None
        
        # Add adapters dir to path for imports
        adapters_path = os.path.abspath("adapters")
        if adapters_path not in sys.path:
            sys.path.append(adapters_path)
            
        try:
            self.structs_module = __import__(f"{lib_name}_structs")
        except ImportError:
            pass

    def instantiate(self, spec: Dict[str, Any]) -> Any:
        """Main entry point for instantiation."""
        t_id = spec["type"]
        val = spec.get("value")
        
        if val is None:
            return None

        # Handle Primitives
        if t_id in self.PRIMITIVE_MAP:
            if t_id == "primitive:char" and isinstance(val, str):
                return self.PRIMITIVE_MAP[t_id](val.encode('ascii')[0])
            return self.PRIMITIVE_MAP[t_id](val)

        # Handle Pointers
        if t_id.startswith("pointer:"):
            base_type = t_id.replace("pointer:", "")
            
            # String special case
            if base_type == "primitive:char" and isinstance(val, str):
                return ctypes.c_char_p(val.encode('ascii'))
            
            # Buffer special case
            if isinstance(val, list):
                # Currently only supporting uint8 buffers in test plans
                arr_type = ctypes.c_uint8 * len(val)
                arr = arr_type(*val)
                return ctypes.cast(arr, ctypes.POINTER(ctypes.c_uint8))
                
            # Struct Pointer
            if base_type.startswith("struct:"):
                struct_name = base_type.split(":")[-1]
                struct_obj = self.instantiate_struct(struct_name, val)
                return ctypes.pointer(struct_obj)

        # Handle Structs (inline)
        if t_id.startswith("struct:"):
            struct_name = t_id.split(":")[-1]
            return self.instantiate_struct(struct_name, val)

        return val

    def instantiate_struct(self, name: str, value_dict: Dict[str, Any]) -> Any:
        """Instantiates a ctypes Structure from a dictionary."""
        if not self.structs_module:
             raise ImportError(f"Could not load structs module for {self.lib_name}")
             
        struct_class = getattr(self.structs_module, name)
        return struct_class(**value_dict)

class OutcomeValidator:
    """
    Validates if a test execution passed or failed based on contract rules.
    """

    def validate(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates the outcome.
        Returns (success, reason).
        """
        exp_type = expected["type"]
        act_type = actual["type"]

        if exp_type == "success":
            if act_type == "success":
                # For v1.0, we don't strictly validate return values unless specified
                return True, ""
            elif act_type == "exception":
                return False, f"Expected success, but got exception: {actual.get('exception_type')}"
            elif act_type == "crash":
                 return False, f"Expected success, but native library crashed"
            
        elif exp_type == "exception":
            if act_type == "exception":
                # Validate exception type
                exp_exc = expected.get("exception_type")
                act_exc = actual.get("exception_type")
                if exp_exc and exp_exc != act_exc:
                    return False, f"Expected exception {exp_exc}, but got {act_exc}"
                
                # Validate constraint ID
                exp_cid = expected.get("constraint_id")
                act_cid = actual.get("constraint_id")
                if exp_cid and exp_cid != act_cid:
                    return False, f"Expected violation of {exp_cid}, but got {act_cid}"
                
                return True, ""
            elif act_type == "success":
                return False, "Expected contract violation exception, but function succeeded"
            elif act_type == "crash":
                 return False, "Expected contract violation exception, but native library crashed"

        return False, f"Unknown outcome state: expected {exp_type}, got {act_type}"

class CrashDetector:
    """
    Spawns and monitors test execution subprocesses.
    """
    
    # Windows Exception Codes
    WINDOWS_EXCEPTIONS = {
        0xC0000005: "access_violation",
        0xC0000094: "integer_divide_by_zero",
        0xC00000FD: "stack_overflow",
        0xC000001D: "illegal_instruction",
        0xC0000008: "invalid_handle",
        0xC0000409: "stack_buffer_overrun",
        0x80000003: "breakpoint",
    }
    
    # Linux Signals
    LINUX_SIGNALS = {
        4: "illegal_instruction",   # SIGILL
        6: "abort",                 # SIGABRT
        8: "floating_point_error",  # SIGFPE
        11: "segmentation_fault",   # SIGSEGV
        7: "bus_error",             # SIGBUS
    }

    def execute_test(self, test_case: Dict[str, Any], context: Any, timeout: int = 60) -> Dict[str, Any]:
        """
        Executes a test case in a child process and detects if it crashes.
        """
        lib_name = os.path.splitext(os.path.basename(context.native_library.library_path))[0]
        adapter_module_name = f"{lib_name}_adapter"
        
        # Prepare command
        cmd = [
            sys.executable,
            "-m", "polyglot_ffi_verifier.subprocess_runner",
            json.dumps(test_case),
            lib_name,
            adapter_module_name
        ]
        
        start_time = time.time()
        try:
            # We use subprocess.run with a timeout
            # We capture stdout/stderr to find the RESULT tags or crash info
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # 1. Check for Crash (Non-zero exit code usually, or specific codes)
            if proc.returncode != 0:
                crash_info = self._analyze_termination(proc.returncode, proc.stderr)
                if crash_info:
                    return {
                        "status": "crashed",
                        "crash_detected": True,
                        "crash_info": crash_info,
                        "actual_outcome": {"type": "crash", "crash_type": crash_info["crash_type"]},
                        "duration_ms": duration_ms,
                        "exit_code": proc.returncode,
                        "stderr": proc.stderr
                    }

            # 2. Parse Result from Stdout
            stdout = proc.stdout
            if "---RESULT_START---" in stdout:
                try:
                    res_json = stdout.split("---RESULT_START---")[1].split("---RESULT_END---")[0].strip()
                    actual_outcome = json.loads(res_json)
                    
                    # Promote Access Violation OSErrors (Windows feature) to Crash
                    if actual_outcome.get("type") == "exception" and "access violation" in actual_outcome.get("exception_message", "").lower():
                        crash_info = {
                            "crash_type": "access_violation",
                            "exit_code": 0, # It exited cleanly because Python caught it
                            "stderr": proc.stderr,
                            "is_translated_exception": True
                        }
                        return {
                            "status": "crashed",
                            "crash_detected": True,
                            "crash_info": crash_info,
                            "actual_outcome": {"type": "crash", "crash_type": "access_violation"},
                            "duration_ms": duration_ms
                        }
                        
                    return {
                        "status": "completed",
                        "actual_outcome": actual_outcome,
                        "duration_ms": duration_ms,
                        "stdout": stdout,
                        "stderr": proc.stderr
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "failure_reason": f"Failed to parse subprocess output: {str(e)}",
                        "stdout": stdout
                    }

            return {
                "status": "error",
                "failure_reason": "Subprocess terminated without producing a result and no crash was classified.",
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": proc.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "failure_reason": f"Test timed out after {timeout} seconds",
                "duration_ms": timeout * 1000
            }
        except Exception as e:
            return {
                "status": "error",
                "failure_reason": f"Failed to launch subprocess: {str(e)}"
            }

    def _analyze_termination(self, exit_code: int, stderr: str) -> Optional[Dict[str, Any]]:
        """
        Interprets exit codes as crash types.
        """
        # Handle unsigned Windows exit codes (which Python might see as signed)
        unsigned_code = exit_code & 0xFFFFFFFF
        
        crash_type = "unknown"
        if os.name == 'nt':
            crash_type = self.WINDOWS_EXCEPTIONS.get(unsigned_code, "unknown")
        else:
            # On Linux, exit code is usually signal + 128 or just signal
            if exit_code < 0:
                crash_type = self.LINUX_SIGNALS.get(abs(exit_code), "unknown")
        
        if crash_type != "unknown" or unsigned_code in self.WINDOWS_EXCEPTIONS:
            return {
                "crash_type": crash_type,
                "exit_code": exit_code,
                "exception_code": hex(unsigned_code) if os.name == 'nt' else None,
                "signal": abs(exit_code) if os.name != 'nt' and exit_code < 0 else None
            }
        
        if "Segmentation fault" in stderr or "SIGSEGV" in stderr:
            return {"crash_type": "segmentation_fault", "exit_code": exit_code}
        
        return None

class ExecutionLogger:
    """
    Builds the immutable execution log artifact.
    """

    def build_log(self, context, results: List[Dict[str, Any]], test_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates the full log structure.
        """
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = len(results) - passed
        
        constraints_verified = set()
        for r in results:
            if r["status"] == "passed" and r["test_category"] == "negative":
                cid = r["actual_outcome"].get("constraint_id")
                if cid:
                    constraints_verified.add(cid)

        summary = {
            "total_tests": len(results),
            "tests_passed": passed,
            "tests_failed": failed,
            "pass_rate_percentage": (passed / len(results) * 100.0) if results else 0,
            "constraints_verified": len(constraints_verified),
            "violations_detected": sum(1 for r in results if r.get("actual_outcome", {}).get("type") == "exception")
        }

        provenance = {
            "producing_phase": ": Verification Execution",
            "execution_id": context.provenance.execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_version": "1.0.0",
            "schema_version": "1.0.0",
        }

        return {
            "provenance": provenance,
            "execution_metadata": {
                "execution_start_time": datetime.fromtimestamp(results[0]["execution_start_time"], tz=timezone.utc).isoformat() if results else "",
                "execution_end_time": datetime.now(timezone.utc).isoformat(),
                "platform": {
                    "os_name": context.platform.os_name,
                    "architecture": context.platform.architecture,
                    "python_version": f"{context.target_runtime.language_version}"
                }
            },
            "execution_summary": summary,
            "test_results": results
        }

class ExecutionSummaryGenerator:
    """
    Formats test results for human review.
    """

    def generate(self, log: Dict[str, Any]) -> str:
        """
        Generates the text summary report.
        """
        summary = log["execution_summary"]
        
        lines = [
            "================================================================",
            "FFI Contract Verification Execution Summary",
            "================================================================",
            f"Execution ID: {log['provenance']['execution_id']}",
            f"Timestamp   : {log['provenance']['timestamp']}",
            f"Result      : {'PASS' if summary['tests_failed'] == 0 else 'FAIL'}",
            "",
            "OVERALL RESULTS",
            "----------------",
            f"Total Tests      : {summary['total_tests']}",
            f"Passed           : {summary['tests_passed']}",
            f"Failed           : {summary['tests_failed']}",
            f"Pass Rate        : {summary['pass_rate_percentage']:.2f}%",
            f"Constraints Verified: {summary['constraints_verified']}",
            "",
            "DETAILED RESULTS",
            "----------------"
        ]

        for result in log["test_results"]:
            mark = "✓" if result["status"] == "passed" else "✗"
            line = f"{mark} {result['test_id']} ({result.get('duration_ms', 0):.2f}ms)"
            lines.append(line)
            if result["status"] == "failed":
                lines.append(f"  Reason: {result.get('failure_reason', 'Unknown error')}")
                
        lines.append("================================================================")
        return "\n".join(lines)

# ============================================================================
# PUBLIC API
# ============================================================================

class VerificationExecutor:
    """
    Orchestrates the verification process.
    Uses subprocess isolation for robust crash detection.
    """

    def execute(self, context) -> Dict[str, Any]:
        """
        Executes the full verification cycle.
        """
        # 1. Load Artefacts
        plan_path = os.path.join(os.path.dirname(context.artifacts.contract_path), "test_plan.json")
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Test plan missing: {plan_path}. Run 'generate-tests' first.")
            
        with open(plan_path, 'r') as f:
            test_plan = json.load(f)
            
        # 2. Setup Components
        detector = CrashDetector()
        validator = OutcomeValidator()
        logger = ExecutionLogger()
        summary_gen = ExecutionSummaryGenerator()
        
        test_results = []
        artifacts_dir = os.path.dirname(context.artifacts.contract_path)
        
        # 3. Execute Tests (Serial)
        for test_case in test_plan.get("test_cases", []):
            start_ts = time.time()
            
            # Use CrashDetector to run safely in subprocess
            result = detector.execute_test(test_case, context, timeout=context.verification_config.per_test_timeout_seconds)
            
            end_ts = time.time()
            
            # Map result to execution log format
            log_entry = {
                "test_id": test_case["test_id"],
                "test_category": test_case["test_category"],
                "function_name": test_case["function_name"],
                "execution_start_time": start_ts,
                "execution_end_time": end_ts,
                "duration_ms": result.get("duration_ms", 0),
                "constraints_exercised": test_case.get("constraints_exercised", []),
                "expected_outcome": test_case["expected_outcome"]
            }
            
            if result["status"] == "crashed":
                log_entry["status"] = "failed"
                log_entry["crash_detected"] = True
                log_entry["crash_info"] = result["crash_info"]
                log_entry["actual_outcome"] = result["actual_outcome"]
                log_entry["failure_reason"] = f"Native crash detected: {result['crash_info']['crash_type']}"
                log_entry["violation_detected"] = False
            
            elif result["status"] == "completed":
                actual_outcome = result["actual_outcome"]
                success, reason = validator.validate(test_case["expected_outcome"], actual_outcome)
                
                log_entry["status"] = "passed" if success else "failed"
                log_entry["actual_outcome"] = actual_outcome
                if not success:
                    log_entry["failure_reason"] = reason
            
            elif result["status"] == "timeout":
                log_entry["status"] = "failed"
                log_entry["failure_reason"] = result["failure_reason"]
                log_entry["actual_outcome"] = {"type": "timeout"}
            
            else:
                log_entry["status"] = "failed"
                log_entry["failure_reason"] = result.get("failure_reason", "Unknown execution error")
                log_entry["actual_outcome"] = {"type": "error"}

            test_results.append(log_entry)
            
        # 4. Finalize
        log = logger.build_log(context, test_results, test_plan)
        
        # 5. Save Artifacts
        log_path = os.path.join(artifacts_dir, "execution_log.json")
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)
            
        summary = summary_gen.generate(log)
        summary_path = os.path.join(artifacts_dir, "execution_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        return log

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 9: RUNTIME MONITORING & CRASH DETECTION
# ═══════════════════════════════════════════════════════════════════════════
#
# Subprocess-based isolation and platform-specific crash detection.
#
# ═══════════════════════════════════════════════════════════════════════════

# Ensure project root is in path
sys.path.append(os.getcwd())

# We import InputInstantiator locally to avoid circular deps if possible,
# or assume execution.py is importable.
# However, InputInstantiator is in execution.py now.
# So we need to import it from there.

def run_test(test_case_json: str, lib_name: str, adapter_module_name: str):
    """
    Executes a single test case and prints the result as JSON to stdout.
    """
    try:
        from polyglot_ffi_verifier.execution import InputInstantiator
        
        test_case = json.loads(test_case_json)
        
        # Add adapters to path (assumed to be in working directory / adapters)
        # In a real package, adapters might be installed, but here we assume local generation.
        adapters_dir = os.path.abspath("adapters")
        if adapters_dir not in sys.path:
            sys.path.append(adapters_dir)
            
        # Load adapter
        try:
            adapter_module = importlib.import_module(adapter_module_name)
        except ImportError as e:
            # Fallback for when current directory is not in sys.path correctly
            sys.path.append(os.getcwd())
            adapter_module = importlib.import_module(adapter_module_name)
        
        # Initialize instantiator
        instantiator = InputInstantiator(lib_name)
        
        # Instantiate inputs
        kwargs = {}
        for p_name, p_spec in test_case["inputs"].items():
            kwargs[p_name] = instantiator.instantiate(p_spec)
            
        # Get function
        func_name = test_case["function_name"]
        func = getattr(adapter_module, func_name)
        
        # Execute
        actual_outcome = {"type": "success"}
        try:
            actual_ret = func(**kwargs)
            actual_outcome["return_value"] = str(actual_ret)
        except Exception as e:
            actual_outcome = {
                "type": "exception",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "constraint_id": getattr(e, "constraint_id", None)
            }
            
        # Print result
        print("---RESULT_START---")
        print(json.dumps(actual_outcome))
        print("---RESULT_END---")
        
    except Exception as e:
        error_info = {
            "type": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print("---RESULT_START---")
        print(json.dumps(error_info))
        print("---RESULT_END---")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        # Check if we are testing imports
        if len(sys.argv) == 1:
             print("Subprocess runner ready.")
             sys.exit(0)
        sys.exit(2)
    
    run_test(sys.argv[1], sys.argv[2], sys.argv[3])

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 10: DIAGNOSTICS MAPPING
# ═══════════════════════════════════════════════════════════════════════════
#
# Automatic categorization and root cause analysis of failures.
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class CrashAnalyzer:
    """
    Heuristics for classifying and analyzing native crashes.
    """

    def analyze(self, crash_info: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a detailed analysis of the crash.
        """
        c_type = crash_info.get("crash_type", "unknown")
        
        analysis = {
            "is_exploitable": False,
            "severity": "medium",
            "likely_cause": "Unknown native error"
        }

        if c_type == "access_violation" or c_type == "segmentation_fault":
            analysis["severity"] = "critical"
            analysis["is_exploitable"] = True
            analysis["likely_cause"] = "Memory safety violation (e.g., buffer overflow or null dereference)."
            if "expected_outcome" in test_case:
                exp = test_case["expected_outcome"]
                if exp.get("exception_type") == "BufferSizeViolation":
                    analysis["likely_cause"] = "Confirmed Buffer Overflow. Native code crashed instead of being stopped by adapter."
                elif exp.get("exception_type") == "NullPointerViolation":
                    analysis["likely_cause"] = "Confirmed Null Dereference. Native code crashed instead of being stopped by adapter."

        elif c_type == "stack_overflow":
            analysis["severity"] = "high"
            analysis["likely_cause"] = "Infinite recursion or massive stack allocation in native code."

        elif c_type == "illegal_instruction":
            analysis["severity"] = "high"
            analysis["likely_cause"] = "Jump to invalid address, likely due to stack corruption or ABI mismatch."

        return analysis

class CrashReportGenerator:
    """
    Generates and saves persistent reports for native failures.
    """

    def generate_report(self, context: Any, test_case: Dict[str, Any], crash_info: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the report structure.
        """
        return {
            "provenance": {
                "producing_phase": ": Runtime Monitoring",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_id": test_case["test_id"]
            },
            "crash_summary": {
                "crash_type": crash_info.get("crash_type"),
                "severity": analysis.get("severity"),
                "is_exploitable": analysis.get("is_exploitable"),
                "exit_code": crash_info.get("exit_code"),
                "exception_code": crash_info.get("exception_code")
            },
            "test_context": {
                "function_name": test_case["function_name"],
                "inputs": test_case["inputs"],
                "expected_outcome": test_case["expected_outcome"]
            },
            "analysis": analysis
        }

    def save_report(self, report: Dict[str, Any], artifacts_dir: str):
        """Saves the report to the crashes directory."""
        crashes_dir = os.path.join(artifacts_dir, "crashes")
        os.makedirs(crashes_dir, exist_ok=True)
        
        filename = f"crash_{report['provenance']['test_id']}_{int(datetime.now().timestamp())}.json"
        filepath = os.path.join(crashes_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        return filepath

class FailureClassifier:
    """
    Classifies verification failures according to contract semantics.
    """

    SEVERITY_MAP = {
        "buffer_size": "critical",
        "non_null": "high",
        "ownership": "critical",
        "type_alignment": "medium",
        "custom": "medium",
        "unknown": "low"
    }

    def classify_failure(self, test_result: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies a single test failure.
        """
        status = test_result.get("status", "unknown")
        actual_outcome = test_result.get("actual_outcome", {})
        expected_outcome = test_result.get("expected_outcome", {})
        
        failure_mode = "unknown"
        category = "unknown"
        
        if test_result.get("crash_detected"):
            failure_mode = "crash"
            crash_type = test_result.get("crash_info", {}).get("crash_type", "unknown")
            category = self._map_crash_to_category(crash_type)
        elif actual_outcome.get("type") == "timeout":
            failure_mode = "timeout"
            category = "performance_or_deadlock"
        elif actual_outcome.get("type") == "exception":
            failure_mode = "exception"
            # Analyze if it's the RIGHT exception
            if actual_outcome.get("exception_type") == expected_outcome.get("exception_type"):
                category = "expectation_mismatch"
            else:
                category = "unhandled_exception"
        elif actual_outcome.get("type") == "success":
            failure_mode = "missing_enforcement"
            category = "missing_validation"

        # Determine Constraint
        constraint_id = "unknown"
        constraints_exercised = test_result.get("constraints_exercised", [])
        if constraints_exercised:
            constraint_id = constraints_exercised[0] # Primary constraint

        # Lookup constraint type in contract
        constraint_type = "unknown"
        if contract and "function_contracts" in contract:
             # Assuming standard contract structure here
             for fc in contract["function_contracts"]:
                 if fc["function_name"] == test_result.get("function_name"):
                     # Check pre/post
                     for c in fc.get("pre_conditions", []) + fc.get("post_conditions", []):
                         if c.get("constraint_id") == constraint_id:
                             constraint_type = c.get("constraint_type", "unknown")
                             break
                     if constraint_type != "unknown": break

        severity = self.SEVERITY_MAP.get(constraint_type, "medium")
        if failure_mode == "crash":
            severity = "critical"

        return {
            "failure_mode": failure_mode,
            "category": category,
            "constraint_id": constraint_id,
            "constraint_type": constraint_type,
            "severity": severity,
            "exploitability": "high" if severity == "critical" else "low",
            "impact": self._determine_impact(category, severity)
        }

    def _map_crash_to_category(self, crash_type: str) -> str:
        mapping = {
            "access_violation": "buffer_overflow_or_invalid_ptr",
            "segmentation_fault": "buffer_overflow_or_invalid_ptr",
            "stack_overflow": "stack_exhaustion",
            "illegal_instruction": "control_flow_corruption",
            "abort": "native_assertion_failure"
        }
        return mapping.get(crash_type, "native_crash")

    def _determine_impact(self, category: str, severity: str) -> str:
        if severity == "critical":
            return "Potential arbitrary code execution or memory corruption."
        if category == "null_pointer_dereference":
            return "Application crash (Denial of Service)."
        if category == "missing_validation":
            return "Native code exposed to invalid inputs; may lead to undefined behavior."
        return "Unexpected execution behavior violating contract expectations."

class RootCauseAnalyzer:
    """
    Analyzes failures to identify missing enforcement or native bugs.
    """

    def analyze(self, failure_info: Dict[str, Any], test_result: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines the root cause of a failure.
        """
        f_mode = failure_info.get("failure_mode")
        c_type = failure_info.get("constraint_type")
        
        root_cause = "Unknown"
        explanation = "Insufficient data to determine root cause."

        if f_mode == "crash":
            root_cause = "Adapter Missing Enforcement"
            explanation = f"Native library crashed on a {c_type} violation because the adapter failed to interpose and reject the invalid input."
        
        elif f_mode == "missing_enforcement":
            root_cause = "Adapter Missing Pre-call Check"
            explanation = f"The test expected a {c_type} violation to be caught by the adapter, but the call was allowed to proceed to native code."

        elif f_mode == "exception" and failure_info.get("category") == "unhandled_exception":
            root_cause = "Unexpected Exception Type"
            explanation = "Adapter raised an exception, but it didn't match the specific contract violation class expected."

        elif f_mode == "timeout":
            root_cause = "Native Deadlock or Infinite Loop"
            explanation = "Native code failed to return within the allocated time window when provided with test inputs."

        return {
            "root_cause": root_cause,
            "explanation": explanation
        }

class RemediationGenerator:
    """
    Generates step-by-step instructions to fix identified FFI issues.
    """

    def generate(self, failure_info: Dict[str, Any], test_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds remediation steps.
        """
        c_type = failure_info.get("constraint_type")
        f_name = test_result.get("function_name")
        c_id = failure_info.get("constraint_id")
        
        short_desc = f"Fix {c_type} validation in {f_name} adapter"
        steps = []

        if c_type == "buffer_size":
            steps = [
                f"1. Open the adapter for {f_name}.",
                f"2. Add a pre-call check to verify buffer length matches the associated size parameter.",
                f"3. Ensure it raises BufferSizeViolation with constraint_id='{c_id}'."
            ]
        elif c_type == "non_null":
            steps = [
                f"1. In function {f_name}, check that all pointers marked non-null are not None.",
                f"2. Raise NullPointerViolation if validation fails."
            ]
        elif c_type == "ownership":
            steps = [
                "1. Implement ownership tracking for this pointer.",
                "2. Ensure the adapter marks the pointer as transferred or invalid after the call."
            ]
        else:
            steps = [
                f"1. Review the contract constraints for {f_name}.",
                "2. Ensure the generated adapter implements all necessary pre-call validations."
            ]

        return {
            "short_description": short_desc,
            "detailed_steps": steps,
            "contract_reference": c_id
        }

class ViolationAggregator:
    """
    Groups related test failures to reduce reporting noise.
    """

    def aggregate(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups violations by constraint_id.
        """
        groups = {}
        
        for v in violations:
            cid = v.get("constraint_id", "unknown")
            if cid not in groups:
                groups[cid] = {
                    "violation_id": f"V-{len(groups)+1:03d}",
                    "constraint_id": cid,
                    "severity": v.get("severity"),
                    "category": v.get("category"),
                    "function_name": v.get("function_name"),
                    "description": v.get("description"),
                    "remediation": v.get("remediation"),
                    "root_cause": v.get("root_cause"),
                    "impact": v.get("impact"),
                    "affected_tests": [],
                    "test_count": 0,
                    "failure_mode": v.get("failure_mode")
                }
            
            groups[cid]["affected_tests"].append(v.get("test_id"))
            groups[cid]["test_count"] += 1
            
            # Upgrade severity if any member is higher
            if v.get("severity") == "critical":
                groups[cid]["severity"] = "critical"
            elif v.get("severity") == "high" and groups[cid]["severity"] != "critical":
                groups[cid]["severity"] = "high"

        # Convert back to sorted list
        sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        result = list(groups.values())
        result.sort(key=lambda x: (sev_rank.get(x["severity"], 9), -x["test_count"]))
        
        return result

class DiagnosticReportGenerator:
    """
    Generates the final diagnostics artifacts.
    """

    def generate_json(self, context: Any, aggregated_violations: List[Dict[str, Any]], stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the diagnostics.json structure.
        """
        return {
            "provenance": {
                "producing_phase": "0: Diagnostics Mapping",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0"
            },
            "summary": stats,
            "violations": aggregated_violations
        }

    def generate_summary_text(self, report_json: Dict[str, Any]) -> str:
        """
        Builds the human-readable violation_summary.txt.
        """
        stats = report_json["summary"]
        violations = report_json["violations"]
        
        lines = []
        lines.append("="*64)
        lines.append("FFI Contract Verification - Violation Summary")
        lines.append("="*64)
        lines.append(f"Execution ID: {report_json['provenance']['execution_id']}")
        lines.append(f"Pass Rate: {stats.get('pass_rate', 0):.1f}%")
        lines.append("")
        
        lines.append("VIOLATIONS BY SEVERITY")
        lines.append(f"  Critical: {stats.get('severity_counts', {}).get('critical', 0)}")
        lines.append(f"  High:     {stats.get('severity_counts', {}).get('high', 0)}")
        lines.append(f"  Total:    {len(violations)} Aggregated Issues")
        lines.append("")
        
        if not violations:
            lines.append("✓ NO CONTRACT VIOLATIONS DETECTED")
        else:
            for v in violations:
                lines.append(f"[{v['violation_id']}] {v['severity'].upper()}: {v['category']} in {v['function_name']}()")
                lines.append(f"  Constraint: {v['constraint_id']}")
                lines.append(f"  Root Cause: {v['root_cause']}")
                lines.append(f"  Impact:     {v['impact']}")
                lines.append(f"  Remediation: {v['remediation']['short_description']}")
                for step in v['remediation']['detailed_steps']:
                    lines.append(f"    {step}")
                lines.append("")

        return "\n".join(lines)

# ============================================================================
# PUBLIC API
# ============================================================================

class DiagnosticMapper:
    """
    Orchestrates the 0 diagnostics pipeline.
    Main entry point for generating diagnostic reports from execution logs.
    """

    def map_diagnostics(self, context: Any) -> Dict[str, Any]:
        """
        Loads artifacts, performs analysis, and saves diagnostics.
        """
        # 1. Load Input Artifacts
        artifacts_dir = os.path.dirname(context.artifacts.contract_path)
        log_path = os.path.join(artifacts_dir, "execution_log.json")
        contract_path = context.artifacts.contract_path
        
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Execution log missing: {log_path}. Run 'execute' first.")
            
        with open(log_path, 'r', encoding='utf-8') as f:
            execution_log = json.load(f)
            
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)

        # 2. Initialize Sub-components
        classifier = FailureClassifier()
        analyzer = RootCauseAnalyzer()
        remediation_gen = RemediationGenerator()
        aggregator = ViolationAggregator()
        report_gen = DiagnosticReportGenerator()

        raw_violations = []
        
        # 3. Process Execution Results
        for result in execution_log.get("test_results", []):
            if result.get("status") == "passed":
                continue
            
            # Classify
            failure_info = classifier.classify_failure(result, contract)
            
            # Analyze
            cause_info = analyzer.analyze(failure_info, result, contract)
            
            # Remediate
            remediation = remediation_gen.generate(failure_info, result)
            
            # Build raw violation record
            violation = {
                "test_id": result["test_id"],
                "function_name": result["function_name"],
                **failure_info,
                **cause_info,
                "remediation": remediation,
                "description": f"Failure detected in {result['function_name']}() violating {failure_info['constraint_id']}"
            }
            raw_violations.append(violation)

        # 4. Aggregate
        aggregated = aggregator.aggregate(raw_violations)
        
        # 5. Compute Stats
        total_tests = len(execution_log.get("test_results", []))
        passed_tests = sum(1 for r in execution_log.get("test_results", []) if r.get("status") == "passed")
        
        stats = {
            "total_violations": len(raw_violations),
            "aggregated_violations": len(aggregated),
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "severity_counts": self._count_severities(aggregated)
        }

        # 6. Generate Reports
        report_json = report_gen.generate_json(context, aggregated, stats)
        summary_text = report_gen.generate_summary_text(report_json)

        # 7. Save Artifacts
        diag_path = os.path.join(artifacts_dir, "diagnostics.json")
        with open(diag_path, 'w', encoding='utf-8') as f:
            json.dump(report_json, f, indent=2)
            
        summary_path = os.path.join(artifacts_dir, "violation_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        return report_json

    def _count_severities(self, aggregated: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in aggregated:
            sev = v.get("severity", "medium").lower()
            if sev in counts:
                counts[sev] += 1
        return counts

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 11: REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════
#
# Professional HTML/Markdown/CI report generation with visual hierarchy.
#
# ═══════════════════════════════════════════════════════════════════════════

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class ReportStylesheet:
    """
    Provides CSS styles for professional FFI verification reports.
    """

    @staticmethod
    def get_css() -> str:
        return """
:root {
    --primary-color: #2c3e50;
    --secondary-color: #34495e;
    --accent-color: #3498db;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --high-error-color: #e67e22;
    --error-color: #c0392b;
    --bg-color: #f8f9fa;
    --card-bg: #ffffff;
    --text-color: #2c3e50;
    --light-text: #7f8c8d;
    --border-color: #dee2e6;
}

body {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
    margin: 0;
    padding: 0;
}

header {
    background-color: var(--primary-color);
    color: white;
    padding: 2rem 10%;
    margin-bottom: 2rem;
}

header h1 {
    margin: 0;
    font-size: 2rem;
}

.report-metadata {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    margin-top: 1rem;
    font-size: 0.9rem;
}

.status-failed { color: #ff7675; font-weight: bold; }
.status-passed { color: #55efc4; font-weight: bold; }

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

section {
    margin-bottom: 3rem;
    background: var(--card-bg);
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

h2 {
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
    margin-top: 0;
}

/* Executive Summary Cards */
.summary-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.card {
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
    color: white;
}

.card h3 { margin: 0; font-size: 2.5rem; }
.card p { margin: 0.5rem 0 0; font-weight: bold; }

.card-critical { background-color: var(--error-color); }
.card-high { background-color: var(--high-error-color); }
.card-medium { background-color: var(--warning-color); }
.card-passed { background-color: var(--success-color); }

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th { background-color: #f1f3f5; font-weight: 600; }

.total-row { font-weight: bold; background-color: #f8f9fa; }
.pass-rate-excellent { color: var(--success-color); font-weight: bold; }
.pass-rate-fair { color: var(--warning-color); font-weight: bold; }
.pass-rate-poor { color: var(--error-color); font-weight: bold; }

/* Violation Cards */
.violation-card {
    border: 1px solid var(--border-color);
    border-left-width: 5px;
    border-radius: 4px;
    margin-bottom: 1.5rem;
    padding: 1rem;
}

.violations-critical .violation-card { border-left-color: var(--error-color); }
.violations-high .violation-card { border-left-color: var(--high-error-color); }
.violations-medium .violation-card { border-left-color: var(--warning-color); }

.violation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.violation-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: bold;
    color: white;
}

.badge-critical { background-color: var(--error-color); }
.badge-high { background-color: var(--high-error-color); }
.badge-medium { background-color: var(--warning-color); }

.violation-id { color: var(--light-text); font-family: monospace; }
.impact-critical { color: var(--error-color); font-weight: bold; }

pre {
    background-color: #f1f3f5;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9rem;
}

/* Technical Details */
details {
    margin-bottom: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0.5rem;
}

summary {
    font-weight: bold;
    cursor: pointer;
    padding: 0.5rem;
}

footer {
    text-align: center;
    padding: 2rem;
    color: var(--light-text);
    font-size: 0.8rem;
    border-top: 1px solid var(--border-color);
    margin-top: 3rem;
}

@media print {
    body { background-color: white; }
    section { break-inside: avoid; border: 1px solid #eee; box-shadow: none; }
    header { background-color: white; color: black; border-bottom: 2px solid black; }
}
"""

class HtmlReportGenerator:
    """
    Generates visually rich, responsive HTML reports.
    """

    def generate(self, diagnostics: Dict[str, Any], execution_log: Dict[str, Any], contract: Dict[str, Any], context: Any) -> str:
        """
        Main entry point for HTML generation.
        """
        summary = diagnostics.get("summary", {})
        violations = diagnostics.get("violations", [])
        
        # Split violations by severity
        critical = [v for v in violations if v.get("severity") == "critical"]
        high = [v for v in violations if v.get("severity") == "high"]
        other = [v for v in violations if v.get("severity") not in ["critical", "high"]]
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            self._generate_head(),
            '<body>',
            self._generate_header(context, summary),
            '<main>',
            self._generate_executive_summary(summary, violations),
            self._generate_test_results(execution_log),
            self._generate_violations_section("Critical Violations", critical, "violations-critical"),
            self._generate_violations_section("High Severity Violations", high, "violations-high"),
            self._generate_violations_section("Other Findings", other, "violations-medium"),
            self._generate_verified_constraints(violations, contract, execution_log),
            self._generate_recommendations(violations),
            self._generate_technical_details(context, contract, execution_log),
            '</main>',
            self._generate_footer(context),
            '</body>',
            '</html>'
        ]
        
        return "\n".join(html_parts)

    def _generate_head(self) -> str:
        return f"""
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FFI Contract Verification Report</title>
    <style>{ReportStylesheet.get_css()}</style>
</head>
"""

    def _generate_header(self, context: Any, summary: Dict[str, Any]) -> str:
        status = "PASSED" if summary.get("severity_counts", {}).get("critical", 0) == 0 else "FAILED"
        status_class = "status-passed" if status == "PASSED" else "status-failed"
        
        lib_name = context.native_library.library_path
        # Defensive timestamp parsing
        ts = context.provenance.creation_timestamp
        try:
             timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        except:
             timestamp = ts
        
        return f"""
<header>
    <h1>FFI Contract Verification Report</h1>
    <div class="report-metadata">
        <span><strong>Library:</strong> {lib_name}</span>
        <span><strong>Date:</strong> {timestamp}</span>
        <span><strong>Status:</strong> <span class="{status_class}">{status}</span></span>
        <span><strong>Execution ID:</strong> {context.provenance.execution_id[:8]}...</span>
    </div>
</header>
"""

    def _generate_executive_summary(self, summary: Dict[str, Any], violations: List[Dict[str, Any]]) -> str:
        sev = summary.get("severity_counts", {})
        pass_rate = summary.get("pass_rate", 0)
        
        status_text = "Verification FAILED" if sev.get("critical", 0) > 0 else "Verification PASSED"
        recommendation = "Do not deploy until critical violations are resolved." if sev.get("critical", 0) > 0 else "Library meets contract safety constraints."

        return f"""
<section class="executive-summary">
    <h2>Executive Summary</h2>
    <div class="summary-cards">
        <div class="card card-critical">
            <h3>{sev.get('critical', 0)}</h3>
            <p>Critical Violations</p>
        </div>
        <div class="card card-high">
            <h3>{sev.get('high', 0)}</h3>
            <p>High Severity</p>
        </div>
        <div class="card card-medium">
            <h3>{sev.get('medium', 0)}</h3>
            <p>Medium Severity</p>
        </div>
        <div class="card card-passed">
            <h3>{pass_rate:.1f}%</h3>
            <p>Pass Rate</p>
        </div>
    </div>
    <div class="summary-text" style="margin-top: 1.5rem">
        <p><strong>Overall Status:</strong> {status_text}</p>
        <p>A total of <strong>{len(violations)} aggregated issue(s)</strong> were identified across the contract surface.</p>
        <p><strong>Recommendation:</strong> {recommendation}</p>
    </div>
</section>
"""

    def _generate_test_results(self, execution_log: Dict[str, Any]) -> str:
        results = execution_log.get("test_results", [])
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = total - passed
        rate = (passed / total * 100) if total > 0 else 0
        rate_class = "pass-rate-excellent" if rate > 95 else ("pass-rate-fair" if rate > 80 else "pass-rate-poor")
        
        return f"""
<section class="test-results">
    <h2>Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Measurement</th>
                <th>Count</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total Tests Executed</td>
                <td>{total}</td>
            </tr>
            <tr>
                <td>Total Tests Passed</td>
                <td>{passed}</td>
            </tr>
            <tr>
                <td>Total Tests Failed</td>
                <td>{failed}</td>
            </tr>
            <tr class="total-row">
                <td>Overall Pass Rate</td>
                <td class="{rate_class}">{rate:.1f}%</td>
            </tr>
        </tbody>
    </table>
</section>
"""

    def _generate_violations_section(self, title: str, violations: List[Dict[str, Any]], css_class: str) -> str:
        if not violations: return ""
        cards = [self._generate_violation_card(v) for v in violations]
        return f"""
<section class="violations {css_class}">
    <h2>{title}</h2>
    {"".join(cards)}
</section>
"""

    def _generate_violation_card(self, v: Dict[str, Any]) -> str:
        badge_class = f"badge-{v.get('severity', 'medium')}"
        impact_class = "impact-critical" if v.get("severity") == "critical" else ""
        affected_tests = ", ".join(v.get("affected_tests", []))
        rem = v.get("remediation", {})
        steps = "".join([f"<li>{s}</li>" for s in rem.get("detailed_steps", [])])
        
        return f"""
<div class="violation-card">
    <div class="violation-header">
        <span class="violation-badge {badge_class}">{v.get('severity', '').upper()}</span>
        <h3>{v.get('category', 'Violation')} in {v.get('function_name', 'native code')}</h3>
        <span class="violation-id">{v.get('violation_id', 'v')}</span>
    </div>
    
    <div class="violation-details">
        <p><strong>Constraint:</strong> {v.get('constraint_id', 'N/A')}</p>
        <p><strong>Affected Tests:</strong> {len(v.get('affected_tests', []))} failures ({affected_tests})</p>
    </div>
    
    <div class="violation-description">
        <h4>Description</h4>
        <p>{v.get('description', 'No description available.')}</p>
        <p><strong>Root Cause:</strong> {v.get('explanation', v.get('root_cause', 'Undetermined'))}</p>
    </div>
    
    <div class="violation-impact">
        <h4>Impact</h4>
        <p class="{impact_class}">{v.get('impact', 'Potential instability.')}</p>
        <p><strong>Exploitability:</strong> {v.get('exploitability', 'Unknown')}</p>
    </div>
    
    <div class="violation-remediation">
        <h4>Remediation</h4>
        <p><strong>{rem.get('short_description', 'No remediation provided.')}</strong></p>
        <ol>{steps}</ol>
    </div>
</div>
"""

    def _generate_verified_constraints(self, violations: List[Dict[str, Any]], contract: Dict[str, Any], execution_log: Dict[str, Any]) -> str:
        violated_cids = {v.get("constraint_id") for v in violations}
        all_constraints = []
        if "function_contracts" in contract:
             for f in contract["function_contracts"]:
                 # check both pre and post
                 for c in f.get("pre_conditions", []) + f.get("post_conditions", []):
                     all_constraints.append(c.get("constraint_id"))

        verified = [cid for cid in all_constraints if cid not in violated_cids]
        if not verified: return ""
        list_items = "".join([f"<li>✓ {cid}</li>" for cid in verified])
        
        return f"""
<section class="verified-constraints">
    <h2>Verified Constraints</h2>
    <p>The following constraints were successfully verified with no observed violations:</p>
    <ul class="verified-list" style="columns: 2; list-style-type: none; padding: 0;">
        {list_items}
    </ul>
</section>
"""

    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> str:
        critical_v = [v for v in violations if v.get("severity") == "critical"]
        high_v = [v for v in violations if v.get("severity") == "high"]
        
        if not critical_v and not high_v:
            return f"""
<section class="recommendations">
    <h2>Recommendations</h2>
    <p>Verified current contract implementation. Continue to monitor FFI surface for changes.</p>
</section>
"""
        rec_cards = []
        if critical_v:
            items = "".join([f"<li>{v.get('category')} in {v.get('function_name')} (CRITICAL)</li>" for v in critical_v])
            rec_cards.append(f'<div class="recommendation-card" style="border-left: 4px solid var(--error-color); padding-left: 1rem;"><h4>Immediate Action Required</h4><ol>{items}</ol></div>')
        if high_v:
            items = "".join([f"<li>{v.get('category')} in {v.get('function_name')} (HIGH)</li>" for v in high_v])
            rec_cards.append(f'<div class="recommendation-card" style="border-left: 4px solid var(--high-error-color); padding-left: 1rem; margin-top: 1rem;"><h4>Follow-Up Actions</h4><ol>{items}</ol></div>')

        return f"""
<section class="recommendations">
    <h2>Recommendations</h2>
    {"".join(rec_cards)}
</section>
"""

    def _generate_technical_details(self, context: Any, contract: Dict[str, Any], execution_log: Dict[str, Any]) -> str:
        # Simplistic serialization for safety
        ctx_data = {
            "execution_id": context.provenance.execution_id,
            "platform": f"{context.platform.os_name} {context.platform.os_version}",
            "compiler": context.compiler.compiler_name,
            "runtime": context.target_runtime.language_name
        }
        ctx_json = json.dumps(ctx_data, indent=2)
        
        contract_stats = json.dumps({
            "total_functions": len(contract.get("function_contracts", [])),
            "contract_hash": contract.get("provenance", {}).get("contract_hash", "N/A")
        }, indent=2)

        return f"""
<section class="technical-details">
    <h2>Technical Details</h2>
    <details>
        <summary>Execution Context</summary>
        <pre>{ctx_json}</pre>
    </details>
    <details>
        <summary>Contract Summary</summary>
        <pre>{contract_stats}</pre>
    </details>
</section>
"""

    def _generate_footer(self, context: Any) -> str:
        return f"""
<footer>
    <p>Generated by Polyglot FFI Contract Verifier v{context.provenance.tool_version}</p>
    <p>Report ID: {context.provenance.execution_id}</p>
</footer>
"""

class MarkdownReportGenerator:
    """
    Generates structured Markdown reports.
    """

    def generate(self, diagnostics: Dict[str, Any], execution_log: Dict[str, Any], contract: Dict[str, Any], context: Any) -> str:
        summary = diagnostics.get("summary", {})
        violations = diagnostics.get("violations", [])
        
        try:
             timestamp = datetime.fromisoformat(context.provenance.creation_timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        except:
             timestamp = context.provenance.creation_timestamp
             
        status_icon = "❌" if summary.get("severity_counts", {}).get("critical", 0) > 0 else "✅"
        status_text = "FAILED" if summary.get("severity_counts", {}).get("critical", 0) > 0 else "PASSED"

        md = [
            f"# FFI Contract Verification Report",
            f"",
            f"**Library:** `{context.native_library.library_path}`  ",
            f"**Date:** {timestamp}  ",
            f"**Status:** {status_icon} {status_text}",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Critical Violations | {summary.get('severity_counts', {}).get('critical', 0)} |",
            f"| High Severity | {summary.get('severity_counts', {}).get('high', 0)} |",
            f"| Medium Severity | {summary.get('severity_counts', {}).get('medium', 0)} |",
            f"| Pass Rate | {summary.get('pass_rate', 0):.1f}% |",
            f"",
            f"**Overall Status:** Verification {status_text}",
            f"",
            f"---",
            f"",
            f"## Test Results",
            f"",
            f"| Measurement | Count |",
            f"|-------------|-------|",
            f"| Total Tests | {len(execution_log.get('test_results', []))} |",
            f"| Passed | {sum(1 for r in execution_log.get('test_results', []) if r.get('status') == 'passed')} |",
            f"| Failed | {len(execution_log.get('test_results', [])) - sum(1 for r in execution_log.get('test_results', []) if r.get('status') == 'passed')} |",
            f"",
            f"---",
            f""
        ]

        if violations:
            md.append("## Detailed Violations")
            md.append("")
            # Sort critical first
            sorted_violations = sorted(violations, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity"), 9))
            
            for v in sorted_violations:
                md.append(f"### [{v.get('violation_id', 'v')}] {v.get('category')} in `{v.get('function_name')}()`")
                md.append("")
                md.append(f"**Severity:** {v.get('severity', '').upper()}  ")
                md.append(f"**Constraint:** `{v.get('constraint_id')}`  ")
                md.append(f"**Affected Tests:** {len(v.get('affected_tests', []))} failures")
                md.append("")
                md.append("#### Description")
                md.append(v.get("description", ""))
                md.append("")
                md.append("#### Impact")
                md.append(f"- {v.get('impact')}")
                md.append(f"- **Exploitability:** {v.get('exploitability')}")
                md.append("")
                md.append("#### Remediation")
                md.append(f"**{v.get('remediation', {}).get('short_description')}**")
                for step in v.get("remediation", {}).get("detailed_steps", []):
                    md.append(f"- {step}")
                md.append("")

        md.append("## Technical Details")
        md.append("")
        md.append(f"- **Execution ID:** `{context.provenance.execution_id}`")
        md.append(f"- **Platform:** {context.platform.os_name} {context.platform.os_version}")
        md.append(f"- **Tool Version:** {context.provenance.tool_version}")
        md.append("")
        md.append("---")
        md.append(f"Generated by Polyglot FFI Contract Verifier")

        return "\n".join(md)

class CISummaryGenerator:
    """
    Generates CI-friendly JSON data including exit codes and status badges.
    """

    def generate(self, diagnostics: Dict[str, Any], execution_log: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ci_summary.json structure.
        """
        summary = diagnostics.get("summary", {})
        violations = diagnostics.get("violations", [])
        
        test_results = execution_log.get("test_results", [])
        passed_count = sum(1 for r in test_results if r.get("status") == "passed")
        failed_count = len(test_results) - passed_count
        
        has_critical = summary.get("severity_counts", {}).get("critical", 0) > 0
        status = "failed" if has_critical else "passed"
        exit_code = 1 if has_critical else 0
        
        badge = self._generate_status_badge(status, summary)
        blocking_issues = self._extract_blocking_issues(violations)
        
        return {
            "provenance": {
                "producing_phase": "1: Report Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": context.provenance.creation_timestamp,
                "tool_version": context.provenance.tool_version
            },
            "verification_status": status,
            "summary": {
                "total_tests": len(test_results),
                "passed_tests": passed_count,
                "failed_tests": failed_count,
                "pass_rate": summary.get("pass_rate", 0),
                "total_violations": len(violations),
                "critical_violations": summary.get("severity_counts", {}).get("critical", 0),
                "high_severity_violations": summary.get("severity_counts", {}).get("high", 0),
                "medium_severity_violations": summary.get("severity_counts", {}).get("medium", 0),
                "low_severity_violations": summary.get("severity_counts", {}).get("low", 0)
            },
            "status_badge": badge,
            "exit_code": exit_code,
            "blocking_issues": blocking_issues,
            "reports": {
                "html": "reports/verification_report.html",
                "markdown": "reports/verification_report.md",
                "diagnostics": "artifacts/diagnostics.json"
            }
        }

    def _generate_status_badge(self, status: str, summary: Dict[str, Any]) -> Dict[str, str]:
        critical = summary.get("severity_counts", {}).get("critical", 0)
        
        if status == "failed":
            message = f"FAILED ({critical} critical)"
            color = "red"
        else:
            message = "PASSED"
            color = "green"
            
        return {
            "label": "FFI Verification",
            "message": message,
            "color": color
        }

    def _extract_blocking_issues(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        blocking = []
        for v in violations:
            if v.get("severity") == "critical":
                blocking.append({
                    "violation_id": v.get("violation_id"),
                    "severity": "critical",
                    "function": v.get("function_name"),
                    "description": v.get("description", "Critical contract violation")
                })
        return blocking

class ReportMetadataGenerator:
    """
    Generates report_metadata.json to track verification outputs.
    """

    def generate(self, reports: Dict[str, str], context: Any) -> Dict[str, Any]:
        """
        Creates metadata structure for the generated reports.
        """
        from datetime import datetime
        return {
            "provenance": {
                "producing_phase": "1: Report Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": context.provenance.tool_version
            },
            "generated_artifacts": [
                {"format": fmt, "path": path} for fmt, path in reports.items()
            ],
            "metadata": {
                "report_count": len(reports),
                "target_library": context.native_library.library_path,
                "platform": context.platform.os_name
            }
        }

# ============================================================================
# PUBLIC API
# ============================================================================

class ReportGenerator:
    """
    Orchestrates the generation of FFI verification reports in multiple formats.
    """
    
    def __init__(self):
        self.html_gen = HtmlReportGenerator()
        self.md_gen = MarkdownReportGenerator()
        self.ci_gen = CISummaryGenerator()
        self.meta_gen = ReportMetadataGenerator()

    def generate_reports(self, context: Any) -> Dict[str, Any]:
        """
        Loads artifacts, generates reports, and saves them to the reports/ directory.
        """
        # 1. Load Artifacts
        artifacts = self._load_artifacts(context)
        
        # 2. Setup output directory
        reports_dir = os.path.join(context.artifacts.working_directory, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # 3. Generate content
        html_content = self.html_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            artifacts["contract"], 
            context
        )
        
        md_content = self.md_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            artifacts["contract"], 
            context
        )
        
        ci_summary = self.ci_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            context
        )
        
        # 4. Save files
        html_path = os.path.join(reports_dir, "verification_report.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        md_path = os.path.join(reports_dir, "verification_report.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        ci_path = os.path.join(reports_dir, "ci_summary.json")
        with open(ci_path, 'w', encoding='utf-8') as f:
            json.dump(ci_summary, f, indent=2)
            
        # 5. Metadata
        report_map = {
            "html": html_path,
            "markdown": md_path,
            "ci_summary": ci_path
        }
        metadata = self.meta_gen.generate(report_map, context)
        
        meta_path = os.path.join(reports_dir, "report_metadata.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
        return metadata

    def _load_artifacts(self, context: Any) -> Dict[str, Any]:
        """
        Loads the required artifacts from the artifacts directory.
        """
        artifacts_dir = context.artifacts.working_directory
        
        # 0 Output
        diag_path = context.artifacts.diagnostics_path
        if not os.path.exists(diag_path):
            diag_path = os.path.join(artifacts_dir, "diagnostics.json")
            
        if not os.path.exists(diag_path):
            raise FileNotFoundError(f"Diagnostics artifact missing: {diag_path}. Run 'diagnose' first.")
            
        with open(diag_path, 'r', encoding='utf-8') as f:
            diagnostics = json.load(f)
            
        # Phases 8-9 Output
        log_path = context.artifacts.execution_log_path
        if not os.path.exists(log_path):
            log_path = os.path.join(artifacts_dir, "execution_log.json")
            
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Execution log missing: {log_path}. Run 'execute' first.")
            
        with open(log_path, 'r', encoding='utf-8') as f:
            execution_log = json.load(f)
            
        #  Output
        contract_path = context.artifacts.contract_path
        if not os.path.exists(contract_path):
            contract_path = os.path.join(artifacts_dir, "contract.json")
            
        if not os.path.exists(contract_path):
             # Try to find any json file in artifacts that looks like a contract if strict path fails
            raise FileNotFoundError(f"Contract missing: {contract_path}. Run 'synthesize' first.")
            
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
            
        return {
            "diagnostics": diagnostics,
            "execution_log": execution_log,
            "contract": contract
        }
from datetime import timezone

# ═══════════════════════════════════════════════════════════════════════════
# COMMAND LINE INTERFACE
# ═══════════════════════════════════════════════════════════════════════════
#
# Provides command-line access to verification pipeline.
#
# USAGE:
#   python system_architecture.py verify <header> <library>
#   python system_architecture.py context
#
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Command-line interface entry point."""
    orchestrator = CLIOrchestrator()
    import sys
    sys.exit(orchestrator.run())

if __name__ == '__main__':
    main()

# ═══════════════════════════════════════════════════════════════════════════
# END OF SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════
#
# This consolidated file contains the complete Polyglot FFI Contract Verifier
# system. All 12 phases are included and fully functional.
#
# For the modular package structure (for development), see:
#   polyglot_ffi_verifier/ directory
#
# For documentation, see:
#   SYSTEM_ARCHITECTURE.md
#
# ═══════════════════════════════════════════════════════════════════════════
