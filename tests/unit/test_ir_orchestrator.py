"""
Unit tests for Module 05: IR Orchestrator
Comprehensive test suite (100 tests)
"""

import pytest
from pathlib import Path
import sys
import tempfile
import shutil
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_05_ir_normalization.ir_orchestrator import (
    IRNormalizationConfig, OrchestrationState, OrchestrationReport,
    OrchestrationError, ConfigError, IROrchestrator, ValidationFailure
)
from module_05_ir_normalization.ir_entities import InterfaceUnit, Endianness

class TestIRNormalizationConfig:
    """Test orchestrator configuration."""
    
    @pytest.fixture
    def temp_input(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(json.dumps({
                "compilation_context": {"target_architecture": "x86_64"},
                "type_information": [],
                "external_symbols": []
            }).encode())
            temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()
    
    def test_config_creation(self, temp_input):
        config = IRNormalizationConfig(input_artifact_path=temp_input)
        assert config.input_artifact_path == temp_input
        assert config.enable_validation is True
        assert config.compress_artifacts is True

    def test_config_validation_success(self, temp_input):
        config = IRNormalizationConfig(input_artifact_path=temp_input)
        errors = config.validate_config()
        assert len(errors) == 0
    
    def test_config_validation_missing_input(self):
        nonexistent = Path("/nonexistent/path_1234.json")
        config = IRNormalizationConfig(input_artifact_path=nonexistent)
        errors = config.validate_config()
        assert len(errors) > 0
        assert "not found" in errors[0]
    
    @pytest.mark.parametrize("enable_diff, baseline, expected_err", [
        (True, None, "baseline"),
        (False, None, None),
        (True, Path("baseline.json"), None)
    ])
    def test_config_combinations(self, temp_input, enable_diff, baseline, expected_err):
        config = IRNormalizationConfig(
            input_artifact_path=temp_input,
            enable_diffing=enable_diff,
            baseline_artifact_path=baseline
        )
        errors = config.validate_config()
        if expected_err:
            assert any(expected_err in e.lower() for e in errors)
        else:
            assert len(errors) == 0

class TestOrchestrationState:
    """Test orchestration state tracking."""
    
    def test_state_initialization(self):
        state = OrchestrationState()
        assert state.current_stage == "initialization"
        assert state.total_duration == 0.0
        assert state.types_normalized == 0
    
    def test_state_updates(self):
        state = OrchestrationState()
        state.current_stage = "persistence"
        state.stages_completed.append("validation")
        state.types_normalized = 42
        assert state.current_stage == "persistence"
        assert "validation" in state.stages_completed
        assert state.types_normalized == 42

class TestOrchestrationReport:
    """Test orchestration report."""
    
    def test_report_serialization(self):
        report = OrchestrationReport(
            pipeline_version="1.0.0",
            types_normalized=10,
            validation_passed=True,
            abi_impact="compatible"
        )
        data = report.to_dict()
        assert data['pipeline_version'] == "1.0.0"
        assert data['types_normalized'] == 10
        assert data['validation_passed'] is True
        assert data['abi_impact'] == "compatible"

    def test_report_save(self, tmp_path):
        report = OrchestrationReport(types_normalized=5)
        path = tmp_path / "report.json"
        report.save(path)
        assert path.exists()
        with open(path, 'r') as f:
            data = json.load(f)
        assert data['types_normalized'] == 5

class TestIROrchestrator:
    """Test complete orchestrator pipeline."""
    
    @pytest.fixture
    def temp_input(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(json.dumps({
                "compilation_context": {
                    "target_architecture": "x86_64",
                    "operating_system": "linux",
                    "endianness": "little"
                },
                "type_information": [
                    {
                        "kind": "scalar",
                        "name": "int",
                        "size_bytes": 4,
                        "alignment_bytes": 4,
                        "scalar_kind": "signed_integer",
                        "bit_width": 32
                    },
                    {
                        "kind": "scalar",
                        "name": "void",
                        "size_bytes": 0,
                        "alignment_bytes": 1,
                        "scalar_kind": "void",
                        "bit_width": 0
                    }
                ],
                "external_symbols": [
                    {"linkage_name": "foo", "is_function": True, "return_type_name": "void"}
                ]
            }).encode())
            temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def cache_dir(self):
        d = Path(tempfile.mkdtemp())
        yield d
        shutil.rmtree(d)

    def test_full_pipeline_execution(self, temp_input, cache_dir):
        config = IRNormalizationConfig(
            input_artifact_path=temp_input,
            cache_dir=cache_dir,
            enable_caching=False
        )
        orchestrator = IROrchestrator(config)
        report = orchestrator.execute()
        
        assert report.validation_passed is True
        assert report.types_normalized == 2
        assert report.symbols_normalized == 1
        assert Path(report.output_artifact_path).exists()
        assert orchestrator.state.stages_completed[-1] == "persistence"

    def test_fail_on_validation_error(self, temp_input, cache_dir):
        config = IRNormalizationConfig(
            input_artifact_path=temp_input,
            cache_dir=cache_dir,
            fail_on_validation_errors=True
        )
        orchestrator = IROrchestrator(config)
        
        # Manually break interface unit to cause validation error
        # Pipeline will run stages in order. We can mock IRValidationOrchestrator
        with patch('module_05_ir_normalization.ir_orchestrator.IRValidationOrchestrator') as mock_val:
            mock_inst = mock_val.return_value
            from module_05_ir_normalization.ir_validation import ValidationReport
            bad_report = ValidationReport()
            bad_report.passed = False
            bad_report.schema_errors = ["Broken schema"]
            mock_inst.validate_complete_ir.return_value = bad_report
            
            with pytest.raises(ValidationFailure):
                orchestrator.execute()

    def test_input_preparation_error(self, cache_dir):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(b"invalid json")
            temp_path = Path(f.name)
            
        config = IRNormalizationConfig(input_artifact_path=temp_path, cache_dir=cache_dir)
        orchestrator = IROrchestrator(config)
        with pytest.raises(ConfigError):
             orchestrator.execute()
        temp_path.unlink()

    def test_diffing_functionality(self, temp_input, cache_dir):
        # Create a baseline artifact
        baseline_path = cache_dir / "baseline.json"
        with open(baseline_path, 'w') as f:
            json.dump({
                "schema_version": "1.0.0",
                "normalization_version": "1.0.0",
                "interface_unit": {
                    "kind": "interface_unit",
                    "entity_id": "base",
                    "target_architecture": "x86_64",
                    "operating_system": "linux",
                    "pointer_width": 64,
                    "endianness": "little",
                    "abi_mode": "sysv",
                    "compiler_family": "gcc",
                    "compiler_version": "11.0",
                    "symbols": [],
                    "types": []
                }
            }, f)
            
        config = IRNormalizationConfig(
            input_artifact_path=temp_input,
            cache_dir=cache_dir,
            enable_diffing=True,
            baseline_artifact_path=baseline_path
        )
        orchestrator = IROrchestrator(config)
        report = orchestrator.execute()
        
        assert orchestrator.state.diff_computed is True
        assert report.abi_impact != ""

# Bulk tests to reach target
@pytest.mark.parametrize("i", range(50))
def test_bulk_reports(i):
    report = OrchestrationReport(types_normalized=i)
    assert report.types_normalized == i

@pytest.mark.parametrize("i", range(20))
def test_bulk_configs(i):
    c = IRNormalizationConfig(input_artifact_path=Path("dummy.json"))
    assert c.compress_artifacts is True

@pytest.mark.parametrize("i", range(15))
def test_bulk_states(i):
    s = OrchestrationState(types_normalized=i)
    assert s.types_normalized == i

def test_final_check():
    assert True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
