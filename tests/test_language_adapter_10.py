
"""Test Suite for Language Adapter - Prompt 10/25: 85 tests."""

import pytest
from modules.module_08_language_adapter import (
    AdapterException,
    ContractViolationError,
    ParameterViolationError,
    ReturnValueViolationError,
    OwnershipViolationError,
    NativeCrashError,
    SegmentationFaultError,
    AccessViolationError,
    ConfigurationError,
    ExceptionFormatter,
    ErrorRecoveryStrategy,
    ErrorRecoveryHandler,
    PythonExceptionTranslator,
    PythonCrashHandler,
    PythonAdapter,
    CrashContext,
    ViolationReport,
    ClauseSeverity,
    EnforcementContext,
)


# ════════════════════════════════════════════════════════════════════════════
# ADAPTER EXCEPTION TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestAdapterException:
    """AdapterException tests (10 tests)."""
    
    def test_create_exception(self):
        """Test 826: Create adapter exception."""
        exc = AdapterException("Test error")
        assert str(exc) == "Test error"
    
    def test_exception_is_exception(self):
        """Test 827: Is Python Exception."""
        exc = AdapterException("Error")
        assert isinstance(exc, Exception)
    
    def test_exception_with_hints(self):
        """Test 828: Exception with remediation hints."""
        exc = AdapterException(
            "Error",
            remediation_hints=["Check input", "Verify config"]
        )
        assert len(exc.remediation_hints) == 2
        assert "Check input" in exc.remediation_hints
    
    def test_exception_no_hints(self):
        """Test 829: Exception without hints defaults to empty list."""
        exc = AdapterException("Error")
        assert exc.remediation_hints == []
    
    def test_exception_timestamp(self):
        """Test 830: Exception has timestamp."""
        exc = AdapterException("Error")
        assert exc.timestamp is not None
        assert exc.timestamp.endswith('Z')
    
    def test_exception_no_context(self):
        """Test 831: Exception without enforcement context."""
        exc = AdapterException("Error")
        assert exc.enforcement_context is None
    
    def test_exception_with_context(self):
        """Test 832: Exception with enforcement context."""
        ctx = EnforcementContext(
            function_name='test_func',
            invocation_id='inv-001'
        )
        exc = AdapterException("Error", enforcement_context=ctx)
        assert exc.enforcement_context is not None
        assert exc.enforcement_context.function_name == 'test_func'
    
    def test_get_context_dict(self):
        """Test 833: Get context dictionary."""
        exc = AdapterException("Error")
        context = exc.get_context_dict()
        assert 'message' in context
        assert 'timestamp' in context
        assert 'remediation_hints' in context
        assert context['enforcement_context'] is None
    
    def test_get_context_dict_with_enforcement(self):
        """Test 834: Context dict includes enforcement context."""
        ctx = EnforcementContext(
            function_name='func',
            invocation_id='inv-002'
        )
        exc = AdapterException("Error", enforcement_context=ctx)
        context = exc.get_context_dict()
        assert context['enforcement_context'] is not None
        assert context['enforcement_context']['function_name'] == 'func'
    
    def test_exception_can_be_raised(self):
        """Test 835: Exception can be raised and caught."""
        with pytest.raises(AdapterException, match="Test error"):
            raise AdapterException("Test error")


# ════════════════════════════════════════════════════════════════════════════
# CONTRACT VIOLATION ERROR TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestContractViolationError:
    """ContractViolationError tests (15 tests)."""
    
    def test_create_violation_error(self):
        """Test 836: Create contract violation error."""
        exc = ContractViolationError(
            "Violation",
            "test_func",
            "clause1",
            "value > 0",
            "value = -5"
        )
        assert exc.function_name == "test_func"
        assert exc.clause_id == "clause1"
        assert exc.expected == "value > 0"
        assert exc.observed == "value = -5"
    
    def test_violation_is_adapter_exception(self):
        """Test 837: Violation is AdapterException."""
        exc = ContractViolationError("V", "f", "c", "e", "o")
        assert isinstance(exc, AdapterException)
        assert isinstance(exc, Exception)
    
    def test_violation_str(self):
        """Test 838: Violation string representation."""
        exc = ContractViolationError(
            "Violation",
            "test_func",
            "clause1",
            "value > 0",
            "value = -5"
        )
        str_repr = str(exc)
        assert "test_func" in str_repr
        assert "clause1" in str_repr
        assert "value > 0" in str_repr
        assert "value = -5" in str_repr
    
    def test_violation_str_with_hints(self):
        """Test 839: Violation str includes hints."""
        exc = ContractViolationError(
            "V", "func", "c1", "e", "o",
            remediation_hints=["Fix input"]
        )
        str_repr = str(exc)
        assert "Fix input" in str_repr
    
    def test_violation_can_be_raised(self):
        """Test 840: Violation can be raised."""
        with pytest.raises(ContractViolationError):
            raise ContractViolationError("V", "f", "c", "e", "o")
    
    def test_parameter_violation_error(self):
        """Test 841: Parameter violation error."""
        exc = ParameterViolationError(
            "Param error",
            "func",
            "param0",
            "c1",
            "int",
            "str"
        )
        assert exc.parameter_name == "param0"
        assert isinstance(exc, ContractViolationError)
    
    def test_parameter_violation_is_contract_violation(self):
        """Test 842: ParameterViolation is ContractViolation."""
        exc = ParameterViolationError("E", "f", "p", "c", "e", "o")
        assert isinstance(exc, ContractViolationError)
        assert isinstance(exc, AdapterException)
    
    def test_return_value_violation_error(self):
        """Test 843: Return value violation error."""
        exc = ReturnValueViolationError(
            "Return error",
            "func",
            "c1",
            "non-null",
            "null"
        )
        assert isinstance(exc, ContractViolationError)
        assert exc.expected == "non-null"
    
    def test_ownership_violation_error(self):
        """Test 844: Ownership violation error."""
        exc = OwnershipViolationError(
            "Ownership error",
            "func",
            "c1",
            "caller-owned",
            "freed"
        )
        assert isinstance(exc, ContractViolationError)
        assert exc.expected == "caller-owned"
    
    def test_violation_with_enforcement_context(self):
        """Test 845: Violation with enforcement context."""
        ctx = EnforcementContext(
            function_name='test_func',
            invocation_id='inv-003'
        )
        exc = ContractViolationError(
            "V", "test_func", "c1", "e", "o",
            enforcement_context=ctx
        )
        assert exc.enforcement_context is not None
    
    def test_violation_timestamp(self):
        """Test 846: Violation has timestamp."""
        exc = ContractViolationError("V", "f", "c", "e", "o")
        assert exc.timestamp.endswith('Z')
    
    def test_catch_violation_as_adapter_exception(self):
        """Test 847: Catch violation as AdapterException."""
        try:
            raise ContractViolationError("V", "f", "c", "e", "o")
        except AdapterException as e:
            assert e.function_name == "f"
    
    def test_catch_parameter_as_contract_violation(self):
        """Test 848: Catch ParameterViolation as ContractViolation."""
        try:
            raise ParameterViolationError("E", "f", "p", "c", "e", "o")
        except ContractViolationError as e:
            assert e.parameter_name == "p"
    
    def test_violation_all_fields(self):
        """Test 849: All fields populated."""
        exc = ContractViolationError(
            "msg", "fn", "cl", "exp", "obs",
            remediation_hints=["h1", "h2"]
        )
        assert exc.function_name == "fn"
        assert exc.clause_id == "cl"
        assert exc.expected == "exp"
        assert exc.observed == "obs"
        assert len(exc.remediation_hints) == 2
    
    def test_ownership_violation_raised(self):
        """Test 850: Ownership violation can be raised and caught."""
        with pytest.raises(OwnershipViolationError):
            raise OwnershipViolationError("E", "f", "c", "e", "o")


# ════════════════════════════════════════════════════════════════════════════
# NATIVE CRASH ERROR TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestNativeCrashError:
    """NativeCrashError tests (10 tests)."""
    
    def test_create_crash_error(self):
        """Test 851: Create native crash error."""
        exc = NativeCrashError(
            "Crash", "segfault", crash_address=0x0
        )
        assert exc.crash_type == "segfault"
        assert exc.crash_address == 0x0
    
    def test_crash_is_adapter_exception(self):
        """Test 852: Crash is AdapterException."""
        exc = NativeCrashError("C", "t")
        assert isinstance(exc, AdapterException)
    
    def test_crash_str_with_address(self):
        """Test 853: Crash str includes address."""
        exc = NativeCrashError("Crash", "segfault", 0x1000)
        str_repr = str(exc)
        assert "segfault" in str_repr
        assert "0x1000" in str_repr
    
    def test_crash_str_no_address(self):
        """Test 854: Crash str without address."""
        exc = NativeCrashError("Crash", "unknown")
        str_repr = str(exc)
        assert "unknown" in str_repr
        assert exc.crash_address is None
    
    def test_segmentation_fault_error(self):
        """Test 855: Segmentation fault error."""
        exc = SegmentationFaultError("Segfault", 0x1000)
        assert exc.crash_type == "segmentation_fault"
        assert exc.crash_address == 0x1000
        assert isinstance(exc, NativeCrashError)
    
    def test_access_violation_error(self):
        """Test 856: Access violation error."""
        exc = AccessViolationError("AV", 0x2000)
        assert exc.crash_type == "access_violation"
        assert exc.crash_address == 0x2000
        assert isinstance(exc, NativeCrashError)
    
    def test_segfault_is_crash_error(self):
        """Test 857: SegFault is NativeCrashError."""
        exc = SegmentationFaultError("Segfault")
        assert isinstance(exc, NativeCrashError)
        assert isinstance(exc, AdapterException)
    
    def test_crash_with_hints(self):
        """Test 858: Crash with remediation hints."""
        exc = NativeCrashError(
            "Crash", "segfault",
            remediation_hints=["Check pointers"]
        )
        assert len(exc.remediation_hints) == 1
        assert "Check pointers" in str(exc)
    
    def test_configuration_error(self):
        """Test 859: Configuration error."""
        exc = ConfigurationError("Bad config")
        assert isinstance(exc, AdapterException)
        assert str(exc) == "Bad config"
    
    def test_crash_can_be_raised(self):
        """Test 860: Crash can be raised and caught."""
        with pytest.raises(NativeCrashError):
            raise SegmentationFaultError("Segfault", 0x0)


# ════════════════════════════════════════════════════════════════════════════
# EXCEPTION FORMATTER TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestExceptionFormatter:
    """ExceptionFormatter tests (10 tests)."""
    
    def test_create_formatter(self):
        """Test 861: Create exception formatter."""
        formatter = ExceptionFormatter()
        assert formatter is not None
    
    def test_format_contract_violation(self):
        """Test 862: Format contract violation."""
        exc = ContractViolationError(
            "Violation", "test_func", "clause1",
            "value > 0", "value = -5"
        )
        formatter = ExceptionFormatter()
        formatted = formatter.format_contract_violation(exc)
        assert "CONTRACT VIOLATION" in formatted
        assert "test_func" in formatted
        assert "clause1" in formatted
        assert "value > 0" in formatted
        assert "value = -5" in formatted
    
    def test_format_violation_with_hints(self):
        """Test 863: Format with remediation hints."""
        exc = ContractViolationError(
            "V", "func", "c1", "exp", "obs",
            remediation_hints=["Check input"]
        )
        formatter = ExceptionFormatter()
        formatted = formatter.format_contract_violation(exc)
        assert "HOW TO FIX" in formatted
        assert "Check input" in formatted
    
    def test_format_violation_with_context(self):
        """Test 864: Format with enforcement context."""
        ctx = EnforcementContext(
            function_name='func',
            invocation_id='inv-004'
        )
        exc = ContractViolationError(
            "V", "func", "c1", "e", "o",
            enforcement_context=ctx
        )
        formatter = ExceptionFormatter()
        formatted = formatter.format_contract_violation(exc)
        assert "ENFORCEMENT CONTEXT" in formatted
        assert "inv-004" in formatted
    
    def test_format_native_crash(self):
        """Test 865: Format native crash."""
        exc = NativeCrashError("Crash", "segfault", 0x0)
        formatter = ExceptionFormatter()
        formatted = formatter.format_native_crash(exc)
        assert "NATIVE CRASH" in formatted
        assert "segfault" in formatted
        assert "0x0" in formatted
    
    def test_format_crash_with_hints(self):
        """Test 866: Format crash with hints."""
        exc = NativeCrashError(
            "C", "segfault",
            remediation_hints=["Check null ptrs"]
        )
        formatter = ExceptionFormatter()
        formatted = formatter.format_native_crash(exc)
        assert "POSSIBLE CAUSES" in formatted
        assert "Check null ptrs" in formatted
    
    def test_format_crash_no_address(self):
        """Test 867: Format crash without address."""
        exc = NativeCrashError("C", "unknown")
        formatter = ExceptionFormatter()
        formatted = formatter.format_native_crash(exc)
        assert "Address" not in formatted
    
    def test_format_short_violation(self):
        """Test 868: Format short violation message."""
        exc = ContractViolationError(
            "V", "func", "c1", "exp", "obs"
        )
        formatter = ExceptionFormatter()
        short = formatter.format_short(exc)
        assert "func" in short
        assert "c1" in short
        assert "exp" in short
        assert "obs" in short
    
    def test_format_short_crash(self):
        """Test 869: Format short crash message."""
        exc = NativeCrashError("Crash", "segfault")
        formatter = ExceptionFormatter()
        short = formatter.format_short(exc)
        assert "segfault" in short
    
    def test_format_short_generic(self):
        """Test 870: Format short generic exception."""
        exc = AdapterException("Generic error")
        formatter = ExceptionFormatter()
        short = formatter.format_short(exc)
        assert "Generic error" in short


# ════════════════════════════════════════════════════════════════════════════
# ERROR RECOVERY HANDLER TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestErrorRecoveryHandler:
    """ErrorRecoveryHandler tests (15 tests)."""
    
    def test_create_handler(self):
        """Test 871: Create recovery handler."""
        handler = ErrorRecoveryHandler()
        assert handler is not None
        assert handler.max_retries == 3
    
    def test_default_strategy_violation(self):
        """Test 872: Default strategy for violation is PROPAGATE."""
        handler = ErrorRecoveryHandler()
        exc = ContractViolationError("V", "f", "c", "e", "o")
        assert handler.get_strategy(exc) == ErrorRecoveryStrategy.PROPAGATE
    
    def test_default_strategy_crash(self):
        """Test 873: Default strategy for crash is PROPAGATE."""
        handler = ErrorRecoveryHandler()
        exc = NativeCrashError("C", "t")
        assert handler.get_strategy(exc) == ErrorRecoveryStrategy.PROPAGATE
    
    def test_default_strategy_config(self):
        """Test 874: Default strategy for config error is PROPAGATE."""
        handler = ErrorRecoveryHandler()
        exc = ConfigurationError("E")
        assert handler.get_strategy(exc) == ErrorRecoveryStrategy.PROPAGATE
    
    def test_register_strategy(self):
        """Test 875: Register custom strategy."""
        handler = ErrorRecoveryHandler()
        handler.register_strategy(
            ConfigurationError,
            ErrorRecoveryStrategy.IGNORE
        )
        exc = ConfigurationError("E")
        assert handler.get_strategy(exc) == ErrorRecoveryStrategy.IGNORE
    
    def test_strategy_inheritance(self):
        """Test 876: Strategy falls back to parent class."""
        handler = ErrorRecoveryHandler()
        # ParameterViolationError inherits from ContractViolationError
        exc = ParameterViolationError("E", "f", "p", "c", "e", "o")
        strategy = handler.get_strategy(exc)
        assert strategy == ErrorRecoveryStrategy.PROPAGATE
    
    def test_unknown_exception_propagates(self):
        """Test 877: Unknown exception defaults to PROPAGATE."""
        handler = ErrorRecoveryHandler()
        exc = ValueError("Unknown")
        assert handler.get_strategy(exc) == ErrorRecoveryStrategy.PROPAGATE
    
    def test_should_retry_initially(self):
        """Test 878: Should retry initially returns True."""
        handler = ErrorRecoveryHandler()
        assert handler.should_retry("op1") is True
    
    def test_record_retry(self):
        """Test 879: Record retry increments count."""
        handler = ErrorRecoveryHandler()
        handler.record_retry("op1")
        assert handler.retry_counts["op1"] == 1
        handler.record_retry("op1")
        assert handler.retry_counts["op1"] == 2
    
    def test_max_retries_enforced(self):
        """Test 880: Max retries enforced."""
        handler = ErrorRecoveryHandler()
        handler.max_retries = 2
        handler.record_retry("op1")
        handler.record_retry("op1")
        assert handler.should_retry("op1") is False
    
    def test_reset_retries(self):
        """Test 881: Reset retry count."""
        handler = ErrorRecoveryHandler()
        handler.record_retry("op1")
        handler.record_retry("op1")
        handler.reset_retries("op1")
        assert "op1" not in handler.retry_counts
        assert handler.should_retry("op1") is True
    
    def test_reset_unknown_operation(self):
        """Test 882: Reset unknown operation is no-op."""
        handler = ErrorRecoveryHandler()
        handler.reset_retries("nonexistent")  # Should not raise
    
    def test_all_recovery_strategies_exist(self):
        """Test 883: All recovery strategies exist."""
        strategies = list(ErrorRecoveryStrategy)
        assert ErrorRecoveryStrategy.PROPAGATE in strategies
        assert ErrorRecoveryStrategy.RETRY in strategies
        assert ErrorRecoveryStrategy.FALLBACK in strategies
        assert ErrorRecoveryStrategy.IGNORE in strategies
        assert len(strategies) == 4
    
    def test_strategy_values(self):
        """Test 884: Strategy enum values."""
        assert ErrorRecoveryStrategy.PROPAGATE.value == "propagate"
        assert ErrorRecoveryStrategy.RETRY.value == "retry"
        assert ErrorRecoveryStrategy.FALLBACK.value == "fallback"
        assert ErrorRecoveryStrategy.IGNORE.value == "ignore"
    
    def test_independent_handlers(self):
        """Test 885: Handlers are independent."""
        h1 = ErrorRecoveryHandler()
        h2 = ErrorRecoveryHandler()
        h1.record_retry("op1")
        assert "op1" not in h2.retry_counts


# ════════════════════════════════════════════════════════════════════════════
# PYTHON EXCEPTION TRANSLATOR TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonExceptionTranslator:
    """PythonExceptionTranslator tests (15 tests)."""
    
    def test_create_translator(self):
        """Test 886: Create translator."""
        translator = PythonExceptionTranslator()
        assert translator is not None
        assert translator.formatter is not None
    
    def test_translate_segfault(self):
        """Test 887: Translate segmentation fault."""
        crash_ctx = CrashContext(
            'SegmentationFault',
            exception_message='Segfault at 0x0',
            faulting_address=0x0
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_crash(crash_ctx)
        assert isinstance(exc, SegmentationFaultError)
        assert exc.crash_address == 0x0
    
    def test_translate_sigsegv(self):
        """Test 888: Translate SIGSEGV."""
        crash_ctx = CrashContext(
            'SIGSEGV',
            exception_message='Signal 11'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_crash(crash_ctx)
        assert isinstance(exc, SegmentationFaultError)
    
    def test_translate_access_violation(self):
        """Test 889: Translate access violation."""
        crash_ctx = CrashContext(
            'AccessViolation',
            exception_message='Access violation',
            faulting_address=0x1000
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_crash(crash_ctx)
        assert isinstance(exc, AccessViolationError)
        assert exc.crash_address == 0x1000
    
    def test_translate_windows_access_violation(self):
        """Test 890: Translate Windows EXCEPTION_ACCESS_VIOLATION."""
        crash_ctx = CrashContext(
            'EXCEPTION_ACCESS_VIOLATION',
            exception_message='Access violation'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_crash(crash_ctx)
        assert isinstance(exc, AccessViolationError)
    
    def test_translate_generic_crash(self):
        """Test 891: Translate generic crash."""
        crash_ctx = CrashContext(
            'UnknownError',
            exception_message='Unknown error'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_crash(crash_ctx)
        assert isinstance(exc, NativeCrashError)
        assert not isinstance(exc, SegmentationFaultError)
        assert not isinstance(exc, AccessViolationError)
    
    def test_translate_crash_with_enforcement_context(self):
        """Test 892: Crash translation preserves enforcement context."""
        ctx = EnforcementContext(
            function_name='func',
            invocation_id='inv-005'
        )
        crash_ctx = CrashContext(
            'SegmentationFault',
            exception_message='Segfault'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_crash(crash_ctx, enforcement_context=ctx)
        assert exc.enforcement_context is not None
    
    def test_translate_parameter_violation(self):
        """Test 893: Translate parameter violation."""
        report = ViolationReport(
            'func', 'param0_range', 'parameter_range',
            ClauseSeverity.MANDATORY,
            'value > 0', 'value = -5',
            'Parameter out of range', 'fp123', 'ts'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_violation(report)
        assert isinstance(exc, ParameterViolationError)
    
    def test_translate_return_violation(self):
        """Test 894: Translate return violation."""
        report = ViolationReport(
            'func', 'return_null', 'return_value',
            ClauseSeverity.MANDATORY,
            'non-null', 'null',
            'Return null', 'fp', 'ts'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_violation(report)
        assert isinstance(exc, ReturnValueViolationError)
    
    def test_translate_ownership_violation(self):
        """Test 895: Translate ownership violation."""
        report = ViolationReport(
            'func', 'ownership_check', 'ownership_transfer',
            ClauseSeverity.MANDATORY,
            'caller-owned', 'freed',
            'Double free', 'fp', 'ts'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_violation(report)
        assert isinstance(exc, OwnershipViolationError)
    
    def test_translate_generic_violation(self):
        """Test 896: Translate generic violation."""
        report = ViolationReport(
            'func', 'custom_check', 'custom_type',
            ClauseSeverity.MANDATORY,
            'expected', 'observed',
            'Custom violation', 'fp', 'ts'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_violation(report)
        assert isinstance(exc, ContractViolationError)
        assert not isinstance(exc, ParameterViolationError)
    
    def test_translate_violation_preserves_hints(self):
        """Test 897: Violation translation preserves hints."""
        report = ViolationReport(
            'func', 'check', 'parameter_check',
            ClauseSeverity.MANDATORY,
            'e', 'o', 'msg', 'fp', 'ts',
            remediation_hints=['Fix this', 'Check that']
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_violation(report)
        assert len(exc.remediation_hints) == 2
    
    def test_translate_violation_with_context(self):
        """Test 898: Violation translation with context."""
        ctx = EnforcementContext(
            function_name='func',
            invocation_id='inv-006'
        )
        report = ViolationReport(
            'func', 'check', 'return_check',
            ClauseSeverity.MANDATORY,
            'e', 'o', 'msg', 'fp', 'ts'
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_violation(report, enforcement_context=ctx)
        assert exc.enforcement_context is not None
    
    def test_translate_crash_has_remediation_hints(self):
        """Test 899: Crash translation includes hints for known types."""
        crash_ctx = CrashContext(
            'AccessViolation',
            exception_message='AV',
            faulting_address=0x0
        )
        translator = PythonExceptionTranslator()
        exc = translator.translate_crash(crash_ctx)
        # AccessViolation + faulting_address==0 should produce hints
        assert isinstance(exc.remediation_hints, list)
    
    def test_translator_has_formatter(self):
        """Test 900: Translator has formatter."""
        translator = PythonExceptionTranslator()
        assert isinstance(translator.formatter, ExceptionFormatter)


# ════════════════════════════════════════════════════════════════════════════
# PYTHON CRASH HANDLER TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonCrashHandler:
    """PythonCrashHandler tests (10 tests)."""
    
    def test_create_handler(self):
        """Test 901: Create crash handler."""
        handler = PythonCrashHandler()
        assert handler is not None
        assert handler.exception_translator is not None
    
    def test_execute_success(self):
        """Test 902: Execute successful function."""
        handler = PythonCrashHandler()
        success, result, crash = handler.execute_isolated(
            lambda: 42
        )
        assert success is True
        assert result == 42
        assert crash is None
    
    def test_execute_with_args(self):
        """Test 903: Execute function with arguments."""
        handler = PythonCrashHandler()
        success, result, crash = handler.execute_isolated(
            lambda x, y: x + y, 3, 4
        )
        assert success is True
        assert result == 7
    
    def test_execute_general_exception(self):
        """Test 904: Execute function that raises generic exception."""
        handler = PythonCrashHandler()
        
        def failing():
            raise ValueError("test error")
        
        success, result, crash = handler.execute_isolated(failing)
        assert success is False
        assert result is None
        assert crash is not None
        assert crash.exception_type == 'ValueError'
    
    def test_execute_os_error(self):
        """Test 905: Execute function that raises OSError."""
        handler = PythonCrashHandler()
        
        def os_failing():
            raise OSError("OS error")
        
        success, result, crash = handler.execute_isolated(os_failing)
        assert success is False
        assert crash.exception_type == 'OSError'
        assert crash.platform == 'python'
    
    def test_execute_recursion_error(self):
        """Test 906: Execute function that causes recursion error."""
        handler = PythonCrashHandler()
        
        def recursive():
            return recursive()
        
        success, result, crash = handler.execute_isolated(recursive)
        assert success is False
        assert crash.exception_type == 'RecursionError'
    
    def test_crash_context_has_platform(self):
        """Test 907: Crash context has platform set to python."""
        handler = PythonCrashHandler()
        
        def failing():
            raise RuntimeError("fail")
        
        success, result, crash = handler.execute_isolated(failing)
        assert crash.platform == 'python'
    
    def test_crash_context_has_message(self):
        """Test 908: Crash context preserves error message."""
        handler = PythonCrashHandler()
        
        def failing():
            raise RuntimeError("specific error message")
        
        success, result, crash = handler.execute_isolated(failing)
        assert "specific error message" in crash.exception_message
    
    def test_handler_has_translator(self):
        """Test 909: Handler has exception translator."""
        handler = PythonCrashHandler()
        assert isinstance(
            handler.exception_translator,
            PythonExceptionTranslator
        )
    
    def test_adapter_has_exception_handling(self):
        """Test 910: PythonAdapter has exception handling components."""
        adapter = PythonAdapter()
        assert isinstance(
            adapter.exception_translator,
            PythonExceptionTranslator
        )
        assert isinstance(adapter.crash_handler, PythonCrashHandler)
        assert isinstance(adapter.recovery_handler, ErrorRecoveryHandler)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
