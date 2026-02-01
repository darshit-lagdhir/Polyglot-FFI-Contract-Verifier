"""
CI Integration Manager
Main orchestrator for CI/CD setup and automation.
"""

import os
import yaml
from typing import Dict, Any, Optional

from .workflow_template_generator import WorkflowTemplateGenerator
from .configuration_manager import ConfigurationManager

class CIIntegrationManager:
    """
    Coordinates CI template generation and configuration.
    """

    def __init__(self):
        self.template_gen = WorkflowTemplateGenerator()
        self.config_mgr = ConfigurationManager()

    def setup_ci(self, platform: str, config_path: Optional[str] = None) -> None:
        """
        Generates workflow files for the specified platform.
        """
        config = self.config_mgr.load_config(config_path or "")
        
        if platform == "github":
            content = self.template_gen.generate_github_actions()
            content = self.template_gen.customize_template(content, config)
            self._write_template(".github/workflows/ffi-verification.yml", content)
        elif platform == "gitlab":
            content = self.template_gen.generate_gitlab_ci()
            content = self.template_gen.customize_template(content, config)
            self._write_template(".gitlab-ci.yml", content)
        elif platform == "jenkins":
            content = self.template_gen.generate_jenkinsfile()
            content = self.template_gen.customize_template(content, config)
            self._write_template("Jenkinsfile", content)
        else:
            raise ValueError(f"Unsupported CI platform: {platform}")

    def _write_template(self, path: str, content: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, 'w') as f:
            f.write(content)
        print(f"Generated CI template: {path}")

    def detect_platform(self) -> str:
        if os.environ.get("GITHUB_ACTIONS"):
            return "github"
        if os.environ.get("GITLAB_CI"):
            return "gitlab"
        if os.environ.get("JENKINS_URL"):
            return "jenkins"
        return "generic"
