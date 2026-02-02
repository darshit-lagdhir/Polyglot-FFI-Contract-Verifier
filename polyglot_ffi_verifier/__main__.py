"""
Entry point for running Polyglot FFI Verifier as a module.
Usage: python -m polyglot_ffi_verifier [command] [options]
"""

import sys
from .pipeline import CLIOrchestrator

def main():
    orchestrator = CLIOrchestrator()
    sys.exit(orchestrator.run())

if __name__ == "__main__":
    main()
