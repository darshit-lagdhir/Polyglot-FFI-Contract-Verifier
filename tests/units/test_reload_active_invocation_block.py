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
# File Integrity Identifier: 03c1fd8c6dde3468
# ==============================================================================

import unittest
from unittest.mock import MagicMock
from modules.module_08_language_adapter.language_adapter import (
    LanguageAdapter, EnforcementContext, ContractMetadata, ReloadInProgressError
)

class TestReloadActiveInvocationBlock(unittest.TestCase):
    def test_invocation_blocked_during_reload(self):
        meta = ContractMetadata(fingerprint="test_fp", architecture="x64", abi_fingerprint="abi1", descriptors={})
        adapter = LanguageAdapter()
        ctx = adapter._manager.register_context("test_fp", meta)
        
        # Manually set reload in progress
        ctx.hot_reload_manager.reload_in_progress = True
        
        with self.assertRaises(ReloadInProgressError):
            adapter.validate_invocation("func1", [], "test_fp")

if __name__ == "__main__":
    unittest.main()