"""
Diagnostic Report Generator
Produces JSON and text artifacts for verification results.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

class DiagnosticReportGenerator:
    """
    Generates the final diagnostics artifacts.
    """

    def generate_json(self, context: Any, aggregated_violations: List[Dict[str, Any]], stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the diagnostics.json structure.
        """
        return {
            "provenance": {
                "producing_phase": "0: Diagnostics Mapping",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": context.provenance.tool_version
            },
            "summary": stats,
            "violations": aggregated_violations
        }

    def generate_summary_text(self, report_json: Dict[str, Any]) -> str:
        """
        Builds the human-readable violation_summary.txt.
        """
        stats = report_json["summary"]
        violations = report_json["violations"]
        
        lines = []
        lines.append("="*64)
        lines.append("FFI Contract Verification - Violation Summary")
        lines.append("="*64)
        lines.append(f"Execution ID: {report_json['provenance']['execution_id']}")
        lines.append(f"Pass Rate: {stats.get('pass_rate', 0):.1f}%")
        lines.append("")
        
        lines.append("VIOLATIONS BY SEVERITY")
        lines.append(f"  Critical: {stats.get('severity_counts', {}).get('critical', 0)}")
        lines.append(f"  High:     {stats.get('severity_counts', {}).get('high', 0)}")
        lines.append(f"  Total:    {len(violations)} Aggregated Issues")
        lines.append("")

        if not violations:
            lines.append("✓ NO CONTRACT VIOLATIONS DETECTED")
        else:
            for v in violations:
                lines.append(f"[{v['violation_id']}] {v['severity'].upper()}: {v['category']} in {v['function_name']}()")
                lines.append(f"  Constraint: {v['constraint_id']}")
                lines.append(f"  Root Cause: {v['root_cause']}")
                lines.append(f"  Impact:     {v['impact']}")
                lines.append(f"  Remediation: {v['remediation']['short_description']}")
                for step in v['remediation']['detailed_steps']:
                    lines.append(f"    {step}")
                lines.append("")

        return "\n".join(lines)
