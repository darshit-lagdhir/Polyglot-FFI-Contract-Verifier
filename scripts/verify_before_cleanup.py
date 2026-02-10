#!/usr/bin/env python3
"""
Verify it's safe to delete files before cleanup.
Run this BEFORE executing any deletions.
"""

import os
import sys
from pathlib import Path
import re

def check_imports(module_names):
    """Check if any Python files import the specified modules."""
    print("=" * 80)
    print("CHECKING FOR IMPORTS OF STUB MODULES")
    print("=" * 80)
    
    project_root = Path.cwd()
    python_files = list(project_root.rglob("*.py"))
    
    found_imports = {}
    
    for module in module_names:
        found_imports[module] = []
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for various import patterns
                patterns = [
                    rf"from {module}",
                    rf"import {module}",
                ]
                
                for pattern in patterns:
                    if re.search(pattern, content):
                        found_imports[module].append(str(py_file))
            except:
                pass
    
    # Report findings
    safe_to_delete = True
    
    for module, files in found_imports.items():
        if files:
            print(f"\n⚠️  WARNING: Module '{module}' IS IMPORTED!")
            print(f"   Found in {len(files)} file(s):")
            for f in files:
                print(f"     - {f}")
            safe_to_delete = False
        else:
            print(f"✓ Module '{module}' - No imports found (SAFE TO DELETE)")
    
    return safe_to_delete

def check_file_exists(files):
    """Check which files actually exist."""
    print("\n" + "=" * 80)
    print("CHECKING FILE EXISTENCE")
    print("=" * 80)
    
    existing = []
    missing = []
    
    for file_path in files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size if path.is_file() else "DIR"
            print(f"✓ EXISTS: {file_path} ({size} bytes)" if size != "DIR" else f"✓ EXISTS: {file_path} (directory)")
            existing.append(file_path)
        else:
            print(f"✗ MISSING: {file_path}")
            missing.append(file_path)
    
    return existing, missing

def main():
    print("PFCV PROJECT CLEANUP - VERIFICATION SCRIPT")
    print("=" * 80)
    print()
    
    # Step 1: Check stub module imports
    stub_modules = [
        "module_01_ffi_verifier",
        "module_02_verification_pipeline",
        "module_03_build_process",
        "module_04_native_interface_ingestion",
    ]
    
    safe_to_delete_stubs = check_imports(stub_modules)
    
    # Step 2: Check if files to delete actually exist
    files_to_check = [
        # Category A
        "docs/CHANGELOG.md",
        "docs/CONTRIBUTING.md",
        "docs/api_reference.md",
        
        # Category B
        "modules/module_01_ffi_verifier/SYSTEM_ARCHITECTURE.md",
        "modules/module_02_verification_pipeline/VERIFICATION_PIPELINE.md",
        "modules/module_03_build_process/BUILD_PROCESS.md",
        "modules/module_04_native_interface_ingestion/NATIVE_INTERFACE_INGESTION.md",
        "releases/MODULE_02_CERTIFICATION.md",
        "releases/RELEASE_NOTES_v1.0.0.md",
        
        # Category C (stub files)
        "modules/module_01_ffi_verifier/system_architecture.py",
        "modules/module_02_verification_pipeline/verification_pipeline.py",
        "modules/module_03_build_process/build_process.py",
        "modules/module_04_native_interface_ingestion/native_interface_ingestion.py",
        
        # Category E
        "config/pytest.ini",
        "config/requirements-dev.txt",
        "config/requirements.txt",
        
        # Category F
        "docs/module_06_completion_summary.md",
        
        # Category G
        "CLEANUPAI",
    ]
    
    existing, missing = check_file_exists(files_to_check)
    
    # Step 3: Final report
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    if safe_to_delete_stubs:
        print("✓ STUB MODULES: Safe to delete (no imports found)")
    else:
        print("✗ STUB MODULES: DO NOT DELETE (imports found!)")
    
    print(f"\n✓ Files found and ready to delete: {len(existing)}")
    print(f"✗ Files already missing: {len(missing)}")
    
    print("\n" + "=" * 80)
    if safe_to_delete_stubs and len(existing) > 0:
        print("✅ VERIFICATION PASSED - Safe to proceed with cleanup")
        print("=" * 80)
        print("\nNext step: Run the cleanup script")
        return 0
    else:
        print("⚠️  VERIFICATION FAILED - Review warnings above")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
