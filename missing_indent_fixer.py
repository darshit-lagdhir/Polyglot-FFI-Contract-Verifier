import os
import re


def fix_missing_indent(path):
    print(f"Checking {path}")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    fixed = False
    new_lines = []
    for i in range(len(lines)):
        line = lines[i]
        new_lines.append(line)
        if line.strip().endswith(":"):
            indent = len(line) - len(line.lstrip())
            # Check next non-empty line
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    next_indent = len(lines[j]) - len(lines[j].lstrip())
                    if next_indent <= indent and not lines[j].strip().startswith(
                        ("#", "elif ", "else:", "except", "finally:")
                    ):
                        # This line SHOULD be indented
                        lines[j] = " " * (indent + 4) + lines[j].lstrip()
                        print(f"  Fixed missing indent at line {j+1}")
                        fixed = True
                    break

    if fixed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)


if __name__ == "__main__":
    targets = [
        r"modules\module_04_native_interface_ingestion\native_interface_ingestion.py",
        r"modules\module_01_ffi_verifier\system_architecture.py",
        r"modules\module_03_build_process\build_process.py",
        r"modules\module_02_verification_pipeline\verification_pipeline.py",
    ]
    for t in targets:
        if os.path.exists(t):
            fix_missing_indent(t)
