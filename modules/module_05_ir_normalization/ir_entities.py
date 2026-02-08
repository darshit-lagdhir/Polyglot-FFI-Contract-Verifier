"""
Module 05: Intermediate Representation (IR) Normalization
: Foundational IR Entity Model and Graph Architecture

This module implements the core entity model for the IR, providing the foundational
data structures that represent native interfaces in a normalized, canonical form.
"""

from dataclasses import dataclass, field, InitVar
from typing import List, Dict, Optional, Set, Any
from enum import Enum
import hashlib

# ============================================================================
# ENUMERATIONS FOR IR ENTITY CLASSIFICATION
# ============================================================================

class EntityKind(Enum):
    """Classification of IR entities."""
    INTERFACE_UNIT = "interface_unit"
    FUNCTION_SYMBOL = "function_symbol"
    VARIABLE_SYMBOL = "variable_symbol"
    TYPE_SYMBOL = "type_symbol"
    SCALAR_TYPE = "scalar_type"
    POINTER_TYPE = "pointer_type"
    ARRAY_TYPE = "array_type"
    STRUCTURE_TYPE = "structure_type"
    UNION_TYPE = "union_type"
    ENUM_TYPE = "enum_type"
    FUNCTION_POINTER_TYPE = "function_pointer_type"
    FIELD = "field"
    PADDING = "padding"
    PARAMETER = "parameter"
    RETURN = "return"
    ATTRIBUTE = "attribute"
    METADATA = "metadata"

class ScalarKind(Enum):
    """Classification of scalar types."""
    SIGNED_INTEGER = "signed_integer"
    UNSIGNED_INTEGER = "unsigned_integer"
    FLOATING_POINT = "floating_point"
    BOOLEAN = "boolean"
    CHARACTER = "character"
    VOID = "void"

class CallingConvention(Enum):
    """Calling conventions for functions."""
    CDECL = "cdecl"
    STDCALL = "stdcall"
    FASTCALL = "fastcall"
    THISCALL = "thiscall"
    VECTORCALL = "vectorcall"
    WIN64 = "win64"
    SYSV_AMD64 = "sysv_amd64"
    AAPCS = "aapcs"
    AAPCS_VFP = "aapcs_vfp"

class ReturnMechanism(Enum):
    """How return values are passed."""
    DIRECT = "direct"  # Returned in registers
    HIDDEN_POINTER = "hidden_pointer"  # Via implicit first parameter
    AGGREGATE = "aggregate"  # Platform-specific aggregate rules
    SPLIT = "split"  # Split across multiple registers

class Endianness(Enum):
    """Byte ordering."""
    LITTLE = "little"
    BIG = "big"

# ============================================================================
# BASE IR ENTITY
# ============================================================================

@dataclass(kw_only=True)
class IREntity:
    """
    Base class for all IR entities.
    
    Every entity has:
    - Unique identifier (stable across versions)
    - Entity kind classification
    - Optional metadata
    """
    
    entity_id: str
    kind: EntityKind
    metadata: Optional['MetadataEntity'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary."""
        return {
            'entity_id': self.entity_id,
            'kind': self.kind.value,
            'metadata': self.metadata.to_dict() if self.metadata else None
        }
    
    @staticmethod
    def generate_id(kind: EntityKind, *components: str) -> str:
        """
        Generate stable entity ID from structural components.
        
        IDs are deterministic and based on entity structure, not memory
        addresses or traversal order.
        """
        content = f"{kind.value}::" + "::".join(str(c) for c in components)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

# ============================================================================
# METADATA ENTITY
# ============================================================================

@dataclass(kw_only=True)
class MetadataEntity(IREntity):
    """
    Provenance and traceability information.
    
    Attached to IR entities to provide source location, origin, and context.
    """
    
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    header_origin: Optional[str] = None
    ingestion_timestamp: Optional[str] = None
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False, default=EntityKind.METADATA)
    
    def __post_init__(self):
        self.kind = EntityKind.METADATA
        self.entity_id = self.generate_id(
            EntityKind.METADATA,
            self.source_file or "unknown",
            str(self.line_number or 0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata."""
        data = super().to_dict()
        data.update({
            'source_file': self.source_file,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'header_origin': self.header_origin
        })
        return data

# ============================================================================
# ============================================================================

@dataclass(kw_only=True)
class InterfaceUnit(IREntity):
    """
    Root container for all IR entities.
    
    Represents a complete native interface surface observed under a specific
    compilation context. All entities are interpreted relative to this context.
    """
    
    # Platform context
    target_architecture: str  # e.g., "x86_64", "aarch64"
    operating_system: str  # e.g., "linux", "windows", "macos"
    pointer_width: int  # 32 or 64
    endianness: Endianness
    abi_mode: str  # e.g., "sysv", "win64", "aapcs"
    
    # Compiler context
    compiler_family: str  # e.g., "gcc", "clang", "msvc"
    compiler_version: str
    compilation_flags: List[str] = field(default_factory=list)
    
    # IR metadata
    ir_schema_version: str = "1.0.0"
    normalization_version: str = "1.0.0"
    creation_timestamp: Optional[str] = None
    
    # Contained entities
    symbols: List['SymbolEntity'] = field(default_factory=list)
    types: List['TypeEntity'] = field(default_factory=list)
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False, default=EntityKind.INTERFACE_UNIT)
    
    def __post_init__(self):
        self.kind = EntityKind.INTERFACE_UNIT
        self.entity_id = self.generate_id(
            EntityKind.INTERFACE_UNIT,
            self.target_architecture,
            self.operating_system,
            str(self.pointer_width),
            self.abi_mode
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize interface unit."""
        data = super().to_dict()
        data.update({
            'target_architecture': self.target_architecture,
            'operating_system': self.operating_system,
            'pointer_width': self.pointer_width,
            'endianness': self.endianness.value,
            'abi_mode': self.abi_mode,
            'compiler_family': self.compiler_family,
            'compiler_version': self.compiler_version,
            'compilation_flags': self.compilation_flags,
            'ir_schema_version': self.ir_schema_version,
            'normalization_version': self.normalization_version,
            'symbols': [s.to_dict() for s in self.symbols],
            'types': [t.to_dict() for t in self.types]
        })
        return data

# ============================================================================
# SYMBOL ENTITIES
# ============================================================================

@dataclass(kw_only=True)
class SymbolEntity(IREntity):
    """
    Base class for externally visible symbols.
    
    Represents linkage points that may be referenced across language boundaries.
    """
    
    linkage_name: str  # Mangled name in binary
    source_name: Optional[str] = None  # Human-readable name
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False)
    
    def __post_init__(self):
        # Subclasses must set self.kind before calling super().__post_init__()
        # or we calculate ID using whatever self.kind currently is.
        self.entity_id = self.generate_id(self.kind, self.linkage_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize symbol."""
        data = super().to_dict()
        data.update({
            'linkage_name': self.linkage_name,
            'source_name': self.source_name
        })
        return data

@dataclass(kw_only=True)
class FunctionSymbol(SymbolEntity):
    """
    Callable function symbol.
    
    Represents a function that may be called across FFI boundaries.
    """
    
    calling_convention: CallingConvention
    return_entity: Optional['ReturnEntity'] = None
    parameters: List['ParameterEntity'] = field(default_factory=list)
    is_variadic: bool = False
    attributes: List['AttributeEntity'] = field(default_factory=list)
    
    # Overrides
    kind: EntityKind = field(init=False, default=EntityKind.FUNCTION_SYMBOL)
    
    def __post_init__(self):
        self.kind = EntityKind.FUNCTION_SYMBOL
        super().__post_init__()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize function symbol."""
        data = super().to_dict()
        data.update({
            'calling_convention': self.calling_convention.value,
            'return_entity': self.return_entity.to_dict() if self.return_entity else None,
            'parameters': [p.to_dict() for p in self.parameters],
            'is_variadic': self.is_variadic,
            'attributes': [a.to_dict() for a in self.attributes]
        })
        return data

@dataclass(kw_only=True)
class VariableSymbol(SymbolEntity):
    """
    Global variable symbol.
    
    Represents a global variable accessible across FFI boundaries.
    """
    
    type_reference: str
    is_const: bool = False
    visibility: str = "extern"  # extern, static, internal
    attributes: List['AttributeEntity'] = field(default_factory=list)
    
    # Overrides
    kind: EntityKind = field(init=False, default=EntityKind.VARIABLE_SYMBOL)
    
    def __post_init__(self):
        self.kind = EntityKind.VARIABLE_SYMBOL
        super().__post_init__()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize variable symbol."""
        data = super().to_dict()
        data.update({
            'type_reference': self.type_reference,
            'is_const': self.is_const,
            'visibility': self.visibility,
            'attributes': [a.to_dict() for a in self.attributes]
        })
        return data

# ============================================================================
# TYPE ENTITIES
# ============================================================================

@dataclass(kw_only=True)
class TypeEntity(IREntity):
    """
    Base class for canonical types.
    
    All types have size and alignment. Type entities are immutable once created.
    """
    
    size_bytes: int
    alignment_bytes: int
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False)
    
    def __post_init__(self):
        self.entity_id = self.generate_id(self.kind, str(self.size_bytes), str(self.alignment_bytes))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize type."""
        data = super().to_dict()
        data.update({
            'size_bytes': self.size_bytes,
            'alignment_bytes': self.alignment_bytes
        })
        return data

@dataclass(kw_only=True)
class ScalarType(TypeEntity):
    """
    Scalar type (integers, floats, booleans).
    
    Represents primitive types with explicit width, signedness, and representation.
    """
    
    scalar_kind: ScalarKind
    bit_width: int
    is_signed: bool = False
    
    # Overrides
    size_bytes: int = 0
    alignment_bytes: int = 0
    kind: EntityKind = field(init=False, default=EntityKind.SCALAR_TYPE)
    
    def __post_init__(self):
        self.kind = EntityKind.SCALAR_TYPE
        if self.size_bytes == 0:
            self.size_bytes = (self.bit_width + 7) // 8
        if self.alignment_bytes == 0:
            self.alignment_bytes = self.size_bytes
            
        self.entity_id = self.generate_id(
            EntityKind.SCALAR_TYPE,
            self.scalar_kind.value,
            str(self.bit_width),
            str(self.is_signed)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize scalar type."""
        data = super().to_dict()
        data.update({
            'scalar_kind': self.scalar_kind.value,
            'bit_width': self.bit_width,
            'is_signed': self.is_signed
        })
        return data

@dataclass(kw_only=True)
class PointerType(TypeEntity):
    """
    Pointer type.
    
    Represents pointer with explicit depth, target type, and platform-specific
    pointer size.
    """
    
    pointer_depth: int
    target_type_reference: str
    pointer_width: InitVar[int] = 64
    
    # Overrides
    size_bytes: int = 0
    alignment_bytes: int = 0
    kind: EntityKind = field(init=False, default=EntityKind.POINTER_TYPE)
    
    def __post_init__(self, pointer_width: int):
        self.kind = EntityKind.POINTER_TYPE
        self.size_bytes = pointer_width // 8
        self.alignment_bytes = self.size_bytes
        
        self.entity_id = self.generate_id(
            EntityKind.POINTER_TYPE,
            str(self.pointer_depth),
            self.target_type_reference
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize pointer type."""
        data = super().to_dict()
        data.update({
            'pointer_depth': self.pointer_depth,
            'target_type_reference': self.target_type_reference
        })
        return data

# ============================================================================
# FIELD AND PADDING ENTITIES
# ============================================================================

@dataclass(kw_only=True)
class FieldEntity(IREntity):
    """
    Structure or union field.
    
    Represents a single field with explicit offset and type information.
    """
    
    field_index: int
    field_name: Optional[str]
    type_reference: str
    byte_offset: int
    bit_offset: int = 0  # For bitfields
    size_bytes: int = 0
    alignment_bytes: int = 0
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False, default=EntityKind.FIELD)
    
    def __post_init__(self):
        self.kind = EntityKind.FIELD
        self.entity_id = self.generate_id(
            EntityKind.FIELD,
            str(self.field_index),
            self.field_name or f"field_{self.field_index}",
            str(self.byte_offset)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize field."""
        data = super().to_dict()
        data.update({
            'field_index': self.field_index,
            'field_name': self.field_name,
            'type_reference': self.type_reference,
            'byte_offset': self.byte_offset,
            'bit_offset': self.bit_offset,
            'size_bytes': self.size_bytes,
            'alignment_bytes': self.alignment_bytes
        })
        return data

@dataclass(kw_only=True)
class PaddingEntity(IREntity):
    """
    Explicit padding region.
    
    Padding is represented as a first-class entity rather than an implied gap.
    This is critical for detecting layout mismatches.
    """
    
    byte_offset: int
    size_bytes: int
    reason: str = "alignment"
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False, default=EntityKind.PADDING)
    
    def __post_init__(self):
        self.kind = EntityKind.PADDING
        self.entity_id = self.generate_id(
            EntityKind.PADDING,
            str(self.byte_offset),
            str(self.size_bytes)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize padding."""
        data = super().to_dict()
        data.update({
            'byte_offset': self.byte_offset,
            'size_bytes': self.size_bytes,
            'reason': self.reason
        })
        return data

# ============================================================================
# PARAMETER AND RETURN ENTITIES
# ============================================================================

@dataclass(kw_only=True)
class ParameterEntity(IREntity):
    """
    Function parameter.
    
    Represents a single parameter with explicit type and position information.
    """
    
    parameter_index: int
    parameter_name: Optional[str]
    type_reference: str
    is_const: bool = False
    is_volatile: bool = False
    is_restrict: bool = False
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False, default=EntityKind.PARAMETER)
    
    def __post_init__(self):
        self.kind = EntityKind.PARAMETER
        self.entity_id = self.generate_id(
            EntityKind.PARAMETER,
            str(self.parameter_index),
            self.parameter_name or f"param_{self.parameter_index}",
            self.type_reference
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize parameter."""
        data = super().to_dict()
        data.update({
            'parameter_index': self.parameter_index,
            'parameter_name': self.parameter_name,
            'type_reference': self.type_reference,
            'is_const': self.is_const,
            'is_volatile': self.is_volatile,
            'is_restrict': self.is_restrict
        })
        return data

@dataclass(kw_only=True)
class ReturnEntity(IREntity):
    """
    Function return value.
    
    Explicit representation of return mechanism allows modeling complex return
    behavior (hidden pointers, aggregate returns, etc.).
    """
    
    type_reference: str
    return_mechanism: ReturnMechanism = ReturnMechanism.DIRECT
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False, default=EntityKind.RETURN)
    
    def __post_init__(self):
        self.kind = EntityKind.RETURN
        self.entity_id = self.generate_id(
            EntityKind.RETURN,
            self.type_reference,
            self.return_mechanism.value
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize return entity."""
        data = super().to_dict()
        data.update({
            'type_reference': self.type_reference,
            'return_mechanism': self.return_mechanism.value
        })
        return data

# ============================================================================
# ATTRIBUTE ENTITY
# ============================================================================

@dataclass(kw_only=True)
class AttributeEntity(IREntity):
    """
    ABI-relevant attribute.
    
    Captures modifiers that affect calling conventions, layout, or visibility.
    """
    
    attribute_name: str
    attribute_value: Optional[str] = None
    
    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False, default=EntityKind.ATTRIBUTE)
    
    def __post_init__(self):
        self.kind = EntityKind.ATTRIBUTE
        self.entity_id = self.generate_id(
            EntityKind.ATTRIBUTE,
            self.attribute_name,
            self.attribute_value or ""
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize attribute."""
        data = super().to_dict()
        data.update({
            'attribute_name': self.attribute_name,
            'attribute_value': self.attribute_value
        })
        return data

# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "1.0.0"
__module__ = "Module 05: IR Normalization"
__prompt__ = "1/15"
__status__ = "Foundation - IR Entity Model"
