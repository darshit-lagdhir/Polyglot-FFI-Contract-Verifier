import sys
import re


def fix_indentation(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    inside_function = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue

        if stripped.startswith("def "):
            inside_function = True
            # Keep def line as is (assuming it's correct at 4 spaces usually)
            new_lines.append(line)
            continue

        if stripped.startswith("class "):
            inside_function = False
            new_lines.append(line)
            continue

        if inside_function:
            # Check indentation
            curr_indent = len(line) - len(line.lstrip())

            # Heuristics
            if curr_indent == 0:
                # Unindented code inside function -> Indent 8 spaces
                new_lines.append("        " + stripped + "\n")
            elif curr_indent == 16:
                # Double indented -> Unindent to 8 spaces
                new_lines.append("        " + stripped + "\n")
            elif curr_indent == 12:
                # Weird 12 spaces -> Unindent to 8
                new_lines.append("        " + stripped + "\n")
            else:
                # Keep as is (e.g. 8 spaces)
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Fixed {filepath}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_indentation(sys.argv[1])
