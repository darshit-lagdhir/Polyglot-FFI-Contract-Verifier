import sys
import os


def remove_adjacent_duplicates(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    prev_line = None

    for line in lines:
        stripped = line.strip()
        if not stripped:  # Keep blank lines? Yes.
            new_lines.append(line)
            prev_line = stripped
            continue

        if stripped == prev_line:
            print(f"Removed duplicate line: {stripped}")
            continue  # Skip duplicate

        new_lines.append(line)
        prev_line = stripped

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Cleaned {filepath}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        remove_adjacent_duplicates(sys.argv[1])
    else:
        # If no arg, run on ALL py files in tests/ (risky? but duplicate code
        # is bad anyway)
        for root, dirs, files in os.walk("tests"):
            for file in files:
                if file.endswith(".py"):
                    remove_adjacent_duplicates(os.path.join(root, file))
