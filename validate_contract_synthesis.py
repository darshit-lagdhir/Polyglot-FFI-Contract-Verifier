"""
Validation Script for Contract Synthesis
Tests all 12 requirements for Phase 4.
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

from src.core.execution_context import (
    ExecutionContext, ProvenanceMetadata, PlatformIdentification, 
    CompilerInformation, NativeLibraryInformation, ArtifactPaths,
    TargetLanguageRuntime, VerificationConfiguration
)
from src.synthesis.contract_synthesizer import ContractSynthesizer

def create_mock_ir(temp_dir: str) -> Dict[str, Any]:
    """Create a sample normalized IR for testing."""
    return {
        "provenance": {
            "producing_phase": "Phase 3: Intermediate Representation Normalization",
            "execution_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "platform": {
            "os_name": "Windows",
            "architecture": "AMD64",
            "pointer_width": 64,
            "endianness": "little"
        },
        "functions": [
            {
                "name": "add",
                "return_type_id": "primitive:int32",
                "parameters": [
                    {"name": "a", "type_id": "primitive:int32", "qualifiers": {}},
                    {"name": "b", "type_id": "primitive:int32", "qualifiers": {}}
                ],
                "calling_convention": "cdecl"
            },
            {
                "name": "process",
                "return_type_id": "primitive:int32",
                "parameters": [
                    {"name": "cfg", "type_id": "pointer:struct:Config", "qualifiers": {"is_const": True}}
                ],
                "calling_convention": "cdecl"
            },
            {
                "name": "process_optional",
                "return_type_id": "primitive:int32",
                "parameters": [
                    {"name": "optional_cfg", "type_id": "pointer:struct:Config", "qualifiers": {}}
                ],
                "calling_convention": "cdecl"
            },
            {
                "name": "create_config",
                "return_type_id": "pointer:struct:Config",
                "parameters": [],
                "calling_convention": "cdecl"
            },
            {
                "name": "write",
                "return_type_id": "primitive:int32",
                "parameters": [
                    {"name": "buf", "type_id": "pointer:primitive:void", "qualifiers": {}},
                    {"name": "size", "type_id": "primitive:uint64", "qualifiers": {}}
                ],
                "calling_convention": "cdecl"
            }
        ],
        "structs": [
            {
                "name": "Config",
                "type_id": "struct:Config",
                "size_bytes": 16,
                "alignment_bytes": 8,
                "fields": [
                    {"name": "mode", "type_id": "primitive:int32", "offset_bytes": 0},
                    {"name": "data", "type_id": "pointer:primitive:void", "offset_bytes": 8}
                ]
            }
        ],
        "type_registry": {
            "primitive:int32": {"kind": "primitive", "name": "int32"},
            "primitive:uint64": {"kind": "primitive", "name": "uint64"},
            "pointer:struct:Config": {"kind": "pointer", "pointee": "struct:Config"},
            "struct:Config": {
                "kind": "struct",
                "name": "Config",
                "size_bytes": 16,
                "alignment_bytes": 8
            },
            "pointer:primitive:void": {"kind": "pointer", "pointee": "primitive:void"}
        }
    }

def create_mock_context(temp_dir: str, ir_path: str) -> ExecutionContext:
    """Create a mock ExecutionContext."""
    exec_id = str(uuid.uuid4())
    return ExecutionContext(
        platform=PlatformIdentification("Windows", "10", "AMD64", 64, "little"),
        compiler=CompilerInformation("cl", "cl.exe", "19.0", [], [], {}),
        native_library=NativeLibraryInformation("test.lib", "hash", [], [], "test.h"),
        target_runtime=TargetLanguageRuntime("Python", "3.9", "ctypes", sys.executable, {}),
        verification_config=VerificationConfiguration(42, 5, 60, "isolate", "debug"),
        provenance=ProvenanceMetadata("1.0.0", datetime.now(timezone.utc).isoformat(), exec_id, "1.0.0"),
        artifacts=ArtifactPaths(
            temp_dir, 
            os.path.join(temp_dir, "ni.json"), 
            os.path.abspath(ir_path), 
            os.path.join(temp_dir, "contract.json"),
            os.path.join(temp_dir, "test_plan.json"),
            os.path.join(temp_dir, "log.json"),
            os.path.join(temp_dir, "diag.json"),
            os.path.join(temp_dir, "report.txt"),
            os.path.join(temp_dir, "context.json")
        )
    )

def test_all():
    print("Testing Contract Synthesis...")
    temp_dir = tempfile.mkdtemp()
    ir_path = os.path.join(temp_dir, "ir.json")
    
    try:
        # Preparation
        ir_data = create_mock_ir(temp_dir)
        with open(ir_path, "w") as f: json.dump(ir_data, f)
        context = create_mock_context(temp_dir, ir_path)
        
        synthesizer = ContractSynthesizer()
        contract = synthesizer.synthesize(context)
        
        # TEST 1: ExecutionContext Integration
        assert contract["provenance"]["execution_id"] == context.provenance.execution_id
        print("  [PASS] ExecutionContext integration working")
        
        # TEST 2: Simple Function Contract (add)
        add_contract = next(f for f in contract["function_contracts"] if f["function_name"] == "add")
        assert add_contract["return_contract"]["type_id"] == "primitive:int32"
        print("  [PASS] Simple function contract correct")
        
        # TEST 3: Pointer Nullability (process -> cfg)
        process_contract = next(f for f in contract["function_contracts"] if f["function_name"] == "process")
        cfg_contract = next(p for p in process_contract["parameter_contracts"] if p["parameter_name"] == "cfg")
        assert cfg_contract["nullability"] == "non_null"
        print("  [PASS] Pointer nullability derivation correct")
        
        # TEST 4: Optional Parameter (process_optional -> optional_cfg)
        opt_contract = next(f for f in contract["function_contracts"] if f["function_name"] == "process_optional")
        opt_p_contract = next(p for p in opt_contract["parameter_contracts"] if p["parameter_name"] == "optional_cfg")
        assert opt_p_contract["nullability"] == "nullable"
        print("  [PASS] Optional parameter detection working")
        
        # TEST 5: Ownership Transfer (create_config)
        create_contract = next(f for f in contract["function_contracts"] if f["function_name"] == "create_config")
        assert create_contract["return_contract"]["ownership"] == "transferred"
        print("  [PASS] Ownership transfer detection working")
        
        # TEST 6: Buffer-Length Relationship (write -> buf, size)
        write_contract = next(f for f in contract["function_contracts"] if f["function_name"] == "write")
        buf_size_const = next(c for c in write_contract["pre_conditions"] if c["constraint_type"] == "buffer_size")
        assert buf_size_const["target"] == "parameter:buf"
        assert buf_size_const["size_parameter"] == "size"
        print("  [PASS] Buffer-length relationship detected")
        
        # TEST 7: Struct Layout Contract (Config)
        config_contract = next(s for s in contract["struct_contracts"] if s["struct_name"] == "Config")
        assert any(inv["constraint_type"] == "layout_match" for inv in config_contract["invariants"])
        assert any(fc["field_name"] == "mode" for fc in config_contract["field_contracts"])
        print("  [PASS] Struct layout contract correct")
        
        # TEST 8: Conservative Defaults (process -> cfg defaults)
        assert cfg_contract["ownership"] == "borrowed"
        assert cfg_contract["lifetime"] == "call_duration"
        print("  [PASS] Conservative defaults applied correctly")
        
        # TEST 9: Const Qualifier (process -> cfg const)
        try:
            assert cfg_contract["mutability"] == "immutable"
            print("  [PASS] Const qualifier handled correctly")
        except AssertionError:
            print(f"  [FAIL] Mutability was {cfg_contract['mutability']}, expected 'immutable'")
            raise
        
        # TEST 10: Return Error Code (add/process return int)
        try:
            assert any(c["constraint_type"] == "error_code" for c in process_contract["post_conditions"])
            print("  [PASS] Return error code detected")
        except AssertionError:
            print(f"  [FAIL] No error_code constraint found in post_conditions: {process_contract['post_conditions']}")
            raise
        
        # TEST 11: Provenance Metadata
        assert contract["provenance"]["producing_phase"] == "Phase 4: Contract Synthesis"
        assert os.path.abspath(ir_path) in contract["provenance"]["input_artifacts"]
        print("  [PASS] Provenance metadata complete")
        
        # TEST 12: Constraint ID Uniqueness
        all_ids = []
        for f in contract["function_contracts"]:
            all_ids.extend([c["constraint_id"] for c in f["pre_conditions"]])
            all_ids.extend([c["constraint_id"] for c in f["post_conditions"]])
        for g in contract["global_constraints"]:
            all_ids.append(g["constraint_id"])
        
        assert len(all_ids) == len(set(all_ids))
        print("  [PASS] Constraint IDs unique")
        
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
