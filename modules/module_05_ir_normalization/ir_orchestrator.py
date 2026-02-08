"""
Module 05: IR Orchestration Pipeline

Complete end-to-end orchestration of IR normalization.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import time
import hashlib
from datetime import datetime, timezone

from .ir_entities import (
    InterfaceUnit, Endianness, TypeRegistry, ScalarKind, ArrayKind
)
from .type_normalization import (
    TypeNormalizationPipeline, SymbolNormalizationPipeline,
    TypedefResolver, RawTypeData, RawFunctionData,
    RawVariableData, RawParameterData, RawFieldData
)
from .ir_validation import IRValidationOrchestrator, ValidationReport
from .ir_serialization import (
    IRArtifact, IRArtifactManager, compute_artifact_hash
)
from .ir_diff import IRDiffComputer, recommend_version_bump

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class IRNormalizationConfig:
    """Config for IR normalization pipeline."""
    
    # Input (from Module 04)
    input_artifact_path: Path
    
    # Output
    output_dir: Path = Path('.pfcv/ir_artifacts')
    compress_artifacts: bool = True
    
    # Validation
    enable_validation: bool = True
    fail_on_validation_errors: bool = True
    
    # Caching
    enable_caching: bool = True
    cache_dir: Path = Path('.pfcv/cache/module_05')
    
    # Diffing
    enable_diffing: bool = False
    baseline_artifact_path: Optional[Path] = None
    
    # Reporting
    generate_report: bool = True
    report_output_path: Optional[Path] = None
    
    # Performance
    enable_profiling: bool = False
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        
        if not self.input_artifact_path.exists():
            errors.append(f"Input artifact not found: {self.input_artifact_path}")
        
        if self.enable_diffing and not self.baseline_artifact_path:
            errors.append("Diffing enabled but no baseline specified")
        
        return errors

# ============================================================================
# STATE TRACKING
# ============================================================================

@dataclass
class OrchestrationState:
    """Tracks orchestrator state during execution."""
    
    current_stage: str = "initialization"
    stages_completed: List[str] = field(default_factory=list)
    stage_timings: Dict[str, float] = field(default_factory=dict)
    total_duration: float = 0.0
    
    types_normalized: int = 0
    symbols_normalized: int = 0
    
    validation_passed: bool = False
    validation_errors: int = 0
    
    output_artifact_path: Optional[Path] = None
    
    diff_computed: bool = False
    changes_detected: int = 0
    abi_impact: str = "neutral"

# ============================================================================
# ERROR HANDLING
# ============================================================================

class OrchestrationError(Exception):
    """Base class for orchestration errors."""
    
    def __init__(self, stage: str, message: str, cause: Optional[Exception] = None):
        self.stage = stage
        self.message = message
        self.cause = cause
        super().__init__(f"[{stage}] {message}")

class ConfigError(OrchestrationError):
    """Config is invalid."""
    pass

class NormalizationFailure(OrchestrationError):
    """Normalization stage failed."""
    pass

class ValidationFailure(OrchestrationError):
    """Validation stage failed."""
    pass

# ============================================================================
# PROGRESS REPORTING
# ============================================================================

class ProgressReporter:
    """Reports orchestration progress."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.start_time: Optional[float] = None
    
    def start_pipeline(self):
        """Signal pipeline start."""
        self.start_time = time.time()
        if self.verbose:
            print("=" * 80)
            print("IR NORMALIZATION PIPELINE")
            print("=" * 80)
    
    def start_stage(self, stage_name: str):
        """Signal stage start."""
        if self.verbose:
            print(f"\n[{stage_name}] Starting...")
    
    def complete_stage(self, stage_name: str, duration: float):
        """Signal stage completion."""
        if self.verbose:
            print(f"[{stage_name}] Complete ({duration:.2f}s)")
    
    def complete_pipeline(self, total_duration: float):
        """Signal pipeline completion."""
        if self.verbose:
            print("\n" + "=" * 80)
            print(f"Pipeline complete ({total_duration:.2f}s)")
            print("=" * 80)
    
    def report_error(self, error: OrchestrationError):
        """Report error."""
        if self.verbose:
            print(f"\nERROR [{error.stage}]: {error.message}")

# ============================================================================
# ORCHESTRATION REPORT
# ============================================================================

@dataclass
class OrchestrationReport:
    """Complete orchestration report."""
    
    pipeline_version: str = "1.0.0"
    execution_timestamp: str = ""
    total_duration: float = 0.0
    
    input_artifact_path: str = ""
    input_artifact_hash: str = ""
    
    types_normalized: int = 0
    symbols_normalized: int = 0
    
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    output_artifact_path: str = ""
    output_artifact_hash: str = ""
    artifact_size_bytes: int = 0
    
    diff_summary: Optional[str] = None
    abi_impact: str = "neutral"
    version_bump: str = "none"
    
    stage_timings: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize report."""
        return {
            'pipeline_version': self.pipeline_version,
            'execution_timestamp': self.execution_timestamp,
            'total_duration': self.total_duration,
            'input_artifact_path': self.input_artifact_path,
            'types_normalized': self.types_normalized,
            'symbols_normalized': self.symbols_normalized,
            'validation_passed': self.validation_passed,
            'validation_error_count': len(self.validation_errors),
            'output_artifact_path': self.output_artifact_path,
            'abi_impact': self.abi_impact,
            'version_bump': self.version_bump,
            'stage_timings': self.stage_timings
        }
    
    def save(self, output_path: Path):
        """Save report to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)

# ============================================================================
# IR ORCHESTRATOR
# ============================================================================

class IROrchestrator:
    """
    Orchestrates complete IR normalization pipeline.
    """
    
    def __init__(self, config: IRNormalizationConfig):
        """Initialize orchestrator."""
        self.config = config
        self.state = OrchestrationState()
        self.reporter = ProgressReporter(verbose=True)
        self.report = OrchestrationReport()
        
        # Internal components
        self.type_registry = TypeRegistry()
        self.typedef_resolver = TypedefResolver()
        self.interface_unit: Optional[InterfaceUnit] = None
        self.raw_data: Dict[str, Any] = {}
        self.artifact: Optional[IRArtifact] = None
        self.validation_report: Optional[ValidationReport] = None
    
    def execute(self) -> OrchestrationReport:
        """Execute complete IR normalization pipeline."""
        start_time = time.time()
        self.reporter.start_pipeline()
        
        try:
            self._validate_configuration()
            
            # Check cache
            if self.config.enable_caching:
                cached_artifact = self._check_cache()
                if cached_artifact:
                    pass
            
            self._stage_input_preparation()
            self._stage_type_normalization()
            self._stage_symbol_normalization()
            self._stage_validation()
            self._stage_artifact_assembly()
            self._stage_persistence()
            
            if self.config.enable_diffing:
                self._stage_diffing()
            
            self.state.total_duration = time.time() - start_time
            self._generate_report()
            
            self.reporter.complete_pipeline(self.state.total_duration)
            return self.report
        
        except OrchestrationError as e:
            self.reporter.report_error(e)
            raise
        except Exception as e:
            error = OrchestrationError(self.state.current_stage, f"Unexpected error: {e}", cause=e)
            self.reporter.report_error(error)
            raise error

    def _validate_configuration(self):
        """Validate configuration."""
        self.state.current_stage = "configuration"
        errors = self.config.validate_config()
        if errors:
            raise ConfigError("configuration", f"Invalid configuration: {', '.join(errors)}")

    def _check_cache(self) -> Optional[IRArtifact]:
        """Check if cached artifact exists."""
        return None

    def _stage_input_preparation(self):
        """Stage 1: Input preparation."""
        self.state.current_stage = "input_preparation"
        stage_start = time.time()
        self.reporter.start_stage("Input Preparation")
        
        try:
            with open(self.config.input_artifact_path, 'r') as f:
                self.raw_data = json.load(f)
            
            ctx = self.raw_data.get('compilation_context', {})
            self.interface_unit = InterfaceUnit(
                target_architecture=ctx.get('target_architecture', 'unknown'),
                operating_system=ctx.get('operating_system', 'unknown'),
                pointer_width=ctx.get('pointer_width', 64),
                endianness=Endianness(ctx.get('endianness', 'little')),
                abi_mode=ctx.get('abi_mode', 'unknown'),
                compiler_family=ctx.get('compiler_family', 'unknown'),
                compiler_version=ctx.get('compiler_version', 'unknown')
            )
        except Exception as e:
            raise ConfigError("input_preparation", f"Failed to load input: {e}")
            
        duration = time.time() - stage_start
        self.state.stage_timings["input_preparation"] = duration
        self.state.stages_completed.append("input_preparation")
        self.reporter.complete_stage("Input Preparation", duration)

    def _stage_type_normalization(self):
        """Stage 2: Type normalization."""
        self.state.current_stage = "type_normalization"
        stage_start = time.time()
        self.reporter.start_stage("Type Normalization")
        
        pipeline = TypeNormalizationPipeline(self.interface_unit)
        raw_types_data = self.raw_data.get('type_information', [])
        raw_types = []
        
        for rd in raw_types_data:
            kind_str = rd.get('scalar_kind')
            scalar_k = ScalarKind(kind_str) if kind_str else None
            arr_kind_str = rd.get('array_kind')
            arr_k = ArrayKind(arr_kind_str) if arr_kind_str else None

            rt = RawTypeData(
                kind=rd.get('kind', 'scalar'),
                name=rd.get('name', ''),
                size_bytes=rd.get('size_bytes', 0),
                alignment_bytes=rd.get('alignment_bytes', 0),
                scalar_kind=scalar_k,
                bit_width=rd.get('bit_width'),
                is_signed=rd.get('is_signed'),
                pointer_depth=rd.get('pointer_depth'),
                target_type_name=rd.get('target_type_name'),
                array_kind=arr_k,
                element_type_name=rd.get('element_type_name'),
                element_count=rd.get('element_count'),
                is_typedef=rd.get('is_typedef', False),
                typedef_target=rd.get('typedef_target')
            )
            for fd in rd.get('fields', []):
                rt.fields.append(RawFieldData(
                    name=fd.get('name'),
                    type_name=fd.get('type_name', ''),
                    byte_offset=fd.get('byte_offset', 0),
                    size_bytes=fd.get('size_bytes', 0),
                    alignment_bytes=fd.get('alignment_bytes', 1)
                ))
            raw_types.append(rt)
            
        normalized_types = pipeline.normalize_all_types(raw_types)
        for t in normalized_types:
            self.type_registry.register_type(t)
            self.interface_unit.types.append(t)
            
        self.state.types_normalized = len(normalized_types)
        duration = time.time() - stage_start
        self.state.stage_timings["type_normalization"] = duration
        self.state.stages_completed.append("type_normalization")
        self.reporter.complete_stage("Type Normalization", duration)

    def _stage_symbol_normalization(self):
        """Stage 3: Symbol normalization."""
        self.state.current_stage = "symbol_normalization"
        stage_start = time.time()
        self.reporter.start_stage("Symbol Normalization")
        
        pipeline = SymbolNormalizationPipeline(
            self.type_registry, self.typedef_resolver, self.interface_unit
        )
        
        raw_funcs = self.raw_data.get('external_symbols', [])
        normalized_count = 0
        for rf in raw_funcs:
            if rf.get('is_function', True):
                raw_func = RawFunctionData(
                    linkage_name=rf.get('linkage_name', ''),
                    return_type_name=rf.get('return_type_name', 'void')
                )
                for pd in rf.get('parameters', []):
                    raw_func.parameters.append(RawParameterData(
                        name=pd.get('name'), type_name=pd.get('type_name', 'void')
                    ))
                func = pipeline.normalize_function(raw_func)
                self.interface_unit.symbols.append(func)
                normalized_count += 1
            else:
                raw_var = RawVariableData(
                    linkage_name=rf.get('linkage_name', ''), type_name=rf.get('type_name', '')
                )
                var = pipeline.normalize_variable(raw_var)
                self.interface_unit.symbols.append(var)
                normalized_count += 1
                
        self.state.symbols_normalized = normalized_count
        duration = time.time() - stage_start
        self.state.stage_timings["symbol_normalization"] = duration
        self.state.stages_completed.append("symbol_normalization")
        self.reporter.complete_stage("Symbol Normalization", duration)

    def _stage_validation(self):
        """Stage 4: Validation."""
        if not self.config.enable_validation:
            return
        self.state.current_stage = "validation"
        stage_start = time.time()
        self.reporter.start_stage("Validation")
        
        validator = IRValidationOrchestrator(self.interface_unit, self.type_registry)
        self.validation_report = validator.validate_complete_ir()
        self.state.validation_passed = self.validation_report.passed
        self.state.validation_errors = self.validation_report.total_errors()
        
        if not self.validation_report.passed and self.config.fail_on_validation_errors:
            raise ValidationFailure("validation", f"Validation failed with {self.state.validation_errors} errors")
        
        duration = time.time() - stage_start
        self.state.stage_timings["validation"] = duration
        self.state.stages_completed.append("validation")
        self.reporter.complete_stage("Validation", duration)

    def _stage_artifact_assembly(self):
        """Stage 5: Artifact assembly."""
        self.state.current_stage = "artifact_assembly"
        stage_start = time.time()
        self.reporter.start_stage("Artifact Assembly")
        
        self.artifact = IRArtifact(
            schema_version="1.0.0",
            normalization_version="1.0.0",
            creation_timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.artifact.interface_unit = self.interface_unit
        if self.validation_report:
            self.artifact.validation_report = self.validation_report
        
        duration = time.time() - stage_start
        self.state.stage_timings["artifact_assembly"] = duration
        self.state.stages_completed.append("artifact_assembly")
        self.reporter.complete_stage("Artifact Assembly", duration)

    def _stage_persistence(self):
        """Stage 6: Persistence."""
        self.state.current_stage = "persistence"
        stage_start = time.time()
        self.reporter.start_stage("Persistence")
        
        manager = IRArtifactManager(self.config.cache_dir)
        with open(self.config.input_artifact_path, 'rb') as f:
            source_hash = hashlib.sha256(f.read()).hexdigest()[:16]
            
        artifact_path = manager.save_artifact(
            self.artifact, source_hash, compress=self.config.compress_artifacts
        )
        self.state.output_artifact_path = artifact_path
        
        duration = time.time() - stage_start
        self.state.stage_timings["persistence"] = duration
        self.state.stages_completed.append("persistence")
        self.reporter.complete_stage("Persistence", duration)

    def _stage_diffing(self):
        """Stage 7: Diffing (optional)."""
        self.state.current_stage = "diffing"
        stage_start = time.time()
        self.reporter.start_stage("Diffing")
        if not self.config.baseline_artifact_path:
            return

        try:
             with open(self.config.baseline_artifact_path, 'r') as f:
                 baseline_data = json.load(f)
             baseline_art = IRArtifact.from_dict(baseline_data)
             computer = IRDiffComputer()
             diff = computer.compute_diff(baseline_art, self.artifact)
             
             self.state.diff_computed = True
             self.state.changes_detected = diff.total_changes()
             self.state.abi_impact = diff.overall_impact.value
             self.report.diff_summary = f"Detected {diff.total_changes()} changes. Impact: {diff.overall_impact.value.upper()}"
             self.report.version_bump = recommend_version_bump(diff).value
        except Exception as e:
            self.reporter.report_error(OrchestrationError("diffing", str(e)))
        
        duration = time.time() - stage_start
        self.state.stage_timings["diffing"] = duration
        self.state.stages_completed.append("diffing")
        self.reporter.complete_stage("Diffing", duration)

    def _generate_report(self):
        """Generate orchestration report."""
        self.report.pipeline_version = "1.0.0"
        self.report.execution_timestamp = datetime.now(timezone.utc).isoformat()
        self.report.total_duration = self.state.total_duration
        self.report.input_artifact_path = str(self.config.input_artifact_path)
        self.report.types_normalized = self.state.types_normalized
        self.report.symbols_normalized = self.state.symbols_normalized
        self.report.validation_passed = self.state.validation_passed
        
        if self.state.output_artifact_path:
            self.report.output_artifact_path = str(self.state.output_artifact_path)
            self.report.output_artifact_hash = compute_artifact_hash(self.artifact)
            if self.state.output_artifact_path.exists():
                self.report.artifact_size_bytes = self.state.output_artifact_path.stat().st_size
        
        self.report.abi_impact = self.state.abi_impact
        self.report.stage_timings = self.state.stage_timings
        
        if self.config.generate_report and self.config.report_output_path:
            self.report.save(self.config.report_output_path)

    def _create_cached_report(self, cached_artifact: IRArtifact) -> OrchestrationReport:
        """Create report for cached artifact."""
        report = OrchestrationReport()
        report.execution_timestamp = datetime.now(timezone.utc).isoformat()
        report.input_artifact_path = str(self.config.input_artifact_path)
        report.validation_passed = True
        return report

__all__ = [
    'IRNormalizationConfig', 'OrchestrationState', 'OrchestrationReport',
    'OrchestrationError', 'ConfigError', 'NormalizationFailure',
    'ValidationFailure', 'IROrchestrator'
]
