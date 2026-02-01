"""
Negative Test Generator
Generates test cases that deliberately violate contract constraints.
"""

from typing import Dict, Any, List
from .input_value_generator import InputValueGenerator

class NegativeTestGenerator:
    """
    Produces failure execution test cases for constraint verification.
    """
    
    EXCEPTION_MAP = {
        "non_null": "NullPointerViolation",
        "buffer_size": "BufferSizeViolation",
        "struct_layout": "LayoutMismatchError",
        "alignment": "LayoutMismatchError",
        "borrowed": "OwnershipViolation",
        "transferred": "OwnershipViolation",
        "error_code": "ReturnValueViolation",
        "null_terminated_string": "FFIContractViolation"
    }
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_negative_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates one negative test case per pre-condition."""
        test_cases = []
        name = f_contract["function_name"]
        
        for constraint in f_contract.get("pre_conditions", []):
            tc = self._generate_violation(f_contract, constraint, ir)
            if tc:
                 test_cases.append(tc)
                 
        return test_cases

    def _generate_violation(self, f: Dict[str, Any], c: Dict[str, Any], ir: Dict[str, Any]) -> Dict[str, Any]:
        c_type = c["constraint_type"]
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        
        # Start with typical valid inputs
        inputs = {}
        for p in f.get("parameter_contracts", []):
            p_name = p["parameter_name"]
            inputs[p_name] = {
                "type": p["type_id"],
                "value": self.input_gen.generate_value(p["type_id"], ir, "typical")
            }
            
        # Corrupt the target input based on constraint type
        exc_type = self.EXCEPTION_MAP.get(c_type, "FFIContractViolation")
        
        if c_type == "non_null":
            if target in inputs:
                inputs[target]["value"] = None
            else:
                return None # Target not found
        
        elif c_type == "buffer_size":
            size_param = c.get("size_parameter")
            if size_param in inputs:
                inputs[size_param]["value"] = -1 # Invalid size
            else:
                 # If no size param, we might need to corrupt the buffer itself
                 # but for v1.0 we focus on the size param violation
                 pass

        elif c_type == "struct_layout":
            if target in inputs:
                 # Injected layout error
                 inputs[target]["size_override"] = c.get("required_size_bytes", 100) + 1
            else:
                return None

        elif c_type == "null_terminated_string":
            if target in inputs:
                 inputs[target]["value"] = "not_terminated" # Missing \0
            else:
                return None

        else:
            return None # Unsupported for now

        return {
            "test_id": f"test_{f['function_name']}_violate_{cid}",
            "test_category": "negative",
            "priority": "critical" if c_type in ["non_null", "buffer_size"] else "high",
            "function_name": f["function_name"],
            "description": f"Violate constraint {cid} ({c_type}) for {target}",
            "constraints_exercised": [cid],
            "inputs": inputs,
            "expected_outcome": {
                "type": "exception",
                "exception_type": exc_type,
                "constraint_id": cid,
                "message_pattern": c.get("description", "")
            },
            "rationale": f"Verifies that {c_type} protection is active."
        }
