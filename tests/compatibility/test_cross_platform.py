import pytest
import sys
import platform
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath('modules/module_02_verification_pipeline'))

from verification_pipeline import verify

@pytest.mark.compatibility
class TestCrossPlatformCompatibility:
    """Cross-platform compatibility tests."""
    
    def test_windows_compatibility(self, temp_dir):
        """Test: Windows-specific functionality."""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")
        
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Calculator example not found")
        
        header = example_dir / "calculator.h"
        library = example_dir / "calculator.dll"
        
        if not header.exists() or not library.exists():
            pytest.skip("Calculator files not found")
        
        try:
            result = verify(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(temp_dir / "windows_compat"),
                verbose=False
            )
            
            print(f"\nWindows compatibility: OK")
            assert result is not None
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip(f"libclang not available: {e}")
            else:
                raise
    
    def test_linux_compatibility(self, temp_dir):
        """Test: Linux-specific functionality."""
        if sys.platform != "linux":
            pytest.skip("Linux-only test")
        
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Calculator example not found")
        
        header = example_dir / "calculator.h"
        library = example_dir / "libcalculator.so"
        
        if not header.exists() or not library.exists():
            pytest.skip("Calculator files not found")
        
        try:
            result = verify(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(temp_dir / "linux_compat"),
                verbose=False
            )
            
            print(f"\nLinux compatibility: OK")
            assert result is not None
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip(f"libclang not available: {e}")
            else:
                raise
    
    def test_macos_compatibility(self, temp_dir):
        """Test: macOS-specific functionality."""
        if sys.platform != "darwin":
            pytest.skip("macOS-only test")
        
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Calculator example not found")
        
        header = example_dir / "calculator.h"
        library = example_dir / "libcalculator.dylib"
        
        if not header.exists() or not library.exists():
            pytest.skip("Calculator files not found")
        
        try:
            result = verify(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(temp_dir / "macos_compat"),
                verbose=False
            )
            
            print(f"\nmacOS compatibility: OK")
            assert result is not None
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip(f"libclang not available: {e}")
            else:
                raise

@pytest.mark.compatibility
class TestPythonVersionCompatibility:
    """Python version compatibility tests."""
    
    def test_python_version_supported(self):
        """Test: Python version is supported."""
        version_info = sys.version_info
        
        print(f"\nPython version: {version_info.major}.{version_info.minor}.{version_info.micro}")
        print(f"Platform: {sys.platform}")
        print(f"Architecture: {platform.machine()}")
        
        # Require Python 3.11+
        assert version_info >= (3, 11), \
            f"Python 3.11+ required, got {version_info.major}.{version_info.minor}"
    
    def test_basic_imports(self):
        """Test: Basic imports work."""
        try:
            from verification_pipeline import (
                verify,
                verify_optimized,
                verify_extensible,
                CompletePipeline,
                OptimizedCompletePipeline,
                ExtensiblePipeline
            )
            
            print("\nAll imports successful")
            assert True
            
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
