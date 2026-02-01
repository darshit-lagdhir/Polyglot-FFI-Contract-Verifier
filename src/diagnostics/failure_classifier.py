"""
Failure Classifier
Categorizes test failures by type, severity, and contract constraint.
"""

from typing import Any, Dict, List, Optional

class FailureClassifier:
    """
    Classifies verification failures according to contract semantics.
    """

    SEVERITY_MAP = {
        "buffer_size": "critical",
        "non_null": "high",
        "ownership": "critical",
        "type_alignment": "medium",
        "custom": "medium",
        "unknown": "low"
    }

    def classify_failure(self, test_result: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies a single test failure.
        """
        status = test_result.get("status", "unknown")
        actual_outcome = test_result.get("actual_outcome", {})
        expected_outcome = test_result.get("expected_outcome", {})
        
        failure_mode = "unknown"
        category = "unknown"
        
        if test_result.get("crash_detected"):
            failure_mode = "crash"
            crash_type = test_result.get("crash_info", {}).get("crash_type", "unknown")
            category = self._map_crash_to_category(crash_type)
        elif actual_outcome.get("type") == "timeout":
            failure_mode = "timeout"
            category = "performance_or_deadlock"
        elif actual_outcome.get("type") == "exception":
            failure_mode = "exception"
            # Analyze if it's the RIGHT exception
            if actual_outcome.get("exception_type") == expected_outcome.get("exception_type"):
                # If we expected an exception and got it, why is it "failed" in the log
                # Usually  marks this as passed. If it's failed, maybe constraint ID mismatch.
                category = "expectation_mismatch"
            else:
                category = "unhandled_exception"
        elif actual_outcome.get("type") == "success":
            # Expected exception but got success
            failure_mode = "missing_enforcement"
            category = "missing_validation"

        # Determine Constraint
        constraint_id = "unknown"
        constraints_exercised = test_result.get("constraints_exercised", [])
        if constraints_exercised:
            constraint_id = constraints_exercised[0] # Primary constraint

        # Lookup constraint type in contract
        constraint_type = "unknown"
        if contract and "functions" in contract:
            for func_name, func_spec in contract["functions"].items():
                if func_name == test_result.get("function_name"):
                    for constraint in func_spec.get("constraints", []):
                        if constraint.get("id") == constraint_id:
                            constraint_type = constraint.get("type", "unknown")
                            break

        severity = self.SEVERITY_MAP.get(constraint_type, "medium")
        if failure_mode == "crash":
            severity = "critical" # Crashes are always severe in FFI

        return {
            "failure_mode": failure_mode,
            "category": category,
            "constraint_id": constraint_id,
            "constraint_type": constraint_type,
            "severity": severity,
            "exploitability": "high" if severity == "critical" else "low",
            "impact": self._determine_impact(category, severity)
        }

    def _map_crash_to_category(self, crash_type: str) -> str:
        mapping = {
            "access_violation": "buffer_overflow_or_invalid_ptr",
            "segmentation_fault": "buffer_overflow_or_invalid_ptr",
            "stack_overflow": "stack_exhaustion",
            "illegal_instruction": "control_flow_corruption",
            "abort": "native_assertion_failure"
        }
        return mapping.get(crash_type, "native_crash")

    def _determine_impact(self, category: str, severity: str) -> str:
        if severity == "critical":
            return "Potential arbitrary code execution or memory corruption."
        if category == "null_pointer_dereference":
            return "Application crash (Denial of Service)."
        if category == "missing_validation":
            return "Native code exposed to invalid inputs; may lead to undefined behavior."
        return "Unexpected execution behavior violating contract expectations."
