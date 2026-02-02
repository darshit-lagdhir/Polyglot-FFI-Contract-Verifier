"""
Unit tests for incremental verification and schema features (Module 02 - ).
"""

import os
import sys
import json
import uuid
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules" / "module_02_verification_pipeline"))

from verification_pipeline import (
    ArtifactType, SchemaRegistry, ArtifactSchema, FieldSchema,
    StalenessDetector, StalenessStatus, EnhancedArtifactValidator,
    ArtifactValidator, PipelineStage
)

def test_schema_registry():
    """Test schema registry loading and validation."""
    registry = SchemaRegistry()
    
    # Test built-in schema retrieval
    schema = registry.get_latest_schema(ArtifactType.EXECUTION_CONTEXT)
    assert schema.artifact_type == ArtifactType.EXECUTION_CONTEXT
    assert schema.schema_version == "1.0.0"
    
    print("✓ SchemaRegistry: Loaded built-in schema")
    
    # Test valid artifact
    valid_artifact = {
        "platform": {},
        "compiler": {},
        "native_library": {},
        "target_runtime": {},
        "verification_config": {},
        "provenance": {"schema_version": "1.0.0"},
        "artifacts": {}
    }
    
    errors = schema.validate(valid_artifact)
    assert len(errors) == 0
    print("✓ SchemaRegistry: Valid artifact passed")
    
    # Test invalid artifact (missing field)
    invalid_artifact = {
        "platform": {},
        # Missing compiler
        "native_library": {},
        "target_runtime": {},
        "verification_config": {},
        "provenance": {},
        "artifacts": {}
    }
    
    errors = schema.validate(invalid_artifact)
    assert len(errors) > 0
    assert "Missing required field: compiler" in errors[0]
    print("✓ SchemaRegistry: Invalid artifact caught")

def test_staleness_detector():
    """Test staleness detection logic."""
    
    # Mock stage class
    class MockStage(PipelineStage):
        STAGE_NAME = "mock_stage"
        STAGE_VERSION = "1.0.0"
        REQUIRED_INPUTS = []
        PRODUCED_OUTPUTS = ["output"]
        def _execute_impl(self): pass

    # Create temporary artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.json")
        output_path = os.path.join(tmpdir, "output.json")
        
        # Create input
        with open(input_path, "w") as f:
            json.dump({"data": "input"}, f)
        
        input_hash = ArtifactValidator.compute_artifact_hash(input_path)
        
        # Create output artifact fresh
        output_artifact = {
            "provenance": {
                "execution_id": str(uuid.uuid4()),
                "stage_name": "mock_stage",
                "stage_version": "1.0.0",
                "creation_timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "input_artifact_hashes": {
                    input_path: input_hash
                }
            },
            "data": "output"
        }
        
        with open(output_path, "w") as f:
            json.dump(output_artifact, f)
            
        # Initialize detector
        validator = EnhancedArtifactValidator()
        detector = StalenessDetector(validator)
        
        # Case 1: Fresh
        status = detector.check_staleness(output_path, MockStage)
        if status != StalenessStatus.FRESH:
             print(f"FAILED Case 1: Expected FRESH, got {status}")
        assert status == StalenessStatus.FRESH
        print("✓ StalenessDetector: Fresh artifact detected")
        
        # Case 2: Stale (input changed)
        with open(input_path, "w") as f:
            json.dump({"data": "new_input"}, f) # Hash will change
            
        # Re-compute hash to verify it changed
        new_hash = ArtifactValidator.compute_artifact_hash(input_path)
        if new_hash == input_hash:
             print("WARNING: Hash did not change! Disk I/O lag")
        else:
             print(f"Hash changed: {input_hash} -> {new_hash}")
            
        status = detector.check_staleness(output_path, MockStage)
        if status != StalenessStatus.STALE:
             print(f"FAILED Case 2: Expected STALE, got {status}")
        assert status == StalenessStatus.STALE
        print("✓ StalenessDetector: Stale artifact (input change) detected")
        
        # Case 3: Missing
        status = detector.check_staleness("non_existent.json", MockStage)
        assert status == StalenessStatus.MISSING
        print("✓ StalenessDetector: Missing artifact detected")
        
        # Case 4: Stage version mismatch
        MockStage.STAGE_VERSION = "1.1.0"
        # Restore valid input for this test so we isolate stage version
        with open(input_path, "w") as f:
            json.dump({"data": "input"}, f)
            
        status = detector.check_staleness(output_path, MockStage)
        assert status == StalenessStatus.POTENTIALLY_STALE
        print("✓ StalenessDetector: Version mismatch detected")

if __name__ == "__main__":
    test_schema_registry()
    test_staleness_detector()
    print("\nAll Module 02  tests passed!")
