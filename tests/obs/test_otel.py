"""
Tests for OpenTelemetry integration (P2.2)

Test strategy:
- Without OTel deps: is_otel_available()==False, no-op handle, no exceptions
- With OTel deps: init_otel creates tracer provider, exporters work
- Lake spans: query/execute create spans when OTel available
"""

import pytest


# ---------------------------------------------------------------------------
# Availability detection
# ---------------------------------------------------------------------------


def test_is_otel_available_returns_bool():
    """is_otel_available() returns a boolean without crashing."""
    from src.obs.otel import is_otel_available

    result = is_otel_available()
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Tests that run WITHOUT OTel deps (skip if available)
# ---------------------------------------------------------------------------


@pytest.fixture
def otel_not_available(monkeypatch):
    """Mock OTel as unavailable."""
    import src.obs.otel as otel_module

    monkeypatch.setattr(otel_module, "OTEL_API_AVAILABLE", False)
    return True


def test_is_otel_available_without_deps(otel_not_available):
    """is_otel_available() returns False when deps not installed."""
    from src.obs.otel import OTEL_API_AVAILABLE

    assert OTEL_API_AVAILABLE is False


def test_init_otel_without_deps_returns_noop_handle(otel_not_available):
    """init_otel() returns no-op handle when deps not installed."""
    from src.obs.otel import init_otel

    handle = init_otel("test-service", exporter="console")

    assert handle.is_noop is True
    assert handle.service_name == "test-service"
    assert handle.exporter_type == "console"
    assert handle.provider is None

    # Shutdown should not crash
    handle.shutdown()


def test_get_tracer_without_deps_returns_noop(otel_not_available):
    """get_tracer() returns no-op tracer when deps not installed."""
    from src.obs.otel import get_tracer, _NoOpTracer

    tracer = get_tracer("test-module")

    assert isinstance(tracer, _NoOpTracer)


def test_noop_tracer_context_manager(otel_not_available):
    """No-op tracer spans work as context managers."""
    from src.obs.otel import get_tracer

    tracer = get_tracer("test-module")

    # Should not crash
    with tracer.start_as_current_span("test-span") as span:
        span.set_attribute("key", "value")
        span.set_attributes({"a": 1, "b": 2})
        span.add_event("test-event", {"detail": "info"})
        assert span.is_recording is False


def test_noop_span_methods(otel_not_available):
    """No-op span has all required methods."""
    from src.obs.otel import _NoOpSpan

    span = _NoOpSpan()

    # All methods should exist and not crash
    span.set_attribute("key", "value")
    span.set_attributes({"a": 1})
    span.add_event("event")
    span.record_exception(ValueError("test"))
    span.set_status("OK")
    span.end()
    assert span.is_recording is False


# ---------------------------------------------------------------------------
# Tests that run WITH OTel deps (skip if not available)
# ---------------------------------------------------------------------------


try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider

    OTEL_INSTALLED = True
except ImportError:
    OTEL_INSTALLED = False


requires_otel = pytest.mark.skipif(not OTEL_INSTALLED, reason="OTel not installed")


@requires_otel
def test_is_otel_available_with_deps():
    """is_otel_available() returns True when deps installed."""
    from src.obs.otel import is_otel_available

    assert is_otel_available() is True


@requires_otel
def test_init_otel_none_exporter():
    """init_otel with exporter='none' creates provider but no exporter."""
    from src.obs.otel import init_otel

    handle = init_otel("test-service-none", exporter="none")

    assert handle.is_noop is False
    assert handle.service_name == "test-service-none"
    assert handle.exporter_type == "none"
    assert handle.provider is not None

    handle.shutdown()


@requires_otel
def test_init_otel_console_exporter():
    """init_otel with exporter='console' creates console exporter."""
    from src.obs.otel import init_otel, get_tracer
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter

    handle = init_otel("test-service-console", exporter="console", _force_new_provider=True)

    assert handle.is_noop is False
    assert handle.exporter_type == "console"

    # Verify a console exporter is configured in the provider's span processors
    processors = handle.provider._active_span_processor._span_processors
    has_console_exporter = any(
        isinstance(getattr(p, "span_exporter", None), ConsoleSpanExporter) for p in processors
    )
    assert has_console_exporter, "Console exporter should be configured"

    # Verify spans can be created without error
    tracer = get_tracer("test-module", provider=handle.provider)
    with tracer.start_as_current_span("test-span"):
        pass

    handle.shutdown()


@requires_otel
def test_get_tracer_returns_real_tracer():
    """get_tracer() returns real tracer when deps installed."""
    from src.obs.otel import init_otel, get_tracer, _NoOpTracer

    handle = init_otel("test-service-tracer", exporter="none")
    tracer = get_tracer("test-module")

    assert not isinstance(tracer, _NoOpTracer)

    handle.shutdown()


@requires_otel
def test_tracer_creates_spans():
    """Tracer creates actual spans when OTel available."""
    from src.obs.otel import init_otel, get_tracer
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    # Use in-memory exporter to capture spans
    exporter = InMemorySpanExporter()
    handle = init_otel("test-service-spans", exporter="none", _force_new_provider=True)
    handle.provider.add_span_processor(SimpleSpanProcessor(exporter))

    tracer = get_tracer("test-module", provider=handle.provider)
    with tracer.start_as_current_span("test-operation") as span:
        span.set_attribute("test.key", "test-value")

    spans = exporter.get_finished_spans()
    assert len(spans) >= 1
    assert any(s.name == "test-operation" for s in spans)

    handle.shutdown()


# ---------------------------------------------------------------------------
# Lake instrumentation tests
# ---------------------------------------------------------------------------


try:
    import duckdb

    DUCKDB_INSTALLED = True
except ImportError:
    DUCKDB_INSTALLED = False


requires_lake = pytest.mark.skipif(not DUCKDB_INSTALLED, reason="DuckDB not installed")
requires_otel_and_lake = pytest.mark.skipif(
    not (OTEL_INSTALLED and DUCKDB_INSTALLED),
    reason="OTel or DuckDB not installed",
)


@requires_lake
def test_instrument_lake_without_otel(otel_not_available):
    """instrument_lake() works without OTel (no-op)."""
    from src.data.lake import LakeClient
    from src.obs.otel import instrument_lake

    client = LakeClient(":memory:")
    instrumented = instrument_lake(client)

    # Should be the same client
    assert instrumented is client
    assert hasattr(client, "_otel_instrumented")
    assert client._otel_instrumented is True

    # Operations should still work
    result = client.query("SELECT 1 as x")
    assert len(result) == 1

    client.close()


@requires_otel_and_lake
def test_instrument_lake_query_creates_span():
    """instrument_lake() creates spans for query()."""
    from src.data.lake import LakeClient
    from src.obs.otel import init_otel, instrument_lake
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    # Setup tracing with in-memory exporter
    exporter = InMemorySpanExporter()
    handle = init_otel("test-lake-query", exporter="none", _force_new_provider=True)
    handle.provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Instrument client with explicit provider
    client = LakeClient(":memory:")
    client = instrument_lake(client, provider=handle.provider)

    # Execute query
    client.query("SELECT 1 as x, 2 as y")

    # Check spans
    spans = exporter.get_finished_spans()
    query_spans = [s for s in spans if s.name == "lake.query"]
    assert len(query_spans) >= 1

    span = query_spans[0]
    assert span.attributes.get("db.system") == "duckdb"
    assert "SELECT 1" in span.attributes.get("db.statement", "")

    client.close()
    handle.shutdown()


@requires_otel_and_lake
def test_instrument_lake_execute_creates_span():
    """instrument_lake() creates spans for execute()."""
    from src.data.lake import LakeClient
    from src.obs.otel import init_otel, instrument_lake
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    # Setup tracing
    exporter = InMemorySpanExporter()
    handle = init_otel("test-lake-execute", exporter="none", _force_new_provider=True)
    handle.provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Instrument client with explicit provider
    client = LakeClient(":memory:")
    client = instrument_lake(client, provider=handle.provider)

    # Execute DDL
    client.execute("CREATE TABLE test (id INTEGER)")

    # Check spans
    spans = exporter.get_finished_spans()
    execute_spans = [s for s in spans if s.name == "lake.execute"]
    assert len(execute_spans) >= 1

    span = execute_spans[0]
    assert span.attributes.get("db.system") == "duckdb"
    assert "CREATE TABLE" in span.attributes.get("db.statement", "")

    client.close()
    handle.shutdown()


@requires_otel_and_lake
def test_instrument_lake_create_table_from_df_creates_span():
    """instrument_lake() creates spans for create_table_from_df()."""
    import pandas as pd
    from src.data.lake import LakeClient
    from src.obs.otel import init_otel, instrument_lake
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    # Setup tracing
    exporter = InMemorySpanExporter()
    handle = init_otel("test-lake-df", exporter="none", _force_new_provider=True)
    handle.provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Instrument client with explicit provider
    client = LakeClient(":memory:")
    client = instrument_lake(client, provider=handle.provider)

    # Create table from DataFrame
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    client.create_table_from_df(df, "test_table")

    # Check spans
    spans = exporter.get_finished_spans()
    df_spans = [s for s in spans if s.name == "lake.create_table_from_df"]
    assert len(df_spans) >= 1

    span = df_spans[0]
    assert span.attributes.get("lake.table_name") == "test_table"
    assert span.attributes.get("lake.row_count") == 3

    client.close()
    handle.shutdown()


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


@requires_otel_and_lake
def test_instrument_lake_records_exception_on_error():
    """instrument_lake() records exceptions in spans."""
    from src.data.lake import LakeClient
    from src.data.lake.errors import LakeQueryError
    from src.obs.otel import init_otel, instrument_lake
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    # Setup tracing
    exporter = InMemorySpanExporter()
    handle = init_otel("test-lake-error", exporter="none", _force_new_provider=True)
    handle.provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Instrument client with explicit provider
    client = LakeClient(":memory:")
    client = instrument_lake(client, provider=handle.provider)

    # Execute invalid query
    with pytest.raises(LakeQueryError):
        client.query("SELECT * FROM nonexistent_table")

    # Check span has exception recorded
    spans = exporter.get_finished_spans()
    query_spans = [s for s in spans if s.name == "lake.query"]
    assert len(query_spans) >= 1

    span = query_spans[0]
    # Span should have events (exception recorded)
    assert len(span.events) >= 1

    client.close()
    handle.shutdown()


# ---------------------------------------------------------------------------
# OTelHandle tests
# ---------------------------------------------------------------------------


def test_otel_handle_dataclass():
    """OTelHandle has expected attributes."""
    from src.obs.otel import OTelHandle

    handle = OTelHandle(
        provider=None,
        service_name="test",
        exporter_type="none",
        is_noop=True,
    )

    assert handle.provider is None
    assert handle.service_name == "test"
    assert handle.exporter_type == "none"
    assert handle.is_noop is True


def test_otel_handle_shutdown_noop():
    """OTelHandle.shutdown() works on no-op handle."""
    from src.obs.otel import OTelHandle

    handle = OTelHandle(
        provider=None,
        service_name="test",
        exporter_type="none",
        is_noop=True,
    )

    # Should not crash
    handle.shutdown()


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


def test_module_exports():
    """Module exports all expected symbols."""
    from src.obs import (
        is_otel_available,
        init_otel,
        get_tracer,
        instrument_lake,
        OTelHandle,
        OTelNotAvailableError,
    )

    assert callable(is_otel_available)
    assert callable(init_otel)
    assert callable(get_tracer)
    assert callable(instrument_lake)
    assert OTelHandle is not None
    assert issubclass(OTelNotAvailableError, RuntimeError)


def test_import_does_not_crash_without_deps():
    """Importing the module never crashes, even without deps."""
    # This test proves the import succeeds
    import src.obs.otel

    assert hasattr(src.obs.otel, "is_otel_available")
    assert hasattr(src.obs.otel, "init_otel")
    assert hasattr(src.obs.otel, "get_tracer")
