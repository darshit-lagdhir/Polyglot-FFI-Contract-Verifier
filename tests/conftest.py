import pytest
import tempfile
import os
from pathlib import Path

# ───────────────────────────────────────────────────────────────
# Pytest Config
# ───────────────────────────────────────────────────────────────


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end (slow)")
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")


# ───────────────────────────────────────────────────────────────
# Shared Fixtures
# ───────────────────────────────────────────────────────────────


@pytest.fixture
def temp_dir():
    """Provide temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_stage():
    """Provide mock pipeline stage."""

    class MockStage:
        STAGE_NAME = "mock_stage"
        STAGE_VERSION = "1.0.0"
        REQUIRED_INPUTS = []
        PRODUCED_OUTPUTS = ["mock_output"]

    return MockStage()


@pytest.fixture
def sample_header(temp_dir):
    """Create sample C header for testing."""
    header = temp_dir / "sample.h"
    header.write_text("""
#ifndef SAMPLE_H
#define SAMPLE_H

int add(int a, int b);
void process(const char* data, int length);

#endif
    """)
    return str(header)


# ───────────────────────────────────────────────────────────────
# Test Utilities
# ───────────────────────────────────────────────────────────────


class Helpers:
    """Test helper functions."""

    @staticmethod
    def create_mock_artifact(path: Path, artifact_type: str):
        """Create mock artifact file."""
        import json

        artifact = {
            "provenance": {
                "execution_id": "test-123",
                "stage_name": artifact_type,
                "stage_version": "1.0.0",
                "creation_timestamp": "2026-01-01T00:00:00Z",
                "schema_version": "1.0.0",
                "input_artifact_hashes": {},
            },
            "data": {},
        }

        path.write_text(json.dumps(artifact, indent=2))
        return str(path)


@pytest.fixture
def helpers():
    """Provide test helpers."""
    return Helpers()
