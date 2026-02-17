"""Deployment configuration examples."""

from modules.module_08_language_adapter import (
    AdapterConfiguration,
    EnforcementPolicy,
    PerformanceProfile,
    PipelineConfig,
)

class DeploymentConfigurations:
    """
    Production-ready deployment configurations.
    
    Provides optimized configurations for different environments.
    """

    @staticmethod
    def development_config() -> AdapterConfiguration:
        """
        Development configuration.
        
        - Strict enforcement
        - Verbose logging
        - All diagnostics enabled
        """
        config = AdapterConfiguration(
            enforcement_policy=EnforcementPolicy.strict(),
            performance_profile=PerformanceProfile.debug(),
            verbose_logging=True,
            trace_validation=True,
            dump_inputs=True
        )
        
        return config

    @staticmethod
    def production_config() -> AdapterConfiguration:
        """
        Production configuration.
        
        - Balanced enforcement
        - Error logging only
        - Caching enabled
        """
        config = AdapterConfiguration(
            enforcement_policy=EnforcementPolicy.balanced(),
            performance_profile=PerformanceProfile.fast(),
            verbose_logging=False,
            trace_validation=False
        )
        
        return config

    @staticmethod
    def testing_config() -> AdapterConfiguration:
        """
        Testing configuration.
        
        - Permissive enforcement
        - Full diagnostics
        - Performance profiling
        """
        config = AdapterConfiguration(
            enforcement_policy=EnforcementPolicy.permissive(),
            performance_profile=PerformanceProfile.debug(),
            verbose_logging=True,
            trace_validation=True
        )
        
        return config
