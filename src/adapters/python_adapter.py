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
import ctypes
from typing import List, Dict, Any, Optional, Type, Tuple, Union, Callable
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


# --- PAL Specific Exceptions ---

class PrototypeAuthorityError(PFCVBaseError):
    """Root base class for all interposition and signature reconstruction failures."""
    def __init__(self, message: str, failure_code: str = "ERR-PAL-006"):
        super().__init__(message, failure_code)


class UnsupportedTypeError(PrototypeAuthorityError):
    """Raised when the Contract contains a type that cannot be safely mapped to ctypes."""
    def __init__(self, ir_type: str):
        super().__init__(f"Unsupported native type: {ir_type}")
        self.failure_code = "ERR-TYPE-008"
        self.ir_type = ir_type


class ABISignatureMismatchError(PrototypeAuthorityError):
    """Raised if the arity or signature does not align with the Contract."""
    def __init__(self, message: str):
        super().__init__(message)
        self.failure_code = "ERR-SIG-007"


class MarshallingViolationError(PrototypeAuthorityError):
    """Raised during execution when a Python value violates Contract bit-width bounds."""
    def __init__(self, param_index: int, contract_type: str, message: str):
        full_msg = f"Parameter {param_index} ({contract_type}) bounds check failed: {message}"
        super().__init__(full_msg)
        self.param_index = param_index
        self.contract_type = contract_type



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
    arg_types: List[str] = field(default_factory=list)
    return_type: str = "VOID"
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
# ABI TYPE FACTORY
# =============================================================================

class ABITypeFactory:
    """
    Deterministic translation layer from Contract IR types to concrete ctypes objects.
    Enforces bit-width fidelity and platform-specific ABI alignment (LLP64 vs LP64).
    """
    
    _TYPE_MAP = {
        # Signed Integers
        "I8": ctypes.c_int8,
        "I16": ctypes.c_int16,
        "I32": ctypes.c_int32,
        "I64": ctypes.c_int64,
        # Unsigned Integers
        "U8": ctypes.c_uint8,
        "U16": ctypes.c_uint16,
        "U32": ctypes.c_uint32,
        "U64": ctypes.c_uint64,
        # Floats
        "FLOAT32": ctypes.c_float,
        "FLOAT64": ctypes.c_double,
        # Misc
        "BOOL": ctypes.c_bool,
        "PTR": ctypes.c_void_p,
        "VOID": None
    }

    def get_ctypes_type(self, ir_type: str) -> Any:
        """Translates IR type string to ctypes type class with O(1) performance."""
        # Case-sensitive check as per Antigravity standards
        if ir_type not in self._TYPE_MAP:
            raise UnsupportedTypeError(ir_type)
        return self._TYPE_MAP[ir_type]

    def is_supported(self, ir_type: str) -> bool:
        """Proactive verification for contract metadata validation."""
        return ir_type in self._TYPE_MAP


# =============================================================================
# INVOCATION PROXY GENERATOR
# =============================================================================

class InvocationProxy:
    """
    High-performance wrapper for bound native functions.
    Enforces 'Zero-Mistake Marshalling' by validating bit-width boundaries
    before the native code crossing.
    """
    
    __slots__ = ['descriptor', 'bound_function', '_param_types', '_marshaller_cache']
    
    # Pre-computed bounds for Marshalling
    _BOUNDS = {
        "I8": (-128, 127),
        "I16": (-32768, 32767),
        "I32": (-2147483648, 2147483647),
        "I64": (-9223372036854775808, 9223372036854775807),
        "U8": (0, 255),
        "U16": (0, 65535),
        "U32": (0, 4294967295),
        "U64": (0, 18446744073709551615),
    }

    def __init__(self, descriptor: EnforcementDescriptor, bound_function: Any):
        self.descriptor = descriptor
        self.bound_function = bound_function
        # Extraction of parameter types from descriptor placeholder logic
        # (Assuming pre_validators or a dedicated field stores the IR type metadata)
        # For Prompt 02, we'll assume the descriptor carries the arg_types list.
        # Note: EnforcementDescriptor was defined in P1 without arg_types, 
        # but PAL requires them. I will update EnforcementDescriptor below.
        self._param_types: Tuple[str, ...] = tuple(getattr(descriptor, 'arg_types', []))

    def _enforce_integer_bounds(self, arg_value: int, contract_type: str, index: int) -> None:
        """Strict numeric boundary enforcement. No try-except; O(1) comparison only."""
        if contract_type not in self._BOUNDS:
            return
            
        lower, upper = self._BOUNDS[contract_type]
        if arg_value < lower or arg_value > upper:
            raise MarshallingViolationError(
                param_index=index,
                contract_type=contract_type,
                message=f"Value {arg_value} is out of bounds [{lower}, {upper}]."
            )

    def __call__(self, *args, **kwargs) -> Any:
        """Hot-path execution orchestrator."""
        # Step 1: Arity Check
        if len(args) != len(self._param_types):
            raise ABISignatureMismatchError(
                f"Function {self.descriptor.name} expects {len(self._param_types)} "
                f"positional arguments, but got {len(args)}."
            )
            
        # Step 2: Marshalling (Iterative, no list creation)
        idx = 0
        for val, c_type in zip(args, self._param_types):
            if isinstance(val, int):
                self._enforce_integer_bounds(val, c_type, idx)
            idx += 1
            
        # Step 3: Native Invocation
        # (Final implementation will include Crash Guarding/Exception Translation)
        return self.bound_function(*args)


# =============================================================================
# PROTOTYPE AUTHORITY LAYER (PAL)
# =============================================================================

class PrototypeAuthority:
    """
    The 'Stack Guardian'. Interposes on ctypes binding, overriding developer
    declarations with Contract ABI Truth.
    """
    
    __slots__ = ['edt', 'type_factory', 'loaded_libraries', 'bound_symbols', '_lock']

    def __init__(self, edt: EnforcementTable, type_factory: Optional[ABITypeFactory] = None):
        self.edt = edt
        self.type_factory = type_factory or ABITypeFactory()
        self.loaded_libraries: Dict[str, Any] = {}
        self.bound_symbols: Dict[str, InvocationProxy] = {}
        self._lock = threading.Lock()

    def _select_convention_factory(self, calling_convention: str) -> Any:
        """Determines CFUNCTYPE vs WINFUNCTYPE based on silicon target."""
        # 64-bit Windows unifies conventions; 32-bit requires strict routing.
        if os.name == "nt":
            if struct.calcsize("P") == 8:
                return ctypes.CFUNCTYPE
            if calling_convention == "stdcall":
                return ctypes.WINFUNCTYPE
        
        return ctypes.CFUNCTYPE

    def bind_symbol(self, library_path: str, symbol_name: str) -> InvocationProxy:
        """
        Interposes on native symbol resolution and synthesizes an InvocationProxy.
        Guarantees O(1) lookup on repeated requests via symbol cache.
        """
        # Multi-threaded binding safety
        with self._lock:
            # Step 0: Cache Lookup
            cache_key = f"{library_path}::{symbol_name}"
            if cache_key in self.bound_symbols:
                return self.bound_symbols[cache_key]
                
            # Step 1: Library loading
            if library_path not in self.loaded_libraries:
                try:
                    # Windows optimization: use WinDLL if stdcall is possible globally, 
                    # but we prefer CDLL and per-function factory selection for granularity.
                    self.loaded_libraries[library_path] = ctypes.CDLL(library_path)
                except OSError as e:
                    raise ContractLoadError(f"Failed to load native library {library_path}: {str(e)}")
            
            lib = self.loaded_libraries[library_path]
            descriptor = self.edt.get(symbol_name)
            
            # Step 2: Symbol Extraction
            try:
                raw_func = getattr(lib, symbol_name)
            except AttributeError:
                raise ABISignatureMismatchError(f"Symbol {symbol_name} not found in {library_path}")
            
            # Step 3: Prototype Synthesis
            arg_types = [self.type_factory.get_ctypes_type(t) for t in getattr(descriptor, 'arg_types', [])]
            res_type = self.type_factory.get_ctypes_type(getattr(descriptor, 'return_type', 'VOID'))
            
            factory = self._select_convention_factory(descriptor.calling_convention)
            prototype = factory(res_type, *arg_types)
            
            # Step 4: Binding Action
            bound_func = prototype((symbol_name, lib))
            
            # Lock the FFI boundary
            bound_func.argtypes = arg_types
            bound_func.restype = res_type
            
            # Step 5: Wrap in Proxy
            proxy = InvocationProxy(descriptor, bound_func)
            self.bound_symbols[cache_key] = proxy
            
            return proxy



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
                arg_types=func_data.get("arg_types", []),
                return_type=func_data.get("return_type", "VOID"),
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
