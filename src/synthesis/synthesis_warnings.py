"""
Synthesis Warning Logger
Tracks ambiguities and conservative assumptions made during synthesis.
"""

from typing import List, Dict, Any

class SynthesisWarningLogger:
    """
    Captures warnings when automated analysis falls back to conservative defaults
    or encounters ambiguous patterns.
    """
    
    def __init__(self):
        self.warnings: List[Dict[str, Any]] = []

    def log(self, category: str, message: str, severity: str = "warning", context: str = ""):
        """Add a warning to the list."""
        self.warnings.append({
            "category": category,
            "message": message,
            "severity": severity,
            "context": context
        })

    def warn_ambiguous_ownership(self, func_name: str, param_name: str):
        self.log(
            "OWNERSHIP_AMBIGUITY",
            f"Could not determine ownership for parameter '{param_name}' in '{func_name}'. Assuming borrowed.",
            "warning",
            func_name
        )

    def warn_missing_buffer_size(self, func_name: str, param_name: str):
        self.log(
            "BUFFER_SAFETY",
            f"Pointer parameter '{param_name}' in '{func_name}' appears to be a buffer but has no associated size parameter.",
            "error",
            func_name
        )

    def warn_variadic_function(self, func_name: str):
        self.log(
            "VARIADIC_LIMITATION",
            f"Function '{func_name}' is variadic. Full verification is not supported without manual format string validation.",
            "warning",
            func_name
        )

    def get_all(self) -> List[Dict[str, Any]]:
        return self.warnings
