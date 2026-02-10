#!/usr/bin/env python3
"""
Fix syntax errors in test files - missing colons in class definitions.
"""

import re
from pathlib import Path

def fix_missing_colons(file_path):
    """Fix missing colons in class definitions."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix: class ClassName\n    """docstring""" -> class ClassName:\n    """docstring"""
        content = re.sub(r'^(class \w+)\n(\s+""")', r'\1:\n\2', content, flags=re.MULTILINE)
        
        # Fix: class ClassName\n    # comment -> class ClassName:\n    # comment  
        content = re.sub(r'^(class \w+)\n(\s+#)', r'\1:\n\2', content, flags=re.MULTILINE)
        
        # Fix: class ClassName\n    def -> class ClassName:\n    def
        content = re.sub(r'^(class \w+)\n(\s+def )', r'\1:\n\2', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Fixed"
        return False, "No changes"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    test_dir = Path("tests")
    
    # Files with syntax errors
    problem_files = [
        "tests/unit/test_ir_diff.py",
        "tests/unit/test_ir_entities.py",
        "tests/unit/test_ir_orchestrator.py",
        "tests/unit/test_ir_serialization.py",
        "tests/unit/test_ir_types.py",
        "tests/unit/test_ir_validation.py",
        "tests/unit/test_performance.py",
        "tests/unit/test_symbol_normalization.py",
        "tests/unit/test_type_normalization.py",
        "tests/unit/test_cli.py",
    ]
    
    fixed_count = 0
    for file_path_str in problem_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"  Skipped: {file_path} (not found)")
            continue
            
        changed, msg = fix_missing_colons(file_path)
        if changed:
            print(f"✓ Fixed: {file_path}")
            fixed_count += 1
        else:
            print(f"  {file_path}: {msg}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()
