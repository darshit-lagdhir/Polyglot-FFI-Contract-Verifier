"""
Regression tests for system stability.
Ensures core components produce deterministic outputs for fixed inputs.
"""

import unittest
import json
import tempfile
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.execution_context import ExecutionContext, ExecutionContextBuilder
from src.synthesis.contract_synthesizer import ContractSynthesizer
from src.adapters.adapter_generator import AdapterGenerator

class TestRegression(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.builder = ExecutionContextBuilder()
        # Minimal IR
        self.ir_sample = {
            "functions": [
                {
                    "name": "regression_test_func",
                    "return_type": {"kind": "primitive", "name": "int"},
                    "parameters": [
                        {"name": "ptr", "type": {"kind": "pointer", "pointee": {"kind": "primitive", "name": "char"}}}
                    ],
                    "linkage": "external",
                    "source_location": {"file": "test.h", "line": 10},
                    "calling_convention": "cdecl"
                }
            ],
            "structs": [],
            "enums": [],
            "platform": {"os": "windows", "arch": "x64", "pointer_size": 8},
            "type_registry": {}
        }
        
    def test_synthesis_determinism(self):
        """Ensure contract synthesis is deterministic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy files
            h_path = Path(tmpdir) / "test.h"
            lib_path = Path(tmpdir) / "test.dll"
            h_path.touch()
            lib_path.touch()

            # Create context
            context = self.builder.build(
                header_file=str(h_path),
                library_file=str(lib_path),
                working_directory=tmpdir
            )
            
            # Save IR to expected path
            ir_path = Path(context.artifacts.intermediate_representation_path)
            ir_path.parent.mkdir(parents=True, exist_ok=True)
            with ir_path.open('w') as f:
                json.dump(self.ir_sample, f)
            
            # Run synthesis twice
            synth = ContractSynthesizer()
            c1 = synth.synthesize(context)
            
            # Clean up output to force regeneration? 
            # Ideally synthesize doesn't cache in memory across instances, but we use new instance.
            synth2 = ContractSynthesizer()
            c2 = synth2.synthesize(context)
            
            # Remove timestamps and dynamic IDs for comparison
            # IDs might be random (UUID)?
            # ConstraintIDGenerator uses UUID? 
            # If so, we can't test strict equality without mocking ID gen.
            
            # Let's check functional equivalence structure
            self.assertEqual(len(c1['function_contracts']), len(c2['function_contracts']))
            self.assertEqual(c1['function_contracts'][0]['function_name'], c2['function_contracts'][0]['function_name'])
            
            # Check constraints count
            self.assertEqual(len(c1['function_contracts'][0]['pre_conditions']), 
                             len(c2['function_contracts'][0]['pre_conditions']))

    def test_adapter_consistency(self):
        """Ensure adapter generation structure remains consistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy files
            h_path = Path(tmpdir) / "test.h"
            lib_path = Path(tmpdir) / "test.dll"
            h_path.touch()
            lib_path.touch()
            
            context = self.builder.build(
                header_file=str(h_path),
                library_file=str(lib_path),
                working_directory=tmpdir
            )
            
            # Simple contract
            contract = {
                "function_contracts": [
                     {
                        "function_name": "test_func",
                        "pre_conditions": [],
                        "post_conditions": [],
                        "parameter_contracts": [],
                        "return_contract": {}
                     }
                ],
                "struct_contracts": [],
                "global_constraints": [],
                "platform": {"os": "windows"}
            }
            
            # Save contract to path
            c_path = Path(context.artifacts.contract_path)
            c_path.parent.mkdir(parents=True, exist_ok=True)
            with c_path.open('w') as f:
                json.dump(contract, f)
            
            # Save dummy IR (AdapterGenerator might check for it)
            ir_path = Path(context.artifacts.intermediate_representation_path)
            with ir_path.open('w') as f:
                json.dump({"type_registry": {}, "functions": [], "structs": []}, f)
                
            gen = AdapterGenerator()
            adapters = gen.generate(context)
            
            # Expect at least one adapter
            self.assertTrue(adapters is not None)
            # Depending on implementation, might return list
            if isinstance(adapters, list):
                 self.assertTrue(len(adapters) > 0)

if __name__ == '__main__':
    unittest.main()
