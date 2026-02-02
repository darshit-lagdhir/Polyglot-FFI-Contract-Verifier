"""Polyglot FFI Contract Verifier."""

import sys
import os

# Add the modules directory to sys.path so we can import verification_pipeline
# This ensures that when the package is installed, it can find the core logic.
# In a real production scenario, we might move verification_pipeline.py into this folder,
# but to maintain the module-based project structure, we use this bridge.
MODULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'modules', 'module_02_verification_pipeline')
if MODULES_PATH not in sys.path:
    sys.path.insert(0, MODULES_PATH)

from .__version__ import __version__

# Re-export main functions
try:
    from verification_pipeline import (
        verify,
        verify_optimized,
        verify_extensible,
        VerificationResult
    )
except ImportError:
    # Fallback for different environments or if pathing is slightly different
    # (The above sys.path insertion should handle it usually)
    pass

__all__ = [
    '__version__',
    'verify',
    'verify_optimized',
    'verify_extensible',
    'VerificationResult'
]
