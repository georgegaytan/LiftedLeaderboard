import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# Context variable for current trace context
trace_context: ContextVar[Optional['TraceSpan']] = ContextVar(
    'trace_context', default=None
)

logger = logging.getLogger(__name__)


@dataclass
class TraceSpan:
    '''A trace span with timing and metadata.'''

    name: str
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent: Optional['TraceSpan'] = None
    children: list['TraceSpan'] = field(default_factory=list)

    @property
    def duration(self) -> Optional[float]:
        '''Get duration in seconds.'''
        return self.end_time - self.start_time if self.end_time else None

    def finish(self) -> None:
        '''Mark the span as finished.'''
        self.end_time = time.perf_counter()

        # Log the span completion
        duration_ms = (self.duration or 0) * 1000
        metadata_str = ', '.join(f'{k}={v}' for k, v in self.metadata.items())

        if self.parent:
            logger.info(
                f'⏱️  {self.name}: '
                f'{duration_ms:.2f}ms '
                f'(parent: {self.parent.name}) [{metadata_str}]'
            )
        else:
            logger.info(f'⏱️  {self.name}: {duration_ms:.2f}ms [{metadata_str}]')


@contextmanager
def trace_span(name: str, metadata: Optional[Dict[str, Any]] = None):
    '''Create a trace span with automatic timing and context management.

    Args:
        name: Name of the span
        metadata: Optional metadata to attach to the span

    Example:
        with trace_span("database.query", {"table": "users", "operation": "select"}):
            rows = db.fetchall("SELECT * FROM users")
    '''
    # Get current parent span
    parent = trace_context.get()

    # Create new span
    span = TraceSpan(name=name, metadata=metadata or {}, parent=parent)

    # Add to parent's children if exists
    if parent:
        parent.children.append(span)

    # Set as current context
    token = trace_context.set(span)

    try:
        yield span
    finally:
        span.finish()
        # Restore previous context
        trace_context.reset(token)


def get_current_span() -> Optional[TraceSpan]:
    '''Get the current trace span.'''
    return trace_context.get()


def add_span_metadata(key: str, value: Any) -> None:
    '''Add metadata to the current span.'''
    current = trace_context.get()
    if current:
        current.metadata[key] = value
