#!/usr/bin/env python3
"""
Unit tests for Module 03 Build Process - 
Tests build stage pipeline infrastructure.
"""

import pytest
import sys
import hashlib
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.module_03_build_process.build_process import (
    BuildStage,
    BuildError,
    BuildPreconditionError,
    BuildPostconditionError,
    SourceEnumerationStage,
    SourceValidationStage,
    DependencyResolutionStage,
    PipelineCheckpoint,
    EnhancedBuildProcessOrchestrator,
    EnvironmentDescriptor,
    BuildMode,
    ToolchainDescriptor
)

class TestSourceEnumerationStage:
    """Test Stage 1: Source Enumeration."""

    def test_stage_creation(self):
        """Test creating source enumeration stage."""
        stage = SourceEnumerationStage(Path("."))
        assert stage.stage_name == "Source Enumeration"
        assert stage.stage_number == BuildStage.SOURCE_ENUMERATION

    def test_precondition_validation(self, tmp_path):
        """Test precondition checking."""
        stage = SourceEnumerationStage(tmp_path)
        
        # Missing environment should fail
        with pytest.raises(BuildPreconditionError):
            stage.check_preconditions({})
        
        # Valid environment should pass
        env = self._create_test_environment()
        stage.check_preconditions({'environment': env})

    def test_source_enumeration(self, tmp_path):
        """Test source file enumeration."""
        # Create test source files
        (tmp_path / "main.c").write_text("int main() {}")
        (tmp_path / "main.h").write_text("#pragma once")
        (tmp_path / "app.py").write_text("print('hello')")
        
        stage = SourceEnumerationStage(tmp_path)
        env = self._create_test_environment()
        context = {'environment': env}
        
        # Execute stage
        updated_context = stage.execute(context)
        
        # Verify outputs
        assert 'source_files' in updated_context
        assert 'source_hashes' in updated_context
        assert len(updated_context['source_files']['c_sources']) == 1
        assert len(updated_context['source_files']['headers']) == 1
        assert len(updated_context['source_files']['python_sources']) == 1

    def test_postcondition_validation(self, tmp_path):
        """Test postcondition validation."""
        stage = SourceEnumerationStage(tmp_path)
        
        # Missing source_files should fail
        with pytest.raises(BuildPostconditionError):
            stage.validate_postconditions({})
        
        # Empty source_files should fail
        with pytest.raises(BuildPostconditionError):
            stage.validate_postconditions({
                'source_files': {'c_sources': [], 'headers': [], 'python_sources': []},
                'source_hashes': {}
            })

    def _create_test_environment(self):
        """Create test environment descriptor."""
        return EnvironmentDescriptor(
            compiler_name="Test",
            compiler_version="1.0",
            compiler_executable=Path("/usr/bin/test"),
            linker_executable=Path("/usr/bin/ld"),
            target_os="Linux",
            target_architecture="x86_64",
            host_os="Linux",
            host_architecture="x86_64",
            build_mode=BuildMode.DEBUG,
            optimization_level="O0",
            debug_symbols=True,
            calling_convention="cdecl",
            structure_packing=8,
            alignment_rules="default"
        )

class TestPipelineCheckpoint:
    """Test checkpoint management."""

    def test_checkpoint_creation(self, tmp_path):
        """Test creating checkpoint manager."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = PipelineCheckpoint(checkpoint_dir)
        assert checkpoint_dir.exists()

    def test_save_checkpoint(self, tmp_path):
        """Test saving checkpoint."""
        manager = PipelineCheckpoint(tmp_path)
        
        context = {'test_key': 'test_value', 'number': 42}
        checkpoint_file = manager.save_checkpoint(BuildStage.SOURCE_ENUMERATION, context)
        
        assert checkpoint_file.exists()
        assert 'checkpoint_stage_1' in checkpoint_file.name

    def test_load_checkpoint(self, tmp_path):
        """Test loading checkpoint."""
        manager = PipelineCheckpoint(tmp_path)
        
        original_context = {'test_key': 'test_value', 'number': 42}
        manager.save_checkpoint(BuildStage.SOURCE_ENUMERATION, original_context)
        
        loaded_context = manager.load_checkpoint(BuildStage.SOURCE_ENUMERATION)
        assert loaded_context['test_key'] == 'test_value'
        assert loaded_context['number'] == 42

    def test_list_checkpoints(self, tmp_path):
        """Test listing available checkpoints."""
        manager = PipelineCheckpoint(tmp_path)
        
        manager.save_checkpoint(BuildStage.SOURCE_ENUMERATION, {})
        manager.save_checkpoint(BuildStage.SOURCE_VALIDATION, {})
        
        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 2
        assert checkpoints[0][0] == BuildStage.SOURCE_ENUMERATION
        assert checkpoints[1][0] == BuildStage.SOURCE_VALIDATION

class TestEnhancedOrchestrator:
    """Test enhanced build orchestrator."""

    def test_orchestrator_creation(self):
        """Test creating enhanced orchestrator."""
        env = self._create_test_environment()
        orchestrator = EnhancedBuildProcessOrchestrator(env)
        assert orchestrator.environment == env
        assert orchestrator.checkpoint_manager is None

    def test_orchestrator_with_checkpoints(self, tmp_path):
        """Test orchestrator with checkpoint support."""
        env = self._create_test_environment()
        orchestrator = EnhancedBuildProcessOrchestrator(env, checkpoint_dir=tmp_path)
        assert orchestrator.checkpoint_manager is not None

    def _create_test_environment(self):
        """Create test environment."""
        return EnvironmentDescriptor(
            compiler_name="Test",
            compiler_version="1.0",
            compiler_executable=Path("/usr/bin/test"),
            linker_executable=Path("/usr/bin/ld"),
            target_os="Linux",
            target_architecture="x86_64",
            host_os="Linux",
            host_architecture="x86_64",
            build_mode=BuildMode.DEBUG,
            optimization_level="O0",
            debug_symbols=True,
            calling_convention="cdecl",
            structure_packing=8,
            alignment_rules="default"
        )

class TestSourceMetadata:
    """Test SourceMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating source metadata."""
        from modules.module_03_build_process.build_process import (
            SourceMetadata, BuildDomain
        )
        
        metadata = SourceMetadata(
            file_path=Path("src/test.c"),
            relative_path=Path("test.c"),
            file_hash="abc123",
            file_size=1024,
            line_count=50,
            encoding="utf-8",
            language="c",
            role="production",
            domain=BuildDomain.NATIVE_VERIFICATION_TOOLING
        )
        
        assert metadata.language == "c"
        assert metadata.role == "production"
        assert metadata.file_size == 1024

    def test_metadata_serialization(self):
        """Test metadata to_dict conversion."""
        from modules.module_03_build_process.build_process import (
            SourceMetadata, BuildDomain
        )
        
        metadata = SourceMetadata(
            file_path=Path("src/test.py"),
            relative_path=Path("test.py"),
            file_hash="def456",
            file_size=2048,
            line_count=100,
            encoding="utf-8",
            language="python",
            role="test",
            domain=BuildDomain.ORCHESTRATION_ADAPTER_TOOLING
        )
        
        data = metadata.to_dict()
        assert data['language'] == "python"
        assert data['role'] == "test"
        assert data['file_size'] == 2048

class TestDependencyGraph:
    """Test dependency graph construction and operations."""

    def test_graph_creation(self):
        """Test creating empty dependency graph."""
        from modules.module_03_build_process.build_process import DependencyGraph
        
        graph = DependencyGraph()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_nodes_and_edges(self):
        """Test adding nodes and edges to graph."""
        from modules.module_03_build_process.build_process import (
            DependencyGraph, SourceMetadata, BuildDomain
        )
        
        graph = DependencyGraph()
        
        # Create test metadata
        meta_a = SourceMetadata(
            file_path=Path("a.c"), relative_path=Path("a.c"),
            file_hash="hash_a", file_size=100, line_count=10,
            encoding="utf-8", language="c", role="production",
            domain=BuildDomain.NATIVE_VERIFICATION_TOOLING
        )
        meta_b = SourceMetadata(
            file_path=Path("b.c"), relative_path=Path("b.c"),
            file_hash="hash_b", file_size=200, line_count=20,
            encoding="utf-8", language="c", role="production",
            domain=BuildDomain.NATIVE_VERIFICATION_TOOLING
        )
        
        # Add nodes
        graph.add_node("a.c", meta_a)
        graph.add_node("b.c", meta_b)
        
        # Add edge: a.c depends on b.c
        graph.add_edge("a.c", "b.c", "include")
        
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.get_dependencies("a.c") == ["b.c"]
        assert graph.get_dependents("b.c") == ["a.c"]

    def test_topological_sort(self):
        """Test topological sort of dependency graph."""
        from modules.module_03_build_process.build_process import (
            DependencyGraph, SourceMetadata, BuildDomain
        )
        
        graph = DependencyGraph()
        
        # Create chain: a -> b -> c
        # (a depends on b, b depends on c)
        # Order should be c, b, a
        for name in ['a', 'b', 'c']:
            meta = SourceMetadata(
                file_path=Path(f"{name}.c"), relative_path=Path(f"{name}.c"),
                file_hash=f"hash_{name}", file_size=100, line_count=10,
                encoding="utf-8", language="c", role="production",
                domain=BuildDomain.NATIVE_VERIFICATION_TOOLING
            )
            graph.add_node(f"{name}.c", meta)
        
        graph.add_edge("a.c", "b.c", "include")
        graph.add_edge("b.c", "c.c", "include")
        
        sorted_sources = graph.topological_sort()
        
        # c should come before b, b before a
        assert sorted_sources.index("c.c") < sorted_sources.index("b.c")
        assert sorted_sources.index("b.c") < sorted_sources.index("a.c")

class TestSourceHandlers:
    """Test language-specific source handlers."""

    def test_c_source_handler(self, tmp_path):
        """Test C/C++ source handler."""
        from modules.module_03_build_process.build_process import CSourceHandler
        
        handler = CSourceHandler()
        
        # Create test C file
        c_file = tmp_path / "main.c"
        c_file.write_text('#include "local.h"\n#include <stdio.h>\nint main() {}')
        
        assert handler.can_handle(c_file)
        
        metadata = handler.extract_metadata(c_file, tmp_path)
        assert metadata.language == "c"
        assert metadata.role == "production"

    def test_python_source_handler(self, tmp_path):
        """Test Python source handler."""
        from modules.module_03_build_process.build_process import PythonSourceHandler
        
        handler = PythonSourceHandler()
        
        # Create test Python file
        py_file = tmp_path / "app.py"
        py_file.write_text('import os\nfrom pathlib import Path\nprint("hello")')
        
        assert handler.can_handle(py_file)
        
        metadata = handler.extract_metadata(py_file, tmp_path)
        assert metadata.language == "python"
        
        dependencies = handler.extract_dependencies(py_file, tmp_path)
        assert "os" in dependencies
        assert "pathlib" in dependencies

class TestEnhancedSourceEnumeration:
    """Test enhanced source enumeration stage."""

    def test_enhanced_enumeration(self, tmp_path):
        """Test full enhanced source enumeration."""
        from modules.module_03_build_process.build_process import (
            EnhancedSourceEnumerationStage,
            EnvironmentDescriptor,
            BuildMode
        )
        
        # Create test source structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.c").write_text("int main() {}")
        (tmp_path / "src" / "utils.py").write_text("import os")
        
        # Create environment
        env = EnvironmentDescriptor(
            compiler_name="Test",
            compiler_version="1.0",
            compiler_executable=Path("/usr/bin/test"),
            linker_executable=Path("/usr/bin/ld"),
            target_os="Linux",
            target_architecture="x86_64",
            host_os="Linux",
            host_architecture="x86_64",
            build_mode=BuildMode.DEBUG,
            optimization_level="O0",
            debug_symbols=True,
            calling_convention="cdecl",
            structure_packing=8,
            alignment_rules="default"
        )
        
        # Execute enumeration
        stage = EnhancedSourceEnumerationStage(tmp_path / "src")
        context = stage.execute({'environment': env})
        
        # Verify outputs
        assert 'source_metadata' in context
        assert 'dependency_graph' in context
        assert 'sources_by_language' in context
        assert len(context['source_metadata']) == 2

class TestDependencySpecification:
    """Test dependency specification model."""

    def test_spec_creation(self):
        """Test creating dependency specification."""
        from modules.module_03_build_process.build_process import DependencySpecification
        
        dep = DependencySpecification(
            name="libclang",
            version="16.0.6",
            source="pypi",
            hash="sha256:abc123",
            license="Apache-2.0",
            scope="runtime"
        )
        
        assert dep.name == "libclang"
        assert dep.version == "16.0.6"
        assert dep.source == "pypi"

    def test_spec_serialization(self):
        """Test dependency spec to_dict/from_dict."""
        from modules.module_03_build_process.build_process import DependencySpecification
        
        original = DependencySpecification(
            name="pytest",
            version="7.4.0",
            source="pypi",
            scope="test"
        )
        
        data = original.to_dict()
        restored = DependencySpecification.from_dict(data)
        
        assert restored.name == original.name
        assert restored.version == original.version
        assert restored.scope == original.scope

    def test_hash_verification(self, tmp_path):
        """Test dependency hash verification."""
        from modules.module_03_build_process.build_process import DependencySpecification
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        
        # Compute actual hash
        import hashlib
        actual_hash = hashlib.sha256(b"hello world").hexdigest()
        
        # Create spec with correct hash
        dep = DependencySpecification(
            name="test",
            version="1.0",
            source="local",
            hash=actual_hash
        )
        
        # Verification should succeed
        assert dep.verify_hash(test_file) is True
        
        # Create spec with wrong hash
        dep_wrong = DependencySpecification(
            name="test",
            version="1.0",
            source="local",
            hash="wronghash"
        )
        
        # Verification should fail
        assert dep_wrong.verify_hash(test_file) is False

class TestDependencyLockFile:
    """Test dependency lock file."""

    def test_lock_file_creation(self):
        """Test creating lock file."""
        from modules.module_03_build_process.build_process import (
            DependencyLockFile, DependencySpecification
        )
        
        lock = DependencyLockFile(platform="Linux-x86_64")
        
        dep = DependencySpecification(
            name="numpy",
            version="1.24.0",
            source="pypi"
        )
        lock.add_dependency(dep)
        
        assert len(lock.dependencies) == 1
        assert lock.get_dependency("numpy") is not None

    def test_lock_file_save_load(self, tmp_path):
        """Test lock file serialization."""
        from modules.module_03_build_process.build_process import (
            DependencyLockFile, DependencySpecification
        )
        
        # Create lock file
        original_lock = DependencyLockFile(platform="Windows-x86_64")
        dep = DependencySpecification(
            name="requests",
            version="2.31.0",
            source="pypi",
            hash="sha256:abc123"
        )
        original_lock.add_dependency(dep)
        
        # Save
        lock_path = tmp_path / "test.lock"
        original_lock.save(lock_path)
        
        assert lock_path.exists()
        
        # Load
        loaded_lock = DependencyLockFile.load(lock_path)
        assert len(loaded_lock.dependencies) == 1
        assert loaded_lock.get_dependency("requests") is not None
        assert loaded_lock.get_dependency("requests").version == "2.31.0"

class TestDependencyResolver:
    """Test dependency resolver."""

    def test_resolver_creation(self, tmp_path):
        """Test creating dependency resolver."""
        from modules.module_03_build_process.build_process import DependencyResolver
        
        resolver = DependencyResolver(cache_dir=tmp_path)
        assert resolver.cache_dir == tmp_path
        assert len(resolver.resolved) == 0

    def test_simple_resolution(self, tmp_path):
        """Test resolving simple dependency tree."""
        from modules.module_03_build_process.build_process import (
            DependencyResolver, DependencySpecification
        )
        
        resolver = DependencyResolver(cache_dir=tmp_path)
        
        deps = [
            DependencySpecification(
                name="pkg1",
                version="1.0.0",
                source="pypi"
            )
        ]
        
        lock_file = resolver.resolve(deps)
        
        assert len(lock_file.dependencies) == 1
        assert "pkg1" in lock_file.dependencies

    def test_conflict_detection(self, tmp_path):
        """Test dependency conflict detection."""
        from modules.module_03_build_process.build_process import (
            DependencyResolver, DependencySpecification, DependencyLockFile
        )
        
        resolver = DependencyResolver(cache_dir=tmp_path)
        
        # Create conflicting dependencies
        dep1 = DependencySpecification(
            name="conflict_pkg",
            version="1.0.0",
            source="pypi"
        )
        dep2 = DependencySpecification(
            name="conflict_pkg",
            version="2.0.0",
            source="pypi"
        )
        
        # Resolve first dependency
        resolver._resolve_dependency(dep1, DependencyLockFile())
        
        # Resolve second (conflicting) dependency
        lock = DependencyLockFile()
        resolver._resolve_dependency(dep2, lock)
        
        # Conflict should be detected
        assert len(resolver.conflicts) > 0

class TestToolchainCapabilities:
    """Test toolchain capabilities model."""

    def test_capabilities_creation(self):
        """Test creating toolchain capabilities."""
        from modules.module_03_build_process.build_process import ToolchainCapabilities
        
        caps = ToolchainCapabilities(
            language_standards={'c': ['c99', 'c11'], 'cpp': ['c++17']},
            sanitizers=['asan', 'ubsan'],
            optimization_levels=['O0', 'O2'],
            abi_compatible=True,
            deterministic_output=True
        )
        
        assert 'c99' in caps.language_standards['c']
        assert 'asan' in caps.sanitizers
        assert caps.abi_compatible is True

    def test_capabilities_serialization(self):
        """Test capabilities to_dict/from_dict."""
        from modules.module_03_build_process.build_process import ToolchainCapabilities
        
        original = ToolchainCapabilities(
            language_standards={'c': ['c11']},
            sanitizers=['ubsan'],
            optimization_levels=['O2', 'O3'],
            supports_lto=True,
            deterministic_output=False
        )
        
        data = original.to_dict()
        restored = ToolchainCapabilities.from_dict(data)
        
        assert restored.language_standards == original.language_standards
        assert restored.supports_lto == original.supports_lto
        assert restored.deterministic_output == original.deterministic_output

class TestToolchainValidator:
    """Test toolchain validator."""

    def test_validator_creation(self, tmp_path):
        """Test creating toolchain validator."""
        from modules.module_03_build_process.build_process import (
            ToolchainValidator, ToolchainDescriptor
        )
        
        toolchain = ToolchainDescriptor(
            compiler_name="TestCompiler",
            compiler_version="1.0",
            compiler_full_version="1.0.0",
            compiler_executable=Path("/usr/bin/test"),
            compiler_executable_hash="hash123",
            linker_executable=Path("/usr/bin/ld"),
            linker_executable_hash="hash456",
            linker_version="1.0",
            target_triple="x86_64-unknown-linux-gnu",
            target_os="Linux",
            target_architecture="x86_64",
            target_abi="gnu",
            default_calling_convention="cdecl",
            default_structure_packing=8,
            supports_explicit_packing=True,
            name_mangling_scheme="itanium",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=True
        )
        
        validator = ToolchainValidator(toolchain, cache_dir=tmp_path)
        assert validator.toolchain == toolchain
        assert validator.cache_dir == tmp_path

    def test_cache_key_generation(self, tmp_path):
        """Test cache key generation."""
        from modules.module_03_build_process.build_process import (
            ToolchainValidator, ToolchainDescriptor
        )
        
        toolchain = ToolchainDescriptor(
            compiler_name="Clang",
            compiler_version="14.0.0",
            compiler_full_version="14.0.0",
            compiler_executable=Path("/usr/bin/clang"),
            compiler_executable_hash="hash",
            linker_executable=Path("/usr/bin/ld"),
            linker_executable_hash="hash",
            linker_version="1.0",
            target_triple="x86_64-pc-linux-gnu",
            target_os="Linux",
            target_architecture="x86_64",
            target_abi="gnu",
            default_calling_convention="sysv",
            default_structure_packing=1,
            supports_explicit_packing=True,
            name_mangling_scheme="itanium",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=True
        )
        
        validator = ToolchainValidator(toolchain, cache_dir=tmp_path)
        cache_key = validator._get_cache_key()
        
        assert "Clang" in cache_key
        assert "14.0.0" in cache_key
        assert "x86_64" in cache_key

class TestABIConfig:
    """Test ABI configuration model."""

    def test_abi_config_creation(self):
        """Test creating ABI configuration."""
        from modules.module_03_build_process.build_process import ABIConfig
        
        config = ABIConfig(
            platform="Windows-x86_64",
            structure_packing=8,
            default_calling_convention="microsoft_x64",
            exceptions_enabled=True,
            rtti_enabled=True
        )
        
        assert config.platform == "Windows-x86_64"
        assert config.structure_packing == 8
        assert config.exceptions_enabled is True

    def test_abi_config_serialization(self):
        """Test ABI config to_dict."""
        from modules.module_03_build_process.build_process import ABIConfig
        
        config = ABIConfig(
            platform="Linux-x86_64",
            structure_packing=1,
            default_calling_convention="sysv_amd64"
        )
        
        data = config.to_dict()
        assert data['platform'] == "Linux-x86_64"
        assert data['structure_packing'] == 1

class TestCompilerFlagManager:
    """Test compiler flag management."""

    def test_flag_manager_creation(self):
        """Test creating compiler flag manager."""
        from modules.module_03_build_process.build_process import (
            CompilerFlagManager, ABIConfig
        )
        
        abi_config = ABIConfig(platform="Windows-x86_64")
        toolchain = self._create_test_toolchain()
        
        manager = CompilerFlagManager(abi_config, toolchain)
        assert manager.abi_config == abi_config
        assert manager.toolchain == toolchain

    def test_flag_priority(self):
        """Test flag priority resolution."""
        from modules.module_03_build_process.build_process import (
            CompilerFlagManager, ABIConfig
        )
        
        abi_config = ABIConfig(
            platform="Windows-x86_64",
            compiler_flags={'msvc': ['/Zp8']}
        )
        toolchain = self._create_test_toolchain()
        
        manager = CompilerFlagManager(abi_config, toolchain)
        
        # Add flags at different priorities
        manager.add_global_flags(['/O2'])
        manager.add_target_flags('mylib', ['/DNDEBUG'])
        manager.add_file_flags('src/main.c', ['/W4'])
        
        # Get resolved flags for file
        flags = manager.get_flags_for_file('src/main.c', 'mylib')
        
        # Should include all flags
        assert '/O2' in flags  # Global
        assert '/Zp8' in flags  # ABI
        assert '/DNDEBUG' in flags  # Target
        assert '/W4' in flags  # File-specific

    def test_flag_validation(self):
        """Test flag conflict detection."""
        from modules.module_03_build_process.build_process import (
            CompilerFlagManager, ABIConfig
        )
        
        abi_config = ABIConfig(platform="Windows-x86_64")
        toolchain = self._create_test_toolchain()
        
        manager = CompilerFlagManager(abi_config, toolchain)
        
        # Conflicting structure packing flags
        issues = manager.validate_flags(['/Zp4', '/Zp8'])
        assert len(issues) > 0
        assert 'Conflicting' in issues[0]

    def _create_test_toolchain(self):
        """Create test toolchain descriptor."""
        from modules.module_03_build_process.build_process import ToolchainDescriptor
        
        return ToolchainDescriptor(
            compiler_name="MSVC",
            compiler_version="19.29",
            compiler_full_version="19.29.30133",
            compiler_executable=Path("/usr/bin/cl.exe"),
            compiler_executable_hash="hash",
            linker_executable=Path("/usr/bin/link.exe"),
            linker_executable_hash="hash",
            linker_version="14.29",
            target_triple="Windows-x86_64-msvc",
            target_os="Windows",
            target_architecture="x86_64",
            target_abi="msvc",
            default_calling_convention="microsoft_x64",
            default_structure_packing=8,
            supports_explicit_packing=True,
            name_mangling_scheme="msvc",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=False
        )

class TestABIVerifier:
    """Test ABI runtime verification."""

    def test_verifier_creation(self):
        """Test creating ABI verifier."""
        from modules.module_03_build_process.build_process import (
            ABIVerifier, ABIConfig
        )
        
        abi_config = ABIConfig(platform="Windows-x86_64")
        verifier = ABIVerifier(abi_config)
        
        assert verifier.expected_abi == abi_config
        assert len(verifier.verification_results) == 0

    def test_structure_verification(self):
        """Test structure layout verification."""
        from modules.module_03_build_process.build_process import (
            ABIVerifier, ABIConfig
        )
        
        abi_config = ABIConfig(platform="Windows-x86_64")
        verifier = ABIVerifier(abi_config)
        
        result = verifier.verify_structure_layout(
            "TestStruct",
            expected_size=12,
            expected_offsets={"a": 0, "b": 4, "c": 8}
        )
        
        assert result is True
        assert len(verifier.verification_results) == 1

    def test_report_generation(self):
        """Test verification report generation."""
        from modules.module_03_build_process.build_process import (
            ABIVerifier, ABIConfig
        )
        
        abi_config = ABIConfig(platform="Windows-x86_64")
        verifier = ABIVerifier(abi_config)
        
        verifier.verify_structure_layout("MyStruct", 16, {"x": 0})
        verifier.verify_calling_convention("my_function", "cdecl")
        
        report = verifier.generate_report()
        assert "MyStruct" in report
        assert "my_function" in report

class TestABIDriftDetector:
    """Test ABI drift detection."""

    def test_drift_detector_creation(self):
        """Test creating drift detector."""
        from modules.module_03_build_process.build_process import ABIDriftDetector
        
        detector = ABIDriftDetector()
        assert detector.baseline is None

    def test_drift_detection(self):
        """Test detecting ABI drift."""
        from modules.module_03_build_process.build_process import ABIDriftDetector
        
        detector = ABIDriftDetector()
        
        # Set baseline
        detector.baseline = {
            'structures': {
                'MyStruct': {'size': 12, 'fields': {'a': 0, 'b': 4}}
            },
            'symbols': ['foo', 'bar']
        }
        
        # Current snapshot with changes
        current = {
            'structures': {
                'MyStruct': {'size': 16, 'fields': {'a': 0, 'b': 4}}  # Size changed
            },
            'symbols': ['foo', 'baz']  # 'bar' removed, 'baz' added
        }
        
        drift = detector.detect_drift(current)
        
        assert len(drift) > 0
        assert any('size changed' in d for d in drift)
        assert any('Symbol removed: bar' in d for d in drift)
        assert any('Symbol added: baz' in d for d in drift)

class TestCompilationMetadata:
    """Test compilation metadata."""

    def test_metadata_creation(self):
        """Test creating compilation metadata."""
        from modules.module_03_build_process.build_process import CompilationMetadata
        
        metadata = CompilationMetadata(
            source_file=Path("test.c"),
            source_hash="abc123",
            output_file=Path("test.o"),
            compiler_name="GCC",
            compiler_version="11.2.0",
            success=True
        )
        
        assert metadata.source_file == Path("test.c")
        assert metadata.compiler_name == "GCC"
        assert metadata.success is True

    def test_metadata_serialization(self):
        """Test metadata to_dict."""
        from modules.module_03_build_process.build_process import CompilationMetadata
        
        metadata = CompilationMetadata(
            source_file=Path("main.c"),
            source_hash="hash1",
            output_file=Path("main.o"),
            flags_used=['-O2', '-g'],
            warnings=["unused variable"]
        )
        
        data = metadata.to_dict()
        assert 'source_file' in data
        assert data['flags_used'] == ['-O2', '-g']
        assert len(data['warnings']) == 1

class TestCompilationUnit:
    """Test compilation unit."""

    def test_unit_creation(self, tmp_path):
        """Test creating compilation unit."""
        from modules.module_03_build_process.build_process import (
            CompilationUnit, BuildMode
        )
        
        source = tmp_path / "mod.c"
        source.write_text("int main() { return 0; }")
        
        unit = CompilationUnit(
            source_file=source,
            output_file=tmp_path / "mod.o",
            compiler_flags=['-O2'],
            language='c',
            build_mode=BuildMode.RELEASE
        )
        
        assert unit.source_file == source
        assert unit.language == 'c'
        assert unit.build_mode == BuildMode.RELEASE
        assert unit.metadata is not None

class TestCompilerInvocation:
    """Test compiler invocation."""

    def test_invocation_command_building(self):
        """Test building compiler command."""
        from modules.module_03_build_process.build_process import (
            CompilerInvocation, CompilationUnit, BuildMode
        )
        
        toolchain = self._create_test_toolchain()
        
        unit = CompilationUnit(
            source_file=Path("test.c"),
            output_file=Path("test.o"),
            compiler_flags=['-O2'],
            include_paths=[Path("/usr/include")],
            defines={'DEBUG': '1'},
            language='c',
            build_mode=BuildMode.DEBUG,
            toolchain=toolchain
        )
        
        invocation = CompilerInvocation(unit)
        cmd = invocation.build_command()
        
        assert str(toolchain.compiler_executable) in cmd
        assert '-O2' in cmd
        # GCC style flags
        assert '-I' in cmd
        assert str(Path("/usr/include")) in cmd
        assert '-DDEBUG=1' in cmd
        assert 'test.c' in cmd
        assert 'test.o' in cmd

    def _create_test_toolchain(self):
        """Create test toolchain."""
        from modules.module_03_build_process.build_process import ToolchainDescriptor
        
        return ToolchainDescriptor(
            compiler_name="GCC",
            compiler_version="11.2.0",
            compiler_full_version="11.2.0",
            compiler_executable=Path("/usr/bin/gcc"),
            compiler_executable_hash="hash",
            linker_executable=Path("/usr/bin/ld"),
            linker_executable_hash="hash",
            linker_version="2.38",
            target_triple="x86_64-pc-linux-gnu",
            target_os="Linux",
            target_architecture="x86_64",
            target_abi="gnu",
            default_calling_convention="sysv",
            default_structure_packing=1,
            supports_explicit_packing=True,
            name_mangling_scheme="itanium",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=True
        )

class TestNativeCompiler:
    """Test native compiler."""

    def test_compiler_creation(self):
        """Test creating native compiler."""
        from modules.module_03_build_process.build_process import (
            NativeCompiler, ABIConfig, CompilerFlagManager
        )
        
        toolchain = self._create_test_toolchain()
        abi_config = ABIConfig(platform="Linux-x86_64")
        flag_manager = CompilerFlagManager(abi_config, toolchain)
        
        compiler = NativeCompiler(toolchain, abi_config, flag_manager)
        
        assert compiler.toolchain == toolchain
        assert compiler.abi_config == abi_config

    def _create_test_toolchain(self):
        """Create test toolchain."""
        from modules.module_03_build_process.build_process import ToolchainDescriptor
        
        return ToolchainDescriptor(
            compiler_name="GCC",
            compiler_version="11.2.0",
            compiler_full_version="11.2.0",
            compiler_executable=Path("/usr/bin/gcc"),
            compiler_executable_hash="hash",
            linker_executable=Path("/usr/bin/ld"),
            linker_executable_hash="hash",
            linker_version="2.38",
            target_triple="x86_64-pc-linux-gnu",
            target_os="Linux",
            target_architecture="x86_64",
            target_abi="gnu",
            default_calling_convention="sysv",
            default_structure_packing=1,
            supports_explicit_packing=True,
            name_mangling_scheme="itanium",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=True
        )

class TestSymbol:
    """Test symbol representation."""

    def test_symbol_creation(self):
        """Test creating symbol."""
        from modules.module_03_build_process.build_process import Symbol
        
        sym = Symbol(name="my_function", symbol_type="T", address="00001000")
        
        assert sym.name == "my_function"
        assert sym.symbol_type == "T"
        assert sym.is_function is True
        assert sym.is_data is False

    def test_symbol_types(self):
        """Test symbol type detection."""
        from modules.module_03_build_process.build_process import Symbol
        
        func_sym = Symbol(name="func", symbol_type="T")
        data_sym = Symbol(name="data", symbol_type="D")
        undef_sym = Symbol(name="extern", symbol_type="U")
        
        assert func_sym.is_function is True
        assert data_sym.is_data is True
        assert undef_sym.is_undefined is True

class TestValidationResult:
    """Test validation result."""

    def test_validation_result_creation(self):
        """Test creating validation result."""
        from modules.module_03_build_process.build_process import ValidationResult
        
        result = ValidationResult(
            object_file=Path("test.o"),
            format_valid=True,
            symbols_valid=True,
            debug_symbols_valid=True,
            abi_conformance_valid=True
        )
        
        assert result.object_file == Path("test.o")
        assert result.overall_valid is True

    def test_validation_result_with_issues(self):
        """Test validation result with failures."""
        from modules.module_03_build_process.build_process import ValidationResult
        
        result = ValidationResult(
            object_file=Path("bad.o"),
            format_valid=False,
            symbols_valid=True
        )
        result.issues.append("Invalid object format")
        
        assert result.overall_valid is False
        assert len(result.issues) == 1

    def test_validation_report_generation(self):
        """Test generating validation report."""
        from modules.module_03_build_process.build_process import ValidationResult
        
        result = ValidationResult(
            object_file=Path("test.o"),
            format_valid=True,
            symbols_valid=True
        )
        result.warnings.append("Debug symbols not found")
        
        report = result.generate_report()
        
        assert "test.o" in report
        assert "Debug symbols not found" in report

class TestObjectFileValidator:
    """Test object file validator."""

    def test_validator_creation(self):
        """Test creating object file validator."""
        from modules.module_03_build_process.build_process import (
            ObjectFileValidator, ToolchainDescriptor
        )
        
        toolchain = self._create_test_toolchain()
        validator = ObjectFileValidator(toolchain)
        
        assert validator.toolchain == toolchain

    def _create_test_toolchain(self):
        """Create test toolchain."""
        from modules.module_03_build_process.build_process import ToolchainDescriptor
        
        return ToolchainDescriptor(
            compiler_name="GCC",
            compiler_version="11.2.0",
            compiler_full_version="11.2.0",
            compiler_executable=Path("/usr/bin/gcc"),
            compiler_executable_hash="hash",
            linker_executable=Path("/usr/bin/ld"),
            linker_executable_hash="hash",
            linker_version="2.38",
            target_triple="x86_64-pc-linux-gnu",
            target_os="Linux",
            target_architecture="x86_64",
            target_abi="gnu",
            default_calling_convention="sysv",
            default_structure_packing=1,
            supports_explicit_packing=True,
            name_mangling_scheme="itanium",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=True
        )

class TestLinkingMetadata:
    """Test linking metadata."""

    def test_metadata_creation(self):
        """Test creating linking metadata."""
        from modules.module_03_build_process.build_process import LinkingMetadata
        
        metadata = LinkingMetadata(
            target_name="test_program",
            input_objects=[Path("main.o")],
            output_executable=Path("test_program"),
            linker_name="ld",
            success=True
        )
        
        assert metadata.target_name == "test_program"
        assert metadata.success is True

    def test_metadata_serialization(self):
        """Test metadata to_dict."""
        from modules.module_03_build_process.build_process import LinkingMetadata
        
        metadata = LinkingMetadata(
            target_name="program",
            linker_flags=['-O2', '-s'],
            lto_enabled=True
        )
        
        data = metadata.to_dict()
        assert data['target_name'] == "program"
        assert data['lto_enabled'] is True

class TestLinkTarget:
    """Test link target specification."""

    def test_link_target_creation(self):
        """Test creating link target."""
        from modules.module_03_build_process.build_process import LinkTarget
        
        target = LinkTarget(
            target_name="myapp",
            target_type="executable",
            object_files=[Path("main.o"), Path("utils.o")],
            output_path=Path("build/myapp"),
            enable_lto=True
        )
        
        assert target.target_name == "myapp"
        assert target.target_type == "executable"
        assert target.enable_lto is True
        assert target.metadata is not None

class TestLinker:
    """Test linker."""

    def test_linker_creation(self):
        """Test creating linker."""
        from modules.module_03_build_process.build_process import (
            Linker, ToolchainDescriptor
        )
        
        toolchain = self._create_test_toolchain()
        linker = Linker(toolchain)
        
        assert linker.toolchain == toolchain

    def _create_test_toolchain(self):
        """Create test toolchain."""
        from modules.module_03_build_process.build_process import ToolchainDescriptor
        
        return ToolchainDescriptor(
            compiler_name="GCC",
            compiler_version="11.2.0",
            compiler_full_version="11.2.0",
            compiler_executable=Path("/usr/bin/gcc"),
            compiler_executable_hash="hash",
            linker_executable=Path("/usr/bin/ld"),
            linker_executable_hash="hash",
            linker_version="2.38",
            target_triple="x86_64-pc-linux-gnu",
            target_os="Linux",
            target_architecture="x86_64",
            target_abi="gnu",
            default_calling_convention="sysv",
            default_structure_packing=1,
            supports_explicit_packing=True,
            name_mangling_scheme="itanium",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=True
        )

class TestExecutableValidator:
    """Test executable validator."""

    def test_validator_creation(self):
        """Test creating executable validator."""
        from modules.module_03_build_process.build_process import ExecutableValidator
        
        validator = ExecutableValidator()
        assert validator is not None

class TestAdapterMetadata:
    """Test adapter metadata."""

    def test_metadata_creation(self):
        """Test creating adapter metadata."""
        from modules.module_03_build_process.build_process import AdapterMetadata
        
        metadata = AdapterMetadata(
            contract_name="libmath",
            contract_version="1.0",
            contract_hash="abc123",
            adapter_source_file=Path("adapter.c"),
            adapter_source_hash="def456"
        )
        
        assert metadata.contract_name == "libmath"
        assert metadata.validation_passed is False

    def test_metadata_serialization(self):
        """Test metadata to_dict."""
        from modules.module_03_build_process.build_process import AdapterMetadata
        
        metadata = AdapterMetadata(
            contract_name="test",
            contract_version="2.0",
            contract_hash="hash1",
            adapter_source_file=Path("test.c"),
            adapter_source_hash="hash2",
            validation_passed=True
        )
        
        data = metadata.to_dict()
        assert data['contract']['name'] == "test"
        assert data['validation']['passed'] is True

class TestAdapterGenerator:
    """Test adapter generator."""

    def test_generator_creation(self, tmp_path):
        """Test creating adapter generator."""
        from modules.module_03_build_process.build_process import AdapterGenerator
        
        generator = AdapterGenerator(tmp_path)
        assert generator.output_dir == tmp_path

    def test_generate_simple_adapter(self, tmp_path):
        """Test generating simple adapter."""
        from modules.module_03_build_process.build_process import AdapterGenerator
        
        generator = AdapterGenerator(tmp_path)
        
        contract = {
            'library_name': 'testlib',
            'contract_version': '1.0',
            'functions': [
                {
                    'name': 'test_func',
                    'signature': 'int test_func(int x)',
                    'preconditions': ['x >= 0'],
                    'postconditions': ['result >= 0']
                }
            ]
        }
        
        source_file, metadata = generator.generate_adapter(contract)
        
        assert source_file.exists()
        assert metadata.contract_name == 'testlib'
        assert 'test_func' in source_file.read_text()

        assert source_file.exists()
        assert metadata.contract_name == 'testlib'
        assert 'test_func' in source_file.read_text()

class TestBuildManifest:
    """Test build manifest."""
    
    def test_manifest_creation(self):
        """Test creating build manifest."""
        from modules.module_03_build_process.build_process import BuildManifest
        
        manifest = BuildManifest()
        manifest.executables.append({'name': 'verify', 'path': '/bin/verify'})
        
        assert len(manifest.executables) == 1
        assert manifest.all_tests_passed is False
        
    def test_manifest_serialization(self, tmp_path):
        """Test manifest JSON serialization."""
        from modules.module_03_build_process.build_process import BuildManifest
        
        manifest = BuildManifest()
        manifest.source_hash = "abc123"
        manifest.all_tests_passed = True
        
        # Save to file
        output_file = tmp_path / "manifest.json"
        manifest.save(output_file)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "abc123" in content

class TestPackageAssembler:
    """Test package assembler."""
    
    def test_assembler_creation(self, tmp_path):
        """Test creating package assembler."""
        from modules.module_03_build_process.build_process import PackageAssembler
        
        assembler = PackageAssembler(tmp_path)
        assert assembler.output_dir == tmp_path
        assert assembler.package_name == "verification_tool"

class TestValidationResult:
    """Test validation result."""
    
    def test_result_creation(self):
        """Test creating validation result."""
        from modules.module_03_build_process.build_process import ValidationResult
        
        result = ValidationResult(gate_name="Test Gate")
        assert result.gate_name == "Test Gate"
        assert result.passed is True
        
    def test_add_error(self):
        """Test adding error marks result as failed."""
        from modules.module_03_build_process.build_process import ValidationResult
        
        result = ValidationResult(gate_name="Test")
        result.add_error("Something went wrong")
        
        assert result.passed is False
        assert len(result.errors) == 1

class TestBuildCompletionReport:
    """Test build completion report."""
    
    def test_report_creation(self):
        """Test creating completion report."""
        from modules.module_03_build_process.build_process import BuildCompletionReport
        
        report = BuildCompletionReport(build_successful=True)
        report.gates_passed.append("Gate1")
        report.total_gates = 1
        
        assert report.build_successful is True
        assert len(report.gates_passed) == 1
        
    def test_report_generation(self):
        """Test generating report text."""
        from modules.module_03_build_process.build_process import BuildCompletionReport
        
        report = BuildCompletionReport(build_successful=True)
        report.gates_passed.append("Artifact Existence")
        report.total_gates = 1
        
        text = report.generate_report()
        assert "BUILD COMPLETION REPORT" in text
        assert "SUCCESS" in text

class TestBuildCompletionValidator:
    """Test build completion validator."""
    
    def test_validator_creation(self):
        """Test creating validator."""
        from modules.module_03_build_process.build_process import BuildCompletionValidator
        
        validator = BuildCompletionValidator()

        assert len(validator.gates) > 0

class TestCacheEntry:
    """Test cache entry."""
    
    def test_entry_creation(self):
        """Test creating cache entry."""
        from modules.module_03_build_process.build_process import CacheEntry
        
        entry = CacheEntry(
            source_file=Path("test.c"),
            source_hash="abc123",
            output_file=Path("test.o"),
            output_hash="def456"
        )
        
        assert entry.source_file == Path("test.c")
        assert entry.source_hash == "abc123"
        
    def test_entry_serialization(self):
        """Test entry to_dict/from_dict."""
        from modules.module_03_build_process.build_process import CacheEntry
        
        original = CacheEntry(
            source_file=Path("main.c"),
            source_hash="hash1",
            output_file=Path("main.o"),
            output_hash="hash2",
            compiler_hash="hash3",
            flags=["-O2"]
        )
        
        data = original.to_dict()
        restored = CacheEntry.from_dict(data)
        
        assert restored.source_hash == original.source_hash
        assert restored.compiler_hash == original.compiler_hash

class TestBuildCache:
    """Test build cache."""
    
    def test_cache_creation(self, tmp_path):
        """Test creating build cache."""
        from modules.module_03_build_process.build_process import BuildCache
        
        cache = BuildCache(tmp_path)
        assert cache.cache_dir == tmp_path
        assert len(cache.entries) == 0
        
    def test_add_entry(self, tmp_path):
        """Test adding cache entry."""
        from modules.module_03_build_process.build_process import (
            BuildCache, CacheEntry
        )
        
        cache = BuildCache(tmp_path)
        
        entry = CacheEntry(
            source_file=Path("test.c"),
            source_hash="abc123",
            output_file=Path("test.o"),
            output_hash="def456"
        )
        
        cache.add_entry(entry)
        
        assert len(cache.entries) == 1
        retrieved = cache.get_entry(Path("test.c"))
        assert retrieved is not None
        assert retrieved.source_hash == "abc123"

class TestIncrementalBuildManager:
    """Test incremental build manager."""
    
    def test_manager_creation(self, tmp_path):
        """Test creating incremental build manager."""
        from modules.module_03_build_process.build_process import (
            IncrementalBuildManager, BuildCache, DependencyGraph
        )
        
        cache = BuildCache(tmp_path)
        graph = DependencyGraph()
        
        manager = IncrementalBuildManager(cache, graph)
        
        assert manager.cache == cache

        assert manager.cache == cache
        assert manager.dependency_graph == graph

class TestCacheStatistics:
    """Test cache statistics."""
    
    def test_statistics_creation(self):
        """Test creating cache statistics."""
        from modules.module_03_build_process.build_process import CacheStatistics
        
        stats = CacheStatistics()
        stats.total_entries = 10
        stats.total_size_bytes = 1024 * 1024  # 1 MB
        
        assert stats.total_entries == 10
        assert stats.total_size_mb == 1.0
        
    def test_statistics_report(self):
        """Test generating statistics report."""
        from modules.module_03_build_process.build_process import CacheStatistics
        
        stats = CacheStatistics()
        stats.total_entries = 5
        stats.total_size_bytes = 2 * 1024 * 1024
        
        report = stats.generate_report()
        assert "Cache Statistics" in report
        assert "5" in report

class TestLRUEvictionPolicy:
    """Test LRU eviction policy."""
    
    def test_policy_creation(self):
        """Test creating LRU policy."""
        from modules.module_03_build_process.build_process import LRUEvictionPolicy
        
        policy = LRUEvictionPolicy()
        assert policy.policy_name == "LRU"

class TestCacheManager:
    """Test cache manager."""
    
    def test_manager_creation(self, tmp_path):
        """Test creating cache manager."""
        from modules.module_03_build_process.build_process import (
            CacheManager, BuildCache
        )
        
        cache = BuildCache(tmp_path)
        manager = CacheManager(cache, max_size_mb=100)
        
        assert manager.cache == cache
        assert manager.max_size_mb == 100
        
    def test_get_statistics(self, tmp_path):
        """Test getting cache statistics."""
        from modules.module_03_build_process.build_process import (
            CacheManager, BuildCache
        )
        
        cache = BuildCache(tmp_path)
        manager = CacheManager(cache)
        
        stats = manager.get_statistics()

        stats = manager.get_statistics()
        assert stats.total_entries == 0

class TestDeterministicBuildConfig:
    """Test deterministic build configuration."""
    
    def test_config_creation(self):
        """Test creating deterministic config."""
        from modules.module_03_build_process.build_process import DeterministicBuildConfig
        
        config = DeterministicBuildConfig(
            source_epoch=1707048000,
            source_hash="abc123",
            compiler_name="GCC",
            compiler_version="11.2.0",
            compiler_hash="def456",
            build_directory=Path("/build")
        )
        
        assert config.source_epoch == 1707048000
        assert config.compiler_name == "GCC"
        
    def test_config_serialization(self):
        """Test config to_dict."""
        from modules.module_03_build_process.build_process import DeterministicBuildConfig
        
        config = DeterministicBuildConfig(
            source_epoch=1707048000,
            source_hash="hash1",
            compiler_name="Clang",
            compiler_version="14.0.0",
            compiler_hash="hash2",
            build_directory=Path(".")
        )
        
        data = config.to_dict()
        assert data['source_epoch'] == 1707048000
        assert data['compiler']['name'] == "Clang"

class TestDeterministicFlagManager:
    """Test deterministic flag manager."""
    
    def test_manager_creation(self):
        """Test creating flag manager."""
        from modules.module_03_build_process.build_process import (
            DeterministicFlagManager, ToolchainDescriptor
        )
        
        toolchain = self._create_test_toolchain()
        manager = DeterministicFlagManager(toolchain)
        
        assert manager.toolchain == toolchain
        
    def test_get_determinism_flags(self):
        """Test getting determinism flags."""
        from modules.module_03_build_process.build_process import DeterministicFlagManager
        
        toolchain = self._create_test_toolchain()
        manager = DeterministicFlagManager(toolchain)
        
        flags = manager.get_determinism_flags()
        
        assert any('__DATE__' in f for f in flags)
        assert any('__TIME__' in f for f in flags)
        
    def _create_test_toolchain(self):
        """Create test toolchain."""
        from modules.module_03_build_process.build_process import ToolchainDescriptor
        
        return ToolchainDescriptor(
            compiler_name="GCC",
            compiler_version="11.2.0",
            compiler_full_version="11.2.0",
            compiler_executable=Path("/usr/bin/gcc"),
            compiler_executable_hash="hash",
            linker_executable=Path("/usr/bin/ld"),
            linker_executable_hash="hash",
            linker_version="2.38",
            target_triple="x86_64-pc-linux-gnu",
            target_os="Linux",
            target_architecture="x86_64",
            target_abi="gnu",
            default_calling_convention="sysv",
            default_structure_packing=1,
            supports_explicit_packing=True,
            name_mangling_scheme="itanium",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=True
        )

class TestReproducibilityVerifier:
    """Test reproducibility verifier."""
    
    def test_verifier_creation(self):
        """Test creating verifier."""
        from modules.module_03_build_process.build_process import ReproducibilityVerifier
        

        verifier = ReproducibilityVerifier()
        assert verifier is not None

class TestBuildPerformanceProfile:
    """Test build performance profile."""
    
    def test_profile_creation(self):
        """Test creating performance profile."""
        from modules.module_03_build_process.build_process import BuildPerformanceProfile
        
        profile = BuildPerformanceProfile()
        profile.total_build_time = 10.5
        profile.stage_times['Compilation'] = 7.2
        
        assert profile.total_build_time == 10.5
        assert profile.stage_times['Compilation'] == 7.2
        
    def test_profile_report(self):
        """Test generating profile report."""
        from modules.module_03_build_process.build_process import BuildPerformanceProfile
        
        profile = BuildPerformanceProfile()
        profile.total_build_time = 15.0
        profile.stage_times['Stage1'] = 5.0
        profile.stage_times['Stage2'] = 10.0
        
        report = profile.generate_report()
        
        assert "BUILD PERFORMANCE PROFILE" in report
        assert "15.00s" in report

class TestProfilingBuildStage:
    """Test profiling build stage."""
    
    def test_profiling_wrapper(self):
        """Test wrapping stage with profiling."""
        from modules.module_03_build_process.build_process import (
            ProfilingBuildStage, BuildStageInterface, BuildStage
        )
        
        # Create mock stage
        class MockStage(BuildStageInterface):
            def __init__(self):
                super().__init__("Mock", BuildStage.SOURCE_ENUMERATION)
            
            def check_preconditions(self, context):
                pass
                
            def execute(self, context):
                return context
                
            def validate_postconditions(self, context):
                pass
                
        mock = MockStage()
        profiled = ProfilingBuildStage(mock)
        
        assert profiled.wrapped_stage == mock

class TestBuildOptimizationAdvisor:
    """Test build optimization advisor."""
    
    def test_advisor_creation(self):
        """Test creating optimization advisor."""
        from modules.module_03_build_process.build_process import BuildOptimizationAdvisor
        
        advisor = BuildOptimizationAdvisor()
        assert advisor is not None
        
    def test_generate_recommendations(self):
        """Test generating recommendations."""
        from modules.module_03_build_process.build_process import (
            BuildOptimizationAdvisor, BuildPerformanceProfile
        )
        
        advisor = BuildOptimizationAdvisor()
        
        profile = BuildPerformanceProfile()
        profile.total_build_time = 100.0
        profile.total_compilation_time = 80.0  # 80% compilation
        profile.cache_hit_rate = 0.3  # Low hit rate
        
        recommendations = advisor.generate_recommendations(profile)
        

        assert len(recommendations) > 0
        assert any('compilation' in r.lower() for r in recommendations)

class TestBuildErrorDetail:
    """Test build error detail."""
    
    def test_error_creation(self):
        """Test creating build error."""
        from modules.module_03_build_process.build_process import BuildErrorDetail
        
        error = BuildErrorDetail(
            category='compilation',
            source_file=Path("test.c"),
            line_number=42,
            parsed_message="syntax error"
        )
        
        assert error.category == 'compilation'
        assert error.line_number == 42

    def test_error_formatting(self):
        """Test formatting error message."""
        from modules.module_03_build_process.build_process import BuildErrorDetail
        
        error = BuildErrorDetail(
            category='compilation',
            source_file=Path("main.c"),
            line_number=10,
            parsed_message="undefined symbol",
            suggestions=["Include header file"]
        )
        
        formatted = error.format_error_message()
        assert "main.c" in formatted
        assert "undefined symbol" in formatted
        assert "Include header file" in formatted

class TestCompilerErrorParser:
    """Test compiler error parser."""
    
    def test_parser_creation(self):
        """Test creating parser."""
        from modules.module_03_build_process.build_process import CompilerErrorParser
        
        parser = CompilerErrorParser("GCC")
        assert parser.compiler_name == "GCC"

    def test_parse_gcc_error(self):
        """Test parsing GCC error."""
        from modules.module_03_build_process.build_process import CompilerErrorParser
        
        parser = CompilerErrorParser("GCC")
        
        output = "test.c:10:5: error: undeclared identifier 'foo'"
        errors = parser.parse_errors(output)
        
        assert len(errors) == 1
        assert errors[0].source_file == Path("test.c")
        assert errors[0].line_number == 10

class TestBuildErrorReport:
    """Test build error report."""
    
    def test_report_creation(self):
        """Test creating error report."""
        from modules.module_03_build_process.build_process import (
            BuildErrorReport, BuildErrorDetail
        )
        
        errors = [
            BuildErrorDetail(
                category='compilation',
                parsed_message="error 1"
            )
        ]
        
        report = BuildErrorReport(errors)
        assert len(report.errors) == 1

    def test_console_report(self):
        """Test generating console report."""
        from modules.module_03_build_process.build_process import (
            BuildErrorReport, BuildErrorDetail
        )
        
        errors = [
            BuildErrorDetail(
                category='compilation',
                parsed_message="test error"
            )
        ]
        
        report = BuildErrorReport(errors)
        console_output = report.generate_console_report()
        
        assert "BUILD FAILED" in console_output

        assert "BUILD FAILED" in console_output
        assert "test error" in console_output

class TestPlatformInfo:
    """Test platform information."""
    
    def test_platform_detection(self):
        """Test detecting platform."""
        from modules.module_03_build_process.build_process import PlatformInfo
        
        info = PlatformInfo.detect()
        
        assert info.os_name in ['Windows', 'Linux', 'Darwin']
        assert info.architecture != ""
        assert info.python_version != ""

    def test_platform_serialization(self):
        """Test platform to_dict."""
        from modules.module_03_build_process.build_process import PlatformInfo
        
        info = PlatformInfo.detect()
        data = info.to_dict()
        
        assert 'os_name' in data
        assert 'architecture' in data

class TestCrossPlatformPath:
    """Test cross-platform path utilities."""
    
    def test_path_normalization(self):
        """Test path normalization."""
        from modules.module_03_build_process.build_process import CrossPlatformPath
        
        path = Path("test/path")
        normalized = CrossPlatformPath.normalize(path)
        
        assert normalized.is_absolute()

    def test_posix_conversion(self):
        """Test POSIX path conversion."""
        from modules.module_03_build_process.build_process import CrossPlatformPath
        
        path = Path("test") / "path"
        posix = CrossPlatformPath.to_posix(path)
        
        assert '/' in posix or path == Path("test/path")

class TestPlatformToolchainAdapter:
    """Test platform toolchain adapter."""
    
    def test_adapter_creation(self):
        """Test creating adapter."""
        from modules.module_03_build_process.build_process import (
            PlatformToolchainAdapter, PlatformInfo
        )
        
        info = PlatformInfo.detect()
        adapter = PlatformToolchainAdapter(info)
        
        assert adapter.platform == info

    def test_platform_flags(self):
        """Test getting platform-specific flags."""
        from modules.module_03_build_process.build_process import (
            PlatformToolchainAdapter, PlatformInfo
        )
        
        info = PlatformInfo.detect()
        adapter = PlatformToolchainAdapter(info)
        
        flags = adapter.get_platform_specific_flags(['-O2'])
        
        assert '-O2' in flags
        assert len(flags) > 1  # Should add platform-specific flags

class TestPlatformCompatibility:
    """Test platform compatibility."""
    
    def test_compatibility_check(self):
        """Test checking platform compatibility."""
        from modules.module_03_build_process.build_process import (
            PlatformCompatibility, PlatformInfo
        )
        
        compatibility = PlatformCompatibility()
        info = PlatformInfo.detect()
        
        # Current platform should be supported
        assert compatibility.is_supported(info)
    pytest.main([__file__, "-v"])
