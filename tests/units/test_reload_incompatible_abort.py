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
# File Integrity Identifier: 493c86f2e16296ff
# ==============================================================================

import unittest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, ReloadCompatibilityError
)

class TestReloadIncompatible(unittest.TestCase):
    def test_abi_mismatch_aborts(self):
        meta1 = ContractMetadata(fingerprint="fp", architecture="x64", abi_fingerprint="abi1", descriptors={})
        meta2 = ContractMetadata(fingerprint="fp", architecture="x64", abi_fingerprint="abi2", descriptors={})
        
        ctx = EnforcementContext("fp", meta1)
        
        with self.assertRaises(ReloadCompatibilityError):
            ctx.hot_reload_manager.perform_reload(meta2, lambda: None)

if __name__ == "__main__":
    unittest.main()
