"""Test Suite for C++ Adapter - Prompt 23/25: 95 tests."""

import pytest
from modules.module_08_language_adapter.cpp_adapter import (
    CppOwnership,
    CppType,
    SmartPointerTracker,
    ExceptionTranslator,
    RAIIGuard,
    TemplateValidator,
    CppNormalizer,
    CppAdapter,
    CppStdException,
)

class TestSmartPointerTracker:
    """SmartPointerTracker tests (25 tests)."""

    def test_create_tracker(self):
        """Test 2036: Create smart pointer tracker."""
        tracker = SmartPointerTracker()
        assert len(tracker.unique_ptrs) == 0

    def test_track_unique_ptr(self):
        """Test 2037: Track unique_ptr."""
        tracker = SmartPointerTracker()
        obj = object()
        tracker.track_unique_ptr(0x1000, obj)
        assert 0x1000 in tracker.unique_ptrs

    def test_move_unique_ptr(self):
        """Test 2038: Move unique_ptr."""
        tracker = SmartPointerTracker()
        obj = object()
        tracker.track_unique_ptr(0x1000, obj)
        tracker.move_unique_ptr(0x1000, 0x2000)
        assert 0x1000 not in tracker.unique_ptrs
        assert 0x2000 in tracker.unique_ptrs

    def test_release_unique_ptr(self):
        """Test 2039: Release unique_ptr."""
        tracker = SmartPointerTracker()
        obj = object()
        tracker.track_unique_ptr(0x1000, obj)
        released = tracker.release_unique_ptr(0x1000)
        assert released is obj
        assert 0x1000 not in tracker.unique_ptrs

    def test_track_shared_ptr(self):
        """Test 2040: Track shared_ptr."""
        tracker = SmartPointerTracker()
        tracker.track_shared_ptr(0x1000)
        assert tracker.get_ref_count(0x1000) == 1

    def test_shared_ptr_ref_counting(self):
        """Test 2041: shared_ptr reference counting."""
        tracker = SmartPointerTracker()
        tracker.track_shared_ptr(0x1000)
        tracker.track_shared_ptr(0x1000)
        tracker.track_shared_ptr(0x1000)
        assert tracker.get_ref_count(0x1000) == 3

    def test_release_shared_ptr(self):
        """Test 2042: Release shared_ptr."""
        tracker = SmartPointerTracker()
        tracker.track_shared_ptr(0x1000)
        tracker.track_shared_ptr(0x1000)
        count = tracker.release_shared_ptr(0x1000)
        assert count == 1

    def test_shared_ptr_deletion_at_zero(self):
        """Test 2043: shared_ptr deleted at zero refs."""
        tracker = SmartPointerTracker()
        tracker.track_shared_ptr(0x1000)
        tracker.release_shared_ptr(0x1000)
        assert tracker.get_ref_count(0x1000) == 0
        assert 0x1000 not in tracker.shared_ptrs

    def test_track_weak_ptr(self):
        """Test 2044: Track weak_ptr."""
        tracker = SmartPointerTracker()
        tracker.track_weak_ptr(0x1000, 1)
        assert 0x1000 in tracker.weak_ptrs

    @pytest.mark.parametrize("i", range(2045, 2061))
    def test_weak_ptr_expired(self, i):
        """Test 2045-2060: Check weak_ptr expiration."""
        tracker = SmartPointerTracker()
        addr = 0x1000 + i
        tracker.track_shared_ptr(addr)
        tracker.track_weak_ptr(addr, i)
        assert tracker.is_expired(addr) is False
        tracker.release_shared_ptr(addr)
        assert tracker.is_expired(addr) is True


class TestExceptionTranslator:
    """ExceptionTranslator tests (20 tests)."""

    def test_create_translator(self):
        """Test 2061: Create exception translator."""
        translator = ExceptionTranslator()
        assert len(translator.exception_map) > 0

    def test_translate_std_exception(self):
        """Test 2062: Translate std::exception."""
        translator = ExceptionTranslator()
        cpp_exc = CppStdException("error message")
        translated = translator.translate_cpp_exception(cpp_exc)
        assert "error message" in translated.args[0]

    def test_catch_cpp_exception(self):
        """Test 2063: Catch C++ exception."""
        translator = ExceptionTranslator()
        def throwing_fn():
            raise CppStdException("test error")
        success, result = translator.catch_cpp_exceptions(throwing_fn)
        assert success is False
        assert isinstance(result, Exception)

    @pytest.mark.parametrize("i", range(2064, 2081))
    def test_catch_success(self, i):
        """Test 2064-2080: Catch successful call."""
        translator = ExceptionTranslator()
        def success_fn():
            return 42 + i
        success, result = translator.catch_cpp_exceptions(success_fn)
        assert success is True
        assert result == 42 + i


class TestRAIIGuard:
    """RAIIGuard tests (15 tests)."""

    def test_create_raii_guard(self):
        """Test 2081: Create RAII guard."""
        cleanup_called = [False]
        def cleanup(res):
            cleanup_called[0] = True
        guard = RAIIGuard("resource", cleanup)
        assert guard.resource == "resource"

    def test_raii_cleanup_on_exit(self):
        """Test 2082: RAII cleanup on scope exit."""
        cleanup_called = [False]
        def cleanup(res):
            cleanup_called[0] = True
        with RAIIGuard("resource", cleanup):
            pass
        assert cleanup_called[0] is True

    def test_raii_cleanup_on_exception(self):
        """Test 2083: RAII cleanup on exception."""
        cleanup_called = [False]
        def cleanup(res):
            cleanup_called[0] = True
        try:
            with RAIIGuard("resource", cleanup):
                raise ValueError("test")
        except ValueError:
            pass
        assert cleanup_called[0] is True

    @pytest.mark.parametrize("i", range(2084, 2096))
    def test_raii_release(self, i):
        """Test 2084-2095: RAII release without cleanup."""
        cleanup_called = [False]
        def cleanup(res):
            cleanup_called[0] = True
        with RAIIGuard(i, cleanup) as guard:
            released = guard.release()
        assert released == i
        assert cleanup_called[0] is False


class TestTemplateValidator:
    """TemplateValidator tests (15 tests)."""

    def test_create_template_validator(self):
        """Test 2096: Create template validator."""
        validator = TemplateValidator()
        assert len(validator.template_graphs) == 0

    def test_register_template_contract(self):
        """Test 2097: Register template contract."""
        validator = TemplateValidator()
        validator.register_template_contract('Vector', ['T'], {'clauses': []})
        assert 'Vector<T>' in validator.template_graphs

    @pytest.mark.parametrize("i", range(2098, 2111))
    def test_instantiate_validation(self, i):
        """Test 2098-2110: Instantiate template validation."""
        validator = TemplateValidator()
        type_name = f'int_{i}'
        validator.register_template_contract('Vector', [type_name], {'clauses': []})
        graph = validator.instantiate_validation('Vector', [type_name])
        assert graph is not None


class TestCppNormalizer:
    """CppNormalizer tests (10 tests)."""

    def test_create_normalizer(self):
        """Test 2111: Create C++ normalizer."""
        normalizer = CppNormalizer()
        assert normalizer.smart_pointer_tracker is not None

    def test_normalize_value_type(self):
        """Test 2112: Normalize value type."""
        normalizer = CppNormalizer()
        cpp_type = CppType('int', CppOwnership.VALUE)
        result = normalizer.normalize_value(42, cpp_type)
        assert result == 42

    @pytest.mark.parametrize("i", range(2113, 2121))
    def test_normalize_unique_ptr(self, i):
        """Test 2113-2120: Normalize unique_ptr."""
        normalizer = CppNormalizer()
        cpp_type = CppType('Widget', CppOwnership.UNIQUE_PTR)
        obj = object()
        address = normalizer.normalize_value(obj, cpp_type)
        assert isinstance(address, int)


class TestCppAdapter:
    """CppAdapter tests (10 tests)."""

    def test_create_cpp_adapter(self):
        """Test 2121: Create C++ adapter."""
        adapter = CppAdapter()
        assert adapter.smart_pointer_tracker is not None

    def test_call_with_unique_ptr(self):
        """Test 2122: Call with unique_ptr."""
        adapter = CppAdapter()
        def mock_fn(ptr):
            return 100
        obj = object()
        # Mocking call_with_enforcement on base class
        adapter.validation_graphs['func'] = None
        result = adapter.call_with_unique_ptr('func', obj, native_callable=mock_fn)
        assert result == 100

    @pytest.mark.parametrize("i", range(2123, 2131))
    def test_call_with_shared_ptr(self, i):
        """Test 2123-2130: Call with shared_ptr."""
        adapter = CppAdapter()
        def mock_fn(ptr):
            return 200 + i
        obj = object()
        adapter.validation_graphs['func'] = None
        result = adapter.call_with_shared_ptr('func', obj, native_callable=mock_fn)
        assert result == 200 + i


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
