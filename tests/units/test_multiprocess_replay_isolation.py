"""
Test: Multi-Process Replay Isolation (Prompt 19 Part 2)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, InvocationJournalEntry
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_REPLAY", 64, {})

def test_replay_journal_isolation_post_fork():
    """Checks that the replay journal is cleared on post-fork re-init."""
    ctx = EnforcementContext("FP_REPLAY", _meta())
    
    # Add an entry
    ctx.journal_manager._journal.append(InvocationJournalEntry(
        sequence_index=1, function_name="f", inputs=[], return_value=None, 
        violations=[], lifecycle_before="alloc", lifecycle_after="alloc",
        profiling_delta={}, reload_seq=0, fingerprint="FP"
    ))
    assert len(ctx.journal_manager._journal) == 1
    
    # Re-init
    ctx.process_isolation.post_fork_reinitialize()
    
    # Must be empty
    assert len(ctx.journal_manager._journal) == 0
