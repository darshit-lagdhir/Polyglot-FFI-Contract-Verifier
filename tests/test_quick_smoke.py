"""
Quick test to verify  (Orchestration Layer) implementation works correctly.
"""

import argparse
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from polyglot_ffi_verifier.context import ExecutionContextBuilder
from polyglot_ffi_verifier.pipeline import CLIOrchestrator

def test_basic_functionality():
    """Test basic execution context creation."""
    print("Testing Execution Context Creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files
        dummy_lib = os.path.join(tmpdir, "test.dll")
        with open(dummy_lib, 'wb') as f:
            f.write(b"DUMMY_LIBRARY_CONTENT")
        
        dummy_header = os.path.join(tmpdir, "test.h")
        with open(dummy_header, 'w') as f:
            f.write("// Test header\nvoid test_function(void);\n")
        
        # Build execution context
        builder = ExecutionContextBuilder()
        context = builder.build(
            header_file=dummy_header,
            library_file=dummy_lib,
            random_seed=42,
            working_directory=tmpdir
        )
        
        # Verify context was created
        assert context is not None, "Context should not be None"
        assert context.platform is not None, "Platform should be set"
        assert context.compiler is not None, "Compiler should be set"
        assert context.native_library is not None, "Native library should be set"
        assert context.target_runtime is not None, "Target runtime should be set"
        assert context.verification_config is not None, "Verification config should be set"
        assert context.provenance is not None, "Provenance should be set"
        assert context.artifacts is not None, "Artifacts should be set"
        
        print(f"✓ ExecutionContext created successfully")
        print(f"  Execution ID: {context.provenance.execution_id}")
        print(f"  Platform: {context.platform.os_name} {context.platform.architecture}")
        print(f"  Compiler: {context.compiler.compiler_name} {context.compiler.compiler_version}")
        print(f"  Python: {context.target_runtime.language_version}")
        print(f"  Random Seed: {context.verification_config.random_seed}")
        
        # Verify immutability
        try:
            context.platform.os_name = "Modified"
            print("✗ Context is NOT immutable (this is bad)")
            return False
        except Exception:
            print("✓ Context is immutable (cannot be modified)")
        
        # Verify serialization
        json_str = context.to_json()
        assert len(json_str) > 0, "JSON should not be empty"
        print(f"✓ Context serializes to JSON ({len(json_str)} bytes)")
        
        # Verify context was saved
        assert os.path.exists(context.artifacts.execution_context_path), "Context file should exist"
        print(f"✓ Context saved to: {context.artifacts.execution_context_path}")
        
        # Verify context can be loaded
        from polyglot_ffi_verifier.context import ExecutionContext
        loaded = ExecutionContext.load(context.artifacts.execution_context_path)
        assert loaded.provenance.execution_id == context.provenance.execution_id, "Loaded context should match"
        print(f"✓ Context can be loaded from disk")
        
        return True

def test_cli():
    """Test CLI orchestrator."""
    print("\nTesting CLI Orchestrator...")
    
    cli = CLIOrchestrator()
    
    # Check that parser exists
    assert cli.parser is not None, "Parser should exist"
    print("✓ CLI parser created")
    
    # Check commands exist
    subparsers_actions = [
        action for action in cli.parser._actions 
        if isinstance(action, argparse._SubParsersAction)
    ]
    
    if subparsers_actions:
        commands = list(subparsers_actions[0].choices.keys())
        expected = ["verify", "ingest", "synthesize", "generate-adapters", 
                   "generate-tests", "execute", "diagnose", "report", "context"]
        
        for cmd in expected:
            if cmd in commands:
                print(f"✓ Command '{cmd}' available")
            else:
                print(f"✗ Command '{cmd}' MISSING")
                return False
    
    return True

def main():
    print("=" * 70)
    print("  Polyglot FFI Contract Verifier - Quick Validation")
    print("  : Execution Context and Orchestration Layer")
    print("=" * 70)
    print()
    
    try:
        success = True
        
        # Test execution context
        if not test_basic_functionality():
            success = False
        
        # Test CLI
        if not test_cli():
            success = False
        
        print()
        print("=" * 70)
        if success:
            print("  ✓ ALL TESTS PASSED")
            print("=" * 70)
            return 0
        else:
            print("  ✗ SOME TESTS FAILED")
            print("=" * 70)
            return 1
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
