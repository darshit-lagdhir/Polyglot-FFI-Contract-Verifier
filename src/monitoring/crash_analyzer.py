"""
Crash Analyzer
Heuristics for classifying and analyzing native crashes.
"""

from typing import Any, Dict, Optional

class CrashAnalyzer:
    """
    Analyzes crash data to provide human-readable diagnostics.
    """

    def analyze(self, crash_info: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a detailed analysis of the crash.
        """
        c_type = crash_info.get("crash_type", "unknown")
        
        analysis = {
            "is_exploitable": False,
            "severity": "medium",
            "likely_cause": "Unknown native error"
        }

        if c_type == "access_violation" or c_type == "segmentation_fault":
            analysis["severity"] = "critical"
            analysis["is_exploitable"] = True
            analysis["likely_cause"] = "Memory safety violation (e.g., buffer overflow or null dereference)."
            if "expected_outcome" in test_case:
                exp = test_case["expected_outcome"]
                if exp.get("exception_type") == "BufferSizeViolation":
                    analysis["likely_cause"] = "Confirmed Buffer Overflow. Native code crashed instead of being stopped by adapter."
                elif exp.get("exception_type") == "NullPointerViolation":
                    analysis["likely_cause"] = "Confirmed Null Dereference. Native code crashed instead of being stopped by adapter."

        elif c_type == "stack_overflow":
            analysis["severity"] = "high"
            analysis["likely_cause"] = "Infinite recursion or massive stack allocation in native code."

        elif c_type == "illegal_instruction":
            analysis["severity"] = "high"
            analysis["likely_cause"] = "Jump to invalid address, likely due to stack corruption or ABI mismatch."

        return analysis
