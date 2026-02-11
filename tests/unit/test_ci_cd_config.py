"""
Unit tests for Module 06: CI/CD Configuration (Prompt 13/15)
Testing Level: MEDIUM (25 tests)
"""

import pytest
from pathlib import Path
import yaml
import sys

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestGitHubWorkflows:
    """Test GitHub Actions workflow files."""
    
    def test_test_workflow_exists(self):
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "test.yml"
        assert workflow_path.exists(), "Main test workflow not found"
    
    def test_publish_workflow_exists(self):
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "publish.yml"
        assert workflow_path.exists(), "Publish workflow not found"


class TestWorkflowContent:
    """Test GitHub Actions workflow content."""
    
    @pytest.fixture
    def test_workflow(self):
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "test.yml"
        with open(workflow_path, encoding='utf-8') as f:
            return yaml.safe_load(f)

    def test_workflow_has_name(self, test_workflow):
        assert "name" in test_workflow
        assert "Test" in test_workflow["name"]
    
    def test_workflow_has_triggers(self, test_workflow):
        # 'on' might be parsed as True if not quoted, but we quoted it
        on_key = "on" if "on" in test_workflow else True
        assert on_key in test_workflow
        triggers = test_workflow[on_key]
        assert "push" in triggers or "pull_request" in triggers
    
    def test_workflow_has_jobs(self, test_workflow):
        assert "jobs" in test_workflow
        assert "test" in test_workflow["jobs"]
    
    def test_workflow_tests_python_versions(self, test_workflow):
        test_job = test_workflow["jobs"]["test"]
        assert "strategy" in test_job
        assert "matrix" in test_job["strategy"]
        assert "python-version" in test_job["strategy"]["matrix"]
        
        versions = test_job["strategy"]["matrix"]["python-version"]
        assert "3.11" in versions
        assert len(versions) == 1, "Should only test one version to save minutes"

    def test_workflow_has_module_06_tasks(self, test_workflow):
        steps = test_workflow["jobs"]["test"]["steps"]
        m06_step = any("Module 06" in step.get("name", "") for step in steps)
        assert m06_step, "Module 06 specific tests not found in test workflow"

    def test_workflow_has_coverage_upload(self, test_workflow):
        steps = test_workflow["jobs"]["test"]["steps"]
        codecov_step = any("codecov-action" in step.get("uses", "") for step in steps)
        assert codecov_step, "Codecov upload not found in test workflow"

    def test_workflow_has_quality_checks(self, test_workflow):
        steps = test_workflow["jobs"]["test"]["steps"]
        quality_step = any("Quality" in step.get("name", "") for step in steps)
        assert quality_step, "Quality checks step not found in test workflow"


class TestPreCommitConfig:
    """Test pre-commit configuration."""
    
    def test_precommit_config_exists(self):
        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        assert config_path.exists(), "Pre-commit config not found"
    
    @pytest.fixture
    def precommit_config(self):
        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        with open(config_path, encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def test_has_repos(self, precommit_config):
        assert "repos" in precommit_config
        assert len(precommit_config["repos"]) > 0

    def test_has_black_hook(self, precommit_config):
        repos = precommit_config.get("repos", [])
        black_repos = [r for r in repos if "black" in r.get("repo", "")]
        assert len(black_repos) > 0, "Black hook not found"
    
    def test_has_flake8_hook(self, precommit_config):
        repos = precommit_config.get("repos", [])
        flake8_repos = [r for r in repos if "flake8" in r.get("repo", "")]
        assert len(flake8_repos) > 0, "Flake8 hook not found"
    
    def test_has_isort_hook(self, precommit_config):
        repos = precommit_config.get("repos", [])
        isort_repos = [r for r in repos if "isort" in r.get("repo", "")]
        assert len(isort_repos) > 0, "isort hook not found"

    def test_has_yaml_hook(self, precommit_config):
        repos = precommit_config.get("repos", [])
        hooks = []
        for r in repos:
            hooks.extend([h.get("id") for h in r.get("hooks", [])])
        assert "check-yaml" in hooks




class TestCIWorkflowPaths:
    """Test that workflows target the correct paths."""

    @pytest.fixture
    def test_workflow(self):
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "test.yml"
        with open(workflow_path, encoding='utf-8') as f:
            return yaml.safe_load(f)

    def test_push_paths_correct(self, test_workflow):
        # 'on' might be True or 'on'
        on_val = test_workflow.get("on") or test_workflow.get(True)
        paths = on_val["push"].get("paths", [])
        assert any("modules/**" in p for p in paths)



# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
