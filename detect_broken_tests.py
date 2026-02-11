import os
import ast


def find_syntax_errors(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".py"):
                path = os.path.join(dirpath, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    ast.parse(content, filename=path)
                except SyntaxError as e:
                    print(f"SyntaxError in {path}: line {e.lineno}, col {e.offset}: {e.msg}")
                except IndentationError as e:
                    print(f"IndentationError in {path}: line {e.lineno}: {e.msg}")
                except Exception as e:
                    print(f"Error reading {path}: {e}")


if __name__ == "__main__":
    find_syntax_errors("tests")
