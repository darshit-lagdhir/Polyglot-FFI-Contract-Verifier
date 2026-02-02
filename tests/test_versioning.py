"""
Validation Script for Contract Schema Versioning
Tests all 12 requirements for Phase 5.
"""

import os
import json
import sys
import uuid
import shutil
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Any

# Ensure we can import from src
sys.path.append(os.getcwd())

from polyglot_ffi_verifier.context import (
    ExecutionContext, ProvenanceMetadata, PlatformIdentification, 
    CompilerInformation, NativeLibraryInformation, ArtifactPaths,
    TargetLanguageRuntime, VerificationConfiguration
)
from polyglot_ffi_verifier.versioning import ContractSchemaValidator
from polyglot_ffi_verifier.versioning import ContractComparator
from polyglot_ffi_verifier.versioning import SchemaVersionManager
from polyglot_ffi_verifier.versioning import CompatibilityReportGenerator

def create_base_contract() -> Dict[str, Any]:
    """Returns a basic valid contract."""
    return {
        "provenance": {
            "producing_phase": "Phase 4: Contract Synthesis",
            "execution_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_version": "1.0.0",
            "schema_version": "1.0.0",
            "input_artifacts": []
        },
        "platform": {"os_name": "Windows", "architecture": "AMD64", "pointer_width": 64},
        "function_contracts": [],
        "struct_contracts": [],
        "type_contracts": {},
        "global_constraints": [],
        "synthesis_metadata": {}
    }

def create_mock_context(temp_dir: str) -> ExecutionContext:
    """Create a mock ExecutionContext."""
    exec_id = str(uuid.uuid4())
    return ExecutionContext(
        platform=PlatformIdentification("Windows", "10", "AMD64", 64, "little"),
        compiler=CompilerInformation("cl", "cl.exe", "19.0", [], [], {}),
        native_library=NativeLibraryInformation("test.lib", "hash", [], [], "test.h"),
        target_runtime=TargetLanguageRuntime("Python", "3.9", "ctypes", sys.executable, {}),
        verification_config=VerificationConfiguration(42, 5, 60, "isolate", "debug"),
        provenance=ProvenanceMetadata("1.0.0", datetime.now(timezone.utc).isoformat(), exec_id, "1.0.0"),
        artifacts=ArtifactPaths(temp_dir, "", "", os.path.join(temp_dir, "contract.json"), "", "", "", "", "")
    )

def test_all():
    print("Testing Contract Schema Versioning...")
    temp_dir = tempfile.mkdtemp()
    
    try:
        # TEST 1: Schema Version Validation
        contract = create_base_contract()
        path = os.path.join(temp_dir, "c1.json")
        with open(path, "w") as f: json.dump(contract, f)
        
        validator = ContractSchemaValidator()
        res = validator.validate_contract(path)
        assert res["valid"] == True
        print("  [PASS] Schema version validation working")
        
        # TEST 2: Schema Compatibility Check
        mgr = SchemaVersionManager()
        assert mgr.is_schema_compatible("1.0.0", "1.0.0") == True
        assert mgr.is_schema_compatible("1.0.0", "1.1.0") == True # Minor diff
        assert mgr.is_schema_compatible("1.0.0", "2.0.0") == False # Major diff
        print("  [PASS] Schema compatibility check correct")
        
        # TEST 3: Function Added Detection
        c_base = create_base_contract()
        c_new = create_base_contract()
        c_new["function_contracts"].append({"function_name": "new_func"})
        
        b_path = os.path.join(temp_dir, "baseline.json")
        n_path = os.path.join(temp_dir, "current.json")
        with open(b_path, "w") as f: json.dump(c_base, f)
        with open(n_path, "w") as f: json.dump(c_new, f)
        
        comparator = ContractComparator()
        diff = comparator.compare_contracts(b_path, n_path, "test-exec")
        assert any(c["change_type"] == "function_added" for c in diff["changes"])
        print("  [PASS] Function added detection working")
        
        # TEST 4: Function Removed Detection
        c_new_2 = create_base_contract() # empty
        diff = comparator.compare_contracts(n_path, b_path, "test-exec") # n_path has 1 func
        assert any(c["change_type"] == "function_removed" and c["change_category"] == "breaking" for c in diff["changes"])
        print("  [PASS] Function removed detection working")
        
        # TEST 5: Parameter Type Changed Detection
        c_b = create_base_contract()
        c_b["function_contracts"].append({
            "function_name": "f1",
            "parameter_contracts": [{"parameter_name": "p1", "type_id": "int"}]
        })
        c_n = create_base_contract()
        c_n["function_contracts"].append({
            "function_name": "f1",
            "parameter_contracts": [{"parameter_name": "p1", "type_id": "long"}]
        })
        with open(b_path, "w") as f: json.dump(c_b, f)
        with open(n_path, "w") as f: json.dump(c_n, f)
        diff = comparator.compare_contracts(b_path, n_path, "test-exec")
        assert any(c["change_type"] == "parameter_type_changed" and c["change_category"] == "breaking" for c in diff["changes"])
        print("  [PASS] Parameter type change detection working")
        
        # TEST 6: Struct Field Added Detection
        c_b = create_base_contract()
        c_b["struct_contracts"].append({
            "struct_name": "S1",
            "field_contracts": [{"field_name": "f1", "type_id": "int"}]
        })
        c_n = create_base_contract()
        c_n["struct_contracts"].append({
            "struct_name": "S1",
            "field_contracts": [
                {"field_name": "f1", "type_id": "int"},
                {"field_name": "f2", "type_id": "int"}
            ]
        })
        with open(b_path, "w") as f: json.dump(c_b, f)
        with open(n_path, "w") as f: json.dump(c_n, f)
        diff = comparator.compare_contracts(b_path, n_path, "test-exec")
        assert any(c["change_type"] == "field_added" and c["change_category"] == "potentially_breaking" for c in diff["changes"])
        print("  [PASS] Struct field added detection working")
        
        # TEST 7: Constraint Added Detection
        c_b = create_base_contract()
        c_b["function_contracts"].append({
            "function_name": "f1",
            "parameter_contracts": [{"parameter_name": "p1", "nullability": "nullable"}]
        })
        c_n = create_base_contract()
        c_n["function_contracts"].append({
            "function_name": "f1",
            "parameter_contracts": [{"parameter_name": "p1", "nullability": "non_null"}]
        })
        with open(b_path, "w") as f: json.dump(c_b, f)
        with open(n_path, "w") as f: json.dump(c_n, f)
        diff = comparator.compare_contracts(b_path, n_path, "test-exec")
        assert any(c["change_category"] == "semantic" for c in diff["changes"])
        print("  [PASS] Constraint added detection working")
        
        # TEST 8: Compatibility Level Assessment
        assert diff["summary"]["breaking_changes"] == 0
        assert diff["summary"]["semantic_changes"] > 0
        gen = CompatibilityReportGenerator()
        level = gen._compute_compatibility_level(diff["summary"])
        assert level == "SEMANTICALLY_INCOMPATIBLE"
        print("  [PASS] Compatibility level assessment correct")
        
        # TEST 9: Diff Artifact Generation
        assert "provenance" in diff
        assert diff["provenance"]["execution_id"] == "test-exec"
        print("  [PASS] Diff artifact generation working")
        
        # TEST 10: Compatibility Report Generation
        report = gen.generate_report(diff)
        assert "SEMANTICALLY_INCOMPATIBLE" in report
        assert "[SEMANTIC]" in report
        print("  [PASS] Compatibility report generation working")
        
        # TEST 11: No Changes Detection
        diff_none = comparator.compare_contracts(b_path, b_path, "test-exec")
        assert diff_none["summary"]["total_changes"] == 0
        assert gen._compute_compatibility_level(diff_none["summary"]) == "FULLY_COMPATIBLE"
        print("  [PASS] No changes detection working")
        
        # TEST 12: Provenance Metadata
        assert diff["provenance"]["producing_phase"] == "Phase 5: Contract Schema Versioning"
        print("  [PASS] Provenance metadata complete")
        
        print("\n  [PASS] ALL TESTS PASSED (12/12)")
        return True
    except Exception as e:
        print(f"\n  [FAIL] TEST FAILED: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    if test_all():
        sys.exit(0)
    else:
        sys.exit(1)
