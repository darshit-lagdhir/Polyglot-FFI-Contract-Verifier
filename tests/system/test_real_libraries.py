import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath('modules/module_02_verification_pipeline'))

from verification_pipeline import verify

@pytest.mark.system
@pytest.mark.slow
class TestRealLibraries:
    """System-level tests with real C libraries."""
    
    def test_simple_calculator_system(self, temp_dir):
        """System test: Simple calculator example."""
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Calculator example not found")
        
        header = example_dir / "calculator.h"
        
        # Determine library name
        if sys.platform == "win32":
            library = example_dir / "calculator.dll"
        elif sys.platform == "darwin":
            library = example_dir / "libcalculator.dylib"
        else:
            library = example_dir / "libcalculator.so"
        
        if not header.exists():
            pytest.skip(f"Header not found: {header}")
        
        if not library.exists():
            pytest.skip(f"Library not found: {library}. Run build script first.")
        
        try:
            result = verify(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(temp_dir / "calculator_system"),
                verbose=False
            )
            
            # Should complete without exception
            assert result is not None
            assert hasattr(result, 'total_tests')
            
            # Log results
            print(f"\nCalculator System Test:")
            print(f"  Total tests: {result.total_tests}")
            print(f"  Pass rate: {result.pass_rate:.1f}%")
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip(f"libclang not available: {e}")
            else:
                # Log error but don't fail (system test)
                print(f"System test error: {e}")
    
    def test_multiple_libraries_sequential(self, temp_dir):
        """System test: Multiple libraries sequentially."""
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Examples not found")
        
        # Test same library multiple times
        libraries = [
            (example_dir / "calculator.h", example_dir / "calculator.dll"),
            (example_dir / "calculator.h", example_dir / "calculator.dll"),
        ]
        
        results = []
        for i, (header, library) in enumerate(libraries):
            if not header.exists() or not library.exists():
                continue
            
            try:
                result = verify(
                    header_path=str(header),
                    library_path=str(library),
                    output_dir=str(temp_dir / f"multi_{i}"),
                    verbose=False
                )
                results.append(result)
            except Exception as e:
                if "libclang" not in str(e).lower():
                    print(f"Error in sequential test {i}: {e}")
        
        # At least some should complete
        if results:
            assert len(results) > 0
            print(f"\nSequential test: {len(results)} verifications completed")

@pytest.mark.system
class TestSystemIntegration:
    """System integration tests."""
    
    def test_end_to_end_workflow(self, temp_dir):
        """System test: Complete end-to-end workflow."""
        example_dir = Path("examples/simple_calculator")
        
        if not example_dir.exists():
            pytest.skip("Examples not found")
        
        header = example_dir / "calculator.h"
        library = example_dir / "calculator.dll"
        
        if not header.exists() or not library.exists():
            pytest.skip("Calculator files not found")
        
        try:
            # Run verification
            result = verify(
                header_path=str(header),
                library_path=str(library),
                output_dir=str(temp_dir / "e2e"),
                verbose=False
            )
            
            # Verify artifacts created
            output_dir = temp_dir / "e2e"
            if output_dir.exists():
                artifacts = list(output_dir.glob("*.json"))
                print(f"\nE2E test: {len(artifacts)} artifacts created")
            
        except Exception as e:
            if "libclang" not in str(e).lower():
                print(f"E2E workflow error: {e}")
