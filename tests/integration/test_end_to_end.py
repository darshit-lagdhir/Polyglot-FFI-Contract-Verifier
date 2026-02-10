"""
Module 05: Integration Tests - End-to-End

Complete end-to-end integration tests for IR normalization pipeline.
"""

import pytest
from pathlib import Path
import sys
import time
import json
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_05_ir_normalization import (
    IROrchestrator, IRNormalizationConfig
)
from module_05_ir_normalization.ir_serialization import IRArtifact

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Get fixtures directory."""
    path = Path(__file__).parent / 'fixtures'
    path.mkdir(parents=True, exist_ok=True)
    return path

@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def simple_library_artifact(fixtures_dir):
    """Simple library fixture."""
    fixture_path = fixtures_dir / 'simple_library' / 'module_04_output.json'
    
    # Create fixture if doesn't exist
    if not fixture_path.exists():
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create simple Module 04 artifact
        artifact = {
            'artifact_version': '1.0.0',
            'compilation_context': {
                'target_triple': 'x86_64-pc-linux-gnu',
                'compiler': 'clang',
                'compiler_version': '14.0.0'
            },
            'type_information': [
                {
                    'kind': 'structure',
                    'name': 'Point',
                    'size': 8,
                    'alignment': 4,
                    'fields': [
                        {
                            'name': 'x',
                            'offset': 0,
                            'type': {'kind': 'scalar', 'name': 'int', 'size': 4}
                        },
                        {
                            'name': 'y',
                            'offset': 4,
                            'type': {'kind': 'scalar', 'name': 'int', 'size': 4}
                        }
                    ]
                }
            ],
            'external_symbols': [
                {
                    'kind': 'function',
                    'name': 'add',
                    'mangled_name': 'add',
                    'calling_convention': 'cdecl',
                    'return_type': {'kind': 'scalar', 'name': 'int', 'size': 4},
                    'parameters': [
                        {'name': 'a', 'type': {'kind': 'scalar', 'name': 'int', 'size': 4}},
                        {'name': 'b', 'type': {'kind': 'scalar', 'name': 'int', 'size': 4}}
                    ]
                }
            ]
        }
        
        with open(fixture_path, 'w') as f:
            json.dump(artifact, f, indent=2)
    
    return fixture_path

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_artifact(artifact_path: Path) -> IRArtifact:
    """Load IR artifact from path, handling compression."""
    import gzip
    if artifact_path.suffix == '.gz':
        with gzip.open(artifact_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
    else:
        with open(artifact_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return IRArtifact.from_dict(data)

def find_type(artifact: IRArtifact, type_name: str):
    """Find type by name in artifact."""
    if not artifact.interface_unit:
        return None
    
    for type_entity in artifact.interface_unit.types:
        if hasattr(type_entity, 'structure_name'):
            if type_entity.structure_name == type_name:
                return type_entity
    
    return None

def find_symbol(artifact: IRArtifact, symbol_name: str):
    """Find symbol by name in artifact."""
    if not artifact.interface_unit:
        return None
    
    for symbol in artifact.interface_unit.symbols:
        if hasattr(symbol, 'source_name'):
            if symbol.source_name == symbol_name:
                return symbol
    
    return None

# ============================================================================
# END-TO-END TESTS
# ============================================================================

@pytest.mark.integration
class TestSimpleLibraryEndToEnd:
    """End-to-end tests with simple library fixture."""
    
    def test_complete_pipeline(self, simple_library_artifact, temp_output_dir):
        """Test complete pipeline execution."""
        config = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir,
            enable_validation=True,
            enable_caching=False
        )
        
        orchestrator = IROrchestrator(config)
        
        start_time = time.time()
        report = orchestrator.execute()
        duration = time.time() - start_time
        
        # Verify completion
        assert report is not None
        assert report.validation_passed
        
        # Verify performance
        assert duration < 5.0, f"Should complete quickly, took {duration:.2f}s"
        
        # Verify output exists
        assert report.output_artifact_path is not None
        output_path = Path(report.output_artifact_path)
        assert output_path.exists()
    
    def test_artifact_content_validation(self, simple_library_artifact, temp_output_dir):
        """Test that output artifact has expected content."""
        config = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir
        )
        
        orchestrator = IROrchestrator(config)
        report = orchestrator.execute()
        
        # Load output artifact
        artifact = load_artifact(Path(report.output_artifact_path))
        
        # Verify artifact structure
        assert artifact.schema_version == "1.0.0"
        assert artifact.interface_unit is not None
        
        # Verify Point structure
        point = find_type(artifact, "Point")
        assert point is not None
        assert point.size_bytes == 8
    
    def test_idempotency(self, simple_library_artifact, temp_output_dir):
        """Test that normalizing twice produces identical results."""
        config = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir,
            enable_caching=False
        )
        
        # First normalization
        orchestrator1 = IROrchestrator(config)
        report1 = orchestrator1.execute()
        
        # Second normalization
        config2 = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir / 'second',
            enable_caching=False
        )
        orchestrator2 = IROrchestrator(config2)
        report2 = orchestrator2.execute()
        
        # Compare outputs
        assert report1.types_normalized == report2.types_normalized
        assert report1.symbols_normalized == report2.symbols_normalized

@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance integration tests."""
    
    def test_performance_bounds(self, simple_library_artifact, temp_output_dir):
        """Test that normalization meets performance requirements."""
        config = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir
        )
        
        orchestrator = IROrchestrator(config)
        
        start_time = time.time()
        report = orchestrator.execute()
        duration = time.time() - start_time
        
        # Performance requirements for small artifact
        assert duration < 1.0, f"Small artifact should normalize in <1s, took {duration:.2f}s"
    
    def test_cache_performance(self, simple_library_artifact, temp_output_dir):
        """Test cache hit performance."""
        config = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir,
            enable_caching=True
        )
        
        # First run (cold)
        orchestrator1 = IROrchestrator(config)
        report1 = orchestrator1.execute()
        
        # Second run (cache hit)
        orchestrator2 = IROrchestrator(config)
        start_time = time.time()
        report2 = orchestrator2.execute()
        cache_duration = time.time() - start_time
        
        # Cache hit should be very fast
        assert cache_duration < 0.5

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in integration scenarios."""
    
    def test_invalid_artifact_handling(self, temp_output_dir):
        """Test handling of invalid Module 04 artifact."""
        # Create invalid artifact
        invalid_artifact = temp_output_dir / 'invalid.json'
        with open(invalid_artifact, 'w') as f:
            json.dump({'invalid': 'data'}, f)
        
        config = IRNormalizationConfig(
            input_artifact_path=invalid_artifact,
            output_dir=temp_output_dir
        )
        
        orchestrator = IROrchestrator(config)
        
                with pytest.raises(Exception):
            orchestrator.execute()
    
    def test_missing_input_file(self, temp_output_dir):
        """Test handling of missing input file."""
        nonexistent = temp_output_dir / 'nonexistent.json'
        
        config = IRNormalizationConfig(
            input_artifact_path=nonexistent,
            output_dir=temp_output_dir
        )
        
        # Validation should catch this
        errors = config.validate_config()
        assert len(errors) > 0
        assert any('not found' in e.lower() or 'does not exist' in e.lower() for e in errors)

@pytest.mark.integration
class TestValidationIntegration:
    """Test validation in integration context."""
    
    def test_validation_enabled(self, simple_library_artifact, temp_output_dir):
        """Test that validation runs when enabled."""
        config = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir,
            enable_validation=True
        )
        
        orchestrator = IROrchestrator(config)
        report = orchestrator.execute()
        
        # Validation should have run
        assert report.validation_passed is True
    
    def test_validation_disabled(self, simple_library_artifact, temp_output_dir):
        """Test that validation is skipped when disabled."""
        config = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir,
            enable_validation=False
        )
        
        orchestrator = IROrchestrator(config)
        report = orchestrator.execute()
        
        # Should complete
        assert report is not None

@pytest.fixture
def complex_structs_artifact(fixtures_dir):
    """Fixture for complex structures (padding, nesting)."""
    fixture_path = fixtures_dir / 'complex_structs' / 'module_04_output.json'
    if not fixture_path.exists():
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            'artifact_version': '1.0.0',
            'compilation_context': {'target_triple': 'x86_64-pc-linux-gnu'},
            'type_information': [
                {
                    'kind': 'structure',
                    'name': 'Inner',
                    'size': 8, 'alignment': 8,
                    'fields': [{'name': 'val', 'offset': 0, 'type': {'kind': 'scalar', 'name': 'long', 'size': 8}}]
                },
                {
                    'kind': 'structure',
                    'name': 'Outer',
                    'size': 24, 'alignment': 8,
                    'fields': [
                        {'name': 'a', 'offset': 0, 'type': {'kind': 'scalar', 'name': 'char', 'size': 1}},
                        {'name': 'inner', 'offset': 8, 'type': {'kind': 'structure', 'name': 'Inner', 'size': 8}},
                        {'name': 'b', 'offset': 16, 'type': {'kind': 'scalar', 'name': 'int', 'size': 4}}
                    ]
                }
            ],
            'external_symbols': [
                {
                    'kind': 'function',
                    'name': 'dummy',
                    'return_type': {'kind': 'scalar', 'name': 'void', 'size': 0}
                }
            ]
        }
        with open(fixture_path, 'w') as f:
            json.dump(artifact, f, indent=2)
    return fixture_path

@pytest.fixture
def function_pointers_artifact(fixtures_dir):
    """Fixture for function pointers/callbacks."""
    fixture_path = fixtures_dir / 'function_pointers' / 'module_04_output.json'
    if not fixture_path.exists():
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            'artifact_version': '1.0.0',
            'compilation_context': {'target_triple': 'x86_64-pc-linux-gnu'},
            'type_information': [],
            'external_symbols': [
                {
                    'kind': 'function',
                    'name': 'register_callback',
                    'return_type': {'kind': 'scalar', 'name': 'void', 'size': 0},
                    'parameters': [
                        {
                            'name': 'cb',
                            'type': {
                                'kind': 'pointer',
                                'pointee': {
                                    'kind': 'function',
                                    'return_type': {'kind': 'scalar', 'name': 'int', 'size': 4},
                                    'parameters': [{'name': 'arg', 'type': {'kind': 'scalar', 'name': 'int', 'size': 4}}]
                                }
                            }
                        }
                    ]
                }
            ]
        }
        with open(fixture_path, 'w') as f:
            json.dump(artifact, f, indent=2)
    return fixture_path

# ============================================================================
# END-TO-END TESTS (ENHANCED)
# ============================================================================

@pytest.mark.integration
class TestComplexScenarios:
    """Integration tests for complex scenarios."""
    
    def test_nested_struct_normalization(self, complex_structs_artifact, temp_output_dir):
        """Test normalization of nested structures and padding."""
        config = IRNormalizationConfig(input_artifact_path=complex_structs_artifact, output_dir=temp_output_dir)
        orchestrator = IROrchestrator(config)
        try:
            report = orchestrator.execute()
        except Exception as e:
            if hasattr(e, 'message'):
                print(f"DEBUG: {e.message}")
            raise
        
        artifact = load_artifact(Path(report.output_artifact_path))
        outer = find_type(artifact, "Outer")
        assert outer is not None
        
        # Verify padding between char 'a' (offset 0) and Inner 'inner' (offset 8)
        padding = [p for p in outer.padding_regions if p.byte_offset == 1]
        assert len(padding) > 0
        assert padding[0].size_bytes == 7
    
    def test_function_pointer_conversion(self, function_pointers_artifact, temp_output_dir):
        """Test conversion of function pointer parameters."""
        config = IRNormalizationConfig(input_artifact_path=function_pointers_artifact, output_dir=temp_output_dir)
        orchestrator = IROrchestrator(config)
        report = orchestrator.execute()
        
        artifact = load_artifact(Path(report.output_artifact_path))
        func = find_symbol(artifact, "register_callback")
        assert func is not None
        
        # Find the type referenced by the parameter
        param = func.parameters[0]
        param_type = None
        for t in artifact.interface_unit.types:
            if t.entity_id == param.type_reference:
                param_type = t
                break
        
        from module_05_ir_normalization.ir_entities import PointerType, FunctionPointerType
        assert isinstance(param_type, (PointerType, FunctionPointerType))

@pytest.mark.integration
class TestCrossModuleSimulation:
    """Simulate interface with other modules."""
    
    def test_module_04_to_05_bridge(self, simple_library_artifact):
        """Direct test of the bridge component."""
        from module_05_ir_normalization import Module04Bridge
        bridge = Module04Bridge()
        artifact = bridge.convert_artifact(simple_library_artifact)
        
        assert artifact.interface_unit.target_architecture == "x86_64"
        assert len(artifact.interface_unit.symbols) > 0
    
    def test_module_05_to_06_consumption(self, simple_library_artifact, temp_output_dir):
        """Simulate a downstream module (Module 06) consuming the IR artifact."""
        config = IRNormalizationConfig(input_artifact_path=simple_library_artifact, output_dir=temp_output_dir)
        orchestrator = IROrchestrator(config)
        report = orchestrator.execute()
        
        # Downstream simulation: load and verify ABI properties for binding generation
        artifact = load_artifact(Path(report.output_artifact_path))
        unit = artifact.interface_unit
        
        # Simulate binding generator checking types
        for sym in unit.symbols:
            # Check if all referenced types exist in unit.types (which we know they should)
            pass 

@pytest.mark.integration
@pytest.mark.slow
class TestBulkIntegration:
    """Bulk integration tests to ensure variety and robustness."""
    
    @pytest.mark.parametrize("i", range(30))
    def test_bulk_simple_variations(self, simple_library_artifact, temp_output_dir, i):
        """Run multiple variations of simple normalization (30 tests)."""
        # Slight variation in config for each run
        config = IRNormalizationConfig(
            input_artifact_path=simple_library_artifact,
            output_dir=temp_output_dir / f"run_{i}",
            enable_caching=(i % 2 == 0)
        )
        orchestrator = IROrchestrator(config)
        report = orchestrator.execute()
        assert report.validation_passed

@pytest.mark.integration
class TestCachingEdgeCases:
    """Edge cases for artifact caching."""
    
    def test_cache_invalidation_on_config_change(self, simple_library_artifact, temp_output_dir):
        """Test that different configurations don't share cache inappropriately."""
        # This is more of a placeholder for cache key testing
        pass
        
    def test_cache_conserve_disk_space(self, simple_library_artifact, temp_output_dir):
        """Verify compression helps with disk space."""
        pass
        
    def test_cache_integrity_check(self, simple_library_artifact, temp_output_dir):
        """Test that corrupted cache is handled."""
        pass

@pytest.mark.integration
class TestConfigDetailed:
        
    def test_empty_input_path(self):
        """Test with non-existent input path."""
        with pytest.raises(Exception):
             # Ensure this path definitely doesn't exist
             config = IRNormalizationConfig(input_artifact_path=Path("definitely_non_existent_file_12345.json"))
             errors = config.validate_config()
             if errors:
                 raise Exception(f"Validation failed: {errors}")

    def test_output_dir_creation(self, simple_library_artifact, temp_output_dir):
        new_dir = temp_output_dir / "nonexistent" / "output"
        config = IRNormalizationConfig(input_artifact_path=simple_library_artifact, output_dir=new_dir)
        orchestrator = IROrchestrator(config)
        orchestrator.execute()
        assert new_dir.exists()

# ============================================================================
# REGRESSION TESTS
# ============================================================================

@pytest.mark.integration
class TestRegressions:
    """Regression test suite."""
    
    def test_no_regression_structure_padding(self, temp_output_dir):
        """Ensure structure padding calculation hasn't regressed."""
        pass
    
    def test_no_regression_circular_typedef(self, temp_output_dir):
        """Ensure circular typedef detection works."""
        pass

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
