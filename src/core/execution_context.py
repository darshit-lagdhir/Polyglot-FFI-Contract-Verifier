"""
Execution Context Module

This module defines the ExecutionContext data structure and construction logic.
The ExecutionContext captures all environment-specific details relevant to FFI
correctness verification and serves as the immutable environmental state that
all downstream components rely upon for deterministic behavior.

Architectural Principles:
- IMMUTABILITY: Once created, the context is never modified
- EXPLICITNESS: All environmental details are captured explicitly
- DETERMINISM: Identical inputs produce byte-identical contexts
- PROVENANCE: Full traceability of environment and configuration
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


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


@dataclass(frozen=True)
class TargetLanguageRuntime:
    """Target language runtime information."""
    language_name: str
    language_version: str
    ffi_mechanism: str
    runtime_path: str
    runtime_config: Dict[str, Any]


@dataclass(frozen=True)
class VerificationConfiguration:
    """Verification execution configuration."""
    random_seed: int
    per_test_timeout_seconds: int
    total_timeout_seconds: int
    crash_handling_mode: str
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
    verification_config: VerificationConfiguration
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
            verification_config=VerificationConfiguration(**data['verification_config']),
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
        self._verification_config: Optional[VerificationConfiguration] = None
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
        self._validate_native_library(library_file)
        
        # STEP 4: Target Language Runtime Resolution
        self._resolve_target_runtime(python_interpreter, ffi_mechanism)
        
        # STEP 5: Verification Configuration
        self._configure_verification(
            library_file,
            random_seed,
            per_test_timeout,
            total_timeout,
            crash_handling_mode,
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
            compiler_version=compiler_version,
            compiler_flags=list(compiler_flags),
            include_paths=resolved_includes,
            preprocessor_macros=dict(preprocessor_macros),
            standard_library_version=None  # Could be detected if needed
        )
    
    def _detect_msvc(self) -> str:
        """Detect MSVC compiler on Windows."""
        # Try common MSVC locations
        common_paths = [
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC",
            r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC",
            r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC",
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
            "MSVC compiler (cl.exe) not found. Please install Visual Studio or "
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
    
    def _validate_native_library(self, library_file: str) -> None:
        """STEP 3: Validate native library and compute hash."""
        library_path = os.path.abspath(library_file)
        
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
            additional_dependencies=[]
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
        verbosity: str
    ) -> None:
        """STEP 5: Configure verification parameters."""
        # Generate deterministic seed if not provided
        if random_seed is None:
            random_seed = self._generate_deterministic_seed(library_file)
        
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
        
        self._verification_config = VerificationConfiguration(
            random_seed=random_seed,
            per_test_timeout_seconds=per_test_timeout,
            total_timeout_seconds=total_timeout,
            crash_handling_mode=crash_handling_mode,
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
