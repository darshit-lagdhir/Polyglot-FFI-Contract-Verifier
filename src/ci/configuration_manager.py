"""
Config Manager
Handles loading and validation of verifier settings from files and environment.
"""

import os
import yaml
from typing import Any, Dict

class ConfigManager:
    """
    Loads configuration from YAML files and environment variables.
    """

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "paths": {
                "header": "native/interface.h",
                "library": "build/library.dll",
                "output_dir": "ffi_verification"
            },
            "execution": {
                "timeout_seconds": 600,
                "enable_crash_detection": True,
                "subprocess_timeout": 60
            },
            "failure_policy": {
                "strict_mode": False,
                "block_on_critical": True,
                "block_on_high": False,
                "max_violations": 10
            },
            "reporting": {
                "generate_html": True,
                "generate_markdown": True,
                "generate_ci_summary": True,
                "upload_artifacts": True
            },
            "ci": {
                "platform": "github",
                "status_badge": True,
                "comment_on_pr": True,
                "fail_fast": False
            }
        }

    def load_config(self, config_path: str) -> Dict[str, Any]:
        config = self.get_default_config()
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._deep_update(config, user_config)
        
        # Override with environment variables
        env_config = self.load_from_environment()
        self._deep_update(config, env_config)
        
        return config

    def load_from_environment(self) -> Dict[str, Any]:
        env_vars = {}
        if os.environ.get("FFI_HEADER_PATH"):
            self._set_path(env_vars, "paths.header", os.environ["FFI_HEADER_PATH"])
        if os.environ.get("FFI_LIBRARY_PATH"):
            self._set_path(env_vars, "paths.library", os.environ["FFI_LIBRARY_PATH"])
        if os.environ.get("FFI_VERIFIER_STRICT"):
            self._set_path(env_vars, "failure_policy.strict_mode", os.environ["FFI_VERIFIER_STRICT"].lower() == "true")
        if os.environ.get("FFI_VERIFIER_TIMEOUT"):
            self._set_path(env_vars, "execution.timeout_seconds", int(os.environ["FFI_VERIFIER_TIMEOUT"]))
        return env_vars

    def validate_config(self, config: Dict[str, Any]) -> bool:
        # Simple validation for demonstration
        if not config.get("paths", {}).get("header"):
            return False
        return True

    def _deep_update(self, base: Dict[str, Any], update: Dict[str, Any]):
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def _set_path(self, d: Dict[str, Any], path: str, value: Any):
        keys = path.split('.')
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
