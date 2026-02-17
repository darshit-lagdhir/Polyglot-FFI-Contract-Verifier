"""Logging and observability framework for Language Adapter."""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


# ════════════════════════════════════════════════════════════════════════════
# SECTION 93: LOG LEVELS AND CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

class LogLevel(Enum):
    """Logging levels."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogConfiguration:
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    format: str = 'json'  # 'json' or 'text'
    include_context: bool = True
    include_stack_trace: bool = True
    max_message_length: int = 10000


# ════════════════════════════════════════════════════════════════════════════
# SECTION 94: STRUCTURED LOGGER
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    logger: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'level': self.level,
            'logger': self.logger,
            'message': self.message,
            'context': self.context
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class StructuredLogger:
    """
    Structured logger with context support.
    
    Produces machine-parseable logs with rich context.
    """

    def __init__(
        self,
        name: str,
        config: Optional[LogConfiguration] = None
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            config: Logging configuration
        """
        self.name = name
        self.config = config or LogConfiguration()
        self.context: Dict[str, Any] = {}
        self.entries: List[LogEntry] = []
        self.handlers: List[Callable[[LogEntry], None]] = []

    def set_context(self, **kwargs) -> None:
        """
        Set context for all subsequent logs.
        
        Args:
            **kwargs: Context key-value pairs
        """
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear logging context."""
        self.context.clear()

    def add_handler(self, handler: Callable[[LogEntry], None]) -> None:
        """
        Add log handler.
        
        Args:
            handler: Handler function
        """
        self.handlers.append(handler)

    def _log(
        self,
        level: LogLevel,
        message: str,
        **context
    ) -> None:
        """
        Internal logging method.
        
        Args:
            level: Log level
            message: Log message
            **context: Additional context
        """
        if level.value < self.config.level.value:
            return
        
        # Truncate message if too long
        if len(message) > self.config.max_message_length:
            message = message[:self.config.max_message_length] + '...'
        
        # Merge context
        full_context = {**self.context, **context}
        
        # Create log entry
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            level=level.name,
            logger=self.name,
            message=message,
            context=full_context if self.config.include_context else {}
        )
        
        self.entries.append(entry)
        
        # Notify handlers
        for handler in self.handlers:
            try:
                handler(entry)
            except Exception:
                pass  # Don't let handler errors break logging

    def debug(self, message: str, **context) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **context)

    def info(self, message: str, **context) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, **context)

    def warning(self, message: str, **context) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **context)

    def error(self, message: str, **context) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, **context)

    def critical(self, message: str, **context) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **context)

    def get_entries(
        self,
        level: Optional[LogLevel] = None
    ) -> List[LogEntry]:
        """
        Get log entries, optionally filtered by level.
        
        Args:
            level: Minimum log level
            
        Returns:
            List of log entries
        """
        if level is None:
            return self.entries
        
        return [e for e in self.entries if LogLevel[e.level].value >= level.value]


# ════════════════════════════════════════════════════════════════════════════
# SECTION 95: METRICS COLLECTOR
# ════════════════════════════════════════════════════════════════════════════

class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    """Metric data point."""
    name: str
    type: MetricType
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.type.value,
            'value': self.value,
            'tags': self.tags,
            'timestamp': self.timestamp
        }


class MetricsCollector:
    """
    Collects and aggregates metrics.
    
    Supports counters, gauges, and histograms.
    """

    def __init__(self):
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.metrics: List[Metric] = []

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment counter.
        
        Args:
            name: Counter name
            value: Increment value
            tags: Optional tags
        """
        if name not in self.counters:
            self.counters[name] = 0.0
        
        self.counters[name] += value
        
        metric = Metric(name, MetricType.COUNTER, self.counters[name], tags or {})
        self.metrics.append(metric)

    def set_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set gauge value.
        
        Args:
            name: Gauge name
            value: Gauge value
            tags: Optional tags
        """
        self.gauges[name] = value
        
        metric = Metric(name, MetricType.GAUGE, value, tags or {})
        self.metrics.append(metric)

    def record_histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record histogram value.
        
        Args:
            name: Histogram name
            value: Value to record
            tags: Optional tags
        """
        if name not in self.histograms:
            self.histograms[name] = []
        
        self.histograms[name].append(value)
        
        metric = Metric(name, MetricType.HISTOGRAM, value, tags or {})
        self.metrics.append(metric)

    def get_counter(self, name: str) -> float:
        """Get counter value."""
        return self.counters.get(name, 0.0)

    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self.gauges.get(name, 0.0)

    def get_histogram_stats(
        self,
        name: str
    ) -> Dict[str, float]:
        """
        Get histogram statistics.
        
        Args:
            name: Histogram name
            
        Returns:
            Statistics dictionary
        """
        values = self.histograms.get(name, [])
        
        if not values:
            return {'count': 0}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            'count': count,
            'min': min(sorted_values),
            'max': max(sorted_values),
            'mean': sum(sorted_values) / count,
            'p50': sorted_values[count // 2],
            'p95': sorted_values[int(count * 0.95)],
            'p99': sorted_values[int(count * 0.99)] if count > 0 else sorted_values[0]
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 96: TRACING CONTEXT
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Span:
    """Distributed tracing span."""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: str
    end_time: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self) -> None:
        """Finish span."""
        self.end_time = datetime.utcnow().isoformat() + 'Z'

    def set_tag(self, key: str, value: Any) -> None:
        """Set span tag."""
        self.tags[key] = value

    def log(self, **fields) -> None:
        """Log event in span."""
        self.logs.append({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            **fields
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'span_id': self.span_id,
            'trace_id': self.trace_id,
            'parent_span_id': self.parent_span_id,
            'operation_name': self.operation_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'tags': self.tags,
            'logs': self.logs
        }


class TracingContext:
    """
    Distributed tracing context.
    
    Manages trace and span lifecycle.
    """

    def __init__(self):
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: List[Span] = []
        self.current_trace_id: Optional[str] = None

    def start_trace(self) -> str:
        """
        Start new trace.
        
        Returns:
            Trace ID
        """
        self.current_trace_id = str(uuid.uuid4())
        return self.current_trace_id

    def start_span(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None
    ) -> Span:
        """
        Start new span.
        
        Args:
            operation_name: Operation name
            parent_span_id: Parent span ID
            
        Returns:
            New span
        """
        if self.current_trace_id is None:
            self.start_trace()
        
        span = Span(
            span_id=str(uuid.uuid4()),
            trace_id=self.current_trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.utcnow().isoformat() + 'Z'
        )
        
        self.active_spans[span.span_id] = span
        return span

    def finish_span(self, span: Span) -> None:
        """
        Finish span.
        
        Args:
            span: Span to finish
        """
        span.finish()
        
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]
        
        self.completed_spans.append(span)

    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for trace."""
        return [s for s in self.completed_spans if s.trace_id == trace_id]


# ════════════════════════════════════════════════════════════════════════════
# SECTION 97: EVENT EMITTER
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Event:
    """Observability event."""
    event_type: str
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event_type': self.event_type,
            'timestamp': self.timestamp,
            'data': self.data
        }


class EventEmitter:
    """
    Event streaming framework.
    
    Emits events for real-time monitoring.
    """

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.events: List[Event] = []

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to event type.
        
        Args:
            event_type: Event type to subscribe to
            callback: Callback function
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)

    def emit(
        self,
        event_type: str,
        **data
    ) -> None:
        """
        Emit event.
        
        Args:
            event_type: Event type
            **data: Event data
        """
        event = Event(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            data=data
        )
        
        self.events.append(event)
        
        # Notify subscribers
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception:
                pass  # Don't let subscriber errors break emission


# ════════════════════════════════════════════════════════════════════════════
# SECTION 98: OBSERVABILITY MANAGER
# ════════════════════════════════════════════════════════════════════════════

class ObservabilityManager:
    """
    Unified observability management.
    
    Coordinates logging, metrics, tracing, and events.
    """

    def __init__(self, adapter_name: str = 'adapter'):
        self.logger = StructuredLogger(adapter_name)
        self.metrics = MetricsCollector()
        self.tracing = TracingContext()
        self.events = EventEmitter()
        
        # Set up default event handlers
        self.events.subscribe('violation', self._on_violation)
        self.events.subscribe('error', self._on_error)

    def _on_violation(self, event: Event) -> None:
        """Handle violation event."""
        # Avoid 'message' clash with logger.warning parameter
        msg = event.data.get('message', 'Contract violation')
        ctx = {k: v for k, v in event.data.items() if k != 'message'}
        self.logger.warning(msg, **ctx)
        self.metrics.increment_counter('violations.total')

    def _on_error(self, event: Event) -> None:
        """Handle error event."""
        # Avoid 'message' clash with logger.error parameter
        msg = event.data.get('message', 'Error occurred')
        ctx = {k: v for k, v in event.data.items() if k != 'message'}
        self.logger.error(msg, **ctx)
        self.metrics.increment_counter('errors.total')

    def track_invocation(
        self,
        function_name: str,
        duration_ms: float,
        success: bool
    ) -> None:
        """
        Track function invocation.
        
        Args:
            function_name: Function name
            duration_ms: Duration in milliseconds
            success: Whether invocation succeeded
        """
        self.metrics.increment_counter('invocations.total')
        self.metrics.record_histogram('invocations.duration_ms', duration_ms)
        
        if success:
            self.metrics.increment_counter('invocations.success')
        else:
            self.metrics.increment_counter('invocations.failure')
        
        self.logger.info(
            "Invocation completed",
            function=function_name,
            duration_ms=duration_ms,
            success=success
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get observability summary."""
        return {
            'logs': {
                'total': len(self.logger.entries),
                'by_level': {
                    level.name: len(self.logger.get_entries(level))
                    for level in LogLevel
                }
            },
            'metrics': {
                'counters': dict(self.metrics.counters),
                'gauges': dict(self.metrics.gauges)
            },
            'tracing': {
                'active_spans': len(self.tracing.active_spans),
                'completed_spans': len(self.tracing.completed_spans)
            },
            'events': {
                'total': len(self.events.events)
            }
        }


# Export all observability components
__all__ = [
    'LogLevel',
    'LogConfiguration',
    'LogEntry',
    'StructuredLogger',
    'MetricType',
    'Metric',
    'MetricsCollector',
    'Span',
    'TracingContext',
    'Event',
    'EventEmitter',
    'ObservabilityManager',
]
