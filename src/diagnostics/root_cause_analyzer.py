"""
Root Cause Analyzer
Determines why failures occurred based on symptoms and contract intent.
"""

from typing import Any, Dict

class RootCauseAnalyzer:
    """
    Analyzes failures to identify missing enforcement or native bugs.
    """

    def analyze(self, failure_info: Dict[str, Any], test_result: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines the root cause of a failure.
        """
        f_mode = failure_info.get("failure_mode")
        c_type = failure_info.get("constraint_type")
        
        root_cause = "Unknown"
        explanation = "Insufficient data to determine root cause."

        if f_mode == "crash":
            root_cause = "Adapter Missing Enforcement"
            explanation = f"Native library crashed on a {c_type} violation because the adapter failed to interpose and reject the invalid input."
        
        elif f_mode == "missing_enforcement":
            root_cause = "Adapter Missing Pre-call Check"
            explanation = f"The test expected a {c_type} violation to be caught by the adapter, but the call was allowed to proceed to native code."

        elif f_mode == "exception" and failure_info.get("category") == "unhandled_exception":
            root_cause = "Unexpected Exception Type"
            explanation = "Adapter raised an exception, but it didn't match the specific contract violation class expected."

        elif f_mode == "timeout":
            root_cause = "Native Deadlock or Infinite Loop"
            explanation = "Native code failed to return within the allocated time window when provided with test inputs."

        return {
            "root_cause": root_cause,
            "explanation": explanation
        }
