"""
Unit tests for verification pipeline (Module 02).
Updated for : State Machines & Artifact Validation.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import List

# Add module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules" / "module_02_verification_pipeline"))

from verification_pipeline import (
    StageState, PipelineError, ConfigError, PreconditionError,
    StageError, PostconditionError, ArtifactProvenance, ArtifactValidator,
    PipelineStage, StageRegistry, PipelineExecutionLog, VerificationPipeline,
    SemanticVersion, StateMachineValidator, InvalidStateTransitionError,
    DependencyGraph, EnhancedArtifactValidator, EnhancedVerificationPipeline
)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

def test_stage_state_enum():
    """Test StageState enumeration."""
    assert StageState.PENDING.value == "pending"
    assert StageState.READY.value == "ready"
    assert StageState.EXECUTING.value == "executing"
    assert StageState.COMPLETED.value == "completed"
    assert StageState.FAILED.value == "failed"
    assert StageState.SKIPPED.value == "skipped"
    print("✓ StageState enum test passed")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

def test_semantic_version():
    """Test SemanticVersion parsing and compatibility."""
    # Parsing
    v1 = SemanticVersion.parse("1.2.3")
    assert v1.major == 1 and v1.minor == 2 and v1.patch == 3
    
    # Compatibility
    required = SemanticVersion.parse("1.2.0")
    
    # Exact match compatible
    assert SemanticVersion.parse("1.2.0").is_compatible_with(required)
    
    # Newer patch compatible
    assert SemanticVersion.parse("1.2.9").is_compatible_with(required)
    
    # Newer minor compatible
    assert SemanticVersion.parse("1.3.0").is_compatible_with(required)
    
    # Older minor incompatible
    assert not SemanticVersion.parse("1.1.9").is_compatible_with(required)
    
    # Different major incompatible
    assert not SemanticVersion.parse("2.0.0").is_compatible_with(required)
    
    print("✓ SemanticVersion test passed")

def test_state_machine_validator():
    """Test StateMachineValidator transitions."""
    # Valid transitions
    StateMachineValidator.validate_transition("test", StageState.PENDING, StageState.READY)
    StateMachineValidator.validate_transition("test", StageState.READY, StageState.EXECUTING)
    StateMachineValidator.validate_transition("test", StageState.EXECUTING, StageState.COMPLETED)
    StateMachineValidator.validate_transition("test", StageState.EXECUTING, StageState.FAILED)
    
    # Invalid transition (COMPLETED is terminal)
    try:
        StateMachineValidator.validate_transition("test", StageState.COMPLETED, StageState.EXECUTING)
        assert False, "Should raise InvalidStateTransitionError"
    except InvalidStateTransitionError:
        pass
        
    print("✓ StateMachineValidator test passed")

def test_dependency_graph():
    """Test DependencyGraph topological sort and cycle detection."""
    
    class StageA(PipelineStage):
        STAGE_NAME = "stage_a"
        REQUIRED_INPUTS = []
        PRODUCED_OUTPUTS = ["artifact_a"]
        def _execute_impl(self): pass

    class StageB(PipelineStage):
        STAGE_NAME = "stage_b"
        REQUIRED_INPUTS = ["artifact_a"] # depends on A
        PRODUCED_OUTPUTS = ["artifact_b"]
        def _execute_impl(self): pass
        
    class StageC(PipelineStage):
        STAGE_NAME = "stage_c"
        REQUIRED_INPUTS = ["artifact_b"] # depends on B
        PRODUCED_OUTPUTS = ["artifact_c"]
        def _execute_impl(self): pass

    # Test valid graph
    graph = DependencyGraph([StageC, StageA, StageB]) # Order shouldn't matter
    order = graph.topological_sort()
    
    # A must appear before B, B must appear before C
    assert order.index("stage_a") < order.index("stage_b")
    assert order.index("stage_b") < order.index("stage_c")
    assert graph.detect_cycles() is None
    
    # Test circular dependency
    class StageCycle1(PipelineStage):
        STAGE_NAME = "cycle_1"
        REQUIRED_INPUTS = ["art_2"]
        PRODUCED_OUTPUTS = ["art_1"]
        def _execute_impl(self): pass
        
    class StageCycle2(PipelineStage):
        STAGE_NAME = "cycle_2"
        REQUIRED_INPUTS = ["art_1"]
        PRODUCED_OUTPUTS = ["art_2"]
        def _execute_impl(self): pass
        
    graph_cycle = DependencyGraph([StageCycle1, StageCycle2])
    cycle = graph_cycle.detect_cycles()
    assert cycle is not None
    assert "cycle_1" in cycle and "cycle_2" in cycle
    
    print("✓ DependencyGraph test passed")

if __name__ == "__main__":
    test_stage_state_enum()
    test_semantic_version()
    test_state_machine_validator()
    test_dependency_graph()
    print("\nAll Module 02 tests passed!")
