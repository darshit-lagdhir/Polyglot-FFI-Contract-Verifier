#!/usr/bin/env python3
"""Bump version number."""

import re
import sys
from pathlib import Path

def bump_version(part: str):
    """Bump version (major, minor, or patch)."""
    version_file = Path("src/polyglot_ffi_verifier/__version__.py")
    if not version_file.exists():
        print(f"Error: {version_file} not found")
        sys.exit(1)
        
    content = version_file.read_text()
    
    # Extract current version
    match = re.search(r'__version__ = "(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        print("Error: Could not find version string in file")
        sys.exit(1)
        
    major, minor, patch = map(int, match.groups())
    
    # Bump appropriate part
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Update file
    new_content = re.sub(
        r'__version__ = "\d+\.\d+\.\d+"',
        f'__version__ = "{new_version}"',
        content
    )
    new_content = re.sub(
        r'__version_info__ = \(\d+, \d+, \d+\)',
        f'__version_info__ = ({major}, {minor}, {patch})',
        new_content
    )
    
    version_file.write_text(new_content)
    print(f"Version bumped to {new_version}")
    
    # Also update pyproject.toml if it exists
    pyproject_file = Path("pyproject.toml")
    if pyproject_file.exists():
        py_content = pyproject_file.read_text()
        new_py_content = re.sub(
            r'version = "\d+\.\d+\.\d+"',
            f'version = "{new_version}"',
            py_content
        )
        pyproject_file.write_text(new_py_content)
        print(f"Updated pyproject.toml to {new_version}")
        
    return new_version

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["major", "minor", "patch"]:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)
    
    bump_version(sys.argv[1])
