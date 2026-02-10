import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath('modules/module_02_verification_pipeline'))

from verification_pipeline import (
    CacheManager,
    PerformanceProfiler,
    verify_optimized,
    DependencyGraph,
    ParallelPipelineExecutor
)

def test_cache_manager():
    """Test cache manager functionality."""
    print("Testing CacheManager...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(tmpdir)
        
        # Test cache key computation
        key = cache.compute_cache_key({'file1': 'test.txt'})
        assert len(key) == 64  # SHA-256 hex
        print("  ✓ Cache key computation works")
        
        # Test stats
        stats = cache.get_stats()
        assert stats['total_entries'] == 0
        assert stats['total_hits'] == 0
        print("  ✓ Cache stats initialized correctly")
        
        # Test store and lookup
        inputs = {'input1': 'value1'}
        outputs = {'output1': 'path1'}
        cache.store('test_stage', '1.0.0', inputs, outputs)
        
        stats = cache.get_stats()
        assert stats['total_entries'] == 1
        print("  ✓ Cache store works")
        
        # Test invalidation
        cache.invalidate_stage('test_stage')
        stats = cache.get_stats()
        assert stats['total_entries'] == 0
        print("  ✓ Cache invalidation works")
        
        # Test clear all
        cache.store('test_stage', '1.0.0', inputs, outputs)
        cache.clear_all()
        stats = cache.get_stats()
        assert stats['total_entries'] == 0
        print("  ✓ Cache clear works")
    
    print("✓ CacheManager tests passed\n")

def test_performance_profiler():
    """Test performance profiler."""
    print("Testing PerformanceProfiler...")
    
    profiler = PerformanceProfiler()
    
    # Profile a simple function
    def test_func():
        import time
        time.sleep(0.1)
        return "done"
    
    result = profiler.profile_stage("test_stage", test_func)
    assert result == "done"
    assert "test_stage" in profiler.stage_profiles
    assert profiler.stage_profiles["test_stage"]["wall_time"] >= 0.1
    print("  ✓ Stage profiling works")
    
    # Generate report
    report = profiler.generate_report()
    assert "Performance Profile" in report
    assert "test_stage" in report
    print("  ✓ Report generation works")
    
    print("✓ PerformanceProfiler tests passed\n")

def test_dependency_graph():
    """Test dependency graph construction."""
    print("Testing DependencyGraph...")
    
    # Create mock stage classes
    class Stage1:
        STAGE_NAME = "stage1"
        REQUIRED_INPUTS = []
        PRODUCED_OUTPUTS = ["output1"]
    
    class Stage2:
        STAGE_NAME = "stage2"
        REQUIRED_INPUTS = ["output1"]
        PRODUCED_OUTPUTS = ["output2"]
    
    graph = DependencyGraph([Stage1, Stage2])
    
    assert graph.graph["stage1"] == set()
    assert graph.graph["stage2"] == {"stage1"}
    print("  ✓ Dependency graph construction works")
    
    print("✓ DependencyGraph tests passed\n")

def test_optimized_api():
        print("Testing verify_optimized API...")
    
        assert callable(verify_optimized)
    print("  ✓ verify_optimized() API available")
    
        try:
        verify_optimized("nonexistent.h", "nonexistent.dll", cache=False)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print("  ✓ Correctly caught missing input files")
    
    print("✓ Optimized API tests passed\n")

if __name__ == "__main__":
    test_cache_manager()
    test_performance_profiler()
    test_dependency_graph()
    test_optimized_api()
    
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
