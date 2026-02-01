"""
Boundary Value Test Generator
Generates tests for edge cases like zero, max/min, and empty buffers.
"""

from typing import Dict, Any, List
from .input_value_generator import InputValueGenerator

class BoundaryValueTestGenerator:
    """
    Produces edge case test cases.
    """
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_boundary_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates boundary tests for relevant parameters."""
        test_cases = []
        
        for p in f_contract.get("parameter_contracts", []):
            t_id = p["type_id"]
            if "int" in t_id or "uint" in t_id:
                # Add Zero Test
                test_cases.append(self._create_boundary_test(f_contract, ir, p["parameter_name"], "zero", 0))
                # Add Max Test
                max_val = self.input_gen.generate_value(t_id, ir, "maximal")
                test_cases.append(self._create_boundary_test(f_contract, ir, p["parameter_name"], "max", max_val))
                
        return test_cases

    def _create_boundary_test(self, f: Dict[str, Any], ir: Dict[str, Any], p_name: str, b_type: str, val: Any) -> Dict[str, Any]:
        inputs = {}
        for p in f.get("parameter_contracts", []):
            inputs[p["parameter_name"]] = {
                "type": p["type_id"],
                "value": val if p["parameter_name"] == p_name else self.input_gen.generate_value(p["type_id"], ir, "typical")
            }
            
        return {
            "test_id": f"test_{f['function_name']}_boundary_{p_name}_{b_type}",
            "test_category": "boundary",
            "priority": "normal",
            "function_name": f["function_name"],
            "description": f"Boundary test ({b_type}) for parameter {p_name}",
            "constraints_exercised": [], # Exercised implicitly
            "inputs": inputs,
            "expected_outcome": {
                "type": "success"
            },
            "rationale": f"Checks handling of {b_type} boundary for {p_name}."
        }
