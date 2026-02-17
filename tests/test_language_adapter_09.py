
"""Test Suite for Language Adapter - Prompt 09/25: 90 tests."""

import pytest
from modules.module_08_language_adapter import (
    PythonPointerWrapper,
    BufferPinner,
    AllocationTracker,
    ReferenceHolder,
    MemoryValidator,
    PythonMemoryManager,
    PythonAdapter,
    OwnershipKind,
)


# ════════════════════════════════════════════════════════════════════════════
# PYTHON POINTER WRAPPER TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonPointerWrapper:
    """PythonPointerWrapper tests (20 tests)."""
    
    def test_create_wrapper(self):
        """Test 736: Create pointer wrapper."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        assert wrapper.address == 0x1000
        assert wrapper.size == 1024
    
    def test_wrapper_initially_valid(self):
        """Test 737: Wrapper initially valid."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        assert wrapper.is_valid() is True
    
    def test_get_address_valid(self):
        """Test 738: Get address when valid."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        assert wrapper.get_address() == 0x1000
    
    def test_mark_freed(self):
        """Test 739: Mark pointer freed."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        wrapper.mark_freed()
        assert wrapper.is_valid() is False
    
    def test_double_free_raises(self):
        """Test 740: Double-free raises error."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        wrapper.mark_freed()
        
        with pytest.raises(RuntimeError, match='Double-free'):
            wrapper.mark_freed()
    
    def test_get_address_after_free_raises(self):
        """Test 741: Get address after free raises."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        wrapper.mark_freed()
        
        with pytest.raises(RuntimeError, match='Invalid pointer'):
            wrapper.get_address()
    
    def test_invalidate(self):
        """Test 742: Invalidate pointer."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        wrapper.invalidate()
        assert wrapper.is_valid() is False
    
    def test_invalidate_then_get_address_raises(self):
        """Test 743: Get address after invalidate raises."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        wrapper.invalidate()
        with pytest.raises(RuntimeError, match='Invalid pointer'):
            wrapper.get_address()
    
    def test_wrapper_with_caller_ownership(self):
        """Test 744: Wrapper with caller ownership."""
        wrapper = PythonPointerWrapper(
            0x1000, 1024,
            ownership=OwnershipKind.CALLER_OWNED
        )
        assert wrapper.ownership == OwnershipKind.CALLER_OWNED
    
    def test_wrapper_with_callee_ownership(self):
        """Test 745: Wrapper with callee ownership."""
        wrapper = PythonPointerWrapper(
            0x1000, 1024,
            ownership=OwnershipKind.CALLEE_OWNED
        )
        assert wrapper.ownership == OwnershipKind.CALLEE_OWNED
    
    def test_wrapper_default_ownership(self):
        """Test 746: Default ownership is UNKNOWN."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        assert wrapper.ownership == OwnershipKind.UNKNOWN
    
    def test_wrapper_with_python_object(self):
        """Test 747: Wrapper with Python object."""
        obj = b'test'
        wrapper = PythonPointerWrapper(0x1000, 4, python_object=obj)
        assert wrapper.python_object == obj
    
    def test_wrapper_no_python_object(self):
        """Test 748: Wrapper without Python object defaults to None."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        assert wrapper.python_object is None
    
    def test_wrapper_int_conversion(self):
        """Test 749: Convert wrapper to int."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        assert int(wrapper) == 0x1000
    
    def test_wrapper_int_conversion_after_free_raises(self):
        """Test 750: Int conversion after free raises."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        wrapper.mark_freed()
        with pytest.raises(RuntimeError):
            int(wrapper)
    
    def test_wrapper_repr_valid(self):
        """Test 751: Repr shows valid status."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        repr_str = repr(wrapper)
        assert '0x1000' in repr_str
        assert 'valid' in repr_str
    
    def test_wrapper_repr_invalid(self):
        """Test 752: Repr shows invalid status."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        wrapper.invalidate()
        repr_str = repr(wrapper)
        assert 'invalid' in repr_str
    
    def test_wrapper_size_zero(self):
        """Test 753: Wrapper with zero size."""
        wrapper = PythonPointerWrapper(0x1000, 0)
        assert wrapper.size == 0
        assert wrapper.is_valid() is True
    
    def test_wrapper_large_address(self):
        """Test 754: Wrapper with large address."""
        wrapper = PythonPointerWrapper(0xFFFFFFFFFFFF, 4096)
        assert wrapper.address == 0xFFFFFFFFFFFF
        assert wrapper.is_valid() is True
    
    def test_wrapper_freed_flag_independent(self):
        """Test 755: Freed and valid flags are independent."""
        wrapper = PythonPointerWrapper(0x1000, 1024)
        assert wrapper._freed is False
        assert wrapper._valid is True
        wrapper.invalidate()
        assert wrapper._freed is False
        assert wrapper._valid is False


# ════════════════════════════════════════════════════════════════════════════
# BUFFER PINNER TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestBufferPinner:
    """BufferPinner tests (15 tests)."""
    
    def test_create_pinner(self):
        """Test 756: Create buffer pinner."""
        pinner = BufferPinner()
        assert len(pinner.pinned_buffers) == 0
    
    def test_pin_bytes(self):
        """Test 757: Pin bytes object."""
        pinner = BufferPinner()
        data = b'test'
        address, size = pinner.pin_buffer(data)
        assert size == 4
        assert address in pinner.pinned_buffers
    
    def test_pin_bytearray(self):
        """Test 758: Pin bytearray."""
        pinner = BufferPinner()
        data = bytearray(b'test')
        address, size = pinner.pin_buffer(data)
        assert size == 4
        assert address in pinner.pinned_buffers
    
    def test_pin_memoryview(self):
        """Test 759: Pin memoryview."""
        pinner = BufferPinner()
        underlying = b'test'
        data = memoryview(underlying)
        address, size = pinner.pin_buffer(data)
        assert size == 4
    
    def test_pin_invalid_object(self):
        """Test 760: Pin invalid object raises."""
        pinner = BufferPinner()
        with pytest.raises(ValueError, match='not a buffer'):
            pinner.pin_buffer(42)
    
    def test_unpin_buffer(self):
        """Test 761: Unpin buffer."""
        pinner = BufferPinner()
        data = b'test'
        address, _ = pinner.pin_buffer(data)
        assert pinner.unpin_buffer(address) is True
        assert address not in pinner.pinned_buffers
    
    def test_unpin_not_pinned(self):
        """Test 762: Unpin not-pinned buffer."""
        pinner = BufferPinner()
        assert pinner.unpin_buffer(0x9999) is False
    
    def test_unpin_all(self):
        """Test 763: Unpin all buffers."""
        pinner = BufferPinner()
        pinner.pin_buffer(b'test1')
        pinner.pin_buffer(b'test2')
        pinner.unpin_all()
        assert len(pinner.pinned_buffers) == 0
    
    def test_is_pinned_true(self):
        """Test 764: is_pinned returns True for pinned buffer."""
        pinner = BufferPinner()
        data = b'data'
        address, _ = pinner.pin_buffer(data)
        assert pinner.is_pinned(address) is True
    
    def test_is_pinned_false(self):
        """Test 765: is_pinned returns False for non-pinned."""
        pinner = BufferPinner()
        assert pinner.is_pinned(0x9999) is False
    
    def test_get_pinned_count(self):
        """Test 766: Get pinned count."""
        pinner = BufferPinner()
        assert pinner.get_pinned_count() == 0
        pinner.pin_buffer(b'test')
        assert pinner.get_pinned_count() == 1
    
    def test_pin_empty_bytes(self):
        """Test 767: Pin empty bytes."""
        pinner = BufferPinner()
        address, size = pinner.pin_buffer(b'')
        assert size == 0
    
    def test_pin_large_buffer(self):
        """Test 768: Pin large buffer."""
        pinner = BufferPinner()
        data = b'\x00' * 10000
        address, size = pinner.pin_buffer(data)
        assert size == 10000
    
    def test_pin_dict_raises(self):
        """Test 769: Pin dict raises ValueError."""
        pinner = BufferPinner()
        with pytest.raises(ValueError):
            pinner.pin_buffer({'key': 'value'})
    
    def test_pin_string_raises(self):
        """Test 770: Pin string raises ValueError (not buffer protocol)."""
        pinner = BufferPinner()
        with pytest.raises(ValueError):
            pinner.pin_buffer('not a buffer')


# ════════════════════════════════════════════════════════════════════════════
# ALLOCATION TRACKER TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestAllocationTracker:
    """AllocationTracker tests (20 tests)."""
    
    def test_create_tracker(self):
        """Test 771: Create allocation tracker."""
        tracker = AllocationTracker()
        assert tracker.allocation_count == 0
        assert len(tracker.allocations) == 0
    
    def test_track_allocation(self):
        """Test 772: Track allocation."""
        tracker = AllocationTracker()
        tracker.track_allocation(
            0x1000, 1024, 'python',
            OwnershipKind.CALLER_OWNED
        )
        assert tracker.allocation_count == 1
    
    def test_get_allocation(self):
        """Test 773: Get allocation info."""
        tracker = AllocationTracker()
        tracker.track_allocation(
            0x1000, 1024, 'python',
            OwnershipKind.CALLER_OWNED
        )
        alloc = tracker.get_allocation(0x1000)
        assert alloc is not None
        assert alloc['size'] == 1024
        assert alloc['source'] == 'python'
    
    def test_get_allocation_not_found(self):
        """Test 774: Get non-existent allocation."""
        tracker = AllocationTracker()
        assert tracker.get_allocation(0x9999) is None
    
    def test_mark_freed(self):
        """Test 775: Mark allocation freed."""
        tracker = AllocationTracker()
        tracker.track_allocation(
            0x1000, 1024, 'python',
            OwnershipKind.CALLER_OWNED
        )
        tracker.mark_freed(0x1000)
        alloc = tracker.get_allocation(0x1000)
        assert alloc['freed'] is True
        assert 'freed_at' in alloc
    
    def test_double_free_raises(self):
        """Test 776: Double-free raises."""
        tracker = AllocationTracker()
        tracker.track_allocation(
            0x1000, 1024, 'python',
            OwnershipKind.CALLER_OWNED
        )
        tracker.mark_freed(0x1000)
        with pytest.raises(ValueError, match='Double-free'):
            tracker.mark_freed(0x1000)
    
    def test_free_unknown_raises(self):
        """Test 777: Free unknown allocation raises."""
        tracker = AllocationTracker()
        with pytest.raises(ValueError, match='Unknown allocation'):
            tracker.mark_freed(0x9999)
    
    def test_transfer_ownership(self):
        """Test 778: Transfer ownership."""
        tracker = AllocationTracker()
        tracker.track_allocation(
            0x1000, 1024, 'python',
            OwnershipKind.CALLER_OWNED
        )
        tracker.transfer_ownership(0x1000, OwnershipKind.CALLEE_OWNED)
        alloc = tracker.get_allocation(0x1000)
        assert alloc['ownership'] == OwnershipKind.CALLEE_OWNED
    
    def test_transfer_ownership_records_history(self):
        """Test 779: Transfer ownership records history."""
        tracker = AllocationTracker()
        tracker.track_allocation(
            0x1000, 1024, 'python',
            OwnershipKind.CALLER_OWNED
        )
        tracker.transfer_ownership(0x1000, OwnershipKind.CALLEE_OWNED)
        alloc = tracker.get_allocation(0x1000)
        assert 'ownership_transferred' in alloc
        assert alloc['ownership_transferred']['from'] == 'caller_owned'
        assert alloc['ownership_transferred']['to'] == 'callee_owned'
    
    def test_transfer_unknown_raises(self):
        """Test 780: Transfer unknown allocation raises."""
        tracker = AllocationTracker()
        with pytest.raises(ValueError, match='Unknown allocation'):
            tracker.transfer_ownership(0x9999, OwnershipKind.CALLEE_OWNED)
    
    def test_get_active_allocations(self):
        """Test 781: Get active allocations."""
        tracker = AllocationTracker()
        tracker.track_allocation(0x1000, 1024, 'python', OwnershipKind.CALLER_OWNED)
        tracker.track_allocation(0x2000, 2048, 'python', OwnershipKind.CALLER_OWNED)
        tracker.mark_freed(0x1000)
        active = tracker.get_active_allocations()
        assert len(active) == 1
        assert active[0]['address'] == 0x2000
    
    def test_get_active_allocations_empty(self):
        """Test 782: No active allocations."""
        tracker = AllocationTracker()
        assert len(tracker.get_active_allocations()) == 0
    
    def test_get_statistics(self):
        """Test 783: Get statistics."""
        tracker = AllocationTracker()
        tracker.track_allocation(0x1000, 1024, 'python', OwnershipKind.CALLER_OWNED)
        tracker.track_allocation(0x2000, 2048, 'native', OwnershipKind.CALLEE_OWNED)
        stats = tracker.get_statistics()
        assert stats['total_allocations'] == 2
        assert stats['active_allocations'] == 2
        assert stats['freed_allocations'] == 0
    
    def test_statistics_total_bytes(self):
        """Test 784: Statistics show total active bytes."""
        tracker = AllocationTracker()
        tracker.track_allocation(0x1000, 1024, 'python', OwnershipKind.CALLER_OWNED)
        tracker.track_allocation(0x2000, 2048, 'python', OwnershipKind.CALLER_OWNED)
        stats = tracker.get_statistics()
        assert stats['total_bytes_active'] == 3072
    
    def test_statistics_by_source(self):
        """Test 785: Statistics by source."""
        tracker = AllocationTracker()
        tracker.track_allocation(0x1000, 1024, 'python', OwnershipKind.CALLER_OWNED)
        tracker.track_allocation(0x2000, 2048, 'native', OwnershipKind.CALLEE_OWNED)
        stats = tracker.get_statistics()
        assert stats['by_source']['python'] == 1
        assert stats['by_source']['native'] == 1
    
    def test_statistics_after_free(self):
        """Test 786: Statistics after freeing."""
        tracker = AllocationTracker()
        tracker.track_allocation(0x1000, 1024, 'python', OwnershipKind.CALLER_OWNED)
        tracker.mark_freed(0x1000)
        stats = tracker.get_statistics()
        assert stats['active_allocations'] == 0
        assert stats['freed_allocations'] == 1
    
    def test_track_with_metadata(self):
        """Test 787: Track allocation with metadata."""
        tracker = AllocationTracker()
        tracker.track_allocation(
            0x1000, 1024, 'python',
            OwnershipKind.CALLER_OWNED,
            metadata={'type': 'buffer', 'name': 'data'}
        )
        alloc = tracker.get_allocation(0x1000)
        assert alloc['metadata']['type'] == 'buffer'
    
    def test_track_with_no_metadata(self):
        """Test 788: Track allocation without metadata defaults to empty dict."""
        tracker = AllocationTracker()
        tracker.track_allocation(0x1000, 1024, 'python', OwnershipKind.CALLER_OWNED)
        alloc = tracker.get_allocation(0x1000)
        assert alloc['metadata'] == {}
    
    def test_allocation_has_timestamp(self):
        """Test 789: Allocation has timestamp."""
        tracker = AllocationTracker()
        tracker.track_allocation(0x1000, 1024, 'python', OwnershipKind.CALLER_OWNED)
        alloc = tracker.get_allocation(0x1000)
        assert 'timestamp' in alloc
        assert alloc['timestamp'].endswith('Z')
    
    def test_multiple_allocations_count(self):
        """Test 790: Multiple allocations increment count."""
        tracker = AllocationTracker()
        for i in range(5):
            tracker.track_allocation(
                0x1000 + i * 0x1000, 1024, 'python',
                OwnershipKind.CALLER_OWNED
            )
        assert tracker.allocation_count == 5


# ════════════════════════════════════════════════════════════════════════════
# REFERENCE HOLDER TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestReferenceHolder:
    """ReferenceHolder tests (10 tests)."""
    
    def test_create_holder(self):
        """Test 791: Create reference holder."""
        holder = ReferenceHolder()
        assert len(holder.held_references) == 0
    
    def test_hold_reference(self):
        """Test 792: Hold reference."""
        holder = ReferenceHolder()
        obj = b'test'
        holder.hold(obj)
        assert len(holder.held_references) == 1
    
    def test_release_reference(self):
        """Test 793: Release reference."""
        holder = ReferenceHolder()
        obj = b'test'
        holder.hold(obj)
        assert holder.release(obj) is True
        assert len(holder.held_references) == 0
    
    def test_release_not_held(self):
        """Test 794: Release not-held reference."""
        holder = ReferenceHolder()
        assert holder.release(b'test') is False
    
    def test_release_all(self):
        """Test 795: Release all references."""
        holder = ReferenceHolder()
        holder.hold(b'test1')
        holder.hold(b'test2')
        holder.release_all()
        assert len(holder.held_references) == 0
    
    def test_context_manager(self):
        """Test 796: Context manager releases all on exit."""
        holder = ReferenceHolder()
        obj = b'test'
        with holder:
            holder.hold(obj)
            assert len(holder.held_references) == 1
        assert len(holder.held_references) == 0
    
    def test_is_held_true(self):
        """Test 797: is_held returns True for held object."""
        holder = ReferenceHolder()
        obj = b'data'
        holder.hold(obj)
        assert holder.is_held(obj) is True
    
    def test_is_held_false(self):
        """Test 798: is_held returns False for non-held object."""
        holder = ReferenceHolder()
        assert holder.is_held(b'data') is False
    
    def test_get_count(self):
        """Test 799: Get count returns correct number."""
        holder = ReferenceHolder()
        assert holder.get_count() == 0
        holder.hold(b'a')
        holder.hold(b'b')
        assert holder.get_count() == 2
    
    def test_hold_multiple_same_object(self):
        """Test 800: Holding same object multiple times."""
        holder = ReferenceHolder()
        obj = b'test'
        holder.hold(obj)
        holder.hold(obj)
        assert holder.get_count() == 2
        holder.release(obj)
        assert holder.get_count() == 1


# ════════════════════════════════════════════════════════════════════════════
# MEMORY VALIDATOR TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestMemoryValidator:
    """MemoryValidator tests (10 tests)."""
    
    def test_validate_buffer_access_valid(self):
        """Test 801: Valid buffer access."""
        validator = MemoryValidator()
        valid, msg = validator.validate_buffer_access(0x1000, 1024, 0, 512)
        assert valid is True
        assert msg is None
    
    def test_validate_buffer_access_exact_bounds(self):
        """Test 802: Access exactly at buffer bounds."""
        validator = MemoryValidator()
        valid, _ = validator.validate_buffer_access(0x1000, 1024, 0, 1024)
        assert valid is True
    
    def test_validate_buffer_access_out_of_bounds(self):
        """Test 803: Out of bounds access."""
        validator = MemoryValidator()
        valid, msg = validator.validate_buffer_access(0x1000, 1024, 0, 2048)
        assert valid is False
        assert 'bounds' in msg.lower()
    
    def test_validate_buffer_negative_offset(self):
        """Test 804: Negative offset."""
        validator = MemoryValidator()
        valid, msg = validator.validate_buffer_access(0x1000, 1024, -1, 512)
        assert valid is False
        assert 'negative' in msg.lower()
    
    def test_validate_buffer_negative_size(self):
        """Test 805: Negative size."""
        validator = MemoryValidator()
        valid, msg = validator.validate_buffer_access(0x1000, 1024, 0, -1)
        assert valid is False
        assert 'negative' in msg.lower()
    
    def test_validate_alignment_aligned(self):
        """Test 806: Aligned address."""
        validator = MemoryValidator()
        valid, msg = validator.validate_alignment(0x1000, 4)
        assert valid is True
        assert msg is None
    
    def test_validate_alignment_unaligned(self):
        """Test 807: Unaligned address."""
        validator = MemoryValidator()
        valid, msg = validator.validate_alignment(0x1001, 4)
        assert valid is False
        assert 'not aligned' in msg
    
    def test_validate_pointer_not_null_valid(self):
        """Test 808: Non-null pointer."""
        validator = MemoryValidator()
        valid, msg = validator.validate_pointer_not_null(0x1000)
        assert valid is True
        assert msg is None
    
    def test_validate_pointer_not_null_invalid(self):
        """Test 809: Null pointer."""
        validator = MemoryValidator()
        valid, msg = validator.validate_pointer_not_null(0x0)
        assert valid is False
        assert 'null' in msg.lower()
    
    def test_validate_size_positive(self):
        """Test 810: Validate positive size."""
        validator = MemoryValidator()
        valid, _ = validator.validate_size_positive(1024)
        assert valid is True
        valid, msg = validator.validate_size_positive(0)
        assert valid is False
        valid, msg = validator.validate_size_positive(-1)
        assert valid is False


# ════════════════════════════════════════════════════════════════════════════
# PYTHON MEMORY MANAGER TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonMemoryManager:
    """PythonMemoryManager tests (15 tests)."""
    
    def test_create_manager(self):
        """Test 811: Create memory manager."""
        manager = PythonMemoryManager()
        assert manager.buffer_pinner is not None
        assert manager.allocation_tracker is not None
        assert manager.reference_holder is not None
        assert manager.memory_validator is not None
    
    def test_wrap_buffer(self):
        """Test 812: Wrap buffer."""
        manager = PythonMemoryManager()
        data = b'test'
        wrapper = manager.wrap_buffer(data)
        assert isinstance(wrapper, PythonPointerWrapper)
        assert wrapper.size == 4
        assert wrapper.is_valid() is True
    
    def test_wrap_buffer_tracks_allocation(self):
        """Test 813: Wrap buffer tracks allocation."""
        manager = PythonMemoryManager()
        data = b'test'
        wrapper = manager.wrap_buffer(data)
        stats = manager.allocation_tracker.get_statistics()
        assert stats['total_allocations'] == 1
    
    def test_wrap_buffer_pins_buffer(self):
        """Test 814: Wrap buffer pins the buffer."""
        manager = PythonMemoryManager()
        data = b'test'
        wrapper = manager.wrap_buffer(data)
        assert manager.buffer_pinner.get_pinned_count() == 1
    
    def test_wrap_buffer_holds_reference(self):
        """Test 815: Wrap buffer holds reference."""
        manager = PythonMemoryManager()
        data = b'test'
        wrapper = manager.wrap_buffer(data)
        assert manager.reference_holder.get_count() == 1
    
    def test_wrap_native_pointer(self):
        """Test 816: Wrap native pointer."""
        manager = PythonMemoryManager()
        wrapper = manager.wrap_native_pointer(0x1000, 1024)
        assert wrapper.address == 0x1000
        assert wrapper.size == 1024
        assert wrapper.ownership == OwnershipKind.CALLEE_OWNED
    
    def test_free_pointer(self):
        """Test 817: Free pointer cleans up everything."""
        manager = PythonMemoryManager()
        wrapper = manager.wrap_native_pointer(0x1000, 1024)
        manager.free_pointer(wrapper)
        assert wrapper.is_valid() is False
        assert manager.get_pointer_wrapper(0x1000) is None
    
    def test_free_buffer_pointer(self):
        """Test 818: Free buffer pointer unpins and releases."""
        manager = PythonMemoryManager()
        data = b'test'
        wrapper = manager.wrap_buffer(data)
        address = wrapper.address
        manager.free_pointer(wrapper)
        assert manager.buffer_pinner.get_pinned_count() == 0
        assert manager.reference_holder.get_count() == 0
    
    def test_get_pointer_wrapper(self):
        """Test 819: Get pointer wrapper by address."""
        manager = PythonMemoryManager()
        wrapper = manager.wrap_native_pointer(0x1000, 1024)
        found = manager.get_pointer_wrapper(0x1000)
        assert found is wrapper
    
    def test_get_pointer_wrapper_not_found(self):
        """Test 820: Get non-existent pointer wrapper."""
        manager = PythonMemoryManager()
        assert manager.get_pointer_wrapper(0x9999) is None
    
    def test_validate_buffer_access(self):
        """Test 821: Validate buffer access through manager."""
        manager = PythonMemoryManager()
        wrapper = manager.wrap_native_pointer(0x1000, 1024)
        valid, _ = manager.validate_buffer_access(wrapper, 0, 512)
        assert valid is True
    
    def test_validate_buffer_access_out_of_bounds(self):
        """Test 822: Validate buffer access out of bounds."""
        manager = PythonMemoryManager()
        wrapper = manager.wrap_native_pointer(0x1000, 1024)
        valid, msg = manager.validate_buffer_access(wrapper, 0, 2048)
        assert valid is False
    
    def test_cleanup(self):
        """Test 823: Cleanup releases all resources."""
        manager = PythonMemoryManager()
        manager.wrap_buffer(b'test1')
        manager.wrap_buffer(b'test2')
        manager.cleanup()
        assert len(manager.pointer_wrappers) == 0
        assert manager.buffer_pinner.get_pinned_count() == 0
        assert manager.reference_holder.get_count() == 0
    
    def test_get_statistics(self):
        """Test 824: Get statistics includes all sub-components."""
        manager = PythonMemoryManager()
        manager.wrap_buffer(b'test')
        stats = manager.get_statistics()
        assert 'allocation_tracker' in stats
        assert 'pinned_buffers' in stats
        assert 'held_references' in stats
        assert 'active_wrappers' in stats
        assert stats['pinned_buffers'] == 1
        assert stats['held_references'] == 1
        assert stats['active_wrappers'] == 1
    
    def test_adapter_has_memory_manager(self):
        """Test 825: PythonAdapter has memory manager."""
        adapter = PythonAdapter()
        assert isinstance(adapter.memory_manager, PythonMemoryManager)
        wrapper = adapter.prepare_buffer_parameter(b'hello')
        assert isinstance(wrapper, PythonPointerWrapper)
        assert wrapper.size == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
