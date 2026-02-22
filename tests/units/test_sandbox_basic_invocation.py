# ==============================================================================
# Polyglot FFI Contract Verifier - Unit Tests
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
# ==============================================================================
import unittest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, RuntimeConfiguration, LanguageAdapter, ContractProjector
)
import os

class TestSandboxBasic(unittest.TestCase):
    def test_sandbox_invocation_success(self):
        # Setup minimal context
        meta = ContractMetadata(
            schema_version="1.0",
            synthesis_version="0.1",
            fingerprint="test_fp_sandbox_basic",
            abi_bits=64 if os.sys.maxsize > 2**32 else 32,
            descriptors={}
        )
        ctx = EnforcementContext("test_fp_sandbox_basic", meta)
        ctx.config_controller.update(RuntimeConfiguration(sandbox_enabled=True))
        
        # Test basic start/stop
        ctx.sandbox_manager.start_worker()
        self.assertTrue(ctx.sandbox_manager.worker_process.is_alive())
        ctx.sandbox_manager.stop_worker()
        self.assertFalse(ctx.sandbox_manager.worker_process)

if __name__ == "__main__":
    unittest.main()
