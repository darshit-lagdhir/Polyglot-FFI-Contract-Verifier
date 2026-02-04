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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
