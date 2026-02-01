"""
Naming Convention Analyzer
Extracts semantic hints from function and parameter names.
"""

from typing import Optional, List

class NamingConventionAnalyzer:
    """
    Analyzes C naming conventions to infer intent for nullability, ownership, etc.
    """
    
    def is_nullable_name(self, name: str) -> bool:
        """Rule 1: Detect nullability hints."""
        lower_name = name.lower()
        prefixes = ["optional_", "maybe_", "nullable_"]
        suffixes = ["_opt", "_nullable", "_maybe"]
        
        return any(lower_name.startswith(p) for p in prefixes) or \
               any(lower_name.endswith(s) for s in suffixes)

    def is_ownership_transfer_function(self, func_name: str) -> Optional[str]:
        """Rule 2: Detect ownership transfer intent."""
        lower_name = func_name.lower()
        
        # Transfers to Caller (Allocation)
        transfers_to_caller = ["create_", "alloc_", "new_", "init_", "clone_", "dup_"]
        if any(lower_name.startswith(p) for p in transfers_to_caller):
            return "caller"
            
        # Transfers to Callee (Deallocation/Take-ownership)
        transfers_to_callee = ["destroy_", "free_", "delete_", "release_", "sink_", "take_"]
        if any(lower_name.startswith(p) for p in transfers_to_callee):
            return "callee"
            
        return None

    def is_borrowed_function(self, func_name: str) -> bool:
        """Detect intent for non-transferring operations."""
        lower_name = func_name.lower()
        prefixes = ["get_", "find_", "query_", "peek_", "view_", "process_", "write_", "read_"]
        return any(lower_name.startswith(p) for p in prefixes)

    def detect_buffer_size_relationship(self, pointer_name: str, scalar_name: str) -> bool:
        """Rule 4: Detect relationship between a buffer and its size parameter."""
        p_name = pointer_name.lower()
        s_name = scalar_name.lower()
        
        # 1. Name match + size/len suffix
        size_indicators = ["_size", "_len", "_count", "_length", "size", "len", "count"]
        for indicator in size_indicators:
            if s_name == f"{p_name}{indicator}" or s_name == indicator:
                return True
                
        # 2. Heuristic for common pairs
        common_pairs = {
            "buffer": ["buffer_size", "buf_len", "size"],
            "data": ["data_size", "datalen", "len"],
            "items": ["count", "num_items"],
            "ptr": ["size", "count"]
        }
        
        if p_name in common_pairs and s_name in common_pairs[p_name]:
            return True
            
        return False

    def is_error_code_return(self, func_name: str, return_type_id: str) -> bool:
        """Rule 6: Detect if return value represents an error code."""
        if return_type_id not in ["primitive:int32", "primitive:int64", "primitive:int16"]:
            return False
            
        lower_name = func_name.lower()
        indicators = ["status", "error", "result", "code", "write", "process", "save", "init", "open"]
        return any(ind in lower_name for ind in indicators)
