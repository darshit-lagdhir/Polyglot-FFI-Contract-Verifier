"""
Unit tests for Module 05: IR Entity Model
Basic test suite (40 tests)
"""

import pytest
from pathlib import Path
import sys

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_05_ir_normalization.ir_entities import (
    EntityKind, ScalarKind, CallingConvention, ReturnMechanism, Endianness,
    IREntity, MetadataEntity, InterfaceUnit,
    SymbolEntity, FunctionSymbol, VariableSymbol,
    TypeEntity, ScalarType, PointerType,
    FieldEntity, PaddingEntity, ParameterEntity, ReturnEntity, AttributeEntity
)

# ============================================================================
# TEST: ENTITY KIND ENUMERATIONS
# ============================================================================

class TestEnumerations:
    """Test IR enumeration types."""
    
    def test_entity_kind_values(self):
        """Test EntityKind enumeration has expected values."""
        assert EntityKind.INTERFACE_UNIT.value == "interface_unit"
        assert EntityKind.FUNCTION_SYMBOL.value == "function_symbol"
        assert EntityKind.SCALAR_TYPE.value == "scalar_type"
    
    def test_scalar_kind_values(self):
        """Test ScalarKind enumeration."""
        assert ScalarKind.SIGNED_INTEGER.value == "signed_integer"
        assert ScalarKind.UNSIGNED_INTEGER.value == "unsigned_integer"
        assert ScalarKind.FLOATING_POINT.value == "floating_point"
    
    def test_calling_convention_values(self):
        """Test CallingConvention enumeration."""
        assert CallingConvention.CDECL.value == "cdecl"
        assert CallingConvention.STDCALL.value == "stdcall"
        assert CallingConvention.WIN64.value == "win64"
    
    def test_return_mechanism_values(self):
        """Test ReturnMechanism enumeration."""
        assert ReturnMechanism.DIRECT.value == "direct"
        assert ReturnMechanism.HIDDEN_POINTER.value == "hidden_pointer"
    
    def test_endianness_values(self):
        """Test Endianness enumeration."""
        assert Endianness.LITTLE.value == "little"
        assert Endianness.BIG.value == "big"

# ============================================================================
# TEST: BASE IR ENTITY
# ============================================================================

class TestIREntity:
    """Test base IREntity class."""
    
    def test_entity_creation(self):
        """Test creating base entity."""
        entity = IREntity(entity_id="test_id", kind=EntityKind.METADATA, metadata=None)
        
        assert entity.entity_id == "test_id"
        assert entity.kind == EntityKind.METADATA
        assert entity.metadata is None
    
    def test_entity_id_generation(self):
        """Test stable ID generation."""
        id1 = IREntity.generate_id(EntityKind.FUNCTION_SYMBOL, "func_name", "cdecl")
        id2 = IREntity.generate_id(EntityKind.FUNCTION_SYMBOL, "func_name", "cdecl")
        
        # Same inputs produce same ID (deterministic)
        assert id1 == id2
        
        # Different inputs produce different IDs
        id3 = IREntity.generate_id(EntityKind.FUNCTION_SYMBOL, "other_name", "cdecl")
        assert id1 != id3
    
    def test_entity_serialization(self):
        """Test entity serialization."""
        entity = IREntity(entity_id="test_id", kind=EntityKind.FUNCTION_SYMBOL, metadata=None)
        
        data = entity.to_dict()
        
        assert data['entity_id'] == "test_id"
        assert data['kind'] == "function_symbol"

# ============================================================================
# TEST: METADATA ENTITY
# ============================================================================

class TestMetadataEntity:
    """Test MetadataEntity."""
    
    def test_metadata_creation(self):
        """Test creating metadata."""
        metadata = MetadataEntity(
            source_file="test.h",
            line_number=42,
            column_number=10
        )
        
        assert metadata.source_file == "test.h"
        assert metadata.line_number == 42
        assert metadata.column_number == 10
        assert metadata.kind == EntityKind.METADATA
    
    def test_metadata_with_none_values(self):
        """Test metadata with None values."""
        metadata = MetadataEntity()
        
        assert metadata.source_file is None
        assert metadata.line_number is None
    
    def test_metadata_serialization(self):
        """Test metadata serialization."""
        metadata = MetadataEntity(source_file="api.h", line_number=100, column_number=5)
        
        data = metadata.to_dict()
        
        assert data['source_file'] == "api.h"
        assert data['line_number'] == 100
        assert data['column_number'] == 5

# ============================================================================
# TEST: INTERFACE UNIT
# ============================================================================

class TestInterfaceUnit:
    """Test InterfaceUnit - top-level IR container."""
    
    def test_interface_unit_creation(self):
        """Test creating interface unit."""
        unit = InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=Endianness.LITTLE,
            abi_mode="sysv",
            compiler_family="gcc",
            compiler_version="11.2.0"
        )
        
        assert unit.target_architecture == "x86_64"
        assert unit.operating_system == "linux"
        assert unit.pointer_width == 64
        assert unit.endianness == Endianness.LITTLE
        assert unit.abi_mode == "sysv"
        assert unit.compiler_family == "gcc"
        assert unit.kind == EntityKind.INTERFACE_UNIT
    
    def test_interface_unit_defaults(self):
        """Test interface unit default values."""
        unit = InterfaceUnit(
            target_architecture="aarch64", operating_system="macos", 
            pointer_width=64, endianness=Endianness.LITTLE, abi_mode="aapcs",
            compiler_family="clang", compiler_version="14.0.0"
        )
        
        assert unit.ir_schema_version == "1.0.0"
        assert unit.normalization_version == "1.0.0"
        assert len(unit.symbols) == 0
        assert len(unit.types) == 0
    
    def test_interface_unit_serialization(self):
        """Test interface unit serialization."""
        unit = InterfaceUnit(
            target_architecture="x86_64", operating_system="windows", 
            pointer_width=64, endianness=Endianness.LITTLE, abi_mode="win64",
            compiler_family="msvc", compiler_version="19.29"
        )
        
        data = unit.to_dict()
        
        assert data['target_architecture'] == "x86_64"
        assert data['operating_system'] == "windows"
        assert data['pointer_width'] == 64
        assert data['endianness'] == "little"

# ============================================================================
# TEST: FUNCTION SYMBOL
# ============================================================================

class TestFunctionSymbol:
    """Test FunctionSymbol."""
    
    def test_function_symbol_creation(self):
        """Test creating function symbol."""
        func = FunctionSymbol(
            linkage_name="_Z7processPKci",
            calling_convention=CallingConvention.CDECL,
            source_name="process"
        )
        
        assert func.linkage_name == "_Z7processPKci"
        assert func.source_name == "process"
        assert func.calling_convention == CallingConvention.CDECL
        assert func.kind == EntityKind.FUNCTION_SYMBOL
        assert func.is_variadic is False
    
    def test_function_with_parameters(self):
        """Test function with parameters."""
        func = FunctionSymbol(linkage_name="func", calling_convention=CallingConvention.CDECL)
        
        param = ParameterEntity(parameter_index=0, parameter_name="x", type_reference="int_type_ref")
        func.parameters.append(param)
        
        assert len(func.parameters) == 1
        assert func.parameters[0].parameter_name == "x"
    
    def test_function_serialization(self):
        """Test function serialization."""
        func = FunctionSymbol(linkage_name="my_func", calling_convention=CallingConvention.STDCALL)
        
        data = func.to_dict()
        
        assert data['linkage_name'] == "my_func"
        assert data['calling_convention'] == "stdcall"
        assert data['is_variadic'] is False

# ============================================================================
# TEST: VARIABLE SYMBOL
# ============================================================================

class TestVariableSymbol:
    """Test VariableSymbol."""
    
    def test_variable_symbol_creation(self):
        """Test creating variable symbol."""
        var = VariableSymbol(
            linkage_name="global_counter",
            type_reference="int32_type",
            source_name="counter"
        )
        
        assert var.linkage_name == "global_counter"
        assert var.source_name == "counter"
        assert var.type_reference == "int32_type"
        assert var.kind == EntityKind.VARIABLE_SYMBOL
        assert var.is_const is False
    
    def test_const_variable(self):
        """Test const variable."""
        var = VariableSymbol(linkage_name="VERSION", type_reference="int_type")
        var.is_const = True
        
        assert var.is_const is True
    
    def test_variable_serialization(self):
        """Test variable serialization."""
        var = VariableSymbol(linkage_name="my_var", type_reference="uint64_type")
        
        data = var.to_dict()
        
        assert data['linkage_name'] == "my_var"
        assert data['type_reference'] == "uint64_type"
        assert data['visibility'] == "extern"

# ============================================================================
# TEST: SCALAR TYPE
# ============================================================================

class TestScalarType:
    """Test ScalarType."""
    
    def test_signed_integer_creation(self):
        """Test creating signed integer type."""
        int32 = ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True)
        
        assert int32.scalar_kind == ScalarKind.SIGNED_INTEGER
        assert int32.bit_width == 32
        assert int32.is_signed is True
        assert int32.size_bytes == 4
        assert int32.alignment_bytes == 4
    
    def test_unsigned_integer_creation(self):
        """Test creating unsigned integer type."""
        uint64 = ScalarType(scalar_kind=ScalarKind.UNSIGNED_INTEGER, bit_width=64, is_signed=False)
        
        assert uint64.scalar_kind == ScalarKind.UNSIGNED_INTEGER
        assert uint64.bit_width == 64
        assert uint64.is_signed is False
        assert uint64.size_bytes == 8
    
    def test_floating_point_creation(self):
        """Test creating floating-point type."""
        float32 = ScalarType(scalar_kind=ScalarKind.FLOATING_POINT, bit_width=32, is_signed=True)
        
        assert float32.scalar_kind == ScalarKind.FLOATING_POINT
        assert float32.bit_width == 32
        assert float32.size_bytes == 4
    
    def test_boolean_creation(self):
        """Test creating boolean type."""
        bool_type = ScalarType(scalar_kind=ScalarKind.BOOLEAN, bit_width=8, is_signed=False)
        
        assert bool_type.scalar_kind == ScalarKind.BOOLEAN
        assert bool_type.bit_width == 8
        assert bool_type.size_bytes == 1
    
    def test_scalar_serialization(self):
        """Test scalar type serialization."""
        int16 = ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=16, is_signed=True)
        
        data = int16.to_dict()
        
        assert data['scalar_kind'] == "signed_integer"
        assert data['bit_width'] == 16
        assert data['size_bytes'] == 2

# ============================================================================
# TEST: POINTER TYPE
# ============================================================================

class TestPointerType:
    """Test PointerType."""
    
    def test_pointer_creation_64bit(self):
        """Test creating 64-bit pointer."""
        ptr = PointerType(
            pointer_depth=1,
            target_type_reference="int32_type",
            pointer_width=64
        )
        
        assert ptr.pointer_depth == 1
        assert ptr.target_type_reference == "int32_type"
        assert ptr.size_bytes == 8
        assert ptr.alignment_bytes == 8
    
    def test_pointer_creation_32bit(self):
        """Test creating 32-bit pointer."""
        ptr = PointerType(
            pointer_depth=1,
            target_type_reference="char_type",
            pointer_width=32
        )
        
        assert ptr.size_bytes == 4
        assert ptr.alignment_bytes == 4
    
    def test_double_pointer(self):
        """Test double pointer."""
        ptr_ptr = PointerType(
            pointer_depth=2,
            target_type_reference="void_type",
            pointer_width=64
        )
        
        assert ptr_ptr.pointer_depth == 2
    
    def test_pointer_serialization(self):
        """Test pointer serialization."""
        ptr = PointerType(pointer_depth=1, target_type_reference="float_type", pointer_width=64)
        
        data = ptr.to_dict()
        
        assert data['pointer_depth'] == 1
        assert data['target_type_reference'] == "float_type"
        assert data['size_bytes'] == 8

# ============================================================================
# TEST: FIELD ENTITY
# ============================================================================

class TestFieldEntity:
    """Test FieldEntity."""
    
    def test_field_creation(self):
        """Test creating field."""
        field = FieldEntity(
            field_index=0,
            field_name="x",
            type_reference="int32_type",
            byte_offset=0
        )
        
        assert field.field_index == 0
        assert field.field_name == "x"
        assert field.type_reference == "int32_type"
        assert field.byte_offset == 0
        assert field.kind == EntityKind.FIELD
    
    def test_field_without_name(self):
        """Test field without name (anonymous)."""
        field = FieldEntity(field_index=1, field_name=None, type_reference="float_type", byte_offset=4)
        
        assert field.field_name is None
        assert field.field_index == 1
    
    def test_field_serialization(self):
        """Test field serialization."""
        field = FieldEntity(field_index=2, field_name="data", type_reference="array_type", byte_offset=8)
        field.size_bytes = 256
        
        data = field.to_dict()
        
        assert data['field_index'] == 2
        assert data['field_name'] == "data"
        assert data['byte_offset'] == 8
        assert data['size_bytes'] == 256

# ============================================================================
# TEST: PADDING ENTITY
# ============================================================================

class TestPaddingEntity:
    """Test PaddingEntity - explicit padding representation."""
    
    def test_padding_creation(self):
        """Test creating padding."""
        padding = PaddingEntity(
            byte_offset=1,
            size_bytes=3,
            reason="alignment"
        )
        
        assert padding.byte_offset == 1
        assert padding.size_bytes == 3
        assert padding.reason == "alignment"
        assert padding.kind == EntityKind.PADDING
    
    def test_padding_default_reason(self):
        """Test padding with default reason."""
        padding = PaddingEntity(byte_offset=4, size_bytes=4)
        
        assert padding.reason == "alignment"
    
    def test_padding_serialization(self):
        """Test padding serialization."""
        padding = PaddingEntity(byte_offset=8, size_bytes=8, reason="struct end padding")
        
        data = padding.to_dict()
        
        assert data['byte_offset'] == 8
        assert data['size_bytes'] == 8
        assert data['reason'] == "struct end padding"

# ============================================================================
# TEST: PARAMETER ENTITY
# ============================================================================

class TestParameterEntity:
    """Test ParameterEntity."""
    
    def test_parameter_creation(self):
        """Test creating parameter."""
        param = ParameterEntity(
            parameter_index=0,
            parameter_name="buffer",
            type_reference="ptr_uint8_type"
        )
        
        assert param.parameter_index == 0
        assert param.parameter_name == "buffer"
        assert param.type_reference == "ptr_uint8_type"
        assert param.kind == EntityKind.PARAMETER
    
    def test_parameter_qualifiers(self):
        """Test parameter with qualifiers."""
        param = ParameterEntity(parameter_index=1, parameter_name="length", type_reference="size_t_type")
        param.is_const = True
        
        assert param.is_const is True
        assert param.is_volatile is False
    
    def test_parameter_serialization(self):
        """Test parameter serialization."""
        param = ParameterEntity(parameter_index=2, parameter_name="flags", type_reference="uint32_type")
        
        data = param.to_dict()
        
        assert data['parameter_index'] == 2
        assert data['parameter_name'] == "flags"

# ============================================================================
# TEST: RETURN ENTITY
# ============================================================================

class TestReturnEntity:
    """Test ReturnEntity."""
    
    def test_return_direct(self):
        """Test direct return."""
        ret = ReturnEntity(type_reference="int32_type", return_mechanism=ReturnMechanism.DIRECT)
        
        assert ret.type_reference == "int32_type"
        assert ret.return_mechanism == ReturnMechanism.DIRECT
        assert ret.kind == EntityKind.RETURN
    
    def test_return_hidden_pointer(self):
        """Test hidden pointer return (for large structures)."""
        ret = ReturnEntity(type_reference="large_struct_type", return_mechanism=ReturnMechanism.HIDDEN_POINTER)
        
        assert ret.return_mechanism == ReturnMechanism.HIDDEN_POINTER
    
    def test_return_serialization(self):
        """Test return serialization."""
        ret = ReturnEntity(type_reference="void_type", return_mechanism=ReturnMechanism.DIRECT)
        
        data = ret.to_dict()
        
        assert data['type_reference'] == "void_type"
        assert data['return_mechanism'] == "direct"

# ============================================================================
# TEST: ATTRIBUTE ENTITY
# ============================================================================

class TestAttributeEntity:
    """Test AttributeEntity."""
    
    def test_attribute_creation(self):
        """Test creating attribute."""
        attr = AttributeEntity(attribute_name="aligned", attribute_value="16")
        
        assert attr.attribute_name == "aligned"
        assert attr.attribute_value == "16"
        assert attr.kind == EntityKind.ATTRIBUTE
    
    def test_attribute_without_value(self):
        """Test attribute without value."""
        attr = AttributeEntity(attribute_name="packed")
        
        assert attr.attribute_name == "packed"
        assert attr.attribute_value is None
    
    def test_attribute_serialization(self):
        """Test attribute serialization."""
        attr = AttributeEntity(attribute_name="visibility", attribute_value="hidden")
        
        data = attr.to_dict()
        
        assert data['attribute_name'] == "visibility"
        assert data['attribute_value'] == "hidden"

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple entities."""
    
    def test_complete_function_with_metadata(self):
        """Test function with all components."""
        # Create metadata
        metadata = MetadataEntity(source_file="api.h", line_number=100, column_number=5)
        
        # Create function
        func = FunctionSymbol(linkage_name="process_data", calling_convention=CallingConvention.CDECL)
        func.metadata = metadata
        
        # Add parameter
        param = ParameterEntity(parameter_index=0, parameter_name="buffer", type_reference="ptr_type")
        func.parameters.append(param)
        
        # Add return
        ret = ReturnEntity(type_reference="int_type", return_mechanism=ReturnMechanism.DIRECT)
        func.return_entity = ret
        
        # Verify structure
        assert func.metadata.source_file == "api.h"
        assert len(func.parameters) == 1
        assert func.return_entity.return_mechanism == ReturnMechanism.DIRECT
    
    def test_interface_unit_with_symbols(self):
        """Test interface unit containing symbols."""
        unit = InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", 
            pointer_width=64, endianness=Endianness.LITTLE, abi_mode="sysv",
            compiler_family="gcc", compiler_version="11.2.0"
        )
        
        # Add function symbol
        func = FunctionSymbol(linkage_name="my_func", calling_convention=CallingConvention.CDECL)
        unit.symbols.append(func)
        
        # Add variable symbol
        var = VariableSymbol(linkage_name="my_var", type_reference="int_type")
        unit.symbols.append(var)
        
        assert len(unit.symbols) == 2
        assert unit.symbols[0].kind == EntityKind.FUNCTION_SYMBOL
        assert unit.symbols[1].kind == EntityKind.VARIABLE_SYMBOL

# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
