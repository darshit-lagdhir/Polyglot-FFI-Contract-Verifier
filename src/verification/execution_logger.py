"""
Execution Logger
Compiles test results into the final execution log.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

class ExecutionLogger:
    """
    Builds the immutable execution log artifact.
    """

    def build_log(self, context, results: List[Dict[str, Any]], test_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates the full log structure.
        """
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = len(results) - passed
        
        # Analyze constraint verification
        # We look at which constraints had at least one successful negative test
        constraints_verified = set()
        for r in results:
            if r["status"] == "passed" and r["test_category"] == "negative":
                cid = r["actual_outcome"].get("constraint_id")
                if cid:
                    constraints_verified.add(cid)

        summary = {
            "total_tests": len(results),
            "tests_passed": passed,
            "tests_failed": failed,
            "pass_rate_percentage": (passed / len(results) * 100.0) if results else 0,
            "constraints_verified": len(constraints_verified),
            "violations_detected": sum(1 for r in results if r.get("actual_outcome", {}).get("type") == "exception")
        }

        # Provenance
        provenance = {
            "producing_phase": ": Verification Execution",
            "execution_id": context.provenance.execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_version": "1.0.0",
            "schema_version": "1.0.0",
        }

        return {
            "provenance": provenance,
            "execution_metadata": {
                "execution_start_time": datetime.fromtimestamp(results[0]["execution_start_time"], tz=timezone.utc).isoformat() if results else "",
                "execution_end_time": datetime.now(timezone.utc).isoformat(),
                "platform": {
                    "os_name": context.platform.os_name,
                    "architecture": context.platform.architecture,
                    "python_version": f"{context.target_runtime.language_version}"
                }
            },
            "execution_summary": summary,
            "test_results": results
        }
