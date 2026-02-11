import os
import py_compile
import re


def fix_all_file_errors(path):
    print(f"Fixing {path}")
    iters = 0
    while iters < 1000:
        try:
            py_compile.compile(path, doraise=True)
            print(f"  {path} is fixed!")
            return True
        except py_compile.PyCompileError as e:
            msg = str(e)
            m = re.search(r"line (\d+)", msg)
            if not m:
                print(f"  Could not find line in error: {msg}")
                break
            ln = int(m.group(1))
            idx = ln - 1

            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if idx >= len(lines):
                break
            line = lines[idx]

            if "expected an indented block" in msg:
                print(f"  Line {ln}: adding indentation")
                lines[idx] = "    " + line
            elif (
                "unindent does not match" in msg
                or "unexpected indent" in msg
                or "invalid syntax" in msg
            ):
                # This is likely a dedent keyword that belongs to a parent
                # Try to dedent it until it works or match previous
                stripped = line.lstrip()
                curr_ind = len(line) - len(stripped)
                if curr_ind >= 4:
                    print(f"  Line {ln}: dedenting")
                    lines[idx] = " " * (curr_ind - 4) + stripped
                else:
                    # Stymied. Try to remove the line if it's junk or just skip
                    print(f"  Line {ln}: cannot dedent further")
                    break
            else:
                print(f"  Unknown error at {ln}: {msg}")
                break

            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            iters += 1
    return False


if __name__ == "__main__":
    targets = [
        r"modules\module_01_ffi_verifier\system_architecture.py",
        r"modules\module_02_verification_pipeline\verification_pipeline.py",
        r"modules\module_03_build_process\build_process.py",
        r"modules\module_04_native_interface_ingestion\native_interface_ingestion.py",
    ]
    for t in targets:
        if os.path.exists(t):
            fix_all_file_errors(t)

    # Generic sweep
    for root, dirs, files in os.walk("."):
        if any(x in root for x in ["venv", ".git", ".gemini"]):
            continue
        for f in files:
            if f.endswith(".py") and not f.endswith("fixer.py"):
                path = os.path.join(root, f)
                if "module" in path or "tests" in path:
                    # try it
                    try:
                        py_compile.compile(path, doraise=True)
                    except:
                        fix_all_file_errors(path)
