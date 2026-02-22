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
# File Integrity Identifier: 6d6eeb6dae7907ad
# ==============================================================================

import unittest
import threading
import time
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    LanguageAdapter, 
    MultiContractContextManager, 
    EnforcementContext,
    ContractMetadata,
    OwnershipViolationError
)

class TestConcurrencyHardening(unittest.TestCase):
    """
    Stress tests for concurrency hardening framework.
    """

    def setUp(self):
        self.manager = MultiContractContextManager.get_instance()
        # Mock metadata
        self.metadata = ContractMetadata(
            schema_version="1.0",
            synthesis_version="0.1.0",
            fingerprint="TEST_FINGERPRINT_0123456789",
            abi_bits=64,
            descriptors={}
        )
        self.context = self.manager.register_context(self.metadata.fingerprint, self.metadata)

    def test_concurrent_registration(self):
        """Test concurrent pointer registration in the same segment."""
        errors = []
        def task(ptr):
            try:
                self.context.registry.register(ptr, "test_func", "caller_owned", self.metadata.fingerprint)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(100):
            t = threading.Thread(target=task, args=(0x1000 + i,))
            threads.append(t)
        
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(len(errors), 0, f"Concurrent registration failed: {errors}")

    def test_lock_hierarchy_violation(self):
        """Test that lock hierarchy enforcement works."""
        from modules.module_08_language_adapter.language_adapter import HierarchicalLock, LOCK_LEVEL_CONFIG, LOCK_LEVEL_POINTER
        
        lock_config = HierarchicalLock(LOCK_LEVEL_CONFIG, "Config")
        lock_pointer = HierarchicalLock(LOCK_LEVEL_POINTER, "Pointer")

        try:
            with lock_pointer:
                with lock_config: # Illegal: Level 1 inside Level 3
                    pass
            self.fail("Should have raised RuntimeError for hierarchy violation")
        except RuntimeError as e:
            self.assertIn("Lock acquisition violation", str(e))

    def test_multi_contract_isolation(self):
        """Test that two contracts have isolated registries."""
        meta2 = ContractMetadata(
            schema_version="1.0",
            synthesis_version="0.1.0",
            fingerprint="ANOTHER_FINGERPRINT_987654321",
            abi_bits=64,
            descriptors={}
        )
        ctx2 = self.manager.register_context(meta2.fingerprint, meta2)

        ptr = 0xABCD
        self.context.registry.register(ptr, "func1", "caller_owned", self.metadata.fingerprint)
        
        # ptr should NOT be in ctx2
        record = ctx2.registry._get_record(ptr, meta2.fingerprint, 0)
        self.assertIsNone(record)

if __name__ == "__main__":
    unittest.main()
