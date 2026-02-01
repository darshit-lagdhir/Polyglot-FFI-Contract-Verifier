"""
Schema Version Manager
Manages the contract schema versioning strategy and compatibility rules.
"""

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
