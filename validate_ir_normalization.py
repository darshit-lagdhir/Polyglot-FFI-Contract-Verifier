"""
Validation Script for Intermediate Representation Normalization
Tests all 8 requirements for Phase 3.
"""

import os
import json
import sys
import uuid
import shutil
import tempfile
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, List, Any

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.core.execution_context import (
    ExecutionContext, ProvenanceMetadata, PlatformIdentification, 
    CompilerInformation, NativeLibraryInformation, ArtifactPaths,
    TargetLanguageRuntime, VerificationConfiguration
)
from src.representation.ir_normalizer import IRNormalizer
from src.representation.type_resolver import TypeResolver
from src.representation.qualifier_normalizer import QualifierNormalizer
from src.representation.layout_normalizer import LayoutNormalizer

def create_mock_native_interface() -> Dict[str, Any]:
    """Create a sample native interface artifact for testing."""
    return {
        "provenance": {
            "producing_phase": "Native Interface Ingestion",
            "execution_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_version": "1.0.0",
            "schema_version": "1.0.0",
            "input_artifacts": ["test.h", "test.lib"],
            "compiler_invocation": "clang -m64 test.h"
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
                "return_type": {"kind": "primitive", "name": "int", "size_bytes": 4, "alignment_bytes": 4},
                "parameters": [
                    {
                        "name": "a",
                        "type": {"kind": "primitive", "name": "int", "size_bytes": 4, "alignment_bytes": 4},
                        "qualifiers": []
                    }
                ],
                "calling_convention": "cdecl",
                "source_location": {"file": "test.h", "line": 10, "column": 5}
            }
        ],
        "structs": [
            {
                "name": "Config",
                "size_bytes": 16,
                "alignment_bytes": 8,
                "fields": [
                    {
                        "name": "mode",
                        "offset_bytes": 0,
                        "type": {"kind": "primitive", "name": "int", "size_bytes": 4, "alignment_bytes": 4}
                    },
                    {
                        "name": "__padding_1",
                        "offset_bytes": 4,
                        "is_implicit": True,
                        "type": {"kind": "padding", "size_bytes": 4}
                    },
                    {
                        "name": "data",
                        "offset_bytes": 8,
                        "type": {
                            "kind": "pointer",
                            "size_bytes": 8,
                            "alignment_bytes": 8,
                            "pointee": {"kind": "primitive", "name": "void"}
                        }
                    }
                ],
                "source_location": {"file": "test.h", "line": 20, "column": 1}
            }
        ],
        "enums": [
            {
                "name": "Status",
                "underlying_type": {"kind": "primitive", "name": "int", "size_bytes": 4, "alignment_bytes": 4},
                "values": [{"name": "OK", "value": 0}],
                "source_location": {"file": "test.h", "line": 30, "column": 1}
            }
        ]
    }

def create_mock_context(temp_dir: str, ni_path: str) -> ExecutionContext:
    """Create a mock ExecutionContext manually."""
    exec_id = str(uuid.uuid4())
    return ExecutionContext(
        platform=PlatformIdentification(
            os_name="Windows",
            os_version="10",
            architecture="AMD64",
            pointer_width=64,
            endianness="little"
        ),
        compiler=CompilerInformation(
            compiler_name="MSVC",
            compiler_path="C:\\mock\\cl.exe",
            compiler_version="19.28",
            compiler_flags=[],
            include_paths=[],
            preprocessor_macros={}
        ),
        native_library=NativeLibraryInformation(
            library_path=os.path.join(temp_dir, "test.lib"),
            library_hash="mock_hash",
            library_load_paths=[],
            additional_dependencies=[],
            interface_header_path=os.path.join(temp_dir, "test.h")
        ),
        target_runtime=TargetLanguageRuntime(
            language_name="Python",
            language_version="3.9",
            ffi_mechanism="ctypes",
            runtime_path=sys.executable,
            runtime_config={}
        ),
        verification_config=VerificationConfiguration(
            random_seed=42,
            per_test_timeout_seconds=5,
            total_timeout_seconds=60,
            crash_handling_mode="isolate",
            verbosity_level="debug"
        ),
        provenance=ProvenanceMetadata(
            schema_version="1.0.0",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            execution_id=exec_id,
            tool_version="1.0.0"
        ),
        artifacts=ArtifactPaths(
            working_directory=temp_dir,
            native_interface_path=os.path.abspath(ni_path),
            intermediate_representation_path=os.path.join(temp_dir, "ir.json"),
            contract_path=os.path.join(temp_dir, "contract.json"),
            test_plan_path=os.path.join(temp_dir, "test_plan.json"),
            execution_log_path=os.path.join(temp_dir, "log.json"),
            diagnostics_path=os.path.join(temp_dir, "diag.json"),
            report_path=os.path.join(temp_dir, "report.txt"),
            execution_context_path=os.path.join(temp_dir, "context.json")
        )
    )

def test_execution_context_integration():
    """TEST 1: Verify normalizer respects platform information."""
    print("Testing ExecutionContext Integration...")
    temp_dir = tempfile.mkdtemp()
    it_ni = os.path.join(temp_dir, "test_ni_1.json")
    try:
        mock_ni = create_mock_native_interface()
        with open(it_ni, "w") as f: json.dump(mock_ni, f)
            
        context = create_mock_context(temp_dir, it_ni)
        
        normalizer = IRNormalizer()
        ir = normalizer.normalize(context)
        
        assert ir["platform"]["os_name"] == "Windows"
        assert ir["provenance"]["execution_id"] == context.provenance.execution_id
        
        print("  [PASS] ExecutionContext integration working")
        return True
    except Exception as e:
        print(f"  [FAIL] ExecutionContext integration failed: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_type_registry_construction():
    """TEST 2: Verify type_registry is populated correctly with unique IDs."""
    print("Testing Type Registry Construction...")
    try:
        resolver = TypeResolver({"pointer_width": 64})
        registry = {}
        
        # Primitive
        t1 = {"kind": "primitive", "name": "int", "size_bytes": 4}
        id1 = resolver.resolve_type(t1, registry)
        assert id1 == "primitive:int32"
        
        # Pointer to same primitive
        t2 = {"kind": "pointer", "pointee": t1, "size_bytes": 8}
        id2 = resolver.resolve_type(t2, registry)
        assert id2 == "pointer:primitive:int32"
        
        # Re-resolve same primitive
        id3 = resolver.resolve_type(t1, registry)
        assert id1 == id3
        assert len(registry) == 2
        
        print("  [PASS] Type registry construction correct")
        return True
    except Exception as e:
        print(f"  [FAIL] Type registry construction failed: {e}")
        return False

def test_typedef_resolution():
    """TEST 3: Verify typedef chains resolve to canonical types."""
    print("Testing Typedef Resolution...")
    try:
        resolver = TypeResolver({"pointer_width": 64})
        registry = {}
        
        # typedef int MyInt;
        my_int = {
            "kind": "typedef",
            "name": "MyInt",
            "underlying_type": {"kind": "primitive", "name": "int", "size_bytes": 4}
        }
        
        # typedef MyInt YourInt;
        your_int = {
            "kind": "typedef",
            "name": "YourInt",
            "underlying_type": my_int
        }
        
        type_id = resolver.resolve_type(your_int, registry)
        assert type_id == "primitive:int32"
        assert "YourInt" not in type_id
        
        print("  [PASS] Typedef resolution working")
        return True
    except Exception as e:
        print(f"  [FAIL] Typedef resolution failed: {e}")
        return False

def test_primitive_mapping():
    """TEST 4: Verify canonical primitive mapping for Windows x64."""
    print("Testing Canonical Primitive Mapping...")
    try:
        resolver = TypeResolver({"os_name": "Windows", "architecture": "AMD64", "pointer_width": 64})
        
        # Test Windows x64 'long' (32-bit)
        long_type = {"kind": "primitive", "name": "long"}
        id1 = resolver.resolve_type(long_type, {})
        assert id1 == "primitive:int32"
        
        # Test 'long long' (64-bit)
        ll_type = {"kind": "primitive", "name": "long long"}
        id2 = resolver.resolve_type(ll_type, {})
        assert id2 == "primitive:int64"
        
        # Test 'size_t' (64-bit)
        sz_type = {"kind": "primitive", "name": "size_t"}
        id3 = resolver.resolve_type(sz_type, {})
        assert id3 == "primitive:uint64"
        
        print("  [PASS] Canonical primitive mapping correct")
        return True
    except Exception as e:
        print(f"  [FAIL] Canonical primitive mapping failed: {e}")
        return False

def test_qualifier_normalization():
    """TEST 5: Verify qualifier normalization working."""
    print("Testing Qualifier Normalization...")
    try:
        norm = QualifierNormalizer()
        
        q1 = norm.normalize(["const", "VOLATILE"])
        assert q1["is_const"] is True
        assert q1["is_volatile"] is True
        assert q1["is_restrict"] is False
        
        q2 = norm.normalize([])
        assert all(v is False for v in q2.values())
        
        print("  [PASS] Qualifier normalization working")
        return True
    except Exception as e:
        print(f"  [FAIL] Qualifier normalization failed: {e}")
        return False

def test_struct_layout_preservation():
    """TEST 6: Verify struct layouts preserved with type ID references."""
    print("Testing Struct Layout Preservation...")
    try:
        mock_ni = create_mock_native_interface()
        struct_info = mock_ni["structs"][0]
        
        resolver = TypeResolver(mock_ni["platform"])
        registry = {}
        layout_norm = LayoutNormalizer(resolver)
        
        norm_struct = layout_norm.normalize_struct(struct_info, registry)
        
        assert norm_struct["size_bytes"] == 16
        assert norm_struct["fields"][0]["type_id"] == "primitive:int32"
        assert norm_struct["fields"][1]["type_id"] == "padding:4"
        assert norm_struct["fields"][2]["type_id"] == "pointer:primitive:void"
        
        print("  [PASS] Struct layout preservation correct")
        return True
    except Exception as e:
        print(f"  [FAIL] Struct layout preservation failed: {e}")
        return False

def test_function_normalization():
    """TEST 7: Verify function parameters and return types use IDs."""
    print("Testing Function Normalization...")
    try:
        mock_ni = create_mock_native_interface()
        func_info = mock_ni["functions"][0]
        
        normalizer = IRNormalizer()
        resolver = TypeResolver(mock_ni["platform"])
        registry = {}
        
        norm_func = normalizer._normalize_function(func_info, resolver, registry)
        
        assert norm_func["return_type_id"] == "primitive:int32"
        assert norm_func["parameters"][0]["type_id"] == "primitive:int32"
        assert "qualifiers" in norm_func["parameters"][0]
        
        print("  [PASS] Function normalization working")
        return True
    except Exception as e:
        print(f"  [FAIL] Function normalization failed: {e}")
        return False

def test_provenance_metadata():
    """TEST 8: Verify provenance metadata complete and correct."""
    print("Testing Provenance Metadata...")
    temp_dir = tempfile.mkdtemp()
    it_ni = os.path.join(temp_dir, "test_ni_8.json")
    try:
        mock_ni = create_mock_native_interface()
        with open(it_ni, "w") as f: json.dump(mock_ni, f)
            
        context = create_mock_context(temp_dir, it_ni)
        
        normalizer = IRNormalizer()
        ir = normalizer.normalize(context)
        
        prov = ir["provenance"]
        assert prov["producing_phase"] == "Phase 3: Intermediate Representation Normalization"
        assert prov["execution_id"] == context.provenance.execution_id
        assert os.path.basename(prov["input_artifacts"][0]) == "test_ni_8.json"
        
        print("  [PASS] Provenance metadata complete")
        return True
    except Exception as e:
        print(f"  [FAIL] Provenance metadata failed: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print("=" * 70)
    print("  Intermediate Representation Normalization Validation")
    print("=" * 70)
    print()
    
    tests = [
        test_execution_context_integration,
        test_type_registry_construction,
        test_typedef_resolution,
        test_primitive_mapping,
        test_qualifier_normalization,
        test_struct_layout_preservation,
        test_function_normalization,
        test_provenance_metadata
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
        
    print("=" * 70)
    if passed == len(tests):
        print(f"  [PASS] ALL TESTS PASSED ({passed}/{len(tests)})")
        return 0
    else:
        print(f"  [FAIL] SOME TESTS FAILED ({passed}/{len(tests)} passed)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
