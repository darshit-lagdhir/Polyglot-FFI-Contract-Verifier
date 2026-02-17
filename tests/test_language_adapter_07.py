
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
    PipelineConfig,
)


# ════════════════════════════════════════════════════════════════════════════
# ENFORCEMENT POLICY TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

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
    
    def test_should_enforce_mandatory_always(self):
        """Test 564: Always enforce mandatory regardless of policy."""
        for factory in [EnforcementPolicy.strict, EnforcementPolicy.balanced, EnforcementPolicy.permissive]:
            policy = factory()
            assert policy.should_enforce(ClauseSeverity.MANDATORY) is True
    
    def test_should_enforce_advisory_strict(self):
        """Test 565: Strict enforces advisory."""
        policy = EnforcementPolicy.strict()
        assert policy.should_enforce(ClauseSeverity.ADVISORY) is True
    
    def test_should_enforce_advisory_balanced(self):
        """Test 566: Balanced doesn't enforce advisory."""
        policy = EnforcementPolicy.balanced()
        assert policy.should_enforce(ClauseSeverity.ADVISORY) is False
    
    def test_should_enforce_advisory_permissive(self):
        """Test 567: Permissive doesn't enforce advisory."""
        policy = EnforcementPolicy.permissive()
        assert policy.should_enforce(ClauseSeverity.ADVISORY) is False
    
    def test_should_enforce_optional_when_treat_as_advisory(self):
        """Test 568: Optional enforcement when treat_optional_as_advisory is True."""
        policy = EnforcementPolicy(
            policy_type=PolicyType.CUSTOM,
            treat_optional_as_advisory=True
        )
        assert policy.should_enforce(ClauseSeverity.OPTIONAL) is True
    
    def test_should_not_enforce_optional_when_disabled(self):
        """Test 569: Optional not enforced when treat_optional_as_advisory is False."""
        policy = EnforcementPolicy(
            policy_type=PolicyType.CUSTOM,
            treat_optional_as_advisory=False
        )
        assert policy.should_enforce(ClauseSeverity.OPTIONAL) is False
    
    def test_policy_to_dict_strict(self):
        """Test 570: Strict policy serialization."""
        policy = EnforcementPolicy.strict()
        data = policy.to_dict()
        assert data['policy_type'] == 'strict'
        assert data['fail_fast'] is True
        assert data['treat_advisory_as_mandatory'] is True
        assert data['max_violations'] == 1
    
    def test_policy_to_dict_balanced(self):
        """Test 571: Balanced policy serialization."""
        policy = EnforcementPolicy.balanced()
        data = policy.to_dict()
        assert data['policy_type'] == 'balanced'
        assert data['fail_fast'] is False
        assert data['allow_missing_clauses'] is True
        assert data['max_violations'] == 10
    
    def test_policy_to_dict_permissive(self):
        """Test 572: Permissive policy serialization."""
        policy = EnforcementPolicy.permissive()
        data = policy.to_dict()
        assert data['policy_type'] == 'permissive'
        assert data['max_violations'] == 0
    
    def test_custom_policy(self):
        """Test 573: Custom policy creation."""
        policy = EnforcementPolicy(
            policy_type=PolicyType.CUSTOM,
            fail_fast=False,
            max_violations=5
        )
        assert policy.policy_type == PolicyType.CUSTOM
        assert policy.max_violations == 5
    
    def test_violation_callback_assignment(self):
        """Test 574: Policy with callback."""
        called = []
        def callback(violation):
            called.append(violation)
        
        policy = EnforcementPolicy(
            policy_type=PolicyType.CUSTOM,
            violation_callback=callback
        )
        assert policy.violation_callback is not None
        policy.violation_callback('test_violation')
        assert len(called) == 1
        assert called[0] == 'test_violation'
    
    def test_strict_no_missing_clauses(self):
        """Test 575: Strict disallows missing clauses."""
        policy = EnforcementPolicy.strict()
        assert policy.allow_missing_clauses is False
    
    def test_balanced_allows_missing_clauses(self):
        """Test 576: Balanced allows missing clauses."""
        policy = EnforcementPolicy.balanced()
        assert policy.allow_missing_clauses is True
    
    def test_strict_max_violations_is_one(self):
        """Test 577: Strict stops after 1 violation."""
        policy = EnforcementPolicy.strict()
        assert policy.max_violations == 1
    
    def test_permissive_unlimited_violations(self):
        """Test 578: Permissive has unlimited violations."""
        policy = EnforcementPolicy.permissive()
        assert policy.max_violations == 0
    
    def test_policy_type_enum_values(self):
        """Test 579: PolicyType enum values."""
        assert PolicyType.STRICT.value == 'strict'
        assert PolicyType.BALANCED.value == 'balanced'
        assert PolicyType.PERMISSIVE.value == 'permissive'
        assert PolicyType.CUSTOM.value == 'custom'
    
    def test_policy_to_dict_has_all_keys(self):
        """Test 580: Policy to_dict contains all expected keys."""
        policy = EnforcementPolicy.strict()
        data = policy.to_dict()
        expected_keys = {'policy_type', 'fail_fast', 'treat_advisory_as_mandatory',
                         'treat_optional_as_advisory', 'allow_missing_clauses', 'max_violations'}
        assert set(data.keys()) == expected_keys


# ════════════════════════════════════════════════════════════════════════════
# PERFORMANCE PROFILE TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

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
    
    def test_profile_to_dict_fast(self):
        """Test 585: Fast profile serialization."""
        profile = PerformanceProfile.fast()
        data = profile.to_dict()
        assert data['optimization_level'] == 3
        assert data['enable_caching'] is True
        assert data['parallel_validation'] is True
    
    def test_fast_profile_parallel_enabled(self):
        """Test 586: Fast profile enables parallel validation."""
        profile = PerformanceProfile.fast()
        assert profile.parallel_validation is True
    
    def test_fast_profile_lazy_enabled(self):
        """Test 587: Fast profile enables lazy validation."""
        profile = PerformanceProfile.fast()
        assert profile.lazy_validation is True
    
    def test_fast_profile_low_timeout(self):
        """Test 588: Fast profile has low timeout."""
        profile = PerformanceProfile.fast()
        assert profile.clause_timeout_ms == 100
    
    def test_debug_profile_high_timeout(self):
        """Test 589: Debug profile has high timeout."""
        profile = PerformanceProfile.debug()
        assert profile.clause_timeout_ms == 5000
    
    def test_balanced_profile_no_profiling(self):
        """Test 590: Balanced profile disables profiling."""
        profile = PerformanceProfile.balanced()
        assert profile.profile_execution is False
    
    def test_debug_profile_no_caching(self):
        """Test 591: Debug profile disables caching."""
        profile = PerformanceProfile.debug()
        assert profile.enable_caching is False
    
    def test_profile_to_dict_has_all_keys(self):
        """Test 592: Profile to_dict contains all expected keys."""
        profile = PerformanceProfile.balanced()
        data = profile.to_dict()
        expected_keys = {'optimization_level', 'enable_caching', 'parallel_validation',
                         'lazy_validation', 'clause_timeout_ms', 'profile_execution'}
        assert set(data.keys()) == expected_keys
    
    def test_default_profile_values(self):
        """Test 593: Default profile field values."""
        profile = PerformanceProfile()
        assert profile.optimization_level == 1
        assert profile.enable_caching is False
        assert profile.clause_timeout_ms == 1000
    
    def test_custom_timeout(self):
        """Test 594: Custom clause timeout."""
        profile = PerformanceProfile(clause_timeout_ms=500)
        assert profile.clause_timeout_ms == 500
    
    def test_profile_to_dict_debug(self):
        """Test 595: Debug profile serialization."""
        profile = PerformanceProfile.debug()
        data = profile.to_dict()
        assert data['optimization_level'] == 0
        assert data['profile_execution'] is True


# ════════════════════════════════════════════════════════════════════════════
# ADAPTER CONFIGURATION TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

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
        assert len(config.ignore_clause_types) == 2
    
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
        """Test 605: Config serialization."""
        config = AdapterConfiguration()
        data = config.to_dict()
        assert 'enforcement_policy' in data
        assert 'performance_profile' in data
    
    def test_config_to_dict_has_all_keys(self):
        """Test 606: Config to_dict contains all expected keys."""
        config = AdapterConfiguration()
        data = config.to_dict()
        expected_keys = {'enforcement_policy', 'performance_profile', 'pipeline_config',
                         'verbose_logging', 'trace_validation', 'dump_inputs',
                         'dump_memory', 'ignore_clause_types', 'require_clause_types'}
        assert set(data.keys()) == expected_keys
    
    def test_default_debugging_disabled(self):
        """Test 607: Default config has debugging disabled."""
        config = AdapterConfiguration()
        assert config.verbose_logging is False
        assert config.trace_validation is False
        assert config.dump_inputs is False
        assert config.dump_memory is False
    
    def test_effective_config_none_function(self):
        """Test 608: Effective config with None function returns self."""
        config = AdapterConfiguration(verbose_logging=True)
        effective = config.get_effective_config(None)
        assert effective is config
    
    def test_effective_config_does_not_modify_original(self):
        """Test 609: Effective config override doesn't modify original."""
        config = AdapterConfiguration(verbose_logging=False)
        config.function_overrides['func'] = {'verbose_logging': True}
        
        _ = config.get_effective_config('func')
        assert config.verbose_logging is False
    
    def test_config_dump_options(self):
        """Test 610: Config dump memory and inputs options."""
        config = AdapterConfiguration(dump_inputs=True, dump_memory=True)
        assert config.dump_inputs is True
        assert config.dump_memory is True


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION VALIDATOR TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestConfigurationValidator:
    """ConfigurationValidator tests (10 tests)."""
    
    def test_validate_valid_config(self):
        """Test 611: Valid configuration passes."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        
        valid, errors = validator.validate(config)
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_invalid_optimization_high(self):
        """Test 612: Optimization level too high."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.optimization_level = 5
        
        valid, errors = validator.validate(config)
        assert valid is False
        assert any('optimization_level' in e for e in errors)
    
    def test_validate_invalid_optimization_negative(self):
        """Test 613: Negative optimization level."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.optimization_level = -1
        
        valid, errors = validator.validate(config)
        assert valid is False
    
    def test_validate_negative_timeout(self):
        """Test 614: Negative timeout fails."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.clause_timeout_ms = -1
        
        valid, errors = validator.validate(config)
        assert valid is False
    
    def test_validate_zero_timeout(self):
        """Test 615: Zero timeout fails."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.clause_timeout_ms = 0
        
        valid, errors = validator.validate(config)
        assert valid is False
    
    def test_validate_negative_max_violations(self):
        """Test 616: Negative max violations fails."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.enforcement_policy.max_violations = -1
        
        valid, errors = validator.validate(config)
        assert valid is False
    
    def test_validate_conflicting_lazy_failfast(self):
        """Test 617: Lazy validation + fail_fast conflict detected."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.lazy_validation = True
        config.enforcement_policy.fail_fast = True
        
        valid, errors = validator.validate(config)
        assert valid is False
        assert any('lazy_validation' in e for e in errors)
    
    def test_validate_overlapping_clause_sets(self):
        """Test 618: Overlapping ignore/require sets."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration(
            ignore_clause_types={'range'},
            require_clause_types={'range'}
        )
        
        valid, errors = validator.validate(config)
        assert valid is False
    
    def test_validate_valid_boundary_optimization(self):
        """Test 619: Valid boundary optimization levels (0 and 3)."""
        validator = ConfigurationValidator()
        for level in [0, 1, 2, 3]:
            config = AdapterConfiguration()
            config.performance_profile.optimization_level = level
            valid, errors = validator.validate(config)
            assert valid is True, f"Level {level} should be valid"
    
    def test_validate_multiple_errors(self):
        """Test 620: Multiple errors detected simultaneously."""
        validator = ConfigurationValidator()
        config = AdapterConfiguration()
        config.performance_profile.optimization_level = 10
        config.performance_profile.clause_timeout_ms = -5
        config.enforcement_policy.max_violations = -1
        
        valid, errors = validator.validate(config)
        assert valid is False
        assert len(errors) >= 3


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION LOADER TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestConfigurationLoader:
    """ConfigurationLoader tests (15 tests)."""
    
    def test_load_from_empty_dict(self):
        """Test 621: Load from empty dict."""
        loader = ConfigurationLoader()
        config = loader.load_from_dict({})
        assert config is not None
    
    def test_load_policy_from_dict(self):
        """Test 622: Load enforcement policy from dict."""
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
        """Test 623: Load performance profile from dict."""
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
        assert config.trace_validation is True
    
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
        """Test 627: Invalid config raises error."""
        loader = ConfigurationLoader()
        config_dict = {
            'performance_profile': {
                'optimization_level': 10  # Invalid
            }
        }
        with pytest.raises(ValueError, match='Invalid configuration'):
            loader.load_from_dict(config_dict)
    
    def test_load_permissive_policy_from_dict(self):
        """Test 628: Load permissive policy from dict."""
        loader = ConfigurationLoader()
        config_dict = {
            'enforcement_policy': {
                'policy_type': 'permissive',
                'fail_fast': False
            }
        }
        config = loader.load_from_dict(config_dict)
        assert config.enforcement_policy.policy_type == PolicyType.PERMISSIVE
    
    def test_load_with_max_violations(self):
        """Test 629: Load config with max_violations."""
        loader = ConfigurationLoader()
        config_dict = {
            'enforcement_policy': {
                'policy_type': 'balanced',
                'max_violations': 25
            }
        }
        config = loader.load_from_dict(config_dict)
        assert config.enforcement_policy.max_violations == 25
    
    def test_load_env_returns_dict(self):
        """Test 630: Load from env returns dictionary."""
        loader = ConfigurationLoader()
        result = loader.load_from_env(prefix="NONEXISTENT_PREFIX_")
        assert isinstance(result, dict)
    
    def test_load_from_file_strict_policy(self):
        """Test 631: Load strict policy from file."""
        loader = ConfigurationLoader()
        config_dict = {
            'enforcement_policy': {'policy_type': 'strict', 'fail_fast': True}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config_dict, f)
            path = f.name
        
        try:
            config = loader.load_from_file(path)
            assert config.enforcement_policy.policy_type == PolicyType.STRICT
        finally:
            Path(path).unlink()
    
    def test_load_caching_from_dict(self):
        """Test 632: Load caching option from dict."""
        loader = ConfigurationLoader()
        config_dict = {
            'performance_profile': {
                'enable_caching': True,
                'clause_timeout_ms': 500
            }
        }
        config = loader.load_from_dict(config_dict)
        assert config.performance_profile.enable_caching is True
        assert config.performance_profile.clause_timeout_ms == 500
    
    def test_load_validator_initialized(self):
        """Test 633: Loader has validator initialized."""
        loader = ConfigurationLoader()
        assert loader.validator is not None
        assert isinstance(loader.validator, ConfigurationValidator)
    
    def test_load_partial_performance_dict(self):
        """Test 634: Load partial performance profile uses defaults."""
        loader = ConfigurationLoader()
        config_dict = {
            'performance_profile': {
                'optimization_level': 2
            }
        }
        config = loader.load_from_dict(config_dict)
        assert config.performance_profile.optimization_level == 2
        assert config.performance_profile.clause_timeout_ms == 1000  # default
    
    def test_load_combined_policy_and_profile(self):
        """Test 635: Load both policy and profile together."""
        loader = ConfigurationLoader()
        config_dict = {
            'enforcement_policy': {'policy_type': 'strict', 'fail_fast': True},
            'performance_profile': {'optimization_level': 2},
            'verbose_logging': True
        }
        config = loader.load_from_dict(config_dict)
        assert config.enforcement_policy.policy_type == PolicyType.STRICT
        assert config.performance_profile.optimization_level == 2
        assert config.verbose_logging is True


# ════════════════════════════════════════════════════════════════════════════
# POLICY REGISTRY TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

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
        """Test 641: Unregister non-existent returns False."""
        registry = PolicyRegistry()
        assert registry.unregister('nonexistent') is False
    
    def test_registry_default_count(self):
        """Test 642: Registry starts with 3 default policies."""
        registry = PolicyRegistry()
        assert len(registry.list_policies()) == 3
    
    def test_register_overwrite_existing(self):
        """Test 643: Re-registering overwrites existing policy."""
        registry = PolicyRegistry()
        custom = EnforcementPolicy(policy_type=PolicyType.CUSTOM, max_violations=99)
        registry.register('strict', custom)
        retrieved = registry.get('strict')
        assert retrieved.policy_type == PolicyType.CUSTOM
        assert retrieved.max_violations == 99
    
    def test_get_balanced_policy(self):
        """Test 644: Get balanced policy from registry."""
        registry = PolicyRegistry()
        policy = registry.get('balanced')
        assert policy is not None
        assert policy.policy_type == PolicyType.BALANCED
    
    def test_get_permissive_policy(self):
        """Test 645: Get permissive policy from registry."""
        registry = PolicyRegistry()
        policy = registry.get('permissive')
        assert policy is not None
        assert policy.policy_type == PolicyType.PERMISSIVE


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION MANAGER TESTS (5 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestConfigurationManager:
    """ConfigurationManager tests (5 tests)."""
    
    def test_create_manager(self):
        """Test 646: Create configuration manager."""
        manager = ConfigurationManager()
        assert manager.loader is not None
        assert manager.validator is not None
        assert manager.policy_registry is not None
    
    def test_load_configuration_from_dict(self):
        """Test 647: Load configuration from dict."""
        manager = ConfigurationManager()
        config_dict = {'verbose_logging': True}
        config = manager.load_configuration(config_dict)
        assert config.verbose_logging is True
        assert manager.active_config is config
    
    def test_get_active_config_default(self):
        """Test 648: Get active configuration creates default when none set."""
        manager = ConfigurationManager()
        config = manager.get_active_config()
        assert config is not None
        assert isinstance(config, AdapterConfiguration)
    
    def test_update_config(self):
        """Test 649: Update active configuration."""
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
        assert config.function_overrides['func']['verbose_logging'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
