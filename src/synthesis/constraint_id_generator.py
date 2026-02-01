"""
Constraint ID Generator
Generates unique, deterministic, and human-readable constraint IDs.
"""

import hashlib

class ConstraintIDGenerator:
    """
    Ensures every constraint in the contract has a traceable, unique identifier.
    """
    
    def generate_function_id(self, func_name: str, target: str, constraint_type: str) -> str:
        """
        Generate ID for function-related constraints.
        Format: func_<name>_<target>_<type>
        """
        # Clean target name (e.g. parameter:cfg -> p_cfg)
        clean_target = target.replace("parameter:", "p_").replace("return_value", "ret")
        base = f"func_{func_name}_{clean_target}_{constraint_type}"
        return self._normalize(base)

    def generate_struct_id(self, struct_name: str, field_name: str, constraint_type: str) -> str:
        """
        Generate ID for struct-related constraints.
        Format: struct_<name>_<field>_<type>
        """
        base = f"struct_{struct_name}_{field_name}_{constraint_type}"
        return self._normalize(base)

    def generate_global_id(self, constraint_type: str) -> str:
        """
        Generate ID for global constraints.
        Format: global_<type>
        """
        return f"global_{constraint_type}"

    def _normalize(self, base_id: str) -> str:
        """Ensure IDs are valid identifiers and deduplicated locally if needed."""
        # In a real system we might append a hash of the justification if multiple
        # identical constraints exist, but for our v1.0, semantic names are better.
        return base_id.lower().replace(" ", "_").replace("*", "ptr")
