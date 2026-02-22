# ==============================================================================
# Polyglot FFI Contract Verifier - Unit Tests
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
# ==============================================================================
import unittest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, RuntimeConfiguration, TransitionAuditRecord, LifecycleState, LifecycleReason
)

class TestMemoryCompaction(unittest.TestCase):
    def test_history_capping(self):
        meta = ContractMetadata("1.0", "0.1", "fp", 64, {})
        ctx = EnforcementContext("fp", meta)
        ctx.config_controller.update(RuntimeConfiguration(max_transition_history_per_pointer=5))
        
        ctx.registry.register(0x123, "f", "caller_owned", "fp")
        record = ctx.registry.get_record(0x123, "fp", 0)
        
        # Add 10 history entries
        for i in range(10):
            record.append_audit(TransitionAuditRecord(
                pointer=0x123,
                from_state=LifecycleState.UNREGISTERED,
                to_state=LifecycleState.REGISTERED_CALLER_OWNED,
                reason=LifecycleReason.INITIAL_REGISTRATION,
                function_name="f",
                access_index=i
            ))
            
        ctx.registry.compact_history()
        self.assertEqual(len(record.history), 5)

if __name__ == "__main__":
    unittest.main()
