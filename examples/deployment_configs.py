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
# File Integrity Identifier: 20e614e47507c844
# ==============================================================================

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