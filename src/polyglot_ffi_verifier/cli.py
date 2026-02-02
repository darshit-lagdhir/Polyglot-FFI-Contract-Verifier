"""Command-line interface."""

import sys
import os

# Add the modules directory to sys.path
MODULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'modules', 'module_02_verification_pipeline')
if MODULES_PATH not in sys.path:
    sys.path.insert(0, MODULES_PATH)

try:
    from verification_pipeline import cli_main
except ImportError:
    # Handle error or provide a basic main if not found
    def cli_main():
        print("Error: Could not find verification_pipeline module.")
        return 1

def main():
    """Main CLI entry point."""
    return cli_main()

if __name__ == '__main__':
    sys.exit(main())
