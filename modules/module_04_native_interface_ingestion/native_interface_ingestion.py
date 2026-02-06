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
__prompt__ = "2/20"
__status__ = "clang_integration"

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
# SOURCE LOCATION
# ============================================================================

@dataclass
class SourceLocation:
    """Source code location."""
    
    file_path: str
    line: int
    column: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize location."""
        return {
            'file': self.file_path,
            'line': self.line,
            'column': self.column
        }

# ============================================================================
# EXTERNAL SYMBOL (ENHANCED IN PROMPT 2)
# ============================================================================

@dataclass
class ExternalSymbol:
    """
    Externally visible symbol (function, variable, type).
    
    Extended in  with metadata from AST traversal.
    """
    
    name: str
    kind: str  # 'function', 'variable', 'type', 'struct', 'union', 'enum', 'typedef'
    
        source_location: Optional[SourceLocation] = None
    linkage: Optional[str] = None  # 'external', 'internal', 'unique_external'
    visibility: Optional[str] = None
    type_spelling: Optional[str] = None
    is_definition: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize symbol to dictionary."""
        data = {
            'name': self.name,
            'kind': self.kind,
            'is_definition': self.is_definition
        }
        
        if self.source_location:
            data['source_location'] = self.source_location.to_dict()
        
        if self.linkage:
            data['linkage'] = self.linkage
        
        if self.type_spelling:
            data['type_spelling'] = self.type_spelling
        
        return data

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

# ============================================================================
# CLANG FRONTEND INTEGRATION ()
# ============================================================================

import sys
import ctypes
from enum import IntEnum

# ============================================================================
# LIBCLANG BINDINGS (MINIMAL SUBSET)
# ============================================================================

# Attempt to load libclang
try:
    if sys.platform == 'win32':
        libclang = ctypes.CDLL('libclang.dll')
    elif sys.platform == 'darwin':
        libclang = ctypes.CDLL('libclang.dylib')
    else:
        libclang = ctypes.CDLL('libclang.so')
    LIBCLANG_AVAILABLE = True
except OSError:
    LIBCLANG_AVAILABLE = False
    libclang = None

# Opaque types
class CXIndex(ctypes.Structure):
    pass

class CXTranslationUnit(ctypes.Structure):
    pass

class CXIDE(ctypes.Structure):
    _fields_ = [
        ('kind', ctypes.c_int),
        ('xdata', ctypes.c_int),
        ('data', ctypes.c_void_p * 3)
    ]

class CXString(ctypes.Structure):
    _fields_ = [('data', ctypes.c_void_p), ('private_flags', ctypes.c_uint)]

class CXSourceLocation(ctypes.Structure):
    _fields_ = [('ptr_data', ctypes.c_void_p * 2), ('int_data', ctypes.c_uint)]

# Enums
class CXIDEKind(IntEnum):
    UNEXPOSED_DECL = 1
    STRUCT_DECL = 2
    UNION_DECL = 3
    ENUM_DECL = 5
    FUNCTION_DECL = 8
    VAR_DECL = 9
    TYPEDEF_DECL = 20

class CXLinkageKind(IntEnum):
    INVALID = 0
    NO_LINKAGE = 1
    INTERNAL = 2
    UNIQUE_EXTERNAL = 3
    EXTERNAL = 4

class CXChildVisitResult(IntEnum):
    BREAK = 0
    CONTINUE = 1
    RECURSE = 2

# Function prototypes
if LIBCLANG_AVAILABLE:
    # Index management
    libclang.clang_createIndex.argtypes = [ctypes.c_int, ctypes.c_int]
    libclang.clang_createIndex.restype = ctypes.POINTER(CXIndex)
    
    libclang.clang_disposeIndex.argtypes = [ctypes.POINTER(CXIndex)]
    libclang.clang_disposeIndex.restype = None
    
    # Translation unit parsing
    libclang.clang_parseTranslationUnit.argtypes = [
        ctypes.POINTER(CXIndex),
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_uint
    ]
    libclang.clang_parseTranslationUnit.restype = ctypes.POINTER(CXTranslationUnit)
    
    libclang.clang_disposeTranslationUnit.argtypes = [ctypes.POINTER(CXTranslationUnit)]
    libclang.clang_disposeTranslationUnit.restype = None
    
    # IDE operations
    libclang.clang_getTranslationUnitIDE.argtypes = [ctypes.POINTER(CXTranslationUnit)]
    libclang.clang_getTranslationUnitIDE.restype = CXIDE
    
    libclang.clang_getIDEKind.argtypes = [CXIDE]
    libclang.clang_getIDEKind.restype = ctypes.c_int
    
    libclang.clang_getIDESpelling.argtypes = [CXIDE]
    libclang.clang_getIDESpelling.restype = CXString
    
    libclang.clang_getIDELinkage.argtypes = [CXIDE]
    libclang.clang_getIDELinkage.restype = ctypes.c_int
    
    # String operations
    libclang.clang_getCString.argtypes = [CXString]
    libclang.clang_getCString.restype = ctypes.c_char_p
    
    libclang.clang_disposeString.argtypes = [CXString]
    libclang.clang_disposeString.restype = None
    
    # Visitor
    CXIDEVisitor = ctypes.CFUNCTYPE(
        ctypes.c_int,
        CXIDE,
        CXIDE,
        ctypes.c_void_p
    )
    
    libclang.clang_visitChildren.argtypes = [
        CXIDE,
        CXIDEVisitor,
        ctypes.c_void_p
    ]
    libclang.clang_visitChildren.restype = ctypes.c_uint

# Helper functions
def clang_string_to_python(cxstring: CXString) -> str:
    """Convert CXString to Python string and dispose."""
    if not LIBCLANG_AVAILABLE:
        return ""
    
    c_str = libclang.clang_getCString(cxstring)
    py_str = c_str.decode('utf-8') if c_str else ""
    libclang.clang_disposeString(cxstring)
    return py_str

# ============================================================================
# CLANG COMPILATION UNIT
# ============================================================================

class ClangCompilationUnit(CompilationUnit):
    """Clang-specific compilation unit wrapping CXTranslationUnit."""
    
    def __init__(
        self,
        index: ctypes.POINTER(CXIndex),
        translation_unit: ctypes.POINTER(CXTranslationUnit)
    ):
        super().__init__(internal_repr=translation_unit)
        self.index = index
        self.translation_unit = translation_unit
    
    def dispose(self):
        """Release Clang resources."""
        if LIBCLANG_AVAILABLE and self.translation_unit:
            libclang.clang_disposeTranslationUnit(self.translation_unit)
            self.translation_unit = None
        
        if LIBCLANG_AVAILABLE and self.index:
            libclang.clang_disposeIndex(self.index)
            self.index = None

# ============================================================================
# CLANG FRONTEND
# ============================================================================

class ClangFrontend(CompilerFrontend):
    """
    Clang compiler frontend integration via libclang.
    
    Provides access to Clang's preprocessor, parser, and AST for extracting
    native interface information with compiler-grade fidelity.
    """
    
    def __init__(self):
        """Initialize Clang frontend."""
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError(
                "libclang not available. Install LLVM/Clang and ensure "
                "libclang library is in system path."
            )
        
        self._compiler_name = "clang"
        self._compiler_version = "unknown"  # TODO: Query via clang_getClangVersion
    
    @property
    def compiler_name(self) -> str:
        """Get compiler name."""
        return self._compiler_name
    
    @property
    def compiler_version(self) -> str:
        """Get compiler version."""
        return self._compiler_version
    
    def parse_headers(
        self,
        context: CompilationContext
    ) -> CompilationUnit:
        """
        Parse headers using Clang frontend.
        
        Args:
            context: Complete compilation environment
            
        Returns:
            ClangCompilationUnit with parsed AST
            
        Raises:
            ConfigError: Invalid compilation context
            ToolchainError: Clang invocation failed
        """
        if not context.header_files:
            raise ConfigError("No header files specified in compilation context")
        
        # Create index
        index = libclang.clang_createIndex(0, 1)  # excludePCH=0, displayDiagnostics=1
        if not index:
            raise ToolchainError("Failed to create Clang index")
        
        # Build command-line arguments
        args = self._build_clang_args(context)
        
        # Convert to C argument array
        c_args = (ctypes.c_char_p * len(args))()
        for i, arg in enumerate(args):
            c_args[i] = arg.encode('utf-8')
        
        # Parse first header file
        # TODO: Support multiple headers via virtual header
        header_path = str(context.header_files[0])
        
        translation_unit = libclang.clang_parseTranslationUnit(
            index,
            header_path.encode('utf-8'),
            c_args,
            len(args),
            None,  # unsaved_files
            0,     # num_unsaved_files
            0      # options (use defaults)
        )
        
        if not translation_unit:
            libclang.clang_disposeIndex(index)
            raise ToolchainError(f"Failed to parse header: {header_path}")
        
        return ClangCompilationUnit(index, translation_unit)
    
    def _build_clang_args(self, context: CompilationContext) -> List[str]:
        """
        Build Clang command-line arguments from compilation context.
        
        Args:
            context: Compilation context
            
        Returns:
            List of command-line arguments
        """
        args = []
        
        # Include paths
        for include_path in context.include_paths:
            args.append(f'-I{include_path}')
        
        # Macro definitions
        for name, value in context.macro_definitions.items():
            if value:
                args.append(f'-D{name}={value}')
            else:
                args.append(f'-D{name}')
        
        # Target triple
        if context.target_triple:
            args.append('-target')
            args.append(context.target_triple)
        
        # Language standard
        if context.language_standard:
            args.append(f'-std={context.language_standard}')
        
        # ABI flags
        args.extend(context.abi_flags)
        
        return args
    
    def extract_symbols(
        self,
        unit: CompilationUnit
    ) -> List[ExternalSymbol]:
        """
        Extract externally visible symbols from compilation unit.
        
        Args:
            unit: Parsed compilation unit (must be ClangCompilationUnit)
            
        Returns:
            List of external symbols
            
        Raises:
            ExtractionError: Symbol extraction failed
        """
        if not isinstance(unit, ClangCompilationUnit):
            raise ExtractionError("Expected ClangCompilationUnit")
        
        symbols = []
        
        # Get root cursor
        cursor = libclang.clang_getTranslationUnitIDE(unit.translation_unit)
        
        # Visitor callback
        def visitor(child_cursor, parent_cursor, client_data):
            try:
                symbol = self._process_cursor(child_cursor)
                if symbol:
                    symbols.append(symbol)
            except Exception:
                # Log but continue traversal
                pass
            
            return CXChildVisitResult.RECURSE
        
        # Create CFUNCTYPE callback
        visitor_func = CXIDEVisitor(visitor)
        
        # Traverse AST
        libclang.clang_visitChildren(cursor, visitor_func, None)
        
        return symbols
    
    def _process_cursor(self, cursor: CXIDE) -> Optional[ExternalSymbol]:
        """
        Process a cursor and extract symbol information if external.
        
        Args:
            cursor: Clang cursor
            
        Returns:
            ExternalSymbol if cursor represents external symbol, None otherwise
        """
        # Get cursor kind
        kind = libclang.clang_getIDEKind(cursor)
        
        # Only process declarations
        if kind not in [
            CXIDEKind.FUNCTION_DECL,
            CXIDEKind.VAR_DECL,
            CXIDEKind.STRUCT_DECL,
            CXIDEKind.UNION_DECL,
            CXIDEKind.ENUM_DECL,
            CXIDEKind.TYPEDEF_DECL
        ]:
            return None
        
        # Check linkage
        linkage = libclang.clang_getIDELinkage(cursor)
        if linkage != CXLinkageKind.EXTERNAL:
            return None
        
        # Get symbol name
        name_cxstr = libclang.clang_getIDESpelling(cursor)
        name = clang_string_to_python(name_cxstr)
        
        if not name:
            return None
        
        # Map cursor kind to symbol kind
        kind_map = {
            CXIDEKind.FUNCTION_DECL: 'function',
            CXIDEKind.VAR_DECL: 'variable',
            CXIDEKind.STRUCT_DECL: 'struct',
            CXIDEKind.UNION_DECL: 'union',
            CXIDEKind.ENUM_DECL: 'enum',
            CXIDEKind.TYPEDEF_DECL: 'typedef'
        }
        
        symbol_kind = kind_map.get(kind, 'unknown')
        
        # Create symbol
        symbol = ExternalSymbol(
            name=name,
            kind=symbol_kind,
            linkage='external'
        )
        
        return symbol
    
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
                return None
