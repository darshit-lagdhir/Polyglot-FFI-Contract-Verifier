"""
Change Classifier
Categorizes detected contract changes by their impact on compatibility.
"""

from enum import Enum
from typing import Dict, Any, List

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
