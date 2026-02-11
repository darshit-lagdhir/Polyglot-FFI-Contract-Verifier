import os
import py_compile


def find_bad_files():
    bad = []
    for root, ds, fs in os.walk("."):
        if any(x in root for x in ["venv", ".git", ".gemini"]):
            continue
        for f in fs:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    py_compile.compile(path, doraise=True)
                except Exception as e:
                    bad.append((path, str(e)))
    return bad


if __name__ == "__main__":
    for p, e in find_bad_files():
        print(f"{p} ERROR: {e}")
