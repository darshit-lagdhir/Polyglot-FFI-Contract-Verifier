"""Test Suite for Rust Adapter - Prompt 22/25: 90 tests."""

import pytest
from typing import Any, List
from modules.module_08_language_adapter.rust_adapter import (
    RustOwnership,
    RustType,
    RustTypeMapper,
    RustOwnershipBridge,
    RustNormalizer,
    RustAdapter,
    SafeFFIWrapper,
    RustExceptionHandler,
    RustPanic,
)

class TestRustType:
    """RustType tests (15 tests)."""

    def test_create_rust_type(self):
        """Test 1946: Create Rust type."""
        rust_type = RustType('i32', RustOwnership.OWNED)
        assert rust_type.name == 'i32'
        assert rust_type.ownership == RustOwnership.OWNED

    def test_owned_to_c_type(self):
        """Test 1947: Convert owned type to C."""
        rust_type = RustType('i32', RustOwnership.OWNED)
        c_type = rust_type.to_c_type()
        assert c_type == 'int32_t'

    def test_borrowed_to_c_type(self):
        """Test 1948: Convert borrowed type to C."""
        rust_type = RustType('i32', RustOwnership.BORROWED)
        c_type = rust_type.to_c_type()
        assert 'const' in c_type
        assert '*' in c_type

    def test_mutable_to_c_type(self):
        """Test 1949: Convert mutable borrow to C."""
        rust_type = RustType('u64', RustOwnership.MUTABLE)
        c_type = rust_type.to_c_type()
        assert '*' in c_type
        assert 'const' not in c_type

    @pytest.mark.parametrize("i", range(1950, 1961))
    def test_nullable_type(self, i):
        """Test 1950-1960: Nullable type."""
        rust_type = RustType('i32', RustOwnership.OWNED, is_nullable=(i % 2 == 0))
        assert rust_type.is_nullable == (i % 2 == 0)


class TestRustTypeMapper:
    """RustTypeMapper tests (20 tests)."""

    def test_create_type_mapper(self):
        """Test 1961: Create type mapper."""
        mapper = RustTypeMapper()
        assert len(mapper.type_cache) == 0

    def test_infer_owned_ownership(self):
        """Test 1962: Infer owned ownership."""
        mapper = RustTypeMapper()
        ownership = mapper.infer_ownership('Vec<u8>')
        assert ownership == RustOwnership.OWNED

    def test_infer_borrowed_ownership(self):
        """Test 1963: Infer borrowed ownership."""
        mapper = RustTypeMapper()
        ownership = mapper.infer_ownership('&str')
        assert ownership == RustOwnership.BORROWED

    def test_infer_mutable_ownership(self):
        """Test 1964: Infer mutable ownership."""
        mapper = RustTypeMapper()
        ownership = mapper.infer_ownership('&mut Vec<u8>')
        assert ownership == RustOwnership.MUTABLE

    def test_infer_raw_const_ownership(self):
        """Test 1965: Infer raw const ownership."""
        mapper = RustTypeMapper()
        ownership = mapper.infer_ownership('*const u8')
        assert ownership == RustOwnership.RAW_CONST

    def test_infer_raw_mut_ownership(self):
        """Test 1966: Infer raw mut ownership."""
        mapper = RustTypeMapper()
        ownership = mapper.infer_ownership('*mut u8')
        assert ownership == RustOwnership.RAW_MUT

    def test_parse_simple_type(self):
        """Test 1967: Parse simple type."""
        mapper = RustTypeMapper()
        rust_type = mapper.parse_rust_type('i32')
        assert rust_type.name == 'i32'
        assert rust_type.ownership == RustOwnership.OWNED

    def test_parse_borrowed_type(self):
        """Test 1968: Parse borrowed type."""
        mapper = RustTypeMapper()
        rust_type = mapper.parse_rust_type('&str')
        assert rust_type.ownership == RustOwnership.BORROWED

    def test_parse_option_type(self):
        """Test 1969: Parse Option type."""
        mapper = RustTypeMapper()
        rust_type = mapper.parse_rust_type('Option<i32>')
        assert rust_type.is_nullable is True
        assert rust_type.name == 'i32'

    @pytest.mark.parametrize("i", range(1970, 1981))
    def test_type_caching(self, i):
        """Test 1970-1980: Type parsing is cached."""
        mapper = RustTypeMapper()
        type_str = f'i32_{i % 3}'
        type1 = mapper.parse_rust_type(type_str)
        type2 = mapper.parse_rust_type(type_str)
        assert type1 is type2


class TestRustOwnershipBridge:
    """RustOwnershipBridge tests (20 tests)."""

    def test_create_ownership_bridge(self):
        """Test 1981: Create ownership bridge."""
        bridge = RustOwnershipBridge()
        assert len(bridge.borrows) == 0

    def test_record_borrow(self):
        """Test 1982: Record borrow."""
        bridge = RustOwnershipBridge()
        bridge.record_borrow(0x1000, RustOwnership.BORROWED)
        assert 0x1000 in bridge.borrows
        assert bridge.borrows[0x1000] == RustOwnership.BORROWED

    def test_validate_borrow_correct(self):
        """Test 1983: Validate correct borrow."""
        bridge = RustOwnershipBridge()
        bridge.record_borrow(0x1000, RustOwnership.BORROWED)
        valid = bridge.validate_borrow(0x1000, RustOwnership.BORROWED)
        assert valid is True

    def test_validate_borrow_incorrect(self):
        """Test 1984: Validate incorrect borrow."""
        bridge = RustOwnershipBridge()
        bridge.record_borrow(0x1000, RustOwnership.BORROWED)
        valid = bridge.validate_borrow(0x1000, RustOwnership.MUTABLE)
        assert valid is False

    def test_release_borrow(self):
        """Test 1985: Release borrow."""
        bridge = RustOwnershipBridge()
        bridge.record_borrow(0x1000, RustOwnership.BORROWED)
        bridge.release_borrow(0x1000)
        assert 0x1000 not in bridge.borrows

    def test_record_lifetime(self):
        """Test 1986: Record lifetime."""
        bridge = RustOwnershipBridge()
        bridge.record_borrow(0x1000, RustOwnership.BORROWED, lifetime='a')
        assert bridge.lifetimes[0x1000] == 'a'

    @pytest.mark.parametrize("i", range(1987, 2001))
    def test_check_lifetime_valid(self, i):
        """Test 1987-2000: Check lifetime validity."""
        bridge = RustOwnershipBridge()
        addr = 0x1000 + i
        bridge.record_borrow(addr, RustOwnership.BORROWED, lifetime=f'scope_{i}')
        valid = bridge.check_lifetime_valid(addr, f'scope_{i}')
        assert valid is True


class TestRustNormalizer:
    """RustNormalizer tests (15 tests)."""

    def test_create_normalizer(self):
        """Test 2001: Create normalizer."""
        normalizer = RustNormalizer()
        assert normalizer.type_mapper is not None

    def test_normalize_owned_value(self):
        """Test 2002: Normalize owned value."""
        normalizer = RustNormalizer()
        rust_type = RustType('i32', RustOwnership.OWNED)
        result = normalizer.normalize_value(42, rust_type)
        assert result == 42

    def test_normalize_none_option(self):
        """Test 2003: Normalize None Option."""
        normalizer = RustNormalizer()
        rust_type = RustType('i32', RustOwnership.OWNED, is_nullable=True)
        result = normalizer.normalize_value(None, rust_type)
        assert result is None

    @pytest.mark.parametrize("i", range(2004, 2016))
    def test_normalize_slice(self, i):
        """Test 2004-2015: Normalize slice."""
        normalizer = RustNormalizer()
        data = list(range(i % 10 + 1))
        ptr, length = normalizer.normalize_slice(data)
        assert length == len(data)
        assert isinstance(ptr, int)


class TestRustAdapter:
    """RustAdapter tests (20 tests)."""

    def test_create_rust_adapter(self):
        """Test 2016: Create Rust adapter."""
        adapter = RustAdapter()
        assert adapter.type_mapper is not None
        assert adapter.ownership_bridge is not None

    def test_validate_pre_call_minimal(self):
        """Test 2017: Pre-call validation minimal."""
        adapter = RustAdapter()
        # No validation graph - should pass
        result = adapter.validate_pre_call('test_func', [42])
        assert result is True

    def test_transfer_ownership(self):
        """Test 2018: Transfer ownership to native."""
        adapter = RustAdapter()
        adapter.transfer_ownership_to_native('value', 0x1000)
        assert 0x1000 in adapter.ownership_bridge.borrows

    def test_borrow_immutable(self):
        """Test 2019: Borrow immutably."""
        adapter = RustAdapter()
        adapter.borrow_for_call('value', 0x2000, mutable=False)
        borrow = adapter.ownership_bridge.borrows[0x2000]
        assert borrow == RustOwnership.BORROWED

    def test_borrow_mutable(self):
        """Test 2020: Borrow mutably."""
        adapter = RustAdapter()
        adapter.borrow_for_call('value', 0x3000, mutable=True)
        borrow = adapter.ownership_bridge.borrows[0x3000]
        assert borrow == RustOwnership.MUTABLE

    @pytest.mark.parametrize("i", range(2021, 2036))
    def test_call_unsafe_function(self, i):
        """Test 2021-2035: Call unsafe function."""
        adapter = RustAdapter()
        def unsafe_op(a, b):
            return a + b + i
        result = adapter.call_unsafe('op', unsafe_op, 10, 20)
        assert result == 10 + 20 + i

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
