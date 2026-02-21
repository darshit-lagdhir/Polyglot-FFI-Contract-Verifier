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
# File Integrity Identifier: 97907acef45a3a7f
# ==============================================================================

import unittest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, RuntimeConfiguration
)

class TestProfilingIsolation(unittest.TestCase):
    def test_isolation(self):
        ctx1 = EnforcementContext("fp1", ContractMetadata("fp1", "x64", "abi1", {}))
        ctx2 = EnforcementContext("fp2", ContractMetadata("fp2", "x64", "abi2", {}))
        ctx1.config_controller.update(RuntimeConfiguration(profiling_enabled=True))
        ctx2.config_controller.update(RuntimeConfiguration(profiling_enabled=True))
        
        ctx1.profiling_manager.increment("f", "invocation_count", 1)
        ctx2.profiling_manager.increment("f", "invocation_count", 2)
        
        self.assertEqual(ctx1.get_profiling_summary()["f"]["invocation_count"], 1)
        self.assertEqual(ctx2.get_profiling_summary()["f"]["invocation_count"], 2)

if __name__ == "__main__":
    unittest.main()