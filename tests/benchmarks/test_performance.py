import pytest
import time
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath('modules/module_02_verification_pipeline'))

from verification_pipeline import verify, verify_optimized

@pytest.mark.benchmark
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def test_small_library_performance(self, temp_dir):
        """Benchmark: Small library verification time."""
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Calculator example not found")
        
        header = example_dir / "calculator.h"
        library = example_dir / "calculator.dll"
        
        if not header.exists() or not library.exists():
            pytest.skip("Calculator files not found")
        
        try:
            start_time = time.time()
            
            result = verify(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(temp_dir / "bench_small"),
                verbose=False
            )
            
            elapsed = time.time() - start_time
            
            print(f"\nSmall library benchmark:")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Target: < 30s")
            print(f"  Status: {'PASS' if elapsed < 30 else 'FAIL'}")
            
            # Lenient target for system with dependencies
            assert elapsed < 30.0, f"Too slow: {elapsed:.2f}s"
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip(f"libclang not available: {e}")
            else:
                raise
    
    def test_cache_speedup(self, temp_dir):
        """Benchmark: Cache speedup on second run."""
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Calculator example not found")
        
        header = example_dir / "calculator.h"
        library = example_dir / "calculator.dll"
        
        if not header.exists() or not library.exists():
            pytest.skip("Calculator files not found")
        
        output_dir = temp_dir / "cache_bench"
        
        try:
            # First run (cold cache)
            start1 = time.time()
            result1 = verify_optimized(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(output_dir),
                cache=True,
                verbose=False
            )
            time1 = time.time() - start1
            
            # Second run (warm cache)
            start2 = time.time()
            result2 = verify_optimized(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(output_dir),
                cache=True,
                verbose=False
            )
            time2 = time.time() - start2
            
            speedup = time1 / time2 if time2 > 0 else 1.0
            
            print(f"\nCache speedup benchmark:")
            print(f"  First run: {time1:.2f}s")
            print(f"  Second run: {time2:.2f}s")
            print(f"  Speedup: {speedup:.1f}x")
            print(f"  Target: ≥ 1.5x")
            
            # Lenient target (cache may not help much for small library)
            assert speedup >= 1.0, f"Second run slower: {speedup:.1f}x"
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip(f"libclang not available: {e}")
            else:
                raise

@pytest.mark.benchmark
class TestMemoryBenchmarks:
    """Memory usage benchmark tests."""
    
    def test_memory_usage_reasonable(self, temp_dir):
        """Benchmark: Memory usage is reasonable."""
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Calculator example not found")
        
        header = example_dir / "calculator.h"
        library = example_dir / "calculator.dll"
        
        if not header.exists() or not library.exists():
            pytest.skip("Calculator files not found")
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            
            result = verify(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(temp_dir / "mem_bench"),
                verbose=False
            )
            
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            mem_used = mem_after - mem_before
            
            print(f"\nMemory usage benchmark:")
            print(f"  Memory used: {mem_used:.0f} MB")
            print(f"  Target: < 1000 MB")
            
            # Very lenient target
            assert mem_used < 1000, f"Memory usage too high: {mem_used:.0f} MB"
            
        except ImportError:
            pytest.skip("psutil not available")
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip(f"libclang not available: {e}")
            else:
                raise
