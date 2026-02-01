"""
Positive Test Generator
Generates valid test cases that satisfy all contract constraints.
"""

from typing import Dict, Any, List
from .input_value_generator import InputValueGenerator

class PositiveTestGenerator:
    """
    Produces successful execution test cases.
    """
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_positive_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates a set of positive test cases for a function."""
        name = f_contract["function_name"]
        test_cases = []
        
        # 1. Minimal Valid
        test_cases.append(self._create_test_case(f_contract, ir, "minimal"))
        
        # 2. Typical Valid
        test_cases.append(self._create_test_case(f_contract, ir, "typical"))
        
        return test_cases

    def _create_test_case(self, f: Dict[str, Any], ir: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        params = {}
        for p in f.get("parameter_contracts", []):
            params[p["parameter_name"]] = {
                "type": p["type_id"],
                "value": self.input_gen.generate_value(p["type_id"], ir, strategy)
            }
            
        cids = [pc["constraint_id"] for pc in f.get("pre_conditions", [])]
        
        return {
            "test_id": f"test_{f['function_name']}_positive_{strategy}",
            "test_category": "positive",
            "priority": "normal",
            "function_name": f["function_name"],
            "description": f"Valid call to {f['function_name']} with {strategy} inputs",
            "constraints_exercised": cids,
            "inputs": params,
            "expected_outcome": {
                "type": "success",
                "return_value_type": f.get("return_contract", {}).get("type_id", "primitive:void")
            },
            "rationale": f"Verifies that valid {strategy} inputs are accepted."
        }
