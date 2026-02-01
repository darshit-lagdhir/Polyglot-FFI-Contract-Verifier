"""
CI Status Checker
Validates verification outcomes against failure policies.
"""

from typing import Dict, Any

class CIStatusChecker:
    """
    Determines if a verification run should be considered a failure in CI.
    """

    def check_status(self, summary: Dict[str, Any], policy: Dict[str, Any]) -> int:
        if self.should_fail(summary, policy):
            return 1
        return 0

    def should_fail(self, summary: Dict[str, Any], policy: Dict[str, Any]) -> bool:
        v_summary = summary.get('summary', {})
        status = summary.get('verification_status')
        critical = v_summary.get('critical_violations', 0)
        total_violations = v_summary.get('total_violations', 0)
        
        if policy.get('strict_mode', False) and total_violations > 0:
            return True
            
        if policy.get('block_on_critical', True) and critical > 0:
            return True
            
        max_v = policy.get('max_violations', 10)
        if total_violations > max_v:
            return True
            
        return False

    def print_ci_summary(self, summary: Dict[str, Any]) -> None:
        v_summary = summary.get('summary', {})
        status = summary.get('verification_status', 'UNKNOWN').upper()
        
        print("=" * 60)
        print(f"FFI CONTRACT VERIFICATION SUMMARY: {status}")
        print("=" * 60)
        print(f"Tests: {v_summary.get('passed_tests', 0)}/{v_summary.get('total_tests', 0)} passed ({v_summary.get('pass_rate', 0):.1f}%)")
        print(f"Violations:")
        print(f"  Critical: {v_summary.get('critical_violations', 0)}")
        print(f"  High:     {v_summary.get('high_severity_violations', 0)}")
        print(f"  Total:    {v_summary.get('total_violations', 0)}")
        print("=" * 60)
