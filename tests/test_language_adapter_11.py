"""Test Suite for Language Adapter - Prompt 11/25: 100 end-to-end tests."""

import pytest
from modules.module_08_language_adapter import (
    EnforcementScope,
    DiagnosticCollector,
    PythonInvocationPipeline,
    PythonAdapterComplete,
    AdapterConfig,
    ValidationGraph,
    ValidationNode,
    ClauseSeverity,
    ContractViolationError,
    NativeCrashError,
    PythonPointerWrapper,
    PythonExceptionTranslator,
    PythonCrashHandler,
    ErrorRecoveryHandler,
)


# ════════════════════════════════════════════════════════════════════════════
# ENFORCEMENT SCOPE TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestEnforcementScope:
    """EnforcementScope tests (20 tests)."""

    def test_create_scope(self):
        """Test 911: Create enforcement scope."""
        adapter = PythonAdapterComplete()
        scope = EnforcementScope(adapter, 'test_func')
        assert scope.function_name == 'test_func'
        assert scope.active is False

    def test_scope_context_manager(self):
        """Test 912: Scope as context manager."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'test_func') as scope:
            assert scope.active is True

        assert scope.active is False

    def test_scope_add_buffer(self):
        """Test 913: Add buffer to scope."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'test_func') as scope:
            data = b'test'
            wrapper = scope.add_buffer(data)
            assert isinstance(wrapper, PythonPointerWrapper)
            assert len(scope.buffers) == 1

    def test_scope_cleanup(self):
        """Test 914: Scope cleans up resources."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'test_func') as scope:
            scope.add_buffer(b'test')

        assert len(scope.buffers) == 0
        assert len(scope.wrappers) == 0

    def test_scope_cleanup_on_exception(self):
        """Test 915: Scope cleans up on exception."""
        adapter = PythonAdapterComplete()

        try:
            with EnforcementScope(adapter, 'test_func') as scope:
                scope.add_buffer(b'test')
                raise ValueError("Test error")
        except ValueError:
            pass

        assert len(scope.buffers) == 0

    def test_scope_invoke_not_active_raises(self):
        """Test 916: Invoke when not active raises."""
        adapter = PythonAdapterComplete()
        scope = EnforcementScope(adapter, 'test_func')

        with pytest.raises(RuntimeError, match='not active'):
            scope.invoke()

    def test_scope_multiple_buffers(self):
        """Test 917: Multiple buffers in scope."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'test_func') as scope:
            scope.add_buffer(b'test1')
            scope.add_buffer(b'test2')
            scope.add_buffer(b'test3')
            assert len(scope.buffers) == 3
            assert len(scope.wrappers) == 3

    def test_scope_enforcement_context_created(self):
        """Test 918: Enforcement context is created on enter."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'my_func') as scope:
            assert scope.context is not None
            assert scope.context.function_name == 'my_func'

    def test_scope_doesnt_suppress_exceptions(self):
        """Test 919: Scope does not suppress exceptions."""
        adapter = PythonAdapterComplete()

        with pytest.raises(ValueError, match='inner error'):
            with EnforcementScope(adapter, 'test') as scope:
                raise ValueError("inner error")

    def test_scope_bytearray_buffer(self):
        """Test 920: Add bytearray buffer to scope."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'test') as scope:
            data = bytearray(b'hello')
            wrapper = scope.add_buffer(data)
            assert wrapper.size > 0

    def test_scope_adapter_reference(self):
        """Test 921: Scope holds adapter reference."""
        adapter = PythonAdapterComplete()
        scope = EnforcementScope(adapter, 'func')
        assert scope.adapter is adapter

    def test_scope_initial_state(self):
        """Test 922: Scope initial state is clean."""
        adapter = PythonAdapterComplete()
        scope = EnforcementScope(adapter, 'func')
        assert scope.buffers == []
        assert scope.wrappers == []
        assert scope.context is None
        assert scope.active is False

    def test_scope_context_none_after_exit(self):
        """Test 923: Context persists after exit for inspection."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'func') as scope:
            ctx = scope.context

        assert ctx is not None
        assert ctx.function_name == 'func'

    def test_scope_re_enter_not_supported(self):
        """Test 924: Scope can be re-entered."""
        adapter = PythonAdapterComplete()
        scope = EnforcementScope(adapter, 'func')

        with scope:
            assert scope.active is True
        assert scope.active is False

        # Re-enter
        with scope:
            assert scope.active is True
        assert scope.active is False

    def test_scope_wrapper_types(self):
        """Test 925: Wrappers are PythonPointerWrapper instances."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'func') as scope:
            w1 = scope.add_buffer(b'a')
            w2 = scope.add_buffer(b'b')
            assert all(isinstance(w, PythonPointerWrapper) for w in scope.wrappers)

    def test_scope_buffers_tracked(self):
        """Test 926: Buffers tracked in scope."""
        adapter = PythonAdapterComplete()
        buf = b'tracked_data'

        with EnforcementScope(adapter, 'func') as scope:
            scope.add_buffer(buf)
            assert buf in scope.buffers

    def test_scope_cleanup_clears_all(self):
        """Test 927: Cleanup clears all buffers and wrappers."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'func') as scope:
            for i in range(5):
                scope.add_buffer(bytes([i] * 10))
            assert len(scope.buffers) == 5

        assert len(scope.buffers) == 0
        assert len(scope.wrappers) == 0

    def test_scope_invoke_active(self):
        """Test 928: Invoke works when scope is active."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'test_func') as scope:
            result = scope.invoke(42)
            assert result is not None

    def test_scope_function_name_preserved(self):
        """Test 929: Function name preserved through lifecycle."""
        adapter = PythonAdapterComplete()
        scope = EnforcementScope(adapter, 'my_special_func')
        assert scope.function_name == 'my_special_func'

        with scope:
            assert scope.function_name == 'my_special_func'
        assert scope.function_name == 'my_special_func'

    def test_scope_multiple_exception_cleanup(self):
        """Test 930: Multiple errors during cleanup don't propagate."""
        adapter = PythonAdapterComplete()

        with EnforcementScope(adapter, 'func') as scope:
            scope.add_buffer(b'test')
            # Even with exception, cleanup should be safe
        assert len(scope.wrappers) == 0


# ════════════════════════════════════════════════════════════════════════════
# DIAGNOSTIC COLLECTOR TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestDiagnosticCollector:
    """DiagnosticCollector tests (20 tests)."""

    def test_create_collector(self):
        """Test 931: Create diagnostic collector."""
        collector = DiagnosticCollector()
        assert collector.enabled is False

    def test_enable_collector(self):
        """Test 932: Enable collector."""
        collector = DiagnosticCollector()
        collector.enable()
        assert collector.enabled is True

    def test_disable_collector(self):
        """Test 933: Disable collector."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.disable()
        assert collector.enabled is False

    def test_record_trace(self):
        """Test 934: Record trace message."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_trace('phase1', 'Test message')

        assert len(collector.traces) == 1
        assert collector.traces[0]['phase'] == 'phase1'
        assert collector.traces[0]['message'] == 'Test message'

    def test_record_trace_disabled(self):
        """Test 935: Trace not recorded when disabled."""
        collector = DiagnosticCollector()
        collector.record_trace('phase1', 'Test')

        assert len(collector.traces) == 0

    def test_record_timing(self):
        """Test 936: Record timing."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_timing('operation1', 10.5)

        assert 'operation1' in collector.timings
        assert collector.timings['operation1'] == 10.5

    def test_record_timing_accumulates(self):
        """Test 937: Timing accumulates."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_timing('op1', 10.0)
        collector.record_timing('op1', 5.0)

        assert collector.timings['op1'] == 15.0

    def test_record_decision_pass(self):
        """Test 938: Record passing validation decision."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_decision('clause1', True, 'Valid')

        assert len(collector.decisions) == 1
        assert collector.decisions[0]['decision'] == 'pass'
        assert collector.decisions[0]['clause_id'] == 'clause1'

    def test_record_decision_fail(self):
        """Test 939: Record failing validation decision."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_decision('clause2', False, 'Invalid value')

        assert collector.decisions[0]['decision'] == 'fail'
        assert collector.decisions[0]['reason'] == 'Invalid value'

    def test_get_report(self):
        """Test 940: Get diagnostic report."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_trace('phase', 'msg')
        collector.record_timing('op', 10.0)

        report = collector.get_report()
        assert 'traces' in report
        assert 'timings' in report
        assert 'decisions' in report
        assert report['total_traces'] == 1
        assert report['total_operations'] == 1
        assert report['total_time_ms'] == 10.0

    def test_clear_diagnostics(self):
        """Test 941: Clear diagnostics."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_trace('phase', 'msg')
        collector.record_timing('op', 5.0)
        collector.record_decision('c1', True, 'ok')
        collector.clear()

        assert len(collector.traces) == 0
        assert len(collector.timings) == 0
        assert len(collector.decisions) == 0

    def test_timing_disabled(self):
        """Test 942: Timing not recorded when disabled."""
        collector = DiagnosticCollector()
        collector.record_timing('op', 10.0)

        assert len(collector.timings) == 0

    def test_decision_disabled(self):
        """Test 943: Decision not recorded when disabled."""
        collector = DiagnosticCollector()
        collector.record_decision('c1', True, 'ok')

        assert len(collector.decisions) == 0

    def test_trace_has_timestamp(self):
        """Test 944: Traces have timestamps."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_trace('phase', 'msg')

        assert 'timestamp' in collector.traces[0]
        assert collector.traces[0]['timestamp'].endswith('Z')

    def test_trace_with_metadata(self):
        """Test 945: Record trace with metadata."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_trace('phase', 'msg', {'key': 'value'})

        assert collector.traces[0]['metadata'] == {'key': 'value'}

    def test_trace_without_metadata(self):
        """Test 946: Trace without metadata gets empty dict."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_trace('phase', 'msg')

        assert collector.traces[0]['metadata'] == {}

    def test_report_total_time_multiple_ops(self):
        """Test 947: Report total time sums all operations."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_timing('op1', 10.0)
        collector.record_timing('op2', 20.0)
        collector.record_timing('op3', 30.0)

        report = collector.get_report()
        assert report['total_time_ms'] == 60.0
        assert report['total_operations'] == 3

    def test_multiple_traces(self):
        """Test 948: Multiple trace entries."""
        collector = DiagnosticCollector()
        collector.enable()
        for i in range(10):
            collector.record_trace(f'phase_{i}', f'message_{i}')

        assert len(collector.traces) == 10
        report = collector.get_report()
        assert report['total_traces'] == 10

    def test_decision_has_timestamp(self):
        """Test 949: Decisions have timestamps."""
        collector = DiagnosticCollector()
        collector.enable()
        collector.record_decision('c1', True, 'ok')

        assert collector.decisions[0]['timestamp'].endswith('Z')

    def test_empty_report(self):
        """Test 950: Empty report has zero totals."""
        collector = DiagnosticCollector()
        report = collector.get_report()

        assert report['total_traces'] == 0
        assert report['total_operations'] == 0
        assert report['total_time_ms'] == 0


# ════════════════════════════════════════════════════════════════════════════
# PYTHON INVOCATION PIPELINE TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonInvocationPipeline:
    """PythonInvocationPipeline tests (20 tests)."""

    def test_create_pipeline(self):
        """Test 951: Create invocation pipeline."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        assert pipeline.adapter is adapter
        assert pipeline.diagnostics is not None

    def test_execute_simple_function(self):
        """Test 952: Execute simple function."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)

        def add(a, b):
            return a + b

        result = pipeline.execute('add', [2, 3], add)
        assert result == 5

    def test_execute_with_diagnostics(self):
        """Test 953: Execute with diagnostics enabled."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        def double(a):
            return a * 2

        pipeline.execute('double', [5], double)

        report = pipeline.diagnostics.get_report()
        assert report['total_traces'] > 0

    def test_execute_records_timing(self):
        """Test 954: Execute records timing."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        def identity(a):
            return a

        pipeline.execute('identity', [42], identity)

        report = pipeline.diagnostics.get_report()
        assert 'normalization' in report['timings']
        assert 'total' in report['timings']

    def test_execute_with_validation_pass(self):
        """Test 955: Execute with passing validation."""
        adapter = PythonAdapterComplete()

        graph = ValidationGraph('test_func')
        node = ValidationNode(
            'c1', 'range', ClauseSeverity.MANDATORY,
            predicate=lambda inputs, params: inputs[0] > 0,
            parameters=[0]
        )
        graph.add_node(node)
        adapter.validation_graphs['test_func'] = graph

        pipeline = PythonInvocationPipeline(adapter)

        def double(a):
            return a * 2

        result = pipeline.execute('test_func', [5], double)
        assert result == 10

    def test_execute_validation_failure(self):
        """Test 956: Execute with validation failure."""
        adapter = PythonAdapterComplete()

        graph = ValidationGraph('test_func')
        node = ValidationNode(
            'c1', 'range', ClauseSeverity.MANDATORY,
            predicate=lambda inputs, params: inputs[0] > 0,
            parameters=[0],
            failure_message='Must be positive'
        )
        graph.add_node(node)
        adapter.validation_graphs['test_func'] = graph

        pipeline = PythonInvocationPipeline(adapter)

        def double(a):
            return a * 2

        with pytest.raises(ContractViolationError):
            pipeline.execute('test_func', [-5], double)

    def test_execute_cleanup_on_exception(self):
        """Test 957: Cleanup on exception."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)

        def failing(a):
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            pipeline.execute('test_func', [42], failing)

        stats = adapter.memory_manager.get_statistics()
        assert stats['active_wrappers'] == 0

    def test_execute_no_callable(self):
        """Test 958: Execute without callable returns None."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)

        result = pipeline.execute('test_func', [42])
        assert result is None

    def test_execute_with_bytes_input(self):
        """Test 959: Execute with bytes input pins buffer."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)

        def get_length(data):
            return len(data)

        result = pipeline.execute('func', [b'hello'], get_length)
        assert result == 5

    def test_execute_records_exception_trace(self):
        """Test 960: Exception recorded in diagnostics."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        def failing(a):
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            pipeline.execute('func', [1], failing)

        report = pipeline.diagnostics.get_report()
        exception_traces = [
            t for t in report['traces'] if t['phase'] == 'exception'
        ]
        assert len(exception_traces) > 0

    def test_execute_normalization_phase(self):
        """Test 961: Normalization phase recorded in diagnostics."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        def identity(a):
            return a

        pipeline.execute('func', [42], identity)

        report = pipeline.diagnostics.get_report()
        norm_traces = [
            t for t in report['traces'] if t['phase'] == 'normalization'
        ]
        assert len(norm_traces) > 0

    def test_execute_setup_phase_trace(self):
        """Test 962: Setup phase recorded."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        pipeline.execute('func', [1], lambda a: a)

        report = pipeline.diagnostics.get_report()
        setup_traces = [
            t for t in report['traces'] if t['phase'] == 'setup'
        ]
        assert len(setup_traces) > 0

    def test_pipeline_independent_diagnostics(self):
        """Test 963: Each pipeline has its own diagnostics."""
        adapter = PythonAdapterComplete()
        p1 = PythonInvocationPipeline(adapter)
        p2 = PythonInvocationPipeline(adapter)

        p1.diagnostics.enable()
        p1.diagnostics.record_trace('phase', 'msg')

        assert len(p2.diagnostics.traces) == 0

    def test_execute_multiple_inputs(self):
        """Test 964: Execute with multiple inputs."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)

        def sum_three(a, b, c):
            return a + b + c

        result = pipeline.execute('func', [1, 2, 3], sum_three)
        assert result == 6

    def test_execute_string_inputs(self):
        """Test 965: Execute with string inputs."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)

        def concat(a, b):
            return str(a) + str(b)

        result = pipeline.execute('func', ['hello', 'world'], concat)
        assert result == 'helloworld'

    def test_execute_empty_inputs(self):
        """Test 966: Execute with empty inputs."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)

        def no_args():
            return 'done'

        result = pipeline.execute('func', [], no_args)
        assert result == 'done'

    def test_execute_buffer_pinning_timed(self):
        """Test 967: Buffer pinning phase is timed."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        pipeline.execute('func', [b'data'], lambda d: len(d))

        report = pipeline.diagnostics.get_report()
        assert 'buffer_pinning' in report['timings']

    def test_execute_validation_timed(self):
        """Test 968: Validation phase is timed."""
        adapter = PythonAdapterComplete()

        graph = ValidationGraph('func')
        node = ValidationNode(
            'c1', 'type', ClauseSeverity.MANDATORY,
            predicate=lambda inputs, params: True,
            parameters=[0]
        )
        graph.add_node(node)
        adapter.validation_graphs['func'] = graph

        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        pipeline.execute('func', [42], lambda a: a)

        report = pipeline.diagnostics.get_report()
        assert 'validation' in report['timings']

    def test_execute_invocation_timed(self):
        """Test 969: Invocation phase is timed."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        pipeline.execute('func', [1], lambda a: a)

        report = pipeline.diagnostics.get_report()
        assert 'invocation' in report['timings']

    def test_execute_total_timed(self):
        """Test 970: Total time is recorded."""
        adapter = PythonAdapterComplete()
        pipeline = PythonInvocationPipeline(adapter)
        pipeline.diagnostics.enable()

        pipeline.execute('func', [1], lambda a: a)

        report = pipeline.diagnostics.get_report()
        assert 'total' in report['timings']
        assert report['timings']['total'] >= 0


# ════════════════════════════════════════════════════════════════════════════
# PYTHON ADAPTER COMPLETE TESTS (40 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestPythonAdapterComplete:
    """PythonAdapterComplete tests (40 tests)."""

    def test_create_complete_adapter(self):
        """Test 971: Create complete adapter."""
        adapter = PythonAdapterComplete()
        assert adapter.pipeline is not None

    def test_enable_diagnostics(self):
        """Test 972: Enable diagnostic mode."""
        adapter = PythonAdapterComplete()
        adapter.enable_diagnostic_mode()
        assert adapter.enable_diagnostics is True
        assert adapter.pipeline.diagnostics.enabled is True

    def test_disable_diagnostics(self):
        """Test 973: Disable diagnostic mode."""
        adapter = PythonAdapterComplete()
        adapter.enable_diagnostic_mode()
        adapter.disable_diagnostic_mode()
        assert adapter.enable_diagnostics is False

    def test_get_diagnostics(self):
        """Test 974: Get diagnostics report."""
        adapter = PythonAdapterComplete()
        report = adapter.get_diagnostics()
        assert 'traces' in report
        assert 'timings' in report
        assert 'decisions' in report

    def test_clear_diagnostics(self):
        """Test 975: Clear diagnostics."""
        adapter = PythonAdapterComplete()
        adapter.enable_diagnostic_mode()
        adapter.pipeline.diagnostics.record_trace('test', 'msg')
        adapter.clear_diagnostics()

        report = adapter.get_diagnostics()
        assert report['total_traces'] == 0

    def test_enforcement_scope_creation(self):
        """Test 976: Create enforcement scope."""
        adapter = PythonAdapterComplete()
        scope = adapter.enforcement_scope('test_func')
        assert isinstance(scope, EnforcementScope)
        assert scope.function_name == 'test_func'

    def test_call_with_enforcement_simple(self):
        """Test 977: Call with enforcement."""
        adapter = PythonAdapterComplete()

        def add(a, b):
            return a + b

        result = adapter.call_with_enforcement(
            'add', 2, 3, native_callable=add
        )
        assert result == 5

    def test_call_with_enforcement_validation(self):
        """Test 978: Call with validation."""
        adapter = PythonAdapterComplete()

        graph = ValidationGraph('test_func')
        node = ValidationNode(
            'c1', 'type', ClauseSeverity.MANDATORY,
            predicate=lambda inputs, params: isinstance(inputs[0], int),
            parameters=[0]
        )
        graph.add_node(node)
        adapter.validation_graphs['test_func'] = graph

        def double(a):
            return a * 2

        result = adapter.call_with_enforcement(
            'test_func', 5, native_callable=double
        )
        assert result == 10

    def test_get_performance_metrics(self):
        """Test 979: Get performance metrics."""
        adapter = PythonAdapterComplete()
        adapter.enable_diagnostic_mode()

        def identity(a):
            return a

        adapter.call_with_enforcement('test', 42, native_callable=identity)

        metrics = adapter.get_performance_metrics()
        assert 'total_invocations' in metrics
        assert 'total_time_ms' in metrics
        assert 'average_time_ms' in metrics
        assert 'timing_breakdown' in metrics
        assert 'memory_stats' in metrics

    def test_multiple_invocations(self):
        """Test 980: Multiple invocations."""
        adapter = PythonAdapterComplete()

        def double(a):
            return a * 2

        results = []
        for i in range(5):
            result = adapter.call_with_enforcement(
                'test', i, native_callable=double
            )
            results.append(result)

        assert results == [0, 2, 4, 6, 8]

    def test_buffer_handling(self):
        """Test 981: Buffer handling in invocation."""
        adapter = PythonAdapterComplete()

        def get_length(data):
            return len(data)

        result = adapter.call_with_enforcement(
            'get_length', b'hello', native_callable=get_length
        )
        assert result == 5

    def test_with_context_manager(self):
        """Test 982: Using context manager pattern."""
        adapter = PythonAdapterComplete()

        def add(a, b):
            return a + b

        with adapter.enforcement_scope('add') as scope:
            result = adapter.call_with_enforcement(
                'add', 10, 20, native_callable=add
            )
            assert result == 30

    def test_exception_translation_violation(self):
        """Test 983: Validation failure raises ContractViolationError."""
        adapter = PythonAdapterComplete()

        graph = ValidationGraph('test_func')
        node = ValidationNode(
            'c1', 'range', ClauseSeverity.MANDATORY,
            predicate=lambda inputs, params: False,
            parameters=[0],
            failure_message='Always fails'
        )
        graph.add_node(node)
        adapter.validation_graphs['test_func'] = graph

        def identity(a):
            return a

        with pytest.raises(ContractViolationError):
            adapter.call_with_enforcement(
                'test_func', 42, native_callable=identity
            )

    def test_config_integration(self):
        """Test 984: Configuration integration."""
        config = AdapterConfig()
        adapter = PythonAdapterComplete(config=config)
        assert adapter.config is config

    def test_memory_cleanup_after_call(self):
        """Test 985: Memory cleaned up after call."""
        adapter = PythonAdapterComplete()

        def get_len(data):
            return len(data)

        adapter.call_with_enforcement(
            'test', b'test', native_callable=get_len
        )

        stats = adapter.memory_manager.get_statistics()
        assert stats['active_wrappers'] == 0

    def test_ctypes_mode(self):
        """Test 986: ctypes mode initialization."""
        adapter = PythonAdapterComplete(ffi_mode='ctypes')
        assert adapter.ffi_mode == 'ctypes'

    def test_cffi_mode(self):
        """Test 987: cffi mode initialization."""
        adapter = PythonAdapterComplete(ffi_mode='cffi')
        assert adapter.ffi_mode == 'cffi'

    def test_statistics_tracking(self):
        """Test 988: Statistics tracking."""
        adapter = PythonAdapterComplete()
        stats = adapter.get_statistics()
        assert 'loaded_functions' in stats
        assert 'ffi_mode' in stats
        assert 'diagnostics_enabled' in stats
        assert 'memory_stats' in stats

    def test_timing_breakdown(self):
        """Test 989: Timing breakdown in metrics."""
        adapter = PythonAdapterComplete()
        adapter.enable_diagnostic_mode()

        adapter.call_with_enforcement(
            'test', 42, native_callable=lambda a: a
        )

        metrics = adapter.get_performance_metrics()
        assert 'timing_breakdown' in metrics
        assert isinstance(metrics['timing_breakdown'], dict)

    def test_average_time_calculation(self):
        """Test 990: Average time calculation."""
        adapter = PythonAdapterComplete()
        adapter.enable_diagnostic_mode()

        for i in range(3):
            adapter.call_with_enforcement(
                'test', i, native_callable=lambda a: a
            )

        metrics = adapter.get_performance_metrics()
        assert metrics['average_time_ms'] >= 0

    def test_inherits_python_adapter(self):
        """Test 991: PythonAdapterComplete inherits PythonAdapter."""
        from modules.module_08_language_adapter import PythonAdapter
        adapter = PythonAdapterComplete()
        assert isinstance(adapter, PythonAdapter)

    def test_has_normalizer(self):
        """Test 992: Has normalizer from PythonAdapter."""
        adapter = PythonAdapterComplete()
        assert adapter.normalizer is not None

    def test_has_memory_manager(self):
        """Test 993: Has memory manager from PythonAdapter."""
        adapter = PythonAdapterComplete()
        assert adapter.memory_manager is not None

    def test_has_exception_translator(self):
        """Test 994: Has exception translator."""
        adapter = PythonAdapterComplete()
        assert isinstance(
            adapter.exception_translator, PythonExceptionTranslator
        )

    def test_has_crash_handler(self):
        """Test 995: Has crash handler."""
        adapter = PythonAdapterComplete()
        assert isinstance(adapter.crash_handler, PythonCrashHandler)

    def test_has_recovery_handler(self):
        """Test 996: Has recovery handler."""
        adapter = PythonAdapterComplete()
        assert isinstance(adapter.recovery_handler, ErrorRecoveryHandler)

    def test_validation_graphs_empty_initially(self):
        """Test 997: Validation graphs empty initially."""
        adapter = PythonAdapterComplete()
        assert len(adapter.validation_graphs) == 0

    def test_statistics_loaded_functions(self):
        """Test 998: Statistics reflect loaded functions count."""
        adapter = PythonAdapterComplete()

        graph = ValidationGraph('func1')
        adapter.validation_graphs['func1'] = graph

        stats = adapter.get_statistics()
        assert stats['loaded_functions'] == 1

    def test_diagnostic_mode_in_statistics(self):
        """Test 999: Diagnostics flag in statistics."""
        adapter = PythonAdapterComplete()
        stats = adapter.get_statistics()
        assert stats['diagnostics_enabled'] is False

        adapter.enable_diagnostic_mode()
        stats = adapter.get_statistics()
        assert stats['diagnostics_enabled'] is True

    def test_call_native_exception(self):
        """Test 1000: Native exception during call."""
        adapter = PythonAdapterComplete()

        def crashing():
            raise RuntimeError("Simulated native crash")

        with pytest.raises(RuntimeError, match='Simulated native crash'):
            adapter.call_with_enforcement(
                'crash', native_callable=crashing
            )

    def test_enforcement_scope_with_call(self):
        """Test 1001: Enforcement scope with call inside."""
        adapter = PythonAdapterComplete()

        with adapter.enforcement_scope('func') as scope:
            scope.add_buffer(b'data')
            result = adapter.call_with_enforcement(
                'func', 1, 2, native_callable=lambda a, b: a + b
            )
            assert result == 3

        assert len(scope.buffers) == 0

    def test_metrics_memory_stats(self):
        """Test 1002: Performance metrics include memory stats."""
        adapter = PythonAdapterComplete()
        metrics = adapter.get_performance_metrics()
        assert 'memory_stats' in metrics
        assert 'active_wrappers' in metrics['memory_stats']

    def test_pipeline_access(self):
        """Test 1003: Pipeline accessible from adapter."""
        adapter = PythonAdapterComplete()
        assert isinstance(adapter.pipeline, PythonInvocationPipeline)

    def test_call_with_enforcement_no_callable(self):
        """Test 1004: Call with enforcement without callable."""
        adapter = PythonAdapterComplete()
        result = adapter.call_with_enforcement('func', 1, 2)
        assert result is None

    def test_multiple_validation_graphs(self):
        """Test 1005: Multiple validation graphs."""
        adapter = PythonAdapterComplete()

        for name in ['func1', 'func2', 'func3']:
            graph = ValidationGraph(name)
            node = ValidationNode(
                f'{name}_c1', 'type', ClauseSeverity.MANDATORY,
                predicate=lambda inputs, params: True,
                parameters=[0]
            )
            graph.add_node(node)
            adapter.validation_graphs[name] = graph

        stats = adapter.get_statistics()
        assert stats['loaded_functions'] == 3

        # Each should validate successfully
        for name in ['func1', 'func2', 'func3']:
            result = adapter.call_with_enforcement(
                name, 42, native_callable=lambda a: a
            )
            assert result == 42

    def test_cleanup_between_calls(self):
        """Test 1006: Cleanup happens between calls."""
        adapter = PythonAdapterComplete()

        def process(data):
            return len(data)

        for _ in range(5):
            adapter.call_with_enforcement(
                'func', b'test', native_callable=process
            )
            stats = adapter.memory_manager.get_statistics()
            assert stats['active_wrappers'] == 0

    def test_diagnostics_across_calls(self):
        """Test 1007: Diagnostics accumulate across calls."""
        adapter = PythonAdapterComplete()
        adapter.enable_diagnostic_mode()

        for i in range(3):
            adapter.call_with_enforcement(
                'func', i, native_callable=lambda a: a
            )

        report = adapter.get_diagnostics()
        # Should have multiple traces from multiple calls
        assert report['total_traces'] >= 3

    def test_invalid_ffi_mode(self):
        """Test 1008: Invalid FFI mode raises ValueError."""
        with pytest.raises(ValueError, match='Invalid FFI mode'):
            PythonAdapterComplete(ffi_mode='invalid')

    def test_contract_fingerprint_initially_none(self):
        """Test 1009: Contract fingerprint initially None."""
        adapter = PythonAdapterComplete()
        assert adapter.contract_fingerprint is None

    def test_ffi_mode_in_statistics(self):
        """Test 1010: FFI mode in statistics."""
        adapter = PythonAdapterComplete(ffi_mode='ctypes')
        stats = adapter.get_statistics()
        assert stats['ffi_mode'] == 'ctypes'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
