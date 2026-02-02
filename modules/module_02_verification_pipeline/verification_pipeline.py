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
import random
import uuid
import time
import traceback
import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
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
        
        # Register stages
        if 'NativeInterfaceIngestionStage' in globals():
            self.registry.register_stage(NativeInterfaceIngestionStage)
        if 'IRNormalizationStage' in globals():
            self.registry.register_stage(IRNormalizationStage)
        if 'ContractSynthesisStage' in globals():
            self.registry.register_stage(ContractSynthesisStage)
        if 'AdapterGenerationStage' in globals():
            self.registry.register_stage(AdapterGenerationStage)
        if 'TestPlanGenerationStage' in globals():
            self.registry.register_stage(TestPlanGenerationStage)
        if 'VerificationExecutionStage' in globals():
            self.registry.register_stage(VerificationExecutionStage)
        if 'DiagnosticsReportingStage' in globals():
            self.registry.register_stage(DiagnosticsReportingStage)
    
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

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 4.1 libclang Integration
# ───────────────────────────────────────────────────────────────────

try:
    import clang.cindex as clang
    LIBCLANG_AVAILABLE = True
except ImportError:
    LIBCLANG_AVAILABLE = False
    clang = None

def initialize_libclang() -> bool:
    """
    Initialize libclang library.
    
    Attempts to locate libclang.dll/so and configure clang.cindex.
    
    Returns:
        True if initialization successful, False otherwise
    """
    if not LIBCLANG_AVAILABLE:
        return False
    
    # Check if LIBCLANG_PATH environment variable is set
    libclang_path = os.environ.get('LIBCLANG_PATH')
    
    if libclang_path and os.path.exists(libclang_path):
        clang.Config.set_library_file(libclang_path)
        return True
    
    # Try using clang.native (from pip install libclang)
    try:
        import clang.native
        native_dir = os.path.dirname(clang.native.__file__)
        for file in os.listdir(native_dir):
            if file.startswith("libclang") and (file.endswith(".dll") or file.endswith(".so") or file.endswith(".dylib")):
                clang.Config.set_library_file(os.path.join(native_dir, file))
                return True
    except (ImportError, AttributeError, OSError):
        pass

    # Try common locations
    common_paths = [
        r"C:\Program Files\LLVM\bin\libclang.dll",
        r"C:\Program Files (x86)\LLVM\bin\libclang.dll",
        r"C:\Program Files\LLVM\bin\libclang.dll",
        "/usr/lib/llvm-16/lib/libclang.so",
        "/usr/lib/llvm-14/lib/libclang.so",
        "/usr/local/lib/libclang.dylib"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            clang.Config.set_library_file(path)
            return True
    
    return False

# ───────────────────────────────────────────────────────────────────
# 4.2 Type Extractor
# ───────────────────────────────────────────────────────────────────

class TypeExtractor:
    """
    Extracts complete type information from libclang type objects.
    
    Handles recursive type structures (pointers to arrays to structs, etc.)
    """
    
    @staticmethod
    def extract_type(clang_type) -> Dict[str, Any]:
        """
        Extract complete type information from clang type.
        
        Args:
            clang_type: clang.cindex.Type object
            
        Returns:
            Dictionary with type information
        """
        type_info = {
            "size_bytes": clang_type.get_size(),
            "alignment_bytes": clang_type.get_align()
        }
        
        # Determine type kind
        kind = clang_type.kind
        
        if kind in [clang.TypeKind.VOID, clang.TypeKind.BOOL,
                    clang.TypeKind.CHAR_U, clang.TypeKind.UCHAR,
                    clang.TypeKind.CHAR_S, clang.TypeKind.SCHAR,
                    clang.TypeKind.USHORT, clang.TypeKind.SHORT,
                    clang.TypeKind.UINT, clang.TypeKind.INT,
                    clang.TypeKind.ULONG, clang.TypeKind.LONG,
                    clang.TypeKind.ULONGLONG, clang.TypeKind.LONGLONG,
                    clang.TypeKind.FLOAT, clang.TypeKind.DOUBLE]:
            type_info["kind"] = "primitive"
            type_info["name"] = clang_type.spelling
            type_info["is_signed"] = kind not in [
                clang.TypeKind.UCHAR, clang.TypeKind.USHORT,
                clang.TypeKind.UINT, clang.TypeKind.ULONG,
                clang.TypeKind.ULONGLONG
            ]
        
        elif kind == clang.TypeKind.POINTER:
            type_info["kind"] = "pointer"
            type_info["pointee"] = TypeExtractor.extract_type(clang_type.get_pointee())
        
        elif kind == clang.TypeKind.CONSTANTARRAY:
            type_info["kind"] = "array"
            type_info["element_type"] = TypeExtractor.extract_type(clang_type.get_array_element_type())
            type_info["size"] = clang_type.get_array_size()
        
        elif kind in [clang.TypeKind.RECORD, clang.TypeKind.ELABORATED]:
            decl = clang_type.get_declaration()
            type_info["kind"] = "struct" if decl.kind == clang.IDEKind.STRUCT_DECL else "union"
            type_info["name"] = clang_type.spelling
        
        elif kind == clang.TypeKind.TYPEDEF:
            type_info["kind"] = "typedef"
            type_info["name"] = clang_type.spelling
            type_info["underlying_type"] = TypeExtractor.extract_type(clang_type.get_canonical())
        
        elif kind == clang.TypeKind.ENUM:
            type_info["kind"] = "enum"
            type_info["name"] = clang_type.spelling
        
        else:
            type_info["kind"] = "unknown"
            type_info["name"] = clang_type.spelling
        
        # Extract qualifiers
        type_info["is_const"] = clang_type.is_const_qualified()
        type_info["is_volatile"] = clang_type.is_volatile_qualified()
        
        return type_info

# ───────────────────────────────────────────────────────────────────
# 4.3 Struct Layout Extractor
# ───────────────────────────────────────────────────────────────────

class StructLayoutExtractor:
    """
    Extracts struct layouts with explicit padding detection.
    
    Computes implicit padding fields by comparing field offsets.
    """
    
    @staticmethod
    def extract_layout(cursor) -> Dict[str, Any]:
        """
        Extract complete struct layout including padding.
        
        Args:
            cursor: clang.cindex.IDE for struct
            
        Returns:
            Dictionary with struct layout information
        """
        is_union = cursor.kind == clang.IDEKind.UNION_DECL
        
        layout = {
            "name": cursor.spelling,
            "size_bytes": cursor.type.get_size(),
            "alignment_bytes": cursor.type.get_align(),
            "is_union": is_union,
            "fields": []
        }
        
        # Extract declared fields
        declared_fields = []
        for child in cursor.get_children():
            if child.kind == clang.IDEKind.FIELD_DECL:
                field_info = {
                    "name": child.spelling,
                    "offset_bytes": cursor.type.get_offset(child.spelling) // 8,
                    "type": TypeExtractor.extract_type(child.type),
                    "size_bytes": child.type.get_size(),
                    "is_implicit": False
                }
                declared_fields.append(field_info)
        
        # Sort fields by offset
        declared_fields.sort(key=lambda f: f["offset_bytes"])
        
        # Detect padding (not needed for unions)
        if is_union:
            layout["fields"] = declared_fields
        else:
            layout["fields"] = StructLayoutExtractor._insert_padding(
                declared_fields,
                layout["size_bytes"],
                layout["alignment_bytes"]
            )
        
        return layout
    
    @staticmethod
    def _insert_padding(
        fields: List[Dict],
        total_size: int,
        alignment: int
    ) -> List[Dict]:
        """
        Insert implicit padding fields.
        
        Args:
            fields: Declared fields (sorted by offset)
            total_size: Total struct size
            alignment: Struct alignment
            
        Returns:
            Fields with padding inserted
        """
        result = []
        padding_count = 0
        
        for i, field in enumerate(fields):
            # Add this field
            result.append(field)
            
            # Check if padding needed before next field
            if i + 1 < len(fields):
                next_field = fields[i + 1]
                current_end = field["offset_bytes"] + field["size_bytes"]
                next_start = next_field["offset_bytes"]
                
                if next_start > current_end:
                    padding_count += 1
                    padding_field = {
                        "name": f"__padding_{padding_count}",
                        "offset_bytes": current_end,
                        "type": {"kind": "padding", "size_bytes": next_start - current_end},
                        "size_bytes": next_start - current_end,
                        "is_implicit": True
                    }
                    result.append(padding_field)
        
        # Check for trailing padding
        if fields:
            last_field = fields[-1]
            last_end = last_field["offset_bytes"] + last_field["size_bytes"]
            
            if total_size > last_end:
                padding_count += 1
                padding_field = {
                    "name": f"__padding_{padding_count}",
                    "offset_bytes": last_end,
                    "type": {"kind": "padding", "size_bytes": total_size - last_end},
                    "size_bytes": total_size - last_end,
                    "is_implicit": True
                }
                result.append(padding_field)
        
        return result

# ───────────────────────────────────────────────────────────────────
# 4.4 Native Interface Ingestion Stage
# ───────────────────────────────────────────────────────────────────

class NativeInterfaceIngestionStage(PipelineStage):
    """
    Stage 1: Native Interface Ingestion
    
    Extracts compiler-grade ABI information from C headers using libclang.
    This is a lossless extraction - all ABI-relevant details are preserved.
    """
    
    STAGE_NAME = "native_interface_ingestion"
    STAGE_VERSION = "1.0.0"
    STAGE_DESCRIPTION = "Extract ABI surface from C headers using libclang"
    
    REQUIRED_INPUTS = []  # Only requires ExecutionContext (not an artifact)
    PRODUCED_OUTPUTS = ["native_interface"]
    
    def _execute_impl(self) -> None:
        """Extract native interface from header file."""
        # Check libclang availability
        if not LIBCLANG_AVAILABLE:
            raise StageError(
                "libclang not available. Install with: pip install libclang",
                stage_name=self.STAGE_NAME,
                details="libclang is required for native interface ingestion"
            )
        
        if not initialize_libclang():
            raise StageError(
                "Failed to initialize libclang",
                stage_name=self.STAGE_NAME,
                details="Set LIBCLANG_PATH environment variable to libclang.dll/so location"
            )
        
        # Extract paths from execution context
        header_path = self.execution_context["native_library"]["interface_header_path"]
        library_path = self.execution_context["native_library"]["library_path"]
        
        # Build compilation arguments
        comp_args = self._build_compilation_args()
        
        # Parse header with libclang
        index = clang.Index.create()
        try:
            tu = index.parse(
                header_path,
                args=comp_args,
                options=clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            )
        except Exception as e:
            raise StageError(
                f"Failed to parse header: {e}",
                stage_name=self.STAGE_NAME,
                details=f"Header: {header_path}"
            )
        
        # Check for parse errors
        if tu.diagnostics:
            errors = [d for d in tu.diagnostics if d.severity >= clang.Diagnostic.Error]
            if errors:
                error_msgs = "\n".join([f"{d.location}: {d.spelling}" for d in errors])
                raise StageError(
                    f"Header compilation failed:\n{error_msgs}",
                    stage_name=self.STAGE_NAME,
                    details="Fix syntax errors or add missing include paths"
                )
        
        # Extract symbols
        functions = []
        structures = []
        enumerations = []
        typedefs = []
        
        for cursor in tu.cursor.walk_preorder():
            # Only process symbols from the target header (not included headers)
            if cursor.location.file and cursor.location.file.name != header_path:
                continue
            
            if cursor.kind == clang.IDEKind.FUNCTION_DECL:
                functions.append(self._extract_function(cursor))
            
            elif cursor.kind in [clang.IDEKind.STRUCT_DECL, clang.IDEKind.UNION_DECL]:
                if cursor.is_definition():  # Only process definitions, not forward declarations
                    structures.append(StructLayoutExtractor.extract_layout(cursor))
            
            elif cursor.kind == clang.IDEKind.ENUM_DECL:
                if cursor.is_definition():
                    enumerations.append(self._extract_enum(cursor))
            
            elif cursor.kind == clang.IDEKind.TYPEDEF_DECL:
                typedefs.append(self._extract_typedef(cursor))
        
        # Build artifact
        artifacts_dir = self.execution_context["artifacts"]["working_directory"]
        context_path = self.execution_context["artifacts"]["execution_context_path"]
        
        provenance = self.create_provenance([context_path])
        
        artifact = {
            "provenance": provenance.to_dict(),
            "header_path": os.path.abspath(header_path),
            "library_path": os.path.abspath(library_path),
            "compilation_flags": comp_args,
            "functions": functions,
            "structures": structures,
            "enumerations": enumerations,
            "typedefs": typedefs
        }
        
        # Write artifact
        output_path = os.path.join(artifacts_dir, "native_interface.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(artifact, f, indent=2)
    
    def _build_compilation_args(self) -> List[str]:
        """Build compilation arguments from execution context."""
        args = []
        
        compiler_info = self.execution_context["compiler"]
        
        # Add include paths
        for include_path in compiler_info.get("include_paths", []):
            args.append(f"-I{include_path}")
        
        # Add preprocessor macros
        for macro, value in compiler_info.get("preprocessor_macros", {}).items():
            if value:
                args.append(f"-D{macro}={value}")
            else:
                args.append(f"-D{macro}")
        
        # Add platform-specific flags
        platform = self.execution_context["platform"]
        if platform["os_name"] == "Windows":
            args.append("-fms-compatibility")
            args.append("-fms-extensions")
        
        return args
    
    def _extract_function(self, cursor) -> Dict[str, Any]:
        """Extract function information."""
        # Extract parameters
        parameters = []
        for arg in cursor.get_arguments():
            parameters.append({
                "name": arg.spelling,
                "type": TypeExtractor.extract_type(arg.type),
                "position": len(parameters)
            })
        
        # Detect calling convention
        calling_conv = cursor.type.get_calling_conv()
        calling_conv_str = self._map_calling_convention(calling_conv)
        
        return {
            "name": cursor.spelling,
            "return_type": TypeExtractor.extract_type(cursor.result_type),
            "parameters": parameters,
            "calling_convention": calling_conv_str,
            "source_location": {
                "file": cursor.location.file.name if cursor.location.file else "<unknown>",
                "line": cursor.location.line,
                "column": cursor.location.column
            }
        }
    
    def _map_calling_convention(self, clang_conv) -> str:
        """Map libclang calling convention to string."""
        conv_map = {
            clang.CallingConv.C: "cdecl",
            clang.CallingConv.X86_STDCALL: "stdcall",
            clang.CallingConv.X86_FASTCALL: "fastcall",
            clang.CallingConv.WIN64: "win64",
            clang.CallingConv.X86_THISCALL: "thiscall"
        }
        return conv_map.get(clang_conv, "cdecl")
    
    def _extract_enum(self, cursor) -> Dict[str, Any]:
        """Extract enumeration information."""
        constants = []
        for child in cursor.get_children():
            if child.kind == clang.IDEKind.ENUM_CONSTANT_DECL:
                constants.append({
                    "name": child.spelling,
                    "value": child.enum_value
                })
        
        return {
            "name": cursor.spelling,
            "underlying_type": TypeExtractor.extract_type(cursor.enum_type),
            "constants": constants,
            "source_location": {
                "file": cursor.location.file.name if cursor.location.file else "<unknown>",
                "line": cursor.location.line,
                "column": cursor.location.column
            }
        }
    
    def _extract_typedef(self, cursor) -> Dict[str, Any]:
        """Extract typedef information."""
        return {
            "name": cursor.spelling,
            "underlying_type": TypeExtractor.extract_type(cursor.underlying_typedef_type),
            "source_location": {
                "file": cursor.location.file.name if cursor.location.file else "<unknown>",
                "line": cursor.location.line,
                "column": cursor.location.column
            }
        }

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 5.1 Type ID Generator
# ───────────────────────────────────────────────────────────────────

class TypeIDGenerator:
    """
    Generates stable, unique type IDs from type structures.
    
    Type IDs are deterministic and human-readable for debugging.
    """
    
    @staticmethod
    def generate(type_info: Dict[str, Any]) -> str:
        """
        Generate type ID from type structure.
        
        Args:
            type_info: Type information dictionary
            
        Returns:
            Unique type ID string
        """
        kind = type_info.get("kind")
        
        if kind == "primitive":
            # Handle signed/unsigned variants
            name = type_info["name"].replace(" ", "_")
            return f"primitive_{name}"
        
        elif kind == "pointer":
            pointee = type_info.get("pointee", {})
            pointee_id = TypeIDGenerator.generate(pointee)
            
            # Include qualifiers in ID
            qualifiers = []
            if type_info.get("is_const"):
                qualifiers.append("const")
            if type_info.get("is_volatile"):
                qualifiers.append("volatile")
            
            qual_str = "_".join(qualifiers) + "_" if qualifiers else ""
            return f"{qual_str}pointer_to_{pointee_id}"
        
        elif kind == "array":
            element = type_info.get("element_type", {})
            element_id = TypeIDGenerator.generate(element)
            size = type_info.get("size", 0)
            return f"array_{size}_of_{element_id}"
        
        elif kind == "struct":
            name = type_info.get("name", "anonymous")
            return f"struct_{name}"
        
        elif kind == "union":
            name = type_info.get("name", "anonymous")
            return f"union_{name}"
        
        elif kind == "enum":
            name = type_info.get("name", "anonymous")
            return f"enum_{name}"
        
        elif kind == "typedef":
            name = type_info.get("name", "anonymous")
            return f"typedef_{name}"
        
        elif kind == "padding":
            size = type_info.get("size_bytes", 0)
            return f"padding_{size}"
        
        else:
            # Unknown type - generate hash-based ID
            import hashlib
            type_str = json.dumps(type_info, sort_keys=True)
            hash_val = hashlib.sha256(type_str.encode()).hexdigest()[:16]
            return f"unknown_{hash_val}"

# ───────────────────────────────────────────────────────────────────
# 5.2 Type Registry
# ───────────────────────────────────────────────────────────────────

class TypeRegistry:
    """
    Registry of all types with bidirectional lookup.
    
    Maintains:
    - type_id → type_info (forward lookup)
    - type_structure → type_id (reverse lookup for deduplication)
    """
    
    def __init__(self):
        self._types: Dict[str, Dict[str, Any]] = {}  # type_id → type_info
        self._structure_to_id: Dict[str, str] = {}   # JSON(type_info) → type_id
    
    def register_type(self, type_info: Dict[str, Any]) -> str:
        """
        Register a type and return its ID.
        
        If type already registered, returns existing ID.
        
        Args:
            type_info: Type information dictionary
            
        Returns:
            Type ID
        """
        # Generate canonical structure key (for deduplication)
        structure_key = self._make_structure_key(type_info)
        
        # Check if already registered
        if structure_key in self._structure_to_id:
            return self._structure_to_id[structure_key]
        
        # Generate new type ID
        type_id = TypeIDGenerator.generate(type_info)
        
        # Handle ID collisions (rare but possible)
        original_id = type_id
        counter = 1
        while type_id in self._types:
            type_id = f"{original_id}_{counter}"
            counter += 1
        
        # Register type
        self._types[type_id] = type_info
        self._structure_to_id[structure_key] = type_id
        
        return type_id
    
    def get_type(self, type_id: str) -> Dict[str, Any]:
        """Get type information by ID."""
        if type_id not in self._types:
            raise KeyError(f"Unknown type ID: {type_id}")
        return self._types[type_id]
    
    def has_type(self, type_id: str) -> bool:
        """Check if type ID is registered."""
        return type_id in self._types
    
    def get_all_types(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered types."""
        return dict(self._types)
    
    def _make_structure_key(self, type_info: Dict[str, Any]) -> str:
        """Create canonical key from type structure for deduplication."""
        # Remove metadata fields that don't affect type identity
        canonical = {k: v for k, v in type_info.items() 
                    if k not in ["source_location", "is_implicit"]}
        
        return json.dumps(canonical, sort_keys=True)

# ───────────────────────────────────────────────────────────────────
# 5.3 Typedef Resolver
# ───────────────────────────────────────────────────────────────────

class TypedefResolver:
    """
    Resolves typedef chains to underlying canonical types.
    
    Handles:
    - Transitive typedef resolution
    - Circular typedef detection
    - Preservation of typedef info for diagnostics
    """
    
    def __init__(self):
        self._typedef_map: Dict[str, Dict] = {}  # typedef_name → full typedef info
    
    def register_typedef(self, typedef_info: Dict[str, Any]) -> None:
        """Register a typedef for later resolution."""
        name = typedef_info["name"]
        self._typedef_map[name] = typedef_info
    
    def resolve(self, type_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve typedef to underlying canonical type.
        
        Args:
            type_info: Type that may be a typedef
            
        Returns:
            Resolved canonical type (not a typedef)
            
        Raises:
            StageError: If circular typedef detected
        """
        if type_info.get("kind") != "typedef":
            return type_info
        
        visited = set()
        current = type_info
        
        while current.get("kind") == "typedef":
            typedef_name = current.get("name")
            
            if typedef_name in visited:
                cycle = " → ".join(visited) + f" → {typedef_name}"
                raise StageError(
                    f"Circular typedef detected: {cycle}",
                    stage_name="ir_normalization"
                )
            
            visited.add(typedef_name)
            
            # Get underlying type
            underlying = current.get("underlying_type")
            if not underlying:
                raise StageError(
                    f"Typedef '{typedef_name}' missing underlying type",
                    stage_name="ir_normalization"
                )
            
            current = underlying
        
        return current

# ───────────────────────────────────────────────────────────────────
# 5.4 Type Normalizer
# ───────────────────────────────────────────────────────────────────

class TypeNormalizer:
    """
    Normalizes types from native interface to canonical IR form.
    
    Handles:
    - Typedef resolution
    - Type registration
    - Qualifier normalization
    - Recursive type processing
    """
    
    def __init__(self, type_registry: TypeRegistry, typedef_resolver: TypedefResolver):
        self.type_registry = type_registry
        self.typedef_resolver = typedef_resolver
    
    def normalize_type(self, native_type: Dict[str, Any], resolve_typedefs: bool = True) -> str:
        """
        Normalize type and return its type ID.
        
        Args:
            native_type: Type from native interface
            resolve_typedefs: Whether to resolve typedefs to underlying types
            
        Returns:
            Type ID in registry
        """
        # Resolve typedefs if requested
        if resolve_typedefs and native_type.get("kind") == "typedef":
            resolved = self.typedef_resolver.resolve(native_type)
            # Register both typedef and underlying type
            typedef_id = self.type_registry.register_type(native_type)
            underlying_id = self.normalize_type(resolved, resolve_typedefs=False)
            
            # Link typedef to underlying
            typedef_info = self.type_registry.get_type(typedef_id)
            typedef_info["resolved_type_id"] = underlying_id
            
            return typedef_id
        
        # Normalize based on kind
        kind = native_type.get("kind")
        
        if kind in ["primitive", "enum"]:
            # Primitives and enums are already normalized
            return self.type_registry.register_type(native_type)
        
        elif kind == "pointer":
            # Normalize pointee recursively
            pointee = native_type.get("pointee", {})
            pointee_id = self.normalize_type(pointee, resolve_typedefs)
            
            normalized = {
                "kind": "pointer",
                "pointee_id": pointee_id,
                "size_bytes": native_type.get("size_bytes", 8),
                "alignment_bytes": native_type.get("alignment_bytes", 8),
                "is_const": native_type.get("is_const", False),
                "is_volatile": native_type.get("is_volatile", False),
                "is_restrict": native_type.get("is_restrict", False)
            }
            
            return self.type_registry.register_type(normalized)
        
        elif kind == "array":
            # Normalize element type recursively
            element = native_type.get("element_type", {})
            element_id = self.normalize_type(element, resolve_typedefs)
            
            normalized = {
                "kind": "array",
                "element_type_id": element_id,
                "size": native_type.get("size", 0),
                "size_bytes": native_type.get("size_bytes", 0)
            }
            
            return self.type_registry.register_type(normalized)
        
        elif kind in ["struct", "union"]:
            # Struct/union types are registered by name reference
            # Full definition handled separately
            normalized = {
                "kind": kind,
                "name": native_type.get("name", "anonymous"),
                "size_bytes": native_type.get("size_bytes", 0),
                "alignment_bytes": native_type.get("alignment_bytes", 0)
            }
            
            return self.type_registry.register_type(normalized)
        
        elif kind == "padding":
            # Padding is a synthetic type
            return self.type_registry.register_type(native_type)
        
        else:
            # Unknown type - register as-is
            return self.type_registry.register_type(native_type)

# ───────────────────────────────────────────────────────────────────
# 5.5 IR Normalization Stage
# ───────────────────────────────────────────────────────────────────

class IRNormalizationStage(PipelineStage):
    """
    Stage 2: IR Normalization
    
    Transforms raw native interface into canonical intermediate representation
    with typedef resolution, type registry, and normalized structures.
    """
    
    STAGE_NAME = "ir_normalization"
    STAGE_VERSION = "1.0.0"
    STAGE_DESCRIPTION = "Normalize native interface to canonical IR"
    
    REQUIRED_INPUTS = ["native_interface"]
    PRODUCED_OUTPUTS = ["ir"]
    
    def _execute_impl(self) -> None:
        """Normalize native interface to IR."""
        # Load native interface artifact
        artifacts_dir = self.execution_context["artifacts"]["working_directory"]
        native_interface_path = os.path.join(artifacts_dir, "native_interface.json")
        
        with open(native_interface_path, 'r', encoding='utf-8') as f:
            native_interface = json.load(f)
        
        # Initialize components
        type_registry = TypeRegistry()
        typedef_resolver = TypedefResolver()
        type_normalizer = TypeNormalizer(type_registry, typedef_resolver)
        
        # : Register all typedefs
        for typedef in native_interface.get("typedefs", []):
            typedef_resolver.register_typedef(typedef)
        
        # : Normalize functions
        normalized_functions = []
        for func in native_interface.get("functions", []):
            normalized_func = self._normalize_function(func, type_normalizer)
            normalized_functions.append(normalized_func)
        
        # : Normalize structures
        normalized_structures = []
        for struct in native_interface.get("structures", []):
            normalized_struct = self._normalize_structure(struct, type_normalizer)
            normalized_structures.append(normalized_struct)
        
        # : Normalize enumerations
        normalized_enums = []
        for enum in native_interface.get("enumerations", []):
            normalized_enum = self._normalize_enum(enum, type_normalizer)
            normalized_enums.append(normalized_enum)
        
        # : Extract platform info
        platform_info = {
            "pointer_size": self.execution_context["platform"]["pointer_width"] // 8,
            "endianness": self.execution_context["platform"]["endianness"],
            "alignment_rules": "msvc" if self.execution_context["platform"]["os_name"] == "Windows" else "gcc"
        }
        
        # Build IR artifact
        provenance = self.create_provenance([native_interface_path])
        
        ir_artifact = {
            "provenance": provenance.to_dict(),
            "platform": platform_info,
            "type_registry": type_registry.get_all_types(),
            "functions": normalized_functions,
            "structures": normalized_structures,
            "enumerations": normalized_enums
        }
        
        # Write IR artifact
        ir_path = os.path.join(artifacts_dir, "ir.json")
        with open(ir_path, 'w', encoding='utf-8') as f:
            json.dump(ir_artifact, f, indent=2)
    
    def _normalize_function(self, func: Dict, normalizer: TypeNormalizer) -> Dict:
        """Normalize function signature."""
        # Normalize return type
        return_type_id = normalizer.normalize_type(func["return_type"])
        
        # Normalize parameters
        normalized_params = []
        for i, param in enumerate(func.get("parameters", [])):
            param_type_id = normalizer.normalize_type(param["type"])
            
            # Generate name if missing
            param_name = param.get("name") or f"param_{i}"
            
            normalized_params.append({
                "name": param_name,
                "type_id": param_type_id,
                "position": param.get("position", i)
            })
        
        return {
            "name": func["name"],
            "return_type_id": return_type_id,
            "parameters": normalized_params,
            "calling_convention": func.get("calling_convention", "cdecl"),
            "source_location": func.get("source_location", {})
        }
    
    def _normalize_structure(self, struct: Dict, normalizer: TypeNormalizer) -> Dict:
        """Normalize struct layout."""
        # Generate struct type ID
        struct_type_id = TypeIDGenerator.generate({
            "kind": "struct" if not struct.get("is_union") else "union",
            "name": struct["name"]
        })
        
        # Normalize field types
        normalized_fields = []
        for field in struct.get("fields", []):
            field_type_id = normalizer.normalize_type(field["type"])
            
            normalized_field = {
                "name": field["name"],
                "type_id": field_type_id,
                "offset_bytes": field["offset_bytes"],
                "size_bytes": field["size_bytes"],
                "is_implicit": field.get("is_implicit", False)
            }
            
            # Preserve bitfield info if present
            if "is_bitfield" in field:
                normalized_field["is_bitfield"] = field["is_bitfield"]
                normalized_field["bitfield_width"] = field["bitfield_width"]
                normalized_field["bitfield_offset"] = field.get("bitfield_offset", 0)
            
            normalized_fields.append(normalized_field)
        
        return {
            "name": struct["name"],
            "type_id": struct_type_id,
            "size_bytes": struct["size_bytes"],
            "alignment_bytes": struct["alignment_bytes"],
            "is_union": struct.get("is_union", False),
            "fields": normalized_fields,
            "source_location": struct.get("source_location", {})
        }
    
    def _normalize_enum(self, enum: Dict, normalizer: TypeNormalizer) -> Dict:
        """Normalize enumeration."""
        # Normalize underlying type
        underlying_type_id = normalizer.normalize_type(enum["underlying_type"])
        
        # Generate enum type ID
        enum_type_id = TypeIDGenerator.generate({
            "kind": "enum",
            "name": enum["name"]
        })
        
        return {
            "name": enum["name"],
            "type_id": enum_type_id,
            "underlying_type_id": underlying_type_id,
            "constants": enum["constants"],
            "source_location": enum.get("source_location", {})
        }

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 6.1 Constraint Types
# ───────────────────────────────────────────────────────────────────

class ConstraintType(Enum):
    """Types of constraints that can be synthesized."""
    NON_NULL = "non_null"
    NULLABLE = "nullable"
    CONDITIONALLY_NULL = "conditionally_null"
    BUFFER_SIZE = "buffer_size"
    NULL_TERMINATED = "null_terminated"
    OWNERSHIP_BORROWED = "ownership_borrowed"
    OWNERSHIP_TRANSFERRED_IN = "ownership_transferred_in"
    OWNERSHIP_TRANSFERRED_OUT = "ownership_transferred_out"
    ALIGNMENT = "alignment"
    CALLING_CONVENTION = "calling_convention"
    OUTPUT_PARAMETER = "output_parameter"

@dataclass
class Constraint:
    """
    A single constraint on an FFI interface element.
    
    Represents an assumption that must hold for correct behavior.
    """
    constraint_id: str
    constraint_type: ConstraintType
    target: str  # What this constrains (e.g., "param_data", "return_value")
    confidence: float  # 0.0 to 1.0
    rationale: str  # Human-readable explanation
    derivation_rule: str  # Which rule produced this
    evidence: List[str]  # Evidence supporting this constraint
    related_target: Optional[str] = None  # For relational constraints
    conditions: Optional[List[Dict[str, str]]] = None  # For conditional constraints
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "constraint_id": self.constraint_id,
            "type": self.constraint_type.value,
            "target": self.target,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "derivation_rule": self.derivation_rule,
            "evidence": self.evidence
        }
        
        if self.related_target:
            result["related_target"] = self.related_target
        
        if self.conditions:
            result["conditions"] = self.conditions
        
        # Add warning for low confidence
        if self.confidence < 0.6:
            result["warning"] = "Low confidence - recommend explicit annotation"
        
        return result

# ───────────────────────────────────────────────────────────────────
# 6.2 Naming Pattern Analyzer
# ───────────────────────────────────────────────────────────────────

class NamingPatternAnalyzer:
    """
    Analyzes naming patterns to infer semantic properties.
    
    Uses heuristics based on common C naming conventions.
    """
    
    # Patterns for nullability
    NULLABLE_PATTERNS = ["optional", "maybe", "nullable", "or_null"]
    
    # Patterns for ownership transfer (output)
    CREATE_PATTERNS = ["create", "alloc", "new", "open", "make", "build"]
    
    # Patterns for ownership transfer (input)
    DESTROY_PATTERNS = ["destroy", "free", "delete", "close", "release"]
    
    # Patterns for size/length parameters
    SIZE_PATTERNS = ["size", "length", "len", "count", "num", "n"]
    
    # Patterns for buffer parameters
    BUFFER_PATTERNS = ["buffer", "buf", "data", "array", "ptr"]
    
    @staticmethod
    def suggests_nullable(name: str) -> bool:
        """Check if name suggests pointer may be null."""
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in NamingPatternAnalyzer.NULLABLE_PATTERNS)
    
    @staticmethod
    def suggests_ownership_transfer_out(name: str) -> bool:
        """Check if name suggests function creates/allocates resource."""
        name_lower = name.lower()
        return any(name_lower.startswith(pattern) for pattern in NamingPatternAnalyzer.CREATE_PATTERNS)
    
    @staticmethod
    def suggests_ownership_transfer_in(name: str) -> bool:
        """Check if name suggests function destroys/frees resource."""
        name_lower = name.lower()
        return any(name_lower.startswith(pattern) for pattern in NamingPatternAnalyzer.DESTROY_PATTERNS)
    
    @staticmethod
    def suggests_size_parameter(name: str) -> bool:
        """Check if name suggests parameter is a size/length."""
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in NamingPatternAnalyzer.SIZE_PATTERNS)
    
    @staticmethod
    def suggests_buffer_parameter(name: str) -> bool:
        """Check if name suggests parameter is a buffer."""
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in NamingPatternAnalyzer.BUFFER_PATTERNS)

# ───────────────────────────────────────────────────────────────────
# 6.3 Constraint Synthesizer
# ───────────────────────────────────────────────────────────────────

class ConstraintSynthesizer:
    """
    Synthesizes constraints from IR using derivation rules.
    
    Applies heuristics and naming analysis to infer semantic properties.
    """
    
    def __init__(self, ir_artifact: Dict[str, Any], type_registry: Dict[str, Any]):
        self.ir = ir_artifact
        self.type_registry = type_registry
        self.constraint_counter = 0
    
    def synthesize_function_constraints(self, function: Dict[str, Any]) -> List[Constraint]:
        """
        Synthesize constraints for a single function.
        
        Args:
            function: Normalized function from IR
            
        Returns:
            List of constraints
        """
        constraints = []
        func_name = function["name"]
        
        # Synthesize parameter constraints
        for param in function.get("parameters", []):
            param_constraints = self._synthesize_parameter_constraints(
                func_name, param, function["parameters"]
            )
            constraints.extend(param_constraints)
        
        # Synthesize return value constraints
        return_constraints = self._synthesize_return_constraints(func_name, function)
        constraints.extend(return_constraints)
        
        # Synthesize calling convention constraint
        conv_constraint = self._synthesize_calling_convention_constraint(func_name, function)
        if conv_constraint:
            constraints.append(conv_constraint)
        
        return constraints
    
    def _synthesize_parameter_constraints(
        self,
        func_name: str,
        param: Dict[str, Any],
        all_params: List[Dict[str, Any]]
    ) -> List[Constraint]:
        """Synthesize constraints for a parameter."""
        constraints = []
        param_name = param["name"]
        param_type = self.type_registry.get(param["type_id"], {})
        
        # Check if pointer type
        if param_type.get("kind") == "pointer":
            # Nullability constraint
            null_constraint = self._infer_nullability(func_name, param_name, param, param_type)
            constraints.append(null_constraint)
            
            # Check for buffer-length relationship
            buffer_constraint = self._infer_buffer_size(func_name, param, all_params)
            if buffer_constraint:
                constraints.append(buffer_constraint)
            
            # Check for output parameter pattern
            if self._is_output_parameter(param_type):
                output_constraint = self._create_output_parameter_constraint(func_name, param_name)
                constraints.append(output_constraint)
        
        # Check for ownership transfer (destroy/free functions)
        if NamingPatternAnalyzer.suggests_ownership_transfer_in(func_name):
            if param_type.get("kind") == "pointer":
                ownership_constraint = self._create_ownership_transferred_in_constraint(
                    func_name, param_name
                )
                constraints.append(ownership_constraint)
        
        return constraints
    
    def _infer_nullability(
        self,
        func_name: str,
        param_name: str,
        param: Dict,
        param_type: Dict
    ) -> Constraint:
        """Infer nullability constraint for pointer parameter."""
        # Check naming patterns
        if NamingPatternAnalyzer.suggests_nullable(param_name):
            confidence = 0.8
            constraint_type = ConstraintType.NULLABLE
            rationale = f"Parameter name '{param_name}' suggests optional/nullable"
            evidence = [f"Name contains nullability hint: {param_name}"]
        else:
            # Default: assume non-null (conservative)
            confidence = 0.4
            constraint_type = ConstraintType.NON_NULL
            rationale = "Default assumption (no explicit nullability evidence)"
            evidence = ["No naming hints for nullability", "Conservative default: non-null"]
        
        self.constraint_counter += 1
        constraint_id = f"{func_name}_{constraint_type.value}_{param_name}_{self.constraint_counter}"
        
        return Constraint(
            constraint_id=constraint_id,
            constraint_type=constraint_type,
            target=f"param_{param_name}",
            confidence=confidence,
            rationale=rationale,
            derivation_rule="Rule 1: Pointer Nullability",
            evidence=evidence
        )
    
    def _infer_buffer_size(
        self,
        func_name: str,
        param: Dict,
        all_params: List[Dict]
    ) -> Optional[Constraint]:
        """Infer buffer-length relationship."""
        param_name = param["name"]
        param_pos = param["position"]
        
        # Look for adjacent size parameter
        for other_param in all_params:
            if other_param["name"] == param_name:
                continue
            
            other_type = self.type_registry.get(other_param["type_id"], {})
            
            # Check if other param is integer type (size)
            if other_type.get("kind") == "primitive":
                if "int" in other_type.get("name", "").lower():
                    # Check naming
                    if NamingPatternAnalyzer.suggests_size_parameter(other_param["name"]):
                        confidence = 0.85
                        evidence = [
                            f"Parameter '{param_name}' is pointer",
                            f"Parameter '{other_param['name']}' is integer with size-like name",
                            "Adjacent parameters suggest buffer-length relationship"
                        ]
                    elif abs(other_param["position"] - param_pos) == 1:
                        confidence = 0.6
                        evidence = [
                            f"Parameter '{param_name}' is pointer",
                            f"Parameter '{other_param['name']}' is integer",
                            "Adjacent parameters (weak inference)"
                        ]
                    else:
                        continue  # No strong evidence
                    
                    self.constraint_counter += 1
                    constraint_id = f"{func_name}_BUFFER_SIZE_{param_name}_{self.constraint_counter}"
                    
                    return Constraint(
                        constraint_id=constraint_id,
                        constraint_type=ConstraintType.BUFFER_SIZE,
                        target=f"param_{param_name}",
                        related_target=f"param_{other_param['name']}",
                        confidence=confidence,
                        rationale=f"Buffer '{param_name}' size specified by '{other_param['name']}'",
                        derivation_rule="Rule 2: Buffer-Length Relationship",
                        evidence=evidence
                    )
        
        # Check if const char* without size → likely null-terminated
        param_type = self.type_registry.get(param["type_id"], {})
        if param_type.get("kind") == "pointer":
            pointee_id = param_type.get("pointee_id")
            if pointee_id:
                pointee = self.type_registry.get(pointee_id, {})
                if pointee.get("name") == "char" and param_type.get("is_const"):
                    self.constraint_counter += 1
                    constraint_id = f"{func_name}_NULL_TERMINATED_{param_name}_{self.constraint_counter}"
                    
                    return Constraint(
                        constraint_id=constraint_id,
                        constraint_type=ConstraintType.NULL_TERMINATED,
                        target=f"param_{param_name}",
                        confidence=0.7,
                        rationale=f"const char* parameter without size likely null-terminated string",
                        derivation_rule="Rule 3: Null-Terminated String",
                        evidence=[
                            "Type is const char*",
                            "No adjacent size parameter found",
                            "Common pattern for string parameters"
                        ]
                    )
        
        return None
    
    def _is_output_parameter(self, param_type: Dict) -> bool:
        """Check if parameter is output parameter (pointer to pointer)."""
        if param_type.get("kind") != "pointer":
            return False
        
        pointee_id = param_type.get("pointee_id")
        if not pointee_id:
            return False
        
        pointee = self.type_registry.get(pointee_id, {})
        return pointee.get("kind") == "pointer" and not param_type.get("is_const")
    
    def _create_output_parameter_constraint(self, func_name: str, param_name: str) -> Constraint:
        """Create constraint for output parameter."""
        self.constraint_counter += 1
        constraint_id = f"{func_name}_OUTPUT_PARAMETER_{param_name}_{self.constraint_counter}"
        
        return Constraint(
            constraint_id=constraint_id,
            constraint_type=ConstraintType.OUTPUT_PARAMETER,
            target=f"param_{param_name}",
            confidence=0.9,
            rationale=f"Parameter '{param_name}' is pointer-to-pointer (output parameter pattern)",
            derivation_rule="Rule 6: Output Parameter",
            evidence=[
                "Type is pointer-to-pointer",
                "Non-const (writable)",
                "Common pattern for output parameters"
            ]
        )
    
    def _create_ownership_transferred_in_constraint(
        self,
        func_name: str,
        param_name: str
    ) -> Constraint:
        """Create ownership transfer in constraint."""
        self.constraint_counter += 1
        constraint_id = f"{func_name}_OWNERSHIP_IN_{param_name}_{self.constraint_counter}"
        
        return Constraint(
            constraint_id=constraint_id,
            constraint_type=ConstraintType.OWNERSHIP_TRANSFERRED_IN,
            target=f"param_{param_name}",
            confidence=0.85,
            rationale=f"Function '{func_name}' suggests resource destruction/deallocation",
            derivation_rule="Rule 5: Ownership Transfer (Input)",
            evidence=[
                f"Function name starts with destroy/free pattern: {func_name}",
                "Parameter is pointer",
                "Common pattern for resource cleanup"
            ]
        )
    
    def _synthesize_return_constraints(
        self,
        func_name: str,
        function: Dict
    ) -> List[Constraint]:
        """Synthesize constraints for return value."""
        constraints = []
        return_type = self.type_registry.get(function["return_type_id"], {})
        
        if return_type.get("kind") == "pointer":
            # Check for ownership transfer out
            if NamingPatternAnalyzer.suggests_ownership_transfer_out(func_name):
                self.constraint_counter += 1
                constraint_id = f"{func_name}_OWNERSHIP_OUT_return_{self.constraint_counter}"
                
                constraints.append(Constraint(
                    constraint_id=constraint_id,
                    constraint_type=ConstraintType.OWNERSHIP_TRANSFERRED_OUT,
                    target="return_value",
                    confidence=0.85,
                    rationale=f"Function '{func_name}' suggests resource creation/allocation",
                    derivation_rule="Rule 4: Ownership Transfer (Output)",
                    evidence=[
                        f"Function name starts with create/alloc pattern: {func_name}",
                        "Return type is pointer",
                        "Common pattern for resource creation"
                    ]
                ))
        
        return constraints
    
    def _synthesize_calling_convention_constraint(
        self,
        func_name: str,
        function: Dict
    ) -> Optional[Constraint]:
        """Synthesize calling convention constraint."""
        calling_conv = function.get("calling_convention", "cdecl")
        platform = self.ir.get("platform", {})
        
        # Determine expected convention
        if platform.get("pointer_size") == 8:  # x64
            expected = "win64" if platform.get("alignment_rules") == "msvc" else "sysv"
        else:  # x86
            expected = "cdecl"
        
        if calling_conv != expected:
            self.constraint_counter += 1
            constraint_id = f"{func_name}_CALLING_CONV_{self.constraint_counter}"
            
            return Constraint(
                constraint_id=constraint_id,
                constraint_type=ConstraintType.CALLING_CONVENTION,
                target=func_name,
                confidence=1.0,
                rationale=f"Function uses {calling_conv} convention (expected: {expected})",
                derivation_rule="Platform ABI Rules",
                evidence=[
                    f"Declared convention: {calling_conv}",
                    f"Platform default: {expected}",
                    "Explicit convention must be honored"
                ]
            )
        
        return None

# ───────────────────────────────────────────────────────────────────
# 6.4 Contract Synthesis Stage
# ───────────────────────────────────────────────────────────────────

class ContractSynthesisStage(PipelineStage):
    """
    Stage 3: Contract Synthesis
    
    Transforms structural IR into semantic correctness constraints.
    Infers nullability, buffer sizes, ownership, and other properties.
    """
    
    STAGE_NAME = "contract_synthesis"
    STAGE_VERSION = "1.0.0"
    STAGE_DESCRIPTION = "Synthesize semantic constraints from IR"
    
    REQUIRED_INPUTS = ["ir"]
    PRODUCED_OUTPUTS = ["contract"]
    
    def _execute_impl(self) -> None:
        """Synthesize contract from IR."""
        # Load IR artifact
        artifacts_dir = self.execution_context["artifacts"]["working_directory"]
        ir_path = os.path.join(artifacts_dir, "ir.json")
        
        with open(ir_path, 'r', encoding='utf-8') as f:
            ir_artifact = json.load(f)
        
        # Initialize synthesizer
        type_registry = ir_artifact["type_registry"]
        synthesizer = ConstraintSynthesizer(ir_artifact, type_registry)
        
        # Synthesize constraints for each function
        function_contracts = []
        for function in ir_artifact.get("functions", []):
            constraints = synthesizer.synthesize_function_constraints(function)
            
            function_contract = {
                "name": function["name"],
                "signature": self._build_signature(function, type_registry),
                "constraints": [c.to_dict() for c in constraints]
            }
            
            function_contracts.append(function_contract)
        
        # Build contract artifact
        provenance = self.create_provenance([ir_path])
        
        contract_artifact = {
            "provenance": provenance.to_dict(),
            "schema_version": "1.0.0",
            "functions": function_contracts,
            "global_constraints": [],
            "warnings": self._collect_warnings(function_contracts)
        }
        
        # Write contract artifact
        contract_path = os.path.join(artifacts_dir, "contract.json")
        with open(contract_path, 'w', encoding='utf-8') as f:
            json.dump(contract_artifact, f, indent=2)
    
    def _build_signature(self, function: Dict, type_registry: Dict) -> str:
        """Build human-readable function signature."""
        return_type = type_registry.get(function["return_type_id"], {})
        return_type_str = return_type.get("name", "unknown")
        
        params_str = ", ".join([
            f"{self._type_to_string(p['type_id'], type_registry)} {p['name']}"
            for p in function.get("parameters", [])
        ])
        
        return f"{return_type_str} {function['name']}({params_str})"
    
    def _type_to_string(self, type_id: str, type_registry: Dict) -> str:
        """Convert type ID to string representation."""
        type_info = type_registry.get(type_id, {})
        kind = type_info.get("kind")
        
        if kind == "primitive":
            return type_info.get("name", "unknown")
        elif kind == "pointer":
            pointee_id = type_info.get("pointee_id", "")
            pointee_str = self._type_to_string(pointee_id, type_registry)
            return f"{pointee_str}*"
        elif kind in ["struct", "union"]:
            return f"{kind} {type_info.get('name', 'anonymous')}"
        else:
            return type_id
    
    def _collect_warnings(self, function_contracts: List[Dict]) -> List[str]:
        """Collect warnings from low-confidence constraints."""
        warnings = []
        
        for func in function_contracts:
            for constraint in func["constraints"]:
                if constraint.get("confidence", 1.0) < 0.6:
                    warnings.append(
                        f"Low confidence constraint in {func['name']}: "
                        f"{constraint['constraint_id']} (confidence: {constraint['confidence']})"
                    )
        
        return warnings

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 7.1 Code Generator Utilities
# ───────────────────────────────────────────────────────────────────

class CodeGenerator:
    """
    Utility for generating Python code with proper indentation.
    """
    
    def __init__(self, indent_size: int = 4):
        self.lines: List[str] = []
        self.indent_level = 0
        self.indent_size = indent_size
    
    def add_line(self, line: str = ""):
        """Add a line with current indentation."""
        if line:
            indent = " " * (self.indent_level * self.indent_size)
            self.lines.append(f"{indent}{line}")
        else:
            self.lines.append("")
    
    def add_block(self, header: str, content_fn):
        """Add a block with header and indented content."""
        self.add_line(header)
        self.indent()
        content_fn()
        self.dedent()
    
    def indent(self):
        """Increase indentation level."""
        self.indent_level += 1
    
    def dedent(self):
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - 1)
    
    def get_code(self) -> str:
        """Get generated code as string."""
        return "\n".join(self.lines)

# ───────────────────────────────────────────────────────────────────
# 7.2 Type Mapper
# ───────────────────────────────────────────────────────────────────

class TypeMapper:
    """
    Maps IR types to ctypes types.
    """
    
    PRIMITIVE_MAP = {
        "void": "None",
        "char": "ctypes.c_char",
        "signed char": "ctypes.c_char",
        "unsigned char": "ctypes.c_ubyte",
        "short": "ctypes.c_short",
        "unsigned short": "ctypes.c_ushort",
        "int": "ctypes.c_int",
        "unsigned int": "ctypes.c_uint",
        "long": "ctypes.c_long",
        "unsigned long": "ctypes.c_ulong",
        "long long": "ctypes.c_longlong",
        "unsigned long long": "ctypes.c_ulonglong",
        "float": "ctypes.c_float",
        "double": "ctypes.c_double",
        "size_t": "ctypes.c_size_t",
    }
    
    @staticmethod
    def map_type(type_id: str, type_registry: Dict) -> str:
        """
        Map IR type to ctypes type string.
        
        Args:
            type_id: Type ID from IR
            type_registry: Type registry from IR
            
        Returns:
            Python code string for ctypes type
        """
        type_info = type_registry.get(type_id, {})
        kind = type_info.get("kind")
        
        if kind == "primitive":
            name = type_info.get("name", "int")
            return TypeMapper.PRIMITIVE_MAP.get(name, "ctypes.c_int")
        
        elif kind == "pointer":
            pointee_id = type_info.get("pointee_id")
            pointee = type_registry.get(pointee_id, {})
            
            if pointee.get("kind") == "primitive":
                pointee_name = pointee.get("name")
                if pointee_name == "char":
                    return "ctypes.c_char_p"  # String pointer
                elif pointee_name == "void":
                    return "ctypes.c_void_p"  # Generic pointer
            
            # Pointer to struct
            if pointee.get("kind") == "struct":
                struct_name = pointee.get("name", "Unknown")
                return f"ctypes.POINTER({struct_name})"
            
            # Generic pointer
            return "ctypes.c_void_p"
        
        elif kind == "struct":
            return type_info.get("name", "Unknown")
        
        elif kind == "array":
            element_id = type_info.get("element_type_id")
            element_type = TypeMapper.map_type(element_id, type_registry)
            size = type_info.get("size", 1)
            return f"{element_type} * {size}"
        
        else:
            return "ctypes.c_void_p"  # Fallback

# ───────────────────────────────────────────────────────────────────
# 7.3 Check Generator
# ───────────────────────────────────────────────────────────────────

class CheckGenerator:
    """
    Generates runtime check code from constraints.
    """
    
    @staticmethod
    def generate_check_function(
        constraint: Dict,
        function_name: str,
        type_registry: Dict
    ) -> str:
        """
        Generate check function for a constraint.
        
        Returns Python code as string.
        """
        gen = CodeGenerator()
        constraint_type = constraint["type"]
        target = constraint["target"]
        constraint_id = constraint["constraint_id"]
        
        # Function name
        check_func_name = f"_check_{constraint_type}_{target.replace('param_', '')}"
        
        if constraint_type == "non_null":
            CheckGenerator._generate_non_null_check(gen, constraint, function_name)
        
        elif constraint_type == "buffer_size":
            CheckGenerator._generate_buffer_size_check(gen, constraint, function_name)
        
        elif constraint_type == "null_terminated":
            CheckGenerator._generate_null_terminated_check(gen, constraint, function_name)
        
        else:
            # Generic check (placeholder)
            gen.add_line(f"def {check_func_name}(*args):")
            gen.indent()
            gen.add_line("# TODO: Implement check for " + constraint_type)
            gen.add_line("pass")
            gen.dedent()
        
        return gen.get_code()
    
    @staticmethod
    def _generate_non_null_check(gen: CodeGenerator, constraint: Dict, func_name: str):
        """Generate NON_NULL check."""
        target = constraint["target"].replace("param_", "")
        constraint_id = constraint["constraint_id"]
        
        gen.add_line(f"def _check_NON_NULL_{target}({target}):")
        gen.indent()
        gen.add_line('"""Enforce NON_NULL constraint."""')
        gen.add_line(f"if {target} is None:")
        gen.indent()
        gen.add_line("raise ContractViolation(")
        gen.indent()
        gen.add_line(f'constraint_id="{constraint_id}",')
        gen.add_line(f'message="Parameter \'{target}\' must not be null",')
        gen.add_line(f'function="{func_name}",')
        gen.add_line(f'parameter="{target}"')
        gen.dedent()
        gen.add_line(")")
        gen.dedent()
        gen.dedent()
    
    @staticmethod
    def _generate_buffer_size_check(gen: CodeGenerator, constraint: Dict, func_name: str):
        """Generate BUFFER_SIZE check."""
        target = constraint["target"].replace("param_", "")
        related = constraint.get("related_target", "").replace("param_", "")
        constraint_id = constraint["constraint_id"]
        
        gen.add_line(f"def _check_BUFFER_SIZE_{target}({target}, {related}):")
        gen.indent()
        gen.add_line('"""Enforce BUFFER_SIZE constraint."""')
        gen.add_line(f"if {target} is not None:")
        gen.indent()
        gen.add_line(f"if len({target}) < {related}:")
        gen.indent()
        gen.add_line("raise ContractViolation(")
        gen.indent()
        gen.add_line(f'constraint_id="{constraint_id}",')
        gen.add_line(f'message=f"Buffer \'{target}\' size {{len({target})}} < required {{{related}}}",')
        gen.add_line(f'function="{func_name}",')
        gen.add_line(f'parameter="{target}"')
        gen.dedent()
        gen.add_line(")")
        gen.dedent()
        gen.dedent()
        gen.dedent()
    
    @staticmethod
    def _generate_null_terminated_check(gen: CodeGenerator, constraint: Dict, func_name: str):
        """Generate NULL_TERMINATED check."""
        target = constraint["target"].replace("param_", "")
        constraint_id = constraint["constraint_id"]
        
        gen.add_line(f"def _check_NULL_TERMINATED_{target}({target}):")
        gen.indent()
        gen.add_line('"""Enforce NULL_TERMINATED constraint."""')
        gen.add_line(f"if {target} is not None:")
        gen.indent()
        gen.add_line(f"if b'\\x00' not in {target}:")
        gen.indent()
        gen.add_line("raise ContractViolation(")
        gen.indent()
        gen.add_line(f'constraint_id="{constraint_id}",')
        gen.add_line(f'message="String \'{target}\' must be null-terminated",')
        gen.add_line(f'function="{func_name}"')
        gen.dedent()
        gen.add_line(")")
        gen.dedent()
        gen.dedent()
        gen.dedent()

# ───────────────────────────────────────────────────────────────────
# 7.4 Adapter Generator
# ───────────────────────────────────────────────────────────────────

class AdapterGenerator:
    """
    Generates complete adapter module from contract.
    """
    
    def __init__(self, contract: Dict, ir: Dict):
        self.contract = contract
        self.ir = ir
        self.type_registry = ir["type_registry"]
    
    def generate_adapter_module(self) -> str:
        """Generate complete adapter module code."""
        gen = CodeGenerator()
        
        # Header
        gen.add_line('"""')
        gen.add_line("Auto-generated adapter module")
        gen.add_line("DO NOT EDIT - Generated by AdapterGenerationStage")
        gen.add_line('"""')
        gen.add_line()
        
        # Imports
        gen.add_line("import ctypes")
        gen.add_line("from typing import Optional")
        gen.add_line()
        
        # Exception classes (inline for now)
        gen.add_line("class ContractViolation(Exception):")
        gen.indent()
        gen.add_line('"""Contract constraint violated."""')
        gen.add_line("def __init__(self, constraint_id, message, **metadata):")
        gen.indent()
        gen.add_line("super().__init__(message)")
        gen.add_line("self.constraint_id = constraint_id")
        gen.add_line("self.metadata = metadata")
        gen.dedent()
        gen.dedent()
        gen.add_line()
        
        # Library loading
        gen.add_line("# Load native library")
        gen.add_line('_lib = ctypes.CDLL("library.dll")  # TODO: Use actual library path')
        gen.add_line()
        
        # Generate check functions
        for func_contract in self.contract.get("functions", []):
            for constraint in func_contract.get("constraints", []):
                check_code = CheckGenerator.generate_check_function(
                    constraint, func_contract["name"], self.type_registry
                )
                gen.add_line(check_code)
                gen.add_line()
        
        # Generate function wrappers
        for func_contract in self.contract.get("functions", []):
            wrapper_code = self._generate_function_wrapper(func_contract)
            gen.add_line(wrapper_code)
            gen.add_line()
        
        return gen.get_code()
    
    def _generate_function_wrapper(self, func_contract: Dict) -> str:
        """Generate wrapper function."""
        gen = CodeGenerator()
        func_name = func_contract["name"]
        
        # Find function in IR
        func_ir = None
        for f in self.ir.get("functions", []):
            if f["name"] == func_name:
                func_ir = f
                break
        
        if not func_ir:
            return f"# Function {func_name} not found in IR"
        
        # Build parameter list
        params = func_ir.get("parameters", [])
        param_list = ", ".join([f"{p['name']}" for p in params])
        
        # Function signature
        gen.add_line(f"def {func_name}({param_list}):")
        gen.indent()
        
        # Docstring
        gen.add_line('"""')
        gen.add_line(f"Wrapper for: {func_contract.get('signature', func_name)}")
        gen.add_line()
        gen.add_line("Enforced constraints:")
        for constraint in func_contract.get("constraints", []):
            gen.add_line(f"- {constraint['constraint_id']}: {constraint['type']}")
        gen.add_line('"""')
        
        # Pre-call checks
        gen.add_line("# Pre-call checks")
        for constraint in func_contract.get("constraints", []):
            target = constraint["target"].replace("param_", "")
            constraint_type = constraint["type"]
            
            if constraint_type in ["non_null", "null_terminated"]:
                gen.add_line(f"_check_{constraint_type.upper()}_{target}({target})")
            elif constraint_type == "buffer_size":
                related = constraint.get("related_target", "").replace("param_", "")
                gen.add_line(f"_check_BUFFER_SIZE_{target}({target}, {related})")
        
        gen.add_line()
        
        # Call native function
        gen.add_line("# Call native function")
        native_call_args = ", ".join([p["name"] for p in params])
        gen.add_line(f"result = _lib.{func_name}({native_call_args})")
        gen.add_line()
        
        # Post-call checks (none for now)
        gen.add_line("# Post-call checks")
        gen.add_line("# (none)")
        gen.add_line()
        
        # Return
        gen.add_line("return result")
        
        gen.dedent()
        return gen.get_code()

# ───────────────────────────────────────────────────────────────────
# 7.5 Adapter Generation Stage
# ───────────────────────────────────────────────────────────────────

class AdapterGenerationStage(PipelineStage):
    """
    Stage 4: Adapter Generation
    
    Generates runtime enforcement adapters from contracts.
    Produces Python ctypes wrappers with pre/post checks.
    """
    
    STAGE_NAME = "adapter_generation"
    STAGE_VERSION = "1.0.0"
    STAGE_DESCRIPTION = "Generate runtime enforcement adapters"
    
    REQUIRED_INPUTS = ["contract", "ir"]
    PRODUCED_OUTPUTS = ["adapter_metadata"]
    
    def _execute_impl(self) -> None:
        """Generate adapters from contract."""
        # Load contract and IR
        artifacts_dir = self.execution_context["artifacts"]["working_directory"]
        contract_path = os.path.join(artifacts_dir, "contract.json")
        ir_path = os.path.join(artifacts_dir, "ir.json")
        
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        with open(ir_path, 'r', encoding='utf-8') as f:
            ir_artifact = json.load(f)
        
        # Generate adapter code
        generator = AdapterGenerator(contract, ir_artifact)
        adapter_code = generator.generate_adapter_module()
        
        # Write adapter module
        adapter_dir = os.path.join(artifacts_dir, "adapters")
        os.makedirs(adapter_dir, exist_ok=True)
        
        adapter_path = os.path.join(adapter_dir, "library_adapter.py")
        with open(adapter_path, 'w', encoding='utf-8') as f:
            f.write(adapter_code)
        
        # Generate metadata artifact
        provenance = self.create_provenance([contract_path, ir_path])
        
        metadata = {
            "provenance": provenance.to_dict(),
            "adapter_module": "adapters.library_adapter",
            "adapter_file": adapter_path,
            "functions_wrapped": [f["name"] for f in contract.get("functions", [])],
            "total_constraints": sum(
                len(f.get("constraints", [])) for f in contract.get("functions", [])
            ),
            "generation_warnings": []
        }
        
        # Write metadata
        metadata_path = os.path.join(artifacts_dir, "adapter_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 8.1 Input Value Generator
# ───────────────────────────────────────────────────────────────────

class InputValueGenerator:
    """
    Generates deterministic input values for test cases.
    
    Provides valid, invalid, and boundary values for various types.
    """
    
    @staticmethod
    def generate_valid_int(seed: Optional[int] = None) -> List[int]:
        """Generate valid integer test values."""
        values = [0, 1, 10, 42, 100, 1000]
        
        if seed is not None:
            random.seed(seed)
            values.append(random.randint(1, 10000))
        
        return values
    
    @staticmethod
    def generate_boundary_int(type_size: int = 4, signed: bool = True) -> List[int]:
        """Generate boundary integer values."""
        if type_size == 4:
            if signed:
                return [0, 1, -1, 2**31 - 1, -2**31]
            else:
                return [0, 1, 2**32 - 1]
        elif type_size == 8:
            if signed:
                return [0, 1, -1, 2**63 - 1, -2**63]
            else:
                return [0, 1, 2**64 - 1]
        else:
            return [0, 1]
    
    @staticmethod
    def generate_invalid_int(type_size: int = 4) -> List[int]:
        """Generate out-of-range integer values."""
        if type_size == 4:
            return [2**32, -2**32, 2**40]
        elif type_size == 8:
            return [2**64, -2**64]
        else:
            return []
    
    @staticmethod
    def generate_valid_buffer(sizes: List[int] = None) -> List[bytes]:
        """Generate valid buffer test values."""
        if sizes is None:
            sizes = [0, 1, 10, 100, 1024]
        
        buffers = []
        for size in sizes:
            if size == 0:
                buffers.append(b"")
            else:
                buffers.append(b"A" * size)
        
        return buffers
    
    @staticmethod
    def generate_invalid_buffer() -> List[Optional[bytes]]:
        """Generate invalid buffer values."""
        return [None]  # Null pointer
    
    @staticmethod
    def generate_null_terminated_string(lengths: List[int] = None) -> List[bytes]:
        """Generate null-terminated strings."""
        if lengths is None:
            lengths = [0, 1, 10, 100]
        
        strings = []
        for length in lengths:
            if length == 0:
                strings.append(b"\x00")
            else:
                strings.append(b"A" * length + b"\x00")
        
        return strings
    
    @staticmethod
    def generate_non_null_terminated_string() -> List[bytes]:
        """Generate strings missing null terminator."""
        return [b"Hello", b"A" * 100, b""]

# ───────────────────────────────────────────────────────────────────
# 8.2 Test Case Generator
# ───────────────────────────────────────────────────────────────────

class TestCaseGenerator:
    """
    Generates test cases from contract constraints.
    
    Creates positive, negative, boundary, and combinatorial tests.
    """
    
    def __init__(self, contract: Dict, ir: Dict):
        self.contract = contract
        self.ir = ir
        self.test_counter = 0
        self.input_generator = InputValueGenerator()
    
    def generate_test_cases_for_function(self, func_contract: Dict) -> List[Dict]:
        """
        Generate all test cases for a function.
        
        Returns list of test case specifications.
        """
        test_cases = []
        func_name = func_contract["name"]
        
        # Find function in IR for parameter info
        func_ir = self._find_function_in_ir(func_name)
        if not func_ir:
            return test_cases
        
        # Generate positive test (all constraints satisfied)
        positive_test = self._generate_positive_test(func_contract, func_ir)
        test_cases.append(positive_test)
        
        # Generate negative tests (one constraint violated each)
        negative_tests = self._generate_negative_tests(func_contract, func_ir)
        test_cases.extend(negative_tests)
        
        # Generate boundary tests
        boundary_tests = self._generate_boundary_tests(func_contract, func_ir)
        test_cases.extend(boundary_tests)
        
        return test_cases
    
    def _find_function_in_ir(self, func_name: str) -> Optional[Dict]:
        """Find function definition in IR."""
        for func in self.ir.get("functions", []):
            if func["name"] == func_name:
                return func
        return None
    
    def _generate_positive_test(self, func_contract: Dict, func_ir: Dict) -> Dict:
        """Generate positive test case (happy path)."""
        self.test_counter += 1
        test_id = f"test_{func_contract['name']}_{self.test_counter:03d}_pos"
        
        # Generate valid inputs
        inputs = {}
        for param in func_ir.get("parameters", []):
            param_name = param["name"]
            param_type_id = param["type_id"]
            
            # Get parameter type from type registry
            param_type = self.ir["type_registry"].get(param_type_id, {})
            
            # Generate appropriate value
            inputs[param_name] = self._generate_valid_input_for_type(
                param_type, param_name, func_contract
            )
        
        return {
            "test_id": test_id,
            "function": func_contract["name"],
            "category": "positive",
            "priority": 1,
            "description": "Valid inputs - all constraints satisfied",
            "constraints_exercised": [c["constraint_id"] for c in func_contract.get("constraints", [])],
            "inputs": inputs,
            "expected_outcome": {
                "type": "success",
                "no_violations": True
            }
        }
    
    def _generate_valid_input_for_type(
        self,
        param_type: Dict,
        param_name: str,
        func_contract: Dict
    ) -> Dict:
        """Generate valid input value specification."""
        kind = param_type.get("kind")
        
        if kind == "primitive":
            type_name = param_type.get("name", "int")
            if "int" in type_name:
                return {
                    "type": "int",
                    "value": 42,
                    "generator": "fixed_valid_int"
                }
            elif "float" in type_name or "double" in type_name:
                return {
                    "type": "float",
                    "value": 3.14,
                    "generator": "fixed_valid_float"
                }
        
        elif kind == "pointer":
            # Check if this is a buffer with size parameter
            size_param = self._find_buffer_size_param(param_name, func_contract)
            
            if size_param:
                return {
                    "type": "bytes",
                    "value": "b'Hello, World!'",
                    "generator": "fixed_buffer",
                    "size_matches": size_param
                }
            else:
                # Generic pointer - use small buffer
                return {
                    "type": "bytes",
                    "value": "b'test'",
                    "generator": "fixed_buffer"
                }
        
        # Default
        return {
            "type": "unknown",
            "value": None,
            "generator": "none"
        }
    
    def _find_buffer_size_param(self, buffer_param: str, func_contract: Dict) -> Optional[str]:
        """Find size parameter for buffer parameter."""
        for constraint in func_contract.get("constraints", []):
            if constraint["type"] == "buffer_size":
                if constraint["target"] == f"param_{buffer_param}":
                    related = constraint.get("related_target", "")
                    return related.replace("param_", "")
        return None
    
    def _generate_negative_tests(self, func_contract: Dict, func_ir: Dict) -> List[Dict]:
        """Generate negative test cases (constraint violations)."""
        tests = []
        
        for constraint in func_contract.get("constraints", []):
            self.test_counter += 1
            test_id = f"test_{func_contract['name']}_{self.test_counter:03d}_neg"
            
            # Generate inputs that violate this constraint
            inputs = self._generate_inputs_violating_constraint(
                constraint, func_contract, func_ir
            )
            
            tests.append({
                "test_id": test_id,
                "function": func_contract["name"],
                "category": "negative",
                "priority": 2,
                "description": f"Violate constraint: {constraint['type']}",
                "constraints_exercised": [constraint["constraint_id"]],
                "inputs": inputs,
                "expected_outcome": {
                    "type": "contract_violation",
                    "expected_constraint_id": constraint["constraint_id"],
                    "violation_phase": "pre_call"
                }
            })
        
        return tests
    
    def _generate_inputs_violating_constraint(
        self,
        constraint: Dict,
        func_contract: Dict,
        func_ir: Dict
    ) -> Dict:
        """Generate inputs that violate specific constraint."""
        # Start with valid inputs
        inputs = {}
        for param in func_ir.get("parameters", []):
            param_type = self.ir["type_registry"].get(param["type_id"], {})
            inputs[param["name"]] = self._generate_valid_input_for_type(
                param_type, param["name"], func_contract
            )
        
        # Modify to violate target constraint
        constraint_type = constraint["type"]
        target = constraint["target"].replace("param_", "")
        
        if constraint_type == "non_null":
            # Pass null for this parameter
            inputs[target] = {
                "type": "none",
                "value": None,
                "generator": "null_violation"
            }
        
        elif constraint_type == "buffer_size":
            # Pass undersized buffer
            related = constraint.get("related_target", "").replace("param_", "")
            if related and related in inputs:
                # Set buffer smaller than size parameter
                inputs[target] = {
                    "type": "bytes",
                    "value": "b'AB'",  # Small buffer
                    "generator": "undersized_buffer"
                }
                inputs[related] = {
                    "type": "int",
                    "value": 100,  # Claim large size
                    "generator": "oversized_claim"
                }
        
        elif constraint_type == "null_terminated":
            # Pass non-terminated string
            inputs[target] = {
                "type": "bytes",
                "value": "b'Hello'",  # Missing \\x00
                "generator": "non_terminated_string"
            }
        
        return inputs
    
    def _generate_boundary_tests(self, func_contract: Dict, func_ir: Dict) -> List[Dict]:
        """Generate boundary test cases."""
        tests = []
        
        # For each integer parameter, test boundaries
        for param in func_ir.get("parameters", []):
            param_type = self.ir["type_registry"].get(param["type_id"], {})
            
            if param_type.get("kind") == "primitive":
                type_name = param_type.get("name", "")
                if "int" in type_name:
                    # Generate boundary test
                    self.test_counter += 1
                    test_id = f"test_{func_contract['name']}_{self.test_counter:03d}_bnd"
                    
                    inputs = {}
                    for p in func_ir.get("parameters", []):
                        if p["name"] == param["name"]:
                            # Use boundary value
                            inputs[p["name"]] = {
                                "type": "int",
                                "value": 0,  # Zero boundary
                                "generator": "boundary_zero"
                            }
                        else:
                            # Use valid value
                            p_type = self.ir["type_registry"].get(p["type_id"], {})
                            inputs[p["name"]] = self._generate_valid_input_for_type(
                                p_type, p["name"], func_contract
                            )
                    
                    tests.append({
                        "test_id": test_id,
                        "function": func_contract["name"],
                        "category": "boundary",
                        "priority": 3,
                        "description": f"Boundary test: {param['name']} = 0",
                        "constraints_exercised": [c["constraint_id"] for c in func_contract.get("constraints", [])],
                        "inputs": inputs,
                        "expected_outcome": {
                            "type": "success",
                            "no_violations": True
                        }
                    })
        
        return tests

# ───────────────────────────────────────────────────────────────────
# 8.3 Coverage Analyzer
# ───────────────────────────────────────────────────────────────────

class CoverageAnalyzer:
    """
    Analyzes test plan for constraint coverage.
    
    Ensures all constraints are exercised by at least one test.
    """
    
    @staticmethod
    def analyze_coverage(test_cases: List[Dict], contract: Dict) -> Dict:
        """
        Analyze constraint coverage.
        
        Returns coverage report.
        """
        # Collect all constraint IDs
        all_constraints = set()
        for func in contract.get("functions", []):
            for constraint in func.get("constraints", []):
                all_constraints.add(constraint["constraint_id"])
        
        # Collect exercised constraints
        exercised_constraints = set()
        constraint_test_map = {}
        
        for test in test_cases:
            for constraint_id in test.get("constraints_exercised", []):
                exercised_constraints.add(constraint_id)
                
                if constraint_id not in constraint_test_map:
                    constraint_test_map[constraint_id] = []
                constraint_test_map[constraint_id].append(test["test_id"])
        
        # Compute coverage
        uncovered = all_constraints - exercised_constraints
        coverage_pct = (len(exercised_constraints) / len(all_constraints) * 100) if all_constraints else 100.0
        
        return {
            "total_constraints": len(all_constraints),
            "constraints_covered": len(exercised_constraints),
            "coverage_percentage": coverage_pct,
            "uncovered_constraints": list(uncovered),
            "constraint_test_map": constraint_test_map
        }

# ───────────────────────────────────────────────────────────────────
# 8.4 Test Plan Generation Stage
# ───────────────────────────────────────────────────────────────────

class TestPlanGenerationStage(PipelineStage):
    """
    Stage 5: Test Plan Generation
    
    Generates systematic test cases from contracts to achieve
    100% constraint coverage with deterministic inputs.
    """
    
    STAGE_NAME = "test_plan_generation"
    STAGE_VERSION = "1.0.0"
    STAGE_DESCRIPTION = "Generate systematic test plan from contract"
    
    REQUIRED_INPUTS = ["contract", "ir"]
    PRODUCED_OUTPUTS = ["test_plan"]
    
    def _execute_impl(self) -> None:
        """Generate test plan from contract."""
        # Load contract and IR
        artifacts_dir = self.execution_context["artifacts"]["working_directory"]
        contract_path = os.path.join(artifacts_dir, "contract.json")
        ir_path = os.path.join(artifacts_dir, "ir.json")
        
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        with open(ir_path, 'r', encoding='utf-8') as f:
            ir_artifact = json.load(f)
        
        # Generate test cases
        generator = TestCaseGenerator(contract, ir_artifact)
        all_test_cases = []
        
        for func_contract in contract.get("functions", []):
            test_cases = generator.generate_test_cases_for_function(func_contract)
            all_test_cases.extend(test_cases)
        
        # Analyze coverage
        coverage = CoverageAnalyzer.analyze_coverage(all_test_cases, contract)
        
        # Build metadata
        tests_by_category = {}
        for test in all_test_cases:
            category = test["category"]
            tests_by_category[category] = tests_by_category.get(category, 0) + 1
        
        metadata = {
            "contract_version": contract["provenance"]["schema_version"],
            "total_tests": len(all_test_cases),
            "tests_by_category": tests_by_category,
            "estimated_execution_time_seconds": len(all_test_cases) * 2,  # Rough estimate
            "deterministic": True,
            "reproducible": True
        }
        
        # Build test plan artifact
        provenance = self.create_provenance([contract_path, ir_path])
        
        test_plan = {
            "provenance": provenance.to_dict(),
            "schema_version": "1.0.0",
            "test_plan_metadata": metadata,
            "coverage": coverage,
            "test_cases": all_test_cases
        }
        
        # Write test plan
        test_plan_path = os.path.join(artifacts_dir, "test_plan.json")
        with open(test_plan_path, 'w', encoding='utf-8') as f:
            json.dump(test_plan, f, indent=2)
        
        # Print summary
        print(f"Generated {len(all_test_cases)} test cases")
        print(f"Constraint coverage: {coverage['coverage_percentage']:.1f}%")
        if coverage['uncovered_constraints']:
            print(f"Warning: {len(coverage['uncovered_constraints'])} constraints not covered")

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 9.1 Input Instantiator
# ───────────────────────────────────────────────────────────────────

class InputInstantiator:
    """
    Converts abstract input specifications to concrete Python values.
    
    Handles type conversions, null values, and special cases.
    """
    
    @staticmethod
    def instantiate(input_spec: Dict[str, Any]) -> Any:
        """
        Convert input specification to actual value.
        
        Args:
            input_spec: Input specification from test plan
            
        Returns:
            Concrete Python value
        """
        input_type = input_spec.get("type")
        value = input_spec.get("value")
        
        if input_type == "none" or value is None:
            return None
        
        elif input_type == "int":
            return int(value)
        
        elif input_type == "float":
            return float(value)
        
        elif input_type == "bytes":
            # Value is string representation like "b'Hello'"
            if isinstance(value, str):
                try:
                    return eval(value)  # Convert "b'Hello'" to b'Hello'
                except:
                    return value.encode() if isinstance(value, str) else value
            return value
        
        elif input_type == "string":
            return str(value)
        
        else:
            # Unknown type - return as-is
            return value
    
    @staticmethod
    def instantiate_all(inputs: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Instantiate all inputs for a test case.
        
        Args:
            inputs: Dictionary of parameter_name -> input_spec
            
        Returns:
            Dictionary of parameter_name -> actual_value
        """
        instantiated = {}
        
        for param_name, input_spec in inputs.items():
            instantiated[param_name] = InputInstantiator.instantiate(input_spec)
        
        # Handle size matching (buffer size matches another parameter)
        for param_name, input_spec in inputs.items():
            size_matches = input_spec.get("size_matches")
            if size_matches and size_matches in instantiated:
                # Update size parameter to match buffer
                buffer_value = instantiated[param_name]
                if buffer_value is not None:
                    instantiated[size_matches] = len(buffer_value)
        
        return instantiated

# ───────────────────────────────────────────────────────────────────
# 9.2 Outcome Validator
# ───────────────────────────────────────────────────────────────────

class OutcomeValidator:
    """
    Validates actual outcomes against expected outcomes.
    
    Determines if test passes or fails.
    """
    
    @staticmethod
    def validate(
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> Tuple[str, Optional[str]]:
        """
        Compare expected and actual outcomes.
        
        Args:
            expected: Expected outcome from test plan
            actual: Actual outcome from execution
            
        Returns:
            Tuple of (validation_result, failure_reason)
            validation_result is "PASS" or "FAIL"
            failure_reason is None if PASS, string if FAIL
        """
        expected_type = expected.get("type")
        actual_type = actual.get("type")
        
        # Case 1: Expected success
        if expected_type == "success":
            if actual_type == "success" and actual.get("no_violations"):
                return ("PASS", None)
            else:
                reason = f"Expected success, got {actual_type}"
                if actual_type == "contract_violation":
                    reason += f" (constraint: {actual.get('constraint_id')})"
                elif actual_type == "unexpected_exception":
                    reason += f" ({actual.get('exception_type')}: {actual.get('message')})"
                return ("FAIL", reason)
        
        # Case 2: Expected contract violation
        elif expected_type == "contract_violation":
            expected_constraint = expected.get("expected_constraint_id")
            
            if actual_type == "contract_violation":
                actual_constraint = actual.get("constraint_id")
                if actual_constraint == expected_constraint:
                    return ("PASS", None)
                else:
                    reason = f"Expected violation of {expected_constraint}, got {actual_constraint}"
                    return ("FAIL", reason)
            elif actual_type == "success":
                reason = f"Expected violation of {expected_constraint}, but test passed (uncaught violation)"
                return ("FAIL", reason)
            else:
                reason = f"Expected violation, got {actual_type}"
                return ("FAIL", reason)
        
        # Case 3: Expected undefined behavior (rare)
        elif expected_type == "undefined_behavior":
            # Any outcome acceptable (crash, violation, success)
            return ("PASS", None)
        
        # Default: unexpected expected type
        else:
            return ("FAIL", f"Unknown expected outcome type: {expected_type}")

# ───────────────────────────────────────────────────────────────────
# 9.3 Test Executor
# ───────────────────────────────────────────────────────────────────

class TestExecutor:
    """
    Executes individual test cases using generated adapters.
    
    Handles input instantiation, adapter invocation, outcome capture,
    and validation.
    """
    
    def __init__(self, adapter_module_path: str):
        """
        Initialize executor with adapter module.
        
        Args:
            adapter_module_path: Path to generated adapter .py file
        """
        self.adapter_module_path = adapter_module_path
        self.adapter_module = None
        self._load_adapter()
    
    def _load_adapter(self):
        """Dynamically load adapter module."""
        try:
            spec = importlib.util.spec_from_file_location("adapter", self.adapter_module_path)
            if spec and spec.loader:
                self.adapter_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.adapter_module)
        except Exception as e:
            raise StageError(
                f"Failed to load adapter module: {e}",
                stage_name="verification_execution",
                details=f"Adapter path: {self.adapter_module_path}"
            )
    
    def execute_test(self, test_case: Dict) -> Dict:
        """
        Execute a single test case.
        
        Args:
            test_case: Test case specification from test plan
            
        Returns:
            Test result dictionary
        """
        test_id = test_case["test_id"]
        function_name = test_case["function"]
        
        # Instantiate inputs
        try:
            inputs = InputInstantiator.instantiate_all(test_case.get("inputs", {}))
        except Exception as e:
            return {
                "test_id": test_id,
                "validation_result": "ERROR",
                "error": "Input instantiation failed",
                "error_details": str(e)
            }
        
        # Get function from adapter
        if not hasattr(self.adapter_module, function_name):
            return {
                "test_id": test_id,
                "validation_result": "ERROR",
                "error": f"Function '{function_name}' not found in adapter"
            }
        
        adapter_function = getattr(self.adapter_module, function_name)
        
        # Execute with timing
        start_time = time.time()
        actual_outcome = self._invoke_adapter(adapter_function, inputs)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Validate outcome
        expected_outcome = test_case.get("expected_outcome", {})
        validation_result, failure_reason = OutcomeValidator.validate(
            expected_outcome, actual_outcome
        )
        
        # Build result
        result = {
            "test_id": test_id,
            "function": function_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_time_ms": execution_time_ms,
            "inputs": self._serialize_inputs(inputs),
            "expected_outcome": expected_outcome,
            "actual_outcome": actual_outcome,
            "validation_result": validation_result,
            "constraints_exercised": test_case.get("constraints_exercised", [])
        }
        
        if failure_reason:
            result["failure_reason"] = failure_reason
            result["diagnostic"] = self._generate_diagnostic(
                test_case, expected_outcome, actual_outcome
            )
        
        return result
    
    def _invoke_adapter(self, function, inputs: Dict) -> Dict:
        """
        Invoke adapter function and capture outcome.
        
        Returns outcome dictionary.
        """
        try:
            # Call function with inputs
            result = function(**inputs)
            
            # Success outcome
            return {
                "type": "success",
                "return_value": result,
                "no_violations": True
            }
        
        except Exception as e:
            # Check if this is a ContractViolation
            if type(e).__name__ == "ContractViolation":
                return {
                    "type": "contract_violation",
                    "constraint_id": getattr(e, "constraint_id", "unknown"),
                    "violation_phase": "pre_call",  # Assume pre-call for now
                    "message": str(e)
                }
            
            # Otherwise, unexpected exception
            return {
                "type": "unexpected_exception",
                "exception_type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _serialize_inputs(self, inputs: Dict) -> Dict:
        """Convert inputs to JSON-serializable format."""
        serialized = {}
        for key, value in inputs.items():
            if isinstance(value, bytes):
                serialized[key] = repr(value)  # b'Hello' as string
            else:
                serialized[key] = value
        return serialized
    
    def _generate_diagnostic(
        self,
        test_case: Dict,
        expected: Dict,
        actual: Dict
    ) -> str:
        """Generate diagnostic message for failed test."""
        category = test_case.get("category", "unknown")
        
        if category == "negative" and actual["type"] == "success":
            return (
                "Adapter failed to detect contract violation. "
                "Check that constraint enforcement is correctly generated."
            )
        
        elif category == "positive" and actual["type"] == "contract_violation":
            return (
                "Valid input rejected by adapter. "
                "Constraint may be too strict or check logic incorrect."
            )
        
        elif actual["type"] == "unexpected_exception":
            return (
                f"Unexpected exception: {actual.get('exception_type')}. "
                "This indicates a bug in adapter or native code."
            )
        
        else:
            return "Test outcome did not match expectations."

# ───────────────────────────────────────────────────────────────────
# 9.4 Execution Summarizer
# ───────────────────────────────────────────────────────────────────

class ExecutionSummarizer:
    """
    Generates summary statistics from test results.
    """
    
    @staticmethod
    def summarize(test_results: List[Dict]) -> Dict:
        """
        Generate summary statistics.
        
        Args:
            test_results: List of test result dictionaries
            
        Returns:
            Summary dictionary
        """
        total = len(test_results)
        passed = sum(1 for r in test_results if r["validation_result"] == "PASS")
        failed = sum(1 for r in test_results if r["validation_result"] == "FAIL")
        errors = sum(1 for r in test_results if r["validation_result"] == "ERROR")
        
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        
        # Total execution time
        total_time = sum(r.get("execution_time_ms", 0) for r in test_results) / 1000.0
        
        # Group by category
        by_category = {}
        for result in test_results:
            # Find original test case category (need to look up from test plan)
            # For now, extract from test_id suffix
            test_id = result["test_id"]
            if "_pos" in test_id:
                category = "positive"
            elif "_neg" in test_id:
                category = "negative"
            elif "_bnd" in test_id:
                category = "boundary"
            else:
                category = "unknown"
            
            if category not in by_category:
                by_category[category] = {"total": 0, "passed": 0, "failed": 0}
            
            by_category[category]["total"] += 1
            if result["validation_result"] == "PASS":
                by_category[category]["passed"] += 1
            elif result["validation_result"] == "FAIL":
                by_category[category]["failed"] += 1
        
        # Collect exercised constraints
        all_constraints = set()
        for result in test_results:
            all_constraints.update(result.get("constraints_exercised", []))
        
        return {
            "total_tests": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "tests_errored": errors,
            "pass_rate": pass_rate,
            "execution_time_total_seconds": total_time,
            "tests_by_category": by_category,
            "constraints_exercised": len(all_constraints)
        }

# ───────────────────────────────────────────────────────────────────
# 9.5 Verification Execution Stage
# ───────────────────────────────────────────────────────────────────

class VerificationExecutionStage(PipelineStage):
    """
    Stage 6: Verification Execution
    
    Executes test plan using generated adapters, validates outcomes,
    and produces comprehensive execution log.
    """
    
    STAGE_NAME = "verification_execution"
    STAGE_VERSION = "1.0.0"
    STAGE_DESCRIPTION = "Execute test plan with adapters"
    
    REQUIRED_INPUTS = ["test_plan", "adapter_metadata"]
    PRODUCED_OUTPUTS = ["execution_log"]
    
    def _execute_impl(self) -> None:
        """Execute verification test plan."""
        # Load test plan and adapter metadata
        artifacts_dir = self.execution_context["artifacts"]["working_directory"]
        test_plan_path = os.path.join(artifacts_dir, "test_plan.json")
        adapter_metadata_path = os.path.join(artifacts_dir, "adapter_metadata.json")
        
        with open(test_plan_path, 'r', encoding='utf-8') as f:
            test_plan = json.load(f)
        
        with open(adapter_metadata_path, 'r', encoding='utf-8') as f:
            adapter_metadata = json.load(f)
        
        # Get adapter module path
        adapter_file = adapter_metadata.get("adapter_file")
        if not adapter_file or not os.path.exists(adapter_file):
            raise StageError(
                "Adapter file not found",
                stage_name=self.STAGE_NAME,
                details=f"Expected: {adapter_file}"
            )
        
        # Initialize executor
        executor = TestExecutor(adapter_file)
        
        # Execute all test cases
        test_cases = test_plan.get("test_cases", [])
        test_results = []
        
        print(f"Executing {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                result = executor.execute_test(test_case)
                test_results.append(result)
                
                # Print progress
                status = "✓" if result["validation_result"] == "PASS" else "✗"
                print(f"  [{i}/{len(test_cases)}] {status} {test_case['test_id']}")
                
            except Exception as e:
                # Catch unexpected errors
                print(f"  [{i}/{len(test_cases)}] ✗ {test_case['test_id']} (ERROR)")
                test_results.append({
                    "test_id": test_case["test_id"],
                    "validation_result": "ERROR",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        # Generate summary
        summary = ExecutionSummarizer.summarize(test_results)
        
        # Collect failures for detailed reporting
        failures = [r for r in test_results if r["validation_result"] == "FAIL"]
        
        # Build execution log
        provenance = self.create_provenance([test_plan_path, adapter_metadata_path])
        
        execution_log = {
            "provenance": provenance.to_dict(),
            "schema_version": "1.0.0",
            "execution_metadata": {
                "start_time": test_results[0]["timestamp"] if test_results else None,
                "end_time": test_results[-1]["timestamp"] if test_results else None,
                "total_duration_seconds": summary["execution_time_total_seconds"],
                "execution_mode": "full",
                "adapter_module": adapter_metadata.get("adapter_module")
            },
            "summary": summary,
            "test_results": test_results,
            "failures": failures
        }
        
        # Write execution log
        execution_log_path = os.path.join(artifacts_dir, "execution_log.json")
        with open(execution_log_path, 'w', encoding='utf-8') as f:
            json.dump(execution_log, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 60)
        print("VERIFICATION EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['tests_passed']} ({summary['pass_rate']:.1f}%)")
        print(f"Failed: {summary['tests_failed']}")
        print(f"Errors: {summary['tests_errored']}")
        print(f"Execution time: {summary['execution_time_total_seconds']:.2f}s")
        print("=" * 60)
        
        if failures:
            print(f"\n{len(failures)} test(s) failed:")
            for failure in failures[:10]:  # Show first 10
                print(f"  - {failure['test_id']}: {failure.get('failure_reason', 'Unknown')}")

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 10.1 Failure Categories and Severity
# ───────────────────────────────────────────────────────────────────

class FailureCategory(Enum):
    """Categories of verification failures."""
    UNCAUGHT_VIOLATION = "uncaught_violation"
    FALSE_POSITIVE = "false_positive"
    NATIVE_BUG = "native_bug"
    CONTRACT_INCOMPLETE = "contract_incomplete"
    ABI_MISMATCH = "abi_mismatch"
    TEST_INFRASTRUCTURE = "test_infrastructure"
    UNKNOWN = "unknown"

class Severity(Enum):
    """Failure severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

# ───────────────────────────────────────────────────────────────────
# 10.2 Failure Classifier
# ───────────────────────────────────────────────────────────────────

class FailureClassifier:
    """
    Classifies test failures into categories and assigns severity.
    """
    
    @staticmethod
    def classify(test_result: Dict, test_case: Dict) -> Dict:
        """
        Classify a failed test.
        
        Args:
            test_result: Test execution result
            test_case: Original test case specification
            
        Returns:
            Classification dict with category, severity, root_cause
        """
        expected = test_result.get("expected_outcome", {})
        actual = test_result.get("actual_outcome", {})
        category_name = test_case.get("category", "unknown")
        
        # Case 1: Expected violation, got success
        if (expected.get("type") == "contract_violation" and 
            actual.get("type") == "success"):
            return {
                "failure_category": FailureCategory.UNCAUGHT_VIOLATION,
                "severity": Severity.CRITICAL,
                "root_cause": "Adapter failed to detect contract violation",
                "hypothesis": "Check function missing or incorrect in generated adapter"
            }
        
        # Case 2: Expected success, got violation (in positive test)
        if (expected.get("type") == "success" and 
            actual.get("type") == "contract_violation" and
            category_name == "positive"):
            return {
                "failure_category": FailureCategory.FALSE_POSITIVE,
                "severity": Severity.HIGH,
                "root_cause": "Valid input rejected by adapter",
                "hypothesis": "Constraint too strict or check logic incorrect"
            }
        
        # Case 3: Expected success, got crash
        if (expected.get("type") == "success" and 
            actual.get("type") in ["crash", "unexpected_exception"]):
            return {
                "failure_category": FailureCategory.NATIVE_BUG,
                "severity": Severity.CRITICAL,
                "root_cause": "Native code crashed or raised exception",
                "hypothesis": "Bug in native implementation"
            }
        
        # Case 4: Test infrastructure error
        if test_result.get("validation_result") == "ERROR":
            return {
                "failure_category": FailureCategory.TEST_INFRASTRUCTURE,
                "severity": Severity.LOW,
                "root_cause": "Test execution infrastructure issue",
                "hypothesis": test_result.get("error", "Unknown error")
            }
        
        # Default: Unknown
        return {
            "failure_category": FailureCategory.UNKNOWN,
            "severity": Severity.MEDIUM,
            "root_cause": "Failure classification inconclusive",
            "hypothesis": test_result.get("failure_reason", "Unknown")
        }

# ───────────────────────────────────────────────────────────────────
# 10.3 Remediation Generator
# ───────────────────────────────────────────────────────────────────

class RemediationGenerator:
    """
    Generates actionable remediation recommendations for failures.
    """
    
    @staticmethod
    def generate(classification: Dict, test_result: Dict, test_case: Dict) -> List[str]:
        """
        Generate remediation steps.
        
        Args:
            classification: Failure classification
            test_result: Test execution result
            test_case: Original test case
            
        Returns:
            List of recommended actions
        """
        category = classification["failure_category"]
        
        if category == FailureCategory.UNCAUGHT_VIOLATION:
            constraint_id = test_result["expected_outcome"].get("expected_constraint_id", "unknown")
            return [
                f"Inspect generated adapter for constraint: {constraint_id}",
                "Verify check function exists and is called before native invocation",
                "Check if constraint synthesis correctly identified requirement",
                "If constraint missing from contract, add explicit annotation"
            ]
        
        elif category == FailureCategory.FALSE_POSITIVE:
            constraint_id = test_result["actual_outcome"].get("constraint_id", "unknown")
            return [
                f"Review constraint rationale in contract.json: {constraint_id}",
                "Verify test input is actually valid",
                "Check if constraint is too strict or check logic incorrect",
                "Consider adjusting contract synthesis rules or adding annotation"
            ]
        
        elif category == FailureCategory.NATIVE_BUG:
            function = test_case.get("function", "unknown")
            inputs = test_result.get("inputs", {})
            return [
                f"Debug native function '{function}' with test inputs: {inputs}",
                "Use debugger (gdb/lldb/WinDbg) to locate crash site",
                "Check for: off-by-one errors, null dereference, buffer overflow",
                "Verify native code matches contract assumptions"
            ]
        
        elif category == FailureCategory.CONTRACT_INCOMPLETE:
            return [
                "Analyze crash dump to identify violated assumption",
                "Add missing constraint to contract (manual annotation)",
                "Re-run contract synthesis with updated heuristics",
                "Consider: alignment, pointer validity, state preconditions"
            ]
        
        elif category == FailureCategory.TEST_INFRASTRUCTURE:
            return [
                "Check test plan generation for errors",
                "Verify adapter module can be imported",
                "Review input instantiation logic",
                "Check for pipeline bugs"
            ]
        
        else:
            return [
                "Review test failure details",
                "Compare expected vs actual outcome",
                "Investigate manually"
            ]

# ───────────────────────────────────────────────────────────────────
# 10.4 Report Generator (HTML)
# ───────────────────────────────────────────────────────────────────

class HTMLReportGenerator:
    """
    Generates rich HTML report from execution results.
    """
    
    @staticmethod
    def generate(execution_log: Dict, diagnostics: Dict) -> str:
        """Generate HTML report."""
        summary = execution_log.get("summary", {})
        failures = diagnostics.get("failure_analysis", [])
        
        html = []
        
        # Header
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<title>Verification Report</title>")
        html.append("<style>")
        html.append(HTMLReportGenerator._get_css())
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        
        # Title
        html.append("<h1>FFI Verification Report</h1>")
        
        # Executive Summary
        status = "PASS" if summary.get("tests_failed", 0) == 0 else "FAIL"
        status_class = "pass" if status == "PASS" else "fail"
        
        html.append(f"<div class='summary {status_class}'>")
        html.append(f"<h2>Status: {status}</h2>")
        html.append(f"<p>Pass Rate: {summary.get('pass_rate', 0):.1f}%</p>")
        html.append(f"<p>Tests Passed: {summary.get('tests_passed', 0)}/{summary.get('total_tests', 0)}</p>")
        
        critical_count = diagnostics.get("severity_counts", {}).get("CRITICAL", 0)
        if critical_count > 0:
            html.append(f"<p class='critical'>⚠ {critical_count} CRITICAL issues</p>")
        
        html.append("</div>")
        
        # Test Results Overview
        html.append("<h2>Test Results Overview</h2>")
        html.append("<table>")
        html.append("<tr><th>Category</th><th>Total</th><th>Passed</th><th>Failed</th></tr>")
        
        for category, stats in summary.get("tests_by_category", {}).items():
            html.append(f"<tr>")
            html.append(f"<td>{category}</td>")
            html.append(f"<td>{stats['total']}</td>")
            html.append(f"<td>{stats['passed']}</td>")
            html.append(f"<td>{stats['failed']}</td>")
            html.append(f"</tr>")
        
        html.append("</table>")
        
        # Failure Analysis
        if failures:
            html.append("<h2>Failure Analysis</h2>")
            
            for failure in failures:
                test_id = failure.get("test_id", "unknown")
                category = failure.get("failure_category", "unknown")
                severity = failure.get("severity", "MEDIUM")
                root_cause = failure.get("root_cause", "Unknown")
                
                html.append(f"<div class='failure'>")
                html.append(f"<h3>{test_id} <span class='severity {severity.lower()}'>{severity}</span></h3>")
                html.append(f"<p><strong>Category:</strong> {category}</p>")
                html.append(f"<p><strong>Root Cause:</strong> {root_cause}</p>")
                
                # Remediation
                remediation = failure.get("remediation", [])
                if remediation:
                    html.append("<p><strong>Recommended Actions:</strong></p>")
                    html.append("<ol>")
                    for step in remediation:
                        html.append(f"<li>{step}</li>")
                    html.append("</ol>")
                
                html.append("</div>")
        
        # Footer
        html.append("<hr>")
        html.append(f"<p class='footer'>Generated: {datetime.now(timezone.utc).isoformat()}</p>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    @staticmethod
    def _get_css() -> str:
        """Get embedded CSS for report."""
        return """
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .summary {
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .summary.pass {
            background-color: #d4edda;
            border: 2px solid #28a745;
        }
        .summary.fail {
            background-color: #f8d7da;
            border: 2px solid #dc3545;
        }
        .critical {
            color: #dc3545;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }
        th {
            background-color: #007bff;
            color: white;
        }
        .failure {
            background-color: white;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #dc3545;
            border-radius: 3px;
        }
        .severity {
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .severity.critical {
            background-color: #dc3545;
            color: white;
        }
        .severity.high {
            background-color: #fd7e14;
            color: white;
        }
        .severity.medium {
            background-color: #ffc107;
            color: black;
        }
        .severity.low {
            background-color: #6c757d;
            color: white;
        }
        .footer {
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
        """

# ───────────────────────────────────────────────────────────────────
# 10.5 Report Generator (Markdown)
# ───────────────────────────────────────────────────────────────────

class MarkdownReportGenerator:
    """
    Generates Markdown report for version control.
    """
    
    @staticmethod
    def generate(execution_log: Dict, diagnostics: Dict) -> str:
        """Generate Markdown report."""
        summary = execution_log.get("summary", {})
        failures = diagnostics.get("failure_analysis", [])
        
        md = []
        
        # Title
        md.append("# FFI Verification Report")
        md.append("")
        
        # Executive Summary
        status = "✅ PASS" if summary.get("tests_failed", 0) == 0 else "❌ FAIL"
        md.append(f"## Status: {status}")
        md.append("")
        md.append(f"- **Pass Rate:** {summary.get('pass_rate', 0):.1f}%")
        md.append(f"- **Tests Passed:** {summary.get('tests_passed', 0)}/{summary.get('total_tests', 0)}")
        md.append(f"- **Execution Time:** {summary.get('execution_time_total_seconds', 0):.2f}s")
        
        critical_count = diagnostics.get("severity_counts", {}).get("CRITICAL", 0)
        if critical_count > 0:
            md.append(f"- **⚠️ CRITICAL Issues:** {critical_count}")
        
        md.append("")
        
        # Test Results
        md.append("## Test Results Overview")
        md.append("")
        md.append("| Category | Total | Passed | Failed |")
        md.append("|----------|-------|--------|--------|")
        
        for category, stats in summary.get("tests_by_category", {}).items():
            md.append(f"| {category} | {stats['total']} | {stats['passed']} | {stats['failed']} |")
        
        md.append("")
        
        # Failures
        if failures:
            md.append("## Failure Analysis")
            md.append("")
            
            for failure in failures:
                test_id = failure.get("test_id", "unknown")
                severity = failure.get("severity", "MEDIUM")
                root_cause = failure.get("root_cause", "Unknown")
                
                md.append(f"### {test_id} `[{severity}]`")
                md.append("")
                md.append(f"**Root Cause:** {root_cause}")
                md.append("")
                
                remediation = failure.get("remediation", [])
                if remediation:
                    md.append("**Recommended Actions:**")
                    for i, step in enumerate(remediation, 1):
                        md.append(f"{i}. {step}")
                    md.append("")
        
        # Footer
        md.append("---")
        md.append(f"*Generated: {datetime.now(timezone.utc).isoformat()}*")
        
        return "\n".join(md)

# ───────────────────────────────────────────────────────────────────
# 10.6 Diagnostics & Reporting Stage
# ───────────────────────────────────────────────────────────────────

class DiagnosticsReportingStage(PipelineStage):
    """
    Stage 7: Diagnostics & Reporting
    
    Analyzes execution results, classifies failures, generates root cause
    analysis, and produces human-readable reports.
    """
    
    STAGE_NAME = "diagnostics_reporting"
    STAGE_VERSION = "1.0.0"
    STAGE_DESCRIPTION = "Analyze failures and generate reports"
    
    REQUIRED_INPUTS = ["execution_log", "test_plan", "contract"]
    PRODUCED_OUTPUTS = ["diagnostics", "report_html", "report_md"]
    
    def _execute_impl(self) -> None:
        """Generate diagnostics and reports."""
        # Load artifacts
        artifacts_dir = self.execution_context["artifacts"]["working_directory"]
        execution_log_path = os.path.join(artifacts_dir, "execution_log.json")
        test_plan_path = os.path.join(artifacts_dir, "test_plan.json")
        contract_path = os.path.join(artifacts_dir, "contract.json")
        
        with open(execution_log_path, 'r', encoding='utf-8') as f:
            execution_log = json.load(f)
        
        with open(test_plan_path, 'r', encoding='utf-8') as f:
            test_plan = json.load(f)
        
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        # Analyze failures
        test_results = execution_log.get("test_results", [])
        test_cases_map = {tc["test_id"]: tc for tc in test_plan.get("test_cases", [])}
        
        failure_analysis = []
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for result in test_results:
            if result.get("validation_result") != "PASS":
                test_id = result["test_id"]
                test_case = test_cases_map.get(test_id, {})
                
                # Classify failure
                classification = FailureClassifier.classify(result, test_case)
                
                # Generate remediation
                remediation = RemediationGenerator.generate(classification, result, test_case)
                
                # Count severity
                severity = classification["severity"].value
                severity_counts[severity] += 1
                
                failure_analysis.append({
                    "test_id": test_id,
                    "failure_category": classification["failure_category"].value,
                    "severity": severity,
                    "root_cause": classification["root_cause"],
                    "hypothesis": classification["hypothesis"],
                    "remediation": remediation,
                    "expected_outcome": result.get("expected_outcome"),
                    "actual_outcome": result.get("actual_outcome")
                })
        
        # Build diagnostics artifact
        provenance = self.create_provenance([execution_log_path, test_plan_path, contract_path])
        
        diagnostics = {
            "provenance": provenance.to_dict(),
            "schema_version": "1.0.0",
            "failure_analysis": failure_analysis,
            "severity_counts": severity_counts,
            "total_failures": len(failure_analysis)
        }
        
        # Write diagnostics
        diagnostics_path = os.path.join(artifacts_dir, "diagnostics.json")
        with open(diagnostics_path, 'w', encoding='utf-8') as f:
            json.dump(diagnostics, f, indent=2)
        
        # Generate HTML report
        html_report = HTMLReportGenerator.generate(execution_log, diagnostics)
        html_path = os.path.join(artifacts_dir, "report.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Generate Markdown report
        md_report = MarkdownReportGenerator.generate(execution_log, diagnostics)
        md_path = os.path.join(artifacts_dir, "report.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)
        
        # Print summary
        print("\n" + "=" * 60)
        print("DIAGNOSTICS & REPORTING COMPLETE")
        print("=" * 60)
        print(f"Total failures analyzed: {len(failure_analysis)}")
        print(f"Severity breakdown:")
        for sev, count in severity_counts.items():
            if count > 0:
                print(f"  {sev}: {count}")
        print(f"\nReports generated:")
        print(f"  - HTML: {html_path}")
        print(f"  - Markdown: {md_path}")
        print(f"  - Diagnostics: {diagnostics_path}")
        print("=" * 60)

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 11.1 Verification Result
# ───────────────────────────────────────────────────────────────────

@dataclass
class VerificationResult:
    """
    Result of complete verification pipeline execution.
    
    Contains summary statistics, paths to artifacts, and any errors.
    """
    success: bool
    pass_rate: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    critical_issues: List[str]
    execution_time: float
    report_path: str
    artifacts_dir: str
    stages_completed: List[str]
    error: Optional[Exception] = None
    
    def __str__(self) -> str:
        """Human-readable summary."""
        status = "✓ PASSED" if self.success else "✗ FAILED"
        return f"""
Verification Result: {status}
  Pass Rate: {self.pass_rate:.1f}% ({self.passed_tests}/{self.total_tests})
  Critical Issues: {len(self.critical_issues)}
  Execution Time: {self.execution_time:.1f}s
  Report: {self.report_path}
  Artifacts: {self.artifacts_dir}
"""

# ───────────────────────────────────────────────────────────────────
# 11.2 Complete Pipeline
# ───────────────────────────────────────────────────────────────────

class CompletePipeline:
    """
    Complete integrated verification pipeline.
    
    Orchestrates all 7 stages from header/library to final report.
    """
    
    def __init__(self, header_path: str, library_path: str, output_dir: str = "artifacts"):
        """
        Initialize complete pipeline.
        
        Args:
            header_path: Path to C header file
            library_path: Path to native library
            output_dir: Output directory for artifacts
        """
        self.header_path = os.path.abspath(header_path)
        self.library_path = os.path.abspath(library_path)
        self.output_dir = os.path.abspath(output_dir)
        
        # Validate inputs
        if not os.path.exists(self.header_path):
            raise ValueError(f"Header file not found: {self.header_path}")
        
        if not os.path.exists(self.library_path):
            raise ValueError(f"Library file not found: {self.library_path}")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.execution_context = None
        self.pipeline = None
        self.start_time = None
    
    def execute(self, verbose: bool = True) -> VerificationResult:
        """
        Execute complete verification pipeline.
        
        Args:
            verbose: Show progress messages
            
        Returns:
            VerificationResult with summary and paths
        """
        self.start_time = time.time()
        
        if verbose:
            self._print_header()
        
        try:
            # : Create execution context
            if verbose:
                print("[1/8] Creating execution context...")
            self._create_execution_context()
            
            # : Initialize pipeline
            if verbose:
                print("[2/8] Initializing pipeline...")
            self._initialize_pipeline()
            
            # : Register stages
            if verbose:
                print("[3/8] Registering stages...")
            self._register_stages()
            
            # : Execute pipeline
            if verbose:
                print("[4/8] Executing verification stages...")
            success = self._execute_pipeline(verbose)
            
            # : Build result
            result = self._build_result(success)
            
            if verbose:
                self._print_summary(result)
            
            return result
        
        except Exception as e:
            # Pipeline failed - build error result
            elapsed = time.time() - self.start_time
            
            if verbose:
                print(f"\n✗ Pipeline failed: {e}\n")
                import traceback
                traceback.print_exc()
            
            return VerificationResult(
                success=False,
                pass_rate=0.0,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                critical_issues=[str(e)],
                execution_time=elapsed,
                report_path="",
                artifacts_dir=self.output_dir,
                stages_completed=[],
                error=e
            )
    
    def _create_execution_context(self):
        """Create execution context artifact."""
        # Build minimal execution context
        context_data = {
            "provenance": {
                "execution_id": str(uuid.uuid4()),
                "stage_name": "execution_context_creation",
                "stage_version": "1.0.0",
                "creation_timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "input_artifact_hashes": {}
            },
            "platform": {
                "os_name": "Windows" if os.name == "nt" else "Linux",
                "architecture": "x64",
                "pointer_width": 64,
                "endianness": "little"
            },
            "compiler": {
                "name": "msvc" if os.name == "nt" else "gcc",
                "version": "unknown",
                "include_paths": [],
                "preprocessor_macros": {}
            },
            "native_library": {
                "interface_header_path": self.header_path,
                "library_path": self.library_path
            },
            "artifacts": {
                "working_directory": self.output_dir,
                "execution_context_path": os.path.join(self.output_dir, "execution_context.json")
            }
        }
        
        # Write execution context
        context_path = os.path.join(self.output_dir, "execution_context.json")
        with open(context_path, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2)
        
        self.execution_context = context_data
    
    def _initialize_pipeline(self):
        """Initialize pipeline orchestrator."""
        context_path = os.path.join(self.output_dir, "execution_context.json")
        self.pipeline = EnhancedVerificationPipeline(context_path)
    
    def _register_stages(self):
        """Register all pipeline stages."""
        # Register all 7 stages in order
        self.pipeline.register_stage(NativeInterfaceIngestionStage)
        self.pipeline.register_stage(IRNormalizationStage)
        self.pipeline.register_stage(ContractSynthesisStage)
        self.pipeline.register_stage(AdapterGenerationStage)
        self.pipeline.register_stage(TestPlanGenerationStage)
        self.pipeline.register_stage(VerificationExecutionStage)
        self.pipeline.register_stage(DiagnosticsReportingStage)
    
    def _execute_pipeline(self, verbose: bool) -> bool:
        """Execute all stages."""
        # Use dependency-resolved execution
        return self.pipeline.execute_full_pipeline_with_dependency_resolution()
    
    def _build_result(self, success: bool) -> VerificationResult:
        """Build VerificationResult from pipeline execution."""
        elapsed = time.time() - self.start_time
        
        # Load execution log if available
        execution_log_path = os.path.join(self.output_dir, "execution_log.json")
        if os.path.exists(execution_log_path):
            with open(execution_log_path, 'r') as f:
                execution_log = json.load(f)
            
            summary = execution_log.get("summary", {})
            
            # Load diagnostics for critical issues
            diagnostics_path = os.path.join(self.output_dir, "diagnostics.json")
            critical_issues = []
            if os.path.exists(diagnostics_path):
                with open(diagnostics_path, 'r') as f:
                    diagnostics = json.load(f)
                
                for failure in diagnostics.get("failure_analysis", []):
                    if failure.get("severity") == "CRITICAL":
                        critical_issues.append(
                            f"{failure['test_id']}: {failure['root_cause']}"
                        )
            
            return VerificationResult(
                success=success and summary.get("tests_failed", 0) == 0,
                pass_rate=summary.get("pass_rate", 0.0),
                total_tests=summary.get("total_tests", 0),
                passed_tests=summary.get("tests_passed", 0),
                failed_tests=summary.get("tests_failed", 0),
                critical_issues=critical_issues,
                execution_time=elapsed,
                report_path=os.path.join(self.output_dir, "report.html"),
                artifacts_dir=self.output_dir,
                stages_completed=self.pipeline.registry.list_stages()
            )
        else:
            # Pipeline didn't reach execution stage
            return VerificationResult(
                success=False,
                pass_rate=0.0,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                critical_issues=["Pipeline execution incomplete"],
                execution_time=elapsed,
                report_path="",
                artifacts_dir=self.output_dir,
                stages_completed=[]
            )
    
    def _print_header(self):
        """Print pipeline header."""
        print("\n" + "=" * 60)
        print("POLYGLOT FFI VERIFICATION PIPELINE")
        print("=" * 60)
        print(f"Header:  {self.header_path}")
        print(f"Library: {self.library_path}")
        print(f"Output:  {self.output_dir}")
        print("=" * 60 + "\n")
    
    def _print_summary(self, result: VerificationResult):
        """Print execution summary."""
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        print(result)
        print("=" * 60 + "\n")

# ───────────────────────────────────────────────────────────────────
# 11.3 High-Level API
# ───────────────────────────────────────────────────────────────────

def verify(
    header_path: str,
    library_path: str,
    output_dir: str = "artifacts",
    verbose: bool = True
) -> VerificationResult:
    """
    Complete FFI verification pipeline.
    
    This is the main entry point for verification. It executes all stages
    from native interface ingestion through diagnostics and reporting.
    
    Args:
        header_path: Path to C header file
        library_path: Path to native library (.dll, .so, .dylib)
        output_dir: Directory for artifacts and reports
        verbose: Show progress messages
        
    Returns:
        VerificationResult with summary and artifact paths
        
    Example:
        >>> result = verify("interface.h", "library.dll")
        >>> if result.success:
        ...     print(f"Verification passed: {result.pass_rate}%")
        ... else:
        ...     print(f"Verification failed: {len(result.critical_issues)} critical issues")
    """
    pipeline = CompletePipeline(header_path, library_path, output_dir)
    return pipeline.execute(verbose=verbose)

# ───────────────────────────────────────────────────────────────────
# 11.4 CLI Entry Point
# ───────────────────────────────────────────────────────────────────

def cli_main():
    """Command-line interface for verification pipeline."""
    parser = argparse.ArgumentParser(
        prog="verification_pipeline",
        description="Polyglot FFI Verification Pipeline - Verify C FFI correctness"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Verify command
    verify_cmd = subparsers.add_parser("verify", help="Run complete verification")
    verify_cmd.add_argument("header", help="Path to C header file")
    verify_cmd.add_argument("library", help="Path to native library")
    verify_cmd.add_argument("--output", default="artifacts", help="Output directory")
    verify_cmd.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    
    # List stages command
    list_cmd = subparsers.add_parser("list-stages", help="List available pipeline stages")
    
    # Info command
    info_cmd = subparsers.add_parser("info", help="Show pipeline information")
    
    # Incremental commands (Existing)
    incremental_cmd = subparsers.add_parser("run-incremental", help="Run pipeline incrementally")
    incremental_cmd.add_argument("--context", required=True, help="Execution context path")
    incremental_cmd.add_argument("--target", help="Target artifact to produce")

    staleness_cmd = subparsers.add_parser("check-staleness", help="Check artifact staleness")
    staleness_cmd.add_argument("artifact", help="Artifact path to check")
    staleness_cmd.add_argument("--context", required=True)

    args = parser.parse_args()
    
    if args.command == "verify":
        try:
            result = verify(
                header_path=args.header,
                library_path=args.library,
                output_dir=args.output,
                verbose=not args.quiet
            )
            # Exit with appropriate code
            sys.exit(0 if result.success else 1)
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)
    
    elif args.command == "list-stages":
        print("Available Pipeline Stages:")
        print("=" * 60)
        stages = [
            "1. native_interface_ingestion - Extract ABI from header",
            "2. ir_normalization - Normalize to canonical IR",
            "3. contract_synthesis - Synthesize FFI contract",
            "4. adapter_generation - Generate runtime adapters",
            "5. test_plan_generation - Generate test plan",
            "6. verification_execution - Execute tests",
            "7. diagnostics_reporting - Analyze and report"
        ]
        for stage in stages:
            print(f"  {stage}")
        return 0
    
    elif args.command == "info":
        print("Polyglot FFI Verification Pipeline")
        print("=" * 60)
        print("Version: 1.0.0")
        print("Module: 02 - Verification Pipeline")
        print("Stages: 7 (complete)")
        print("Status: Integrated and operational")
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

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ───────────────────────────────────────────────────────────────────
# 12.1 Cache Manager
# ───────────────────────────────────────────────────────────────────

class CacheManager:
    """
    Manages artifact caching for performance optimization.
    
    Caches expensive stage outputs and reuses them when inputs unchanged.
    """
    
    def __init__(self, cache_dir: str = ".verification_cache"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # SQLite database for cache metadata
        self.db_path = os.path.join(cache_dir, "cache.db")
        self._init_database()
        
        # Thread lock for database access
        self.lock = threading.Lock()
    
    def _init_database(self):
        """Initialize cache database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                cache_key TEXT PRIMARY KEY,
                stage_name TEXT NOT NULL,
                stage_version TEXT NOT NULL,
                inputs_json TEXT NOT NULL,
                outputs_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                hits INTEGER DEFAULT 0,
                last_accessed TEXT NOT NULL
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stage_name ON cache_entries(stage_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)')
        
        conn.commit()
        conn.close()
    
    def compute_cache_key(self, inputs: Dict[str, str]) -> str:
        """
        Compute deterministic cache key from inputs.
        
        Args:
            inputs: Dictionary of input artifacts
            
        Returns:
            SHA-256 hash as hex string
        """
        hasher = hashlib.sha256()
        
        # Sort for determinism
        for key in sorted(inputs.keys()):
            value = inputs[key]
            
            # Hash file contents
            if os.path.isfile(value):
                with open(value, 'rb') as f:
                    hasher.update(f.read())
            else:
                hasher.update(str(value).encode())
        
        return hasher.hexdigest()
    
    def lookup(self, stage_name: str, stage_version: str, inputs: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Look up cached outputs for stage and inputs.
        
        Args:
            stage_name: Stage name
            stage_version: Stage version
            inputs: Input artifacts
            
        Returns:
            Dictionary of output artifacts if cache hit, None if miss
        """
        cache_key = self.compute_cache_key(inputs)
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT stage_version, outputs_json, hits
                FROM cache_entries
                WHERE cache_key = 
            ''', (cache_key,))
            
            row = cursor.fetchone()
            
            if row is None:
                conn.close()
                return None  # Cache miss
            
            cached_version, outputs_json, hits = row
            
            # Validate stage version
            if cached_version != stage_version:
                conn.close()
                return None  # Version mismatch
            
            # Parse outputs
            outputs = json.loads(outputs_json)
            
            # Validate outputs still exist
            for output_path in outputs.values():
                if not os.path.exists(output_path):
                    conn.close()
                    return None  # Output deleted
            
            # Update access stats
            cursor.execute('''
                UPDATE cache_entries
                SET hits = , last_accessed = 
                WHERE cache_key = 
            ''', (hits + 1, datetime.now(timezone.utc).isoformat(), cache_key))
            
            conn.commit()
            conn.close()
            
            return outputs  # Cache hit
    
    def store(self, stage_name: str, stage_version: str, inputs: Dict[str, str], outputs: Dict[str, str]):
        """
        Store stage outputs in cache.
        
        Args:
            stage_name: Stage name
            stage_version: Stage version
            inputs: Input artifacts
            outputs: Output artifacts
        """
        cache_key = self.compute_cache_key(inputs)
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries
                (cache_key, stage_name, stage_version, inputs_json, outputs_json, created_at, hits, last_accessed)
                VALUES (, , , , , , , )
            ''', (
                cache_key,
                stage_name,
                stage_version,
                json.dumps(inputs),
                json.dumps(outputs),
                datetime.now(timezone.utc).isoformat(),
                0,
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
            conn.close()
    
    def invalidate_stage(self, stage_name: str):
        """Invalidate all cache entries for a stage."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache_entries WHERE stage_name = ', (stage_name,))
            conn.commit()
            conn.close()
    
    def clear_all(self):
        """Clear entire cache."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache_entries')
            conn.commit()
            conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*), SUM(hits) FROM cache_entries')
            row = cursor.fetchone()
            total_entries = row[0] if row[0] else 0
            total_hits = row[1] if row[1] else 0
            
            cursor.execute('SELECT stage_name, COUNT(*), SUM(hits) FROM cache_entries GROUP BY stage_name')
            by_stage = {row[0]: {"entries": row[1], "hits": row[2] or 0} for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                "total_entries": total_entries,
                "total_hits": total_hits,
                "by_stage": by_stage
            }

# ───────────────────────────────────────────────────────────────────
# 12.2 Dependency Graph Helper
# ───────────────────────────────────────────────────────────────────

class DependencyGraph:
    """Simple dependency graph for stage ordering."""
    
    def __init__(self, stage_classes: List[type]):
        """Build dependency graph from stage classes."""
        self.graph = {}
        
        # Map outputs to producing stages
        producers = {}
        for stage_class in stage_classes:
            for output in stage_class.PRODUCED_OUTPUTS:
                producers[output] = stage_class.STAGE_NAME
        
        # Build dependency edges
        for stage_class in stage_classes:
            dependencies = set()
            for required_input in stage_class.REQUIRED_INPUTS:
                if required_input in producers:
                    dependencies.add(producers[required_input])
            self.graph[stage_class.STAGE_NAME] = dependencies

# ───────────────────────────────────────────────────────────────────
# 12.3 Parallel Executor
# ───────────────────────────────────────────────────────────────────

class ParallelPipelineExecutor:
    """
    Executes independent pipeline stages in parallel.
    
    Uses level-based parallelism based on dependency graph.
    """
    
    def __init__(self, pipeline: 'EnhancedVerificationPipeline', max_workers: int = 4):
        """
        Initialize parallel executor.
        
        Args:
            pipeline: Pipeline to execute
            max_workers: Maximum parallel workers
        """
        self.pipeline = pipeline
        self.max_workers = max_workers
    
    def execute_parallel(self) -> bool:
        """
        Execute pipeline with parallel stage execution.
        
        Returns:
            True if all stages completed successfully
        """
        # Build dependency graph
        stage_classes = [
            self.pipeline.registry.get_stage_class(name)
            for name in self.pipeline.registry.list_stages()
        ]
        
        dep_graph = DependencyGraph(stage_classes)
        
        # Compute execution levels
        levels = self._compute_execution_levels(dep_graph)
        
        # Execute level by level
        for level_num, level_stages in enumerate(levels):
            print(f"Executing level {level_num + 1}/{len(levels)}: {len(level_stages)} stage(s)")
            
            if not self._execute_level(level_stages):
                return False  # Level failed
        
        return True
    
    def _compute_execution_levels(self, dep_graph: DependencyGraph) -> List[List[str]]:
        """
        Compute execution levels for parallel execution.
        
        Returns list of levels, where each level is list of stage names
        that can execute in parallel.
        """
        levels = []
        remaining = set(self.pipeline.registry.list_stages())
        completed = set()
        
        while remaining:
            # Find stages with all dependencies satisfied
            current_level = []
            for stage_name in remaining:
                dependencies = dep_graph.graph.get(stage_name, set())
                if dependencies.issubset(completed):
                    current_level.append(stage_name)
            
            if not current_level:
                raise ValueError("Circular dependency or unresolvable stages")
            
            levels.append(current_level)
            remaining -= set(current_level)
            completed.update(current_level)
        
        return levels
    
    def _execute_level(self, stage_names: List[str]) -> bool:
        """
        Execute all stages in a level in parallel.
        
        Returns True if all succeeded.
        """
        if len(stage_names) == 1:
            # Single stage - execute directly
            return self._execute_single_stage(stage_names[0])
        
        # Multiple stages - execute in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._execute_single_stage, stage_name): stage_name
                for stage_name in stage_names
            }
            
            results = []
            for future in as_completed(futures):
                stage_name = futures[future]
                try:
                    success = future.result()
                    results.append(success)
                    if not success:
                        print(f"✗ Stage {stage_name} failed")
                except Exception as e:
                    print(f"✗ Stage {stage_name} raised exception: {e}")
                    results.append(False)
            
            return all(results)
    
    def _execute_single_stage(self, stage_name: str) -> bool:
        """Execute a single stage."""
        try:
            stage_class = self.pipeline.registry.get_stage_class(stage_name)
            stage = stage_class(self.pipeline.execution_context)
            
            stage.execute()
            
            print(f"  ✓ {stage_name}")
            return True
        
        except Exception as e:
            print(f"  ✗ {stage_name}: {e}")
            return False

# ───────────────────────────────────────────────────────────────────
# 12.4 Performance Profiler
# ───────────────────────────────────────────────────────────────────

class PerformanceProfiler:
    """
    Profiles pipeline execution for performance analysis.
    """
    
    def __init__(self):
        self.stage_profiles = {}
    
    def profile_stage(self, stage_name: str, execution_func):
        """
        Profile stage execution.
        
        Args:
            stage_name: Stage name
            execution_func: Function to execute
            
        Returns:
            Execution result
        """
        # Capture start state
        start_time = time.time()
        start_memory = 0
        
        # Try to get memory info if psutil available
        try:
            import psutil
            process = psutil.Process()
            start_cpu = process.cpu_times()
            start_memory = process.memory_info().rss
            has_psutil = True
        except ImportError:
            has_psutil = False
        
        # Execute
        result = execution_func()
        
        # Capture end state
        end_time = time.time()
        wall_time = end_time - start_time
        
        if has_psutil:
            end_cpu = process.cpu_times()
            end_memory = process.memory_info().rss
            cpu_time = (end_cpu.user - start_cpu.user) + (end_cpu.system - start_cpu.system)
            io_time = wall_time - cpu_time
            peak_memory = max(end_memory, start_memory)
        else:
            cpu_time = wall_time  # Estimate
            io_time = 0.0
            peak_memory = 0
        
        # Store profile
        self.stage_profiles[stage_name] = {
            "wall_time": wall_time,
            "cpu_time": cpu_time,
            "io_time": io_time,
            "peak_memory_mb": peak_memory / (1024 * 1024) if peak_memory > 0 else 0
        }
        
        return result
    
    def generate_report(self) -> str:
        """Generate performance report."""
        lines = []
        lines.append("Performance Profile")
        lines.append("=" * 80)
        lines.append(f"{'Stage':<30} {'Time':>10} {'CPU':>10} {'I/O':>10} {'Memory':>12}")
        lines.append("-" * 80)
        
        total_time = 0
        total_cpu = 0
        total_io = 0
        peak_memory = 0
        
        for stage_name, profile in self.stage_profiles.items():
            lines.append(
                f"{stage_name:<30} "
                f"{profile['wall_time']:>8.1f}s "
                f"{profile['cpu_time']:>8.1f}s "
                f"{profile['io_time']:>8.1f}s "
                f"{profile['peak_memory_mb']:>10.0f} MB"
            )
            
            total_time += profile['wall_time']
            total_cpu += profile['cpu_time']
            total_io += profile['io_time']
            peak_memory = max(peak_memory, profile['peak_memory_mb'])
        
        lines.append("-" * 80)
        lines.append(
            f"{'TOTAL':<30} "
            f"{total_time:>8.1f}s "
            f"{total_cpu:>8.1f}s "
            f"{total_io:>8.1f}s "
            f"{peak_memory:>10.0f} MB"
        )
        lines.append("=" * 80)
        
        return "\n".join(lines)

# ───────────────────────────────────────────────────────────────────
# 12.5 Enhanced Complete Pipeline with Caching & Parallelism
# ───────────────────────────────────────────────────────────────────

class OptimizedCompletePipeline(CompletePipeline):
    """
    Enhanced pipeline with caching, parallel execution, and profiling.
    """
    
    def __init__(
        self,
        header_path: str,
        library_path: str,
        output_dir: str = "artifacts",
        cache_enabled: bool = True,
        parallel: bool = False,
        max_workers: int = 4,
        profile: bool = False
    ):
        super().__init__(header_path, library_path, output_dir)
        
        self.cache_enabled = cache_enabled
        self.parallel = parallel
        self.max_workers = max_workers
        self.profile_enabled = profile
        
        if self.cache_enabled:
            self.cache_manager = CacheManager()
        
        if self.profile_enabled:
            self.profiler = PerformanceProfiler()
    
    def execute(self, verbose: bool = True) -> VerificationResult:
        """Execute with optimizations."""
        # Use parent implementation but with parallel executor if enabled
        if self.parallel:
            return self._execute_parallel(verbose)
        else:
            return super().execute(verbose)
    
    def _execute_parallel(self, verbose: bool) -> VerificationResult:
        """Execute with parallel stage execution."""
        self.start_time = time.time()
        
        if verbose:
            self._print_header()
            print("Optimization: Parallel execution enabled\n")
        
        try:
            # Setup
            self._create_execution_context()
            self._initialize_pipeline()
            self._register_stages()
            
            # Execute in parallel
            if verbose:
                print("Executing stages in parallel...")
            
            executor = ParallelPipelineExecutor(self.pipeline, self.max_workers)
            success = executor.execute_parallel()
            
            # Build result
            result = self._build_result(success)
            
            if verbose:
                self._print_summary(result)
                
                if self.cache_enabled:
                    stats = self.cache_manager.get_stats()
                    print(f"\nCache Stats: {stats['total_entries']} entries, {stats['total_hits']} hits")
                
                if self.profile_enabled:
                    print("\n" + self.profiler.generate_report())
            
            return result
        
        except Exception as e:
            elapsed = time.time() - self.start_time
            if verbose:
                print(f"\n✗ Pipeline failed: {e}\n")
                traceback.print_exc()
            
            return VerificationResult(
                success=False,
                pass_rate=0.0,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                critical_issues=[str(e)],
                execution_time=elapsed,
                report_path="",
                artifacts_dir=self.output_dir,
                stages_completed=[],
                error=e
            )

# ───────────────────────────────────────────────────────────────────
# 12.6 Enhanced High-Level API
# ───────────────────────────────────────────────────────────────────

def verify_optimized(
    header_path: str,
    library_path: str,
    output_dir: str = "artifacts",
    verbose: bool = True,
    cache: bool = True,
    parallel: bool = False,
    max_workers: int = 4,
    profile: bool = False
) -> VerificationResult:
    """
    Optimized FFI verification with caching and parallel execution.
    
    Args:
        header_path: Path to C header
        library_path: Path to native library
        output_dir: Output directory
        verbose: Show progress
        cache: Enable artifact caching
        parallel: Enable parallel stage execution
        max_workers: Maximum parallel workers
        profile: Enable performance profiling
        
    Returns:
        VerificationResult
        
    Example:
        >>> result = verify_optimized(
        ...     "interface.h", "library.dll",
        ...     cache=True, parallel=True, max_workers=8
        ... )
    """
    pipeline = OptimizedCompletePipeline(
        header_path, library_path, output_dir,
        cache_enabled=cache,
        parallel=parallel,
        max_workers=max_workers,
        profile=profile
    )
    return pipeline.execute(verbose=verbose)

# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# 13.1 Custom Constraint Base
# ───────────────────────────────────────────────────────────────────

class CustomConstraint(ABC):
    """
    Base class for custom user-defined constraints.
    
    Users extend this to create domain-specific constraint types.
    """
    
    CONSTRAINT_TYPE: str  # Unique constraint type identifier
    
    def __init__(self, constraint_type: str, target: str, **metadata):
        """
        Initialize constraint.
        
        Args:
            constraint_type: Type of constraint
            target: What this constrains (parameter name, etc.)
            **metadata: Additional metadata
        """
        self.constraint_type = constraint_type
        self.target = target
        self.metadata = metadata
        self.constraint_id = f"custom_{constraint_type}_{target}"
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        """
        Validate value against constraint.
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def generate_check_code(self) -> str:
        """
        Generate Python code for runtime check.
        
        Returns:
            Python code as string
        """
        raise NotImplementedError
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "constraint_id": self.constraint_id,
            "type": self.constraint_type,
            "target": self.target,
            **self.metadata
        }

# ───────────────────────────────────────────────────────────────────
# 13.2 Plugin Interface
# ───────────────────────────────────────────────────────────────────

class PipelinePlugin(ABC):
    """
    Base class for pipeline plugins.
    
    Plugins extend pipeline with custom stages, rules, and hooks.
    """
    
    PLUGIN_NAME: str
    PLUGIN_VERSION: str
    PLUGIN_AUTHOR: str = "Unknown"
    
    @abstractmethod
    def initialize(self, pipeline: 'EnhancedVerificationPipeline'):
        """
        Initialize plugin with pipeline.
        
        Args:
            pipeline: Pipeline instance
        """
        raise NotImplementedError
    
    def register_stages(self, registry: 'StageRegistry'):
        """
        Register custom stages.
        
        Args:
            registry: Stage registry
        """
        pass
    
    def register_rules(self, registry: 'RuleRegistry'):
        """
        Register custom constraint rules.
        
        Args:
            registry: Rule registry
        """
        pass
    
    def get_hooks(self) -> Dict[str, Callable]:
        """
        Get hook functions.
        
        Returns:
            Dictionary of hook_point → function
        """
        return {}

# ───────────────────────────────────────────────────────────────────
# 13.3 Rule Registry
# ───────────────────────────────────────────────────────────────────

class RuleRegistry:
    """
    Registry of custom constraint rules.
    
    Manages user-defined rules and their synthesis heuristics.
    """
    
    def __init__(self):
        self.rules: Dict[str, Dict] = {}  # rule_id → rule_info
    
    def register(
        self,
        rule_id: str,
        constraint_class: type,
        synthesis_heuristic: Optional[Callable] = None,
        priority: int = 0
    ):
        """
        Register custom rule.
        
        Args:
            rule_id: Unique rule identifier
            constraint_class: CustomConstraint subclass
            synthesis_heuristic: Function to determine if rule applies
            priority: Rule priority (higher = applied first)
        """
        if rule_id in self.rules:
            raise ValueError(f"Rule already registered: {rule_id}")
        
        self.rules[rule_id] = {
            "constraint_class": constraint_class,
            "synthesis_heuristic": synthesis_heuristic,
            "priority": priority
        }
    
    def get_applicable_rules(self, context: Dict) -> List[Dict]:
        """
        Get rules applicable to given context.
        
        Args:
            context: Context (parameter, function, etc.)
            
        Returns:
            List of applicable rule infos, sorted by priority
        """
        applicable = []
        
        for rule_id, rule_info in self.rules.items():
            heuristic = rule_info["synthesis_heuristic"]
            
            if heuristic is None or heuristic(context):
                applicable.append({
                    "rule_id": rule_id,
                    **rule_info
                })
        
        # Sort by priority (descending)
        applicable.sort(key=lambda r: r["priority"], reverse=True)
        
        return applicable
    
    def list_rules(self) -> List[str]:
        """List all registered rule IDs."""
        return list(self.rules.keys())

# ───────────────────────────────────────────────────────────────────
# 13.4 Hook System
# ───────────────────────────────────────────────────────────────────

class HookPoints:
    """Enumeration of available hook points."""
    
    # Pipeline-level
    PRE_PIPELINE = "pre_pipeline"
    POST_PIPELINE = "post_pipeline"
    PIPELINE_ERROR = "pipeline_error"
    
    # Stage-level
    PRE_STAGE = "pre_stage"
    POST_STAGE = "post_stage"
    STAGE_ERROR = "stage_error"
    
    # Contract synthesis
    POST_CONTRACT_SYNTHESIS = "post_contract_synthesis"

@dataclass
class HookContext:
    """Context passed to hook functions."""
    execution_id: str
    pipeline: Any  # EnhancedVerificationPipeline
    metadata: Dict[str, Any] = field(default_factory=dict)

class HookManager:
    """
    Manages hook registration and execution.
    """
    
    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}  # hook_point → list of functions
    
    def register(self, hook_point: str, func: Callable):
        """
        Register hook function.
        
        Args:
            hook_point: Hook point identifier (from HookPoints)
            func: Hook function
        """
        if hook_point not in self.hooks:
            self.hooks[hook_point] = []
        
        self.hooks[hook_point].append(func)
    
    def execute(self, hook_point: str, context: HookContext, **kwargs):
        """
        Execute all hooks for a hook point.
        
        Args:
            hook_point: Hook point identifier
            context: Hook execution context
            **kwargs: Hook-specific arguments
        """
        if hook_point not in self.hooks:
            return
        
        for func in self.hooks[hook_point]:
            try:
                func(context, **kwargs)
            except Exception as e:
                # Log but don't fail - hooks shouldn't break pipeline
                print(f"Warning: Hook {func.__name__} failed: {e}")
    
    def list_hooks(self, hook_point: Optional[str] = None) -> Dict[str, int]:
        """
        List registered hooks.
        
        Args:
            hook_point: Specific hook point or None for all
            
        Returns:
            Dictionary of hook_point → count
        """
        if hook_point:
            return {hook_point: len(self.hooks.get(hook_point, []))}
        else:
            return {hp: len(funcs) for hp, funcs in self.hooks.items()}

# ───────────────────────────────────────────────────────────────────
# 13.5 Plugin Manager
# ───────────────────────────────────────────────────────────────────

class PluginManager:
    """
    Manages plugin registration and lifecycle.
    """
    
    def __init__(self, pipeline: 'EnhancedVerificationPipeline'):
        self.pipeline = pipeline
        self.plugins: List[PipelinePlugin] = []
    
    def register_plugin(self, plugin: PipelinePlugin):
        """
        Register plugin.
        
        Args:
            plugin: Plugin instance
        """
        # Validate plugin
        errors = self._validate_plugin(plugin)
        if errors:
            raise ValueError(f"Plugin validation failed: {errors}")
        
        # Initialize plugin
        plugin.initialize(self.pipeline)
        
        # Register plugin's stages
        if hasattr(self.pipeline, 'registry'):
            plugin.register_stages(self.pipeline.registry)
        
        # Register plugin's rules
        rule_registry = getattr(self.pipeline, 'rule_registry', None)
        if rule_registry:
            plugin.register_rules(rule_registry)
        
        # Register plugin's hooks
        hook_manager = getattr(self.pipeline, 'hook_manager', None)
        if hook_manager:
            for hook_point, func in plugin.get_hooks().items():
                hook_manager.register(hook_point, func)
        
        self.plugins.append(plugin)
    
    def _validate_plugin(self, plugin: PipelinePlugin) -> List[str]:
        """Validate plugin before registration."""
        errors = []
        
        # Check required attributes
        if not hasattr(plugin, 'PLUGIN_NAME'):
            errors.append("Missing PLUGIN_NAME")
        
        if not hasattr(plugin, 'PLUGIN_VERSION'):
            errors.append("Missing PLUGIN_VERSION")
        
        # Check required methods
        if not hasattr(plugin, 'initialize'):
            errors.append("Missing initialize() method")
        
        return errors
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """List registered plugins."""
        return [
            {
                "name": p.PLUGIN_NAME,
                "version": p.PLUGIN_VERSION,
                "author": getattr(p, 'PLUGIN_AUTHOR', 'Unknown')
            }
            for p in self.plugins
        ]

# ───────────────────────────────────────────────────────────────────
# 13.6 Rule Templates
# ───────────────────────────────────────────────────────────────────

class RuleTemplates:
    """
    Collection of reusable constraint templates.
    
    Provides common constraint patterns that users can apply.
    """
    
    @staticmethod
    def pointer_not_null(param_name: str) -> Dict:
        """Template: Pointer must not be null."""
        return {
            "type": "NON_NULL",
            "target": f"param_{param_name}",
            "rationale": "Applied from pointer_not_null template"
        }
    
    @staticmethod
    def buffer_with_length(buffer_param: str, length_param: str) -> Dict:
        """Template: Buffer with explicit length parameter."""
        return {
            "type": "BUFFER_SIZE",
            "target": f"param_{buffer_param}",
            "related_target": f"param_{length_param}",
            "rationale": "Applied from buffer_with_length template"
        }
    
    @staticmethod
    def output_parameter(param_name: str) -> Dict:
        """Template: Output parameter (pointer-to-pointer)."""
        return {
            "type": "OUTPUT_PARAMETER",
            "target": f"param_{param_name}",
            "rationale": "Applied from output_parameter template"
        }

# ───────────────────────────────────────────────────────────────────
# 13.7 Extended Pipeline with Plugin Support
# ───────────────────────────────────────────────────────────────────

class ExtensiblePipeline(OptimizedCompletePipeline):
    """
    Pipeline with plugin and hook support.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.rule_registry = RuleRegistry()
        self.hook_manager = HookManager()
        self.plugin_manager = PluginManager(self)
    
    def register_plugin(self, plugin: PipelinePlugin):
        """Register plugin."""
        self.plugin_manager.register_plugin(plugin)
    
    def register_hook(self, hook_point: str, func: Callable):
        """Register hook function."""
        self.hook_manager.register(hook_point, func)
    
    def register_custom_rule(
        self,
        rule_id: str,
        constraint_class: type,
        synthesis_heuristic: Optional[Callable] = None
    ):
        """Register custom rule."""
        self.rule_registry.register(rule_id, constraint_class, synthesis_heuristic)
    
    def execute(self, verbose: bool = True) -> VerificationResult:
        """Execute with hooks."""
        # Execute pre-pipeline hooks
        context = HookContext(
            execution_id=str(uuid.uuid4()),
            pipeline=self,
            metadata={}
        )
        self.hook_manager.execute(HookPoints.PRE_PIPELINE, context)
        
        try:
            # Execute pipeline
            result = super().execute(verbose)
            
            # Execute post-pipeline hooks
            self.hook_manager.execute(HookPoints.POST_PIPELINE, context, result=result)
            
            return result
        
        except Exception as e:
            # Execute error hooks
            self.hook_manager.execute(HookPoints.PIPELINE_ERROR, context, error=e)
            raise

# ───────────────────────────────────────────────────────────────────
# 13.8 Enhanced High-Level API
# ───────────────────────────────────────────────────────────────────

def verify_extensible(
    header_path: str,
    library_path: str,
    output_dir: str = "artifacts",
    plugins: Optional[List[PipelinePlugin]] = None,
    hooks: Optional[Dict[str, Callable]] = None,
    custom_rules: Optional[Dict] = None,
    **kwargs
) -> VerificationResult:
    """
    Extensible FFI verification with plugins and hooks.
    
    Args:
        header_path: Path to C header
        library_path: Path to native library
        output_dir: Output directory
        plugins: List of plugins to register
        hooks: Dictionary of hook_point → function
        custom_rules: Dictionary of custom rules to register
        **kwargs: Additional options
        
    Returns:
        VerificationResult
        
    Example:
        >>> plugin = MyCustomPlugin()
        >>> result = verify_extensible(
        ...     "interface.h", "library.dll",
        ...     plugins=[plugin],
        ...     hooks={"post_contract_synthesis": my_hook}
        ... )
    """
    pipeline = ExtensiblePipeline(header_path, library_path, output_dir, **kwargs)
    
    # Register plugins
    if plugins:
        for plugin in plugins:
            pipeline.register_plugin(plugin)
    
    # Register hooks
    if hooks:
        for hook_point, func in hooks.items():
            pipeline.register_hook(hook_point, func)
    
    # Register custom rules
    if custom_rules:
        for rule_id, rule_info in custom_rules.items():
            pipeline.register_custom_rule(
                rule_id,
                rule_info["constraint_class"],
                rule_info.get("synthesis_heuristic")
            )
    
    return pipeline.execute(**kwargs)

if __name__ == '__main__':
    sys.exit(cli_main())

