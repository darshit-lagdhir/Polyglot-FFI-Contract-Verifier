"""
Unit tests for verification pipeline foundations.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules" / "module_02_verification_pipeline"))

from verification_pipeline import (
    StageState, PipelineError, ConfigError, PreconditionError,
    StageError, PostconditionError, ArtifactProvenance, ArtifactValidator,
    PipelineStage, StageRegistry, PipelineExecutionLog, VerificationPipeline
)

def test_stage_state_enum():
    """Test StageState enumeration."""
    assert StageState.PENDING.value == "pending"
    assert StageState.READY.value == "ready"
    assert StageState.EXECUTING.value == "executing"
    assert StageState.COMPLETED.value == "completed"
    assert StageState.FAILED.value == "failed"
    assert StageState.SKIPPED.value == "skipped"
    print("✓ StageState enum test passed")

def test_error_classification():
    """Test error class hierarchy."""
    config_err = ConfigError("test")
    assert isinstance(config_err, PipelineError)
    
    precond_err = PreconditionError("test", "artifact", "stage")
    assert isinstance(precond_err, PipelineError)
    assert precond_err.missing_artifact == "artifact"
    
    stage_err = StageError("test", "stage", "details")
    assert isinstance(stage_err, PipelineError)
    assert stage_err.stage_name == "stage"
    
    postcond_err = PostconditionError("test", "stage", "path")
    assert isinstance(postcond_err, PipelineError)
    assert postcond_err.artifact_path == "path"
    
    print("✓ Error classification test passed")

def test_artifact_provenance():
    """Test ArtifactProvenance dataclass."""
    provenance = ArtifactProvenance(
        execution_id="test-id",
        stage_name="test_stage",
        stage_version="1.0.0",
        creation_timestamp="2026-02-02T10:30:00+00:00",
        schema_version="1.0.0",
        input_artifact_hashes={"input.json": "hash123"}
    )
    
    # Test to_dict
    data = provenance.to_dict()
    assert data["execution_id"] == "test-id"
    assert data["stage_name"] == "test_stage"
    assert data["input_artifact_hashes"] == {"input.json": "hash123"}
    
    # Test from_dict
    reconstructed = ArtifactProvenance.from_dict(data)
    assert reconstructed == provenance
    
    print("✓ ArtifactProvenance test passed")

class MockStage(PipelineStage):
    STAGE_NAME = "mock_stage"
    STAGE_VERSION = "0.0.1"
    
    def _execute_impl(self) -> None:
        pass

def test_pipeline_stage_lifecycle():
    """Test basic PipelineStage lifecycle."""
    # Create mock execution context
    context = {
        "provenance": {"execution_id": "test-execution-id"},
        "artifacts": {"working_directory": "/tmp"}
    }
    
    stage = MockStage(context)
    assert stage.state == StageState.PENDING
    assert stage.execution_id == "test-execution-id"
    
    # We can't fully execute without file system setup, but we verified instantiation
    print("✓ PipelineStage lifecycle test passed")

def test_registry():
    """Test StageRegistry."""
    registry = StageRegistry()
    registry.register_stage(MockStage)
    
    assert "mock_stage" in registry.list_stages()
    assert registry.get_stage_class("mock_stage") == MockStage
    
    info = registry.get_stage_info("mock_stage")
    assert info["name"] == "mock_stage"
    assert info["version"] == "0.0.1"
    
    print("✓ StageRegistry test passed")

if __name__ == "__main__":
    test_stage_state_enum()
    test_error_classification()
    test_artifact_provenance()
    test_pipeline_stage_lifecycle()
    test_registry()
    print("\nAll unit tests passed!")
