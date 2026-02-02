"""
Execution Module

This module handles the execution of FFI tests, including:
- Input instantiation from test plans
- Sandbox/Subprocess execution for crash isolation
- Outcome validation against contracts
- Execution logging and summary generation

Consolidates:
- VerificationExecutor: Main orchestrator
- CrashDetector: Monitors native crashes
- InputInstantiator: Creates ctypes objects
- OutcomeValidator: Checks results
- ExecutionLogger: Builds logs
- ExecutionSummaryGenerator: Report helper

From original implementation:  (src/verification/) &  (src/monitoring/)
"""

import os
import json
import sys
import time
import ctypes
import subprocess
import traceback
import importlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class InputInstantiator:
    """
    Transforms JSON-based values into ctypes instances for FFI calls.
    """
    
    PRIMITIVE_MAP = {
        "primitive:int8": ctypes.c_int8,
        "primitive:int16": ctypes.c_int16,
        "primitive:int32": ctypes.c_int32,
        "primitive:int64": ctypes.c_int64,
        "primitive:uint8": ctypes.c_uint8,
        "primitive:uint16": ctypes.c_uint16,
        "primitive:uint32": ctypes.c_uint32,
        "primitive:uint64": ctypes.c_uint64,
        "primitive:float": ctypes.c_float,
        "primitive:double": ctypes.c_double,
        "primitive:char": ctypes.c_char,
        "primitive:bool": ctypes.c_bool,
        "primitive:void": None
    }

    def __init__(self, lib_name: str):
        self.lib_name = lib_name
        self.structs_module = None
        
        # Add adapters dir to path for imports
        adapters_path = os.path.abspath("adapters")
        if adapters_path not in sys.path:
            sys.path.append(adapters_path)
            
        try:
            self.structs_module = __import__(f"{lib_name}_structs")
        except ImportError:
            pass

    def instantiate(self, spec: Dict[str, Any]) -> Any:
        """Main entry point for instantiation."""
        t_id = spec["type"]
        val = spec.get("value")
        
        if val is None:
            return None

        # Handle Primitives
        if t_id in self.PRIMITIVE_MAP:
            if t_id == "primitive:char" and isinstance(val, str):
                return self.PRIMITIVE_MAP[t_id](val.encode('ascii')[0])
            return self.PRIMITIVE_MAP[t_id](val)

        # Handle Pointers
        if t_id.startswith("pointer:"):
            base_type = t_id.replace("pointer:", "")
            
            # String special case
            if base_type == "primitive:char" and isinstance(val, str):
                return ctypes.c_char_p(val.encode('ascii'))
            
            # Buffer special case
            if isinstance(val, list):
                # Currently only supporting uint8 buffers in test plans
                arr_type = ctypes.c_uint8 * len(val)
                arr = arr_type(*val)
                return ctypes.cast(arr, ctypes.POINTER(ctypes.c_uint8))
                
            # Struct Pointer
            if base_type.startswith("struct:"):
                struct_name = base_type.split(":")[-1]
                struct_obj = self.instantiate_struct(struct_name, val)
                return ctypes.pointer(struct_obj)

        # Handle Structs (inline)
        if t_id.startswith("struct:"):
            struct_name = t_id.split(":")[-1]
            return self.instantiate_struct(struct_name, val)

        return val

    def instantiate_struct(self, name: str, value_dict: Dict[str, Any]) -> Any:
        """Instantiates a ctypes Structure from a dictionary."""
        if not self.structs_module:
             raise ImportError(f"Could not load structs module for {self.lib_name}")
             
        struct_class = getattr(self.structs_module, name)
        return struct_class(**value_dict)

class OutcomeValidator:
    """
    Validates if a test execution passed or failed based on contract rules.
    """

    def validate(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates the outcome.
        Returns (success, reason).
        """
        exp_type = expected["type"]
        act_type = actual["type"]

        if exp_type == "success":
            if act_type == "success":
                # For v1.0, we don't strictly validate return values unless specified
                return True, ""
            elif act_type == "exception":
                return False, f"Expected success, but got exception: {actual.get('exception_type')}"
            elif act_type == "crash":
                 return False, f"Expected success, but native library crashed"
            
        elif exp_type == "exception":
            if act_type == "exception":
                # Validate exception type
                exp_exc = expected.get("exception_type")
                act_exc = actual.get("exception_type")
                if exp_exc and exp_exc != act_exc:
                    return False, f"Expected exception {exp_exc}, but got {act_exc}"
                
                # Validate constraint ID
                exp_cid = expected.get("constraint_id")
                act_cid = actual.get("constraint_id")
                if exp_cid and exp_cid != act_cid:
                    return False, f"Expected violation of {exp_cid}, but got {act_cid}"
                
                return True, ""
            elif act_type == "success":
                return False, "Expected contract violation exception, but function succeeded"
            elif act_type == "crash":
                 return False, "Expected contract violation exception, but native library crashed"

        return False, f"Unknown outcome state: expected {exp_type}, got {act_type}"

class CrashDetector:
    """
    Spawns and monitors test execution subprocesses.
    """
    
    # Windows Exception Codes
    WINDOWS_EXCEPTIONS = {
        0xC0000005: "access_violation",
        0xC0000094: "integer_divide_by_zero",
        0xC00000FD: "stack_overflow",
        0xC000001D: "illegal_instruction",
        0xC0000008: "invalid_handle",
        0xC0000409: "stack_buffer_overrun",
        0x80000003: "breakpoint",
    }
    
    # Linux Signals
    LINUX_SIGNALS = {
        4: "illegal_instruction",   # SIGILL
        6: "abort",                 # SIGABRT
        8: "floating_point_error",  # SIGFPE
        11: "segmentation_fault",   # SIGSEGV
        7: "bus_error",             # SIGBUS
    }

    def execute_test(self, test_case: Dict[str, Any], context: Any, timeout: int = 60) -> Dict[str, Any]:
        """
        Executes a test case in a child process and detects if it crashes.
        """
        lib_name = os.path.splitext(os.path.basename(context.native_library.library_path))[0]
        adapter_module_name = f"{lib_name}_adapter"
        
        # Prepare command
        cmd = [
            sys.executable,
            "-m", "polyglot_ffi_verifier.subprocess_runner",
            json.dumps(test_case),
            lib_name,
            adapter_module_name
        ]
        
        start_time = time.time()
        try:
            # We use subprocess.run with a timeout
            # We capture stdout/stderr to find the RESULT tags or crash info
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # 1. Check for Crash (Non-zero exit code usually, or specific codes)
            if proc.returncode != 0:
                crash_info = self._analyze_termination(proc.returncode, proc.stderr)
                if crash_info:
                    return {
                        "status": "crashed",
                        "crash_detected": True,
                        "crash_info": crash_info,
                        "actual_outcome": {"type": "crash", "crash_type": crash_info["crash_type"]},
                        "duration_ms": duration_ms,
                        "exit_code": proc.returncode,
                        "stderr": proc.stderr
                    }

            # 2. Parse Result from Stdout
            stdout = proc.stdout
            if "---RESULT_START---" in stdout:
                try:
                    res_json = stdout.split("---RESULT_START---")[1].split("---RESULT_END---")[0].strip()
                    actual_outcome = json.loads(res_json)
                    
                    # Promote Access Violation OSErrors (Windows feature) to Crash
                    if actual_outcome.get("type") == "exception" and "access violation" in actual_outcome.get("exception_message", "").lower():
                        crash_info = {
                            "crash_type": "access_violation",
                            "exit_code": 0, # It exited cleanly because Python caught it
                            "stderr": proc.stderr,
                            "is_translated_exception": True
                        }
                        return {
                            "status": "crashed",
                            "crash_detected": True,
                            "crash_info": crash_info,
                            "actual_outcome": {"type": "crash", "crash_type": "access_violation"},
                            "duration_ms": duration_ms
                        }
                        
                    return {
                        "status": "completed",
                        "actual_outcome": actual_outcome,
                        "duration_ms": duration_ms,
                        "stdout": stdout,
                        "stderr": proc.stderr
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "failure_reason": f"Failed to parse subprocess output: {str(e)}",
                        "stdout": stdout
                    }

            return {
                "status": "error",
                "failure_reason": "Subprocess terminated without producing a result and no crash was classified.",
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": proc.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "failure_reason": f"Test timed out after {timeout} seconds",
                "duration_ms": timeout * 1000
            }
        except Exception as e:
            return {
                "status": "error",
                "failure_reason": f"Failed to launch subprocess: {str(e)}"
            }

    def _analyze_termination(self, exit_code: int, stderr: str) -> Optional[Dict[str, Any]]:
        """
        Interprets exit codes as crash types.
        """
        # Handle unsigned Windows exit codes (which Python might see as signed)
        unsigned_code = exit_code & 0xFFFFFFFF
        
        crash_type = "unknown"
        if os.name == 'nt':
            crash_type = self.WINDOWS_EXCEPTIONS.get(unsigned_code, "unknown")
        else:
            # On Linux, exit code is usually signal + 128 or just signal
            if exit_code < 0:
                crash_type = self.LINUX_SIGNALS.get(abs(exit_code), "unknown")
        
        if crash_type != "unknown" or unsigned_code in self.WINDOWS_EXCEPTIONS:
            return {
                "crash_type": crash_type,
                "exit_code": exit_code,
                "exception_code": hex(unsigned_code) if os.name == 'nt' else None,
                "signal": abs(exit_code) if os.name != 'nt' and exit_code < 0 else None
            }
        
        if "Segmentation fault" in stderr or "SIGSEGV" in stderr:
            return {"crash_type": "segmentation_fault", "exit_code": exit_code}
        
        return None

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

class ExecutionSummaryGenerator:
    """
    Formats test results for human review.
    """

    def generate(self, log: Dict[str, Any]) -> str:
        """
        Generates the text summary report.
        """
        summary = log["execution_summary"]
        
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
                
        lines.append("================================================================")
        return "\n".join(lines)

# ============================================================================
# PUBLIC API
# ============================================================================

class VerificationExecutor:
    """
    Orchestrates the verification process.
    Uses subprocess isolation for robust crash detection.
    """

    def execute(self, context) -> Dict[str, Any]:
        """
        Executes the full verification cycle.
        """
        # 1. Load Artefacts
        plan_path = os.path.join(os.path.dirname(context.artifacts.contract_path), "test_plan.json")
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Test plan missing: {plan_path}. Run 'generate-tests' first.")
            
        with open(plan_path, 'r') as f:
            test_plan = json.load(f)
            
        # 2. Setup Components
        detector = CrashDetector()
        validator = OutcomeValidator()
        logger = ExecutionLogger()
        summary_gen = ExecutionSummaryGenerator()
        
        test_results = []
        artifacts_dir = os.path.dirname(context.artifacts.contract_path)
        
        # 3. Execute Tests (Serial)
        for test_case in test_plan.get("test_cases", []):
            start_ts = time.time()
            
            # Use CrashDetector to run safely in subprocess
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
                log_entry["failure_reason"] = f"Native crash detected: {result['crash_info']['crash_type']}"
                log_entry["violation_detected"] = False
            
            elif result["status"] == "completed":
                actual_outcome = result["actual_outcome"]
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
            
        # 4. Finalize
        log = logger.build_log(context, test_results, test_plan)
        
        # 5. Save Artifacts
        log_path = os.path.join(artifacts_dir, "execution_log.json")
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)
            
        summary = summary_gen.generate(log)
        summary_path = os.path.join(artifacts_dir, "execution_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        return log
