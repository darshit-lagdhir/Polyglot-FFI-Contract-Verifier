"""
Coverage Analyzer
Tracks constraint coverage and builds the coverage map.
"""

from typing import Dict, Any, List

class CoverageAnalyzer:
    """
    Computes coverage statistics for a generated test plan.
    """
    
    def analyze_coverage(self, test_cases: List[Dict[str, Any]], contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes which constraints are covered by the test cases.
        """
        all_constraints = self._extract_all_constraints(contract)
        coverage_map = {cid: [] for cid in all_constraints}
        
        for tc in test_cases:
            for cid in tc.get("constraints_exercised", []):
                if cid in coverage_map:
                    coverage_map[cid].append(tc["test_id"])

        covered_count = sum(1 for cid in coverage_map if len(coverage_map[cid]) > 0)
        total_count = len(all_constraints)
        
        uncovered = [cid for cid in coverage_map if len(coverage_map[cid]) == 0]
        
        return {
            "summary": {
                "total_constraints": total_count,
                "covered_constraints": covered_count,
                "uncovered_constraints": len(uncovered),
                "coverage_percentage": (covered_count / total_count * 100.0) if total_count > 0 else 100.0
            },
            "coverage_map": coverage_map,
            "uncovered_constraints": uncovered
        }

    def _extract_all_constraints(self, contract: Dict[str, Any]) -> List[str]:
        """Extracts every unique constraint ID from the contract."""
        ids = set()
        for f in contract.get("function_contracts", []):
            for pc in f.get("pre_conditions", []):
                 ids.add(pc["constraint_id"])
            for pc in f.get("post_conditions", []):
                 ids.add(pc["constraint_id"])
        return sorted(list(ids))
