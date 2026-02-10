#!/usr/bin/env python3
"""
Comprehensive fix for all Module 05 indentation errors.
This script manually fixes known indentation issues.
"""

import subprocess
from pathlib import Path

def get_syntax_error(file_path):
    """Get syntax error details from a file."""
    result = subprocess.run(
        ['python', '-m', 'py_compile', str(file_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return None
    
    # Extract error info
    stderr = result.stderr
    if 'IndentationError' in stderr or 'SyntaxError' in stderr:
        # Extract line number
        import re
        match = re.search(r'line (\d+)', stderr)
        if match:
            line_num = int(match.group(1))
            return line_num
    
    return None

def view_and_fix_line(file_path, line_num, context=3):
    """View a line with context and attempt to fix it."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    idx = line_num - 1
    if idx < 0 or idx >= len(lines):
        return False
    
    # Show context
    print(f"\n{file_path}:{line_num}")
    print("Context:")
    for i in range(max(0, idx - context), min(len(lines), idx + context + 1)):
        marker = ">>>" if i == idx else "   "
        print(f"{marker} {i+1:4d}: {lines[i].rstrip()}")
    
    # Analyze the problematic line
    line = lines[idx]
    stripped = line.lstrip()
    current_indent = len(line) - len(stripped)
    
    # Check previous non-empty line for expected indentation
    prev_idx = idx - 1
    while prev_idx >= 0 and not lines[prev_idx].strip():
        prev_idx -= 1
    
    if prev_idx >= 0:
        prev_line = lines[prev_idx]
        prev_stripped = prev_line.lstrip()
        prev_indent = len(prev_line) - len(prev_stripped)
        
        # Determine correct indentation
        # If previous line ends with ':', next line should be indented +4
        # Otherwise, should match or be less
        
        if prev_stripped.rstrip().endswith(':'):
            expected_indent = prev_indent + 4
        elif stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ')):
            # These should align with previous block level
            expected_indent = prev_indent
        elif stripped.startswith(('return ', 'raise ', 'pass', 'break', 'continue')):
            # Statements inside a function
            expected_indent = prev_indent
        else:
            # Default: match previous indentation
            expected_indent = prev_indent
        
        if current_indent != expected_indent:
            print(f"Fixing: {current_indent} spaces -> {expected_indent} spaces")
            lines[idx] = ' ' * expected_indent + stripped
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
    
    return False

def fix_all_files():
    """Fix all Module 05 files."""
    module_dir = Path("modules/module_05_ir_normalization")
    
    files = [
        "cli.py",
        "documentation.py",
        "ir_entities.py",
        "ir_serialization.py",
        "ir_types.py",
        "ir_validation.py",
        "performance.py",
        "symbol_normalization.py",
        "type_normalization.py",
    ]
    
    fixed_count = 0
    
    for filename in files:
        file_path = module_dir / filename
        if not file_path.exists():
            continue
        
        max_iterations = 20
        iteration = 0
        
        while iteration < max_iterations:
            error_line = get_syntax_error(file_path)
            if error_line is None:
                print(f"\n✓ {filename} - OK")
                break
            
            if view_and_fix_line(file_path, error_line):
                iteration += 1
                fixed_count += 1
            else:
                print(f"\n✗ {filename} - Could not auto-fix line {error_line}")
                break
        
        if iteration >= max_iterations:
            print(f"\n✗ {filename} - Too many iterations")
    
    print(f"\n\nTotal fixes applied: {fixed_count}")

if __name__ == "__main__":
    fix_all_files()
