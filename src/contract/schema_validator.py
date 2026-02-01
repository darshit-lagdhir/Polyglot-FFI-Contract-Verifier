"""
Contract Schema Validator
Ensures contract artifacts conform to the expected schema and version.
"""

import json
from typing import List, Dict, Any, Optional
from .schema_version_manager import SchemaVersionManager

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
