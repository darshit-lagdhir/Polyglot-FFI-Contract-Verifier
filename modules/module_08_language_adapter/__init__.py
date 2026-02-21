# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: 33cdf36711219b30
# ==============================================================================

"""
Language Adapter - Complete API Export
"""
from .__version__ import __version__
from .language_adapter import *
from .testing_utils import *
from .persistence import *
from .observability import *

def create_adapter(contract_path=None, config=None):
    adapter = PythonAdapterComplete(config)
    if contract_path:
        adapter.load_contract(contract_path)
    return adapter

def load_contract(contract_path: str):
    adapter = PythonAdapterComplete()
    return adapter.load_contract(contract_path)

def enforce_contract(contract_path: str):
    """Decorator to enforce contract on a function."""
    adapter = create_adapter(contract_path)
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(adapter, *args, **kwargs)
        return wrapper
    return decorator