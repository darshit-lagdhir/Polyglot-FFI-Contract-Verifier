"""
Crash Handler (Linux)
Placeholder for platform-specific context capture (Signals).
"""

import signal

def signal_handler(signum, frame):
    """Simple signal handler to ensure clean exit with code."""
    # Note: Parent uses returncode to detect signals
    pass

def install_signal_handlers():
    """Installs handlers for SIGSEGV, SIGABRT, etc."""
    # In v1.0, we let the signals terminate the process so the 
    # parent detects it via WTERMSIG.
    pass
