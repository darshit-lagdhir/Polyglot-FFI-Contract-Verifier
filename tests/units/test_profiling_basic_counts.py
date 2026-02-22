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
# File Integrity Identifier: aab98fd4c873db12
# ==============================================================================

import unittest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    LanguageAdapter, RuntimeConfiguration, EnforcementContext, ContractMetadata
)

class TestProfilingBasicCounts(unittest.TestCase):
    def test_invocation_count_increments(self):
        config = RuntimeConfiguration(profiling_enabled=True)
        meta = ContractMetadata(fingerprint="test_fp", architecture="x64", abi_fingerprint="abi1", descriptors={"func1": {}})
        ctx = EnforcementContext("test_fp", meta)
        ctx.config_controller.update(config)
        
        pm = ctx.profiling_manager
        pm.increment("func1", "invocation_count")
        pm.increment("func1", "invocation_count")
        
        summary = pm.get_summary()
        self.assertEqual(summary["func1"]["invocation_count"], 2)

if __name__ == "__main__":
    unittest.main()
