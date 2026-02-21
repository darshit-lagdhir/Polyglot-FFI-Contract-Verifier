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
# File Integrity Identifier: ad4cc92dc1b1dc72
# ==============================================================================

import unittest
from unittest.mock import MagicMock
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, HotReloadManager
)

class TestReloadBasicSuccess(unittest.TestCase):
    def test_reload_swaps_metadata(self):
        meta1 = ContractMetadata(fingerprint="test_fp", architecture="x64", abi_fingerprint="abi1", descriptors={})
        meta2 = ContractMetadata(fingerprint="test_fp", architecture="x64", abi_fingerprint="abi1", descriptors={"new": {}})
        
        ctx = EnforcementContext("test_fp", meta1)
        
        def reload_handler():
            ctx.metadata = meta2
            
        ctx.hot_reload_manager.perform_reload(meta2, reload_handler)
        
        self.assertEqual(ctx.metadata.descriptors, {"new": {}})
        self.assertEqual(ctx.hot_reload_manager.reload_sequence_counter, 1)

if __name__ == "__main__":
    unittest.main()