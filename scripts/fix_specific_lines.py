#!/usr/bin/env python3
"""
Fix specific indentation errors by line number.
"""

fixes = {
    "modules/module_05_ir_normalization/cli.py": {
        528: "    parser = create_parser()",  # Remove 4 extra spaces
    },
    "modules/module_05_ir_normalization/documentation.py": {
        111: None,  # Will check manually
    },
    "modules/module_05_ir_normalization/ir_entities.py": {
        183: None,
    },
    "modules/module_05_ir_normalization/ir_serialization.py": {
        108: None,
    },
    "modules/module_05_ir_normalization/ir_validation.py": {
        88: None,
    },
    "modules/module_05_ir_normalization/performance.py": {
        163: None,
    },
    "modules/module_05_ir_normalization/type_normalization.py": {
        400: None,
    },
}

def fix_line(file_path, line_num, new_content):
    """Fix a specific line in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    idx = line_num - 1
    if idx < 0 or idx >= len(lines):
        print(f"  {file_path}:{line_num} - Line out of range")
        return False
    
    if new_content:
        lines[idx] = new_content + "\n"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  ✓ Fixed {file_path}:{line_num}")
        return True
    else:
        # Just print the line for manual inspection
        print(f"  Line {line_num}: {repr(lines[idx][:60])}")
        return False

def main():
    for file_path, line_fixes in fixes.items():
        print(f"\n{file_path}:")
        for line_num, new_content in line_fixes.items():
            fix_line(file_path, line_num, new_content)

if __name__ == "__main__":
    main()
