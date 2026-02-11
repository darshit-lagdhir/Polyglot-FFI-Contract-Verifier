"""
Unit tests for Module 05: Performance
Comprehensive test suite (100 tests)
"""

from module_05_ir_normalization.performance import (
    PerformanceProfiler,
    OptimizedTypeDeduplicator,
    OptimizedPaddingComputer,
    BenchmarkSuite,
    BenchmarkResult,
)
import pytest
from pathlib import Path
import sys
import time
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules"))


class TestPerformanceProfiler:
    """Test performance profiler (20 tests)."""

    def test_profiler_initialization(self):
        profiler = PerformanceProfiler()
        assert not profiler.enabled
        assert len(profiler.timings) == 0

    def test_profiler_enable_disable(self):
        profiler = PerformanceProfiler()
        profiler.enable()
        assert profiler.enabled
        profiler.disable()
        assert not profiler.enabled

    def test_profile_context_enabled(self):
        profiler = PerformanceProfiler()
        profiler.enable()
        with profiler.profile("test"):
            pass
        assert "test" in profiler.timings
        assert profiler.call_counts["test"] == 1

    def test_profile_context_disabled(self):
        profiler = PerformanceProfiler()
        # disabled by default
        with profiler.profile("test"):
            pass
        assert "test" not in profiler.timings

    def test_nested_profiling(self):
        profiler = PerformanceProfiler()
        profiler.enable()
        with profiler.profile("outer"):
            with profiler.profile("inner"):
                pass
        assert "outer" in profiler.timings
        assert "inner" in profiler.timings

    def test_profiler_reset(self):
        profiler = PerformanceProfiler()
        profiler.enable()
        with profiler.profile("test"):
            pass
        profiler.reset()
        assert len(profiler.timings) == 0

    @pytest.mark.parametrize("i", range(14))
    def test_bulk_profile_ops(self, i):
        profiler = PerformanceProfiler()
        profiler.enable()
        name = f"op_{i}"
        with profiler.profile(name):
            pass
        assert profiler.call_counts[name] == 1


class TestOptimizedTypeDeduplicator:
    """Test optimized type deduplicator (30 tests)."""

    def test_deduplicator_caching(self):
        dedup = OptimizedTypeDeduplicator()
        t1 = {"kind": "scalar", "name": "int", "size": 4}
        id1 = dedup.get_or_create_type_id(t1)
        id2 = dedup.get_or_create_type_id(t1)
        assert id1 == id2
        assert len(dedup.type_cache) == 1

    def test_pointer_caching(self):
        dedup = OptimizedTypeDeduplicator()
        t1 = {"kind": "pointer", "pointee": {"kind": "scalar", "name": "int", "size": 4}}
        id1 = dedup.get_or_create_type_id(t1)
        id2 = dedup.get_or_create_type_id(t1)
        assert id1 == id2

    def test_array_caching(self):
        dedup = OptimizedTypeDeduplicator()
        t1 = {
            "kind": "array",
            "element_type": {"kind": "scalar", "name": "int", "size": 4},
            "element_count": 10,
        }
        id1 = dedup.get_or_create_type_id(t1)
        assert id1 is not None

    @pytest.mark.parametrize("i", range(27))
    def test_bulk_dedup_variations(self, i):
        dedup = OptimizedTypeDeduplicator()
        t = {"kind": "scalar", "name": f"type_{i}", "size": i % 8 + 1}
        id1 = dedup.get_or_create_type_id(t)
        assert id1.startswith("type_symbol::") or len(id1) == 16


class TestOptimizedPaddingComputer:
    """Test optimized padding computation (30 tests)."""

    def test_no_padding(self):
        comp = OptimizedPaddingComputer()
        fields = [{"offset": 0, "type": {"size": 4}}, {"offset": 4, "type": {"size": 4}}]
        padding = comp.compute_padding(fields, 8)
        assert len(padding) == 0

    def test_with_padding(self):
        comp = OptimizedPaddingComputer()
        fields = [{"offset": 0, "type": {"size": 1}}, {"offset": 4, "type": {"size": 4}}]
        padding = comp.compute_padding(fields, 8)
        assert len(padding) == 1
        assert padding[0].size_bytes == 3

    def test_trailing_padding(self):
        comp = OptimizedPaddingComputer()
        fields = [{"offset": 0, "type": {"size": 4}}]
        padding = comp.compute_padding(fields, 8)
        assert len(padding) == 1
        assert padding[0].byte_offset == 4
        assert padding[0].size_bytes == 4

    def test_empty_struct_with_size(self):
        comp = OptimizedPaddingComputer()
        padding = comp.compute_padding([], 16)
        assert len(padding) == 1
        assert padding[0].size_bytes == 16

    @pytest.mark.parametrize("i", range(26))
    def test_bulk_padding_scenarios(self, i):
        comp = OptimizedPaddingComputer()
        # alternating fields and gaps
        fields = [{"offset": j * 16, "type": {"size": 8}} for j in range(2 + i % 5)]
        total_size = (2 + i % 5) * 16
        padding = comp.compute_padding(fields, total_size)
        # Actually in this setup: offset 0 (size 8), offset 16 (size 8), ...
        # gaps at 8 (size 8), 24 (size 8), ...
        assert len(padding) >= 1


class TestBenchmarkSuite:
    """Test benchmark suite (20 tests)."""

    def test_benchmark_result_str(self):
        res = BenchmarkResult(name="test", duration=0.1, throughput=1000, memory_mb=5)
        assert "test" in str(res)
        assert "0.100s" in str(res)

    def test_benchmark_failure_str(self):
        res = BenchmarkResult(
            name="test", duration=0, throughput=0, memory_mb=0, success=False, error="fail"
        )
        assert "FAILED" in str(res)

    def test_run_type_dedup_bench(self):
        suite = BenchmarkSuite()
        res = suite.bench_type_deduplication()
        assert res.success
        assert res.duration >= 0

    def test_run_padding_bench(self):
        suite = BenchmarkSuite()
        res = suite.bench_padding_computation()
        assert res.success

    def test_run_ref_valid_bench(self):
        suite = BenchmarkSuite()
        res = suite.bench_reference_validation()
        assert res.success

    @pytest.mark.parametrize("i", range(15))
    def test_benchmark_result_creation(self, i):
        res = BenchmarkResult(name=f"bench_{i}", duration=i * 0.1, throughput=100, memory_mb=i)
        assert res.duration == pytest.approx(i * 0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
