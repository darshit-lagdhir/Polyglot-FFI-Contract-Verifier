"""
Module 05: Type Normalization Pipeline

Transforms raw compiler-extracted types into canonical IR types.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any, Tuple
from pathlib import Path

from .ir_entities import (
    TypeEntity, ScalarType, PointerType, ArrayType, StructureType,
    UnionType, EnumerationType, FunctionPointerType,
    FieldEntity, PaddingEntity, ParameterEntity, ReturnEntity,
    TypeRegistry, InterfaceUnit,
    ScalarKind, ArrayKind, CallingConvention, ReturnMechanism,
    EntityKind
)

# ============================================================================
# RAW TYPE DATA STRUCTURES (INPUT FROM MODULE 04)
# ============================================================================

@dataclass
class RawTypeData:
    """Raw type data from Module 04 ingestion."""
    kind: str  # "scalar", "pointer", "array", "structure", etc.
    name: str
    size_bytes: int
    alignment_bytes: int
    
    # Type-specific fields
    scalar_kind: Optional[ScalarKind] = None
    bit_width: Optional[int] = None
    is_signed: Optional[bool] = None
    
    pointer_depth: Optional[int] = None
    target_type_name: Optional[str] = None
    
    array_kind: Optional[ArrayKind] = None
    element_type_name: Optional[str] = None
    element_count: Optional[int] = None
    
    fields: List['RawFieldData'] = field(default_factory=list)
    members: List['RawFieldData'] = field(default_factory=list)
    
    enumerators: Dict[str, int] = field(default_factory=dict)
    underlying_type_name: Optional[str] = None
    
    # Typedef
    is_typedef: bool = False
    typedef_target: Optional[str] = None

@dataclass
class RawFieldData:
    """Raw field/member data."""
    name: Optional[str]
    type_name: str
    byte_offset: int
    size_bytes: int
    alignment_bytes: int
    bit_offset: Optional[int] = None
    bit_width: Optional[int] = None

# ============================================================================
# NORMALIZATION ERRORS
# ============================================================================

class NormalizationError(Exception):
    """Base class for normalization errors."""
    pass

class CircularTypedefError(NormalizationError):
    """Circular typedef chain detected."""
    pass

class TypeResolutionError(NormalizationError):
    """Type reference cannot be resolved."""
    pass

# ============================================================================
# TYPEDEF RESOLVER
# ============================================================================

class TypedefResolver:
    """Resolves typedef chains to canonical types."""
    
    def __init__(self):
        self.typedef_map: Dict[str, str] = {}
        self.typedef_chains: Dict[str, List[str]] = {}
    
    def add_typedef(self, source_name: str, target_name: str):
        """Register a typedef."""
        self.typedef_map[source_name] = target_name
    
    def resolve(self, type_name: str) -> Tuple[str, List[str]]:
        """
        Resolve typedef chain to canonical type.
        
        Returns:
            (canonical_name, typedef_chain)
        """
        if type_name in self.typedef_chains:
            # We need to return the terminal type. 
            # The cache should store the result.
            visited = set()
            current = type_name
            chain = []
            while current in self.typedef_map:
                if current in visited:
                    raise CircularTypedefError(
                        f"Circular typedef: {' -> '.join(chain + [current])}"
                    )
                visited.add(current)
                chain.append(current)
                current = self.typedef_map[current]
            return (current, chain)
        
        chain = []
        visited = set()
        current = type_name
        
        while current in self.typedef_map:
            if current in visited:
                raise CircularTypedefError(
                    f"Circular typedef: {' -> '.join(chain + [current])}"
                )
            
            visited.add(current)
            chain.append(current)
            current = self.typedef_map[current]
        
        # Cache result
        self.typedef_chains[type_name] = chain
        
        return (current, chain)

# ============================================================================
# ALIGNMENT UTILITIES
# ============================================================================

def align_up(value: int, alignment: int) -> int:
    """Align value up to next alignment boundary."""
    if alignment == 0:
        return value
    return (value + alignment - 1) & ~(alignment - 1)

def is_power_of_two(n: int) -> bool:
    """Check if number is power of 2."""
    return n > 0 and (n & (n - 1)) == 0

# ============================================================================
# TYPE NORMALIZATION PIPELINE
# ============================================================================

class TypeNormalizationPipeline:
    """
    Orchestrates type normalization process.
    
    Transforms raw compiler-extracted types into canonical IR types.
    """
    
    def __init__(self, interface_unit: InterfaceUnit):
        """
        Initialize normalization pipeline.
        
        Args:
            interface_unit: IR interface unit providing platform context
        """
        self.interface_unit = interface_unit
        self.type_registry = TypeRegistry()
        self.typedef_resolver = TypedefResolver()
        
        # Track normalization state
        self.normalized_types: Dict[str, TypeEntity] = {}
        self.in_progress: Set[str] = set()
    
    def normalize_all_types(
        self,
        raw_types: List[RawTypeData]
    ) -> List[TypeEntity]:
        """
        Normalize all types from raw compiler data.
        
        Args:
            raw_types: Raw type data from Module 04
            
        Returns:
            List of normalized type entities
        """
        # : Build typedef map
        for raw_type in raw_types:
            if raw_type.is_typedef and raw_type.typedef_target:
                self.typedef_resolver.add_typedef(
                    raw_type.name,
                    raw_type.typedef_target
                )
        
        # : Normalize each type
        normalized = []
        for raw_type in raw_types:
            if raw_type.is_typedef:
                continue  # Skip typedefs, they're resolved during normalization
            
            try:
                normalized_type = self.normalize_type(raw_type)
                if normalized_type:
                    normalized.append(normalized_type)
            except Exception as e:
                raise NormalizationError(
                    f"Failed to normalize type {raw_type.name}: {e}"
                )
        
        # : Validate all references
        errors = self.type_registry.validate_references()
        if errors:
            raise NormalizationError(
                f"Type reference validation failed:\n" + "\n".join(errors)
            )
        
        return normalized
    
    def normalize_type(self, raw_type: RawTypeData) -> Optional[TypeEntity]:
        """
        Normalize a single type.
        
        Args:
            raw_type: Raw type data
            
        Returns:
            Normalized type entity
        """
        # Check if already normalized
        if raw_type.name in self.normalized_types:
            return self.normalized_types[raw_type.name]
        
        # Detect circular dependencies
        if raw_type.name in self.in_progress:
            raise NormalizationError(
                f"Circular type dependency: {raw_type.name}"
            )
        
        self.in_progress.add(raw_type.name)
        
        try:
            # Normalize based on kind
            if raw_type.kind == "scalar":
                normalized = self._normalize_scalar(raw_type)
            elif raw_type.kind == "pointer":
                normalized = self._normalize_pointer(raw_type)
            elif raw_type.kind == "array":
                normalized = self._normalize_array(raw_type)
            elif raw_type.kind == "structure":
                normalized = self._normalize_structure(raw_type)
            elif raw_type.kind == "union":
                normalized = self._normalize_union(raw_type)
            elif raw_type.kind == "enum":
                normalized = self._normalize_enum(raw_type)
            elif raw_type.kind == "function_pointer":
                normalized = self._normalize_function_pointer(raw_type)
            else:
                raise NormalizationError(f"Unknown type kind: {raw_type.kind}")
            
            # Register normalized type
            if normalized:
                self.type_registry.register_type(normalized)
                self.normalized_types[raw_type.name] = normalized
            
            return normalized
        
        finally:
            self.in_progress.remove(raw_type.name)
    
    def _normalize_scalar(self, raw_type: RawTypeData) -> ScalarType:
        """Normalize scalar type."""
        if not raw_type.scalar_kind or raw_type.bit_width is None:
            raise NormalizationError(
                f"Scalar type {raw_type.name} missing required fields"
            )
        
        return ScalarType(
            scalar_kind=raw_type.scalar_kind,
            bit_width=raw_type.bit_width,
            is_signed=raw_type.is_signed or False
        )
    
    def _normalize_pointer(self, raw_type: RawTypeData) -> PointerType:
        """Normalize pointer type."""
        if not raw_type.target_type_name:
            raise NormalizationError(
                f"Pointer type {raw_type.name} missing target type"
            )
        
        # Resolve target type reference
        target_name, _ = self.typedef_resolver.resolve(raw_type.target_type_name)
        
        # Get target type entity ID
        if target_name in self.normalized_types:
            target_id = self.normalized_types[target_name].entity_id
        else:
            # Use name as placeholder - will be validated later
            target_id = target_name
        
        return PointerType(
            pointer_depth=raw_type.pointer_depth or 1,
            target_type_reference=target_id,
            pointer_width=self.interface_unit.pointer_width
        )
    
    def _normalize_array(self, raw_type: RawTypeData) -> ArrayType:
        """Normalize array type."""
        if not raw_type.element_type_name or not raw_type.array_kind:
            raise NormalizationError(
                f"Array type {raw_type.name} missing required fields"
            )
        
        # Resolve element type
        element_name, _ = self.typedef_resolver.resolve(
            raw_type.element_type_name
        )
        
        if element_name in self.normalized_types:
            element_type = self.normalized_types[element_name]
            element_id = element_type.entity_id
            element_size = element_type.size_bytes
            element_align = element_type.alignment_bytes
        else:
            element_id = element_name
            element_size = 0
            element_align = 1
        
        return ArrayType(
            array_kind=raw_type.array_kind,
            element_type_reference=element_id,
            element_count=raw_type.element_count,
            element_size=element_size,
            element_alignment=element_align
        )
    
    def _normalize_structure(self, raw_type: RawTypeData) -> StructureType:
        """Normalize structure type with explicit padding."""
        struct = StructureType(
            structure_name=raw_type.name,
            size_bytes=raw_type.size_bytes,
            alignment_bytes=raw_type.alignment_bytes
        )
        
        # Sort fields by offset
        sorted_fields = sorted(raw_type.fields, key=lambda f: f.byte_offset)
        
        current_offset = 0
        for i, raw_field in enumerate(sorted_fields):
            # Resolve field type
            field_type_name, _ = self.typedef_resolver.resolve(
                raw_field.type_name
            )
            
            if field_type_name in self.normalized_types:
                field_type_id = self.normalized_types[field_type_name].entity_id
            else:
                field_type_id = field_type_name
            
            # Insert padding if gap exists
            if raw_field.byte_offset > current_offset:
                padding_size = raw_field.byte_offset - current_offset
                padding = PaddingEntity(
                    byte_offset=current_offset,
                    size_bytes=padding_size,
                    reason="field alignment"
                )
                struct.add_padding(padding)
            
            # Create field
            field = FieldEntity(
                field_index=i,
                field_name=raw_field.name,
                type_reference=field_type_id,
                byte_offset=raw_field.byte_offset
            )
            field.size_bytes = raw_field.size_bytes
            field.alignment_bytes = raw_field.alignment_bytes
            
            if raw_field.bit_width is not None:
                field.bit_offset = raw_field.bit_offset or 0
            
            struct.add_field(field)
            current_offset = raw_field.byte_offset + raw_field.size_bytes
        
        # Add trailing padding
        if raw_type.size_bytes > current_offset:
            trailing_size = raw_type.size_bytes - current_offset
            trailing_padding = PaddingEntity(
                byte_offset=current_offset,
                size_bytes=trailing_size,
                reason="structure end padding"
            )
            struct.add_padding(trailing_padding)
        
        return struct
    
    def _normalize_union(self, raw_type: RawTypeData) -> UnionType:
        """Normalize union type."""
        union = UnionType(
            union_name=raw_type.name,
            size_bytes=raw_type.size_bytes,
            alignment_bytes=raw_type.alignment_bytes
        )
        
        for i, raw_member in enumerate(raw_type.members):
            # Resolve member type
            member_type_name, _ = self.typedef_resolver.resolve(
                raw_member.type_name
            )
            
            if member_type_name in self.normalized_types:
                member_type_id = self.normalized_types[member_type_name].entity_id
            else:
                member_type_id = member_type_name
            
            # Create member (all at offset 0)
            member = FieldEntity(
                field_index=i,
                field_name=raw_member.name,
                type_reference=member_type_id,
                byte_offset=0  # Union invariant
            )
            member.size_bytes = raw_member.size_bytes
            member.alignment_bytes = raw_member.alignment_bytes
            
            union.add_member(member)
        
        return union
    
    def _normalize_enum(self, raw_type: RawTypeData) -> EnumerationType:
        """Normalize enumeration type."""
        if not raw_type.underlying_type_name:
            raise NormalizationError(
                f"Enum {raw_type.name} missing underlying type"
            )
        
        # Resolve underlying type
        underlying_name, _ = self.typedef_resolver.resolve(
            raw_type.underlying_type_name
        )
        
        if underlying_name in self.normalized_types:
            underlying_id = self.normalized_types[underlying_name].entity_id
        else:
            underlying_id = underlying_name
        
        enum = EnumerationType(
            enum_name=raw_type.name,
            underlying_type_reference=underlying_id,
            size_bytes=raw_type.size_bytes,
            alignment_bytes=raw_type.alignment_bytes
        )
        
        # Add enumerators
        for name, value in raw_type.enumerators.items():
            enum.add_enumerator(name, value)
        
        return enum
    
    def _normalize_function_pointer(
        self,
        raw_type: RawTypeData
    ) -> FunctionPointerType:
        """Normalize function pointer type."""
        # Use default calling convention if not specified
        calling_conv = CallingConvention.CDECL  # Platform default
        
        # Resolve return type
        return_type_name = "void"  # Default
        if return_type_name in self.normalized_types:
            return_type_id = self.normalized_types[return_type_name].entity_id
        else:
            return_type_id = return_type_name
        
        func_ptr = FunctionPointerType(
            calling_convention=calling_conv,
            return_type_reference=return_type_id,
            pointer_width=self.interface_unit.pointer_width
        )
        
        return func_ptr

__all__ = [
    'TypeNormalizationPipeline',
    'TypedefResolver',
    'NormalizationError',
    'CircularTypedefError',
    'TypeResolutionError',
    'RawTypeData',
    'RawFieldData'
]
