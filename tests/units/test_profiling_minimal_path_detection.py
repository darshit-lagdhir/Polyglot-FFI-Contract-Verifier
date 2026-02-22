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
# File Integrity Identifier: 12a2aa4ad7bc5202
# ==============================================================================

import unittest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    ValidationEngine, ValidationGraph, EnforcementContext, ContractMetadata, RuntimeConfiguration
)

class TestProfilingMinimalPath(unittest.TestCase):
    def test_minimal_path_detection(self):
        engine = ValidationEngine()
        graph = ValidationGraph() # Empty graph = minimal path
        
        meta = ContractMetadata(fingerprint="test_fp", architecture="x64", abi_fingerprint="abi1", descriptors={})
        ctx = EnforcementContext("test_fp", meta)
        ctx.config_controller.update(RuntimeConfiguration(profiling_enabled=True))
        
        engine.validate(graph, [], ctx, "func1")
        
        summary = ctx.get_profiling_summary()
        self.assertEqual(summary["func1"]["sandbox_invocations"], 1)

if __name__ == "__main__":
    unittest.main()
