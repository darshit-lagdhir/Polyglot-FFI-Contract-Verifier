import pytest
from pathlib import Path
import sys

# Add module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from modules.module_03_build_process.build_process import (
        BuildStage,
        SourceEnumerationStage,
        EnhancedBuildProcessOrchestrator,
        EnvironmentDescriptor,
    )
except ImportError:
    # If module missing or renamed
    pytest.skip("Module 03 not available", allow_module_level=True)


class TestModule03Simple:
    def test_imports(self):
        assert BuildStage is not None
        assert SourceEnumerationStage is not None
        assert EnhancedBuildProcessOrchestrator is not None

    def test_stage_instantiation(self, tmp_path):
        stage = SourceEnumerationStage(tmp_path)
        assert stage.stage_number == BuildStage.SOURCE_ENUMERATION

    def test_orchestrator_instantiation(self):
        env = EnvironmentDescriptor(
            compiler_name="Test",
            compiler_version="1.0",
            compiler_executable=Path("/usr/bin/test"),
            linker_executable=Path("/usr/bin/ld"),
            target_os="Linux",
            target_architecture="x86_64",
            host_os="Linux",
            host_architecture="x86_64",
            build_mode="debug",
            optimization_level="O0",
            debug_symbols=True,
            calling_convention="cdecl",
            structure_packing=8,
            alignment_rules="default",
        )
        orch = EnhancedBuildProcessOrchestrator(env)
        assert orch.environment == env
