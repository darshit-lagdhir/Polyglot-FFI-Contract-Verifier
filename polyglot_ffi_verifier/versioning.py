"""
Contract Versioning Module

This module handles FFI Contract versioning, compatibility checking, and evolution tracking.
It implements algorithms to compare contracts, detect breaking changes, and validate schemas.

Consolidates:
- ContractComparator: Main engine for detecting evolutions ()
- ChangeClassifier: Analyzes impact of changes (Compatible/Breaking)
- ContractSchemaValidator: Validates JSON structure
- CompatibilityReportGenerator: Produces human-readable reports
- SchemaVersionManager: Manages Semantic Versioning of schemas

From original implementation:  (src/contract/)
"""

import os
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class SchemaVersionManager:
    """
    Implements Semantic Versioning (MAJOR.MINOR.PATCH) for FFI contracts.
    """
    
    CURRENT_VERSION = "1.0.0"
    
    @staticmethod
    def get_current_schema_version() -> str:
        """Returns the current schema version of the verifier."""
        return SchemaVersionManager.CURRENT_VERSION
        
    @staticmethod
    def parse_version(version_str: str) -> tuple:
        """Parses a version string into a tuple of integers (major, minor, patch)."""
        try:
            parts = [int(p) for p in version_str.split(".")]
            while len(parts) < 3:
                parts.append(0)
            return tuple(parts[:3])
        except (ValueError, AttributeError):
            return (0, 0, 0)
            
    @staticmethod
    def is_schema_compatible(baseline_version: str, current_version: str) -> bool:
        """
        Tools can read contracts within the same MAJOR version.
        Future versions (higher minor/patch) are generally readable if backward compatibility 
        is maintained in the logic.
        """
        v1 = SchemaVersionManager.parse_version(baseline_version)
        v2 = SchemaVersionManager.parse_version(current_version)
        
        # Major versions must match for guaranteed compatibility
        return v1[0] == v2[0]
        
    @staticmethod
    def is_breaking_schema_change(old_version: str, new_version: str) -> bool:
        """Different major versions indicate breaking schema changes."""
        return not SchemaVersionManager.is_schema_compatible(old_version, new_version)
        
    @staticmethod
    def get_schema_changelog(version: str) -> str:
        """Returns a brief description of schema changes for a given version."""
        changelogs = {
            "1.0.0": "Initial contract schema focusing on nullability, ownership, and layout."
        }
        return changelogs.get(version, "Unknown version")

class ChangeCategory(Enum):
    COMPATIBLE = "compatible"
    BREAKING = "breaking"
    POTENTIALLY_BREAKING = "potentially_breaking"
    SEMANTIC = "semantic"
    SCHEMA = "schema"

class ChangeClassifier:
    """
    Analyzes raw contract changes and assigns risk categories and actions.
    """
    
    CHANGE_MAPPING = {
        # Function changes
        "function_added": ChangeCategory.COMPATIBLE,
        "function_removed": ChangeCategory.BREAKING,
        "parameter_added": ChangeCategory.BREAKING,
        "parameter_removed": ChangeCategory.BREAKING,
        "parameter_type_changed": ChangeCategory.BREAKING,
        "return_type_changed": ChangeCategory.BREAKING,
        "calling_convention_changed": ChangeCategory.BREAKING,
        "constraint_added": ChangeCategory.SEMANTIC,
        "constraint_removed": ChangeCategory.SEMANTIC,
        "constraint_changed": ChangeCategory.SEMANTIC,
        
        # Struct changes
        "struct_added": ChangeCategory.COMPATIBLE,
        "struct_removed": ChangeCategory.BREAKING,
        "struct_size_changed": ChangeCategory.BREAKING,
        "struct_alignment_changed": ChangeCategory.BREAKING,
        "field_added": ChangeCategory.POTENTIALLY_BREAKING,
        "field_removed": ChangeCategory.BREAKING,
        "field_type_changed": ChangeCategory.BREAKING,
        "field_offset_changed": ChangeCategory.BREAKING,
        
        # Type registry changes
        "type_added": ChangeCategory.COMPATIBLE,
        "type_removed": ChangeCategory.BREAKING,
        "type_size_changed": ChangeCategory.BREAKING,
        "type_alignment_changed": ChangeCategory.BREAKING,
        
        # Global changes
        "global_constraint_added": ChangeCategory.COMPATIBLE,
        "global_constraint_removed": ChangeCategory.SEMANTIC
    }

    def classify(self, change_type: str) -> ChangeCategory:
        """Determines the category of a change based on its type."""
        return self.CHANGE_MAPPING.get(change_type, ChangeCategory.POTENTIALLY_BREAKING)

    def assess_impact(self, change_type: str, context: str = "") -> str:
        """Provides a human-readable description of the impact."""
        impacts = {
            "function_removed": "Existing bindings will fail to link or call this function.",
            "parameter_type_changed": "ABI mismatch; will cause crashes or garbage data processing.",
            "struct_size_changed": f"Structure layout has changed. Data corruption likely if not recompiled.",
            "constraint_added": "Existing code may violate new safety rules (e.g. nullability).",
            "field_added": "Struct size increased. Existing bindings might read/write past buffer if size was fixed.",
            "calling_convention_changed": "Stack corruption guaranteed if calling convention is not updated."
        }
        return impacts.get(change_type, f"Modification to {context} may affect runtime behavior.")

    def recommend_action(self, change_type: str) -> str:
        """Suggests what the developer should do."""
        category = self.classify(change_type)
        if category == ChangeCategory.BREAKING:
            return "Update language bindings immediately, regenerate adapters, and recompile."
        if category == ChangeCategory.SEMANTIC:
            return "Review application logic for compliance with new semantic constraints."
        if category == ChangeCategory.POTENTIALLY_BREAKING:
            return "Regenerate struct definitions and check for hardcoded size assumptions."
        if category == ChangeCategory.COMPATIBLE:
            return "Regenerate adapters to expose new functionality (optional)."
        return "Inspect the change manually to determine impact."

class ContractSchemaValidator:
    """
    Validates that a contract artifact is well-formed and schema-compatible.
    """
    
    REQUIRED_ROOT_KEYS = [
        "provenance", "platform", "function_contracts", 
        "struct_contracts", "type_contracts", "global_constraints"
    ]
    
    def validate_contract(self, contract_path: str) -> Dict[str, Any]:
        """
        Loads and validates a contract file.
        Returns a dict: {"valid": bool, "contract": dict, "errors": list}
        """
        errors = []
        try:
            with open(contract_path, 'r') as f:
                contract = json.load(f)
        except Exception as e:
            return {"valid": False, "contract": None, "errors": [f"Failed to parse JSON: {str(e)}"]}
            
        # Check required keys
        for key in self.REQUIRED_ROOT_KEYS:
            if key not in contract:
                errors.append(f"Missing required root key: '{key}'")
                
        # Check provenance/schema_version
        if "provenance" in contract:
            version = contract["provenance"].get("schema_version")
            if not version:
                errors.append("Missing schema_version in provenance")
            else:
                current_ver = SchemaVersionManager.get_current_schema_version()
                if not SchemaVersionManager.is_schema_compatible(version, current_ver):
                    errors.append(f"Incompatible schema version: {version}. Expected compatibility with {current_ver}")
        else:
            errors.append("Missing provenance section")
            
        return {
            "valid": len(errors) == 0,
            "contract": contract if len(errors) == 0 else None,
            "errors": errors
        }

    def validate_against_schema(self, contract: Dict[str, Any], schema_version: str) -> List[str]:
        """Validates an in-memory contract against a specific version (placeholder for deep validation)."""
        # For now, we reuse the same logic
        errors = []
        for key in self.REQUIRED_ROOT_KEYS:
            if key not in contract:
                errors.append(f"Missing key: {key}")
        return errors

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

# ============================================================================
# PUBLIC API
# ============================================================================

class ContractComparator:
    """
    Compares a baseline contract against a current contract to detect evolutions.
    """
    
    def __init__(self):
        self.validator = ContractSchemaValidator()
        self.classifier = ChangeClassifier()
        self.version_manager = SchemaVersionManager()

    def compare_contracts(self, baseline_path: str, current_path: str, execution_id: str) -> Dict[str, Any]:
        """
        Executes the 8-step comparison algorithm.
        """
        # STEP 1: Load and Validate
        baseline_res = self.validator.validate_contract(baseline_path)
        current_res = self.validator.validate_contract(current_path)
        
        if not current_res["valid"]:
             raise ValueError(f"Current contract is invalid: {current_res['errors']}")
        
        baseline = baseline_res["contract"] or {}
        current = current_res["contract"]
        
        # STEP 2: Check Schema Compatibility
        b_version = baseline.get("provenance", {}).get("schema_version", "0.0.0")
        c_version = current.get("provenance", {}).get("schema_version", self.version_manager.get_current_schema_version())
        
        schema_info = {
            "baseline_schema_version": b_version,
            "current_schema_version": c_version,
            "compatible": self.version_manager.is_schema_compatible(b_version, c_version),
            "compatibility_notes": "Schemas are compatible" if self.version_manager.is_schema_compatible(b_version, c_version) else "Breaking schema change"
        }

        changes = []
        
        if baseline:
            # STEP 4: Detect Function Changes
            changes.extend(self._detect_function_changes(baseline.get("function_contracts", []), current.get("function_contracts", [])))
            
            # STEP 5: Detect Struct Changes
            changes.extend(self._detect_struct_changes(baseline.get("struct_contracts", []), current.get("struct_contracts", [])))
            
            # STEP 6: Detect Type Changes
            changes.extend(self._detect_type_changes(baseline.get("type_registry", {}), current.get("type_registry", {})))
            
            # STEP 7: Detect Global Changes
            changes.extend(self._detect_global_changes(baseline.get("global_constraints", []), current.get("global_constraints", [])))
        else:
            # Treating as initial contract if baseline is empty
            pass

        # STEP 8: Generate Diff Artifact
        summary = self._generate_summary(changes)
        
        diff = {
            "provenance": {
                "producing_phase": ": Contract Schema Versioning",
                "execution_id": execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "diff_schema_version": "1.0.0",
                "baseline_contract": os.path.abspath(baseline_path) if baseline_path else None,
                "current_contract": os.path.abspath(current_path)
            },
            "schema_compatibility": schema_info,
            "summary": summary,
            "changes": changes
        }
        
        return diff

    def _detect_function_changes(self, baseline: List[Dict], current: List[Dict]) -> List[Dict]:
        changes = []
        b_map = {f["function_name"]: f for f in baseline}
        c_map = {f["function_name"]: f for f in current}
        
        # Functions added
        for name in c_map:
            if name not in b_map:
                changes.append(self._create_change("function_added", "function", name))
                
        # Functions removed/modified
        for name, b_func in b_map.items():
            if name not in c_map:
                changes.append(self._create_change("function_removed", "function", name))
                continue
                
            c_func = c_map[name]
            
            # Calling convention
            if b_func.get("calling_convention") != c_func.get("calling_convention"):
                changes.append(self._create_change("calling_convention_changed", "function", name, 
                                               b_func.get("calling_convention"), c_func.get("calling_convention")))
            
            # Return type
            b_ret = b_func.get("return_contract", {}).get("type_id")
            c_ret = c_func.get("return_contract", {}).get("type_id")
            if b_ret != c_ret:
                 changes.append(self._create_change("return_type_changed", "function", name, b_ret, c_ret))

            # Parameters
            b_params_list = b_func.get("parameter_contracts", [])
            c_params_list = c_func.get("parameter_contracts", [])
            b_params = {p["parameter_name"]: p for p in b_params_list}
            c_params = {p["parameter_name"]: p for p in c_params_list}
            
            if len(c_params_list) > len(b_params_list):
                 changes.append(self._create_change("parameter_added", "function", name, len(b_params_list), len(c_params_list)))
            elif len(c_params_list) < len(b_params_list):
                 changes.append(self._create_change("parameter_removed", "function", name, len(b_params_list), len(c_params_list)))
            
            for p_name, b_p in b_params.items():
                if p_name not in c_params:
                    # Individual parameter removed (naming mismatch or actual removal)
                    continue
                c_p = c_params[p_name]
                if b_p.get("type_id") != c_p.get("type_id"):
                    changes.append(self._create_change("parameter_type_changed", "parameter", f"{name}.{p_name}", b_p.get("type_id"), c_p.get("type_id")))
                
                # Semantic changes (nullability, ownership)
                for prop in ["nullability", "ownership", "lifetime"]:
                    if b_p.get(prop) != c_p.get(prop):
                        change_type = "constraint_added" if b_p.get(prop) is None else "constraint_changed"
                        if c_p.get(prop) is None: change_type = "constraint_removed"
                        changes.append(self._create_change(change_type, "parameter", f"{name}.{p_name}.{prop}", b_p.get(prop), c_p.get(prop)))

        return changes

    def _detect_struct_changes(self, baseline: List[Dict], current: List[Dict]) -> List[Dict]:
        changes = []
        b_map = {s["struct_name"]: s for s in baseline}
        c_map = {s["struct_name"]: s for s in current}
        
        for name in c_map:
            if name not in b_map:
                changes.append(self._create_change("struct_added", "struct", name))
                
        for name, b_s in b_map.items():
            if name not in c_map:
                changes.append(self._create_change("struct_removed", "struct", name))
                continue
                
            c_s = c_map[name]
            if b_s.get("size_bytes") != c_s.get("size_bytes"):
                changes.append(self._create_change("struct_size_changed", "struct", name, b_s.get("size_bytes"), c_s.get("size_bytes")))
            if b_s.get("alignment_bytes") != c_s.get("alignment_bytes"):
                changes.append(self._create_change("struct_alignment_changed", "struct", name, b_s.get("alignment_bytes"), c_s.get("alignment_bytes")))

            # Field changes
            b_fields = {f["field_name"]: f for f in b_s.get("field_contracts", [])}
            c_fields = {f["field_name"]: f for f in c_s.get("field_contracts", [])}
            
            for f_name in c_fields:
                if f_name not in b_fields:
                    changes.append(self._create_change("field_added", "field", f"{name}.{f_name}"))
                    
            for f_name, b_f in b_fields.items():
                if f_name not in c_fields:
                    changes.append(self._create_change("field_removed", "field", f"{name}.{f_name}"))
                    continue
                c_f = c_fields[f_name]
                if b_f.get("type_id") != c_f.get("type_id"):
                    changes.append(self._create_change("field_type_changed", "field", f"{name}.{f_name}", b_f.get("type_id"), c_f.get("type_id")))
                if b_f.get("offset_bytes") != c_f.get("offset_bytes"):
                    changes.append(self._create_change("field_offset_changed", "field", f"{name}.{f_name}", b_f.get("offset_bytes"), c_f.get("offset_bytes")))

        return changes

    def _detect_type_changes(self, baseline: Dict, current: Dict) -> List[Dict]:
        changes = []
        for tid, c_info in current.items():
            if tid not in baseline:
                changes.append(self._create_change("type_added", "type_id", tid))
        for tid, b_info in baseline.items():
            if tid not in current:
                changes.append(self._create_change("type_removed", "type_id", tid))
        return changes

    def _detect_global_changes(self, baseline: List[Dict], current: List[Dict]) -> List[Dict]:
        changes = []
        b_ids = [g.get("constraint_id") for g in baseline]
        c_ids = [g.get("constraint_id") for g in current]
        
        for cid in c_ids:
            if cid not in b_ids:
                changes.append(self._create_change("global_constraint_added", "global", cid))
        for cid in b_ids:
            if cid not in c_ids:
                changes.append(self._create_change("global_constraint_removed", "global", cid))
        return changes

    def _create_change(self, change_type: str, element_type: str, element_name: str, old_val: Any = None, new_val: Any = None) -> Dict:
        category = self.classifier.classify(change_type)
        return {
            "change_type": change_type,
            "change_category": category.value,
            "element_type": element_type,
            "element_name": element_name,
            "old_value": old_val,
            "new_value": new_val,
            "description": f"{change_type.replace('_',' ').capitalize()} in {element_type} '{element_name}'",
            "impact": self.classifier.assess_impact(change_type, element_name),
            "action_required": self.classifier.recommend_action(change_type)
        }

    def _generate_summary(self, changes: List[Dict]) -> Dict:
        summary = {
            "total_changes": len(changes),
            "breaking_changes": 0,
            "compatible_changes": 0,
            "potentially_breaking_changes": 0,
            "semantic_changes": 0
        }
        for c in changes:
            cat = c["change_category"]
            summary[f"{cat}_changes"] = summary.get(f"{cat}_changes", 0) + 1
            
        return summary
