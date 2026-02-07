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
Prompt: 12/20
Status: source_location_tracking
"""

import json
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# VERSION AND METADATA
# ============================================================================

__version__ = "1.0.0"
__module__ = "04"
__prompt__ = "12/20"
__status__ = "source_location_tracking"

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

    def __repr__(self) -> str:
        """String representation."""
        return f"CompilationContext(headers={len(self.header_files)})"

# ============================================================================
# SOURCE LOCATION ()
# ============================================================================

@dataclass
class SourceLocation:
    """
    Complete source location information.
    
    Captures file, line, column, and location context.
    """
    
    file_path: str
    line: int
    column: int
    
    # Location type
    is_spelling: bool = True  # True for spelling, False for expansion
    is_in_system_header: bool = False
    
    # Additional context
    offset: int = 0  # Byte offset in file
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize location."""
        data = {
            'file': self.file_path,
            'line': self.line,
            'column': self.column
        }
        
        if self.is_in_system_header:
            data['is_system_header'] = True
        
        if self.offset > 0:
            data['offset'] = self.offset
        
        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.file_path}:{self.line}:{self.column}"

# ============================================================================
# SOURCE RANGE ()
# ============================================================================

@dataclass
class SourceRange:
    """
    Source range spanning start and end locations.
    
    Represents multi-line declarations or code spans.
    """
    
    start: SourceLocation
    end: SourceLocation
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize range."""
        return {
            'start': self.start.to_dict(),
            'end': self.end.to_dict()
        }

# ============================================================================
# PROVENANCE INFO ()
# ============================================================================

@dataclass
class ProvenanceInfo:
    """
    Provenance metadata for declarations.
    
    Captures location, include chain, header classification,
    and modification tracking.
    """
    
    # Primary location
    location: SourceLocation
    extent: Optional[SourceRange] = None
    
    # Include chain (list of header files leading to this declaration)
    include_chain: List[str] = field(default_factory=list)
    include_depth: int = 0
    
    # Header classification
    is_public_header: bool = True
    is_system_header: bool = False
    
    # Expansion context (for macro-generated declarations)
    expansion_location: Optional[SourceLocation] = None
    
    # Modification tracking
    file_modification_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize provenance."""
        data = {
            'location': self.location.to_dict(),
            'include_depth': self.include_depth,
            'is_public_header': self.is_public_header
        }
        
        if self.extent:
            data['extent'] = self.extent.to_dict()
        
        if self.include_chain:
            data['include_chain'] = self.include_chain
        
        if self.expansion_location:
            data['expansion_location'] = self.expansion_location.to_dict()
        
        if self.file_modification_time:
            data['file_modification_time'] = self.file_modification_time
        
        return data

# ============================================================================
# ATTRIBUTE INFO ()
# ============================================================================

@dataclass
class AttributeInfo:
    """
    Information about a compiler attribute.
    
    Captures attribute kind, syntax, arguments, and ABI impact.
    """
    
    attribute_kind: str  # 'aligned', 'packed', 'visibility', 'deprecated', 'calling_conv', etc.
    attribute_syntax: str  # '__attribute__', '__declspec', '[[...]]', 'pragma'
    
    # Attribute arguments
    arguments: List[str] = field(default_factory=list)
    
    # Impact classification
    affects_abi: bool = False  # Changes structure layout, alignment, or calling convention
    affects_visibility: bool = False  # Changes symbol export/import
    affects_semantics: bool = False  # Changes behavior (noreturn, const, etc.)
    
    # Additional metadata
    platform_specific: bool = False  # Attribute is platform-specific
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize attribute info."""
        data = {
            'attribute_kind': self.attribute_kind,
            'attribute_syntax': self.attribute_syntax,
            'affects_abi': self.affects_abi,
            'affects_visibility': self.affects_visibility
        }
        
        if self.arguments:
            data['arguments'] = self.arguments
        
        if self.platform_specific:
            data['platform_specific'] = True
        
        return data

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
    kind: str  # 'function', 'variable', 'type', 'struct', 'union', 'enum', 'typedef', 'macro'
    
        source_location: Optional[SourceLocation] = None
    linkage: Optional[str] = None  # 'external', 'internal', 'unique_external'
    visibility: Optional[str] = None
    type_spelling: Optional[str] = None
    is_definition: bool = False
    
        function_signature: Optional['FunctionSignature'] = None
    
        global_variable_info: Optional['GlobalVariableInfo'] = None
    
        macro_info: Optional['MacroInfo'] = None
    
        attributes: List[AttributeInfo] = field(default_factory=list)
    
    # Quick access flags (derived from attributes)
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    
        provenance: Optional[ProvenanceInfo] = None
    
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
            
        if self.function_signature:
            data['function_signature'] = self.function_signature.to_dict()
            
        if self.macro_info:
            data['macro_info'] = self.macro_info.to_dict()
        
        if self.attributes:
            data['attributes'] = [attr.to_dict() for attr in self.attributes]
        
        if self.is_deprecated:
            data['is_deprecated'] = True
            if self.deprecation_message:
                data['deprecation_message'] = self.deprecation_message
        
        if self.provenance:
            data['provenance'] = self.provenance.to_dict()
        
        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"ExternalSymbol(name='{self.name}', kind='{self.kind}')"

# ============================================================================
# TYPE INFO (STUB FOR PROMPT 1)
# ============================================================================

@dataclass
class MacroInfo:
    """
    Information about a preprocessor macro.
    
    Captures macro name, value, parameters, and provenance.
    """
    
    macro_name: str
    macro_value: Optional[str] = None  # Expanded constant value
    macro_body: str = ""  # Raw token sequence
    
    # Function-like macros
    is_function_like: bool = False
    parameters: List[str] = field(default_factory=list)
    
    # Classification
    macro_type: str = "unknown"  # 'integer', 'string', 'float', 'expression', 'empty'
    
    # Provenance
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    is_predefined: bool = False
    is_builtin: bool = False
    is_platform_specific: bool = False
    
    # Conditional context
    conditional_context: List[str] = field(default_factory=list)  # Stack of active #ifdef conditions
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize macro info."""
        data = {
            'macro_name': self.macro_name,
            'macro_body': self.macro_body,
            'macro_type': self.macro_type,
            'is_function_like': self.is_function_like
        }
        
        if self.macro_value is not None:
            data['macro_value'] = self.macro_value
        
        if self.parameters:
            data['parameters'] = self.parameters
        
        if self.source_file:
            data['source_file'] = self.source_file
            data['line_number'] = self.line_number
        
        if self.is_predefined:
            data['is_predefined'] = True
        
        if self.is_platform_specific:
            data['is_platform_specific'] = True
        
        if self.conditional_context:
            data['conditional_context'] = self.conditional_context
        
        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"MacroInfo(name='{self.macro_name}', type='{self.macro_type}')"

@dataclass
class ParameterInfo:
    """
    Information about a function parameter.
    
    Captures parameter name, type, qualifiers, and type metadata.
    """
    
    name: str
    param_type: str  # Type spelling
    type_info: Optional['TypeInfo'] = None
    
    # Qualifiers
    is_const: bool = False
    is_volatile: bool = False
    is_restrict: bool = False
    
    # Metadata
    is_synthetic_name: bool = False  # Generated placeholder name
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize parameter info."""
        data = {
            'name': self.name,
            'param_type': self.param_type,
            'is_const': self.is_const,
            'is_synthetic_name': self.is_synthetic_name
        }
        
        if self.type_info:
            data['type_info'] = self.type_info.to_dict()
        
        return data

@dataclass
class FunctionSignature:
    """
    Complete function signature including parameters, return type, and calling convention.
    """
    
    return_type: str
    return_type_info: Optional['TypeInfo'] = None
    
    parameters: List[ParameterInfo] = field(default_factory=list)
    
    calling_convention: str = "cdecl"
    is_variadic: bool = False
    
    # Language and linkage
    language_linkage: str = "C"  # 'C' or 'C++'
    
    # Exception handling (C++ only)
    is_noexcept: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize function signature."""
        data = {
            'return_type': self.return_type,
            'parameters': [p.to_dict() for p in self.parameters],
            'calling_convention': self.calling_convention,
            'is_variadic': self.is_variadic,
            'language_linkage': self.language_linkage
        }
        
        if self.return_type_info:
            data['return_type_info'] = self.return_type_info.to_dict()
        
        if self.is_noexcept:
            data['is_noexcept'] = True
        
        return data

@dataclass
class GlobalVariableInfo:
    """
    Complete information about a global variable.
    
    Captures type, size, alignment, mutability, threading, and visibility.
    """
    
    variable_type: str  # Type spelling
    type_info: Optional['TypeInfo'] = None
    
    # Size and alignment
    size_bytes: int = 0
    alignment_bytes: int = 0
    
    # Mutability qualifiers
    is_const: bool = False
    is_volatile: bool = False
    is_restrict: bool = False
    
    # Thread-local storage
    is_thread_local: bool = False
    
    # Linkage and visibility
    visibility: Optional[str] = None  # 'default', 'hidden', 'protected', 'invalid'
    
    # Attributes
    section: Optional[str] = None  # Memory section name
    explicit_alignment: Optional[int] = None  # Explicit alignment attribute
    
    # Definition status
    is_definition: bool = False  # True if this is a definition, not just declaration
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize global variable info."""
        data = {
            'variable_type': self.variable_type,
            'size_bytes': self.size_bytes,
            'alignment_bytes': self.alignment_bytes,
            'is_const': self.is_const,
            'is_volatile': self.is_volatile,
            'is_thread_local': self.is_thread_local,
            'is_definition': self.is_definition
        }
        
        if self.type_info:
            data['type_info'] = self.type_info.to_dict()
        
        if self.visibility:
            data['visibility'] = self.visibility
        
        if self.section:
            data['section'] = self.section
        
        if self.explicit_alignment:
            data['explicit_alignment'] = self.explicit_alignment
        
        return data

@dataclass
class EnumeratorInfo:
    """
    Information about a single enumerator (enum constant).
    
    Captures both signed and unsigned interpretations of the value.
    """
    
    name: str
    value_signed: int  # Signed interpretation
    value_unsigned: int  # Unsigned interpretation (for large values)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize enumerator info."""
        return {
            'name': self.name,
            'value_signed': self.value_signed,
            'value_unsigned': self.value_unsigned
        }

@dataclass
class TypedefInfo:
    """
    Information about a typedef.
    
    Captures the typedef name, underlying type, canonical type,
    and complete resolution chain.
    """
    
    typedef_name: str           # The typedef identifier
    underlying_type: str        # Direct underlying type
    canonical_type: str         # Fully resolved canonical type
    typedef_chain: List[str]    # Complete chain: [name, ..., canonical]
    
    # Completeness
    is_forward_declaration: bool = False
    is_incomplete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize typedef info."""
        return {
            'typedef_name': self.typedef_name,
            'underlying_type': self.underlying_type,
            'canonical_type': self.canonical_type,
            'typedef_chain': self.typedef_chain,
            'is_forward_declaration': self.is_forward_declaration,
            'is_incomplete': self.is_incomplete
        }

@dataclass
class TypeInfo:
    """
    Complete type information extracted from compiler.
    
    Extended in  with comprehensive ABI-relevant properties.
    """
    
    # Identity
    name: str  # Declared type name
    canonical_name: str  # Canonical name after typedef resolution
    
    # Classification
    kind: str  # 'primitive', 'pointer', 'array', 'record', 'function', 'enum', 'typedef', 'unknown'
    
    # Size and alignment (-1 if incomplete)
    size_bytes: int = -1
    alignment_bytes: int = -1
    
    # Pointer types
    pointee_type: Optional[str] = None
    pointer_depth: int = 0
    
    # Array types
    element_type: Optional[str] = None
    array_size: Optional[int] = None  # None for incomplete arrays
    
    # Function types
    return_type: Optional[str] = None
    parameter_types: List[str] = field(default_factory=list)
    is_variadic: bool = False
    calling_convention: Optional[str] = None
    
    # Record types
    record_kind: Optional[str] = None  # 'struct', 'union', None
    
    # Enum types
    underlying_type: Optional[str] = None
    
    # Qualifiers
    is_const: bool = False
    is_volatile: bool = False
    is_restrict: bool = False
    
    # Completeness
    is_incomplete: bool = False
    
        record_layout: Optional['RecordLayout'] = None
    
        enum_enumerators: List['EnumeratorInfo'] = field(default_factory=list)
    enum_underlying_type: Optional[str] = None
    enum_is_signed: Optional[bool] = None
    enum_min_value: Optional[int] = None
    enum_max_value: Optional[int] = None
    enum_is_bitmask: bool = False
    enum_is_sequential: bool = False
    
        typedef_info: Optional[TypedefInfo] = None
    
    # Simplified typedef chain (for quick access)
    typedef_chain: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize type info to dictionary."""
        data = {
            'name': self.name,
            'canonical_name': self.canonical_name,
            'kind': self.kind,
            'size_bytes': self.size_bytes,
            'alignment_bytes': self.alignment_bytes,
            'is_incomplete': self.is_incomplete
        }
        
        if self.pointee_type:
            data['pointee_type'] = self.pointee_type
            data['pointer_depth'] = self.pointer_depth
        
        if self.element_type:
            data['element_type'] = self.element_type
            data['array_size'] = self.array_size
        
        if self.return_type:
            data['return_type'] = self.return_type
            data['parameter_types'] = self.parameter_types
            data['is_variadic'] = self.is_variadic
            data['calling_convention'] = self.calling_convention
        
        if self.record_kind:
            data['record_kind'] = self.record_kind
        
        if self.underlying_type:
            data['underlying_type'] = self.underlying_type
        
        if self.is_const or self.is_volatile or self.is_restrict:
            data['qualifiers'] = {
                'const': self.is_const,
                'volatile': self.is_volatile,
                'restrict': self.is_restrict
            }
        
        if self.record_layout:
            data['record_layout'] = self.record_layout.to_dict()
        
        # Enum metadata
        if self.enum_enumerators:
            data['enum'] = {
                'enumerators': [e.to_dict() for e in self.enum_enumerators],
                'underlying_type': self.enum_underlying_type,
                'is_signed': self.enum_is_signed,
                'min_value': self.enum_min_value,
                'max_value': self.enum_max_value,
                'is_bitmask': self.enum_is_bitmask,
                'is_sequential': self.enum_is_sequential
            }
            
        if self.typedef_info:
            data['typedef_info'] = self.typedef_info.to_dict()
            
        if self.typedef_chain:
            data['typedef_chain'] = self.typedef_chain
        
        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"TypeInfo(name='{self.name}', kind='{self.kind}')"

# ============================================================================
# FIELD AND RECORD LAYOUT DATA STRUCTURES ()
# ============================================================================

@dataclass
class FieldInfo:
    """
    Complete information about a structure or union field.
    
    Captures field name, type, offset, size, and alignment for ABI verification.
    """
    
    name: str
    field_type: str  # Type name (e.g., 'int', 'struct Point*')
    offset_bytes: int  # Byte offset from structure base
    offset_bits: int = 0  # Exact bit offset
    size_bytes: int = 0
    alignment_bytes: int = 0
    
        is_bitfield: bool = False
    bitfield_width: Optional[int] = None
    
    # Complete type information
    type_info: Optional['TypeInfo'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize field info."""
        data = {
            'name': self.name,
            'field_type': self.field_type,
            'offset_bytes': self.offset_bytes,
            'offset_bits': self.offset_bits,
            'size_bytes': self.size_bytes,
            'alignment_bytes': self.alignment_bytes
        }
        
        if self.is_bitfield:
            data['is_bitfield'] = True
            data['bitfield_width'] = self.bitfield_width
        
        if self.type_info:
            data['type_info'] = self.type_info.to_dict()
        
        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"FieldInfo(name='{self.name}', type='{self.field_type}')"

@dataclass
class PaddingInfo:
    """
    Represents padding bytes in a structure.
    
    Padding occurs between fields (for alignment) or at the end (for array alignment).
    """
    
    offset_bytes: int
    size_bytes: int
    reason: str  # 'inter-field', 'trailing', 'explicit'
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize padding info."""
        return {
            'offset_bytes': self.offset_bytes,
            'size_bytes': self.size_bytes,
            'reason': self.reason
        }

@dataclass
class RecordLayout:
    """
    Complete layout of a structure or union.
    
    Captures all fields, padding, size, and alignment for ABI-sensitive verification.
    """
    
    name: str
    kind: str  # 'struct', 'union'
    size_bytes: int
    alignment_bytes: int
    
    fields: List[FieldInfo] = field(default_factory=list)
    padding_regions: List[PaddingInfo] = field(default_factory=list)
    
    # Layout attributes
    is_packed: bool = False
    is_anonymous: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize record layout."""
        return {
            'name': self.name,
            'kind': self.kind,
            'size_bytes': self.size_bytes,
            'alignment_bytes': self.alignment_bytes,
            'fields': [f.to_dict() for f in self.fields],
            'padding_regions': [p.to_dict() for p in self.padding_regions],
            'is_packed': self.is_packed,
            'is_anonymous': self.is_anonymous
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"RecordLayout(name='{self.name}', kind='{self.kind}')"

# ============================================================================
# GLOBAL VARIABLE EXTRACTOR ()
# ============================================================================

class GlobalVariableExtractor:
    """
    Extracts complete global variable information from Clang AST.
    
    Handles mutability analysis, thread-local detection, visibility queries,
    and attribute extraction.
    """
    
    def __init__(self, type_extractor: 'TypeExtractor'):
        """
        Initialize global variable extractor.
        
        Args:
            type_extractor: TypeExtractor for variable type resolution
        """
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available")
        
        self.type_extractor = type_extractor
    
    def extract_global_variable(
        self,
        var_cursor: 'CXIDE'
    ) -> GlobalVariableInfo:
        """
        Extract complete global variable information.
        
        Args:
            var_cursor: Variable declaration cursor
            
        Returns:
            Complete GlobalVariableInfo
        """
        # Get variable type
        var_type = libclang.clang_getIDEType(var_cursor)
        type_spelling = self.type_extractor._get_type_spelling(var_type)
        
        # Get size and alignment
        size = libclang.clang_Type_getSizeOf(var_type)
        alignment = libclang.clang_Type_getAlignOf(var_type)
        
        # Detect mutability qualifiers
        is_const = bool(libclang.clang_isConstQualifiedType(var_type))
        is_volatile = bool(libclang.clang_isVolatileQualifiedType(var_type))
        is_restrict = bool(libclang.clang_isRestrictQualifiedType(var_type))
        
        # Detect thread-local storage
        is_thread_local = self._detect_thread_local(var_cursor)
        
        # Get visibility
        visibility = self._get_visibility(var_cursor)
        
        # Check if definition
        if hasattr(libclang, 'clang_isIDEDefinition'):
            is_definition = bool(libclang.clang_isIDEDefinition(var_cursor))
        else:
            # Fallback: check spelling equality with logical name which is weak
            # Better fallback: use clang_getIDEDefinition and compare cursors
            is_definition = False # Default
        
        # Create variable info
        var_info = GlobalVariableInfo(
            variable_type=type_spelling,
            size_bytes=max(0, size),
            alignment_bytes=max(0, alignment),
            is_const=is_const,
            is_volatile=is_volatile,
            is_restrict=is_restrict,
            is_thread_local=is_thread_local,
            visibility=visibility,
            is_definition=is_definition
        )
        
        # Extract complete type info
        try:
            var_info.type_info = self.type_extractor.extract_type(var_type)
        except Exception:
            pass
        
        return var_info
    
    def _detect_thread_local(self, cursor: 'CXIDE') -> bool:
        """
        Detect if variable is thread-local.
        
        Args:
            cursor: Variable cursor
            
        Returns:
            True if thread-local
        """
        # Check display name for thread-local keywords
        display_name_cxstr = libclang.clang_getIDEDisplayName(cursor)
        display_name = clang_string_to_python(display_name_cxstr)
        
        # Look for TLS keywords
        tls_keywords = ['__thread', 'thread_local', '_Thread_local', '__declspec(thread)']
        for keyword in tls_keywords:
            if keyword in display_name:
                return True
        
        return False
    
    def _get_visibility(self, cursor: 'CXIDE') -> str:
        """
        Get symbol visibility.
        
        Args:
            cursor: Variable cursor
            
        Returns:
            Visibility string
        """
        if not hasattr(libclang, 'clang_getIDEVisibility'):
            return 'unknown'
            
        visibility = libclang.clang_getIDEVisibility(cursor)
        
        visibility_map = {
            CXVisibilityKind.DEFAULT: 'default',
            CXVisibilityKind.HIDDEN: 'hidden',
            CXVisibilityKind.PROTECTED: 'protected',
            CXVisibilityKind.INVALID: 'invalid'
        }
        
        return visibility_map.get(visibility, 'unknown')

# ============================================================================
# FUNCTION SIGNATURE EXTRACTOR ()
# ============================================================================

class FunctionSignatureExtractor:
    """
    Extracts complete function signatures from Clang AST.
    
    Handles parameter extraction, calling convention detection,
    variadic function handling, and return type analysis.
    """
    
    def __init__(self, type_extractor: 'TypeExtractor'):
        """
        Initialize function signature extractor.
        
        Args:
            type_extractor: TypeExtractor for parameter and return types
        """
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available")
        
        self.type_extractor = type_extractor
    
    def extract_function_signature(
        self,
        function_cursor: 'CXIDE'
    ) -> FunctionSignature:
        """
        Extract complete function signature.
        
        Args:
            function_cursor: Function declaration cursor
            
        Returns:
            Complete FunctionSignature
        """
        # Get function type
        func_type = libclang.clang_getIDEType(function_cursor)
        
        # Extract return type
        return_type_cx = libclang.clang_getResultType(func_type)
        return_type_spelling = self.type_extractor._get_type_spelling(return_type_cx)
        
        # Extract parameters
        parameters = self._extract_parameters(function_cursor, func_type)
        
        # Detect calling convention
        calling_conv = self._get_calling_convention(func_type)
        
        # Detect variadic
        is_variadic = bool(libclang.clang_isFunctionTypeVariadic(func_type))
        
        # Detect language linkage
        language = self._get_language_linkage(function_cursor)
        
        # Create signature
        signature = FunctionSignature(
            return_type=return_type_spelling,
            parameters=parameters,
            calling_convention=calling_conv,
            is_variadic=is_variadic,
            language_linkage=language
        )
        
        # Extract complete return type info
        try:
            signature.return_type_info = self.type_extractor.extract_type(return_type_cx)
        except Exception:
            pass
        
        return signature
    
    def _extract_parameters(
        self,
        function_cursor: 'CXIDE',
        func_type: 'CXType'
    ) -> List[ParameterInfo]:
        """
        Extract all parameters from a function.
        
        Args:
            function_cursor: Function cursor
            func_type: Function type
            
        Returns:
            List of ParameterInfo
        """
        parameters = []
        param_index = 0
        
        # Visitor to collect parameter cursors
        def param_visitor(child_cursor, parent_cursor, client_data):
            nonlocal param_index
            
            if libclang.clang_getIDEKind(child_cursor) != CXIDEKind.PARM_DECL:
                return CXChildVisitResult.CONTINUE
            
            try:
                param = self._extract_parameter(child_cursor, param_index)
                parameters.append(param)
                param_index += 1
            except Exception:
                pass
            
            return CXChildVisitResult.CONTINUE
        
        visitor_func = CXIDEVisitor(param_visitor)
        libclang.clang_visitChildren(function_cursor, visitor_func, None)
        
        return parameters
    
    def _extract_parameter(
        self,
        param_cursor: 'CXIDE',
        index: int
    ) -> ParameterInfo:
        """
        Extract a single parameter.
        
        Args:
            param_cursor: Parameter cursor
            index: Parameter index (for synthetic names)
            
        Returns:
            ParameterInfo
        """
        # Get parameter name
        name_cxstr = libclang.clang_getIDESpelling(param_cursor)
        name = clang_string_to_python(name_cxstr)
        
        # Generate synthetic name if missing
        is_synthetic = False
        if not name:
            name = f"param{index}"
            is_synthetic = True
        
        # Get parameter type
        param_type = libclang.clang_getIDEType(param_cursor)
        type_spelling = self.type_extractor._get_type_spelling(param_type)
        
        # Detect qualifiers
        is_const = bool(libclang.clang_isConstQualifiedType(param_type))
        is_volatile = bool(libclang.clang_isVolatileQualifiedType(param_type))
        is_restrict = bool(libclang.clang_isRestrictQualifiedType(param_type))
        
        # Create parameter info
        param_info = ParameterInfo(
            name=name,
            param_type=type_spelling,
            is_const=is_const,
            is_volatile=is_volatile,
            is_restrict=is_restrict,
            is_synthetic_name=is_synthetic
        )
        
        # Extract complete type info
        try:
            param_info.type_info = self.type_extractor.extract_type(param_type)
        except Exception:
            pass
        
        return param_info
    
    def _get_calling_convention(self, func_type: 'CXType') -> str:
        """
        Determine function calling convention.
        
        Args:
            func_type: Function type
            
        Returns:
            Calling convention name
        """
        calling_conv = libclang.clang_getFunctionTypeCallingConv(func_type)
        
        # Map Clang calling convention to string
        conv_map = {
            CXCallingConv.C: 'cdecl',
            CXCallingConv.X86_STDCALL: 'stdcall',
            CXCallingConv.X86_FASTCALL: 'fastcall',
            CXCallingConv.X86_THISCALL: 'thiscall',
            CXCallingConv.X86_PASCAL: 'pascal',
            CXCallingConv.AAPCS: 'aapcs',
            CXCallingConv.AAPCS_VFP: 'aapcs_vfp',
            CXCallingConv.X86_REGCALL: 'regcall',
            CXCallingConv.WIN64: 'win64',
            CXCallingConv.DEFAULT: 'default'
        }
        
        return conv_map.get(calling_conv, 'unknown')
    
    def _get_language_linkage(self, cursor: 'CXIDE') -> str:
        """
        Determine language linkage (C vs C++).
        
        Args:
            cursor: Function cursor
            
        Returns:
            'C' or 'C++'
        """
        language = libclang.clang_getIDELanguage(cursor)
        
        if language == CXLanguageKind.C:
            return 'C'
        elif language == CXLanguageKind.C_PLUS_PLUS:
            return 'C++'
        else:
            return 'unknown'

# ============================================================================
# ENUM EXTRACTOR ()
# ============================================================================

class EnumExtractor:
    """
    Extracts complete enumeration information from Clang AST.
    
    Handles enumerator value extraction, underlying type detection,
    signedness analysis, and value range computation.
    """
    
    def __init__(self, type_extractor: 'TypeExtractor'):
        """
        Initialize enum extractor.
        
        Args:
            type_extractor: TypeExtractor for underlying type resolution
        """
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available")
        
        self.type_extractor = type_extractor
    
    def extract_enum_info(
        self,
        enum_cursor: 'CXIDE',
        enum_type: 'CXType'
    ) -> Dict[str, Any]:
        """
        Extract complete enum information.
        
        Args:
            enum_cursor: Enum declaration cursor
            enum_type: Enum type
            
        Returns:
            Dictionary with enum metadata
        """
        # Extract enumerators
        enumerators = self._extract_enumerators(enum_cursor)
        
        # Extract underlying type
        underlying_type_cx = libclang.clang_getEnumDeclIntegerType(enum_cursor)
        underlying_type_spelling = self.type_extractor._get_type_spelling(underlying_type_cx)
        
        # Determine signedness
        is_signed = self._is_signed_type(underlying_type_cx)
        
        # Compute value range
        if enumerators:
            if is_signed:
                values = [e.value_signed for e in enumerators]
            else:
                values = [e.value_unsigned for e in enumerators]
            
            min_value = min(values)
            max_value = max(values)
        else:
            min_value = None
            max_value = None
        
        # Detect bitmask pattern
        is_bitmask = self._is_bitmask_enum(enumerators, is_signed)
        
        # Detect sequential pattern
        is_sequential = self._is_sequential_enum(enumerators, is_signed)
        
        return {
            'enumerators': enumerators,
            'underlying_type': underlying_type_spelling,
            'is_signed': is_signed,
            'min_value': min_value,
            'max_value': max_value,
            'is_bitmask': is_bitmask,
            'is_sequential': is_sequential
        }
    
    def _extract_enumerators(self, enum_cursor: 'CXIDE') -> List[EnumeratorInfo]:
        """
        Extract all enumerators from an enum.
        
        Args:
            enum_cursor: Enum declaration cursor
            
        Returns:
            List of EnumeratorInfo
        """
        enumerators = []
        
        # Visitor to collect enum constants
        def enumerator_visitor(child_cursor, parent_cursor, client_data):
            if libclang.clang_getIDEKind(child_cursor) != CXIDEKind.ENUM_CONSTANT_DECL:
                return CXChildVisitResult.CONTINUE
            
            try:
                enumerator = self._extract_enumerator(child_cursor)
                enumerators.append(enumerator)
            except Exception:
                pass
            
            return CXChildVisitResult.CONTINUE
        
        visitor_func = CXIDEVisitor(enumerator_visitor)
        libclang.clang_visitChildren(enum_cursor, visitor_func, None)
        
        return enumerators
    
    def _extract_enumerator(self, constant_cursor: 'CXIDE') -> EnumeratorInfo:
        """
        Extract a single enumerator.
        
        Args:
            constant_cursor: Enum constant cursor
            
        Returns:
            EnumeratorInfo
        """
        # Get enumerator name
        name_cxstr = libclang.clang_getIDESpelling(constant_cursor)
        name = clang_string_to_python(name_cxstr)
        
        # Get signed value
        value_signed = libclang.clang_getEnumConstantDeclValue(constant_cursor)
        
        # Get unsigned value
        value_unsigned = libclang.clang_getEnumConstantDeclUnsignedValue(constant_cursor)
        
        return EnumeratorInfo(
            name=name,
            value_signed=value_signed,
            value_unsigned=value_unsigned
        )
    
    def _is_signed_type(self, cxtype: 'CXType') -> bool:
        """
        Determine if a type is signed.
        
        Args:
            cxtype: Type to check
            
        Returns:
            True if signed, False if unsigned
        """
        kind = cxtype.kind
        
        # Unsigned types
        if kind in [
            CXTypeKind.UCHAR, CXTypeKind.USHORT, CXTypeKind.UINT,
            CXTypeKind.ULONG, CXTypeKind.ULONGLONG, CXTypeKind.CHAR_U
        ]:
            return False
        
        # Signed types (default for most integer types)
        return True
    
    def _is_bitmask_enum(
        self,
        enumerators: List[EnumeratorInfo],
        is_signed: bool
    ) -> bool:
        """
        Detect if enum is a bitmask (all values are powers of 2).
        
        Args:
            enumerators: List of enumerators
            is_signed: Whether enum is signed
            
        Returns:
            True if bitmask pattern detected
        """
        if not enumerators:
            return False
        
        for enum in enumerators:
            value = enum.value_signed if is_signed else enum.value_unsigned
            
            # Skip zero (common in bitmasks)
            if value == 0:
                continue
            
            # Check if power of 2: (value & (value - 1)) == 0
            if value < 0 or (value & (value - 1)) != 0:
                return False
        
        return True
    
    def _is_sequential_enum(
        self,
        enumerators: List[EnumeratorInfo],
        is_signed: bool
    ) -> bool:
        """
        Detect if enum has sequential values (0, 1, 2, ... or similar).
        
        Args:
            enumerators: List of enumerators
            is_signed: Whether enum is signed
            
        Returns:
            True if sequential pattern detected
        """
        if len(enumerators) < 2:
            return False
        
        values = [
            (e.value_signed if is_signed else e.value_unsigned)
            for e in enumerators
        ]
        
        # Check if consecutive
        sorted_values = sorted(values)
        for i in range(len(sorted_values) - 1):
            if sorted_values[i + 1] != sorted_values[i] + 1:
                return False
        
        return True

# ============================================================================
# RECORD LAYOUT EXTRACTOR ()
# ============================================================================

class RecordLayoutExtractor:
    """
    Extracts complete structure and union layouts from Clang AST.
    
    Handles field enumeration, offset calculation, padding detection,
    and nested structure resolution.
    """
    
    def __init__(self, type_extractor: 'TypeExtractor'):
        """
        Initialize record layout extractor.
        
        Args:
            type_extractor: TypeExtractor for resolving field types
        """
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available")
        
        self.type_extractor = type_extractor
    
    def extract_record_layout(
        self,
        cursor: 'CXIDE',
        record_type: 'CXType'
    ) -> RecordLayout:
        """
        Extract complete layout of a structure or union.
        
        Args:
            cursor: Record declaration cursor
            record_type: CXType of the record
            
        Returns:
            Complete RecordLayout
        """
        # Get record name
        name_cxstr = libclang.clang_getIDESpelling(cursor)
        name = clang_string_to_python(name_cxstr)
        
        # Detect if anonymous
        is_anonymous = (not name or name.startswith('(anonymous'))
        
        # Get cursor kind to determine struct vs union
        cursor_kind = libclang.clang_getIDEKind(cursor)
        kind = 'union' if cursor_kind == CXIDEKind.UNION_DECL else 'struct'
        
        # Get size and alignment
        size = libclang.clang_Type_getSizeOf(record_type)
        alignment = libclang.clang_Type_getAlignOf(record_type)
        
        # Create layout
        layout = RecordLayout(
            name=name if name else '<anonymous>',
            kind=kind,
            size_bytes=max(0, size),
            alignment_bytes=max(0, alignment),
            is_anonymous=is_anonymous
        )
        
        # Extract fields
        self._extract_fields(cursor, record_type, layout)
        
        # Detect padding
        self._detect_padding(layout)
        
        return layout
    
    def _extract_fields(
        self,
        cursor: 'CXIDE',
        record_type: 'CXType',
        layout: RecordLayout
    ):
        """
        Extract all fields from a record.
        
        Args:
            cursor: Record cursor
            record_type: Record type
            layout: RecordLayout to populate
        """
        fields = []
        
        # Visitor to collect field cursors
        def field_visitor(child_cursor, parent_cursor, client_data):
            # Only process field declarations (CXIDE_FieldDecl = 9)
            if libclang.clang_getIDEKind(child_cursor) != 9:
                return CXChildVisitResult.CONTINUE
            
            try:
                field_info = self._extract_field(child_cursor)
                fields.append(field_info)
            except Exception:
                pass  # Skip problematic fields
            
            return CXChildVisitResult.CONTINUE
        
        visitor_func = CXIDEVisitor(field_visitor)
        libclang.clang_visitChildren(cursor, visitor_func, None)
        
        layout.fields = fields
    
    def _extract_field(self, field_cursor: 'CXIDE') -> FieldInfo:
        """
        Extract information for a single field.
        
        Args:
            field_cursor: Field declaration cursor
            
        Returns:
            FieldInfo
        """
        # Get field name
        name_cxstr = libclang.clang_getIDESpelling(field_cursor)
        name = clang_string_to_python(name_cxstr)
        
        # Get field type
        field_type = libclang.clang_getIDEType(field_cursor)
        type_spelling = self.type_extractor._get_type_spelling(field_type)
        
        # Get field offset (in bits, convert to bytes)
        offset_bits = libclang.clang_IDE_getOffsetOfField(field_cursor)
        offset_bytes = offset_bits // 8 if offset_bits >= 0 else 0
        
        # Get field size and alignment
        size = libclang.clang_Type_getSizeOf(field_type)
        alignment = libclang.clang_Type_getAlignOf(field_type)
        
                is_bitfield = bool(libclang.clang_IDE_isBitField(field_cursor))
        bit_width = None
        if is_bitfield:
            bit_width = libclang.clang_getFieldDeclBitWidth(field_cursor)
        
        # Create field info
        field_info = FieldInfo(
            name=name,
            field_type=type_spelling,
            offset_bytes=offset_bytes,
            offset_bits=max(0, offset_bits),
            size_bytes=max(0, size),
            alignment_bytes=max(0, alignment),
            is_bitfield=is_bitfield,
            bitfield_width=bit_width
        )
        
        # Extract complete type info (recursive)
        try:
            field_info.type_info = self.type_extractor.extract_type(field_type)
        except Exception:
            pass  # Type extraction may fail for complex types
        
        return field_info
    
    def _detect_padding(self, layout: RecordLayout):
        """
        Detect padding regions in a record.
        
        Args:
            layout: RecordLayout to analyze
        """
        if not layout.fields:
            return
        
        # Sort fields by offset (important for structures)
        # For unions, all fields are at offset 0, so gaps don't really mean padding in the same way
        if layout.kind == 'union':
            return
            
        sorted_fields = sorted(layout.fields, key=lambda f: f.offset_bytes)
        
        # Detect inter-field padding
        for i in range(len(sorted_fields) - 1):
            current_field = sorted_fields[i]
            next_field = sorted_fields[i + 1]
            
            current_end = current_field.offset_bytes + current_field.size_bytes
            gap = next_field.offset_bytes - current_end
            
            if gap > 0:
                padding = PaddingInfo(
                    offset_bytes=current_end,
                    size_bytes=gap,
                    reason='inter-field'
                )
                layout.padding_regions.append(padding)
        
        # Detect trailing padding
        if sorted_fields:
            last_field = sorted_fields[-1]
            last_end = last_field.offset_bytes + last_field.size_bytes
            
            if last_end < layout.size_bytes:
                padding = PaddingInfo(
                    offset_bytes=last_end,
                    size_bytes=layout.size_bytes - last_end,
                    reason='trailing'
                )
                layout.padding_regions.append(padding)

class TypedefResolver:
    """
    Resolves typedef chains and tracks typedef definitions.
    
    Handles typedef chain traversal, circular typedef detection,
    and typedef provenance tracking.
    """

    def __init__(self, type_extractor: 'TypeExtractor'):
        """
        Initialize typedef resolver.
        
        Args:
            type_extractor: TypeExtractor for type queries
        """
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available")
        
        self.type_extractor = type_extractor
        
        # Cache of resolved typedefs
        self._typedef_cache: Dict[str, TypedefInfo] = {}

    def resolve_typedef_chain(self, typedef_type: 'CXType') -> List[str]:
        """
        Resolve complete typedef chain to canonical type.
        
        Args:
            typedef_type: Typedef type to resolve
            
        Returns:
            List of type names from typedef to canonical
            
        Raises:
            CircularTypedefError: If circular typedef detected
        """
        chain = []
        visited = set()
        current_type = typedef_type
        
        # Traverse typedef chain
        max_depth = 100  # Prevent infinite loops
        depth = 0
        
        while current_type.kind == CXTypeKind.TYPEDEF and depth < max_depth:
            type_spelling = self.type_extractor._get_type_spelling(current_type)
            
            # Detect circular reference
            if type_spelling in visited:
                raise CircularTypedefError(
                    f"Circular typedef detected: {type_spelling} appears multiple times in chain"
                )
            
            visited.add(type_spelling)
            chain.append(type_spelling)
            
            # Get underlying type via declaration
            decl = libclang.clang_getTypeDeclaration(current_type)
            if decl.kind == CXIDEKind.NO_DECL_FOUND:
                break
                
            current_type = libclang.clang_getTypedefDeclUnderlyingType(decl)
            depth += 1
        
        # Add final canonical type
        canonical_type = libclang.clang_getCanonicalType(typedef_type)
        canonical_spelling = self.type_extractor._get_type_spelling(canonical_type)
        
        if not chain or chain[-1] != canonical_spelling:
            chain.append(canonical_spelling)
        
        return chain

    def extract_typedef_info(self, typedef_cursor: 'CXIDE') -> 'TypedefInfo':
        """
        Extract complete typedef information from typedef declaration.
        
        Args:
            typedef_cursor: Typedef declaration cursor
            
        Returns:
            TypedefInfo with complete chain
        """
        # Get typedef name
        name_cxstr = libclang.clang_getIDESpelling(typedef_cursor)
        typedef_name = clang_string_to_python(name_cxstr)
        
        # Check cache
        if typedef_name in self._typedef_cache:
            return self._typedef_cache[typedef_name]
        
        # Get underlying type
        underlying_type_cx = libclang.clang_getTypedefDeclUnderlyingType(typedef_cursor)
        underlying_type_spelling = self.type_extractor._get_type_spelling(underlying_type_cx)
        
        # Get canonical type
        canonical_type_cx = libclang.clang_getCanonicalType(underlying_type_cx)
        canonical_type_spelling = self.type_extractor._get_type_spelling(canonical_type_cx)
        
        # Resolve complete chain
        try:
            typedef_chain = self.resolve_typedef_chain(libclang.clang_getIDEType(typedef_cursor))
        except CircularTypedefError:
            typedef_chain = [typedef_name, "<circular>"]
        
        # Check if incomplete
        size = libclang.clang_Type_getSizeOf(underlying_type_cx)
        is_incomplete = (size < 0)
        
        # Create typedef info
        typedef_info = TypedefInfo(
            typedef_name=typedef_name,
            underlying_type=underlying_type_spelling,
            canonical_type=canonical_type_spelling,
            typedef_chain=typedef_chain,
            is_incomplete=is_incomplete
        )
        
        # Cache
        self._typedef_cache[typedef_name] = typedef_info
        
        return typedef_info

    def is_typedef_type(self, cxtype: 'CXType') -> bool:
        """
        Check if a type is a typedef.
        
        Args:
            cxtype: Type to check
            
        Returns:
            True if typedef
        """
        return cxtype.kind == CXTypeKind.TYPEDEF

# ============================================================================
# MACRO EXTRACTOR ()
# ============================================================================

class MacroExtractor:
    """
    Extracts preprocessor macro definitions from Clang AST.
    
    Handles object-like macros, function-like macros, and conditional
    compilation analysis.
    """
    
    def __init__(self):
        """Initialize macro extractor."""
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available")
        
        # Track platform-specific macro names
        self._platform_macros = {
            '_WIN32', '_WIN64', '__WIN32__', '__WINDOWS__',
            '__linux__', '__unix__', '__APPLE__', '__MACH__',
            '__x86_64__', '__amd64__', '__aarch64__', '__arm__',
            '_MSC_VER', '__GNUC__', '__clang__'
        }

    def extract_macro(self, macro_cursor: 'CXIDE') -> MacroInfo:
        """
        Extract complete macro information.
        
        Args:
            macro_cursor: Macro definition cursor
            
        Returns:
            Complete MacroInfo
        """
        # Get macro name
        name_cxstr = libclang.clang_getIDESpelling(macro_cursor)
        macro_name = clang_string_to_python(name_cxstr)
        
        # Check if function-like
        is_function_like = bool(libclang.clang_IDE_isMacroFunctionLike(macro_cursor))
        
        # Check if builtin/predefined
        is_builtin = bool(libclang.clang_IDE_isMacroBuiltin(macro_cursor))
        
        # Get source location
        location = libclang.clang_getIDELocation(macro_cursor)
        source_file = None
        line_number = None
        
        # Extract full location
        if LIBCLANG_AVAILABLE:
            cxfile = ctypes.c_void_p()
            line = ctypes.c_uint()
            column = ctypes.c_uint()
            offset = ctypes.c_uint()
            
            libclang.clang_getSpellingLocation(
                location,
                ctypes.byref(cxfile),
                ctypes.byref(line),
                ctypes.byref(column),
                ctypes.byref(offset)
            )
            
            if cxfile.value:
                file_cxstr = libclang.clang_getFileName(cxfile)
                source_file = clang_string_to_python(file_cxstr)
                line_number = int(line.value)
        
        # Detect platform-specific
        is_platform_specific = macro_name in self._platform_macros
        
        # Create macro info
        macro_info = MacroInfo(
            macro_name=macro_name,
            is_function_like=is_function_like,
            is_builtin=is_builtin,
            is_predefined=is_builtin,
            is_platform_specific=is_platform_specific,
            source_file=source_file,
            line_number=line_number
        )
        
        # Classify macro type (simplified - full implementation would parse tokens)
        macro_info.macro_type = self._classify_macro(macro_name)
        
        return macro_info

    def _classify_macro(self, macro_name: str) -> str:
        """
        Classify macro by name patterns.
        
        Args:
            macro_name: Macro name
            
        Returns:
            Macro type classification
        """
        # Simple heuristics based on naming conventions
        if macro_name.startswith('__'):
            return 'builtin'
        elif macro_name.isupper():
            return 'constant'  # Likely integer or string constant
        else:
            return 'unknown'

    def is_platform_macro(self, macro_name: str) -> bool:
        """
        Check if macro is platform-specific.
        
        Args:
            macro_name: Macro name
            
        Returns:
            True if platform-specific
        """
        return macro_name in self._platform_macros

# ============================================================================
# LOCATION EXTRACTOR ()
# ============================================================================

class LocationExtractor:
    """
    Extracts source location and provenance information from Clang AST.
    
    Handles spelling/expansion locations, ranges, include chains,
    and header classification.
    """
    
    def __init__(self):
        """Initialize location extractor."""
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available")
    
    def extract_location(
        self,
        cursor: 'CXIDE'
    ) -> SourceLocation:
        """
        Extract source location from cursor.
        
        Args:
            cursor: IDE to extract location from
            
        Returns:
            SourceLocation
        """
        # Get cursor location
        location = libclang.clang_getIDELocation(cursor)
        
        # Extract spelling location
        file_ptr = ctypes.POINTER(CXFile)()
        line = ctypes.c_uint()
        column = ctypes.c_uint()
        offset = ctypes.c_uint()
        
        libclang.clang_getSpellingLocation(
            location,
            ctypes.byref(file_ptr),
            ctypes.byref(line),
            ctypes.byref(column),
            ctypes.byref(offset)
        )
        
        # Get file name
        file_path = "<unknown>"
        if file_ptr:
            file_name_cxstr = libclang.clang_getFileName(file_ptr)
            file_path = clang_string_to_python(file_name_cxstr)
        
        # Check if in system header
        is_system = bool(libclang.clang_Location_isInSystemHeader(location))
        
        return SourceLocation(
            file_path=file_path,
            line=line.value,
            column=column.value,
            is_spelling=True,
            is_in_system_header=is_system,
            offset=offset.value
        )
    
    def extract_range(
        self,
        cursor: 'CXIDE'
    ) -> SourceRange:
        """
        Extract source range from cursor.
        
        Args:
            cursor: IDE to extract range from
            
        Returns:
            SourceRange
        """
        # Get cursor extent
        extent = libclang.clang_getIDEExtent(cursor)
        
        # Get start and end locations
        start_loc = libclang.clang_getRangeStart(extent)
        end_loc = libclang.clang_getRangeEnd(extent)
        
        # Extract start location
        start_file = ctypes.POINTER(CXFile)()
        start_line = ctypes.c_uint()
        start_col = ctypes.c_uint()
        start_offset = ctypes.c_uint()
        
        libclang.clang_getSpellingLocation(
            start_loc,
            ctypes.byref(start_file),
            ctypes.byref(start_line),
            ctypes.byref(start_col),
            ctypes.byref(start_offset)
        )
        
        start_path = "<unknown>"
        if start_file:
            start_name = libclang.clang_getFileName(start_file)
            start_path = clang_string_to_python(start_name)
        
        # Extract end location
        end_file = ctypes.POINTER(CXFile)()
        end_line = ctypes.c_uint()
        end_col = ctypes.c_uint()
        end_offset = ctypes.c_uint()
        
        libclang.clang_getSpellingLocation(
            end_loc,
            ctypes.byref(end_file),
            ctypes.byref(end_line),
            ctypes.byref(end_col),
            ctypes.byref(end_offset)
        )
        
        end_path = start_path  # Assume same file
        if end_file:
            end_name = libclang.clang_getFileName(end_file)
            end_path = clang_string_to_python(end_name)
        
        start_location = SourceLocation(
            file_path=start_path,
            line=start_line.value,
            column=start_col.value,
            offset=start_offset.value
        )
        
        end_location = SourceLocation(
            file_path=end_path,
            line=end_line.value,
            column=end_col.value,
            offset=end_offset.value
        )
        
        return SourceRange(start=start_location, end=end_location)
    
    def extract_provenance(
        self,
        cursor: 'CXIDE'
    ) -> ProvenanceInfo:
        """
        Extract complete provenance information.
        
        Args:
            cursor: IDE to extract provenance from
            
        Returns:
            ProvenanceInfo
        """
        # Extract primary location
        location = self.extract_location(cursor)
        
        # Extract extent
        extent = self.extract_range(cursor)
        
        # Determine header classification
        is_system_header = location.is_in_system_header
        is_public_header = not is_system_header  # Heuristic: non-system = public
        
        return ProvenanceInfo(
            location=location,
            extent=extent,
            is_system_header=is_system_header,
            is_public_header=is_public_header
        )

# ============================================================================
# ATTRIBUTE EXTRACTOR ()
# ============================================================================

class AttributeExtractor:
    """
    Extracts compiler attributes from Clang AST.
    
    Handles GCC/Clang __attribute__, MSVC __declspec, C++11/C23 [[...]],
    and pragma directives.
    """
    
    def __init__(self):
        """Initialize attribute extractor."""
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available")
        
        # Map attribute names to impact classification
        self._abi_affecting_attributes = {
            'aligned', 'packed', 'ms_struct', 'gcc_struct',
            'stdcall', 'cdecl', 'fastcall', 'thiscall', 'vectorcall'
        }
        
        self._visibility_affecting_attributes = {
            'visibility', 'dllexport', 'dllimport', 'hidden', 'default'
        }
    
    def extract_attributes(
        self,
        cursor: 'CXIDE'
    ) -> List[AttributeInfo]:
        """
        Extract all attributes from a cursor.
        
        Args:
            cursor: Declaration cursor
            
        Returns:
            List of AttributeInfo
        """
        attributes = []
        
        # Check if cursor has attributes
        if not libclang.clang_IDE_hasAttrs(cursor):
            return attributes
        
        # Important: Full attribute extraction requires traversing cursor children
        # and identifying attribute-specific cursor kinds. This is simplified
                
        # Detect common attributes through heuristics
        attributes.extend(self._detect_alignment_attributes(cursor))
        attributes.extend(self._detect_deprecated_attributes(cursor))
        
        return attributes
    
    def _detect_alignment_attributes(
        self,
        cursor: 'CXIDE'
    ) -> List[AttributeInfo]:
        """
        Detect alignment attributes.
        
        Args:
            cursor: IDE to analyze
            
        Returns:
            List of alignment AttributeInfo
        """
        attributes = []
        
        # Get cursor type
        cursor_type = libclang.clang_getIDEType(cursor)
        
        # Get alignment
        alignment = libclang.clang_Type_getAlignOf(cursor_type)
        
        # Check if alignment is non-standard (heuristic)
        # Full implementation would parse actual attribute syntax
        if alignment > 0:
            # Assume explicit alignment if unusually large
            if alignment >= 16:
                attr = AttributeInfo(
                    attribute_kind='aligned',
                    attribute_syntax='__attribute__',
                    arguments=[str(alignment)],
                    affects_abi=True
                )
                attributes.append(attr)
        
        return attributes
    
    def _detect_deprecated_attributes(
        self,
        cursor: 'CXIDE'
    ) -> List[AttributeInfo]:
        """
        Detect deprecated attributes.
        
        Args:
            cursor: IDE to analyze
            
        Returns:
            List of deprecated AttributeInfo
        """
        attributes = []
        
        # Important: Full implementation would parse cursor attributes
        # This is a simplified placeholder
        
        return attributes
    
    def classify_attribute(
        self,
        attribute_kind: str
    ) -> Dict[str, bool]:
        """
        Classify attribute impact.
        
        Args:
            attribute_kind: Attribute name
            
        Returns:
            Dictionary with impact flags
        """
        return {
            'affects_abi': attribute_kind in self._abi_affecting_attributes,
            'affects_visibility': attribute_kind in self._visibility_affecting_attributes,
            'affects_semantics': attribute_kind in {'noreturn', 'const', 'pure', 'nodiscard'}
        }

# ============================================================================
# TYPE EXTRACTOR ()
# ============================================================================

class TypeExtractor:
    """
    Extracts complete type information from Clang AST.
    
    Handles type classification, canonicalization, size/alignment queries,
    and recursive type decomposition.
    """
    
    def __init__(self):
        """Initialize type extractor."""
        if not LIBCLANG_AVAILABLE:
            raise ToolchainError("libclang not available for type extraction")
        
        # Cache for extracted types
        self._type_cache: Dict[str, TypeInfo] = {}
        self._record_extractor: Optional['RecordLayoutExtractor'] = None
        self._enum_extractor: Optional['EnumExtractor'] = None
        self._typedef_resolver: Optional['TypedefResolver'] = None
    
    def set_record_extractor(self, extractor: 'RecordLayoutExtractor'):
        """Set record layout extractor (avoid circular dependency)."""
        self._record_extractor = extractor
        
    def set_enum_extractor(self, extractor: 'EnumExtractor'):
        """Set enum extractor (avoid circular dependency)."""
        self._enum_extractor = extractor

    def set_typedef_resolver(self, resolver: 'TypedefResolver'):
        """Set typedef resolver (avoid circular dependency)."""
        self._typedef_resolver = resolver
    
    def extract_type(self, cxtype: 'CXType') -> TypeInfo:
        """
        Extract complete type information from CXType.
        
        Args:
            cxtype: Clang CXType
            
        Returns:
            Complete TypeInfo
        """
        # Get type spelling
        type_spelling = self._get_type_spelling(cxtype)
        
        # Check cache
        if type_spelling in self._type_cache:
            return self._type_cache[type_spelling]
        
        # Get canonical type
        canonical_type = libclang.clang_getCanonicalType(cxtype)
        canonical_spelling = self._get_type_spelling(canonical_type)
        
        # Classify type
        kind = self._classify_type(cxtype)
        
        # Extract size and alignment
        size = libclang.clang_Type_getSizeOf(cxtype)
        alignment = libclang.clang_Type_getAlignOf(cxtype)
        
        is_incomplete = (size < 0)
        
        # Create base type info
        type_info = TypeInfo(
            name=type_spelling,
            canonical_name=canonical_spelling,
            kind=kind,
            size_bytes=max(0, size),
            alignment_bytes=max(0, alignment),
            is_incomplete=is_incomplete
        )
        
        # Extract qualifiers
        type_info.is_const = bool(libclang.clang_isConstQualifiedType(cxtype))
        type_info.is_volatile = bool(libclang.clang_isVolatileQualifiedType(cxtype))
        type_info.is_restrict = bool(libclang.clang_isRestrictQualifiedType(cxtype))
        
        # Extract kind-specific properties
        if kind == 'pointer':
            self._extract_pointer_info(cxtype, type_info)
        elif kind == 'array':
            self._extract_array_info(cxtype, type_info)
        elif kind == 'function':
            self._extract_function_info(cxtype, type_info)
        elif kind == 'record':
            self._extract_record_info(cxtype, type_info)
        elif kind == 'enum':
            self._extract_enum_info(cxtype, type_info)
                if kind == 'typedef' and self._typedef_resolver:
            try:
                typedef_chain = self._typedef_resolver.resolve_typedef_chain(cxtype)
                type_info.typedef_chain = typedef_chain
                
                # If we have a cursor for this typedef, we can extract more info
                decl_cursor = libclang.clang_getTypeDeclaration(cxtype)
                if decl_cursor.kind in [CXIDEKind.TYPEDEF_DECL, CXIDEKind.TYPE_ALIAS_DECL]:
                    type_info.typedef_info = self._typedef_resolver.extract_typedef_info(decl_cursor)
            except CircularTypedefError:
                type_info.typedef_chain = [type_spelling, "<circular>"]
        
        # Cache and return
        self._type_cache[type_spelling] = type_info
        return type_info
    
    def _get_type_spelling(self, cxtype: 'CXType') -> str:
        """Get human-readable type spelling."""
        spelling_cxstr = libclang.clang_getTypeSpelling(cxtype)
        return clang_string_to_python(spelling_cxstr)
    
    def _classify_type(self, cxtype: 'CXType') -> str:
        """Classify type into ABI category."""
        kind = cxtype.kind
        
        # Primitive types
        if kind in [
            CXTypeKind.VOID, CXTypeKind.BOOL,
            CXTypeKind.CHAR_U, CXTypeKind.UCHAR, CXTypeKind.CHAR_S, CXTypeKind.SCHAR,
            CXTypeKind.USHORT, CXTypeKind.UINT, CXTypeKind.ULONG, CXTypeKind.ULONGLONG,
            CXTypeKind.SHORT, CXTypeKind.INT, CXTypeKind.LONG, CXTypeKind.LONGLONG,
            CXTypeKind.FLOAT, CXTypeKind.DOUBLE
        ]:
            return 'primitive'
        
        elif kind == CXTypeKind.POINTER:
            return 'pointer'
        
        elif kind in [CXTypeKind.CONSTANTARRAY, CXTypeKind.INCOMPLETEARRAY]:
            return 'array'
        
        elif kind == CXTypeKind.FUNCTIONPROTO:
            return 'function'
        
        elif kind == CXTypeKind.RECORD:
            return 'record'
        
        elif kind == CXTypeKind.ENUM:
            return 'enum'
        
        elif kind == CXTypeKind.TYPEDEF:
            return 'typedef'
        
        else:
            return 'unknown'
    
    def _extract_pointer_info(self, cxtype: 'CXType', type_info: TypeInfo):
        """Extract pointer type information."""
        pointee = libclang.clang_getPointeeType(cxtype)
        type_info.pointee_type = self._get_type_spelling(pointee)
        
        # Calculate pointer depth
        depth = 1
        current = pointee
        while current.kind == CXTypeKind.POINTER:
            depth += 1
            current = libclang.clang_getPointeeType(current)
        
        type_info.pointer_depth = depth
    
    def _extract_array_info(self, cxtype: 'CXType', type_info: TypeInfo):
        """Extract array type information."""
        element = libclang.clang_getArrayElementType(cxtype)
        type_info.element_type = self._get_type_spelling(element)
        
        # Get array size if constant
        if cxtype.kind == CXTypeKind.CONSTANTARRAY:
            size = libclang.clang_getArraySize(cxtype)
            type_info.array_size = size if size >= 0 else None
        else:
            type_info.array_size = None
            

    def _extract_function_info(self, cxtype: 'CXType', type_info: TypeInfo):
        """Extract function type information."""
        # Return type
        return_type = libclang.clang_getResultType(cxtype)
        type_info.return_type = self._get_type_spelling(return_type)
        
        # Parameter types
        num_params = libclang.clang_getNumArgTypes(cxtype)
        for i in range(num_params):
            param_type = libclang.clang_getArgType(cxtype, i)
            param_spelling = self._get_type_spelling(param_type)
            type_info.parameter_types.append(param_spelling)
        
        # Variadic flag
        type_info.is_variadic = bool(libclang.clang_isFunctionTypeVariadic(cxtype))
        
        # Calling convention
        calling_conv = libclang.clang_getFunctionTypeCallingConv(cxtype)
        calling_conv_map = {
            CXCallingConv.C: 'cdecl',
            CXCallingConv.X86_STDCALL: 'stdcall',
            CXCallingConv.X86_FASTCALL: 'fastcall',
            CXCallingConv.X86_THISCALL: 'thiscall',
            CXCallingConv.WIN64: 'win64',
            CXCallingConv.DEFAULT: 'default'
        }
        type_info.calling_convention = calling_conv_map.get(calling_conv, 'unknown')
    
    def _extract_record_info(self, cxtype: 'CXType', type_info: TypeInfo):
        """
        Extract record (struct/union) type information.
        
        Enhanced in  to extract complete layout.
        """
        # Detect struct vs union (requires cursor)
        type_info.record_kind = 'struct'  # Default assumption
        
        # Important: Full layout extraction requires cursor, which is not available
        # from CXType alone. Layout extraction happens when processing cursors
        # in ClangFrontend. This method sets up basic record info.
    
    def _extract_enum_info(self, cxtype: 'CXType', type_info: TypeInfo):
        """
        Extract enum type information.
        
        Enhanced in  to extract complete enum metadata.
        
        Important: Full extraction requires cursor, which is not available from
        CXType alone. Enum extraction happens when processing cursors in
        ClangFrontend. This method sets up basic enum info.
        """
        # Placeholder - full extraction in ClangFrontend with cursor access
        type_info.underlying_type = 'int'  # Default assumption

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
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
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
            k: TypeInfo(
                name=v['name'],
                canonical_name=v['canonical_name'],
                kind=v.get('kind', 'unknown'),
                size_bytes=v.get('size_bytes', -1),
                alignment_bytes=v.get('alignment_bytes', -1),
                is_incomplete=v.get('is_incomplete', False)
            )
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

class CircularTypedefError(IngestionError):
    """Error raised when circular typedef chain detected."""
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
def _load_libclang():
    """Attempt to load libclang library with fallback search paths."""
    if sys.platform == 'win32':
        names = ['libclang.dll']
    elif sys.platform == 'darwin':
        names = ['libclang.dylib']
    else:
        names = ['libclang.so', 'libclang.so.1']
    
    # Try standard loading first
    for name in names:
        try:
            return ctypes.CDLL(name)
        except OSError:
            continue
            
    # Fallback for Windows: check if libclang python package is installed
    if sys.platform == 'win32':
        try:
            import clang.native
            base_path = Path(clang.native.__file__).parent
            lib_path = base_path / 'libclang.dll'
            if lib_path.exists():
                return ctypes.CDLL(str(lib_path))
        except (ImportError, AttributeError, OSError):
            pass
            
    return None

libclang = _load_libclang()
LIBCLANG_AVAILABLE = libclang is not None

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

class CXSourceRange(ctypes.Structure):
    _fields_ = [('ptr_data', ctypes.c_void_p * 2), ('begin_int_data', ctypes.c_uint), ('end_int_data', ctypes.c_uint)]

class CXFile(ctypes.Structure):
    pass

class CXType(ctypes.Structure):
    _fields_ = [('kind', ctypes.c_int), ('data', ctypes.c_void_p * 2)]

# Enums
class CXTypeKind(IntEnum):
    INVALID = 0
    UNEXPOSED = 1
    VOID = 2
    BOOL = 3
    CHAR_U = 4
    UCHAR = 5
    CHAR_S = 6
    SCHAR = 7
    USHORT = 8
    UINT = 9
    ULONG = 10
    ULONGLONG = 11
    SHORT = 13
    INT = 17
    LONG = 18
    LONGLONG = 19
    FLOAT = 21
    DOUBLE = 22
    POINTER = 101
    CONSTANTARRAY = 112
    INCOMPLETEARRAY = 114
    FUNCTIONPROTO = 111
    RECORD = 105
    ENUM = 106
    TYPEDEF = 107

class CXCallingConv(IntEnum):
    DEFAULT = 0
    C = 1
    X86_STDCALL = 2
    X86_FASTCALL = 3
    X86_THISCALL = 4
    X86_PASCAL = 5
    AAPCS = 6
    AAPCS_VFP = 7
    X86_REGCALL = 8
    WIN64 = 9

class CXIDEKind(IntEnum):
    UNEXPOSED_DECL = 1
    STRUCT_DECL = 2
    UNION_DECL = 3
    ENUM_DECL = 5
    FUNCTION_DECL = 8
    VAR_DECL = 9
    PARM_DECL = 10
    ENUM_CONSTANT_DECL = 22
    TYPEDEF_DECL = 20
    TYPE_ALIAS_DECL = 301
    MACRO_DEFINITION = 501
    MACRO_EXPANSION = 502
    NO_DECL_FOUND = 700 

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

# Language linkage
class CXLanguageKind(IntEnum):
    INVALID = 0
    C = 1
    C_PLUS_PLUS = 2

# Function prototypes
class CXVisibilityKind(IntEnum):
    INVALID = 0
    HIDDEN = 1
    PROTECTED = 2
    DEFAULT = 3

# Function prototypes
if LIBCLANG_AVAILABLE:
    def bind(name, argtypes=None, restype=None):
        try:
            func = getattr(libclang, name)
            if argtypes is not None:
                func.argtypes = argtypes
            if restype is not None:
                func.restype = restype
            return func
        except AttributeError:
            return None

    # Index management
    bind('clang_createIndex', [ctypes.c_int, ctypes.c_int], ctypes.POINTER(CXIndex))
    bind('clang_disposeIndex', [ctypes.POINTER(CXIndex)], None)
    
    # Translation unit parsing
    bind('clang_parseTranslationUnit', [
        ctypes.POINTER(CXIndex),
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_uint
    ], ctypes.POINTER(CXTranslationUnit))
    
    bind('clang_disposeTranslationUnit', [ctypes.POINTER(CXTranslationUnit)], None)
    
    # IDE operations
    bind('clang_getTranslationUnitIDE', [ctypes.POINTER(CXTranslationUnit)], CXIDE)
    bind('clang_getIDEKind', [CXIDE], ctypes.c_int)
    bind('clang_getIDESpelling', [CXIDE], CXString)
    bind('clang_getIDELinkage', [CXIDE], ctypes.c_int)
    bind('clang_getIDELanguage', [CXIDE], ctypes.c_int)
    bind('clang_getIDEDisplayName', [CXIDE], CXString)
    bind('clang_getIDEVisibility', [CXIDE], ctypes.c_int)
    bind('clang_isIDEDefinition', [CXIDE], ctypes.c_int)
    bind('clang_IDE_hasAttrs', [CXIDE], ctypes.c_int)
    
    # String operations
    bind('clang_getCString', [CXString], ctypes.c_char_p)
    bind('clang_disposeString', [CXString], None)
    
    # Location operations
    bind('clang_getIDELocation', [CXIDE], CXSourceLocation)
    bind('clang_getSpellingLocation', [
        CXSourceLocation,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.POINTER(ctypes.c_uint)
    ], None)
    bind('clang_getFileName', [ctypes.c_void_p], CXString)
    
    # Visitor
    CXIDEVisitor = ctypes.CFUNCTYPE(
        ctypes.c_int,
        CXIDE,
        CXIDE,
        ctypes.c_void_p
    )
    
    bind('clang_visitChildren', [
        CXIDE,
        CXIDEVisitor,
        ctypes.c_void_p
    ], ctypes.c_uint)

        bind('clang_getIDEType', [CXIDE], CXType)
    bind('clang_getCanonicalType', [CXType], CXType)
    bind('clang_getTypeSpelling', [CXType], CXString)
    bind('clang_Type_getSizeOf', [CXType], ctypes.c_longlong)
    bind('clang_Type_getAlignOf', [CXType], ctypes.c_longlong)
    bind('clang_getResultType', [CXType], CXType)
    bind('clang_isFunctionTypeVariadic', [CXType], ctypes.c_uint)
    bind('clang_getFunctionTypeCallingConv', [CXType], ctypes.c_int)
    bind('clang_isConstQualifiedType', [CXType], ctypes.c_int)
    bind('clang_isVolatileQualifiedType', [CXType], ctypes.c_int)
    bind('clang_isRestrictQualifiedType', [CXType], ctypes.c_int)
    bind('clang_getPointeeType', [CXType], CXType)
    bind('clang_getArrayElementType', [CXType], CXType)
    bind('clang_getArraySize', [CXType], ctypes.c_longlong)
    bind('clang_getNumArgTypes', [CXType], ctypes.c_int)
    bind('clang_getArgType', [CXType, ctypes.c_uint], CXType)

        bind('clang_IDE_getOffsetOfField', [CXIDE], ctypes.c_longlong)
    bind('clang_Type_getNumFields', [CXType], ctypes.c_int)
    bind('clang_IDE_isBitField', [CXIDE], ctypes.c_uint)
    bind('clang_getFieldDeclBitWidth', [CXIDE], ctypes.c_int)

        bind('clang_getEnumDeclIntegerType', [CXIDE], CXType)
    bind('clang_getEnumConstantDeclValue', [CXIDE], ctypes.c_longlong)
    bind('clang_getEnumConstantDeclUnsignedValue', [CXIDE], ctypes.c_ulonglong)
    
        bind('clang_getTypeDeclaration', [CXType], CXIDE)
    bind('clang_getTypedefDeclUnderlyingType', [CXIDE], CXType)
    bind('clang_getTypedefName', [CXType], CXString)
    
        bind('clang_IDE_isMacroFunctionLike', [CXIDE], ctypes.c_int)
    bind('clang_IDE_isMacroBuiltin', [CXIDE], ctypes.c_int)

        bind('clang_getIDEExtent', [CXIDE], CXSourceRange)
    bind('clang_getFileName', [ctypes.c_void_p], CXString)
    bind('clang_getRangeStart', [CXSourceRange], CXSourceLocation)
    bind('clang_getRangeEnd', [CXSourceRange], CXSourceLocation)
    bind('clang_Location_isInSystemHeader', [CXSourceLocation], ctypes.c_int)

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
    
    Enhanced in  with complete type extraction.
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
        
                self._type_extractor = TypeExtractor()
        self._record_extractor = RecordLayoutExtractor(self._type_extractor)
        self._enum_extractor = EnumExtractor(self._type_extractor)
        self._function_extractor = FunctionSignatureExtractor(self._type_extractor)
        self._variable_extractor = GlobalVariableExtractor(self._type_extractor)
        self._typedef_resolver = TypedefResolver(self._type_extractor)
        self._macro_extractor = MacroExtractor()
        self._attribute_extractor = AttributeExtractor()
        self._location_extractor = LocationExtractor()
        
        self._type_extractor.set_record_extractor(self._record_extractor)
        self._type_extractor.set_enum_extractor(self._enum_extractor)
        self._type_extractor.set_typedef_resolver(self._typedef_resolver)
    
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
        
        # Parse with detailed preprocessing record to capture macros
        options = 0x01  # CXTranslationUnit_DetailedPreprocessingRecord
        
        translation_unit = libclang.clang_parseTranslationUnit(
            index,
            header_path.encode('utf-8'),
            c_args,
            len(args),
            None,  # unsaved_files
            0,     # num_unsaved_files
            options
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
                # Full implementation in later prompts
        return None
    
    def _process_cursor(self, cursor: CXIDE) -> Optional[ExternalSymbol]:
        """
        Process a cursor and extract symbol information if external.
        
        Enhanced in 0 to extract macros.
        """
        # Get cursor kind
        kind = libclang.clang_getIDEKind(cursor)
        
                if kind == CXIDEKind.MACRO_DEFINITION:
            try:
                macro_info = self._macro_extractor.extract_macro(cursor)
                
                # Create symbol for macro
                symbol = ExternalSymbol(
                    name=macro_info.macro_name,
                    kind='macro',
                    linkage='none',
                    macro_info=macro_info
                )
                
                if macro_info.source_file:
                    symbol.source_location = SourceLocation(
                        file_path=macro_info.source_file,
                        line=macro_info.line_number if macro_info.line_number else 0,
                        column=0
                    )
                
                return symbol
            except Exception:
                return None
                
                # Add location to symbol if available
                if macro_info.source_file:
                    symbol.source_location = SourceLocation(
                        file_path=macro_info.source_file,
                        line=macro_info.line_number or 0,
                        column=0
                    )
                
                return symbol
        
        # Get cursor name
        name_cxstr = libclang.clang_getIDESpelling(cursor)
        name = clang_string_to_python(name_cxstr)
        
        if not name:
            return None
        
        # Get cursor type
        cursor_type = libclang.clang_getIDEType(cursor)
        type_spelling_cxstr = libclang.clang_getTypeSpelling(cursor_type)
        type_spelling = clang_string_to_python(type_spelling_cxstr)
        
                provenance = None
        source_location = None
        try:
            provenance = self._location_extractor.extract_provenance(cursor)
            source_location = provenance.location
        except Exception:
            pass

        # Only process declarations
        if kind not in [
            CXIDEKind.FUNCTION_DECL,
            CXIDEKind.VAR_DECL,
            CXIDEKind.STRUCT_DECL,
            CXIDEKind.UNION_DECL,
            CXIDEKind.ENUM_DECL,
            CXIDEKind.TYPEDEF_DECL,
            CXIDEKind.TYPE_ALIAS_DECL
        ]:
            return None
        
        # Check linkage
        linkage_kind = libclang.clang_getIDELinkage(cursor)
        # Linkage can be external or none (for types/macros)
        is_external = (linkage_kind == CXLinkageKind.EXTERNAL)
        is_type_decl = kind in [
            CXIDEKind.STRUCT_DECL, 
            CXIDEKind.UNION_DECL, 
            CXIDEKind.ENUM_DECL,
            CXIDEKind.TYPEDEF_DECL,
            CXIDEKind.TYPE_ALIAS_DECL
        ]
        
        if not is_external and not is_type_decl:
            return None
        
        linkage_map = {
            CXLinkageKind.EXTERNAL: 'external',
            CXLinkageKind.INTERNAL: 'internal',
            CXLinkageKind.UNIQUE_EXTERNAL: 'unique_external',
            CXLinkageKind.NO_LINKAGE: 'none'
        }
        linkage_str = linkage_map.get(linkage_kind, 'none')
        
        # Get symbol name (already extracted)
        # name = clang_string_to_python(name_cxstr)
        
        if not name:
            return None
        
        # Map cursor kind to symbol kind
        kind_map = {
            CXIDEKind.FUNCTION_DECL: 'function',
            CXIDEKind.VAR_DECL: 'variable',
            CXIDEKind.STRUCT_DECL: 'struct',
            CXIDEKind.UNION_DECL: 'union',
            CXIDEKind.ENUM_DECL: 'enum',
            CXIDEKind.TYPEDEF_DECL: 'typedef',
            CXIDEKind.TYPE_ALIAS_DECL: 'typedef'
        }
        
        symbol_kind = kind_map.get(kind, 'unknown')
        
        # Extract type information
        # cursor_type already extracted
        # type_spelling already extracted
        
        # Create symbol
        symbol = ExternalSymbol(
            name=name,
            kind=symbol_kind,
            linkage=linkage_str,
            type_spelling=type_spelling,
            source_location=source_location,
            provenance=provenance
        )
        
                if kind in [CXIDEKind.STRUCT_DECL, CXIDEKind.UNION_DECL]:
            try:
                # Extract basic type info first
                symbol_type_info = self._type_extractor.extract_type(cursor_type)
                
                # Extract detailed layout
                layoutValue = self._record_extractor.extract_record_layout(cursor, cursor_type)
                symbol_type_info.record_layout = layoutValue
            except Exception:
                pass
        
                if kind == CXIDEKind.ENUM_DECL:
            try:
                # Extract basic type info first
                symbol_type_info = self._type_extractor.extract_type(cursor_type)
                
                # Extract detailed enum info
                enum_meta = self._enum_extractor.extract_enum_info(cursor, cursor_type)
                
                # Update TypeInfo with enum metadata
                symbol_type_info.enum_enumerators = enum_meta['enumerators']
                symbol_type_info.enum_underlying_type = enum_meta['underlying_type']
                symbol_type_info.enum_is_signed = enum_meta['is_signed']
                symbol_type_info.enum_min_value = enum_meta['min_value']
                symbol_type_info.enum_max_value = enum_meta['max_value']
                symbol_type_info.enum_is_bitmask = enum_meta['is_bitmask']
                symbol_type_info.enum_is_sequential = enum_meta['is_sequential']
            except Exception:
                pass
        
                if symbol_kind == 'function':
            try:
                signature = self._function_extractor.extract_function_signature(cursor)
                symbol.function_signature = signature
            except Exception:
                pass
                
                if symbol_kind == 'variable':
            try:
                var_info = self._variable_extractor.extract_global_variable(cursor)
                symbol.global_variable_info = var_info
            except Exception:
                pass
        
                if kind in [CXIDEKind.TYPEDEF_DECL, CXIDEKind.TYPE_ALIAS_DECL]:
            try:
                # Use resolver to get complete info
                typedef_info = self._typedef_resolver.extract_typedef_info(cursor)
                
                # Update symbol kind to 'typedef' (already handled in kind_map but being explicit)
                symbol.kind = 'typedef'
                
                # Make sure the type_info in TypeExtractor is also updated
                self._type_extractor.extract_type(cursor_type)
            except Exception:
                pass
        
                try:
            attributes = self._attribute_extractor.extract_attributes(cursor)
            if attributes:
                symbol.attributes = attributes
            
            # Check for deprecated attribute
            for attr in attributes:
                if attr.attribute_kind == 'deprecated':
                    symbol.is_deprecated = True
                    if attr.arguments:
                        symbol.deprecation_message = attr.arguments[0]
        except Exception:
            pass
            
        return symbol
