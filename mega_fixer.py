import os
import py_compile
import re
import subprocess


def fix_indentation_errors(path):
    print(f"Fixing {path}...")
    for i in range(2000):  # High limit for complex files
        try:
            py_compile.compile(path, doraise=True)
            print(f"  {path} is now valid!")
            return True
        except py_compile.PyCompileError as e:
            msg = str(e)
            m = re.search(r"line (\d+)", msg)
            if not m:
                break
            ln = int(m.group(1))
            idx = ln - 1

            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if idx >= len(lines):
                break
            line = lines[idx]
            stripped = line.lstrip()
            if not stripped:
                lines[idx] = "\n"
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                continue

            curr_indent = len(line) - len(stripped)

            # Case 1: Expected an indented block
            if "expected an indented block" in msg:
                # Find previous block starter
                for j in range(idx - 1, -1, -1):
                    if lines[j].strip():
                        p_ind = len(lines[j]) - len(lines[j].lstrip())
                        lines[idx] = " " * (p_ind + 4) + stripped
                        print(f"  L{ln}: Indented to {p_ind+4}")
                        break

            # Case 2: Unindent does not match any outer level
            elif (
                "unindent does not match" in msg
                or "unexpected indent" in msg
                or "invalid syntax" in msg
            ):
                # For invalid syntax on elif/else/except/finally
                if stripped.startswith(("elif ", "else:", "except", "finally:")):
                    # It's likely too far OUT or too far IN.
                    # Try to find the matching 'if' or 'try' by matching its current indent or finding the nearest parent.
                    # As a broad heuristic, let's try to INCREMENT its indent by 4 first if it's too low,
                    # OR match the last 'if'/'try' that ended in ':'
                    found = False
                    for j in range(idx - 1, -1, -1):
                        p_line = lines[j].strip()
                        if not p_line:
                            continue
                        p_ind = len(lines[j]) - len(lines[j].lstrip())

                        # If we find a colon-ending line at any level >= curr_indent, it might be a sibling's child
                        # But we want the parent.
                        # Actually, let's try to see if indenting it +4 fixes it.
                        pass

                    # Simpler: just match the previous line's indent and if that fails, try prev-prev...
                    # Wait, for a dedent keyword, it should be at the SAME level as some previous block starter.
                    match_found = False
                    for j in range(idx - 1, -1, -1):
                        p_line = lines[j].strip()
                        if not p_line:
                            continue
                        if p_line.endswith(":"):
                            p_ind = len(lines[j]) - len(lines[j].lstrip())
                            # If we match this level, we might be sibling
                            # If we match this level + 4, we are child (illegal)
                            # Let's try matching p_ind
                            lines[idx] = " " * p_ind + stripped
                            # we'll see if it compiles next iteration
                            match_found = True
                            print(f"  L{ln}: Matched level {p_ind} from L{j+1}")
                            break
                    if not match_found:
                        lines[idx] = "    " + line  # last resort
                else:
                    # Not a dedent keyword. Just try to match previous line's indent
                    for j in range(idx - 1, -1, -1):
                        if lines[j].strip():
                            p_ind = len(lines[j]) - len(lines[j].lstrip())
                            lines[idx] = " " * p_ind + stripped
                            print(f"  L{ln}: Matched level {p_ind} from L{j+1}")
                            break

            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)

    return False


if __name__ == "__main__":
    targets = [
        r"modules\module_04_native_interface_ingestion\native_interface_ingestion.py",
        r"modules\module_01_ffi_verifier\system_architecture.py",
        r"modules\module_03_build_process\build_process.py",
        r"modules\module_02_verification_pipeline\verification_pipeline.py",
    ]
    for t in targets:
        if os.path.exists(t):
            fix_indentation_errors(t)
            # Polish with black
            subprocess.run(["black", t], capture_output=True)
            # Final check
            try:
                py_compile.compile(t, doraise=True)
                print(f"FINAL: {t} is VALID")
            except Exception as e:
                print(f"FINAL: {t} still FAILED: {e}")
