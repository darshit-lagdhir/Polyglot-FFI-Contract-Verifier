"""
Diagnosis Module

This module handles the analysis of test failures and crashes, generating detailed diagnostic reports.
It provides root cause analysis, risk assessment, and actionable remediation steps.

Consolidates:
- DiagnosticMapper: Main orchestrator
- CrashAnalyzer: Heuristics for native crashes
- FailureClassifier: Categorizes verification failures
- RootCauseAnalyzer: Identifies why failures occurred
- RemediationGenerator: Suggests fixes
- ViolationAggregator: Groups related issues
- DiagnosticReportGenerator: Formats final reports (JSON/Text)

From original implementation: Phase 10 (src/diagnostics/) & partial Phase 9 (src/monitoring/)
"""

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class CrashAnalyzer:
    """
    Heuristics for classifying and analyzing native crashes.
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
                category = "expectation_mismatch"
            else:
                category = "unhandled_exception"
        elif actual_outcome.get("type") == "success":
            failure_mode = "missing_enforcement"
            category = "missing_validation"

        # Determine Constraint
        constraint_id = "unknown"
        constraints_exercised = test_result.get("constraints_exercised", [])
        if constraints_exercised:
            constraint_id = constraints_exercised[0] # Primary constraint

        # Lookup constraint type in contract
        constraint_type = "unknown"
        if contract and "function_contracts" in contract:
             # Assuming standard contract structure here
             for fc in contract["function_contracts"]:
                 if fc["function_name"] == test_result.get("function_name"):
                     # Check pre/post
                     for c in fc.get("pre_conditions", []) + fc.get("post_conditions", []):
                         if c.get("constraint_id") == constraint_id:
                             constraint_type = c.get("constraint_type", "unknown")
                             break
                     if constraint_type != "unknown": break

        severity = self.SEVERITY_MAP.get(constraint_type, "medium")
        if failure_mode == "crash":
            severity = "critical"

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


class RemediationGenerator:
    """
    Generates step-by-step instructions to fix identified FFI issues.
    """

    def generate(self, failure_info: Dict[str, Any], test_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds remediation steps.
        """
        c_type = failure_info.get("constraint_type")
        f_name = test_result.get("function_name")
        c_id = failure_info.get("constraint_id")
        
        short_desc = f"Fix {c_type} validation in {f_name} adapter"
        steps = []

        if c_type == "buffer_size":
            steps = [
                f"1. Open the adapter for {f_name}.",
                f"2. Add a pre-call check to verify buffer length matches the associated size parameter.",
                f"3. Ensure it raises BufferSizeViolation with constraint_id='{c_id}'."
            ]
        elif c_type == "non_null":
            steps = [
                f"1. In function {f_name}, check that all pointers marked non-null are not None.",
                f"2. Raise NullPointerViolation if validation fails."
            ]
        elif c_type == "ownership":
            steps = [
                "1. Implement ownership tracking for this pointer.",
                "2. Ensure the adapter marks the pointer as transferred or invalid after the call."
            ]
        else:
            steps = [
                f"1. Review the contract constraints for {f_name}.",
                "2. Ensure the generated adapter implements all necessary pre-call validations."
            ]

        return {
            "short_description": short_desc,
            "detailed_steps": steps,
            "contract_reference": c_id
        }


class ViolationAggregator:
    """
    Groups related test failures to reduce reporting noise.
    """

    def aggregate(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups violations by constraint_id.
        """
        groups = {}
        
        for v in violations:
            cid = v.get("constraint_id", "unknown")
            if cid not in groups:
                groups[cid] = {
                    "violation_id": f"V-{len(groups)+1:03d}",
                    "constraint_id": cid,
                    "severity": v.get("severity"),
                    "category": v.get("category"),
                    "function_name": v.get("function_name"),
                    "description": v.get("description"),
                    "remediation": v.get("remediation"),
                    "root_cause": v.get("root_cause"),
                    "impact": v.get("impact"),
                    "affected_tests": [],
                    "test_count": 0,
                    "failure_mode": v.get("failure_mode")
                }
            
            groups[cid]["affected_tests"].append(v.get("test_id"))
            groups[cid]["test_count"] += 1
            
            # Upgrade severity if any member is higher
            if v.get("severity") == "critical":
                groups[cid]["severity"] = "critical"
            elif v.get("severity") == "high" and groups[cid]["severity"] != "critical":
                groups[cid]["severity"] = "high"

        # Convert back to sorted list
        sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        result = list(groups.values())
        result.sort(key=lambda x: (sev_rank.get(x["severity"], 9), -x["test_count"]))
        
        return result


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
                "producing_phase": "Phase 10: Diagnostics Mapping",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0"
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


# ============================================================================
# PUBLIC API
# ============================================================================

class DiagnosticMapper:
    """
    Orchestrates the Phase 10 diagnostics pipeline.
    Main entry point for generating diagnostic reports from execution logs.
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
