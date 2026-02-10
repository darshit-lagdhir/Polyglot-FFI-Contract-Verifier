#!/usr/bin/env python3
"""
Auto-fix all indentation errors in Module 05 by compiling and fixing.
"""

import subprocess
import re
from pathlib import Path

def get_indentation_errors(file_path):
    """Get all indentation errors from a file."""
    result = subprocess.run(
        ['python', '-m', 'py_compile', str(file_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return []
    
    # Parse error message
    errors = []
    for line in result.stderr.split('\n'):
        if 'IndentationError' in line and ', line' in line:
            match = re.search(r'line (\d+)', line)
            if match:
                errors.append(int(match.group(1)))
    
    return errors

def fix_indentation(file_path, error_line):
    """Fix indentation at a specific line by reducing excess spaces."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    idx = error_line - 1
    if idx < 0 or idx >= len(lines):
        return False
    
    line = lines[idx]
    stripped = line.lstrip()
    
    if not stripped or stripped.startswith('#'):
        return False
    
    # Count current indentation
    current_indent = len(line) - len(stripped)
    
    # Try reducing by 4 spaces
    if current_indent >= 4:
        new_indent = current_indent - 4
        lines[idx] = ' ' * new_indent + stripped
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    
    return False

def fix_file(file_path):
    """Fix all indentation errors in a file."""
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        errors = get_indentation_errors(file_path)
        if not errors:
            return True
        
        # Fix the first error
        if fix_indentation(file_path, errors[0]):
            iteration += 1
        else:
            print(f"  Could not fix {file_path}:{errors[0]}")
            return False
    
    return False

def main():
    module_dir = Path("modules/module_05_ir_normalization")
    
    files_to_fix = [
        "cli.py",
        "documentation.py",
        "ir_entities.py",
        "ir_serialization.py",
        "ir_validation.py",
        "performance.py",
        "type_normalization.py",
    ]
    
    for filename in files_to_fix:
        file_path = module_dir / filename
        print(f"\nFixing {filename}...")
        
        if fix_file(file_path):
            print(f"  ✓ {filename} fixed successfully")
        else:
            print(f"  ✗ {filename} still has errors")

if __name__ == "__main__":
    main()
