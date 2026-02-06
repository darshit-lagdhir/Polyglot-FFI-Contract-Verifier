#!/usr/bin/env python3
"""
Module 04: Native Interface Ingestion

This module extracts ground-truth interface definitions from native code by
interrogating compiler frontends directly. It establishes the foundation for
all downstream FFI verification.

Architectural Principles:
- Compiler reality is the single source of truth
- Environment fidelity through explicit compilation contexts
- Lossless information preservation
- Zero semantic interpretation
- Deterministic and reproducible outputs

Author: PFCV Authors
Module: 04
Prompt: 1/20
Status: Foundation
"""

import json
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# VERSION AND METADATA
# ============================================================================

__version__ = "1.0.0"
__module__ = "04"
__prompt__ = "1/20"
__status__ = "foundation"

# ============================================================================
# COMPILATION CONTEXT
# ============================================================================

@dataclass
class CompilationContext:
    """
    Complete compilation environment for ingestion fidelity.
    
    Captures all parameters that influence compiler behavior and ABI decisions.
    This context must be explicit and complete for reproducible ingestion.
    """
    
    # Source inputs
    header_files: List[Path]
    
    # Include search paths (order-sensitive)
    include_paths: List[Path] = field(default_factory=list)
    
    # Preprocessor macro definitions
    macro_definitions: Dict[str, str] = field(default_factory=dict)
    
    # Target configuration (architecture-os-abi)
    target_triple: str = ""
    
    # ABI-affecting compiler flags
    abi_flags: List[str] = field(default_factory=list)
    
    # Language standard
    language_standard: str = "c11"
    
    # Compiler identification
    compiler_name: str = "clang"
    compiler_version: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context for storage and reproducibility."""
        return {
            'header_files': [str(h) for h in self.header_files],
            'include_paths': [str(p) for p in self.include_paths],
            'macro_definitions': self.macro_definitions,
            'target_triple': self.target_triple,
            'abi_flags': self.abi_flags,
            'language_standard': self.language_standard,
            'compiler': {
                'name': self.compiler_name,
                'version': self.compiler_version
            }
        }
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash of compilation context.
        
        Used for cache invalidation and reproducibility tracking.
        """
        context_json = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(context_json.encode()).hexdigest()

# ============================================================================
# EXTERNAL SYMBOL (STUB FOR PROMPT 1)
# ============================================================================

@dataclass
class ExternalSymbol:
    """
    Represents an externally visible symbol (function, variable, type).
    
    This is a minimal stub for . Full implementation in later prompts.
    """
    
    name: str
    kind: str  # 'function', 'variable', 'type'
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize symbol to dictionary."""
        return {
            'name': self.name,
            'kind': self.kind
        }

# ============================================================================
# TYPE INFO (STUB FOR PROMPT 1)
# ============================================================================

@dataclass
class TypeInfo:
    """
    Complete type information extracted from compiler.
    
    This is a minimal stub for . Full implementation in later prompts.
    """
    
    name: str
    canonical_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize type info to dictionary."""
        return {
            'name': self.name,
            'canonical_name': self.canonical_name
        }

# ============================================================================
# RAW INTERFACE ARTIFACT
# ============================================================================

@dataclass
class RawInterfaceArtifact:
    """
    Primary output of native interface ingestion.
    
    Contains the complete, compiler-faithful representation of an external
    interface including symbols, types, and dependency relationships.
    """
    
    # Artifact metadata
    artifact_version: str = "1.0"
    generation_timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    
    # Compilation context used for ingestion
    compilation_context: Optional[CompilationContext] = None
    
    # Extracted symbols
    external_symbols: List[ExternalSymbol] = field(default_factory=list)
    
    # Type definitions
    type_definitions: Dict[str, TypeInfo] = field(default_factory=dict)
    
    # Symbol dependency graph
    symbol_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    # Validation state
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    def to_json(self) -> str:
        """
        Serialize artifact to JSON.
        
        Returns:
            JSON string representation of complete artifact
        """
        data = {
            'artifact_version': self.artifact_version,
            'generation_timestamp': self.generation_timestamp,
            'compilation_context': (
                self.compilation_context.to_dict()
                if self.compilation_context
                else None
            ),
            'external_symbols': [s.to_dict() for s in self.external_symbols],
            'type_definitions': {
                k: v.to_dict() for k, v in self.type_definitions.items()
            },
            'symbol_dependencies': self.symbol_dependencies,
            'validation': {
                'passed': self.validation_passed,
                'errors': self.validation_errors
            }
        }
        return json.dumps(data, indent=2)
    
    def save(self, output_path: Path):
        """Save artifact to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def load(cls, artifact_path: Path) -> 'RawInterfaceArtifact':
        """Load artifact from file."""
        with open(artifact_path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct compilation context
        context_data = data.get('compilation_context')
        context = None
        if context_data:
            context = CompilationContext(
                header_files=[Path(h) for h in context_data['header_files']],
                include_paths=[Path(p) for p in context_data.get('include_paths', [])],
                macro_definitions=context_data.get('macro_definitions', {}),
                target_triple=context_data.get('target_triple', ''),
                abi_flags=context_data.get('abi_flags', []),
                language_standard=context_data.get('language_standard', 'c11'),
                compiler_name=context_data['compiler']['name'],
                compiler_version=context_data['compiler']['version']
            )
        
                symbols = [
            ExternalSymbol(name=s['name'], kind=s['kind'])
            for s in data.get('external_symbols', [])
        ]
        
                types = {
            k: TypeInfo(name=v['name'], canonical_name=v['canonical_name'])
            for k, v in data.get('type_definitions', {}).items()
        }
        
        return cls(
            artifact_version=data['artifact_version'],
            generation_timestamp=data['generation_timestamp'],
            compilation_context=context,
            external_symbols=symbols,
            type_definitions=types,
            symbol_dependencies=data.get('symbol_dependencies', {}),
            validation_passed=data['validation']['passed'],
            validation_errors=data['validation']['errors']
        )

# ============================================================================
# COMPILER FRONTEND ABSTRACTION
# ============================================================================

class CompilationUnit:
    """
    Opaque handle to compiler's internal representation.
    
    Different compilers (Clang, MSVC, rustc) will have different internal
    representations. This class provides a uniform interface.
    """
    
    def __init__(self, internal_repr: Any = None):
        self.internal_repr = internal_repr

class CompilerFrontend(ABC):
    """
    Abstract base class for compiler frontend integrations.
    
    Each supported compiler (Clang, MSVC, rustc) implements this interface
    to provide uniform access to compiler-internal representations.
    """
    
    @abstractmethod
    def parse_headers(
        self,
        context: CompilationContext
    ) -> CompilationUnit:
        """
        Parse headers using compiler frontend.
        
        Args:
            context: Complete compilation environment
            
        Returns:
            CompilationUnit containing compiler's internal representation
            
        Raises:
            IngestionError: If parsing fails or compiler unavailable
        """
        pass
    
    @abstractmethod
    def extract_symbols(
        self,
        unit: CompilationUnit
    ) -> List[ExternalSymbol]:
        """
        Extract externally visible symbols from compilation unit.
        
        Args:
            unit: Parsed compilation unit
            
        Returns:
            List of external symbols (functions, variables, types)
        """
        pass
    
    @abstractmethod
    def get_type_info(
        self,
        unit: CompilationUnit,
        type_name: str
    ) -> Optional[TypeInfo]:
        """
        Retrieve complete type information.
        
        Args:
            unit: Parsed compilation unit
            type_name: Name of type to retrieve
            
        Returns:
            TypeInfo if found, None otherwise
        """
        pass
    
    @property
    @abstractmethod
    def compiler_name(self) -> str:
        """Get compiler name (e.g., 'clang', 'msvc')."""
        pass
    
    @property
    @abstractmethod
    def compiler_version(self) -> str:
        """Get compiler version string."""
        pass

# ============================================================================
# INGESTION ERRORS
# ============================================================================

class IngestionError(Exception):
    """Base class for all ingestion errors."""
    pass

class ConfigError(IngestionError):
    """Error in compilation context or configuration."""
    pass

class ToolchainError(IngestionError):
    """Error invoking or interacting with compiler."""
    pass

class ExtractionError(IngestionError):
    """Error extracting information from compiler representation."""
    pass

class ValidationError(IngestionError):
    """Error validating extracted interface."""
    pass

# ============================================================================
# MODULE METADATA
# ============================================================================

def get_module_info() -> Dict[str, str]:
    """Get module metadata."""
    return {
        'module': __module__,
        'version': __version__,
        'prompt': __prompt__,
        'status': __status__,
        'name': 'Native Interface Ingestion'
    }
