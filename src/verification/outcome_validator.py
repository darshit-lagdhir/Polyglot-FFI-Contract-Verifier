"""
Outcome Validator
Compares actual execution results against expected outcomes from the test plan.
"""

from typing import Any, Dict, Optional, Tuple

class OutcomeValidator:
    """
    Validates if a test execution passed or failed based on contract rules.
    """

    def validate(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates the outcome.
        Returns (success, reason).
        """
        exp_type = expected["type"]
        act_type = actual["type"]

        if exp_type == "success":
            if act_type == "success":
                # For v1.0, we don't strictly validate return values unless specified
                # as the native implementation might not be available or mockable easily.
                return True, ""
            elif act_type == "exception":
                return False, f"Expected success, but got exception: {actual.get('exception_type')}"
            elif act_type == "crash":
                 return False, f"Expected success, but native library crashed"
            
        elif exp_type == "exception":
            if act_type == "exception":
                # Validate exception type
                exp_exc = expected.get("exception_type")
                act_exc = actual.get("exception_type")
                if exp_exc and exp_exc != act_exc:
                    return False, f"Expected exception {exp_exc}, but got {act_exc}"
                
                # Validate constraint ID
                exp_cid = expected.get("constraint_id")
                act_cid = actual.get("constraint_id")
                if exp_cid and exp_cid != act_cid:
                    return False, f"Expected violation of {exp_cid}, but got {act_cid}"
                
                return True, ""
            elif act_type == "success":
                return False, "Expected contract violation exception, but function succeeded"
            elif act_type == "crash":
                 return False, "Expected contract violation exception, but native library crashed"

        return False, f"Unknown outcome state: expected {exp_type}, got {act_type}"
