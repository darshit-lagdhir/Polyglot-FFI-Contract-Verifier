# ==============================================================================
# Polyglot FFI Contract Verifier - Unit Tests
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
# ==============================================================================
import unittest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, RuntimeConfiguration, InvocationJournalEntry
)

class TestReplayJournal(unittest.TestCase):
    def test_journal_recording(self):
        meta = ContractMetadata("1.0", "0.1", "fp", 64, {})
        ctx = EnforcementContext("fp", meta)
        ctx.config_controller.update(RuntimeConfiguration(journaling_enabled=True, journal_max_entries=2))
        
        entry1 = InvocationJournalEntry(1, "f1", [], None, [], "START", "END", {}, 0, "fp")
        entry2 = InvocationJournalEntry(2, "f2", [], None, [], "START", "END", {}, 0, "fp")
        entry3 = InvocationJournalEntry(3, "f3", [], None, [], "START", "END", {}, 0, "fp")
        
        ctx.journal_manager.record_entry(entry1)
        ctx.journal_manager.record_entry(entry2)
        ctx.journal_manager.record_entry(entry3)
        
        self.assertEqual(len(ctx.journal_manager._journal), 2)
        self.assertEqual(ctx.journal_manager._journal[0].sequence_index, 2)
        self.assertEqual(ctx.journal_manager._journal[1].sequence_index, 3)

if __name__ == "__main__":
    unittest.main()
