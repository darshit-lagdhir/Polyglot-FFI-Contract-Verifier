"""
Violation Aggregator
Groups related test failures to reduce reporting noise.
"""

from typing import Any, Dict, List

class ViolationAggregator:
    """
    Groups individual test failures by the underlying contract constraint.
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
