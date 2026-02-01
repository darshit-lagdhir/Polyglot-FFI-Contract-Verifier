"""
Crash Detector
Monitors subprocess execution and detects native crashes.
"""

import subprocess
import sys
import os
import json
import time
from typing import Any, Dict, Optional

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
            "-m", "src.monitoring.subprocess_test_executor",
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
            # subprocess.run returncode is -signal if terminated by signal
            if exit_code < 0:
                crash_type = self.LINUX_SIGNALS.get(abs(exit_code), "unknown")
        
        if crash_type != "unknown" or unsigned_code in self.WINDOWS_EXCEPTIONS:
            return {
                "crash_type": crash_type,
                "exit_code": exit_code,
                "exception_code": hex(unsigned_code) if os.name == 'nt' else None,
                "signal": abs(exit_code) if os.name != 'nt' and exit_code < 0 else None
            }
        
        # Heuristic search in stderr for common crash strings (SIGSEGV, etc)
        if "Segmentation fault" in stderr or "SIGSEGV" in stderr:
            return {"crash_type": "segmentation_fault", "exit_code": exit_code}
        
        return None
