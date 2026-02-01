"""
Diagnostic Mapper
Main orchestrator for transforming execution logs into semantic diagnostics.
"""

import os
import json
from typing import Any, Dict, List

from .failure_classifier import FailureClassifier
from .root_cause_analyzer import RootCauseAnalyzer
from .remediation_generator import RemediationGenerator
from .violation_aggregator import ViolationAggregator
from .diagnostic_report_generator import DiagnosticReportGenerator

class DiagnosticMapper:
    """
    Orchestrates the 0 diagnostics pipeline.
    """

    def map_diagnostics(self, context: Any) -> Dict[str, Any]:
        """
        Loads artifacts, performs analysis, and saves diagnostics.
        """
        # 1. Load Input Artifacts
        artifacts_dir = os.path.dirname(context.artifacts.contract_path)
        log_path = os.path.join(artifacts_dir, "execution_log.json")
        contract_path = context.artifacts.contract_path
        
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Execution log missing: {log_path}. Run 'execute' first.")
            
        with open(log_path, 'r', encoding='utf-8') as f:
            execution_log = json.load(f)
            
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)

        # 2. Initialize Sub-components
        classifier = FailureClassifier()
        analyzer = RootCauseAnalyzer()
        remediation_gen = RemediationGenerator()
        aggregator = ViolationAggregator()
        report_gen = DiagnosticReportGenerator()

        raw_violations = []
        
        # 3. Process Execution Results
        for result in execution_log.get("test_results", []):
            if result.get("status") == "passed":
                continue
            
            # Classify
            failure_info = classifier.classify_failure(result, contract)
            
            # Analyze
            cause_info = analyzer.analyze(failure_info, result, contract)
            
            # Remediate
            remediation = remediation_gen.generate(failure_info, result)
            
            # Build raw violation record
            violation = {
                "test_id": result["test_id"],
                "function_name": result["function_name"],
                **failure_info,
                **cause_info,
                "remediation": remediation,
                "description": f"Failure detected in {result['function_name']}() violating {failure_info['constraint_id']}"
            }
            raw_violations.append(violation)

        # 4. Aggregate
        aggregated = aggregator.aggregate(raw_violations)
        
        # 5. Compute Stats
        total_tests = len(execution_log.get("test_results", []))
        passed_tests = sum(1 for r in execution_log.get("test_results", []) if r.get("status") == "passed")
        
        stats = {
            "total_violations": len(raw_violations),
            "aggregated_violations": len(aggregated),
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "severity_counts": self._count_severities(aggregated)
        }

        # 6. Generate Reports
        report_json = report_gen.generate_json(context, aggregated, stats)
        summary_text = report_gen.generate_summary_text(report_json)

        # 7. Save Artifacts
        diag_path = os.path.join(artifacts_dir, "diagnostics.json")
        with open(diag_path, 'w', encoding='utf-8') as f:
            json.dump(report_json, f, indent=2)
            
        summary_path = os.path.join(artifacts_dir, "violation_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        return report_json

    def _count_severities(self, aggregated: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in aggregated:
            sev = v.get("severity", "medium").lower()
            if sev in counts:
                counts[sev] += 1
        return counts
