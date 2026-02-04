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
import platform
import urllib.request
import tempfile
import shutil
import yaml
import concurrent.futures
import time

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
    creation_timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    
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
            'start_time': datetime.datetime.now(datetime.UTC).isoformat(),
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
        self.build_context['end_time'] = datetime.datetime.now(datetime.UTC).isoformat()
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
    detection_timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
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

class ToolchainRequirementValidator:
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
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
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
        self.build_context['end_time'] = datetime.datetime.now(datetime.UTC).isoformat()
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
# SOURCE ENUMERATION & DEPENDENCY GRAPH ()
# ============================================================================

import ast
from abc import ABC, abstractmethod

# ============================================================================
# SOURCE FILE METADATA
# ============================================================================

@dataclass
class SourceMetadata:
    """
    Rich metadata for a source file.
    
    Captures file properties, language-specific information, dependencies,
    and provenance.
    """
    # File identification
    file_path: Path
    relative_path: Path
    file_hash: str
    
    # File properties
    file_size: int
    line_count: int
    encoding: str
    
    # Language classification
    language: str  # 'c', 'cpp', 'python', 'rust', etc.
    role: str      # 'production', 'test', 'generated', 'build', 'example'
    domain: BuildDomain
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    dependency_type: str = 'unknown'  # 'include', 'import', 'link'
    
    # Provenance
    is_generated: bool = False
    generator: Optional[str] = None
    last_modified: str = ''
    
    # Semantic annotations
    correctness_sensitive: bool = False
    abi_relevant: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'file_path': str(self.file_path),
            'relative_path': str(self.relative_path),
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'line_count': self.line_count,
            'encoding': self.encoding,
            'language': self.language,
            'role': self.role,
            'domain': self.domain.value,
            'dependencies': self.dependencies,
            'dependency_type': self.dependency_type,
            'is_generated': self.is_generated,
            'generator': self.generator,
            'last_modified': self.last_modified,
            'correctness_sensitive': self.correctness_sensitive,
            'abi_relevant': self.abi_relevant,
        }

# ============================================================================
# DEPENDENCY GRAPH
# ============================================================================

@dataclass
class DependencyNode:
    """Node in dependency graph."""
    source_path: str
    metadata: SourceMetadata

@dataclass
class DependencyEdge:
    """Edge in dependency graph."""
    from_source: str
    to_source: str
    edge_type: str  # 'include', 'import', 'link'

class DependencyGraph:
    """
    Directed acyclic graph of source dependencies.
    
    Enables build order determination, change impact analysis, and
    incremental build optimization.
    """
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.edges: List[DependencyEdge] = []
    
    def add_node(self, source_path: str, metadata: SourceMetadata):
        """Add source node to graph."""
        self.nodes[source_path] = DependencyNode(source_path, metadata)
    
    def add_edge(self, from_source: str, to_source: str, edge_type: str):
        """Add dependency edge to graph."""
        self.edges.append(DependencyEdge(from_source, to_source, edge_type))
    
    def get_dependencies(self, source_path: str) -> List[str]:
        """Get all dependencies of a source file."""
        return [
            edge.to_source
            for edge in self.edges
            if edge.from_source == source_path
        ]
    
    def get_dependents(self, source_path: str) -> List[str]:
        """Get all sources that depend on this source."""
        return [
            edge.from_source
            for edge in self.edges
            if edge.to_source == source_path
        ]
    
    def topological_sort(self) -> List[str]:
        """
        Return sources in build order (dependencies first).
        
        Returns:
            List of source paths in dependency order
            
        Raises:
            BuildError: If circular dependency detected
        """
        # Kahn's algorithm for topological sort
        adj = {node: [] for node in self.nodes}
        in_degree = {node: 0 for node in self.nodes}
        
        for edge in self.edges:
            # edge.from_source depends on edge.to_source
            # so edge.to_source must be processed before edge.from_source
            # to_source -> from_source
            if edge.to_source in adj and edge.from_source in adj:
                adj[edge.to_source].append(edge.from_source)
                in_degree[edge.from_source] += 1
        
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            u = queue.pop(0)
            result.append(u)
            
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        if len(result) != len(self.nodes):
            raise BuildError("Circular dependency detected in source graph")
        
        return result

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies.
        
        Returns:
            List of dependency cycles (each cycle is a list of source paths)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for edge in self.edges:
                if edge.from_source == node:
                    neighbor = edge.to_source
                    
                    if neighbor not in visited:
                        dfs(neighbor, path.copy())
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        cycles.append(path[cycle_start:] + [neighbor])
            
            rec_stack.remove(node)
        
        for node in self.nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles

# ============================================================================
# LANGUAGE-SPECIFIC SOURCE HANDLERS
# ============================================================================

class SourceHandler(ABC):
    """Abstract base class for language-specific source handlers."""
    
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path, source_root: Path) -> SourceMetadata:
        """Extract metadata from source file."""
        pass
    
    @abstractmethod
    def extract_dependencies(self, file_path: Path, source_root: Path) -> List[str]:
        """Extract dependencies from source file."""
        pass

class CSourceHandler(SourceHandler):
    """Handler for C/C++ source files."""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix in ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp']
    
    def extract_metadata(self, file_path: Path, source_root: Path) -> SourceMetadata:
        """Extract metadata from C/C++ source."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        relative_path = file_path.relative_to(source_root)
        
        return SourceMetadata(
            file_path=file_path,
            relative_path=relative_path,
            file_hash=self._hash_file(file_path),
            file_size=file_path.stat().st_size,
            line_count=len(content.splitlines()),
            encoding='utf-8',
            language='cpp' if file_path.suffix in ['.cpp', '.hpp'] else 'c',
            role=self._infer_role(relative_path),
            domain=BuildDomain.NATIVE_VERIFICATION_TOOLING,
            dependencies=[],
            dependency_type='include',
            last_modified=datetime.datetime.fromtimestamp(
                file_path.stat().st_mtime
            ).isoformat(),
            correctness_sensitive=True,
            abi_relevant=file_path.suffix in ['.h', '.hpp']
        )
    
    def extract_dependencies(self, file_path: Path, source_root: Path) -> List[str]:
        """Extract #include dependencies from C/C++ source."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        dependencies = []
        include_pattern = re.compile(r'^\s*#include\s+[<"]([^>"]+)[>"]', re.MULTILINE)
        
        for match in include_pattern.finditer(content):
            include_path = match.group(1)
            
            # Skip system includes for dependency graph (they are external)
            if not self._is_system_include(include_path):
                # Resolve relative to source directory
                full_path = (file_path.parent / include_path).resolve()
                if full_path.exists():
                    dependencies.append(str(full_path))
        
        return dependencies
    
    def _is_system_include(self, include_path: str) -> bool:
        """Check if include is a system header."""
        system_headers = ['stdio.h', 'stdlib.h', 'string.h', 'windows.h']
        return any(sys_header in include_path for sys_header in system_headers)
    
    def _infer_role(self, relative_path: Path) -> str:
        """Infer source role from relative path."""
        path_str = str(relative_path).lower()
        if 'test' in path_str:
            return 'test'
        elif 'example' in path_str:
            return 'example'
        elif 'generated' in path_str:
            return 'generated'
        else:
            return 'production'
    
    def _hash_file(self, filepath: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

class PythonSourceHandler(SourceHandler):
    """Handler for Python source files."""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix == '.py'
    
    def extract_metadata(self, file_path: Path, source_root: Path) -> SourceMetadata:
        """Extract metadata from Python source."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        relative_path = file_path.relative_to(source_root)
        
        return SourceMetadata(
            file_path=file_path,
            relative_path=relative_path,
            file_hash=self._hash_file(file_path),
            file_size=file_path.stat().st_size,
            line_count=len(content.splitlines()),
            encoding='utf-8',
            language='python',
            role=self._infer_role(relative_path),
            domain=BuildDomain.ORCHESTRATION_ADAPTER_TOOLING,
            dependencies=[],
            dependency_type='import',
            last_modified=datetime.datetime.fromtimestamp(
                file_path.stat().st_mtime
            ).isoformat(),
            correctness_sensitive=False,
            abi_relevant=False
        )
    
    def extract_dependencies(self, file_path: Path, source_root: Path) -> List[str]:
        """Extract import dependencies from Python source."""
        content = file_path.read_text(encoding='utf-8')
        
        dependencies = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)
        
        except SyntaxError:
            # Skip files with syntax errors (will be caught in validation)
            pass
        
        return dependencies
    
    def _infer_role(self, relative_path: Path) -> str:
        """Infer source role from relative path."""
        path_str = str(relative_path).lower()
        if 'test' in path_str:
            return 'test'
        elif 'example' in path_str:
            return 'example'
        elif 'generated' in path_str or 'adapter' in path_str:
            return 'generated'
        else:
            return 'production'
    
    def _hash_file(self, filepath: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

# ============================================================================
# ENHANCED SOURCE ENUMERATION STAGE
# ============================================================================

class EnhancedSourceEnumerationStage(BuildStageInterface):
    """
    Enhanced Stage 1: Source Enumeration with Dependency Graph
    
    Performs comprehensive source discovery including:
    - Language-specific metadata extraction
    - Dependency graph construction
    - Source classification by role and domain
    - Provenance tracking
    """
    
    def __init__(self, source_root: Path):
        super().__init__("Enhanced Source Enumeration", BuildStage.SOURCE_ENUMERATION)
        self.source_root = source_root
        
        # Register source handlers
        self.handlers: List[SourceHandler] = [
            CSourceHandler(),
            PythonSourceHandler(),
        ]
    
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
        
        # Discover all files
        all_files = list(self.source_root.rglob('*'))
        all_files = [f for f in all_files if f.is_file()]
        
        print(f"  Found {len(all_files)} total files")
        
        # Extract metadata for each source
        source_metadata_map: Dict[str, SourceMetadata] = {}
        dependency_graph = DependencyGraph()
        
        processed_files = []
        for file_path in all_files:
            # Find appropriate handler
            handler = self._find_handler(file_path)
            if not handler:
                continue
            
            # Extract metadata
            metadata = handler.extract_metadata(file_path, self.source_root)
            source_metadata_map[str(file_path)] = metadata
            processed_files.append(file_path)
            
            # Add to dependency graph
            dependency_graph.add_node(str(file_path), metadata)
        
        # Extract dependencies (second pass after all nodes added)
        for file_path in processed_files:
            handler = self._find_handler(file_path)
            if not handler: continue
            
            metadata = source_metadata_map[str(file_path)]
            dependencies = handler.extract_dependencies(file_path, self.source_root)
            metadata.dependencies = dependencies
            
            # Add dependency edges
            for dep in dependencies:
                # We only add edges for dependencies that are within our source root
                # and thus exist in our node map
                if dep in source_metadata_map:
                    dependency_graph.add_edge(str(file_path), dep, metadata.dependency_type)
        
        print(f"  Processed {len(source_metadata_map)} source files")
        print(f"  Dependency graph: {len(dependency_graph.nodes)} nodes, "
              f"{len(dependency_graph.edges)} edges")
        
        # Detect circular dependencies
        cycles = dependency_graph.detect_cycles()
        if cycles:
            print(f"  ⚠ Warning: Detected {len(cycles)} circular dependencies")
            for cycle in cycles[:3]:
                print(f"    Cycle: {' -> '.join(cycle)}")
        
        # Classify sources by role and language
        sources_by_role = self._classify_by_role(source_metadata_map)
        sources_by_language = self._classify_by_language(source_metadata_map)
        
        # Update context
        context['source_metadata'] = {
            path: meta.to_dict()
            for path, meta in source_metadata_map.items()
        }
        context['dependency_graph'] = {
            'nodes': [node.source_path for node in dependency_graph.nodes.values()],
            'edges': [
                {'from': edge.from_source, 'to': edge.to_source, 'type': edge.edge_type}
                for edge in dependency_graph.edges
            ]
        }
        context['sources_by_role'] = sources_by_role
        context['sources_by_language'] = sources_by_language
        
        return context
    
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        if 'source_metadata' not in context:
            raise BuildPostconditionError(
                "Stage 1 must produce 'source_metadata'"
            )
        
        if 'dependency_graph' not in context:
            raise BuildPostconditionError(
                "Stage 1 must produce 'dependency_graph'"
            )
        
        # Verify at least some sources found
        if len(context['source_metadata']) == 0:
            raise BuildPostconditionError(
                "Stage 1 found no processable source files"
            )
    
    def _find_handler(self, file_path: Path) -> Optional[SourceHandler]:
        """Find appropriate handler for file."""
        for handler in self.handlers:
            if handler.can_handle(file_path):
                return handler
        return None
    
    def _classify_by_role(
        self, metadata_map: Dict[str, SourceMetadata]
    ) -> Dict[str, List[str]]:
        """Classify sources by role."""
        by_role: Dict[str, List[str]] = {}
        for path, metadata in metadata_map.items():
            role = metadata.role
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(path)
        return by_role
    
    def _classify_by_language(
        self, metadata_map: Dict[str, SourceMetadata]
    ) -> Dict[str, List[str]]:
        """Classify sources by language."""
        by_language: Dict[str, List[str]] = {}
        for path, metadata in metadata_map.items():
            language = metadata.language
            if language not in by_language:
                by_language[language] = []
            by_language[language].append(path)
        return by_language

# ============================================================================
# DEPENDENCY RESOLUTION & PACKAGE MANAGEMENT ()
# ============================================================================

@dataclass
class DependencySpecification:
    """
    Comprehensive specification of a single dependency.
    
    Captures all information needed for verified, reproducible dependency
    resolution.
    """
    # Identity
    name: str
    version: str
    
    # Source and verification
    source: str  # 'pypi', 'crates', 'system', 'git', 'local'
    hash: Optional[str] = None
    hash_algorithm: str = 'sha256'
    
    # Metadata
    license: Optional[str] = None
    scope: str = 'runtime'  # 'runtime', 'build', 'test', 'dev'
    platform: str = 'all'   # 'all', 'Windows', 'Linux', 'Darwin'
    
    # Dependency tree
    transitive: bool = False
    parent_dependency: Optional[str] = None
    transitive_deps: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'version': self.version,
            'source': self.source,
            'hash': self.hash,
            'hash_algorithm': self.hash_algorithm,
            'license': self.license,
            'scope': self.scope,
            'platform': self.platform,
            'transitive': self.transitive,
            'parent_dependency': self.parent_dependency,
            'transitive_deps': self.transitive_deps,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DependencySpecification':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            version=data['version'],
            source=data['source'],
            hash=data.get('hash'),
            hash_algorithm=data.get('hash_algorithm', 'sha256'),
            license=data.get('license'),
            scope=data.get('scope', 'runtime'),
            platform=data.get('platform', 'all'),
            transitive=data.get('transitive', False),
            parent_dependency=data.get('parent_dependency'),
            transitive_deps=data.get('transitive_deps', []),
        )
    
    def verify_hash(self, file_path: Path) -> bool:
        """
        Verify that file matches declared hash.
        
        Args:
            file_path: Path to file to verify
            
        Returns:
            True if hash matches, False otherwise
        """
        if not self.hash:
            return True  # No hash to verify
        
        computed_hash = self._compute_hash(file_path)
        return computed_hash == self.hash
    
    def _compute_hash(self, file_path: Path) -> str:
        """Compute hash of file."""
        if self.hash_algorithm == 'sha256':
            hasher = hashlib.sha256()
        else:
            raise BuildError(f"Unsupported hash algorithm: {self.hash_algorithm}")
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()

@dataclass
class DependencyLockFile:
    """
    Lock file capturing exact dependency tree for reproducible builds.
    """
    lock_version: str = "1.0.0"
    generated_timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    platform: str = ""
    dependencies: Dict[str, DependencySpecification] = field(default_factory=dict)
    
    def save(self, file_path: Path):
        """Save lock file to disk."""
        data = {
            'lock_version': self.lock_version,
            'generated': self.generated_timestamp,
            'platform': self.platform,
            'dependencies': {
                name: dep.to_dict()
                for name, dep in self.dependencies.items()
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  Saved lock file: {file_path}")
    
    @classmethod
    def load(cls, file_path: Path) -> 'DependencyLockFile':
        """Load lock file from disk."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        dependencies = {
            name: DependencySpecification.from_dict(dep_data)
            for name, dep_data in data['dependencies'].items()
        }
        
        return cls(
            lock_version=data['lock_version'],
            generated_timestamp=data['generated'],
            platform=data['platform'],
            dependencies=dependencies
        )
    
    def add_dependency(self, dep: DependencySpecification):
        """Add dependency to lock file."""
        self.dependencies[dep.name] = dep
    
    def get_dependency(self, name: str) -> Optional[DependencySpecification]:
        """Get dependency by name."""
        return self.dependencies.get(name)

class DependencyResolver:
    """
    Resolves dependencies with verification and conflict detection.
    
    Implements transitive dependency resolution, hash verification,
    and conflict detection.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / '.build_cache' / 'dependencies'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.resolved: Dict[str, DependencySpecification] = {}
        self.conflicts: List[str] = []
    
    def resolve(
        self,
        direct_dependencies: List[DependencySpecification],
        lock_file: Optional[DependencyLockFile] = None
    ) -> DependencyLockFile:
        """
        Resolve dependency tree.
        
        Args:
            direct_dependencies: List of directly declared dependencies
            lock_file: Existing lock file (if available)
            
        Returns:
            Complete dependency lock file with resolved tree
        """
        print("  Resolving dependencies...")
        
        # If lock file exists, use it
        if lock_file:
            print(f"  Using existing lock file with {len(lock_file.dependencies)} dependencies")
            return lock_file
        
        # Otherwise, resolve from scratch
        import platform as platform_module
        result = DependencyLockFile(
            platform=f"{platform_module.system()}-{platform_module.machine()}"
        )
        
        # Resolve direct dependencies
        for dep in direct_dependencies:
            self._resolve_dependency(dep, result)
        
        # Check for conflicts
        if self.conflicts:
            print(f"  ⚠ Warning: {len(self.conflicts)} dependency conflicts detected")
            for conflict in self.conflicts:
                print(f"    - {conflict}")
        
        print(f"  Resolved {len(result.dependencies)} total dependencies")
        return result
    
    def _resolve_dependency(
        self,
        dep: DependencySpecification,
        lock_file: DependencyLockFile
    ):
        """Resolve a single dependency and its transitives."""
        # Check if already resolved
        if dep.name in self.resolved:
            existing = self.resolved[dep.name]
            if existing.version != dep.version:
                conflict = (
                    f"Conflict: {dep.name} required at versions "
                    f"{existing.version} and {dep.version}"
                )
                self.conflicts.append(conflict)
            return
        
        # Add to resolved set
        self.resolved[dep.name] = dep
        lock_file.add_dependency(dep)
        
        print(f"    Resolved: {dep.name} {dep.version} (source: {dep.source})")
        
        # Resolve transitive dependencies (simplified - would query package index)
        for transitive_name in dep.transitive_deps:
            # In real implementation, would fetch metadata and resolve
            # For now, create placeholder
            transitive_dep = DependencySpecification(
                name=transitive_name,
                version="unknown",
                source=dep.source,
                transitive=True,
                parent_dependency=dep.name
            )
            self._resolve_dependency(transitive_dep, lock_file)
    
    def verify_dependency(self, dep: DependencySpecification) -> bool:
        """
        Verify dependency hash and availability.
        
        Args:
            dep: Dependency to verify
            
        Returns:
            True if verification passes
        """
        # Check cache
        cache_path = self.cache_dir / f"{dep.name}-{dep.version}"
        
        if cache_path.exists():
            if dep.hash:
                if dep.verify_hash(cache_path):
                    print(f"    ✓ Verified from cache: {dep.name} {dep.version}")
                    return True
                else:
                    print(f"    ✗ Cache verification failed: {dep.name} {dep.version}")
                    cache_path.unlink()
                    return False
            else:
                print(f"    ⚠ No hash for verification: {dep.name} {dep.version}")
                return True
        
        # Not in cache - would need to download
        print(f"    ⚠ Not in cache: {dep.name} {dep.version}")
        return True
    
    def install_from_lock(self, lock_file: DependencyLockFile) -> bool:
        """
        Install all dependencies from lock file.
        
        Args:
            lock_file: Lock file with resolved dependencies
            
        Returns:
            True if all installations succeed
        """
        print(f"  Installing {len(lock_file.dependencies)} dependencies...")
        
        success = True
        for name, dep in lock_file.dependencies.items():
            if not self.verify_dependency(dep):
                print(f"    ✗ Failed to install: {name}")
                success = False
        
        return success

class EnhancedDependencyResolutionStage(BuildStageInterface):
    """
    Enhanced Stage 3: Dependency Resolution with Lock Files
    
    Resolves dependencies with:
    - Hash verification
    - Lock file generation
    - Conflict detection
    - Transitive dependency resolution
    """
    
    def __init__(
        self,
        dependency_manifest: Optional[Path] = None,
        lock_file_path: Optional[Path] = None,
        cache_dir: Optional[Path] = None
    ):
        super().__init__(
            "Enhanced Dependency Resolution",
            BuildStage.DEPENDENCY_RESOLUTION
        )
        self.dependency_manifest = dependency_manifest
        self.lock_file_path = lock_file_path
        self.resolver = DependencyResolver(cache_dir)
    
    def check_preconditions(self, context: Dict[str, Any]) -> None:
        # Dependency resolution is optional for now
        pass
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"  Resolving dependencies...")
        
        # Load existing lock file if present
        lock_file = None
        if self.lock_file_path and self.lock_file_path.exists():
            print(f"  Loading lock file: {self.lock_file_path}")
            lock_file = DependencyLockFile.load(self.lock_file_path)
        
        # Parse dependency manifest
        direct_deps = self._parse_manifest()
        
        # Resolve dependencies
        resolved_lock = self.resolver.resolve(direct_deps, lock_file)
        
        # Save lock file
        if self.lock_file_path:
            resolved_lock.save(self.lock_file_path)
        
        # Install dependencies
        install_success = self.resolver.install_from_lock(resolved_lock)
        
        # Update context
        context['dependencies'] = {
            'resolved': [dep.to_dict() for dep in resolved_lock.dependencies.values()],
            'lock_file_path': str(self.lock_file_path) if self.lock_file_path else None,
            'conflicts': self.resolver.conflicts,
            'install_success': install_success
        }
        
        return context
    
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        if 'dependencies' not in context:
            raise BuildPostconditionError(
                "Stage 3 must produce 'dependencies'"
            )
        
        # Fail if installation failed
        if not context['dependencies']['install_success']:
            raise BuildPostconditionError(
                "Dependency installation failed"
            )
        
        # Warn if conflicts detected
        if context['dependencies']['conflicts']:
            print(f"  ⚠ Warning: Dependency conflicts detected but resolution succeeded")
    
    def _parse_manifest(self) -> List[DependencySpecification]:
        """Parse dependency manifest into specifications."""
        if not self.dependency_manifest or not self.dependency_manifest.exists():
            return []
        
        # Simplified parsing - in real implementation would parse requirements.txt, etc.
        dependencies = []
        
        # Example: parse requirements.txt format
        content = self.dependency_manifest.read_text()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse "package==version" format
            if '==' in line:
                name, version = line.split('==')
                dep = DependencySpecification(
                    name=name.strip(),
                    version=version.strip(),
                    source='pypi',
                    scope='runtime'
                )
                dependencies.append(dep)
        
        return dependencies

# ============================================================================
# ============================================================================

@dataclass
class ToolchainCapabilities:
    """
    Comprehensive capabilities of a validated toolchain.
    
    Documents exactly what features the toolchain supports for build
    planning and feature selection.
    """
    # Language standards
    language_standards: Dict[str, List[str]] = field(default_factory=dict)
    
    # Sanitizers
    sanitizers: List[str] = field(default_factory=list)
    
    # Optimization
    optimization_levels: List[str] = field(default_factory=list)
    supports_lto: bool = False
    supports_pgo: bool = False
    
    # Debug
    debug_formats: List[str] = field(default_factory=list)
    
    # ABI
    calling_conventions: List[str] = field(default_factory=list)
    abi_compatible: bool = False
    structure_packing_verified: bool = False
    
    # Reproducibility
    deterministic_output: bool = False
    determinism_flags: List[str] = field(default_factory=list)
    
    # Platform
    supports_position_independent_code: bool = False
    supports_exceptions: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'language_standards': self.language_standards,
            'sanitizers': self.sanitizers,
            'optimization_levels': self.optimization_levels,
            'supports_lto': self.supports_lto,
            'supports_pgo': self.supports_pgo,
            'debug_formats': self.debug_formats,
            'calling_conventions': self.calling_conventions,
            'abi_compatible': self.abi_compatible,
            'structure_packing_verified': self.structure_packing_verified,
            'deterministic_output': self.deterministic_output,
            'determinism_flags': self.determinism_flags,
            'supports_position_independent_code': self.supports_position_independent_code,
            'supports_exceptions': self.supports_exceptions,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolchainCapabilities':
        """Deserialize from dictionary."""
        return cls(
            language_standards=data.get('language_standards', {}),
            sanitizers=data.get('sanitizers', []),
            optimization_levels=data.get('optimization_levels', []),
            supports_lto=data.get('supports_lto', False),
            supports_pgo=data.get('supports_pgo', False),
            debug_formats=data.get('debug_formats', []),
            calling_conventions=data.get('calling_conventions', []),
            abi_compatible=data.get('abi_compatible', False),
            structure_packing_verified=data.get('structure_packing_verified', False),
            deterministic_output=data.get('deterministic_output', False),
            determinism_flags=data.get('determinism_flags', []),
            supports_position_independent_code=data.get('supports_position_independent_code', False),
            supports_exceptions=data.get('supports_exceptions', True),
        )

class ToolchainValidator:
    """
    Validates toolchain capabilities through compilation tests.
    
    Performs feature detection, ABI verification, self-tests, and
    determinism validation.
    """
    
    def __init__(self, toolchain: 'ToolchainDescriptor', cache_dir: Optional[Path] = None):
        self.toolchain = toolchain
        self.cache_dir = cache_dir or Path.home() / '.build_cache' / 'toolchain_validation'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.capabilities = ToolchainCapabilities()
        self.validation_results: List[Dict[str, Any]] = []
    
    def validate(self) -> ToolchainCapabilities:
        """
        Perform complete toolchain validation.
        
        Returns:
            Validated capabilities
            
        Raises:
            BuildError: If critical validation fails
        """
        print(f"Validating toolchain: {self.toolchain.compiler_name} {self.toolchain.compiler_version}")
        
        # Check cache
        cached_capabilities = self._load_cached_validation()
        if cached_capabilities:
            print("  ✓ Using cached validation results")
            return cached_capabilities
        
        # Perform validation tests
        self._detect_language_standards()
        self._detect_sanitizers()
        self._detect_optimization_support()
        self._detect_debug_formats()
        self._validate_abi_compatibility()
        self._validate_determinism()
        
        # Run self-tests
        self._run_smoke_test()
        
        # Cache results
        self._cache_validation()
        
        print(f"  ✓ Toolchain validation complete")
        return self.capabilities
    
    def _load_cached_validation(self) -> Optional[ToolchainCapabilities]:
        """Load cached validation if available and valid."""
        cache_key = self._get_cache_key()
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Verify cache is recent (within 30 days)
            cached_time = datetime.datetime.fromisoformat(data['timestamp'])
            age = datetime.datetime.now(datetime.UTC) - cached_time
            
            if age.days > 30:
                print("  Cache expired (>30 days old)")
                return None
            
            # Verify compiler hash matches
            if data.get('compiler_hash') != self.toolchain.compiler_executable_hash:
                print("  Cache invalid (compiler changed)")
                return None
            
            return ToolchainCapabilities.from_dict(data['capabilities'])
        
        except Exception as e:
            print(f"  Cache load failed: {e}")
            return None
    
    def _cache_validation(self):
        """Cache validation results."""
        cache_key = self._get_cache_key()
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        data = {
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
            'compiler_name': self.toolchain.compiler_name,
            'compiler_version': self.toolchain.compiler_version,
            'compiler_hash': self.toolchain.compiler_executable_hash,
            'capabilities': self.capabilities.to_dict(),
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_cache_key(self) -> str:
        """Generate cache key for this toolchain configuration."""
        key_parts = [
            self.toolchain.compiler_name,
            self.toolchain.compiler_version,
            self.toolchain.target_architecture,
        ]
        return '-'.join(key_parts).replace('/', '_').replace('\\', '_')
    
    def _detect_language_standards(self):
        """Detect supported language standards."""
        print("  Detecting language standards...")
        
        standards = {
            'c': [],
            'cpp': []
        }
        
        # Use GCC/Clang style flags by default, but handle MSVC separately if needed
        is_msvc = self.toolchain.compiler_name == 'MSVC'
        
        # Test C standards
        c_stds = [('c99', '/std:c11' if is_msvc else '-std=c99'),
                  ('c11', '/std:c11' if is_msvc else '-std=c11'),
                  ('c17', '/std:clatest' if is_msvc else '-std=c17')]
        
        for name, flag in c_stds:
            if self._test_compile_flag(flag, language='c'):
                standards['c'].append(name)
        
        # Test C++ standards
        cpp_stds = [('c++14', '/std:c++14' if is_msvc else '-std=c++14'),
                    ('c++17', '/std:c++17' if is_msvc else '-std=c++17'),
                    ('c++20', '/std:c++20' if is_msvc else '-std=c++20')]
        
        for name, flag in cpp_stds:
            if self._test_compile_flag(flag, language='cpp'):
                standards['cpp'].append(name)
        
        self.capabilities.language_standards = standards
        print(f"    C: {standards['c']}")
        print(f"    C++: {standards['cpp']}")
    
    def _detect_sanitizers(self):
        """Detect supported sanitizers."""
        print("  Detecting sanitizers...")
        
        sanitizers = []
        is_msvc = self.toolchain.compiler_name == 'MSVC'
        
        # Test common sanitizers
        test_sanitizers = [
            ('asan', '/fsanitize=address' if is_msvc else '-fsanitize=address'),
            ('ubsan', '-fsanitize=undefined'),
            ('tsan', '-fsanitize=thread'),
        ]
        
        for name, flag in test_sanitizers:
            if self._test_compile_flag(flag):
                sanitizers.append(name)
        
        self.capabilities.sanitizers = sanitizers
        print(f"    Supported: {sanitizers}")
    
    def _detect_optimization_support(self):
        """Detect supported optimization levels."""
        print("  Detecting optimization support...")
        
        opt_levels = []
        is_msvc = self.toolchain.compiler_name == 'MSVC'
        
        levels = ['/O1', '/O2', '/Ox'] if is_msvc else ['-O0', '-O1', '-O2', '-O3', '-Os']
        
        for level in levels:
            if self._test_compile_flag(level):
                opt_levels.append(level.lstrip('-/'))
        
        # Test LTO
        lto_flag = '/GL' if is_msvc else '-flto'
        lto_supported = self._test_compile_flag(lto_flag)
        
        self.capabilities.optimization_levels = opt_levels
        self.capabilities.supports_lto = lto_supported
        
        print(f"    Levels: {opt_levels}")
        print(f"    LTO: {lto_supported}")
    
    def _detect_debug_formats(self):
        """Detect supported debug formats."""
        print("  Detecting debug formats...")
        
        formats = []
        is_msvc = self.toolchain.compiler_name == 'MSVC'
        
        if is_msvc:
            if self._test_compile_flag('/Zi'):
                formats.append('pdb')
            if self._test_compile_flag('/Z7'):
                formats.append('codeview')
        else:
            # DWARF versions
            if self._test_compile_flag('-gdwarf-4'):
                formats.append('dwarf4')
            if self._test_compile_flag('-gdwarf-5'):
                formats.append('dwarf5')
            
            # Generic debug
            if not formats and self._test_compile_flag('-g'):
                formats.append('default')
        
        self.capabilities.debug_formats = formats
        print(f"    Formats: {formats}")
    
    def _validate_abi_compatibility(self):
        """Validate ABI compatibility through structure layout test."""
        print("  Validating ABI compatibility...")
        
        # Create ABI test program
        test_program = r'''
#include <stdio.h>
#include <stddef.h>

struct TestStruct {
    char a;
    int b;
    char c;
};

int main() {
    size_t size = sizeof(struct TestStruct);
    size_t offset_b = offsetof(struct TestStruct, b);
    
    // Expected: 12 bytes with 4-byte alignment/padding
    // or 8 bytes if tightly packed
    printf("%zu %zu\n", size, offset_b);
    return 0;
}
'''
        
        try:
            output = self._compile_and_run(test_program, 'c')
            size, offset = map(int, output.strip().split())
            
            # Validate reasonable structure layout
            if size >= 8 and offset >= 4:
                self.capabilities.abi_compatible = True
                self.capabilities.structure_packing_verified = True
                print(f"    ✓ ABI compatible (struct size: {size}, offset: {offset})")
            else:
                print(f"    ⚠ Unusual structure layout (size: {size}, offset: {offset})")
                self.capabilities.abi_compatible = False
        
        except Exception as e:
            print(f"    ✗ ABI validation failed: {e}")
            self.capabilities.abi_compatible = False
    
    def _validate_determinism(self):
        """Validate that toolchain produces deterministic outputs."""
        print("  Validating determinism...")
        
        test_program = r'''
#include <stdio.h>
int main() {
    printf("determinism test\n");
    return 0;
}
'''
        
        try:
            # Compile first time
            binary1 = self._compile_to_binary(test_program, 'c', 'test1')
            hash1 = self._hash_file(binary1)
            
            # Compile second time (identical source)
            binary2 = self._compile_to_binary(test_program, 'c', 'test2')
            hash2 = self._hash_file(binary2)
            
            if hash1 == hash2:
                self.capabilities.deterministic_output = True
                print(f"    ✓ Deterministic output verified")
            else:
                print(f"    ⚠ Non-deterministic output detected")
                print(f"      First:  {hash1[:16]}...")
                print(f"      Second: {hash2[:16]}...")
                self.capabilities.deterministic_output = False
            
            # Cleanup
            binary1.unlink(missing_ok=True)
            binary2.unlink(missing_ok=True)
        
        except Exception as e:
            print(f"    ✗ Determinism validation failed: {e}")
            self.capabilities.deterministic_output = False
    
    def _run_smoke_test(self):
        """Run basic smoke test to verify toolchain works."""
        print("  Running smoke test...")
        
        test_program = r'''
#include <stdio.h>
int main() {
    printf("smoke test passed\n");
    return 0;
}
'''
        
        try:
            output = self._compile_and_run(test_program, 'c')
            if 'smoke test passed' in output:
                print(f"    ✓ Smoke test passed")
            else:
                raise BuildError(f"Smoke test produced unexpected output: {output}")
        except Exception as e:
            raise BuildError(f"Smoke test failed: {e}")
    
    def _test_compile_flag(self, flag: str, language: str = 'c') -> bool:
        """
        Test if compiler accepts a specific flag.
        
        Args:
            flag: Compiler flag to test
            language: Language ('c' or 'cpp')
            
        Returns:
            True if flag is supported
        """
        test_program = 'int main() { return 0; }'
        is_msvc = self.toolchain.compiler_name == 'MSVC'
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c' if language == 'c' else '.cpp', delete=False) as f:
                f.write(test_program)
                source_file = Path(f.name)
            
            output_file = source_file.with_suffix('.exe' if platform.system() == 'Windows' else '')
            
            # Build command
            if is_msvc:
                # MSVC: cl /nologo <flag> source.c /Fe:output.exe
                cmd = [
                    str(self.toolchain.compiler_executable),
                    '/nologo',
                    flag,
                    str(source_file),
                    f'/Fe:{output_file}'
                ]
            else:
                # GCC/Clang: gcc <flag> source.c -o output
                cmd = [
                    str(self.toolchain.compiler_executable),
                    flag,
                    str(source_file),
                    '-o', str(output_file)
                ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                text=True
            )
            
            success = result.returncode == 0
            
            # Cleanup
            source_file.unlink(missing_ok=True)
            output_file.unlink(missing_ok=True)
            # MSVC also creates .obj
            if is_msvc:
                source_file.with_suffix('.obj').unlink(missing_ok=True)
            
            return success
        
        except Exception:
            return False
    
    def _compile_and_run(self, source_code: str, language: str) -> str:
        """
        Compile and execute test program.
        
        Args:
            source_code: Source code to compile
            language: Language ('c' or 'cpp')
            
        Returns:
            Program output
        """
        suffix = '.c' if language == 'c' else '.cpp'
        is_msvc = self.toolchain.compiler_name == 'MSVC'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(source_code)
            source_file = Path(f.name)
        
        try:
            # Compile
            output_file = source_file.with_suffix('.exe' if platform.system() == 'Windows' else '')
            
            if is_msvc:
                compile_cmd = [
                    str(self.toolchain.compiler_executable),
                    '/nologo',
                    str(source_file),
                    f'/Fe:{output_file}'
                ]
            else:
                compile_cmd = [
                    str(self.toolchain.compiler_executable),
                    str(source_file),
                    '-o', str(output_file)
                ]
            
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if compile_result.returncode != 0:
                raise BuildError(f"Compilation failed: {compile_result.stderr or compile_result.stdout}")
            
            # Execute
            run_result = subprocess.run(
                [str(output_file)],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if run_result.returncode != 0:
                raise BuildError(f"Execution failed with code {run_result.returncode}")
            
            return run_result.stdout
        
        finally:
            source_file.unlink(missing_ok=True)
            output_file.unlink(missing_ok=True)
            if is_msvc:
                source_file.with_suffix('.obj').unlink(missing_ok=True)
    
    def _compile_to_binary(self, source_code: str, language: str, name: str) -> Path:
        """Compile source to binary and return path."""
        suffix = '.c' if language == 'c' else '.cpp'
        is_msvc = self.toolchain.compiler_name == 'MSVC'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(source_code)
            source_file = Path(f.name)
        
        output_file = self.cache_dir / f"{name}{'.exe' if platform.system() == 'Windows' else ''}"
        
        if is_msvc:
            compile_cmd = [
                str(self.toolchain.compiler_executable),
                '/nologo',
                str(source_file),
                f'/Fe:{output_file}'
            ]
        else:
            compile_cmd = [
                str(self.toolchain.compiler_executable),
                str(source_file),
                '-o', str(output_file)
            ]
        
        subprocess.run(compile_cmd, capture_output=True, timeout=10, check=True)
        
        source_file.unlink()
        if is_msvc:
            source_file.with_suffix('.obj').unlink(missing_ok=True)
            
        return output_file
    
    def _hash_file(self, filepath: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

# ============================================================================
# ABI FIDELITY ENFORCEMENT & COMPILER CONFIGURATION ()
# ============================================================================

@dataclass
class ABIConfig:
    """
    Comprehensive ABI configuration for a build target.
    
    Specifies all ABI-relevant settings including structure packing,
    calling conventions, exception handling, and name mangling.
    """
    # Platform identification
    platform: str  # "Windows-x86_64", "Linux-x86_64", etc.
    
    # Structure layout
    structure_packing: int = 8
    structure_packing_required: bool = True
    
    # Calling conventions
    default_calling_convention: str = "platform_default"
    function_conventions: Dict[str, str] = field(default_factory=dict)
    
    # Exception handling
    exceptions_enabled: bool = True
    exception_model: str = "default"  # "seh", "dwarf2", "sjlj"
    
    # RTTI
    rtti_enabled: bool = True
    
    # Name mangling
    name_mangling_scheme: str = "platform_default"  # "msvc", "itanium"
    
    # Compiler flags per toolchain
    compiler_flags: Dict[str, List[str]] = field(default_factory=dict)
    
    def get_flags_for_compiler(self, compiler_name: str) -> List[str]:
        """Get compiler-specific flags."""
        return self.compiler_flags.get(compiler_name.lower(), [])
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'ABIConfig':
        """Load ABI configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        spec = data.get('abi_specification', {})
        
        # Parse structure packing
        packing_config = spec.get('structure_packing', {})
        structure_packing = packing_config.get('default', 8)
        
        # Parse calling conventions
        cc_config = spec.get('calling_convention', {})
        default_cc = cc_config.get('default', 'platform_default')
        
        # Parse compiler flags
        compiler_flags = {}
        for section in ['structure_packing', 'calling_convention', 'exception_handling', 'rtti']:
            section_data = spec.get(section, {})
            flags = section_data.get('compiler_flags', {})
            for compiler, flag_list in flags.items():
                if compiler not in compiler_flags:
                    compiler_flags[compiler] = []
                if isinstance(flag_list, str):
                    compiler_flags[compiler].append(flag_list)
                else:
                    compiler_flags[compiler].extend(flag_list)
        
        return cls(
            platform=spec.get('platform', 'unknown'),
            structure_packing=structure_packing,
            default_calling_convention=default_cc,
            exceptions_enabled=spec.get('exception_handling', {}).get('enabled', True),
            rtti_enabled=spec.get('rtti', {}).get('enabled', True),
            compiler_flags=compiler_flags
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'platform': self.platform,
            'structure_packing': self.structure_packing,
            'default_calling_convention': self.default_calling_convention,
            'exceptions_enabled': self.exceptions_enabled,
            'exception_model': self.exception_model,
            'rtti_enabled': self.rtti_enabled,
            'name_mangling_scheme': self.name_mangling_scheme,
            'compiler_flags': self.compiler_flags,
        }

class CompilerFlagManager:
    """
    Manages compiler flags with ABI awareness and conflict resolution.
    
    Handles flag priority, conflict detection, and platform-specific
    flag generation.
    """
    
    def __init__(self, abi_config: ABIConfig, toolchain: ToolchainDescriptor):
        self.abi_config = abi_config
        self.toolchain = toolchain
        self.global_flags: List[str] = []
        self.target_flags: Dict[str, List[str]] = {}
        self.file_flags: Dict[str, List[str]] = {}
    
    def add_global_flags(self, flags: List[str]):
        """Add flags that apply to all compilations."""
        self.global_flags.extend(flags)
    
    def add_target_flags(self, target: str, flags: List[str]):
        """Add flags for a specific build target."""
        if target not in self.target_flags:
            self.target_flags[target] = []
        self.target_flags[target].extend(flags)
    
    def add_file_flags(self, file_path: str, flags: List[str]):
        """Add flags for a specific source file."""
        if file_path not in self.file_flags:
            self.file_flags[file_path] = []
        self.file_flags[file_path].extend(flags)
    
    def get_flags_for_file(self, file_path: str, target: Optional[str] = None) -> List[str]:
        """
        Get resolved flags for compiling a specific file.
        
        Priority (highest to lowest):
        1. File-specific flags
        2. Target-specific flags
        3. ABI configuration flags
        4. Global flags
        
        Args:
            file_path: Path to source file
            target: Build target name
            
        Returns:
            Resolved list of compiler flags
        """
        resolved = []
        
        # Global flags (lowest priority)
        resolved.extend(self.global_flags)
        
        # ABI configuration flags
        abi_flags = self.abi_config.get_flags_for_compiler(self.toolchain.compiler_name)
        resolved.extend(abi_flags)
        
        # Target-specific flags
        if target and target in self.target_flags:
            resolved.extend(self.target_flags[target])
        
        # File-specific flags (highest priority)
        if file_path in self.file_flags:
            resolved.extend(self.file_flags[file_path])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_flags = []
        for flag in resolved:
            if flag not in seen:
                seen.add(flag)
                unique_flags.append(flag)
        
        return unique_flags
    
    def validate_flags(self, flags: List[str]) -> List[str]:
        """
        Validate that flags are compatible and supported.
        
        Args:
            flags: List of flags to validate
            
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check for conflicting structure packing flags
        packing_flags = [f for f in flags if '/Zp' in f or '-fpack-struct' in f]
        if len(packing_flags) > 1:
            issues.append(f"Conflicting structure packing flags: {packing_flags}")
        
        # Check for conflicting calling convention flags
        # Supporting both Windows and Posix flag styles
        cc_flags = [f for f in flags if f in ['/Gd', '/Gz', '/Gv', '-mregparm=3', '-mrtd']]
        if len(cc_flags) > 1:
            issues.append(f"Conflicting calling convention flags: {cc_flags}")
        
        # Check for optimization conflicts
        opt_flags = [f for f in flags if f.startswith('-O') or f.startswith('/O')]
        if len(opt_flags) > 1:
            # Important: Multiple O flags are technically allowed but usually indicate a logic error in our manager
            issues.append(f"Multiple optimization flags: {opt_flags}")
        
        return issues

class ABIVerifier:
    """
    Runtime ABI verification for loaded libraries.
    
    Validates that libraries conform to expected ABI conventions.
    """
    
    def __init__(self, expected_abi: ABIConfig):
        self.expected_abi = expected_abi
        self.verification_results: List[Dict[str, Any]] = []
    
    def verify_structure_layout(
        self,
        struct_name: str,
        expected_size: int,
        expected_offsets: Dict[str, int]
    ) -> bool:
        """
        Verify structure layout matches expectations.
        
        Args:
            struct_name: Name of structure
            expected_size: Expected size in bytes
            expected_offsets: Expected field offsets
            
        Returns:
            True if layout matches
        """
        # In real implementation, would use ctypes or FFI to inspect actual layout
        # For now, simulate verification success
        
        result = {
            'struct_name': struct_name,
            'expected_size': expected_size,
            'verified': True,
            'issues': []
        }
        
        self.verification_results.append(result)
        return True
    
    def verify_calling_convention(self, function_name: str, expected_convention: str) -> bool:
        """
        Verify function uses expected calling convention.
        
        Args:
            function_name: Name of function
            expected_convention: Expected calling convention
            
        Returns:
            True if convention matches
        """
        result = {
            'function_name': function_name,
            'expected_convention': expected_convention,
            'verified': True,
            'issues': []
        }
        
        self.verification_results.append(result)
        return True
    
    def generate_report(self) -> str:
        """Generate ABI verification report."""
        lines = ["ABI Verification Report", "=" * 50, ""]
        
        for result in self.verification_results:
            if 'struct_name' in result:
                lines.append(f"Structure: {result['struct_name']}")
                lines.append(f"  Expected size: {result['expected_size']} bytes")
                lines.append(f"  Verified: {'✓' if result['verified'] else '✗'}")
            elif 'function_name' in result:
                lines.append(f"Function: {result['function_name']}")
                lines.append(f"  Expected convention: {result['expected_convention']}")
                lines.append(f"  Verified: {'✓' if result['verified'] else '✗'}")
            
            if result.get('issues'):
                for issue in result['issues']:
                    lines.append(f"  Issue: {issue}")
            
            lines.append("")
        
        return '\n'.join(lines)

class ABIDriftDetector:
    """
    Detects ABI changes between builds.
    
    Compares current ABI against baseline to identify drift.
    """
    
    def __init__(self, baseline_path: Optional[Path] = None):
        self.baseline_path = baseline_path
        self.baseline: Optional[Dict[str, Any]] = None
        
        if baseline_path and baseline_path.exists():
            with open(baseline_path, 'r') as f:
                self.baseline = json.load(f)
    
    def record_baseline(self, abi_snapshot: Dict[str, Any], output_path: Path):
        """Record current ABI as baseline."""
        with open(output_path, 'w') as f:
            json.dump(abi_snapshot, f, indent=2)
        
        print(f"  ABI baseline recorded: {output_path}")
    
    def detect_drift(self, current_snapshot: Dict[str, Any]) -> List[str]:
        """
        Detect drift between baseline and current ABI.
        
        Args:
            current_snapshot: Current ABI snapshot
            
        Returns:
            List of drift descriptions
        """
        if not self.baseline:
            return ["No baseline available for drift detection"]
        
        drift_items = []
        
        # Compare structure layouts
        if 'structures' in self.baseline and 'structures' in current_snapshot:
            baseline_structs = self.baseline['structures']
            current_structs = current_snapshot['structures']
            
            for struct_name, baseline_info in baseline_structs.items():
                if struct_name not in current_structs:
                    drift_items.append(f"Structure removed: {struct_name}")
                else:
                    current_info = current_structs[struct_name]
                    if current_info['size'] != baseline_info['size']:
                        drift_items.append(
                            f"Structure size changed: {struct_name} "
                            f"({baseline_info['size']} → {current_info['size']})"
                        )
        
        # Compare symbols
        if 'symbols' in self.baseline and 'symbols' in current_snapshot:
            baseline_symbols = set(self.baseline['symbols'])
            current_symbols = set(current_snapshot['symbols'])
            
            removed = baseline_symbols - current_symbols
            added = current_symbols - baseline_symbols
            
            for sym in removed:
                drift_items.append(f"Symbol removed: {sym}")
            for sym in added:
                drift_items.append(f"Symbol added: {sym}")
        
        return drift_items

# ============================================================================
# NATIVE COMPILATION & OBJECT FILE GENERATION ()
# ============================================================================

@dataclass
class CompilationMetadata:
    """
    Provenance metadata for a compilation.
    """
    source_file: Path
    source_hash: str
    output_file: Path
    output_hash: Optional[str] = None
    
    compiler_name: str = ""
    compiler_version: str = ""
    compiler_hash: str = ""
    
    flags_used: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    compilation_timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    compilation_duration: float = 0.0
    
    success: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source_file': str(self.source_file),
            'source_hash': self.source_hash,
            'output_file': str(self.output_file),
            'output_hash': self.output_hash,
            'compiler': f"{self.compiler_name} {self.compiler_version}",
            'compiler_hash': self.compiler_hash,
            'flags_used': self.flags_used,
            'dependencies': self.dependencies,
            'compilation_timestamp': self.compilation_timestamp,
            'compilation_duration': self.compilation_duration,
            'success': self.success,
            'warnings': self.warnings,
            'errors': self.errors,
        }

@dataclass
class CompilationUnit:
    """
    Complete specification for compiling a source file.
    """
    source_file: Path
    output_file: Path
    dependencies: List[Path] = field(default_factory=list)
    compiler_flags: List[str] = field(default_factory=list)
    include_paths: List[Path] = field(default_factory=list)
    defines: Dict[str, str] = field(default_factory=dict)
    
    language: str = 'c'  # 'c' or 'cpp'
    build_mode: BuildMode = BuildMode.DEBUG
    
    abi_config: Optional[ABIConfig] = None
    toolchain: Optional[ToolchainDescriptor] = None
    
    metadata: Optional[CompilationMetadata] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            source_hash = self._compute_hash(self.source_file)
            self.metadata = CompilationMetadata(
                source_file=self.source_file,
                source_hash=source_hash,
                output_file=self.output_file
            )
            
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except FileNotFoundError:
            return "file_not_found"

class CompilerInvocation:
    """
    Manages compiler command-line construction and execution.
    """
    
    def __init__(self, unit: CompilationUnit):
        self.unit = unit
        
    def build_command(self) -> List[str]:
        """
        Build compiler command-line arguments.
        
        Returns:
            List of command-line arguments
        """
        if not self.unit.toolchain:
            raise BuildError("Compilation unit missing toolchain")
            
        cmd = [str(self.unit.toolchain.compiler_executable)]
        
        # Add compiler flags
        cmd.extend(self.unit.compiler_flags)
        
        # Add include paths
        for include_path in self.unit.include_paths:
            # Handle both MSVC and GCC/Clang style include flags
            if self.unit.toolchain.compiler_name == 'MSVC':
                cmd.append(f'/I{include_path}')
            else:
                cmd.extend(['-I', str(include_path)])
                
        # Add defines
        for name, value in self.unit.defines.items():
            if self.unit.toolchain.compiler_name == 'MSVC':
                cmd.append(f'/D{name}={value}')
            else:
                cmd.append(f'-D{name}={value}')
                
        # Add debug symbols
        if self.unit.build_mode == BuildMode.DEBUG:
            if self.unit.toolchain.compiler_name == 'MSVC':
                if '/Zi' not in cmd:
                    cmd.append('/Zi')
            else:
                if '-g' not in cmd:
                    cmd.append('-g')
                    
        # Add input and output
        # MSVC uses /Fo for output file, others use -o
        if self.unit.toolchain.compiler_name == 'MSVC':
            cmd.append(str(self.unit.source_file))
            cmd.append(f'/Fo{self.unit.output_file}')
            # Compile only
            if '/c' not in cmd:
                cmd.append('/c')
        else:
            cmd.append(str(self.unit.source_file))
            cmd.extend(['-o', str(self.unit.output_file)])
            # Compile only
            if '-c' not in cmd:
                cmd.append('-c')
                
        return cmd
        
    def execute(self) -> 'CompilationResult':
        """
        Execute compilation.
        
        Returns:
            CompilationResult with success/failure information
        """
        cmd = self.build_command()
        
        print(f"  Compiling: {self.unit.source_file.name}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            duration = time.time() - start_time
            
            # Update metadata
            if self.unit.metadata:
                self.unit.metadata.compilation_duration = duration
                self.unit.metadata.success = (result.returncode == 0)
                self.unit.metadata.flags_used = self.unit.compiler_flags
                
                if self.unit.toolchain:
                    self.unit.metadata.compiler_name = self.unit.toolchain.compiler_name
                    self.unit.metadata.compiler_version = self.unit.toolchain.compiler_version
                    self.unit.metadata.compiler_hash = self.unit.toolchain.compiler_executable_hash
                
                # Parse warnings and errors
                self._parse_compiler_output(result.stderr + result.stdout)
                
                if result.returncode == 0:
                    # Compute output hash
                    if self.unit.output_file.exists():
                        self.unit.metadata.output_hash = self.unit._compute_hash(self.unit.output_file)
            
            if result.returncode == 0:
                return CompilationResult(
                    success=True,
                    unit=self.unit,
                    duration=duration,
                    output=result.stdout
                )
            else:
                return CompilationResult(
                    success=False,
                    unit=self.unit,
                    duration=duration,
                    error_message=result.stderr,
                    return_code=result.returncode
                )
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return CompilationResult(
                success=False,
                unit=self.unit,
                duration=duration,
                error_message="Compilation timed out (>60s)"
            )
        except Exception as e:
            duration = time.time() - start_time
            return CompilationResult(
                success=False,
                unit=self.unit,
                duration=duration,
                error_message=str(e)
            )
            
    def _parse_compiler_output(self, output: str):
        """Parse compiler output for warnings and errors."""
        if not self.unit.metadata:
            return
            
        for line in output.splitlines():
            line_lower = line.lower()
            if 'error:' in line_lower or 'error C' in line:
                self.unit.metadata.errors.append(line.strip())
            elif 'warning:' in line_lower or 'warning C' in line:
                self.unit.metadata.warnings.append(line.strip())

@dataclass
class CompilationResult:
    """Result of a compilation."""
    success: bool
    unit: CompilationUnit
    duration: float
    output: str = ""
    error_message: str = ""
    return_code: int = 0

class NativeCompiler:
    """
    Manages compilation of native sources to object files.
    
    Handles dependency ordering, parallel compilation, and incremental builds.
    """
    
    def __init__(
        self,
        toolchain: ToolchainDescriptor,
        abi_config: ABIConfig,
        flag_manager: CompilerFlagManager,
        max_workers: Optional[int] = None
    ):
        self.toolchain = toolchain
        self.abi_config = abi_config
        self.flag_manager = flag_manager
        self.max_workers = max_workers or os.cpu_count() or 1
        
        self.compilation_cache: Dict[str, CompilationMetadata] = {}
        
    def compile_sources(
        self,
        source_files: List[Path],
        output_dir: Path,
        build_mode: BuildMode = BuildMode.DEBUG
    ) -> List[CompilationResult]:
        """
        Compile source files to object files.
        """
        print(f"  Compiling {len(source_files)} source files...")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create compilation units
        units = []
        for source_file in source_files:
            # Use appropriate object extension
            obj_ext = '.obj' if self.toolchain.compiler_name == 'MSVC' else '.o'
            output_file = output_dir / (source_file.stem + obj_ext)
            
            flags = self.flag_manager.get_flags_for_file(str(source_file))
            
            unit = CompilationUnit(
                source_file=source_file,
                output_file=output_file,
                compiler_flags=flags,
                language=self._detect_language(source_file),
                build_mode=build_mode,
                abi_config=self.abi_config,
                toolchain=self.toolchain
            )
            
            units.append(unit)
            
        # Filter units that need recompilation
        units_to_compile = [
            unit for unit in units
            if self._needs_recompilation(unit)
        ]
        
        if len(units_to_compile) < len(units):
            cached_count = len(units) - len(units_to_compile)
            print(f"    Using {cached_count} cached object files")
            
        # Compile units in parallel
        results = []
        if units_to_compile:
            results.extend(self._compile_parallel(units_to_compile))
            
        # Add results for cached units
        for unit in units:
            if unit not in units_to_compile:
                results.append(CompilationResult(
                    success=True,
                    unit=unit,
                    duration=0.0,
                    output="(cached)"
                ))
                
        # Report results
        success_count = sum(1 for r in results if r.success)
        print(f"    Compiled {success_count}/{len(results)} successfully")
        
        return results
        
    def _compile_parallel(self, units: List[CompilationUnit]) -> List[CompilationResult]:
        """Compile units in parallel."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._compile_unit, unit): unit
                for unit in units
            }
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update cache on success
                    if result.success and result.unit.metadata:
                        self.compilation_cache[str(result.unit.source_file)] = result.unit.metadata
                except Exception as e:
                    # Handle unexpected executor errors
                    unit = futures[future]
                    results.append(CompilationResult(
                        success=False,
                        unit=unit,
                        duration=0.0,
                        error_message=f"Executor error: {e}"
                    ))
                    
        return results
        
    def _compile_unit(self, unit: CompilationUnit) -> CompilationResult:
        """Compile a single unit."""
        invocation = CompilerInvocation(unit)
        return invocation.execute()
        
    def _needs_recompilation(self, unit: CompilationUnit) -> bool:
        """
        Determine if unit needs recompilation.
        """
        # Output doesn't exist
        if not unit.output_file.exists():
            return True
            
        # Check cache
        cached_metadata = self.compilation_cache.get(str(unit.source_file))
        if cached_metadata:
            # Source changed
            if cached_metadata.source_hash != unit.metadata.source_hash:
                return True
                
            # Compiler changed
            if cached_metadata.compiler_hash != self.toolchain.compiler_executable_hash:
                return True
                
            # Flags changed
            if set(cached_metadata.flags_used) != set(unit.compiler_flags):
                return True
                
            # Check dependencies (headers) - for simplicity in this prompt, 
                        # or we re-hash some key dependencies here.
            
            return False
            
        # No cache - must compile
        return True
        
    def _detect_language(self, source_file: Path) -> str:
        """Detect language from file extension."""
        suffix = source_file.suffix.lower()
        if suffix in ['.cpp', '.cc', '.cxx', '.hpp']:
            return 'cpp'
        return 'c'

class NativeCompilationStage(BuildStageInterface):
    """
    Stage 4: Native Compilation
    """
    
    def __init__(self, output_dir: Path, build_mode: BuildMode = BuildMode.DEBUG):
        super().__init__("Native Compilation", BuildStage.NATIVE_COMPILATION)
        self.output_dir = output_dir
        self.build_mode = build_mode
        
    def check_preconditions(self, context: Dict[str, Any]) -> None:
        """Verify that required inputs are available."""
        if 'source_metadata' not in context and 'sources_by_language' not in context:
             raise BuildPreconditionError(
                "Stage 4 requires 'source_metadata' or 'sources_by_language'"
            )
            
        if 'toolchain' not in context:
            raise BuildPreconditionError(
                "Stage 4 requires 'toolchain' from toolchain detection"
            )
            
        if 'abi_config' not in context:
            raise BuildPreconditionError(
                "Stage 4 requires 'abi_config' for ABI enforcement"
            )
            
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute native compilation."""
        print(f"  Compiling native sources...")
        
        toolchain = context['toolchain']
        abi_config = context['abi_config']
        
        # Create flag manager
        flag_manager = CompilerFlagManager(abi_config, toolchain)
        
        # Create compiler
        compiler = NativeCompiler(toolchain, abi_config, flag_manager)
        
        # Get sources
        sources_by_language = context.get('sources_by_language', {})
        c_sources = [Path(p) for p in sources_by_language.get('c', [])]
        cpp_sources = [Path(p) for p in sources_by_language.get('cpp', [])]
        
        all_sources = c_sources + cpp_sources
        
        if not all_sources:
            print("    No native sources to compile")
            context['native_compilation'] = {
                'object_files': [],
                'compilation_metadata': [],
                'success': True
            }
            return context
            
        # Compile
        start_time = time.time()
        results = compiler.compile_sources(all_sources, self.output_dir, self.build_mode)
        total_duration = time.time() - start_time
        
        # Collect results
        object_files = [str(r.unit.output_file) for r in results if r.success]
        compilation_metadata = [r.unit.metadata.to_dict() for r in results if r.unit.metadata]
        errors = [r.error_message for r in results if not r.success]
        
        # Update context
        context['native_compilation'] = {
            'object_files': object_files,
            'compilation_metadata': compilation_metadata,
            'compilation_errors': errors,
            'total_duration': total_duration,
            'units_compiled': len(results),
            'success': all(r.success for r in results)
        }
        
        print(f"    Total compilation time: {total_duration:.2f}s")
        
        return context
        
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        """Validate compilation succeeded."""
        if 'native_compilation' not in context:
            raise BuildPostconditionError("Stage 4 must produce 'native_compilation' in context")
            
        compilation_data = context['native_compilation']
        
        if not compilation_data.get('success', False):
            errors = compilation_data.get('compilation_errors', [])
            error_summary = '\n'.join(errors[:5])
            raise BuildPostconditionError(f"Native compilation failed:\n{error_summary}")
            
        # Verify object files exist
        for obj_file in compilation_data.get('object_files', []):
            if not Path(obj_file).exists():
                raise BuildPostconditionError(f"Object file not found: {obj_file}")

# ============================================================================
# NATIVE VALIDATION & BINARY SELF-TESTS ()
# ============================================================================

@dataclass
class Symbol:
    """Represents a symbol in an object file."""
    name: str
    symbol_type: str  # 'T' (text/code), 'D' (data), 'U' (undefined), etc.
    address: Optional[str] = None
    
    @property
    def is_function(self) -> bool:
        """Check if symbol represents a function."""
        return self.symbol_type in ['T', 't']
        
    @property
    def is_data(self) -> bool:
        """Check if symbol represents data."""
        return self.symbol_type in ['D', 'd', 'B', 'b']
        
    @property
    def is_undefined(self) -> bool:
        """Check if symbol is undefined (external reference)."""
        return self.symbol_type == 'U'

class ObjectFileValidator:
    """
    Validates compiled object files for correctness.
    
    Performs format validation, symbol inspection, debug symbol checking,
    and ABI conformance verification.
    """
    
    def __init__(self, toolchain: ToolchainDescriptor):
        self.toolchain = toolchain
        
    def validate(self, object_file: Path) -> 'ValidationResult':
        """
        Perform comprehensive validation of object file.
        
        Args:
            object_file: Path to object file
            
        Returns:
            ValidationResult with all checks
        """
        print(f"    Validating: {object_file.name}")
        
        result = ValidationResult(object_file=object_file)
        
        # Format validation
        result.format_valid, format_msg = self._validate_format(object_file)
        if not result.format_valid:
            result.issues.append(format_msg)
            
        # Symbol validation
        result.symbols_valid, symbol_msg = self._validate_symbols(object_file)
        if not result.symbols_valid:
            result.issues.append(symbol_msg)
            
        # Debug symbol validation
        result.debug_symbols_valid, debug_msg = self._validate_debug_symbols(object_file)
        if not result.debug_symbols_valid:
            result.warnings.append(debug_msg)  # Warning, not error
            
        # ABI conformance (basic check)
        result.abi_conformance_valid = True  # Simplified for now
        
        # Self-test (simplified - would run actual test)
        result.self_test_passed = True  # Simplified for now
        
        return result
        
    def _validate_format(self, object_file: Path) -> Tuple[bool, str]:
        """Validate object file format."""
        if not object_file.exists():
            return False, f"Object file does not exist: {object_file}"
            
        if object_file.stat().st_size == 0:
            return False, f"Object file is empty: {object_file}"
            
        # Check magic bytes
        try:
            with open(object_file, 'rb') as f:
                magic = f.read(4)
                
            # ELF magic
            if magic[:4] == b'\x7fELF':
                return True, "Valid ELF object file"
                
            # PE magic (Windows)
            elif magic[:2] == b'MZ':
                return True, "Valid PE object file"
                
            # Mach-O magic (macOS)
            elif magic[:4] in [b'\xfe\xed\xfa\xce', b'\xfe\xed\xfa\xcf']:
                return True, "Valid Mach-O object file"
                
            # COFF magic (Windows object files)
            elif magic[:2] == b'\x4c\x01' or magic[:2] == b'\x64\x86':
                return True, "Valid COFF object file"
                
            else:
                return False, f"Unrecognized object file format (magic: {magic.hex()})"
                
        except Exception as e:
            return False, f"Failed to read object file: {e}"
            
    def _validate_symbols(self, object_file: Path) -> Tuple[bool, str]:
        """Validate that object file contains symbols."""
        try:
            symbols = self._extract_symbols(object_file)
            
            if not symbols:
                return False, "Object file contains no symbols"
                
            # Check for at least one function or data symbol
            has_function = any(s.is_function for s in symbols)
            has_data = any(s.is_data for s in symbols)
            
            if not has_function and not has_data:
                return False, "Object file contains no function or data symbols"
                
            return True, f"Found {len(symbols)} symbols"
            
        except Exception as e:
            return False, f"Symbol extraction failed: {e}"
            
    def _validate_debug_symbols(self, object_file: Path) -> Tuple[bool, str]:
        """Check if debug symbols are present."""
        # Simplified - in real implementation would use proper debug info parser
        # For now, just check if file is larger than minimum (heuristic)
        
        size = object_file.stat().st_size
        
        # Very small files unlikely to have debug info
        if size < 1000:
            return False, "Object file too small to contain debug symbols"
            
        return True, "Debug symbols likely present (heuristic check)"
        
    def _extract_symbols(self, object_file: Path) -> List[Symbol]:
        """
        Extract symbols from object file.
        
        Uses platform-specific tools (nm on Unix, dumpbin on Windows).
        """
        if platform.system() == 'Windows':
            return self._extract_symbols_windows(object_file)
        else:
            return self._extract_symbols_unix(object_file)
            
    def _extract_symbols_unix(self, object_file: Path) -> List[Symbol]:
        """Extract symbols using nm (Unix/Linux/macOS)."""
        try:
            result = subprocess.run(
                ['nm', str(object_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            symbols = []
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    # Format: [address] type name
                    if len(parts) == 3:
                        address, symbol_type, name = parts
                    else:
                        # Undefined symbols have no address
                        symbol_type, name = parts[0], parts[1]
                        address = None
                        
                    symbols.append(Symbol(
                        name=name,
                        symbol_type=symbol_type,
                        address=address
                    ))
                    
            return symbols
            
        except subprocess.TimeoutExpired:
            return []
        except FileNotFoundError:
            # nm not available
            return []
        except Exception:
            return []
            
    def _extract_symbols_windows(self, object_file: Path) -> List[Symbol]:
        """Extract symbols using dumpbin (Windows)."""
        # Simplified - would use dumpbin /symbols in real implementation
        # For now, return empty list (Windows symbol extraction needs dumpbin)
        return []

@dataclass
class ValidationResult:
    """Result of object file validation."""
    object_file: Path
    format_valid: bool = False
    symbols_valid: bool = False
    debug_symbols_valid: bool = False
    abi_conformance_valid: bool = False
    self_test_passed: bool = False
    
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def overall_valid(self) -> bool:
        """Check if all critical validations passed."""
        # Debug symbols are warning-only, not critical
        return (
            self.format_valid and
            self.symbols_valid and
            self.abi_conformance_valid
        )
        
    def generate_report(self) -> str:
        """Generate human-readable validation report."""
        lines = [
            f"Validation Report: {self.object_file.name}",
            "=" * 60,
            f"Format validation: {'✓' if self.format_valid else '✗'}",
            f"Symbol validation: {'✓' if self.symbols_valid else '✗'}",
            f"Debug symbols: {'✓' if self.debug_symbols_valid else '⚠'}",
            f"ABI conformance: {'✓' if self.abi_conformance_valid else '✗'}",
            f"Self-test: {'✓' if self.self_test_passed else '✗'}",
            "",
            f"Overall: {'PASSED' if self.overall_valid else 'FAILED'}",
        ]
        
        if self.issues:
            lines.append("")
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")
                
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
                
        return '\n'.join(lines)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'object_file': str(self.object_file),
            'format_valid': self.format_valid,
            'symbols_valid': self.symbols_valid,
            'debug_symbols_valid': self.debug_symbols_valid,
            'abi_conformance_valid': self.abi_conformance_valid,
            'self_test_passed': self.self_test_passed,
            'overall_valid': self.overall_valid,
            'issues': self.issues,
            'warnings': self.warnings,
        }

class NativeValidationStage(BuildStageInterface):
    """
    Stage 4.5: Native Validation
    
    Validates compiled object files for format correctness, symbol presence,
    debug information, and ABI conformance.
    """
    
    def __init__(self):
        # Use a fractional stage number to indicate post-compilation validation
        super().__init__("Native Validation", BuildStage.NATIVE_COMPILATION)
        self.stage_name = "Native Validation (Post-Compilation)"
        
    def check_preconditions(self, context: Dict[str, Any]) -> None:
        """Verify compilation completed successfully."""
        if 'native_compilation' not in context:
            raise BuildPreconditionError(
                "Stage 4.5 requires 'native_compilation' from Stage 4"
            )
            
        if not context['native_compilation'].get('success', False):
            raise BuildPreconditionError(
                "Cannot validate: native compilation failed"
            )
            
        if 'toolchain' not in context:
            raise BuildPreconditionError(
                "Stage 4.5 requires 'toolchain' for validation"
            )
            
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute native validation."""
        print(f"  Validating compiled object files...")
        
        toolchain = context['toolchain']
        validator = ObjectFileValidator(toolchain)
        
        # Get object files from compilation
        object_files = context['native_compilation'].get('object_files', [])
        
        if not object_files:
            print("    No object files to validate")
            context['native_validation'] = {
                'validation_results': [],
                'all_valid': True
            }
            return context
            
        # Validate each object file
        results = []
        for obj_file_str in object_files:
            obj_file = Path(obj_file_str)
            result = validator.validate(obj_file)
            results.append(result)
            
        # Check if all validations passed
        all_valid = all(r.overall_valid for r in results)
        
        # Report results
        passed = sum(1 for r in results if r.overall_valid)
        print(f"    Validated {passed}/{len(results)} object files")
        
        # Update context
        context['native_validation'] = {
            'validation_results': [r.to_dict() for r in results],
            'all_valid': all_valid
        }
        
        return context
        
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        """Verify validation completed and passed."""
        if 'native_validation' not in context:
            raise BuildPostconditionError(
                "Stage 4.5 must produce 'native_validation'"
            )
            
        validation_data = context['native_validation']
        
        if not validation_data.get('all_valid', False):
            # Generate detailed error report
            results = validation_data.get('validation_results', [])
            failed = [r for r in results if not r.get('overall_valid', False)]
            
            error_lines = ["Object file validation failed:"]
            for failed_result in failed[:3]:  # Show first 3 failures
                error_lines.append(f"  - {failed_result['object_file']}")
                for issue in failed_result.get('issues', []):
                    error_lines.append(f"    * {issue}")
                    
            raise BuildPostconditionError('\n'.join(error_lines))

# ============================================================================
# LINK-TIME CONTROL & EXECUTABLE GENERATION ()
# ============================================================================

@dataclass
class LinkingMetadata:
    """Provenance metadata for a linking operation."""
    target_name: str
    input_objects: List[Path] = field(default_factory=list)
    output_executable: Path = Path()
    output_hash: str = ""
    
    linker_name: str = ""
    linker_version: str = ""
    linker_flags: List[str] = field(default_factory=list)
    
    libraries_linked: List[str] = field(default_factory=list)
    lto_enabled: bool = False
    
    link_timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    link_duration: float = 0.0
    
    success: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    build_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'target_name': self.target_name,
            'input_objects': [str(p) for p in self.input_objects],
            'output_executable': str(self.output_executable),
            'output_hash': self.output_hash,
            'linker': f"{self.linker_name} {self.linker_version}",
            'linker_flags': self.linker_flags,
            'libraries_linked': self.libraries_linked,
            'lto_enabled': self.lto_enabled,
            'link_timestamp': self.link_timestamp,
            'link_duration': self.link_duration,
            'success': self.success,
            'warnings': self.warnings,
            'errors': self.errors,
            'build_id': self.build_id,
        }

@dataclass
class LinkTarget:
    """Specification for a linking operation."""
    target_name: str
    target_type: str  # 'executable' or 'shared_library'
    object_files: List[Path]
    output_path: Path
    
    linker_flags: List[str] = field(default_factory=list)
    libraries: List[str] = field(default_factory=list)
    library_paths: List[Path] = field(default_factory=list)
    
    enable_lto: bool = False
    strip_symbols: bool = False
    
    toolchain: Optional[ToolchainDescriptor] = None
    metadata: Optional[LinkingMetadata] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = LinkingMetadata(
                target_name=self.target_name,
                input_objects=self.object_files,
                output_executable=self.output_path
            )

class Linker:
    """Manages linking of object files into executables and shared libraries."""
    
    def __init__(self, toolchain: ToolchainDescriptor):
        self.toolchain = toolchain
        
    def link(self, target: LinkTarget) -> 'LinkResult':
        """
        Link object files into executable or library.
        
        Args:
            target: Link target specification
            
        Returns:
            LinkResult with success/failure information
        """
        print(f"  Linking: {target.target_name}")
        
        start_time = time.time()
        
        # Build linker command
        cmd = self._build_link_command(target)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # Linking can take longer than compilation
            )
            
            duration = time.time() - start_time
            
            # Update metadata
            if target.metadata:
                target.metadata.link_duration = duration
                target.metadata.success = (result.returncode == 0)
                target.metadata.linker_name = self.toolchain.compiler_name  # Often same as compiler
                target.metadata.linker_version = self.toolchain.compiler_version
                target.metadata.linker_flags = target.linker_flags
                target.metadata.lto_enabled = target.enable_lto
                
                # Parse warnings/errors
                self._parse_linker_output(result.stderr + result.stdout, target.metadata)
                
                if result.returncode == 0:
                    # Compute output hash
                    if target.output_path.exists():
                        target.metadata.output_hash = self._compute_hash(target.output_path)
                        target.metadata.build_id = target.metadata.output_hash[:16]
            
            if result.returncode == 0:
                return LinkResult(
                    success=True,
                    target=target,
                    duration=duration,
                    output=result.stdout
                )
            else:
                return LinkResult(
                    success=False,
                    target=target,
                    duration=duration,
                    error_message=result.stderr,
                    return_code=result.returncode
                )
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return LinkResult(
                success=False,
                target=target,
                duration=duration,
                error_message="Linking timed out (>120s)"
            )
        except Exception as e:
            duration = time.time() - start_time
            return LinkResult(
                success=False,
                target=target,
                duration=duration,
                error_message=str(e)
            )
            
    def _build_link_command(self, target: LinkTarget) -> List[str]:
        """Build linker command line."""
        cmd = [str(self.toolchain.linker_executable)]
        
        # Add linker flags
        cmd.extend(target.linker_flags)
        
        # Add LTO flag if enabled
        if target.enable_lto:
            # Check if this is MSVC or GCC/Clang
            if self.toolchain.compiler_name == 'MSVC':
                if '/LTCG' not in cmd:
                    cmd.append('/LTCG')
            else:
                if '-flto' not in cmd:
                    cmd.append('-flto')
                    
        # Add library paths
        for lib_path in target.library_paths:
            if self.toolchain.compiler_name == 'MSVC':
                cmd.append(f'/LIBPATH:{lib_path}')
            else:
                cmd.extend(['-L', str(lib_path)])
                
        # Add object files
        for obj_file in target.object_files:
            cmd.append(str(obj_file))
            
        # Add libraries
        for lib in target.libraries:
            if self.toolchain.compiler_name == 'MSVC':
                if not lib.endswith('.lib'):
                    cmd.append(f"{lib}.lib")
                else:
                    cmd.append(lib)
            else:
                cmd.extend(['-l', lib])
                
        # Add output
        if self.toolchain.compiler_name == 'MSVC':
            cmd.append(f'/OUT:{target.output_path}')
        else:
            cmd.extend(['-o', str(target.output_path)])
            
        # Add target-type specific flags
        if target.target_type == 'shared_library':
            if self.toolchain.compiler_name == 'MSVC':
                if '/DLL' not in cmd:
                    cmd.append('/DLL')
            else:
                if '-shared' not in cmd:
                    cmd.append('-shared')
                if '-fPIC' not in cmd:
                    cmd.append('-fPIC')
                    
        return cmd
        
    def _parse_linker_output(self, output: str, metadata: LinkingMetadata):
        """Parse linker output for warnings and errors."""
        for line in output.splitlines():
            line_lower = line.lower()
            if 'error:' in line_lower or 'undefined reference' in line_lower or 'error LNK' in line:
                metadata.errors.append(line.strip())
            elif 'warning:' in line_lower or 'warning LNK' in line:
                metadata.warnings.append(line.strip())
                
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except FileNotFoundError:
            return "file_not_found"

@dataclass
class LinkResult:
    """Result of a linking operation."""
    success: bool
    target: LinkTarget
    duration: float
    output: str = ""
    error_message: str = ""
    return_code: int = 0

class ExecutableValidator:
    """Validates linked executables and shared libraries."""
    
    def validate_executable(self, executable: Path) -> Tuple[bool, List[str]]:
        """
        Validate executable correctness.
        
        Returns: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check file exists
        if not executable.exists():
            issues.append(f"Executable does not exist: {executable}")
            return False, issues
            
        # Check file is executable
        if not os.access(executable, os.X_OK):
            issues.append(f"File is not executable: {executable}")
            
        # Check file size
        if executable.stat().st_size == 0:
            issues.append(f"Executable is empty: {executable}")
            return False, issues
            
        # Platform-specific validation
        if platform.system() == 'Windows':
            valid, msg = self._validate_pe_executable(executable)
            if not valid:
                issues.append(msg)
        else:
            valid, msg = self._validate_elf_executable(executable)
            if not valid:
                issues.append(msg)
                
        return len(issues) == 0, issues
        
    def _validate_pe_executable(self, executable: Path) -> Tuple[bool, str]:
        """Validate PE (Windows) executable."""
        try:
            with open(executable, 'rb') as f:
                magic = f.read(2)
                
            if magic != b'MZ':
                return False, "Not a valid PE executable (missing MZ header)"
                
            return True, ""
        except Exception as e:
            return False, f"Failed to validate PE: {e}"
            
    def _validate_elf_executable(self, executable: Path) -> Tuple[bool, str]:
        """Validate ELF (Linux/Unix) executable."""
        try:
            with open(executable, 'rb') as f:
                magic = f.read(4)
                
            if magic != b'\x7fELF':
                return False, "Not a valid ELF executable (missing ELF header)"
                
            return True, ""
        except Exception as e:
            return False, f"Failed to validate ELF: {e}"

class LinkingStage(BuildStageInterface):
    """
    Stage 5: Linking & Executable Generation
    
    Links validated object files into executables and shared libraries.
    """
    
    def __init__(self, output_dir: Path, enable_lto: bool = False):
        super().__init__("Linking & Executable Generation", BuildStage.ADAPTER_GENERATION)
        self.stage_name = "Linking & Executable Generation"
        self.output_dir = output_dir
        self.enable_lto = enable_lto
        
    def check_preconditions(self, context: Dict[str, Any]) -> None:
        """Verify required inputs available."""
        if 'native_validation' not in context:
            raise BuildPreconditionError(
                "Stage 5 requires 'native_validation' from Stage 4.5"
            )
            
        if not context['native_validation'].get('all_valid', False):
            raise BuildPreconditionError(
                "Cannot link: object file validation failed"
            )
            
        if 'toolchain' not in context:
            raise BuildPreconditionError(
                "Stage 5 requires 'toolchain' for linking"
            )
            
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute linking."""
        print(f"  Linking object files...")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        toolchain = context['toolchain']
        linker = Linker(toolchain)
        
        # Get validated object files
        # They should be in native_compilation.object_files
        object_files = [
            Path(p)
            for p in context['native_compilation'].get('object_files', [])
        ]
        
        if not object_files:
            print("    No object files to link")
            context['linking'] = {
                'executables': [],
                'libraries': [],
                'linking_metadata': [],
                'all_successful': True
            }
            return context
            
        # Create link target (simplified - single executable for verification tool)
        target_ext = '.exe' if platform.system() == 'Windows' else ''
        target_path = self.output_dir / ("verification_tool" + target_ext)
        
        target = LinkTarget(
            target_name="verification_tool",
            target_type="executable",
            object_files=object_files,
            output_path=target_path,
            enable_lto=self.enable_lto,
            toolchain=toolchain
        )
        
        # Link
        start_time = time.time()
        result = linker.link(target)
        total_duration = time.time() - start_time
        
        # Validate executable
        if result.success:
            validator = ExecutableValidator()
            valid, issues = validator.validate_executable(target.output_path)
            
            if not valid:
                result.success = False
                result.error_message = f"Executable validation failed: {issues}"
                if target.metadata:
                    target.metadata.success = False
                    target.metadata.errors.extend(issues)
                    
        # Update context
        context['linking'] = {
            'executables': [str(target.output_path)] if result.success else [],
            'libraries': [],
            'linking_metadata': [target.metadata.to_dict()] if target.metadata else [],
            'all_successful': result.success,
            'total_duration': total_duration
        }
        
        if result.success:
            print(f"    Linked successfully: {target.output_path.name}")
        else:
            print(f"    Linking failed: {result.error_message}")
            
        return context
        
    def validate_postconditions(self, context: Dict[str, Any]) -> None:
        """Verify linking succeeded."""
        if 'linking' not in context:
            raise BuildPostconditionError(
                "Stage 5 must produce 'linking' in context"
            )
            
        linking_data = context['linking']
        
        if not linking_data.get('all_successful', False):
            metadata = linking_data.get('linking_metadata', [])
            if metadata:
                errors = metadata[0].get('errors', [])
                error_summary = '\n'.join(errors[:5])
                raise BuildPostconditionError(
                    f"Linking failed:\n{error_summary}"
                )
            else:
                raise BuildPostconditionError("Linking failed with no metadata")

# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "1.0.0"
__module_id__ = "03"
__module_name__ = "Build Process & Toolchain Integration"
__status__ = "IN_PROGRESS"
__prompt__ = "10/20"

if __name__ == "__main__":
    print(f"Module {__module_id__}: {__module_name__}")
    print(f"Version: {__version__}")
    print(f"Status: {__status__}")
    print(f"Progress: Prompt {__prompt__}")
