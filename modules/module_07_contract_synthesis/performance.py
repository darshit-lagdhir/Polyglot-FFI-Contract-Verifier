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
# File Integrity Identifier: fcaf9a08e7babad5
# ==============================================================================

class LRUCache:
    """
    Least Recently Used (LRU) cache with size limit.
    
    Automatically evicts least recently used items when capacity reached.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if self.max_size <= 0:
            return None
            
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        
        self.misses += 1
        return None

    def put(self, key: str, value: Any):
        """
        Put value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if self.max_size <= 0:
            return
            
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                self.cache.popitem(last=False)
        
        self.cache[key] = value

    def clear(self):
        """Clear all cached items."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_hit_rate(self) -> float:
        """Get cache hit rate (0.0 to 1.0)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.get_hit_rate()
        }

class SynthesisCache:
    """
    Multi-level cache for synthesis operations.
    
    Caches:
    - Complete synthesis results
    - Intermediate analysis results
    - Per-rule execution results
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize synthesis cache.
        
        Args:
            max_size: Maximum cache size per level
        """
        self.synthesis_cache = LRUCache(max_size)
        self.analysis_cache = LRUCache(max_size * 2)
        self.rule_cache = LRUCache(max_size * 10)
        self.logger = logger

    def get_synthesis_result(self, ir_fingerprint: str, synthesis_version: str):
        """Get cached synthesis result."""
        cache_key = f"{ir_fingerprint}:{synthesis_version}"
        return self.synthesis_cache.get(cache_key)

    def put_synthesis_result(
        self,
        ir_fingerprint: str,
        synthesis_version: str,
        result: Any
    ):
        """Cache synthesis result."""
        cache_key = f"{ir_fingerprint}:{synthesis_version}"
        self.synthesis_cache.put(cache_key, result)
        self.logger.debug(f"Cached synthesis result: {cache_key}")

    def get_analysis_result(self, functions_fingerprint: str):
        """Get cached contextual analysis."""
        return self.analysis_cache.get(functions_fingerprint)

    def put_analysis_result(self, functions_fingerprint: str, analysis: Any):
        """Cache contextual analysis."""
        self.analysis_cache.put(functions_fingerprint, analysis)

    def get_rule_result(self, rule_id: str, entity_fingerprint: str):
        """Get cached rule execution result."""
        cache_key = f"{rule_id}:{entity_fingerprint}"
        return self.rule_cache.get(cache_key)

    def put_rule_result(
        self,
        rule_id: str,
        entity_fingerprint: str,
        result: Any
    ):
        """Cache rule execution result."""
        cache_key = f"{rule_id}:{entity_fingerprint}"
        self.rule_cache.put(cache_key, result)

    def clear_all(self):
        """Clear all cache levels."""
        self.synthesis_cache.clear()
        self.analysis_cache.clear()
        self.rule_cache.clear()

    def get_stats(self) -> Dict[str, Dict]:
        """Get statistics for all cache levels."""
        return {
            'synthesis': self.synthesis_cache.get_stats(),
            'analysis': self.analysis_cache.get_stats(),
            'rule': self.rule_cache.get_stats()
        }

# ============================================================================
# PROFILING TOOLS
# ============================================================================

@dataclass
class PhaseProfile:
    """Profile data for a synthesis phase."""
    phase_name: str
    duration: float
    call_count: int = 1

    @property
    def avg_duration(self) -> float:
        """Average duration per call."""
        return self.duration / self.call_count if self.call_count > 0 else 0.0

class PhaseProfiler:
    """
    Profile synthesis phases.
    
    Tracks time spent in each synthesis phase.
    """

    def __init__(self):
        self.phase_profiles: Dict[str, PhaseProfile] = {}
        self.current_phase: Optional[str] = None
        self.phase_start: float = 0.0

    @contextmanager
    def profile_phase(self, phase_name: str):
        """
        Context manager to profile a synthesis phase.
        
        Args:
            phase_name: Name of phase being profiled
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            if phase_name in self.phase_profiles:
                profile = self.phase_profiles[phase_name]
                profile.duration += duration
                profile.call_count += 1
            else:
                self.phase_profiles[phase_name] = PhaseProfile(
                    phase_name=phase_name,
                    duration=duration,
                    call_count=1
                )

    def get_report(self) -> str:
        """Generate profiling report."""
        if not self.phase_profiles:
            return "No profiling data available"
        
        total_time = sum(p.duration for p in self.phase_profiles.values())
        
        lines = []
        lines.append("Synthesis Phase Profile")
        lines.append("=" * 70)
        
        # Sort by duration (descending)
        sorted_profiles = sorted(
            self.phase_profiles.values(),
            key=lambda p: p.duration,
            reverse=True
        )
        
        for profile in sorted_profiles:
            percentage = (profile.duration / total_time * 100) if total_time > 0 else 0
            lines.append(
                f"{profile.phase_name:30s} "
                f"{profile.duration:8.3f}s "
                f"({percentage:5.1f}%) "
                f"calls={profile.call_count:4d}"
            )
        
        lines.append("=" * 70)
        lines.append(f"{'Total':30s} {total_time:8.3f}s (100.0%)")
        
        return "\n".join(lines)

    def clear(self):
        """Clear all profiling data."""
        self.phase_profiles.clear()

@dataclass
class RuleStats:
    """Statistics for rule execution."""
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0

    @property
    def avg_time(self) -> float:
        """Average execution time."""
        return self.total_time / self.count if self.count > 0 else 0.0

class RuleProfiler:
    """
    Profile individual synthesis rules.
    
    Tracks execution time and frequency for each rule.
    """

    def __init__(self):
        self.rule_stats: Dict[str, RuleStats] = defaultdict(RuleStats)

    def record_execution(self, rule_id: str, duration: float):
        """Record rule execution time."""
        stats = self.rule_stats[rule_id]
        stats.count += 1
        stats.total_time += duration
        stats.min_time = min(stats.min_time, duration)
        stats.max_time = max(stats.max_time, duration)

    def get_report(self) -> str:
        """Generate rule profiling report."""
        if not self.rule_stats:
            return "No rule profiling data available"
        
        lines = []
        lines.append("Rule Execution Profile")
        lines.append("=" * 90)
        lines.append(
            f"{'Rule ID':40s} {'Count':>6s} {'Avg (ms)':>10s} "
            f"{'Min (ms)':>10s} {'Max (ms)':>10s} {'Total (s)':>10s}"
        )
        lines.append("=" * 90)
        
        sorted_rules = sorted(
            self.rule_stats.items(),
            key=lambda x: x[1].total_time,
            reverse=True
        )
        
        for rule_id, stats in sorted_rules:
            avg_ms = stats.avg_time * 1000
            min_ms = stats.min_time * 1000
            max_ms = stats.max_time * 1000
            lines.append(
                f"{rule_id:40s} "
                f"{stats.count:6d} "
                f"{avg_ms:10.2f} "
                f"{min_ms:10.2f} "
                f"{max_ms:10.2f} "
                f"{stats.total_time:10.3f}"
            )
        
        return "\n".join(lines)

    def clear(self):
        """Clear all rule profiling data."""
        self.rule_stats.clear()

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics for synthesis operations."""
    synthesis_count: int = 0
    total_time: float = 0.0
    total_clauses: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def avg_time(self) -> float:
        return self.total_time / self.synthesis_count if self.synthesis_count > 0 else 0.0

    @property
    def avg_clauses(self) -> float:
        return self.total_clauses / self.synthesis_count if self.synthesis_count > 0 else 0.0

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

    @property
    def throughput(self) -> float:
        return self.synthesis_count / self.total_time if self.total_time > 0 else 0.0

class PerformanceMonitor:
    """Monitor synthesis performance in real-time."""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.logger = logger

    def record_synthesis(
        self,
        duration: float,
        clause_count: int,
        cache_hit: bool
    ):
        """Record synthesis operation metrics."""
        self.metrics.synthesis_count += 1
        self.metrics.total_time += duration
        self.metrics.total_clauses += clause_count
        
        if cache_hit:
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            'count': self.metrics.synthesis_count,
            'avg_time_ms': self.metrics.avg_time * 1000,
            'avg_clauses': self.metrics.avg_clauses,
            'cache_hit_rate': self.metrics.cache_hit_rate,
            'throughput': self.metrics.throughput
        }

    def get_report(self) -> str:
        """Generate performance report."""
        stats = self.get_stats()
        
        lines = []
        lines.append("Performance Metrics")
        lines.append("=" * 50)
        lines.append(f"Operations:        {stats['count']}")
        lines.append(f"Avg time:          {stats['avg_time_ms']:.2f} ms")
        lines.append(f"Avg clauses:       {stats['avg_clauses']:.1f}")
        lines.append(f"Cache hit rate:    {stats['cache_hit_rate']:.1%}")
        lines.append(f"Throughput:        {stats['throughput']:.2f} ops/s")
        
        return "\n".join(lines)

    def clear(self):
        """Clear all metrics."""
        self.metrics = PerformanceMetrics()

# ============================================================================
# BENCHMARKING
# ============================================================================

@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    scenario: str
    iterations: int
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    expected_time_ms: float
    passed: bool

    def get_speedup(self, baseline_time_ms: float) -> float:
        """Calculate speedup vs baseline."""
        if self.avg_time_ms == 0:
            return 0.0
        return baseline_time_ms / self.avg_time_ms

class SynthesisBenchmark:
    """Benchmark synthesis performance."""

    SCENARIOS = {
        'tiny': {
            'description': 'Tiny interface (5 functions, 2 types)',
            'functions': 5,
            'types': 2,
            'expected_time_ms': 50
        },
        'small': {
            'description': 'Small interface (20 functions, 10 types)',
            'functions': 20,
            'types': 10,
            'expected_time_ms': 100
        },
        'medium': {
            'description': 'Medium interface (100 functions, 50 types)',
            'functions': 100,
            'types': 50,
            'expected_time_ms': 500
        },
        'large': {
            'description': 'Large interface (500 functions, 200 types)',
            'functions': 500,
            'types': 200,
            'expected_time_ms': 2000
        }
    }

    def __init__(self, engine):
        """
        Initialize benchmark.
        
        Args:
            engine: SynthesisEngine instance to benchmark
        """
        self.engine = engine
        self.logger = logger

    def run_benchmark(
        self,
        scenario_name: str,
        iterations: int = 10
    ) -> BenchmarkResult:
        """Run benchmark scenario."""
        if scenario_name not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.SCENARIOS[scenario_name]
        self.logger.info(f"Running benchmark: {scenario['description']}")
        
        # Generate test IR
        ir_unit = self._generate_test_ir(scenario)
        
        # Run iterations
        times = []
        for i in range(iterations):
            start = time.time()
            # Note: synthesis_engine expects (ir_unit, target_interface_id)
            result = self.engine.synthesize(ir_unit, f"bench_{i}")
            duration = (time.time() - start) * 1000  # ms
            
            if not result.success:
                raise RuntimeError(f"Synthesis failed in benchmark iteration {i}")
            
            times.append(duration)
        
        # Statistics
        import statistics
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        
        expected = scenario['expected_time_ms']
        passed = avg_time < expected
        
        return BenchmarkResult(
            scenario=scenario_name,
            iterations=iterations,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            std_dev_ms=std_dev,
            expected_time_ms=expected,
            passed=passed
        )

    def _generate_test_ir(self, scenario):
        """Generate test IR for scenario."""
        from module_05_ir_normalization.ir_entities import (
            InterfaceUnit, StructureType, FunctionSymbol, ReturnEntity, ScalarKind,
            Endianness, CallingConvention, ReturnMechanism
        )
        
        # Create unit
        ir_unit = InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=Endianness.LITTLE,
            abi_mode="sysv",
            compiler_family="gcc",
            compiler_version="10.0"
        )
        ir_unit.entity_id = "benchmark"
        
        # Generate types
        for i in range(scenario['types']):
            struct = StructureType(
                structure_name=f"struct Type{i}",
                size_bytes=16,
                alignment_bytes=8,
                is_packed=False
            )
            ir_unit.types.append(struct)
        
        # Generate functions
        for i in range(scenario['functions']):
            ret_entity = ReturnEntity(
                type_reference="int32_t",
                return_mechanism=ReturnMechanism.DIRECT
            )
            
            # Simple scalar parameters
            params = []
            
            func = FunctionSymbol(
                linkage_name=f"function_{i}",
                source_name=f"function_{i}",
                calling_convention=CallingConvention.CDECL,
                return_entity=ret_entity,
                parameters=params
            )
            ir_unit.symbols.append(func)
        
        return ir_unit

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'LRUCache',
    'SynthesisCache',
    'PhaseProfiler',
    'PhaseProfile',
    'RuleProfiler',
    'RuleStats',
    'PerformanceMonitor',
    'PerformanceMetrics',
    'SynthesisBenchmark',
    'BenchmarkResult',
]