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
# File Integrity Identifier: aaa02a5465af2a3c
# ==============================================================================

import unittest
import ctypes
from dataclasses import dataclass
from typing import List, Optional
import sys
import os

# Set PYTHONPATH
sys.path.append(os.getcwd())

from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    LifecycleState,
    LifecycleReason,
    LifecycleStateModel,
    TransitionCoordinator,
    OwnershipRegistry,
    PointerOwnershipRecord,
    OwnershipViolationError,
    ContractViolationError,
    StructureMutationValidator,
    ContractRuntimeLoader,
    _canonical_pointer_key,
    TransitionAuditRecord
)

class TestLifecycleMutationGovernance(unittest.TestCase):

    def setUp(self):
        self.registry = OwnershipRegistry()
        self.coordinator = self.registry._transition_coordinator
        self.fingerprint = "test_fingerprint"

    def test_formal_state_machine_validation(self):
        """Verify the static transition matrix enforces legal paths."""
        self.assertTrue(LifecycleStateModel.validate_transition(
            LifecycleState.UNREGISTERED, LifecycleState.REGISTERED_CALLER_OWNED))
        self.assertFalse(LifecycleStateModel.validate_transition(
            LifecycleState.FREED, LifecycleState.REGISTERED_CALLER_OWNED))
        self.assertFalse(LifecycleStateModel.validate_transition(
            LifecycleState.TERMINAL_INVALID, LifecycleState.REGISTERED_CALLER_OWNED))

    def test_transition_coordinator_enforcement(self):
        """Verify TransitionCoordinator rejects illegal mutations."""
        ptr = 0x1234
        self.registry.register(ptr, "alloc", "caller_owned", self.fingerprint)
        
        # Current state: REGISTERED_CALLER_OWNED
        # Attempt illegal transition to REGISTERED_CALLEE_OWNED
        with self.assertRaises(OwnershipViolationError) as cm:
            self.coordinator.transition_to(
                ptr, self.fingerprint, 0,
                LifecycleState.REGISTERED_CALLEE_OWNED,
                "Illegal test"
            )
        self.assertIn("Illegal transition", str(cm.exception))
        
        # Verify terminal state after illegal transition
        key = _canonical_pointer_key(ptr, self.fingerprint, 0)
        self.assertEqual(self.registry._registry[key].state, LifecycleState.TERMINAL_INVALID)

    def test_audit_history_integrity(self):
        """Verify TransitionAuditRecord history is preserved and capped."""
        ptr = 0xABCD
        self.registry.register(ptr, "alloc", "caller_owned", self.fingerprint)
        
        key = _canonical_pointer_key(ptr, self.fingerprint, 0)
        record = self.registry._registry[key]
        
        # After register, history should have INITIAL_REGISTRATION
        self.assertGreaterEqual(len(record.history), 1)
        self.assertEqual(record.history[-1].new_state, LifecycleState.REGISTERED_CALLER_OWNED)
        
        # Transition to FREED
        self.registry.mark_freed(ptr, "dealloc", self.fingerprint)
        self.assertEqual(record.state, LifecycleState.FREED)
        self.assertEqual(record.history[-1].new_state, LifecycleState.FREED)

    def test_structure_mutation_governance(self):
        """Verify immutable field mutation detection."""
        class Header(ctypes.Structure):
            _fields_ = [("version", ctypes.c_int32), ("flags", ctypes.c_int32)]
            
        contract_dict = {
            "schema_version": "1.0",
            "synthesis_version": "1.0.0",
            "fingerprint": self.fingerprint,
            "abi": 64,
            "functions": {
                "dummy": {"calling_convention": "cdecl", "arg_types": [], "return_type": "void"}
            },
            "structs": {
                "Header": {
                    "fields": [
                        {"name": "version", "type": "int32", "immutable": True},
                        {"name": "flags", "type": "int32", "immutable": False}
                    ]
                }
            }
        }
        
        loader = ContractRuntimeLoader(contract_dict)
        metadata = loader.metadata
        
        validator = StructureMutationValidator(metadata)
        h = Header(version=1, flags=0)
        
        # Capture snapshot
        policy = validator._policies["Header"]
        snapshot = validator.capture_snapshot(h, policy)
        
        # Mutate non-immutable field -> OK
        h.flags = 1
        validator.verify_mutation(h, snapshot, policy, "h", "test_func", self.fingerprint)
        
        # Mutate immutable field -> FAIL
        h.version = 2
        with self.assertRaises(ContractViolationError):
            validator.verify_mutation(h, snapshot, policy, "h", "test_func", self.fingerprint)

    def test_nested_structure_mutation(self):
        """Verify recursive immutability across nested structures."""
        class Inner(ctypes.Structure):
            _fields_ = [("inner_id", ctypes.c_int32)]
        class Outer(ctypes.Structure):
            _fields_ = [("inner", Inner), ("status", ctypes.c_int32)]
            
        contract_dict = {
            "schema_version": "1.0",
            "synthesis_version": "1.0.0",
            "fingerprint": self.fingerprint,
            "abi": 64,
            "functions": {
                 "dummy": {"calling_convention": "cdecl", "arg_types": [], "return_type": "void"}
            },
            "structs": {
                "Inner": {
                    "fields": [{"name": "inner_id", "type": "int32", "immutable": True}]
                },
                "Outer": {
                    "fields": [
                        {"name": "inner", "type": "Inner"},
                        {"name": "status", "type": "int32", "immutable": True}
                    ]
                }
            }
        }
        
        loader = ContractRuntimeLoader(contract_dict)
        metadata = loader.metadata
        
        validator = StructureMutationValidator(metadata)
        o = Outer()
        o.inner.inner_id = 100
        o.status = 1
        
        policy = validator._policies["Outer"]
        snapshot = validator.capture_snapshot(o, policy)
        
        # Mutate nested immutable field -> FAIL
        o.inner.inner_id = 101
        with self.assertRaises(ContractViolationError):
            validator.verify_mutation(o, snapshot, policy, "o", "test_func", self.fingerprint)

if __name__ == "__main__":
    unittest.main()
