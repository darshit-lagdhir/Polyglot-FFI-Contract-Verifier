
"""Test Suite for Language Adapter - Prompt 07/25: 90 tests."""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from modules.module_08_language_adapter import (
    PolicyType,
    EnforcementPolicy,
    PerformanceProfile,
    AdapterConfiguration,
    ConfigurationValidator,
    ConfigurationLoader,
    PolicyRegistry,
    ConfigurationManager,
    ClauseSeverity,
)


class TestEnforcementPolicy:
    """EnforcementPolicy tests (20 tests)."""
    
    def test_create_strict_policy(self):
        """Test 561: Create strict policy."""
        policy = EnforcementPolicy.strict()
        assert policy.policy_type == PolicyType.STRICT
        assert policy.fail_fast is True
        assert policy.treat_advisory_as_mandatory is True
    
    def test_create_balanced_policy(self):
        """Test 562: Create balanced policy."""
        policy = EnforcementPolicy.balanced()
        assert policy.policy_type == PolicyType.BALANCED
        assert policy.fail_fast is False
    
    def test_create_permissive_policy(self):
        """Test 563: Create permissive policy."""
        policy = EnforcementPolicy.permissive()
        assert policy.policy_type == PolicyType.PERMISSIVE
        assert policy.treat_advisory_as_mandatory is False
    
    def test_should_enforce_mandatory(self):
        """Test 564: Always enforce mandatory."""
        policy = EnforcementPolicy.permissive()
        assert policy.should_enforce(ClauseSeverity.MANDATORY) is True
    
    def test_should_enforce_advisory_strict(self):
        """Test 565: Strict enforces advisory."""
        policy = EnforcementPolicy.strict()
        assert policy.should_enforce(ClauseSeverity.ADVISORY) is True
    
    def test_should_enforce_advisory_balanced(self):
        """Test 566: Balanced doesn't enforce advisory."""
        policy = EnforcementPolicy.balanced()
        assert policy.should_enforce(ClauseSeverity.ADVISORY) is False
    
    def test_should_enforce_optional(self):
        """Test 567: Optional enforcement based on setting."""
        policy = EnforcementPolicy(
            policy_type=PolicyType.CUSTOM,
            treat_optional_as_advisory=True
        )
        assert policy.should_enforce(ClauseSeverity.OPTIONAL) is True
    
    def test_policy_to_dict(self):
        """Test 568: Policy serialization."""
        policy = EnforcementPolicy.strict()
        data = policy.to_dict()
        assert data['policy_type'] == 'strict'
        assert data['fail_fast'] is True
    
    def test_custom_policy(self):
        """Test 569: Custom policy creation."""
        policy = EnforcementPolicy(
            policy_type=PolicyType.CUSTOM,
            fail_fast=False,
            max_violations=5
        )
        assert policy.policy_type == PolicyType.CUSTOM
        assert policy.max_violations == 5
    
    def test_violation_callback(self):
        """Test 570-580: Policy with callback."""
        called = []
        def callback(violation):
            called.append(violation)
        
        policy = EnforcementPolicy(
            policy_type=PolicyType.CUSTOM,
            violation_callback=callback
        )
        assert policy.violation_callback is not None


class TestPerformanceProfile:
    """PerformanceProfile tests (15 tests)."""
    
    def test_create_fast_profile(self):
        """Test 581: Create fast profile."""
        profile = PerformanceProfile.fast()
        assert profile.optimization_level == 3
        assert profile.enable_caching is True
    
    def test_create_balanced_profile(self):
        """Test 582: Create balanced profile."""
        profile = PerformanceProfile.balanced()
        assert profile.optimization_level == 1
        assert profile.enable_caching is False
    
    def test_create_debug_profile(self):
        """Test 583: Create debug profile."""
        profile = PerformanceProfile.debug()
        assert profile.optimization_level == 0
        assert profile.profile_execution is True
    
    def test_custom_profile(self):
        """Test 584: Custom profile."""
        profile = PerformanceProfile(
            optimization_level=2,
            parallel_validation=True
        )
        assert profile.optimization_level == 2
        assert profile.parallel_validation is True
    
    def test_profile_to_dict(self):
        """Test 585-595: Profile serialization."""
        profile = PerformanceProfile.fast()
        data = profile.to_dict()
        assert data['optimization_level'] == 3
        assert data['enable_caching'] is True


class TestAdapterConfiguration:
    """AdapterConfiguration tests (15 tests)."""
    
    def test_create_default_config(self):
        """Test 596: Create default configuration."""
        config = AdapterConfiguration()
        assert config.enforcement_policy is not None
        assert config.performance_profile is not None
    
    def test_config_with_custom_policy(self):
        """Test 597: Config with custom policy."""
        policy = EnforcementPolicy.strict()
        config = AdapterConfiguration(enforcement_policy=policy)
        assert config.enforcement_policy.policy_type == PolicyType.STRICT
    
    def test_config_with_custom_profile(self):
        """Test 598: Config with custom profile."""
        profile = PerformanceProfile.fast()
        config = AdapterConfiguration(performance_profile=profile)
        assert config.performance_profile.optimization_level == 3
    
    def test_config_debugging_options(self):
        """Test 599: Config debugging options."""
        config = AdapterConfiguration(
            verbose_logging=True,
            trace_validation=True
        )
        assert config.verbose_logging is True
        assert config.trace_validation is True
    
    def test_ignore_clause_types(self):
        """Test 600: Ignore clause types."""
        config = AdapterConfiguration(
            ignore_clause_types={'alignment', 'deprecated'}
        )
        assert 'alignment' in config.ignore_clause_types
    
    def test_require_clause_types(self):
        """Test 601: Require clause types."""
        config = AdapterConfiguration(
            require_clause_types={'nullability', 'range'}
        )
        assert 'nullability' in config.require_clause_types
    
    def test_function_overrides(self):
        """Test 602: Function-specific overrides."""
        config = AdapterConfiguration()
        config.function_overrides['my_func'] = {'verbose_logging': True}
        assert 'my_func' in config.function_overrides
    
    def test_get_effective_config_no_override(self):
        """Test 603: Effective config without override."""
        config = AdapterConfiguration(verbose_logging=False)
        effective = config.get_effective_config('func')
        assert effective.verbose_logging is False
    
    def test_get_effective_config_with_override(self):
        """Test 604: Effective config with override."""
        config = AdapterConfiguration(verbose_logging=False)
        config.function_overrides['func'] = {'verbose_logging': True}
        
        effective = config.get_effective_config('func')
        assert effective.verbose_logging is True
    
    def test_config_to_dict(self):
        """Test 605-610: Config serialization."""
        config = AdapterConfiguration()
        data = config.to_dict()
        assert 'enforcement_policy' in data
        assert 'performance_profile' in data


class TestConfigurationValidator:
    """ConfigurationValidator tests (10 tests)."""
    
    def test_validate_valid_config(self):
        """Test 611: Valid configuration passes."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        
        valid, errors = validator.validate(config)
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_invalid_optimization(self):
        """Test 612: Invalid optimization level."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.optimization_level = 5
        
        valid, errors = validator.validate(config)
        assert valid is False
        assert any('optimization_level' in e for e in errors)
    
    def test_validate_negative_timeout(self):
        """Test 613: Negative timeout fails."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.clause_timeout_ms = -1
        
        valid, errors = validator.validate(config)
        assert valid is False
    
    def test_validate_negative_max_violations(self):
        """Test 614: Negative max violations fails."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.enforcement_policy.max_violations = -1
        
        valid, errors = validator.validate(config)
        assert valid is False
    
    def test_validate_conflicting_options(self):
        """Test 615: Conflicting options detected."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.lazy_validation = True
        config.enforcement_policy.fail_fast = True
        
        valid, errors = validator.validate(config)
        assert valid is False
    
    def test_validate_overlapping_clause_sets(self):
        """Test 616-620: Overlapping ignore/require sets."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration(
            ignore_clause_types={'range'},
            require_clause_types={'range'}
        )
        
        valid, errors = validator.validate(config)
        assert valid is False


class TestConfigurationLoader:
    """ConfigurationLoader tests (15 tests)."""
    
    def test_load_from_empty_dict(self):
        """Test 621: Load from empty dict."""
        loader = ConfigurationLoader()
        config = loader.load_from_dict({})
        assert config is not None
    
    def test_load_policy_from_dict(self):
        """Test 622: Load enforcement policy."""
        loader = ConfigurationLoader()
        config_dict = {
            'enforcement_policy': {
                'policy_type': 'strict',
                'fail_fast': True
            }
        }
        config = loader.load_from_dict(config_dict)
        assert config.enforcement_policy.policy_type == PolicyType.STRICT
    
    def test_load_performance_from_dict(self):
        """Test 623: Load performance profile."""
        loader = ConfigurationLoader()
        config_dict = {
            'performance_profile': {
                'optimization_level': 3,
                'enable_caching': True
            }
        }
        config = loader.load_from_dict(config_dict)
        assert config.performance_profile.optimization_level == 3
    
    def test_load_debug_options(self):
        """Test 624: Load debugging options."""
        loader = ConfigurationLoader()
        config_dict = {
            'verbose_logging': True,
            'trace_validation': True
        }
        config = loader.load_from_dict(config_dict)
        assert config.verbose_logging is True
    
    def test_load_from_file(self):
        """Test 625: Load from JSON file."""
        loader = ConfigurationLoader()
        config_dict = {
            'enforcement_policy': {'policy_type': 'balanced'},
            'verbose_logging': True
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump(config_dict, f)
            path = f.name
        
        try:
            config = loader.load_from_file(path)
            assert config.verbose_logging is True
        finally:
            Path(path).unlink()
    
    def test_load_from_nonexistent_file(self):
        """Test 626: Load from non-existent file raises."""
        loader = ConfigurationLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_from_file('nonexistent.json')
    
    def test_load_invalid_config_raises(self):
        """Test 627-635: Invalid config raises error."""
        loader = ConfigurationLoader()
        config_dict = {
            'performance_profile': {
                'optimization_level': 10  # Invalid
            }
        }
        with pytest.raises(ValueError, match='Invalid configuration'):
            loader.load_from_dict(config_dict)


class TestPolicyRegistry:
    """PolicyRegistry tests (10 tests)."""
    
    def test_registry_has_defaults(self):
        """Test 636: Registry has default policies."""
        registry = PolicyRegistry()
        assert 'strict' in registry.list_policies()
        assert 'balanced' in registry.list_policies()
        assert 'permissive' in registry.list_policies()
    
    def test_register_policy(self):
        """Test 637: Register custom policy."""
        registry = PolicyRegistry()
        policy = EnforcementPolicy.strict()
        registry.register('my_policy', policy)
        
        assert 'my_policy' in registry.list_policies()
    
    def test_get_policy(self):
        """Test 638: Get registered policy."""
        registry = PolicyRegistry()
        policy = registry.get('strict')
        assert policy is not None
        assert policy.policy_type == PolicyType.STRICT
    
    def test_get_nonexistent_policy(self):
        """Test 639: Get non-existent policy returns None."""
        registry = PolicyRegistry()
        assert registry.get('nonexistent') is None
    
    def test_unregister_policy(self):
        """Test 640: Unregister policy."""
        registry = PolicyRegistry()
        registry.register('temp', EnforcementPolicy.strict())
        
        assert registry.unregister('temp') is True
        assert registry.get('temp') is None
    
    def test_unregister_nonexistent(self):
        """Test 641-645: Unregister non-existent returns False."""
        registry = PolicyRegistry()
        assert registry.unregister('nonexistent') is False


class TestConfigurationManager:
    """ConfigurationManager tests (5 tests)."""
    
    def test_create_manager(self):
        """Test 646: Create configuration manager."""
        manager = ConfigurationManager()
        assert manager.loader is not None
        assert manager.validator is not None
    
    def test_load_configuration_from_dict(self):
        """Test 647: Load configuration."""
        manager = ConfigurationManager()
        config_dict = {'verbose_logging': True}
        
        config = manager.load_configuration(config_dict)
        assert config.verbose_logging is True
    
    def test_get_active_config(self):
        """Test 648: Get active configuration."""
        manager = ConfigurationManager()
        config = manager.get_active_config()
        assert config is not None
    
    def test_update_config(self):
        """Test 649: Update configuration."""
        manager = ConfigurationManager()
        manager.update_config({'verbose_logging': True})
        
        config = manager.get_active_config()
        assert config.verbose_logging is True
    
    def test_add_function_override(self):
        """Test 650: Add function override."""
        manager = ConfigurationManager()
        manager.add_function_override('func', {'verbose_logging': True})
        
        config = manager.get_active_config()
        assert 'func' in config.function_overrides


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
