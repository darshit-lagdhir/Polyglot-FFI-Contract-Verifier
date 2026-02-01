"""
Crash Report Generator
Produces detailed JSON reports for each crash.
"""

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict

class CrashReportGenerator:
    """
    Generates and saves persistent reports for native failures.
    """

    def generate_report(self, context: Any, test_case: Dict[str, Any], crash_info: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the report structure.
        """
        return {
            "provenance": {
                "producing_phase": "Phase 9: Runtime Monitoring",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_id": test_case["test_id"]
            },
            "crash_summary": {
                "crash_type": crash_info.get("crash_type"),
                "severity": analysis.get("severity"),
                "is_exploitable": analysis.get("is_exploitable"),
                "exit_code": crash_info.get("exit_code"),
                "exception_code": crash_info.get("exception_code")
            },
            "test_context": {
                "function_name": test_case["function_name"],
                "inputs": test_case["inputs"],
                "expected_outcome": test_case["expected_outcome"]
            },
            "analysis": analysis
        }

    def save_report(self, report: Dict[str, Any], artifacts_dir: str):
        """Saves the report to the crashes directory."""
        crashes_dir = os.path.join(artifacts_dir, "crashes")
        os.makedirs(crashes_dir, exist_ok=True)
        
        filename = f"crash_{report['provenance']['test_id']}_{int(datetime.now().timestamp())}.json"
        filepath = os.path.join(crashes_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        return filepath
