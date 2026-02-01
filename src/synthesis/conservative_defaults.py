"""
Conservative Default Policy
Defines the safe fallback policies when semantic information is missing.
"""

from typing import Dict, Any

class ConservativeDefaultPolicy:
    """
    Implements mandatory fallback policies to ensure safety over permissiveness.
    """
    
    @staticmethod
    def default_nullability() -> str:
        """DEFAULT POLICY 1: Pointers are required unless proven optional."""
        return "non_null"
        
    @staticmethod
    def default_ownership() -> str:
        """DEFAULT POLICY 2: Assume borrowed (caller keeps ownership)."""
        return "borrowed"
        
    @staticmethod
    def default_lifetime() -> str:
        """DEFAULT POLICY 3: Valid only during function call."""
        return "call_duration"
        
    @staticmethod
    def default_mutability(is_const: bool) -> str:
        """DEFAULT POLICY 4: Favor immutable if const, else mutable."""
        return "immutable" if is_const else "mutable"
        
    @staticmethod
    def default_buffer_safety() -> Dict[str, Any]:
        """DEFAULT POLICY 5: Buffers are high risk."""
        return {
            "is_fixed_size": False,
            "requires_validation": True,
            "severity": "warning"
        }
        
    @staticmethod
    def default_return_semantics(return_type_id: str) -> str:
        """DEFAULT POLICY 6: Integer returns are treated as error codes."""
        if return_type_id.startswith("primitive:int"):
            return "error_code"
        return "value"
