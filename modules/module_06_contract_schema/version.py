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
# File Integrity Identifier: 14c8651179943640
# ==============================================================================

"""Version information for Module 06: Contract Schema & Synthesis."""

version = "1.0.0"
version_info = (1, 0, 0)

# Version history
VERSION_HISTORY = {
    "1.0.0": {
        "date": "2025-01-20",
        "changes": [
            "Initial release of Contract Schema system",
            "Complete contract entity model (12+ entity types)",
            "Typed clause hierarchy (9 clause types)",
            "Multi-layer validation framework (3 layers)",
            "Semantic versioning with compatibility tracking",
            "JSON serialization with integrity verification",
            "Automated contract generation from IR artifacts",
            "Advanced contract diffing with migration guidance",
            "CLI interface with 6 commands",
            "Enforcement boundary with language adapters",
            "Python adapter for runtime enforcement",
            "870+ unit and integration tests",
            "Complete API documentation",
        ],
        "breaking_changes": [],
        "deprecations": [],
    }
}


def get_version() -> str:
    """Get current version string."""
    return version


def get_version_info() -> tuple:
    """Get version as tuple."""
    return version_info


def get_version_history() -> dict:
    """Get complete version history."""
    return VERSION_HISTORY