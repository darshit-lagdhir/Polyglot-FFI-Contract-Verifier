"""
Compatibility Report Generator
Produces human-readable text reports summarizing FFI contract evolution and risks.
"""

from typing import Dict, Any, List

class CompatibilityReportGenerator:
    """
    Transforms a change diff into a professional compatibility assessment report.
    """
    
    def generate_report(self, diff: Dict[str, Any]) -> str:
        """Generates the full plain-text report."""
        summary = diff.get("summary", {})
        changes = diff.get("changes", [])
        schema = diff.get("schema_compatibility", {})
        
        lines = []
        lines.append("=" * 64)
        lines.append("FFI Contract Compatibility Assessment")
        lines.append("=" * 64)
        lines.append("")
        lines.append(f"Current Contract:  {diff['provenance'].get('current_contract')}")
        lines.append(f"Baseline Contract: {diff['provenance'].get('baseline_contract') or 'NONE'}")
        lines.append("")
        lines.append("Schema Versions:")
        lines.append(f"  Baseline: {schema.get('baseline_schema_version')}")
        lines.append(f"  Current:  {schema.get('current_schema_version')}")
        lines.append(f"  Compatible: {'YES' if schema.get('compatible') else 'NO'}")
        lines.append("")
        
        comp_level = self._compute_compatibility_level(summary)
        lines.append("-" * 64)
        lines.append(f"COMPATIBILITY LEVEL: {comp_level}")
        lines.append("-" * 64)
        lines.append("")
        lines.append("SUMMARY:")
        lines.append(f"  Total Changes: {summary.get('total_changes', 0)}")
        lines.append(f"  Breaking Changes: {summary.get('breaking_changes', 0)}")
        lines.append(f"  Potentially Breaking: {summary.get('potentially_breaking_changes', 0)}")
        lines.append(f"  Semantic Changes: {summary.get('semantic_changes', 0)}")
        lines.append(f"  Compatible Changes: {summary.get('compatible_changes', 0)}")
        lines.append("")
        
        # Group changes by category
        categories = ["breaking", "potentially_breaking", "semantic", "compatible"]
        for cat in categories:
            cat_changes = [c for c in changes if c["change_category"] == cat]
            if not cat_changes:
                continue
                
            lines.append("=" * 64)
            lines.append(f"{cat.upper().replace('_', ' ')} CHANGES ({len(cat_changes)})")
            lines.append("=" * 64)
            lines.append("")
            
            for c in cat_changes:
                lines.append(f"[{cat.upper().replace('_', ' ')}] {c['change_type'].replace('_', ' ').capitalize()}")
                lines.append(f"  Element: {c['element_type']} '{c['element_name']}'")
                if c.get("old_value") is not None or c.get("new_value") is not None:
                    lines.append(f"  Change: {c.get('old_value')} -> {c.get('new_value')}")
                lines.append(f"  Impact: {c['impact']}")
                lines.append(f"  Action: {c['action_required']}")
                lines.append("")

        lines.append("=" * 64)
        lines.append("RECOMMENDED ACTIONS")
        lines.append("=" * 64)
        lines.append("")
        actions = self._generate_actions(summary, changes)
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {action}")
        lines.append("")
        lines.append("=" * 64)
        
        return "\n".join(lines)

    def _compute_compatibility_level(self, summary: Dict) -> str:
        if summary.get("breaking_changes", 0) > 0:
            return "BREAKING"
        if summary.get("potentially_breaking_changes", 0) > 0:
            return "POTENTIALLY_BREAKING"
        if summary.get("semantic_changes", 0) > 0:
            return "SEMANTICALLY_INCOMPATIBLE"
        if summary.get("total_changes", 0) == 0:
            return "FULLY_COMPATIBLE"
        return "COMPATIBLE"

    def _generate_actions(self, summary: Dict, changes: List[Dict]) -> List[str]:
        actions = []
        if summary.get("breaking_changes", 0) > 0:
            actions.append("CRITICAL: Update language bindings immediately to reflect removals or signature changes.")
            actions.append("CRITICAL: Recompile and redeploy all dependent applications.")
        if summary.get("potentially_breaking_changes", 0) > 0:
             actions.append("IMPORTANT: Review struct layout changes; offsets or sizes may have changed.")
        if summary.get("semantic_changes", 0) > 0:
            actions.append("REVIEW: Check application logic against new semantic constraints (nullability, ownership).")
        if summary.get("total_changes", 0) > 0:
            actions.append("REGENERATE: Run language adapter generation to sync verification infrastructure.")
            actions.append("TEST: Execute full FFI verification suite to confirm compatibility.")
        else:
            actions.append("No changes detected. Existing bindings remain fully compatible.")
            
        return actions
