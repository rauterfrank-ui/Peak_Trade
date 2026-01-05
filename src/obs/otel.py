"""
OpenTelemetry Integration (P2.2)
================================
Minimal OTel wiring as optional feature with graceful degradation.

Features:
- Optional dependency on opentelemetry-* packages
- No-op fallback when deps not installed
- Support for OTLP, console, and none exporters
- LakeClient instrumentation for query/execute spans

Usage:
    from src.obs import is_otel_available, init_otel, get_tracer

    if is_otel_available():
        handle = init_otel("my-service", exporter="console")
        tracer = get_tracer("my-module")
        with tracer.start_as_current_span("my-operation"):
            # ... traced code ...
            pass
        handle.shutdown()
    else:
        # No-op tracer, no crashes
        tracer = get_tracer("my-module")
        with tracer.start_as_current_span("my-operation"):
            pass  # Works fine, just no tracing

Non-goals (P2.3):
- Docker/Grafana/Collector setup
- Global auto-instrumentation
- Metrics/Logging integration
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, TypeVar

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer, TracerProvider
    from src.data.lake.client import LakeClient


# ---------------------------------------------------------------------------
# Optional imports - graceful degradation
# ---------------------------------------------------------------------------

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )

    OTEL_API_AVAILABLE = True
except ImportError:
    OTEL_API_AVAILABLE = False
    trace = None  # type: ignore
    SDKTracerProvider = None  # type: ignore
    BatchSpanProcessor = None  # type: ignore
    ConsoleSpanExporter = None  # type: ignore
    SimpleSpanProcessor = None  # type: ignore

# OTLP exporter is separate optional
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False
    OTLPSpanExporter = None  # type: ignore


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class OTelNotAvailableError(RuntimeError):
    """Raised when OpenTelemetry features are requested but deps not installed."""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = "OpenTelemetry is not available. Install with: pip install peak_trade[otel]"
        super().__init__(message)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_otel_available() -> bool:
    """
    Check if OpenTelemetry features are available.

    Returns:
        True if opentelemetry-api and opentelemetry-sdk are installed.
    """
    return OTEL_API_AVAILABLE


@dataclass
class OTelHandle:
    """
    Handle for managing OpenTelemetry lifecycle.

    Attributes:
        provider: The TracerProvider instance (or None for no-op).
        service_name: The service name used for tracing.
        exporter_type: The exporter type configured.
        is_noop: True if this is a no-op handle (OTel not available).
    """

    provider: Optional[Any]  # TracerProvider or None
    service_name: str
    exporter_type: str
    is_noop: bool = False

    def shutdown(self) -> None:
        """Shutdown the tracer provider, flushing any pending spans."""
        if self.provider is not None and hasattr(self.provider, "shutdown"):
            self.provider.shutdown()


# Global state for current provider
_current_provider: Optional[Any] = None
_global_provider_set: bool = False


def init_otel(
    service_name: str,
    exporter: Literal["otlp", "console", "none"] = "none",
    endpoint: Optional[str] = None,
    *,
    _force_new_provider: bool = False,
) -> OTelHandle:
    """
    Initialize OpenTelemetry with specified configuration.

    Args:
        service_name: Name of the service for tracing context.
        exporter: Exporter type - "otlp", "console", or "none".
                  "none" creates a provider but exports nothing.
        endpoint: OTLP endpoint URL (only used when exporter="otlp").
                  Defaults to "http://localhost:4317" if not specified.
        _force_new_provider: Internal flag for testing - creates new provider
                            without setting as global (allows multiple inits).

    Returns:
        OTelHandle for managing the OTel lifecycle.

    Note:
        If OTel dependencies are not installed, returns a no-op handle
        that does nothing but won't crash.

    Example:
        >>> handle = init_otel("peak-trade", exporter="console")
        >>> # ... use tracing ...
        >>> handle.shutdown()
    """
    global _current_provider, _global_provider_set

    if not OTEL_API_AVAILABLE:
        return OTelHandle(
            provider=None,
            service_name=service_name,
            exporter_type=exporter,
            is_noop=True,
        )

    # Create provider with resource
    from opentelemetry.sdk.resources import Resource

    resource = Resource.create({"service.name": service_name})
    provider = SDKTracerProvider(resource=resource)

    # Configure exporter
    if exporter == "console":
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
    elif exporter == "otlp":
        if not OTLP_AVAILABLE:
            raise OTelNotAvailableError(
                "OTLP exporter not available. Install with: pip install opentelemetry-exporter-otlp"
            )
        otlp_endpoint = endpoint or "http://localhost:4317"
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
    # else: "none" - no processor, spans are created but not exported

    # Set as global provider (only once, OTel doesn't allow override)
    if not _global_provider_set and not _force_new_provider:
        trace.set_tracer_provider(provider)
        _global_provider_set = True

    _current_provider = provider

    return OTelHandle(
        provider=provider,
        service_name=service_name,
        exporter_type=exporter,
        is_noop=False,
    )


def get_tracer(name: str, provider: Optional[Any] = None) -> "Tracer":
    """
    Get a tracer instance for the given module name.

    Args:
        name: Name for the tracer (typically module name).
        provider: Optional TracerProvider to use. If not specified, uses
                  the current provider set by init_otel(), or the global one.

    Returns:
        A Tracer instance. If OTel is not available, returns a no-op tracer
        that creates no-op spans (safe to use, just doesn't trace).

    Example:
        >>> tracer = get_tracer("src.data.lake")
        >>> with tracer.start_as_current_span("query"):
        ...     result = execute_query()
    """
    if not OTEL_API_AVAILABLE:
        return _NoOpTracer()

    # Use provided provider, or current provider, or global
    if provider is not None:
        return provider.get_tracer(name)
    if _current_provider is not None:
        return _current_provider.get_tracer(name)
    return trace.get_tracer(name)


# ---------------------------------------------------------------------------
# No-Op Implementations
# ---------------------------------------------------------------------------


class _NoOpSpan:
    """No-op span that does nothing."""

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *args) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_attributes(self, attributes: dict) -> None:
        pass

    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        pass

    def record_exception(self, exception: BaseException) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass

    def end(self) -> None:
        pass

    @property
    def is_recording(self) -> bool:
        return False


class _NoOpTracer:
    """No-op tracer that creates no-op spans."""

    def start_span(self, name: str, **kwargs) -> _NoOpSpan:
        return _NoOpSpan()

    def start_as_current_span(self, name: str, **kwargs) -> _NoOpSpan:
        return _NoOpSpan()


# ---------------------------------------------------------------------------
# LakeClient Instrumentation
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def instrument_lake(
    client: "LakeClient",
    provider: Optional[Any] = None,
) -> "LakeClient":
    """
    Add OpenTelemetry spans to LakeClient operations.

    Wraps query(), execute(), register_parquet_file(), and register_parquet_folder()
    methods to create spans for each operation.

    Args:
        client: LakeClient instance to instrument.
        provider: Optional TracerProvider to use for creating spans.

    Returns:
        The same client instance with instrumented methods.

    Note:
        If OTel is not available, returns the client unchanged (no-op).
        Safe to call unconditionally.

    Example:
        >>> from src.data.lake import LakeClient
        >>> from src.obs import instrument_lake, init_otel
        >>>
        >>> init_otel("my-service", exporter="console")
        >>> client = LakeClient(":memory:")
        >>> client = instrument_lake(client)
        >>> client.query("SELECT 1")  # Creates a span
    """
    tracer = get_tracer("src.data.lake", provider=provider)

    # Store original methods
    original_query = client.query
    original_execute = client.execute
    original_register_parquet_file = client.register_parquet_file
    original_register_parquet_folder = client.register_parquet_folder
    original_create_table_from_df = client.create_table_from_df

    @functools.wraps(original_query)
    def traced_query(sql: str):
        with tracer.start_as_current_span("lake.query") as span:
            span.set_attribute("db.system", "duckdb")
            span.set_attribute("db.statement", sql[:500])  # Truncate long queries
            try:
                result = original_query(sql)
                span.set_attribute(
                    "db.row_count", len(result) if hasattr(result, "__len__") else -1
                )
                return result
            except Exception as e:
                span.record_exception(e)
                raise

    @functools.wraps(original_execute)
    def traced_execute(sql: str):
        with tracer.start_as_current_span("lake.execute") as span:
            span.set_attribute("db.system", "duckdb")
            span.set_attribute("db.statement", sql[:500])
            try:
                return original_execute(sql)
            except Exception as e:
                span.record_exception(e)
                raise

    @functools.wraps(original_register_parquet_file)
    def traced_register_parquet_file(file_path, table_name):
        with tracer.start_as_current_span("lake.register_parquet_file") as span:
            span.set_attribute("db.system", "duckdb")
            span.set_attribute("lake.table_name", table_name)
            span.set_attribute("lake.file_path", str(file_path))
            try:
                return original_register_parquet_file(file_path, table_name)
            except Exception as e:
                span.record_exception(e)
                raise

    @functools.wraps(original_register_parquet_folder)
    def traced_register_parquet_folder(folder_path, table_name, glob_pattern="**/*.parquet"):
        with tracer.start_as_current_span("lake.register_parquet_folder") as span:
            span.set_attribute("db.system", "duckdb")
            span.set_attribute("lake.table_name", table_name)
            span.set_attribute("lake.folder_path", str(folder_path))
            span.set_attribute("lake.glob_pattern", glob_pattern)
            try:
                return original_register_parquet_folder(folder_path, table_name, glob_pattern)
            except Exception as e:
                span.record_exception(e)
                raise

    @functools.wraps(original_create_table_from_df)
    def traced_create_table_from_df(df, table_name, if_exists="replace"):
        with tracer.start_as_current_span("lake.create_table_from_df") as span:
            span.set_attribute("db.system", "duckdb")
            span.set_attribute("lake.table_name", table_name)
            span.set_attribute("lake.if_exists", if_exists)
            span.set_attribute("lake.row_count", len(df) if hasattr(df, "__len__") else -1)
            try:
                return original_create_table_from_df(df, table_name, if_exists)
            except Exception as e:
                span.record_exception(e)
                raise

    # Replace methods
    client.query = traced_query  # type: ignore
    client.execute = traced_execute  # type: ignore
    client.register_parquet_file = traced_register_parquet_file  # type: ignore
    client.register_parquet_folder = traced_register_parquet_folder  # type: ignore
    client.create_table_from_df = traced_create_table_from_df  # type: ignore

    # Mark as instrumented
    client._otel_instrumented = True  # type: ignore

    return client
