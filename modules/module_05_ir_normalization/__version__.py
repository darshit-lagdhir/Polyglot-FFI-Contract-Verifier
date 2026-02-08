"""Version information for Module 05."""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)

# Version history
VERSION_HISTORY = {
    "1.0.0": {
        "date": "2025-01-15",
        "changes": [
            "Initial release",
            "Complete IR normalization pipeline",
            "Module 04 integration bridge",
            "Comprehensive validation framework",
            "Performance optimizations",
            "Full CLI interface"
        ]
    }
}

def get_version() -> str:
    """Get current version string."""
    return __version__

def get_version_info() -> tuple:
    """Get version as tuple."""
    return __version_info__
