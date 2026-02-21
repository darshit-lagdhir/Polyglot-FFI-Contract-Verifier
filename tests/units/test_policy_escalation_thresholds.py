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
# File Integrity Identifier: 21eabfdb36174160
# ==============================================================================

import unittest
from modules.module_08_language_adapter.language_adapter import (
    ClauseSeverity, ClausePolicyRule, DynamicEnforcementPolicyManager, EnforcementContext, ContractMetadata
)

class TestPolicyEscalationThresholds(unittest.TestCase):
    def test_escalation_logic(self):
        meta = ContractMetadata(fingerprint="test_fp", architecture="x64", abi_fingerprint="abi1", descriptors={})
        ctx = EnforcementContext("test_fp", meta)
        policy_mgr = ctx.policy_manager
        
        rule = ClausePolicyRule(
            clause_id="C1",
            default_severity=ClauseSeverity.WARNING,
            escalation_thresholds=[(5, ClauseSeverity.ERROR), (10, ClauseSeverity.FATAL)]
        )
        policy_mgr.register_rule(rule)
        
        # 0 occurrences
        self.assertEqual(policy_mgr.get_effective_severity("C1", 0), ClauseSeverity.WARNING)
        # 5 occurrences
        self.assertEqual(policy_mgr.get_effective_severity("C1", 5), ClauseSeverity.ERROR)
        # 10 occurrences
        self.assertEqual(policy_mgr.get_effective_severity("C1", 10), ClauseSeverity.FATAL)

if __name__ == "__main__":
    unittest.main()