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
# File Integrity Identifier: 8ba9a4b1b3a0ca4f
# ==============================================================================

class PerformanceProfiler:
    """Profiles pipeline performance."""

    def __init__(self, enabled: bool = False) -> None:
        self.timings: Dict[str, float] = {}
        self.call_counts: Dict[str, int] = {}
        self.enabled = enabled
        self.stack: List[tuple] = []

    @property
    def stage_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Compatibility property for tests."""
        return {
            name: {
                "wall_time": duration,
                "call_count": self.call_counts.get(name, 1),
            }
            for name, duration in self.timings.items()
        }

    def generate_report(self) -> str:
        """Generate performance report string."""
        lines = ["Performance Profile", "=" * 40]
        for name, duration in self.timings.items():
            count = self.call_counts.get(name, 1)
            lines.append(f"{name}: {duration:.4f}s (calls: {count})")
        return "\n".join(lines)

    def enable(self) -> None:
        """Enable profiling."""
        self.enabled = True

    def disable(self) -> None:
        """Disable profiling."""
        self.enabled = False

    def profile_stage(self, name: str, func, *args, **kwargs) -> Any:
        """
        Profile a function execution as a stage.
        
        Args:
            name: Stage name
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func execution
        """
        with self.profile(name):
            return func(*args, **kwargs)

    @contextmanager
    def profile(self, name: str) -> Iterator[None]:
        """
        Profile a code block.

        Usage:
            with profiler.profile("operation_name"):
                # code to profile
        """
        if not self.enabled:
            yield
            return

        start = time.perf_counter()
        self.stack.append((name, start))

        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.stack.pop()

            if name in self.timings:
                self.timings[name] += duration
                self.call_counts[name] += 1
            else:
                self.timings[name] = duration
                self.call_counts[name] = 1

    def record(self, name: str, duration: float):
        """Manually record timing."""
        if not self.enabled:
            return

        if name in self.timings:
            self.timings[name] += duration
            self.call_counts[name] += 1
        else:
            self.timings[name] = duration
            self.call_counts[name] = 1

    def report(self) -> str:
        """Generate profiling report."""
        if not self.enabled:
            return "Profiling not enabled"

        lines = ["Performance Profile", "=" * 80]

        if not self.timings:
            return "No profiling data collected"

        sorted_timings = sorted(self.timings.items(), key=lambda x: x[1], reverse=True)

        total_time = sum(self.timings.values())

        lines.append(f"\nTotal Time: {total_time:.3f}s\n")
        lines.append(f"{'Operation':<40} {'Time':<12} {'Calls':<10} {'Avg':<12} {'%':<8}")
        lines.append("-" * 80)

        for name, duration in sorted_timings[:20]:  # Top 20
            calls = self.call_counts[name]
            avg = duration / calls if calls > 0 else 0
            pct = (duration / total_time) * 100 if total_time > 0 else 0

            lines.append(f"{name:<40} {duration:>10.3f}s {calls:>8}  {avg:>10.3f}s {pct:>6.1f}%")

        if len(sorted_timings) > 20:
            lines.append(f"\n... and {len(sorted_timings) - 20} more operations")

        return "\n".join(lines)

    def reset(self):
        """Reset profiling data."""
        self.timings.clear()
        self.call_counts.clear()
        self.stack.clear()


# ============================================================================
# OPTIMIZED TYPE DEDUPLICATOR
# ============================================================================


class OptimizedTypeDeduplicator:
    """
    Type deduplicator with performance optimizations.

    Improvements:
        - Lightweight cache keys (avoid expensive hash computation)
    - Pre-computed hashes stored
    - Fast path for common types
    """

    def __init__(self) -> None:
        self.type_cache: Dict[str, str] = {}  # fast_key -> entity_id
        self.hash_cache: Dict[str, str] = {}  # fast_key -> struct_hash

    def get_or_create_type_id(self, type_data: Dict[str, Any]) -> str:
        """Get entity ID with optimized lookup."""
        # Fast cache key (lighter than full hash)
        cache_key = self._make_fast_cache_key(type_data)

        if cache_key in self.type_cache:
            return self.type_cache[cache_key]

        # Compute structural hash only for new types
        struct_hash = self._compute_structural_hash(type_data)

        # Generate entity ID
        # Important: In a real system we'd determine the correct EntityKind
        # For optimization purposes, we use a generic TYPE_SYMBOL or similar if
        # appropriate,
        entity_id = IREntity.generate_id(EntityKind.TYPE_SYMBOL, struct_hash)

        # Cache both keys
        self.type_cache[cache_key] = entity_id
        self.hash_cache[cache_key] = struct_hash

        return entity_id

    def _make_fast_cache_key(self, type_data: Dict[str, Any]) -> str:
        """Create lightweight cache key."""
        # Use tuple of key properties (fast, hashable)
        kind = type_data.get("kind", "")
        size = type_data.get("size", 0)
        name = type_data.get("name", "")

        # Build key recursively for nested types
        if kind == "pointer":
            pointee_key = self._make_fast_cache_key(type_data.get("pointee", {}))
            return f"ptr:{pointee_key}"
        elif kind == "array":
            element_key = self._make_fast_cache_key(type_data.get("element_type", {}))
            count = type_data.get("element_count", "incomplete")
            return f"arr:{element_key}:{count}"
        elif kind == "scalar":
            signed = type_data.get("is_signed", False)
            return f"scalar:{name}:{size}:{signed}"
        else:
            return f"{kind}:{name}:{size}"

    def _compute_structural_hash(self, type_data: Dict[str, Any]) -> str:
        """Compute structural hash (expensive, only for new types)."""
        # Normalize for hashing
        normalized = self._normalize_for_hash(type_data)
        type_str = json.dumps(normalized, sort_keys=True)

        return hashlib.sha256(type_str.encode()).hexdigest()[:16]

    def _normalize_for_hash(self, type_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize type data for consistent hashing."""
        normalized = {}

        # Include only structural properties
        for key in ["kind", "size", "alignment"]:
            if key in type_data:
                normalized[key] = type_data[key]

        # Handle nested types
        if "pointee" in type_data:
            normalized["pointee"] = self._normalize_for_hash(type_data["pointee"])

        if "element_type" in type_data:
            normalized["element_type"] = self._normalize_for_hash(type_data["element_type"])

        if "is_signed" in type_data:
            normalized["is_signed"] = type_data["is_signed"]

        return normalized


# ============================================================================
# OPTIMIZED PADDING COMPUTATION
# ============================================================================


class OptimizedPaddingComputer:
    """Optimized structure padding computation."""

    def compute_padding(
        self, fields_data: List[Dict[str, Any]], total_size: int
    ) -> List[PaddingEntity]:
        """
        Compute padding with optimizations.

        Optimizations:
            - Assumes pre-sorted fields (common case)
        - Vectorized computation with numpy (if available)
        - Fast path for no-padding case
        """
        if not fields_data:
            if total_size > 0:
                return [
                    PaddingEntity(byte_offset=0, size_bytes=total_size, reason="empty structure")
                ]
            return []

        # Fast path: check if padding needed at all
        if self._has_no_padding(fields_data, total_size):
            return []

        # Use vectorized if available
        if HAS_NUMPY and len(fields_data) > 10:
            return self._compute_padding_vectorized(fields_data, total_size)
        return self._compute_padding_sequential(fields_data, total_size)

    def _has_no_padding(self, fields_data: List[Dict[str, Any]], total_size: int) -> bool:
        """Quick check if structure has no padding."""
        expected_offset = 0

        for field in fields_data:
            if field.get("offset", 0) != expected_offset:
                return False
            f_size = field.get("type", {}).get("size", 0)
            expected_offset += f_size

        return expected_offset == total_size

    def _compute_padding_sequential(
        self, fields_data: List[Dict[str, Any]], total_size: int
    ) -> List[PaddingEntity]:
        """Sequential padding computation (fallback)."""
        padding_regions = []
        current_offset = 0

        # Ensure sorted
        sorted_fields = sorted(fields_data, key=lambda f: f.get("offset", 0))

        for field in sorted_fields:
            field_offset = field.get("offset", 0)

            # Gap before this field
            if field_offset > current_offset:
                gap_size = field_offset - current_offset
                padding_regions.append(
                    PaddingEntity(
                        byte_offset=current_offset, size_bytes=gap_size, reason="field alignment"
                    )
                )

            field_size = field.get("type", {}).get("size", 0)
            current_offset = field_offset + field_size

        if total_size > current_offset:
            trailing_size = total_size - current_offset
            padding_regions.append(
                PaddingEntity(
                    byte_offset=current_offset, size_bytes=trailing_size, reason="structure end"
                )
            )

        return padding_regions

    def _compute_padding_vectorized(
        self, fields_data: List[Dict[str, Any]], total_size: int
    ) -> List[PaddingEntity]:
        """Vectorized padding computation using numpy."""
        # Sort fields explicitly for vectorized logic
        sorted_fields = sorted(fields_data, key=lambda f: f.get("offset", 0))

        offsets = np.array([f.get("offset", 0) for f in sorted_fields])
        sizes = np.array([f.get("type", {}).get("size", 0) for f in sorted_fields])

        # Compute field end positions
        field_ends = offsets + sizes

        # Compute gaps
        # Gaps are between end of field i and start of field i+1
        next_offsets = np.append(offsets[1:], total_size)
        gaps = next_offsets - field_ends

        # Create padding entities for non-zero gaps
        padding_regions = []
        for i, gap_size in enumerate(gaps):
            if gap_size > 0:
                reason = "structure end" if i == len(gaps) - 1 else "field alignment"
                padding_regions.append(
                    PaddingEntity(
                        byte_offset=int(field_ends[i]), size_bytes=int(gap_size), reason=reason
                    )
                )

        # Don't forget potential padding at the very beginning (though
        # triple-splitting usually handles this)
        if len(offsets) > 0 and offsets[0] > 0:
            padding_regions.insert(
                0,
                PaddingEntity(
                    byte_offset=0, size_bytes=int(offsets[0]), reason="structural offset"
                ),
            )

        return padding_regions


# ============================================================================
# BENCHMARK SUITE
# ============================================================================


@dataclass
class BenchmarkResult:
    """Benchmark measurement result."""

    name: str
    duration: float
    throughput: float
    memory_mb: float
    success: bool = True
    error: Optional[str] = None

    def __str__(self):
        if not self.success:
            return f"{self.name}: FAILED - {self.error}"

        return f"{self.name}: {self.duration:.3f}s ({self.throughput:.0f} entities/s, {self.memory_mb:.1f} MB)"


class BenchmarkSuite:
    """Performance benchmark suite."""

    def __init__(self) -> None:
        self.results: List[BenchmarkResult] = []

    def run_all(self) -> List[BenchmarkResult]:
        """Run all benchmarks."""
        self.results = []

        print("Running Performance Benchmarks...")
        print("=" * 80)

        self.results.append(self.bench_type_deduplication())
        self.results.append(self.bench_padding_computation())
        self.results.append(self.bench_reference_validation())

        print("\nBenchmark Results:")
        print("-" * 80)
        for result in self.results:
            print(result)

        return self.results

    def bench_type_deduplication(self) -> BenchmarkResult:
        """Benchmark type deduplication performance."""
        dedup = OptimizedTypeDeduplicator()

        # Generate test data
        num_types = 1000
        type_data_list = [
            {"kind": "scalar", "name": f"type_{i}", "size": 4, "is_signed": True}
            for i in range(num_types)
        ]

        start = time.perf_counter()

        for type_data in type_data_list:
            dedup.get_or_create_type_id(type_data)

        duration = time.perf_counter() - start
        throughput = num_types / duration if duration > 0 else float("inf")

        return BenchmarkResult(
            name="Type Deduplication (1000 types)",
            duration=duration,
            throughput=throughput,
            memory_mb=0.0,
        )

    def bench_padding_computation(self) -> BenchmarkResult:
        """Benchmark padding computation performance."""
        computer = OptimizedPaddingComputer()

        # Generate structure with many fields
        num_fields = 100
        fields_data = [
            {"name": f"field_{i}", "offset": i * 8, "type": {"size": 4, "alignment": 4}}
            for i in range(num_fields)
        ]

        total_size = num_fields * 8

        start = time.perf_counter()

        # Compute padding multiple times
        iterations = 1000
        for _ in range(iterations):
            computer.compute_padding(fields_data, total_size)

        duration = time.perf_counter() - start
        throughput = (num_fields * iterations) / duration if duration > 0 else float("inf")

        return BenchmarkResult(
            name="Padding Computation (100 fields × 1000 iter)",
            duration=duration,
            throughput=throughput,
            memory_mb=0.0,
        )

    def bench_reference_validation(self) -> BenchmarkResult:
        """Benchmark reference validation performance."""
        # Create mock type registry
        num_types = 5000
        valid_ids = {f"type_{i}" for i in range(num_types)}

        # Create references to validate
        num_references = 10000
        references = [f"type_{i % num_types}" for i in range(num_references)]

        start = time.perf_counter()

        # Validate references using set membership
        invalid_count = sum(1 for ref in references if ref not in valid_ids)

        duration = time.perf_counter() - start
        throughput = num_references / duration if duration > 0 else float("inf")

        return BenchmarkResult(
            name="Reference Validation (10000 refs)",
            duration=duration,
            throughput=throughput,
            memory_mb=0.0,
        )


# ============================================================================
# GLOBAL PROFILER INSTANCE
# ============================================================================


# Global profiler for easy access
_global_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance."""
    return _global_profiler


__all__ = [
    "PerformanceProfiler",
    "OptimizedTypeDeduplicator",
    "OptimizedPaddingComputer",
    "BenchmarkSuite",
    "BenchmarkResult",
    "get_profiler",
    "HAS_NUMPY",
]