"""
Monitored Verification Executor
Orchestrates test execution with crash detection.
"""

import os
import json
import time
from typing import Any, Dict, List

from src.monitoring.crash_detector import CrashDetector
from src.monitoring.crash_analyzer import CrashAnalyzer
from src.monitoring.crash_report_generator import CrashReportGenerator
from src.verification.execution_logger import ExecutionLogger
from src.verification.execution_summary_generator import ExecutionSummaryGenerator
from src.verification.outcome_validator import OutcomeValidator

class MonitoredVerificationExecutor:
    """
    Enhanced executor using subprocess isolation and crash monitoring.
    """

    def execute(self, context) -> Dict[str, Any]:
        """
        Executes tests with monitoring.
        """
        # 1. Load Test Plan
        plan_path = os.path.join(os.path.dirname(context.artifacts.contract_path), "test_plan.json")
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Test plan missing. Run 'generate-tests' first.")
            
        with open(plan_path, 'r', encoding='utf-8') as f:
            test_plan = json.load(f)

        # 2. Init Components
        detector = CrashDetector()
        analyzer = CrashAnalyzer()
        report_gen = CrashReportGenerator()
        validator = OutcomeValidator()
        logger = ExecutionLogger()
        summary_gen = ExecutionSummaryGenerator()
        
        test_results = []
        artifacts_dir = os.path.dirname(context.artifacts.contract_path)
        
        # 3. Serial Execution Loop
        for test_case in test_plan.get("test_cases", []):
            # Run in subprocess
            start_ts = time.time()
            result = detector.execute_test(test_case, context, timeout=context.verification_config.per_test_timeout_seconds)
            end_ts = time.time()
            
            # Map result to execution log format
            log_entry = {
                "test_id": test_case["test_id"],
                "test_category": test_case["test_category"],
                "function_name": test_case["function_name"],
                "execution_start_time": start_ts,
                "execution_end_time": end_ts,
                "duration_ms": result.get("duration_ms", 0),
                "constraints_exercised": test_case.get("constraints_exercised", []),
                "expected_outcome": test_case["expected_outcome"]
            }
            
            if result["status"] == "crashed":
                log_entry["status"] = "failed"
                log_entry["crash_detected"] = True
                log_entry["crash_info"] = result["crash_info"]
                log_entry["actual_outcome"] = result["actual_outcome"]
                
                # Analyze and generate report
                analysis = analyzer.analyze(result["crash_info"], test_case)
                report = report_gen.generate_report(context, test_case, result["crash_info"], analysis)
                report_gen.save_report(report, artifacts_dir)
                
                log_entry["failure_reason"] = f"Native crash detected: {result['crash_info']['crash_type']}"
                log_entry["violation_detected"] = False # Crash bypassed enforcement
            
            elif result["status"] == "completed":
                actual_outcome = result["actual_outcome"]
                # Validate outcome (since validator is  logic, we reuse it)
                success, reason = validator.validate(test_case["expected_outcome"], actual_outcome)
                
                log_entry["status"] = "passed" if success else "failed"
                log_entry["actual_outcome"] = actual_outcome
                if not success:
                    log_entry["failure_reason"] = reason
            
            elif result["status"] == "timeout":
                log_entry["status"] = "failed"
                log_entry["failure_reason"] = result["failure_reason"]
                log_entry["actual_outcome"] = {"type": "timeout"}
            
            else:
                log_entry["status"] = "failed"
                log_entry["failure_reason"] = result.get("failure_reason", "Unknown execution error")
                log_entry["actual_outcome"] = {"type": "error"}

            test_results.append(log_entry)

        # 4. Finalize Log and Summary
        log = logger.build_log(context, test_results, test_plan)
        
        # Save Artifacts
        log_path = os.path.join(artifacts_dir, "execution_log.json")
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)
            
        summary = summary_gen.generate(log)
        summary_path = os.path.join(artifacts_dir, "execution_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        return log
