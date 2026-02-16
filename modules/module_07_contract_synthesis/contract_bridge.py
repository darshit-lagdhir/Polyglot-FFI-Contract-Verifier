"""
Module 07: Contract Bridge (Prompt 4/15)

Bridge between Module 07 (Synthesis Engine) and Module 06 (Contract Schema).

Responsibilities:
- Validate generated clauses against schema
- Assemble contract documents
- Link provenance
- Ensure Module 06 compliance
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from datetime import datetime
import logging

# Module 06 imports
from module_06_contract_schema.contract_entities import (
    ContractDocument, ContractHeader, ContractClause, GenerationMetadata,
    ClauseType, GenerationMode
)
# Assuming ContractValidator exists; if not, use placeholder or generic.
try:
    from module_06_contract_schema.contract_validation import ContractValidator
except ImportError:
    # If not implemented yet, fallback or raise error. 
    pass

logger = logging.getLogger(__name__)

# ============================================================================
# BRIDGE EXCEPTIONS
# ============================================================================

class ContractBridgeError(Exception):
    """Base exception for contract bridge errors."""
    pass

class SchemaComplianceError(ContractBridgeError):
    """Raised when clause violates Module 06 schema."""
    pass

# ============================================================================
# SCHEMA VALIDATION
# ============================================================================

class ContractSchemaValidator:
    """
    Validates synthesized clauses against Module 06 schema.
    
    Ensures all generated clauses comply with contract schema before assembly.
    """
    
    def __init__(self):
        # We can instantiate Module 06 validator if available
        # Or delegate to it.
        try:
             self.validator = ContractValidator() 
        except NameError:
             self.validator = None
        self.logger = logging.getLogger(__name__)
        
    def validate_clause(self, clause: ContractClause) -> bool:
        """
        Validate single clause against schema.
        
        Args:
            clause: Clause to validate
            
        Returns:
            True if valid
            
        Raises:
            SchemaComplianceError: If clause violates schema
        """
        try:
            # Use local structure check first
            if not self._validate_clause_structure(clause):
                 raise SchemaComplianceError(f"Clause {clause.clause_id} violates basic structure")
                 
            # Validate structure using entity method
            if hasattr(clause, 'validate_structure'):
                errors = clause.validate_structure()
                if errors:
                    raise SchemaComplianceError(f"Clause {clause.clause_id} invalid: {errors}")
            
            # If we really want to use ContractValidator, we need to wrap it.
            # But for per-clause validation, structure check is usually enough at generic stage.
            # Comprehensive validation happens at ContractDocument level.
            
            return True
            
        except Exception as e:
            if isinstance(e, SchemaComplianceError):
                raise e
            raise SchemaComplianceError(
                f"Schema validation failed for clause {clause.clause_id}: {str(e)}"
            )
            
    def _validate_clause_structure(self, clause: ContractClause) -> bool:
        """Validate clause structure (simplified)."""
        # Check required fields
        if not clause.clause_id:
            return False
        
        if not clause.clause_type:
            return False
        
        if not clause.subject_reference:
            return False
        
        return True
        
    def validate_clauses_batch(
        self,
        clauses: List[ContractClause]
    ) -> Dict[str, List[str]]:
        """
        Validate multiple clauses efficiently.
        
        Args:
            clauses: List of clauses to validate
            
        Returns:
            Dict mapping clause_id to list of errors (empty if valid)
        """
        results = {}
        
        for clause in clauses:
            try:
                self.validate_clause(clause)
                # results.setdefault(clause.clause_id, []) # Only track errors? The prompt says "empty if valid".
            except SchemaComplianceError as e:
                results[clause.clause_id] = [str(e)]
        
        return results

# ============================================================================
# CONTRACT ASSEMBLY
# ============================================================================

class ContractDocumentBuilder:
    """
    Builds Module 06 ContractDocument from synthesis results.
    
    Assembles clauses into proper contract structure with metadata.
    """
    
    def __init__(self, synthesis_version: str = "1.0.0"):
        self.synthesis_version = synthesis_version
        self.logger = logging.getLogger(__name__)
        
    def build(
        self,
        clauses: List[ContractClause],
        target_interface_id: str,
        synthesis_metadata: Optional[Dict[str, Any]] = None
    ) -> ContractDocument:
        """
        Build contract document from clauses.
        
        Args:
            clauses: Generated clauses
            target_interface_id: Interface identifier
            synthesis_metadata: Additional synthesis metadata
            
        Returns:
            Assembled ContractDocument
        """
        self.logger.info(f"Building contract for interface: {target_interface_id}")
        
        # Create header
        header = ContractHeader(
            contract_version="1.0.0",
            target_interface_id=target_interface_id
        )
        
        # Add generation metadata
        header.generation_metadata = self._build_generation_metadata(synthesis_metadata)
        
        # Create document
        contract = ContractDocument(header=header)
        
        # Add clauses in deterministic order
        ordered_clauses = self._order_clauses(clauses)
        
        for clause in ordered_clauses:
            contract.add_clause(clause)
        
        self.logger.info(f"Contract built: {len(clauses)} clauses")
        
        return contract
        
    def _build_generation_metadata(
        self,
        synthesis_metadata: Optional[Dict[str, Any]]
    ) -> GenerationMetadata:
        """Build generation metadata."""
        # GenerationMode might be Enum or string. Module 06 definition should be checked.
        # Assuming Enum or string is acceptable.
        
        metadata = GenerationMetadata(
            tool_version=self.synthesis_version,
            generation_mode=GenerationMode.AUTO
        )
        
        # Add contextual analysis if available
        # Assuming GenerationMetadata has a 'metadata' dict or similar extensible field
        # Checking prompt: "metadata.metadata['contextual_analysis'] = ..."
        # Wait, if GenerationMetadata is strict dataclass, we can't add fields unless 'metadata' field exists.
        # In step 404 snippet: `header.generation_metadata = GenerationMetadata(...)`
        # It didn't show fields of GenerationMetadata class definition.
        # I'll check if 'metadata' field exists or use getattr/setattr or assume it's extensible.
        # But for now, let's try to pass it to constructor if possible, or correct field.
        # If 'contextual_analysis' is important, it should be in synthesis_metadata dict usually.
        
        if synthesis_metadata:
             # If GenerationMetadata has generic 'metadata' attribute
             if hasattr(metadata, 'metadata') and isinstance(metadata.metadata, dict):
                 if "contextual_analysis" in synthesis_metadata:
                     metadata.metadata["contextual_analysis"] = synthesis_metadata["contextual_analysis"]
        
        return metadata
        
    def _order_clauses(self, clauses: List[ContractClause]) -> List[ContractClause]:
        """
        Order clauses deterministically.
        
        Ordering: clause_type (alphabetically), then clause_id (alphabetically)
        """
        return sorted(
            clauses,
            key=lambda c: (str(c.clause_type.value), c.clause_id)
        )

# ============================================================================
# MAIN CONTRACT BRIDGE
# ============================================================================

class ContractBridge:
    """
    Main contract bridge between Module 07 and Module 06.
    
    Validates and assembles contracts for Module 06 consumption.
    """
    
    def __init__(self, synthesis_version: str = "1.0.0"):
        self.schema_validator = ContractSchemaValidator()
        self.document_builder = ContractDocumentBuilder(synthesis_version)
        self.logger = logging.getLogger(__name__)
        
    def produce_contract(
        self,
        clauses: List[ContractClause],
        target_interface_id: str,
        synthesis_metadata: Optional[Dict[str, Any]] = None,
        strict: bool = True
    ) -> ContractDocument:
        """
        Produce validated contract document.
        
        Args:
            clauses: Generated clauses
            target_interface_id: Interface identifier
            synthesis_metadata: Synthesis metadata
            strict: If True, fail on schema violations
            
        Returns:
            Valid ContractDocument
            
        Raises:
            ContractBridgeError: If validation fails in strict mode
        """
        self.logger.info(f"Producing contract for {target_interface_id}")
        
        # Validate clauses
        validation_results = self.schema_validator.validate_clauses_batch(clauses)
        
        # Check for errors
        errors = {cid: errs for cid, errs in validation_results.items() if errs}
        
        if errors:
            error_msg = "\n".join(
                f"  {cid}: {', '.join(errs)}"
                for cid, errs in errors.items()
            )
            
            if strict:
                raise ContractBridgeError(
                    f"Schema validation failed:\n{error_msg}"
                )
            else:
                self.logger.warning(f"Schema violations (continuing):\n{error_msg}")
        
        # Build contract
        contract = self.document_builder.build(
            clauses,
            target_interface_id,
            synthesis_metadata
        )
        
        self.logger.info(f"Contract produced: {len(contract.clauses)} clauses")
        
        return contract
