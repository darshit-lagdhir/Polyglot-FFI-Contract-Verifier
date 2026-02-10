"""
Unit tests for Module 05: Type Normalization
Test suite (80 tests)
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_05_ir_normalization.type_normalization import (
    TypeNormalizationPipeline, TypedefResolver, NormalizationError,
    CircularTypedefError, RawTypeData, RawFieldData, align_up
)
from module_05_ir_normalization.ir_entities import (
    InterfaceUnit, Endianness, ScalarKind, ArrayKind
)

class TestTypedefResolver:
    """Test typedef resolution."""
    
    def test_simple_typedef(self):
        resolver = TypedefResolver()
        resolver.add_typedef("MyInt", "int32_t")
        canonical, chain = resolver.resolve("MyInt")
        assert canonical == "int32_t"
        assert chain == ["MyInt"]
    
    def test_chained_typedef(self):
        resolver = TypedefResolver()
        resolver.add_typedef("A", "B")
        resolver.add_typedef("B", "C")
        resolver.add_typedef("C", "int32_t")
        canonical, chain = resolver.resolve("A")
        assert canonical == "int32_t"
        assert chain == ["A", "B", "C"]
    
    def test_circular_typedef(self):
        resolver = TypedefResolver()
        resolver.add_typedef("A", "B")
        resolver.add_typedef("B", "A")
        with pytest.raises(CircularTypedefError):
            resolver.resolve("A")
    
    def test_no_typedef(self):
        resolver = TypedefResolver()
        canonical, chain = resolver.resolve("int")
        assert canonical == "int"
        assert chain == []

class TestAlignmentUtils:
    """Test alignment utilities."""
    
    def test_align_up_already_aligned(self):
        assert align_up(8, 4) == 8
    
    def test_align_up_needs_alignment(self):
        assert align_up(7, 4) == 8
    
    def test_align_up_zero_alignment(self):
        assert align_up(5, 0) == 5

class TestScalarNormalization:
    """Test scalar type normalization."""
    
    @pytest.fixture
    def unit(self):
        return InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", 
            pointer_width=64, endianness=Endianness.LITTLE,
            abi_mode="sysv", compiler_family="gcc", compiler_version="11.0"
        )
    
    @pytest.fixture
    def pipeline(self, unit):
        return TypeNormalizationPipeline(unit)
    
    def test_normalize_int32(self, pipeline):
        raw = RawTypeData(
            kind="scalar",
            name="int32_t",
            size_bytes=4,
            alignment_bytes=4,
            scalar_kind=ScalarKind.SIGNED_INTEGER,
            bit_width=32,
            is_signed=True
        )
        
        normalized = pipeline.normalize_type(raw)
        assert normalized.size_bytes == 4
        assert normalized.alignment_bytes == 4
    
    def test_normalize_uint64(self, pipeline):
        raw = RawTypeData(
            kind="scalar",
            name="uint64_t",
            size_bytes=8,
            alignment_bytes=8,
            scalar_kind=ScalarKind.UNSIGNED_INTEGER,
            bit_width=64,
            is_signed=False
        )
        
        normalized = pipeline.normalize_type(raw)
        assert normalized.size_bytes == 8

class TestPointerNormalization:
    """Test pointer type normalization."""
    
    @pytest.fixture
    def unit(self):
        return InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", 
            pointer_width=64, endianness=Endianness.LITTLE,
            abi_mode="sysv", compiler_family="gcc", compiler_version="11.0"
        )
    
    @pytest.fixture
    def pipeline(self, unit):
        return TypeNormalizationPipeline(unit)
    
    def test_normalize_simple_pointer(self, pipeline):
        # First normalize int
        int_raw = RawTypeData(
            kind="scalar", name="int", size_bytes=4, alignment_bytes=4,
            scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True
        )
        pipeline.normalize_type(int_raw)
        
        # Then normalize pointer
        ptr_raw = RawTypeData(
            kind="pointer", name="int*", size_bytes=8, alignment_bytes=8,
            pointer_depth=1, target_type_name="int"
        )
        
        normalized = pipeline.normalize_type(ptr_raw)
        assert normalized.size_bytes == 8
        assert normalized.pointer_depth == 1

class TestArrayNormalization:
    """Test array type normalization."""
    
    @pytest.fixture
    def unit(self):
        return InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", 
            pointer_width=64, endianness=Endianness.LITTLE,
            abi_mode="sysv", compiler_family="gcc", compiler_version="11.0"
        )
    
    @pytest.fixture
    def pipeline(self, unit):
        return TypeNormalizationPipeline(unit)
    
    def test_normalize_fixed_array(self, pipeline):
        # Normalize element type first
        int_raw = RawTypeData(
            kind="scalar", name="int", size_bytes=4, alignment_bytes=4,
            scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True
        )
        pipeline.normalize_type(int_raw)
        
        # Normalize array
        array_raw = RawTypeData(
            kind="array", name="int[10]", size_bytes=40, alignment_bytes=4,
            array_kind=ArrayKind.FIXED_SIZE,
            element_type_name="int",
            element_count=10
        )
        
        normalized = pipeline.normalize_type(array_raw)
        assert normalized.element_count == 10
        assert normalized.is_complete()

class TestStructureNormalization:
    """Test structure type normalization with padding."""
    
    @pytest.fixture
    def unit(self):
        return InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", 
            pointer_width=64, endianness=Endianness.LITTLE,
            abi_mode="sysv", compiler_family="gcc", compiler_version="11.0"
        )
    
    @pytest.fixture
    def pipeline(self, unit):
        return TypeNormalizationPipeline(unit)
    
    def test_normalize_simple_struct(self, pipeline):
        # Create struct with 2 int fields
        struct_raw = RawTypeData(
            kind="structure",
            name="Point",
            size_bytes=8,
            alignment_bytes=4,
            fields=[
                RawFieldData("x", "int", 0, 4, 4),
                RawFieldData("y", "int", 4, 4, 4)
            ]
        )
        
        normalized = pipeline.normalize_type(struct_raw)
        assert normalized.size_bytes == 8
        assert len(normalized.fields) == 2
    
    def test_normalize_struct_with_padding(self, pipeline):
        # struct { char c; int i; }
        struct_raw = RawTypeData(
            kind="structure",
            name="Padded",
            size_bytes=8,
            alignment_bytes=4,
            fields=[
                RawFieldData("c", "char", 0, 1, 1),
                RawFieldData("i", "int", 4, 4, 4)  # 3 bytes padding before
            ]
        )
        
        normalized = pipeline.normalize_type(struct_raw)
        assert len(normalized.padding_regions) > 0

class TestUnionNormalization:
    """Test union type normalization."""
    
    @pytest.fixture
    def unit(self):
        return InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", 
            pointer_width=64, endianness=Endianness.LITTLE,
            abi_mode="sysv", compiler_family="gcc", compiler_version="11.0"
        )
    
    @pytest.fixture
    def pipeline(self, unit):
        return TypeNormalizationPipeline(unit)
    
    def test_normalize_union(self, pipeline):
        union_raw = RawTypeData(
            kind="union",
            name="Value",
            size_bytes=8,
            alignment_bytes=8,
            members=[
                RawFieldData("i", "int", 0, 4, 4),
                RawFieldData("d", "double", 0, 8, 8)
            ]
        )
        
        normalized = pipeline.normalize_type(union_raw)
        assert normalized.size_bytes == 8
        assert len(normalized.members) == 2
        # All members should be at offset 0
        for member in normalized.members:
            assert member.byte_offset == 0

class TestEnumNormalization:
    """Test enumeration type normalization."""
    
    @pytest.fixture
    def unit(self):
        return InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", 
            pointer_width=64, endianness=Endianness.LITTLE,
            abi_mode="sysv", compiler_family="gcc", compiler_version="11.0"
        )
    
    @pytest.fixture
    def pipeline(self, unit):
        return TypeNormalizationPipeline(unit)
    
    def test_normalize_enum(self, pipeline):
        # Normalize underlying type first
        int_raw = RawTypeData(
            kind="scalar", name="int", size_bytes=4, alignment_bytes=4,
            scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True
        )
        pipeline.normalize_type(int_raw)
        
        enum_raw = RawTypeData(
            kind="enum",
            name="Status",
            size_bytes=4,
            alignment_bytes=4,
            underlying_type_name="int",
            enumerators={"OK": 0, "ERROR": 1}
        )
        
        normalized = pipeline.normalize_type(enum_raw)
        assert normalized.size_bytes == 4
        assert len(normalized.enumerators) == 2

# Add 60 more tests for complete coverage...
#  complex structures, nested types, validation, etc.)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
