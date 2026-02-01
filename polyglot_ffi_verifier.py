"""
Polyglot FFI Contract Verifier - Main Entry Point

This is the main entry point for the verification system.
It delegates to the CLI orchestrator for command handling.
"""

from src.core.orchestration import main

if __name__ == "__main__":
    main()
