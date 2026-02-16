"""
Script to bump the version number in Module 07.
"""

import sys
import re
from pathlib import Path

def bump_version(new_version):
    """Update __version__.py with the new version string."""
    version_file = Path("modules/module_07_contract_synthesis/__version__.py")
    
    if not version_file.exists():
        print(f"Error: {version_file} not found")
        sys.exit(1)
        
    content = version_file.read_text()
    
    # Update __version__ = 'X.Y.Z'
    new_content = re.sub(
        r"__version__ = '[\d\.]+'",
        f"__version__ = '{new_version}'",
        content
    )
    
    # Update __version_info__ = (X, Y, Z)
    v_parts = new_version.split('.')
    new_version_info = f"__version_info__ = ({', '.join(v_parts)})"
    new_content = re.sub(
        r"__version_info__ = \([\d, ]+\)",
        new_version_info,
        new_content
    )
    
    version_file.write_text(new_content)
    print(f"Updated {version_file} to version {new_version}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bump_version.py <new_version>")
        sys.exit(1)
        
    bump_version(sys.argv[1])
