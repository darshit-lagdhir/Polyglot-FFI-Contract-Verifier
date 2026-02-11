"""
Integration test configuration and shared fixtures.
"""

import pytest
from pathlib import Path


def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


@pytest.fixture(scope="session")
def integration_fixtures_dir():
    """Get integration test fixtures directory."""
    return Path(__file__).parent / "fixtures"
