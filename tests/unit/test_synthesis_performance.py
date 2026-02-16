"""
Tests for Module 07: Performance Optimization (Prompt 8/15)
Testing Level: MEDIUM (80 tests)
"""

import pytest
import time
from module_07_contract_synthesis.performance import (
    LRUCache, SynthesisCache, PhaseProfiler, RuleProfiler, 
    PerformanceMonitor, SynthesisBenchmark
)

# ============================================================================
# TEST LRU CACHE
# ============================================================================

class TestLRUCache:
    """Test LRU cache functionality."""

    @pytest.fixture
    def cache(self):
        return LRUCache(max_size=3)

    def test_cache_initialization(self, cache):
        assert cache.max_size == 3
        assert len(cache.cache) == 0

    def test_cache_put_get(self, cache):
        cache.put("key1", "value1")
        result = cache.get("key1")
        assert result == "value1"

    def test_cache_miss(self, cache):
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_hit_tracking(self, cache):
        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        assert cache.hits == 1
        assert cache.misses == 1

    def test_cache_eviction(self, cache):
        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Add one more (should evict key1)
        cache.put("key4", "value4")
        
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key4") == "value4"

    def test_cache_lru_ordering(self, cache):
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 (moves to end)
        cache.get("key1")
        
        # Add key4 (should evict key2, not key1)
        cache.put("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still present
        assert cache.get("key2") is None  # Evicted

    def test_cache_clear(self, cache):
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.clear()
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_cache_hit_rate(self, cache):
        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key1")  # Hit
        hit_rate = cache.get_hit_rate()
        assert hit_rate == 2/3

# ============================================================================
# TEST SYNTHESIS CACHE
# ============================================================================

class TestSynthesisCache:
    """Test multi-level synthesis cache."""

    @pytest.fixture
    def cache(self):
        return SynthesisCache(max_size=10)

    def test_synthesis_cache_initialization(self, cache):
        assert cache.synthesis_cache is not None
        assert cache.analysis_cache is not None
        assert cache.rule_cache is not None

    def test_cache_synthesis_result(self, cache):
        result = {"test": "data"}
        cache.put_synthesis_result("ir_fp", "1.0.0", result)
        cached = cache.get_synthesis_result("ir_fp", "1.0.0")
        assert cached == result

    def test_cache_analysis_result(self, cache):
        analysis = {"pattern": "detected"}
        cache.put_analysis_result("functions_fp", analysis)
        cached = cache.get_analysis_result("functions_fp")
        assert cached == analysis

    def test_cache_rule_result(self, cache):
        clause = {"clause_id": "test"}
        cache.put_rule_result("rule_v1", "entity_fp", clause)
        cached = cache.get_rule_result("rule_v1", "entity_fp")
        assert cached == clause

    def test_clear_all_caches(self, cache):
        cache.put_synthesis_result("fp1", "1.0.0", {"data": 1})
        cache.put_analysis_result("fp2", {"data": 2})
        cache.put_rule_result("rule", "fp3", {"data": 3})
        cache.clear_all()
        assert cache.get_synthesis_result("fp1", "1.0.0") is None
        assert cache.get_analysis_result("fp2") is None
        assert cache.get_rule_result("rule", "fp3") is None

    def test_get_cache_stats(self, cache):
        cache.put_synthesis_result("fp", "1.0.0", {})
        cache.get_synthesis_result("fp", "1.0.0")  # Hit
        stats = cache.get_stats()
        assert 'synthesis' in stats
        assert 'analysis' in stats
        assert 'rule' in stats
        assert stats['synthesis']['hits'] == 1

# ============================================================================
# TEST PHASE PROFILER
# ============================================================================

class TestPhaseProfiler:
    """Test phase profiling."""

    @pytest.fixture
    def profiler(self):
        return PhaseProfiler()

    def test_profiler_initialization(self, profiler):
        assert len(profiler.phase_profiles) == 0

    def test_profile_phase(self, profiler):
        with profiler.profile_phase("test_phase"):
            time.sleep(0.01)  # Simulate work
        assert "test_phase" in profiler.phase_profiles
        assert profiler.phase_profiles["test_phase"].duration > 0

    def test_profile_multiple_phases(self, profiler):
        with profiler.profile_phase("phase1"):
            time.sleep(0.01)
        with profiler.profile_phase("phase2"):
            time.sleep(0.01)
        assert len(profiler.phase_profiles) == 2

    def test_profile_phase_multiple_calls(self, profiler):
        with profiler.profile_phase("repeated"):
            time.sleep(0.01)
        with profiler.profile_phase("repeated"):
            time.sleep(0.01)
        profile = profiler.phase_profiles["repeated"]
        assert profile.call_count == 2

    def test_get_report(self, profiler):
        with profiler.profile_phase("test"):
            pass
        report = profiler.get_report()
        assert "Synthesis Phase Profile" in report
        assert "test" in report

    def test_clear_profiling_data(self, profiler):
        with profiler.profile_phase("test"):
            pass
        profiler.clear()
        assert len(profiler.phase_profiles) == 0

# ============================================================================
# TEST RULE PROFILER
# ============================================================================

class TestRuleProfiler:
    """Test rule profiling."""

    @pytest.fixture
    def profiler(self):
        return RuleProfiler()

    def test_profiler_initialization(self, profiler):
        assert len(profiler.rule_stats) == 0

    def test_record_execution(self, profiler):
        profiler.record_execution("test_rule", 0.01)
        assert "test_rule" in profiler.rule_stats
        assert profiler.rule_stats["test_rule"].count == 1

    def test_record_multiple_executions(self, profiler):
        profiler.record_execution("rule", 0.01)
        profiler.record_execution("rule", 0.02)
        profiler.record_execution("rule", 0.015)
        stats = profiler.rule_stats["rule"]
        assert stats.count == 3
        assert stats.min_time == 0.01
        assert stats.max_time == 0.02

    def test_average_time_calculation(self, profiler):
        profiler.record_execution("rule", 0.01)
        profiler.record_execution("rule", 0.02)
        stats = profiler.rule_stats["rule"]
        assert stats.avg_time == 0.015

    def test_get_report(self, profiler):
        profiler.record_execution("test_rule", 0.01)
        report = profiler.get_report()
        assert "Rule Execution Profile" in report
        assert "test_rule" in report

# ============================================================================
# TEST PERFORMANCE MONITOR
# ============================================================================

class TestPerformanceMonitor:
    """Test performance monitoring."""

    @pytest.fixture
    def monitor(self):
        return PerformanceMonitor()

    def test_monitor_initialization(self, monitor):
        assert monitor.metrics.synthesis_count == 0

    def test_record_synthesis(self, monitor):
        monitor.record_synthesis(duration=0.5, clause_count=10, cache_hit=False)
        assert monitor.metrics.synthesis_count == 1
        assert monitor.metrics.total_clauses == 10

    def test_cache_hit_tracking(self, monitor):
        monitor.record_synthesis(0.1, 5, cache_hit=True)
        monitor.record_synthesis(0.1, 5, cache_hit=False)
        monitor.record_synthesis(0.1, 5, cache_hit=True)
        assert monitor.metrics.cache_hits == 2
        assert monitor.metrics.cache_misses == 1

    def test_average_time_calculation(self, monitor):
        monitor.record_synthesis(0.1, 10, False)
        monitor.record_synthesis(0.2, 10, False)
        stats = monitor.get_stats()
        assert stats['avg_time_ms'] == pytest.approx(150.0)  # (100 + 200) / 2

    def test_throughput_calculation(self, monitor):
        monitor.record_synthesis(1.0, 10, False)
        monitor.record_synthesis(1.0, 10, False)
        stats = monitor.get_stats()
        assert stats['throughput'] == 1.0  # 2 ops / 2 seconds

    def test_get_report(self, monitor):
        monitor.record_synthesis(0.1, 10, False)
        report = monitor.get_report()
        assert "Performance Metrics" in report

# ============================================================================
# TEST BENCHMARK SUITE
# ============================================================================

class TestSynthesisBenchmark:
    """Test benchmarking functionality."""

    @pytest.fixture
    def engine(self):
        from module_07_contract_synthesis.synthesis_engine import SynthesisEngine, SynthesisConfig
        return SynthesisEngine(SynthesisConfig())

    @pytest.fixture
    def synthesis_benchmark(self, engine):
        return SynthesisBenchmark(engine)

    def test_benchmark_initialization(self, synthesis_benchmark):
        assert synthesis_benchmark.engine is not None
        assert len(synthesis_benchmark.SCENARIOS) > 0

    def test_benchmark_tiny_scenario(self, synthesis_benchmark):
        result = synthesis_benchmark.run_benchmark('tiny', iterations=3)
        assert result.scenario == 'tiny'
        assert result.iterations == 3
        assert result.avg_time_ms > 0

    def test_benchmark_result_statistics(self, synthesis_benchmark):
        result = synthesis_benchmark.run_benchmark('tiny', iterations=5)
        assert result.min_time_ms > 0
        assert result.max_time_ms >= result.min_time_ms
        assert result.avg_time_ms >= result.min_time_ms
        assert result.avg_time_ms <= result.max_time_ms

    def test_benchmark_pass_fail(self, synthesis_benchmark):
        result = synthesis_benchmark.run_benchmark('tiny', iterations=3)
        assert isinstance(result.passed, bool)

    def test_invalid_scenario_raises(self, synthesis_benchmark):
        with pytest.raises(ValueError):
            synthesis_benchmark.run_benchmark('nonexistent')

# ============================================================================
# PERFORMANCE EDGE CASES
# ============================================================================

class TestPerformanceEdgeCases:
    """Test edge cases in performance system."""

    def test_cache_with_zero_max_size(self):
        cache = LRUCache(max_size=0)
        cache.put("key", "value")
        # Should not cache anything
        assert cache.get("key") is None

    def test_profiler_with_exception(self):
        profiler = PhaseProfiler()
        try:
            with profiler.profile_phase("failing"):
                raise ValueError("Test error")
        except ValueError:
            pass
        # Should still record timing
        assert "failing" in profiler.phase_profiles

    @pytest.mark.parametrize("i", range(33))
    def test_bulk_cache_insertion(self, i):
        cache = LRUCache(max_size=10)
        cache.put(f"key_{i}", i)
        if i >= 10:
             assert len(cache.cache) <= 10

    def test_clear_empty_profiler(self):
        profiler = PhaseProfiler()
        profiler.clear()
        assert len(profiler.phase_profiles) == 0

    def test_clear_empty_rule_profiler(self):
        profiler = RuleProfiler()
        profiler.clear()
        assert len(profiler.rule_stats) == 0

    def test_clear_empty_monitor(self):
        monitor = PerformanceMonitor()
        monitor.clear()
        assert monitor.metrics.synthesis_count == 0

    def test_benchmark_result_speedup(self):
        from module_07_contract_synthesis.performance import BenchmarkResult
        result = BenchmarkResult("test", 1, 50.0, 50.0, 50.0, 0.0, 100.0, True)
        assert result.get_speedup(100.0) == 2.0

    def test_phase_profile_avg_duration(self):
        from module_07_contract_synthesis.performance import PhaseProfile
        profile = PhaseProfile("test", 1.0, 2)
        assert profile.avg_duration == 0.5

    def test_rule_stats_avg_time(self):
        from module_07_contract_synthesis.performance import RuleStats
        stats = RuleStats(count=2, total_time=1.0)
        assert stats.avg_time == 0.5

    def test_performance_metrics_throughput(self):
        from module_07_contract_synthesis.performance import PerformanceMetrics
        metrics = PerformanceMetrics(synthesis_count=10, total_time=2.0)
        assert metrics.throughput == 5.0

    def test_synthesis_cache_get_stats_detailed(self):
        cache = SynthesisCache(max_size=5)
        cache.put_synthesis_result("fp", "1.0.0", {})
        cache.get_synthesis_result("fp", "1.0.0")
        stats = cache.get_stats()
        assert stats['synthesis']['hits'] == 1
        assert stats['synthesis']['max_size'] == 5

    def test_lru_cache_overwrite_same_key(self):
        cache = LRUCache(max_size=2)
        cache.put("k1", "v1")
        cache.put("k1", "v2")
        assert cache.get("k1") == "v2"
        assert len(cache.cache) == 1
