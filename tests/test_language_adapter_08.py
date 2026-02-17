
"""Test Suite for Language Adapter - Prompt 08/25: 85 tests."""

import pytest
import ctypes
from typing import Dict, Any, List

from modules.module_08_language_adapter import (
    PythonTypeMapper,
    PythonNormalizer,
    PythonSignatureMirror,
    CtypesIntegration,
    CffiIntegration,
    PythonAdapter,
)


# ════════════════════════════════════════════════════════════════════════════
# PYTHON TYPE MAPPER TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonTypeMapper:
    """PythonTypeMapper tests (15 tests)."""
    
    def test_create_mapper(self):
        """Test 651: Create type mapper."""
        mapper = PythonTypeMapper()
        assert mapper is not None
        assert len(mapper.python_to_c) > 0
        assert len(mapper.c_to_python) > 0
    
    def test_python_to_c_int(self):
        """Test 652: Map Python int to C."""
        mapper = PythonTypeMapper()
        c_type = mapper.get_c_type(int)
        assert c_type == 'int'
    
    def test_python_to_c_float(self):
        """Test 653: Map Python float to C."""
        mapper = PythonTypeMapper()
        c_type = mapper.get_c_type(float)
        assert c_type == 'double'
    
    def test_python_to_c_str(self):
        """Test 654: Map Python str to C."""
        mapper = PythonTypeMapper()
        c_type = mapper.get_c_type(str)
        assert c_type == 'char*'
    
    def test_python_to_c_bytes(self):
        """Test 655: Map Python bytes to C."""
        mapper = PythonTypeMapper()
        c_type = mapper.get_c_type(bytes)
        assert c_type == 'char*'
    
    def test_python_to_c_bool(self):
        """Test 656: Map Python bool to C."""
        mapper = PythonTypeMapper()
        c_type = mapper.get_c_type(bool)
        assert c_type == 'bool'
    
    def test_python_to_c_none(self):
        """Test 657: Map NoneType to C void*."""
        mapper = PythonTypeMapper()
        c_type = mapper.get_c_type(type(None))
        assert c_type == 'void*'
    
    def test_c_to_python_int(self):
        """Test 658: Map C int to Python."""
        mapper = PythonTypeMapper()
        py_type = mapper.get_python_type('int')
        assert py_type == int
    
    def test_c_to_python_double(self):
        """Test 659: Map C double to Python."""
        mapper = PythonTypeMapper()
        py_type = mapper.get_python_type('double')
        assert py_type == float
    
    def test_c_to_python_char_ptr(self):
        """Test 660: Map C char* to Python."""
        mapper = PythonTypeMapper()
        py_type = mapper.get_python_type('char*')
        assert py_type == bytes
    
    def test_c_to_python_const_char_ptr(self):
        """Test 661: Map C const char* to Python."""
        mapper = PythonTypeMapper()
        py_type = mapper.get_python_type('const char*')
        assert py_type == bytes
    
    def test_c_to_python_fixed_width(self):
        """Test 662: Map C fixed-width ints to Python."""
        mapper = PythonTypeMapper()
        for c_type in ['int32_t', 'uint32_t', 'int64_t', 'uint64_t']:
            assert mapper.get_python_type(c_type) == int
    
    def test_is_pointer_type_true(self):
        """Test 663: Detect pointer type."""
        mapper = PythonTypeMapper()
        assert mapper.is_pointer_type('char*') is True
        assert mapper.is_pointer_type('void*') is True
        assert mapper.is_pointer_type('int*') is True
    
    def test_is_pointer_type_false(self):
        """Test 664: Detect non-pointer type."""
        mapper = PythonTypeMapper()
        assert mapper.is_pointer_type('int') is False
        assert mapper.is_pointer_type('double') is False
        assert mapper.is_pointer_type('bool') is False
    
    def test_unknown_python_type(self):
        """Test 665: Unknown types return None."""
        mapper = PythonTypeMapper()
        assert mapper.get_c_type(dict) is None
        assert mapper.get_c_type(list) is None
        assert mapper.get_python_type('unknown_type') is None


# ════════════════════════════════════════════════════════════════════════════
# PYTHON NORMALIZER TESTS (25 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonNormalizer:
    """PythonNormalizer tests (25 tests)."""
    
    def test_create_normalizer(self):
        """Test 666: Create normalizer."""
        norm = PythonNormalizer()
        assert norm is not None
        assert norm.type_mapper is not None
    
    def test_normalize_none(self):
        """Test 667: Normalize None."""
        norm = PythonNormalizer()
        assert norm.normalize_value(None) is None
    
    def test_normalize_int(self):
        """Test 668: Normalize int."""
        norm = PythonNormalizer()
        assert norm.normalize_value(42) == 42
    
    def test_normalize_negative_int(self):
        """Test 669: Normalize negative int."""
        norm = PythonNormalizer()
        assert norm.normalize_value(-100) == -100
    
    def test_normalize_large_int(self):
        """Test 670: Normalize large int (Python arbitrary precision)."""
        norm = PythonNormalizer()
        large = 2**64
        assert norm.normalize_value(large) == large
    
    def test_normalize_float(self):
        """Test 671: Normalize float."""
        norm = PythonNormalizer()
        assert norm.normalize_value(3.14) == 3.14
    
    def test_normalize_bool_true(self):
        """Test 672: Normalize True to 1."""
        norm = PythonNormalizer()
        assert norm.normalize_value(True) == 1
    
    def test_normalize_bool_false(self):
        """Test 673: Normalize False to 0."""
        norm = PythonNormalizer()
        assert norm.normalize_value(False) == 0
    
    def test_normalize_bool_is_int(self):
        """Test 674: Normalized bool is integer type."""
        norm = PythonNormalizer()
        result = norm.normalize_value(True)
        assert isinstance(result, int)
        assert not isinstance(result, bool)
    
    def test_normalize_string(self):
        """Test 675: Normalize string."""
        norm = PythonNormalizer()
        assert norm.normalize_value('hello') == 'hello'
    
    def test_normalize_empty_string(self):
        """Test 676: Normalize empty string."""
        norm = PythonNormalizer()
        assert norm.normalize_value('') == ''
    
    def test_normalize_bytes(self):
        """Test 677: Normalize bytes."""
        norm = PythonNormalizer()
        data = b'test'
        assert norm.normalize_value(data) == data
    
    def test_normalize_bytearray(self):
        """Test 678: Normalize bytearray to bytes."""
        norm = PythonNormalizer()
        ba = bytearray(b'test')
        result = norm.normalize_value(ba)
        assert isinstance(result, bytes)
        assert result == b'test'
    
    def test_normalize_memoryview(self):
        """Test 679: Normalize memoryview to bytes."""
        norm = PythonNormalizer()
        mv = memoryview(b'test')
        result = norm.normalize_value(mv)
        assert isinstance(result, bytes)
        assert result == b'test'
    
    def test_normalize_buffer_bytes(self):
        """Test 680: Normalize buffer from bytes."""
        norm = PythonNormalizer()
        data = b'test'
        normalized, length = norm.normalize_buffer(data)
        assert normalized == data
        assert length == 4
    
    def test_normalize_buffer_none(self):
        """Test 681: Normalize None buffer."""
        norm = PythonNormalizer()
        normalized, length = norm.normalize_buffer(None)
        assert normalized is None
        assert length == 0
    
    def test_normalize_buffer_string(self):
        """Test 682: Normalize string buffer."""
        norm = PythonNormalizer()
        normalized, length = norm.normalize_buffer('hello')
        assert isinstance(normalized, bytes)
        assert normalized == b'hello'
        assert length == 5
    
    def test_normalize_buffer_bytearray(self):
        """Test 683: Normalize bytearray buffer."""
        norm = PythonNormalizer()
        ba = bytearray(b'test')
        normalized, length = norm.normalize_buffer(ba)
        assert normalized == b'test'
        assert length == 4
    
    def test_normalize_buffer_memoryview(self):
        """Test 684: Normalize memoryview buffer."""
        norm = PythonNormalizer()
        mv = memoryview(b'data')
        normalized, length = norm.normalize_buffer(mv)
        assert normalized == b'data'
        assert length == 4
    
    def test_normalize_buffer_unicode(self):
        """Test 685: Normalize unicode string buffer with encoding."""
        norm = PythonNormalizer()
        normalized, length = norm.normalize_buffer('héllo')
        assert isinstance(normalized, bytes)
        assert length > 5  # UTF-8 encoding of é is 2 bytes
    
    def test_normalize_buffer_unsupported(self):
        """Test 686: Normalize unsupported buffer type."""
        norm = PythonNormalizer()
        normalized, length = norm.normalize_buffer(42)
        assert normalized is None
        assert length == 0
    
    def test_normalize_inputs_list(self):
        """Test 687: Normalize list of inputs."""
        norm = PythonNormalizer()
        inputs = [42, 3.14, 'hello', None]
        result = norm.normalize_inputs(inputs)
        assert len(result) == 4
        assert result[0] == 42
        assert result[1] == 3.14
        assert result[2] == 'hello'
        assert result[3] is None
    
    def test_normalize_inputs_with_bools(self):
        """Test 688: Normalize inputs with bools converts to ints."""
        norm = PythonNormalizer()
        inputs = [True, False, 42]
        result = norm.normalize_inputs(inputs)
        assert result == [1, 0, 42]
    
    def test_normalize_unknown_type(self):
        """Test 689: Unknown types pass through."""
        norm = PythonNormalizer()
        obj = {'key': 'value'}
        assert norm.normalize_value(obj) == obj
    
    def test_can_normalize(self):
        """Test 690: can_normalize returns True for standard types."""
        norm = PythonNormalizer()
        assert norm.can_normalize(42) is True
        assert norm.can_normalize('hello') is True
        assert norm.can_normalize(None) is True
        assert norm.can_normalize(3.14) is True


# ════════════════════════════════════════════════════════════════════════════
# PYTHON SIGNATURE MIRROR TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonSignatureMirror:
    """PythonSignatureMirror tests (15 tests)."""
    
    def test_create_mirror(self):
        """Test 691: Create signature mirror."""
        mirror = PythonSignatureMirror()
        assert mirror is not None
        assert mirror.type_mapper is not None
    
    def test_build_simple_signature(self):
        """Test 692: Build simple signature."""
        mirror = PythonSignatureMirror()
        contract = {
            'name': 'add',
            'parameters': [
                {'name': 'a', 'type': 'int'},
                {'name': 'b', 'type': 'int'}
            ],
            'return': {'type': 'int'}
        }
        
        sig = mirror.build_signature(contract)
        assert sig['name'] == 'add'
        assert len(sig['parameters']) == 2
        assert sig['return_type'] == 'int'
    
    def test_signature_param_types(self):
        """Test 693: Parameter type mapping in signature."""
        mirror = PythonSignatureMirror()
        contract = {
            'name': 'func',
            'parameters': [
                {'name': 'a', 'type': 'int'},
                {'name': 'b', 'type': 'double'}
            ],
            'return': {'type': 'void'}
        }
        
        sig = mirror.build_signature(contract)
        assert sig['parameters'][0]['c_type'] == 'int'
        assert sig['parameters'][0]['python_type'] == int
        assert sig['parameters'][1]['c_type'] == 'double'
        assert sig['parameters'][1]['python_type'] == float
    
    def test_signature_with_no_params(self):
        """Test 694: Signature with no parameters."""
        mirror = PythonSignatureMirror()
        contract = {
            'name': 'get_value',
            'parameters': [],
            'return': {'type': 'int'}
        }
        
        sig = mirror.build_signature(contract)
        assert len(sig['parameters']) == 0
        assert sig['return_type'] == 'int'
    
    def test_signature_default_calling_convention(self):
        """Test 695: Default calling convention is cdecl."""
        mirror = PythonSignatureMirror()
        contract = {'name': 'func', 'parameters': []}
        
        sig = mirror.build_signature(contract)
        assert sig['calling_convention'] == 'cdecl'
    
    def test_signature_custom_calling_convention(self):
        """Test 696: Extract custom calling convention."""
        mirror = PythonSignatureMirror()
        contract = {
            'name': 'func',
            'calling_convention': 'stdcall',
            'parameters': []
        }
        
        sig = mirror.build_signature(contract)
        assert sig['calling_convention'] == 'stdcall'
    
    def test_signature_default_return_type(self):
        """Test 697: Default return type is void."""
        mirror = PythonSignatureMirror()
        contract = {'name': 'func', 'parameters': []}
        
        sig = mirror.build_signature(contract)
        assert sig['return_type'] == 'void'
    
    def test_signature_default_name(self):
        """Test 698: Default name is 'unknown'."""
        mirror = PythonSignatureMirror()
        contract = {'parameters': []}
        
        sig = mirror.build_signature(contract)
        assert sig['name'] == 'unknown'
    
    def test_get_ctypes_signature(self):
        """Test 699: ctypes signature generation."""
        mirror = PythonSignatureMirror()
        sig = {
            'name': 'func',
            'parameters': [
                {'name': 'a', 'c_type': 'int'},
                {'name': 'b', 'c_type': 'double'}
            ],
            'return_type': 'int'
        }
        
        ctypes_sig = mirror.get_ctypes_signature(sig)
        assert 'argtypes' in ctypes_sig
        assert 'restype' in ctypes_sig
        assert len(ctypes_sig['argtypes']) == 2
        assert ctypes_sig['argtypes'][0] == ctypes.c_int
        assert ctypes_sig['argtypes'][1] == ctypes.c_double
        assert ctypes_sig['restype'] == ctypes.c_int
    
    def test_get_ctypes_signature_no_params(self):
        """Test 700: ctypes signature with no params."""
        mirror = PythonSignatureMirror()
        sig = {
            'name': 'func',
            'parameters': [],
            'return_type': 'void'
        }
        
        ctypes_sig = mirror.get_ctypes_signature(sig)
        assert len(ctypes_sig['argtypes']) == 0
    
    def test_get_ctypes_signature_char_ptr(self):
        """Test 701: ctypes signature with char*."""
        mirror = PythonSignatureMirror()
        sig = {
            'name': 'func',
            'parameters': [{'name': 's', 'c_type': 'char*'}],
            'return_type': 'char*'
        }
        
        ctypes_sig = mirror.get_ctypes_signature(sig)
        assert ctypes_sig['argtypes'][0] == ctypes.c_char_p
        assert ctypes_sig['restype'] == ctypes.c_char_p
    
    def test_get_cffi_cdef_simple(self):
        """Test 702: Build cffi cdef string."""
        mirror = PythonSignatureMirror()
        sig = {
            'name': 'add',
            'parameters': [
                {'name': 'a', 'c_type': 'int'},
                {'name': 'b', 'c_type': 'int'}
            ],
            'return_type': 'int'
        }
        
        cdef = mirror.get_cffi_cdef(sig)
        assert cdef == 'int add(int a, int b);'
    
    def test_get_cffi_cdef_no_params(self):
        """Test 703: Build cffi cdef with no params."""
        mirror = PythonSignatureMirror()
        sig = {
            'name': 'get_value',
            'parameters': [],
            'return_type': 'int'
        }
        
        cdef = mirror.get_cffi_cdef(sig)
        assert 'void' in cdef
        assert 'get_value' in cdef
    
    def test_get_cffi_cdef_complex(self):
        """Test 704: Build cffi cdef with mixed types."""
        mirror = PythonSignatureMirror()
        sig = {
            'name': 'process',
            'parameters': [
                {'name': 'data', 'c_type': 'char*'},
                {'name': 'len', 'c_type': 'int'}
            ],
            'return_type': 'int'
        }
        
        cdef = mirror.get_cffi_cdef(sig)
        assert 'char* data' in cdef
        assert 'int len' in cdef
    
    def test_build_signature_with_return(self):
        """Test 705: Build signature extracts return type."""
        mirror = PythonSignatureMirror()
        contract = {
            'name': 'calc',
            'parameters': [{'name': 'x', 'type': 'double'}],
            'return': {'type': 'double'}
        }
        
        sig = mirror.build_signature(contract)
        assert sig['return_type'] == 'double'


# ════════════════════════════════════════════════════════════════════════════
# CTYPES INTEGRATION TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestCtypesIntegration:
    """CtypesIntegration tests (15 tests)."""
    
    def test_create_integration(self):
        """Test 706: Create ctypes integration."""
        integration = CtypesIntegration()
        assert integration is not None
    
    def test_has_signature_mirror(self):
        """Test 707: Has signature mirror."""
        integration = CtypesIntegration()
        assert integration.signature_mirror is not None
        assert isinstance(integration.signature_mirror, PythonSignatureMirror)
    
    def test_loaded_libraries_empty(self):
        """Test 708: Loaded libraries initially empty."""
        integration = CtypesIntegration()
        assert len(integration.loaded_libraries) == 0
    
    def test_load_library_invalid_path(self):
        """Test 709: Load invalid library raises error."""
        integration = CtypesIntegration()
        with pytest.raises(RuntimeError, match='Failed to load library'):
            integration.load_library('nonexistent_lib_xyz.so')
    
    def test_configure_function_not_found(self):
        """Test 710: Configure non-existent function raises ValueError."""
        integration = CtypesIntegration()
        
        class MockLib:
            pass
        
        lib = MockLib()
        sig = {'name': 'func', 'parameters': [], 'return_type': 'int'}
        
        with pytest.raises(ValueError, match='not found'):
            integration.configure_function(lib, 'missing_func', sig)
    
    def test_configure_function_found(self):
        """Test 711: Configure existing function applies signature."""
        integration = CtypesIntegration()
        
        class MockFunc:
            argtypes = None
            restype = None
        
        class MockLib:
            my_func = MockFunc()
        
        lib = MockLib()
        sig = {
            'name': 'my_func',
            'parameters': [{'name': 'x', 'c_type': 'int'}],
            'return_type': 'int'
        }
        
        func = integration.configure_function(lib, 'my_func', sig)
        assert func is not None
    
    def test_get_loaded_libraries_empty(self):
        """Test 712: Get loaded libraries returns empty list initially."""
        integration = CtypesIntegration()
        assert integration.get_loaded_libraries() == []
    
    def test_load_library_cdecl(self):
        """Test 713: Load library respects cdecl default."""
        integration = CtypesIntegration()
        # This will fail since we don't have a real lib, but verifying the path
        with pytest.raises(RuntimeError):
            integration.load_library('fake_lib.so', 'cdecl')
    
    def test_load_library_stdcall(self):
        """Test 714: Load library with stdcall convention."""
        integration = CtypesIntegration()
        with pytest.raises(RuntimeError):
            integration.load_library('fake_lib.dll', 'stdcall')
    
    def test_signature_mirror_type(self):
        """Test 715: Signature mirror is PythonSignatureMirror."""
        integration = CtypesIntegration()
        assert isinstance(integration.signature_mirror, PythonSignatureMirror)
    
    def test_loaded_libraries_is_dict(self):
        """Test 716: Loaded libraries storage is a dict."""
        integration = CtypesIntegration()
        assert isinstance(integration.loaded_libraries, dict)
    
    def test_configure_function_with_void_return(self):
        """Test 717: Configure function with void return."""
        integration = CtypesIntegration()
        
        class MockFunc:
            argtypes = None
            restype = None
        
        class MockLib:
            do_nothing = MockFunc()
        
        lib = MockLib()
        sig = {
            'name': 'do_nothing',
            'parameters': [],
            'return_type': 'void'
        }
        
        func = integration.configure_function(lib, 'do_nothing', sig)
        assert func is not None
    
    def test_configure_function_multiple_params(self):
        """Test 718: Configure function with multiple parameter types."""
        integration = CtypesIntegration()
        
        class MockFunc:
            argtypes = None
            restype = None
        
        class MockLib:
            process = MockFunc()
        
        lib = MockLib()
        sig = {
            'name': 'process',
            'parameters': [
                {'name': 'data', 'c_type': 'char*'},
                {'name': 'len', 'c_type': 'int'},
                {'name': 'factor', 'c_type': 'double'}
            ],
            'return_type': 'int'
        }
        
        func = integration.configure_function(lib, 'process', sig)
        assert func.argtypes is not None
        assert len(func.argtypes) == 3
    
    def test_load_library_error_includes_message(self):
        """Test 719: Load library error includes descriptive message."""
        integration = CtypesIntegration()
        with pytest.raises(RuntimeError) as exc_info:
            integration.load_library('nonexistent_xyz.so')
        assert 'Failed to load library' in str(exc_info.value)
    
    def test_new_integration_independent(self):
        """Test 720: Each integration is independent."""
        int1 = CtypesIntegration()
        int2 = CtypesIntegration()
        assert int1.loaded_libraries is not int2.loaded_libraries


# ════════════════════════════════════════════════════════════════════════════
# CFFI INTEGRATION TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestCffiIntegration:
    """CffiIntegration tests (10 tests)."""
    
    def test_create_integration(self):
        """Test 721: Create cffi integration."""
        integration = CffiIntegration()
        assert integration is not None
    
    def test_ffi_initially_none(self):
        """Test 722: FFI initially None."""
        integration = CffiIntegration()
        assert integration.ffi is None
    
    def test_build_cdef_simple(self):
        """Test 723: Build cdef string for simple function."""
        integration = CffiIntegration()
        sig = {
            'name': 'add',
            'parameters': [
                {'name': 'a', 'c_type': 'int'},
                {'name': 'b', 'c_type': 'int'}
            ],
            'return_type': 'int'
        }
        
        cdef = integration.build_cdef_from_signature(sig)
        assert 'int add(int a, int b)' in cdef
        assert cdef.endswith(';')
    
    def test_build_cdef_no_params(self):
        """Test 724: Build cdef with no params uses void."""
        integration = CffiIntegration()
        sig = {
            'name': 'get_value',
            'parameters': [],
            'return_type': 'int'
        }
        
        cdef = integration.build_cdef_from_signature(sig)
        assert 'void' in cdef
        assert 'get_value' in cdef
    
    def test_build_cdef_char_ptr(self):
        """Test 725: Build cdef with char* parameter."""
        integration = CffiIntegration()
        sig = {
            'name': 'print_str',
            'parameters': [{'name': 'msg', 'c_type': 'char*'}],
            'return_type': 'void'
        }
        
        cdef = integration.build_cdef_from_signature(sig)
        assert 'char* msg' in cdef
    
    def test_loaded_libraries_empty(self):
        """Test 726: Loaded libraries initially empty."""
        integration = CffiIntegration()
        assert len(integration.loaded_libraries) == 0
    
    def test_get_loaded_libraries(self):
        """Test 727: Get loaded libraries returns list."""
        integration = CffiIntegration()
        result = integration.get_loaded_libraries()
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_build_cdef_multiple_params(self):
        """Test 728: Build cdef with multiple params."""
        integration = CffiIntegration()
        sig = {
            'name': 'compute',
            'parameters': [
                {'name': 'x', 'c_type': 'double'},
                {'name': 'y', 'c_type': 'double'},
                {'name': 'n', 'c_type': 'int'}
            ],
            'return_type': 'double'
        }
        
        cdef = integration.build_cdef_from_signature(sig)
        assert 'double compute(double x, double y, int n);' == cdef
    
    def test_build_cdef_void_return(self):
        """Test 729: Build cdef with void return type."""
        integration = CffiIntegration()
        sig = {
            'name': 'init',
            'parameters': [],
            'return_type': 'void'
        }
        
        cdef = integration.build_cdef_from_signature(sig)
        assert cdef.startswith('void ')
    
    def test_new_integration_independent(self):
        """Test 730: Each integration is independent."""
        int1 = CffiIntegration()
        int2 = CffiIntegration()
        assert int1.loaded_libraries is not int2.loaded_libraries
        assert int1.ffi is int2.ffi  # Both None initially


# ════════════════════════════════════════════════════════════════════════════
# PYTHON ADAPTER TESTS (5 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonAdapter:
    """PythonAdapter tests (5 tests)."""
    
    def test_create_adapter_ctypes(self):
        """Test 731: Create Python adapter with ctypes mode."""
        adapter = PythonAdapter(ffi_mode='ctypes')
        assert adapter.ffi_mode == 'ctypes'
        assert isinstance(adapter.ffi_integration, CtypesIntegration)
    
    def test_create_adapter_cffi(self):
        """Test 732: Create Python adapter with cffi mode."""
        adapter = PythonAdapter(ffi_mode='cffi')
        assert adapter.ffi_mode == 'cffi'
        assert isinstance(adapter.ffi_integration, CffiIntegration)
    
    def test_create_adapter_invalid_mode(self):
        """Test 733: Invalid FFI mode raises error."""
        with pytest.raises(ValueError, match='Invalid FFI mode'):
            PythonAdapter(ffi_mode='invalid')
    
    def test_adapter_has_normalizer(self):
        """Test 734: Adapter has Python normalizer."""
        adapter = PythonAdapter()
        assert isinstance(adapter.normalizer, PythonNormalizer)
        assert isinstance(adapter.get_normalizer(), PythonNormalizer)
    
    def test_adapter_has_signature_mirror(self):
        """Test 735: Adapter has signature mirror."""
        adapter = PythonAdapter()
        assert isinstance(adapter.signature_mirror, PythonSignatureMirror)
        assert adapter.get_ffi_mode() == 'ctypes'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
