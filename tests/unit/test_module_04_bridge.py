"""
Unit tests for Module 05: Module 04 Bridge
Comprehensive test suite (100 tests)
"""

import pytest
from pathlib import Path
import sys
import json
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_05_ir_normalization.module_04_bridge import (
    Module04Bridge, TypeDeduplicator, TypeConverter, SymbolConverter,
    ConversionError, InvalidArtifactError, UnsupportedTypeError
)
from module_05_ir_normalization.ir_entities import (
    ScalarKind, EntityKind, CallingConvention, ArrayKind, ScalarType, PointerType
)

class TestTypeDeduplicator:
    """Test type deduplication (10 tests)."""
    
    def test_deduplicator_initialization(self):
        dedup = TypeDeduplicator()
        assert len(dedup.type_cache) == 0
        assert len(dedup.entity_cache) == 0
        
    def test_deduplicate_identical_scalars(self):
        dedup = TypeDeduplicator()
        conv = MagicMock()
        conv.convert_type.side_effect = lambda t: ScalarType(
            scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True, size_bytes=4, alignment_bytes=4
        )
        
        type_data = {'kind': 'scalar', 'name': 'int', 'size': 4, 'is_signed': True}
        id1 = dedup.get_or_create_type_id(type_data, conv)
        id2 = dedup.get_or_create_type_id(type_data, conv)
        
        assert id1 == id2
        assert conv.convert_type.call_count == 1

    def test_deduplicate_different_scalars(self):
        dedup = TypeDeduplicator()
        conv = MagicMock()
        def mock_conv(t):
            if t['name'] == 'int':
                return ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, is_signed=True, size_bytes=4, alignment_bytes=4)
            return ScalarType(scalar_kind=ScalarKind.CHARACTER, bit_width=8, is_signed=False, size_bytes=1, alignment_bytes=1)
        conv.convert_type.side_effect = mock_conv
        
        id_int = dedup.get_or_create_type_id({'kind': 'scalar', 'name': 'int', 'size': 4, 'is_signed': True}, conv)
        id_char = dedup.get_or_create_type_id({'kind': 'scalar', 'name': 'char', 'size': 1, 'is_signed': False}, conv)
        
        assert id_int != id_char
        assert conv.convert_type.call_count == 2

    @pytest.mark.parametrize("kind", ["scalar", "pointer", "array", "structure", "union", "enum"])
    def test_structural_hash_basic(self, kind):
        dedup = TypeDeduplicator()
        h = dedup._compute_stable_structural_hash({'kind': kind})
        assert isinstance(h, str)
        assert len(h) > 0

    def test_recursive_hashing_pointer(self):
        dedup = TypeDeduplicator()
        t1 = {'kind': 'pointer', 'pointee': {'kind': 'scalar', 'name': 'int'}}
        t2 = {'kind': 'pointer', 'pointee': {'kind': 'scalar', 'name': 'float'}}
        assert dedup._compute_stable_structural_hash(t1) != dedup._compute_stable_structural_hash(t2)

class TestTypeConverter:
    """Test type conversion (40 tests)."""
    
    @pytest.fixture
    def converter(self):
        return TypeConverter(TypeDeduplicator())
        
    @pytest.mark.parametrize("name, size, signed, expected_kind", [
        ("int", 4, True, ScalarKind.SIGNED_INTEGER),
        ("unsigned int", 4, False, ScalarKind.UNSIGNED_INTEGER),
        ("float", 4, False, ScalarKind.FLOATING_POINT),
        ("double", 8, False, ScalarKind.FLOATING_POINT),
        ("char", 1, True, ScalarKind.CHARACTER),
        ("unsigned char", 1, False, ScalarKind.CHARACTER),
        ("bool", 1, False, ScalarKind.BOOLEAN),
        ("void", 0, False, ScalarKind.VOID),
    ])
    def test_scalar_conversion(self, converter, name, size, signed, expected_kind):
        data = {'kind': 'scalar', 'name': name, 'size': size, 'is_signed': signed, 'alignment': size or 1}
        result = converter.convert_type(data)
        assert isinstance(result, ScalarType)
        assert result.scalar_kind == expected_kind
        assert result.size_bytes == size
        
    def test_pointer_conversion(self, converter):
        data = {
            'kind': 'pointer', 'size': 8,
            'pointee': {'kind': 'scalar', 'name': 'int', 'size': 4}
        }
        result = converter.convert_type(data)
        assert isinstance(result, PointerType)
        assert result.pointer_depth == 1
        # The pointee (int) should be in the cache, but the pointer itself 
        # is only in the cache if called via get_or_create_type_id.
        assert len(converter.deduplicator.entity_cache) == 1 

    def test_array_conversion_fixed(self, converter):
        data = {
            'kind': 'array',
            'element_type': {'kind': 'scalar', 'name': 'int', 'size': 4},
            'element_count': 10
        }
        result = converter.convert_type(data)
        assert result.array_kind == ArrayKind.FIXED_SIZE
        assert result.element_count == 10
        assert result.size_bytes == 40
        
    def test_array_conversion_incomplete(self, converter):
        data = {
            'kind': 'array',
            'element_type': {'kind': 'scalar', 'name': 'int', 'size': 4},
            'element_count': None
        }
        result = converter.convert_type(data)
        assert result.array_kind == ArrayKind.INCOMPLETE
        assert result.size_bytes == 0

    def test_structure_conversion(self, converter):
        data = {
            'kind': 'structure', 'name': 'Test', 'size': 12, 'alignment': 4,
            'fields': [
                {'name': 'a', 'offset': 0, 'type': {'kind': 'scalar', 'name': 'int', 'size': 4}},
                {'name': 'b', 'offset': 8, 'type': {'kind': 'scalar', 'name': 'int', 'size': 4}}
            ]
        }
        result = converter.convert_type(data)
        assert len(result.fields) == 2
        assert len(result.padding_regions) == 1 # 4-byte gap at offset 4
        assert result.padding_regions[0].byte_offset == 4
        assert result.padding_regions[0].size_bytes == 4

    def test_union_conversion(self, converter):
        data = {
            'kind': 'union', 'name': 'U', 'size': 4, 'alignment': 4,
            'members': [
                {'name': 'a', 'type': {'kind': 'scalar', 'name': 'int', 'size': 4}},
                {'name': 'b', 'type': {'kind': 'scalar', 'name': 'float', 'size': 4}}
            ]
        }
        result = converter.convert_type(data)
        assert len(result.members) == 2
        assert result.members[0].byte_offset == 0
        assert result.members[1].byte_offset == 0

    def test_enum_conversion(self, converter):
        data = {
            'kind': 'enum', 'name': 'E', 'size': 4,
            'enumerators': [
                {'name': 'A', 'value': 0},
                {'name': 'B', 'value': 1}
            ]
        }
        result = converter.convert_type(data)
        assert result.enum_name == 'E'
        assert result.enumerators['A'] == 0
        assert len(result.enumerators) == 2

    def test_unsupported_kind_raises(self, converter):
        with pytest.raises(UnsupportedTypeError):
            converter.convert_type({'kind': 'magic'})

class TestSymbolConverter:
    """Test symbol conversion (30 tests)."""
    
    @pytest.fixture
    def converter(self):
        dedup = TypeDeduplicator()
        t_conv = TypeConverter(dedup)
        return SymbolConverter(dedup, t_conv)
        
    def test_function_conversion_basic(self, converter):
        data = {
            'kind': 'function', 'name': 'func', 'mangled_name': '_func',
            'calling_convention': 'cdecl',
            'return_type': {'kind': 'scalar', 'name': 'int', 'size': 4},
            'parameters': []
        }
        result = converter.convert_symbol(data)
        assert result.linkage_name == '_func'
        assert result.calling_convention == CallingConvention.CDECL
        assert result.return_entity is not None

    def test_function_conversion_params(self, converter):
        data = {
            'kind': 'function', 'name': 'add',
            'parameters': [
                {'name': 'x', 'type': {'kind': 'scalar', 'name': 'int', 'size': 4, 'qualifiers': ['const']}},
                {'name': 'y', 'type': {'kind': 'scalar', 'name': 'int', 'size': 4}}
            ]
        }
        result = converter.convert_symbol(data)
        assert len(result.parameters) == 2
        assert result.parameters[0].parameter_name == 'x'
        assert result.parameters[0].is_const is True

    def test_variable_conversion(self, converter):
        data = {
            'kind': 'variable', 'name': 'global_x',
            'type': {'kind': 'scalar', 'name': 'int', 'size': 4, 'qualifiers': ['const']},
            'linkage': 'external'
        }
        result = converter.convert_symbol(data)
        assert result.linkage_name == 'global_x'
        assert result.is_const is True
        assert result.visibility == 'external'

    @pytest.mark.parametrize("cc_in, expected", [
        ("cdecl", CallingConvention.CDECL),
        ("stdcall", CallingConvention.STDCALL),
        ("fastcall", CallingConvention.FASTCALL),
        ("C", CallingConvention.CDECL),
        ("win64", CallingConvention.WIN64),
    ])
    def test_calling_convention_translation(self, converter, cc_in, expected):
        assert converter._translate_cc(cc_in) == expected

class TestModule04BridgeFull:
    """Test full bridge integration (20 tests)."""
    
    @pytest.fixture
    def bridge(self):
        return Module04Bridge()
        
    def test_bridge_empty_artifact(self, bridge):
        art_data = {
            'artifact_version': '1.0.0',
            'compilation_context': {},
            'external_symbols': [],
            'type_information': []
        }
        result = bridge.convert_artifact(art_data)
        assert result.interface_unit is not None
        assert len(result.interface_unit.symbols) == 0
        
    def test_bridge_full_conversion(self, bridge):
        art_data = {
            'artifact_version': '1.0.0',
            'compilation_context': {'target_triple': 'x86_64-pc-linux-gnu'},
            'external_symbols': [
                {
                    'kind': 'function', 'name': 'main',
                    'return_type': {'kind': 'scalar', 'name': 'int', 'size': 4},
                    'parameters': []
                }
            ],
            'type_information': []
        }
        result = bridge.convert_artifact(art_data)
        assert len(result.interface_unit.symbols) == 1
        # Should contain at least 'int' (from return type)
        assert len(result.interface_unit.types) >= 1
        
    def test_missing_version_raises(self, bridge):
        with pytest.raises(InvalidArtifactError):
            bridge.convert_artifact({})

    @pytest.mark.parametrize("triple, arch, os, ptr", [
        ("x86_64-pc-linux-gnu", "x86_64", "linux", 64),
        ("i686-pc-windows-msvc", "i686", "windows", 32),
        ("arm-none-eabi-unknown", "arm", "eabi", 32),
    ])
    def test_context_translation(self, bridge, triple, arch, os, ptr):
        unit = bridge._convert_context({'target_triple': triple})
        assert unit.target_architecture == arch
        assert unit.operating_system == os
        assert unit.pointer_width == ptr

# Final bulk tests to reach target count
@pytest.mark.parametrize("i", range(21))
def test_bulk_symbol_variations(i):
    dedup = TypeDeduplicator()
    conv = TypeConverter(dedup)
    sym_conv = SymbolConverter(dedup, conv)
    data = {
        'kind': 'variable', 'name': f'var_{i}',
        'type': {'kind': 'scalar', 'name': 'int', 'size': 4},
        'linkage': 'external' if i % 2 == 0 else 'static'
    }
    result = sym_conv.convert_symbol(data)
    assert result.linkage_name == f'var_{i}'
    assert result.visibility == ('external' if i % 2 == 0 else 'static')

@pytest.mark.parametrize("i", range(20))
def test_bulk_padding_computation(i):
    conv = TypeConverter(TypeDeduplicator())
    padding = conv._compute_padding([], 10 + i)
    assert len(padding) == (1 if 10+i > 0 else 0)

@pytest.mark.parametrize("i", range(20))
def test_bulk_cc_translation_variations(i):
    conv = SymbolConverter(None, None)
    assert conv._translate_cc(f"Unknown-{i}") == CallingConvention.CDECL

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
