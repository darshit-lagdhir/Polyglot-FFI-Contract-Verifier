"""
Execution Summary Generator
Produces human-readable reports from the execution log.
"""

from typing import Any, Dict

class ExecutionSummaryGenerator:
    """
    Formats test results for human review.
    """

    def generate(self, log: Dict[str, Any]) -> str:
        """
        Generates the text summary report.
        """
        summary = log["execution_summary"]
        meta = log["execution_metadata"]
        
        lines = [
            "================================================================",
            "FFI Contract Verification Execution Summary",
            "================================================================",
            f"Execution ID: {log['provenance']['execution_id']}",
            f"Timestamp   : {log['provenance']['timestamp']}",
            f"Result      : {'PASS' if summary['tests_failed'] == 0 else 'FAIL'}",
            "",
            "OVERALL RESULTS",
            "----------------",
            f"Total Tests      : {summary['total_tests']}",
            f"Passed           : {summary['tests_passed']}",
            f"Failed           : {summary['tests_failed']}",
            f"Pass Rate        : {summary['pass_rate_percentage']:.2f}%",
            f"Constraints Verified: {summary['constraints_verified']}",
            "",
            "DETAILED RESULTS",
            "----------------"
        ]

        for result in log["test_results"]:
            mark = "✓" if result["status"] == "passed" else "✗"
            line = f"{mark} {result['test_id']} ({result.get('duration_ms', 0):.2f}ms)"
            lines.append(line)
            if result["status"] == "failed":
                lines.append(f"  Reason: {result.get('failure_reason', 'Unknown error')}")

        lines.append("")
        lines.append("RECOMMENDATIONS")
        lines.append("---------------")
        if summary["tests_failed"] > 0:
            lines.append("1. Critical failures detected. Review execution_log.json for details.")
            lines.append("2. Verify native implementation matches contract expectations.")
        else:
            lines.append("1. All contract tests passed.")
            lines.append("2. Consider adding more boundary cases to the contract if applicable.")
            
        lines.append("================================================================")
        
        return "\n".join(lines)
