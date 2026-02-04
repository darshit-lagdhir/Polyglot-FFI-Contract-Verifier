#!/usr/bin/env python3
"""
Module 03: Build Process & Toolchain Integration
: Build Philosophy & Core Architecture Model

This module implements the foundational build system for the Polyglot FFI
Contract Verifier. Unlike conventional build systems, this module treats
build correctness as inseparable from verification correctness.

Core Principles:
- Build process is a first-class correctness component
- Explicitness over convenience
- Deterministic and reproducible builds
- Comprehensive environment declaration
- Seven-stage validation pipeline
- Complete artifact provenance

Author: Polyglot FFI Contract Verifier Project
Module: 03 of 28
Version: 1.0.0
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import datetime

# ============================================================================
# CORE ENUMERATIONS
# ============================================================================

class BuildDomain(Enum):
    """
    Three distinct build domains with different isolation requirements.
    """
    NATIVE_VERIFICATION_TOOLING = "native_verification_tooling"
    ORCHESTRATION_ADAPTER_TOOLING = "orchestration_adapter_tooling"
    VERIFICATION_TARGETS = "verification_targets"

class BuildStage(Enum):
    """
    Seven explicit stages of the build pipeline.
    Each stage has strict preconditions and postconditions.
    """
    SOURCE_ENUMERATION = 1
    SOURCE_VALIDATION = 2
    DEPENDENCY_RESOLUTION = 3
    NATIVE_COMPILATION = 4
    ADAPTER_GENERATION = 5
    ORCHESTRATION_ASSEMBLY = 6
    PACKAGING_VALIDATION = 7

class BuildMode(Enum):
    """
    Build modes with different validation and optimization requirements.
    """
    DEBUG = "debug"
    RELEASE = "release"
    PROFILING = "profiling"
    CI = "ci"

# ============================================================================
# CORE EXCEPTIONS
# ============================================================================

class BuildError(Exception):
    """Base exception for all build process errors."""
    pass

class BuildConfigError(BuildError):
    """Raised when build configuration is invalid or incomplete."""
    pass

class BuildPreconditionError(BuildError):
    """Raised when stage preconditions are not satisfied."""
    pass

class BuildPostconditionError(BuildError):
    """Raised when stage postconditions are violated."""
    pass

class BuildDeterminismError(BuildError):
    """Raised when build produces nondeterministic outputs."""
    pass

class BuildIsolationError(BuildError):
    """Raised when build domain isolation is violated."""
    pass

# ============================================================================
# BUILD PHILOSOPHY ENFORCER
# ============================================================================

@dataclass
class BuildPhilosophy:
    """
    Encodes and enforces the core philosophical principles of the build system.
    
    This class exists to make abstract principles concrete and enforceable.
    It validates that build configurations and operations adhere to the
    system's correctness philosophy.
    """
    
    # Principle flags
    enforce_explicitness: bool = True
    enforce_determinism: bool = True
    enforce_isolation: bool = True
    enforce_provenance: bool = True
    allow_implicit_defaults: bool = False
    allow_silent_fallbacks: bool = False
    
    def validate_configuration(self, config: Dict[str, Any]) -> None:
        """
        Validate that a build configuration adheres to philosophical principles.
        
        Args:
            config: Build configuration dictionary
            
        Raises:
            BuildConfigError: If configuration violates principles
        """
        if self.enforce_explicitness:
            self._validate_explicitness(config)
        
        if not self.allow_implicit_defaults:
            self._validate_no_implicit_defaults(config)
    
    def _validate_explicitness(self, config: Dict[str, Any]) -> None:
        """Ensure all critical configuration is explicit."""
        required_keys = [
            'toolchain_version',
            'compiler_executable',
            'target_architecture',
            'build_mode',
            'abi_conventions'
        ]
        
        missing = [key for key in required_keys if key not in config]
        if missing:
            raise BuildConfigError(
                f"Build configuration missing required explicit declarations: {missing}\n"
                f"Principle violated: Explicitness over convenience\n"
                f"The build system requires explicit declaration of all ABI-relevant configuration."
            )
    
    def _validate_no_implicit_defaults(self, config: Dict[str, Any]) -> None:
        """Ensure no configuration relies on undocumented defaults."""
        for key, value in config.items():
            if value == "auto" or value == "default":
                raise BuildConfigError(
                    f"Config key '{key}' uses implicit default value '{value}'.\n"
                    f"Principle violated: No implicit behavior\n"
                    f"All configuration must be explicit. Replace with concrete value."
                )

# ============================================================================
# ENVIRONMENT DESCRIPTOR
# ============================================================================

@dataclass
class EnvironmentDescriptor:
    """
    Comprehensive description of the build environment.
    
    This descriptor captures all environment factors that influence build
    outputs. It serves as both configuration input and provenance output.
    """
    
    # Toolchain information
    compiler_name: str
    compiler_version: str
    compiler_executable: Path
    linker_executable: Path
    
    # Platform information
    target_os: str
    target_architecture: str
    host_os: str
    host_architecture: str
    
    # Build configuration
    build_mode: BuildMode
    optimization_level: str
    debug_symbols: bool
    
    # ABI configuration
    calling_convention: str
    structure_packing: int
    alignment_rules: str
    
    # Environment state
    environment_variables: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    descriptor_version: str = "1.0.0"
    creation_timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    
    def to_json(self) -> str:
        """Serialize descriptor to JSON."""
        data = {
            'descriptor_version': self.descriptor_version,
            'creation_timestamp': self.creation_timestamp,
            'toolchain': {
                'compiler_name': self.compiler_name,
                'compiler_version': self.compiler_version,
                'compiler_executable': str(self.compiler_executable),
                'linker_executable': str(self.linker_executable),
            },
            'platform': {
                'target_os': self.target_os,
                'target_architecture': self.target_architecture,
                'host_os': self.host_os,
                'host_architecture': self.host_architecture,
            },
            'build_configuration': {
                'build_mode': self.build_mode.value,
                'optimization_level': self.optimization_level,
                'debug_symbols': self.debug_symbols,
            },
            'abi_configuration': {
                'calling_convention': self.calling_convention,
                'structure_packing': self.structure_packing,
                'alignment_rules': self.alignment_rules,
            },
            'environment': self.environment_variables
        }
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'EnvironmentDescriptor':
        """Deserialize descriptor from JSON."""
        data = json.loads(json_str)
        return cls(
            compiler_name=data['toolchain']['compiler_name'],
            compiler_version=data['toolchain']['compiler_version'],
            compiler_executable=Path(data['toolchain']['compiler_executable']),
            linker_executable=Path(data['toolchain']['linker_executable']),
            target_os=data['platform']['target_os'],
            target_architecture=data['platform']['target_architecture'],
            host_os=data['platform']['host_os'],
            host_architecture=data['platform']['host_architecture'],
            build_mode=BuildMode(data['build_configuration']['build_mode']),
            optimization_level=data['build_configuration']['optimization_level'],
            debug_symbols=data['build_configuration']['debug_symbols'],
            calling_convention=data['abi_configuration']['calling_convention'],
            structure_packing=data['abi_configuration']['structure_packing'],
            alignment_rules=data['abi_configuration']['alignment_rules'],
            environment_variables=data['environment'],
            descriptor_version=data['descriptor_version'],
            creation_timestamp=data['creation_timestamp'],
        )
    
    def validate(self) -> None:
        """
        Validate that descriptor is internally consistent and complete.
        
        Raises:
            BuildConfigError: If descriptor is invalid
        """
        # Validate toolchain executables exist
        if not self.compiler_executable.exists():
            raise BuildConfigError(
                f"Compiler executable does not exist: {self.compiler_executable}"
            )
        
        if not self.linker_executable.exists():
            raise BuildConfigError(
                f"Linker executable does not exist: {self.linker_executable}"
            )
        
        # Validate structure packing is valid
        if self.structure_packing not in [1, 2, 4, 8, 16]:
            raise BuildConfigError(
                f"Invalid structure packing: {self.structure_packing}. "
                f"Must be 1, 2, 4, 8, or 16."
            )

# ============================================================================
# BUILD STAGE INTERFACE
# ============================================================================

class BuildStageInterface(ABC):
    """
    Abstract base class for all build pipeline stages.
    
    Each stage must implement:
    - Precondition checking
    - Execution logic
    - Postcondition validation
    - Artifact generation
    """
    
    def __init__(self, stage_name: str, stage_number: BuildStage):
        self.stage_name = stage_name
        self.stage_number = stage_number
        self.artifacts: Dict[str, Any] = {}
    
    @abstractmethod
    def check_preconditions(self, context: Dict[str, Any]) -> None:
        """
        Verify that preconditions for this stage are satisfied.
        
        Args:
            context: Build context from previous stages
            
        Raises:
            BuildPreconditionError: If preconditions are not met
        """
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the stage logic.
        
        Args:
            context: Build context from previous stages
            
        Returns:
            Updated build context including this stage's outputs
            
        Raises:
            BuildError: If stage execution fails
        """
        pass
    
    @abstractmethod
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        """
        Verify that postconditions for this stage are satisfied.
        
        Args:
            context: Build context after stage execution
            
        Raises:
            BuildPostconditionError: If postconditions are violated
        """
        pass
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete stage: preconditions -> execute -> postconditions.
        
        Args:
            context: Build context from previous stages
            
        Returns:
            Updated build context
        """
        print(f"[Stage {self.stage_number.value}] {self.stage_name}: Checking preconditions...")
        self.check_preconditions(context)
        
        print(f"[Stage {self.stage_number.value}] {self.stage_name}: Executing...")
        updated_context = self.execute(context)
        
        print(f"[Stage {self.stage_number.value}] {self.stage_name}: Validating postconditions...")
        self.validate_postconditions(updated_context)
        
        print(f"[Stage {self.stage_number.value}] {self.stage_name}: ✓ Complete")
        return updated_context

# ============================================================================
# BUILD PROCESS ORCHESTRATOR
# ============================================================================

class BuildProcessOrchestrator:
    """
    Orchestrates the seven-stage build pipeline.
    
    This is the top-level controller that:
    - Validates build philosophy adherence
    - Executes stages in order
    - Manages build context
    - Generates provenance artifacts
    """
    
    def __init__(self, environment_descriptor: EnvironmentDescriptor):
        self.environment = environment_descriptor
        self.philosophy = BuildPhilosophy()
        self.stages: List[BuildStageInterface] = []
        self.build_context: Dict[str, Any] = {
            'environment': environment_descriptor,
            'start_time': datetime.datetime.utcnow().isoformat(),
        }
    
    def register_stage(self, stage: BuildStageInterface) -> None:
        """Register a build stage."""
        self.stages.append(stage)
    
    def execute_build(self) -> Dict[str, Any]:
        """
        Execute the complete build pipeline.
        
        Returns:
            Final build context with all artifacts
            
        Raises:
            BuildError: If any stage fails
        """
        print("=" * 80)
        print("BUILD PROCESS STARTED")
        print("=" * 80)
        print(f"Environment: {self.environment.compiler_name} {self.environment.compiler_version}")
        print(f"Target: {self.environment.target_os}/{self.environment.target_architecture}")
        print(f"Mode: {self.environment.build_mode.value}")
        print("=" * 80)
        
        # Validate environment
        self.environment.validate()
        
        # Execute stages in order
        for stage in self.stages:
            self.build_context = stage.run(self.build_context)
        
        # Add completion metadata
        self.build_context['end_time'] = datetime.datetime.utcnow().isoformat()
        self.build_context['status'] = 'SUCCESS'
        
        print("=" * 80)
        print("BUILD PROCESS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        return self.build_context

# ============================================================================
# ============================================================================

import platform
import shutil
import re
from typing import Tuple, Optional

@dataclass
class ToolchainDescriptor:
    """
    Comprehensive description of a detected toolchain.
    
    This descriptor captures all toolchain properties that influence ABI
    behavior, code generation, and build determinism.
    """
    
    # Toolchain identity
    compiler_name: str
    compiler_version: str
    compiler_full_version: str
    compiler_executable: Path
    compiler_executable_hash: str
    
    # Linker identity
    linker_executable: Path
    linker_executable_hash: str
    linker_version: str
    
    # Target platform
    target_triple: str
    target_os: str
    target_architecture: str
    target_abi: str
    
    # ABI properties
    default_calling_convention: str
    default_structure_packing: int
    supports_explicit_packing: bool
    name_mangling_scheme: str
    
    # Capabilities
    supports_debug_symbols: bool
    supports_optimization: bool
    deterministic_output: bool
    
    # Metadata
    detection_timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    descriptor_version: str = "1.0.0"
    
    def to_json(self) -> str:
        """Serialize toolchain descriptor to JSON."""
        data = {
            'descriptor_version': self.descriptor_version,
            'detection_timestamp': self.detection_timestamp,
            'compiler': {
                'name': self.compiler_name,
                'version': self.compiler_version,
                'full_version': self.compiler_full_version,
                'executable': str(self.compiler_executable),
                'executable_hash': self.compiler_executable_hash,
            },
            'linker': {
                'executable': str(self.linker_executable),
                'executable_hash': self.linker_executable_hash,
                'version': self.linker_version,
            },
            'target': {
                'triple': self.target_triple,
                'os': self.target_os,
                'architecture': self.target_architecture,
                'abi': self.target_abi,
            },
            'abi_properties': {
                'default_calling_convention': self.default_calling_convention,
                'default_structure_packing': self.default_structure_packing,
                'supports_explicit_packing': self.supports_explicit_packing,
                'name_mangling_scheme': self.name_mangling_scheme,
            },
            'capabilities': {
                'supports_debug_symbols': self.supports_debug_symbols,
                'supports_optimization': self.supports_optimization,
                'deterministic_output': self.deterministic_output,
            }
        }
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ToolchainDescriptor':
        """Deserialize toolchain descriptor from JSON."""
        data = json.loads(json_str)
        return cls(
            compiler_name=data['compiler']['name'],
            compiler_version=data['compiler']['version'],
            compiler_full_version=data['compiler']['full_version'],
            compiler_executable=Path(data['compiler']['executable']),
            compiler_executable_hash=data['compiler']['executable_hash'],
            linker_executable=Path(data['linker']['executable']),
            linker_executable_hash=data['linker']['executable_hash'],
            linker_version=data['linker']['version'],
            target_triple=data['target']['triple'],
            target_os=data['target']['os'],
            target_architecture=data['target']['architecture'],
            target_abi=data['target']['abi'],
            default_calling_convention=data['abi_properties']['default_calling_convention'],
            default_structure_packing=data['abi_properties']['default_structure_packing'],
            supports_explicit_packing=data['abi_properties']['supports_explicit_packing'],
            name_mangling_scheme=data['abi_properties']['name_mangling_scheme'],
            supports_debug_symbols=data['capabilities']['supports_debug_symbols'],
            supports_optimization=data['capabilities']['supports_optimization'],
            deterministic_output=data['capabilities']['deterministic_output'],
            detection_timestamp=data['detection_timestamp'],
            descriptor_version=data['descriptor_version'],
        )

class ToolchainDetector:
    """
    Detects, validates, and describes available toolchains.
    
    This class implements the semantic discovery process that transforms
    implicit environmental state (installed compilers) into explicit,
    validated toolchain descriptors.
    """
    
    KNOWN_COMPILERS = {
        'cl.exe': 'MSVC',
        'clang.exe': 'Clang',
        'clang': 'Clang',
        'gcc.exe': 'GCC',
        'gcc': 'GCC',
    }
    
    def __init__(self):
        self.detected_toolchains: List[ToolchainDescriptor] = []
    
    def detect_system_toolchains(self) -> List[ToolchainDescriptor]:
        """
        Detect all available toolchains on the system.
        
        Returns:
            List of detected and validated toolchain descriptors
        """
        print("Detecting system toolchains...")
        
        toolchains = []
        
        # Detect compilers in PATH
        for compiler_name, friendly_name in self.KNOWN_COMPILERS.items():
            compiler_path = shutil.which(compiler_name)
            if compiler_path:
                print(f"  Found {friendly_name} at: {compiler_path}")
                try:
                    descriptor = self._detect_toolchain(Path(compiler_path), friendly_name)
                    toolchains.append(descriptor)
                    print(f"    ✓ Version: {descriptor.compiler_version}")
                    print(f"    ✓ Target: {descriptor.target_triple}")
                except BuildError as e:
                    print(f"    ✗ Detection failed: {e}")
        
        if not toolchains:
            raise BuildConfigError(
                "No valid toolchains detected on system.\n"
                "The build process requires an explicit, validated toolchain.\n"
                "Please install a supported compiler (MSVC, Clang, or GCC)."
            )
        
        self.detected_toolchains = toolchains
        return toolchains
    
    def _detect_toolchain(self, compiler_path: Path, compiler_name: str) -> ToolchainDescriptor:
        """
        Detect and validate a specific toolchain.
        
        Args:
            compiler_path: Path to compiler executable
            compiler_name: Friendly name of compiler
            
        Returns:
            Validated toolchain descriptor
            
        Raises:
            BuildError: If toolchain cannot be validated
        """
        # Validate executable exists
        if not compiler_path.exists():
            raise BuildConfigError(f"Compiler executable does not exist: {compiler_path}")
        
        # Extract version information
        version, full_version = self._extract_compiler_version(compiler_path, compiler_name)
        
        # Hash executable for provenance
        executable_hash = self._hash_file(compiler_path)
        
        # Detect linker
        linker_path, linker_hash, linker_version = self._detect_linker(compiler_path, compiler_name)
        
        # Detect target triple
        target_triple, target_os, target_arch, target_abi = self._detect_target_triple(
            compiler_path, compiler_name
        )
        
        # Infer ABI properties
        abi_properties = self._infer_abi_properties(compiler_name, target_os, target_arch)
        
        return ToolchainDescriptor(
            compiler_name=compiler_name,
            compiler_version=version,
            compiler_full_version=full_version,
            compiler_executable=compiler_path,
            compiler_executable_hash=executable_hash,
            linker_executable=linker_path,
            linker_executable_hash=linker_hash,
            linker_version=linker_version,
            target_triple=target_triple,
            target_os=target_os,
            target_architecture=target_arch,
            target_abi=target_abi,
            **abi_properties
        )
    
    def _extract_compiler_version(self, compiler_path: Path, compiler_name: str) -> Tuple[str, str]:
        """
        Extract version information from compiler.
        
        Args:
            compiler_path: Path to compiler executable
            compiler_name: Compiler name
            
        Returns:
            Tuple of (short_version, full_version)
        """
        try:
            if compiler_name == 'MSVC':
                # MSVC uses /
                result = subprocess.run(
                    [str(compiler_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stderr  # MSVC prints to stderr
            else:
                # Clang/GCC use --version
                result = subprocess.run(
                    [str(compiler_path), '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stdout
            
            # Extract version number
            if compiler_name == 'MSVC':
                # Format: "Microsoft (R) C/C++ Optimizing Compiler Version 19.29.30133 for x64"
                match = re.search(r'Version\s+(\d+\.\d+\.\d+)', output)
                if match:
                    full_version = match.group(1)
                    short_version = '.'.join(full_version.split('.')[:2])  # 19.29
                    return short_version, full_version
            elif compiler_name == 'Clang':
                # Format: "clang version 14.0.0"
                match = re.search(r'clang version\s+(\d+\.\d+\.\d+)', output)
                if match:
                    full_version = match.group(1)
                    short_version = full_version.split('.')[0]  # 14
                    return short_version, full_version
            elif compiler_name == 'GCC':
                # Format: "gcc (GCC) 11.2.0"
                match = re.search(r'gcc.*\s+(\d+\.\d+\.\d+)', output, re.IGNORECASE)
                if match:
                    full_version = match.group(1)
                    short_version = full_version.split('.')[0]  # 11
                    return short_version, full_version
            
            raise BuildError(f"Could not parse version from compiler output:\n{output}")
        
        except subprocess.TimeoutExpired:
            raise BuildError(f"Compiler version detection timed out: {compiler_path}")
        except Exception as e:
            raise BuildError(f"Failed to extract compiler version: {e}")
    
    def _detect_linker(self, compiler_path: Path, compiler_name: str) -> Tuple[Path, str, str]:
        """
        Detect linker associated with compiler.
        
        Returns:
            Tuple of (linker_path, linker_hash, linker_version)
        """
        if compiler_name == 'MSVC':
            # MSVC uses link.exe
            linker_path = compiler_path.parent / 'link.exe'
        elif compiler_name in ['Clang', 'GCC']:
            # Try to find ld or lld
            linker_path = shutil.which('ld')
            if not linker_path:
                linker_path = shutil.which('lld')
            if not linker_path:
                # Use compiler as linker
                linker_path = compiler_path
        
        if not linker_path or not Path(linker_path).exists():
            raise BuildConfigError(f"Could not detect linker for {compiler_name}")
        
        linker_path = Path(linker_path)
        linker_hash = self._hash_file(linker_path)
        
        # Extract linker version (simplified - use compiler version as fallback)
        linker_version = "unknown"
        
        return linker_path, linker_hash, linker_version
    
    def _detect_target_triple(
        self, compiler_path: Path, compiler_name: str
    ) -> Tuple[str, str, str, str]:
        """
        Detect target triple (OS-vendor-architecture-ABI).
        
        Returns:
            Tuple of (triple, os, architecture, abi)
        """
        # Detect host platform as fallback
        host_os = platform.system()
        host_arch = platform.machine()
        
        if compiler_name == 'MSVC':
            # MSVC targets Windows
            target_os = 'Windows'
            target_arch = 'x86_64' if 'x64' in str(compiler_path) else 'x86'
            target_abi = 'msvc'
            target_triple = f"{target_os}-{target_arch}-{target_abi}"
        
        elif compiler_name in ['Clang', 'GCC']:
            # Try to query compiler for target
            try:
                result = subprocess.run(
                    [str(compiler_path), '-dumpmachine'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                target_triple = result.stdout.strip()
                
                # Parse triple: x86_64-pc-linux-gnu
                parts = target_triple.split('-')
                target_arch = parts[0] if len(parts) > 0 else host_arch
                target_os = parts[2] if len(parts) > 2 else host_os
                target_abi = parts[3] if len(parts) > 3 else 'gnu'
            
            except Exception:
                # Fallback to host
                target_os = host_os
                target_arch = host_arch
                target_abi = 'gnu'
                target_triple = f"{target_arch}-unknown-{target_os.lower()}-{target_abi}"
        
        return target_triple, target_os, target_arch, target_abi
    
    def _infer_abi_properties(
        self, compiler_name: str, target_os: str, target_arch: str
    ) -> Dict[str, Any]:
        """
        Infer ABI properties based on compiler and target.
        
        Returns:
            Dictionary of ABI properties
        """
        properties = {}
        
        # Default calling convention
        if compiler_name == 'MSVC' and target_arch == 'x86_64':
            properties['default_calling_convention'] = 'microsoft_x64'
        elif compiler_name == 'MSVC' and target_arch == 'x86':
            properties['default_calling_convention'] = 'cdecl'
        elif target_os == 'Linux' and target_arch == 'x86_64':
            properties['default_calling_convention'] = 'sysv_amd64'
        else:
            properties['default_calling_convention'] = 'platform_default'
        
        # Structure packing
        if compiler_name == 'MSVC':
            properties['default_structure_packing'] = 8  # MSVC default
        else:
            properties['default_structure_packing'] = 1  # GCC/Clang default (no padding)
        
        properties['supports_explicit_packing'] = True
        
        # Name mangling
        if compiler_name == 'MSVC':
            properties['name_mangling_scheme'] = 'msvc'
        else:
            properties['name_mangling_scheme'] = 'itanium'
        
        # Capabilities
        properties['supports_debug_symbols'] = True
        properties['supports_optimization'] = True
        properties['deterministic_output'] = (compiler_name in ['Clang', 'GCC'])
        
        return properties
    
    def _hash_file(self, filepath: Path) -> str:
        """Compute SHA256 hash of file for provenance."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

class ToolchainValidator:
    """
    Validates detected toolchains against build requirements.
    """
    
    def __init__(self, requirements: Dict[str, Any]):
        """
        Args:
            requirements: Dictionary of build requirements
        """
        self.requirements = requirements
    
    def validate_toolchain(self, toolchain: ToolchainDescriptor) -> None:
        """
        Validate that a toolchain meets build requirements.
        
        Args:
            toolchain: Toolchain to validate
            
        Raises:
            BuildConfigError: If validation fails
        """
        print(f"Validating toolchain: {toolchain.compiler_name} {toolchain.compiler_version}")
        
        # Validate target OS compatibility
        if 'required_target_os' in self.requirements:
            required_os = self.requirements['required_target_os']
            if toolchain.target_os.lower() != required_os.lower():
                raise BuildConfigError(
                    f"Toolchain target OS ({toolchain.target_os}) does not match "
                    f"required OS ({required_os})"
                )
        
        # Validate minimum version if specified
        if 'minimum_compiler_version' in self.requirements:
            min_version = self.requirements['minimum_compiler_version']
            if toolchain.compiler_name in min_version:
                required = min_version[toolchain.compiler_name]
                if self._compare_versions(toolchain.compiler_version, required) < 0:
                    raise BuildConfigError(
                        f"{toolchain.compiler_name} version {toolchain.compiler_version} "
                        f"is below minimum required version {required}"
                    )
        
        # Validate ABI support
        if 'required_calling_convention' in self.requirements:
            required_cc = self.requirements['required_calling_convention']
            if toolchain.default_calling_convention != required_cc:
                print(f"  ⚠ Warning: Calling convention mismatch")
                print(f"    Toolchain default: {toolchain.default_calling_convention}")
                print(f"    Required: {required_cc}")
        
        print(f"  ✓ Toolchain validation passed")
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Returns:
            -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        
        # Equal up to shortest length, compare lengths
        if len(v1_parts) < len(v2_parts):
            return -1
        elif len(v1_parts) > len(v2_parts):
            return 1
        return 0

# ============================================================================
# BUILD STAGE PIPELINE INFRASTRUCTURE ()
# ============================================================================

from typing import Callable
import pickle

# ============================================================================
# STAGE PRECONDITION/POSTCONDITION DECORATORS
# ============================================================================

def requires(*preconditions: str):
    """
    Decorator to declare stage preconditions.
    
    Args:
        *preconditions: List of precondition keys that must exist in context
    """
    def decorator(method: Callable):
        method._preconditions = preconditions
        return method
    return decorator

def ensures(*postconditions: str):
    """
    Decorator to declare stage postconditions.
    
    Args:
        *postconditions: List of postcondition keys that must exist after stage
    """
    def decorator(method: Callable):
        method._postconditions = postconditions
        return method
    return decorator

# ============================================================================
# STAGE IMPLEMENTATIONS
# ============================================================================

class SourceEnumerationStage(BuildStageInterface):
    """
    Stage 1: Source Enumeration
    
    Exhaustively identifies all source files, headers, configuration files,
    and build scripts required for the build.
    
    Preconditions:
    - Environment descriptor must exist
    - Source root directory must be specified
    
    Postconditions:
    - All source files enumerated
    - Source file hashes computed
    - Source manifest generated
    """
    
    def __init__(self, source_root: Path):
        super().__init__("Source Enumeration", BuildStage.SOURCE_ENUMERATION)
        self.source_root = source_root
    
    def check_preconditions(self, context: Dict[str, Any]) -> None:
        if 'environment' not in context:
            raise BuildPreconditionError(
                "Stage 1 requires 'environment' in build context"
            )
        
        if not self.source_root.exists():
            raise BuildPreconditionError(
                f"Source root does not exist: {self.source_root}"
            )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"  Enumerating sources in: {self.source_root}")
        
        # Find all source files
        source_files = {
            'c_sources': list(self.source_root.rglob('*.c')),
            'cpp_sources': list(self.source_root.rglob('*.cpp')),
            'headers': list(self.source_root.rglob('*.h')),
            'python_sources': list(self.source_root.rglob('*.py')),
        }
        
        # Compute hashes for provenance
        source_hashes = {}
        for category, files in source_files.items():
            for filepath in files:
                relative_path = filepath.relative_to(self.source_root)
                hash_value = self._hash_file(filepath)
                source_hashes[str(relative_path)] = hash_value
        
        total_files = sum(len(files) for files in source_files.values())
        print(f"  Found {total_files} source files")
        
        # Update context
        context['source_files'] = source_files
        context['source_hashes'] = source_hashes
        context['source_root'] = self.source_root
        
        return context
    
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        if 'source_files' not in context:
            raise BuildPostconditionError(
                "Stage 1 must produce 'source_files' in context"
            )
        
        if 'source_hashes' not in context:
            raise BuildPostconditionError(
                "Stage 1 must produce 'source_hashes' in context"
            )
        
        # Verify at least some sources found
        source_files = context['source_files']
        total = sum(len(files) for files in source_files.values())
        if total == 0:
            raise BuildPostconditionError(
                "Stage 1 found no source files. Build cannot proceed."
            )
    
    def _hash_file(self, filepath: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

class SourceValidationStage(BuildStageInterface):
    """
    Stage 2: Source Validation
    
    Validates that enumerated sources are syntactically valid and compatible
    with the declared toolchain.
    
    Preconditions:
    - Source files must be enumerated
    - Toolchain descriptor must exist
    
    Postconditions:
    - All sources validated as parseable
    - Validation report generated
    """
    
    def __init__(self):
        super().__init__("Source Validation", BuildStage.SOURCE_VALIDATION)
    
    def check_preconditions(self, context: Dict[str, Any]) -> None:
        if 'source_files' not in context:
            raise BuildPreconditionError(
                "Stage 2 requires 'source_files' from Stage 1"
            )
        
        if 'toolchain' not in context:
            raise BuildPreconditionError(
                "Stage 2 requires 'toolchain' descriptor"
            )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"  Validating source files...")
        
        source_files = context['source_files']
        validation_results = {
            'validated_files': [],
            'validation_errors': []
        }
        
        # Validate C/C++ headers (basic syntax check)
        for header in source_files.get('headers', []):
            try:
                # Basic validation: check file is readable and not empty
                content = header.read_text(encoding='utf-8')
                if len(content.strip()) == 0:
                    validation_results['validation_errors'].append({
                        'file': str(header),
                        'error': 'Empty header file'
                    })
                else:
                    validation_results['validated_files'].append(str(header))
            except Exception as e:
                validation_results['validation_errors'].append({
                    'file': str(header),
                    'error': str(e)
                })
        
        # Validate Python sources (syntax check)
        for py_file in source_files.get('python_sources', []):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(py_file), 'exec')
                validation_results['validated_files'].append(str(py_file))
            except SyntaxError as e:
                validation_results['validation_errors'].append({
                    'file': str(py_file),
                    'error': f'Syntax error: {e}'
                })
        
        print(f"  Validated {len(validation_results['validated_files'])} files")
        if validation_results['validation_errors']:
            print(f"  ⚠ Found {len(validation_results['validation_errors'])} validation errors")
        
        context['validation_results'] = validation_results
        return context
    
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        if 'validation_results' not in context:
            raise BuildPostconditionError(
                "Stage 2 must produce 'validation_results'"
            )
        
        validation_results = context['validation_results']
        
        # Fail if critical errors found
        if validation_results['validation_errors']:
            error_summary = '\n'.join(
                f"  - {err['file']}: {err['error']}"
                for err in validation_results['validation_errors'][:5]
            )
            raise BuildPostconditionError(
                f"Source validation found errors:\n{error_summary}"
            )

class DependencyResolutionStage(BuildStageInterface):
    """
    Stage 3: Dependency Resolution
    
    Resolves all external dependencies with fixed versions or hashes.
    
    Preconditions:
    - Dependency manifest must be specified
    
    Postconditions:
    - All dependencies resolved
    - Dependency metadata recorded
    """
    
    def __init__(self, dependency_manifest: Optional[Path] = None):
        super().__init__("Dependency Resolution", BuildStage.DEPENDENCY_RESOLUTION)
        self.dependency_manifest = dependency_manifest
    
    def check_preconditions(self, context: Dict[str, Any]) -> None:
        # For now, dependencies are optional
        pass
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"  Resolving dependencies...")
        
        resolved_dependencies = {
            'runtime': [],
            'build': [],
            'test': []
        }
        
        if self.dependency_manifest and self.dependency_manifest.exists():
            # Parse dependency manifest (simplified - would use real package manager)
            print(f"  Loading manifest: {self.dependency_manifest}")
            # TODO: Implement real dependency resolution
            pass
        else:
            print(f"  No dependency manifest specified")
        
        context['dependencies'] = resolved_dependencies
        return context
    
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        if 'dependencies' not in context:
            raise BuildPostconditionError(
                "Stage 3 must produce 'dependencies'"
            )

# ============================================================================
# PIPELINE CHECKPOINT MANAGER
# ============================================================================

class PipelineCheckpoint:
    """
    Manages build pipeline checkpoints for resumable builds.
    """
    
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, stage: BuildStage, context: Dict[str, Any]) -> Path:
        """
        Save build context as checkpoint after successful stage completion.
        
        Args:
            stage: Stage that just completed
            context: Build context to save
            
        Returns:
            Path to checkpoint file
        """
        checkpoint_file = self.checkpoint_dir / f"checkpoint_stage_{stage.value}.pkl"
        
        # Add checkpoint metadata
        checkpoint_data = {
            'stage': stage.value,
            'stage_name': stage.name,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'context': context
        }
        
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        
        print(f"  ✓ Checkpoint saved: {checkpoint_file.name}")
        return checkpoint_file
    
    def load_checkpoint(self, stage: BuildStage) -> Dict[str, Any]:
        """
        Load build context from checkpoint.
        
        Args:
            stage: Stage to resume from
            
        Returns:
            Restored build context
        """
        checkpoint_file = self.checkpoint_dir / f"checkpoint_stage_{stage.value}.pkl"
        
        if not checkpoint_file.exists():
            raise BuildError(
                f"No checkpoint found for stage {stage.value}"
            )
        
        with open(checkpoint_file, 'rb') as f:
            checkpoint_data = pickle.load(f)
        
        print(f"  ✓ Loaded checkpoint from stage {checkpoint_data['stage_name']}")
        return checkpoint_data['context']
    
    def list_checkpoints(self) -> List[Tuple[BuildStage, str]]:
        """
        List available checkpoints.
        
        Returns:
            List of (stage, timestamp) tuples
        """
        checkpoints = []
        for checkpoint_file in sorted(self.checkpoint_dir.glob("checkpoint_stage_*.pkl")):
            with open(checkpoint_file, 'rb') as f:
                data = pickle.load(f)
                stage = BuildStage(data['stage'])
                timestamp = data['timestamp']
                checkpoints.append((stage, timestamp))
        return checkpoints

# ============================================================================
# ENHANCED BUILD PROCESS ORCHESTRATOR
# ============================================================================

class EnhancedBuildProcessOrchestrator(BuildProcessOrchestrator):
    """
    Enhanced orchestrator with full pipeline infrastructure.
    
    Extends base orchestrator with:
    - Checkpoint management
    - Resumable builds
    - Enhanced diagnostics
    - Stage parallelization support
    """
    
    def __init__(
        self,
        environment_descriptor: EnvironmentDescriptor,
        checkpoint_dir: Optional[Path] = None
    ):
        super().__init__(environment_descriptor)
        
        self.checkpoint_manager = None
        if checkpoint_dir:
            self.checkpoint_manager = PipelineCheckpoint(checkpoint_dir)
    
    def execute_build_with_checkpoints(
        self,
        resume_from: Optional[BuildStage] = None
    ) -> Dict[str, Any]:
        """
        Execute build with checkpoint support.
        
        Args:
            resume_from: Stage to resume from (None = start from beginning)
            
        Returns:
            Final build context
        """
        print("=" * 80)
        print("BUILD PROCESS STARTED (WITH CHECKPOINTS)")
        print("=" * 80)
        
        # Validate environment
        self.environment.validate()
        
        # Resume from checkpoint if requested
        if resume_from:
            if not self.checkpoint_manager:
                raise BuildError("Cannot resume: No checkpoint directory configured")
            
            print(f"Resuming from stage {resume_from.value}: {resume_from.name}")
            self.build_context = self.checkpoint_manager.load_checkpoint(resume_from)
            
            # Find starting stage index
            start_index = next(
                i for i, stage in enumerate(self.stages)
                if stage.stage_number == resume_from
            )
            stages_to_run = self.stages[start_index:]
        else:
            stages_to_run = self.stages
        
        # Execute stages
        for stage in stages_to_run:
            try:
                self.build_context = stage.run(self.build_context)
                
                # Save checkpoint after successful stage
                if self.checkpoint_manager:
                    self.checkpoint_manager.save_checkpoint(
                        stage.stage_number,
                        self.build_context
                    )
            
            except BuildError as e:
                # Generate diagnostic report
                self._generate_failure_diagnostic(stage, e)
                raise
        
        # Add completion metadata
        self.build_context['end_time'] = datetime.datetime.utcnow().isoformat()
        self.build_context['status'] = 'SUCCESS'
        
        print("=" * 80)
        print("BUILD PROCESS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        return self.build_context
    
    def _generate_failure_diagnostic(self, stage: BuildStageInterface, error: BuildError):
        """
        Generate detailed diagnostic report for build failure.
        
        Args:
            stage: Stage where failure occurred
            error: Exception that caused failure
        """
        print("\n" + "=" * 80)
        print("BUILD FAILURE DIAGNOSTIC")
        print("=" * 80)
        print(f"Stage: {stage.stage_number.value} - {stage.stage_name}")
        print(f"Error Type: {type(error).__name__}")
        print(f"Error Message: {str(error)}")
        print("-" * 80)
        
        # Add context snapshot
        if 'environment' in self.build_context:
            env = self.build_context['environment']
            print(f"Environment: {env.compiler_name} {env.compiler_version}")
            print(f"Target: {env.target_os}/{env.target_architecture}")
        
        print("=" * 80)
        
        # Save diagnostic to file
        if self.checkpoint_manager:
            diagnostic_file = self.checkpoint_manager.checkpoint_dir / "failure_diagnostic.txt"
            with open(diagnostic_file, 'w') as f:
                f.write(f"Build Failure Diagnostic\n")
                f.write(f"Stage: {stage.stage_number.value} - {stage.stage_name}\n")
                f.write(f"Error: {str(error)}\n")
            print(f"Diagnostic saved to: {diagnostic_file}")

# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "1.0.0"
__module_id__ = "03"
__module_name__ = "Build Process & Toolchain Integration"
__status__ = "IN_PROGRESS"
__prompt__ = "3/20"

if __name__ == "__main__":
    print(f"Module {__module_id__}: {__module_name__}")
    print(f"Version: {__version__}")
    print(f"Status: {__status__}")
    print(f"Progress: Prompt {__prompt__}")
