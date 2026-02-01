"""
Native Interface Ingestion Validation Script

Validates the ingestion layer implementation with comprehensive tests covering:
- ExecutionContext integration
- Header parsing
- Struct layout with padding
- Enum extraction
- Typedef extraction
- Calling convention detection
- Source location tracking
- Provenance metadata
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.execution_context import ExecutionContextBuilder
from ingestion.native_interface_analyzer import NativeInterfaceAnalyzer


def create_test_header(content: str) -> str:
    """Create a temporary test header file."""
    fd, path = tempfile.mkstemp(suffix='.h', text=True)
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path


def test_execution_context_integration():
    """TEST 1: Verify ingestion integrates with ExecutionContext."""
    print("Testing ExecutionContext Integration...")
    
    try:
        # Create a dummy header for context building
        header_path = create_test_header("int x;")
        
        # Create a minimal execution context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=header_path,
            library_file=r"C:\Windows\System32\kernel32.dll",
            working_directory=os.getcwd()
        )
        
        # Verify analyzer can access context fields
        analyzer = NativeInterfaceAnalyzer()
        assert context.compiler.compiler_path is not None
        assert context.platform.os_name == "Windows"
        assert context.provenance.execution_id is not None
        
        # Cleanup
        os.unlink(header_path)
        
        print("  [PASS] ExecutionContext integration working")
        return True
    except Exception as e:
        print(f"  [FAIL] ExecutionContext integration failed: {e}")
        if 'header_path' in locals():
            try:
                os.unlink(header_path)
            except:
                pass
        return False


def test_simple_header_parsing():
    """TEST 2: Verify simple header parsing works."""
    print("Testing Simple Header Parsing...")
    
    try:
        # Create test header
        header_content = """
int add(int a, int b);
void print_message(const char* message);
"""
        header_path = create_test_header(header_content)
        
        # Create context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=header_path,
            library_file=r"C:\Windows\System32\kernel32.dll",
            working_directory=os.getcwd()
        )
        
        # Analyze header
        analyzer = NativeInterfaceAnalyzer()
        artifact = analyzer.analyze(
            header_path=header_path,
            library_path=r"C:\Windows\System32\kernel32.dll",
            context=context
        )
        
        # Verify functions extracted
        assert len(artifact["functions"]) >= 2
        func_names = [f["name"] for f in artifact["functions"]]
        assert "add" in func_names
        assert "print_message" in func_names
        
        # Verify function signatures
        add_func = next(f for f in artifact["functions"] if f["name"] == "add")
        assert add_func["return_type"]["kind"] == "primitive"
        assert add_func["return_type"]["name"] == "int"
        assert len(add_func["parameters"]) == 2
        
        # Cleanup
        os.unlink(header_path)
        
        print("  [PASS] Simple header parsing successful")
        return True
    except Exception as e:
        print(f"  [FAIL] Simple header parsing failed: {e}")
        if 'header_path' in locals():
            try:
                os.unlink(header_path)
            except:
                pass
        return False


def test_struct_layout_with_padding():
    """TEST 3: Verify struct layout computation with padding."""
    print("Testing Struct Layout with Padding...")
    
    try:
        # Create test header with struct requiring padding
        header_content = """
struct TestStruct {
    int a;
    void* b;
    char c;
};
"""
        header_path = create_test_header(header_content)
        
        # Create context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=header_path,
            library_file=r"C:\Windows\System32\kernel32.dll",
            working_directory=os.getcwd()
        )
        
        # Analyze header
        analyzer = NativeInterfaceAnalyzer()
        artifact = analyzer.analyze(
            header_path=header_path,
            library_path=r"C:\Windows\System32\kernel32.dll",
            context=context
        )
        
        # Verify struct extracted
        assert len(artifact["structs"]) >= 1
        test_struct = next(s for s in artifact["structs"] if s["name"] == "TestStruct")
        
        # Verify padding is present
        # On x64: int (4 bytes) + padding (4 bytes) + void* (8 bytes) + char (1 byte) + padding (7 bytes) = 24 bytes
        assert test_struct["size_bytes"] == 24
        assert test_struct["alignment_bytes"] == 8
        
        # Check for padding fields
        field_names = [f["name"] for f in test_struct["fields"]]
        has_padding = any("__padding_" in name for name in field_names)
        assert has_padding, "Expected padding fields in struct layout"
        
        # Cleanup
        os.unlink(header_path)
        
        print("  [PASS] Struct layout with padding correct")
        return True
    except Exception as e:
        print(f"  [FAIL] Struct layout with padding failed: {e}")
        if 'header_path' in locals():
            try:
                os.unlink(header_path)
            except:
                pass
        return False


def test_enum_extraction():
    """TEST 4: Verify enum extraction works."""
    print("Testing Enum Extraction...")
    
    try:
        # Create test header with enum
        header_content = """
enum Color {
    RED = 0,
    GREEN = 1,
    BLUE = 2
};
"""
        header_path = create_test_header(header_content)
        
        # Create context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=header_path,
            library_file=r"C:\Windows\System32\kernel32.dll",
            working_directory=os.getcwd()
        )
        
        # Analyze header
        analyzer = NativeInterfaceAnalyzer()
        artifact = analyzer.analyze(
            header_path=header_path,
            library_path=r"C:\Windows\System32\kernel32.dll",
            context=context
        )
        
        # Verify enum extracted
        assert len(artifact["enums"]) >= 1
        color_enum = next(e for e in artifact["enums"] if e["name"] == "Color")
        
        # Verify enum values
        assert len(color_enum["values"]) == 3
        value_names = [v["name"] for v in color_enum["values"]]
        assert "RED" in value_names
        assert "GREEN" in value_names
        assert "BLUE" in value_names
        
        # Verify values are correct
        red_value = next(v for v in color_enum["values"] if v["name"] == "RED")
        assert red_value["value"] == 0
        
        # Cleanup
        os.unlink(header_path)
        
        print("  [PASS] Enum extraction working")
        return True
    except Exception as e:
        print(f"  [FAIL] Enum extraction failed: {e}")
        if 'header_path' in locals():
            try:
                os.unlink(header_path)
            except:
                pass
        return False


def test_typedef_extraction():
    """TEST 5: Verify typedef extraction works."""
    print("Testing Typedef Extraction...")
    
    try:
        # Create test header with typedefs
        header_content = """
typedef int MyInt;
typedef MyInt YourInt;
typedef unsigned long MySizeT;
"""
        header_path = create_test_header(header_content)
        
        # Create context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=header_path,
            library_file=r"C:\Windows\System32\kernel32.dll",
            working_directory=os.getcwd()
        )
        
        # Analyze header
        analyzer = NativeInterfaceAnalyzer()
        artifact = analyzer.analyze(
            header_path=header_path,
            library_path=r"C:\Windows\System32\kernel32.dll",
            context=context
        )
        
        # Verify typedefs extracted
        assert len(artifact["typedefs"]) >= 3
        typedef_names = [t["name"] for t in artifact["typedefs"]]
        assert "MyInt" in typedef_names
        assert "YourInt" in typedef_names
        
        # Cleanup
        os.unlink(header_path)
        
        print("  [PASS] Typedef extraction working")
        return True
    except Exception as e:
        print(f"  [FAIL] Typedef extraction failed: {e}")
        if 'header_path' in locals():
            try:
                os.unlink(header_path)
            except:
                pass
        return False


def test_calling_convention_detection():
    """TEST 6: Verify calling convention detection (Windows-specific)."""
    print("Testing Calling Convention Detection...")
    
    try:
        # Create test header with different calling conventions
        header_content = """
int __cdecl normal_func(int x);
int __stdcall windows_func(int x);
"""
        header_path = create_test_header(header_content)
        
        # Create context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=header_path,
            library_file=r"C:\Windows\System32\kernel32.dll",
            working_directory=os.getcwd()
        )
        
        # Analyze header
        analyzer = NativeInterfaceAnalyzer()
        artifact = analyzer.analyze(
            header_path=header_path,
            library_path=r"C:\Windows\System32\kernel32.dll",
            context=context
        )
        
        # Verify calling conventions detected
        assert len(artifact["functions"]) >= 2
        
        # Check that calling conventions are recorded
        for func in artifact["functions"]:
            assert "calling_convention" in func
            assert func["calling_convention"] in ["cdecl", "stdcall", "fastcall", "win64"]
        
        # Cleanup
        os.unlink(header_path)
        
        print("  [PASS] Calling convention detection working")
        return True
    except Exception as e:
        print(f"  [FAIL] Calling convention detection failed: {e}")
        if 'header_path' in locals():
            try:
                os.unlink(header_path)
            except:
                pass
        return False


def test_source_location_tracking():
    """TEST 7: Verify source location tracking works."""
    print("Testing Source Location Tracking...")
    
    try:
        # Create test header
        header_content = """
int test_function(int x);

struct TestStruct {
    int field1;
};
"""
        header_path = create_test_header(header_content)
        
        # Create context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=header_path,
            library_file=r"C:\Windows\System32\kernel32.dll",
            working_directory=os.getcwd()
        )
        
        # Analyze header
        analyzer = NativeInterfaceAnalyzer()
        artifact = analyzer.analyze(
            header_path=header_path,
            library_path=r"C:\Windows\System32\kernel32.dll",
            context=context
        )
        
        # Verify all functions have source locations
        for func in artifact["functions"]:
            assert "source_location" in func
            assert "file" in func["source_location"]
            assert "line" in func["source_location"]
            assert "column" in func["source_location"]
            # Verify file path is absolute
            assert os.path.isabs(func["source_location"]["file"]) or func["source_location"]["file"] == "<unknown>"
        
        # Verify all structs have source locations
        for struct in artifact["structs"]:
            assert "source_location" in struct
            assert "file" in struct["source_location"]
        
        # Cleanup
        os.unlink(header_path)
        
        print("  [PASS] Source location tracking working")
        return True
    except Exception as e:
        print(f"  [FAIL] Source location tracking failed: {e}")
        if 'header_path' in locals():
            try:
                os.unlink(header_path)
            except:
                pass
        return False


def test_provenance_metadata():
    """TEST 8: Verify provenance metadata is complete."""
    print("Testing Provenance Metadata...")
    
    try:
        # Create test header
        header_content = "int test(void);"
        header_path = create_test_header(header_content)
        
        # Create context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=header_path,
            library_file=r"C:\Windows\System32\kernel32.dll",
            working_directory=os.getcwd()
        )
        
        # Analyze header
        analyzer = NativeInterfaceAnalyzer()
        artifact = analyzer.analyze(
            header_path=header_path,
            library_path=r"C:\Windows\System32\kernel32.dll",
            context=context
        )
        
        # Verify provenance section exists
        assert "provenance" in artifact
        prov = artifact["provenance"]
        
        # Verify all required fields
        assert "producing_phase" in prov
        assert "execution_id" in prov
        assert "timestamp" in prov
        assert "tool_version" in prov
        assert "schema_version" in prov
        assert "input_artifacts" in prov
        assert "compiler_invocation" in prov
        
        # Verify execution_id matches context
        assert prov["execution_id"] == context.provenance.execution_id
        
        # Verify platform section
        assert "platform" in artifact
        platform = artifact["platform"]
        assert platform["os_name"] == context.platform.os_name
        assert platform["architecture"] == context.platform.architecture
        
        # Cleanup
        os.unlink(header_path)
        
        print("  [PASS] Provenance metadata complete")
        return True
    except Exception as e:
        print(f"  [FAIL] Provenance metadata failed: {e}")
        if 'header_path' in locals():
            try:
                os.unlink(header_path)
            except:
                pass
        return False


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("  Native Interface Ingestion Validation")
    print("=" * 70)
    print()
    
    tests = [
        test_execution_context_integration,
        test_simple_header_parsing,
        test_struct_layout_with_padding,
        test_enum_extraction,
        test_typedef_extraction,
        test_calling_convention_detection,
        test_source_location_tracking,
        test_provenance_metadata,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  [FAIL] Test crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"  [PASS] ALL TESTS PASSED ({passed}/{total})")
        print("=" * 70)
        return 0
    else:
        print(f"  [FAIL] SOME TESTS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
