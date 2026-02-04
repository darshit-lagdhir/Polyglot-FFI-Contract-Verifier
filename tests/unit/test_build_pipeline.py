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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
