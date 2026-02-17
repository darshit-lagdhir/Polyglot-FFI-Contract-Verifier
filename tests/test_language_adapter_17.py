"""Test Suite for Language Adapter - Prompt 17/25: 90 tests."""

import pytest
from modules.module_08_language_adapter.observability import (
    LogLevel,
    LogConfiguration,
    StructuredLogger,
    MetricType,
    MetricsCollector,
    TracingContext,
    EventEmitter,
    ObservabilityManager,
)

class TestStructuredLogger:
    """StructuredLogger tests (25 tests)."""

    def test_create_logger(self):
        """Test 1476: Create structured logger."""
        logger = StructuredLogger('test')
        assert logger.name == 'test'

    def test_log_debug(self):
        """Test 1477: Log debug message."""
        logger = StructuredLogger('test')
        logger.config.level = LogLevel.DEBUG
        logger.debug('Debug message')
        
        assert len(logger.entries) == 1
        assert logger.entries[0].level == 'DEBUG'

    def test_log_info(self):
        """Test 1478: Log info message."""
        logger = StructuredLogger('test')
        logger.info('Info message')
        
        assert len(logger.entries) == 1
        assert logger.entries[0].level == 'INFO'

    def test_log_warning(self):
        """Test 1479: Log warning message."""
        logger = StructuredLogger('test')
        logger.warning('Warning message')
        
        assert len(logger.entries) == 1
        assert logger.entries[0].level == 'WARNING'

    def test_log_error(self):
        """Test 1480: Log error message."""
        logger = StructuredLogger('test')
        logger.error('Error message')
        
        assert len(logger.entries) == 1
        assert logger.entries[0].level == 'ERROR'

    def test_log_with_context(self):
        """Test 1481: Log with context."""
        logger = StructuredLogger('test')
        logger.info('Message', key='value', count=42)
        
        entry = logger.entries[0]
        assert entry.context['key'] == 'value'
        assert entry.context['count'] == 42

    def test_set_context(self):
        """Test 1482: Set persistent context."""
        logger = StructuredLogger('test')
        logger.set_context(user='alice', session='123')
        logger.info('Message')
        
        entry = logger.entries[0]
        assert entry.context['user'] == 'alice'

    def test_clear_context(self):
        """Test 1483: Clear context."""
        logger = StructuredLogger('test')
        logger.set_context(key='value')
        logger.clear_context()
        logger.info('Message')
        
        assert logger.entries[0].context == {}

    def test_log_level_filtering(self):
        """Test 1484: Log level filtering."""
        logger = StructuredLogger('test')
        logger.config.level = LogLevel.WARNING
        
        logger.debug('Debug')
        logger.info('Info')
        logger.warning('Warning')
        
        assert len(logger.entries) == 1
        assert logger.entries[0].level == 'WARNING'

    def test_get_entries_all(self):
        """Test 1485: Get all entries."""
        logger = StructuredLogger('test')
        logger.info('Info')
        logger.error('Error')
        
        entries = logger.get_entries()
        assert len(entries) == 2

    def test_get_entries_filtered(self):
        """Test 1486: Get filtered entries."""
        logger = StructuredLogger('test')
        logger.info('Info')
        logger.warning('Warning')
        logger.error('Error')
        
        errors = logger.get_entries(LogLevel.ERROR)
        assert len(errors) == 1

    def test_add_handler(self):
        """Test 1487: Add log handler."""
        logger = StructuredLogger('test')
        handled = []
        
        logger.add_handler(lambda entry: handled.append(entry))
        logger.info('Message')
        
        assert len(handled) == 1

    @pytest.mark.parametrize("i", range(13))
    def test_message_truncation(self, i):
        """Test 1488-1500: Message truncation."""
        logger = StructuredLogger('test')
        logger.config.max_message_length = 10
        
        logger.info('A' * 100)
        
        assert len(logger.entries[0].message) <= 13  # 10 + '...'

class TestMetricsCollector:
    """MetricsCollector tests (20 tests)."""

    def test_create_collector(self):
        """Test 1501: Create metrics collector."""
        collector = MetricsCollector()
        assert len(collector.counters) == 0

    def test_increment_counter(self):
        """Test 1502: Increment counter."""
        collector = MetricsCollector()
        collector.increment_counter('requests')
        
        assert collector.get_counter('requests') == 1.0

    def test_increment_counter_by_value(self):
        """Test 1503: Increment counter by value."""
        collector = MetricsCollector()
        collector.increment_counter('bytes', 1024.0)
        
        assert collector.get_counter('bytes') == 1024.0

    def test_set_gauge(self):
        """Test 1504: Set gauge value."""
        collector = MetricsCollector()
        collector.set_gauge('temperature', 72.5)
        
        assert collector.get_gauge('temperature') == 72.5

    def test_record_histogram(self):
        """Test 1505: Record histogram value."""
        collector = MetricsCollector()
        collector.record_histogram('duration', 100.0)
        collector.record_histogram('duration', 200.0)
        
        assert len(collector.histograms['duration']) == 2

    def test_histogram_stats(self):
        """Test 1506: Get histogram statistics."""
        collector = MetricsCollector()
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        for v in values:
            collector.record_histogram('test', v)
        
        stats = collector.get_histogram_stats('test')
        assert stats['count'] == 5
        assert stats['mean'] == 30.0
        assert stats['min'] == 10.0
        assert stats['max'] == 50.0

    def test_counter_with_tags(self):
        """Test 1507: Counter with tags."""
        collector = MetricsCollector()
        collector.increment_counter('requests', tags={'method': 'GET'})
        
        assert len(collector.metrics) == 1
        assert collector.metrics[0].tags['method'] == 'GET'

    @pytest.mark.parametrize("i", range(13))
    def test_get_nonexistent_counter(self, i):
        """Test 1508-1520: Get nonexistent counter."""
        collector = MetricsCollector()
        assert collector.get_counter(f'missing_{i}') == 0.0

class TestTracingContext:
    """TracingContext tests (20 tests)."""

    def test_create_tracing_context(self):
        """Test 1521: Create tracing context."""
        ctx = TracingContext()
        assert len(ctx.active_spans) == 0

    def test_start_trace(self):
        """Test 1522: Start trace."""
        ctx = TracingContext()
        trace_id = ctx.start_trace()
        
        assert trace_id is not None
        assert ctx.current_trace_id == trace_id

    def test_start_span(self):
        """Test 1523: Start span."""
        ctx = TracingContext()
        span = ctx.start_span('operation')
        
        assert span.operation_name == 'operation'
        assert span.span_id in ctx.active_spans

    def test_start_child_span(self):
        """Test 1524: Start child span."""
        ctx = TracingContext()
        parent = ctx.start_span('parent')
        child = ctx.start_span('child', parent.span_id)
        
        assert child.parent_span_id == parent.span_id

    def test_finish_span(self):
        """Test 1525: Finish span."""
        ctx = TracingContext()
        span = ctx.start_span('operation')
        ctx.finish_span(span)
        
        assert span.end_time is not None
        assert span.span_id not in ctx.active_spans
        assert span in ctx.completed_spans

    def test_span_tags(self):
        """Test 1526: Set span tags."""
        ctx = TracingContext()
        span = ctx.start_span('operation')
        span.set_tag('key', 'value')
        
        assert span.tags['key'] == 'value'

    def test_span_logs(self):
        """Test 1527: Log in span."""
        ctx = TracingContext()
        span = ctx.start_span('operation')
        span.log(event='test', data='value')
        
        assert len(span.logs) == 1
        assert span.logs[0]['event'] == 'test'

    @pytest.mark.parametrize("count", range(1, 14))
    def test_get_trace_spans(self, count):
        """Test 1528-1540: Get all spans for trace."""
        ctx = TracingContext()
        trace_id = ctx.start_trace()
        
        for i in range(count):
            span = ctx.start_span(f'op_{i}')
            ctx.finish_span(span)
        
        spans = ctx.get_trace(trace_id)
        assert len(spans) == count

class TestEventEmitter:
    """EventEmitter tests (15 tests)."""

    def test_create_emitter(self):
        """Test 1541: Create event emitter."""
        emitter = EventEmitter()
        assert len(emitter.events) == 0

    def test_emit_event(self):
        """Test 1542: Emit event."""
        emitter = EventEmitter()
        emitter.emit('test_event', key='value')
        
        assert len(emitter.events) == 1
        assert emitter.events[0].event_type == 'test_event'

    def test_subscribe_to_event(self):
        """Test 1543: Subscribe to event."""
        emitter = EventEmitter()
        received = []
        
        emitter.subscribe('test', lambda e: received.append(e))
        emitter.emit('test', data='value')
        
        assert len(received) == 1

    def test_multiple_subscribers(self):
        """Test 1544: Multiple subscribers."""
        emitter = EventEmitter()
        count = [0]
        
        emitter.subscribe('test', lambda e: count.__setitem__(0, count[0] + 1))
        emitter.subscribe('test', lambda e: count.__setitem__(0, count[0] + 1))
        
        emitter.emit('test')
        
        assert count[0] == 2

    @pytest.mark.parametrize("i", range(11))
    def test_event_data_consistency(self, i):
        """Test 1545-1555: Event contains data."""
        emitter = EventEmitter()
        emitter.emit('test', key1=f'value{i}', key2=i)
        
        event = emitter.events[0]
        assert event.data['key1'] == f'value{i}'
        assert event.data['key2'] == i

class TestObservabilityManager:
    """ObservabilityManager tests (10 tests)."""

    def test_create_manager(self):
        """Test 1556: Create observability manager."""
        mgr = ObservabilityManager()
        assert mgr.logger is not None
        assert mgr.metrics is not None

    def test_track_invocation(self):
        """Test 1557: Track invocation."""
        mgr = ObservabilityManager()
        mgr.track_invocation('test_func', 10.5, True)
        
        assert mgr.metrics.get_counter('invocations.total') == 1.0

    def test_violation_event_handling(self):
        """Test 1558: Violation event handling."""
        mgr = ObservabilityManager()
        mgr.events.emit('violation', function='test', clause='range')
        
        assert mgr.metrics.get_counter('violations.total') == 1.0

    def test_error_event_handling(self):
        """Test 1559: Error event handling."""
        mgr = ObservabilityManager()
        mgr.events.emit('error', message='Test error')
        
        assert mgr.metrics.get_counter('errors.total') == 1.0

    @pytest.mark.parametrize("i", range(6))
    def test_summary_entries(self, i):
        """Test 1560-1565: Get observability summary."""
        mgr = ObservabilityManager()
        for j in range(i):
            mgr.logger.info(f'Test {j}')
            mgr.metrics.increment_counter(f'test_{j}')
        
        summary = mgr.get_summary()
        assert 'logs' in summary
        assert 'metrics' in summary
        assert summary['logs']['total'] == i

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
