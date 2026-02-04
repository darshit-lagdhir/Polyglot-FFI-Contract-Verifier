#!/usr/bin/env python3
"""
Unit tests for Module 03 Build Process - 
Tests build philosophy enforcement and core architecture.
"""

import pytest
import sys
from pathlib import Path

# Add module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.module_03_build_process.build_process import (
    BuildPhilosophy,
    BuildConfigError,
    EnvironmentDescriptor,
    BuildMode,
    BuildDomain,
    BuildStage,
)

class TestBuildPhilosophy:
    """Test the BuildPhilosophy class and principle enforcement."""
    
    def test_philosophy_creation(self):
        """Test creating a BuildPhilosophy instance with defaults."""
        philosophy = BuildPhilosophy()
        
        assert philosophy.enforce_explicitness is True
        assert philosophy.enforce_determinism is True
        assert philosophy.enforce_isolation is True
        assert philosophy.enforce_provenance is True
        assert philosophy.allow_implicit_defaults is False
        assert philosophy.allow_silent_fallbacks is False
    
    def test_validate_explicit_configuration_success(self):
        """Test that explicit configuration passes validation."""
        philosophy = BuildPhilosophy()
        
        config = {
            'toolchain_version': '19.29',
            'compiler_executable': '/usr/bin/clang',
            'target_architecture': 'x86_64',
            'build_mode': 'release',
            'abi_conventions': 'msvc_x64'
        }
        
        # Should not raise
        philosophy.validate_configuration(config)
    
    def test_validate_missing_required_keys_fails(self):
        """Test that missing required configuration keys cause failure."""
        philosophy = BuildPhilosophy()
        
        config = {
            'toolchain_version': '19.29',
            # Missing: compiler_executable, target_architecture, build_mode, abi_conventions
        }
        
        with pytest.raises(BuildConfigError) as exc_info:
            philosophy.validate_configuration(config)
        
        assert "missing required explicit declarations" in str(exc_info.value)
        assert "compiler_executable" in str(exc_info.value)
    
    def test_validate_implicit_defaults_rejected(self):
        """Test that implicit default values are rejected."""
        philosophy = BuildPhilosophy()
        
        config = {
            'toolchain_version': '19.29',
            'compiler_executable': '/usr/bin/clang',
            'target_architecture': 'auto',              'build_mode': 'release',
            'abi_conventions': 'msvc_x64'
        }
        
        with pytest.raises(BuildConfigError) as exc_info:
            philosophy.validate_configuration(config)
        
        assert "implicit default value" in str(exc_info.value)
        assert "target_architecture" in str(exc_info.value)

class TestEnvironmentDescriptor:
    """Test the EnvironmentDescriptor class."""
    
    def test_descriptor_creation(self):
        """Test creating an EnvironmentDescriptor."""
        descriptor = EnvironmentDescriptor(
            compiler_name="MSVC",
            compiler_version="19.29",
            compiler_executable=Path("/usr/bin/cl.exe"),
            linker_executable=Path("/usr/bin/link.exe"),
            target_os="Windows",
            target_architecture="x86_64",
            host_os="Windows",
            host_architecture="x86_64",
            build_mode=BuildMode.RELEASE,
            optimization_level="O2",
            debug_symbols=True,
            calling_convention="cdecl",
            structure_packing=8,
            alignment_rules="default"
        )
        
        assert descriptor.compiler_name == "MSVC"
        assert descriptor.compiler_version == "19.29"
        assert descriptor.build_mode == BuildMode.RELEASE
        assert descriptor.structure_packing == 8
    
    def test_descriptor_serialization(self):
        """Test that descriptor can be serialized to JSON and back."""
        original = EnvironmentDescriptor(
            compiler_name="MSVC",
            compiler_version="19.29",
            compiler_executable=Path("/usr/bin/cl.exe"),
            linker_executable=Path("/usr/bin/link.exe"),
            target_os="Windows",
            target_architecture="x86_64",
            host_os="Windows",
            host_architecture="x86_64",
            build_mode=BuildMode.RELEASE,
            optimization_level="O2",
            debug_symbols=True,
            calling_convention="cdecl",
            structure_packing=8,
            alignment_rules="default"
        )
        
        # Serialize
        json_str = original.to_json()
        assert "MSVC" in json_str
        assert "19.29" in json_str
        
        # Deserialize
        restored = EnvironmentDescriptor.from_json(json_str)
        
        assert restored.compiler_name == original.compiler_name
        assert restored.compiler_version == original.compiler_version
        assert restored.build_mode == original.build_mode
        assert restored.structure_packing == original.structure_packing

class TestBuildEnums:
    """Test build process enumerations."""
    
    def test_build_domain_enum(self):
        """Test BuildDomain enumeration."""
        assert BuildDomain.NATIVE_VERIFICATION_TOOLING.value == "native_verification_tooling"
        assert BuildDomain.ORCHESTRATION_ADAPTER_TOOLING.value == "orchestration_adapter_tooling"
        assert BuildDomain.VERIFICATION_TARGETS.value == "verification_targets"
    
    def test_build_stage_enum(self):
        """Test BuildStage enumeration."""
        assert BuildStage.SOURCE_ENUMERATION.value == 1
        assert BuildStage.SOURCE_VALIDATION.value == 2
        assert BuildStage.PACKAGING_VALIDATION.value == 7
    
    def test_build_mode_enum(self):
        """Test BuildMode enumeration."""
        assert BuildMode.DEBUG.value == "debug"
        assert BuildMode.RELEASE.value == "release"
        assert BuildMode.CI.value == "ci"

class TestToolchainDetection:
    """Test toolchain detection and validation."""
    
    def test_toolchain_detector_creation(self):
        """Test creating a ToolchainDetector instance."""
        from modules.module_03_build_process.build_process import ToolchainDetector
        
        detector = ToolchainDetector()
        assert detector is not None
        assert len(detector.detected_toolchains) == 0
    
    def test_toolchain_descriptor_creation(self):
        """Test creating a ToolchainDescriptor."""
        from modules.module_03_build_process.build_process import ToolchainDescriptor
        
        descriptor = ToolchainDescriptor(
            compiler_name="MSVC",
            compiler_version="19.29",
            compiler_full_version="19.29.30133",
            compiler_executable=Path("/usr/bin/cl.exe"),
            compiler_executable_hash="abc123",
            linker_executable=Path("/usr/bin/link.exe"),
            linker_executable_hash="def456",
            linker_version="14.29",
            target_triple="Windows-x86_64-msvc",
            target_os="Windows",
            target_architecture="x86_64",
            target_abi="msvc",
            default_calling_convention="microsoft_x64",
            default_structure_packing=8,
            supports_explicit_packing=True,
            name_mangling_scheme="msvc",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=False
        )
        
        assert descriptor.compiler_name == "MSVC"
        assert descriptor.target_triple == "Windows-x86_64-msvc"
        assert descriptor.default_structure_packing == 8
    
    def test_toolchain_descriptor_serialization(self):
        """Test toolchain descriptor JSON serialization."""
        from modules.module_03_build_process.build_process import ToolchainDescriptor
        
        original = ToolchainDescriptor(
            compiler_name="Clang",
            compiler_version="14",
            compiler_full_version="14.0.0",
            compiler_executable=Path("/usr/bin/clang"),
            compiler_executable_hash="hash1",
            linker_executable=Path("/usr/bin/ld"),
            linker_executable_hash="hash2",
            linker_version="2.38",
            target_triple="x86_64-pc-linux-gnu",
            target_os="Linux",
            target_architecture="x86_64",
            target_abi="gnu",
            default_calling_convention="sysv_amd64",
            default_structure_packing=1,
            supports_explicit_packing=True,
            name_mangling_scheme="itanium",
            supports_debug_symbols=True,
            supports_optimization=True,
            deterministic_output=True
        )
        
        # Serialize
        json_str = original.to_json()
        assert "Clang" in json_str
        assert "sysv_amd64" in json_str
        
        # Deserialize
        restored = ToolchainDescriptor.from_json(json_str)
        assert restored.compiler_name == original.compiler_name
        assert restored.target_triple == original.target_triple
        assert restored.deterministic_output == original.deterministic_output
    
    def test_toolchain_requirement_validator_creation(self):
        """Test creating a ToolchainRequirementValidator."""
        from modules.module_03_build_process.build_process import ToolchainRequirementValidator
        
        requirements = {
            'required_target_os': 'Windows',
            'minimum_compiler_version': {
                'MSVC': '19.20'
            }
        }
        
        validator = ToolchainRequirementValidator(requirements)
        assert validator.requirements == requirements
    
    def test_version_comparison(self):
        """Test version comparison logic."""
        from modules.module_03_build_process.build_process import ToolchainRequirementValidator
        
        validator = ToolchainRequirementValidator({})
        
        assert validator._compare_versions("19.29", "19.20") == 1  # newer
        assert validator._compare_versions("19.20", "19.29") == -1  # older
        assert validator._compare_versions("19.29", "19.29") == 0  # equal
        assert validator._compare_versions("14", "13") == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
