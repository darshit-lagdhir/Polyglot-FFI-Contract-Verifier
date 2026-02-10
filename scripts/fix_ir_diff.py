#!/usr/bin/env python3
"""Fix class definition in ir_diff.py"""

file_path = "modules/module_05_ir_normalization/ir_diff.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 425 (index 424) should be "class ChangeSummary:"
if lines[424].strip() == "class Change":
    lines[424] = "class ChangeSummary:\n"
    print("Fixed line 425: class Change -> class ChangeSummary:")
else:
    print(f"Line 425 content: {repr(lines[424])}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
