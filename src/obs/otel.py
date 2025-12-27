"""Minimal OpenTelemetry wiring (optional).

Design goals:
- Optional dependencies (no import crashes).
- Useful defaults, but no forced global auto-instrumentation.
- Simple LakeClient span wrappers via instrument_lake().

Exported API:
- is_otel_available
- init_otel
- get_tracer
- instrument_lake
- OTelHandle
- OTelNotAvailableError
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional, TYPE_CHECKING
import contextlib
import functools

ExporterType = Literal["none", "console", "otlp"]

if TYPE_CHECKING:  # pragma: no cover
    # Only for typing; must not be required at runtime.
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.trace import Tracer  # type: ignore


class OTelNotAvailableError(RuntimeError):
    """Raised when OpenTelemetry is requested but dependencies are missing."""

    def __init__(self, message: str | None = None) -> None:
        msg = message or ("OpenTelemetry is not available. Install with: pip install -e '.[otel]'")
        super().__init__(msg)


@dataclass(frozen=True)
class OTelHandle:
    """Result of init_otel()."""

    provider: Any
    service_name: str
    exporter_type: ExporterType
    is_noop: bool


class _NoOpSpan:
    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def set_attribute(self, key: str, value: Any) -> None:
        return None

    def record_exception(self, exc: BaseException) -> None:
        return None

    def set_status(self, status: Any) -> None:
        return None


class _NoOpTracer:
    @contextlib.contextmanager
    def start_as_current_span(self, name: str, **kwargs: Any):
        yield _NoOpSpan()


def is_otel_available() -> bool:
    """Return True if OpenTelemetry API+SDK are importable."""
    try:
        import opentelemetry.trace  # noqa: F401
        import opentelemetry.sdk.trace  # noqa: F401

        return True
    except Exception:
        return False


def init_otel(
    service_name: str,
    exporter: ExporterType = "none",
    endpoint: Optional[str] = None,
) -> OTelHandle:
    """Initialize tracing.

    exporter="none": always returns a no-op handle (no deps required).
    exporter!="none": requires OpenTelemetry deps, otherwise raises OTelNotAvailableError.
    """
    if exporter == "none":
        return OTelHandle(
            provider=None, service_name=service_name, exporter_type=exporter, is_noop=True
        )

    if not is_otel_available():
        raise OTelNotAvailableError()

    # Lazy imports
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if exporter == "console":
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    elif exporter == "otlp":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        except Exception as e:  # pragma: no cover
            raise OTelNotAvailableError(
                "OTLP exporter not available. Install with: pip install -e '.[otel]'"
            ) from e

        kwargs: dict[str, Any] = {}
        if endpoint:
            kwargs["endpoint"] = endpoint
        provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(**kwargs)))
    else:  # pragma: no cover
        raise ValueError(f"Unsupported exporter: {exporter}")

    # Best-effort set global provider (doesn't need to be relied upon)
    try:
        trace.set_tracer_provider(provider)
    except Exception:
        # If provider already set, do not fail.
        pass

    return OTelHandle(
        provider=provider, service_name=service_name, exporter_type=exporter, is_noop=False
    )


def get_tracer(name: str, provider: Any | None = None) -> Any:
    """Get a tracer. Returns a no-op tracer if deps missing."""
    if not is_otel_available():
        return _NoOpTracer()

    from opentelemetry import trace

    if provider is not None:
        return trace.get_tracer(name, tracer_provider=provider)
    return trace.get_tracer(name)


def instrument_lake(client: Any, provider: Any | None = None) -> Any:
    """Wrap common LakeClient methods to emit spans.

    Returns the same client instance (methods are wrapped in-place).
    If OpenTelemetry is unavailable, returns client unchanged.
    """
    if not is_otel_available():
        return client

    tracer = get_tracer("src.obs.instrument_lake", provider=provider)

    def _wrap(method_name: str, span_name: str):
        if not hasattr(client, method_name):
            return
        orig = getattr(client, method_name)
        if not callable(orig):
            return

        @functools.wraps(orig)
        def wrapped(*args: Any, **kwargs: Any):
            # Lazy imports for status handling
            try:
                from opentelemetry.trace.status import Status, StatusCode
            except Exception:  # pragma: no cover
                Status = None  # type: ignore
                StatusCode = None  # type: ignore

            with tracer.start_as_current_span(span_name) as span:
                # Common attributes
                try:
                    span.set_attribute("lake.method", method_name)
                    if args and isinstance(args[0], str) and method_name in ("query", "execute"):
                        span.set_attribute("db.statement", args[0])
                    if "path" in kwargs and isinstance(kwargs["path"], str):
                        span.set_attribute("lake.path", kwargs["path"])
                except Exception:
                    pass

                try:
                    return orig(*args, **kwargs)
                except Exception as e:
                    try:
                        span.record_exception(e)
                        if Status is not None and StatusCode is not None:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                    except Exception:
                        pass
                    raise

        setattr(client, method_name, wrapped)

    _wrap("query", "lake.query")
    _wrap("execute", "lake.execute")
    _wrap("create_table_from_df", "lake.create_table_from_df")
    _wrap("register_parquet_file", "lake.register_parquet_file")
    _wrap("register_parquet_folder", "lake.register_parquet_folder")
    _wrap("close", "lake.close")

    return client
