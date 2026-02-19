"""
Polyglot FFI Contract Verifier (PFCV)
Module 09: Python Adapter Model
Phase 1: Infrastructural Ingestion & Cryptographic Anchoring

This module implements the secure, deterministic contract runtime loader for 
the Python environment, providing SHA-256 integrity verification, 
ABI interrogation, and memory-optimized enforcement descriptors.
"""

import json
import hashlib
import hmac
import os
import sys
import struct
import threading
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass, field


# =============================================================================
# EXCEPTION TAXONOMY
# =============================================================================

class PFCVBaseError(Exception):
    """Root class for all Polyglot FFI Contract Verifier exceptions."""
    def __init__(self, message: str, failure_code: str):
        super().__init__(f"[{failure_code}] {message}")
        self.failure_code = failure_code


class ContractLoadError(PFCVBaseError):
    """Raised for I/O or structural JSON failures during contract ingestion."""
    def __init__(self, message: str):
        super().__init__(message, "ERR-LOG-001")


class ContractIntegrityViolationError(PFCVBaseError):
    """Raised when the contract fingerprint does not match the computed hash."""
    def __init__(self, expected: str, observed: str):
        message = f"Integrity mismatch! Expected: {expected}, Observed: {observed}"
        super().__init__(message, "ERR-INT-002")
        self.expected = expected
        self.observed = observed


class ABIMismatchError(PFCVBaseError):
    """Raised when the host environment deviates from the contract's ABI truth."""
    def __init__(self, message: str):
        super().__init__(message, "ERR-ABI-003")


class VersionIncompatibilityError(PFCVBaseError):
    """Raised when the contract version falls outside the supported compatibility matrix."""
    def __init__(self, message: str):
        super().__init__(message, "ERR-VER-004")



# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(slots=True)
class EnforcementDescriptor:
    """
    Memory-optimized descriptor for a single native function.
    Utilizes __slots__ to eliminate __dict__ overhead in high-scale environments.
    """
    name: str
    calling_convention: str
    is_variadic: bool
    symbol_address: Optional[int] = None
    pre_validators: List[Any] = field(default_factory=list)
    post_validators: List[Any] = field(default_factory=list)
    relational_map: Dict[str, Any] = field(default_factory=dict)
    ownership_slots: Dict[str, Any] = field(default_factory=dict)


class EnforcementTable:
    """
    O(1) lookup table for EnforcementDescriptors.
    Enforces single-registration logic to prevent silent constraint shadowing.
    """
    def __init__(self):
        self._descriptors: Dict[str, EnforcementDescriptor] = {}

    def register(self, descriptor: EnforcementDescriptor) -> None:
        """Register a new function descriptor with collision detection."""
        if descriptor.name in self._descriptors:
            raise PFCVBaseError(
                f"Function collision detected: {descriptor.name} is already registered.",
                "ERR-TABLE-005"
            )
        self._descriptors[descriptor.name] = descriptor

    def get(self, name: str) -> EnforcementDescriptor:
        """Retrieve a descriptor by name in constant time."""
        if name not in self._descriptors:
            raise ContractLoadError(f"Function {name} not found in enforcement table.")
        return self._descriptors[name]

    def __len__(self) -> int:
        return len(self._descriptors)

    def names(self) -> List[str]:
        """Return a sorted list of registered function names."""
        return sorted(self._descriptors.keys())



# =============================================================================
# CONTRACT RUNTIME LOADER
# =============================================================================

class ContractLoader:
    """
    The secure, deterministic orchestrator for contract ingestion.
    Performs binary ingestion, HMAC-based integrity checks, and ABI alignment.
    """
    
    SCHEMA_VERSION_MIN = (1, 0, 0)
    SYNTHESIS_VERSION_MIN = (0, 8, 5)
    
    def __init__(self, contract_path: str):
        self.contract_path = os.path.abspath(contract_path)
        self.is_loaded: bool = False
        self.raw_bytes: bytes = b""
        self.contract_data: Dict[str, Any] = {}
        self.table: EnforcementTable = EnforcementTable()
        self._lock = threading.Lock()

    def load(self) -> EnforcementTable:
        """
        Executes the total automated ingestion pipeline.
        Returns a verified EnforcementTable or raises a fatal exception.
        """
        with self._lock:
            if self.is_loaded:
                return self.table
                
            # 1. Ingestion
            self._ingest_binary()
            
            # 2. Integrity Verification
            self._verify_fingerprint()
            
            # 3. Host Interrogation (ABI Truth Mapping)
            self._interrogate_host()
            
            # 4. Version Validation
            self._verify_version_logic()
            
            # 5. Compilation
            self._build_table()
            
            self.is_loaded = True
            return self.table

    def _ingest_binary(self) -> None:
        """Reads the contract strictly in raw binary mode to prevent newline mutation."""
        try:
            with open(self.contract_path, "rb") as f:
                self.raw_bytes = f.read()
            self.contract_data = json.loads(self.raw_bytes.decode("utf-8"))
        except FileNotFoundError:
            raise ContractLoadError(f"Contract file not found: {self.contract_path}")
        except json.JSONDecodeError as e:
            raise ContractLoadError(f"Malformed JSON in contract: {str(e)}")
        except Exception as e:
            raise ContractLoadError(f"I/O Error during ingestion: {str(e)}")

    def _verify_fingerprint(self) -> None:
        """Calculates SHA-256 hash on canonical representation and verifies via HMAC."""
        # Extract declared fingerprint
        declared_fingerprint = self.contract_data.get("metadata", {}).get("fingerprint")
        if not declared_fingerprint:
            raise ContractLoadError("Contract is missing mandatory fingerprint metadata.")

        # Deep copy and canonicalize
        canonical_dict = self._get_canonical_dict(self.contract_data)
        canonical_json = json.dumps(
            canonical_dict,
            sort_keys=True,
            separators=(',', ':')
        )
        canonical_bytes = canonical_json.encode("utf-8")
        
        # Compute SHA-256
        computed_fingerprint = hashlib.sha256(canonical_bytes).hexdigest()
        
        # Constant-time comparison
        if not hmac.compare_digest(declared_fingerprint, computed_fingerprint):
            raise ContractIntegrityViolationError(
                expected=declared_fingerprint,
                observed=computed_fingerprint
            )

    def _get_canonical_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a deep copy of the contract excluding the fingerprint key."""
        # Simple deep copy for this specific structure
        import copy
        new_data = copy.deepcopy(data)
        if "metadata" in new_data and "fingerprint" in new_data["metadata"]:
            del new_data["metadata"]["fingerprint"]
        return new_data

    def _interrogate_host(self) -> None:
        """Verifies pointer width, endianness, and OS platform family."""
        abi_meta = self.contract_data.get("abi_metadata", {})
        if not abi_meta:
            raise ContractLoadError("Contract is missing mandatory abi_metadata block.")

        # 1. Pointer Width Verification (The 32/64-bit Guardrail)
        host_ptr_width = struct.calcsize("P") * 8
        contract_ptr_width = abi_meta.get("ptr_width")
        if host_ptr_width != contract_ptr_width:
            raise ABIMismatchError(
                f"Architecture mismatch: Host is {host_ptr_width}-bit, "
                f"but contract targets {contract_ptr_width}-bit. "
                "Truncation or extension risk detected."
            )

        # 2. Endianness Validation
        host_endian = sys.byteorder
        contract_endian = abi_meta.get("endianness")
        if host_endian != contract_endian:
            raise ABIMismatchError(
                f"Endianness reversal: Host is {host_endian}, "
                f"but contract is {contract_endian}."
            )

        # 3. OS Platform Family Identification
        host_os = "windows" if os.name == "nt" else "linux/unix"
        contract_os = abi_meta.get("target_os")
        if host_os != contract_os:
            raise ABIMismatchError(
                f"Platform incompatibility: Host is {host_os}, "
                f"but contract targets {contract_os}."
            )

    def _verify_version_logic(self) -> None:
        """Validates schema and synthesis version strings via integer components."""
        meta = self.contract_data.get("metadata", {})
        schema_v = meta.get("schema_version", "0.0.0")
        synth_v = meta.get("synthesis_version", "0.0.0")

        def parse_v(v_str: str) -> tuple:
            try:
                return tuple(map(int, v_str.split(".")))
            except ValueError:
                raise VersionIncompatibilityError(f"Invalid version format: {v_str}")

        current_schema = parse_v(schema_v)
        current_synth = parse_v(synth_v)

        # Version Matrix Checks
        if current_schema[0] != self.SCHEMA_VERSION_MIN[0]:
             raise VersionIncompatibilityError(
                 f"Major schema version mismatch. Expected {self.SCHEMA_VERSION_MIN[0]}.x, Got {schema_v}"
             )
        
        if current_schema < self.SCHEMA_VERSION_MIN:
            raise VersionIncompatibilityError(
                f"Schema version {schema_v} is below minimum requirement {'.'.join(map(str, self.SCHEMA_VERSION_MIN))}"
            )

        if current_synth < self.SYNTHESIS_VERSION_MIN:
            raise VersionIncompatibilityError(
                f"Synthesis version {synth_v} is below minimum {'.'.join(map(str, self.SYNTHESIS_VERSION_MIN))}"
            )

    def _build_table(self) -> None:
        """Compiles function array into EnforcementDescriptor objects."""
        functions = self.contract_data.get("functions", [])
        for func_data in functions:
            descriptor = EnforcementDescriptor(
                name=func_data["name"],
                calling_convention=func_data.get("calling_convention", "cdecl"),
                is_variadic=func_data.get("is_variadic", False),
                symbol_address=func_data.get("symbol_address")
            )
            # Placeholder for future expansion of lists/dicts
            self.table.register(descriptor)

    def get_calling_convention_factory(self, name: str) -> Any:
        """
        Returns the correct ctypes function factory based on ABI and metadata.
        Optimized for Windows stdcall/cdecl matrix.
        """
        import ctypes
        descriptor = self.table.get(name)
        
        # On 64-bit Windows, calling conventions are unified.
        if struct.calcsize("P") == 8 and os.name == "nt":
            return ctypes.CFUNCTYPE

        if descriptor.calling_convention == "stdcall":
            return ctypes.WINFUNCTYPE
        
        return ctypes.CFUNCTYPE
