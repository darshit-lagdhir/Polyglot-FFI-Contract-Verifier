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
# File Integrity Identifier: a4a6a9ab4e33fb18
# ==============================================================================

import unittest
from modules.module_08_language_adapter.language_adapter import (
    ClauseSeverity, ClausePolicyRule, EnforcementContext, ContractMetadata, ValidationEngine, ValidationGraph, ValidationNode
)

class TestPolicyIgnore(unittest.TestCase):
    def test_ignore_behavior(self):
        ctx = EnforcementContext("fp", ContractMetadata("fp", "x64", "abi1", {}))
        ctx.policy_manager.register_rule(ClausePolicyRule("C1", ClauseSeverity.IGNORE))
        
        engine = ValidationEngine()
        graph = ValidationGraph()
        # A predicate that returns False but should be IGNORED
        node = ValidationNode("C1", predicate=lambda x, p: False)
        graph.add_node(node)
        
        # Should return True because C1 is IGNORED
        result = engine.validate(graph, [], ctx, "f1")
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()