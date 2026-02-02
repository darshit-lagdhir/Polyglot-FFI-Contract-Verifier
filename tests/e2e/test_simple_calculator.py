import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath('modules/module_02_verification_pipeline'))

from verification_pipeline import verify

@pytest.mark.e2e
@pytest.mark.slow
class TestSimpleCalculatorE2E:
    """End-to-end test with simple calculator example."""
    
    @pytest.fixture(scope="class")
    def calculator_example_dir(self):
        """Get calculator example directory."""
        return Path("examples/simple_calculator")
    
    @pytest.fixture(scope="class")
    def calculator_library(self, calculator_example_dir):
        """Build calculator library once for all tests."""
        # Check if library already exists
        if sys.platform == "win32":
            library = calculator_example_dir / "calculator.dll"
        elif sys.platform == "darwin":
            library = calculator_example_dir / "libcalculator.dylib"
        else:
            library = calculator_example_dir / "libcalculator.so"
        
        # Build if needed
        if not library.exists():
            if sys.platform == "win32":
                os.system(f"cd {calculator_example_dir} && build.bat")
            else:
                os.system(f"cd {calculator_example_dir} && bash build.sh")
        
        if not library.exists():
            pytest.skip(f"Could not build library: {library}")
        
        yield {
            "header": str(calculator_example_dir / "calculator.h"),
            "library": str(library)
        }
    
    def test_calculator_verification_runs(self, calculator_library, temp_dir):
        """Verification should run without errors."""
        try:
            result = verify(
                header_path=calculator_library["header"],
                library_path=calculator_library["library"],
                output_dir=str(temp_dir / "results"),
                verbose=False
            )
            
            # Should complete without exception
            assert result is not None
            assert hasattr(result, 'success')
            
        except Exception as e:
            # If verification fails due to missing dependencies (libclang, etc.),
            # that's acceptable for this test
            if "libclang" in str(e).lower() or "clang" in str(e).lower():
                pytest.skip(f"Missing libclang: {e}")
            else:
                raise
    
    def test_calculator_artifacts_created(self, calculator_library, temp_dir):
        """Artifacts should be created."""
        output_dir = temp_dir / "results"
        
        try:
            result = verify(
                header_path=calculator_library["header"],
                library_path=calculator_library["library"],
                output_dir=str(output_dir),
                verbose=False
            )
            
            # Check that output directory was created
            assert output_dir.exists()
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip(f"Missing libclang: {e}")
            else:
                raise

@pytest.mark.e2e
class TestVerifyAPI:
    """E2E tests for verify() API."""
    
    def test_verify_with_invalid_header(self, temp_dir):
        """Should handle invalid header gracefully."""
        header = temp_dir / "invalid.h"
        library = temp_dir / "library.dll"
        
        # Create empty files
        header.write_text("")
        library.write_text("")
        
        try:
            result = verify(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(temp_dir / "results"),
                verbose=False
            )
            
            # Should return result even if it fails
            assert result is not None
            
        except Exception as e:
            # Expected to fail, but should be a controlled failure
            assert "libclang" in str(e).lower() or "not found" in str(e).lower()
    
    def test_verify_with_missing_files(self, temp_dir):
        """Should raise error for missing files."""
        with pytest.raises((ValueError, FileNotFoundError, OSError)):
            verify(
                header_path="nonexistent.h",
                library_path="nonexistent.dll",
                output_dir=str(temp_dir / "results"),
                verbose=False
            )
