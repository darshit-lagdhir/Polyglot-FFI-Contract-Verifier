#!/usr/bin/env python3
"""
Fix all indentation errors in Module 05 files.
"""

import re
from pathlib import Path

# Files and their error lines
fixes = [
    ("modules/module_05_ir_normalization/cli.py", 529),
    ("modules/module_05_ir_normalization/documentation.py", 111),
    ("modules/module_05_ir_normalization/ir_entities.py", 183),
    ("modules/module_05_ir_normalization/ir_serialization.py", 108),
    ("modules/module_05_ir_normalization/ir_validation.py", 88),
    ("modules/module_05_ir_normalization/performance.py", 163),
    ("modules/module_05_ir_normalization/type_normalization.py", 400),
]

def fix_file(file_path, error_line):
    """Fix indentation error at specific line."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check context around the error line
    idx = error_line - 1
    if idx < 0 or idx >= len(lines):
        print(f"  {file_path}:{error_line} - Line out of range")
        return False
    
    # Common fix: remove extra leading spaces (usually 4 or 8 spaces too many)
    line = lines[idx]
    stripped = line.lstrip()
    
    if not stripped:
        print(f"  {file_path}:{error_line} - Empty line, skipping")
        return False
    
    # Count leading spaces
    leading_spaces = len(line) - len(stripped)
    
    # Try to detect correct indentation from previous non-empty line
    prev_idx = idx - 1
    while prev_idx >= 0 and not lines[prev_idx].strip():
        prev_idx -= 1
    
    if prev_idx >= 0:
        prev_line = lines[prev_idx]
        prev_stripped = prev_line.lstrip()
        prev_spaces = len(prev_line) - len(prev_stripped)
        
        # If current line has significantly more spaces than previous, reduce it
        if leading_spaces > prev_spaces + 8:
            # Reduce by 4 or 8 spaces
            new_spaces = max(prev_spaces, leading_spaces - 8)
            lines[idx] = ' ' * new_spaces + stripped
            print(f"  ✓ Fixed {file_path}:{error_line} ({leading_spaces} -> {new_spaces} spaces)")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
    
    print(f"  ? {file_path}:{error_line} - Could not auto-fix (spaces: {leading_spaces})")
    print(f"    Content: {repr(line[:50])}")
    return False

def main():
    fixed_count = 0
    for file_path, error_line in fixes:
        if fix_file(file_path, error_line):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count}/{len(fixes)} files")

if __name__ == "__main__":
    main()
