"""
Contract Comparator
Implements the multi-step algorithm for identifying changes between two FFI contracts.
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .schema_validator import ContractSchemaValidator
from .change_classifier import ChangeClassifier, ChangeCategory
from .schema_version_manager import SchemaVersionManager

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
