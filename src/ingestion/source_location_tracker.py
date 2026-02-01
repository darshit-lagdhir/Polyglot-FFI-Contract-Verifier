"""
Source Location Tracker

Captures and formats source locations from libclang AST nodes.
Ensures all source locations are absolute paths and consistently formatted.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    """Immutable source location representation."""
    file: str
    line: int
    column: int


class SourceLocationTracker:
    """
    Tracks and formats source locations from AST nodes.
    
    Responsibilities:
    - Extract source locations from libclang cursors
    - Resolve paths to absolute paths
    - Format locations consistently for artifact output
    - Handle missing/invalid locations gracefully
    """
    
    def __init__(self):
        """Initialize source location tracker."""
        pass
    
    def get_location(self, cursor) -> SourceLocation:
        """
        Extract source location from a libclang cursor.
        
        Args:
            cursor: libclang cursor object
            
        Returns:
            SourceLocation with absolute file path
            
        Note:
            If location cannot be determined, returns unknown location
            with file="<unknown>", line=0, column=0
        """
        try:
            location = cursor.location
            if location.file:
                file_path = os.path.abspath(location.file.name)
                return SourceLocation(
                    file=file_path,
                    line=location.line,
                    column=location.column
                )
            else:
                return self._unknown_location()
        except Exception:
            return self._unknown_location()
    
    def format_location(self, location: SourceLocation) -> Dict[str, Any]:
        """
        Format source location for JSON artifact output.
        
        Args:
            location: SourceLocation object
            
        Returns:
            Dictionary with file, line, column keys
        """
        return {
            "file": location.file,
            "line": location.line,
            "column": location.column
        }
    
    def _unknown_location(self) -> SourceLocation:
        """
        Create an unknown source location.
        
        Returns:
            SourceLocation with placeholder values
        """
        return SourceLocation(
            file="<unknown>",
            line=0,
            column=0
        )
    
    def get_location_dict(self, cursor) -> Dict[str, Any]:
        """
        Convenience method to get formatted location directly from cursor.
        
        Args:
            cursor: libclang cursor object
            
        Returns:
            Formatted location dictionary
        """
        location = self.get_location(cursor)
        return self.format_location(location)
