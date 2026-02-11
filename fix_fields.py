import sys
import re


def fix_fields(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    inside_class = False
    inside_function = False

    for line in lines:
        stripped = line.strip()

        # Detect context
        if stripped.startswith("class "):
            inside_class = True
            inside_function = False
            new_lines.append(line)
            continue

        if stripped.startswith("def "):
            inside_function = True
            new_lines.append(line)
            continue

        # Detect end of context? Hard in Python without parsing indent.
        # But we can look at indentation of current line.
        indent = len(line) - len(line.lstrip())

        if indent == 0 and stripped:
            inside_class = False
            inside_function = False

        # If we are inside class but NOT inside function (i.e. fields)
        if inside_class and not inside_function:
            # If line is indented 8 spaces (misindented field)
            if indent == 8 and stripped:
                # Unindent to 4 spaces
                # Check if it looks like a variable annotation to be safe
                if ":" in stripped or "=" in stripped:
                    new_lines.append("    " + stripped + "\n")
                    continue

        # If line implies function start?
        # If indent is 4 spaces and starts with 'def ', we handled it above.
        # If indent is 4 spaces and IS NOT 'def', it might be a field.
        # If indent is 0, we reset.

        new_lines.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Fixed fields in {filepath}")


if __name__ == "__main__":
    import os

    if len(sys.argv) > 1:
        fix_fields(sys.argv[1])
