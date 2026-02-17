"""Test Suite for Language Adapter - Prompt 14/25: 95 tests."""

import pytest
import time
from modules.module_08_language_adapter import (
    ValidationCache,
    PredicateCache,
    FastPathDetector,
    LazyEvaluator,
    PerformanceProfiler,
    OptimizationManager,
    PythonAdapterComplete,
    ValidationGraph,
    ValidationNode,
    ClauseSeverity,
    AdapterConfig,
    EnforcementMode,
)


# ════════════════════════════════════════════════════════════════════════════
# VALIDATION CACHE TESTS (25 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestValidationCache:
    """ValidationCache tests (25 tests)."""

    def test_create_cache(self):
        """Test 1196: Create validation cache."""
        cache = ValidationCache()
        assert cache.enabled is True

    def test_cache_default_max_entries(self):
        """Test 1197: Default max entries."""
        cache = ValidationCache()
        assert cache.max_entries == 1000

    def test_cache_default_ttl(self):
        """Test 1198: Default TTL."""
        cache = ValidationCache()
        assert cache.ttl_seconds == 300

    def test_cache_custom_max(self):
        """Test 1199: Custom max entries."""
        cache = ValidationCache(max_entries=50)
        assert cache.max_entries == 50

    def test_cache_custom_ttl(self):
        """Test 1200: Custom TTL."""
        cache = ValidationCache(ttl_seconds=60)
        assert cache.ttl_seconds == 60

    def test_cache_miss(self):
        """Test 1201: Cache miss returns None."""
        cache = ValidationCache()
        result = cache.get('func1', 'clause1', [42])
        assert result is None

    def test_cache_put_get(self):
        """Test 1202: Put and get from cache."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], True)

        result = cache.get('func1', 'clause1', [42])
        assert result is True

    def test_cache_put_get_false(self):
        """Test 1203: Cache False results."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], False)

        result = cache.get('func1', 'clause1', [42])
        assert result is False

    def test_cache_different_inputs(self):
        """Test 1204: Different inputs miss cache."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], True)

        result = cache.get('func1', 'clause1', [43])
        assert result is None

    def test_cache_different_function(self):
        """Test 1205: Different function misses cache."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], True)

        result = cache.get('func2', 'clause1', [42])
        assert result is None

    def test_cache_different_clause(self):
        """Test 1206: Different clause misses cache."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], True)

        result = cache.get('func1', 'clause2', [42])
        assert result is None

    def test_cache_disabled_put(self):
        """Test 1207: Disabled cache ignores put."""
        cache = ValidationCache()
        cache.enabled = False
        cache.put('func1', 'clause1', [42], True)

        assert len(cache.cache) == 0

    def test_cache_disabled_get(self):
        """Test 1208: Disabled cache returns None on get."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], True)
        cache.enabled = False

        result = cache.get('func1', 'clause1', [42])
        assert result is None

    def test_cache_ttl_expiration(self):
        """Test 1209: TTL expiration."""
        cache = ValidationCache(ttl_seconds=1)
        cache.put('func1', 'clause1', [42], True)

        time.sleep(1.1)

        result = cache.get('func1', 'clause1', [42])
        assert result is None

    def test_cache_lru_eviction(self):
        """Test 1210: LRU eviction at capacity."""
        cache = ValidationCache(max_entries=2)

        cache.put('func1', 'clause1', [1], True)
        cache.put('func1', 'clause2', [2], True)
        cache.put('func1', 'clause3', [3], True)

        assert len(cache.cache) == 2

    def test_cache_invalidate_all(self):
        """Test 1211: Invalidate all entries."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], True)
        cache.put('func2', 'clause1', [42], True)

        cache.invalidate()

        assert len(cache.cache) == 0

    def test_cache_invalidate_function(self):
        """Test 1212: Invalidate specific function."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], True)
        cache.put('func2', 'clause1', [42], True)

        cache.invalidate('func1')

        assert cache.get('func1', 'clause1', [42]) is None
        assert cache.get('func2', 'clause1', [42]) is True

    def test_cache_statistics(self):
        """Test 1213: Cache statistics."""
        cache = ValidationCache()
        cache.put('func1', 'clause1', [42], True)

        stats = cache.get_statistics()
        assert stats['entries'] == 1
        assert stats['enabled'] is True
        assert stats['max_entries'] == 1000
        assert stats['ttl_seconds'] == 300

    def test_cache_statistics_empty(self):
        """Test 1214: Empty cache statistics."""
        cache = ValidationCache()
        stats = cache.get_statistics()
        assert stats['entries'] == 0

    def test_cache_multiple_entries(self):
        """Test 1215: Multiple entries."""
        cache = ValidationCache()
        for i in range(10):
            cache.put('func1', f'clause{i}', [i], True)

        stats = cache.get_statistics()
        assert stats['entries'] == 10

    def test_cache_key_format(self):
        """Test 1216: Cache key format."""
        cache = ValidationCache()
        key = cache._make_key('func1', 'clause1', 'hash123')
        assert key == 'func1:clause1:hash123'

    def test_cache_hash_inputs(self):
        """Test 1217: Hash inputs produces consistent hash."""
        cache = ValidationCache()
        hash1 = cache._hash_inputs([42, 3.14])
        hash2 = cache._hash_inputs([42, 3.14])
        assert hash1 == hash2

    def test_cache_hash_different_inputs(self):
        """Test 1218: Different inputs produce different hash."""
        cache = ValidationCache()
        hash1 = cache._hash_inputs([42])
        hash2 = cache._hash_inputs([43])
        assert hash1 != hash2

    def test_cache_lru_evicts_oldest(self):
        """Test 1219: LRU evicts the least recently used."""
        cache = ValidationCache(max_entries=2)

        cache.put('func1', 'c1', [1], True)
        time.sleep(0.01)
        cache.put('func1', 'c2', [2], True)
        time.sleep(0.01)

        # Access c1 to make it recently used
        cache.get('func1', 'c1', [1])
        time.sleep(0.01)

        # Add c3 — should evict c2 (LRU)
        cache.put('func1', 'c3', [3], True)

        assert cache.get('func1', 'c1', [1]) is True
        assert cache.get('func1', 'c2', [2]) is None

    def test_cache_invalidate_preserves_other(self):
        """Test 1220: Function invalidation preserves others."""
        cache = ValidationCache()
        cache.put('func1', 'c1', [1], True)
        cache.put('func2', 'c1', [1], False)
        cache.put('func3', 'c1', [1], True)

        cache.invalidate('func1')

        assert cache.get('func2', 'c1', [1]) is False
        assert cache.get('func3', 'c1', [1]) is True


# ════════════════════════════════════════════════════════════════════════════
# PREDICATE CACHE TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPredicateCache:
    """PredicateCache tests (15 tests)."""

    def test_create_predicate_cache(self):
        """Test 1221: Create predicate cache."""
        cache = PredicateCache()
        assert len(cache.compiled_predicates) == 0

    def test_cache_compiled_predicate(self):
        """Test 1222: Cache compiled predicate."""
        cache = PredicateCache()
        pred = lambda x: x > 0

        cache.cache_compiled_predicate('pred1', pred)

        result = cache.get_compiled_predicate('pred1')
        assert result is pred

    def test_get_nonexistent_predicate(self):
        """Test 1223: Get nonexistent predicate."""
        cache = PredicateCache()
        assert cache.get_compiled_predicate('missing') is None

    def test_hit_count_on_hit(self):
        """Test 1224: Hit count increments on cache hit."""
        cache = PredicateCache()
        cache.cache_compiled_predicate('pred1', lambda x: x)

        cache.get_compiled_predicate('pred1')

        assert cache.hit_count == 1

    def test_miss_count_on_miss(self):
        """Test 1225: Miss count increments on cache miss."""
        cache = PredicateCache()
        cache.get_compiled_predicate('missing')

        assert cache.miss_count == 1

    def test_predicate_cache_statistics(self):
        """Test 1226: Predicate cache statistics."""
        cache = PredicateCache()
        cache.cache_compiled_predicate('pred1', lambda x: x > 0)

        stats = cache.get_statistics()
        assert stats['compiled_predicates'] == 1

    def test_hit_rate_calculation(self):
        """Test 1227: Hit rate calculation."""
        cache = PredicateCache()
        cache.cache_compiled_predicate('pred1', lambda x: x)

        cache.get_compiled_predicate('pred1')  # hit
        cache.get_compiled_predicate('pred1')  # hit
        cache.get_compiled_predicate('miss')   # miss

        stats = cache.get_statistics()
        assert stats['hit_rate'] == pytest.approx(2/3)

    def test_hit_rate_empty(self):
        """Test 1228: Hit rate with no lookups."""
        cache = PredicateCache()
        stats = cache.get_statistics()
        assert stats['hit_rate'] == 0.0

    def test_multiple_predicates(self):
        """Test 1229: Multiple predicates."""
        cache = PredicateCache()
        cache.cache_compiled_predicate('pred1', lambda x: x > 0)
        cache.cache_compiled_predicate('pred2', lambda x: x < 100)

        assert cache.get_compiled_predicate('pred1') is not None
        assert cache.get_compiled_predicate('pred2') is not None

    def test_overwrite_predicate(self):
        """Test 1230: Overwrite predicate."""
        cache = PredicateCache()
        pred_old = lambda x: x > 0
        pred_new = lambda x: x > 10

        cache.cache_compiled_predicate('pred1', pred_old)
        cache.cache_compiled_predicate('pred1', pred_new)

        assert cache.get_compiled_predicate('pred1') is pred_new

    def test_statistics_after_operations(self):
        """Test 1231: Statistics after mixed operations."""
        cache = PredicateCache()
        cache.cache_compiled_predicate('p1', lambda: None)

        cache.get_compiled_predicate('p1')   # hit
        cache.get_compiled_predicate('p2')   # miss
        cache.get_compiled_predicate('p1')   # hit

        stats = cache.get_statistics()
        assert stats['hit_count'] == 2
        assert stats['miss_count'] == 1
        assert stats['compiled_predicates'] == 1

    def test_result_cache_initialized(self):
        """Test 1232: Result cache initialized empty."""
        cache = PredicateCache()
        assert len(cache.result_cache) == 0

    def test_predicate_callable(self):
        """Test 1233: Cached predicate is callable."""
        cache = PredicateCache()
        cache.cache_compiled_predicate('pred1', lambda x: x > 0)

        pred = cache.get_compiled_predicate('pred1')
        assert callable(pred)
        assert pred(5) is True
        assert pred(-1) is False

    def test_initial_counts_zero(self):
        """Test 1234: Initial hit/miss counts are zero."""
        cache = PredicateCache()
        assert cache.hit_count == 0
        assert cache.miss_count == 0

    def test_predicate_count_in_stats(self):
        """Test 1235: Predicate count in statistics."""
        cache = PredicateCache()
        for i in range(5):
            cache.cache_compiled_predicate(f'pred{i}', lambda x: x)

        stats = cache.get_statistics()
        assert stats['compiled_predicates'] == 5


# ════════════════════════════════════════════════════════════════════════════
# FAST PATH DETECTOR TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestFastPathDetector:
    """FastPathDetector tests (15 tests)."""

    def test_create_detector(self):
        """Test 1236: Create fast path detector."""
        detector = FastPathDetector()
        assert detector is not None

    def test_skip_validation_no_graph(self):
        """Test 1237: Skip validation when no graph."""
        detector = FastPathDetector()
        config = AdapterConfig()

        assert detector.can_skip_validation(None, config) is True

    def test_skip_validation_empty_graph(self):
        """Test 1238: Skip validation for empty graph."""
        detector = FastPathDetector()
        config = AdapterConfig()
        graph = ValidationGraph('func')

        assert detector.can_skip_validation(graph, config) is True

    def test_no_skip_with_mandatory_nodes(self):
        """Test 1239: Don't skip with mandatory nodes."""
        detector = FastPathDetector()
        config = AdapterConfig()
        graph = ValidationGraph('func')
        node = ValidationNode('c1', 'test', ClauseSeverity.MANDATORY)
        graph.add_node(node)

        assert detector.can_skip_validation(graph, config) is False

    def test_skip_permissive_advisory_only(self):
        """Test 1240: Skip in permissive mode with advisory only."""
        detector = FastPathDetector()
        config = AdapterConfig(mode=EnforcementMode.PERMISSIVE)
        graph = ValidationGraph('func')
        node = ValidationNode('c1', 'test', ClauseSeverity.ADVISORY)
        graph.add_node(node)

        assert detector.can_skip_validation(graph, config) is True

    def test_no_skip_permissive_with_mandatory(self):
        """Test 1241: Don't skip permissive with mandatory."""
        detector = FastPathDetector()
        config = AdapterConfig(mode=EnforcementMode.PERMISSIVE)
        graph = ValidationGraph('func')
        node = ValidationNode('c1', 'test', ClauseSeverity.MANDATORY)
        graph.add_node(node)

        assert detector.can_skip_validation(graph, config) is False

    def test_no_skip_strict_advisory_only(self):
        """Test 1242: Don't skip in strict mode even with advisory."""
        detector = FastPathDetector()
        config = AdapterConfig(mode=EnforcementMode.STRICT)
        graph = ValidationGraph('func')
        node = ValidationNode('c1', 'test', ClauseSeverity.ADVISORY)
        graph.add_node(node)

        assert detector.can_skip_validation(graph, config) is False

    def test_skip_normalization_simple_types(self):
        """Test 1243: Skip normalization for simple types."""
        detector = FastPathDetector()
        inputs = [42, 3.14, True, None]

        assert detector.can_skip_normalization(inputs) is True

    def test_no_skip_normalization_strings(self):
        """Test 1244: Don't skip for strings."""
        detector = FastPathDetector()
        inputs = [42, 'string']

        assert detector.can_skip_normalization(inputs) is False

    def test_no_skip_normalization_lists(self):
        """Test 1245: Don't skip for lists."""
        detector = FastPathDetector()
        inputs = [[1, 2, 3]]

        assert detector.can_skip_normalization(inputs) is False

    def test_no_skip_normalization_dicts(self):
        """Test 1246: Don't skip for dicts."""
        detector = FastPathDetector()
        inputs = [{'key': 'val'}]

        assert detector.can_skip_normalization(inputs) is False

    def test_skip_normalization_empty(self):
        """Test 1247: Skip for empty inputs."""
        detector = FastPathDetector()
        assert detector.can_skip_normalization([]) is True

    def test_skip_diagnostics_disabled(self):
        """Test 1248: Skip diagnostics when disabled."""
        detector = FastPathDetector()
        assert detector.can_skip_diagnostics(False) is True

    def test_no_skip_diagnostics_enabled(self):
        """Test 1249: Don't skip diagnostics when enabled."""
        detector = FastPathDetector()
        assert detector.can_skip_diagnostics(True) is False

    def test_skip_normalization_none_only(self):
        """Test 1250: Skip normalization for None-only."""
        detector = FastPathDetector()
        assert detector.can_skip_normalization([None]) is True


# ════════════════════════════════════════════════════════════════════════════
# LAZY EVALUATOR TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestLazyEvaluator:
    """LazyEvaluator tests (10 tests)."""

    def test_create_lazy_evaluator(self):
        """Test 1251: Create lazy evaluator."""
        evaluator = LazyEvaluator()
        assert len(evaluator.pending_operations) == 0
        assert len(evaluator.evaluated_results) == 0

    def test_register_lazy_operation(self):
        """Test 1252: Register lazy operation."""
        evaluator = LazyEvaluator()
        evaluator.register_lazy('op1', lambda: 42)

        assert 'op1' in evaluator.pending_operations

    def test_evaluate_operation(self):
        """Test 1253: Evaluate lazy operation."""
        evaluator = LazyEvaluator()
        evaluator.register_lazy('op1', lambda: 42)

        result = evaluator.evaluate('op1')
        assert result == 42

    def test_evaluate_caches_result(self):
        """Test 1254: Result is cached after evaluation."""
        evaluator = LazyEvaluator()
        call_count = [0]

        def operation():
            call_count[0] += 1
            return 42

        evaluator.register_lazy('op1', operation)

        evaluator.evaluate('op1')
        evaluator.evaluate('op1')

        assert call_count[0] == 1

    def test_is_evaluated_false(self):
        """Test 1255: Not evaluated before call."""
        evaluator = LazyEvaluator()
        evaluator.register_lazy('op1', lambda: 42)

        assert evaluator.is_evaluated('op1') is False

    def test_is_evaluated_true(self):
        """Test 1256: Evaluated after call."""
        evaluator = LazyEvaluator()
        evaluator.register_lazy('op1', lambda: 42)

        evaluator.evaluate('op1')
        assert evaluator.is_evaluated('op1') is True

    def test_evaluate_unknown_raises(self):
        """Test 1257: Evaluate unknown operation raises."""
        evaluator = LazyEvaluator()

        with pytest.raises(ValueError, match='Unknown operation'):
            evaluator.evaluate('missing')

    def test_multiple_operations(self):
        """Test 1258: Multiple lazy operations."""
        evaluator = LazyEvaluator()
        evaluator.register_lazy('op1', lambda: 10)
        evaluator.register_lazy('op2', lambda: 20)

        assert evaluator.evaluate('op1') == 10
        assert evaluator.evaluate('op2') == 20

    def test_overwrite_operation(self):
        """Test 1259: Overwriting lazy operation."""
        evaluator = LazyEvaluator()
        evaluator.register_lazy('op1', lambda: 10)
        evaluator.register_lazy('op1', lambda: 20)

        result = evaluator.evaluate('op1')
        assert result == 20

    def test_complex_operation(self):
        """Test 1260: Complex lazy operation."""
        evaluator = LazyEvaluator()
        evaluator.register_lazy(
            'op1',
            lambda: {'key': [1, 2, 3], 'nested': True}
        )

        result = evaluator.evaluate('op1')
        assert result['key'] == [1, 2, 3]
        assert result['nested'] is True


# ════════════════════════════════════════════════════════════════════════════
# PERFORMANCE PROFILER TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPerformanceProfiler:
    """PerformanceProfiler tests (15 tests)."""

    def test_create_profiler(self):
        """Test 1261: Create performance profiler."""
        profiler = PerformanceProfiler()
        assert profiler.enabled is False

    def test_enable_profiler(self):
        """Test 1262: Enable profiler."""
        profiler = PerformanceProfiler()
        profiler.enable()
        assert profiler.enabled is True

    def test_disable_profiler(self):
        """Test 1263: Disable profiler."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.disable()
        assert profiler.enabled is False

    def test_record_timing_disabled(self):
        """Test 1264: Recording when disabled doesn't store."""
        profiler = PerformanceProfiler()
        profiler.record_timing('op1', 10.5)

        assert len(profiler.timings) == 0

    def test_record_timing_enabled(self):
        """Test 1265: Recording when enabled stores timing."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 10.5)

        assert 'op1' in profiler.timings
        assert profiler.timings['op1'] == [10.5]

    def test_multiple_timings(self):
        """Test 1266: Multiple timings for same operation."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 10.0)
        profiler.record_timing('op1', 20.0)

        assert len(profiler.timings['op1']) == 2

    def test_get_profile_count(self):
        """Test 1267: Profile count."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 10.0)
        profiler.record_timing('op1', 20.0)

        profile = profiler.get_profile()
        assert profile['op1']['count'] == 2

    def test_get_profile_mean(self):
        """Test 1268: Profile mean."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 10.0)
        profiler.record_timing('op1', 20.0)

        profile = profiler.get_profile()
        assert profile['op1']['mean_ms'] == 15.0

    def test_get_profile_total(self):
        """Test 1269: Profile total."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 10.0)
        profiler.record_timing('op1', 20.0)

        profile = profiler.get_profile()
        assert profile['op1']['total_ms'] == 30.0

    def test_profile_min_max(self):
        """Test 1270: Profile min and max."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 5.0)
        profiler.record_timing('op1', 10.0)
        profiler.record_timing('op1', 15.0)

        profile = profiler.get_profile()
        assert profile['op1']['min_ms'] == 5.0
        assert profile['op1']['max_ms'] == 15.0

    def test_profile_median(self):
        """Test 1271: Profile median."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 5.0)
        profiler.record_timing('op1', 10.0)
        profiler.record_timing('op1', 15.0)

        profile = profiler.get_profile()
        assert profile['op1']['median_ms'] == 10.0

    def test_reset_profiling(self):
        """Test 1272: Reset profiling data."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 10.0)

        profiler.reset()

        assert len(profiler.timings) == 0

    def test_multiple_operations(self):
        """Test 1273: Multiple operation timings."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 10.0)
        profiler.record_timing('op2', 20.0)

        profile = profiler.get_profile()
        assert 'op1' in profile
        assert 'op2' in profile

    def test_empty_profile(self):
        """Test 1274: Empty profile."""
        profiler = PerformanceProfiler()
        profile = profiler.get_profile()
        assert profile == {}

    def test_timings_preserved_after_disable(self):
        """Test 1275: Timings preserved after disable."""
        profiler = PerformanceProfiler()
        profiler.enable()
        profiler.record_timing('op1', 10.0)
        profiler.disable()

        profile = profiler.get_profile()
        assert profile['op1']['count'] == 1


# ════════════════════════════════════════════════════════════════════════════
# OPTIMIZATION MANAGER TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestOptimizationManager:
    """OptimizationManager tests (15 tests)."""

    def test_create_manager(self):
        """Test 1276: Create optimization manager."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        assert manager.adapter is adapter

    def test_manager_has_validation_cache(self):
        """Test 1277: Manager has validation cache."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        assert isinstance(manager.validation_cache, ValidationCache)

    def test_manager_has_predicate_cache(self):
        """Test 1278: Manager has predicate cache."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        assert isinstance(manager.predicate_cache, PredicateCache)

    def test_manager_has_fast_path(self):
        """Test 1279: Manager has fast path detector."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        assert isinstance(manager.fast_path_detector, FastPathDetector)

    def test_manager_has_lazy_evaluator(self):
        """Test 1280: Manager has lazy evaluator."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        assert isinstance(manager.lazy_evaluator, LazyEvaluator)

    def test_manager_has_profiler(self):
        """Test 1281: Manager has profiler."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        assert isinstance(manager.profiler, PerformanceProfiler)

    def test_enable_caching(self):
        """Test 1282: Enable caching."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        manager.enable_caching()
        assert manager.validation_cache.enabled is True

    def test_disable_caching(self):
        """Test 1283: Disable caching."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        manager.enable_caching()
        manager.disable_caching()
        assert manager.validation_cache.enabled is False

    def test_enable_profiling(self):
        """Test 1284: Enable profiling."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        manager.enable_profiling()
        assert manager.profiler.enabled is True

    def test_disable_profiling(self):
        """Test 1285: Disable profiling."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        manager.enable_profiling()
        manager.disable_profiling()
        assert manager.profiler.enabled is False

    def test_get_optimization_report(self):
        """Test 1286: Get optimization report."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        report = manager.get_optimization_report()
        assert 'validation_cache' in report
        assert 'predicate_cache' in report
        assert 'performance_profile' in report
        assert 'lazy_evaluation' in report

    def test_invalidate_caches(self):
        """Test 1287: Invalidate all caches."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)
        manager.validation_cache.put('f', 'c', [1], True)

        manager.invalidate_caches()

        assert len(manager.validation_cache.cache) == 0

    def test_reset_profiling(self):
        """Test 1288: Reset profiling."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)
        manager.enable_profiling()
        manager.profiler.record_timing('op1', 10.0)

        manager.reset_profiling()

        assert len(manager.profiler.timings) == 0

    def test_should_use_fast_path_unknown(self):
        """Test 1289: Fast path for unknown function."""
        adapter = PythonAdapterComplete()
        manager = OptimizationManager(adapter)

        # Unknown function has no graph → should skip but config check
        # comes first; adapter has config, graph is None → True
        result = manager.should_use_fast_path('unknown_func')
        assert result is True

    def test_should_use_fast_path_with_graph(self):
        """Test 1290: Fast path with mandatory graph."""
        adapter = PythonAdapterComplete()
        graph = ValidationGraph('func')
        node = ValidationNode('c1', 'test', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        adapter.validation_graphs['func'] = graph

        manager = OptimizationManager(adapter)

        assert manager.should_use_fast_path('func') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
