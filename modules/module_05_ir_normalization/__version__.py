# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: fc6662dc0da08b12
# ==============================================================================

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
            "Full CLI interface",
        ],
    }
}


def get_version() -> str:
    """Get current version string."""
    return __version__


def get_version_info() -> tuple:
    """Get version as tuple."""
    return __version_info__