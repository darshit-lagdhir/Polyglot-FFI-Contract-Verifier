import os


def normalize_file(path):
    print(f"Normalizing {path}")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    # (indent, type)
    stack = [(0, "top")]

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            new_lines.append("\n")
            continue

        content = line.lstrip()
        actual_indent = len(line) - len(content)

        # Rule 1: Sibling detection for dedent keywords
        dedent_keys = {"elif ": "if", "else:": "if", "except": "try", "finally:": "try"}
        target_indent = None
        for key, p_type in dedent_keys.items():
            if content.startswith(key):
                # Search stack for matching parent or ancestor
                for s_ind, s_type in reversed(stack):
                    if (key == "else:" and s_type in ["if", "for", "while", "try"]) or (
                        s_type == p_type
                    ):
                        target_indent = s_ind
                        break
                break

        if target_indent is not None:
            curr_indent = target_indent
        else:
            # Rule 2: Child detection
            if i > 0 and lines[i - 1].strip().endswith(":"):
                prev_indent = len(new_lines[-1]) - len(new_lines[-1].lstrip())
                curr_indent = prev_indent + 4
            else:
                # Rule 3: Try to keep actual unless it's obviously bad (like 0 or 4 inside a block)
                if (
                    actual_indent == 0
                    and stack[-1][0] > 0
                    and not content.startswith(
                        ("class ", "def ", "import ", "from ", "#", "@", '"""')
                    )
                ):
                    curr_indent = stack[-1][0]
                elif (
                    actual_indent < 8
                    and stack[-1][1] in ["class", "def"]
                    and not content.startswith(("class ", "def ", "import ", "from ", "#", "@"))
                ):
                    # Heuristic: inside a class/def, everything usually >= 8 (if class at 0, def at 4)
                    # If we unindented too far, it's likely a mistake
                    curr_indent = stack[-1][0]
                else:
                    curr_indent = actual_indent

        # Final sanity check: multiple of 4
        if curr_indent % 4 != 0:
            curr_indent = (curr_indent // 4) * 4

        # Update stack
        if content.endswith(":"):
            b_type = "unknown"
            if content.startswith("if "):
                b_type = "if"
            elif content.startswith("try:"):
                b_type = "try"
            elif content.startswith("for "):
                b_type = "for"
            elif content.startswith("while "):
                b_type = "while"
            elif content.startswith("class "):
                b_type = "class"
            elif content.startswith("def "):
                b_type = "def"

            while stack and curr_indent < stack[-1][0]:
                stack.pop()

            if not stack or curr_indent > stack[-1][0]:
                stack.append((curr_indent, b_type))
            else:
                stack[-1] = (curr_indent, b_type)
        else:
            while stack and curr_indent < stack[-1][0]:
                stack.pop()

        new_lines.append(" " * curr_indent + content)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


if __name__ == "__main__":
    for root, ds, fs in os.walk("."):
        if any(x in root for x in ["venv", ".git", ".gemini"]):
            continue
        for f in fs:
            if (
                f.endswith(".py")
                and not f.endswith("fixer.py")
                and not f.endswith("find_bad.py")
                and not f.endswith("get_errors.py")
            ):
                normalize_file(os.path.join(root, f))

    os.system("black .")
