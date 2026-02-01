"""
Qualifier Normalizer
Normalizes type qualifiers (const, volatile, restrict) into a canonical format.
"""

from typing import List, Dict

class QualifierNormalizer:
    """
    Normalizes type qualifiers from compiler-specific lists to canonical boolean maps.
    """
    
    def normalize(self, qualifiers: List[str]) -> Dict[str, bool]:
        """
        Convert a list of qualifier strings into a normalized dictionary.
        
        Args:
            qualifiers: List of strings like ["const", "volatile"]
            
        Returns:
            Dictionary with canonical keys and boolean values
        """
        # Ensure input is a list
        if not isinstance(qualifiers, list):
            qualifiers = []
            
        # Case insensitive matching
        q_lower = [q.lower() for q in qualifiers]
        
        return {
            "is_const": "const" in q_lower,
            "is_volatile": "volatile" in q_lower,
            "is_restrict": "restrict" in q_lower
        }

    @staticmethod
    def extract_from_type(type_info: Dict) -> Dict[str, bool]:
        """ Helper to extract qualifiers from a type info dictionary if present. """
        qualifiers = type_info.get("qualifiers", [])
        return QualifierNormalizer().normalize(qualifiers)
