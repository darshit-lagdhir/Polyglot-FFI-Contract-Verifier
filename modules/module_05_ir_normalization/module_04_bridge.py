"""
Module 05: Module 04 Integration Bridge

Converts Module 04 RawInterfaceArtifact to Module 05 IR entities.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set, Union
from pathlib import Path
import json
import hashlib

from .ir_entities import (
    IREntity, EntityKind, InterfaceUnit, Endianness, ScalarType, PointerType, ArrayType,
    StructureType, UnionType, EnumerationType, FunctionPointerType,
    FunctionSymbol, VariableSymbol, FieldEntity, PaddingEntity,
    ParameterEntity, ReturnEntity, MetadataEntity, AttributeEntity,
    ScalarKind, ArrayKind, CallingConvention, ReturnMechanism,
    TypeRegistry, TypeEntity
)
from .ir_serialization import IRArtifact

# ============================================================================
# CONVERSION ERRORS
# ============================================================================

class ConversionError(Exception):
    """Base class for conversion errors."""
    pass

class InvalidArtifactError(ConversionError):
    """Module 04 artifact is invalid or corrupted."""
    pass

class UnsupportedTypeError(ConversionError):
    """Module 04 contains unsupported type construct."""
    pass

class MissingFieldError(ConversionError):
    """Required field missing from Module 04 artifact."""
    pass

# ============================================================================
# TYPE DEDUPLICATOR
# ============================================================================

class TypeDeduplicator:
    """Deduplicates types by structural equivalence."""
    
    def __init__(self):
        self.type_cache: Dict[str, str] = {}  # structural_hash -> entity_id
        self.entity_cache: Dict[str, TypeEntity] = {} # entity_id -> entity
    
    def get_or_create_type_id(
        self,
        type_data: Dict[str, Any],
        converter: 'TypeConverter'
    ) -> str:
        """
        Get entity ID for type, computing structural hash.
        
        Returns entity ID for deduplicated type.
        """
        # We need a stable hash to check cache
        struct_hash = self._compute_stable_structural_hash(type_data)
        
        if struct_hash in self.type_cache:
            return self.type_cache[struct_hash]
        
        # If not in cache, we must convert it
        entity = converter.convert_type(type_data)
        self.type_cache[struct_hash] = entity.entity_id
        self.entity_cache[entity.entity_id] = entity
        
        return entity.entity_id

    def _compute_stable_structural_hash(self, type_data: Dict[str, Any]) -> str:
        """Compute a stable hash for internal deduplication before entity creation."""
        # Use a simplified version of to_dict/json for hashing
        # This is strictly internal to avoid infinite recursion and ensure we don't 
        # recreate the same entity twice.
        d = type_data.copy()
        # Remove volatile fields if any
        if 'kind' not in d:
             return "unknown"
        
        kind = d['kind']
        components = [kind]
        
        if kind == 'scalar':
            components.extend([d.get('name', ''), str(d.get('size', 0)), str(d.get('is_signed', False))])
        elif kind == 'pointer':
            pointee = d.get('pointee', {})
            components.append(self._compute_stable_structural_hash(pointee))
        elif kind == 'array':
            elem = d.get('element_type', {})
            components.append(self._compute_stable_structural_hash(elem))
            components.append(str(d.get('element_count')))
        elif kind == 'structure':
            components.append(d.get('name', 'anonymous'))
            components.append(str(d.get('size', 0)))
        elif kind == 'union':
            components.append(d.get('name', 'anonymous'))
            components.append(str(d.get('size', 0)))
        elif kind == 'enum':
            components.append(d.get('name', 'anonymous'))
            
        return hashlib.sha256("::".join(components).encode()).hexdigest()

# ============================================================================
# TYPE CONVERTER
# ============================================================================

class TypeConverter:
    """Converts Module 04 types to Module 05 types."""
    
    def __init__(self, deduplicator: TypeDeduplicator):
        self.deduplicator = deduplicator
        self.pointer_width = 64 # Default
    
    def set_pointer_width(self, width: int):
        self.pointer_width = width

    def convert_type(self, type_data: Dict[str, Any]) -> TypeEntity:
        """
        Convert Module 04 type to Module 05 type entity.
        """
        kind = type_data.get('kind')
        
        if kind == 'scalar':
            return self._convert_scalar(type_data)
        elif kind == 'pointer':
            return self._convert_pointer(type_data)
        elif kind == 'array':
            return self._convert_array(type_data)
        elif kind == 'structure':
            return self._convert_structure(type_data)
        elif kind == 'union':
            return self._convert_union(type_data)
        elif kind == 'enum':
            return self._convert_enum(type_data)
        elif kind == 'function' or kind == 'function_pointer':
            return self._convert_function_pointer(type_data)
        elif kind == 'typedef':
            # Handle typedef by resolving target
            target = type_data.get('target', {})
            return self.convert_type(target)
        else:
            raise UnsupportedTypeError(f"Unsupported type kind: {kind}")
    
    def _convert_function_pointer(self, type_data: Dict[str, Any]) -> FunctionPointerType:
        ret_data = type_data.get('return_type', {'kind': 'scalar', 'name': 'void', 'size': 0})
        ret_id = self.deduplicator.get_or_create_type_id(ret_data, self)
        
        fp = FunctionPointerType(
            calling_convention=CallingConvention.CDECL, # Default for pointer types in M04
            return_type_reference=ret_id,
            is_variadic=type_data.get('is_variadic', False),
            pointer_width=self.pointer_width
        )
        
        for i, p_data in enumerate(type_data.get('parameters', [])):
            pt_data = p_data.get('type', {})
            pt_id = self.deduplicator.get_or_create_type_id(pt_data, self)
            fp.add_parameter(ParameterEntity(
                parameter_index=i,
                parameter_name=p_data.get('name'),
                type_reference=pt_id
            ))
            
        return fp
    
    def _convert_scalar(self, type_data: Dict[str, Any]) -> ScalarType:
        name = type_data.get('name', '').lower()
        size = type_data.get('size', 0)
        is_signed = type_data.get('is_signed', False)
        
        if 'void' in name:
            kind = ScalarKind.VOID
        elif 'bool' in name or '_bool' in name:
            kind = ScalarKind.BOOLEAN
        elif 'float' in name or 'double' in name or 'long double' in name:
            kind = ScalarKind.FLOATING_POINT
        elif 'char' in name:
            kind = ScalarKind.CHARACTER
        elif is_signed:
            kind = ScalarKind.SIGNED_INTEGER
        else:
            kind = ScalarKind.UNSIGNED_INTEGER
            
        return ScalarType(
            scalar_kind=kind,
            bit_width=size * 8,
            is_signed=is_signed,
            size_bytes=size,
            alignment_bytes=type_data.get('alignment', size)
        )
    
    def _convert_pointer(self, type_data: Dict[str, Any]) -> PointerType:
        pointee_data = type_data.get('pointee', {})
        target_id = self.deduplicator.get_or_create_type_id(pointee_data, self)
        
        return PointerType(
            pointer_depth=1, # Module 04 usually nests pointers
            target_type_reference=target_id,
            pointer_width=self.pointer_width
        )
    
    def _convert_array(self, type_data: Dict[str, Any]) -> ArrayType:
        element_data = type_data.get('element_type', {})
        element_id = self.deduplicator.get_or_create_type_id(element_data, self)
        element_count = type_data.get('element_count')
        
        if element_count is None:
            kind = ArrayKind.INCOMPLETE
        else:
            kind = ArrayKind.FIXED_SIZE
            
        return ArrayType(
            array_kind=kind,
            element_type_reference=element_id,
            element_count=element_count,
            element_size=element_data.get('size', 0),
            element_alignment=element_data.get('alignment', 1)
        )
    
    def _convert_structure(self, type_data: Dict[str, Any]) -> StructureType:
        name = type_data.get('name', 'anonymous')
        size = type_data.get('size', 0)
        align = type_data.get('alignment', 1)
        
        struct = StructureType(
            structure_name=name,
            size_bytes=size,
            alignment_bytes=align,
            is_packed=type_data.get('is_packed', False)
        )
        
        # Convert fields
        fields_data = type_data.get('fields', [])
        for i, f_data in enumerate(fields_data):
            f_type_data = f_data.get('type', {})
            f_type_id = self.deduplicator.get_or_create_type_id(f_type_data, self)
            
            field = FieldEntity(
                field_index=i,
                field_name=f_data.get('name'),
                type_reference=f_type_id,
                byte_offset=f_data.get('offset', 0),
                bit_offset=f_data.get('bit_offset', 0),
                size_bytes=f_type_data.get('size', 0),
                alignment_bytes=f_type_data.get('alignment', 1)
            )
            struct.add_field(field)
            
        # Compute padding
        padding = self._compute_padding(fields_data, size)
        for p in padding:
            struct.add_padding(p)
            
        return struct
    
    def _convert_union(self, type_data: Dict[str, Any]) -> UnionType:
        name = type_data.get('name', 'anonymous')
        size = type_data.get('size', 0)
        align = type_data.get('alignment', 1)
        
        union = UnionType(
            union_name=name,
            size_bytes=size,
            alignment_bytes=align
        )
        
        members_data = type_data.get('members', [])
        for i, m_data in enumerate(members_data):
            m_type_data = m_data.get('type', {})
            m_type_id = self.deduplicator.get_or_create_type_id(m_type_data, self)
            
            member = FieldEntity(
                field_index=i,
                field_name=m_data.get('name'),
                type_reference=m_type_id,
                byte_offset=0,
                size_bytes=m_type_data.get('size', 0),
                alignment_bytes=m_type_data.get('alignment', 1)
            )
            union.add_member(member)
            
        return union
    
    def _convert_enum(self, type_data: Dict[str, Any]) -> EnumerationType:
        name = type_data.get('name', 'anonymous')
        underlying = type_data.get('underlying_type', {'kind': 'scalar', 'name': 'int', 'size': 4, 'is_signed': True})
        underlying_id = self.deduplicator.get_or_create_type_id(underlying, self)
        
        enum = EnumerationType(
            enum_name=name,
            underlying_type_reference=underlying_id,
            size_bytes=type_data.get('size', 4),
            alignment_bytes=type_data.get('alignment', 4)
        )
        
        for en_data in type_data.get('enumerators', []):
            enum.add_enumerator(en_data['name'], en_data['value'])
            
        return enum

    def _compute_padding(self, fields_data: List[Dict[str, Any]], total_size: int) -> List[PaddingEntity]:
        padding = []
        if not fields_data:
            if total_size > 0:
                 padding.append(PaddingEntity(byte_offset=0, size_bytes=total_size, reason="empty structure"))
            return padding
            
        sorted_fields = sorted(fields_data, key=lambda f: f.get('offset', 0))
        current = 0
        
        for f in sorted_fields:
            offset = f.get('offset', 0)
            if offset > current:
                padding.append(PaddingEntity(byte_offset=current, size_bytes=offset - current, reason="field alignment"))
            
            f_size = f.get('type', {}).get('size', 0)
            current = offset + f_size
            
        if total_size > current:
            padding.append(PaddingEntity(byte_offset=current, size_bytes=total_size - current, reason="trailing padding"))
            
        return padding

# ============================================================================
# SYMBOL CONVERTER
# ============================================================================

class SymbolConverter:
    """Converts Module 04 symbols to Module 05 symbols."""
    
    def __init__(self, deduplicator: TypeDeduplicator, type_converter: TypeConverter):
        self.deduplicator = deduplicator
        self.type_converter = type_converter
    
    def convert_symbol(self, symbol_data: Dict[str, Any]) -> Any:
        kind = symbol_data.get('kind')
        if kind == 'function':
            return self._convert_function(symbol_data)
        elif kind == 'variable':
            return self._convert_variable(symbol_data)
        else:
            raise UnsupportedTypeError(f"Unsupported symbol kind: {kind}")
            
    def _convert_function(self, data: Dict[str, Any]) -> FunctionSymbol:
        name = data.get('name')
        mangled = data.get('mangled_name', name)
        cc = self._translate_cc(data.get('calling_convention', 'cdecl'))
        
        func = FunctionSymbol(
            linkage_name=mangled,
            source_name=name,
            calling_convention=cc,
            is_variadic=data.get('is_variadic', False)
        )
        
        # Return type
        ret_type_data = data.get('return_type', {'kind': 'scalar', 'name': 'void', 'size': 0})
        ret_type_id = self.deduplicator.get_or_create_type_id(ret_type_data, self.type_converter)
        func.return_entity = ReturnEntity(
            type_reference=ret_type_id,
            return_mechanism=ReturnMechanism.DIRECT # Default for now
        )
        
        # Parameters
        for i, p_data in enumerate(data.get('parameters', [])):
            p_type_data = p_data.get('type', {})
            p_type_id = self.deduplicator.get_or_create_type_id(p_type_data, self.type_converter)
            
            param = ParameterEntity(
                parameter_index=i,
                parameter_name=p_data.get('name'),
                type_reference=p_type_id
            )
            # Qualifiers
            quals = p_type_data.get('qualifiers', [])
            param.is_const = 'const' in quals
            param.is_volatile = 'volatile' in quals
            param.is_restrict = 'restrict' in quals
            
            func.parameters.append(param)
            
        # Metadata
        if 'source_location' in data:
            loc = data['source_location']
            func.metadata = MetadataEntity(
                source_file=loc.get('file'),
                line_number=loc.get('line'),
                column_number=loc.get('column')
            )
            
        return func
        
    def _convert_variable(self, data: Dict[str, Any]) -> VariableSymbol:
        name = data.get('name')
        type_data = data.get('type', {})
        type_id = self.deduplicator.get_or_create_type_id(type_data, self.type_converter)
        
        var = VariableSymbol(
            linkage_name=name,
            source_name=name,
            type_reference=type_id,
            is_const='const' in type_data.get('qualifiers', []),
            visibility=data.get('linkage', 'extern')
        )
        
        if 'source_location' in data:
            loc = data['source_location']
            var.metadata = MetadataEntity(
                source_file=loc.get('file'),
                line_number=loc.get('line'),
                column_number=loc.get('column')
            )
            
        return var

    def _translate_cc(self, cc_str: str) -> CallingConvention:
        mapping = {
            'cdecl': CallingConvention.CDECL,
            'stdcall': CallingConvention.STDCALL,
            'fastcall': CallingConvention.FASTCALL,
            'thiscall': CallingConvention.THISCALL,
            'vectorcall': CallingConvention.VECTORCALL,
            'win64': CallingConvention.WIN64,
            'aapcs': CallingConvention.AAPCS,
            'aapcs_vfp': CallingConvention.AAPCS_VFP,
            'sysv_amd64': CallingConvention.SYSV_AMD64
        }
        # Handle libclang variations
        cc_lower = cc_str.lower()
        if cc_lower == 'c': return CallingConvention.CDECL
        if 'stdcall' in cc_lower: return CallingConvention.STDCALL
        
        return mapping.get(cc_lower, CallingConvention.CDECL)

# ============================================================================
# ============================================================================

class Module04Bridge:
    """Bridges Module 04 RawInterfaceArtifact to Module 05 IR."""
    
    def __init__(self):
        self.deduplicator = TypeDeduplicator()
        self.type_converter = TypeConverter(self.deduplicator)
        self.symbol_converter = SymbolConverter(self.deduplicator, self.type_converter)
        self.type_registry = TypeRegistry()
        
    def convert_artifact(self, artifact_path: Union[Path, str, Dict[str, Any]]) -> IRArtifact:
        """Convert Module 04 artifact to Module 05 IR."""
        if isinstance(artifact_path, (str, Path)):
            with open(artifact_path, 'r') as f:
                data = json.load(f)
        else:
            data = artifact_path
            
        self._validate_header(data)
        
        ctx = data.get('compilation_context', {})
        interface_unit = self._convert_context(ctx)
        
        self.type_converter.set_pointer_width(interface_unit.pointer_width)
        
        # Convert symbols (this will trigger type conversion recursively)
        for s_data in data.get('external_symbols', []):
            try:
                symbol = self.symbol_converter.convert_symbol(s_data)
                interface_unit.symbols.append(symbol)
            except Exception as e:
                # Log or re-raise
                print(f"Warning: Symbol conversion failed: {e}")
                
        # Register all converted types
        for entity_id, entity in self.deduplicator.entity_cache.items():
            self.type_registry.register_type(entity)
            interface_unit.types.append(entity)
            
        # Optional: convert explicit type_information if present
        for t_data in data.get('type_information', []):
            self.deduplicator.get_or_create_type_id(t_data, self.type_converter)
            
        # Re-register any newly converted types
        for entity_id, entity in self.deduplicator.entity_cache.items():
            if entity_id not in [t.entity_id for t in interface_unit.types]:
                self.type_registry.register_type(entity)
                interface_unit.types.append(entity)
                
        artifact = IRArtifact(
            interface_unit=interface_unit,
            creation_timestamp=data.get('generation_timestamp')
        )
        return artifact

    def _validate_header(self, data: Dict[str, Any]):
        if 'artifact_version' not in data:
            raise InvalidArtifactError("Missing artifact_version")
            
    def _convert_context(self, ctx: Dict[str, Any]) -> InterfaceUnit:
        triple = ctx.get('target_triple', 'x86_64-pc-linux-gnu')
        parts = triple.split('-')
        arch = parts[0]
        vendor = parts[1] if len(parts) > 1 else "unknown"
        os = parts[2] if len(parts) > 2 else "unknown"
        
        # Determine pointer width
        if '64' in arch:
            ptr_width = 64
        elif '86' in arch or 'arm' in arch or '32' in arch:
            ptr_width = 32
        else:
            ptr_width = 64
            
        # Determine ABI
        abi = "sysv"
        if os == "windows" or "msvc" in triple:
            abi = "win64" if ptr_width == 64 else "stdcall"
        elif "arm" in arch:
            abi = "aapcs"
            
        return InterfaceUnit(
            target_architecture=arch,
            operating_system=os,
            pointer_width=ptr_width,
            endianness=Endianness.LITTLE, # Default
            abi_mode=abi,
            compiler_family=ctx.get('compiler', 'clang'),
            compiler_version=ctx.get('compiler_version', '1.0.0'),
            compilation_flags=ctx.get('compilation_flags', [])
        )

__all__ = [
    'Module04Bridge',
    'ConversionError',
    'InvalidArtifactError',
    'UnsupportedTypeError',
    'MissingFieldError'
]
