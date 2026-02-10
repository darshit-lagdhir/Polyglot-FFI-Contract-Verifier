#!/usr/bin/env python3
"""
Script to fix common indentation errors in test files.
"""

import re
from pathlib import Path

def fix_indentation_errors(file_path):
    """Fix common indentation errors in a Python file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Fix: Extra indentation before function/method definitions
        content = re.sub(r'^(\s{4,})(\s{4,})(def test_)', r'\1\3', content, flags=re.MULTILINE)
        
        # Fix: Extra indentation before assert statements
        content = re.sub(r'^(\s{4,})(\s{4,})(assert )', r'\1\3', content, flags=re.MULTILINE)
        
        # Fix: Extra indentation before from/import statements inside functions
        content = re.sub(r'^(\s{8})(\s{4,})(from |import )', r'\1\3', content, flags=re.MULTILINE)
        
        # Fix: Extra indentation before with/if/for statements
        content = re.sub(r'^(\s{8})(\s{4,})(with |if |for )', r'\1\3', content, flags=re.MULTILINE)
        
        # Fix: Lines with only spaces that should be empty class/function bodies
        content = re.sub(r'^(class \w+.*:)\n\s+$', r'\1\n    pass\n', content, flags=re.MULTILINE)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True, "Fixed"
        return False, "No changes needed"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    test_dir = Path("tests")
    
    # Find all Python test files
    test_files = list(test_dir.rglob("test_*.py"))
    
    print(f"Found {len(test_files)} test files")
    print("=" * 80)
    
    fixed_count = 0
    for test_file in test_files:
        changed, msg = fix_indentation_errors(test_file)
        if changed:
            print(f"✓ Fixed: {test_file}")
            fixed_count += 1
        else:
            print(f"  Skipped: {test_file} - {msg}")
    
    print("=" * 80)
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
