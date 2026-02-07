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
__prompt__ = "6/20"
__status__ = "enum_extraction"

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
        
        return data

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
    size_bytes: int
    alignment_bytes: int
    
    # Bitfield properties (basic detection, full handling in later prompts)
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
            'size_bytes': self.size_bytes,
            'alignment_bytes': self.alignment_bytes
        }
        
        if self.is_bitfield:
            data['is_bitfield'] = True
            data['bitfield_width'] = self.bitfield_width
        
        if self.type_info:
            data['type_info'] = self.type_info.to_dict()
        
        return data

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
        
        # Detect bitfield (offset not byte-aligned or negative size)
        is_bitfield = (offset_bits % 8 != 0) or (size < 0)
        
        # Create field info
        field_info = FieldInfo(
            name=name,
            field_type=type_spelling,
            offset_bytes=offset_bytes,
            size_bytes=max(0, size),
            alignment_bytes=max(0, alignment),
            is_bitfield=is_bitfield
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
    
    def set_record_extractor(self, extractor: 'RecordLayoutExtractor'):
        """Set record layout extractor (avoid circular dependency)."""
        self._record_extractor = extractor
        
    def set_enum_extractor(self, extractor: 'EnumExtractor'):
        """Set enum extractor (avoid circular dependency)."""
        self._enum_extractor = extractor
    
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
    ENUM_CONSTANT_DECL = 22
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

        libclang.clang_getIDEType.argtypes = [CXIDE]
    libclang.clang_getIDEType.restype = CXType
    
    libclang.clang_getCanonicalType.argtypes = [CXType]
    libclang.clang_getCanonicalType.restype = CXType
    
    libclang.clang_getTypeSpelling.argtypes = [CXType]
    libclang.clang_getTypeSpelling.restype = CXString
    
    libclang.clang_Type_getSizeOf.argtypes = [CXType]
    libclang.clang_Type_getSizeOf.restype = ctypes.c_longlong
    
    libclang.clang_Type_getAlignOf.argtypes = [CXType]
    libclang.clang_Type_getAlignOf.restype = ctypes.c_longlong
    
    libclang.clang_getPointeeType.argtypes = [CXType]
    libclang.clang_getPointeeType.restype = CXType
    
    libclang.clang_getArrayElementType.argtypes = [CXType]
    libclang.clang_getArrayElementType.restype = CXType
    
    libclang.clang_getArraySize.argtypes = [CXType]
    libclang.clang_getArraySize.restype = ctypes.c_longlong
    
    libclang.clang_getResultType.argtypes = [CXType]
    libclang.clang_getResultType.restype = CXType
    
    libclang.clang_getNumArgTypes.argtypes = [CXType]
    libclang.clang_getNumArgTypes.restype = ctypes.c_int
    
    libclang.clang_getArgType.argtypes = [CXType, ctypes.c_uint]
    libclang.clang_getArgType.restype = CXType
    
    libclang.clang_isFunctionTypeVariadic.argtypes = [CXType]
    libclang.clang_isFunctionTypeVariadic.restype = ctypes.c_int
    
    libclang.clang_getFunctionTypeCallingConv.argtypes = [CXType]
    libclang.clang_getFunctionTypeCallingConv.restype = ctypes.c_int
    
    libclang.clang_isConstQualifiedType.argtypes = [CXType]
    libclang.clang_isConstQualifiedType.restype = ctypes.c_int
    
    libclang.clang_isVolatileQualifiedType.argtypes = [CXType]
    libclang.clang_isVolatileQualifiedType.restype = ctypes.c_int
    
    libclang.clang_isRestrictQualifiedType.argtypes = [CXType]
    libclang.clang_isRestrictQualifiedType.restype = ctypes.c_int

        libclang.clang_IDE_getOffsetOfField.argtypes = [CXIDE]
    libclang.clang_IDE_getOffsetOfField.restype = ctypes.c_longlong
    
        libclang.clang_Type_getNumFields.argtypes = [CXType]
    libclang.clang_Type_getNumFields.restype = ctypes.c_int

        libclang.clang_getEnumDeclIntegerType.argtypes = [CXIDE]
    libclang.clang_getEnumDeclIntegerType.restype = CXType
    
    libclang.clang_getEnumConstantDeclValue.argtypes = [CXIDE]
    libclang.clang_getEnumConstantDeclValue.restype = ctypes.c_longlong
    
    libclang.clang_getEnumConstantDeclUnsignedValue.argtypes = [CXIDE]
    libclang.clang_getEnumConstantDeclUnsignedValue.restype = ctypes.c_ulonglong

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
        
        self._type_extractor.set_record_extractor(self._record_extractor)
        self._type_extractor.set_enum_extractor(self._enum_extractor)
    
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
        
        Enhanced in  to extract type information.
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
        
        # Extract type information
        cursor_type = libclang.clang_getIDEType(cursor)
        type_spelling = self._type_extractor._get_type_spelling(cursor_type)
        
        # Create symbol
        symbol = ExternalSymbol(
            name=name,
            kind=symbol_kind,
            linkage='external',
            type_spelling=type_spelling
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
        
        return symbol
