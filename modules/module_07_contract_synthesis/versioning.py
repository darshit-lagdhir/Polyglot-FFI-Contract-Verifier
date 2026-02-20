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
# File Integrity Identifier: 25bd0df8f07e28a3
# ==============================================================================

"""
Module 07: Synthesis Versioning (Prompt 5/15)

Synthesis version management, rule evolution tracking, and historical contract compatibility.

Responsibilities:
- Synthesis version semantic versioning
- Rule registry and evolution tracking
- Fingerprint computation
- Regression detection
- Migration utilities
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
import hashlib
import json
import logging

# Add project root to sys.path if needed for imports
# Assuming standard structure where this file is in modules/module_07...
# and we need to import from other modules.

from module_05_ir_normalization.ir_entities import InterfaceUnit as IRInterfaceUnit, EntityKind, TypeEntity, FunctionSymbol
from module_06_contract_schema.contract_entities import ContractDocument
# Assuming ContractSerializer exists in module_06_contract_schema.contract_serialization
# If not, we might need to mock or implement a simple serializer for fingerprinting.
# Let's check imports.
try:
    from module_06_contract_schema.contract_serialization import ContractSerializer
except ImportError:
    # If not present, we will implement a local helper for fingerprinting serialization
    ContractSerializer = None

logger = logging.getLogger(__name__)

# ============================================================================
# VERSION COMPARISON
# ============================================================================

def version_compare(v1: str, op: str, v2: str) -> bool:
    """
    Compare semantic versions.
    
    Args:
        v1: First version (e.g., "1.2.3")
        op: Comparison operator ("==", "!=", "<", "<=", ">", ">=")
        v2: Second version
        
    Returns:
        Result of comparison
    """
    def parse_version(v: str) -> Tuple[int, int, int]:
        parts = v.split('.')
        if len(parts) != 3:
            # Handle partial versions or invalid formats gracefully if needed,
            # but standard requires x.y.z
            # If standard is strict:
            raise ValueError(f"Invalid version format: {v}")
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    
    try:
        v1_tuple = parse_version(v1)
        v2_tuple = parse_version(v2)
    except ValueError as e:
        logger.error(f"Version parsing error: {e}")
        raise

    if op == "==":
        return v1_tuple == v2_tuple
    elif op == "!=":
        return v1_tuple != v2_tuple
    elif op == "<":
        return v1_tuple < v2_tuple
    elif op == "<=":
        return v1_tuple <= v2_tuple
    elif op == ">":
        return v1_tuple > v2_tuple
    elif op == ">=":
        return v1_tuple >= v2_tuple
    else:
        raise ValueError(f"Invalid operator: {op}")

# ============================================================================
# SYNTHESIS RULE DEFINITION
# ============================================================================

@dataclass
class SynthesisRule:
    """
    Registered synthesis rule with immutable identity.
    
    Rules have immutable IDs. When logic changes, create new rule ID.
    """
    
    rule_id: str  # Immutable identifier
    rule_version: str  # Semantic version
    category: str  # "layout", "nullability", "relational", etc.
    description: str
    introduced_in_synthesis: str  # Synthesis version that introduced rule
    deprecated_in_synthesis: Optional[str] = None  # If deprecated
    replaced_by: Optional[str] = None  # Replacement rule ID

    def is_active_in_version(self, synthesis_version: str) -> bool:
        """Check if rule is active for given synthesis version."""
        # Must be introduced before or at version
        if not version_compare(self.introduced_in_synthesis, "<=", synthesis_version):
            return False
        
        # Must not be deprecated at version
        if self.deprecated_in_synthesis:
            if version_compare(self.deprecated_in_synthesis, "<=", synthesis_version):
                return False
        
        return True

# ============================================================================
# RULE REGISTRY
# ============================================================================

class RuleRegistryError(Exception):
    """Rule registry error."""
    pass

class RuleRegistry:
    """
    Registry of all synthesis rules.
    
    Singleton registry tracking rule evolution across synthesis versions.
    """
    
    _rules: Dict[str, SynthesisRule] = {}
    _initialized: bool = False
    
    @classmethod
    def initialize_default_rules(cls):
        """Initialize default rule set."""
        if cls._initialized:
            return
        
        # Register default rules from v1.0.0
        cls.register(SynthesisRule(
            rule_id="layout_structural_projection_v1",
            rule_version="1.0.0",
            category="layout",
            description="Project IR type layouts to layout clauses",
            introduced_in_synthesis="1.0.0"
        ))
        
        cls.register(SynthesisRule(
            rule_id="pointer_nullability_default_v1",
            rule_version="1.0.0",
            category="nullability",
            description="Default pointer parameters to non-null",
            introduced_in_synthesis="1.0.0"
        ))
        
        cls.register(SynthesisRule(
            rule_id="return_ownership_default_v1",
            rule_version="1.0.0",
            category="ownership",
            description="Default returned pointers to caller-owned",
            introduced_in_synthesis="1.0.0"
        ))
        
        cls.register(SynthesisRule(
            rule_id="buffer_length_pattern_detection_v1",
            rule_version="1.0.0",
            category="relational",
            description="Detect buffer-length parameter pairs",
            introduced_in_synthesis="1.0.0"
        ))
        
        cls.register(SynthesisRule(
            rule_id="calling_convention_projection_v1",
            rule_version="1.0.0",
            category="calling_convention",
            description="Project calling conventions from IR",
            introduced_in_synthesis="1.0.0"
        ))
        
        cls.register(SynthesisRule(
            rule_id="abi_fingerprint_projection_v1",
            rule_version="1.0.0",
            category="abi",
            description="Project ABI fingerprints to compatibility clauses",
            introduced_in_synthesis="1.0.0"
        ))
        
        # Contextual analysis rules (v1.1.0+)
        cls.register(SynthesisRule(
            rule_id="ownership_symmetry_detection_v1",
            rule_version="1.1.0",
            category="ownership",
            description="Detect create/destroy function pairs for ownership",
            introduced_in_synthesis="1.1.0"
        ))
        
        cls.register(SynthesisRule(
            rule_id="conditional_nullability_refinement_v1",
            rule_version="1.1.0",
            category="nullability",
            description="Generate conditional nullability based on size parameters",
            introduced_in_synthesis="1.1.0"
        ))
        
        cls.register(SynthesisRule(
            rule_id="severity_escalation_pattern_v1",
            rule_version="1.1.0",
            category="severity",
            description="Escalate severity based on interface-wide patterns",
            introduced_in_synthesis="1.1.0"
        ))
        
        cls._initialized = True
    
    @classmethod
    def register(cls, rule: SynthesisRule):
        """Register a synthesis rule."""
        if rule.rule_id in cls._rules:
            # Check if identical to allow idempotent initialization
            existing = cls._rules[rule.rule_id]
            if existing == rule:
                return
            raise RuleRegistryError(f"Rule {rule.rule_id} already registered with different definition")
        cls._rules[rule.rule_id] = rule
        logger.debug(f"Registered rule: {rule.rule_id}")
    
    @classmethod
    def get_rule(cls, rule_id: str) -> Optional[SynthesisRule]:
        """Retrieve rule by ID."""
        return cls._rules.get(rule_id)
    
    @classmethod
    def get_rules_for_synthesis_version(cls, synthesis_version: str) -> List[SynthesisRule]:
        """Get all rules applicable to synthesis version."""
        return [
            rule for rule in cls._rules.values()
            if rule.is_active_in_version(synthesis_version)
        ]
    
    @classmethod
    def get_all_rules(cls) -> List[SynthesisRule]:
        """Get all registered rules."""
        return list(cls._rules.values())

# Initialize default rules on verification engine start/module load
RuleRegistry.initialize_default_rules()

# ============================================================================
# SYNTHESIS FINGERPRINTING
# ============================================================================

@dataclass
class SynthesisFingerprint:
    """
    Cryptographic fingerprint of synthesis operation.
    
    Used for determinism verification and regression detection.
    """
    
    synthesis_version: str
    ir_fingerprint: str
    ruleset_fingerprint: str
    config_fingerprint: str
    output_fingerprint: str
    
    def compute_composite_hash(self) -> str:
        """Compute composite hash of all components."""
        data = (
            f"{self.synthesis_version}:"
            f"{self.ir_fingerprint}:"
            f"{self.ruleset_fingerprint}:"
            f"{self.config_fingerprint}:"
            f"{self.output_fingerprint}"
        )
        return hashlib.sha256(data.encode()).hexdigest()

class FingerprintComputer:
    """Computes synthesis fingerprints for reproducibility checking."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def compute_ir_fingerprint(self, ir_unit: IRInterfaceUnit) -> str:
        """Compute fingerprint of IR artifact."""
        # Serialize IR deterministically
        ir_dict = self._ir_to_dict(ir_unit)
        serialized = json.dumps(
            ir_dict,
            sort_keys=True,  # Deterministic ordering
            separators=(',', ':')  # No whitespace variance
        )
        return hashlib.sha256(serialized.encode()).hexdigest()
        
    def _ir_to_dict(self, ir_unit: IRInterfaceUnit) -> Dict:
        """Convert IR to dict for fingerprinting."""
        # Use existing to_dict if consistent, or simplified one
        if hasattr(ir_unit, 'to_dict'):
            return ir_unit.to_dict()
        
        # Fallback simplified conversion
        return {
            "entity_id": getattr(ir_unit, "entity_id", "unknown"),
            "target_architecture": getattr(ir_unit, "target_architecture", ""),
            "pointer_width": getattr(ir_unit, "pointer_width", 0),
            # Add other deterministic fields
        }

    def compute_ruleset_fingerprint(self, synthesis_version: str) -> str:
        """Compute fingerprint of active ruleset."""
        rules = RuleRegistry.get_rules_for_synthesis_version(synthesis_version)
        
        # Serialize rule IDs deterministically
        rule_ids = sorted([r.rule_id for r in rules])
        serialized = json.dumps(rule_ids, separators=(',', ':'))
        
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def compute_config_fingerprint(self, config) -> str:
        """Compute fingerprint of synthesis configuration."""
        # Assuming config object has semantic fields
        config_dict = {
            "synthesis_version": getattr(config, "synthesis_version", "1.0.0"),
            "default_pointer_nonnull": getattr(config, "default_pointer_nonnull", True),
            "default_return_ownership": getattr(config, "default_return_ownership", "caller"),
            "strict_mode": getattr(config, "strict_mode", True)
        }
        serialized = json.dumps(config_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def compute_output_fingerprint(self, contract: ContractDocument) -> str:
        """Compute fingerprint of generated contract."""
        if ContractSerializer:
            serializer = ContractSerializer()
            serialized = serializer.serialize(contract)
        else:
            # Fallback simple serialization if serializer not available
            # Just structure to dict
            # Assuming contract structure is serializable by default tools or we make a simple dict
            serialized = str(contract) # Very weak, but fallback
            
        return hashlib.sha256(serialized.encode()).hexdigest()
        
    def compute_full_fingerprint(
        self,
        ir_unit: IRInterfaceUnit,
        config,
        contract: ContractDocument
    ) -> SynthesisFingerprint:
        """Compute full synthesis fingerprint."""
        return SynthesisFingerprint(
            synthesis_version=getattr(config, "synthesis_version", "1.0.0"),
            ir_fingerprint=self.compute_ir_fingerprint(ir_unit),
            ruleset_fingerprint=self.compute_ruleset_fingerprint(getattr(config, "synthesis_version", "1.0.0")),
            config_fingerprint=self.compute_config_fingerprint(config),
            output_fingerprint=self.compute_output_fingerprint(contract)
        )

# ============================================================================
# REGRESSION DETECTION
# ============================================================================

@dataclass
class RegressionReport:
    """Report of detected regression."""
    
    regression_type: str
    message: str = ""
    expected_version: Optional[str] = None
    actual_version: Optional[str] = None
    severity: str = "warning"  # "info", "warning", "error"

class RegressionDetector:
    """Detects synthesis regressions in CI/CD."""
    
    def __init__(self, baseline_dir: Path = Path(".synthesis_baselines")):
        self.baseline_dir = baseline_dir
        self.logger = logging.getLogger(__name__)
        
    def record_baseline(
        self,
        ir_name: str,
        fingerprint: SynthesisFingerprint
    ):
        """Record baseline for regression detection."""
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        
        baseline = {
            "fingerprint": {
                "synthesis_version": fingerprint.synthesis_version,
                "ir_fingerprint": fingerprint.ir_fingerprint,
                "ruleset_fingerprint": fingerprint.ruleset_fingerprint,
                "config_fingerprint": fingerprint.config_fingerprint,
                "output_fingerprint": fingerprint.output_fingerprint,
                "composite_hash": fingerprint.compute_composite_hash()
            },
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        baseline_file = self.baseline_dir / f"{ir_name}_baseline.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline, f, indent=2)
        
        self.logger.info(f"Recorded baseline for {ir_name}")
        
    def check_for_regression(
        self,
        ir_name: str,
        current_fingerprint: SynthesisFingerprint
    ) -> Optional[RegressionReport]:
        """Check if synthesis output has regressed."""
        baseline_file = self.baseline_dir / f"{ir_name}_baseline.json"
        
        if not baseline_file.exists():
            return None  # No baseline
        
        try:
            with open(baseline_file) as f:
                baseline = json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load baseline for {ir_name}: {e}")
            return None
        
        baseline_fp = baseline["fingerprint"]
        
        # Check IR fingerprint - if input changed, baseline is invalid for strictly regression test
        if current_fingerprint.ir_fingerprint != baseline_fp["ir_fingerprint"]:
            # Input changed, so output change is expected. Not a regression in the strict sense.
            return None
            
        # Check version
        if current_fingerprint.synthesis_version != baseline_fp["synthesis_version"]:
            return RegressionReport(
                regression_type="version_change",
                expected_version=baseline_fp["synthesis_version"],
                actual_version=current_fingerprint.synthesis_version,
                severity="info",
                message=f"Synthesis version changed: {baseline_fp['synthesis_version']} -> {current_fingerprint.synthesis_version}"
            )
            
        # Check output - determinism check
        if current_fingerprint.output_fingerprint != baseline_fp["output_fingerprint"]:
            return RegressionReport(
                regression_type="determinism_violation",
                message="Synthesis output changed with identical input and version",
                severity="error"
            )
            
        return None  # No regression

# ============================================================================
# DETERMINISM VERIFICATION
# ============================================================================

@dataclass
class DeterminismReport:
    """Report on determinism verification."""
    
    deterministic: bool
    iterations_tested: int = 0
    fingerprint: Optional[str] = None
    reason: str = ""
    unique_fingerprints: int = 0

class DeterminismVerifier:
    """Verifies synthesis determinism."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def verify_determinism(
        self,
        ir_unit: IRInterfaceUnit,
        synthesis_version: str,
        iterations: int = 10
    ) -> DeterminismReport:
        """
        Verify synthesis produces identical output across multiple runs.
        
        Args:
            ir_unit: IR to synthesize
            synthesis_version: Synthesis version to test
            iterations: Number of synthesis runs
            
        Returns:
            Report on determinism verification
        """
        # Circular import check
        # Ideally, we pass the engine class or instance, but pattern suggests local import
        try:
            from .synthesis_engine import SynthesisEngine, SynthesisConfig
        except ImportError:
            # If standard imports fail, we might be in a different context
            # Assuming relative import works if this file is in correct module
            from module_07_contract_synthesis.synthesis_engine import SynthesisEngine, SynthesisConfig

        config = SynthesisConfig(synthesis_version=synthesis_version)
        engine = SynthesisEngine(config)
        computer = FingerprintComputer()
        
        fingerprints = []
        
        for i in range(iterations):
            # We use distinct target_interface_id just for logs/context, 
            # output content *contract body* should be deterministic regardless of Interface ID usually,
            # BUT ContractHeader includes target_interface_id.
            # Thus, if target_interface_id varies, output fingerprint varies!
            # We MUST use same target_interface_id for determinism check.
            result = engine.synthesize(ir_unit, f"determinism_test_interface")
            
            if not result.success:
                return DeterminismReport(
                    deterministic=False,
                    reason=f"Synthesis failed on iteration {i}: {result.errors}"
                )
            
            fp = computer.compute_output_fingerprint(result.contract)
            fingerprints.append(fp)
            
        # Check all fingerprints identical
        if len(set(fingerprints)) == 1:
            return DeterminismReport(
                deterministic=True,
                iterations_tested=iterations,
                fingerprint=fingerprints[0]
            )
        else:
            return DeterminismReport(
                deterministic=False,
                reason=f"Output varied across {iterations} runs",
                unique_fingerprints=len(set(fingerprints)),
                iterations_tested=iterations
            )