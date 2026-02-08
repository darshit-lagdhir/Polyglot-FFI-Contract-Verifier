"""
Unit tests for Module 05: Complete Type System
Basic test suite (50 tests)
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_05_ir_normalization.ir_entities import (
    ArrayKind, ArrayType, StructureType, UnionType, EnumerationType,
    FunctionPointerType, TypeRegistry, FieldEntity, PaddingEntity,
    ParameterEntity, CallingConvention, ScalarKind, ScalarType,
    EntityKind, PointerType
)

class TestArrayType:
    """Test ArrayType with three semantics."""
    
    def test_fixed_size_array(self):
        array = ArrayType(
            array_kind=ArrayKind.FIXED_SIZE, 
            element_type_reference="int_type", 
            element_count=256, 
            element_size=4, 
            element_alignment=4
        )
        assert array.element_count == 256
        assert array.size_bytes == 1024
        assert array.is_complete()
    
    def test_incomplete_array(self):
        array = ArrayType(
            array_kind=ArrayKind.INCOMPLETE, 
            element_type_reference="int_type", 
            element_count=None, 
            element_size=4, 
            element_alignment=4
        )
        assert array.element_count is None
        assert array.size_bytes == 0
        assert not array.is_complete()
    
    def test_flexible_array_member(self):
        array = ArrayType(
            array_kind=ArrayKind.FLEXIBLE_MEMBER, 
            element_type_reference="uint8_type", 
            element_count=None, 
            element_size=1, 
            element_alignment=1
        )
        assert array.size_bytes == 0
        assert not array.is_complete()
    
    def test_multidimensional_array(self):
        inner = ArrayType(
            array_kind=ArrayKind.FIXED_SIZE, 
            element_type_reference="int_type", 
            element_count=4, 
            element_size=4, 
            element_alignment=4
        )
        outer = ArrayType(
            array_kind=ArrayKind.FIXED_SIZE, 
            element_type_reference=inner.entity_id, 
            element_count=4, 
            element_size=16, 
            element_alignment=4
        )
        assert outer.size_bytes == 64
    
    def test_array_serialization(self):
        array = ArrayType(
            array_kind=ArrayKind.FIXED_SIZE, 
            element_type_reference="double_type", 
            element_count=10, 
            element_size=8, 
            element_alignment=8
        )
        data = array.to_dict()
        assert data['array_kind'] == "fixed_size"
        assert data['element_count'] == 10

class TestStructureType:
    """Test StructureType with explicit padding."""
    
    def test_structure_creation(self):
        struct = StructureType(structure_name="Point", size_bytes=8, alignment_bytes=4)
        assert struct.structure_name == "Point"
        assert struct.size_bytes == 8
    
    def test_structure_with_fields(self):
        struct = StructureType(structure_name="Data", size_bytes=16, alignment_bytes=8)
        field1 = FieldEntity(field_index=0, field_name="x", type_reference="int_type", byte_offset=0)
        field1.size_bytes = 4
        struct.add_field(field1)
        assert len(struct.fields) == 1
    
    def test_structure_with_padding(self):
        struct = StructureType(structure_name="Padded", size_bytes=12, alignment_bytes=4)
        field1 = FieldEntity(field_index=0, field_name="a", type_reference="char_type", byte_offset=0)
        field1.size_bytes = 1
        struct.add_field(field1)
        padding = PaddingEntity(byte_offset=1, size_bytes=3)
        struct.add_padding(padding)
        field2 = FieldEntity(field_index=1, field_name="b", type_reference="int_type", byte_offset=4)
        field2.size_bytes = 4
        struct.add_field(field2)
        assert len(struct.padding_regions) == 1
    
    def test_structure_layout_validation(self):
        struct = StructureType(structure_name="Valid", size_bytes=8, alignment_bytes=4)
        field1 = FieldEntity(field_index=0, field_name="a", type_reference="int_type", byte_offset=0)
        field1.size_bytes = 4
        struct.add_field(field1)
        field2 = FieldEntity(field_index=1, field_name="b", type_reference="int_type", byte_offset=4)
        field2.size_bytes = 4
        struct.add_field(field2)
        errors = struct.validate_layout()
        assert len(errors) == 0
    
    def test_structure_overlapping_fields(self):
        struct = StructureType(structure_name="Invalid", size_bytes=8, alignment_bytes=4)
        field1 = FieldEntity(field_index=0, field_name="a", type_reference="int_type", byte_offset=0)
        field1.size_bytes = 4
        struct.add_field(field1)
        field2 = FieldEntity(field_index=1, field_name="b", type_reference="int_type", byte_offset=2)
        field2.size_bytes = 4
        struct.add_field(field2)
        errors = struct.validate_layout()
        assert len(errors) > 0
    
    def test_packed_structure(self):
        struct = StructureType(structure_name="Packed", size_bytes=5, alignment_bytes=1)
        struct.is_packed = True
        assert struct.is_packed
    
    def test_structure_serialization(self):
        struct = StructureType(structure_name="MyStruct", size_bytes=16, alignment_bytes=8)
        data = struct.to_dict()
        assert data['structure_name'] == "MyStruct"

class TestUnionType:
    """Test UnionType with overlapping members."""
    
    def test_union_creation(self):
        union = UnionType(union_name="Value", size_bytes=8, alignment_bytes=8)
        assert union.union_name == "Value"
        assert union.size_bytes == 8
    
    def test_union_with_members(self):
        union = UnionType(union_name="Data", size_bytes=8, alignment_bytes=8)
        member1 = FieldEntity(field_index=0, field_name="i", type_reference="int32_type", byte_offset=0)
        member1.size_bytes = 4
        union.add_member(member1)
        member2 = FieldEntity(field_index=1, field_name="d", type_reference="double_type", byte_offset=0)
        member2.size_bytes = 8
        union.add_member(member2)
        assert len(union.members) == 2
    
    def test_union_invalid_offset(self):
        union = UnionType(union_name="Invalid", size_bytes=4, alignment_bytes=4)
        member = FieldEntity(field_index=0, field_name="bad", type_reference="int_type", byte_offset=4)
        with pytest.raises(ValueError):
            union.add_member(member)
    
    def test_union_validation(self):
        union = UnionType(union_name="Valid", size_bytes=16, alignment_bytes=8)
        member = FieldEntity(field_index=0, field_name="a", type_reference="int_type", byte_offset=0)
        member.size_bytes = 4
        member.alignment_bytes = 4
        union.add_member(member)
        errors = union.validate_union_invariants()
        assert len(errors) == 0
    
    def test_union_serialization(self):
        union = UnionType(union_name="MyUnion", size_bytes=8, alignment_bytes=8)
        data = union.to_dict()
        assert data['union_name'] == "MyUnion"

class TestEnumerationType:
    """Test EnumerationType with symbolic values."""
    
    def test_enum_creation(self):
        enum = EnumerationType(enum_name="Status", underlying_type_reference="int32_type", size_bytes=4, alignment_bytes=4)
        assert enum.enum_name == "Status"
        assert enum.size_bytes == 4
    
    def test_enum_with_enumerators(self):
        enum = EnumerationType(enum_name="Color", underlying_type_reference="int_type", size_bytes=4, alignment_bytes=4)
        enum.add_enumerator("RED", 0)
        enum.add_enumerator("GREEN", 1)
        enum.add_enumerator("BLUE", 2)
        assert len(enum.enumerators) == 3
    
    def test_enum_negative_values(self):
        enum = EnumerationType(enum_name="ErrorCode", underlying_type_reference="int32_type", size_bytes=4, alignment_bytes=4)
        enum.add_enumerator("SUCCESS", 0)
        enum.add_enumerator("ERROR", -1)
        assert enum.enumerators["ERROR"] == -1
    
    def test_enum_value_range(self):
        enum = EnumerationType(enum_name="Range", underlying_type_reference="int_type", size_bytes=4, alignment_bytes=4)
        enum.add_enumerator("MIN", -100)
        enum.add_enumerator("MAX", 100)
        min_val, max_val = enum.get_value_range()
        assert min_val == -100
        assert max_val == 100
    
    def test_enum_serialization(self):
        enum = EnumerationType(enum_name="MyEnum", underlying_type_reference="uint32_type", size_bytes=4, alignment_bytes=4)
        enum.add_enumerator("A", 10)
        data = enum.to_dict()
        assert data['enum_name'] == "MyEnum"

class TestFunctionPointerType:
    """Test FunctionPointerType with full signature."""
    
    def test_function_pointer_creation(self):
        func_ptr = FunctionPointerType(
            calling_convention=CallingConvention.CDECL, 
            return_type_reference="int_type", 
            pointer_width=64
        )
        assert func_ptr.calling_convention == CallingConvention.CDECL
        assert func_ptr.size_bytes == 8
    
    def test_function_pointer_with_parameters(self):
        func_ptr = FunctionPointerType(
            calling_convention=CallingConvention.STDCALL, 
            return_type_reference="void_type", 
            pointer_width=32
        )
        param = ParameterEntity(parameter_index=0, parameter_name="x", type_reference="int_type")
        func_ptr.add_parameter(param)
        assert len(func_ptr.parameters) == 1
    
    def test_function_pointer_variadic(self):
        func_ptr = FunctionPointerType(
            calling_convention=CallingConvention.CDECL, 
            return_type_reference="int_type", 
            pointer_width=64
        )
        func_ptr.is_variadic = True
        assert func_ptr.is_variadic
    
    def test_function_pointer_signature_match(self):
        func_ptr1 = FunctionPointerType(
            calling_convention=CallingConvention.CDECL, 
            return_type_reference="void_type", 
            pointer_width=64
        )
        param1 = ParameterEntity(parameter_index=0, parameter_name="arg", type_reference="int_type")
        func_ptr1.add_parameter(param1)
        
        func_ptr2 = FunctionPointerType(
            calling_convention=CallingConvention.CDECL, 
            return_type_reference="void_type", 
            pointer_width=64
        )
        param2 = ParameterEntity(parameter_index=0, parameter_name="arg", type_reference="int_type")
        func_ptr2.add_parameter(param2)
        
        assert func_ptr1.signature_matches(func_ptr2)
    
    def test_function_pointer_signature_mismatch(self):
        func_ptr1 = FunctionPointerType(
            calling_convention=CallingConvention.CDECL, 
            return_type_reference="int_type", 
            pointer_width=64
        )
        func_ptr2 = FunctionPointerType(
            calling_convention=CallingConvention.STDCALL, 
            return_type_reference="int_type", 
            pointer_width=64
        )
        assert not func_ptr1.signature_matches(func_ptr2)
    
    def test_function_pointer_serialization(self):
        func_ptr = FunctionPointerType(
            calling_convention=CallingConvention.FASTCALL, 
            return_type_reference="double_type", 
            pointer_width=64
        )
        data = func_ptr.to_dict()
        assert data['calling_convention'] == "fastcall"

class TestTypeRegistry:
    """Test TypeRegistry for type resolution."""
    
    def test_registry_creation(self):
        registry = TypeRegistry()
        assert len(registry.get_all_types()) == 0
    
    def test_register_and_resolve_type(self):
        registry = TypeRegistry()
        int_type = ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True)
        registry.register_type(int_type)
        resolved = registry.resolve_type(int_type.entity_id)
        assert resolved is not None
    
    def test_register_duplicate_type(self):
        registry = TypeRegistry()
        type1 = ScalarType(scalar_kind=ScalarKind.UNSIGNED_INTEGER, bit_width=64, is_signed=False)
        registry.register_type(type1)
        type2 = ScalarType(scalar_kind=ScalarKind.UNSIGNED_INTEGER, bit_width=64, is_signed=False)
        # Manually force ID match if they would naturally differ (though here they would likely match)
        with pytest.raises(ValueError):
            registry.register_type(type2)
    
    def test_validate_valid_references(self):
        registry = TypeRegistry()
        int_type = ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True)
        registry.register_type(int_type)
        ptr_type = PointerType(pointer_depth=1, target_type_reference=int_type.entity_id, pointer_width=64)
        registry.register_type(ptr_type)
        errors = registry.validate_references()
        assert len(errors) == 0
    
    def test_validate_invalid_references(self):
        registry = TypeRegistry()
        ptr_type = PointerType(pointer_depth=1, target_type_reference="nonexistent_type", pointer_width=64)
        registry.register_type(ptr_type)
        errors = registry.validate_references()
        assert len(errors) > 0
    
    def test_get_all_types(self):
        registry = TypeRegistry()
        type1 = ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=8, is_signed=True)
        type2 = ScalarType(scalar_kind=ScalarKind.UNSIGNED_INTEGER, bit_width=16, is_signed=False)
        registry.register_type(type1)
        registry.register_type(type2)
        all_types = registry.get_all_types()
        assert len(all_types) == 2

class TestComplexScenarios:
    """Integration tests with complex types."""
    
    def test_struct_with_array_field(self):
        registry = TypeRegistry()
        int_type = ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True)
        registry.register_type(int_type)
        array = ArrayType(
            array_kind=ArrayKind.FIXED_SIZE, 
            element_type_reference=int_type.entity_id, 
            element_count=10, 
            element_size=4, 
            element_alignment=4
        )
        registry.register_type(array)
        struct = StructureType(structure_name="Container", size_bytes=40, alignment_bytes=4)
        field = FieldEntity(field_index=0, field_name="data", type_reference=array.entity_id, byte_offset=0)
        field.size_bytes = 40
        struct.add_field(field)
        registry.register_type(struct)
        errors = registry.validate_references()
        assert len(errors) == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
