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
        (tmp_path / "test.c").write_text("int main() {}")
        (tmp_path / "test.h").write_text("#pragma once")
        (tmp_path / "test.py").write_text("print('hello')")
        
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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
