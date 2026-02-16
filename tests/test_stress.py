"""
Module 07: Stress Testing Suite (Prompt 12/15)

Comprehensive stress tests for synthesis engine.
"""

import pytest
import time
import statistics
import random
import threading
import sys
from pathlib import Path

# Add modules directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "modules"))

from module_07_contract_synthesis import SynthesisEngine, SynthesisConfig
from module_05_ir_normalization.ir_entities import (
    InterfaceUnit, ScalarType, PointerType, StructureType, 
    FunctionSymbol, ParameterEntity, FieldEntity, Endianness, 
    EntityKind, ScalarKind, CallingConvention
)


# ============================================================================
# STRESS TEST HELPERS
# ============================================================================

def generate_large_ir(num_functions=1000, num_types=500):
    """Generate large IR for stress testing."""
    types = []
    # Create a base int32_t type
    int32 = ScalarType(
        scalar_kind=ScalarKind.SIGNED_INTEGER,
        bit_width=32,
        size_bytes=4,
        alignment_bytes=4,
        is_signed=True
    )
    types.append(int32)

    for i in range(num_types):
        struct_type = StructureType(
            structure_name=f"Type{i}",
            size_bytes=16,
            alignment_bytes=8
        )
        for j in range(4):
            field = FieldEntity(
                field_index=j,
                field_name=f"field{j}",
                type_reference=int32.entity_id,
                byte_offset=j * 4,
                size_bytes=4,
                alignment_bytes=4
            )
            struct_type.add_field(field)
        types.append(struct_type)
    
    symbols = []
    for i in range(num_functions):
        params = [
            ParameterEntity(
                parameter_index=j,
                parameter_name=f"param{j}",
                type_reference=int32.entity_id
            )
            for j in range(5)
        ]
        
        fn = FunctionSymbol(
            linkage_name=f"function_{i}",
            source_name=f"function_{i}",
            calling_convention=CallingConvention.CDECL,
            parameters=params
        )
        symbols.append(fn)
    
    return InterfaceUnit(
        target_architecture="x86_64",
        operating_system="linux",
        pointer_width=64,
        endianness=Endianness.LITTLE,
        abi_mode="sysv",
        compiler_family="gcc",
        compiler_version="11.0",
        symbols=symbols,
        types=types
    )


def generate_deeply_nested_type(depth=20):
    """Generate deeply nested type structure."""
    current_type = ScalarType(
        scalar_kind=ScalarKind.SIGNED_INTEGER,
        bit_width=32,
        size_bytes=4,
        alignment_bytes=4,
        is_signed=True
    )
    
    all_types = [current_type]

    for i in range(depth):
        struct_type = StructureType(
            structure_name=f"nested_{i}",
            size_bytes=16,
            alignment_bytes=8
        )
        field = FieldEntity(
            field_index=0,
            field_name="inner",
            type_reference=current_type.entity_id,
            byte_offset=0,
            size_bytes=current_type.size_bytes,
            alignment_bytes=current_type.alignment_bytes
        )
        struct_type.add_field(field)
        current_type = struct_type
        all_types.append(current_type)
    
    return current_type, all_types


# ============================================================================
# EXTREME SCALE TESTS
# ============================================================================

class TestExtremeScale:
    """Test synthesis with extreme inputs."""
    
    @pytest.mark.slow
    def test_massive_interface_1000_functions(self):
        """Test synthesis with 1000 functions."""
        import tracemalloc
        
        ir_unit = generate_large_ir(num_functions=1000, num_types=100)
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        
        tracemalloc.start()
        start = time.time()
        
        result = engine.synthesize(ir_unit, 'massive_1000')
        
        duration = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Validate
        assert result.success
        assert result.clauses_generated > 0
        
        # Performance targets
        assert duration < 60.0, f"Took {duration:.2f}s (target: < 60s)"
        assert peak < 2_000_000_000, f"Used {peak/1e9:.2f}GB (target: < 2GB)"
        
        print(f"\n1000 functions: {duration:.2f}s, peak memory: {peak/1e6:.1f}MB")
    
    @pytest.mark.slow
    def test_massive_interface_500_types(self):
        """Test synthesis with 500 complex types."""
        ir_unit = generate_large_ir(num_functions=100, num_types=500)
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        
        start = time.time()
        result = engine.synthesize(ir_unit, 'massive_types')
        duration = time.time() - start
        
        assert result.success
        assert duration < 30.0
        
        print(f"\n500 types: {duration:.2f}s")
    
    def test_deeply_nested_types_20_levels(self):
        """Test synthesis with deeply nested types."""
        nested_type, all_types = generate_deeply_nested_type(depth=20)
        
        ir_unit = InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=Endianness.LITTLE,
            abi_mode="sysv",
            compiler_family="gcc",
            compiler_version="11.0",
            types=all_types,
            symbols=[]
        )
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        
        # Should not stack overflow
        result = engine.synthesize(ir_unit, 'deep_20')
        
        assert result.success
    
    def test_many_pointer_parameters(self):
        """Test function with 100 pointer parameters."""
        # Define void* type
        void_ptr = PointerType(
            pointer_depth=1,
            target_type_reference="void",
            pointer_width=64,
            size_bytes=8,
            alignment_bytes=8
        )

        params = [
            ParameterEntity(
                parameter_index=i,
                parameter_name=f"ptr_{i}",
                type_reference=void_ptr.entity_id
            )
            for i in range(100)
        ]
        
        func = FunctionSymbol(
            linkage_name="pointer_heavy",
            source_name="pointer_heavy",
            calling_convention=CallingConvention.CDECL,
            parameters=params
        )
        
        ir_unit = InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=Endianness.LITTLE,
            abi_mode="sysv",
            compiler_family="gcc",
            compiler_version="11.0",
            types=[void_ptr],
            symbols=[func]
        )
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        
        result = engine.synthesize(ir_unit, 'pointers')
        
        assert result.success
        # Should generate nullability clause for each pointer
        assert result.nullability_clauses >= 100


# ============================================================================
# CONCURRENT ACCESS TESTS
# ============================================================================

class TestConcurrentAccess:
    """Test concurrent synthesis operations."""
    
    def test_concurrent_synthesis_10_threads(self):
        """Test 10 concurrent synthesis operations."""
        results = []
        errors = []
        
        def synthesize_thread(thread_id):
            try:
                # Each thread gets own engine
                config = SynthesisConfig()
                engine = SynthesisEngine(config)
                
                ir_unit = generate_large_ir(num_functions=50, num_types=25)
                result = engine.synthesize(ir_unit, f'thread_{thread_id}')
                
                results.append(result)
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create and start threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=synthesize_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Validate
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(r.success for r in results)


# ============================================================================
# LOAD TESTING
# ============================================================================

class TestLoadHandling:
    """Test sustained load handling."""
    
    @pytest.mark.slow
    def test_sustained_load_60_seconds(self):
        """Test sustained synthesis operations for 60 seconds."""
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        
        # Prepare sample IRs
        samples = [
            generate_large_ir(num_functions=50, num_types=25)
            for _ in range(10)
        ]
        
        start_time = time.time()
        end_time = start_time + 60
        
        operations = 0
        successes = 0
        failures = 0
        response_times = []
        
        while time.time() < end_time:
            ir_unit = random.choice(samples)
            
            op_start = time.time()
            result = engine.synthesize(ir_unit, f'load_{operations}')
            op_duration = time.time() - op_start
            
            operations += 1
            response_times.append(op_duration)
            
            if result.success:
                successes += 1
            else:
                failures += 1
        
        if operations == 0:
            pytest.skip("No operations completed")

        total_duration = time.time() - start_time
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        throughput = operations / total_duration
        
        print(f"\nLoad Test Results (60s):")
        print(f"  Operations: {operations}")
        print(f"  Success rate: {successes/operations:.1%}")
        print(f"  Avg response: {avg_time:.3f}s")
        print(f"  Median response: {median_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} ops/s")
        
        # Validate
        assert successes / operations > 0.95  # 95%+ success rate
        assert avg_time < 2.0  # Avg response < 2s


# ============================================================================
# MEMORY LEAK DETECTION
# ============================================================================

class TestMemoryLeaks:
    """Test for memory leaks."""
    
    def test_repeated_synthesis_no_leak(self):
        """Test repeated synthesis doesn't leak memory."""
        import tracemalloc
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        
        ir_unit = generate_large_ir(num_functions=100, num_types=50)
        
        # Warm up
        for _ in range(5):
            engine.synthesize(ir_unit, 'warmup')
        
        # Measure baseline
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        
        # Run many iterations
        for i in range(100):
            result = engine.synthesize(ir_unit, f'iter_{i}')
            assert result.success
        
        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # Compare snapshots
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # Check for significant growth
        total_growth = sum(stat.size_diff for stat in top_stats)
        
        print(f"\nMemory growth after 100 iterations: {total_growth/1e6:.2f}MB")
        
        # Allow some growth, but not excessive
        assert total_growth < 100_000_000  # < 100MB growth


# ============================================================================
# PATHOLOGICAL PATTERN TESTS
# ============================================================================

class TestPathologicalPatterns:
    """Test with unusual/pathological patterns."""
    
    def test_all_functions_identical_signature(self):
        """Test when all functions have identical signatures."""
        int32 = ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, size_bytes=4, alignment_bytes=4, is_signed=True)
        sizet = ScalarType(scalar_kind=ScalarKind.UNSIGNED_INTEGER, bit_width=64, size_bytes=8, alignment_bytes=8, is_signed=False)
        voidptr = PointerType(pointer_depth=1, target_type_reference="void", pointer_width=64, size_bytes=8, alignment_bytes=8)

        # 100 functions with same signature
        functions = []
        for i in range(100):
            fn = FunctionSymbol(
                linkage_name=f"func_{i}",
                source_name=f"func_{i}",
                calling_convention=CallingConvention.CDECL,
                parameters=[
                    ParameterEntity(parameter_index=0, parameter_name="buffer", type_reference=voidptr.entity_id),
                    ParameterEntity(parameter_index=1, parameter_name="length", type_reference=sizet.entity_id)
                ],
                return_entity=None
            )
            functions.append(fn)
        
        ir_unit = InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=Endianness.LITTLE,
            abi_mode="sysv",
            compiler_family="gcc",
            compiler_version="11.0",
            types=[int32, sizet, voidptr],
            symbols=functions
        )
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        
        result = engine.synthesize(ir_unit, 'identical')
        
        assert result.success
        # Should detect strong pattern
        analysis = result.metadata.get('contextual_analysis', {})
        score = analysis.get('coherence_score', 0) if isinstance(analysis, dict) else getattr(analysis, 'coherence_score', 0)
        assert score > 0.95
    
    def test_no_patterns_random_signatures(self):
        """Test when functions have completely random signatures."""
        int32 = ScalarType(scalar_kind=ScalarKind.SIGNED_INTEGER, bit_width=32, size_bytes=4, alignment_bytes=4, is_signed=True)
        float32 = ScalarType(scalar_kind=ScalarKind.FLOATING_POINT, bit_width=32, size_bytes=4, alignment_bytes=4, is_signed=True)
        double64 = ScalarType(scalar_kind=ScalarKind.FLOATING_POINT, bit_width=64, size_bytes=8, alignment_bytes=8, is_signed=True)
        voidptr = PointerType(pointer_depth=1, target_type_reference="void", pointer_width=64, size_bytes=8, alignment_bytes=8)
        
        types = [int32, float32, double64, voidptr]
        type_ids = [t.entity_id for t in types]

        functions = []
        for i in range(50):
            num_params = random.randint(0, 10)
            params = [
                ParameterEntity(
                    parameter_index=j,
                    parameter_name=f"param_{j}",
                    type_reference=random.choice(type_ids)
                )
                for j in range(num_params)
            ]
            
            fn = FunctionSymbol(
                linkage_name=f"random_{i}",
                source_name=f"random_{i}",
                calling_convention=CallingConvention.CDECL,
                parameters=params
            )
            functions.append(fn)
        
        ir_unit = InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=Endianness.LITTLE,
            abi_mode="sysv",
            compiler_family="gcc",
            compiler_version="11.0",
            types=types,
            symbols=functions
        )
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        
        result = engine.synthesize(ir_unit, 'random')
        
        assert result.success


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
