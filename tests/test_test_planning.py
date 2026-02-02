"""
Validation Script for Test Plan Generation
Tests all 12 requirements for Phase 7.
"""

import os
import json
import sys
import uuid
import shutil
import tempfile
from datetime import datetime, timezone

# Ensure we can import from src
sys.path.append(os.getcwd())

from polyglot_ffi_verifier.context import (
    ExecutionContext, ProvenanceMetadata, PlatformIdentification, 
    CompilerInformation, NativeLibraryInformation, ArtifactPaths,
    TargetLanguageRuntime, VerificationConfiguration
)
from polyglot_ffi_verifier.test_planning import TestPlanGenerator

def create_mock_context(temp_dir: str) -> ExecutionContext:
    exec_id = str(uuid.uuid4())
    return ExecutionContext(
        platform=PlatformIdentification("Windows", "10", "AMD64", 64, "little"),
        compiler=CompilerInformation("cl", "cl.exe", "19.0", [], [], {}),
        native_library=NativeLibraryInformation("test.dll", "hash", [], [], "test.h"),
        target_runtime=TargetLanguageRuntime("Python", "3.9", "ctypes", sys.executable, {}),
        verification_config=VerificationConfiguration(42, 5, 60, "isolate", "debug"),
        provenance=ProvenanceMetadata("1.0.0", datetime.now(timezone.utc).isoformat(), exec_id, "1.0.0"),
        artifacts=ArtifactPaths(temp_dir, 
                               os.path.join(temp_dir, "native.json"),
                               os.path.join(temp_dir, "ir.json"),
                               os.path.join(temp_dir, "contract.json"),
                               "", "", "", "", "")
    )

def create_test_artifacts(context: ExecutionContext):
    ir = {
        "platform": {"pointer_width": 64},
        "structs": [{"name": "Config", "fields": [{"name": "mode", "type_id": "primitive:int32", "is_padding": False}]}]
    }
    
    contract = {
        "function_contracts": [
            {
                "function_name": "process",
                "parameter_contracts": [
                    {"parameter_name": "cfg", "type_id": "pointer:struct:Config"}
                ],
                "pre_conditions": [
                    {"constraint_id": "func_process_param_cfg_non_null", "constraint_type": "non_null", "target": "parameter:cfg", "description": "must not be null"},
                    {"constraint_id": "func_process_param_cfg_layout", "constraint_type": "struct_layout", "target": "parameter:cfg", "required_size_bytes": 4}
                ]
            }
        ]
    }
    
    with open(context.artifacts.intermediate_representation_path, 'w') as f:
        json.dump(ir, f)
    with open(context.artifacts.contract_path, 'w') as f:
        json.dump(contract, f)

def test_all():
    print("Testing Test Plan Generation...")
    temp_dir = tempfile.mkdtemp()
    
    try:
        # TEST 1: ExecutionContext Integration
        context = create_mock_context(temp_dir)
        create_test_artifacts(context)
        print("  [PASS] ExecutionContext integration working")
        
        generator = TestPlanGenerator()
        plan = generator.generate(context)
        
        # TEST 2: Positive Test Generation
        pos_tests = [tc for tc in plan["test_cases"] if tc["test_category"] == "positive"]
        assert len(pos_tests) >= 1
        print("  [PASS] Positive test generation correct")
        
        # TEST 3: Negative Test (Null Pointer)
        null_tests = [tc for tc in plan["test_cases"] if tc["test_id"].endswith("violate_func_process_param_cfg_non_null")]
        assert len(null_tests) == 1
        assert null_tests[0]["expected_outcome"]["exception_type"] == "NullPointerViolation"
        print("  [PASS] Negative test (null pointer) generation working")
        
        # TEST 4: Negative Test (Layout)
        layout_tests = [tc for tc in plan["test_cases"] if tc["test_id"].endswith("violate_func_process_param_cfg_layout")]
        assert len(layout_tests) == 1
        assert layout_tests[0]["expected_outcome"]["exception_type"] == "LayoutMismatchError"
        print("  [PASS] Negative test (layout) generation working")
        
        # TEST 5: Boundary Case
        bound_tests = [tc for tc in plan["test_cases"] if tc["test_category"] == "boundary"]
        assert len(bound_tests) >= 1
        print("  [PASS] Boundary value test generation working")
        
        # TEST 6: Coverage Computation
        assert plan["test_suite_metadata"]["constraint_coverage"]["coverage_percentage"] == 100.0
        print("  [PASS] Coverage computation correct (100%)")
        
        # TEST 7: Input Value Generation
        typ_pos = [tc for tc in plan["test_cases"] if tc["test_id"].endswith("positive_typical")][0]
        assert "mode" in typ_pos["inputs"]["cfg"]["value"]
        print("  [PASS] Input value generation working")
        
        # TEST 8: Deterministic Generation
        plan1 = generator.generate(context)
        plan2 = generator.generate(context)
        plan1["provenance"]["timestamp"] = ""
        plan2["provenance"]["timestamp"] = ""
        assert json.dumps(plan1) == json.dumps(plan2)
        print("  [PASS] Deterministic generation verified")
        
        # TEST 9: Priority Assignment
        assert null_tests[0]["priority"] == "critical"
        print("  [PASS] Priority assignment correct")
        
        # TEST 10: Test ID Uniqueness
        ids = [tc["test_id"] for tc in plan["test_cases"]]
        assert len(ids) == len(set(ids))
        print("  [PASS] Test ID uniqueness verified")
        
        # TEST 11: Provenance Metadata
        assert plan["provenance"]["execution_id"] == context.provenance.execution_id
        print("  [PASS] Provenance metadata complete")
        
        # TEST 12: Coverage Map
        assert "func_process_param_cfg_non_null" in plan["constraint_coverage_map"]
        print("  [PASS] Coverage map correctly populated")

        print("\n  [PASS] ALL TESTS PASSED (12/12)")
        return True
    except Exception as e:
        print(f"\n  [FAIL] TEST FAILED: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_all()
