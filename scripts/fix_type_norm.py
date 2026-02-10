#!/usr/bin/env python3
"""Fix line 400 indentation in type_normalization.py"""

file_path = "modules/module_05_ir_normalization/type_normalization.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 400-407 need to be unindented by 4 spaces (move outside for loop)
# Line 400 (index 399) currently has 12 spaces, should have 8
# Lines 401-407 should follow accordingly

fixes = {
    399: "        # Add trailing padding if needed\n",  # Comment line
    400: "        if raw_type.size_bytes > current_offset:\n",
    401: "            trailing_size = raw_type.size_bytes - current_offset\n",
    402: "            trailing_padding = PaddingEntity(\n",
    403: "                byte_offset=current_offset,\n",
    404: "                size_bytes=trailing_size,\n",
    405: "                reason=\"structure end padding\"\n",
    406: "            )\n",
    407: "            struct.add_padding(trailing_padding)\n",
}

for idx, new_line in fixes.items():
    if idx < len(lines):
        lines[idx] = new_line

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed type_normalization.py line 400-407")
