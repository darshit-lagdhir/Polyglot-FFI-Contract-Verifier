#!/usr/bin/env python3
"""
Polyglot FFI Contract Verifier - Module 02: Verification Pipeline
Complete implementation of the formal verification pipeline.

This module implements a deterministic, artifact-driven verification pipeline
that transforms implicit FFI assumptions into explicit, testable correctness claims.

Usage:
    python verification_pipeline.py run <execution_context.json>
    python verification_pipeline.py validate-stage <stage_name>
    
API:
    from verification_pipeline import VerificationPipeline, PipelineStage
    pipeline = VerificationPipeline(context)
    result = pipeline.execute_full()
"""

# ═══════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════

import os
import sys
import json
import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import argparse

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 1.1 Stage State Machine
# ───────────────────────────────────────────────────────────────────

class StageState(Enum):
    """
    Enumeration of valid pipeline stage states.
    
    State transitions are strictly controlled:
    PENDING → READY → EXECUTING → COMPLETED
                                 → FAILED
                     → SKIPPED
    """
    PENDING = "pending"           # Stage ready but preconditions not checked
    READY = "ready"               # Preconditions validated, can execute
    EXECUTING = "executing"       # Stage is currently running
    COMPLETED = "completed"       # Successfully finished, postconditions satisfied
    FAILED = "failed"             # Error encountered, postconditions not satisfied
    SKIPPED = "skipped"           # Skipped due to config or upstream failure

# ───────────────────────────────────────────────────────────────────
# 1.2 Error Classification
# ───────────────────────────────────────────────────────────────────

class PipelineError(Exception):
    """Base class for all pipeline errors."""
    pass

class ConfigError(PipelineError):
    """
    Invalid user configuration or inputs.
    Examples: missing files, unsupported platform, invalid arguments.
    """
    pass

class PreconditionError(PipelineError):
    """
    Required input artifacts missing or invalid.
    Examples: stage requires IR artifact but it doesn't exist.
    """
    def __init__(self, message: str, missing_artifact: str, required_stage: str):
        super().__init__(message)
        self.missing_artifact = missing_artifact
        self.required_stage = required_stage

class StageError(PipelineError):
    """
    Error during stage execution.
    Examples: parse failures, validation errors, runtime exceptions.
    """
    def __init__(self, message: str, stage_name: str, details: Optional[str] = None):
        super().__init__(message)
        self.stage_name = stage_name
        self.details = details

class PostconditionError(PipelineError):
    """
    Stage completed but produced invalid artifacts.
    This indicates a bug in the stage implementation.
    """
    def __init__(self, message: str, stage_name: str, artifact_path: str):
        super().__init__(message)
        self.stage_name = stage_name
        self.artifact_path = artifact_path

# ───────────────────────────────────────────────────────────────────
# 1.3 Artifact Provenance
# ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ArtifactProvenance:
    """
    Provenance metadata embedded in every artifact.
    
    This metadata enables complete traceability from outputs back to inputs
    and execution context.
    """
    execution_id: str                      # UUID linking to ExecutionContext
    stage_name: str                        # Which stage produced this artifact
    stage_version: str                     # Version of producing stage
    creation_timestamp: str                # ISO 8601 UTC timestamp
    schema_version: str                    # Version of artifact schema
    input_artifact_hashes: Dict[str, str]  # Map of input artifact paths to SHA-256 hashes
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for embedding in artifacts."""
        return {
            "execution_id": self.execution_id,
            "stage_name": self.stage_name,
            "stage_version": self.stage_version,
            "creation_timestamp": self.creation_timestamp,
            "schema_version": self.schema_version,
            "input_artifact_hashes": dict(self.input_artifact_hashes)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArtifactProvenance':
        """Deserialize from dictionary."""
        return cls(
            execution_id=data["execution_id"],
            stage_name=data["stage_name"],
            stage_version=data["stage_version"],
            creation_timestamp=data["creation_timestamp"],
            schema_version=data["schema_version"],
            input_artifact_hashes=data["input_artifact_hashes"]
        )

# ───────────────────────────────────────────────────────────────────
# 1.4 Artifact Validator
# ───────────────────────────────────────────────────────────────────

class ArtifactValidator:
    """
    Validates artifacts against their schemas and checks provenance metadata.
    
    All artifacts must pass validation before being used as inputs to stages.
    This enforces the architectural law: "No stage may read artifacts without
    validating them first."
    """
    
    @staticmethod
    def validate_artifact(artifact_path: str, expected_schema_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate artifact exists, is readable, has valid JSON, and contains
        required provenance metadata.
        
        Args:
            artifact_path: Path to artifact file
            expected_schema_version: Optional schema version to enforce
            
        Returns:
            Parsed artifact as dictionary
            
        Raises:
            ConfigError: If artifact doesn't exist or isn't readable
            PostconditionError: If artifact is invalid
        """
        # Check existence
        if not os.path.exists(artifact_path):
            raise ConfigError(f"Artifact not found: {artifact_path}")
        
        # Check readability
        if not os.access(artifact_path, os.R_OK):
            raise ConfigError(f"Artifact not readable: {artifact_path}")
        
        # Parse JSON
        try:
            with open(artifact_path, 'r', encoding='utf-8') as f:
                artifact = json.load(f)
        except json.JSONDecodeError as e:
            raise PostconditionError(
                f"Artifact is not valid JSON: {artifact_path}",
                stage_name="unknown",
                artifact_path=artifact_path
            )
        
        # Validate provenance exists
        if "provenance" not in artifact:
            raise PostconditionError(
                f"Artifact missing provenance metadata: {artifact_path}",
                stage_name="unknown",
                artifact_path=artifact_path
            )
        
        # Validate required provenance fields
        required_fields = [
            "execution_id", "stage_name", "stage_version",
            "creation_timestamp", "schema_version", "input_artifact_hashes"
        ]
        
        provenance = artifact["provenance"]
        for field in required_fields:
            if field not in provenance:
                raise PostconditionError(
                    f"Artifact provenance missing required field '{field}': {artifact_path}",
                    stage_name=provenance.get("stage_name", "unknown"),
                    artifact_path=artifact_path
                )
        
        # Validate schema version if specified
        if expected_schema_version is not None:
            actual_version = provenance["schema_version"]
            if actual_version != expected_schema_version:
                raise PostconditionError(
                    f"Schema version mismatch: expected {expected_schema_version}, got {actual_version}",
                    stage_name=provenance["stage_name"],
                    artifact_path=artifact_path
                )
        
        return artifact
    
    @staticmethod
    def compute_artifact_hash(artifact_path: str) -> str:
        """
        Compute SHA-256 hash of artifact file.
        
        Used for provenance tracking and change detection.
        """
        if not os.path.exists(artifact_path):
            raise ConfigError(f"Cannot hash non-existent artifact: {artifact_path}")
        
        sha256 = hashlib.sha256()
        with open(artifact_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

# ───────────────────────────────────────────────────────────────────
# 1.5 Pipeline Stage (Abstract Base Class)
# ───────────────────────────────────────────────────────────────────

class PipelineStage(ABC):
    """
    Abstract base class for all pipeline stages.
    
    Each stage is a correctness boundary with explicit preconditions,
    postconditions, and invariants. Stages must implement:
    - Precondition checking (required inputs exist and are valid)
    - Execution logic (transformation from inputs to outputs)
    - Postcondition checking (outputs satisfy requirements)
    
    The stage lifecycle is:
    1. __init__: Stage created in PENDING state
    2. validate_preconditions: Check inputs → READY or raise PreconditionError
    3. execute: Perform transformation → COMPLETED or raise StageError
    4. validate_postconditions: Check outputs → success or raise PostconditionError
    """
    
    # Subclasses must override these
    STAGE_NAME: str = "abstract_stage"
    STAGE_VERSION: str = "1.0.0"
    STAGE_DESCRIPTION: str = "Abstract pipeline stage"
    
    # Subclasses must specify required inputs and produced outputs
    REQUIRED_INPUTS: List[str] = []        # List of artifact types required
    PRODUCED_OUTPUTS: List[str] = []       # List of artifact types produced
    
    def __init__(self, execution_context: Dict[str, Any]):
        """
        Initialize stage with execution context.
        
        Args:
            execution_context: Deserialized ExecutionContext artifact
        """
        self.execution_context = execution_context
        self.state = StageState.PENDING
        self.error: Optional[Exception] = None
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        
        # Extract execution ID for provenance
        if "provenance" not in execution_context:
            raise ConfigError("ExecutionContext missing provenance metadata")
        
        self.execution_id = execution_context["provenance"]["execution_id"]
    
    def validate_preconditions(self) -> None:
        """
        Validate that all required input artifacts exist and are valid.
        
        This method enforces the architectural law: "No stage executes until
        all preconditions are satisfied."
        
        Raises:
            PreconditionError: If required artifacts are missing or invalid
        """
        artifacts_dir = self.execution_context.get("artifacts", {}).get("working_directory", "artifacts")
        
        for required_input in self.REQUIRED_INPUTS:
            # Map artifact type to file path
            artifact_path = self._resolve_artifact_path(artifacts_dir, required_input)
            
            # Validate artifact exists and is valid
            try:
                ArtifactValidator.validate_artifact(artifact_path)
            except ConfigError:
                raise PreconditionError(
                    f"Stage '{self.STAGE_NAME}' requires artifact '{required_input}' which doesn't exist",
                    missing_artifact=required_input,
                    required_stage=self._infer_required_stage(required_input)
                )
            except PostconditionError as e:
                raise PreconditionError(
                    f"Stage '{self.STAGE_NAME}' requires valid artifact '{required_input}' but it's corrupted: {e}",
                    missing_artifact=required_input,
                    required_stage=self._infer_required_stage(required_input)
                )
        
        # Transition to READY state
        self.state = StageState.READY
    
    def execute(self) -> None:
        """
        Execute stage transformation.
        
        This is the main entry point for stage execution. It:
        1. Validates preconditions
        2. Transitions to EXECUTING state
        3. Calls _execute_impl (implemented by subclass)
        4. Validates postconditions
        5. Transitions to COMPLETED or FAILED state
        
        Raises:
            PreconditionError: If preconditions aren't satisfied
            StageError: If execution fails
            PostconditionError: If postconditions aren't satisfied
        """
        # Validate preconditions
        if self.state == StageState.PENDING:
            self.validate_preconditions()
        
        if self.state != StageState.READY:
            raise StageError(
                f"Stage '{self.STAGE_NAME}' cannot execute from state {self.state.value}",
                stage_name=self.STAGE_NAME
            )
        
        # Transition to EXECUTING
        self.state = StageState.EXECUTING
        self.start_time = datetime.now(timezone.utc).isoformat()
        
        try:
            # Execute stage logic (implemented by subclass)
            self._execute_impl()
            
            # Validate postconditions
            self.validate_postconditions()
            
            # Transition to COMPLETED
            self.state = StageState.COMPLETED
            self.end_time = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
                        self.error = e
            self.state = StageState.FAILED
            self.end_time = datetime.now(timezone.utc).isoformat()
            raise
    
    @abstractmethod
    def _execute_impl(self) -> None:
        """
        Stage-specific execution logic.
        
        Subclasses must implement this method to perform their transformation.
        This method should:
        1. Read input artifacts (already validated)
        2. Perform stage-specific processing
        3. Write output artifacts with provenance metadata
        
        Raises:
            StageError: If execution fails
        """
        pass
    
    def validate_postconditions(self) -> None:
        """
        Validate that all required output artifacts were produced and are valid.
        
        This enforces the architectural law: "No stage produces artifacts
        without ensuring they satisfy their schema."
        
        Raises:
            PostconditionError: If required outputs are missing or invalid
        """
        artifacts_dir = self.execution_context.get("artifacts", {}).get("working_directory", "artifacts")
        
        for produced_output in self.PRODUCED_OUTPUTS:
            # Map artifact type to file path
            artifact_path = self._resolve_artifact_path(artifacts_dir, produced_output)
            
            # Validate artifact was produced and is valid
            try:
                ArtifactValidator.validate_artifact(artifact_path)
            except (ConfigError, PostconditionError) as e:
                raise PostconditionError(
                    f"Stage '{self.STAGE_NAME}' failed to produce valid artifact '{produced_output}': {e}",
                    stage_name=self.STAGE_NAME,
                    artifact_path=artifact_path
                )
    
    def _resolve_artifact_path(self, artifacts_dir: str, artifact_type: str) -> str:
        """
        Map artifact type to file system path.
        
        This uses a standard naming convention:
        - native_interface → native_interface.json
        - ir → ir.json
        - contract → contract.json
        - etc.
        """
        artifact_filename = f"{artifact_type}.json"
        return os.path.join(artifacts_dir, artifact_filename)
    
    def _infer_required_stage(self, artifact_type: str) -> str:
        """
        Infer which stage produces a given artifact type.
        
        Used for error messages to suggest which stage to run.
        """
        stage_map = {
            "native_interface": "ingestion",
            "ir": "normalization",
            "contract": "synthesis",
            "test_plan": "test_generation",
            "execution_log": "execution",
            "diagnostics": "diagnostics",
            "report": "reporting"
        }
        return stage_map.get(artifact_type, "unknown")
    
    def create_provenance(self, input_artifacts: List[str]) -> ArtifactProvenance:
        """
        Create provenance metadata for an output artifact.
        
        Args:
            input_artifacts: List of input artifact paths
            
        Returns:
            ArtifactProvenance object to embed in output artifact
        """
        # Compute hashes of input artifacts
        input_hashes = {}
        for artifact_path in input_artifacts:
            if os.path.exists(artifact_path):
                input_hashes[artifact_path] = ArtifactValidator.compute_artifact_hash(artifact_path)
        
        return ArtifactProvenance(
            execution_id=self.execution_id,
            stage_name=self.STAGE_NAME,
            stage_version=self.STAGE_VERSION,
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            schema_version="1.0.0",  # TODO: Make configurable per artifact type
            input_artifact_hashes=input_hashes
        )
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of stage execution for logging.
        
        Returns:
            Dictionary with stage name, state, timestamps, error (if any)
        """
        summary = {
            "stage_name": self.STAGE_NAME,
            "stage_version": self.STAGE_VERSION,
            "state": self.state.value,
            "start_time": self.start_time,
            "end_time": self.end_time
        }
        
        if self.error:
            summary["error"] = {
                "type": type(self.error).__name__,
                "message": str(self.error)
            }
        
        return summary

# ───────────────────────────────────────────────────────────────────
# 1.6 Stage Registry
# ───────────────────────────────────────────────────────────────────

class StageRegistry:
    """
    Registry of available pipeline stages.
    
    The registry maintains a mapping from stage names to stage classes
    and validates stage definitions.
    """
    
    def __init__(self):
        self._stages: Dict[str, type] = {}
    
    def register_stage(self, stage_class: type) -> None:
        """
        Register a stage class.
        
        Args:
            stage_class: Subclass of PipelineStage
            
        Raises:
            ValueError: If stage class is invalid
        """
        if not issubclass(stage_class, PipelineStage):
            raise ValueError(f"Stage class must inherit from PipelineStage: {stage_class}")
        
        stage_name = stage_class.STAGE_NAME
        
        if stage_name in self._stages:
            raise ValueError(f"Stage already registered: {stage_name}")
        
        self._stages[stage_name] = stage_class
    
    def get_stage_class(self, stage_name: str) -> type:
        """
        Get stage class by name.
        
        Args:
            stage_name: Name of stage
            
        Returns:
            Stage class
            
        Raises:
            KeyError: If stage not registered
        """
        if stage_name not in self._stages:
            raise KeyError(f"Stage not registered: {stage_name}")
        
        return self._stages[stage_name]
    
    def list_stages(self) -> List[str]:
        """Get list of registered stage names."""
        return list(self._stages.keys())
    
    def get_stage_info(self, stage_name: str) -> Dict[str, Any]:
        """
        Get information about a registered stage.
        
        Args:
            stage_name: Name of stage
            
        Returns:
            Dictionary with stage metadata
        """
        stage_class = self.get_stage_class(stage_name)
        
        return {
            "name": stage_class.STAGE_NAME,
            "version": stage_class.STAGE_VERSION,
            "description": stage_class.STAGE_DESCRIPTION,
            "required_inputs": stage_class.REQUIRED_INPUTS,
            "produced_outputs": stage_class.PRODUCED_OUTPUTS
        }

# ───────────────────────────────────────────────────────────────────
# 1.7 Pipeline Execution Log
# ───────────────────────────────────────────────────────────────────

class PipelineExecutionLog:
    """
    Records all pipeline execution events.
    
    The execution log is append-only and immutable. It captures:
    - Which stages executed
    - State transitions
    - Errors and warnings
    - Produced artifacts
    - Timing information
    """
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.entries: List[Dict[str, Any]] = []
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.end_time: Optional[str] = None
    
    def log_stage_start(self, stage: PipelineStage) -> None:
        """Log that a stage started executing."""
        self.entries.append({
            "event": "stage_start",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage_name": stage.STAGE_NAME,
            "stage_version": stage.STAGE_VERSION,
            "state": stage.state.value
        })
    
    def log_stage_complete(self, stage: PipelineStage) -> None:
        """Log that a stage completed successfully."""
        self.entries.append({
            "event": "stage_complete",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage_name": stage.STAGE_NAME,
            "state": stage.state.value,
            "execution_time_seconds": self._compute_execution_time(stage)
        })
    
    def log_stage_failed(self, stage: PipelineStage, error: Exception) -> None:
        """Log that a stage failed."""
        self.entries.append({
            "event": "stage_failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage_name": stage.STAGE_NAME,
            "state": stage.state.value,
            "error_type": type(error).__name__,
            "error_message": str(error)
        })
    
    def log_pipeline_start(self) -> None:
        """Log that pipeline execution started."""
        self.entries.append({
            "event": "pipeline_start",
            "timestamp": self.start_time,
            "execution_id": self.execution_id
        })
    
    def log_pipeline_complete(self, success: bool) -> None:
        """Log that pipeline execution completed."""
        self.end_time = datetime.now(timezone.utc).isoformat()
        self.entries.append({
            "event": "pipeline_complete",
            "timestamp": self.end_time,
            "execution_id": self.execution_id,
            "success": success
        })
    
    def _compute_execution_time(self, stage: PipelineStage) -> Optional[float]:
        """Compute stage execution time in seconds."""
        if stage.start_time and stage.end_time:
            start = datetime.fromisoformat(stage.start_time)
            end = datetime.fromisoformat(stage.end_time)
            return (end - start).total_seconds()
        return None
    
    def save(self, output_path: str) -> None:
        """Save execution log to file."""
        log_data = {
            "execution_id": self.execution_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "entries": self.entries
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)

# ───────────────────────────────────────────────────────────────────
# 1.8 Verification Pipeline (Orchestrator)
# ───────────────────────────────────────────────────────────────────

class VerificationPipeline:
    """
    Main pipeline orchestrator.
    
    Responsibilities:
    - Load and validate execution context
    - Register and instantiate stages
    - Execute stages in correct order
    - Enforce preconditions and postconditions
    - Handle errors according to classification
    - Produce pipeline execution log
    
    The pipeline enforces all architectural laws:
    - No stage executes until preconditions are satisfied
    - No stage reads unvalidated artifacts
    - No validation steps are skipped
    - All failures are classified and reported
    """
    
    def __init__(self, execution_context_path: str):
        """
        Initialize pipeline with execution context.
        
        Args:
            execution_context_path: Path to execution_context.json
            
        Raises:
            ConfigError: If context is missing or invalid
        """
        # Load and validate execution context
        try:
            self.execution_context = ArtifactValidator.validate_artifact(execution_context_path)
        except Exception as e:
            raise ConfigError(f"Invalid execution context: {e}")
        
        self.execution_id = self.execution_context["provenance"]["execution_id"]
        
        # Initialize stage registry
        self.registry = StageRegistry()
        
        # Initialize execution log
        self.execution_log = PipelineExecutionLog(self.execution_id)
        
        # Stages will be registered by subclasses or dynamically
        self.stages: List[PipelineStage] = []
    
    def register_stage(self, stage_class: type) -> None:
        """
        Register a stage for execution.
        
        Args:
            stage_class: Subclass of PipelineStage
        """
        self.registry.register_stage(stage_class)
    
    def execute_full_pipeline(self) -> bool:
        """
        Execute all registered stages in order.
        
        Returns:
            True if all stages completed successfully, False otherwise
        """
        self.execution_log.log_pipeline_start()
        
        success = True
        
        for stage_class in self._resolve_execution_order():
            try:
                # Instantiate stage
                stage = stage_class(self.execution_context)
                
                # Log start
                self.execution_log.log_stage_start(stage)
                
                # Execute stage (validates preconditions, executes, validates postconditions)
                stage.execute()
                
                # Log completion
                self.execution_log.log_stage_complete(stage)
                
            except PreconditionError as e:
                # Precondition not satisfied - provide helpful error
                self.execution_log.log_stage_failed(stage, e)
                print(f"ERROR: {e}")
                print(f"HINT: Run stage '{e.required_stage}' first to produce '{e.missing_artifact}'")
                success = False
                break
                
            except StageError as e:
                # Stage execution failed
                self.execution_log.log_stage_failed(stage, e)
                print(f"ERROR: Stage '{e.stage_name}' failed: {e}")
                if e.details:
                    print(f"Details: {e.details}")
                success = False
                break
                
            except PostconditionError as e:
                # Stage produced invalid output (internal error)
                self.execution_log.log_stage_failed(stage, e)
                print(f"INTERNAL ERROR: Stage '{e.stage_name}' produced invalid artifact: {e}")
                print(f"This is a bug in the stage implementation. Please report it.")
                success = False
                break
                
            except Exception as e:
                # Unexpected error
                self.execution_log.log_stage_failed(stage, e)
                print(f"UNEXPECTED ERROR in stage '{stage_class.STAGE_NAME}': {e}")
                success = False
                break
        
        # Log pipeline completion
        self.execution_log.log_pipeline_complete(success)
        
        # Save execution log
        log_path = os.path.join(
            self.execution_context["artifacts"]["working_directory"],
            "pipeline_execution_log.json"
        )
        self.execution_log.save(log_path)
        
        return success
    
    def execute_stage(self, stage_name: str) -> bool:
        """
        Execute a single stage by name.
        
        Args:
            stage_name: Name of stage to execute
            
        Returns:
            True if stage completed successfully, False otherwise
        """
        try:
            stage_class = self.registry.get_stage_class(stage_name)
            stage = stage_class(self.execution_context)
            
            self.execution_log.log_stage_start(stage)
            stage.execute()
            self.execution_log.log_stage_complete(stage)
            
            return True
            
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    def _resolve_execution_order(self) -> List[type]:
        """
        Resolve stage execution order based on dependencies.
        
        For now, this returns stages in registration order.
        Future versions could implement topological sort based on
        required_inputs and produced_outputs.
        
        Returns:
            List of stage classes in execution order
        """
        # Simple approach: return in registration order
        return [self.registry.get_stage_class(name) for name in self.registry.list_stages()]
    
    def list_stages(self) -> None:
        """Print list of registered stages."""
        print("Registered Pipeline Stages:")
        print("-" * 60)
        for stage_name in self.registry.list_stages():
            info = self.registry.get_stage_info(stage_name)
            print(f"Stage: {info['name']} (v{info['version']})")
            print(f"  Description: {info['description']}")
            print(f"  Inputs: {', '.join(info['required_inputs']) or 'None'}")
            print(f"  Outputs: {', '.join(info['produced_outputs']) or 'None'}")
            print()

# ───────────────────────────────────────────────────────────────────
# 1.9 CLI for Testing
# ───────────────────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 2.1 Invalid State Transition Error
# ───────────────────────────────────────────────────────────────────

class InvalidStateTransitionError(PipelineError):
    """
    Raised when an invalid stage state transition is attempted.
    
    State transitions must follow strict rules defined by the state machine.
    """
    def __init__(self, stage_name: str, current_state: StageState, attempted_state: StageState):
        self.stage_name = stage_name
        self.current_state = current_state
        self.attempted_state = attempted_state
        super().__init__(
            f"Invalid state transition in stage '{stage_name}': "
            f"{current_state.value} → {attempted_state.value}"
        )

# ───────────────────────────────────────────────────────────────────
# 2.2 State Machine Validator
# ───────────────────────────────────────────────────────────────────

class StateMachineValidator:
    """
    Validates stage state transitions according to formal state machine rules.
    
    This enforces the architectural invariant that state transitions are
    explicit, validated, and follow a deterministic pattern.
    """
    
    # Define valid state transitions
    VALID_TRANSITIONS = {
        StageState.PENDING: {StageState.READY, StageState.SKIPPED},
        StageState.READY: {StageState.EXECUTING},
        StageState.EXECUTING: {StageState.COMPLETED, StageState.FAILED},
        StageState.COMPLETED: set(),  # Terminal state
        StageState.FAILED: set(),     # Terminal state (must restart from PENDING)
        StageState.SKIPPED: set()     # Terminal state
    }
    
    @classmethod
    def validate_transition(
        cls,
        stage_name: str,
        current_state: StageState,
        new_state: StageState
    ) -> None:
        """
        Validate that a state transition is legal.
        
        Args:
            stage_name: Name of stage attempting transition
            current_state: Current state
            new_state: Desired new state
            
        Raises:
            InvalidStateTransitionError: If transition is invalid
        """
        if new_state not in cls.VALID_TRANSITIONS[current_state]:
            raise InvalidStateTransitionError(stage_name, current_state, new_state)
    
    @classmethod
    def is_terminal_state(cls, state: StageState) -> bool:
        """Check if a state is terminal (no outgoing transitions)."""
        return len(cls.VALID_TRANSITIONS[state]) == 0
    
    @classmethod
    def can_retry(cls, state: StageState) -> bool:
        """Check if a stage in this state can be retried."""
                return state in {StageState.FAILED, StageState.SKIPPED}

# ───────────────────────────────────────────────────────────────────
# 2.3 Schema Version Comparator
# ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SemanticVersion:
    """Semantic version (MAJOR.MINOR.PATCH)."""
    major: int
    minor: int
    patch: int
    
    @classmethod
    def parse(cls, version_string: str) -> 'SemanticVersion':
        """
        Parse semantic version string.
        
        Args:
            version_string: Version in format "MAJOR.MINOR.PATCH"
            
        Returns:
            SemanticVersion object
            
        Raises:
            ValueError: If version string is invalid
        """
        parts = version_string.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid semantic version: {version_string} (expected MAJOR.MINOR.PATCH)")
        
        try:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid semantic version: {version_string} (parts must be integers)")
        
        return cls(major=major, minor=minor, patch=patch)
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def is_compatible_with(self, required: 'SemanticVersion') -> bool:
        """
        Check if this version is compatible with a required version.
        
        Compatibility rules (semantic versioning):
        - Major version must match (breaking changes)
        - Minor version must be >= required (backward compatible additions)
        - Patch version irrelevant (bug fixes always compatible)
        
        Args:
            required: Required version
            
        Returns:
            True if compatible, False otherwise
        """
        if self.major != required.major:
            return False  # Major version mismatch = breaking change
        
        if self.minor < required.minor:
            return False  # Older minor version = missing features
        
        # Same major, equal or newer minor = compatible
        return True

class SchemaVersionValidator:
    """
    Validates artifact schema versions for compatibility.
    """
    
    @staticmethod
    def validate_compatibility(
        artifact_path: str,
        artifact_version: str,
        required_version: str
    ) -> None:
        """
        Validate that artifact schema version is compatible with required version.
        
        Args:
            artifact_path: Path to artifact (for error messages)
            artifact_version: Actual schema version in artifact
            required_version: Required schema version
            
        Raises:
            PostconditionError: If versions are incompatible
        """
        try:
            artifact_v = SemanticVersion.parse(artifact_version)
            required_v = SemanticVersion.parse(required_version)
        except ValueError as e:
            raise PostconditionError(
                f"Invalid schema version in artifact: {e}",
                stage_name="unknown",
                artifact_path=artifact_path
            )
        
        if not artifact_v.is_compatible_with(required_v):
            raise PostconditionError(
                f"Schema version incompatible: artifact has {artifact_v}, required {required_v}",
                stage_name="unknown",
                artifact_path=artifact_path
            )

# ───────────────────────────────────────────────────────────────────
# 2.4 Enhanced Artifact Validator
# ───────────────────────────────────────────────────────────────────

class EnhancedArtifactValidator:
    """
    Advanced artifact validation with schema checking, hash verification,
    and provenance validation.
    """
    
    def __init__(self):
        # Cache: (path, mtime, size) → (is_valid, artifact, timestamp)
        self._validation_cache: Dict[Tuple[str, float, int], Tuple[bool, Dict, str]] = {}
    
    def validate_artifact(
        self,
        artifact_path: str,
        expected_schema_version: Optional[str] = None,
        verify_hashes: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive artifact validation.
        
        Args:
            artifact_path: Path to artifact
            expected_schema_version: Expected schema version (if any)
            verify_hashes: Whether to verify input artifact hashes
            
        Returns:
            Parsed and validated artifact
            
        Raises:
            ConfigError: If artifact doesn't exist
            PostconditionError: If artifact is invalid
        """
        # Check cache first
        if os.path.exists(artifact_path):
            stat = os.stat(artifact_path)
            cache_key = (artifact_path, stat.st_mtime, stat.st_size)
            
            if cache_key in self._validation_cache:
                is_valid, artifact, _ = self._validation_cache[cache_key]
                if is_valid:
                    return artifact
        
                artifact = ArtifactValidator.validate_artifact(artifact_path, expected_schema_version)
        
        # Additional validations
        self._validate_provenance_fields(artifact, artifact_path)
        
        if expected_schema_version:
            actual_version = artifact["provenance"]["schema_version"]
            SchemaVersionValidator.validate_compatibility(
                artifact_path, actual_version, expected_schema_version
            )
        
        if verify_hashes:
            self._verify_input_hashes(artifact, artifact_path)
        
        # Cache result
        if os.path.exists(artifact_path):
            stat = os.stat(artifact_path)
            cache_key = (artifact_path, stat.st_mtime, stat.st_size)
            self._validation_cache[cache_key] = (True, artifact, datetime.now(timezone.utc).isoformat())
        
        return artifact
    
    def _validate_provenance_fields(self, artifact: Dict[str, Any], artifact_path: str) -> None:
        """Validate provenance field formats."""
        provenance = artifact["provenance"]
        
        # Validate UUID format
        execution_id = provenance["execution_id"]
        try:
            uuid.UUID(execution_id, version=4)
        except ValueError:
            raise PostconditionError(
                f"Invalid execution_id (not UUID v4): {execution_id}",
                stage_name=provenance.get("stage_name", "unknown"),
                artifact_path=artifact_path
            )
        
        # Validate timestamp format
        timestamp = provenance["creation_timestamp"]
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise PostconditionError(
                f"Invalid timestamp (not ISO 8601): {timestamp}",
                stage_name=provenance["stage_name"],
                artifact_path=artifact_path
            )
        
        # Validate hashes
        for input_path, hash_value in provenance["input_artifact_hashes"].items():
            if len(hash_value) != 64 or not all(c in '0123456789abcdef' for c in hash_value):
                raise PostconditionError(
                    f"Invalid SHA-256 hash for {input_path}: {hash_value}",
                    stage_name=provenance["stage_name"],
                    artifact_path=artifact_path
                )
    
    def _verify_input_hashes(self, artifact: Dict[str, Any], artifact_path: str) -> None:
        """Verify that input artifact hashes match actual files."""
        provenance = artifact["provenance"]
        input_hashes = provenance["input_artifact_hashes"]
        
        for input_path, declared_hash in input_hashes.items():
            if not os.path.exists(input_path):
                # Input artifact missing (may have been cleaned up)
                continue
            
            actual_hash = ArtifactValidator.compute_artifact_hash(input_path)
            if actual_hash != declared_hash:
                raise PostconditionError(
                    f"Hash mismatch for input artifact {input_path}:\n"
                    f"  Declared: {declared_hash}\n"
                    f"  Actual:   {actual_hash}\n"
                    f"This indicates the input artifact has changed since {artifact_path} was created.",
                    stage_name=provenance["stage_name"],
                    artifact_path=artifact_path
                )

# ───────────────────────────────────────────────────────────────────
# 2.5 Dependency Graph & Topological Sort
# ───────────────────────────────────────────────────────────────────

class DependencyGraph:
    """
    Builds and analyzes stage dependency graph for execution order resolution.
    """
    
    def __init__(self, stages: List[type]):
        """
        Initialize dependency graph from stage classes.
        
        Args:
            stages: List of PipelineStage subclasses
        """
        self.stages = {stage.STAGE_NAME: stage for stage in stages}
        self.graph: Dict[str, Set[str]] = {}  # stage_name → set of stages it depends on
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build dependency graph from stage requirements."""
        # Map artifact types to stages that produce them
        producers: Dict[str, str] = {}  # artifact_type → stage_name
        
        for stage_name, stage_class in self.stages.items():
            for output in stage_class.PRODUCED_OUTPUTS:
                if output in producers:
                    raise ValueError(
                        f"Multiple stages produce artifact '{output}': "
                        f"{producers[output]} and {stage_name}"
                    )
                producers[output] = stage_name
        
        # Build dependency edges
        for stage_name, stage_class in self.stages.items():
            dependencies = set()
            
            for required_input in stage_class.REQUIRED_INPUTS:
                if required_input in producers:
                    dependencies.add(producers[required_input])
                # If no producer, input must already exist (e.g., ExecutionContext)
            
            self.graph[stage_name] = dependencies
    
    def topological_sort(self) -> List[str]:
        """
        Compute topological sort of stages (valid execution order).
        
        Returns:
            List of stage names in execution order
            
        Raises:
            ValueError: If dependency graph contains a cycle
        """
        # Kahn's algorithm for topological sort
        in_degree = {stage: 0 for stage in self.stages}
        
        for stage in self.graph:
            in_degree[stage] = len(self.graph[stage])
        
        # Find stages with no dependencies
        queue = [stage for stage, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            stage = queue.pop(0)
            result.append(stage)
            
            # Remove this stage and update in-degrees
            for other_stage in self.graph:
                if stage in self.graph[other_stage]:
                    in_degree[other_stage] -= 1
                    if in_degree[other_stage] == 0:
                        queue.append(other_stage)
        
        if len(result) != len(self.stages):
            # Cycle detected
            remaining = set(self.stages.keys()) - set(result)
            raise ValueError(f"Circular dependency detected among stages: {remaining}")
        
        return result
    
    def detect_cycles(self) -> Optional[List[str]]:
        """
        Detect cycles in dependency graph.
        
        Returns:
            List of stage names forming a cycle, or None if no cycle
        """
        try:
            self.topological_sort()
            return None
        except ValueError:
            # Find cycle using DFS
            visited = set()
            rec_stack = set()
            
            def dfs(stage: str, path: List[str]) -> Optional[List[str]]:
                visited.add(stage)
                rec_stack.add(stage)
                path.append(stage)
                
                for dependency in self.graph.get(stage, set()):
                    if dependency not in visited:
                        cycle = dfs(dependency, path[:])
                        if cycle:
                            return cycle
                    elif dependency in rec_stack:
                        # Found cycle
                        cycle_start = path.index(dependency)
                        return path[cycle_start:] + [dependency]
                
                rec_stack.remove(stage)
                return None
            
            for stage in self.graph:
                if stage not in visited:
                    cycle = dfs(stage, [])
                    if cycle:
                        return cycle
            
            return None

# ───────────────────────────────────────────────────────────────────
# 2.6 Enhanced Pipeline Orchestrator
# ───────────────────────────────────────────────────────────────────

class EnhancedVerificationPipeline(VerificationPipeline):
    """
    Enhanced pipeline orchestrator with advanced state management,
    dependency resolution, and error recovery.
    """
    
    def __init__(self, execution_context_path: str):
        super().__init__(execution_context_path)
        self.artifact_validator = EnhancedArtifactValidator()
        self.state_validator = StateMachineValidator()
    
    def execute_full_pipeline_with_dependency_resolution(self) -> bool:
        """
        Execute pipeline with automatic dependency resolution.
        
        Stages are executed in topological order based on their dependencies.
        
        Returns:
            True if all stages completed successfully
        """
        self.execution_log.log_pipeline_start()
        
        # Build dependency graph
        stage_classes = [self.registry.get_stage_class(name) for name in self.registry.list_stages()]
        
        try:
            dep_graph = DependencyGraph(stage_classes)
            execution_order = dep_graph.topological_sort()
        except ValueError as e:
            print(f"ERROR: {e}")
            cycle = dep_graph.detect_cycles()
            if cycle:
                print(f"Cycle: {' → '.join(cycle)}")
            self.execution_log.log_pipeline_complete(False)
            return False
        
        # Execute stages in order
        success = True
        for stage_name in execution_order:
            stage_class = self.registry.get_stage_class(stage_name)
            
            try:
                stage = stage_class(self.execution_context)
                self.execution_log.log_stage_start(stage)
                
                # Validate state transition: PENDING → READY
                self.state_validator.validate_transition(
                    stage.STAGE_NAME, stage.state, StageState.READY
                )
                
                stage.execute()
                self.execution_log.log_stage_complete(stage)
                
            except InvalidStateTransitionError as e:
                print(f"ERROR: Invalid state transition: {e}")
                self.execution_log.log_stage_failed(stage, e)
                success = False
                break
                
            except (PreconditionError, StageError, PostconditionError) as e:
                self.execution_log.log_stage_failed(stage, e)
                print(f"ERROR: {e}")
                success = False
                break
        
        self.execution_log.log_pipeline_complete(success)
        
        # Save execution log
        log_path = os.path.join(
            self.execution_context["artifacts"]["working_directory"],
            "pipeline_execution_log.json"
        )
        self.execution_log.save(log_path)
        
        return success

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 3.1 Artifact Schema Definitions
# ───────────────────────────────────────────────────────────────────

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

class ArtifactType(Enum):
    """Enumeration of all artifact types in the pipeline."""
    EXECUTION_CONTEXT = "execution_context"
    NATIVE_INTERFACE = "native_interface"
    INTERMEDIATE_REPRESENTATION = "ir"
    CONTRACT = "contract"
    TEST_PLAN = "test_plan"
    EXECUTION_LOG = "execution_log"
    DIAGNOSTICS = "diagnostics"
    REPORT = "report"
    PIPELINE_LOG = "pipeline_execution_log"

@dataclass(frozen=True)
class FieldSchema:
    """Schema definition for a single field in an artifact."""
    name: str
    field_type: str  # "string", "int", "float", "bool", "array", "object"
    required: bool
    description: str
    default: Optional[Any] = None
    constraints: Optional[Dict[str, Any]] = None  # e.g., {"min": 0, "max": 100}
    nested_schema: Optional['ArtifactSchema'] = None  # For objects

@dataclass(frozen=True)
class ArtifactSchema:
    """
    Complete schema definition for an artifact type.
    
    Defines structure, validation rules, and versioning for artifacts.
    """
    artifact_type: ArtifactType
    schema_version: str  # Semantic version
    description: str
    fields: List[FieldSchema]
    
    def validate(self, artifact_data: Dict[str, Any]) -> List[str]:
        """
        Validate artifact data against schema.
        
        Args:
            artifact_data: Parsed artifact to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields present
        for field in self.fields:
            if field.required and field.name not in artifact_data:
                errors.append(f"Missing required field: {field.name}")
        
        # Validate field types and constraints
        for field in self.fields:
            if field.name not in artifact_data:
                continue
            
            value = artifact_data[field.name]
            
            # Type checking
            if not self._check_type(value, field.field_type):
                errors.append(
                    f"Field {field.name} has wrong type: "
                    f"expected {field.field_type}, got {type(value).__name__}"
                )
            
            # Constraint checking
            if field.constraints:
                constraint_errors = self._check_constraints(field.name, value, field.constraints)
                errors.extend(constraint_errors)
            
            # Nested schema validation
            if field.nested_schema and isinstance(value, dict):
                nested_errors = field.nested_schema.validate(value)
                errors.extend([f"{field.name}.{e}" for e in nested_errors])
        
        return errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_checks = {
            "string": lambda v: isinstance(v, str),
            "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "bool": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict)
        }
        
        return type_checks.get(expected_type, lambda v: True)(value)
    
    def _check_constraints(self, field_name: str, value: Any, constraints: Dict) -> List[str]:
        """Check if value satisfies constraints."""
        errors = []
        
        if "min" in constraints and value < constraints["min"]:
            errors.append(f"Field {field_name} below minimum: {value} < {constraints['min']}")
        
        if "max" in constraints and value > constraints["max"]:
            errors.append(f"Field {field_name} above maximum: {value} > {constraints['max']}")
        
        if "enum" in constraints and value not in constraints["enum"]:
            errors.append(f"Field {field_name} not in allowed values: {constraints['enum']}")
        
        if "pattern" in constraints and isinstance(value, str):
            import re
            if not re.match(constraints["pattern"], value):
                errors.append(f"Field {field_name} doesn't match pattern: {constraints['pattern']}")
        
        return errors

class SchemaRegistry:
    """
    Registry of all artifact schemas.
    
    Provides schema lookup, validation, and versioning support.
    """
    
    def __init__(self):
        self._schemas: Dict[ArtifactType, Dict[str, ArtifactSchema]] = {}
        self._register_builtin_schemas()
    
    def register_schema(self, schema: ArtifactSchema) -> None:
        """Register an artifact schema."""
        if schema.artifact_type not in self._schemas:
            self._schemas[schema.artifact_type] = {}
        
        self._schemas[schema.artifact_type][schema.schema_version] = schema
    
    def get_schema(self, artifact_type: ArtifactType, version: str) -> ArtifactSchema:
        """Get schema for specific artifact type and version."""
        if artifact_type not in self._schemas:
            raise ValueError(f"Unknown artifact type: {artifact_type}")
        
        if version not in self._schemas[artifact_type]:
            available = list(self._schemas[artifact_type].keys())
            raise ValueError(
                f"Unknown schema version {version} for {artifact_type}. "
                f"Available: {available}"
            )
        
        return self._schemas[artifact_type][version]
    
    def get_latest_schema(self, artifact_type: ArtifactType) -> ArtifactSchema:
        """Get latest schema version for artifact type."""
        if artifact_type not in self._schemas:
            raise ValueError(f"Unknown artifact type: {artifact_type}")
        
        versions = list(self._schemas[artifact_type].keys())
        if not versions:
            raise ValueError(f"No schemas registered for {artifact_type}")
        
        # Sort versions and return latest
        latest_version = sorted(versions, key=lambda v: SemanticVersion.parse(v))[-1]
        return self._schemas[artifact_type][latest_version]
    
    def _register_builtin_schemas(self) -> None:
        """Register built-in artifact schemas."""
        # ExecutionContext schema
        execution_context_schema = ArtifactSchema(
            artifact_type=ArtifactType.EXECUTION_CONTEXT,
            schema_version="1.0.0",
            description="Immutable execution environment snapshot",
            fields=[
                FieldSchema("platform", "object", True, "Platform identification"),
                FieldSchema("compiler", "object", True, "Compiler information"),
                FieldSchema("native_library", "object", True, "Native library info"),
                FieldSchema("target_runtime", "object", True, "Target language runtime"),
                FieldSchema("verification_config", "object", True, "Verification configuration"),
                FieldSchema("provenance", "object", True, "Provenance metadata"),
                FieldSchema("artifacts", "object", True, "Artifact paths")
            ]
        )
        self.register_schema(execution_context_schema)
        
        # PipelineExecutionLog schema
        pipeline_log_schema = ArtifactSchema(
            artifact_type=ArtifactType.PIPELINE_LOG,
            schema_version="1.0.0",
            description="Pipeline orchestration execution log",
            fields=[
                FieldSchema("execution_id", "string", True, "Execution ID (UUID)"),
                FieldSchema("start_time", "string", True, "Pipeline start timestamp (ISO 8601)"),
                FieldSchema("end_time", "string", False, "Pipeline end timestamp"),
                FieldSchema("entries", "array", True, "Log entries")
            ]
        )
        self.register_schema(pipeline_log_schema)

# ───────────────────────────────────────────────────────────────────
# 3.2 Provenance Chain Validator
# ───────────────────────────────────────────────────────────────────

class ProvenanceChainValidator:
    """
    Validates provenance chains across multiple artifacts.
    
    Ensures artifacts form valid lineage with consistent execution context
    and unbroken hash chains.
    """
    
    def __init__(self, artifact_validator: EnhancedArtifactValidator):
        self.artifact_validator = artifact_validator
    
    def validate_chain(self, artifact_paths: List[str]) -> List[str]:
        """
        Validate provenance chain across multiple artifacts.
        
        Args:
            artifact_paths: List of artifact paths to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Load all artifacts
        artifacts = []
        for path in artifact_paths:
            try:
                artifact = self.artifact_validator.validate_artifact(path, verify_hashes=False)
                artifacts.append((path, artifact))
            except Exception as e:
                errors.append(f"Failed to load {path}: {e}")
                return errors
        
        # Check execution ID consistency
        execution_ids = set(a["provenance"]["execution_id"] for _, a in artifacts)
        if len(execution_ids) > 1:
            errors.append(
                f"Inconsistent execution IDs across artifacts: {execution_ids}. "
                f"All artifacts in a chain must share the same execution_id."
            )
        
        # Check timestamp ordering
        artifacts_with_time = [
            (path, a["provenance"]["creation_timestamp"], a)
            for path, a in artifacts
        ]
        artifacts_with_time.sort(key=lambda x: x[1])
        
        # Build dependency graph
        dep_graph = {}
        for path, artifact in artifacts:
            provenance = artifact["provenance"]
            dep_graph[path] = set(provenance["input_artifact_hashes"].keys())
        
        # Check for cycles (artifacts shouldn't transitively depend on themselves)
        if self._has_cycle(dep_graph):
            errors.append("Provenance chain contains cycle (artifact depends on itself)")
        
        # Verify hash chains
        for path, artifact in artifacts:
            provenance = artifact["provenance"]
            for input_path, declared_hash in provenance["input_artifact_hashes"].items():
                if not os.path.exists(input_path):
                    errors.append(f"{path} references missing input: {input_path}")
                    continue
                
                actual_hash = ArtifactValidator.compute_artifact_hash(input_path)
                if actual_hash != declared_hash:
                    errors.append(
                        f"{path} has hash mismatch for input {input_path}:\n"
                        f"  Declared: {declared_hash}\n"
                        f"  Actual: {actual_hash}"
                    )
        
        return errors
    
    def _has_cycle(self, graph: Dict[str, Set[str]]) -> bool:
        """Detect cycles in dependency graph using DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False

# ───────────────────────────────────────────────────────────────────
# 3.3 Staleness Detector
# ───────────────────────────────────────────────────────────────────

class StalenessStatus(Enum):
    """Artifact freshness status."""
    FRESH = "fresh"                    # All inputs unchanged, can reuse
    STALE = "stale"                    # Inputs changed, must regenerate
    POTENTIALLY_STALE = "potentially_stale"  # Stage updated, may need regeneration
    MISSING = "missing"                # Artifact doesn't exist

class StalenessDetector:
    """
    Detects stale artifacts for incremental verification.
    
    An artifact is stale if its inputs have changed or the stage that
    produced it has been updated.
    """
    
    def __init__(self, artifact_validator: EnhancedArtifactValidator):
        self.artifact_validator = artifact_validator
        self.current_execution_context: Optional[Dict] = None
    
    def set_current_execution_context(self, context: Dict) -> None:
        """Set current execution context for staleness checking."""
        self.current_execution_context = context
    
    def check_staleness(self, artifact_path: str, stage_class: type) -> StalenessStatus:
        """
        Check if artifact is stale.
        
        Args:
            artifact_path: Path to artifact
            stage_class: Stage class that produces this artifact
            
        Returns:
            Staleness status
        """
        # Check if artifact exists
        if not os.path.exists(artifact_path):
            return StalenessStatus.MISSING
        
        try:
            artifact = self.artifact_validator.validate_artifact(artifact_path, verify_hashes=False)
        except Exception as e:
            # Artifact is corrupted or invalid
            return StalenessStatus.STALE
        
        provenance = artifact["provenance"]
        
        # Check 1: Have input artifacts changed
        for input_path, declared_hash in provenance["input_artifact_hashes"].items():
            if not os.path.exists(input_path):
                # Input artifact missing
                return StalenessStatus.STALE
            
            actual_hash = ArtifactValidator.compute_artifact_hash(input_path)
            if actual_hash != declared_hash:
                # Input artifact changed
                return StalenessStatus.STALE
        
        # Check 2: Has stage version changed
        if stage_class.STAGE_VERSION != provenance["stage_version"]:
            # Stage updated - artifact may still be valid but should be regenerated
            return StalenessStatus.POTENTIALLY_STALE
        
        # Check 3: Has execution context changed materially
        if self.current_execution_context:
            current_exec_id = self.current_execution_context["provenance"]["execution_id"]
            artifact_exec_id = provenance["execution_id"]
            
            if current_exec_id != artifact_exec_id:
                # Different execution context - check if relevant fields changed
                if self._execution_context_changed_materially():
                    return StalenessStatus.STALE
        
        # All checks passed - artifact is fresh
        return StalenessStatus.FRESH
    
    def _execution_context_changed_materially(self) -> bool:
        """
        Check if execution context changed in ways that affect artifacts.
        
        Material changes:
        - Platform architecture changed (x64 → x86)
        - Compiler changed or upgraded
        - Compiler flags changed
        
        Non-material changes:
        - Timestamp changed
        - execution_id changed
        - Working directory changed
        """
        # For now, assume any execution context change is material
        # (Full implementation would compare specific fields)
        return True

# ───────────────────────────────────────────────────────────────────
# 3.4 Incremental Pipeline Executor
# ───────────────────────────────────────────────────────────────────

class IncrementalPipelineExecutor:
    """
    Executes pipeline incrementally, reusing fresh artifacts.
    
    Only re-runs stages whose outputs are stale or missing.
    """
    
    def __init__(
        self,
        pipeline: 'EnhancedVerificationPipeline',
        staleness_detector: StalenessDetector
    ):
        self.pipeline = pipeline
        self.staleness_detector = staleness_detector
    
    def execute_incremental(self, target_artifact: Optional[str] = None) -> bool:
        """
        Execute pipeline incrementally.
        
        Args:
            target_artifact: Target artifact to produce (None = all artifacts)
            
        Returns:
            True if execution successful
        """
        self.pipeline.execution_log.log_pipeline_start()
        
        # Build dependency graph
        stage_classes = [
            self.pipeline.registry.get_stage_class(name)
            for name in self.pipeline.registry.list_stages()
        ]
        dep_graph = DependencyGraph(stage_classes)
        
        # Determine execution order
        try:
            execution_order = dep_graph.topological_sort()
        except ValueError as e:
            print(f"ERROR: {e}")
            self.pipeline.execution_log.log_pipeline_complete(False)
            return False
        
        # If target specified, prune stages not needed for target
        if target_artifact:
            execution_order = self._prune_to_target(execution_order, target_artifact, dep_graph)
        
        # Check staleness and execute only stale stages
        success = True
        for stage_name in execution_order:
            stage_class = self.pipeline.registry.get_stage_class(stage_name)
            
            # Determine artifact path
            artifacts_dir = self.pipeline.execution_context["artifacts"]["working_directory"]
            artifact_paths = [
                os.path.join(artifacts_dir, f"{output}.json")
                for output in stage_class.PRODUCED_OUTPUTS
            ]
            
            # Check staleness
            staleness_statuses = [
                self.staleness_detector.check_staleness(path, stage_class)
                for path in artifact_paths
            ]
            
            # Skip if all artifacts are fresh
            if all(status == StalenessStatus.FRESH for status in staleness_statuses):
                print(f"⏭️  Skipping {stage_name} (artifacts are fresh)")
                continue
            
            # Execute stage
            print(f"▶️  Running {stage_name} (artifacts are {staleness_statuses[0].value})")
            
            try:
                stage = stage_class(self.pipeline.execution_context)
                self.pipeline.execution_log.log_stage_start(stage)
                stage.execute()
                self.pipeline.execution_log.log_stage_complete(stage)
            except Exception as e:
                self.pipeline.execution_log.log_stage_failed(stage, e)
                print(f"ERROR: {e}")
                success = False
                break
        
        self.pipeline.execution_log.log_pipeline_complete(success)
        
        # Save execution log
        log_path = os.path.join(
            self.pipeline.execution_context["artifacts"]["working_directory"],
            "pipeline_execution_log.json"
        )
        self.pipeline.execution_log.save(log_path)
        
        return success
    
    def _prune_to_target(
        self,
        execution_order: List[str],
        target_artifact: str,
        dep_graph: DependencyGraph
    ) -> List[str]:
        """Prune execution order to only include stages needed for target."""
        # Find stage that produces target
        target_stage = None
        for stage_name, stage_class in self.pipeline.registry._stages.items():
            if target_artifact in stage_class.PRODUCED_OUTPUTS:
                target_stage = stage_name
                break
        
        if not target_stage:
            raise ValueError(f"No stage produces artifact: {target_artifact}")
        
        # Find all stages that target depends on (recursively)
        needed_stages = set()
        
        def collect_dependencies(stage_name: str):
            needed_stages.add(stage_name)
            for dependency in dep_graph.graph.get(stage_name, set()):
                collect_dependencies(dependency)
        
        collect_dependencies(target_stage)
        
        # Filter execution order
        return [s for s in execution_order if s in needed_stages]

# ───────────────────────────────────────────────────────────────────
# 3.5 CLI Extensions for Incremental Verification
# ───────────────────────────────────────────────────────────────────

def main_with_incremental():
    """CLI with incremental verification support."""
    parser = argparse.ArgumentParser(
        prog="verification_pipeline",
        description="Polyglot FFI Verification Pipeline with Incremental Support"
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Existing commands
    info_cmd = subparsers.add_parser("info", help="Show pipeline information")
    
    # New command: run-incremental
    incremental_cmd = subparsers.add_parser(
        "run-incremental",
        help="Run pipeline incrementally (reuse fresh artifacts)"
    )
    incremental_cmd.add_argument("--context", required=True, help="Execution context path")
    incremental_cmd.add_argument("--target", help="Target artifact to produce")
    
    # New command: check-staleness
    staleness_cmd = subparsers.add_parser(
        "check-staleness",
        help="Check artifact staleness status"
    )
    staleness_cmd.add_argument("artifact", help="Artifact path to check")
    staleness_cmd.add_argument("--context", required=True)
    
    args = parser.parse_args()
    
    if args.command == "info":
        print("Polyglot FFI Verification Pipeline")
        print("=" * 60)
        print("Version: 1.0.0 (with Incremental Support)")
        print("Module: 02 - Verification Pipeline")
        print("Prompt: 3/20 - Artifact Schemas & Incremental Verification")
        return 0
    
    elif args.command == "run-incremental":
        try:
            pipeline = EnhancedVerificationPipeline(args.context)
            pipeline.artifact_validator = EnhancedArtifactValidator()
            
            staleness_detector = StalenessDetector(pipeline.artifact_validator)
            staleness_detector.set_current_execution_context(pipeline.execution_context)
            
            executor = IncrementalPipelineExecutor(pipeline, staleness_detector)
            success = executor.execute_incremental(args.target)
            
            return 0 if success else 1
        except Exception as e:
            print(f"ERROR: {e}")
            return 1
    
    elif args.command == "check-staleness":
        try:
            pipeline = EnhancedVerificationPipeline(args.context)
            validator = EnhancedArtifactValidator()
            detector = StalenessDetector(validator)
            detector.set_current_execution_context(pipeline.execution_context)
            
            # Determine which stage produces this artifact
            artifact_name = os.path.basename(args.artifact).replace(".json", "")
            stage_class = None
            for name in pipeline.registry.list_stages():
                sc = pipeline.registry.get_stage_class(name)
                if artifact_name in sc.PRODUCED_OUTPUTS:
                    stage_class = sc
                    break
            
            if not stage_class:
                print(f"Unknown artifact type: {artifact_name}")
                return 1
            
            status = detector.check_staleness(args.artifact, stage_class)
            print(f"Staleness status: {status.value}")
            
            if status == StalenessStatus.FRESH:
                print("✓ Artifact is fresh and can be reused")
            elif status == StalenessStatus.STALE:
                print("✗ Artifact is stale and must be regenerated")
            elif status == StalenessStatus.POTENTIALLY_STALE:
                print("⚠ Artifact may be stale (stage version changed)")
            elif status == StalenessStatus.MISSING:
                print("✗ Artifact does not exist")
            
            return 0 if status == StalenessStatus.FRESH else 1
        except Exception as e:
            print(f"ERROR: {e}")
            return 1
    
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main_with_incremental())
