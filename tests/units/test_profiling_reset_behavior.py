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
# File Integrity Identifier: f7a746cc383173ee
# ==============================================================================

import unittest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, RuntimeConfiguration
)

class TestProfilingReset(unittest.TestCase):
    def test_reset_clears_metrics(self):
        ctx = EnforcementContext("fp", ContractMetadata("fp", "x64", "abi1", {}))
        ctx.config_controller.update(RuntimeConfiguration(profiling_enabled=True))
        ctx.profiling_manager.increment("f", "invocation_count")
        
        ctx.reset_profiling_metrics()
        self.assertEqual(ctx.get_profiling_summary(), {})

if __name__ == "__main__":
    unittest.main()
