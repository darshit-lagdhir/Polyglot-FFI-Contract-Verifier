"""
Module 05: Intermediate Representation (IR) Normalization
: Foundational IR Entity Model and Graph Architecture

This module implements the core entity model for the IR, providing the foundational
data structures that represent native interfaces in a normalized, canonical form.
"""

import hashlib
from dataclasses import InitVar, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

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

@dataclass
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
    # metadata: Optional['MetadataEntity'] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary."""
        meta = getattr(self, 'metadata', None)
        return {
            'entity_id': self.entity_id,
            'kind': self.kind.value,
            'metadata': meta.to_dict() if meta else None
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

@dataclass
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
    
    # Metadata for consistency (though unusual)
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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

@dataclass
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
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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

@dataclass
class SymbolEntity(IREntity):
    """
    Base class for externally visible symbols.
    
    Represents linkage points that may be referenced across language boundaries.
    """

    linkage_name: str  # Mangled name in binary
    source_name: Optional[str]  # Human-readable name (REQUIRED for Python 3.9 MRO compat)

    # Defaults for base fields
    entity_id: str = field(init=False)
    kind: EntityKind = field(init=False)
    
    # NOTE: metadata is NOT added here because subclasses (FunctionSymbol)
    # add non-default fields. It must be added to subclasses.

    def __post_init__(self) -> None:
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

@dataclass
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
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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

@dataclass
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
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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

@dataclass
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

    def __post_init__(self) -> None:
        self.entity_id = self.generate_id(self.kind, str(self.size_bytes), str(self.alignment_bytes))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize type."""
        data = super().to_dict()
        data.update({
            'size_bytes': self.size_bytes,
            'alignment_bytes': self.alignment_bytes
        })
        return data

@dataclass
class ScalarType(TypeEntity):
    """
    Scalar type (integers, floats, booleans).
    
    Represents primitive types with explicit width, signedness, and representation.
    """

    scalar_kind: ScalarKind = ScalarKind.VOID
    bit_width: int = 0
    is_signed: bool = False

    # Overrides
    size_bytes: int = 0
    alignment_bytes: int = 0
    kind: EntityKind = field(init=False, default=EntityKind.SCALAR_TYPE)
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
        self.kind = EntityKind.SCALAR_TYPE
        if self.size_bytes == 0 and self.bit_width > 0:
            self.size_bytes = (self.bit_width + 7) // 8
        if self.alignment_bytes == 0:
            self.alignment_bytes = max(1, self.size_bytes)

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

@dataclass
class PointerType(TypeEntity):
    """
    Pointer type.
    
    Represents pointer with explicit depth, target type, and platform-specific
    pointer size.
    """

    pointer_depth: int = 1
    target_type_reference: str = ""
    pointer_width: InitVar[int] = 64

    # Overrides
    size_bytes: int = 0
    alignment_bytes: int = 0
    kind: EntityKind = field(init=False, default=EntityKind.POINTER_TYPE)
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self, pointer_width: int) -> None:
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

@dataclass
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
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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

@dataclass
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
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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

@dataclass
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
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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

@dataclass
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
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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

@dataclass
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
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
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
# ARRAY TYPE ()
# ============================================================================

class ArrayKind(Enum):
    """Classification of array types."""
    FIXED_SIZE = "fixed_size"
    INCOMPLETE = "incomplete"
    FLEXIBLE_MEMBER = "flexible_member"

@dataclass
class ArrayType(TypeEntity):
    """Array type with explicit kind and element information."""

    array_kind: ArrayKind = ArrayKind.INCOMPLETE
    element_type_reference: str = ""
    element_count: Optional[int] = None

    # InitVars for size/alignment logic if not provided directly
    element_size: InitVar[int] = 0
    element_alignment: InitVar[int] = 0

    # Defaults for base fields
    size_bytes: int = 0
    alignment_bytes: int = 0
    kind: EntityKind = field(init=False, default=EntityKind.ARRAY_TYPE)
    entity_id: str = field(init=False)
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self, element_size: int, element_alignment: int) -> None:
        self.kind = EntityKind.ARRAY_TYPE
        if self.array_kind == ArrayKind.FIXED_SIZE and self.element_count is not None:
            if self.size_bytes == 0:
                self.size_bytes = element_size * self.element_count
            if self.alignment_bytes == 0:
                self.alignment_bytes = element_alignment
        else:
            if self.size_bytes == 0:
                self.size_bytes = 0
            if self.alignment_bytes == 0:
                self.alignment_bytes = element_alignment if element_alignment > 0 else 1

        count_str = str(self.element_count) if self.element_count is not None else "incomplete"
        self.entity_id = self.generate_id(
            EntityKind.ARRAY_TYPE, self.array_kind.value,
            self.element_type_reference, count_str
        )

    def is_complete(self) -> bool:
        return self.array_kind == ArrayKind.FIXED_SIZE

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'array_kind': self.array_kind.value,
            'element_type_reference': self.element_type_reference,
            'element_count': self.element_count,
            'is_complete': self.is_complete()
        })
        return data

# ============================================================================
# STRUCTURE TYPE
# ============================================================================

@dataclass
class StructureType(TypeEntity):
    """Structure type with ordered fields and explicit padding."""

    structure_name: str = "anonymous"
    fields: List[FieldEntity] = field(default_factory=list)
    padding_regions: List[PaddingEntity] = field(default_factory=list)
    is_packed: bool = False
    explicit_alignment: Optional[int] = None

    # Defaults for base fields
    kind: EntityKind = field(init=False, default=EntityKind.STRUCTURE_TYPE)
    entity_id: str = field(init=False)
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
        self.kind = EntityKind.STRUCTURE_TYPE
        self.entity_id = self.generate_id(
            EntityKind.STRUCTURE_TYPE, self.structure_name, str(self.size_bytes)
        )

    def add_field(self, field: FieldEntity) -> None:
        self.fields.append(field)

    def add_padding(self, padding: PaddingEntity) -> None:
        self.padding_regions.append(padding)

    def validate_layout(self) -> List[str]:
        errors = []
        sorted_fields = sorted(self.fields, key=lambda f: f.byte_offset)

        for i in range(len(sorted_fields) - 1):
            current = sorted_fields[i]
            next_field = sorted_fields[i + 1]
            current_end = current.byte_offset + current.size_bytes

            if next_field.byte_offset < current_end:
                errors.append(
                    f"Field {next_field.field_name} overlaps with {current.field_name}"
                )

        if self.fields:
            last_field = sorted_fields[-1]
            min_size = last_field.byte_offset + last_field.size_bytes
            if self.size_bytes < min_size:
                errors.append(f"Structure size {self.size_bytes} too small")

        if self.alignment_bytes > 0:
            if (self.alignment_bytes & (self.alignment_bytes - 1)) != 0:
                errors.append(f"Alignment {self.alignment_bytes} not power of 2")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'structure_name': self.structure_name,
            'fields': [f.to_dict() for f in self.fields],
            'padding_regions': [p.to_dict() for p in self.padding_regions],
            'is_packed': self.is_packed
        })
        return data

# ============================================================================
# UNION TYPE
# ============================================================================

@dataclass
class UnionType(TypeEntity):
    """Union type with overlapping members."""

    union_name: str = "anonymous"
    members: List[FieldEntity] = field(default_factory=list)

    # Defaults for base fields
    kind: EntityKind = field(init=False, default=EntityKind.UNION_TYPE)
    entity_id: str = field(init=False)
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
        self.kind = EntityKind.UNION_TYPE
        self.entity_id = self.generate_id(
            EntityKind.UNION_TYPE, self.union_name, str(self.size_bytes)
        )

    def add_member(self, member: FieldEntity) -> None:
        if member.byte_offset != 0:
            raise ValueError(
                f"Union member {member.field_name} must be at offset 0"
            )
        self.members.append(member)

    def validate_union_invariants(self) -> List[str]:
        errors = []

        for member in self.members:
            if member.byte_offset != 0:
                errors.append(f"Member {member.field_name} not at offset 0")

        if self.members:
            max_size = max(m.size_bytes for m in self.members)
            if self.size_bytes < max_size:
                errors.append("Union size too small")

            max_align = max(m.alignment_bytes for m in self.members)
            if self.alignment_bytes < max_align:
                errors.append("Union alignment too small")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'union_name': self.union_name,
            'members': [m.to_dict() for m in self.members]
        })
        return data

# ============================================================================
# ENUMERATION TYPE
# ============================================================================

@dataclass
class EnumerationType(TypeEntity):
    """Enumeration type with symbolic integer values."""

    enum_name: str = "anonymous"
    underlying_type_reference: str = "void"
    enumerators: Dict[str, int] = field(default_factory=dict)

    # Defaults for base fields
    kind: EntityKind = field(init=False, default=EntityKind.ENUM_TYPE)
    entity_id: str = field(init=False)
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self) -> None:
        self.kind = EntityKind.ENUM_TYPE
        self.entity_id = self.generate_id(
            EntityKind.ENUM_TYPE, self.enum_name, self.underlying_type_reference
        )

    def add_enumerator(self, name: str, value: int) -> None:
        self.enumerators[name] = value

    def get_value_range(self) -> tuple[int, int]:
        if not self.enumerators:
            return (0, 0)
        values = self.enumerators.values()
        return (min(values), max(values))

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'enum_name': self.enum_name,
            'underlying_type_reference': self.underlying_type_reference,
            'enumerators': self.enumerators
        })
        return data

# ============================================================================
# FUNCTION POINTER TYPE
# ============================================================================

@dataclass
class FunctionPointerType(TypeEntity):
    """Function pointer type with full signature."""

    calling_convention: CallingConvention = CallingConvention.CDECL
    return_type_reference: str = "void"
    parameters: List[ParameterEntity] = field(default_factory=list)
    is_variadic: bool = False
    pointer_width: InitVar[int] = 64

    # Defaults for base fields
    kind: EntityKind = field(init=False, default=EntityKind.FUNCTION_POINTER_TYPE)
    entity_id: str = field(init=False)
    size_bytes: int = field(init=False)
    alignment_bytes: int = field(init=False)
    
    # Metadata
    metadata: Optional['MetadataEntity'] = None

    def __post_init__(self, pointer_width: int) -> None:
        self.kind = EntityKind.FUNCTION_POINTER_TYPE
        self.size_bytes = pointer_width // 8
        self.alignment_bytes = self.size_bytes
        self.entity_id = self.generate_id(
            EntityKind.FUNCTION_POINTER_TYPE,
            self.calling_convention.value, self.return_type_reference
        )

    def add_parameter(self, parameter: ParameterEntity) -> None:
        self.parameters.append(parameter)

    def signature_matches(self, other: 'FunctionPointerType') -> bool:
        if self.calling_convention != other.calling_convention:
            return False
        if self.return_type_reference != other.return_type_reference:
            return False
        if len(self.parameters) != len(other.parameters):
            return False
        for p1, p2 in zip(self.parameters, other.parameters):
            if p1.type_reference != p2.type_reference:
                return False
        if self.is_variadic != other.is_variadic:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'calling_convention': self.calling_convention.value,
            'return_type_reference': self.return_type_reference,
            'parameters': [p.to_dict() for p in self.parameters],
            'is_variadic': self.is_variadic
        })
        return data

# ============================================================================
# TYPE REGISTRY
# ============================================================================

class TypeRegistry:
    """Registry for resolving type references."""

    def __init__(self) -> None:
        self._types: Dict[str, TypeEntity] = {}

    def register_type(self, type_entity: TypeEntity) -> None:
        if type_entity.entity_id in self._types:
            raise ValueError(f"Type {type_entity.entity_id} already registered")
        self._types[type_entity.entity_id] = type_entity

    def resolve_type(self, type_id: str) -> Optional[TypeEntity]:
        return self._types.get(type_id)

    def validate_references(self) -> List[str]:
        errors = []
        for type_id, type_entity in self._types.items():
            if isinstance(type_entity, PointerType):
                if not self.resolve_type(type_entity.target_type_reference):
                    errors.append(f"Pointer {type_id} references undefined type")
            elif isinstance(type_entity, ArrayType):
                if not self.resolve_type(type_entity.element_type_reference):
                    errors.append(f"Array {type_id} references undefined element")
            elif isinstance(type_entity, StructureType):
                for field in type_entity.fields:
                    if not self.resolve_type(field.type_reference):
                        errors.append("Structure field references undefined type")
            elif isinstance(type_entity, UnionType):
                for member in type_entity.members:
                    if not self.resolve_type(member.type_reference):
                        errors.append("Union member references undefined type")
            elif isinstance(type_entity, EnumerationType):
                if not self.resolve_type(type_entity.underlying_type_reference):
                    errors.append("Enum references undefined underlying type")
            elif isinstance(type_entity, FunctionPointerType):
                if not self.resolve_type(type_entity.return_type_reference):
                    errors.append("Function pointer references undefined return type")
                for param in type_entity.parameters:
                    if not self.resolve_type(param.type_reference):
                        errors.append("Function parameter references undefined type")
        return errors

    def get_all_types(self) -> List[TypeEntity]:
        return list(self._types.values())

# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "1.0.0"
__module__ = "Module 05: IR Normalization"
__prompt__ = "2/15"
__status__ = "Complete Type System"
