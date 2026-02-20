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
# File Integrity Identifier: b413679138680351
# ==============================================================================

"""
Example 10: Performance Optimization

This example demonstrates performance optimization techniques:
- Enabling caching
- Profiling synthesis operations
- Performance monitoring

Expected runtime: < 2 seconds
Difficulty: Advanced
"""

import time
import sys
from pathlib import Path

# Add project root and modules to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "modules"))

from module_07_contract_synthesis import SynthesisEngine, SynthesisConfig
from module_07_contract_synthesis.performance import (
    SynthesisCache,
    PhaseProfiler,
    PerformanceMonitor
)
from module_05_ir_normalization.ir_serialization import IRSerializer


def example_caching():
    """Example: Enable caching for performance."""
    print("\n1. Caching for Performance")
    print("-" * 70)
    
    # Path to sample IR
    ir_file = Path(__file__).parent / "data" / "simple_interface.json"
    if not ir_file.exists():
        print("Sample data not found, skipping...")
        return
    
    serializer = IRSerializer()
    ir_unit = serializer.deserialize(ir_file.read_text())
    
    # Initialize cache
    cache = SynthesisCache(max_size=100)
    print(f"[OK] Cache initialized with max_size={cache.synthesis_cache.max_size}")
    
    # Note: Traditional SynthesisEngine in these prompts might not auto-use the cache 
    # unless we pass it or it's integrated. In this example, we show the API.
    
    fp = "sample_fingerprint_001"
    ver = "1.0.0"
    
    print("\nSimulating cache usage:")
    # First run (Miss)
    engine = SynthesisEngine(SynthesisConfig())
    result = engine.synthesize(ir_unit, "test")
    cache.put_synthesis_result(fp, ver, result)
    print("  [OK] Result stored in cache")
    
    # Second run (Hit)
    cached_result = cache.get_synthesis_result(fp, ver)
    if cached_result:
        print("  [OK] Result retrieved from cache")


def example_profiling():
    """Example: Profile synthesis to find bottlenecks."""
    print("\n2. Profiling Synthesis Operations")
    print("-" * 70)
    
    profiler = PhaseProfiler()
    engine = SynthesisEngine(SynthesisConfig())
    
    # Load IR
    ir_file = Path(__file__).parent / "data" / "simple_interface.json"
    serializer = IRSerializer()
    ir_unit = serializer.deserialize(ir_file.read_text())
    
    print("Running synthesis with profiling...")
    with profiler.profile_phase('total_synthesis'):
        result = engine.synthesize(ir_unit, "test")
    
    print("\nProfile report:")
    print(profiler.get_report())


def example_performance_monitoring():
    """Example: Monitor performance metrics."""
    print("\n3. Performance Monitoring")
    print("-" * 70)
    
    monitor = PerformanceMonitor()
    
    # Record some simulated synthesis operations
    print("Recording performance metrics...")
    monitor.record_synthesis(duration=0.15, clause_count=20, cache_hit=False)
    monitor.record_synthesis(duration=0.01, clause_count=20, cache_hit=True)
    monitor.record_synthesis(duration=0.12, clause_count=15, cache_hit=False)
    
    print("\nPerformance report:")
    print(monitor.get_report())


def main():
    """Run performance optimization examples."""
    print("=" * 70)
    print("Example 10: Performance Optimization")
    print("=" * 70)
    
    example_caching()
    example_profiling()
    example_performance_monitoring()
    
    print("\n" + "=" * 70)
    print("Performance optimization examples complete!")
    
    return 0


if __name__ == '__main__':
    exit(main())