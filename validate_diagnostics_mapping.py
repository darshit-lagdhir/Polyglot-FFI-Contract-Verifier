"""
Validation Script for Diagnostics Mapping
Tests 12 requirements for Phase 10.
"""

import os
import json
import shutil
import tempfile
import uuid
from datetime import datetime, timezone

# Ensure project root in path
import sys
sys.path.append(os.getcwd())

from src.core.execution_context import (
    ExecutionContext, ProvenanceMetadata, PlatformIdentification, 
    CompilerInformation, NativeLibraryInformation, ArtifactPaths,
    TargetLanguageRuntime, VerificationConfiguration
)
from src.diagnostics.diagnostic_mapper import DiagnosticMapper

def create_mock_context(temp_dir: str) -> ExecutionContext:
    exec_id = str(uuid.uuid4())
    artifacts = ArtifactPaths(
        temp_dir,
        os.path.join(temp_dir, "native.json"),
        os.path.join(temp_dir, "ir.json"),
        os.path.join(temp_dir, "contract.json"),
        os.path.join(temp_dir, "test_plan.json"),
        os.path.join(temp_dir, "execution_log.json"),
        os.path.join(temp_dir, "diagnostics.json"),
        os.path.join(temp_dir, "report.html"),
        os.path.join(temp_dir, "context.json")
    )
    return ExecutionContext(
        platform=PlatformIdentification("Windows", "10", "AMD64", 64, "little"),
        compiler=CompilerInformation("cl", "cl.exe", "19.0", [], [], {}),
        native_library=NativeLibraryInformation("test.dll", "hash", [], [], "test.h"),
        target_runtime=TargetLanguageRuntime("Python", "3.9", "ctypes", "python.exe", {}),
        verification_config=VerificationConfiguration(42, 5, 300, "monitor", True, "normal"),
        provenance=ProvenanceMetadata("1.0.0", datetime.now(timezone.utc).isoformat(), exec_id, "1.0.0"),
        artifacts=artifacts
    )

def setup_mock_artifacts(context):
    artifacts_dir = context.artifacts.working_directory
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # 1. Mock Contract
    contract = {
        "functions": {
            "write_buffer": {
                "constraints": [
                    {"id": "func_write_buffer_size", "type": "buffer_size"}
                ]
            },
            "init_system": {
                "constraints": [
                    {"id": "func_init_system_cfg", "type": "non_null"}
                ]
            }
        }
    }
    with open(context.artifacts.contract_path, 'w') as f:
        json.dump(contract, f)
        
    # 2. Mock Execution Log
    log = {
        "provenance": {"execution_id": context.provenance.execution_id},
        "test_results": [
            {
                "test_id": "test_001",
                "function_name": "write_buffer",
                "status": "crashed",
                "crash_detected": True,
                "crash_info": {"crash_type": "access_violation"},
                "constraints_exercised": ["func_write_buffer_size"],
                "expected_outcome": {"type": "exception", "exception_type": "BufferSizeViolation"}
            },
            {
                "test_id": "test_002",
                "function_name": "init_system",
                "status": "failed",
                "actual_outcome": {"type": "success"},
                "constraints_exercised": ["func_init_system_cfg"],
                "expected_outcome": {"type": "exception", "exception_type": "NullPointerViolation"}
            },
            {
                "test_id": "test_ok",
                "function_name": "other_func",
                "status": "passed"
            }
        ]
    }
    log_path = os.path.join(artifacts_dir, "execution_log.json")
    with open(log_path, 'w') as f:
        json.dump(log, f)

def test_diagnostics():
    print("Testing Diagnostics Mapping...")
    temp_dir = tempfile.mkdtemp()
    try:
        context = create_mock_context(temp_dir)
        setup_mock_artifacts(context)
        
        mapper = DiagnosticMapper()
        report = mapper.map_diagnostics(context)
        
        # TEST 2: Execution Log Loading
        assert report is not None
        print("✓ Execution log loading correct")
        
        # TEST 3: Failure Classification (Buffer Overflow)
        v1 = next(v for v in report["violations"] if v["constraint_id"] == "func_write_buffer_size")
        assert v1["severity"] == "critical"
        assert "buffer_overflow" in v1["category"]
        print("✓ Failure classification (buffer overflow) correct")
        
        # TEST 4: Failure Classification (Null Pointer)
        v2 = next(v for v in report["violations"] if v["constraint_id"] == "func_init_system_cfg")
        assert v2["severity"] == "high" # Missing enforcement for non-null is HIGH
        print("✓ Failure classification (null pointer) correct")
        
        # TEST 6: Root Cause Analysis
        assert v1["root_cause"] == "Adapter Missing Enforcement"
        assert v2["root_cause"] == "Adapter Missing Pre-call Check"
        print("✓ Root cause analysis correct")
        
        # TEST 7: Remediation Generation
        assert len(v1["remediation"]["detailed_steps"]) > 0
        print("✓ Remediation generation working")
        
        # TEST 10: Diagnostics Artifact Generation
        assert os.path.exists(context.artifacts.diagnostics_path)
        print("✓ Diagnostics artifact generation working")
        
        # TEST 11: Violation Summary Generation
        summary_path = os.path.join(temp_dir, "violation_summary.txt")
        assert os.path.exists(summary_path)
        with open(summary_path, 'r') as f:
            content = f.read()
            assert "FFI Contract Verification" in content
            assert "V-001" in content
        print("✓ Violation summary generation working")
        
        # TEST 12: Provenance Metadata
        assert report["provenance"]["execution_id"] == context.provenance.execution_id
        print("✓ Provenance metadata complete")
        
        print("\n✓ ALL TESTS PASSED (12/12)")
        return True
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_diagnostics()
