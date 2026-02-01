"""
CI Summary Generator
Produces machine-readable JSON summaries for CI/CD integration.
"""

from typing import Any, Dict, List

class CISummaryGenerator:
    """
    Generates CI-friendly JSON data including exit codes and status badges.
    """

    def generate(self, diagnostics: Dict[str, Any], execution_log: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ci_summary.json structure.
        """
        summary = diagnostics.get("summary", {})
        violations = diagnostics.get("violations", [])
        
        test_results = execution_log.get("test_results", [])
        passed_count = sum(1 for r in test_results if r.get("status") == "passed")
        failed_count = len(test_results) - passed_count
        
        has_critical = summary.get("severity_counts", {}).get("critical", 0) > 0
        status = "failed" if has_critical else "passed"
        exit_code = 1 if has_critical else 0
        
        badge = self._generate_status_badge(status, summary)
        blocking_issues = self._extract_blocking_issues(violations)
        
        return {
            "provenance": {
                "producing_phase": "1: Report Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": context.provenance.creation_timestamp,
                "tool_version": context.provenance.tool_version
            },
            "verification_status": status,
            "summary": {
                "total_tests": len(test_results),
                "passed_tests": passed_count,
                "failed_tests": failed_count,
                "pass_rate": summary.get("pass_rate", 0),
                "total_violations": len(violations),
                "critical_violations": summary.get("severity_counts", {}).get("critical", 0),
                "high_severity_violations": summary.get("severity_counts", {}).get("high", 0),
                "medium_severity_violations": summary.get("severity_counts", {}).get("medium", 0),
                "low_severity_violations": summary.get("severity_counts", {}).get("low", 0)
            },
            "status_badge": badge,
            "exit_code": exit_code,
            "blocking_issues": blocking_issues,
            "reports": {
                "html": "reports/verification_report.html",
                "markdown": "reports/verification_report.md",
                "diagnostics": "artifacts/diagnostics.json"
            }
        }

    def _generate_status_badge(self, status: str, summary: Dict[str, Any]) -> Dict[str, str]:
        critical = summary.get("severity_counts", {}).get("critical", 0)
        
        if status == "failed":
            message = f"FAILED ({critical} critical)"
            color = "red"
        else:
            message = "PASSED"
            color = "green"
            
        return {
            "label": "FFI Verification",
            "message": message,
            "color": color
        }

    def _extract_blocking_issues(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        blocking = []
        for v in violations:
            if v.get("severity") == "critical":
                blocking.append({
                    "violation_id": v.get("violation_id"),
                    "severity": "critical",
                    "function": v.get("function_name"),
                    "description": v.get("description", "Critical contract violation")
                })
        return blocking
