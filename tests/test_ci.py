"""
Validation Script for CI/CD Integration
Tests 12 requirements for Phase 12.
"""

import os
import json
import shutil
import tempfile
import yaml
from pathlib import Path

# Ensure project root in path
import sys
sys.path.append(os.getcwd())

from polyglot_ffi_verifier.ci.ci_integration_manager import CIIntegrationManager
from polyglot_ffi_verifier.ci.workflow_template_generator import WorkflowTemplateGenerator
from polyglot_ffi_verifier.ci.badge_generator import BadgeGenerator
from polyglot_ffi_verifier.ci.ci_status_checker import CIStatusChecker
from polyglot_ffi_verifier.ci.configuration_manager import ConfigurationManager
from polyglot_ffi_verifier.ci.artifact_publisher import ArtifactPublisher

def test_ci():
    print("Testing CI/CD Integration...")
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. TEST 1: GitHub actions generation
        gen = WorkflowTemplateGenerator()
        gh_yml = gen.generate_github_actions()
        assert "name: FFI Contract Verification" in gh_yml
        assert "runs-on: windows-latest" in gh_yml
        print("✓ GitHub Actions workflow generation working")

        # 2. TEST 2: GitLab CI generation
        gl_yml = gen.generate_gitlab_ci()
        assert "stages:" in gl_yml
        assert "ffi-verification:" in gl_yml
        print("✓ GitLab CI config generation working")

        # 3. TEST 3: Badge Generation
        badge_gen = BadgeGenerator()
        mock_summary = {
            "verification_status": "failed",
            "summary": {"critical_violations": 2, "pass_rate": 80.0}
        }
        badge = badge_gen.generate_badge(mock_summary)
        assert badge["color"] == "red"
        assert "FAILED" in badge["message"]
        print("✓ Badge generation correct")

        # 4. TEST 4: CI Status Check (Passed)
        checker = CIStatusChecker()
        summary_passed = {
            "verification_status": "passed",
            "summary": {"critical_violations": 0, "total_violations": 0, "passed_tests": 10, "total_tests": 10, "pass_rate": 100.0}
        }
        policy = {"strict_mode": False, "block_on_critical": True}
        assert checker.check_status(summary_passed, policy) == 0
        print("✓ CI status check (passed) correct")

        # 5. TEST 5: CI Status Check (Failed - Critical)
        summary_failed = {
            "verification_status": "failed",
            "summary": {"critical_violations": 1, "total_violations": 1, "passed_tests": 9, "total_tests": 10, "pass_rate": 90.0}
        }
        assert checker.check_status(summary_failed, policy) == 1
        print("✓ CI status check (failed) correct")

        # 6. TEST 6: Warnings Non-Strict
        summary_warn = {
            "verification_status": "passed", # Phase 11 marks passed if no critical
            "summary": {"critical_violations": 0, "total_violations": 2, "passed_tests": 8, "total_tests": 10, "pass_rate": 80.0}
        }
        assert checker.check_status(summary_warn, policy) == 0
        print("✓ CI status check (warnings non-strict) correct")

        # 7. TEST 7: Warnings Strict
        policy_strict = {"strict_mode": True, "block_on_critical": True}
        assert checker.check_status(summary_warn, policy_strict) == 1
        print("✓ CI status check (warnings strict) correct")

        # 8. TEST 8: Configuration Loading
        config_path = os.path.join(temp_dir, "test_config.yml")
        with open(config_path, 'w') as f:
            yaml.dump({"paths": {"header": "custom/header.h"}}, f)
        
        config_mgr = ConfigurationManager()
        config = config_mgr.load_config(config_path)
        assert config["paths"]["header"] == "custom/header.h"
        print("✓ Configuration loading working")

        # 9. TEST 9: Environment Configuration
        os.environ["FFI_VERIFIER_STRICT"] = "true"
        config = config_mgr.load_config(config_path)
        assert config["failure_policy"]["strict_mode"] is True
        print("✓ Environment configuration working")

        # 10. TEST 10: Artifact Preparation
        pub = ArtifactPublisher()
        os.makedirs(os.path.join(temp_dir, "reports"))
        open(os.path.join(temp_dir, "reports/test.txt"), 'w').close()
        artifacts = pub.prepare_artifacts(temp_dir)
        assert any("test.txt" in f for f in artifacts)
        print("✓ Artifact preparation correct")

        # 11. TEST 11: Template Customization
        custom_config = {"paths": {"header": "lib.h", "library": "lib.so"}}
        cust_gh = gen.customize_template(gh_yml, custom_config)
        assert "lib.h" in cust_gh
        assert "lib.so" in cust_gh
        print("✓ Template customization working")

        # 12. TEST 12: Platform Detection
        mgr = CIIntegrationManager()
        os.environ["GITHUB_ACTIONS"] = "true"
        assert mgr.detect_platform() == "github"
        print("✓ Platform detection working")

        print("\n✓ ALL TESTS PASSED (12/12)")
        return True
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_ci()
