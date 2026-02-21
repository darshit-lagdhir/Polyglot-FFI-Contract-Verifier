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
# File Integrity Identifier: fa542027298cde0b
# ==============================================================================

import unittest
from modules.module_08_language_adapter.language_adapter import (
    ClauseSeverity, DynamicEnforcementPolicyManager, EnforcementContext, ContractMetadata
)

class TestPolicyDefault(unittest.TestCase):
    def test_default_is_fatal_in_absence_of_rule(self):
        ctx = EnforcementContext("fp", ContractMetadata("fp", "x64", "abi1", {}))
        self.assertEqual(ctx.policy_manager.get_effective_severity("C1", 0), ClauseSeverity.FATAL)

if __name__ == "__main__":
    unittest.main()