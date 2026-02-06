"""
Unit tests for Module 04: Native Interface Ingestion

Tests foundational data structures, serialization, and architectural contracts.
"""

import sys
import os
import warnings
from pathlib import Path

# Suppress datetime UTC warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='datetime')

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
    ToolchainError,
    get_module_info,
        ClangFrontend,
    ClangCompilationUnit,
    SourceLocation,
    LIBCLANG_AVAILABLE
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
        assert info['prompt'] == '2/20'
        assert info['status'] == 'clang_integration'
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
# TEST: CLANG FRONTEND ()
# ============================================================================

class TestSourceLocation:
    """Test source location representation."""
    
    def test_source_location_creation(self):
        """Test creating source location."""
        loc = SourceLocation(file_path='test.h', line=42, column=10)
        
        assert loc.file_path == 'test.h'
        assert loc.line == 42
        assert loc.column == 10
    
    def test_source_location_serialization(self):
        """Test source location serialization."""
        loc = SourceLocation(file_path='foo.c', line=100, column=5)
        
        data = loc.to_dict()
        
        assert data['file'] == 'foo.c'
        assert data['line'] == 100
        assert data['column'] == 5

class TestEnhancedExternalSymbol:
    """Test enhanced external symbol with metadata."""
    
    def test_symbol_with_location(self):
        """Test symbol with source location."""
        loc = SourceLocation(file_path='api.h', line=10, column=1)
        symbol = ExternalSymbol(
            name='my_func',
            kind='function',
            source_location=loc,
            linkage='external'
        )
        
        assert symbol.name == 'my_func'
        assert symbol.source_location == loc
        assert symbol.linkage == 'external'
    
    def test_symbol_enhanced_serialization(self):
        """Test serialization with enhanced metadata."""
        loc = SourceLocation(file_path='types.h', line=50, column=1)
        symbol = ExternalSymbol(
            name='MyStruct',
            kind='struct',
            source_location=loc,
            linkage='external',
            type_spelling='struct MyStruct'
        )
        
        data = symbol.to_dict()
        
        assert 'source_location' in data
        assert data['source_location']['file'] == 'types.h'
        assert data['linkage'] == 'external'
        assert data['type_spelling'] == 'struct MyStruct'

class TestClangFrontend:
    """Test Clang frontend integration."""
    
    def test_clang_frontend_requires_libclang(self):
        """Test that ClangFrontend raises error when libclang unavailable."""
        if not LIBCLANG_AVAILABLE:
            with pytest.raises(ToolchainError) as exc_info:
                ClangFrontend()
            assert "libclang not available" in str(exc_info.value)
        else:
            # If libclang is available, test creation succeeds
            frontend = ClangFrontend()
            assert frontend.compiler_name == 'clang'
            assert frontend.compiler_version is not None
    
    def test_clang_args_construction(self):
        """Test building Clang command-line arguments."""
        if not LIBCLANG_AVAILABLE:
            # When libclang unavailable, test that we can't create frontend
            with pytest.raises(ToolchainError):
                ClangFrontend()
            return
            
        frontend = ClangFrontend()
        
        context = CompilationContext(
            header_files=[Path('test.h')],
            include_paths=[Path('/usr/include'), Path('/opt/include')],
            macro_definitions={'DEBUG': '1', 'FEATURE_X': ''},
            target_triple='x86_64-pc-linux-gnu',
            language_standard='c11',
            abi_flags=['-fms-extensions']
        )
        
        args = frontend._build_clang_args(context)
        
        assert '-I/usr/include' in args or str(Path('/usr/include')) in ' '.join(args)
        assert '-I/opt/include' in args or str(Path('/opt/include')) in ' '.join(args)
        assert '-DDEBUG=1' in args
        assert '-DFEATURE_X' in args
        assert '-target' in args
        assert 'x86_64-pc-linux-gnu' in args
        assert '-std=c11' in args
        assert '-fms-extensions' in args
    
    def test_parse_headers_requires_headers(self):
        """Test parsing fails without headers."""
        if not LIBCLANG_AVAILABLE:
            # When libclang unavailable, test that we can't create frontend
            with pytest.raises(ToolchainError):
                ClangFrontend()
            return
            
        frontend = ClangFrontend()
        
        context = CompilationContext(header_files=[])
        
        with pytest.raises(ConfigError) as exc_info:
            frontend.parse_headers(context)
        
        assert "No header files" in str(exc_info.value)

class TestClangCompilationUnit:
    """Test Clang compilation unit wrapper."""
    
    def test_compilation_unit_creation(self):
        """Test creating compilation unit wrapper."""
        # Create mock pointers (not actual Clang objects)
        unit = ClangCompilationUnit(index=None, translation_unit=None)
        
        assert unit.index is None
        assert unit.translation_unit is None
    
    def test_compilation_unit_disposal(self):
        """Test disposal doesn't crash with None pointers."""
        unit = ClangCompilationUnit(index=None, translation_unit=None)
        
        # Should not raise
        unit.dispose()
        
        assert unit.index is None
        assert unit.translation_unit is None

# ============================================================================
# MEDIUM LEVEL TESTING: 80-100 TESTS TARGET
# Progress: 28 components minimum for medium level
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
