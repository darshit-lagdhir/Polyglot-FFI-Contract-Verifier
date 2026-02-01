"""
Generated struct definitions for test_library.

Auto-created by Polyglot FFI Contract Verifier.
DO NOT EDIT MANUALLY.
"""

import ctypes
from . import test_library_exceptions as exceptions

class Config(ctypes.Structure):
    """
    Native struct 'Config' binding.
    Size: 16 bytes
    Alignment: 8 bytes
    """
    _fields_ = [
        ("mode", ctypes.c_void_p),
        ("data", ctypes.c_void_p),
    ]

    def __init__(self, **kwargs):
        super().__init__()
        actual_size = ctypes.sizeof(self)
        if actual_size != 16:
            raise exceptions.LayoutMismatchError(
                "struct:Config",
                f"Struct Config has size {actual_size} bytes, expected 16 bytes"
            )
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise ValueError(f"Unknown field: {key}")
            setattr(self, key, value)

