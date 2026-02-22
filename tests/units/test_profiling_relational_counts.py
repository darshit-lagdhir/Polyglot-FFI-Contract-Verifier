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
# File Integrity Identifier: 5cdffaf23cc7e0db
# ==============================================================================

import unittest
from unittest.mock import MagicMock
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    ValidationEngine, ValidationGraph, ValidationNode, EnforcementContext, ContractMetadata, RuntimeConfiguration
)

class TestProfilingRelationalCounts(unittest.TestCase):
    def test_relational_increment(self):
        engine = ValidationEngine()
        graph = ValidationGraph()
        node = ValidationNode(clause_id="C1", predicate=lambda x, p: True, parameters={"clause_type": "relational"})
        graph.add_node(node)
        
        meta = ContractMetadata(fingerprint="test_fp", architecture="x64", abi_fingerprint="abi1", descriptors={})
        ctx = EnforcementContext("test_fp", meta)
        ctx.config_controller.update(RuntimeConfiguration(profiling_enabled=True))
        
        engine.validate(graph, [], ctx, "func1")
        
        summary = ctx.get_profiling_summary()
        self.assertEqual(summary["func1"]["relational_checks"], 1)

if __name__ == "__main__":
    unittest.main()
