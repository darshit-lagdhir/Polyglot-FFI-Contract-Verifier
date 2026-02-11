import re
import sys


def fix_indentation(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find: def func(self...): \n                code
    # And replace with: def func(self...): \n        code
    # We look for 16 spaces (tab issues?) or just excessive spaces.
    # The file seems to use 4 spaces per level.
    # Class level: 0
    # Method level: 4
    # Inside method: 8
    # Faulty indentation: 16 (double indented)

    # We want to replace 16 spaces with 8 spaces ONLY if it follows a def line
    # immediately.

    pattern = r"(def\s+[a-zA-Z0-9_]+\(self[^)]*\):\s*\n)(\s{16})(\S)"

    def replacer(match):
        header = match.group(1)
        indent = match.group(2)
        char = match.group(3)
        # return header + 8 spaces + char
        return header + "        " + char

    new_content = re.sub(pattern, replacer, content)

    # We also need to fix subsequent lines if they were indented relative to the first line.
    # If we only fix the first line, the rest will be "unindent does not match".
    # This is complex with regex.
    # Better approach: parse file line by line.

    return new_content


def fix_indentation_line_by_line(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for Method Definition (4 spaces indent)
        # Note: This regex assumes standard 4-space indent for class methods
        method_match = re.match(r"^(\s{4})def\s+\w+", line)
        if method_match:
            new_lines.append(line)
            i += 1
            if i >= len(lines):
                break

            # Look ahead to see indentation of body
            # Skip empty lines
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1

            if j < len(lines):
                # Check for docstring (8 spaces indent is correct)
                # If docstring starts with 16 spaces, we fix it too.
                # If docstring starts with 8 spaces, we skip it and check code
                # after.

                check_line = lines[j]
                indent_match = re.match(r"^(\s+)", check_line)
                indent_len = len(indent_match.group(1)) if indent_match else 0

                # If first significant line has 16 spaces indent -> Fix Block
                if indent_len == 16:
                    print(f"Fixing indentation block starting at line {j + 1}")
                    # Capture formatting from now until dedent
                    while i < len(lines):
                        curr_line = lines[i]
                        curr_indent_match = re.match(r"^(\s+)", curr_line)
                        curr_indent = len(curr_indent_match.group(1)) if curr_indent_match else 0

                        if not curr_line.strip():
                            new_lines.append(curr_line)
                            i += 1
                            continue

                        # Stop if indentation drops below 8 (end of method/class)
                        # Wait, normal method body is 8 spaces.
                        # So stop if < 8? Or stop if < 16 and not empty?
                        # If we are fixing a 16->8 shift, then originally it was 16.
                        # If next method starts (4 spaces), we stop.
                        if curr_indent <= 4:
                            break

                        # Reduce indentation by 8 spaces
                        # But be careful not to consume essential indentation (e.g. if loop inside method had 20 spaces)
                        # We want to remove *exactly* 8 spaces prefix if
                        # possible.
                        if curr_line.startswith("        "):
                            new_line = curr_line[8:]
                        else:
                            new_line = curr_line.lstrip()  # Fallback

                        new_lines.append(new_line)
                        i += 1
                    continue

                # Else: indentation is correct or handled manually

        new_lines.append(line)
        i += 1

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Fixed {filepath}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_indentation_line_by_line(sys.argv[1])
    else:
        print("Usage: python fix_indentation.py <filepath>")
