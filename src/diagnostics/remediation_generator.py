"""
Remediation Generator
Produces actionable fix recommendations for contract violations.
"""

from typing import Any, Dict, List

class RemediationGenerator:
    """
    Generates step-by-step instructions to fix identified FFI issues.
    """

    def generate(self, failure_info: Dict[str, Any], test_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds remediation steps.
        """
        c_type = failure_info.get("constraint_type")
        f_name = test_result.get("function_name")
        c_id = failure_info.get("constraint_id")
        
        short_desc = f"Fix {c_type} validation in {f_name} adapter"
        steps = []

        if c_type == "buffer_size":
            steps = [
                f"1. Open the adapter for {f_name}.",
                f"2. Add a pre-call check to verify buffer length matches the associated size parameter.",
                f"3. Ensure it raises BufferSizeViolation with constraint_id='{c_id}'."
            ]
        elif c_type == "non_null":
            steps = [
                f"1. In function {f_name}, check that all pointers marked non-null are not None.",
                f"2. Raise NullPointerViolation if validation fails."
            ]
        elif c_type == "ownership":
            steps = [
                "1. Implement ownership tracking for this pointer.",
                "2. Ensure the adapter marks the pointer as transferred or invalid after the call."
            ]
        else:
            steps = [
                f"1. Review the contract constraints for {f_name}.",
                "2. Ensure the generated adapter implements all necessary pre-call validations."
            ]

        return {
            "short_description": short_desc,
            "detailed_steps": steps,
            "contract_reference": c_id
        }
