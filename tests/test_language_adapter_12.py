"""Test Suite for Language Adapter - Prompt 12/25: 95 tests."""

import pytest
from modules.module_08_language_adapter import (
    OwnershipStateExtended,
    TransferAnnotation,
    OwnershipGraph,
    OwnershipStateMachine,
    TransferSemantics,
    OwnershipValidator,
)


# ════════════════════════════════════════════════════════════════════════════
# TRANSFER ANNOTATION TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestTransferAnnotation:
    """TransferAnnotation tests (15 tests)."""

    def test_create_annotation(self):
        """Test 1011: Create transfer annotation."""
        annot = TransferAnnotation(
            parameter_index=0,
            transfer_kind='transfer',
            direction='caller_to_callee'
        )
        assert annot.parameter_index == 0
        assert annot.transfer_kind == 'transfer'
        assert annot.direction == 'caller_to_callee'

    def test_should_transfer_always_true(self):
        """Test 1012: Always transfer returns True on success."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee', 'always')
        assert annot.should_transfer(True) is True

    def test_should_transfer_always_false(self):
        """Test 1013: Always transfer returns True on failure too."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee', 'always')
        assert annot.should_transfer(False) is True

    def test_should_transfer_on_success_true(self):
        """Test 1014: Transfer on success when call succeeds."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee', 'on_success')
        assert annot.should_transfer(True) is True

    def test_should_transfer_on_success_false(self):
        """Test 1015: No transfer on success when call fails."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee', 'on_success')
        assert annot.should_transfer(False) is False

    def test_should_transfer_on_failure_true(self):
        """Test 1016: Transfer on failure when call fails."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee', 'on_failure')
        assert annot.should_transfer(False) is True

    def test_should_transfer_on_failure_false(self):
        """Test 1017: No transfer on failure when call succeeds."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee', 'on_failure')
        assert annot.should_transfer(True) is False

    def test_annotation_with_free_function(self):
        """Test 1018: Annotation with free function."""
        annot = TransferAnnotation(
            0, 'transfer', 'caller_to_callee',
            free_function='custom_free'
        )
        assert annot.free_function == 'custom_free'

    def test_annotation_default_condition(self):
        """Test 1019: Default condition is always."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee')
        assert annot.condition == 'always'

    def test_annotation_default_free_function(self):
        """Test 1020: Default free function is None."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee')
        assert annot.free_function is None

    def test_annotation_to_dict(self):
        """Test 1021: Convert annotation to dictionary."""
        annot = TransferAnnotation(
            0, 'transfer', 'caller_to_callee', 'on_success', 'free_buf'
        )
        d = annot.to_dict()
        assert d['parameter_index'] == 0
        assert d['transfer_kind'] == 'transfer'
        assert d['direction'] == 'caller_to_callee'
        assert d['condition'] == 'on_success'
        assert d['free_function'] == 'free_buf'

    def test_annotation_borrow_kind(self):
        """Test 1022: Borrow annotation."""
        annot = TransferAnnotation(1, 'borrow', 'caller_to_callee')
        assert annot.transfer_kind == 'borrow'
        assert annot.parameter_index == 1

    def test_annotation_shared_kind(self):
        """Test 1023: Shared annotation."""
        annot = TransferAnnotation(2, 'shared', 'caller_to_callee')
        assert annot.transfer_kind == 'shared'

    def test_annotation_callee_to_caller(self):
        """Test 1024: Callee to caller direction."""
        annot = TransferAnnotation(0, 'transfer', 'callee_to_caller')
        assert annot.direction == 'callee_to_caller'

    def test_unknown_condition_returns_false(self):
        """Test 1025: Unknown condition returns False."""
        annot = TransferAnnotation(0, 'transfer', 'caller_to_callee', 'custom')
        assert annot.should_transfer(True) is False
        assert annot.should_transfer(False) is False


# ════════════════════════════════════════════════════════════════════════════
# OWNERSHIP GRAPH TESTS (30 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestOwnershipGraph:
    """OwnershipGraph tests (30 tests)."""

    def test_create_graph(self):
        """Test 1026: Create ownership graph."""
        graph = OwnershipGraph()
        assert len(graph.allocations) == 0

    def test_add_allocation(self):
        """Test 1027: Add allocation."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        assert 0x1000 in graph.allocations
        assert graph.get_owner(0x1000) == 'caller'

    def test_allocation_initial_state(self):
        """Test 1028: Allocation initial state is ALLOCATED."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        assert graph.get_state(0x1000) == OwnershipStateExtended.ALLOCATED

    def test_allocation_ref_count(self):
        """Test 1029: Allocation starts with ref count 1."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        assert graph.ref_counts[0x1000] == 1

    def test_transfer_ownership(self):
        """Test 1030: Transfer ownership."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.transfer_ownership(0x1000, 'callee')

        assert graph.get_owner(0x1000) == 'callee'
        assert graph.get_state(0x1000) == OwnershipStateExtended.TRANSFERRED

    def test_transfer_unknown_raises(self):
        """Test 1031: Transfer unknown allocation raises."""
        graph = OwnershipGraph()

        with pytest.raises(ValueError, match='Unknown allocation'):
            graph.transfer_ownership(0x9999, 'callee')

    def test_transfer_freed_raises(self):
        """Test 1032: Transfer freed allocation raises."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.mark_freed(0x1000)

        with pytest.raises(ValueError, match='freed'):
            graph.transfer_ownership(0x1000, 'callee')

    def test_borrow_allocation(self):
        """Test 1033: Borrow allocation."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.borrow_allocation(0x1000, 'callee')

        assert graph.get_state(0x1000) == OwnershipStateExtended.BORROWED

    def test_borrow_unknown_raises(self):
        """Test 1034: Borrow unknown raises."""
        graph = OwnershipGraph()
        with pytest.raises(ValueError, match='Unknown allocation'):
            graph.borrow_allocation(0x9999, 'callee')

    def test_return_allocation(self):
        """Test 1035: Return borrowed allocation."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.borrow_allocation(0x1000, 'callee')
        graph.return_allocation(0x1000)

        assert graph.get_state(0x1000) == OwnershipStateExtended.RETURNED

    def test_return_not_borrowed_raises(self):
        """Test 1036: Return non-borrowed raises."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        with pytest.raises(ValueError, match='not borrowed'):
            graph.return_allocation(0x1000)

    def test_return_unknown_raises(self):
        """Test 1037: Return unknown raises."""
        graph = OwnershipGraph()
        with pytest.raises(ValueError, match='Unknown allocation'):
            graph.return_allocation(0x9999)

    def test_add_reference(self):
        """Test 1038: Add reference increments count."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.add_reference(0x1000)

        assert graph.ref_counts[0x1000] == 2
        assert graph.get_state(0x1000) == OwnershipStateExtended.SHARED

    def test_add_reference_unknown_raises(self):
        """Test 1039: Add reference unknown raises."""
        graph = OwnershipGraph()
        with pytest.raises(ValueError, match='Unknown allocation'):
            graph.add_reference(0x9999)

    def test_remove_reference(self):
        """Test 1040: Remove reference decrements count."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.add_reference(0x1000)

        should_free = graph.remove_reference(0x1000)
        assert should_free is False
        assert graph.ref_counts[0x1000] == 1

    def test_remove_reference_to_zero(self):
        """Test 1041: Remove last reference returns True."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        should_free = graph.remove_reference(0x1000)
        assert should_free is True
        assert graph.ref_counts[0x1000] == 0

    def test_remove_reference_unknown_raises(self):
        """Test 1042: Remove reference unknown raises."""
        graph = OwnershipGraph()
        with pytest.raises(ValueError, match='Unknown allocation'):
            graph.remove_reference(0x9999)

    def test_mark_freed(self):
        """Test 1043: Mark allocation freed."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.mark_freed(0x1000)

        assert graph.get_state(0x1000) == OwnershipStateExtended.FREED

    def test_double_free_raises(self):
        """Test 1044: Double-free raises."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.mark_freed(0x1000)

        with pytest.raises(ValueError, match='Double-free'):
            graph.mark_freed(0x1000)

    def test_mark_freed_unknown_raises(self):
        """Test 1045: Free unknown raises."""
        graph = OwnershipGraph()
        with pytest.raises(ValueError, match='Unknown allocation'):
            graph.mark_freed(0x9999)

    def test_get_owner_unknown(self):
        """Test 1046: Get owner of unknown returns None."""
        graph = OwnershipGraph()
        assert graph.get_owner(0x9999) is None

    def test_get_state_unknown(self):
        """Test 1047: Get state of unknown returns None."""
        graph = OwnershipGraph()
        assert graph.get_state(0x9999) is None

    def test_register_allocate_hook(self):
        """Test 1048: Register on_allocate hook."""
        graph = OwnershipGraph()
        called = []

        def hook(addr, size, owner):
            called.append((addr, size, owner))

        graph.register_hook('on_allocate', hook)
        graph.add_allocation(0x1000, 1024, 'caller')

        assert len(called) == 1
        assert called[0] == (0x1000, 1024, 'caller')

    def test_register_transfer_hook(self):
        """Test 1049: Register on_transfer hook."""
        graph = OwnershipGraph()
        transfers = []

        def hook(addr, old, new):
            transfers.append((addr, old, new))

        graph.register_hook('on_transfer', hook)
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.transfer_ownership(0x1000, 'callee')

        assert len(transfers) == 1
        assert transfers[0] == (0x1000, 'caller', 'callee')

    def test_register_borrow_hook(self):
        """Test 1050: Register on_borrow hook."""
        graph = OwnershipGraph()
        borrows = []

        graph.register_hook('on_borrow', lambda a, b: borrows.append((a, b)))
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.borrow_allocation(0x1000, 'callee')

        assert len(borrows) == 1
        assert borrows[0] == (0x1000, 'callee')

    def test_register_return_hook(self):
        """Test 1051: Register on_return hook."""
        graph = OwnershipGraph()
        returns = []

        graph.register_hook('on_return', lambda a, o: returns.append((a, o)))
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.borrow_allocation(0x1000, 'callee')
        graph.return_allocation(0x1000)

        assert len(returns) == 1
        assert returns[0] == (0x1000, 'caller')

    def test_register_free_hook(self):
        """Test 1052: Register on_free hook."""
        graph = OwnershipGraph()
        frees = []

        graph.register_hook('on_free', lambda a, o: frees.append((a, o)))
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.mark_freed(0x1000)

        assert len(frees) == 1
        assert frees[0] == (0x1000, 'caller')

    def test_hook_error_doesnt_propagate(self):
        """Test 1053: Hook errors don't propagate."""
        graph = OwnershipGraph()

        def bad_hook(a, s, o):
            raise RuntimeError("Hook error!")

        graph.register_hook('on_allocate', bad_hook)
        # Should not raise
        graph.add_allocation(0x1000, 1024, 'caller')
        assert 0x1000 in graph.allocations

    def test_allocation_history(self):
        """Test 1054: Allocation history tracking."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.transfer_ownership(0x1000, 'callee')

        alloc = graph.allocations[0x1000]
        assert len(alloc['history']) == 1
        assert alloc['history'][0]['event'] == 'transfer'

    def test_multiple_allocations(self):
        """Test 1055: Multiple allocations tracked."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.add_allocation(0x2000, 2048, 'callee')
        graph.add_allocation(0x3000, 512, 'caller')

        assert len(graph.allocations) == 3
        assert graph.get_owner(0x1000) == 'caller'
        assert graph.get_owner(0x2000) == 'callee'
        assert graph.get_owner(0x3000) == 'caller'


# ════════════════════════════════════════════════════════════════════════════
# OWNERSHIP STATE MACHINE TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestOwnershipStateMachine:
    """OwnershipStateMachine tests (15 tests)."""

    def test_create_state_machine(self):
        """Test 1056: Create state machine."""
        sm = OwnershipStateMachine()
        assert sm is not None

    def test_valid_allocated_to_in_call(self):
        """Test 1057: Valid: ALLOCATED -> IN_CALL."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.ALLOCATED,
            OwnershipStateExtended.IN_CALL
        ) is True

    def test_valid_allocated_to_borrowed(self):
        """Test 1058: Valid: ALLOCATED -> BORROWED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.ALLOCATED,
            OwnershipStateExtended.BORROWED
        ) is True

    def test_valid_allocated_to_transferred(self):
        """Test 1059: Valid: ALLOCATED -> TRANSFERRED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.ALLOCATED,
            OwnershipStateExtended.TRANSFERRED
        ) is True

    def test_valid_allocated_to_shared(self):
        """Test 1060: Valid: ALLOCATED -> SHARED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.ALLOCATED,
            OwnershipStateExtended.SHARED
        ) is True

    def test_valid_allocated_to_freed(self):
        """Test 1061: Valid: ALLOCATED -> FREED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.ALLOCATED,
            OwnershipStateExtended.FREED
        ) is True

    def test_valid_borrowed_to_returned(self):
        """Test 1062: Valid: BORROWED -> RETURNED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.BORROWED,
            OwnershipStateExtended.RETURNED
        ) is True

    def test_valid_in_call_to_transferred(self):
        """Test 1063: Valid: IN_CALL -> TRANSFERRED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.IN_CALL,
            OwnershipStateExtended.TRANSFERRED
        ) is True

    def test_valid_transferred_to_freed(self):
        """Test 1064: Valid: TRANSFERRED -> FREED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.TRANSFERRED,
            OwnershipStateExtended.FREED
        ) is True

    def test_valid_returned_to_in_call(self):
        """Test 1065: Valid: RETURNED -> IN_CALL."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.RETURNED,
            OwnershipStateExtended.IN_CALL
        ) is True

    def test_invalid_freed_to_allocated(self):
        """Test 1066: Invalid: FREED -> ALLOCATED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.FREED,
            OwnershipStateExtended.ALLOCATED
        ) is False

    def test_invalid_freed_to_anything(self):
        """Test 1067: Invalid: FREED -> any state."""
        sm = OwnershipStateMachine()
        for state in OwnershipStateExtended:
            assert sm.is_valid_transition(
                OwnershipStateExtended.FREED,
                state
            ) is False

    def test_invalid_borrowed_to_transferred(self):
        """Test 1068: Invalid: BORROWED -> TRANSFERRED."""
        sm = OwnershipStateMachine()
        assert sm.is_valid_transition(
            OwnershipStateExtended.BORROWED,
            OwnershipStateExtended.TRANSFERRED
        ) is False

    def test_validate_valid_does_not_raise(self):
        """Test 1069: validate_transition valid does not raise."""
        sm = OwnershipStateMachine()
        sm.validate_transition(
            OwnershipStateExtended.ALLOCATED,
            OwnershipStateExtended.FREED
        )

    def test_validate_invalid_raises(self):
        """Test 1070: validate_transition invalid raises."""
        sm = OwnershipStateMachine()

        with pytest.raises(ValueError, match='Invalid ownership transition'):
            sm.validate_transition(
                OwnershipStateExtended.FREED,
                OwnershipStateExtended.ALLOCATED
            )


# ════════════════════════════════════════════════════════════════════════════
# TRANSFER SEMANTICS TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestTransferSemantics:
    """TransferSemantics tests (20 tests)."""

    def test_create_transfer_semantics(self):
        """Test 1071: Create transfer semantics."""
        graph = OwnershipGraph()
        ts = TransferSemantics(graph)
        assert ts.graph is graph
        assert ts.state_machine is not None

    def test_pre_call_transfer(self):
        """Test 1072: Apply pre-call transfer."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(0, 'transfer', 'caller_to_callee')
        ts.apply_pre_call_transfers([annotation], {0: 0x1000})

        assert graph.get_owner(0x1000) == 'callee'
        assert graph.get_state(0x1000) == OwnershipStateExtended.TRANSFERRED

    def test_pre_call_borrow(self):
        """Test 1073: Apply pre-call borrow."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(0, 'borrow', 'caller_to_callee')
        ts.apply_pre_call_transfers([annotation], {0: 0x1000})

        assert graph.get_state(0x1000) == OwnershipStateExtended.BORROWED

    def test_pre_call_shared(self):
        """Test 1074: Apply pre-call shared reference."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(0, 'shared', 'caller_to_callee')
        ts.apply_pre_call_transfers([annotation], {0: 0x1000})

        assert graph.ref_counts[0x1000] == 2
        assert graph.get_state(0x1000) == OwnershipStateExtended.SHARED

    def test_pre_call_skip_callee_to_caller(self):
        """Test 1075: Pre-call skips callee_to_caller annotations."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(0, 'transfer', 'callee_to_caller')
        ts.apply_pre_call_transfers([annotation], {0: 0x1000})

        # Should remain unchanged
        assert graph.get_owner(0x1000) == 'caller'
        assert graph.get_state(0x1000) == OwnershipStateExtended.ALLOCATED

    def test_pre_call_skip_unmapped(self):
        """Test 1076: Pre-call skips unmapped parameters."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(5, 'transfer', 'caller_to_callee')
        ts.apply_pre_call_transfers([annotation], {0: 0x1000})

        assert graph.get_state(0x1000) == OwnershipStateExtended.ALLOCATED

    def test_post_call_borrow_return(self):
        """Test 1077: Post-call returns borrowed allocation."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.borrow_allocation(0x1000, 'callee')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(0, 'borrow', 'caller_to_callee')
        ts.apply_post_call_transfers([annotation], {0: 0x1000}, True)

        assert graph.get_state(0x1000) == OwnershipStateExtended.RETURNED

    def test_post_call_callee_to_caller_transfer(self):
        """Test 1078: Post-call callee-to-caller transfer."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'callee')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(0, 'transfer', 'callee_to_caller')
        ts.apply_post_call_transfers([annotation], {0: 0x1000}, True)

        assert graph.get_owner(0x1000) == 'caller'

    def test_post_call_conditional_success(self):
        """Test 1079: Conditional transfer on success."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'callee')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(
            0, 'transfer', 'callee_to_caller', 'on_success'
        )
        ts.apply_post_call_transfers([annotation], {0: 0x1000}, True)

        assert graph.get_owner(0x1000) == 'caller'

    def test_post_call_conditional_no_transfer_on_fail(self):
        """Test 1080: No transfer when condition not met."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'callee')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(
            0, 'transfer', 'callee_to_caller', 'on_success'
        )
        ts.apply_post_call_transfers([annotation], {0: 0x1000}, False)

        assert graph.get_owner(0x1000) == 'callee'

    def test_post_call_skip_unmapped(self):
        """Test 1081: Post-call skips unmapped parameters."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(5, 'transfer', 'callee_to_caller')
        ts.apply_post_call_transfers([annotation], {0: 0x1000}, True)

        assert graph.get_owner(0x1000) == 'caller'

    def test_multiple_pre_call_annotations(self):
        """Test 1082: Multiple pre-call annotations."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.add_allocation(0x2000, 512, 'caller')

        ts = TransferSemantics(graph)
        annotations = [
            TransferAnnotation(0, 'transfer', 'caller_to_callee'),
            TransferAnnotation(1, 'borrow', 'caller_to_callee'),
        ]
        ts.apply_pre_call_transfers(annotations, {0: 0x1000, 1: 0x2000})

        assert graph.get_owner(0x1000) == 'callee'
        assert graph.get_state(0x2000) == OwnershipStateExtended.BORROWED

    def test_full_borrow_lifecycle(self):
        """Test 1083: Full borrow lifecycle: allocate -> borrow -> return."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        borrow_annot = TransferAnnotation(0, 'borrow', 'caller_to_callee')

        # Pre-call: borrow
        ts.apply_pre_call_transfers([borrow_annot], {0: 0x1000})
        assert graph.get_state(0x1000) == OwnershipStateExtended.BORROWED

        # Post-call: return
        ts.apply_post_call_transfers([borrow_annot], {0: 0x1000}, True)
        assert graph.get_state(0x1000) == OwnershipStateExtended.RETURNED

    def test_full_transfer_lifecycle(self):
        """Test 1084: Full transfer lifecycle."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        transfer_annot = TransferAnnotation(0, 'transfer', 'caller_to_callee')

        ts.apply_pre_call_transfers([transfer_annot], {0: 0x1000})
        assert graph.get_owner(0x1000) == 'callee'
        assert graph.get_state(0x1000) == OwnershipStateExtended.TRANSFERRED

    def test_post_call_failure_transfer(self):
        """Test 1085: Conditional transfer on failure."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'callee')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(
            0, 'transfer', 'callee_to_caller', 'on_failure'
        )
        ts.apply_post_call_transfers([annotation], {0: 0x1000}, False)

        assert graph.get_owner(0x1000) == 'caller'

    def test_post_call_failure_no_transfer_on_success(self):
        """Test 1086: On_failure annotation doesn't transfer on success."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'callee')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(
            0, 'transfer', 'callee_to_caller', 'on_failure'
        )
        ts.apply_post_call_transfers([annotation], {0: 0x1000}, True)

        assert graph.get_owner(0x1000) == 'callee'

    def test_empty_annotations_pre_call(self):
        """Test 1087: Empty annotations list for pre-call."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        ts.apply_pre_call_transfers([], {0: 0x1000})

        assert graph.get_state(0x1000) == OwnershipStateExtended.ALLOCATED

    def test_empty_annotations_post_call(self):
        """Test 1088: Empty annotations list for post-call."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        ts.apply_post_call_transfers([], {0: 0x1000}, True)

        assert graph.get_state(0x1000) == OwnershipStateExtended.ALLOCATED

    def test_empty_addresses_pre_call(self):
        """Test 1089: Empty addresses mapping for pre-call."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(0, 'transfer', 'caller_to_callee')
        ts.apply_pre_call_transfers([annotation], {})

        assert graph.get_state(0x1000) == OwnershipStateExtended.ALLOCATED

    def test_empty_addresses_post_call(self):
        """Test 1090: Empty addresses mapping for post-call."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        ts = TransferSemantics(graph)
        annotation = TransferAnnotation(0, 'transfer', 'callee_to_caller')
        ts.apply_post_call_transfers([annotation], {}, True)

        assert graph.get_state(0x1000) == OwnershipStateExtended.ALLOCATED


# ════════════════════════════════════════════════════════════════════════════
# OWNERSHIP VALIDATOR TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestOwnershipValidator:
    """OwnershipValidator tests (15 tests)."""

    def test_create_validator(self):
        """Test 1091: Create ownership validator."""
        graph = OwnershipGraph()
        validator = OwnershipValidator(graph)
        assert validator.graph is graph

    def test_can_free_owner(self):
        """Test 1092: Owner can free."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        validator = OwnershipValidator(graph)
        can_free, msg = validator.can_free(0x1000, 'caller')
        assert can_free is True
        assert msg is None

    def test_cannot_free_non_owner(self):
        """Test 1093: Non-owner cannot free."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        validator = OwnershipValidator(graph)
        can_free, msg = validator.can_free(0x1000, 'other')
        assert can_free is False
        assert 'owner' in msg.lower()

    def test_cannot_free_already_freed(self):
        """Test 1094: Cannot free already freed."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.mark_freed(0x1000)

        validator = OwnershipValidator(graph)
        can_free, msg = validator.can_free(0x1000, 'caller')
        assert can_free is False
        assert 'freed' in msg.lower()

    def test_cannot_free_borrowed(self):
        """Test 1095: Cannot free while borrowed."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.borrow_allocation(0x1000, 'callee')

        validator = OwnershipValidator(graph)
        can_free, msg = validator.can_free(0x1000, 'caller')
        assert can_free is False
        assert 'borrowed' in msg.lower()

    def test_can_transfer_owner(self):
        """Test 1096: Owner can transfer."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        validator = OwnershipValidator(graph)
        can_transfer, msg = validator.can_transfer(0x1000, 'caller')
        assert can_transfer is True
        assert msg is None

    def test_cannot_transfer_non_owner(self):
        """Test 1097: Non-owner cannot transfer."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        validator = OwnershipValidator(graph)
        can_transfer, msg = validator.can_transfer(0x1000, 'other')
        assert can_transfer is False
        assert 'owner' in msg.lower()

    def test_cannot_transfer_freed(self):
        """Test 1098: Cannot transfer freed allocation."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.mark_freed(0x1000)

        validator = OwnershipValidator(graph)
        can_transfer, msg = validator.can_transfer(0x1000, 'caller')
        assert can_transfer is False
        assert 'freed' in msg.lower()

    def test_can_access_owner(self):
        """Test 1099: Owner can access."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        validator = OwnershipValidator(graph)
        can_access, msg = validator.can_access(0x1000, 'caller')
        assert can_access is True
        assert msg is None

    def test_can_access_borrower(self):
        """Test 1100: Borrower can access during borrow."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.borrow_allocation(0x1000, 'callee')

        validator = OwnershipValidator(graph)
        can_access, msg = validator.can_access(0x1000, 'callee')
        assert can_access is True

    def test_can_access_shared(self):
        """Test 1101: Shared allocation can be accessed by others."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.add_reference(0x1000)

        validator = OwnershipValidator(graph)
        can_access, msg = validator.can_access(0x1000, 'other')
        assert can_access is True

    def test_cannot_access_freed(self):
        """Test 1102: Cannot access freed allocation."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.mark_freed(0x1000)

        validator = OwnershipValidator(graph)
        can_access, msg = validator.can_access(0x1000, 'caller')
        assert can_access is False
        assert 'freed' in msg.lower()

    def test_cannot_access_non_owner_non_borrower(self):
        """Test 1103: Cannot access as non-owner non-borrower."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')

        validator = OwnershipValidator(graph)
        can_access, msg = validator.can_access(0x1000, 'random')
        assert can_access is False
        assert 'denied' in msg.lower()

    def test_validator_has_state_machine(self):
        """Test 1104: Validator has state machine."""
        graph = OwnershipGraph()
        validator = OwnershipValidator(graph)
        assert isinstance(validator.state_machine, OwnershipStateMachine)

    def test_can_access_after_transfer(self):
        """Test 1105: Can access after ownership transfer."""
        graph = OwnershipGraph()
        graph.add_allocation(0x1000, 1024, 'caller')
        graph.transfer_ownership(0x1000, 'callee')

        validator = OwnershipValidator(graph)
        # New owner can access
        can_access, _ = validator.can_access(0x1000, 'callee')
        assert can_access is True

        # Old owner cannot access
        can_access, msg = validator.can_access(0x1000, 'caller')
        assert can_access is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
