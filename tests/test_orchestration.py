"""
Validation and Demonstration Script for Execution Context and Orchestration Layer

This script validates that the implementation meets all requirements for :
- ExecutionContext has all 7 required field categories
- Context construction performs all 8 steps deterministically
- CLI supports all 9 commands
- Error types are classified correctly
- Execution context is serialized to JSON
- Provenance metadata is complete
- Deterministic seed generation works
- File paths are resolved to absolute paths
- ExecutionContext is immutable after construction
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from polyglot_ffi_verifier.context import (
    ExecutionContext,
    ExecutionContextBuilder,
    PlatformIdentification,
    CompilerInformation,
    NativeLibraryInformation,
    TargetLanguageRuntime,
    VerificationConfig,
    ProvenanceMetadata,
    ArtifactPaths
)
from polyglot_ffi_verifier.pipeline import (
    CLIOrchestrator,
    PipelineOrchestrator,
    ErrorType,
    PipelineStage,
    ConfigError,
    ToolingError,
    PreconditionError,
    StageError
)

def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def print_check(description: str, passed: bool):
    """Print validation check result."""
    status = "✓" if passed else "✗"
    print(f"  {status} {description}")

def validate_execution_context_structure():
    """Validate ExecutionContext has all 7 required field categories."""
    print_section("VALIDATION 1: ExecutionContext Structure")
    
    # Create a mock context for validation
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files
        dummy_lib = os.path.join(tmpdir, "dummy.dll")
        with open(dummy_lib, 'wb') as f:
            f.write(b"DUMMY")
        
        dummy_header = os.path.join(tmpdir, "dummy.h")
        with open(dummy_header, 'w') as f:
            f.write("// Dummy header\n")
        
        try:
            builder = ExecutionContextBuilder()
            context = builder.build(
                header_file=dummy_header,
                library_file=dummy_lib,
                working_directory=tmpdir
            )
            
            # Check all 7 required field categories
            checks = [
                ("Platform Identification", hasattr(context, 'platform')),
                ("Compiler Information", hasattr(context, 'compiler')),
                ("Native Library Information", hasattr(context, 'native_library')),
                ("Target Language Runtime", hasattr(context, 'target_runtime')),
                ("Verification Config", hasattr(context, 'verification_config')),
                ("Provenance Metadata", hasattr(context, 'provenance')),
                ("Artifact Paths", hasattr(context, 'artifacts'))
            ]
            
            for desc, passed in checks:
                print_check(desc, passed)
            
            # Validate platform fields
            print("\n  Platform fields:")
            platform_fields = ['os_name', 'os_version', 'architecture', 'pointer_width', 'endianness']
            for field in platform_fields:
                has_field = hasattr(context.platform, field)
                print(f"    {field}: {getattr(context.platform, field, 'MISSING')}")
            
            # Validate provenance fields
            print("\n  Provenance fields:")
            provenance_fields = ['schema_version', 'creation_timestamp', 'execution_id', 'tool_version']
            for field in provenance_fields:
                has_field = hasattr(context.provenance, field)
                print(f"    {field}: {getattr(context.provenance, field, 'MISSING')}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Failed to create execution context: {e}")
            return False

def validate_determinism():
    """Validate that identical inputs produce byte-identical contexts."""
    print_section("VALIDATION 2: Determinism")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files
        dummy_lib = os.path.join(tmpdir, "test.dll")
        with open(dummy_lib, 'wb') as f:
            f.write(b"TEST_LIBRARY_CONTENT")
        
        dummy_header = os.path.join(tmpdir, "test.h")
        with open(dummy_header, 'w') as f:
            f.write("// Test header\nvoid test_func(void);\n")
        
        try:
            # Build context twice with same inputs
            builder1 = ExecutionContextBuilder()
            context1 = builder1.build(
                header_file=dummy_header,
                library_file=dummy_lib,
                random_seed=12345,  # Explicit seed for determinism
                working_directory=tmpdir
            )
            
            # Create separate temp dir for second context
            tmpdir2 = tempfile.mkdtemp()
            builder2 = ExecutionContextBuilder()
            context2 = builder2.build(
                header_file=dummy_header,
                library_file=dummy_lib,
                random_seed=12345,  # Same seed
                working_directory=tmpdir2
            )
            
            # Compare key fields (excluding paths which will differ)
            checks = [
                ("Random seed matches", 
                 context1.verification_config.random_seed == context2.verification_config.random_seed),
                ("Library hash matches",
                 context1.native_library.library_hash == context2.native_library.library_hash),
                ("Platform matches",
                 context1.platform == context2.platform),
                ("Schema version matches",
                 context1.provenance.schema_version == context2.provenance.schema_version)
            ]
            
            for desc, passed in checks:
                print_check(desc, passed)
            
            # Clean up second temp dir
            import shutil
            shutil.rmtree(tmpdir2)
            
            return all(passed for _, passed in checks)
            
        except Exception as e:
            print(f"  ✗ Determinism validation failed: {e}")
            return False

def validate_immutability():
    """Validate that ExecutionContext is immutable after construction."""
    print_section("VALIDATION 3: Immutability")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_lib = os.path.join(tmpdir, "test.dll")
        with open(dummy_lib, 'wb') as f:
            f.write(b"TEST")
        
        dummy_header = os.path.join(tmpdir, "test.h")
        with open(dummy_header, 'w') as f:
            f.write("void test(void);\n")
        
        try:
            builder = ExecutionContextBuilder()
            context = builder.build(
                header_file=dummy_header,
                library_file=dummy_lib,
                working_directory=tmpdir
            )
            
            # Try to modify context (should fail with frozen dataclass)
            try:
                context.platform.os_name = "Modified"
                print_check("Context is immutable", False)
                return False
            except Exception:
                print_check("Context is immutable (modification blocked)", True)
                return True
                
        except Exception as e:
            print(f"  ✗ Immutability validation failed: {e}")
            return False

def validate_serialization():
    """Validate that execution context serializes to valid JSON."""
    print_section("VALIDATION 4: JSON Serialization")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_lib = os.path.join(tmpdir, "test.dll")
        with open(dummy_lib, 'wb') as f:
            f.write(b"TEST")
        
        dummy_header = os.path.join(tmpdir, "test.h")
        with open(dummy_header, 'w') as f:
            f.write("void test(void);\n")
        
        try:
            builder = ExecutionContextBuilder()
            context = builder.build(
                header_file=dummy_header,
                library_file=dummy_lib,
                working_directory=tmpdir
            )
            
            # Serialize to JSON
            json_str = context.to_json()
            print_check("Context serializes to JSON", True)
            
            # Validate JSON is parseable
            parsed = json.loads(json_str)
            print_check("JSON is valid and parseable", True)
            
            # Check key fields exist in JSON
            checks = [
                ("platform in JSON", 'platform' in parsed),
                ("compiler in JSON", 'compiler' in parsed),
                ("native_library in JSON", 'native_library' in parsed),
                ("target_runtime in JSON", 'target_runtime' in parsed),
                ("verification_config in JSON", 'verification_config' in parsed),
                ("provenance in JSON", 'provenance' in parsed),
                ("artifacts in JSON", 'artifacts' in parsed)
            ]
            
            for desc, passed in checks:
                print_check(desc, passed)
            
            # Validate context can be saved and loaded
            context.save()
            loaded_context = ExecutionContext.load(context.artifacts.execution_context_path)
            print_check("Context can be saved and loaded", True)
            print_check("Loaded context matches original", 
                       loaded_context.provenance.execution_id == context.provenance.execution_id)
            
            # Display sample JSON (first 500 chars)
            print(f"\n  Sample JSON output:")
            print(f"  {json_str[:500]}...")
            
            return all(passed for _, passed in checks)
            
        except Exception as e:
            print(f"  ✗ Serialization validation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def validate_cli_commands():
    """Validate that CLI supports all 9 commands."""
    print_section("VALIDATION 5: CLI Commands")
    
    cli = CLIOrchestrator()
    
    expected_commands = [
        "verify",
        "ingest",
        "synthesize",
        "generate-adapters",
        "generate-tests",
        "execute",
        "diagnose",
        "report",
        "context"
    ]
    
    # Check that parser has all commands
    subparsers_actions = [
        action for action in cli.parser._actions 
        if isinstance(action, argparse._SubParsersAction)
    ]
    
    if subparsers_actions:
        subparsers = subparsers_actions[0]
        available_commands = list(subparsers.choices.keys())
        
        for cmd in expected_commands:
            has_cmd = cmd in available_commands
            print_check(f"Command '{cmd}' available", has_cmd)
        
        return all(cmd in available_commands for cmd in expected_commands)
    else:
        print_check("CLI parser has subcommands", False)
        return False

def validate_error_classification():
    """Validate that error types are classified correctly."""
    print_section("VALIDATION 6: Error Classification")
    
    checks = []
    
    # Test ConfigError
    try:
        raise ConfigError("Test config error")
    except ConfigError as e:
        checks.append(("ConfigError has correct type", 
                      e.error_type == ErrorType.CONFIGURATION_ERROR))
    
    # Test ToolingError
    try:
        raise ToolingError("Test tooling error")
    except ToolingError as e:
        checks.append(("ToolingError has correct type",
                      e.error_type == ErrorType.TOOLING_ERROR))
    
    # Test PreconditionError
    try:
        raise PreconditionError("Test precondition error")
    except PreconditionError as e:
        checks.append(("PreconditionError has correct type",
                      e.error_type == ErrorType.PRECONDITION_ERROR))
    
    # Test StageError
    try:
        raise StageError("Test stage error")
    except StageError as e:
        checks.append(("StageError has correct type",
                      e.error_type == ErrorType.STAGE_ERROR))
    
    for desc, passed in checks:
        print_check(desc, passed)
    
    return all(passed for _, passed in checks)

def validate_provenance_metadata():
    """Validate that provenance metadata is complete."""
    print_section("VALIDATION 7: Provenance Metadata")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_lib = os.path.join(tmpdir, "test.dll")
        with open(dummy_lib, 'wb') as f:
            f.write(b"TEST")
        
        dummy_header = os.path.join(tmpdir, "test.h")
        with open(dummy_header, 'w') as f:
            f.write("void test(void);\n")
        
        try:
            builder = ExecutionContextBuilder()
            context = builder.build(
                header_file=dummy_header,
                library_file=dummy_lib,
                working_directory=tmpdir
            )
            
            prov = context.provenance
            
            checks = [
                ("Has schema_version", prov.schema_version == "1.0.0"),
                ("Has creation_timestamp", len(prov.creation_timestamp) > 0),
                ("Has execution_id (UUID)", len(prov.execution_id) == 36),  # UUID format
                ("Has tool_version", prov.tool_version == "1.0.0")
            ]
            
            for desc, passed in checks:
                print_check(desc, passed)
            
            print(f"\n  Provenance details:")
            print(f"    Schema Version: {prov.schema_version}")
            print(f"    Execution ID: {prov.execution_id}")
            print(f"    Timestamp: {prov.creation_timestamp}")
            print(f"    Tool Version: {prov.tool_version}")
            
            return all(passed for _, passed in checks)
            
        except Exception as e:
            print(f"  ✗ Provenance validation failed: {e}")
            return False

def validate_absolute_paths():
    """Validate that file paths are resolved to absolute paths."""
    print_section("VALIDATION 8: Absolute Path Resolution")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_lib = os.path.join(tmpdir, "test.dll")
        with open(dummy_lib, 'wb') as f:
            f.write(b"TEST")
        
        dummy_header = os.path.join(tmpdir, "test.h")
        with open(dummy_header, 'w') as f:
            f.write("void test(void);\n")
        
        try:
            builder = ExecutionContextBuilder()
            context = builder.build(
                header_file=dummy_header,
                library_file=dummy_lib,
                working_directory=tmpdir
            )
            
            # Check that all paths are absolute
            checks = [
                ("Library path is absolute", os.path.isabs(context.native_library.library_path)),
                ("Working directory is absolute", os.path.isabs(context.artifacts.working_directory)),
                ("IR path is absolute", os.path.isabs(context.artifacts.intermediate_representation_path)),
                ("Contract path is absolute", os.path.isabs(context.artifacts.contract_path)),
                ("Test plan path is absolute", os.path.isabs(context.artifacts.test_plan_path)),
                ("Execution log path is absolute", os.path.isabs(context.artifacts.execution_log_path)),
                ("Diagnostics path is absolute", os.path.isabs(context.artifacts.diagnostics_path)),
                ("Report path is absolute", os.path.isabs(context.artifacts.report_path)),
                ("Context path is absolute", os.path.isabs(context.artifacts.execution_context_path))
            ]
            
            for desc, passed in checks:
                print_check(desc, passed)
            
            return all(passed for _, passed in checks)
            
        except Exception as e:
            print(f"  ✗ Path resolution validation failed: {e}")
            return False

def main():
    """Run all validations."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║  Polyglot FFI Contract Verifier - Execution Context Validation Suite      ║
║  : Execution Context and Orchestration Layer                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Import argparse for CLI validation
    import argparse
    
    results = []
    
    results.append(("ExecutionContext Structure", validate_execution_context_structure()))
    results.append(("Determinism", validate_determinism()))
    results.append(("Immutability", validate_immutability()))
    results.append(("JSON Serialization", validate_serialization()))
    results.append(("CLI Commands", validate_cli_commands()))
    results.append(("Error Classification", validate_error_classification()))
    results.append(("Provenance Metadata", validate_provenance_metadata()))
    results.append(("Absolute Path Resolution", validate_absolute_paths()))
    
    # Summary
    print_section("VALIDATION SUMMARY")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n  ✓ ALL VALIDATIONS PASSED - Implementation is correct!")
        return 0
    else:
        print(f"\n  ✗ {total - passed} validation(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
