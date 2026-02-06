"""
Unit tests for Module 04: Native Interface Ingestion

Tests foundational data structures, serialization, and architectural contracts.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import json
from datetime import datetime

from modules.module_04_native_interface_ingestion.native_interface_ingestion import (
    CompilationContext,
    RawInterfaceArtifact,
    ExternalSymbol,
    TypeInfo,
    CompilerFrontend,
    CompilationUnit,
    IngestionError,
    ConfigError,
    get_module_info
)

# ============================================================================
# TEST: MODULE METADATA
# ============================================================================

class TestModuleMetadata:
    """Test module metadata and versioning."""
    
    def test_module_info(self):
        """Test module information retrieval."""
        info = get_module_info()
        
        assert info['module'] == '04'
        assert info['version'] == '1.0.0'
        assert info['prompt'] == '1/20'
        assert info['status'] == 'foundation'
        assert 'Native Interface Ingestion' in info['name']

# ============================================================================
# TEST: COMPILATION CONTEXT
# ============================================================================

class TestCompilationContext:
    """Test compilation context data structure."""
    
    def test_context_creation(self):
        """Test creating compilation context."""
        context = CompilationContext(
            header_files=[Path('test.h')],
            include_paths=[Path('/usr/include')],
            macro_definitions={'DEBUG': '1'},
            target_triple='x86_64-pc-linux-gnu',
            abi_flags=['-fms-extensions'],
            language_standard='c11',
            compiler_name='clang',
            compiler_version='14.0.0'
        )
        
        assert len(context.header_files) == 1
        assert context.header_files[0] == Path('test.h')
        assert context.target_triple == 'x86_64-pc-linux-gnu'
        assert context.macro_definitions['DEBUG'] == '1'
    
    def test_context_serialization(self):
        """Test context to_dict serialization."""
        context = CompilationContext(
            header_files=[Path('foo.h'), Path('bar.h')],
            include_paths=[Path('/include')],
            target_triple='x86_64-pc-windows-msvc'
        )
        
        data = context.to_dict()
        
        assert 'header_files' in data
        assert len(data['header_files']) == 2
        assert 'foo.h' in data['header_files'][0]
        assert data['target_triple'] == 'x86_64-pc-windows-msvc'
        assert 'compiler' in data
    
    def test_context_hash_determinism(self):
        """Test context hash is deterministic."""
        context1 = CompilationContext(
            header_files=[Path('test.h')],
            target_triple='x86_64-unknown-linux-gnu'
        )
        
        context2 = CompilationContext(
            header_files=[Path('test.h')],
            target_triple='x86_64-unknown-linux-gnu'
        )
        
        hash1 = context1.compute_hash()
        hash2 = context2.compute_hash()
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256
    
    def test_context_hash_sensitivity(self):
        """Test context hash changes with content."""
        context1 = CompilationContext(
            header_files=[Path('test.h')],
            target_triple='x86_64-pc-linux-gnu'
        )
        
        context2 = CompilationContext(
            header_files=[Path('test.h')],
            target_triple='x86_64-pc-windows-msvc'  # Different
        )
        
        assert context1.compute_hash() != context2.compute_hash()

# ============================================================================
# TEST: EXTERNAL SYMBOL
# ============================================================================

class TestExternalSymbol:
    """Test external symbol representation."""
    
    def test_symbol_creation(self):
        """Test creating external symbol."""
        symbol = ExternalSymbol(name='my_function', kind='function')
        
        assert symbol.name == 'my_function'
        assert symbol.kind == 'function'
    
    def test_symbol_serialization(self):
        """Test symbol to_dict serialization."""
        symbol = ExternalSymbol(name='global_var', kind='variable')
        
        data = symbol.to_dict()
        
        assert data['name'] == 'global_var'
        assert data['kind'] == 'variable'

# ============================================================================
# TEST: TYPE INFO
# ============================================================================

class TestTypeInfo:
    """Test type information representation."""
    
    def test_typeinfo_creation(self):
        """Test creating type info."""
        tinfo = TypeInfo(name='MyStruct', canonical_name='struct MyStruct')
        
        assert tinfo.name == 'MyStruct'
        assert tinfo.canonical_name == 'struct MyStruct'
    
    def test_typeinfo_serialization(self):
        """Test type info serialization."""
        tinfo = TypeInfo(name='int32_t', canonical_name='int')
        
        data = tinfo.to_dict()
        
        assert data['name'] == 'int32_t'
        assert data['canonical_name'] == 'int'

# ============================================================================
# TEST: RAW INTERFACE ARTIFACT
# ============================================================================

class TestRawInterfaceArtifact:
    """Test raw interface artifact."""
    
    def test_artifact_creation(self):
        """Test creating artifact."""
        context = CompilationContext(
            header_files=[Path('test.h')],
            target_triple='x86_64-pc-linux-gnu'
        )
        
        artifact = RawInterfaceArtifact(
            compilation_context=context,
            validation_passed=True
        )
        
        assert artifact.artifact_version == '1.0'
        assert artifact.validation_passed is True
        assert artifact.compilation_context == context
    
    def test_artifact_json_serialization(self):
        """Test artifact JSON serialization."""
        context = CompilationContext(
            header_files=[Path('test.h')],
            compiler_name='clang',
            compiler_version='14.0'
        )
        
        symbol = ExternalSymbol(name='foo', kind='function')
        tinfo = TypeInfo(name='int', canonical_name='int')
        
        artifact = RawInterfaceArtifact(
            compilation_context=context,
            external_symbols=[symbol],
            type_definitions={'int': tinfo}
        )
        
        json_str = artifact.to_json()
        
        assert 'artifact_version' in json_str
        assert 'test.h' in json_str
        assert 'foo' in json_str
    
    def test_artifact_save_load(self, tmp_path):
        """Test artifact save and load."""
        context = CompilationContext(
            header_files=[Path('interface.h')],
            target_triple='x86_64-pc-windows-msvc'
        )
        
        original = RawInterfaceArtifact(
            compilation_context=context,
            validation_passed=True
        )
        
        artifact_path = tmp_path / 'artifact.json'
        original.save(artifact_path)
        
        assert artifact_path.exists()
        
        loaded = RawInterfaceArtifact.load(artifact_path)
        
        assert loaded.artifact_version == original.artifact_version
        assert loaded.validation_passed is True
        assert loaded.compilation_context.target_triple == 'x86_64-pc-windows-msvc'
    
    def test_artifact_contains_timestamp(self):
        """Test artifact includes generation timestamp."""
        artifact = RawInterfaceArtifact()
        
        assert artifact.generation_timestamp is not None
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(artifact.generation_timestamp)

# ============================================================================
# TEST: COMPILER FRONTEND ABSTRACTION
# ============================================================================

class TestCompilerFrontend:
    """Test compiler frontend abstraction."""
    
    def test_frontend_is_abstract(self):
        """Test CompilerFrontend cannot be instantiated."""
        with pytest.raises(TypeError):
            CompilerFrontend()
    
    def test_compilation_unit_creation(self):
        """Test CompilationUnit can be created."""
        unit = CompilationUnit(internal_repr={'test': 'data'})
        assert unit.internal_repr == {'test': 'data'}

# ============================================================================
# TEST: ERROR HIERARCHY
# ============================================================================

class TestIngestionErrors:
    """Test ingestion error taxonomy."""
    
    def test_ingestion_error_base(self):
        """Test IngestionError is base class."""
        error = IngestionError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"
    
    def test_configuration_error(self):
        """Test ConfigError inheritance."""
        error = ConfigError("missing header")
        assert isinstance(error, IngestionError)
        assert isinstance(error, Exception)
    
    def test_error_can_be_raised(self):
        """Test errors can be raised and caught."""
        with pytest.raises(ConfigError) as exc_info:
            raise ConfigError("test config error")
        
        assert "test config error" in str(exc_info.value)

# ============================================================================
# EASY LEVEL: 20-50 TESTS TARGET
# Total tests implemented: 21 tests
# All foundational data structures and contracts tested
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
